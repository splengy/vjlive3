#!/usr/bin/env python3
"""
Naming Consistency Checker — Cross-reference identifiers across specs and code.

Usage:
    python scripts/check_naming.py                        # scan all specs
    python scripts/check_naming.py docs/specs/P1-R3*.md   # scan specific spec
    python scripts/check_naming.py --src src/              # also scan source code
    python scripts/check_naming.py --registry              # show the master name registry
    python scripts/check_naming.py --fix                   # suggest canonical names

Catches:
    - red_LED vs Red_LED vs red-led (case/style mismatches)
    - on_frame_ready vs onFrameReady (snake_case vs camelCase)
    - callback naming inconsistency across modules
    - Same concept with different names in different specs
"""

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


SPECS_DIR = Path(__file__).parent.parent / "docs" / "specs"
SRC_DIR = Path(__file__).parent.parent / "src"
REGISTRY_PATH = Path(__file__).parent.parent / "docs" / "NAME_REGISTRY.json"


@dataclass
class NameOccurrence:
    name: str
    source_file: str
    line_number: int
    context: str  # "spec_interface", "spec_param", "spec_callback", "code_class", etc.


@dataclass
class NamingConflict:
    canonical: str
    variants: List[str]
    occurrences: List[NameOccurrence]
    severity: str  # "error" (same concept, different names), "warning" (style mismatch)


def normalize_name(name: str) -> str:
    """Normalize a name for comparison — strips casing and separators."""
    # Convert camelCase to snake_case
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    result = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1)
    # Remove hyphens, convert to lowercase
    result = result.replace("-", "_").lower()
    # Remove leading/trailing underscores
    result = result.strip("_")
    return result


def detect_style(name: str) -> str:
    """Detect naming convention style."""
    if "-" in name:
        return "kebab-case"
    if "_" in name:
        if name[0].isupper():
            return "Pascal_Snake"
        return "snake_case"
    if name[0].isupper():
        return "PascalCase"
    if any(c.isupper() for c in name[1:]):
        return "camelCase"
    return "lowercase"


def extract_names_from_spec(filepath: str) -> List[NameOccurrence]:
    """Extract variable, function, class, and callback names from a spec file."""
    names = []

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    in_code_block = False
    context = "spec_text"

    for i, line in enumerate(lines, 1):
        # Track code blocks
        if line.strip().startswith("```python"):
            in_code_block = True
            context = "spec_interface"
            continue
        elif line.strip().startswith("```"):
            in_code_block = False
            context = "spec_text"
            continue

        if in_code_block:
            # Extract class names
            class_match = re.findall(r"class\s+(\w+)", line)
            for name in class_match:
                names.append(NameOccurrence(
                    name=name, source_file=filepath,
                    line_number=i, context="spec_class"
                ))

            # Extract function/method names
            func_match = re.findall(r"def\s+(\w+)", line)
            for name in func_match:
                if name.startswith("__") and name.endswith("__"):
                    continue  # skip dunders
                names.append(NameOccurrence(
                    name=name, source_file=filepath,
                    line_number=i, context="spec_method"
                ))

            # Extract parameter names from type hints
            param_match = re.findall(r"(\w+)\s*:\s*\w+", line)
            for name in param_match:
                if name in ("self", "cls", "return", "str", "int", "float",
                            "bool", "list", "dict", "tuple", "set", "None",
                            "Optional", "List", "Dict", "Tuple", "Type"):
                    continue
                names.append(NameOccurrence(
                    name=name, source_file=filepath,
                    line_number=i, context="spec_param"
                ))

        else:
            # Extract backtick-quoted identifiers from markdown
            backtick_names = re.findall(r"`(\w+(?:\.\w+)*)`", line)
            for name in backtick_names:
                # Skip obvious non-identifiers
                if name in ("python", "mermaid", "bash", "json", "yaml"):
                    continue
                # Handle dotted names (e.g., vjlive3.core.module)
                parts = name.split(".")
                for part in parts:
                    if len(part) > 2 and not part[0].isdigit():
                        names.append(NameOccurrence(
                            name=part, source_file=filepath,
                            line_number=i, context="spec_reference"
                        ))

            # Extract callback patterns
            callback_match = re.findall(
                r"(on_\w+|callback_\w+|\w+_callback|\w+_handler|on[A-Z]\w+)",
                line
            )
            for name in callback_match:
                names.append(NameOccurrence(
                    name=name, source_file=filepath,
                    line_number=i, context="spec_callback"
                ))

    return names


def extract_names_from_python(filepath: str) -> List[NameOccurrence]:
    """Extract identifiers from Python source files."""
    names = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, UnicodeDecodeError):
        return names

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            names.append(NameOccurrence(
                name=node.name, source_file=filepath,
                line_number=node.lineno, context="code_class"
            ))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not (node.name.startswith("__") and node.name.endswith("__")):
                names.append(NameOccurrence(
                    name=node.name, source_file=filepath,
                    line_number=node.lineno, context="code_method"
                ))

    return names


