import os
import glob
import re

board_path = "BOARD.md"
fleshed_out_dir = "docs/specs/_02_fleshed_out"

fleshed_files = [os.path.basename(f) for f in glob.glob(f"{fleshed_out_dir}/*.md")]

# Build a fast lookup list of base IDs from the files
# E.g. P7-P7-VE34_dithering.md -> VE34
# E.g. P3-EXT113_spec.md -> EXT113
# E.g. P1-C2_state.md -> C2
file_core_ids = set()
for mf in fleshed_files:
    if mf.startswith("_"): continue
    
    # Match the last segment that looks like an ID before the underscore
    # e.g., P7-P7-VE34_xxx -> VE34
    
    parts = mf.split("_")[0].split("-")
    if len(parts) > 1:
        core = parts[-1]
        
        # some files are P3-VD27.md (no underscore)
        if ".md" in core:
            core = core.replace(".md", "")
            
        file_core_ids.add(core)

print(f"Extracted {len(file_core_ids)} unique core IDs from fleshed files.")

with open(board_path, "r") as f:
    board_lines = f.readlines()

new_lines = []
modified = 0
found_ids = set()

for line in board_lines:
    if line.strip().startswith("|") and "⬜ PENDING SKELETON" in line:
        parts = line.split("|")
        if len(parts) > 2:
            spec_id = parts[1].strip()
            
            # The spec id on board is usually P7-VE34
            board_core = spec_id.split("-")[-1]
            
            # Does this exist in our fleshed out file list?
            if board_core in file_core_ids:
                print(f"Strict Board update: Upgrading {spec_id} (Core: {board_core})")
                line = line.replace("⬜ PENDING SKELETON (Pass 1)", "🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out")
                line = re.sub(r'\| \*(.*)\* \|', '| \\1 |', line)
                modified += 1
                found_ids.add(board_core)
                
    new_lines.append(line)

with open(board_path, "w") as f:
    f.writelines(new_lines)

print(f"Modified {modified} lines in BOARD.md via strict matching.")

# What is still unaccounted for?
missing = file_core_ids - found_ids
# also subtract any that are ALREADY completd on the board
with open(board_path, "r") as f:
    for line in f:
        if "🟩 COMPLETING PASS 2" in line:
            parts = line.split("|")
            if len(parts) > 2:
                spec_id = parts[1].strip()
                bcore = spec_id.split("-")[-1]
                if bcore in missing:
                    missing.remove(bcore)

if len(missing) > 0:
    print(f"\nThere are STILL {len(missing)} fleshed out files that have NO match on the board whatsoever:")
    for m in list(missing)[:20]:
        print(m)
