#!/usr/bin/env python3
import re

def main():
    # Read board
    with open('BOARD.md', 'r') as f:
        board = f.read()
    
    # Read task summary for all phases
    with open('docs/task_generation_summary.md', 'r') as f:
        summary = f.read()
    
    # Parse all tasks by phase
    tasks_by_phase = {'3': [], '4': [], '5': [], '6': [], '7': []}
    current_phase = None
    for line in summary.split('\n'):
        line = line.strip()
        if line.startswith('## Phase '):
            if 'Phase 3' in line:
                current_phase = '3'
            elif 'Phase 4' in line:
                current_phase = '4'
            elif 'Phase 5' in line:
                current_phase = '5'
            elif 'Phase 6' in line:
                current_phase = '6'
            elif 'Phase 7' in line:
                current_phase = '7'
        elif line.startswith('- P') and ':' in line:
            m = re.match(r'- (P\d+-[A-Z]+\d+): (.+?)(?: \((.+)\))?$', line)
            if m:
                tid, desc, cls = m.groups()
                tasks_by_phase[current_phase].append((tid, desc, cls or ''))
    
    # Sort tasks by task ID
    for phase in tasks_by_phase:
        tasks_by_phase[phase].sort(key=lambda x: x[0])
    
    # Generate rows function
    def generate_rows(tasks, source="VJlive-2"):
        rows = []
        for tid, desc, cls in tasks:
            if cls:
                desc = f"{desc} ({cls})"
            rows.append(f"| {tid} | {desc} | P0 | ◯ Todo | {source} |")
        return '\n'.join(rows)
    
    # Build replacement sections
    phase3_rows = generate_rows(tasks_by_phase['3'])
    section_3A = f"""### 3A — Missing Depth Plugins (from vjlive/vdepth/ — audit individually, every plugin is unique)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{phase3_rows}

"""
    
    phase4_rows = generate_rows(tasks_by_phase['4'])
    section_4D = f"""### 4D — Audio Reactive (MISSING from VJlive-2)

| Task ID | Plugin | Status | Source |
|---------|--------|--------|--------|
{phase4_rows}

"""
    
    phase5_rows = generate_rows(tasks_by_phase['5'])
    section_5A = f"""### 5A — Modulators (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{phase5_rows}

"""
    section_5B = f"""### 5B — V-* Visual Effects (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{phase5_rows}

"""
    section_5D = f"""### 5D — Datamosh Family (verify both sources, keep VJlive-2's cleaner impl)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{phase5_rows}

"""
    
    phase6_rows = generate_rows(tasks_by_phase['6'])
    section_6A = f"""### 6A — AI / Neural Systems (VJlive-2 leads)

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|
{phase6_rows}

"""
    section_6B = f"""### 6B — Quantum Consciousness (VJlive-2 leads)

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|
{phase6_rows}

"""
    section_6D = f"""### 6D — Generators (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{phase6_rows}

"""
    section_6E = f"""### 6E — Particle/3D Systems (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{phase6_rows}

"""
    
    phase7_rows = generate_rows(tasks_by_phase['7'])
    section_7C = f"""### 7C — Additional Effects & Utilities (VJlive-2 + vjlive synthesis)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{phase7_rows}

"""
    
    # Replace sections using simple string patterns
    # Phase 3
    board = re.sub(
        r'### 3A — Missing Depth Plugins \(from vjlive/vdepth/ — audit individually, every plugin is unique\)\n\n\| Task ID \| Description \| Priority \| Status \|\n\|---------\|--------\|--------\|--------\|\n(?:".*?\n)*?(?=\n\n### 3B)',
        section_3A,
        board,
        flags=re.DOTALL
    )
    
    # Phase 4D
    board = re.sub(
        r'### 4D — Audio Reactive \(MISSING from VJlive-2\)\n\n\| Task ID \| Plugin \| Status \| Source \|\n\|---------\|--------\|--------\|--------\|\n(?:".*?\n)*?(?=\n\n### 4B)',
        section_4D,
        board,
        flags=re.DOTALL
    )
    
    # Phase 5A
    board = re.sub(
        r'### 5A — Modulators \(MISSING from VJlive-2\)\n\n\| Task ID \| Plugin \| Status \|\n\|---------\|--------\|--------\|\n(?:".*?\n)*?(?=\n\n### 5B)',
        section_5A,
        board,
        flags=re.DOTALL
    )
    
    # Phase 5B
    board = re.sub(
        r'### 5B — V-\* Visual Effects \(MISSING from VJlive-2\)\n\n\| Task ID \| Plugin \| Status \|\n\|---------\|--------\|--------\|\n(?:".*?\n)*?(?=\n\n### 5C)',
        section_5B,
        board,
        flags=re.DOTALL
    )
    
    # Phase 5D
    board = re.sub(
        r'### 5D — Datamosh Family \(verify both sources, keep VJlive-2\'s cleaner impl\)\n\n\| Task ID \| Plugin \| Status \| Source \|\n\|---------\|--------\|--------\|--------\|\n(?:".*?\n)*?(?=\n\n\*\*Phase 5 Gate\*\*)',
        section_5D,
        board,
        flags=re.DOTALL
    )
    
    # Phase 6A
    board = re.sub(
        r'### 6A — AI / Neural Systems \(VJlive-2 leads\)\n\n\| Task ID \| Description \| Status \| Source \|\n\|---------\|--------\|--------\|--------\|\n(?:".*?\n)*?(?=\n\n### 6B)',
        section_6A,
        board,
        flags=re.DOTALL
    )
    
    # Phase 6B
    board = re.sub(
        r'### 6B — Quantum Consciousness \(VJlive-2 leads\)\n\n\| Task ID \| Description \| Status \| Source \|\n\|---------\|--------\|--------\|--------\|\n(?:".*?\n)*?(?=\n\n### 6C)',
        section_6B,
        board,
        flags=re.DOTALL
    )
    
    # Phase 6D
    board = re.sub(
        r'### 6D — Generators \(VJlive-2 unique — keep\)\n\n\| Task ID \| Description \| Priority \| Status \| Source \|\n\|---------\|--------\|--------\|--------\|--------\|\n(?:".*?\n)*?(?=\n\n### 6E)',
        section_6D,
        board,
        flags=re.DOTALL
    )
    
    # Phase 6E
    board = re.sub(
        r'### 6E — Particle/3D Systems \(VJlive-2 unique — keep\)\n\n\| Task ID \| Description \| Priority \| Status \| Source \|\n\|---------\|--------\|--------\|--------\|--------\|\n(?:".*?\n)*?(?=\n\n\*\*Phase 6 Gate\*\*)',
        section_6E,
        board,
        flags=re.DOTALL
    )
    
    # Phase 7C
    board = re.sub(
        r'### 7C — Additional Effects & Utilities \(VJlive-2 \+ vjlive synthesis\)\n\n\| Task ID \| Description \| Priority \| Status \| Source \|\n\|---------\|--------\|--------\|--------\|--------\|\n(?:".*?\n)*?(?=\n\n\*\*Phase 7 Gate\*\*)',
        section_7C,
        board,
        flags=re.DOTALL
    )
    
    # Write back
    with open('BOARD.md', 'w') as f:
        f.write(board)
    
    # Verification
    total_tasks = sum(len(tasks) for tasks in tasks_by_phase.values())
    print(f"✓ Board fixed with {total_tasks} tasks:")
    print(f"  Phase 3: {len(tasks_by_phase['3'])} tasks")
    print(f"  Phase 4: {len(tasks_by_phase['4'])} tasks")
    print(f"  Phase 5: {len(tasks_by_phase['5'])} tasks")
    print(f"  Phase 6: {len(tasks_by_phase['6'])} tasks")
    print(f"  Phase 7: {len(tasks_by_phase['7'])} tasks")
    print(f"  Total: {total_tasks} tasks")

if __name__ == '__main__':
    main()