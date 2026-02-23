import json
from pathlib import Path

def main():
    root = Path('/home/happy/Desktop/claude projects/VJLive3_The_Reckoning')
    board_path = root / 'BOARD.md'
    audit_path = root / 'docs/audit_report_comprehensive.json'
    
    with open(audit_path, 'r') as f:
        data = json.load(f)
        
    missing = data.get('missing_plugins', [])
    
    # deduplicate by class_name
    seen_classes = set()
    deduped = []
    
    # Prioritize those with a "name" (from manifest) over those just from file_scan
    # Sort them so that manifest items come first
    missing.sort(key=lambda x: 0 if 'name' in x else 1)
    
    for p in missing:
        cls_name = p.get('class_name')
        if not cls_name:
            continue
        if cls_name not in seen_classes:
            seen_classes.add(cls_name)
            deduped.append(p)
            
    print(f"Total deduplicated missing plugins: {len(deduped)}")
    
    # Read existing board 
    # WAIT: I need to remove the previously inserted section first
    with open(board_path, 'r') as f:
        board_content = f.read()
        
    if "### P9-MISSING: 490 Missing Legacy Plugins to Port" in board_content:
        # split and remove the previously injected section
        parts = board_content.split("### P9-MISSING: 490 Missing Legacy Plugins to Port")
        before = parts[0]
        # the section ends at "## Ongoing Quality Gates"
        after_parts = parts[1].split("## Ongoing Quality Gates")
        after = "## Ongoing Quality Gates" + after_parts[1]
        board_content = before + after
    
    # Build new section
    new_section = f"\n### P9-MISSING: {len(deduped)} Missing Legacy Plugins to Port\n\n"
    new_section += "| Task ID | Description | Priority | Status | Source |\n"
    new_section += "|---------|-------------|----------|--------|--------|\n"
    
    for i, p in enumerate(deduped, 1):
        task_id = f"P9-MISS{i:03d}"
        
        if 'name' in p:
            desc = f"{p['name']} ({p.get('class_name', '')})"
            source = f"Manifest ({p.get('collection', 'Unknown')})"
        else:
            file_name = p.get('file', 'Unknown')
            group = file_name.replace('.py', '')
            desc = f"{group} ({p.get('class_name', '')})"
            source = "File Scan"
            
        new_section += f"| {task_id} | {desc} | P0 | ⬜ Todo | {source} |\n"
        
    new_section += "\n"
    
    # Insert before "## Ongoing Quality Gates"
    target_str = "## Ongoing Quality Gates"
    
    if target_str in board_content:
        new_content = board_content.replace(target_str, new_section + target_str)
    else:
        new_content = board_content + new_section
        
    with open(board_path, 'w') as f:
        f.write(new_content)
        
    print(f"Mapped {len(deduped)} missing plugins to BOARD.md.")

if __name__ == "__main__":
    main()
