#!/usr/bin/env python3
import os
import ast
import re

legacy_paths = [
    "/home/happy/Desktop/claude projects/vjlive/effects",
    "/home/happy/Desktop/claude projects/vjlive/plugins",
    "/home/happy/Desktop/claude projects/VJlive-2/effects",
    "/home/happy/Desktop/claude projects/VJlive-2/plugins"
]

board_path = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md"
with open(board_path, "r", encoding="utf-8") as f:
    board_content = f.read()

def normalize(name):
    # remove common suffixes
    name = re.sub(r'(?i)plugin$', '', name)
    name = re.sub(r'(?i)effect$', '', name)
    # convert CamelCase to spaces
    name = re.sub(r'([A-Z])', r' \1', name)
    # replace underscores/hyphens with spaces
    name = name.replace('_', ' ').replace('-', ' ')
    # remove extra spaces
    name = ' '.join(name.split()).lower()
    return name

board_normalized = normalize(board_content)

found_classes = []

for base_dir in legacy_paths:
    if not os.path.exists(base_dir):
        continue
    for root, dirs, files in os.walk(base_dir):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith(".py") and not file.startswith('_'): # Skip __init__.py and utils
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Ensure it looks like an effect (inherits something)
                            if node.bases:
                                found_classes.append((node.name, path))
                except Exception as e:
                    pass

missing_vjlive = []
missing_vjlive2 = []

for cls_name, path in found_classes:
    if cls_name in ["BaseEffect", "PluginBase", "Exception", "VjLiveBase"]:
        continue
    
    norm_name = normalize(cls_name)
    if len(norm_name) < 4:
        continue
        
    # Check if norm_name is in the normalized board text
    if norm_name not in board_normalized:
        # Check fallback just in case formatting tripped it
        if cls_name.lower() not in board_content.lower():
            if 'vjlive-2' in path.lower():
                missing_vjlive2.append((cls_name, path))
            else:
                missing_vjlive.append((cls_name, path))

out_path = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/WORKSPACE/COMMS/STATUS/LEGACY_MISSING_FEATURES.md"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("# Parity Analysis: Missing Legacy Features\n")
    f.write("**Analyzed Codebases:** `vjlive`, `VJlive-2`\n")
    f.write(f"**Discovered Missing Features:** {len(missing_vjlive) + len(missing_vjlive2)}\n\n")
    f.write("> The following effect and plugin classes were automatically detected via AST in the legacy codebases but are NOT tracked in `BOARD.md`.\n\n")
    
    f.write("## From `vjlive/` (Source Zero candidates)\n")
    if not missing_vjlive:
        f.write("*None found*\n")
    for cls_name, path in sorted(missing_vjlive):
        rel_path = path.split('/vjlive/')[1]
        f.write(f"- [ ] **{cls_name}** (`{rel_path}`)\n")
        
    f.write("\n## From `VJlive-2/` (Source Zero candidates)\n")
    if not missing_vjlive2:
        f.write("*None found*\n")
    for cls_name, path in sorted(missing_vjlive2):
        rel_path = path.split('/VJlive-2/')[1]
        f.write(f"- [ ] **{cls_name}** (`{rel_path}`)\n")

print(f"Report written to {out_path}")
