#!/usr/bin/env python3
"""
Board Task Extractor — Parse BOARD.md for pending tasks.

Usage:
    python scripts/extract_tasks.py                    # all pending tasks
    python scripts/extract_tasks.py --phase P1         # Phase 1 only
    python scripts/extract_tasks.py --status todo      # only todos
    python scripts/extract_tasks.py --has-spec          # only tasks with specs
    python scripts/extract_tasks.py --no-spec           # tasks needing specs

Outputs task IDs, names, and status from BOARD.md.
"""

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

BOARD_PATH = Path(__file__).parent.parent / "BOARD.md"
SPECS_DIR = Path(__file__).parent.parent / "docs" / "specs"


@dataclass
class Task:
    task_id: str
    name: str
    status: str  # "todo", "in_progress", "done", "blocked"
    phase: str
    has_spec: bool = False
    line_number: int = 0


def parse_board(board_path: str = None) -> List[Task]:
    """Parse BOARD.md and extract tasks."""
    path = Path(board_path) if board_path else BOARD_PATH
    if not path.exists():
        print(f"ERROR: BOARD.md not found at {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    tasks = []
    current_phase = ""

    # Patterns for task lines
    # Common formats:
    # - [ ] P1-R3: Video Source Abstraction
    # - [x] P1-R1: Plugin System
    # | P3-EXT031 | ConsciousnessLevel | Todo |
    task_checkbox = re.compile(
        r"^\s*-\s*\[([ xX/])\]\s*(P\d+-\w+[\d]*)\s*[:\-–]\s*(.+)"
    )
    task_table = re.compile(
        r"\|\s*(P\d+-\w+[\d]*)\s*\|\s*([^|]+)\|\s*([^|]+)"
    )
    phase_header = re.compile(r"^#{1,3}\s*(Phase\s*\d+|P\d+)", re.IGNORECASE)

    for i, line in enumerate(lines, 1):
        # Track current phase
        phase_match = phase_header.match(line)
        if phase_match:
            current_phase = phase_match.group(1).strip()

        # Checkbox format
        cb_match = task_checkbox.match(line)
        if cb_match:
            check, task_id, name = cb_match.groups()
            status_map = {" ": "todo", "x": "done", "X": "done", "/": "in_progress"}
            status = status_map.get(check, "todo")

            # Extract phase from task ID
            phase = re.match(r"(P\d+)", task_id)
            phase_str = phase.group(1) if phase else current_phase

            tasks.append(Task(
                task_id=task_id.strip(),
                name=name.strip(),
                status=status,
                phase=phase_str,
                line_number=i,
            ))

        # Table format
        tb_match = task_table.match(line)
        if tb_match:
            task_id, name, status_text = tb_match.groups()
            status_text = status_text.strip().lower()

            if "done" in status_text or "complete" in status_text or "✅" in status_text:
                status = "done"
            elif "progress" in status_text or "wip" in status_text or "🔄" in status_text:
                status = "in_progress"
            elif "block" in status_text or "🚫" in status_text:
                status = "blocked"
            else:
                status = "todo"

            phase = re.match(r"(P\d+)", task_id)
            phase_str = phase.group(1) if phase else current_phase

            tasks.append(Task(
                task_id=task_id.strip(),
                name=name.strip(),
                status=status,
                phase=phase_str,
                line_number=i,
            ))

    # Check which tasks have specs
    if SPECS_DIR.exists():
        spec_files = {f.stem for f in SPECS_DIR.glob("*.md") if not f.name.startswith("_")}
        for task in tasks:
            task.has_spec = any(task.task_id in sf for sf in spec_files)

    return tasks


def main():
    parser = argparse.ArgumentParser(description="Extract tasks from BOARD.md")
    parser.add_argument("--board", help="Path to BOARD.md", default=None)
    parser.add_argument("--phase", "-p", help="Filter by phase (e.g., P1, P3)")
    parser.add_argument("--status", "-s",
                        choices=["todo", "in_progress", "done", "blocked"],
                        help="Filter by status")
    parser.add_argument("--has-spec", action="store_true", help="Only tasks with specs")
    parser.add_argument("--no-spec", action="store_true", help="Only tasks needing specs")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--ids-only", action="store_true", help="Output only task IDs")
    parser.add_argument("--count", action="store_true", help="Show counts only")
    args = parser.parse_args()

    tasks = parse_board(args.board)

    # Apply filters
    if args.phase:
        tasks = [t for t in tasks if t.phase.upper().startswith(args.phase.upper())]
    if args.status:
        tasks = [t for t in tasks if t.status == args.status]
    if args.has_spec:
        tasks = [t for t in tasks if t.has_spec]
    if args.no_spec:
        tasks = [t for t in tasks if not t.has_spec]

    if args.count:
        by_status = {}
        for t in tasks:
            by_status[t.status] = by_status.get(t.status, 0) + 1
        print(f"Total: {len(tasks)}")
        for s, c in sorted(by_status.items()):
            print(f"  {s}: {c}")
        sys.exit(0)

    if args.ids_only:
        for t in tasks:
            print(t.task_id)
        sys.exit(0)

    if args.json:
        import json
        print(json.dumps([{
            "id": t.task_id,
            "name": t.name,
            "status": t.status,
            "phase": t.phase,
            "has_spec": t.has_spec,
            "line": t.line_number,
        } for t in tasks], indent=2))
    else:
        status_icons = {
            "todo": "⬜", "in_progress": "🔄",
            "done": "✅", "blocked": "🚫"
        }
        spec_icon = lambda t: "📄" if t.has_spec else "  "

        current_phase = ""
        for t in tasks:
            if t.phase != current_phase:
                current_phase = t.phase
                print(f"\n{'='*50}")
                print(f"  {current_phase}")
                print(f"{'='*50}")

            icon = status_icons.get(t.status, "?")
            print(f"  {icon} {spec_icon(t)} {t.task_id}: {t.name}")

        print(f"\nTotal: {len(tasks)} tasks")


if __name__ == "__main__":
    main()
