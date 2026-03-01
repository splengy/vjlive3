import os
import glob

spec_dir = "docs/specs/_02_fleshed_out"
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
        code_blocks = content.count('```python')
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

print(f"Validating quality of {len(md_files)} fleshed out specs...")
poor_quality = 0

for f in md_files:
    # Skip template or hidden files
    if os.path.basename(f).startswith('_'): continue
    
    issues = analyze_quality(f)
    if issues:
        poor_quality += 1
        print(f"⚠️ {os.path.basename(f)}")
        for i in issues:
            print(f"   - {i}")

print(f"\nTotal specs with quality warnings: {poor_quality} out of {len(md_files)}")
