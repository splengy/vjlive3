import os
import shutil
import glob

spec_dir = "docs/specs/_02_fleshed_out"
dest_dir = "docs/specs/_01_skeletons"
os.makedirs(dest_dir, exist_ok=True)
md_files = glob.glob(os.path.join(spec_dir, "*.md"))

def analyze_quality(filepath):
    issues = []
    try:
        size = os.path.getsize(filepath)
        if size < 2000:
            issues.append(f"Too small ({size} bytes)")
            
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        lines = content.split('\n')
        if len(lines) < 50:
            issues.append(f"Too short ({len(lines)} lines)")
            
        # Check required sections
        required_headers = [
            ("Detailed Behavior", "What It Does"),
            ("Public Interface", "Interface"),
            ("Definition of Done", "DoD")
        ]
        
        for primary, alt in required_headers:
            if primary not in content and alt not in content:
                issues.append(f"Missing section: {primary}")
                
        # Check for empty python pass
        pass_count = content.count('    pass\n')
        if pass_count > 5:
            issues.append(f"Too many 'pass' stubs ({pass_count} found)")
            
        # Check DoD completion
        if "Definition of Done" in content:
            unchecked = content.count("- [ ]")
            if unchecked > 0:
                issues.append(f"{unchecked} unchecked DoD items")
                
        return issues
    except Exception as e:
        return [f"Error reading file: {e}"]

print(f"Scanning and returning poor quality specs to {dest_dir}...")
moved_count = 0

for f in md_files:
    # Skip template or hidden files
    if os.path.basename(f).startswith('_'): continue
    
    issues = analyze_quality(f)
    if issues:
        dest_path = os.path.join(dest_dir, os.path.basename(f))
        try:
            shutil.move(f, dest_path)
            moved_count += 1
        except Exception as e:
            print(f"Failed to move {os.path.basename(f)}: {e}")

print(f"\nTotal specs returned to _01_skeletons: {moved_count}")
print(f"Remaining perfect specs in _02_fleshed_out: {len(glob.glob(os.path.join(spec_dir, '*.md')))}")
