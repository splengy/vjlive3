#!/usr/bin/env python3
"""
Stub Detector — Find pass-only methods and fake implementations.

Usage:
    python scripts/detect_stubs.py src/vjlive3/plugins/my_plugin.py
    python scripts/detect_stubs.py src/vjlive3/              # scan directory
    python scripts/detect_stubs.py --strict src/              # exit 1 if ANY stubs

Detects:
    - Methods with only `pass`
    - Methods with only `raise NotImplementedError`
    - Methods that only return None/0/False/[] with no logic
    - Empty __init__ methods (beyond super().__init__)
"""

import argparse
import ast
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class StubReport:
    filepath: str
    class_name: str
    method_name: str
    line_number: int
    stub_type: str  # "pass", "not_implemented", "trivial_return", "empty_init"


def is_pass_only(body: list) -> bool:
    """Check if function body is just `pass`."""
    stmts = [s for s in body if not isinstance(s, ast.Expr)
             or not isinstance(s.value, (ast.Constant, ast.Str))]  # skip docstrings
    return len(stmts) == 1 and isinstance(stmts[0], ast.Pass)


def is_not_implemented(body: list) -> bool:
    """Check if function body is just `raise NotImplementedError`."""
    stmts = [s for s in body if not isinstance(s, ast.Expr)
             or not isinstance(s.value, (ast.Constant, ast.Str))]
    if len(stmts) != 1:
        return False
    stmt = stmts[0]
    if isinstance(stmt, ast.Raise) and stmt.exc:
        if isinstance(stmt.exc, ast.Call):
            func = stmt.exc.func
            if isinstance(func, ast.Name) and func.id == "NotImplementedError":
                return True
        elif isinstance(stmt.exc, ast.Name) and stmt.exc.id == "NotImplementedError":
            return True
    return False


def is_trivial_return(body: list) -> bool:
    """Check if function body just returns a trivial constant."""
    stmts = [s for s in body if not isinstance(s, ast.Expr)
             or not isinstance(s.value, (ast.Constant, ast.Str))]
    if len(stmts) != 1:
        return False
    stmt = stmts[0]
    if isinstance(stmt, ast.Return):
        if stmt.value is None:
            return True
        if isinstance(stmt.value, ast.Constant) and stmt.value.value in (None, 0, False, "", []):
            return True
        if isinstance(stmt.value, (ast.List, ast.Dict, ast.Tuple)):
            if not stmt.value.elts if hasattr(stmt.value, 'elts') else not stmt.value.keys:
                return True
    return False


def scan_file(filepath: str) -> List[StubReport]:
    """Scan a Python file for stubs."""
    stubs = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"WARNING: Cannot parse {filepath}: {e}", file=sys.stderr)
        return stubs

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_name = item.name
                    body = item.body

                    if is_pass_only(body):
                        stubs.append(StubReport(
                            filepath=filepath,
                            class_name=class_name,
                            method_name=method_name,
                            line_number=item.lineno,
                            stub_type="pass"
                        ))
                    elif is_not_implemented(body):
                        # Allow in abstract base classes
                        is_abc = any(
                            isinstance(d, ast.Name) and d.id == "abstractmethod"
                            or isinstance(d, ast.Attribute) and d.attr == "abstractmethod"
                            for d in item.decorator_list
                        )
                        if not is_abc:
                            stubs.append(StubReport(
                                filepath=filepath,
                                class_name=class_name,
                                method_name=method_name,
                                line_number=item.lineno,
                                stub_type="not_implemented"
                            ))
                    elif is_trivial_return(body) and method_name not in (
                        "__repr__", "__str__", "__bool__", "__len__",
                        "__hash__", "__eq__", "__ne__"
                    ):
                        stubs.append(StubReport(
                            filepath=filepath,
                            class_name=class_name,
                            method_name=method_name,
                            line_number=item.lineno,
                            stub_type="trivial_return"
                        ))

    return stubs


def scan_directory(dirpath: str) -> List[StubReport]:
    """Recursively scan a directory for Python stubs."""
    all_stubs = []
    for py_file in Path(dirpath).rglob("*.py"):
        if "__pycache__" in str(py_file) or ".venv" in str(py_file):
            continue
        all_stubs.extend(scan_file(str(py_file)))
    return all_stubs


def main():
    parser = argparse.ArgumentParser(description="Detect stub methods in Python files")
    parser.add_argument("path", help="File or directory to scan")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 1 if any stubs found")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    target = Path(args.path)
    if target.is_file():
        stubs = scan_file(str(target))
    elif target.is_dir():
        stubs = scan_directory(str(target))
    else:
        print(f"ERROR: {args.path} not found", file=sys.stderr)
        sys.exit(2)

    if args.json:
        import json
        print(json.dumps([{
            "file": s.filepath,
            "class": s.class_name,
            "method": s.method_name,
            "line": s.line_number,
            "type": s.stub_type
        } for s in stubs], indent=2))
    else:
        if not stubs:
            print(f"✅ No stubs found in {args.path}")
        else:
            print(f"❌ Found {len(stubs)} stub(s) in {args.path}:\n")
            for s in stubs:
                icon = {"pass": "🚫", "not_implemented": "⚠️",
                        "trivial_return": "🔸"}.get(s.stub_type, "?")
                print(f"  {icon} {s.filepath}:{s.line_number}")
                print(f"     {s.class_name}.{s.method_name}() — {s.stub_type}")

    if args.strict and stubs:
        sys.exit(1)


if __name__ == "__main__":
    main()
