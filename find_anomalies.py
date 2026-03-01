import os
import glob
import re

board_path = "BOARD.md"
fleshed_out_dir = "docs/specs/_02_fleshed_out"

fleshed_files = [os.path.basename(f) for f in glob.glob(f"{fleshed_out_dir}/*.md")]
board_specs = []

with open(board_path, "r") as f:
    for line in f:
        if "🟩 COMPLETING PASS 2" in line:
            parts = line.split("|")
            if len(parts) > 2:
                spec_id = parts[1].strip()
                basename_id = spec_id.split("-")[-1]
                board_specs.append(basename_id)

print(f"Files: {len(fleshed_files)}, Checked: {len(board_specs)}")

unaccounted_files = []
for mf in fleshed_files:
    if mf.startswith("_"): continue
    
    # Try to find a matching ID
    # Usually files are named like P3-EXT013_bad_trip.md
    file_id_match = re.search(r'(P\d-[A-Z0-9]+)', mf)
    
    if file_id_match:
        file_id = file_id_match.group(1).split("-")[-1]
        
        # Is this ID in the board_specs?
        found = False
        for bid in board_specs:
            if bid == file_id:
                found = True
                break
                
        if not found:
            unaccounted_files.append(mf)
    else:
        unaccounted_files.append(mf)

print(f"Found {len(unaccounted_files)} files in fleshed_out that do not match ANY 'COMPLETING PASS 2' checkbox on the board.")
for u in unaccounted_files[:20]:
    print(f" - {u}")
if len(unaccounted_files) > 20:
    print(" ...")