def find_conflicts(all_names: List[NameOccurrence]) -> List[NamingConflict]:
    """Group names by normalized form and find conflicts."""
    # Group by normalized name
    groups: Dict[str, List[NameOccurrence]] = defaultdict(list)
    for occ in all_names:
        normalized = normalize_name(occ.name)
        if len(normalized) < 3:
            continue  # skip very short names
        groups[normalized].append(occ)

    conflicts = []
    for normalized, occurrences in groups.items():
        # Get unique surface forms
        variants = list(set(occ.name for occ in occurrences))
        if len(variants) <= 1:
            continue  # no conflict

        # Determine severity
        styles = set(detect_style(v) for v in variants)
        if len(styles) > 1:
            severity = "error"  # mixing naming conventions
        else:
            severity = "warning"  # same convention, different casing

        # Pick canonical form (prefer snake_case)
        canonical = sorted(variants, key=lambda v: (
            0 if detect_style(v) == "snake_case" else 1,
            len(v)
        ))[0]

        conflicts.append(NamingConflict(
            canonical=canonical,
            variants=sorted(variants),
            occurrences=occurrences,
            severity=severity,
        ))

    # Sort by severity then canonical name
    conflicts.sort(key=lambda c: (0 if c.severity == "error" else 1, c.canonical))
    return conflicts


def save_registry(all_names: List[NameOccurrence]):
    """Save a name registry for future reference."""
    registry = defaultdict(lambda: {"files": set(), "contexts": set()})

    for occ in all_names:
        normalized = normalize_name(occ.name)
        entry = registry[normalized]
        entry["canonical"] = occ.name
        entry["files"].add(Path(occ.source_file).name)
        entry["contexts"].add(occ.context)

    # Convert sets to lists for JSON
    output = {}
    for normalized, data in sorted(registry.items()):
        output[normalized] = {
            "canonical": data["canonical"],
            "files": sorted(data["files"]),
            "contexts": sorted(data["contexts"]),
        }

    with open(REGISTRY_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"📋 Name registry saved to {REGISTRY_PATH} ({len(output)} entries)")


def main():
    parser = argparse.ArgumentParser(
        description="Check naming consistency across specs and code"
    )
    parser.add_argument("paths", nargs="*", help="Spec files or directories to check")
    parser.add_argument("--src", help="Also scan source directory")
    parser.add_argument("--registry", action="store_true",
                        help="Save/show master name registry")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 1 if errors found")
    args = parser.parse_args()

    # Collect files to scan
    spec_files = []
    if args.paths:
        for p in args.paths:
            path = Path(p)
            if path.is_file():
                spec_files.append(str(path))
            elif path.is_dir():
                spec_files.extend(str(f) for f in path.glob("*.md")
                                  if not f.name.startswith("_"))
    else:
        if SPECS_DIR.exists():
            spec_files = [str(f) for f in SPECS_DIR.glob("*.md")
                          if not f.name.startswith("_")]

    # Extract names
    all_names = []
    for sf in spec_files:
        all_names.extend(extract_names_from_spec(sf))

    if args.src:
        src_path = Path(args.src)
        if src_path.exists():
            for py_file in src_path.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    all_names.extend(extract_names_from_python(str(py_file)))

    if not all_names:
        print("No names found. Are there specs in docs/specs/?")
        sys.exit(0)

    print(f"Scanned {len(spec_files)} spec files, found {len(all_names)} identifiers\n")

    # Save registry if requested
    if args.registry:
        save_registry(all_names)

    # Find conflicts
    conflicts = find_conflicts(all_names)

    if args.json:
        print(json.dumps([{
            "canonical": c.canonical,
            "variants": c.variants,
            "severity": c.severity,
            "files": list(set(Path(o.source_file).name for o in c.occurrences)),
        } for c in conflicts], indent=2))
        return

    errors = [c for c in conflicts if c.severity == "error"]
    warnings = [c for c in conflicts if c.severity == "warning"]

    if errors:
        print(f"❌ {len(errors)} naming conflicts (mixed conventions):\n")
        for c in errors:
            files = sorted(set(Path(o.source_file).name for o in c.occurrences))
            print(f"  🚫 {' vs '.join(c.variants)}")
            print(f"     Canonical: {c.canonical}")
            print(f"     Found in: {', '.join(files)}")
            print()

    if warnings:
        print(f"⚠️  {len(warnings)} naming inconsistencies (same convention, different forms):\n")
        for c in warnings[:20]:  # cap at 20
            files = sorted(set(Path(o.source_file).name for o in c.occurrences))
            print(f"  🔸 {' vs '.join(c.variants)}")
            print(f"     Found in: {', '.join(files)}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more")
        print()

    if not conflicts:
        print("✅ No naming conflicts found!")
    else:
        print(f"{'='*50}")
        print(f"Summary: {len(errors)} errors, {len(warnings)} warnings")
        print(f"Total identifiers scanned: {len(all_names)}")

    if args.strict and errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
