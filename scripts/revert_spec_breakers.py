import re
import os
from pathlib import Path

def extract_class_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        classes = re.findall(r'class\s+(\w+)\s*\(', content)
        return classes
    except:
        return []

def main():
    root_dir = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning")
    board_path = root_dir / "BOARD.md"
    check_output = Path("/tmp/spec_check.txt")
    
    if not check_output.exists():
        print("No spec check output found.")
        return
        
    lines = check_output.read_text().split('\n')
    files_to_delete = []
    
    # Extract file paths from the output
    for line in lines:
        if line.endswith(':'):
            filepath = line[:-1]
            if filepath.endswith('.py') and os.path.exists(filepath):
                files_to_delete.append(Path(filepath))
                
    if not files_to_delete:
        print("No files to delete.")
        return
        
    print(f"Found {len(files_to_delete)} files without specs.")
    
    classes_to_revert = set()
    for fp in files_to_delete:
        classes = extract_class_from_file(fp)
        classes_to_revert.update(classes)
        print(f"Deleting {fp.name} (Classes: {classes})")
        # Delete the file
        fp.unlink()
        
    # Update BOARD.md
    if board_path.exists():
        board_content = board_path.read_text()
        
        lines = board_content.split('\n')
        new_lines = []
        reverted_count = 0
        
        for line in lines:
            if '✅ Done' in line:
                # Check if any of the classes are in this line
                for cls in classes_to_revert:
                    if f"({cls})" in line or f"`{cls}`" in line or cls in line:
                        line = line.replace('✅ Done', '⬜ Todo')
                        # Remove the implementation details after the status if it's there
                        line = re.sub(r'— .*?(?=\s*\|)', '', line)
                        reverted_count += 1
                        print(f"Reverted task in BOARD.md for class {cls}")
                        break
            new_lines.append(line)
            
        board_path.write_text('\n'.join(new_lines))
        print(f"Reverted {reverted_count} lines in BOARD.md")

if __name__ == '__main__':
    main()
