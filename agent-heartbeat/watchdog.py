#!/usr/bin/env python3
"""
Watchdog Supervisor — AHOS Process Monitor

The second daemon. Watches the heartbeat process and everything
it depends on. If anything dies, the watchdog restarts it and
logs the incident.

Monitors:
  1. Heartbeat daemon process (restarts on crash)
  2. Julie-Winters connectivity (Orange Pi 5)
  3. Qdrant / RAG availability
  4. Disk space on output directories
  5. Log file growth (detects stuck processes)

Usage:
    python3 watchdog.py                    # Run supervisor
    python3 watchdog.py --status           # Show current status
    python3 watchdog.py --check            # One-shot health check

The watchdog is the ONLY process that should be started manually.
Everything else is managed by it.
"""

import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
HEARTBEAT_SCRIPT = os.path.join(os.path.dirname(__file__), "heartbeat.py")
LOG_DIR = Path(os.path.dirname(__file__)) / "logs"
WATCHDOG_LOG = LOG_DIR / "watchdog.log"
STATUS_FILE = LOG_DIR / "watchdog_status.json"

JULIE_HOST = "192.168.1.60"
JULIE_RAG_PORT = 8080
QDRANT_URL = f"http://{JULIE_HOST}:6333"
QDRANT_COLLECTION = "vjlive_code"

# How often to check (seconds)
CHECK_INTERVAL = 30
# How many consecutive crashes before alerting
CRASH_THRESHOLD = 5
# Minimum seconds between restarts (prevents restart loops)
MIN_RESTART_INTERVAL = 10
# Maximum log file size before rotation (10MB)
MAX_LOG_SIZE = 10 * 1024 * 1024

logger = logging.getLogger("watchdog")

# Alert history file
ALERT_HISTORY = LOG_DIR / "alerts.json"


