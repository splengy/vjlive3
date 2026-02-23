#!/usr/bin/env python3
import re
from pathlib import Path

# Read board
board = Path('BOARD.md').read_text()

# Read task summary
summary = Path('docs/task_generation_summary.md').read_text()

# Parse Phase 5 tasks
phase5_dm = []
phase5_mo = []
phase5_ve = []
for line in summary.split('\n'):
    line = line.strip()
    if line.startswith('- P5-') and ':' in line:
        m = re.match(r'- (P5-[A-Z]+\d+): (.+?)(?: \((.+)\))?$', line)
        if m:
            tid, desc, cls = m.groups()
            if tid.startswith('P5-DM'):
                phase5_dm.append((tid, desc, cls or ''))
            elif tid == 'P5-MO03':
                phase5_mo.append((tid, desc, cls or ''))
            elif tid == 'P5-VE02':
                phase5_ve.append((tid, desc, cls or ''))

phase5_dm.sort(key=lambda x: x[0])

def row(tid, desc, cls):
    if cls:
        desc = f"{desc} ({cls})"
    return f"| {tid} | {desc} | P0 | ◯ Todo | VJlive-2 |"

dm_rows = "\n".join([row(*t) for t in phase5_dm])
mo_row = row(*phase5_mo[0]) if phase5_mo else "| P5-MO03 | blend (ModulateEffect) | P0 | ◯ Todo | VJlive-2 |"
ve_row = row(*phase5_ve[0]) if phase5_ve else "| P5-VE02 | analog_tv (AnalogTVEffect) | P0 | ◯ Todo | VJlive-2 |"

# Build sections
section_5A = f"""### 5A — Modulators (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{mo_row}

"""
section_5B = f"""### 5B — V-* Visual Effects (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{ve_row}

"""
section_5D = f"""### 5D — Datamosh Family (verify both sources, keep VJlive-2's cleaner impl)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
{dm_rows}

"""

# Replace 5A
pattern5A = r"### 5A — Modulators \(MISSING from VJlive-2\)\n\n\| Task ID \| Plugin \| Status \|\n\|---------\|--------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
board = re.sub(pattern5A, section_5A, board, flags=re.DOTALL)

# Replace 5B
pattern5B = r"### 5B — V-\* Visual Effects \(MISSING from VJlive-2\)\n\n\| Task ID \| Plugin \| Status \|\n\|---------\|--------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
board = re.sub(pattern5B, section_5B, board, flags=re.DOTALL)

# Replace 5D
pattern5D = r"### 5D — Datamosh Family \(verify both sources, keep VJlive-2's cleaner impl\)\n\n\| Task ID \| Plugin \| Status \| Source \|\n\|---------\|--------\|--------\|--------\|\n(?:\|.*?\n)*?(?=\n\n)"
board = re.sub(pattern5D, section_5D, board, flags=re.DOTALL)

Path('BOARD.md').write_text(board)
print(f"Phase 5 fixed: DM={len(phase5_dm)}, MO={len(phase5_mo)}, VE={len(phase5_ve)}")
