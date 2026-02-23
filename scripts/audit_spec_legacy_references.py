#!/usr/bin/env python3
"""
Spec Legacy Reference Auditor

This script audits all specification documents to ensure they contain
comprehensive legacy references to the vjlive/ and VJlive-2/ codebases.

It generates a report showing:
- Which specs have adequate legacy references
- Which specs are missing legacy references
- Which specs need enhancement
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Constants
BOARD_PATH = Path("BOARD.md")
SPECS_DIR = Path("docs/specs")
LEGACY_CODEBASES = ["vjlive/", "VJlive-2/"]

def parse_board_tasks() -> Dict[str, dict]:
    """Parse BOARD.md to extract all task IDs, status, and spec references."""
    tasks = {}
    board_content = BOARD_PATH.read_text()
    
    # Pattern to match task rows in the markdown table
    # Format: | P0-G1 | WORKSPACE/PRIME_DIRECTIVE.md | P0 | ✅ Done | |
    pattern = r'\|\s*(P[\d]-[A-Z0-9_-]+)\s*\|\s*[^|]*\s*\|\s*[^|]*\s*\|\s*([^|]*)\s*\|'
    
    for match in re.finditer(pattern, board_content):
        task_id = match.group(1)
        status_raw = match.group(2).strip()
        
        # Determine status
        if "✅ Done" in status_raw:
            status = "Done"
        elif "⬜ Todo" in status_raw:
            status = "Todo"
        elif "🔄 In Progress" in status_raw:
            status = "In Progress"
        elif "🚫 Out of Scope" in status_raw:
            status = "Out of Scope"
        else:
            status = "Unknown"
        
        tasks[task_id] = {"status": status}
    
    return tasks

def find_spec_for_task(task_id: str) -> Optional[Path]:
    """Find the spec file corresponding to a given task ID."""
    # Normalize task ID for filename matching
    task_id_clean = task_id.lower().replace("_", "-")
    
    # Look for files that contain the task ID (case-insensitive)
    for spec_file in SPECS_DIR.glob("*.md"):
        # Skip template and other non-spec files
        if spec_file.name.startswith("_") or spec_file.name == "plugin_manifest_examples.md":
            continue
            
        # Check if filename contains the task ID
        filename = spec_file.stem.lower()
        if task_id_clean in filename:
            return spec_file
    
    return None

def audit_spec_legacy_references(spec_path: Path) -> dict:
    """Audit a spec file for comprehensive legacy references."""
    content = spec_path.read_text()
    
    # Check for legacy source section
    has_legacy_section = bool(re.search(r'##\s*Legacy Source|Legacy Source|##\s*Legacy|Legacy:', content, re.IGNORECASE))
    
    # Check for specific legacy codebase mentions
    mentions_vjlive = bool(re.search(r'vjlive/', content))
    mentions_vjlive2 = bool(re.search(r'VJlive-2/', content))
    
    # Check for file paths (patterns like `path/to/file.py` or path/to/file.py)
    has_file_paths = bool(re.search(r'`[^`]*\.py`', content))
    
    # Check for class names (Class: or classes)
    has_class_names = bool(re.search(r'Class:|classes:', content, re.IGNORECASE))
    
    # Check for algorithm details (key logic, implementation, etc.)
    has_algorithms = bool(re.search(r'key logic|implementation|algorithm|physics|simulation', content, re.IGNORECASE))
    
    # Check for parameters (parameter, default, range)
    has_parameters = bool(re.search(r'parameter|default|range|constraint', content, re.IGNORECASE))
    
    # Check for edge cases
    has_edge_cases = bool(re.search(r'edge case|error handling|fallback|performance', content, re.IGNORECASE))
    
    # Estimate completeness score
    checks = [
        has_legacy_section,
        mentions_vjlive or mentions_vjlive2,
        has_file_paths,
        has_class_names,
        has_algorithms,
        has_parameters,
        has_edge_cases
    ]
    score = sum(checks) / len(checks) * 100
    
    return {
        "has_legacy_section": has_legacy_section,
        "mentions_vjlive": mentions_vjlive,
        "mentions_vjlive2": mentions_vjlive2,
        "has_file_paths": has_file_paths,
        "has_class_names": has_class_names,
        "has_algorithms": has_algorithms,
        "has_parameters": has_parameters,
        "has_edge_cases": has_edge_cases,
        "completeness_score": score
    }

def main():
    """Main audit workflow."""
    print("🔍 Starting Spec Legacy Reference Audit...")
    
    # Parse BOARD.md
    print("📋 Parsing BOARD.md...")
    tasks = parse_board_tasks()
    print(f"   Found {len(tasks)} tasks")
    
    # Count by status
    status_counts = {}
    for task_info in tasks.values():
        status = task_info["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    print(f"   Status: {status_counts}")
    
    # Map tasks to specs
    print("\n🗂️  Mapping tasks to spec files...")
    task_spec_map = {}
    specs_found = 0
    specs_missing = []
    
    for task_id in sorted(tasks.keys()):
        spec_file = find_spec_for_task(task_id)
        if spec_file:
            tasks[task_id]["spec_path"] = spec_file
            task_spec_map[task_id] = spec_file
            specs_found += 1
        else:
            specs_missing.append(task_id)
    
    print(f"   Found spec files for {specs_found} tasks")
    print(f"   Missing spec files for {len(specs_missing)} tasks")
    
    # Audit specs
    print("\n🔬 Auditing spec legacy references...")
    audit_results = {}
    
    for task_id, task_info in tasks.items():
        if "spec_path" not in task_info:
            continue
            
        spec_path = task_info["spec_path"]
        audit = audit_spec_legacy_references(spec_path)
        audit_results[task_id] = {
            "spec_path": str(spec_path),
            "status": task_info["status"],
            "audit": audit
        }
    
    # Generate summary
    print("\n📊 Audit Summary:")
    print(f"   Total specs audited: {len(audit_results)}")
    
    # By status
    for status in ["Done", "Todo", "In Progress", "Unknown"]:
        count = sum(1 for r in audit_results.values() if r["status"] == status)
        if count > 0:
            avg_score = sum(r["audit"]["completeness_score"] for r in audit_results.values() if r["status"] == status) / count
            print(f"   {status}: {count} specs, avg completeness: {avg_score:.1f}%")
    
    # Find specs needing enhancement
    needs_work = {k: v for k, v in audit_results.items() if v["audit"]["completeness_score"] < 100}
    print(f"\n⚠️  Specs needing legacy reference enhancement: {len(needs_work)}")
    
    # Save detailed report
    report_path = Path("docs/spec_legacy_audit_report.json")
    report = {
        "summary": {
            "total_specs": len(audit_results),
            "by_status": status_counts,
            "needs_enhancement": len(needs_work)
        },
        "audit_results": audit_results
    }
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\n📄 Full report saved to: {report_path}")
    
    # List top priority (Done status, low score)
    print("\n🎯 High Priority (Done status, incomplete legacy refs):")
    high_priority = [(tid, r) for tid, r in needs_work.items() if r["status"] == "Done"]
    high_priority.sort(key=lambda x: x[1]["audit"]["completeness_score"])
    
    for task_id, result in high_priority[:20]:  # Show top 20
        score = result["audit"]["completeness_score"]
        spec_name = Path(result["spec_path"]).name
        print(f"   {task_id} ({spec_name}): {score:.0f}% complete")
    
    return audit_results

if __name__ == "__main__":
    main()