# ---------------------------------------------------------------------------
# Desktop Alerting
# ---------------------------------------------------------------------------
def alert(title: str, message: str, urgency: str = "normal") -> None:
    """
    Send a desktop notification and log to alert history.

    Urgency: 'low', 'normal', 'critical'
    Uses notify-send on Linux. Falls back to logging if unavailable.
    """
    timestamp = datetime.now().isoformat()
    logger.warning(f"\u26a0\ufe0f  ALERT [{urgency}]: {title} — {message}")

    # Desktop notification via notify-send
    try:
        subprocess.run(
            [
                "notify-send",
                "--urgency", urgency,
                "--icon", "dialog-warning",
                "--app-name", "AHOS Watchdog",
                f"\U0001f6a8 {title}",
                message,
            ],
            capture_output=True,
            timeout=5,
        )
    except FileNotFoundError:
        logger.debug("notify-send not available — alert logged only")
    except Exception as e:
        logger.debug(f"Desktop notification failed: {e}")

    # Write to alert history for audit trail
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        history = []
        if ALERT_HISTORY.exists():
            try:
                history = json.loads(ALERT_HISTORY.read_text())
            except Exception:
                history = []
        history.append({
            "timestamp": timestamp,
            "urgency": urgency,
            "title": title,
            "message": message,
        })
        # Keep last 100 alerts
        history = history[-100:]
        ALERT_HISTORY.write_text(
            json.dumps(history, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.error(f"Failed to write alert history: {e}")


# ---------------------------------------------------------------------------
# Process Management
# ---------------------------------------------------------------------------
class ProcessMonitor:
    """Monitors and manages a child process."""

    def __init__(self, script_path: str, name: str = "heartbeat"):
        self.script_path = script_path
        self.name = name
        self.process = None
        self.pid = None
        self.start_time = None
        self.crash_count = 0
        self.total_restarts = 0
        self.last_restart = None
        self.last_exit_code = None

    def start(self) -> bool:
        """Start the managed process."""
        if self.is_running():
            logger.info(f"  {self.name} already running (PID {self.pid})")
            return True

        # Prevent restart loops
        if self.last_restart:
            elapsed = (datetime.now() - self.last_restart).total_seconds()
            if elapsed < MIN_RESTART_INTERVAL:
                wait = MIN_RESTART_INTERVAL - elapsed
                logger.warning(f"  Restart throttle: waiting {wait:.0f}s")
                time.sleep(wait)

        try:
            log_file = LOG_DIR / f"{self.name}_{datetime.now().strftime('%Y-%m-%d')}.log"
            self.process = subprocess.Popen(
                [sys.executable, self.script_path, "--daemon", "heartbeat-daemon"],
                stdout=open(str(log_file), "a"),
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(self.script_path),
                preexec_fn=os.setsid,  # Own process group for clean kill
            )
            self.pid = self.process.pid
            self.start_time = datetime.now()
            self.last_restart = datetime.now()
            self.total_restarts += 1
            logger.info(f"  ✅ {self.name} started (PID {self.pid})")
            return True
        except Exception as e:
            logger.error(f"  ❌ Failed to start {self.name}: {e}")
            return False

    def is_running(self) -> bool:
        """Check if the managed process is still alive."""
        if self.process is None:
            return False
        poll = self.process.poll()
        if poll is not None:
            self.last_exit_code = poll
            return False
        return True

    def stop(self) -> None:
        """Gracefully stop the managed process."""
        if self.process and self.is_running():
            logger.info(f"  Stopping {self.name} (PID {self.pid})...")
            try:
                # Send SIGTERM to the process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=10)
                logger.info(f"  ✅ {self.name} stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"  ⚠️  {self.name} didn't stop — sending SIGKILL")
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    self.process.wait(timeout=5)
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"  ❌ Error stopping {self.name}: {e}")

    def check_and_restart(self) -> dict:
        """Check process health and restart if needed. Returns status dict."""
        status = {
            "name": self.name,
            "running": False,
            "pid": self.pid,
            "uptime_seconds": 0,
            "crash_count": self.crash_count,
            "total_restarts": self.total_restarts,
            "last_exit_code": self.last_exit_code,
            "action": "none",
        }

        if self.is_running():
            uptime = (datetime.now() - self.start_time).total_seconds()
            status["running"] = True
            status["uptime_seconds"] = round(uptime)
            # Reset crash count after 5 min of stable running
            if uptime > 300:
                self.crash_count = 0
            return status

        # Process is dead
        if self.pid is not None:
            self.crash_count += 1
            logger.warning(
                f"  💀 {self.name} died (PID {self.pid}, "
                f"exit={self.last_exit_code}, "
                f"crashes={self.crash_count}/{CRASH_THRESHOLD})"
            )
            status["action"] = "crashed"

        if self.crash_count >= CRASH_THRESHOLD:
            logger.error(
                f"  🚨 {self.name} crashed {self.crash_count} times — "
                f"NOT restarting. Manual intervention required."
            )
            status["action"] = "abandoned"
            return status

        # Restart
        logger.info(f"  🔄 Restarting {self.name}...")
        if self.start():
            status["running"] = True
            status["pid"] = self.pid
            status["action"] = "restarted"
        else:
            status["action"] = "restart_failed"

        return status


# ---------------------------------------------------------------------------
# Infrastructure Checks
# ---------------------------------------------------------------------------
def check_julie(host: str = JULIE_HOST, port: int = JULIE_RAG_PORT) -> dict:
    """Check Julie-Winters connectivity and RAG availability."""
    result = {"host": host, "pingable": False, "rag_available": False}

    # Ping check
    try:
        ret = subprocess.run(
            ["ping", "-c", "1", "-W", "2", host],
            capture_output=True, timeout=5,
        )
        result["pingable"] = ret.returncode == 0
    except Exception:
        pass

    # RAG port check
    if result["pingable"]:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"http://{host}:{port}/stats",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                result["rag_available"] = resp.status == 200
        except Exception:
            pass

    return result


def check_qdrant(url: str = QDRANT_URL, collection: str = QDRANT_COLLECTION) -> dict:
    """Check Qdrant is up and the legacy code collection has data.
    
    This is a HARD requirement. If Qdrant is down, the pipeline STOPS.
    No graceful fallbacks. The whole horse crosses the line.
    """
    result = {"url": url, "collection": collection, "reachable": False, "points": 0, "healthy": False}
    
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{url}/collections/{collection}",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            import json as _json
            data = _json.loads(resp.read().decode('utf-8'))
            r = data.get('result', {})
            result['reachable'] = True
            result['points'] = r.get('points_count', 0)
            result['status'] = r.get('status', 'unknown')
            # Healthy = reachable AND has data AND status is green
            result['healthy'] = (
                result['reachable'] 
                and result['points'] > 0 
                and result['status'] == 'green'
            )
    except Exception as e:
        result['error'] = str(e)
    
    return result


def check_disk_space(path: str = ".") -> dict:
    """Check available disk space."""
    try:
        stat = os.statvfs(path)
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
        total_gb = (stat.f_blocks * stat.f_frsize) / (1024 ** 3)
        return {
            "path": path,
            "free_gb": round(free_gb, 1),
            "total_gb": round(total_gb, 1),
            "percent_free": round((free_gb / total_gb) * 100, 1) if total_gb > 0 else 0,
            "warning": free_gb < 1.0,
        }
    except Exception as e:
        return {"path": path, "error": str(e), "warning": True}


def check_log_growth(log_dir: Path = LOG_DIR) -> dict:
    """Check if log files are growing (indicates active processing)."""
    result = {"log_dir": str(log_dir), "files": 0, "total_bytes": 0, "stale": False}
    try:
        log_files = list(log_dir.glob("*.log"))
        result["files"] = len(log_files)
        if log_files:
            newest = max(log_files, key=lambda f: f.stat().st_mtime)
            age = time.time() - newest.stat().st_mtime
            result["newest_log"] = str(newest.name)
            result["newest_age_seconds"] = round(age)
            result["total_bytes"] = sum(f.stat().st_size for f in log_files)
            # Stale if newest log hasn't been written in 10 minutes
            result["stale"] = age > 600
    except Exception as e:
        result["error"] = str(e)
    return result


# ---------------------------------------------------------------------------
# Status Reporting
# ---------------------------------------------------------------------------
def save_status(status: dict) -> None:
    """Save current status to disk for external monitoring."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        status["timestamp"] = datetime.now().isoformat()
        STATUS_FILE.write_text(
            json.dumps(status, indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as e:
        logger.error(f"Failed to save status: {e}")


def print_status(status: dict) -> None:
    """Print human-readable status report."""
    print(f"\n{'=' * 60}")
    print(f"🐕 AHOS Watchdog Status — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'=' * 60}")

    # Heartbeat
    hb = status.get("heartbeat", {})
    running = "✅ RUNNING" if hb.get("running") else "❌ DOWN"
    print(f"\n  Heartbeat: {running}")
    if hb.get("running"):
        print(f"    PID: {hb.get('pid')}")
        uptime = hb.get("uptime_seconds", 0)
        print(f"    Uptime: {uptime // 60}m {uptime % 60}s")
    print(f"    Crashes: {hb.get('crash_count', 0)}")
    print(f"    Total restarts: {hb.get('total_restarts', 0)}")

    # Julie
    julie = status.get("julie", {})
    ping = "✅" if julie.get("pingable") else "❌"
    rag = "✅" if julie.get("rag_available") else "❌"
    print(f"\n  Julie-Winters: ping={ping}  RAG={rag}")

    # Disk
    disk = status.get("disk", {})
    if disk.get("warning"):
        print(f"\n  ⚠️  Disk: {disk.get('free_gb', '?')}GB free — LOW!")
    else:
        print(f"\n  Disk: {disk.get('free_gb', '?')}GB free / {disk.get('total_gb', '?')}GB")

    # Logs
    logs = status.get("logs", {})
    print(f"\n  Logs: {logs.get('files', 0)} files, {logs.get('total_bytes', 0) // 1024}KB")
    if logs.get("stale"):
        print(f"  ⚠️  Logs are stale (no writes in {logs.get('newest_age_seconds', 0)}s)")

    print(f"\n{'=' * 60}")


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------
def main():
    """Watchdog supervisor main loop."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(WATCHDOG_LOG), encoding="utf-8"),
        ],
    )

    # Handle --status and --check flags
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            try:
                status = json.loads(STATUS_FILE.read_text())
                print_status(status)
            except FileNotFoundError:
                print("No status file found. Watchdog hasn't run yet.")
            return
        elif sys.argv[1] == "--check":
            status = {
                "julie": check_julie(),
                "disk": check_disk_space(),
                "logs": check_log_growth(),
            }
            print_status(status)
            return

    logger.info("=" * 60)
    logger.info("🐕 AHOS Watchdog Supervisor")
    logger.info("   Watching the watchers.")
    logger.info(f"   Check interval: {CHECK_INTERVAL}s")
    logger.info(f"   Crash threshold: {CRASH_THRESHOLD}")
    logger.info(f"   Log: {WATCHDOG_LOG}")
    logger.info(f"   Started: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    # Create the heartbeat monitor
    heartbeat = ProcessMonitor(HEARTBEAT_SCRIPT, name="heartbeat")

    # Register signal handlers for clean shutdown
    def shutdown(signum, frame):
        logger.info(f"\n🐕 Watchdog received signal {signum} — shutting down...")
        heartbeat.stop()
        logger.info("🐕 All processes stopped. Goodbye.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Main supervision loop
    check_count = 0
    try:
        while True:
            check_count += 1
            logger.info(f"\n--- Check #{check_count} at {datetime.now().strftime('%H:%M:%S')} ---")

            # 1. Check/restart heartbeat
            hb_status = heartbeat.check_and_restart()

            # Alert on crash events
            if hb_status.get("action") == "crashed":
                alert(
                    "Heartbeat Crashed",
                    f"PID {hb_status.get('pid')} exited with code {hb_status.get('last_exit_code')}. "
                    f"Crash #{hb_status.get('crash_count')}/{CRASH_THRESHOLD}. Restarting...",
                    urgency="normal",
                )
            elif hb_status.get("action") == "abandoned":
                alert(
                    "Heartbeat ABANDONED",
                    f"Crashed {CRASH_THRESHOLD} times. Manual intervention required!",
                    urgency="critical",
                )
            elif hb_status.get("action") == "restart_failed":
                alert(
                    "Heartbeat Restart Failed",
                    "Could not restart the heartbeat process.",
                    urgency="critical",
                )

            # 2. Check Qdrant (EVERY check — this is a hard requirement)
            qdrant_status = check_qdrant()
            if qdrant_status.get("healthy"):
                logger.info(f"  Qdrant: \u2705 {qdrant_status.get('points')} points")
            else:
                logger.error(f"  Qdrant: \u274c DOWN — halting pipeline")
                alert(
                    "Qdrant DOWN — Pipeline HALTED",
                    f"Qdrant at {QDRANT_URL} is unreachable or empty. "
                    f"Error: {qdrant_status.get('error', 'no data')}. "
                    f"Heartbeat STOPPED until Qdrant recovers.",
                    urgency="critical",
                )
                # HARD STOP — kill heartbeat until Qdrant comes back
                if heartbeat.is_running():
                    logger.warning("  Stopping heartbeat — no specs without legacy code")
                    heartbeat.stop()
                # Skip rest of checks, wait for next cycle
                time.sleep(CHECK_INTERVAL)
                continue

            # 3. Check Julie (every 5th check to avoid spam)
            julie_status = {}
            if check_count % 5 == 1:
                julie_status = check_julie()
                if julie_status.get("pingable"):
                    rag = "\u2705" if julie_status.get("rag_available") else "\u274c"
                    logger.info(f"  Julie: ping=\u2705  RAG={rag}")
                else:
                    logger.warning(f"  Julie: \u274c UNREACHABLE")
                    alert(
                        "Julie-Winters Unreachable",
                        f"Cannot ping {JULIE_HOST}. RAG and local LLM review unavailable.",
                        urgency="low",
                    )

            # 3. Check disk space (every 10th check)
            disk_status = {}
            if check_count % 10 == 1:
                disk_status = check_disk_space()
                if disk_status.get("warning"):
                    alert(
                        "Low Disk Space",
                        f"Only {disk_status.get('free_gb')}GB free!",
                        urgency="critical",
                    )
                else:
                    logger.info(f"  Disk: {disk_status.get('free_gb')}GB free")

            # 4. Check log growth
            log_status = check_log_growth()
            if log_status.get("stale") and hb_status.get("running"):
                alert(
                    "Possible Hang Detected",
                    f"Heartbeat is running but logs haven't been written in "
                    f"{log_status.get('newest_age_seconds', 0)}s.",
                    urgency="normal",
                )

            # 5. Save status for external monitoring
            full_status = {
                "heartbeat": hb_status,
                "julie": julie_status,
                "disk": disk_status,
                "logs": log_status,
                "check_count": check_count,
                "watchdog_pid": os.getpid(),
            }
            save_status(full_status)

            # 6. Rotate oversized logs
            try:
                for log_file in LOG_DIR.glob("*.log"):
                    if log_file.stat().st_size > MAX_LOG_SIZE:
                        rotated = log_file.with_suffix(f".{datetime.now().strftime('%H%M%S')}.old")
                        log_file.rename(rotated)
                        logger.info(f"  \U0001f4dc Rotated {log_file.name} \u2192 {rotated.name}")
            except Exception as e:
                logger.error(f"  Log rotation error: {e}")

            # Sleep until next check
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logger.info("\n\U0001f415 Watchdog interrupted \u2014 shutting down...")
        heartbeat.stop()
        logger.info("\U0001f415 Goodbye.")


if __name__ == "__main__":
    main()
