import os
import glob
import re

board_path = "BOARD.md"
fleshed_out_dir = "docs/specs/_02_fleshed_out"

fleshed_files = [os.path.basename(f) for f in glob.glob(f"{fleshed_out_dir}/*.md")]

missing_from_board = []

with open(board_path, "r") as f:
    for line in f:
        if "⬜ PENDING SKELETON" in line:
            parts = line.split("|")
            if len(parts) > 2:
                spec_id = parts[1].strip()
                basename_id = spec_id.split("-")[-1]
                
                # Is it actually in fleshed out?
                for mf in fleshed_files:
                    if basename_id in mf.replace("_", "-"):
                        missing_from_board.append(spec_id)
                        break

print(f"Found {len(missing_from_board)} items marked PENDING but actually fleshed out:")
for m in missing_from_board[:20]:
    print(f" - {m}")
if len(missing_from_board) > 20:
    print(" ...")
