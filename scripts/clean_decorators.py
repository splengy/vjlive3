import os
from pathlib import Path

def clean_file(path: Path):
    try:
        content = path.read_text(encoding='utf-8')
        lines = content.split('\n')
        new_lines = []
        modified = False
        
        for line in lines:
            if '@register_plugin' in line:
                modified = True
                continue
            new_lines.append(line)
            
        if modified:
            path.write_text('\n'.join(new_lines), encoding='utf-8')
            print(f"Scrubbed @register_plugin from {path.name}")
    except Exception as e:
        print(f"Error processing {path}: {e}")

def main():
    root = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning")
    for d in [root / "src", root / "tests"]:
        for f in d.rglob("*.py"):
            clean_file(f)

if __name__ == '__main__':
    main()
