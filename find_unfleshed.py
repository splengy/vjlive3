import os
import glob

# Search in the following active directories
dirs_to_check = [
    "docs/specs/_01_skeletons",
    "docs/specs/_02_active_julie",
    "docs/specs/_03_active_maxx",
    "docs/specs/_02_active_desktop"
]

def check_if_fleshed_out(filepath):
    # Criteria for a fleshed out spec:
    # 1. More than just a few placeholders
    # 2. Contains substantial content under headers like "Detailed Behavior", "Public Interface", etc.
    # 3. Usually > 50 lines or > 2500 bytes (adjusting based on typical skeleton sizes)
    # A skeleton usually has less than 2000 bytes or around 30-40 lines of boilerplate
    
    try:
        size = os.path.getsize(filepath)
        if size < 2500:
            return False # Likely unfleshed
            
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        if len(lines) < 60:
            return False # Too short to be fully fleshed out
            
        # Check for placeholder markers (often empty sections)
        empty_sections = 0
        in_code_block = False
        empty_code_blocks = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('```'):
                in_code_block = not in_code_block
                if not in_code_block: # Closing block
                    pass
            elif in_code_block and line == 'pass':
                empty_code_blocks += 1
                
        if empty_code_blocks > 3: # Too many 'pass' statements in public interface
             return False
             
        return True
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

print("Scanning for unfleshed specs...")
found_unfleshed = []

for d in dirs_to_check:
    print(f"\nChecking directory: {d}")
    if not os.path.exists(d):
        print(f"  Directory not found.")
        continue
        
    md_files = glob.glob(os.path.join(d, "*.md"))
    print(f"  Found {len(md_files)} .md files.")
    
    for f in md_files:
        if not check_if_fleshed_out(f):
            found_unfleshed.append(f)
            print(f"  [UNFLESHED] {os.path.basename(f)} (Size: {os.path.getsize(f)} bytes)")
            
print(f"\nTotal unfleshed specs found in active/skeleton directories: {len(found_unfleshed)}")
