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
        
        if 'audio' in name_lower or 'audio' in file_lower or 'midi' in name_lower or 'osc' in name_lower:
            domains['Audio/MIDI/OSC Control'].append(entry)
        elif 'ai' in name_lower or 'agent' in name_lower or 'llm' in name_lower or 'neural' in name_lower or 'crowd' in name_lower:
            domains['AI/Agents/Crowd Analysis'].append(entry)
        elif 'quantum' in name_lower or 'consciousness' in name_lower or 'mood' in name_lower or 'semantic' in name_lower:
            domains['Quantum/Consciousness/Mood'].append(entry)
        elif 'hardware' in name_lower or 'camera' in name_lower or 'astra' in name_lower or 'realsense' in name_lower or 'vision' in name_lower or 'dmx' in name_lower:
            domains['Hardware/Cameras/DMX'].append(entry)
        elif 'video' in name_lower or 'hap' in name_lower or 'ndi' in name_lower or 'streaming' in name_lower:
            domains['Video/NDI/Streaming'].append(entry)
        elif 'web' in name_lower or 'socket' in name_lower or 'api' in name_lower or 'bridge' in name_lower or 'server' in name_lower:
            domains['Web/API/Networking'].append(entry)
        elif 'performance' in name_lower or 'monitor' in name_lower or 'profil' in name_lower or 'health' in name_lower or 'safety' in name_lower:
            domains['Performance/Health/Safety'].append(entry)
        elif 'shader' in name_lower or 'render' in name_lower or 'gl' in name_lower or 'texture' in name_lower:
            domains['Rendering/Shaders'].append(entry)
        elif 'state' in name_lower or 'config' in name_lower or 'save' in name_lower or 'snapshot' in name_lower or 'project' in name_lower:
            domains['State/Config/Projects'].append(entry)
        else:
            domains['Other Core Logic'].append(entry)

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
            
    print(f"Core logic parity report written to {out_path} with {len(missing_core)} items.")

if __name__ == "__main__":
    main()
