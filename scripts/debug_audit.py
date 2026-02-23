#!/usr/bin/env python3
"""
Debug script to understand the audit report structure.
"""

import json
from pathlib import Path

audit_report_path = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/docs/spec_legacy_audit_report.json")

with open(audit_report_path, 'r', encoding='utf-8') as f:
    audit_report = json.load(f)

print("Audit report keys:", audit_report.keys())
print("\nSample entries:")

for i, (task_id, task_data) in enumerate(audit_report.get('audit_results', {}).items()):
    if i >= 5:
        break
    print(f"\nTask ID: {task_id}")
    print(f"  spec_path: {task_data.get('spec_path')}")
    print(f"  spec_filename: {task_data.get('spec_filename')}")
    print(f"  status: {task_data.get('status')}")
    audit = task_data.get('audit', {})
    print(f"  has_file_paths: {audit.get('has_file_paths')}")
    print(f"  has_class_names: {audit.get('has_class_names')}")
    print(f"  completeness_score: {audit.get('completeness_score')}")

# Count specs that need enhancement
needs_enhancement = 0
for task_id, task_data in audit_report.get('audit_results', {}).items():
    audit = task_data.get('audit', {})
    if audit.get('has_file_paths') and audit.get('has_class_names'):
        continue
    needs_enhancement += 1

print(f"\nTotal specs needing enhancement: {needs_enhancement}")
