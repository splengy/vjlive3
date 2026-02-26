#!/usr/bin/env python3
"""Reset ALL false Done/In Progress marks in BOARD.md.
Phase 0 workspace items (P0-G, P0-W, P0-Q, P0-S, P0-M, P0-A, P0-V, P0-INF) are preserved.
Everything else is reset — including fake 'duplicate/already shipped' entries."""
import os

board_path = os.path.join(os.path.dirname(__file__), '..', 'BOARD.md')

with open(board_path, 'r') as f:
    content = f.read()

done_count = content.count('✅ Done')
progress_count = content.count('🔄 In Progress')
reset_already = content.count('⬜ RESET')

# Only keep Phase 0 items as Done
phase0_ids = ['P0-G', 'P0-W', 'P0-Q', 'P0-S', 'P0-M', 'P0-A', 'P0-V', 'P0-INF']

lines = content.split('\n')
reset_done = 0
reset_progress = 0

for i, line in enumerate(lines):
    # Check if this is a Phase 0 line by task ID
    is_phase0 = any(pid in line for pid in phase0_ids)
    
    if not is_phase0:
        if '✅ Done' in line:
            # Reset ALL non-Phase-0 Done marks including duplicates
            lines[i] = line.replace('✅ Done', '⬜ RESET')
            reset_done += 1
        
        if '🔄 In Progress' in line:
            lines[i] = line.replace('🔄 In Progress', '⬜ RESET')
            reset_progress += 1

with open(board_path, 'w') as f:
    f.write('\n'.join(lines))

print(f'Before: {done_count} Done, {progress_count} In Progress, {reset_already} already RESET')
print(f'This pass: {reset_done} Done → RESET, {reset_progress} In Progress → RESET')
print(f'Total RESET now: {reset_already + reset_done + reset_progress}')
print(f'Phase 0 items preserved as Done')
