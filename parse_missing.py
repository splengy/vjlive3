import re

board_path = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md"
features_path = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/WORKSPACE/COMMS/STATUS/LEGACY_MISSING_FEATURES.md"

with open(features_path, 'r') as f:
    features_content = f.read()

new_table = """### P0-INF3: Missing Legacy Effects Parity (423 Discovered)

| Task ID | Description | Priority | Status | Source |\n|---------|-------------|----------|--------|--------|\n"""

current_source = None
task_id_counter = 1
for line in features_content.split('\n'):
    if line.startswith("## From"):
        if "vjlive/" in line:
            current_source = "vjlive"
        elif "VJlive-2" in line:
            current_source = "VJlive-2"
    elif line.startswith("- [ ] **"):
        match = re.search(r'\*\*([^*]+)\*\*\s+\(`([^`]+)`\)', line)
        if match:
            effect_name = match.group(1).split('.')[-1]
            file_path = match.group(2)
            task_id = f"P3-EXT{task_id_counter:03d}"
            filename = file_path.split('/')[-1].replace('.py', '')
            desc = f"{filename} ({effect_name})"
            new_table += f"| {task_id} | {desc} | P0 | ⬜ Todo | {current_source} |\n"
            task_id_counter += 1

with open(board_path, 'r') as f:
    board_content = f.read()

old_block = """### P0-INF3: Missing Legacy Effects Parity (423 Discovered)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P0-INF3 | Legacy Effects Parity - ~200 unique new effects (comprehensive audit) | P0 | ⬜ Todo | Comprehensive audit of vjlive/ & VJlive-2/ |
| | **Source Report:** `WORKSPACE/COMMS/STATUS/LEGACY_MISSING_FEATURES.md` | | | |
| | **Action Required:** Roo to create specs for these newly discovered effects. | | | |"""

if old_block in board_content:
    new_board = board_content.replace(old_block, new_table)
    with open(board_path, 'w') as f:
        f.write(new_board)
    print("Replaced successfully")
else:
    print("Could not find old block in BOARD.md")

