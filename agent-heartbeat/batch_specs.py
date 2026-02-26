#!/usr/bin/env python3
"""
Dual-board Batch Spec Generator

Dispatches spec generation tasks to Julie (.60) and Maxx (.50) in parallel,
using two threads — one per board. Each board processes its tasks sequentially
through the heartbeat pipeline.

Usage:
    python3 batch_specs.py                # Run all RESET tasks
    python3 batch_specs.py --limit 10     # Test with first 10 tasks
    python3 batch_specs.py --dry-run      # Show what would run
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from queue import Queue

PROJECT = str(Path(os.path.dirname(os.path.abspath(__file__))).parent)
HEARTBEAT = os.path.join(PROJECT, "agent-heartbeat", "heartbeat.py")
BOARD_FILE = os.path.join(PROJECT, "BOARD.md")
SPECS_DIR = os.path.join(PROJECT, "docs", "specs")
LOG_DIR = os.path.join(PROJECT, "agent-heartbeat", "logs")

# Board configs — override julie_host in heartbeat config per-worker
BOARDS = {
    "julie": {"host": "192.168.1.60", "port": 5050},
    "maxx":  {"host": "192.168.1.50", "port": 5050},
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(threadName)-8s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "batch_specs.log"), mode="a"),
    ],
)
logger = logging.getLogger(__name__)


def parse_board_tasks(board_path: str, limit: int = 0) -> list:
    """Extract ALL RESET tasks from BOARD.md — any task ID, any format."""
    tasks = []
    # Pattern 1: | TASK-ID | module (ClassName) | ... ⬜ RESET
    pat_with_class = re.compile(
        r"\|\s*([A-Z0-9][\w-]+)\s*\|\s*(.+?)\s+\(([^)]+)\)\s*\|.*?⬜\s*RESET"
    )
    # Pattern 2: | TASK-ID | plain description | ... ⬜ RESET (no parens)
    pat_plain = re.compile(
        r"\|\s*([A-Z0-9][\w-]+)\s*\|\s*(.+?)\s*\|.*?⬜\s*RESET"
    )
    skipped_existing = 0
    skipped_dupe = 0
    with open(board_path, "r") as f:
        for line in f:
            if "⬜ RESET" not in line:
                continue
            # Skip duplicates marked in BOARD.md
            if "duplicate" in line.lower():
                skipped_dupe += 1
                continue

            # Try pattern with class name first
            m = pat_with_class.search(line)
            if m:
                task_id = m.group(1)
                module_name = m.group(2).strip()
                class_name = m.group(3)
                description = f"{module_name} ({class_name}) - Port from VJlive legacy to VJLive3"
            else:
                # Fall back to plain description
                m = pat_plain.search(line)
                if m:
                    task_id = m.group(1)
                    description = m.group(2).strip()
                    module_name = description
                    class_name = ""
                else:
                    continue

            # Skip already-generated specs (resume capability)
            spec_path = os.path.join(SPECS_DIR, f"{task_id}_spec.md")
            if os.path.exists(spec_path):
                skipped_existing += 1
                continue

            tasks.append({
                "task_id": task_id,
                "module": module_name,
                "class": class_name,
                "description": description,
                "output": f"docs/specs/{task_id}_spec.md",
            })
    logger.info(f"📊 Parsed: {len(tasks)} to run, {skipped_existing} already done, {skipped_dupe} duplicates skipped")
    if limit > 0:
        tasks = tasks[:limit]
    return tasks


def worker(board_name: str, task_queue: Queue, results: list, lock: threading.Lock):
    """
    Worker thread — pulls tasks from the shared queue and runs heartbeat
    with the board's host as the julie_host override.
    """
    board = BOARDS[board_name]
    host = board["host"]
    completed = 0
    failed = 0

    while not task_queue.empty():
        try:
            task = task_queue.get_nowait()
        except Exception:
            break

        task_id = task["task_id"]
        logger.info(f"🍽️  {task_id}: {task['description'][:60]}...")

        start = time.time()
        try:
            # Run heartbeat with JULIE_HOST env var override
            env = os.environ.copy()
            env["JULIE_HOST"] = host
            env["JULIE_PORT"] = str(board["port"])
            env["BOARD_NAME"] = board_name

            result = subprocess.run(
                [sys.executable, HEARTBEAT, task_id, task["description"], task["output"]],
                capture_output=True,
                text=True,
                timeout=700,  # 11+ minutes max
                cwd=PROJECT,
                env=env,
            )
            elapsed = time.time() - start
            success = result.returncode == 0

            if success:
                completed += 1
                logger.info(f"✅ {task_id}: {elapsed:.0f}s")
            else:
                failed += 1
                # Get last meaningful log line
                output = (result.stdout + result.stderr).strip()
                last_line = output.split("\n")[-1] if output else "no output"
                logger.warning(f"❌ {task_id}: {elapsed:.0f}s — {last_line[:100]}")

            with lock:
                results.append({
                    "task_id": task_id,
                    "board": board_name,
                    "success": success,
                    "elapsed": round(elapsed, 1),
                })

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            failed += 1
            logger.error(f"⏰ {task_id}: TIMEOUT after {elapsed:.0f}s")
            with lock:
                results.append({
                    "task_id": task_id,
                    "board": board_name,
                    "success": False,
                    "elapsed": round(elapsed, 1),
                })

        task_queue.task_done()

    logger.info(f"🏁 {board_name} done: {completed} passed, {failed} failed")


def main():
    parser = argparse.ArgumentParser(description="Dual-board batch spec generator")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tasks (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Show tasks without running")
    parser.add_argument("--single", choices=["julie", "maxx"], help="Use only one board")
    args = parser.parse_args()

    # Parse tasks
    tasks = parse_board_tasks(BOARD_FILE, limit=args.limit)
    logger.info(f"📋 Found {len(tasks)} tasks to process")

    if not tasks:
        logger.info("No tasks to process!")
        return

    if args.dry_run:
        for i, t in enumerate(tasks):
            print(f"  {i+1:3d}. {t['task_id']}: {t['description'][:70]}")
        est_min = len(tasks) * 8 / (1 if args.single else 2)
        print(f"\n  Estimated time: {est_min:.0f} minutes ({est_min/60:.1f} hours)")
        return

    # Check board health
    import urllib.request
    boards_to_use = [args.single] if args.single else list(BOARDS.keys())
    healthy_boards = []
    for name in boards_to_use:
        board = BOARDS[name]
        try:
            url = f"http://{board['host']}:{board['port']}/health"
            req = urllib.request.urlopen(url, timeout=5)
            data = json.loads(req.read().decode())
            if data.get("status") == "ok":
                healthy_boards.append(name)
                logger.info(f"✅ {name} ({board['host']}): healthy")
            else:
                logger.warning(f"⚠️  {name}: not ready — {data}")
        except Exception as e:
            logger.warning(f"⚠️  {name} ({board['host']}): unreachable — {e}")

    if not healthy_boards:
        logger.error("❌ No healthy boards! Exiting.")
        sys.exit(1)

    # Fill queue
    task_queue = Queue()
    for t in tasks:
        task_queue.put(t)

    # Launch workers
    results = []
    lock = threading.Lock()
    threads = []
    start_time = time.time()

    for board_name in healthy_boards:
        t = threading.Thread(
            target=worker,
            args=(board_name, task_queue, results, lock),
            name=board_name,
            daemon=True,
        )
        threads.append(t)
        t.start()

    logger.info(f"🚀 Started {len(threads)} worker(s): {', '.join(healthy_boards)}")
    logger.info(f"📊 {len(tasks)} tasks × ~8 min ÷ {len(threads)} boards = ~{len(tasks)*8//len(threads)} min")

    # Wait for completion
    for t in threads:
        t.join()

    total_time = time.time() - start_time
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"BATCH COMPLETE")
    logger.info(f"  Total time: {total_time/60:.1f} minutes")
    logger.info(f"  Tasks: {passed}/{len(results)} passed ({failed} failed)")
    logger.info(f"  Boards: {', '.join(healthy_boards)}")
    logger.info(f"{'='*60}")

    # Save results
    results_file = os.path.join(LOG_DIR, f"batch_results_{time.strftime('%Y%m%d_%H%M%S')}.json")
    with open(results_file, "w") as f:
        json.dump({"results": results, "total_time": total_time, "boards": healthy_boards}, f, indent=2)
    logger.info(f"Results saved to: {results_file}")


if __name__ == "__main__":
    main()
