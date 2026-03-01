import re

board_path = "BOARD.md"

targets = ["P3-VD08", "P4-COR011", "P1-P2", "P2-D6", "P2-I6", "P3-VD7", "P3-VD72"]

with open(board_path, "r") as f:
    board_lines = f.readlines()

new_lines = []
modified = 0

for line in board_lines:
    if line.strip().startswith("|") and "⬜ PENDING SKELETON" in line:
        parts = line.split("|")
        if len(parts) > 2:
            spec_id = parts[1].strip()
            if spec_id in targets:
                print(f"Board update: Upgrading {spec_id} to 🟩 COMPLETING PASS 2")
                line = line.replace("⬜ PENDING SKELETON (Pass 1)", "🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out")
                line = re.sub(r'\| \*(.*)\* \|', '| \\1 |', line)
                modified += 1
                
    new_lines.append(line)

with open(board_path, "w") as f:
    f.writelines(new_lines)

print(f"Modified {modified} lines in BOARD.md.")
