#!/usr/bin/env python3
"""
Sanity Check Automation

Runs automated quality checkpoints for autonomous agents.
Triggers review if sanity checks fail.
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, Tuple

def run_sanity_checks() -> Tuple[bool, Dict[str, bool]]:
    """Run all sanity checks and return overall status."""
    
    results = {}
    all_passed = True
    
    print("=" * 60)
    print("Running Sanity Checks")
    print("=" * 60)
    print()
    
    # 1. Performance Sanity Check
    print("1. Performance Sanity Check")
    try:
        result = subprocess.run(
            ['python3', 'scripts/check_performance_regression.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        passed = result.returncode == 0
        results['Performance Sanity'] = passed
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}")
        if not passed:
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
        all_passed = all_passed and passed
    except Exception as e:
        results['Performance Sanity'] = False
        all_passed = False
        print(f"   ❌ FAIL - Exception: {e}")
    print()
    
    # 2. Test Coverage Check
    print("2. Test Coverage Check")
    try:
        result = subprocess.run(
            ['python3', 'scripts/verify_test_coverage.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        passed = result.returncode == 0
        results['Test Coverage'] = passed
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}")
        if not passed:
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
        all_passed = all_passed and passed
    except Exception as e:
        results['Test Coverage'] = False
        all_passed = False
        print(f"   ❌ FAIL - Exception: {e}")
    print()
    
    # 3. Code Quality Check (pre-commit)
    print("3. Code Quality Check")
    try:
        result = subprocess.run(
            ['python3', '-m', 'pre_commit', 'run', '--all-files'],
            capture_output=True,
            text=True,
            timeout=120
        )
        passed = result.returncode == 0
        results['Code Quality'] = passed
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}")
        if not passed:
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
        all_passed = all_passed and passed
    except Exception as e:
        results['Code Quality'] = False
        all_passed = False
        print(f"   ❌ FAIL - Exception: {e}")
    print()
    
    # 4. Security Scan
    print("4. Security Scan")
    try:
        result = subprocess.run(
            ['python3', 'scripts/security_scan.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        passed = result.returncode == 0
        results['Security Scan'] = passed
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}")
        if not passed:
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
        all_passed = all_passed and passed
    except Exception as e:
        results['Security Scan'] = False
        all_passed = False
        print(f"   ❌ FAIL - Exception: {e}")
    print()
    
    # 5. Integration Test
    print("5. Integration Test")
    try:
        result = subprocess.run(
            ['python3', '-m', 'pytest', 'tests/unit/', '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=120
        )
        passed = result.returncode == 0
        results['Integration Test'] = passed
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}")
        if not passed:
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
        all_passed = all_passed and passed
    except Exception as e:
        results['Integration Test'] = False
        all_passed = False
        print(f"   ❌ FAIL - Exception: {e}")
    print()
    
    # Summary
    print("=" * 60)
    print("Sanity Check Summary")
    print("=" * 60)
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check}: {status}")
    print()
    
    if all_passed:
        print("✅ All sanity checks passed")
    else:
        print("❌ Some sanity checks failed - review required")
    print()
    
    return all_passed, results

def main():
    """Main entry point."""
    passed, results = run_sanity_checks()
    
    if not passed:
        print("=" * 60)
        print("REVIEW REQUIRED")
        print("=" * 60)
        print("Sanity checks failed. This phase requires manual review.")
        print("Please address the failing checks before proceeding.")
        print()
        print("Next steps:")
        print("1. Review the failed check outputs above")
        print("2. Fix identified issues")
        print("3. Re-run sanity checks")
        print("4. Update task_completion.md with results")
        sys.exit(1)
    else:
        print("=" * 60)
        print("AUTONOMOUS OPERATION CONTINUES")
        print("=" * 60)
        print("All sanity checks passed. Agent can continue autonomously.")
        sys.exit(0)

if __name__ == "__main__":
    sys.exit(main())