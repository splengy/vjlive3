"""
Word Salad Detector — AHOS Validator Module

Detects LLM hallucination patterns in generated code output.
These patterns were extracted directly from the Antigravity incident
(SECURITY_AUDIT_2026-02-24.md) where 41 files contained 1,047+
occurrences of meaningless adverb spam.

This module is DETERMINISTIC. No LLM reasoning. Pure regex.
"""

import re
from dataclasses import dataclass, field


# Adverbs that appeared repeatedly in the Antigravity contamination.
# Individually these words CAN be legitimate. The detector looks for
# chains (2+ in a single comment/line) or excessive density (>threshold
# per file).
WORD_SALAD_ADVERBS = [
    "natively",
    "organically",
    "beautifully",
    "securely",
    "properly",
    "gracefully",
    "reliably",
    "predictably",
    "structurally",
    "seamlessly",
    "flawlessly",
    "perfectly",
    "optimally",
    "elegantly",
    "intuitively",
    "dynamically",
    "accurately",
    "correctly",
]

# Phrases that are dead giveaways of LLM padding — never appear in
# human-written code.
WORD_SALAD_PHRASES = [
    r"natively\s+\w+\s+natively",           # "natively X natively" double-hit
    r"checking\s+iterations\s+structurally", # from depth_blur.py
    r"natively\s+allocating\s+new",          # from test_quantum_hyper_tunnel
    r"bounds\s+safely\s+preventing",         # from depth_aware_compression
    r"smoothly\s+accurately",               # adverb chain
    r"gracefully\s+smoothly",               # adverb chain
    r"properly\s+bounds\s+safely",          # adverb chain from depth_aware_compression
    r"natively\s+securely\s+properly",      # triple adverb chain
    r"organically\s+natively",              # adverb chain
    r"reliably\s+organically",              # adverb chain
]

# Compile all patterns once at import time
_ADVERB_PATTERN = re.compile(
    r"\b(" + "|".join(WORD_SALAD_ADVERBS) + r")\b",
    re.IGNORECASE,
)

_PHRASE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in WORD_SALAD_PHRASES]

# Two or more adverbs on the same line is always suspicious
_ADVERB_CHAIN_PATTERN = re.compile(
    r"\b("
    + "|".join(WORD_SALAD_ADVERBS)
    + r")\b.*\b("
    + "|".join(WORD_SALAD_ADVERBS)
    + r")\b",
    re.IGNORECASE,
)


@dataclass
class WordSaladResult:
    """Result of a word salad scan."""

    passed: bool
    total_hits: int = 0
    chain_hits: int = 0
    phrase_hits: int = 0
    density: float = 0.0  # hits per 100 lines
    flagged_lines: list = field(default_factory=list)
    verdict: str = ""


def scan(content: str, max_hits: int = 2, max_density: float = 1.0) -> WordSaladResult:
    """
    Scan code content for word salad patterns.

    Args:
        content: The raw source code string to analyze.
        max_hits: Maximum allowed individual adverb occurrences before
                  the file is flagged.  Default 2 allows occasional
                  legitimate use like "numpy handles arrays natively".
        max_density: Maximum adverb hits per 100 lines before flagging.

    Returns:
        WordSaladResult with pass/fail verdict and evidence.
    """
    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return WordSaladResult(passed=True, verdict="EMPTY_FILE")

    result = WordSaladResult(passed=True)
    flagged = []

    # Pass 1: Count individual adverb hits
    for i, line in enumerate(lines, start=1):
        matches = _ADVERB_PATTERN.findall(line)
        if matches:
            result.total_hits += len(matches)
            flagged.append((i, line.strip(), matches))

    # Pass 2: Detect adverb chains (2+ adverbs on same line)
    for i, line in enumerate(lines, start=1):
        if _ADVERB_CHAIN_PATTERN.search(line):
            result.chain_hits += 1
            # Don't double-add to flagged — already caught in Pass 1

    # Pass 3: Detect known hallucination phrases
    for i, line in enumerate(lines, start=1):
        for pattern in _PHRASE_PATTERNS:
            if pattern.search(line):
                result.phrase_hits += 1

    # Calculate density
    result.density = (result.total_hits / total_lines) * 100
    result.flagged_lines = flagged

    # Verdict logic:
    # - ANY phrase hit = instant fail (these are confirmed hallucination)
    # - ANY chain hit = instant fail (double adverb on one line)
    # - Total hits > threshold = fail
    # - Density > threshold = fail
    reasons = []
    if result.phrase_hits > 0:
        reasons.append(f"PHRASE_HIT: {result.phrase_hits} known hallucination phrases")
    if result.chain_hits > 0:
        reasons.append(f"CHAIN_HIT: {result.chain_hits} lines with 2+ adverbs")
    if result.total_hits > max_hits:
        reasons.append(f"ADVERB_COUNT: {result.total_hits} hits (max {max_hits})")
    if result.density > max_density:
        reasons.append(f"DENSITY: {result.density:.2f} per 100 lines (max {max_density})")

    if reasons:
        result.passed = False
        result.verdict = "REJECTED: " + "; ".join(reasons)
    else:
        result.verdict = f"PASSED: {result.total_hits} hits within tolerance"

    return result


def scan_file(filepath: str, **kwargs) -> WordSaladResult:
    """Convenience function to scan a file on disk. Fails closed on read error."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return scan(f.read(), **kwargs)
    except FileNotFoundError:
        return WordSaladResult(passed=False, verdict=f"FILE_NOT_FOUND: {filepath}")
    except PermissionError:
        return WordSaladResult(passed=False, verdict=f"PERMISSION_DENIED: {filepath}")
    except Exception as e:
        return WordSaladResult(passed=False, verdict=f"READ_ERROR: {filepath}: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python word_salad_detector.py <file_or_directory>")
        sys.exit(1)

    import os

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
        print(f"{status} | {result.total_hits:3d} hits | {fpath}")
        if not result.passed:
            total_rejected += 1
            print(f"       └── {result.verdict}")

    print(f"\n{'=' * 60}")
    print(f"Scanned: {len(files)} files | Rejected: {total_rejected}")
