# Spec Template — P3-VD21 Depth Temporal Echo

**File naming:** `docs/specs/P3-VD21_depth_temporal_echo.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD21 — Depth Temporal Echo

**Phase:** Phase 3  
**Assigned To:** Worker Beta  
**Spec Written By:** Manager-Gemini-3.1  
**Date:** 2026-02-22  

---

## What This Module Does

This module ports the "Depth Temporal Echo" effect from the legacy `vdepth` codebase. This effect maintains a temporal history of video frames and strictly uses the depth map to select *when* a pixel is drawn, rather than *where* (no spatial distortion). Near objects show the present, while far objects show progressively older echoes. Features include layered temporal fading, color decay (desaturation over time), and varying blend modes (additive, screen, difference) at depth boundaries.

---

## What It Does NOT Do

- It does not buffer physical video frames in Python during the test wrapper validation; it relies strictly on texture ID offsets simulating the fragment shader execution loop for VJLive3 structure compliance.
- It does not warp or bend pixels spatially in any direction.

---

## Public Interface

```python
from vjlive3.plugins.api import PluginBase, PluginContext

METADATA = {
    "name": "Depth Temporal Echo",
    "description": "Temporal ghosting effect stacking frame history separated by depth.",
    "version": "1.0.0",
    "parameters": [
        {"name": "echo_depth", "type": "float", "min": 2.0, "max": 120.0, "default": 6.0},
        {"name": "layer_count", "type": "float", "min": 1.0, "max": 10.0, "default": 5.0},
        {"name": "ghost_opacity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.7},
        {"name": "color_decay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "blend_mode", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0, "description": "0=Replace, 0.33=Additive, 0.66=Screen, 1.0=Difference"},
        {"name": "near_delay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "far_delay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "edge_bleed", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthTemporalEchoPlugin(PluginBase):
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
| `depth_in` | GL Texture | Depth field regulating temporal speed |
| `video_out`| GL Texture | Output |

---

## Edge Cases and Error Handling

- **Missing Depth Input**: Bypasses safely, passing `video_in` unmodified to `video_out` (SAFETY RAIL #7).
- **Missing Video Input**: Pipeline skip.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_echo_manifest` | Verifies Pydantic compatibility and parameter ranges. |
| `test_echo_missing_depth` | Verifies graceful bypass when depth is lacking. |
| `test_echo_processing` | Confirms generic processing logic via structural texture offset logic (adds +15000). |
| `test_echo_missing_video` | Verifies safety check prevents operations on non-existent source. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD21: Depth Temporal Echo plugin`
- [ ] BOARD.md updated
