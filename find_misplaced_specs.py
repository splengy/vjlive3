import os
import glob
import shutil
import re

specs_dir = "docs/specs"
fleshed_out_dir = "docs/specs/_02_fleshed_out"
board_path = "BOARD.md"

files = glob.glob(f"{specs_dir}/*.md")

misplaced_files = []

# First, find misplaced fleshed out files
for file_path in files:
    filename = os.path.basename(file_path)
    if filename.startswith("_"): continue # ignore tracking files
    
    with open(file_path, "r") as f:
        content = f.read()
        
    # Is it a skeleton stub or fleshed out?
    if "status: ⬜ todo" in content.lower() or "status: todo" in content.lower() or "PENDING SKELETON" in content:
        # It is a stub, leave it
        pass
    elif len(content) > 1500: # if it's long and doesn't have a stub tag, it's fleshed out
        misplaced_files.append(file_path)

print(f"Found {len(misplaced_files)} misplaced, fully-written specs in the root docs/specs folder:")
for mf in misplaced_files:
    print(f" - {os.path.basename(mf)}")

# Move them
for mf in misplaced_files:
    target = os.path.join(fleshed_out_dir, os.path.basename(mf))
    print(f"Moving {mf} -> {target}")
    shutil.move(mf, target)

# Now update the board
with open(board_path, "r") as f:
    board_lines = f.readlines()

new_lines = []
modified = 0

for line in board_lines:
    if line.strip().startswith("|") and "⬜ PENDING SKELETON" in line:
        # Check if this ID is now in fleshed_out
        parts = line.split("|")
        if len(parts) > 2:
            spec_id = parts[1].strip()
            basename_id = spec_id.split("-")[-1]
            
            # Did we just move it?
            found = False
            for mf in misplaced_files:
                if basename_id in mf.replace("_", "-"):  # Handle exact matches or underscores
                    found = True
                    break
                    
            if found:
                print(f"Board update: Upgrading {spec_id} to 🟩 COMPLETING PASS 2")
                line = line.replace("⬜ PENDING SKELETON (Pass 1)", "🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out")
                # Clean up the end of the line if we just injected text into the middle
                line = re.sub(r'\| \*(.*)\* \|', '| \\1 |', line) # If it had a duplicate tag, it's tricky, but let's just do a basic replace for now
                modified += 1
                
    new_lines.append(line)

with open(board_path, "w") as f:
    f.writelines(new_lines)

print(f"Modified {modified} lines in BOARD.md.")
