"""Quality metrics tracking for VJLive3.

This module provides tools for tracking and monitoring code quality metrics,
including test coverage, code complexity, and security vulnerabilities.

Metrics tracked:
- Test coverage percentage
- Number of print() statements
- Number of eval() calls
- Code complexity metrics
- Security vulnerability counts
- Dependency health
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class QualityMetrics:
    """Container for quality metrics.

    Attributes:
        test_coverage: Test coverage percentage
        print_statements: Number of print() statements found
        eval_calls: Number of eval() calls found
        complexity: Code complexity metrics
        security_issues: Security vulnerability counts
        dependencies: Dependency health metrics
        timestamp: When metrics were collected
    """

    test_coverage: float = 0.0
    print_statements: int = 0
    eval_calls: int = 0
    complexity: Dict[str, Any] = field(default_factory=dict)
    security_issues: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_coverage": self.test_coverage,
            "print_statements": self.print_statements,
            "eval_calls": self.eval_calls,
            "complexity": self.complexity,
            "security_issues": self.security_issues,
            "dependencies": self.dependencies,
            "timestamp": self.timestamp,
        }


class QualityMetricsTracker:
    """Track and monitor quality metrics for the project.

    Example:
        >>> tracker = QualityMetricsTracker()
        >>> metrics = tracker.collect_metrics()
        >>> print(f"Coverage: {metrics.test_coverage}%")
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize quality metrics tracker.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path(".").resolve()
        self._metrics = QualityMetrics()

    def collect_metrics(self) -> QualityMetrics:
        """Collect all quality metrics.

        Returns:
            QualityMetrics object with collected metrics
        """
        self._metrics.timestamp = self._get_current_timestamp()

        # Collect test coverage
        self._collect_coverage()

        # Count print() statements
        self._count_print_statements()

        # Count eval() calls
        self._count_eval_calls()

        # Analyze code complexity
        self._analyze_complexity()

        # Check security issues
        self._check_security()

        # Analyze dependencies
        self._analyze_dependencies()

        return self._metrics

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO 8601 string."""
        from datetime import datetime
        return datetime.now().isoformat()

    def _collect_coverage(self) -> None:
        """Collect test coverage metrics."""
        try:
            # Run coverage command
            result = subprocess.run(
                ["coverage", "report", "--fail-under=0", "--skip-covered"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            # Parse coverage output
            for line in result.stdout.splitlines():
                if line.strip().startswith("TOTAL"):
                    parts = line.split()
                    if len(parts) >= 4:
                        coverage_str = parts[-1].replace("%", "")
                        try:
                            self._metrics.test_coverage = float(coverage_str)
                        except ValueError:
                            pass
                    break

        except Exception as e:
            print(f"Warning: Could not collect coverage: {e}")

    def _count_print_statements(self) -> None:
        """Count print() statements in source code."""
        try:
            # Use grep to count print statements
            result = subprocess.run(
                ["grep", "-r", "print(", "src/", "--include=*.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            self._metrics.print_statements = len(result.stdout.splitlines())
        except Exception as e:
            print(f"Warning: Could not count print statements: {e}")

    def _count_eval_calls(self) -> None:
        """Count eval() calls in source code."""
        try:
            # Use grep to count eval calls
            result = subprocess.run(
                ["grep", "-r", "eval(", "src/", "--include=*.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            self._metrics.eval_calls = len(result.stdout.splitlines())
        except Exception as e:
            print(f"Warning: Could not count eval calls: {e}")

    def _analyze_complexity(self) -> None:
        """Analyze code complexity metrics."""
        try:
            # Use ruff to analyze complexity
            result = subprocess.run(
                ["ruff", "check", "src/", "--format", "json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.stdout:
                data = json.loads(result.stdout)
                # Extract complexity metrics
                complexity = {
                    "files_checked": len(data.get("files", [])),
                    "errors": data.get("summary", {}).get("errors", 0),
                    "warnings": data.get("summary", {}).get("warnings", 0),
                    "fixable": data.get("summary", {}).get("fixable", 0),
                }
                self._metrics.complexity = complexity

        except Exception as e:
            print(f"Warning: Could not analyze complexity: {e}")

    def _check_security(self) -> None:
        """Check for security issues."""
        try:
            # Run bandit security scan
            result = subprocess.run(
                ["bandit", "-r", "src/", "-f", "json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.stdout:
                data = json.loads(result.stdout)
                security_issues = {
                    "files_checked": len(data.get("results", [])),
                    "issues": len(data.get("results", [])),
                    "high": len([i for i in data.get("results", []) if i.get("issue_severity") == "HIGH"]),
                    "medium": len([i for i in data.get("results", []) if i.get("issue_severity") == "MEDIUM"]),
                    "low": len([i for i in data.get("results", []) if i.get("issue_severity") == "LOW"]),
                }
                self._metrics.security_issues = security_issues

        except Exception as e:
            print(f"Warning: Could not check security: {e}")

    def _analyze_dependencies(self) -> None:
        """Analyze dependency health."""
        try:
            # Check for outdated dependencies
            result = subprocess.run(
                ["pip", "list", "--outdated"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            outdated = len(result.stdout.splitlines()) - 1  # Subtract header
            self._metrics.dependencies["outdated"] = outdated

            # Check for known vulnerabilities
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.stdout:
                data = json.loads(result.stdout)
                self._metrics.dependencies["vulnerabilities"] = len(data)

        except Exception as e:
            print(f"Warning: Could not analyze dependencies: {e}")

    def save_metrics(self, filepath: Path) -> None:
        """Save metrics to file."""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(self._metrics.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save metrics: {e}")

    def load_metrics(self, filepath: Path) -> None:
        """Load metrics from file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                self._metrics = QualityMetrics(**data)
        except Exception as e:
            print(f"Warning: Could not load metrics: {e}")

    def compare_metrics(self, other: "QualityMetricsTracker") -> Dict[str, Any]:
        """Compare metrics with another tracker.

        Returns:
            Dictionary with differences between metrics
        """
        current = self._metrics.to_dict()
        other_data = other._metrics.to_dict()

        differences = {}
        for key in current:
            if key in other_data and current[key] != other_data[key]:
                differences[key] = {
                    "current": current[key],
                    "previous": other_data[key],
                    "change": current[key] - other_data[key] if isinstance(current[key], (int, float)) else None
                }

        return differences


