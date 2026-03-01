import os
import glob

board_path = "BOARD.md"
fleshed_out_dir = "docs/specs/_02_fleshed_out"

fleshed_files = [os.path.basename(f) for f in glob.glob(f"{fleshed_out_dir}/*.md")]

# How many checkmarks?
checked_count = 0
with open(board_path, "r") as f:
    for line in f:
        if "🟩 COMPLETING PASS 2" in line:
            checked_count += 1

print(f"Total files in _02_fleshed_out: {len(fleshed_files)}")
print(f"Total '🟩 COMPLETING PASS 2' in BOARD.md: {checked_count}")

# Verify exact match
mismatch = 0
with open(board_path, "r") as f:
    for line in f:
        if "🟩 COMPLETING PASS 2" in line:
            parts = line.split("|")
            if len(parts) > 2:
                spec_id = parts[1].strip()
                basename_id = spec_id.split("-")[-1]
                
                found = False
                for mf in fleshed_files:
                    if basename_id in mf.replace("_", "-"):
                        found = True
                        break
                if not found:
                    print(f"MISMATCH: {spec_id} is checked on board but missing from folder.")
                    mismatch += 1

print(f"Mismatches: {mismatch}")
