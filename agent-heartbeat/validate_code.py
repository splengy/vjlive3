#!/usr/bin/env python3
"""
VJLive3 — Worker Code Validator

Agents MUST run this script before calling complete_task.
Usage: python3 agent-heartbeat/validate_code.py MODULE_NAME

Steps:
1. Syntax check (py_compile)
2. No-Stub Policy check
3. Pytest Execution
4. 80% Coverage Enforcement
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add local path for stub_detector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stub_detector import scan as scan_stubs

def run_validation(module_name: str) -> bool:
    project_root = Path(__file__).resolve().parent.parent
    src_file = project_root / "src" / "vjlive3" / "plugins" / f"{module_name}.py"
    test_file = project_root / "tests" / f"test_{module_name}.py"
    
    print(f"🔍 Validating module: {module_name}")
    print(f"   Source: {src_file.relative_to(project_root)}")
    print(f"   Tests:  {test_file.relative_to(project_root)}\n")

    # 1. Check existence
    if not src_file.exists():
        print(f"❌ FAIL: Source file not found at {src_file}")
        return False
    if not test_file.exists():
        print(f"❌ FAIL: Test file not found at {test_file}")
        return False

    # 2. Syntax Check
    print("⏳ Step 1: Syntax Check...")
    try:
        import py_compile
        py_compile.compile(str(src_file), doraise=True)
        py_compile.compile(str(test_file), doraise=True)
        print("✅ PASS: Syntax OK")
    except py_compile.PyCompileError as e:
        print(f"❌ FAIL: Syntax Error\n{e}")
        return False

    # 3. Stub Check (No-Stub Policy)
    print("\n⏳ Step 2: Stub Detection...")
    with open(src_file) as f:
        code = f.read()
    stub_result = scan_stubs(code)
    if not stub_result.passed:
        print("❌ FAIL: Stub code detected. You MUST implement the full logic.")
        for _, _, msg in stub_result.flagged_lines:
            print(f"   - {msg}")
        return False
    print("✅ PASS: No stubs detected")

    # 4. Pytest & Coverage
    print("\n⏳ Step 3: Pytest & Coverage...")
    os.chdir(project_root)
    cmd = [
        "python3", "-m", "pytest",
        str(test_file),
        f"--cov=src/vjlive3/plugins/{module_name}.py",
        "--cov-report=term-missing",
        "--cov-fail-under=80"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ FAIL: Tests failed or coverage < 80%. Here is the output:\n")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return False

    print("✅ PASS: Pytest successful (≥80% coverage)")
    print("\n🎉 ALL CHECKS PASSED!")
    print(f"You may now move the spec to the fleshed_out folder.")
    print("======================\n")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate a generated module")
    parser.add_argument("module_name", help="Name of the module (e.g., ascii_effect)")
    args = parser.parse_args()
    
    success = run_validation(args.module_name)
    sys.exit(0 if success else 1)
