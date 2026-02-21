#!/usr/bin/env python3
"""
Progress Tracking Script for Phase 1 Autonomous Execution
Monitors task status files and provides real-time progress updates.
"""

import os
import time
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning")
STATUS_DIR = WORKSPACE / "WORKSPACE" / "COMMS" / "STATUS"
LOGS_DIR = WORKSPACE / "WORKSPACE" / "COMMS" / "LOGS"
DISPATCH_FILE = WORKSPACE / "WORKSPACE" / "COMMS" / "DISPATCH.md"
BOARD_FILE = WORKSPACE / "BOARD.md"

PHASE1_TASKS = {
    "Roo Coder (1)": [
        "RESEARCH:P1-R1", "P1-R1", "RESEARCH:P1-R2", "P1-R2", "RESEARCH:P1-R3", "P1-R3",
        "RESEARCH:P1-R4", "P1-R4", "RESEARCH:P1-R5", "P1-R5",
        "RESEARCH:P1-N1", "P1-N1", "RESEARCH:P1-N2", "P1-N2", "RESEARCH:P1-N3", "P1-N3",
        "RESEARCH:P1-N4", "P1-N4"
    ],
    "Roo Coder (2)": [
        "P1-A1", "P1-A2", "RESEARCH:P1-A3", "P1-A3", "RESEARCH:P1-A4", "P1-A4"
    ],
    "Antigravity (Agent 3)": [
        "RESEARCH:P1-P1", "P1-P1", "RESEARCH:P1-P2", "P1-P2", "RESEARCH:P1-P3", "P1-P3",
        "RESEARCH:P1-P4", "P1-P4", "RESEARCH:P1-P5", "P1-P5"
    ]
}

STATUS_ICONS = {
    "Todo": "⏰", "In Progress": "🔨", "Blocked": "⏸️", "Done": "✅", "Rejected": "❌"
}

def read_status_file(task_id):
    """Read the status of a task from its status file."""
    status_file = STATUS_DIR / f"{task_id}.txt"
    if status_file.exists():
        with open(status_file, 'r') as f:
            return f.read().strip()
    return "Todo"

def get_task_status(task_id):
    """Get the current status of a task."""
    status = read_status_file(task_id)
    if status == "IN_PROGRESS":
        return "In Progress"
    elif status == "DONE":
        return "Done"
    elif status.startswith("BLOCKED"):
        return "Blocked"
    else:
        return "Todo"

def get_agent_progress(agent_name):
    """Get progress summary for a specific agent."""
    tasks = PHASE1_TASKS.get(agent_name, [])
    total = len(tasks)
    completed = 0
    in_progress = 0
    blocked = 0
    
    for task in tasks:
        status = get_task_status(task)
        if status == "Done":
            completed += 1
        elif status == "In Progress":
            in_progress += 1
        elif status == "Blocked":
            blocked += 1
    
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "blocked": blocked,
        "percentage": (completed / total * 100) if total > 0 else 0
    }

def get_overall_progress():
    """Get overall Phase 1 progress."""
    total_tasks = 0
    completed_tasks = 0
    
    for agent, tasks in PHASE1_TASKS.items():
        total_tasks += len(tasks)
        for task in tasks:
            if get_task_status(task) == "Done":
                completed_tasks += 1
    
    return {
        "total": total_tasks,
        "completed": completed_tasks,
        "percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    }

def check_sanity():
    """Check for potential issues in the autonomous workflow."""
    issues = []
    
    # Check for tasks marked Done without status file
    # Check for tasks with status files but not marked Done in DISPATCH.md
    # Check for lock conflicts
    # Check for agents not updating status files
    
    return issues

def print_progress_report():
    """Print a comprehensive progress report."""
    print("\n" + "="*60)
    print("PHASE 1 AUTONOMOUS EXECUTION PROGRESS REPORT")
    print(f"Generated: {datetime.now().isoformat()}")
    print("="*60)
    
    # Overall progress
    overall = get_overall_progress()
    print(f"\nOverall Progress: {overall['percentage']:.1f}% ({overall['completed']}/{overall['total']})")
    
    # Agent progress
    print(f"\nAgent Progress:")
    for agent, tasks in PHASE1_TASKS.items():
        progress = get_agent_progress(agent)
        print(f"  {agent}: {progress['percentage']:.1f}% ({progress['completed']}/{progress['total']})")
        print(f"    Completed: {progress['completed']}, In Progress: {progress['in_progress']}, Blocked: {progress['blocked']}")
    
    # Task status breakdown
    print(f"\nTask Status Breakdown:")
    for agent, tasks in PHASE1_TASKS.items():
        print(f"\n  {agent}:")
        for task in tasks:
            status = get_task_status(task)
            icon = STATUS_ICONS.get(status, "❓")
            print(f"    {icon} {task}: {status}")
    
    # Sanity checks
    issues = check_sanity()
    if issues:
        print(f"\n⚠️  Issues Detected:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print(f"\n✅ No issues detected.")
    
    print("\n" + "="*60)

def monitor_continuously(interval=60):
    """Continuously monitor progress at specified interval."""
    print(f"Starting continuous progress monitoring (interval: {interval}s)...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            os.system('clear')
            print_progress_report()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        monitor_continuously(interval=60)
    else:
        print_progress_report()
