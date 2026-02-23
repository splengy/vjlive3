#!/usr/bin/env python3
import os
import ast
import re
from collections import defaultdict

LEGACY_CORES = [
    "/home/happy/Desktop/claude projects/vjlive/core",
    "/home/happy/Desktop/claude projects/VJlive-2/core"
]

NEW_CORE_DIR = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/src/vjlive3"

def get_python_files(directory):
    files_list = []
    for root, _, files in os.walk(directory):
        if '__pycache__' in root or 'venv' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                files_list.append(os.path.join(root, f))
    return files_list

def extract_classes_and_docs(filepath):
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node) or ""
                    results.append({
                        'name': node.name,
                        'doc': docstring,
                        'file': os.path.basename(filepath)
                    })
    except Exception as e:
        pass
    return results

def main():
    print("Gathering legacy core classes...")
    legacy_classes = {}
    for core_dir in LEGACY_CORES:
        if not os.path.exists(core_dir):
            continue
        for py_file in get_python_files(core_dir):
            classes = extract_classes_and_docs(py_file)
            for c in classes:
                # Deduplicate by name
                if c['name'] not in legacy_classes:
                    legacy_classes[c['name']] = c
                elif len(c['doc']) > len(legacy_classes[c['name']]['doc']):
                    legacy_classes[c['name']] = c

    print(f"Found {len(legacy_classes)} unique classes across legacy cores.")

    print("Gathering VJLive3 core classes...")
    vjlive3_classes = set()
    vjlive3_files = get_python_files(NEW_CORE_DIR)
    vjlive3_content = ""
    
    for py_file in vjlive3_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                vjlive3_content += content.lower() + "\n"
            
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    vjlive3_classes.add(node.name.lower())
        except:
            pass
            
    # Load BOARD.md as well
    board_path = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md"
    try:
        with open(board_path, 'r', encoding='utf-8') as f:
            board_content = f.read().lower()
    except:
        board_content = ""

    missing_core = []
    
    # Filter 1: Common noise/base classes
    noise_words = ['exception', 'error', 'test', 'mock', 'dummy', 'base']
    
    for name, data in legacy_classes.items():
        name_lower = name.lower()
        
        # Skip purely noisy structural classes
        if any(w in name_lower for w in noise_words):
            continue
            
        # Is the class name directly in VJLive3?
        if name_lower in vjlive3_classes:
            continue
            
        # Break name into words
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', name)
        words_lower = [w.lower() for w in words]
        
        # If it's a manager, engine, or system, it's highly important core logic
        is_important = any(w in name_lower for w in ['manager', 'engine', 'system', 'coordinator', 'bridge', 'pipeline', 'nexus', 'ai', 'quantum', 'agent', 'consciousness'])
        
        # Heuristic: if the exact name isn't in vjlive3 content and isn't mentioned in BOARD.md
        if name_lower not in vjlive3_content and name_lower not in board_content:
            missing_core.append(data)

    # Grouping by semantic domain based on keywords in filename or name
    domains = defaultdict(list)
    for c in missing_core:
        name_lower = c['name'].lower()
        file_lower = c['file'].lower()
        
        doc_preview = c['doc'][:150].replace('\n', ' ') + '...' if c['doc'] else 'No docstring.'
        entry = f"- **{c['name']}** (`{c['file']}`): {doc_preview}"
        
        domain = 'Other Core Logic'
        if 'audio' in name_lower or 'audio' in file_lower or 'midi' in name_lower or 'osc' in name_lower:
            domain = 'Audio/MIDI/OSC Control'
        elif 'ai' in name_lower or 'agent' in name_lower or 'llm' in name_lower or 'neural' in name_lower or 'crowd' in name_lower:
            domain = 'AI/Agents/Crowd Analysis'
        elif 'quantum' in name_lower or 'consciousness' in name_lower or 'mood' in name_lower or 'semantic' in name_lower:
            domain = 'Quantum/Consciousness/Mood'
        elif 'hardware' in name_lower or 'camera' in name_lower or 'astra' in name_lower or 'realsense' in name_lower or 'vision' in name_lower or 'dmx' in name_lower:
            domain = 'Hardware/Cameras/DMX'
        elif 'video' in name_lower or 'hap' in name_lower or 'ndi' in name_lower or 'streaming' in name_lower:
            domain = 'Video/NDI/Streaming'
        elif 'web' in name_lower or 'socket' in name_lower or 'api' in name_lower or 'bridge' in name_lower or 'server' in name_lower:
            domain = 'Web/API/Networking'
        elif 'performance' in name_lower or 'monitor' in name_lower or 'profil' in name_lower or 'health' in name_lower or 'safety' in name_lower:
            domain = 'Performance/Health/Safety'
        elif 'shader' in name_lower or 'render' in name_lower or 'gl' in name_lower or 'texture' in name_lower:
            domain = 'Rendering/Shaders'
        elif 'state' in name_lower or 'config' in name_lower or 'save' in name_lower or 'snapshot' in name_lower or 'project' in name_lower:
            domain = 'State/Config/Projects'
            
        c['domain'] = domain
        domains[domain].append(entry)

    out_path = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/WORKSPACE/COMMS/STATUS/CORE_LOGIC_PARITY.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Parity Analysis: Missed Core Logic Concepts\n\n")
        f.write("> **Directives:** This audit focuses exclusively on the `core/` infrastructure of the legacy codebases. These represent advanced architectural concepts, overarching state managers, specialized hardware bridges, and intelligent agent integrations that have not yet been ported or mapped onto `BOARD.md`.\n\n")
        
        for domain, entries in sorted(domains.items()):
            if not entries: continue
            f.write(f"## {domain}\n")
            for e in sorted(entries):
                f.write(f"{e}\n")
            f.write("\n")

    import json
    import csv
    output_dir = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/output"
    os.makedirs(output_dir, exist_ok=True)
    
    csv_path = os.path.join(output_dir, "core_logic_audit.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Class Name', 'Domain', 'File Path', 'Docstring'])
        for c in missing_core:
            writer.writerow([c['name'], c['domain'], c['file'], c.get('doc', '')])
            
    json_path = os.path.join(output_dir, "core_logic_categories.json")
    category_dict = defaultdict(list)
    for c in missing_core:
        category_dict[c['domain']].append(c['name'])
        
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(category_dict, f, indent=2)
        
    yaml_path = os.path.join(output_dir, "implementation_roadmap.yaml")
    phases = {
        "Phase 1: Core Systems, State & APIs": [],
        "Phase 2: Hardware, DMX & Distributed Nodes": [],
        "Phase X: Future Extensions": []
    }
    for c in missing_core:
        d = c['domain']
        if d in ['State/Config/Projects', 'Web/API/Networking', 'Performance/Health/Safety', 'Other Core Logic', 'Rendering/Shaders']:
            phases["Phase 1: Core Systems, State & APIs"].append(c['name'])
        elif d in ['Hardware/Cameras/DMX', 'Video/NDI/Streaming', 'Audio/MIDI/OSC Control']:
            phases["Phase 2: Hardware, DMX & Distributed Nodes"].append(c['name'])
        else:
            phases["Phase X: Future Extensions"].append(c['name'])
            
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write("implementation_roadmap:\n")
        f.write("  phases:\n")
        for phase, items in phases.items():
            f.write(f"    '{phase}':\n")
            if not items:
                f.write("      []\n")
            for item in sorted(set(items)):
                f.write(f"      - {item}\n")
                
    print(f"Core logic parity report written to {out_path} with {len(missing_core)} items.")
    print("Core logic audit output datasets written to output/ directory.")

if __name__ == "__main__":
    main()
