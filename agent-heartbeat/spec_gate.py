#!/usr/bin/env python3
"""
Spec Quality Gate — Node 4 in the pipeline.

Checks completed specs for readiness before code generation.
Returns a list of specs that are ready, flagged, or need review.

Usage:
    python3 spec_gate.py                  # Check all specs
    python3 spec_gate.py P3-EXT001        # Check one spec
    python3 spec_gate.py --ready-only     # Only show ready specs
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

# Resolve project root from script location (works on desktop AND OPis via SSHFS)
PROJECT = str(Path(os.path.dirname(os.path.abspath(__file__))).parent)
SPECS_DIR = os.path.join(PROJECT, "docs", "specs")
SRC_DIR = os.path.join(PROJECT, "src", "vjlive3", "plugins")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# Required sections in a spec (any alias counts)
REQUIRED_SECTIONS = [
    "What This Module Does",  # Must have scope definition
]
# Soft requirements — logged as warnings but not blocking
SOFT_SECTIONS = [
    "Public Interface",  # aliases: Detailed Behavior, Parameter Mapping
]

# Minimum spec quality thresholds
MIN_LINES = 30
MIN_BYTES = 500


def check_enrichment(content: str) -> dict:
    """
    Check if a spec has been enriched by the second pass (Roo).
    
    First-pass (4B NPU) produces: interface, params, basic structure.
    Second-pass (Roo) adds: prose, behavior, scope, integration, performance.
    
    Key: We check for PROSE CONTENT after headers, not just headers.
    RKLLM skeletons have headers but only placeholder content.
    """
    def has_prose_after(header_pattern: str, min_chars: int = 50) -> bool:
        """Check if a section header exists AND has real prose content after it."""
        match = re.search(header_pattern + r'\n+(.*?)(?=\n##|\Z)', content, re.IGNORECASE | re.DOTALL)
        if not match:
            return False
        body = match.group(1).strip()
        # Filter out placeholder content
        body_clean = re.sub(r'\[NEEDS RESEARCH\].*', '', body).strip()
        body_clean = re.sub(r'\*.*?\*', '', body_clean).strip()  # Remove italic placeholders
        return len(body_clean) >= min_chars

    enrichment_sections = {
        "description": has_prose_after(r"##\s*Description", min_chars=100),
        "does_not_do": has_prose_after(r"##\s*What This Module Does\s*N[Oo][Tt]", min_chars=50),
        "integration": has_prose_after(r"##\s*Integration", min_chars=50),
        "performance": has_prose_after(r"##\s*Performance", min_chars=50),
    }
    score = sum(enrichment_sections.values())
    return {
        "enriched": score >= 2,  # At least 2 of 4 sections with real prose (not just headers)
        "enrichment_score": score,
        "sections_present": [k for k, v in enrichment_sections.items() if v],
        "sections_missing": [k for k, v in enrichment_sections.items() if not v],
    }


def check_spec(spec_path: str) -> dict:
    """
    Check a single spec file for quality and readiness.
    
    Returns a dict with:
        - task_id: str
        - status: 'ready' | 'needs_review' | 'incomplete'
        - pass_status: 'skeleton' | 'enriched'
        - issues: list of strings describing problems
        - has_code: bool (implementation already exists)
    """
    task_id = Path(spec_path).stem.replace("_spec", "")
    result = {
        "task_id": task_id,
        "spec_path": spec_path,
        "status": "ready",
        "pass_status": "skeleton",  # 'skeleton' = first pass only, 'enriched' = second pass done
        "issues": [],
        "has_code": False,
    }

    # Check if file exists
    if not os.path.exists(spec_path):
        result["status"] = "missing"
        result["issues"].append("Spec file does not exist")
        return result

    with open(spec_path, "r") as f:
        content = f.read()
        lines = content.split("\n")

    # Check minimum size
    if len(lines) < MIN_LINES:
        result["status"] = "incomplete"
        result["issues"].append(f"Too short: {len(lines)} lines (min {MIN_LINES})")

    if len(content) < MIN_BYTES:
        result["status"] = "incomplete"
        result["issues"].append(f"Too small: {len(content)} bytes (min {MIN_BYTES})")

    # Check for [NEEDS RESEARCH] markers (exclude prose that references them in past tense)
    RESEARCH_EXCLUDE = ["fills in", "filled in", "markers and", "marker(s) and", "this expanded", "expanded context"]
    research_hits = [
        (i + 1, line.strip())
        for i, line in enumerate(lines)
        if ("[NEEDS RESEARCH]" in line or "[NEEDS_RESEARCH]" in line)
        and not any(excl in line.lower() for excl in RESEARCH_EXCLUDE)
        and not line.strip().startswith("#")  # skip headings that use the term
    ]
    if research_hits:
        result["status"] = "needs_review"
        result["issues"].append(f"Has {len(research_hits)} [NEEDS RESEARCH] marker(s)")

    # Check for required sections
    for section in REQUIRED_SECTIONS:
        if section.lower() not in content.lower():
            result["issues"].append(f"Missing section: '{section}'")
            if result["status"] == "ready":
                result["status"] = "needs_review"

    # Check for stub indicators in code blocks
    stub_patterns = [
        r"```python\s*\n\s*pass\s*\n\s*```",
        r"raise NotImplementedError",
        r"# TODO: implement",
    ]
    for pat in stub_patterns:
        if re.search(pat, content, re.IGNORECASE):
            result["issues"].append(f"Contains stub code: {pat[:30]}")
            if result["status"] == "ready":
                result["status"] = "needs_review"

    # Check enrichment status
    enrichment = check_enrichment(content)
    if enrichment["enriched"]:
        result["pass_status"] = "enriched"
    result["enrichment"] = enrichment

    # Check if implementation already exists
    module_match = re.search(r"##\s*Task:.*?—\s*(\w+)", content)
    if module_match:
        module_name = module_match.group(1)
        impl_path = os.path.join(SRC_DIR, f"{module_name}.py")
        if os.path.exists(impl_path):
            result["has_code"] = True

    return result


CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec_cache.json")
CACHE_MAX_AGE = 60  # seconds before full refresh


def _load_cache() -> dict:
    """Load the spec cache from disk."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {"timestamp": 0, "mtimes": {}, "results": {}}


