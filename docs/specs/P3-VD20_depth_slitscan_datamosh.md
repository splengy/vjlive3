# Spec Template — P3-VD20 Depth Slitscan Datamosh

**File naming:** `docs/specs/P3-VD20_depth_slitscan_datamosh.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD20 — Depth Slitscan Datamosh

**Phase:** Phase 3  
**Assigned To:** Worker Beta  
**Spec Written By:** Manager-Gemini-3.1  
**Date:** 2026-02-22  

---

## What This Module Does

This module ports the "Depth Slitscan Datamosh" effect from the legacy `vdepth` codebase. It blends the classic slit-scan technique with depth awareness. The scene is temporally smeared along scan lines whose position, direction, width, and speed are physically modulated by depth gradients. Near objects scan quickly, retaining their recent temporal state; far objects update slowly, preserving deep physical history. It includes motion-vector guided datamosh artifacts at the temporal boundaries where time slices crash into each other.

---

## What It Does NOT Do

- It does not allocate new video buffers; it depends strictly on the application to feed the `video_b_in` or simulate feedback dynamically via internal states in a full execution.
- It does not rely purely on random glitching. The glitches exist deliberately at temporal depth-scan boundaries.

---

## Public Interface

```python
from vjlive3.plugins.api import PluginBase, PluginContext

METADATA = {
    "name": "Depth Slitscan Datamosh",
    "description": "Temporal slit-scan smearing heavily modulated by depth buffers.",
    "version": "1.0.0",
    "parameters": [
        {"name": "scan_position", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "scan_speed", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "scan_width", "type": "float", "min": 0.01, "max": 0.5, "default": 0.2},
        {"name": "scan_direction", "type": "float", "min": 0.0, "max": 3.0, "default": 0.0, "description": "0=Horz, 1=Vert, 2=Radial, 3=Spiral"},
        {"name": "depth_speed_mod", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "depth_warp", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "depth_scan_offset", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "near_far_flip", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "chromatic_split", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "channel_phase", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "mosh_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_artifact", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "feedback_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "trail_persistence", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "scan_glow", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthSlitscanDatamoshPlugin(PluginBase):
    def __init__(self) -> None: ...
    def initialize(self, context: PluginContext) -> None: ...
    def process(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Current frame feed |
| `video_b_in` | GL Texture | Optional second layer to merge temporal glitched slices into. |
| `depth_in` | GL Texture | Depth field regulating temporal speed |
| `video_out`| GL Texture | Output |

---

## Edge Cases and Error Handling

- **Missing Depth Input**: Bypasses safely, passing `video_in` unmodified to `video_out` (SAFETY RAIL #7).
- **Missing Secondary Video**: Projects cleanly by falling back onto itself or defaulting to bypass structure.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_slitscan_manifest` | Verifies Pydantic compatibility and parameter ranges. |
| `test_slitscan_missing_depth` | Verifies graceful bypass when depth is lacking. |
| `test_slitscan_processing` | Confirms generic processing logic via structural texture offset logic (adds +14000). |
| `test_slitscan_missing_video` | Verifies the safety check prevents operations on non-existent source. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD20: Depth Slitscan Datamosh plugin`
- [ ] BOARD.md updated
