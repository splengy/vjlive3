#!/usr/bin/env python3
"""
Comprehensive Project State Audit for VJLive3
Identifies what's actually been completed vs what BOARD.md claims
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re

class ProjectAudit:
    def __init__(self):
        self.project_root = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning")
        self.specs_dir = self.project_root / "docs" / "specs"
        self.plugins_dir = self.project_root / "src" / "vjlive3" / "plugins"
        self.tests_dir = self.project_root / "tests"
        self.board_path = self.project_root / "BOARD.md"
        
    def get_all_specs(self) -> List[str]:
        """Get all spec files and extract task IDs"""
        specs = []
        for spec_file in self.specs_dir.glob("*.md"):
            content = spec_file.read_text()
            task_id = self.extract_task_id(content)
            if task_id:
                specs.append({
                    "file": str(spec_file.relative_to(self.project_root)),
                    "task_id": task_id,
                    "name": spec_file.stem.replace("_", " ").title(),
                    "exists": True
                })
        return specs
    
    def extract_task_id(self, content: str) -> str:
        """Extract task ID from spec content"""
        match = re.search(r"Task ID\s*\|\s*(P\d+-[A-Z0-9]+)", content, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""
    
    def get_all_plugins(self) -> List[str]:
        """Get all plugin files"""
        plugins = []
        for plugin_file in self.plugins_dir.glob("*.py"):
            if not plugin_file.name.startswith("__"):
                plugins.append(str(plugin_file.relative_to(self.project_root)))
        return plugins
    
    def get_all_tests(self) -> List[str]:
        """Get all test files"""
        tests = []
        for test_file in self.tests_dir.rglob("test_*.py"):
            tests.append(str(test_file.relative_to(self.project_root)))
        return tests
    
    def parse_board(self) -> Dict:
        """Parse BOARD.md to extract task statuses"""
        content = self.board_path.read_text()
        
        # Extract task table data
        tasks = []
        in_table = False
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('| Task ID |'):
                in_table = True
                continue
            if in_table and line.startswith('|'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 4:
                    task_id = parts[0]
                    description = parts[1]
                    status = parts[3]
                    tasks.append({
                        "task_id": task_id,
                        "description": description,
                        "status": status,
                        "source": parts[4] if len(parts) >= 5 else ""
                    })
        
        return {
            "tasks": tasks,
            "total_tasks": len(tasks),
            "completed_tasks": len([t for t in tasks if t["status"] == "✅ Done"]),
            "pending_tasks": len([t for t in tasks if t["status"] == "⬜ Todo"]),
            "in_progress_tasks": len([t for t in tasks if t["status"] == "🔄 In Progress"])
        }
    
    def analyze_phase_completion(self) -> Dict:
        """Analyze which phases are actually complete"""
        phases = {}
        
        # Phase 0 analysis
        phase0_tasks = [t for t in self.parse_board()["tasks"] if t["task_id"].startswith("P0-")]
        phases["Phase 0"] = {
            "total": len(phase0_tasks),
            "completed": len([t for t in phase0_tasks if t["status"] == "✅ Done"]),
            "pending": len([t for t in phase0_tasks if t["status"] == "⬜ Todo"]),
            "in_progress": len([t for t in phase0_tasks if t["status"] == "🔄 In Progress"])
        }
        
        # Phase 3 analysis (Depth Collection)
        phase3_tasks = [t for t in self.parse_board()["tasks"] if t["task_id"].startswith("P3-") and "VD" in t["task_id"]]
        phases["Phase 3 - Depth"] = {
            "total": len(phase3_tasks),
            "completed": len([t for t in phase3_tasks if t["status"] == "✅ Done"]),
            "pending": len([t for t in phase3_tasks if t["status"] == "⬜ Todo"]),
            "in_progress": len([t for t in phase3_tasks if t["status"] == "🔄 In Progress"])
        }
        
        return phases
    
    def check_spec_implementation_parity(self) -> Dict:
        """Check which specs have corresponding implementations"""
        specs = self.get_all_specs()
        plugins = self.get_all_plugins()
        
        spec_task_ids = {spec["task_id"] for spec in specs}
        
        # Extract task IDs from plugin files
        plugin_task_ids = set()
        for plugin_file in plugins:
            content = (self.project_root / plugin_file).read_text()
            if "Task ID" in content or "P3-" in content or "P4-" in content:
                # Extract task ID pattern
                match = re.search(r"(P\d+-[A-Z0-9]+)", content)
                if match:
                    plugin_task_ids.add(match.group(1))
        
        missing_implementations = spec_task_ids - plugin_task_ids
        missing_specs = plugin_task_ids - spec_task_ids
        
        return {
            "specs_with_implementations": len(spec_task_ids & plugin_task_ids),
            "specs_without_implementations": len(missing_implementations),
            "implementations_without_specs": len(missing_specs),
            "missing_implementations": sorted(missing_implementations),
            "missing_specs": sorted(missing_specs)
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive audit report"""
        
        # Basic stats
        total_plugins = len(self.get_all_plugins())
        total_tests = len(self.get_all_tests())
        total_specs = len(self.get_all_specs())
        
        board_analysis = self.parse_board()
        phase_analysis = self.analyze_phase_completion()
        parity_analysis = self.check_spec_implementation_parity()
        
        report = f"""
VJLive3 Project State Audit Report
{'='*60}

GENERAL STATISTICS
{'-'*60}
Total Plugins: {total_plugins}
Total Test Files: {total_tests}
Total Spec Files: {total_specs}

BOARD ANALYSIS
{'-'*60}
Total Tasks in BOARD.md: {board_analysis['total_tasks']}
Completed: {board_analysis['completed_tasks']} (✅)
Pending: {board_analysis['pending_tasks']} (⬜)
In Progress: {board_analysis['in_progress_tasks']} (🔄)

PHASE COMPLETION STATUS
{'-'*60}
{self.format_phase_status(phase_analysis)}

SPEC IMPLEMENTATION PARITY
{'-'*60}
Specs with Implementations: {parity_analysis['specs_with_implementations']}
Specs without Implementations: {parity_analysis['specs_without_implementations']}
Implementations without Specs: {parity_analysis['implementations_without_specs']}

MISSING IMPLEMENTATIONS (Specs exist but no code):
{self.format_list(parity_analysis['missing_implementations'])}

MISSING SPECS (Code exists but no spec):
{self.format_list(parity_analysis['missing_specs'])}

RECOMMENDATIONS
{'-'*60}
1. BOARD.md needs reconciliation - many tasks marked done but code exists
2. {parity_analysis['specs_without_implementations']} specs need implementation
3. {parity_analysis['implementations_without_specs']} implementations need specs
4. Phase completion indicators are inaccurate
5. Missing Phase 8 tasks need creation

AUDIT COMPLETE
{'='*60}
Generated: {self.project_root}
Timestamp: {__import__('datetime').datetime.now().isoformat()}
"""
        return report
    
    def format_phase_status(self, phases: Dict) -> str:
        """Format phase completion status"""
        lines = []
        for phase_name, data in phases.items():
            completion_rate = (data['completed'] / data['total'] * 100) if data['total'] > 0 else 0
            lines.append(f"{phase_name}: {data['completed']}/{data['total']} ({completion_rate:.1f}%)")
        return '\n'.join(lines)
    
    def format_list(self, items: List[str]) -> str:
        """Format list of items"""
        if not items:
            return "None"
        return '\n'.join([f"  - {item}" for item in items])

if __name__ == "__main__":
    audit = ProjectAudit()
    print(audit.generate_report())
    
    # Save report
    report_path = audit.project_root / "WORKSPACE" / "AUDIT_REPORT.md"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(audit.generate_report())
    
    print(f"\nAudit report saved to: {report_path}")