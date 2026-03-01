#!/usr/bin/env python3
import os
import sys

BOARD_FILE = "BOARD.md"
OUTPUT_DIR = "docs/specs/_01_skeletons"

def get_pending_skeletons():
    pending = []
    with open(BOARD_FILE, 'r') as f:
        for line in f:
            if "| PENDING SKELETON" in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    task_id = parts[1]
                    module_name = parts[2]
                    pending.append((task_id, module_name))
    return pending

def generate_skeleton(task_id, module_name):
    filename = f"{OUTPUT_DIR}/{task_id}_{module_name}.md"
    if os.path.exists(filename):
        return False
        
    print(f"Creating basic skeleton for {task_id} - {module_name}...")
    
    # We will generate a very basic skeleton for the Roo workers to enrich.
    # The true "first pass" RKLLM script is currently bound to Qdrant/Rkllama on Julie
    # Since we can't easily trigger the remote agent from here without messy SSH,
    # we will generate the basic markdown templates locally so the heartbeat daemon
    # can distribute them to the NPUs for "Pass 2". 
    
    skeleton = f"""# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/{task_id}_{module_name}.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: {task_id} — {module_name}

**What This Module Does**

**What This Module Does NOT Do**

---

## Detailed Behavior and Parameter Interactions

---

## Public Interface

---

## Inputs and Outputs

---

## Edge Cases and Error Handling

---

## Mathematical Formulations

---

## Performance Characteristics

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] {task_id}: {module_name}` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  
"""
    with open(filename, 'w') as f:
        f.write(skeleton)
    return True

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pending = get_pending_skeletons()
    print(f"Found {len(pending)} pending skeletons in BOARD.md")
    
    count = 0
    for task_id, module_name in pending:
        # Strip parens from module_name if present e.g. "ascii_effect (ASCIIEffect)"
        if "(" in module_name:
            module_name = module_name.split("(")[1].replace(")", "").strip()
            
        if generate_skeleton(task_id, module_name):
            count += 1
            
    print(f"\nGenerated {count} new skeleton templates in {OUTPUT_DIR}/")
    print("These will now be picked up by the Roo workers (rkllms) for Pass 2 enrichment.")
