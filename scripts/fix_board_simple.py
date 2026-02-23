#!/usr/bin/env python3
"""Simple direct fix for BOARD.md - no regex, just direct replacement."""

import re

def read_board():
    with open('BOARD.md', 'r') as f:
        return f.read()

def write_board(content):
    with open('BOARD.md', 'w') as f:
        f.write(content)
    print("BOARD.md written successfully")

def parse_task_summary():
    """Parse the task generation summary into structured data."""
    with open('docs/task_generation_summary.md', 'r') as f:
        content = f.read()
    
    tasks = {
        'phase3': [],
        'phase4': [],
        'phase5_dm': [],
        'phase5_mo': [],
        'phase5_ve': [],
        'phase6_ge': [],
        'phase6_p3': [],
        'phase6_qc': [],
        'phase7_ve': []
    }
    
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('## Phase '):
            phase = stripped.split('## Phase ')[1].split(':')[0].strip()
            current_phase = phase.lower().replace(' ', '_')
        elif stripped.startswith('- ') and ':' in stripped:
            # Extract task ID, description, and class
            parts = stripped[2:].split(':', 1)
            if len(parts) == 2:
                tid = parts[0].strip()
                rest = parts[1].strip()
                # Check if there's a class in parentheses
                if '(' in rest and rest.endswith(')'):
                    # Find the last '(' to split description and class
                    idx = rest.rfind('(')
                    desc = rest[:idx].strip()
                    cls = rest[idx+1:-1].strip()
                else:
                    desc = rest
                    cls = ''
                
                if tid.startswith('P3-'):
                    tasks['phase3'].append((tid, desc, cls))
                elif tid.startswith('P4-'):
                    tasks['phase4'].append((tid, desc, cls))
                elif tid.startswith('P5-DM'):
                    tasks['phase5_dm'].append((tid, desc, cls))
                elif tid == 'P5-MO03':
                    tasks['phase5_mo'].append((tid, desc, cls))
                elif tid == 'P5-VE02':
                    tasks['phase5_ve'].append((tid, desc, cls))
                elif tid.startswith('P6-GE'):
                    tasks['phase6_ge'].append((tid, desc, cls))
                elif tid.startswith('P6-P3'):
                    tasks['phase6_p3'].append((tid, desc, cls))
                elif tid.startswith('P6-QC'):
                    tasks['phase6_qc'].append((tid, desc, cls))
                elif tid.startswith('P7-VE'):
                    tasks['phase7_ve'].append((tid, desc, cls))
    
    return tasks

def generate_row(tid, desc, cls, priority="P0", status="◯ Todo", source="VJlive-2"):
    """Generate a table row."""
    if cls:
        desc = f"{desc} ({cls})"
    return f"| {tid} | {desc} | {priority} | {status} | {source} |"

def generate_table(task_list, priority="P0", status="◯ Todo", source="VJlive-2"):
    """Generate a complete table from a task list."""
    rows = []
    for tid, desc, cls in sorted(task_list, key=lambda x: x[0]):
        rows.append(generate_row(tid, desc, cls, priority, status, source))
    return "\n".join(rows)

