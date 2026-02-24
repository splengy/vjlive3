"""
Stub Detector — AHOS Validator Module

Detects fraudulent code patterns: NotImplementedError, bare pass,
empty exception handlers, TODO placeholders, and fake implementations.

These patterns were extracted from the Antigravity incident where
quantum_hyper_tunnel.py and desktop_gui.py were complete stubs
masquerading as implementations.

This module is DETERMINISTIC. No LLM reasoning. Pure pattern matching.
"""

import re
from dataclasses import dataclass, field


# Hard-kill patterns: if ANY of these appear, the file is rejected.
INSTANT_REJECT_PATTERNS = [
    (r"raise\s+NotImplementedError", "STUB: raise NotImplementedError"),
    (r'raise\s+RuntimeError\s*\(\s*["\']TODO', "STUB: raise RuntimeError('TODO')"),
    (r"#\s*In a real environment", "FRAUD: admits it's not real"),
    (r"#\s*TODO:\s*implement", "STUB: TODO implement marker"),
    (r"#\s*FIXME:\s*stub", "STUB: FIXME stub marker"),
    (r"#\s*placeholder", "STUB: placeholder marker"),
]

# Suspicious patterns: counted and evaluated against thresholds.
SUSPICIOUS_PATTERNS = [
    (r":\s*pass\s*$", "BARE_PASS: method body is just 'pass'"),
    (r"except\s*:\s*pass", "SWALLOW: bare except:pass hides all errors"),
    (r"except\s+\w+\s*:\s*pass", "SWALLOW: typed except:pass hides errors"),
    (r"return\s+None\s*$", "LAZY_RETURN: function returns None explicitly"),
    (r"assert\s+\w+\s*$", "WEAK_ASSERT: bare 'assert x' with no comparison"),
    (r"assert\s+\w+\s+is\s+not\s+None", "WEAK_ASSERT: 'assert x is not None' tests nothing"),
    (r"assert\s+result\s*$", "WEAK_ASSERT: 'assert result' is meaningless"),
    (r"assert\s+True", "FAKE_ASSERT: 'assert True' always passes"),
]

# Compile patterns
_INSTANT_REJECT = [(re.compile(p, re.IGNORECASE), msg) for p, msg in INSTANT_REJECT_PATTERNS]
_SUSPICIOUS = [(re.compile(p, re.MULTILINE), msg) for p, msg in SUSPICIOUS_PATTERNS]


@dataclass
class StubResult:
    """Result of a stub/fraud scan."""

    passed: bool
    instant_rejects: int = 0
    suspicious_count: int = 0
    bare_pass_count: int = 0
    weak_assert_count: int = 0
    code_lines: int = 0
    total_lines: int = 0
    code_ratio: float = 0.0  # actual code / total lines
    flagged_lines: list = field(default_factory=list)
    verdict: str = ""


def scan(content: str, max_suspicious: int = 1, min_code_ratio: float = 0.3) -> StubResult:
    """
    Scan code content for stub and fraud patterns.

    Args:
        content: The raw source code string to analyze.
        max_suspicious: Maximum suspicious pattern hits before rejection.
        min_code_ratio: Minimum ratio of code lines to total lines.
                        Files with less than 30% actual code are flagged.

    Returns:
        StubResult with pass/fail verdict and evidence.
    """
    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return StubResult(passed=False, verdict="REJECTED: EMPTY_FILE")

    result = StubResult(passed=True, total_lines=total_lines)

    # Count actual code lines (not blank, not comments, not docstrings)
    in_docstring = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                continue  # single-line docstring
            in_docstring = not in_docstring
            continue
        if in_docstring:
            continue
        if stripped and not stripped.startswith("#"):
            result.code_lines += 1

    result.code_ratio = result.code_lines / total_lines if total_lines > 0 else 0

    # Check instant reject patterns
    for i, line in enumerate(lines, start=1):
        for pattern, msg in _INSTANT_REJECT:
            if pattern.search(line):
                result.instant_rejects += 1
                result.flagged_lines.append((i, line.strip(), msg))

    # Check suspicious patterns
    for i, line in enumerate(lines, start=1):
        for pattern, msg in _SUSPICIOUS:
            if pattern.search(line):
                result.suspicious_count += 1
                if "BARE_PASS" in msg:
                    result.bare_pass_count += 1
                if "WEAK_ASSERT" in msg or "FAKE_ASSERT" in msg:
                    result.weak_assert_count += 1
                result.flagged_lines.append((i, line.strip(), msg))

    # Verdict logic
    reasons = []
    if result.instant_rejects > 0:
        reasons.append(f"INSTANT_REJECT: {result.instant_rejects} hard-kill patterns found")
    if result.suspicious_count > max_suspicious:
        reasons.append(f"SUSPICIOUS: {result.suspicious_count} hits (max {max_suspicious})")
    if result.code_ratio < min_code_ratio and total_lines > 20:
        reasons.append(
            f"LOW_CODE: {result.code_ratio:.0%} code ratio "
            f"({result.code_lines}/{total_lines} lines, min {min_code_ratio:.0%})"
        )
    if result.bare_pass_count > 0:
        reasons.append(f"BARE_PASS: {result.bare_pass_count} methods with only 'pass'")

    if reasons:
        result.passed = False
        result.verdict = "REJECTED: " + "; ".join(reasons)
    else:
        result.verdict = (
            f"PASSED: {result.code_lines}/{total_lines} code lines "
            f"({result.code_ratio:.0%}), {result.suspicious_count} minor flags"
        )

    return result


def scan_file(filepath: str, **kwargs) -> StubResult:
    """Convenience function to scan a file on disk. Fails closed on read error."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return scan(f.read(), **kwargs)
    except FileNotFoundError:
        return StubResult(passed=False, verdict=f"FILE_NOT_FOUND: {filepath}")
    except PermissionError:
        return StubResult(passed=False, verdict=f"PERMISSION_DENIED: {filepath}")
    except Exception as e:
        return StubResult(passed=False, verdict=f"READ_ERROR: {filepath}: {e}")


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: python stub_detector.py <file_or_directory>")
        sys.exit(1)

    target = sys.argv[1]
    files = []

    if os.path.isfile(target):
        files = [target]
    elif os.path.isdir(target):
        for root, _, filenames in os.walk(target):
            for fn in filenames:
                if fn.endswith(".py"):
                    files.append(os.path.join(root, fn))

    total_rejected = 0
    for fpath in sorted(files):
        result = scan_file(fpath)
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status} | code:{result.code_ratio:.0%} | stubs:{result.instant_rejects} | {fpath}")
        if not result.passed:
            total_rejected += 1
            print(f"       └── {result.verdict}")
            for line_no, line_text, msg in result.flagged_lines[:5]:
                print(f"           L{line_no}: {msg}")

    print(f"\n{'=' * 60}")
    print(f"Scanned: {len(files)} files | Rejected: {total_rejected}")
