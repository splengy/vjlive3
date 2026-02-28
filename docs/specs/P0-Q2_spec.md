# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P0-Q2_check_file_size.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-Q2 — check_file_size

**Phase:** Phase 0 / P0  
**Assigned To:** Alex Turner  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-05

---

## What This Module Does

This module validates that files in a specified directory meet minimum size thresholds. It is used during plugin manifest audits to ensure configuration files are not empty or malformed, preventing runtime errors due to missing or corrupted data. The output is a list of files that fail the size check with their path and size.

---

## What It Does NOT Do

- It does not validate file content (e.g., syntax, structure).  
- It does not perform checksums or integrity checks.  
- It does not modify files or delete invalid ones.  
- It does not support remote file systems or network paths.  

---

## Public Interface

```python
# Paste planned class/function signatures here before coding

def check_file_size(
    directory: str,
    min_size: int = 1024,
    max_size: int = 1073741824,  # 1GB
) -> list[dict[str, str]]:
    """
    Validates file sizes in a given directory.

    Args:
        directory: Path to the directory containing files to check.
        min_size: Minimum acceptable size in bytes (default: 1024).
        max_size: Maximum acceptable size in bytes (default: 1GB).

    Returns:
        List of dictionaries with keys 'path' and 'size', for files that fail size checks.
    """
```

---

## Inputs and Outputs

| Name       | Type   | Description                                  | Constraints |
|------------|--------|----------------------------------------------|-------------|
| `directory` | `str`  | Path to the directory being audited         | Must be absolute or relative, must exist; if not, raises FileNotFoundError |
| `min_size`  | `int`  | Minimum file size in bytes                 | Must be ≥ 0. Default: 1024 (1KB) |
| `max_size`  | `int`  | Maximum file size in bytes                | Must be > 0. Default: 1073741824 (1GB) |
| return      | `list[dict]` | List of failed files with 'path' and 'size' keys | Empty list if all files pass |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → [NEEDS RESEARCH]  
- What happens on bad input? → Raises `ValueError` for invalid size values or `FileNotFoundError` if directory does not exist.  
- What is the cleanup path? → No external resources are held; no cleanup required.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `os.path`, `pathlib` — used for file system operations — fallback: built-in Python modules  
- Internal modules this depends on:  
  - [None]  

---

## Test Plan

| Test Name                     | What It Verifies |
|------------------------------|------------------|
| `test_check_file_size_valid` | Core function returns correct list of files when all sizes are within bounds |
| `test_check_file_size_min_exceeded` | Returns file when size is below min threshold |
| `test_check_file_size_max_exceeded` | Returns file when size exceeds max threshold |
| `test_check_file_size_nonexistent_dir` | Raises FileNotFoundError if directory does not exist |
| `test_check_file_size_invalid_input` | Raises ValueError for negative or zero min/max sizes |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-Q2: check_file_size module for manifest validation` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 0, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### vjlive1/JUNK/one_off_scripts/_audit_params.py (L1-20)
```python
#!/usr/bin/env python3
"""Audit all plugin manifests for non-conforming float parameter ranges."""
import json, os, glob

results = {}
conforming = []

for mf in sorted(glob.glob('plugins/*/manifest.json')):
    plugin = mf.split('/')[1]
    with open(mf) as f:
        data = json.load(f)
    
    non_conforming = []
    for mod in data.get('modules', []):
        for param in mod.get('parameters', []):
            ptype = param.get('type', '')
            pmax = param.get('max')
            pmin = param.get('min')
            pid = param.get('id', '?')
            
```

### vjlive1/JUNK/one_off_scripts/_audit_params.py (L17-36)
```python
            pmax = param.get('max')
            pmin = param.get('min')
            pid = param.get('id', '?')
            
            if ptype == 'float' and pmax is not None and pmax != 10.0:
                non_conforming.append(
                    f"  {mod.get('id','?')}.{pid}: [min={pmin}, max={pmax}, def={param.get('default')}]"
                )
    
    if non_conforming:
        results[plugin] = non_conforming
    else:
        conforming.append(plugin)

total = 0
for plugin, params in sorted(results.items()):
    print(f"\n{plugin} ({len(params)} float params need fix):")
    for p in params[:5]:
        print(p)
    if len(params) > 5:
```

### vjlive1/JUNK/one_off_scripts/_audit_params.py (L33-43)
```python
    print(f"\n{plugin} ({len(params)} float params need fix):")
    for p in params[:5]:
        print(p)
    if len(params) > 5:
        print(f"  ... and {len(params)-5} more")
    total += len(params)

print(f"\n--- SUMMARY ---")
print(f"Plugins needing manifest fix: {len(results)}")
print(f"Total non-conforming float params: {total}")
print(f"Already at 0-10.0: {', '.join(conforming)}")
```

### vjlive1/JUNK/one_off_scripts/_audit_params.py (L40-43)
```python
print(f"\n--- SUMMARY ---")
print(f"Plugins needing manifest fix: {len(results)}")
print(f"Total non-conforming float params: {total}")
print(f"Already at 0-10.0: {', '.join(conforming)}")
```

### vjlive1/JUNK/one_off_scripts/_audit_params.py (L41-43)
```python
print(f"Plugins needing manifest fix: {len(results)}")
print(f"Total non-conforming float params: {total}")
print(f"Already at 0-10.0: {', '.join(conforming)}")
```