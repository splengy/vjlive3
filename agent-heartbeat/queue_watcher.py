#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
_logger = logging.getLogger("phase2_watcher")

# Add switchboard path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "vjlive_switchboard"))
from server import VJLiveSwitchboard

def watch_phase1_output():
    _logger.info("Initializing Phase 1 Skeleton Watcher...")
    sb = VJLiveSwitchboard()
    docs_dir = Path(__file__).resolve().parent.parent / "docs" / "specs"
    
    seen_tasks = set()
    
    # Pre-populate seen from the DB to avoid log spam on reboot
    sb._load_tasks_from_disk()
    for tid in sb._tasks:
        seen_tasks.add(tid)
        
    _logger.info("Watching %s for new Phase 1 skeletons. Press Ctrl+C to stop.", docs_dir)
    
    try:
        while True:
            new_count = 0
            for file in docs_dir.glob("*.md"):
                if file.name == "_TEMPLATE.md":
                    continue
                
                # Derive task ID from filename (e.g., P3-EXT001_spec.md -> P3-EXT001)
                task_id = file.stem.replace("_spec", "")
                
                if task_id not in seen_tasks:
                    spec_path = f"docs/specs/{file.name}"
                    ok = sb.queue_task(task_id, spec_path)
                    if ok:
                        _logger.info("✅ Discovered and queued new skeleton: %s", task_id)
                        seen_tasks.add(task_id)
                        new_count += 1
            
            if new_count > 0:
                _logger.info("Queued %d new tasks this cycle.", new_count)
                
            time.sleep(5)  # Scan every 5 seconds
            
    except KeyboardInterrupt:
        _logger.info("Watcher stopped by user.")

if __name__ == "__main__":
    watch_phase1_output()
