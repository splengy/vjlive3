# Spec Template — P3-VD11 Depth Color Grade

**File naming:** `docs/specs/P3-VD11_depth_color_grade.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD11 — Depth Color Grade

**Phase:** Phase 3
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module ports the "Depth Color Grade" effect from VJlive-2. It applies a 3-zone color grading system (near, mid, far) based on the input depth map. It allows independent manipulation of lift, gamma, gain, hue rotation, saturation, and temperature shift for each distinct depth zone, effectively allowing foreground performers to be graded differently than the background.

---

## What It Does NOT Do

- It does NOT utilize 3D LUT files (.cube). It performs purely algorithmic lift/gamma/gain and HSV math in the fragment shader.

---

## Public Interface

```python
from vjlive3.plugins.api import Plugin, VJLiveAPI

METADATA = {
    "name": "Depth Color Grade",
    "description": "Per-depth-band color grading (near, mid, far zones).",
    "version": "1.0.0",
    "parameters": [
        {"name": "zone_near", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "zone_far", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "zone_blend", "type": "float", "min": 0.0, "max": 0.5, "default": 0.1},
        # Simplified example params, actual implementation needs per-zone controls
        {"name": "near_saturation", "type": "float", "min": 0.0, "max": 2.0, "default": 1.0},
        {"name": "mid_saturation", "type": "float", "min": 0.0, "max": 2.0, "default": 1.0},
        {"name": "far_saturation", "type": "float", "min": 0.0, "max": 2.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthColorGradePlugin(Plugin):
    """3-Zone Depth Color Corrector."""
    def __init__(self, api: VJLiveAPI) -> None: ...
    def on_load(self) -> None: ...
    def process(self, context) -> None: ...
    def on_unload(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Source Video |
| `depth_in` | GL Texture | Depth map used for zone masking |
| `video_out`| GL Texture | Color-graded output |

---

## Edge Cases and Error Handling

- **Missing Depth Input**: If `depth_in` is missing, the effect must fall back to applying the "mid" zone grading to the entire image rather than breaking or clamping to black (SAFETY RAIL #7).
- **Overlapping Zones**: If `zone_near` > `zone_far`, the shader or python wrapper must swap or clamp them to prevent math inversion in the `smoothstep` blending logic.

---

## Dependencies

- OpenGL Context.
- VJLive3 Plugin API.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_depth_color_grade_manifest` | Verifies Pydantic manifest structure and param limits. |
| `test_depth_color_grade_zone_swap` | Prevents math errors if `zone_near` is pushed past `zone_far`. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD11: Depth Color Grade`
- [ ] BOARD.md updated
