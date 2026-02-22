# Spec Template — P2-H4 NDI Video Transport

**File naming:** `docs/specs/P2-H4_ndi.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-H4 — NDI Video Transport (Full Hub + Streams)

**Phase:** Phase 2
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module provides Network Device Interface (NDI) integration for VJLive3. It acts as both a transmitter (sending VJLive3's master output or specific nodes to other software like OBS or Resolume) and a receiver (ingesting NDI streams into the node graph as texture sources). It manages discovery of NDI sources on the network via an `NDIHub`.

---

## What It Does NOT Do

- It does NOT implement Spout/Syphon (that belongs to P2-H5).
- It does NOT handle WebRTC streaming to browsers (that belongs to the UI/Web API layer).

---

## Public Interface

```python
import numpy as np
from typing import List, Optional, Dict
from vjlive3.plugins.api import Plugin, VJLiveAPI

class NDISender:
    """Sends frames from VJLive3 to the network via NDI."""
    def __init__(self, name: str = "VJLive3 Output") -> None: ...
    def send_frame(self, frame_bgra: np.ndarray) -> bool: ...
    def destroy(self) -> None: ...

class NDIReceiver:
    """Receives frames from the network into VJLive3."""
    def __init__(self, source_name: str) -> None: ...
    def connect(self) -> bool: ...
    def read_frame(self) -> Optional[np.ndarray]: ...
    def disconnect(self) -> None: ...

class NDIHub:
    """Central manager for discovery and routing of NDI streams."""
    def __init__(self) -> None: ...
    def get_available_sources(self) -> List[str]: ...
    def create_sender(self, name: str) -> NDISender: ...
    def create_receiver(self, source_name: str) -> NDIReceiver: ...
    def shutdown(self) -> None: ...
```

---

## Inputs and Outputs

| Type | Format | Description |
|------|--------|-------------|
| Sending | `np.ndarray` | BGRA uint8 arrays, sent at 60fps limit. |
| Receiving | `np.ndarray` | BGRA uint8 arrays, converted to GL Textures by the rendering engine. |

---

## Edge Cases and Error Handling

- What happens if the `NDIlib` Python bindings are not installed or fail to load? → `NDIHub` catches the `ImportError` and falls back to a "Mock" mode. It logs a warning (`logger.warning("NDI library not found. Running in mock mode.")`). `create_sender` and `create_receiver` return mock objects that do nothing and return black frames, respectively. (SAFETY RAIL #6 Compliance).
- What happens if an NDI source disappears from the network? → `NDIReceiver.read_frame()` returns `None`. The plugin must handle this by holding the last frame or displaying a "No Signal" texture, but it MUST NOT crash.
- Resource Leaks: The `destroy` and `disconnect` methods must explicitly free the NDI pointers to avoid memory leaks. (SAFETY RAIL #8).

---

## Dependencies

- Python dependencies: `NDIlib` (or `ndi-python`), `numpy`.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_ndi_mock_mode` | Forcing `NDIlib` to None ensures the hub falls back gracefully to Mock objects without raising exceptions. |
| `test_ndi_sender_mock` | The mock sender accepts frames and returns True. |
| `test_ndi_receiver_mock` | The mock receiver returns a valid empty/black numpy array or None cleanly. |
| `test_ndi_hub_discovery` | Mock discovery returns an empty list (or predefined mock sources) without crashing. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-H4: NDI video transport integration` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
