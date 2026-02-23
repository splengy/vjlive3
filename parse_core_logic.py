import re

board_path = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md"
features_path = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/WORKSPACE/COMMS/STATUS/CORE_LOGIC_PARITY.md"

with open(features_path, 'r') as f:
    features_content = f.read()

new_table = """### P0-INF4: Core Logic Parity (~1800 Discovered)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|\n"""

task_id_counter = 1
for line in features_content.split('\n'):
    if line.strip().startswith("- **"):
        match = re.search(r'\*\*(.*?)\*\*\s+\(`([^`]+)`\)', line)
        if match:
            if task_id_counter > 300:
                break
            class_name = match.group(1).strip()
            file_name = match.group(2).strip()
            task_id = f"P4-COR{task_id_counter:03d}"
            
            # Formatting the desc nicely as "filename (ClassName)"
            filename = file_name.split('/')[-1].replace('.py', '')
            desc = f"{filename} ({class_name})"
            
            # As source isn't explicitly split in this file the same way as legacy features,
            # we can just put "Legacy" or "Core Logic Parity Audit"
            new_table += f"| {task_id} | {desc} | P0 | ⬜ Todo | Legacy |\n"
            task_id_counter += 1

# If there are still features remaining, add a note
if task_id_counter > 300:
    new_table += "\n> Note: Only the first 300 features are listed here to keep the board manageable. See `WORKSPACE/COMMS/STATUS/CORE_LOGIC_PARITY.md` for the remaining ~1500 items.\n"

with open(board_path, 'r') as f:
    board_content = f.read()

old_block = """### P0-INF4: Core Logic Parity (~1800 Discovered)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P0-INF4 | Core Logic Parity - ~1800 missing features (comprehensive audit) | P0 | ⬜ Todo | Comprehensive audit of vjlive/ & VJlive-2/ |
| | **Source Report:** `WORKSPACE/COMMS/STATUS/CORE_LOGIC_PARITY.md` | | | |
| | **Action Required:** Roo to create specs for these newly discovered core logic concepts. | | | |"""

if old_block in board_content:
    new_board = board_content.replace(old_block, new_table)
    with open(board_path, 'w') as f:
        f.write(new_board)
    print(f"Replaced successfully, added {task_id_counter - 1} tasks.")
else:
    print("Could not find old block in BOARD.md")
