import os
import shutil
import time
from pathlib import Path

def main():
    root = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning")
    specs_dir = root / "docs/specs"
    trash_dir = root / "WORKSPACE/TRASH_CAN"
    trash_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    agent_name = "antigravity"
    
    # We generated files today. Let's find files modified in the last 4 hours 
    # (since this session started).
    current_time = time.time()
    four_hours_ago = current_time - (4 * 3600)
    
    moved_count = 0
    specs_moved = []
    
    for filepath in specs_dir.glob("*.md"):
        # Don't delete the template
        if filepath.name == "_TEMPLATE.md":
            continue
            
        mtime = filepath.stat().st_mtime
        if mtime > four_hours_ago:
            # It's one of ours from today
            new_name = f"{filepath.name}.deletion-request.{agent_name}.{timestamp}"
            dest = trash_dir / new_name
            shutil.move(str(filepath), str(dest))
            specs_moved.append(filepath.name)
            moved_count += 1
            
    # Also move the batch scripts we wrote
    scripts_to_remove = [
        "generate_missing_specs.py",
        "generate_rich_specs.py",
        "generate_rich_specs_fuzzy.py",
        "flesh_out_specs.py",
        "list_unmatched_tasks.py",
        "run_spec_audit.py",
        "inject_legacy_references.py",
        "create_spec_audit_checklist.py",
        "map_remaining_core_logic.py"
    ]
    
    scripts_dir = root / "scripts"
    for script_name in scripts_to_remove:
        script_path = scripts_dir / script_name
        if script_path.exists():
            new_name = f"{script_path.name}.deletion-request.{agent_name}.{timestamp}"
            dest = trash_dir / new_name
            shutil.move(str(script_path), str(dest))
            
    # Write the deletion note
    note_path = trash_dir / f"deletion-note-{timestamp}.txt"
    note_content = f"""Deletion Request Note
Agent: {agent_name}
Timestamp: {timestamp}

Why: These {moved_count} spec files and the associated generation scripts were the result of an unauthorized batch-processing operation. Batch processing violates Rule 4 (Bespoke Snowflakes) and Rule 10 of the PRIME_DIRECTIVE. The generated specs were accurately identified as "garbage" because they lacked the bespoke, human-level analysis required for each unique module port. 

Task Prompting Deletion: Manager feedback directly cited the batch generation as producing garbage code and violating the Prime Directive.

List of affected files moved here:
""" + "\n".join(specs_moved)
    
    note_path.write_text(note_content, encoding='utf-8')
    print(f"Moved {moved_count} garbage specs and {len(scripts_to_remove)} illegal batch scripts to TRASH_CAN.")
    
if __name__ == "__main__":
    main()
