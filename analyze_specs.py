import os
import glob
import re
from collections import defaultdict

spec_dir = 'docs/specs/_02_fleshed_out'
files = glob.glob(os.path.join(spec_dir, '*.md'))

categories = defaultdict(int)
dependencies = defaultdict(list)

for file in files:
    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
        # Categorize by prefix
        filename = os.path.basename(file)
        if '-' in filename:
            prefix = filename.split('-')[0]
            categories[prefix] += 1
        else:
            categories['UNCATEGORIZED'] += 1
            
        # Extract potential module dependencies or major systems (very basic heuristic)
        if 'Audio' in content: dependencies['AudioSystem'].append(filename)
        if 'Depth' in content: dependencies['DepthSystem'].append(filename)
        if 'Quantum' in content: dependencies['QuantumSystem'].append(filename)
        if 'DMX' in content or 'ArtNet' in content: dependencies['LightingSystem'].append(filename)
        if 'Datamosh' in content: dependencies['DatamoshSystem'].append(filename)

print("=== Phase 3 Spec Audit ===")
print(f"Total Specs Found: {len(files)}")
print("\nCategories Count:")
for k, v in categories.items():
    print(f"  {k}: {v} specs")

print("\nMajor Subsystems Identified (Spec Count):")
for k, v in dependencies.items():
    print(f"  {k}: {len(v)} related specs")

print("\nTo build the Mermaid map, we have the following primary data clusters: Audio, Depth Tracking, Quantum/Consciousness Hooks, Video Datamoshing, and External Lighting Commands.")
