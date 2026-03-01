import re

board_path = "BOARD.md"

with open(board_path, "r") as f:
    lines = f.readlines()

next_stubs = []

for line in lines:
    if line.strip().startswith("|") and "⬜ PENDING SKELETON (Pass 1)" in line:
        parts = line.split("|")
        if len(parts) > 2:
            spec_id = parts[1].strip()
            name_part = parts[2].strip()
            plugin_name = name_part.split("(")[0].strip()
            
            # Skip P0, P1, P2 non-plugin structural stuff
            if ("P3" in spec_id or "P4" in spec_id or "P5" in spec_id or "P6" in spec_id or "P7" in spec_id) and "duplicate" not in line and "src/" in line:
                # extract file path
                filepath = re.search(r'`(src/[^`]+)`', line)
                if filepath:
                    next_stubs.append((spec_id, plugin_name, filepath.group(1)))
            if len(next_stubs) == 5:
                break

print("Next 5 VALID plugin stubs to flesh out (with source paths):")
for s_id, s_name, path in next_stubs:
    print(f"- {s_id}: {s_name} [{path}]")
