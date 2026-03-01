import os
import glob
import re

board_path = "BOARD.md"
fleshed_out_dir = "docs/specs/_02_fleshed_out"

fleshed_files = [os.path.basename(f) for f in glob.glob(f"{fleshed_out_dir}/*.md")]

# Build a fast lookup list of base IDs from the files, stripping duplicate P-prefixes
file_base_ids = []
for mf in fleshed_files:
    if mf.startswith("_"): continue
    
    # Extract the core ID, e.g. from P7-P7-VE34 we want VE34
    match = re.search(r'([A-Z]+[0-9]+[A-Z]*)', mf)
    if match:
        file_base_ids.append(match.group(1))

with open(board_path, "r") as f:
    board_lines = f.readlines()

new_lines = []
modified = 0

for line in board_lines:
    if line.strip().startswith("|") and "⬜ PENDING SKELETON" in line:
        parts = line.split("|")
        if len(parts) > 2:
            spec_id = parts[1].strip()
            # Extract core ID from board (e.g. from P7-VE34 we want VE34, from P3-EXT434 we want EXT434)
            match = re.search(r'([A-Z]+[0-9]+[A-Z]*)', spec_id)
            if match:
                board_core_id = match.group(1)
                
                # Does this exist in our fleshed out file list?
                if board_core_id in file_base_ids:
                    print(f"Fuzzy Board update: Upgrading {spec_id} (Core: {board_core_id})")
                    line = line.replace("⬜ PENDING SKELETON (Pass 1)", "🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out")
                    line = re.sub(r'\| \*(.*)\* \|', '| \\1 |', line)
                    modified += 1
                
    new_lines.append(line)

with open(board_path, "w") as f:
    f.writelines(new_lines)

print(f"Modified {modified} lines in BOARD.md via fuzzy matching.")
