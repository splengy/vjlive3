import os
import glob
import re

board_path = "BOARD.md"
fleshed_out_dir = "docs/specs/_02_fleshed_out"

fleshed_files = [os.path.basename(f) for f in glob.glob(f"{fleshed_out_dir}/*.md")]

# Re-run the strict matching logic to find the exact 52 orphans
file_core_ids = set()
file_map = {}
for mf in fleshed_files:
    if mf.startswith("_"): continue
    parts = mf.split("_")[0].split("-")
    if len(parts) > 1:
        core = parts[-1]
        if ".md" in core:
            core = core.replace(".md", "")
        file_core_ids.add(core)
        file_map[core] = mf

with open(board_path, "r") as f:
    board_lines = f.readlines()

found_ids = set()
for line in board_lines:
    if line.strip().startswith("|") and ("⬜ PENDING SKELETON" in line or "🟩 COMPLETING PASS 2" in line):
        parts = line.split("|")
        if len(parts) > 2:
            spec_id = parts[1].strip()
            board_core = spec_id.split("-")[-1]
            found_ids.add(board_core)

orphans = file_core_ids - found_ids

# Now generate table rows for the orphans
orphan_rows = []
for core in orphans:
    filename = file_map[core]
    # Estimate the plugin name from the filename
    name_parts = filename.replace(".md", "").split("_")[1:]
    plugin_name = "_".join(name_parts)
    if not plugin_name:
        plugin_name = core
    
    # Try to extract the original P group prefix from the filename (e.g. P3, P7)
    group_match = re.match(r'(P[0-9])-', filename)
    group = group_match.group(1) if group_match else "P-UNK"
    
    spec_id = f"{group}-{core}"
    
    row = f"| {spec_id} | {plugin_name} | P0 | 🟩 COMPLETING PASS 2 | ✅ Spec exists in _02_fleshed_out |\n"
    orphan_rows.append(row)

# Append to BOARD.md
if orphan_rows:
    board_lines.append("\n## Recovered Core Features (Orphan Specs)\n")
    board_lines.append("| ID | Name (Class) | Priority | Status | Location / Notes |\n")
    board_lines.append("|---|---|---|---|---|\n")
    board_lines.extend(orphan_rows)
    
    with open(board_path, "w") as f:
        f.writelines(board_lines)
    print(f"Appended {len(orphan_rows)} orphan specs to BOARD.md")
else:
    print("No orphans found to append.")