def check_for_print_statements(project_root: Path) -> int:
    """Check for print() statements in project.

    Args:
        project_root: Project root directory

    Returns:
        Number of print() statements found
    """
    try:
        result = subprocess.run(
            ["grep", "-r", "print(", str(project_root), "--include=*.py"],
            capture_output=True,
            text=True
        )
        return len(result.stdout.splitlines())
    except Exception:
        return -1


def check_for_eval_calls(project_root: Path) -> int:
    """Check for eval() calls in project.

    Args:
        project_root: Project root directory

    Returns:
        Number of eval() calls found
    """
    try:
        result = subprocess.run(
            ["grep", "-r", "eval(", str(project_root), "--include=*.py"],
            capture_output=True,
            text=True
        )
        return len(result.stdout.splitlines())
    except Exception:
        return -1


def get_code_complexity(project_root: Path) -> Dict[str, Any]:
    """Get code complexity metrics.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with complexity metrics
    """
    try:
        result = subprocess.run(
            ["ruff", "check", str(project_root), "--format", "json"],
            capture_output=True,
            text=True
        )

        if result.stdout:
            data = json.loads(result.stdout)
            return {
                "files_checked": len(data.get("files", [])),
                "errors": data.get("summary", {}).get("errors", 0),
                "warnings": data.get("summary", {}).get("warnings", 0),
                "fixable": data.get("summary", {}).get("fixable", 0),
            }
    except Exception:
        pass

    return {}