def fix_phase3(board, tasks):
    """Replace Phase 3 section with correct tasks."""
    # Find the start of Phase 3
    phase3_start = board.find("### 3A — Missing Depth Plugins")
    if phase3_start == -1:
        print("Phase 3 section not found")
        return board
    
    # Find the end of Phase 3 (next "---" or next "## Phase")
    phase3_end = board.find("---", phase3_start + 100)
    if phase3_end == -1:
        phase3_end = board.find("## Phase 4:", phase3_start)
    
    if phase3_end == -1:
        print("Could not find end of Phase 3")
        return board
    
    # Build new Phase 3 section
    phase3_header = "### 3A — Missing Depth Plugins (from vjlive/vdepth/ — audit individually, every plugin is unique)\n\n| Task ID | Description | Priority | Status |\n|---------|-------------|----------|--------|\n"
    
    # Add the new tasks (only the ones from the audit, not the old done ones)
    new_tasks = []
    for tid, desc, cls in sorted(tasks['phase3'], key=lambda x: x[0]):
        new_tasks.append(generate_row(tid, desc, cls, "P0", "◯ Todo"))
    
    # Add the already done tasks (Beta and some others)
    done_tasks = [
        "| P3-VD7 | Depth Data Mux | P1 | ✅ Done | `src/vjlive3/plugins/depth_data_mux.py` — DepthDataMuxEffect, 6/6 tests ✅ 2026-02-22 |",
        "| P3-VD-Beta1 | Depth Loop Injection | P0 | ✅ Done | `src/vjlive3/plugins/depth_loop_injection.py` — DepthLoopInjectionPlugin, 9/9 tests ✅ 2026-02-22 |",
        "| P3-VD-Beta2 | Depth Parallel Universe | P0 | ✅ Done | `src/vjlive3/plugins/depth_parallel_universe.py` — DepthParallelUniversePlugin, 9/9 tests ✅ 2026-02-22 |",
        "| P3-VD-Beta3 | Depth Portal Composite | P0 | ✅ Done | `src/vjlive3/plugins/depth_portal_composite.py` — DepthPortalCompositePlugin, 9/9 tests ✅ 2026-02-22 |",
        "| P3-VD-Beta4 | Depth Neural Quantum Hyper Tunnel | P0 | ✅ Done | `src/vjlive3/plugins/quantum_hyper_tunnel.py` — DepthNeuralQuantumHyperTunnelPlugin, 6/6 tests ✅ 2026-02-22 |",
        "| P3-VD-Beta5 | Depth Reality Distortion | P0 | ✅ Done | `src/vjlive3/plugins/reality_distortion.py` — RealityDistortionPlugin, 5/5 tests ✅ 2026-02-22 |",
        "| P3-VD33 | Depth Distance Filter | P0 | ✅ Done | `src/vjlive3/plugins/depth_distance_filter.py` — DepthDistanceFilterPlugin, 9/9 tests ✅ 2026-02-22 |",
        "| P3-VD34 | Depth Dual | P0 | ✅ Done | `src/vjlive3/plugins/depth_dual.py` — DepthDualPlugin, 9/9 tests ✅ 2026-02-22 |",
        "| P3-VD35 | Depth Edge Glow | P0 | ✅ Done | `src/vjlive3/plugins/depth_edge_glow.py` — DepthEdgeGlowPlugin, 8/8 tests ✅ 2026-02-22 |",
        "| P3-VD36 | Depth Effects | P0 | ✅ Done | `src/vjlive3/plugins/depth_effect.py` — DepthEffectPlugin, 8/8 tests ✅ 2026-02-22 |",
    ]
    
    # Combine: new tasks first, then done tasks
    all_rows = new_tasks + done_tasks
    
    phase3_section = phase3_header + "\n".join(all_rows) + "\n\n"
    
    # Replace the section
    new_board = board[:phase3_start] + phase3_section + board[phase3_end:]
    return new_board

def fix_phase5(board, tasks):
    """Replace Phase 5 sections with correct tasks."""
    # Fix 5A - Modulators
    section_5A = f"""### 5A — Modulators (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{generate_table(tasks['phase5_mo'], "P0", "◯ Todo", "VJlive-2")}

"""
    
    # Fix 5B - V-* Visual Effects
    section_5B = f"""### 5B — V-* Visual Effects (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{generate_table(tasks['phase5_ve'], "P0", "◯ Todo", "VJlive-2")}

"""
    
    # Fix 5D - Datamosh Family
    section_5D = f"""### 5D — Datamosh Family (verify both sources, keep VJlive-2's cleaner impl)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{generate_table(tasks['phase5_dm'], "P0", "◯ Todo", "VJlive-2")}

"""
    
    # Find and replace 5A
    pattern_5A_start = board.find("### 5A — Modulators (MISSING from VJlive-2)")
    if pattern_5A_start != -1:
        pattern_5A_end = board.find("### 5B", pattern_5A_start + 100)
        if pattern_5A_end == -1:
            pattern_5A_end = board.find("### 5C", pattern_5A_start + 100)
        if pattern_5A_end != -1:
            board = board[:pattern_5A_start] + section_5A + board[pattern_5A_end:]
    
    # Find and replace 5B
    pattern_5B_start = board.find("### 5B — V-* Visual Effects (MISSING from VJlive-2)")
    if pattern_5B_start != -1:
        pattern_5B_end = board.find("### 5C", pattern_5B_start + 100)
        if pattern_5B_end == -1:
            pattern_5B_end = board.find("### 5D", pattern_5B_start + 100)
        if pattern_5B_end != -1:
            board = board[:pattern_5B_start] + section_5B + board[pattern_5B_end:]
    
    # Find and replace 5D
    pattern_5D_start = board.find("### 5D — Datamosh Family")
    if pattern_5D_start != -1:
        pattern_5D_end = board.find("**Phase 5 Gate:**", pattern_5D_start + 100)
        if pattern_5D_end != -1:
            # Find the end of the gate line
            pattern_5D_end = board.find("\n", pattern_5D_end + 100)
            if pattern_5D_end != -1:
                board = board[:pattern_5D_start] + section_5D + board[pattern_5D_end:]
    
    return board

