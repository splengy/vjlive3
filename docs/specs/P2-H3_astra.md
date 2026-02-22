# Spec Template — P2-H3 Astra Depth Camera Integration

**File naming:** `docs/specs/P2-H3_astra.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-H3 — Astra Depth Camera Integration

**Phase:** Phase 2
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module integrates the Orbbec Astra depth camera into VJLive3's plugin and routing system. It captures raw depth arrays and RGB video frames, normalizes them, and provides them as a video/texture source to the node graph. In accordance with SAFETY RAIL #6, it implements a robust "Simulator Mode" that generates procedural depth data if the physical camera is disconnected or missing drivers.

---

## What It Does NOT Do

- It does NOT render advanced 3D point clouds directly (that belongs to depth effects).
- It does NOT perform skeletal tracking or gesture recognition (those are separate higher-level nodes).

---

## Public Interface

```python
import numpy as np
from typing import Optional, Tuple
from vjlive3.plugins.api import Plugin, VJLiveAPI

class AstraDepthCamera:
    """Core hardware abstraction for the Astra camera."""
    def __init__(self, width: int = 640, height: int = 480) -> None: ...
    def start(self) -> bool: ...
    def stop(self) -> None: ...
    def get_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]: 
        """Returns (depth_frame_normalized_0_to_1, rgb_frame_uint8)"""
        ...
    def is_hardware_connected(self) -> bool: ...

class AstraPlugin(Plugin):
    """Plugin wrapper exposing the camera to the node graph."""
    def __init__(self, api: VJLiveAPI) -> None: ...
    def on_load(self) -> None: ...
    def process(self, context) -> None: ...
    def on_unload(self) -> None: ...
```

---

## Inputs and Outputs

| Input | Type | Description |
|-------|------|-------------|
| Device connection | Physical USB | Orbbec Astra camera via OpenNI2 or PyUSB |
| `use_simulation` | `bool` | Force simulated data even if camera is present |

| Output | Type | Description |
|--------|------|-------------|
| `depth_frame` | `np.ndarray` | Float32 array, shape (H,W), normalized 0.0-1.0 |
| `rgb_frame` | `np.ndarray` | UInt8 array, shape (H,W,3), standard RGB |
| Texture outputs | GL Texture | Pushed to the render engine for other nodes to use |

---

## Edge Cases and Error Handling

- What happens if the Astra is unplugged mid-show? → The `get_frames` method detects the read failure, logs a warning, automatically falls back to Simulator mode, and emits a device-lost event.
- What happens if the OpenNI2 drivers are missing on startup? → `AstraDepthCamera` catches the exception during `start()`, logs an ERROR indicating missing drivers, and starts the simulator. (Rail #6 Compliance).

---

## Dependencies

- Python dependencies: `numpy`, `opencv-python` (for generic capture if using cv2 CAP_OPENNI2 backend) or `pyusb` for direct access.
- System dependencies: OpenNI2 shared libraries (Windows/Linux) if going the native ctypes route.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_astra_simulator_fallback` | Instantiating without hardware correctly enters Simulator mode. |
| `test_astra_frame_normalization` | The simulator (and mock hardware) returns depth arrays correctly scaled 0.0-1.0. |
| `test_astra_plugin_registration` | The plugin successfully registers its outputs with the VJLive3 API. |
| `test_astra_disconnect_recovery` | Simulating a hardware disconnect at runtime triggers a smooth fallback to the simulator. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-H3: Astra depth camera integration` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
