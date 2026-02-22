#!/usr/bin/env python3
"""
VJLive3 Legacy Parity Test
Parses the authoritative BOARD.md feature matrix to compute the parity percentage
between the legacy applications (VJlive, VJlive-2) and VJLive3.
"""

import sys
import os
import re

def run_parity_test():
    board_path = os.path.join(os.path.dirname(__file__), "..", "BOARD.md")
    if not os.path.exists(board_path):
        print(f"Error: Could not find {board_path}")
        sys.exit(1)

    with open(board_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all table rows that look like tasks
    # Format typically: | P1-R1 | Description | P0 | ✅ Done | Source |
    
    phases = {}
    current_phase = "Unknown Phase"
    
    total_tasks = 0
    done_tasks = 0
    in_progress = 0
    todo = 0

    lines = content.split('\n')
    for line in lines:
        if line.startswith('## Phase'):
            current_phase = line.split(':', 1)[0].replace('## ', '').strip()
            if current_phase not in phases:
                phases[current_phase] = {'total': 0, 'done': 0, 'in_progress': 0, 'todo': 0}
        
        if line.strip().startswith('| P') and '|' in line:
            # It's a task row
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                status = ""
                for p in parts:
                    if 'Done' in p or '✅' in p:
                        status = 'done'
                        break
                    elif 'Progress' in p or '🔄' in p:
                        status = 'in_progress'
                        break
                    elif 'Todo' in p or '⬜' in p:
                        status = 'todo'
                        break
                
                # Exclude Phase 8 internal project management tasks from "legacy parity" metrics
                if current_phase == "Phase 8":
                    continue
                    
                total_tasks += 1
                phases[current_phase]['total'] += 1
                
                if status == 'done':
                    done_tasks += 1
                    phases[current_phase]['done'] += 1
                elif status == 'in_progress':
                    in_progress += 1
                    phases[current_phase]['in_progress'] += 1
                elif status == 'todo':
                    todo += 1
                    phases[current_phase]['todo'] += 1

    print("============================================================")
    print("           VJLive3 vs Legacy Parity Test Report             ")
    print("============================================================")
    
    for phase_name, counts in phases.items():
        if phase_name == "Unknown Phase" or phase_name == "Phase 8":
            continue
        total = counts['total']
        if total == 0:
            continue
            
        done = counts['done']
        pct = (done / total) * 100
        print(f"{phase_name:<15} | Parity: {pct:5.1f}% | Done: {done:<3} / {total:<3} | Remaining: {counts['todo'] + counts['in_progress']}")
    
    print("------------------------------------------------------------")
    if total_tasks > 0:
        overall_pct = (done_tasks / total_tasks) * 100
        print(f"OVERALL PARITY  |         {overall_pct:5.1f}% | Done: {done_tasks:<3} / {total_tasks:<3} | Remaining: {todo + in_progress}")
    else:
        print("OVERALL PARITY  |          0.0% | Done: 0   / 0   | Remaining: 0")
    print("============================================================")

    # Output machine readable metrics
    if total_tasks > 0:
        if overall_pct >= 100.0:
            print("\n✅ VJLive3 has achieved 100% feature parity with legacy apps.")
        elif overall_pct >= 80.0:
            print("\n⚠️ VJLive3 is in late-stage parity convergence.")
        else:
            print("\n❌ VJLive3 parity is incomplete. Further ports required.")

if __name__ == "__main__":
    run_parity_test()
