#!/usr/bin/env python3
"""
Test Coverage Enforcement Hook

Verifies that any code change in src/vjlive3/ has corresponding test coverage
meeting the ≥80% requirement before allowing the commit.

This enforces SAFETY_RAIL 5: Test Coverage Gate.
"""

import sys
import subprocess
from pathlib import Path

def check_coverage_for_changed_files() -> bool:
    """Check if changed files meet coverage requirements."""
    try:
        # Get list of changed Python files
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
            capture_output=True, text=True, check=True
        )
        changed_files = [
            Path(f) for f in result.stdout.splitlines() 
            if f.endswith('.py') and f.startswith('src/vjlive3/')
        ]
        
        if not changed_files:
            print("✅ No source files changed, coverage check skipped")
            return True
        
        # Run pytest with coverage for these specific files
        print(f"Checking coverage for {len(changed_files)} changed files...")
        
        # Build coverage report
        result = subprocess.run(
            ['pytest', '--cov=src/vjlive3', '--cov-report=term-missing', 'tests/'],
            capture_output=True, text=True, timeout=60
        )
        
        # Parse coverage output
        coverage_lines = [l for l in result.stdout.splitlines() if 'TOTAL' in l]
        if not coverage_lines:
            print("❌ Could not parse coverage report")
            return False
        
        # Extract overall coverage percentage
        total_line = coverage_lines[-1]
        # Format: TOTAL  1234  567  54.1%
        parts = total_line.split()
        if len(parts) >= 4:
            coverage_pct = float(parts[-1].rstrip('%'))
            print(f"Current coverage: {coverage_pct:.1f}%")
            
            if coverage_pct < 80.0:
                print(f"❌ Coverage below 80% (current: {coverage_pct:.1f}%)")
                print("Run: pytest --cov=src/vjlive3 --cov-report=html")
                return False
        
        # Check individual file coverage for changed files
        for file_path in changed_files:
            # Convert to module path
            module_path = str(file_path).replace('/', '.').replace('.py', '')
            if module_path.startswith('src.'):
                module_path = module_path[4:]
            
            # Look for this file in coverage report
            file_coverage = None
            for line in result.stdout.splitlines():
                if module_path in line and '%' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            file_coverage = float(parts[-1].rstrip('%'))
                        except ValueError:
                            continue
            
            if file_coverage is not None and file_coverage < 80.0:
                print(f"❌ {file_path}: coverage {file_coverage:.1f}% < 80%")
                return False
        
        print("✅ Coverage requirements met (≥80%)")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Coverage check timed out")
        return False
    except Exception as e:
        print(f"❌ Coverage check error: {e}")
        return False

def main() -> int:
    """Main entry point."""
    print("="*60)
    print("Test Coverage Enforcement")
    print("="*60)
    
    if check_coverage_for_changed_files():
        return 0
    else:
        print("\n" + "="*60)
        print("❌ COVERAGE GATE FAILED")
        print("="*60)
        print("\nAll code changes must maintain ≥80% test coverage.")
        print("Add tests for your changes before committing.")
        print("Use: pytest --cov=src/vjlive3 --cov-report=html")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())