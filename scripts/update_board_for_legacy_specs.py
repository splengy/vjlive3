import re
from pathlib import Path

def main():
    board_path = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md")
    deleted_specs_path = Path("/tmp/deleted_specs_list.txt")
    
    if not deleted_specs_path.exists():
        print("No deleted specs list found.")
        return
        
    specs = [s.strip() for s in deleted_specs_path.read_text().split('\n') if s.strip()]
    task_ids = [s.split('_')[0] for s in specs] # e.g. P1-A1
    
    lines = board_path.read_text().split('\n')
    new_lines = []
    updated = 0
    
    for line in lines:
        matched = False
        if line.strip().startswith('|'):
            # Check if this line corresponds to one of the deleted specs or its task ID
            for tid, spec_name in zip(task_ids, specs):
                # Ensure we match the exact task ID column, e.g. | P1-A1 |
                if f"| {tid} |" in line or spec_name in line:
                    matched = True
                    # Revert to Todo
                    line = line.replace('✅ Done', '⬜ Todo')
                    line = line.replace('🔄 In Progress', '⬜ Todo')
                    # Replace the entire notes/status implementation cell with "Needs new legacy-based spec"
                    # A board row looks like: | Task ID | Desc | Priority | Status | Notes |
                    # or | Task ID | Desc | Status | Notes |
                    parts = line.split('|')
                    if len(parts) >= 5:
                        parts[-2] = " Needs new legacy-based spec "
                        line = '|'.join(parts)
                    break
        if matched:
            updated += 1
            print(f"Updated Board Line: {line}")
        new_lines.append(line)
        
    board_path.write_text('\n'.join(new_lines))
    print(f"Updated {updated} lines in BOARD.md to reflect need for new specs.")

if __name__ == '__main__':
    main()
