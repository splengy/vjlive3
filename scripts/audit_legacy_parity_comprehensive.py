#!/usr/bin/env python3
"""
Comprehensive Legacy Codebase Audit
Identifies ALL missing features from vjlive and VJlive-2 that need to be ported to VJLive3
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

# Base paths
VJLIVE_ROOT = Path("/home/happy/Desktop/claude projects/vjlive")
VJLIVE2_ROOT = Path("/home/happy/Desktop/claude projects/VJlive-2")
VJLIVE3_ROOT = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning")
BOARD_PATH = VJLIVE3_ROOT / "BOARD.md"
VJLIVE3_PLUGINS = VJLIVE3_ROOT / "src" / "vjlive3" / "plugins"

def extract_class_from_file(filepath):
    """Extract class definitions from a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # Find all class definitions
        classes = re.findall(r'class\s+(\w+)\s*\(', content)
        return classes
    except Exception as e:
        return []

def parse_manifest(manifest_path):
    """Parse a plugin manifest.json and extract module information"""
    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        modules = []
        for module in data.get('modules', []):
            modules.append({
                'id': module.get('id'),
                'name': module.get('name'),
                'class_name': module.get('class_name'),
                'category': module.get('category', 'unknown'),
                'description': module.get('description', ''),
                'module_type': module.get('module_type', 'effect')
            })
        return modules, data.get('name', 'Unknown'), data.get('id', 'unknown')
    except Exception as e:
        print(f"Error parsing {manifest_path}: {e}")
        return [], 'Unknown', 'unknown'

def scan_plugin_directory(plugins_dir):
    """Scan a plugins directory for Python files and extract classes"""
    plugins = []
    if not plugins_dir.exists():
        return plugins

    for py_file in plugins_dir.glob("*.py"):
        if py_file.name.startswith('_') or py_file.name == '__init__.py':
            continue
        classes = extract_class_from_file(py_file)
        for cls in classes:
            plugins.append({
                'file': py_file.name,
                'class_name': cls,
                'source': 'file_scan'
            })

    # Check for manifest.json
    manifest_path = plugins_dir / "manifest.json"
    if manifest_path.exists():
        manifest_modules, collection_name, collection_id = parse_manifest(manifest_path)
        for mod in manifest_modules:
            mod['source'] = 'manifest'
            mod['collection'] = collection_name
            mod['collection_id'] = collection_id
        plugins.extend(manifest_modules)

    return plugins

def read_current_vjlive3_plugins():
    """Read currently implemented plugins in VJLive3"""
    implemented = []
    for py_file in VJLIVE3_PLUGINS.glob("*.py"):
        if py_file.name.startswith('_') or py_file.name == '__init__.py':
            continue
        classes = extract_class_from_file(py_file)
        for cls in classes:
            implemented.append({
                'class_name': cls,
                'file': py_file.name,
                'source': 'vjlive3'
            })
    return implemented

def read_board_tasks():
    """Parse BOARD.md to extract existing task entries"""
    if not BOARD_PATH.exists():
        return []

    with open(BOARD_PATH, 'r') as f:
        content = f.read()

    # Extract task entries (lines starting with ### or similar)
    tasks = []
    current_phase = None
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('###'):
            # This is a task entry
            # Extract task ID and description
            match = re.search(r'###\s+([A-Z0-9\-]+):?\s*(.+)', line)
            if match:
                task_id = match.group(1)
                description = match.group(2)
                tasks.append({
                    'task_id': task_id,
                    'description': description,
                    'line': line
                })
        elif line.startswith('##'):
            # This is a phase header
            phase_match = re.search(r'##\s+(.+)', line)
            if phase_match:
                current_phase = phase_match.group(1)

    return tasks, current_phase

