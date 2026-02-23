import os
from pathlib import Path

# The list of modules that were deleted
DELETED_MODULES = [
    "vjlive3.agents.manifold",
    "vjlive3.audio.source",
    "vjlive3.core.dmx.audio_dmx",
    "vjlive3.core.midi_controller",
    "vjlive3.core.signal_bus",
    "vjlive3.dmx.show_control",
    "vjlive3.llm.providers.openai",
    "vjlive3.plugins.api",
    "vjlive3.video.projection_mapper",
    "vjlive3.render.program",
    "vjlive3.llm.utils",
    "vjlive3.plugins.validator"
]

def clean_file(path: Path):
    try:
        content = path.read_text(encoding='utf-8')
        lines = content.split('\n')
        new_lines = []
        modified = False
        
        skip_mode = False
        for line in lines:
            if skip_mode:
                if ')' in line: # crude multiline import end
                    skip_mode = False
                continue
                
            has_deleted = False
            for mod in DELETED_MODULES:
                if f"import {mod}" in line or f"from {mod}" in line:
                    has_deleted = True
                    break
                    
            if has_deleted:
                modified = True
                if '(' in line and ')' not in line:
                    skip_mode = True # entering multiline import
                continue
                
            new_lines.append(line)
            
        if modified:
            path.write_text('\n'.join(new_lines), encoding='utf-8')
            print(f"Cleaned {path.name}")
    except Exception as e:
        print(f"Error processing {path}: {e}")

def main():
    root = Path("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning")
    for d in [root / "src", root / "tests"]:
        for f in d.rglob("*.py"):
            clean_file(f)

if __name__ == '__main__':
    main()
