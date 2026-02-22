# Spec Template — P2-H5 Spout Support (Windows Video Sharing)

**File naming:** `docs/specs/P2-H5_spout.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-H5 — Spout Support (Windows Video Sharing)

**Phase:** Phase 2
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module provides Spout integration for VJLive3 on Windows. Spout allows for zero-latency, zero-overhead texture sharing directly on the GPU between applications (e.g., sending VJLive3 output to Resolume or OBS, or receiving textures from Unity). It implements both `SpoutSender` and `SpoutReceiver` interfaces, leveraging OpenGL texture handles directly when possible.

---

## What It Does NOT Do

- It does NOT transmit video over the network (that belongs to P2-H4 NDI).
- It does NOT implement Syphon (macOS equivalent) unless specifically wrapping a cross-platform library that handles both transparently.

---

## Public Interface

```python
import numpy as np
from typing import Optional, List
from vjlive3.plugins.api import Plugin, VJLiveAPI

class SpoutSender:
    """Sends textures via Spout to other applications."""
    def __init__(self, name: str = "VJLive3 Spout Output") -> None: ...
    def send_texture(self, texture_id: int, width: int, height: int) -> bool: ...
    def send_image(self, frame_bgra: np.ndarray) -> bool: ...
    def destroy(self) -> None: ...

class SpoutReceiver:
    """Receives textures via Spout from other applications."""
    def __init__(self, sender_name: str) -> None: ...
    def receive_texture(self, target_texture_id: int) -> bool: ...
    def receive_image(self) -> Optional[np.ndarray]: ...
    def destroy(self) -> None: ...

class SpoutManager:
    """Manages Spout context and discovery."""
    def __init__(self) -> None: ...
    def get_senders(self) -> List[str]: ...
```

---

## Inputs and Outputs

| Operation | Type | Description |
|-----------|------|-------------|
| GPU TX | GL Texture ID | Zero-copy transfer of existing OpenGL texture out to Spout. |
| CPU TX | `np.ndarray` | Fallback: Send a CPU array (BGRA uint8) via Spout. |
| GPU RX | GL Texture ID | Zero-copy reception of a Spout texture directly into a GL texture. |
| CPU RX | `np.ndarray` | Fallback: Read a Spout texture back to a CPU array. |

---

## Edge Cases and Error Handling

- **Platform Independence**: If the OS is not Windows, or `pyspout` (or the underlying Spout library) fails to import, the module MUST fall back to a "Mock" mode. `SpoutSender` and `SpoutReceiver` will log a warning and return silently, doing nothing. (SAFETY RAIL #6).
- **Context Loss**: If the OpenGL context is lost or changes, the Spout integration must gracefully re-initialize or ignore the errors without bringing down the main render loop.
- **Resource Management**: Spout handles and shared memory must be explicitly released in `destroy()` to prevent memory leaks. (SAFETY RAIL #8).

---

## Dependencies

- Python dependencies: `SpoutGL` / `pyspout` (or whatever wrapper the project settles on, typically via `ctypes` or a compiled extension).
- OS dependency: Windows. 

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_spout_mock_fallback_on_linux` | On non-Windows platforms, or if the library is missing, instantiation creates Mock objects without crashing. |
| `test_spout_sender_lifecycle` | `SpoutSender` can be created and `destroy()` cleans up resources without error. |
| `test_spout_receiver_mock_read` | `receive_image` on a Mock receiver returns None or a blank array safely. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-H5: Spout support integration` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