def main():
    print("=" * 80)
    print("COMPREHENSIVE LEGACY CODEBASE AUDIT")
    print("=" * 80)

    # Scan vjlive plugins
    print("\n[1] Scanning vjlive legacy codebase...")
    vjlive_plugins = []
    plugins_path = VJLIVE_ROOT / "plugins"
    if plugins_path.exists():
        for plugin_dir in sorted(plugins_path.glob("*")):
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                plugins = scan_plugin_directory(plugin_dir)
                vjlive_plugins.extend(plugins)
                print(f"  - {plugin_dir.name}: {len(plugins)} plugins found")
    else:
        print(f"  - vjlive plugins directory not found: {plugins_path}")

    # Scan VJlive-2 plugins
    print("\n[2] Scanning VJlive-2 legacy codebase...")
    vjlive2_plugins = []
    plugins_path = VJLIVE2_ROOT / "plugins"
    if plugins_path.exists():
        for plugin_dir in sorted(plugins_path.glob("*")):
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                plugins = scan_plugin_directory(plugin_dir)
                vjlive2_plugins.extend(plugins)
                print(f"  - {plugin_dir.name}: {len(plugins)} plugins found")
    else:
        print(f"  - VJlive-2 plugins directory not found: {plugins_path}")

    # Read current VJLive3 plugins
    print("\n[3] Reading VJLive3 currently implemented plugins...")
    vjlive3_plugins = read_current_vjlive3_plugins()
    print(f"  - Total implemented plugins: {len(vjlive3_plugins)}")

    # Read BOARD.md tasks
    print("\n[4] Reading BOARD.md task entries...")
    board_tasks, current_phase = read_board_tasks()
    print(f"  - Total tasks on board: {len(board_tasks)}")

    # Build sets for comparison
    vjlive_classes = {p['class_name'] for p in vjlive_plugins if 'class_name' in p}
    vjlive2_classes = {p['class_name'] for p in vjlive2_plugins if 'class_name' in p}
    vjlive3_classes = {p['class_name'] for p in vjlive3_plugins}

    # Identify missing plugins
    print("\n" + "=" * 80)
    print("AUDIT RESULTS")
    print("=" * 80)

    print(f"\nTotal Legacy Plugins:")
    print(f"  - vjlive: {len(vjlive_classes)} unique classes")
    print(f"  - VJlive-2: {len(vjlive2_classes)} unique classes")
    print(f"  - Combined unique: {len(vjlive_classes | vjlive2_classes)}")

    print(f"\nVJLive3 Status:")
    print(f"  - Already implemented: {len(vjlive3_classes)}")
    print(f"  - Missing from vjlive: {len(vjlive_classes - vjlive3_classes)}")
    print(f"  - Missing from VJlive-2: {len(vjlive2_classes - vjlive3_classes)}")
    print(f"  - Total missing (union): {len((vjlive_classes | vjlive2_classes) - vjlive3_classes)}")

    # Categorize missing plugins
    print("\n" + "=" * 80)
    print("MISSING PLUGINS BY CATEGORY")
    print("=" * 80)

    missing_plugins = []
    for plugin in vjlive_plugins + vjlive2_plugins:
        if 'class_name' in plugin and plugin['class_name'] not in vjlive3_classes:
            missing_plugins.append(plugin)

    # Group by category
    categories = defaultdict(list)
    for plugin in missing_plugins:
        cat = plugin.get('category', 'uncategorized')
        categories[cat].append(plugin)

    for cat in sorted(categories.keys()):
        plugins = categories[cat]
        print(f"\n{cat.upper()}: {len(plugins)} plugins")
        for p in sorted(plugins, key=lambda x: x.get('class_name', '')):
            coll = p.get('collection', 'Unknown')
            print(f"  - {p.get('class_name', 'Unknown')} ({coll})")

    # Enforce output directory
    output_dir = VJLIVE3_ROOT / "output"
    output_dir.mkdir(exist_ok=True)

    # 1. missing_plugins.csv
    csv_path = output_dir / "missing_plugins.csv"
    import csv
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Class Name', 'Category', 'Source File', 'Collection'])
        for p in missing_plugins:
            writer.writerow([
                p.get('class_name', 'Unknown'),
                p.get('category', 'uncategorized'),
                p.get('file', 'Unknown'),
                p.get('collection', 'Unknown')
            ])

    # 2. plugin_categorization.json
    json_path = output_dir / "plugin_categorization.json"
    categorization_data = {
        cat: [p.get('class_name', 'Unknown') for p in plugs]
        for cat, plugs in categories.items()
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(categorization_data, f, indent=2)

    # 3. priority_matrix.yaml
    yaml_path = output_dir / "priority_matrix.yaml"
    priority_data = {"phases": {
        "Phase 3: Depth & Spatiotemporal": categories.get("Depth", []) + categories.get("Spatiotemporal", []),
        "Phase 4: Audio Families & Generators": categories.get("Audio", []) + categories.get("Generator", []),
        "Phase 5: Datamosh & Glitch": categories.get("Datamosh", []) + categories.get("Glitch", []),
        "Phase 6: Quantum & AI": categories.get("Quantum", []) + categories.get("AI", []),
        "Phase 7: Utility & Core": categories.get("Utility", []) + categories.get("Core", [])
    }}
    
    # Write a simple YAML manually to avoid PyYAML dependency issues
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write("priority_matrix:\n")
        f.write("  phases:\n")
        for phase, plugins in priority_data["phases"].items():
            f.write(f"    '{phase}':\n")
            if not plugins:
                f.write("      []\n")
            for p in plugins:
                f.write(f"      - {p.get('class_name', 'Unknown')}\n")

    # Generate detailed report
    report_path = VJLIVE3_ROOT / "docs" / "audit_report_comprehensive.json"
    report = {
        'vjlive_total': len(vjlive_classes),
        'vjlive2_total': len(vjlive2_classes),
        'vjlive3_implemented': len(vjlive3_classes),
        'missing_total': len((vjlive_classes | vjlive2_classes) - vjlive3_classes),
        'missing_by_category': {cat: len(plugs) for cat, plugs in categories.items()},
        'missing_plugins': missing_plugins,
        'board_tasks_count': len(board_tasks)
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n\nFiles generated:")
    print(f"  - {report_path}")
    print(f"  - {csv_path}")
    print(f"  - {json_path}")
    print(f"  - {yaml_path}")

    print("\nNext steps:")
    print("  1. Review the audit report")
    print("  2. Update P0-INF2 specification with accurate counts")
    print("  3. Generate individual task entries for each missing plugin")
    print("  4. Populate BOARD.md with detailed tasks")
    print("  5. Create dispatch assignments (inbox files)")

    return report

if __name__ == "__main__":
    main()
