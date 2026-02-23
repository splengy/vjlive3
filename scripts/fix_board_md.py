#!/usr/bin/env python3
"""
Fix BOARD.md by replacing old task entries with the correct new tasks from the audit.
"""

import re
from pathlib import Path
from collections import defaultdict

# Read task generation summary
def read_task_summary():
    summary_file = Path("docs/task_generation_summary.md")
    content = summary_file.read_text()
    
    tasks_by_phase = defaultdict(list)
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Parse task lines like: "- P3-VD26: Depth Acid Fractal (DepthAcidFractalDatamoshEffect)"
        if line.startswith("- P") and ':' in line:
            match = re.match(r'- (P\d+-[A-Z]+\d+): (.+?)(?: \((.+)\))?$', line)
            if match:
                task_id = match.group(1)
                description = match.group(2)
                class_name = match.group(3) if match.group(3) else ""
                phase = task_id.split('-')[0][1]
                tasks_by_phase[phase].append({
                    'id': task_id,
                    'description': description,
                    'class': class_name
                })
    
    return tasks_by_phase

def generate_task_row(task):
    desc = task['description']
    if task['class']:
        desc += f" ({task['class']})"
    return f"| {task['id']} | {desc} | P0 | ◯ Todo | VJlive-2 |"

def read_board():
    return Path("BOARD.md").read_text()

def write_board(content):
    Path("BOARD.md").write_text(content)

