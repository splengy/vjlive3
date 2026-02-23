#!/usr/bin/env python3
import re

with open('BOARD.md', 'r') as f:
    board = f.read()

# Fix Phase 3: Remove the extra P3-VD24+ line
board = re.sub(
    r'(\| P3-VD75 \| quantum_depth_nexus_effect \(QuantumDepthNexus\) \| P0 \| ◯ Todo \| VJlive-2 \|\n)\n\| P3-VD24\+ \| All remaining depth plugins.*?\n\n',
    r'\1\n',
    board,
    flags=re.DOTALL
)

# Fix Phase 5A: Replace old modulator tasks with new single task
phase5_mo_section = """### 5A — Modulators (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P5-MO03 | blend (ModulateEffect) | P0 | ◯ Todo | VJlive-2 |

"""
board = re.sub(
    r'### 5A — Modulators \(MISSING from VJlive-2\)\n\n\| Task ID \| Plugin \| Status \|\n\|---------\|--------\|--------\|\n(?:\|.*?\n)*?(?=\n\n###)',
    phase5_mo_section,
    board,
    flags=re.DOTALL
)

# Fix Phase 5B: Replace old V-* tasks with new single task
phase5_ve_section = """### 5B — V-* Visual Effects (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P5-VE02 | analog_tv (AnalogTVEffect) | P0 | ◯ Todo | VJlive-2 |

"""
board = re.sub(
    r'### 5B — V-\* Visual Effects \(MISSING from VJlive-2\)\n\n\| Task ID \| Plugin \| Status \|\n\|---------\|--------\|--------\|\n(?:\|.*?\n)*?(?=\n\n###)',
    phase5_ve_section,
    board,
    flags=re.DOTALL
)

# Fix Phase 5D: Replace with all 36 datamosh tasks
with open('docs/task_generation_summary.md', 'r') as f:
    summary = f.read()

phase5_dm = []
for line in summary.split('\n'):
    line = line.strip()
    if line.startswith('- P5-DM') and ':' in line:
        m = re.match(r'- (P5-[A-Z]+\d+): (.+?)(?: \((.+)\))?$', line)
        if m:
            tid, desc, cls = m.groups()
            phase5_dm.append((tid, desc, cls or ''))

phase5_dm.sort(key=lambda x: x[0])
dm_rows = []
for tid, desc, cls in phase5_dm:
    if cls:
        desc = f"{desc} ({cls})"
    dm_rows.append(f"| {tid} | {desc} | P0 | ◯ Todo | VJlive-2 |")
dm_section = f"""### 5D — Datamosh Family (verify both sources, keep VJlive-2's cleaner impl)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{chr(10).join(dm_rows)}

"""
board = re.sub(
    r'### 5D — Datamosh Family \(verify both sources, keep VJlive-2\'s cleaner impl\)\n\n\| Task ID \| Plugin \| Status \| Source \|\n\|---------\|--------\|--------\|--------\|\n(?:\|.*?\n)*?(?=\n\n\*\*Phase 5 Gate\*\*)',
    dm_section,
    board,
    flags=re.DOTALL
)

# Fix Phase 6B: Remove duplicates
board = re.sub(
    r'(\| P6-QC06 \|.*?\n)(?:\| - P6-QC06 \|.*?\n)+',
    r'\1',
    board,
    flags=re.DOTALL
)

# Fix Phase 6D: Remove duplicates and add proper header
phase6_ge = []
phase6_p3 = []
for line in summary.split('\n'):
    line = line.strip()
    if line.startswith('- P6-GE') and ':' in line:
        m = re.match(r'- (P6-[A-Z]+\d+): (.+?)(?: \((.+)\))?$', line)
        if m:
            tid, desc, cls = m.groups()
            phase6_ge.append((tid, desc, cls or ''))
    elif line.startswith('- P6-P3') and ':' in line:
        m = re.match(r'- (P6-[A-Z]+\d+): (.+?)(?: \((.+)\))?$', line)
        if m:
            tid, desc, cls = m.groups()
            phase6_p3.append((tid, desc, cls or ''))

phase6_ge.sort(key=lambda x: x[0])
phase6_p3.sort(key=lambda x: x[0])

ge_rows = '\n'.join([f"| {tid} | {desc} ({cls}) | P0 | ◯ Todo | VJlive-2 |" for tid, desc, cls in phase6_ge])
p3_rows = '\n'.join([f"| {tid} | {desc} ({cls}) | P0 | ◯ Todo | VJlive-2 |" for tid, desc, cls in phase6_p3])

phase6_section = f"""### 6D — Generators (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{ge_rows}

### 6E — Particle/3D Systems (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{p3_rows}

"""
# Find and replace the entire 6D and 6E sections
pattern_6d_6e = r'### 6D — Generators \(VJlive-2 unique — keep\)\n\n### 6E — Particle/3D Systems \(VJlive-2 unique — keep\)\n\n(?:\| Task ID \|.*?\n)*(?:\n\| Task ID \|.*?\n)*?(?=\n\*\*Phase 6 Gate\*\*)'
board = re.sub(pattern_6d_6e, phase6_section, board, flags=re.DOTALL)

with open('BOARD.md', 'w') as f:
    f.write(board)

print("Board fixes applied!")
PYEOF