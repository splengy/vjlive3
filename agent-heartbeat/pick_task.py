#!/usr/bin/env python3
"""
Second Pass Task Picker — Node 5 in the pipeline.

Finds specs that are ready for code generation, acquires switchboard locks,
and outputs the next task for a Roo agent to work on.

Usage:
    python3 pick_task.py julie-roo    # Pick next task for Julie-Roo
    python3 pick_task.py maxx-roo     # Pick next task for Maxx-Roo
    python3 pick_task.py --status     # Show pipeline status

This script is meant to be called by Roo agents on the OPis.
It outputs the task details to stdout for Roo to consume.
"""

import argparse
import fcntl
import json
import logging
import os
import sys
from pathlib import Path

# Add agent-heartbeat to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec_gate import check_spec, scan_all_specs

# Resolve project root from script location (works on desktop AND OPis via SSHFS)
PROJECT = str(Path(os.path.dirname(os.path.abspath(__file__))).parent)
SPECS_DIR = os.path.join(PROJECT, "docs", "specs")
SRC_DIR = os.path.join(PROJECT, "src", "vjlive3", "plugins")
TESTS_DIR = os.path.join(PROJECT, "tests")
LOCK_FILE = os.path.join(PROJECT, "agent-heartbeat", "locks.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_locks() -> dict:
    """Load current task locks."""
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, "r") as f:
            return json.load(f)
    return {}


def save_locks(locks: dict):
    """Save task locks."""
    with open(LOCK_FILE, "w") as f:
        json.dump(locks, f, indent=2)


def acquire_lock(task_id: str, agent_id: str) -> bool:
    """Try to lock a task for an agent. Uses fcntl.flock for atomicity."""
    import time
    os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
    with open(LOCK_FILE, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # Block until we get exclusive lock
        try:
            f.seek(0)
            content = f.read()
            locks = json.loads(content) if content.strip() else {}

            if task_id in locks:
                lock = locks[task_id]
                if time.time() - lock.get("timestamp", 0) > 1800:
                    logger.info(f"Lock expired for {task_id}, taking over")
                else:
                    logger.info(f"Task {task_id} locked by {lock['agent']}")
                    return False

            locks[task_id] = {
                "agent": agent_id,
                "timestamp": time.time(),
            }
            f.seek(0)
            f.truncate()
            json.dump(locks, f, indent=2)
            return True
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def release_lock(task_id: str, agent_id: str):
    """Release a task lock. Uses fcntl.flock for atomicity."""
    if not os.path.exists(LOCK_FILE):
        return
    with open(LOCK_FILE, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            locks = json.loads(f.read() or "{}")
            if task_id in locks and locks[task_id]["agent"] == agent_id:
                del locks[task_id]
                f.seek(0)
                f.truncate()
                json.dump(locks, f, indent=2)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def has_implementation(task_id: str, spec_content: str) -> bool:
    """Check if a task already has a code implementation."""
    import re
    # Extract module name from spec
    module_match = re.search(r"##\s*Task:.*?—\s*(\w+)", spec_content)
    if module_match:
        module_name = module_match.group(1)
        impl_path = os.path.join(SRC_DIR, f"{module_name}.py")
        if os.path.exists(impl_path):
            return True

    # Also check by task ID pattern in src/
    for f in Path(SRC_DIR).glob("*.py"):
        if task_id.lower().replace("-", "_") in f.stem.lower():
            return True

    return False


def pick_next_task(agent_id: str) -> dict | None:
    """
    Find the next spec that hasn't been enriched yet.
    Every spec gets the second pass — no filtering.
    """
    results = scan_all_specs()

    for result in results:
        task_id = result["task_id"]

        # Skip if already enriched
        if result.get("pass_status") == "enriched":
            continue

        # Try to acquire lock
        if not acquire_lock(task_id, agent_id):
            continue

        # Read the spec
        with open(result["spec_path"], "r") as f:
            spec_content = f.read()

        return {
            "task_id": task_id,
            "spec_path": result["spec_path"],
            "spec_content": spec_content,
            "agent": agent_id,
        }

    return None


def pipeline_status():
    """Show the full pipeline status."""
    all_specs = scan_all_specs()

    total = len(all_specs)
    ready = sum(1 for r in all_specs if r["status"] == "ready")
    review = sum(1 for r in all_specs if r["status"] == "needs_review")
    incomplete = sum(1 for r in all_specs if r["status"] == "incomplete")
    has_code = sum(1 for r in all_specs if r["has_code"])
    ready_no_code = sum(1 for r in all_specs if r["status"] == "ready" and not r["has_code"])

    locks = load_locks()
    locked = len(locks)

    print(f"""
╔══════════════════════════════════════════════╗
║         VJLive3 Pipeline Status              ║
╠══════════════════════════════════════════════╣
║  Specs generated:     {total:>4}                   ║
║  ✅ Ready for code:   {ready:>4}                   ║
║  ⚠️  Needs review:     {review:>4}                   ║
║  ❌ Incomplete:        {incomplete:>4}                   ║
║  🔧 Already has code:  {has_code:>4}                   ║
║  🎯 Available to work: {ready_no_code:>4}                   ║
║  🔒 Currently locked:  {locked:>4}                   ║
╚══════════════════════════════════════════════╝
""")

    if locks:
        print("Active locks:")
        import time
        for task_id, lock in locks.items():
            age = (time.time() - lock["timestamp"]) / 60
            print(f"  🔒 {task_id}: {lock['agent']} ({age:.0f}m ago)")


def main():
    parser = argparse.ArgumentParser(description="Second Pass Task Picker")
    parser.add_argument("agent_id", nargs="?", help="Agent ID (e.g. julie-roo, maxx-roo)")
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--release", help="Release lock for task ID")
    args = parser.parse_args()

    if args.status:
        pipeline_status()
        return

    if args.release and args.agent_id:
        release_lock(args.release, args.agent_id)
        print(f"Released lock for {args.release}")
        return

    if not args.agent_id:
        print("Usage: python3 pick_task.py <agent-id>")
        print("       python3 pick_task.py --status")
        sys.exit(1)

    task = pick_next_task(args.agent_id)
    if task:
        print(f"TASK_ID={task['task_id']}")
        print(f"SPEC_PATH={task['spec_path']}")
        print(f"AGENT={task['agent']}")
        print(f"---SPEC---")
        print(task["spec_content"])
    else:
        print("NO_TASKS_AVAILABLE")
        sys.exit(1)


if __name__ == "__main__":
    main()