def main():
    tasks_by_phase = read_task_summary()
    
    print("Tasks loaded:")
    for phase in sorted(tasks_by_phase.keys()):
        print(f"  Phase {phase}: {len(tasks_by_phase[phase])} tasks")
    
    board = read_board()
    
    # PHASE 3
    phase3_rows = "\n".join([generate_task_row(t) for t in tasks_by_phase['3']])
    phase3_section = f"""### 3A — Missing Depth Plugins (from vjlive/vdepth/ — audit individually, every plugin is unique)

| Task ID | Description | Priority | Status |
|---------|-------------|----------|--------|
{phase3_rows}

| P3-VD24+ | All remaining depth plugins in vjlive/vdepth/ — audit, name, and port each individually | P1 | ◯ Todo |

"""
    pattern3 = r"### 3A — Missing Depth Plugins \(from vjlive/vdepth/ — audit individually, every plugin is unique\)\n\n\| Task ID \| Description \| Priority \| Status \|\n\|---------\|-------------\|----------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
    board = re.sub(pattern3, phase3_section, board, flags=re.DOTALL)
    
    # PHASE 4
    phase4_rows = "\n".join([generate_task_row(t) for t in tasks_by_phase['4']])
    phase4_section = f"""### 4A — Bogaudio Collection (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P4-BA01 | B1to8 | P0 | ◯ Todo | vjlive |
| P4-BA02 | BLFO | P0 | ◯ Todo | vjlive |
| P4-BA03 | BMatrix81 | P0 | ◯ Todo | vjlive |
| P4-BA04 | BPEQ6 | P0 | ◯ Todo | vjlive |
| P4-BA05 | BSwitch | P0 | ◯ Todo | vjlive |
| P4-BA06 | BVCF | P0 | ◯ Todo | vjlive |
| P4-BA07 | BVCO | P0 | ◯ Todo | vjlive |
| P4-BA08 | BVELO | P0 | ◯ Todo | vjlive |
| P4-BA09 | NMix4 | P0 | ◯ Todo | vjlive |
| P4-BA10 | NXFade | P0 | ◯ Todo | vjlive |

### 4D — Audio Reactive (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{phase4_rows}

"""
    pattern4a = r"### 4A — Bogaudio Collection \(MISSING from VJlive-2\)\n\n\| Task ID \| Description \| Priority \| Status \|\n\|---------\|-------------\|----------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
    pattern4d = r"### 4D — Audio Reactive \(MISSING from VJlive-2\)\n\n\| Task ID \| Description \| Priority \| Status \|\n\|---------\|-------------\|----------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
    board = re.sub(pattern4a, "", board, flags=re.DOTALL)
    board = re.sub(pattern4d, "", board, flags=re.DOTALL)
    # Insert at 4D position
    match = re.search(pattern4d, board, re.DOTALL)
    if match:
        board = board[:match.start()] + phase4_section + board[match.end():]
    else:
        print("WARNING: 4D section not found for position")
    
    # PHASE 5
    phase5_dm = [t for t in tasks_by_phase['5'] if t['id'].startswith('P5-DM')]
    phase5_mo = [t for t in tasks_by_phase['5'] if t['id'] == 'P5-MO03']
    phase5_ve = [t for t in tasks_by_phase['5'] if t['id'] == 'P5-VE02']
    
    dm_rows = "\n".join([generate_task_row(t) for t in sorted(phase5_dm, key=lambda x: x['id'])])
    mo_row = generate_task_row(phase5_mo[0]) if phase5_mo else "| P5-MO03 | blend (ModulateEffect) | P0 | ◯ Todo | VJlive-2 |"
    ve_row = generate_task_row(phase5_ve[0]) if phase5_ve else "| P5-VE02 | analog_tv (AnalogTVEffect) | P0 | ◯ Todo | VJlive-2 |"
    
    phase5_section = f"""### 5A — Modulators (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{mo_row}

### 5B — V-* Visual Effects (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{ve_row}

### 5D — Datamosh Family (verify both sources, keep VJlive-2's cleaner impl)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{dm_rows}

"""
    pattern5a = r"### 5A — Modulators \(MISSING from VJlive-2\)\n\n\| Task ID \| Description \| Priority \| Status \|\n\|---------\|-------------\|----------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
    pattern5b = r"### 5B — V-\* Visual Effects \(MISSING from VJlive-2\)\n\n\| Task ID \| Description \| Priority \| Status \|\n\|---------\|-------------\|----------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
    pattern5d = r"### 5D — Datamosh Family \(verify both sources, keep VJlive-2's cleaner impl\)\n\n\| Task ID \| Description \| Priority \| Status \|\n\|---------\|-------------\|----------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
    
    board = re.sub(pattern5a, "", board, flags=re.DOTALL)
    board = re.sub(pattern5b, "", board, flags=re.DOTALL)
    board = re.sub(pattern5d, "", board, flags=re.DOTALL)
    
    # Insert at old 5D position
    pos5 = board.find("### 5D — Datamosh Family")
    if pos5 != -1:
        board = board[:pos5] + phase5_section + board[pos5:]
    else:
        print("WARNING: 5D position not found")
    
    # PHASE 6
    phase6_qc = [t for t in tasks_by_phase['6'] if t['id'].startswith('P6-QC')]
    phase6_ge = [t for t in tasks_by_phase['6'] if t['id'].startswith('P6-GE')]
    phase6_p3 = [t for t in tasks_by_phase['6'] if t['id'].startswith('P6-P3')]
    
    qc_rows = "\n".join([generate_task_row(t) for t in sorted(phase6_qc, key=lambda x: x['id'])])
    ge_rows = "\n".join([generate_task_row(t) for t in sorted(phase6_ge, key=lambda x: x['id'])])
    p3_rows = "\n".join([generate_task_row(t) for t in sorted(phase6_p3, key=lambda x: x['id'])])
    
    phase6_section = f"""### 6B — Quantum Consciousness (VJlive-2 leads)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{qc_rows}

### 6D — Generators (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{ge_rows}

### 6E — Particle/3D Systems (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{p3_rows}

"""
    pattern6b = r"### 6B — Quantum Consciousness \(VJlive-2 leads\)\n\n\| Task ID \| Description \| Status \| Source \|\n\|---------\|-------------\|--------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
    pattern6d = r"### 6D — Generators \(VJlive-2 unique — keep\)\n\n\| Task ID \| Description \| Status \|\n\|---------\|-------------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
    
    board = re.sub(pattern6b, "", board, flags=re.DOTALL)
    board = re.sub(pattern6d, "", board, flags=re.DOTALL)
    
    pos6 = board.find("### 6D — Generators")
    if pos6 != -1:
        board = board[:pos6] + phase6_section + board[pos6:]
    else:
        print("WARNING: 6D position not found")
    
    # PHASE 7
    phase7_rows = "\n".join([generate_task_row(t) for t in sorted(tasks_by_phase['7'], key=lambda x: x['id'])])
    phase7_section = f"""### 7C — Additional Effects & Utilities (VJlive-2 + vjlive synthesis)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{phase7_rows}

"""
    pattern7b = r"(### 7B — Business / Licensing\n\n\| Task ID \| Description \| Status \| Source \|\n\|---------\|-------------\|--------\|--------\|\n(?:\|.*?\n)*?\n\n)"
    match = re.search(pattern7b, board, re.DOTALL)
    if match:
        board = board[:match.end()] + phase7_section + board[match.end():]
    else:
        print("WARNING: 7B section not found")
    
    write_board(board)
    print("\nBOARD.md updated successfully!")
    
    print("\nVerification:")
    for phase in ['3', '4', '5', '6', '7']:
        count = len(tasks_by_phase[phase])
        print(f"  Phase {phase}: {count} tasks")
    print(f"  Total: {sum(len(tasks_by_phase[p]) for p in '34567')} tasks")

if __name__ == "__main__":
    main()
