#!/usr/bin/env python3
"""
Code Validator — Node 7 in the pipeline.

Validates generated code after the second pass (Roo code generation).
Checks syntax, imports, tests, and coverage.

Usage:
    python3 code_validator.py P3-EXT001               # Validate a task
    python3 code_validator.py P3-EXT001 --fix-imports  # Try to fix imports
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT = str(Path(os.path.dirname(os.path.abspath(__file__))).parent)
SRC_DIR = os.path.join(PROJECT, "src", "vjlive3", "plugins")
TESTS_DIR = os.path.join(PROJECT, "tests")
SPECS_DIR = os.path.join(PROJECT, "docs", "specs")
COVERAGE_MIN = 80

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def find_impl_file(task_id: str) -> str | None:
    """Find the implementation file for a task ID."""
    # Read spec to get module name
    spec_path = os.path.join(SPECS_DIR, f"{task_id}_spec.md")
    if os.path.exists(spec_path):
        with open(spec_path, "r") as f:
            content = f.read()
        module_match = re.search(r"##\s*Task:.*?—\s*(\w+)", content)
        if module_match:
            module_name = module_match.group(1)
            impl_path = os.path.join(SRC_DIR, f"{module_name}.py")
            if os.path.exists(impl_path):
                return impl_path

    # Fallback: search by task ID
    task_slug = task_id.lower().replace("-", "_")
    for f in Path(SRC_DIR).glob("*.py"):
        if task_slug in f.stem.lower():
            return str(f)

    return None


def find_test_file(impl_path: str) -> str | None:
    """Find the test file for an implementation."""
    module_name = Path(impl_path).stem
    test_path = os.path.join(TESTS_DIR, f"test_{module_name}.py")
    if os.path.exists(test_path):
        return test_path
    return None


def check_syntax(file_path: str) -> tuple[bool, str]:
    """Check if a Python file has valid syntax."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", file_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return True, "OK"
        return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)


def check_stubs(file_path: str) -> tuple[bool, list]:
    """Check for stub patterns in implementation code."""
    with open(file_path, "r") as f:
        content = f.read()
        lines = content.split("\n")

    stubs = []
    stub_patterns = [
        (r"^\s*pass\s*$", "bare pass"),
        (r"raise NotImplementedError", "NotImplementedError"),
        (r"#\s*TODO", "TODO comment"),
        (r"#\s*FIXME", "FIXME comment"),
        (r"\.\.\.", "ellipsis"),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, name in stub_patterns:
            if re.search(pattern, line):
                # Skip if in docstring or comment-only context
                stripped = line.strip()
                if stripped.startswith("#") and name in ("TODO comment", "FIXME comment"):
                    stubs.append(f"L{i}: {name} — {stripped[:60]}")
                elif name == "bare pass":
                    # Check if it's the only statement in a function body
                    stubs.append(f"L{i}: {name}")
                elif name != "bare pass":
                    stubs.append(f"L{i}: {name} — {stripped[:60]}")

    return len(stubs) == 0, stubs


def run_tests(test_path: str, impl_path: str) -> tuple[bool, int, int, float, str]:
    """
    Run pytest on the test file with coverage.
    Returns: (passed, total_tests, passed_tests, coverage_pct, output)
    """
    module_name = Path(impl_path).stem
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest", test_path,
                f"--cov=src.vjlive3.plugins.{module_name}",
                "--cov-report=term-missing",
                "-v", "--tb=short",
            ],
            capture_output=True, text=True, timeout=120,
            cwd=PROJECT,
        )
        output = result.stdout + result.stderr

        # Parse test results
        test_match = re.search(r"(\d+) passed", output)
        fail_match = re.search(r"(\d+) failed", output)
        passed_count = int(test_match.group(1)) if test_match else 0
        failed_count = int(fail_match.group(1)) if fail_match else 0
        total = passed_count + failed_count

        # Parse coverage
        cov_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        coverage = float(cov_match.group(1)) if cov_match else 0.0

        all_passed = result.returncode == 0
        return all_passed, total, passed_count, coverage, output

    except subprocess.TimeoutExpired:
        return False, 0, 0, 0.0, "TIMEOUT"
    except Exception as e:
        return False, 0, 0, 0.0, str(e)


def validate_task(task_id: str) -> dict:
    """Full validation of a task's code implementation."""
    report = {
        "task_id": task_id,
        "passed": False,
        "checks": {},
    }

    # Find implementation
    impl_path = find_impl_file(task_id)
    if not impl_path:
        report["checks"]["impl_exists"] = {"passed": False, "detail": "No implementation file found"}
        return report
    report["checks"]["impl_exists"] = {"passed": True, "detail": impl_path}

    # Syntax check
    syntax_ok, syntax_msg = check_syntax(impl_path)
    report["checks"]["syntax"] = {"passed": syntax_ok, "detail": syntax_msg}
    if not syntax_ok:
        return report

    # Stub check
    no_stubs, stubs = check_stubs(impl_path)
    report["checks"]["no_stubs"] = {"passed": no_stubs, "detail": stubs if stubs else "Clean"}

    # Find and run tests
    test_path = find_test_file(impl_path)
    if not test_path:
        report["checks"]["tests_exist"] = {"passed": False, "detail": "No test file found"}
        return report
    report["checks"]["tests_exist"] = {"passed": True, "detail": test_path}

    # Syntax check test file too
    test_syntax_ok, test_syntax_msg = check_syntax(test_path)
    report["checks"]["test_syntax"] = {"passed": test_syntax_ok, "detail": test_syntax_msg}
    if not test_syntax_ok:
        return report

    # Run tests with coverage
    tests_passed, total, passed_count, coverage, output = run_tests(test_path, impl_path)
    report["checks"]["tests_pass"] = {
        "passed": tests_passed,
        "detail": f"{passed_count}/{total} tests passed",
    }
    report["checks"]["coverage"] = {
        "passed": coverage >= COVERAGE_MIN,
        "detail": f"{coverage:.0f}% (min {COVERAGE_MIN}%)",
    }

    # Overall verdict
    report["passed"] = all(c["passed"] for c in report["checks"].values())
    return report


def main():
    parser = argparse.ArgumentParser(description="Code Validator")
    parser.add_argument("task_id", help="Task ID to validate")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    report = validate_task(args.task_id)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    # Pretty print
    emoji = "✅" if report["passed"] else "❌"
    print(f"\n{emoji} Validation: {report['task_id']}")
    print(f"{'─' * 50}")

    for check_name, check in report["checks"].items():
        icon = "✅" if check["passed"] else "❌"
        detail = check["detail"]
        if isinstance(detail, list):
            detail = f"{len(detail)} issues"
        print(f"  {icon} {check_name}: {detail}")

    print(f"{'─' * 50}")
    verdict = "SHIP IT 🚀" if report["passed"] else "NEEDS WORK"
    print(f"  Verdict: {verdict}\n")

    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
