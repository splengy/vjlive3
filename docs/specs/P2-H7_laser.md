# Spec Template — P2-H7 Laser Safety System & ILDA Output

**File naming:** `docs/specs/P2-H7_laser.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-H7 — Laser Safety System & ILDA Output

**Phase:** Phase 2
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module implements the core laser projection pipeline for VJLive3, strictly adhering to hardware safety limits. It ports the VJlive-2 laser systems (`LaserSafetySystem`, `ILDAOutput`, `bitmap_to_vector`, and `bezier_tracer`). It converts raster textures or geometry into optimized bezier vector paths, verifies every coordinate and intensity against a safety interlock (to prevent static burning or eye-hazardous zones), and sends the verified frames to a laser DAC (e.g., EtherDream, Helios) via ILDA protocols.

---

## What It Does NOT Do

- It does NOT implement physical USB drivers (it assumes standard network sockets or third-party wrappers for the DACs).
- It does NOT automatically render 3D scenes to vectors (it handles 2D texture traces or explicit 2D coordinate arrays).

---

## Public Interface

```python
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

@dataclass
class LaserPoint:
    x: int  # -32768 to 32767
    y: int  # -32768 to 32767
    r: int  # 0-255
    g: int  # 0-255
    b: int  # 0-255
    blank: bool

class LaserSafetySystem:
    """Verifies and enforces safe laser output."""
    def __init__(self, max_brightness: int = 255, safe_zones: List[Tuple[int, int, int, int]] = []) -> None: ...
    def verify_frame(self, points: List[LaserPoint]) -> bool: ...
    def emergency_stop(self) -> None: ...
    def reset(self) -> None: ...

class ILDAOutput:
    """Handles communication with the Laser DAC."""
    def __init__(self, safety_system: LaserSafetySystem, dac_type: str = "etherdream") -> None: ...
    def connect(self, host: str, port: int) -> bool: ...
    def send_frame(self, points: List[LaserPoint]) -> bool: ...
    def close(self) -> None: ...

def bitmap_to_vector(image: 'np.ndarray') -> List[LaserPoint]: ...
def fit_bezier_curves(points: List[LaserPoint]) -> List[LaserPoint]: ...
```

---

## Inputs and Outputs

| Component | Input | Output |
|-----------|-------|--------|
| `bitmap_to_vector` | `np.ndarray` (Image) | `List[LaserPoint]` (Raw paths) |
| `bezier_tracer` | `List[LaserPoint]` (Raw) | `List[LaserPoint]` (Smoothed, point-optimized) |
| `LaserSafetySystem`| `List[LaserPoint]` | `True` if safe, raises `ValueError` or logs `False` if unsafe |
| `ILDAOutput` | `List[LaserPoint]` | Network/USB packets to DAC |

---

## Edge Cases and Error Handling

- **Static Beam Protection**: If the `verify_frame` detects too many consecutive points at the exact same coordinate with high intensity (a stationary beam), it MUST trigger a safety rejection to prevent burning.
- **Out of Bounds**: Coordinates outside the standard ILDA integer range (-32768 to 32767) or outside defined `safe_zones` must be clamped or blanked (laser turned off).
- **Emergency Stop**: The API layer can trigger `emergency_stop()`, which instantly flips a hardware lock state. Subsequent frames are rejected until `reset()` is called explicitly.
- **Fail Graceful**: If the DAC is disconnected, `ILDAOutput.send_frame()` logs a warning, enters a retry/mock mode, and doesn't crash the application. (SAFETY RAIL #6 & #7).

---

## Dependencies

- Python dependencies: `numpy`, `opencv-python` (for edge detection in `bitmap_to_vector`), `scipy` (optional, for curve fitting).

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_laser_safety_static_beam` | A frame with all identical coordinates is rejected by the safety system. |
| `test_laser_safety_out_of_bounds` | Points outside safe zones are correctly flagged and the frame is rejected. |
| `test_ilda_emergency_stop` | Triggering `emergency_stop()` causes `send_frame()` to immediately return False and send zero-intensity. |
| `test_bitmap_to_vector_output` | A solid white square image results in 4 corner points (or perimeter trace) and not random noise. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-H7: Laser safety and ILDA output` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
