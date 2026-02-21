#!/usr/bin/env python3
"""
check_file_lock.py — VJLive3 File Lock Collision Detector

Reads WORKSPACE/COMMS/LOCKS.md and warns if any staged file
is currently locked by another agent.

Non-blocking: exits 0 with a warning message so the commit proceeds
but the agent is informed of the potential collision.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_LOCKS_FILE = Path(__file__).parent.parent / "WORKSPACE" / "COMMS" / "LOCKS.md"
_LOCK_ROW_RE = re.compile(
    r"^\|\s*(?P<path>[^|]+?)\s*\|\s*(?P<agent>[^|]+?)\s*\|"
    r"\s*(?P<checked_out>[^|]+?)\s*\|\s*(?P<eta>[^|]+?)\s*\|"
    r"\s*(?P<status>[^|]+?)\s*\|$"
)


def _get_staged_files() -> list[str]:
    """Return list of staged file paths from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []


def _parse_active_locks() -> list[dict[str, str]]:
    """Parse the Active Locks table from LOCKS.md."""
    if not _LOCKS_FILE.exists():
        return []

    locks: list[dict[str, str]] = []
    in_active = False
    for line in _LOCKS_FILE.read_text(encoding="utf-8").splitlines():
        if "## Active Locks" in line:
            in_active = True
            continue
        if in_active and line.startswith("## "):
            break
        if in_active:
            m = _LOCK_ROW_RE.match(line)
            if m and "no active locks" not in m.group("path").lower():
                locks.append(m.groupdict())
    return locks


def main() -> int:
    staged = _get_staged_files()
    if not staged:
        return 0

    locks = _parse_active_locks()
    if not locks:
        return 0

    conflicts: list[tuple[str, str]] = []
    for lock in locks:
        lock_path = lock["path"].strip()
        lock_agent = lock["agent"].strip()
        for staged_file in staged:
            if lock_path and lock_path in staged_file:
                conflicts.append((staged_file, lock_agent))

    if conflicts:
        print("\n⚠️  FILE LOCK COLLISION DETECTED\n")
        for filepath, agent in conflicts:
            print(f"  {filepath}  →  locked by: {agent}")
        print(
            "\n  Check WORKSPACE/COMMS/LOCKS.md before committing.\n"
            "  Coordinate via WORKSPACE/COMMS/AGENT_SYNC.md.\n"
            "  (This warning is non-blocking — your commit will proceed.)\n"
        )

    # Non-blocking — always exit 0. The warning is informational.
    return 0


if __name__ == "__main__":
    sys.exit(main())