def fix_phase6(board, tasks):
    """Replace Phase 6 sections with correct tasks."""
    # Build 6B - Quantum Consciousness
    section_6B = f"""### 6B — Quantum Consciousness (VJlive-2 leads)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{generate_table(tasks['phase6_qc'], "P0", "◯ Todo", "VJlive-2")}

"""
    
    # Build 6D - Generators
    section_6D = f"""### 6D — Generators (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{generate_table(tasks['phase6_ge'], "P0", "◯ Todo", "VJlive-2")}

"""
    
    # Build 6E - Particle/3D Systems
    section_6E = f"""### 6E — Particle/3D Systems (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{generate_table(tasks['phase6_p3'], "P0", "◯ Todo", "VJlive-2")}

"""
    
    # Find and replace 6B
    pattern_6B_start = board.find("### 6B — Quantum Consciousness")
    if pattern_6B_start != -1:
        pattern_6B_end = board.find("### 6C", pattern_6B_start + 100)
        if pattern_6B_end == -1:
            pattern_6B_end = board.find("### 6D", pattern_6B_start + 100)
        if pattern_6B_end != -1:
            board = board[:pattern_6B_start] + section_6B + board[pattern_6B_end:]
    
    # Find and replace 6D
    pattern_6D_start = board.find("### 6D — Generators")
    if pattern_6D_start != -1:
        pattern_6D_end = board.find("### 6E", pattern_6D_start + 100)
        if pattern_6D_end == -1:
            pattern_6D_end = board.find("### 7", pattern_6D_start + 100)
        if pattern_6D_end != -1:
            board = board[:pattern_6D_start] + section_6D + board[pattern_6D_end:]
    
    # Find and replace 6E
    pattern_6E_start = board.find("### 6E — Particle/3D Systems")
    if pattern_6E_start != -1:
        pattern_6E_end = board.find("### 7", pattern_6E_start + 100)
        if pattern_6E_end != -1:
            board = board[:pattern_6E_start] + section_6E + board[pattern_6E_end:]
    
    return board

def fix_phase7(board, tasks):
    """Replace Phase 7C section with correct tasks."""
    # Build 7C - Additional Effects
    section_7C = f"""### 7C — Additional Effects & Utilities (VJlive-2 + vjlive synthesis)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{generate_table(tasks['phase7_ve'], "P0", "◯ Todo", "VJlive-2")}

"""
    
    # Find 7C section
    pattern_7C_start = board.find("### 7C — Additional Effects")
    if pattern_7C_start != -1:
        pattern_7C_end = board.find("### 7B", pattern_7C_start + 100)
        if pattern_7C_end == -1:
            pattern_7C_end = board.find("### Phase 8", pattern_7C_start + 100)
        if pattern_7C_end != -1:
            board = board[:pattern_7C_start] + section_7C + board[pattern_7C_end:]
    
    return board

def main():
    print("Reading BOARD.md...")
    board = read_board()
    
    print("Parsing task summary...")
    tasks = parse_task_summary()
    print(f"Loaded tasks: Phase3={len(tasks['phase3'])}, Phase4={len(tasks['phase4'])}, Phase5_DM={len(tasks['phase5_dm'])}, Phase5_MO={len(tasks['phase5_mo'])}, Phase5_VE={len(tasks['phase5_ve'])}")
    print(f"Phase6_GE={len(tasks['phase6_ge'])}, Phase6_P3={len(tasks['phase6_p3'])}, Phase6_QC={len(tasks['phase6_qc'])}, Phase7_VE={len(tasks['phase7_ve'])}")
    
    print("Fixing Phase 3...")
    board = fix_phase3(board, tasks)
    
    print("Fixing Phase 5...")
    board = fix_phase5(board, tasks)
    
    print("Fixing Phase 6...")
    board = fix_phase6(board, tasks)
    
    print("Fixing Phase 7...")
    board = fix_phase7(board, tasks)
    
    print("Writing BOARD.md...")
    write_board(board)
    
    print("Done!")

if __name__ == "__main__":
    main()
