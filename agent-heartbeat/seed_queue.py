#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add switchboard path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "vjlive_switchboard"))
from server import VJLiveSwitchboard

def seed_p3_queue():
    sb = VJLiveSwitchboard()
    docs_dir = Path(__file__).resolve().parent.parent / "docs" / "specs"
    
    count = 0
    for file in sorted(docs_dir.glob("P3-*.md")):
        task_id = file.stem.replace("_spec", "")
        spec_path = f"docs/specs/{file.name}"
        
        ok = sb.queue_task(task_id, spec_path)
        if ok:
            print(f"✅ Queued: {task_id}")
            count += 1
        else:
            print(f"⚠️ Skipped: {task_id} (already queued or completed)")
            
    print(f"\n🎉 Successfully seeded {count} tasks for Pass 3 Refinement!")

if __name__ == "__main__":
    seed_p3_queue()
