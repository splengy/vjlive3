#!/usr/bin/env python3
"""
check_stubs.py — VJLive3 No-Stub Policy Enforcer

Scans Python source files for stub patterns using AST analysis.
Used as a pre-commit hook and by `make quality`.

Exit code 0: clean
Exit code 1: stubs found (with file:line report)

Allowed exceptions:
  - @pytest.mark.skip decorated test functions with only `pass`
  - Abstract methods decorated with @abstractmethod
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path


# Stub patterns we reject
_STUB_PATTERNS = {
    "bare_pass": "Function body is only `pass` (without @skip or @abstractmethod)",
    "not_implemented": "raise NotImplementedError — use Logger.termination() instead",
    "empty_except": "Bare `except: pass` — silent failure is forbidden",
    "ellipsis_body": "Function body is only `...` — use Logger.termination() instead",
}


def _has_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
    """Check if a function has a specific decorator by name."""
    for d in node.decorator_list:
        if isinstance(d, ast.Name) and d.id == name:
            return True
        if isinstance(d, ast.Attribute) and d.attr == name:
            return True
        if isinstance(d, ast.Call):
            if isinstance(d.func, ast.Name) and d.func.id == name:
                return True
            if isinstance(d.func, ast.Attribute) and d.func.attr == name:
                return True
    return False


def _is_skipped_or_abstract(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Return True if function is @abstractmethod or @pytest.mark.skip."""
    return (
        _has_decorator(node, "abstractmethod")
        or _has_decorator(node, "skip")
        or _has_decorator(node, "overload")
    )


def _body_is_only(node: ast.FunctionDef | ast.AsyncFunctionDef, stmt_type: type) -> bool:
    """Return True if function body (excluding docstring) is only one stmt_type."""
    body = node.body
    # Strip leading docstring
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    return len(body) == 1 and isinstance(body[0], stmt_type)


def _body_is_ellipsis(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if function body is only `...`."""
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    if len(body) != 1:
        return False
    stmt = body[0]
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and stmt.value.value is ...
    )


def _raises_not_implemented(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if function raises NotImplementedError anywhere."""
    for child in ast.walk(node):
        if isinstance(child, ast.Raise):
            if child.exc is not None:
                exc = child.exc
                if isinstance(exc, ast.Call):
                    exc = exc.func
                if isinstance(exc, ast.Name) and exc.id == "NotImplementedError":
                    return True
    return False


class _StubVisitor(ast.NodeVisitor):
    """AST visitor that collects stub violations."""

    def __init__(self, filepath: str, is_test_file: bool) -> None:
        self.filepath = filepath
        self.is_test_file = is_test_file
        self.violations: list[tuple[int, str]] = []

    def _check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        if _is_skipped_or_abstract(node):
            # Allowed: abstract or explicitly skipped
            self.generic_visit(node)
            return

        # Check bare pass
        if _body_is_only(node, ast.Pass):
            if not (self.is_test_file and _has_decorator(node, "skip")):
                self.violations.append(
                    (node.lineno, f"{_STUB_PATTERNS['bare_pass']}: {node.name}()")
                )

        # Check ellipsis body
        if _body_is_ellipsis(node):
            self.violations.append(
                (node.lineno, f"{_STUB_PATTERNS['ellipsis_body']}: {node.name}()")
            )

        # Check NotImplementedError
        if _raises_not_implemented(node):
            self.violations.append(
                (node.lineno, f"{_STUB_PATTERNS['not_implemented']}: {node.name}()")
            )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Check for bare except: pass."""
        if node.type is None:  # bare except
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                self.violations.append(
                    (node.lineno, _STUB_PATTERNS["empty_except"])
                )
        self.generic_visit(node)


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Scan a single Python file. Returns list of (line, description) violations."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        return [(e.lineno or 0, f"SyntaxError: {e.msg}")]

    is_test = "test" in path.name.lower() or "tests" in str(path).lower()
    visitor = _StubVisitor(str(path), is_test_file=is_test)
    visitor.visit(tree)
    return visitor.violations


def main() -> int:
    """Entry point. Accepts file paths as arguments."""
    if len(sys.argv) < 2:
        print("Usage: check_stubs.py <file_or_dir> [...]")
        return 2

    all_violations: list[tuple[str, int, str]] = []

    for arg in sys.argv[1:]:
        target = Path(arg)
        if target.is_dir():
            files = list(target.rglob("*.py"))
        elif target.suffix == ".py":
            files = [target]
        else:
            continue

        for f in files:
            violations = scan_file(f)
            for line, desc in violations:
                all_violations.append((str(f), line, desc))

    if all_violations:
        print("\n🚫 STUB POLICY VIOLATIONS FOUND\n")
        for filepath, line, desc in all_violations:
            print(f"  {filepath}:{line}  →  {desc}")
        print(
            f"\n{len(all_violations)} violation(s). "
            "Use Logger.termination() for known dead-ends.\n"
            "See /.agent/workflows/no-stub-policy.md\n"
        )
        return 1

    print("✅ Stub check passed — zero violations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
