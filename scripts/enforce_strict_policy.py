import os
import re
from pathlib import Path

def extract_class_from_file(filepath):
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        return set(re.findall(r'class\s+(\w+)\s*\(', content))
    except:
        return set()

def get_spec_from_comments(content):
    patterns = [
        r'#\s*Spec:\s*(.+\.md)',
        r'"""\s*Spec:\s*(.+\.md)',
        r'#\s*Source:\s*docs/specs/(.+\.md)',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            return [m.strip() for m in matches]
    return []

def main():
    root = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning")
    specs_dir = root / "docs/specs"
    src_dir = root / "src" / "vjlive3"
    board_path = root / "BOARD.md"

    # Step 1: Enforce legacy requirement on specs
    legacy_kw = [r'vjlive', r'legacy', r'\b(?:v1|v2)\b', r'vdepth', r'v-effects']
    legacy_pat = re.compile('|'.join(legacy_kw), re.IGNORECASE)
    
    deleted_specs = set()
    print("--- Enforcing Legacy-Basis on Specs ---")
    for spec in specs_dir.rglob('*.md'):
        if spec.name == 'DEFINITION_OF_DONE.md' or spec.name.startswith('_'): continue
        content = spec.read_text(encoding='utf-8', errors='ignore')
        if not legacy_pat.search(content):
            print(f"Deleting spec without legacy basis: {spec.name}")
            spec.unlink()
            deleted_specs.add(spec.name)

    # Step 2: Enforce spec requirement on code
    all_specs = [s.name for s in specs_dir.rglob('*.md')]
    deleted_py_files = []
    classes_to_revert = set()

    print("\n--- Enforcing Spec-Basis on Code ---")
    for py_file in src_dir.rglob('*.py'):
        if py_file.name == '__init__.py' or py_file.name.startswith('test_'): continue
        
        has_spec = False
        content = py_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check explicit comment references
        refs = get_spec_from_comments(content)
        for ref in refs:
            if not ref.endswith('.md'): ref += '.md'
            ref_name = Path(ref).name
            if ref_name in all_specs:
                has_spec = True
                break
                
        # If no valid comment ref, check by filename
        if not has_spec:
            stem = py_file.stem.lower()
            for s in all_specs:
                if stem in s.lower():
                    has_spec = True
                    break

        if not has_spec:
            print(f"Deleting code without an existing spec: {py_file.name}")
            classes = extract_class_from_file(py_file)
            classes_to_revert.update(classes)
            py_file.unlink()
            deleted_py_files.append(py_file.name)

    # Step 3: Update BOARD.md
    if board_path.exists() and classes_to_revert:
        print("\n--- Reverting Tasks in BOARD.md ---")
        lines = board_path.read_text(encoding='utf-8', errors='ignore').split('\n')
        new_lines = []
        reverted = 0
        for line in lines:
            if '✅ Done' in line:
                for cls in classes_to_revert:
                    if f"({cls})" in line or f"`{cls}`" in line or cls in line:
                        line = line.replace('✅ Done', '⬜ Todo')
                        line = re.sub(r'— .*?(?=\s*\|)', '', line)
                        reverted += 1
                        print(f"Reverted task for class: {cls}")
                        break
            new_lines.append(line)
        board_path.write_text('\n'.join(new_lines))
        print(f"Total reverted tasks: {reverted}")
        
    print(f"\nSummary:")
    print(f" - Deleted {len(deleted_specs)} specs lacking legacy basis.")
    print(f" - Deleted {len(deleted_py_files)} code files lacking spec.")

if __name__ == '__main__':
    main()
