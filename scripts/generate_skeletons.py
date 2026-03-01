#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.error
import time

BOARD_FILE = "BOARD.md"
OUTPUT_DIR = "docs/specs/_01_skeletons"
RKLLAMA_URL = "http://192.168.1.60:5050" # Julie spec_server.py

def get_pending_skeletons():
    pending = []
    try:
        # Read the file directly to memory to avoid any locking hangups
        with open(BOARD_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            if "PENDING SKELETON" in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    task_id = parts[1]
                    module_raw = parts[2]
                    
                    if "(" in module_raw:
                        module_name = module_raw.split("(")[1].replace(")", "").strip()
                    else:
                        module_name = module_raw
                        
                    pending.append((task_id, module_name))
    except Exception as e:
        print(f"Error reading BOARD.md: {e}")
        
    return pending

def generate_spec_via_npu(task_id, module_name):
    filename = f"{OUTPUT_DIR}/{task_id}_{module_name}.md"
    if os.path.exists(filename):
        print(f"  Skipping {task_id} — {filename} already exists")
        return True
        
    print(f"  Generating {task_id} — {module_name} via NPU...")
    
    prompt = f"""You are writing a technical specification for VJLive3, a real-time Python/OpenGL visual performance application. Each plugin processes video frames at 60 FPS.

This is a PLUGIN — it extends the visual pipeline with a specific effect.

Write a spec for: {module_name} (Task ID: {task_id})

Use EXACTLY this format with ALL sections:

## Task: {task_id} -- {module_name}

**What This Module Does**
2-3 sentences. What visual effect does it produce?

---

## Public Interface

```python
# Class extending EffectPlugin with process_frame method
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|

---

## What This Module Does NOT Do
- Scope boundaries

---

## Dependencies
- External and internal

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|

**Minimum coverage:** 80%

---

## Definition of Done
- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs
"""

    payload = {
        "prompt": prompt,
        "max_tokens": 2048
    }
    
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{RKLLAMA_URL}/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            response = result.get("response", "")
            
            if response:
                with open(filename, 'w') as f:
                    f.write(response)
                print(f"  ✅ Saved {filename}")
                return True
            else:
                print(f"  ❌ NPU returned empty response")
                return False
                
    except urllib.error.URLError as e:
        print(f"  ❌ NPU API unreachable: {e}")
        return False
    except TimeoutError:
        print(f"  ❌ NPU API timeout")
        return False
    except Exception as e:
        print(f"  ❌ Generation failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting skeleton generation...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pending = get_pending_skeletons()
    print(f"Found {len(pending)} pending skeletons in {BOARD_FILE}")
    
    if len(pending) == 0:
        print("Nothing to do.")
        sys.exit(0)
        
    # Process only the first 5 for now to test the NPU integration
    count = 0
    for task_id, module_name in pending[:5]:
        if generate_spec_via_npu(task_id, module_name):
            count += 1
        time.sleep(2) # Give the NPU a breather
            
    print(f"\nSuccessfully generated {count} skeletons via NPU.")
