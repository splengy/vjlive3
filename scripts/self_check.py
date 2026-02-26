#!/usr/bin/env python3
"""
Agent Self-Check — Run ALL quality checks before submitting code.

Usage:
    python scripts/self_check.py src/vjlive3/core/video_source.py
    python scripts/self_check.py src/vjlive3/core/video_source.py --spec docs/specs/P1-R3_VideoSourceAbstraction.md
    python scripts/self_check.py src/vjlive3/  # scan entire directory

AGENTS: Run this BEFORE submitting code for review.
If this script fails, fix the issues before submitting.
The pre-commit hook will catch anything you miss, but that wastes everyone's time.

Checks run:
    1. Stub detection (no pass-only methods)
    2. File size (no files over 750 lines)
    3. No /tmp/ hardcoded paths
    4. Spec validation (if --spec provided)
    5. Naming consistency (cross-checks against name registry)
    6. Basic syntax check
"""

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
REPO_ROOT = SCRIPTS_DIR.parent


def run_check(name, cmd):
    """Run a check command and return (passed, output)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT)
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Timed out after 30s"
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"


def check_syntax(filepath):
    """Check Python syntax."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source, filename=filepath)
        return True, "Valid syntax"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"


def check_file_size(filepath):
    """Check file is under 750 lines."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = sum(1 for _ in f)
    if lines > 750:
        return False, f"{lines} lines (max 750)"
    return True, f"{lines} lines"


def check_tmp_paths(filepath):
    """Check for hardcoded /tmp/ paths."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f, 1):
            if "/tmp/" in line and not line.strip().startswith("#"):
                return False, f"Line {i}: {line.strip()}"
    return True, "No /tmp/ paths"


def main():
    parser = argparse.ArgumentParser(
        description="Run all quality checks before submitting code"
    )
    parser.add_argument("path", help="Python file or directory to check")
    parser.add_argument("--spec", help="Spec file to validate alongside code")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    target = Path(args.path)
    if target.is_dir():
        files = sorted(target.rglob("*.py"))
        files = [f for f in files if "__pycache__" not in str(f) and ".venv" not in str(f)]
    elif target.is_file():
        files = [target]
    else:
        print(f"ERROR: {args.path} not found")
        sys.exit(2)

    total_checks = 0
    passed_checks = 0
    failed_files = []

    print("🔍 VJLive3 Agent Self-Check")
    print(f"   Target: {args.path}")
    print(f"   Files: {len(files)}")
    print("=" * 50)

    for filepath in files:
        if args.verbose or len(files) <= 5:
            print(f"\n📄 {filepath.name}")

        file_passed = True

        # 1. Syntax check
        total_checks += 1
        ok, msg = check_syntax(str(filepath))
        if ok:
            passed_checks += 1
        else:
            file_passed = False
            print(f"  ❌ Syntax: {msg}")

        # 2. Stub detection
        total_checks += 1
        ok, output = run_check("stubs", [
            sys.executable, str(SCRIPTS_DIR / "detect_stubs.py"),
            str(filepath), "--strict"
        ])
        if ok:
            passed_checks += 1
        else:
            file_passed = False
            # Show stub details
            for line in output.split("\n"):
                if "🚫" in line or "⚠️" in line or "🔸" in line:
                    print(f"  {line.strip()}")

        # 3. File size
        total_checks += 1
        ok, msg = check_file_size(str(filepath))
        if ok:
            passed_checks += 1
        else:
            file_passed = False
            print(f"  ❌ File size: {msg}")

        # 4. /tmp paths
        total_checks += 1
        ok, msg = check_tmp_paths(str(filepath))
        if ok:
            passed_checks += 1
        else:
            file_passed = False
            print(f"  ❌ Hardcoded path: {msg}")

        if file_passed:
            if args.verbose or len(files) <= 5:
                print(f"  ✅ All checks passed")
        else:
            failed_files.append(str(filepath))

    # 5. Spec validation (if provided)
    if args.spec:
        print(f"\n📋 Spec: {args.spec}")
        total_checks += 1
        ok, output = run_check("spec", [
            sys.executable, str(SCRIPTS_DIR / "validate_spec.py"),
            args.spec, "--strict"
        ])
        if ok:
            passed_checks += 1
            print("  ✅ Spec validation passed")
        else:
            print("  ❌ Spec validation failed:")
            for line in output.split("\n"):
                if "🚫" in line or "⚠️" in line:
                    print(f"  {line.strip()}")

    # 6. Naming consistency (if registry exists)
    registry_path = REPO_ROOT / "docs" / "NAME_REGISTRY.json"
    if registry_path.exists():
        print(f"\n📝 Naming consistency")
        total_checks += 1
        ok, output = run_check("naming", [
            sys.executable, str(SCRIPTS_DIR / "check_naming.py"),
            "--src", str(target) if target.is_dir() else str(target.parent),
            "--strict"
        ])
        if ok:
            passed_checks += 1
            print("  ✅ No naming conflicts")
        else:
            print("  ⚠️  Naming issues found:")
            for line in output.split("\n"):
                if "🚫" in line or "🔸" in line:
                    print(f"  {line.strip()}")

    # Summary
    print()
    print("=" * 50)
    if failed_files:
        print(f"❌ FAILED — {passed_checks}/{total_checks} checks passed")
        print(f"   Fix {len(failed_files)} file(s) before submitting:")
        for f in failed_files:
            print(f"   - {f}")
        sys.exit(1)
    else:
        print(f"✅ PASSED — {passed_checks}/{total_checks} checks passed")
        print("   Code is ready for review.")
        sys.exit(0)


if __name__ == "__main__":
    main()
