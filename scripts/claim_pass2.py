#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path

# Path to the BOARD.md file
BOARD_PATH = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md")

# Function to find the next pending task
def find_next_pending_task():
    if not BOARD_PATH.exists():
        return None
    
    with open(BOARD_PATH, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if line.startswith("| 🟦 IN PROGRESS ("):
            # Extract the agent name
            agent_name = line.split("(")[1].split(")")[0].strip()
            # Check if the agent is still active
            if agent_name == "desktop-roo":
                return i
    
    return None

# Main execution
if __name__ == "__main__":
    task_index = find_next_pending_task()
    if task_index is None:
        print("No pending tasks found")
        sys.exit(1)
    
    # Update the BOARD.md file
    with open(BOARD_PATH, 'r+') as f:
        lines = f.readlines()
        lines[task_index] = "| 🟩 COMPLETING PASS 2 | desktop-roo | " + lines[task_index].split("|")[2] + "\n"
        f.seek(0)
        f.writelines(lines)
        f.truncate()
    
    print(f"Task {task_index} claimed successfully")
    sys.exit(0)