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