def get_security_issues(project_root: Path) -> Dict[str, Any]:
    """Get security issues.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with security issue counts
    """
    try:
        result = subprocess.run(
            ["bandit", "-r", str(project_root), "-f", "json"],
            capture_output=True,
            text=True
        )

        if result.stdout:
            data = json.loads(result.stdout)
            return {
                "files_checked": len(data.get("results", [])),
                "issues": len(data.get("results", [])),
                "high": len([i for i in data.get("results", []) if i.get("issue_severity") == "HIGH"]),
                "medium": len([i for i in data.get("results", []) if i.get("issue_severity") == "MEDIUM"]),
                "low": len([i for i in data.get("results", []) if i.get("issue_severity") == "LOW"]),
            }
    except Exception:
        pass

    return {}


def get_dependency_health(project_root: Path) -> Dict[str, Any]:
    """Get dependency health metrics.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with dependency health metrics
    """
    try:
        # Check for outdated dependencies
        result = subprocess.run(
            ["pip", "list", "--outdated"],
            capture_output=True,
            text=True
        )

        outdated = len(result.stdout.splitlines()) - 1  # Subtract header

        # Check for vulnerabilities
        result = subprocess.run(
            ["safety", "check", "--json"],
            capture_output=True,
            text=True
        )

        if result.stdout:
            data = json.loads(result.stdout)
            vulnerabilities = len(data)
        else:
            vulnerabilities = 0

        return {
            "outdated": outdated,
            "vulnerabilities": vulnerabilities,
        }
    except Exception:
        return {}


def generate_quality_report(metrics: QualityMetrics) -> str:
    """Generate a human-readable quality report.

    Args:
        metrics: QualityMetrics object

    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 60)
    report.append("VJLive3 Quality Report")
    report.append(f"Generated: {metrics.timestamp}")
    report.append("=" * 60)
    report.append("")

    # Test Coverage
    report.append(f"Test Coverage: {metrics.test_coverage:.1f}%")
    if metrics.test_coverage < 80:
        report.append("  ❌ Below target (80%)")
    elif metrics.test_coverage < 90:
        report.append("  ⚠️  Below ideal (90%)")
    else:
        report.append("  ✅ Excellent")
    report.append("")

    # Code Quality
    report.append("Code Quality:")
    report.append(f"  Print statements: {metrics.print_statements}")
    if metrics.print_statements > 0:
        report.append("  ❌ Remove print() statements")
    else:
        report.append("  ✅ No print() statements")

    report.append(f"  Eval calls: {metrics.eval_calls}")
    if metrics.eval_calls > 0:
        report.append("  ❌ Remove eval() calls")
    else:
        report.append("  ✅ No eval() calls")

    # Complexity
    report.append(f"  Files checked: {metrics.complexity.get('files_checked', 0)}")
    report.append(f"  Errors: {metrics.complexity.get('errors', 0)}")
    report.append(f"  Warnings: {metrics.complexity.get('warnings', 0)}")
    report.append(f"  Fixable: {metrics.complexity.get('fixable', 0)}")

    # Security
    report.append(f"Security Issues:")
    report.append(f"  Files checked: {metrics.security_issues.get('files_checked', 0)}")
    report.append(f"  Total issues: {metrics.security_issues.get('issues', 0)}")
    report.append(f"  High: {metrics.security_issues.get('high', 0)}")
    report.append(f"  Medium: {metrics.security_issues.get('medium', 0)}")
    report.append(f"  Low: {metrics.security_issues.get('low', 0)}")

    # Dependencies
    report.append(f"Dependencies:")
    report.append(f"  Outdated: {metrics.dependencies.get('outdated', 0)}")
    report.append(f"  Vulnerabilities: {metrics.dependencies.get('vulnerabilities', 0)}")

    report.append("")
    report.append("=" * 60)

    return "\n".join(report)