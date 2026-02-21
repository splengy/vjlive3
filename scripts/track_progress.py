#!/usr/bin/env python3
"""
Autonomous Progress Tracker

Automated progress tracking for autonomous agents.
Maintains progress logs and triggers sanity checks.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

PROGRESS_LOG = Path("WORKSPACE/PROGRESS_LOG.md")

def initialize_progress_log(phase_name: str) -> None:
    """Initialize a new progress log for a phase."""
    PROGRESS_LOG.parent.mkdir(exist_ok=True)
    
    content = f"""# Progress Log: {phase_name}

## Phase Status: In Progress

### Timeline
- **Start**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Last Update**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Expected Completion**: TBD

### Tasks Completed
(No tasks completed yet)

### Current Task
- **Task**: Initializing phase
- **Progress**: 0%
- **Blockers**: None

### Sanity Check Results
- [ ] Performance Sanity: Not run
- [ ] Test Coverage: Not run
- [ ] Code Quality: Not run
- [ ] Security Scan: Not run
- [ ] Integration Test: Not run

### Performance Metrics
- **FPS**: N/A
- **Memory**: N/A
- **CPU**: N/A
- **Test Coverage**: N/A

---
**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Agent**: Autonomous Agent
"""
    
    PROGRESS_LOG.write_text(content)
    print(f"✅ Initialized progress log: {PROGRESS_LOG}")

def update_progress(
    task_name: str,
    status: str,
    progress_pct: int = None,
    blockers: List[str] = None,
    performance_metrics: Dict[str, Any] = None,
    sanity_checks: Dict[str, bool] = None
) -> None:
    """Update the progress log with current status."""
    
    if not PROGRESS_LOG.exists():
        print("⚠️  Progress log not found. Run initialize_progress_log first.")
        return
    
    content = PROGRESS_LOG.read_text()
    lines = content.split('\n')
    
    # Update last update timestamp
    for i, line in enumerate(lines):
        if line.strip().startswith('**Last Updated**'):
            lines[i] = f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            break
    
    # Update current task
    in_current_task = False
    for i, line in enumerate(lines):
        if line.strip().startswith('### Current Task'):
            in_current_task = True
        elif in_current_task and line.strip().startswith('- **Task**'):
            lines[i] = f"- **Task**: {task_name}"
        elif in_current_task and line.strip().startswith('- **Progress**') and progress_pct:
            lines[i] = f"- **Progress**: {progress_pct}%"
        elif in_current_task and line.strip().startswith('- **Blockers**'):
            blockers_list = blockers or ['None']
            lines[i] = f"- **Blockers**: {', '.join(blockers_list)}"
    
    # Add completed task to tasks completed section
    tasks_completed_idx = None
    for i, line in enumerate(lines):
        if line.strip() == '### Tasks Completed':
            tasks_completed_idx = i + 1
            break
    
    if tasks_completed_idx:
        completion_entry = f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {task_name} - {status}"
        lines.insert(tasks_completed_idx, completion_entry)
    
    # Update performance metrics if provided
    if performance_metrics:
        in_performance = False
        for i, line in enumerate(lines):
            if line.strip() == '### Performance Metrics':
                in_performance = True
            elif in_performance and line.strip().startswith('- **FPS**'):
                lines[i] = f"- **FPS**: {performance_metrics.get('FPS', 'N/A')}"
            elif in_performance and line.strip().startswith('- **Memory**'):
                lines[i] = f"- **Memory**: {performance_metrics.get('Memory', 'N/A')}"
            elif in_performance and line.strip().startswith('- **CPU**'):
                lines[i] = f"- **CPU**: {performance_metrics.get('CPU', 'N/A')}"
            elif in_performance and line.strip().startswith('- **Test Coverage**'):
                lines[i] = f"- **Test Coverage**: {performance_metrics.get('coverage', 'N/A')}%"
    
    # Update sanity checks if provided
    if sanity_checks:
        in_sanity = False
        for i, line in enumerate(lines):
            if line.strip() == '### Sanity Check Results':
                in_sanity = True
            elif in_sanity and line.strip().startswith('- ['):
                # Update existing sanity check entries
                for check, result in sanity_checks.items():
                    if check in line:
                        status = "✅ PASS" if result else "❌ FAIL"
                        lines[i] = f"- [x] {check}: {status}"
    
    PROGRESS_LOG.write_text('\n'.join(lines))
    print(f"✅ Updated progress log: {PROGRESS_LOG}")

def mark_phase_complete(phase_name: str) -> None:
    """Mark a phase as complete."""
    if not PROGRESS_LOG.exists():
        print("⚠️  Progress log not found.")
        return
    
    content = PROGRESS_LOG.read_text()
    content = content.replace('## Phase Status: In Progress', '## Phase Status: COMPLETE')
    
    PROGRESS_LOG.write_text(content)
    print(f"✅ Phase '{phase_name}' marked as complete")

def main():
    if len(sys.argv) < 2:
        print("Usage: track_progress.py <command> [args...]")
        print("Commands:")
        print("  init <phase_name>")
        print("  update <task_name> <status> [progress_pct]")
        print("  complete")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        if len(sys.argv) < 3:
            print("Error: phase_name required")
            sys.exit(1)
        initialize_progress_log(sys.argv[2])
    
    elif command == "update":
        if len(sys.argv) < 4:
            print("Error: task_name and status required")
            sys.exit(1)
        
        task_name = sys.argv[2]
        status = sys.argv[3]
        progress_pct = int(sys.argv[4]) if len(sys.argv) > 4 else None
        
        # Try to read JSON data from stdin for additional parameters
        try:
            data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
        except:
            data = {}
        
        update_progress(
            task_name=task_name,
            status=status,
            progress_pct=progress_pct,
            blockers=data.get('blockers'),
            performance_metrics=data.get('performance_metrics'),
            sanity_checks=data.get('sanity_checks')
        )
    
    elif command == "complete":
        mark_phase_complete("Current Phase")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())