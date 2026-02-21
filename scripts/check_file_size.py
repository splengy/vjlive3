#!/usr/bin/env python3
"""
check_file_size.py — VJLive3 750-Line Limit Enforcer

Counts non-blank, non-comment lines in Python files.
Fails if any file exceeds 750 lines.

Exit code 0: all files within limit
Exit code 1: violations found
"""
from __future__ import annotations

import sys
from pathlib import Path


_WARN_THRESHOLD = 700
_HARD_LIMIT = 750


def count_code_lines(path: Path) -> int:
    """Count non-blank, non-comment lines in a Python file."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0

    count = 0
    in_multiline_string = False
    for line in lines:
        stripped = line.strip()
        # Crude multiline string tracking — good enough for the limit check
        if '"""' in stripped or "'''" in stripped:
            in_multiline_string = not in_multiline_string
        if in_multiline_string:
            continue
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        count += 1
    return count


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: check_file_size.py <file_or_dir> [...]")
        return 2

    warnings: list[tuple[str, int]] = []
    violations: list[tuple[str, int]] = []

    for arg in sys.argv[1:]:
        target = Path(arg)
        files = list(target.rglob("*.py")) if target.is_dir() else [target]
        for f in files:
            count = count_code_lines(f)
            if count > _HARD_LIMIT:
                violations.append((str(f), count))
            elif count > _WARN_THRESHOLD:
                warnings.append((str(f), count))

    if warnings:
        print("\n⚠️  FILE SIZE WARNINGS (approaching 750-line limit)\n")
        for filepath, count in warnings:
            print(f"  {filepath}  →  {count} lines (limit: {_HARD_LIMIT})")
        print("  Plan refactoring now before the hard limit is hit.\n")

    if violations:
        print("\n🚫 FILE SIZE VIOLATIONS — HARD LIMIT EXCEEDED\n")
        for filepath, count in violations:
            over = count - _HARD_LIMIT
            print(f"  {filepath}  →  {count} lines ({over} over limit)")
        print(
            f"\n{len(violations)} file(s) exceed {_HARD_LIMIT} lines. "
            "Split into smaller modules. See WORKSPACE/PRIME_DIRECTIVE.md Rule 5.\n"
        )
        return 1

    if not warnings:
        print(f"✅ File size check passed — all files within {_HARD_LIMIT}-line limit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
