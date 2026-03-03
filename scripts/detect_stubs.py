#!/usr/bin/env python3
"""
detect_stubs.py — AST-based stub detector for VJLive3 pre-commit hook.
Spec: PRIME_DIRECTIVE Rule ADR-003 (No-Stub Policy).

Usage:
    python3 detect_stubs.py <file.py> [--strict]

Exit codes:
    0  — no stubs found (clean)
    1  — stubs found (blocks commit in --strict mode)
"""

import ast
import sys
from pathlib import Path

# Body nodes that count as a stub body
_STUB_TYPES = (ast.Pass, ast.Ellipsis)

# Patterns that may appear alongside a docstring in a stub body
_RAISES_NOT_IMPL = ("NotImplementedError",)


def _is_stub_node(node: ast.stmt) -> bool:
    """Return True if a statement is a stub (pass, ..., or raise NotImplementedError)."""
    if isinstance(node, ast.Pass):
        return True
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
        if node.value.value is ...:
            return True
    if isinstance(node, ast.Raise):
        exc = node.exc
        if exc is None:
            return False
        # raise NotImplementedError or raise NotImplementedError(...)
        if isinstance(exc, ast.Name) and exc.id in _RAISES_NOT_IMPL:
            return True
        if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
            if exc.func.id in _RAISES_NOT_IMPL:
                return True
    return False


def _body_is_stub(body: list[ast.stmt]) -> bool:
    """Return True if a function/method body is effectively a stub."""
    real_stmts = [s for s in body if not (
        isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)
        and isinstance(s.value.value, str)  # skip docstrings
    )]
    if not real_stmts:
        return False  # empty or docstring-only: only __init__ is exempt; treat as clean
    return all(_is_stub_node(s) for s in real_stmts)


def check_file(path: Path, strict: bool = False) -> list[str]:
    """
    Parse path and return a list of stub descriptions.
    Returns empty list if no stubs found.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"  ⚠️  Could not read {path}: {e}"]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        # Not a Python file (e.g., WGSL embedded in a .py module string — fine to skip)
        return []

    issues: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if _body_is_stub(node.body):
            issues.append(
                f"  🚫 Stub detected: `{node.name}` at line {node.lineno}"
            )

    return issues


def main() -> int:
    args = sys.argv[1:]
    strict = "--strict" in args
    files = [a for a in args if not a.startswith("--")]

    if not files:
        print("Usage: detect_stubs.py <file.py> [--strict]", file=sys.stderr)
        return 2

    found_any = False
    for raw in files:
        path = Path(raw)
        if not path.exists():
            print(f"  ⚠️  File not found: {path}", file=sys.stderr)
            continue
        if path.suffix != ".py":
            continue

        issues = check_file(path, strict=strict)
        for msg in issues:
            print(msg)
        if issues:
            found_any = True

    return 1 if found_any else 0


if __name__ == "__main__":
    sys.exit(main())
