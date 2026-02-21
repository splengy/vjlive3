#!/usr/bin/env python3
"""
DELETE_ME Folder Verification Script

This script is run periodically by ROO CODE to review deletion requests.
It scans WORKSPACE/DELETE_ME/ for files marked for deletion and verifies
whether they can be safely deleted.

Usage:
    python scripts/verify_delete_requests.py [--dry-run] [--auto-approve]

Options:
    --dry-run        Only report, don't actually delete or move files
    --auto-approve  Automatically approve deletions that pass all checks
"""

import os
import sys
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
DELETE_ME_DIR = WORKSPACE_ROOT / "WORKSPACE" / "DELETE_ME"
ARCHIVE_DIR = WORKSPACE_ROOT / "WORKSPACE" / "ARCHIVE"
AGENT_SYNC_FILE = WORKSPACE_ROOT / "WORKSPACE" / "COMMS" / "AGENT_SYNC.md"

# Ensure directories exist
DELETE_ME_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def parse_deletion_request(filepath: Path) -> Dict:
    """
    Parse a deletion request file and extract metadata.
    
    Expected naming: <original-name>.deletion-request.<agent>.<timestamp>
    """
    pattern = r'^(.*?)\.deletion-request\.([^.]+)\.(\d{8}-\d{6})$'
    match = re.match(pattern, filepath.name)
    
    if not match:
        return None
    
    original_name = match.group(1)
    agent_name = match.group(2)
    timestamp = match.group(3)
    
    # Read the deletion note
    note_file = filepath.with_name(f"{original_name}.deletion-note.txt")
    note_content = ""
    if note_file.exists():
        note_content = note_file.read_text().strip()
    
    return {
        "filepath": filepath,
        "original_name": original_name,
        "agent_name": agent_name,
        "timestamp": timestamp,
        "note_file": note_file,
        "note_content": note_content,
        "original_location": WORKSPACE_ROOT / original_name
    }


def find_deletion_requests() -> List[Dict]:
    """Find all deletion requests in DELETE_ME directory."""
    requests = []
    
    for filepath in DELETE_ME_DIR.glob("*.deletion-request.*"):
        req = parse_deletion_request(filepath)
        if req:
            requests.append(req)
    
    return sorted(requests, key=lambda x: x["timestamp"])


def verify_deletion_request(req: Dict) -> Tuple[bool, str]:
    """
    Verify if a deletion request is valid.
    
    Returns: (can_delete, reason)
    """
    original_path = req["original_location"]
    
    # Check 1: Does original file exist? (It should, that's why it was moved)
    if not original_path.exists():
        return False, "Original file no longer exists at expected location"
    
    # Check 2: Is file referenced in any critical docs?
    critical_files = [
        "WORKSPACE/PRIME_DIRECTIVE.md",
        "WORKSPACE/ROO_CODE_MANAGER_INSTRUCTIONS.md",
        "WORKSPACE/SAFETY_RAILS.md",
        "WORKSPACE/VERIFICATION_CHECKPOINTS.md",
        "WORKSPACE/COMMS/DISPATCH.md",
        "WORKSPACE/WORKER_MANIFEST.md",
        "BOARD.md"
    ]
    
    for critical_file in critical_files:
        cf_path = WORKSPACE_ROOT / critical_file
        if cf_path.exists() and original_path.relative_to(WORKSPACE_ROOT).as_posix() in cf_path.read_text():
            return False, f"File is referenced in critical document: {critical_file}"
    
    # Check 3: Is file a test file that might be imported?
    if "test_" in original_path.name and original_path.suffix == ".py":
        # Check if any other test files import from this file
        test_dir = original_path.parent
        if test_dir.exists():
            for test_file in test_dir.glob("test_*.py"):
                if test_file != original_path:
                    content = test_file.read_text()
                    if original_path.stem in content:
                        return False, f"Test file may be imported by other tests: {test_file.name}"
    
    # Check 4: Is this a core module file?
    core_dirs = ["src/vjlive3/", "mcp_servers/", "scripts/"]
    is_core = any(str(original_path).startswith(str(WORKSPACE_ROOT / d)) for d in core_dirs)
    if is_core and not req["note_content"]:
        return False, "Core module file has no deletion justification"
    
    # Check 5: Is deletion note adequate?
    if len(req["note_content"].split()) < 5:
        return False, "Deletion note is too brief (minimum 5 words)"
    
    # Check 6: Does note mention task ID?
    if not re.search(r'P\d+-[A-Z0-9]+', req["note_content"]):
        return False, "Deletion note must reference a task ID (e.g., P2-H3)"
    
    return True, "All checks passed"