def _save_cache(cache: dict):
    """Save the spec cache to disk."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except IOError:
        pass


def scan_all_specs(ready_only: bool = False) -> list:
    """
    Scan all spec files and return quality results.
    
    Uses mtime-based caching to avoid re-reading unchanged files.
    Only files whose modification time changed since last scan are re-read.
    Full refresh forced every CACHE_MAX_AGE seconds.
    """
    cache = _load_cache()
    now = time.time()
    force_refresh = (now - cache.get("timestamp", 0)) > CACHE_MAX_AGE
    
    spec_files = sorted(Path(SPECS_DIR).glob("*_spec.md"))
    results = []
    cache_hits = 0
    cache_misses = 0
    
    for spec_path in spec_files:
        path_str = str(spec_path)
        try:
            mtime = os.path.getmtime(path_str)
        except OSError:
            continue
        
        cached_mtime = cache.get("mtimes", {}).get(path_str, 0)
        
        if not force_refresh and mtime == cached_mtime and path_str in cache.get("results", {}):
            # Cache hit — use stored result
            result = cache["results"][path_str]
            cache_hits += 1
        else:
            # Cache miss — re-read and re-check
            result = check_spec(path_str)
            cache.setdefault("results", {})[path_str] = result
            cache.setdefault("mtimes", {})[path_str] = mtime
            cache_misses += 1
        
        if ready_only and result.get("status") != "ready":
            continue
        results.append(result)
    
    # Save updated cache
    cache["timestamp"] = now
    _save_cache(cache)
    
    if cache_misses > 0:
        logger.debug(f"Spec cache: {cache_hits} hits, {cache_misses} misses")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Spec Quality Gate")
    parser.add_argument("task_id", nargs="?", help="Check specific task ID")
    parser.add_argument("--ready-only", action="store_true", help="Only show ready specs")
    parser.add_argument("--skeleton-only", action="store_true", help="Only show skeleton (unenriched) specs")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.task_id:
        spec_path = os.path.join(SPECS_DIR, f"{args.task_id}_spec.md")
        result = check_spec(spec_path)
        results = [result]
    else:
        results = scan_all_specs(ready_only=args.ready_only)
        if args.skeleton_only:
            results = [r for r in results if r["pass_status"] == "skeleton"]

    # Summary
    ready = sum(1 for r in results if r["status"] == "ready")
    review = sum(1 for r in results if r["status"] == "needs_review")
    incomplete = sum(1 for r in results if r["status"] == "incomplete")
    skeleton = sum(1 for r in results if r["pass_status"] == "skeleton")
    enriched = sum(1 for r in results if r["pass_status"] == "enriched")
    has_code = sum(1 for r in results if r["has_code"])

    if args.json:
        import json
        print(json.dumps({"results": results, "summary": {
            "total": len(results), "ready": ready, "needs_review": review,
            "incomplete": incomplete, "skeleton": skeleton, "enriched": enriched,
            "has_code": has_code,
        }}, indent=2))
        return

    # Pretty print
    status_emoji = {"ready": "✅", "needs_review": "⚠️ ", "incomplete": "❌", "missing": "💀"}
    pass_emoji = {"skeleton": "📝", "enriched": "📖"}

    for r in results:
        emoji = status_emoji.get(r["status"], "?")
        pe = pass_emoji.get(r["pass_status"], "?")
        code_tag = " [HAS CODE]" if r["has_code"] else ""
        issues = f" — {'; '.join(r['issues'])}" if r["issues"] else ""
        print(f"  {emoji}{pe} {r['task_id']}{code_tag}{issues}")

    print(f"\n  📊 Total: {len(results)} | ✅ Ready: {ready} | ⚠️  Review: {review} | ❌ Incomplete: {incomplete}")
    print(f"  📝 Skeleton (1st pass): {skeleton} | 📖 Enriched (2nd pass): {enriched} | 🔧 Has code: {has_code}")


if __name__ == "__main__":
    main()
