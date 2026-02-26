#!/usr/bin/env python3
"""
Spec Validator — Check a spec file for completeness against the template.

Usage:
    python scripts/validate_spec.py docs/specs/P1-R3_VideoSourceAbstraction.md
    python scripts/validate_spec.py docs/specs/  # validate all specs in directory
    python scripts/validate_spec.py --strict docs/specs/P1-R3_VideoSourceAbstraction.md

Checks:
    - All required sections present
    - Legacy References table populated (not just template placeholders)
    - Public Interface has actual code
    - Test Plan has actual tests
    - Definition of Done checklist present
    - Mermaid diagram present (core specs only)
"""

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    filepath: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score: int = 0  # out of 100


# Required sections for ALL specs
REQUIRED_SECTIONS = [
    "What This Module Does",
    "Public Interface",
    "Inputs and Outputs",
    "Dependencies",
    "Test Plan",
    "Definition of Done",
]

# Additional required sections for CORE specs
CORE_SECTIONS = [
    "Architecture Decisions",
    "Legacy References",
    "Platform Abstraction",
    "What This Module Does NOT Do",
]

TEMPLATE_PLACEHOLDERS = [
    "[TASK-ID]",
    "[Module Name]",
    "2–3 sentences",
    "Paste planned class",
    "What it is",
    "Range / valid values",
    "used for X",
    "list the tests",
]


def detect_spec_type(content: str) -> str:
    """Detect if this is a core or plugin spec."""
    if "Architecture Decisions" in content or "Platform Abstraction" in content:
        return "core"
    return "plugin"


def validate_spec(filepath: str) -> ValidationResult:
    """Validate a single spec file."""
    result = ValidationResult(filepath=filepath, passed=True)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, UnicodeDecodeError) as e:
        result.passed = False
        result.errors.append(f"Cannot read file: {e}")
        return result

    # Skip template files
    basename = Path(filepath).name
    if basename.startswith("_"):
        result.warnings.append("Skipping template/example file")
        result.score = 100
        return result

    spec_type = detect_spec_type(content)
    sections = REQUIRED_SECTIONS.copy()
    if spec_type == "core":
        sections.extend(CORE_SECTIONS)

    points = 0
    max_points = 0

    # Check required sections
    for section in sections:
        max_points += 10
        if re.search(rf"##\s+.*{re.escape(section)}", content, re.IGNORECASE):
            points += 10
        else:
            result.errors.append(f"Missing section: '{section}'")
            result.passed = False

    # Check for template placeholders still present
    for placeholder in TEMPLATE_PLACEHOLDERS:
        if placeholder in content:
            result.warnings.append(f"Template placeholder still present: '{placeholder}'")
            result.passed = False

    # Check Public Interface has actual code
    max_points += 10
    if "```python" in content:
        code_blocks = re.findall(r"```python\s*\n(.+?)```", content, re.DOTALL)
        has_real_code = any(
            "class " in block or "def " in block
            for block in code_blocks
        )
        if has_real_code:
            points += 10
        else:
            result.warnings.append("Public Interface code block has no class/function definitions")
    else:
        result.errors.append("No Python code blocks found")

    # Check Test Plan has actual tests
    max_points += 10
    test_matches = re.findall(r"\|\s*`?test_\w+", content)
    if len(test_matches) >= 3:
        points += 10
    elif test_matches:
        points += 5
        result.warnings.append(f"Only {len(test_matches)} tests defined (recommend ≥3)")
    else:
        result.errors.append("No test cases defined in Test Plan")
        result.passed = False

    # Check Legacy References (core specs)
    if spec_type == "core":
        max_points += 10
        if "VJlive" in content and ("|" in content):
            legacy_rows = re.findall(r"\|\s*VJlive-[12]", content)
            if len(legacy_rows) >= 1:
                points += 10
            else:
                result.warnings.append("Legacy References table appears empty")
        else:
            result.errors.append("No Legacy References with actual VJlive code paths")

    # Check Mermaid diagram (core specs)
    if spec_type == "core":
        max_points += 10
        if "```mermaid" in content:
            points += 10
        else:
            result.warnings.append("No Mermaid dependency graph")

    # Calculate score
    result.score = int((points / max_points) * 100) if max_points > 0 else 0

    if result.score < 50:
        result.passed = False

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate spec files for completeness")
    parser.add_argument("path", help="Spec file or directory to validate")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 1 if any spec fails")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    target = Path(args.path)
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.glob("*.md"))
    else:
        print(f"ERROR: {args.path} not found", file=sys.stderr)
        sys.exit(2)

    results = []
    for f in files:
        if f.name.startswith("_"):
            continue  # skip templates
        results.append(validate_spec(str(f)))

    if args.json:
        import json
        print(json.dumps([{
            "file": r.filepath,
            "passed": r.passed,
            "score": r.score,
            "errors": r.errors,
            "warnings": r.warnings,
        } for r in results], indent=2))
    else:
        total = len(results)
        passed = sum(1 for r in results if r.passed)

        for r in results:
            icon = "✅" if r.passed else "❌"
            print(f"{icon} {Path(r.filepath).name} — {r.score}%")
            for e in r.errors:
                print(f"   🚫 {e}")
            for w in r.warnings:
                print(f"   ⚠️  {w}")
            print()

        print(f"{'='*40}")
        print(f"Results: {passed}/{total} passed")

    if args.strict and any(not r.passed for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