def approve_deletion(req: Dict, dry_run: bool = False) -> bool:
    """Approve a deletion request and move file to archive."""
    archive_path = ARCHIVE_DIR / f"{req['original_name']}.deleted.{req['timestamp']}"
    
    if dry_run:
        print(f"[DRY RUN] Would archive: {req['original_name']} -> {archive_path.name}")
        return True
    
    try:
        # Move original file to archive
        req["original_location"].rename(archive_path)
        
        # Delete the deletion-note.txt
        if req["note_file"].exists():
            req["note_file"].unlink()
        
        # Delete the deletion-request file
        req["filepath"].unlink()
        
        print(f"✓ Archived: {req['original_name']} -> {archive_path.name}")
        return True
    except Exception as e:
        print(f"✗ Failed to archive {req['original_name']}: {e}")
        return False


def reject_deletion(req: Dict, reason: str, dry_run: bool = False) -> bool:
    """Reject a deletion request and restore file to original location."""
    original_path = req["original_location"]
    
    if dry_run:
        print(f"[DRY RUN] Would reject: {req['original_name']} - {reason}")
        return True
    
    try:
        # Move file back to original location
        req["filepath"].rename(original_path)
        
        # Delete the deletion-note.txt
        if req["note_file"].exists():
            req["note_file"].unlink()
        
        print(f"✗ Rejected: {req['original_name']} - {reason}")
        return True
    except Exception as e:
        print(f"✗ Failed to reject {req['original_name']}: {e}")
        return False


def log_to_agent_sync(action: str, details: str, dry_run: bool = False):
    """Log deletion verification results to AGENT_SYNC.md."""
    if dry_run:
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    try:
        with open(AGENT_SYNC_FILE, "a") as f:
            f.write(f"\n## {timestamp} - Deletion Verification\n")
            f.write(f"- **Action:** {action}\n")
            f.write(f"- **Details:** {details}\n")
            f.write(f"- **Agent:** ROO CODE (Manager)\n")
    except Exception as e:
        print(f"Warning: Could not log to AGENT_SYNC.md: {e}")


def main():
    parser = argparse.ArgumentParser(description="Verify deletion requests in DELETE_ME folder")
    parser.add_argument("--dry-run", action="store_true", help="Only report, don't modify files")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve passing requests")
    args = parser.parse_args()
    
    print("=" * 60)
    print("DELETE_ME VERIFICATION REPORT")
    print("=" * 60)
    
    requests = find_deletion_requests()
    
    if not requests:
        print("No deletion requests found.")
        return 0
    
    print(f"Found {len(requests)} deletion request(s):\n")
    
    approved = 0
    rejected = 0
    
    for req in requests:
        print(f"File: {req['original_name']}")
        print(f"  Requested by: {req['agent_name']} at {req['timestamp']}")
        print(f"  Justification: {req['note_content'][:100]}...")
        
        can_delete, reason = verify_deletion_request(req)
        
        if can_delete:
            print(f"  ✓ Verification: PASSED - {reason}")
            if args.auto_approve and not args.dry_run:
                if approve_deletion(req, dry_run=args.dry_run):
                    approved += 1
                    log_to_agent_sync("Deletion Approved", f"{req['original_name']} - {reason}")
            else:
                print(f"  → Ready for approval (use --auto-approve to approve)")
                if args.dry_run:
                    approved += 1
        else:
            print(f"  ✗ Verification: FAILED - {reason}")
            if not args.dry_run:
                if reject_deletion(req, reason, dry_run=args.dry_run):
                    rejected += 1
                    log_to_agent_sync("Deletion Rejected", f"{req['original_name']} - {reason}")
            else:
                rejected += 1
        
        print()
    
    print("=" * 60)
    print(f"Summary: {approved} approved, {rejected} rejected, {len(requests)} total")
    print("=" * 60)
    
    if args.dry_run:
        print("\n[DRY RUN] No files were actually modified.")
    elif not args.auto_approve:
        print("\nNote: Run with --auto-approve to approve passing requests.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())