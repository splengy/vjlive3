#!/usr/bin/env python3
"""
Spec-First Enforcement Hook

Verifies that any code change in src/vjlive3/ has an associated spec document
in docs/specs/ before allowing the commit.

This enforces the PRIME_DIRECTIVE: "SPEC must exist before code."
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# Pattern to match task/spec references in code
# Looking for comments like: # Spec: P1-P2_plugin_loader.md
# or docstrings mentioning spec files
SPEC_REF_PATTERNS = [
    r'#\s*Spec:\s*(.+\.md)',
    r'"""\s*Spec:\s*(.+\.md)',
    r'"""\s*Source:\s*docs/specs/(.+\.md)',
    r'#\s*Source:\s*docs/specs/(.+\.md)',
    r'#\s*Task:\s*(P\d+-[A-Z]\d+)',
]

# Map task IDs to spec file paths (maintain this manually or generate from BOARD.md)
TASK_TO_SPEC = {
    # Phase 1 Rendering
    'P1-R1': 'docs/specs/P1-R1_opengl_context.md',
    'P1-R2': 'docs/specs/P1-R2_gpu_pipeline.md',
    'P1-R3': 'docs/specs/P1-R3_shader_compiler.md',
    'P1-R4': 'docs/specs/P1-R4_texture_manager.md',
    'P1-R5': 'docs/specs/P1-R5_render_engine.md',
    
    # Phase 1 Audio
    'P1-A1': 'docs/specs/P1-A1_audio_analyzer.md',
    'P1-A2': 'docs/specs/P1-A2_beat_detector.md',
    'P1-A3': 'docs/specs/P1-A3_reactivity_bus.md',
    'P1-A4': 'docs/specs/P1-A4_audio_sources.md',
    
    # Phase 1 Node Graph
    'P1-N1': 'docs/specs/P1-N1_node_registry.md',
    'P1-N2': 'docs/specs/P1-N2_node_types.md',
    'P1-N3': 'docs/specs/P1-N3_state_persistence.md',
    'P1-N4': 'docs/specs/P1-N4_node_graph_ui.md',
    
    # Phase 1 Plugin System
    'P1-P1': 'docs/specs/P1-P1_plugin_registry.md',
    'P1-P2': 'docs/specs/P1-P2_plugin_loader.md',
    'P1-P3': 'docs/specs/P1-P3_plugin_hot_reload.md',
    'P1-P4': 'docs/specs/P1-P4_plugin_scanner.md',
    'P1-P5': 'docs/specs/P1-P5_plugin_sandbox.md',
    
    # Phase 2 Hardware
    'P2-H1': 'docs/specs/P2-H1_midi_controller.md',
    'P2-H2': 'docs/specs/P2-H2_oscquery.md',
    'P2-H3': 'docs/specs/P2-H3_astra.md',
    'P2-H4': 'docs/specs/P2-H4_ndi.md',
    'P2-H5': 'docs/specs/P2-H5_spout.md',
    'P2-H6': 'docs/specs/P2-H6_gamepad.md',
    'P2-H7': 'docs/specs/P2-H7_laser_safety.md',
    
    # Phase 2 Distributed
    'P2-X1': 'docs/specs/P2-X1_zmq_coordinator.md',
    'P2-X2': 'docs/specs/P2-X2_timecode_sync.md',
    'P2-X3': 'docs/specs/P2-X3_output_mapper.md',
    'P2-X4': 'docs/specs/P2-X4_projection_mapping.md',
    
    # Phase 2 DMX
    'P2-D1': 'docs/specs/P2-D1_dmx_engine.md',
    'P2-D2': 'docs/specs/P2-D2_artnet_output.md',
    'P2-D3': 'docs/specs/P2-D3_dmx_fx.md',
    'P2-D4': 'docs/specs/P2-D4_show_control.md',
    'P2-D5': 'docs/specs/P2-D5_audio_dmx.md',
    'P2-D6': 'docs/specs/P2-D6_dmx_websocket.md',
}

def find_spec_references(content: str) -> List[str]:
    """Extract spec file references from code content."""
    references = []
    for pattern in SPEC_REF_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        references.extend(matches)
    return references

def spec_file_exists(spec_path: str) -> bool:
    """Check if a spec file exists in the repository."""
    # Try relative to repo root
    repo_root = Path(__file__).parent.parent
    full_path = repo_root / spec_path
    return full_path.exists()

def task_id_to_spec(task_id: str) -> str:
    """Convert task ID to spec file path."""
    task_id = task_id.upper()
    if task_id in TASK_TO_SPEC:
        return TASK_TO_SPEC[task_id]
    # Try to construct path: docs/specs/{task_id}.md
    constructed = f'docs/specs/{task_id}.md'
    return constructed

def validate_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate a single Python file has spec reference."""
    errors = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return False, [f"Failed to read {file_path}: {e}"]
    
    # Find all spec references
    spec_refs = find_spec_references(content)
    
    # Also check for task ID references
    task_id_pattern = r'#\s*Task:\s*(P\d+-[A-Z]\d+)'
    task_matches = re.findall(task_id_pattern, content, re.IGNORECASE)
    
    if task_matches:
        for task_id in task_matches:
            spec_path = task_id_to_spec(task_id)
            if not spec_file_exists(spec_path):
                errors.append(f"Task {task_id} references missing spec: {spec_path}")
    
    # Check if any spec files referenced actually exist
    for spec_ref in spec_refs:
        # Clean up the path
        spec_path = spec_ref.strip()
        if not spec_path.endswith('.md'):
            spec_path += '.md'
        
        if not spec_file_exists(spec_path):
            errors.append(f"Referenced spec not found: {spec_path}")
    
    # If no spec references found, that's an error
    if not spec_refs and not task_matches:
        errors.append("No spec reference found in code. Add a comment like '# Spec: docs/specs/P1-P2_plugin_loader.md' or '# Task: P1-P2'")
    
    return len(errors) == 0, errors

def main() -> int:
    """Main entry point for pre-commit hook."""
    # Get list of files to check from pre-commit
    # If no files specified, check all Python files in src/
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:] if f.endswith('.py')]
    else:
        # Check all Python files in src/vjlive3/
        repo_root = Path(__file__).parent.parent
        src_dir = repo_root / 'src' / 'vjlive3'
        files = list(src_dir.rglob('*.py'))
    
    if not files:
        print("No Python files to check")
        return 0
    
    # Exclude test files and __pycache__
    files = [f for f in files if 'test_' not in f.name and '__pycache__' not in str(f)]
    
    all_valid = True
    all_errors = []
    
    for file_path in files:
        valid, errors = validate_file(file_path)
        if not valid:
            all_valid = False
            all_errors.append(f"\n{file_path}:")
            for error in errors:
                all_errors.append(f"  ❌ {error}")
    
    if not all_valid:
        print("\n" + "="*60)
        print("❌ SPEC-FIRST VIOLATION DETECTED")
        print("="*60)
        print("\nAll code changes must reference an existing spec document.")
        print("Add one of these to your code:")
        print("  - '# Spec: docs/specs/P1-P2_plugin_loader.md'")
        print("  - '# Task: P1-P2'")
        print("  - Docstring with 'Spec:' or 'Source:' reference")
        print("\nFailed files:")
        for error in all_errors:
            print(error)
        print("\n" + "="*60)
        return 1
    
    print(f"✅ Spec compliance verified for {len(files)} files")
    return 0

if __name__ == "__main__":
    sys.exit(main())