import os
import re
from pathlib import Path

def main():
    specs_dir = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/docs/specs")
    legacy_keywords = [r'vjlive', r'legacy', r'\b(?:v1|v2)\b', r'vdepth', r'v-effects']
    pattern = re.compile('|'.join(legacy_keywords), re.IGNORECASE)

    deleted = []
    print("Deleting specs without legacy foundation:")
    for filepath in specs_dir.rglob('*.md'):
        if filepath.name == 'DEFINITION_OF_DONE.md': continue
        if filepath.name.startswith('_'): continue
        
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
            if not pattern.search(content):
                print(f" - {filepath.name}")
                filepath.unlink()
                deleted.append(filepath.name)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    with open("/tmp/deleted_specs_list.txt", "w") as f:
        f.write("\n".join(deleted))
    print(f"Total deleted specs: {len(deleted)}")

if __name__ == '__main__':
    main()
