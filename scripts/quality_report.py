#!/usr/bin/env python3
"""
Quality Metrics Report Generator

This script collects and displays quality metrics for the VJLive3 project,
including test coverage, code quality, security, and dependency health.

Usage:
    python scripts/quality_report.py [options]

Options:
    --output FILE    Save report to file (default: stdout)
    --json          Output in JSON format
    --check         Exit with non-zero if metrics below thresholds
    --thresholds FILE  Load thresholds from JSON file
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vjlive3.utils.quality import QualityMetricsTracker, generate_quality_report


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate quality metrics report for VJLive3"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with non-zero if metrics below thresholds",
    )
    parser.add_argument(
        "--thresholds",
        type=Path,
        help="JSON file with threshold values",
    )
    return parser.parse_args()


def load_thresholds(thresholds_file: Optional[Path]) -> Dict[str, Any]:
    """Load threshold values from file."""
    if not thresholds_file:
        # Default thresholds
        return {
            "test_coverage_min": 80.0,
            "print_statements_max": 0,
            "eval_calls_max": 0,
            "security_high_max": 0,
            "security_medium_max": 0,
            "dependencies_outdated_max": 10,
            "dependencies_vulnerabilities_max": 0,
        }

    try:
        with open(thresholds_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load thresholds: {e}")
        return {}


def check_thresholds(metrics, thresholds: Dict[str, Any]) -> List[str]:
    """Check if metrics meet thresholds."""
    failures = []

    # Test coverage
    if "test_coverage_min" in thresholds:
        if metrics.test_coverage < thresholds["test_coverage_min"]:
            failures.append(
                f"Test coverage {metrics.test_coverage:.1f}% "
                f"below threshold {thresholds['test_coverage_min']}%"
            )

    # Print statements
    if "print_statements_max" in thresholds:
        if metrics.print_statements > thresholds["print_statements_max"]:
            failures.append(
                f"Found {metrics.print_statements} print() statements "
                f"(max allowed: {thresholds['print_statements_max']})"
            )

    # Eval calls
    if "eval_calls_max" in thresholds:
        if metrics.eval_calls > thresholds["eval_calls_max"]:
            failures.append(
                f"Found {metrics.eval_calls} eval() calls "
                f"(max allowed: {thresholds['eval_calls_max']})"
            )

    # Security issues
    if "security_high_max" in thresholds:
        high_issues = metrics.security_issues.get("high", 0)
        if high_issues > thresholds["security_high_max"]:
            failures.append(
                f"Found {high_issues} high severity security issues "
                f"(max allowed: {thresholds['security_high_max']})"
            )

    if "security_medium_max" in thresholds:
        medium_issues = metrics.security_issues.get("medium", 0)
        if medium_issues > thresholds["security_medium_max"]:
            failures.append(
                f"Found {medium_issues} medium severity security issues "
                f"(max allowed: {thresholds['security_medium_max']})"
            )

    # Dependencies
    if "dependencies_outdated_max" in thresholds:
        outdated = metrics.dependencies.get("outdated", 0)
        if outdated > thresholds["dependencies_outdated_max"]:
            failures.append(
                f"Found {outdated} outdated dependencies "
                f"(max allowed: {thresholds['dependencies_outdated_max']})"
            )

    if "dependencies_vulnerabilities_max" in thresholds:
        vulns = metrics.dependencies.get("vulnerabilities", 0)
        if vulns > thresholds["dependencies_vulnerabilities_max"]:
            failures.append(
                f"Found {vulns} vulnerable dependencies "
                f"(max allowed: {thresholds['dependencies_vulnerabilities_max']})"
            )

    return failures


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Collect metrics
    tracker = QualityMetricsTracker(project_root)
    metrics = tracker.collect_metrics()

    # Generate report
    if args.json:
        report = json.dumps(metrics.to_dict(), indent=2)
    else:
        report = generate_quality_report(metrics)

    # Output report
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)

    # Check thresholds if requested
    if args.check:
        thresholds = load_thresholds(args.thresholds)
        failures = check_thresholds(metrics, thresholds)

        if failures:
            print("\n❌ Quality checks failed:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        else:
            print("\n✅ All quality checks passed!")
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())