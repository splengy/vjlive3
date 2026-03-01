# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P0-Q3_check_file_lock.py`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-Q3 — check_file_lock.py

**Phase:** Phase 0 / P0
**Assigned To:** Alex Turner
**Spec Written By:** Jordan Lee
**Date:** 2025-04-05

---

## What This Module Does

This module checks whether a file is locked by another process, using operating system-level file locking mechanisms. It determines if a given file path is currently held in exclusive or shared mode by any running process and returns a boolean indicating the lock status. The primary use case is to prevent concurrent access to configuration files or state files during initialization.

---

## What It Does NOT Do

- It does not attempt to acquire or release locks.
- It does not monitor for lock changes over time (e.g., real-time detection).
- It does not validate file existence or permissions — it only checks for lock status on an existing file.
- It does not provide a mechanism to resolve conflicts; it only reports whether a lock exists.

---

## Public Interface

```python
def is_file_locked(file_path: str) -> bool:
    """
    Check if the specified file is currently locked by another process.

    Args:
        file_path (str): Path to the file being checked for locks.

    Returns:
        bool: True if the file is locked, False otherwise.
    """
```

---

## Inputs and Outputs

| Name         | Type   | Description                              | Constraints |
|--------------|--------|------------------------------------------|-------------|
| `file_path`  | `str`  | Path to the file being checked          | Must be a valid path string; absolute or relative. If relative, resolved to current working directory. Length ≤ 4096 characters. |

---

## Edge Cases and Error Handling

