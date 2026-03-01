# Spec Template — P3-VD18 Depth Video Projection

**File naming:** `docs/specs/P3-VD18_depth_video_projection.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD18 — Depth Video Projection

**Phase:** Phase 3
**Assigned To:** Worker Beta
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module ports the "Depth Video Projection" effect, simulating projection mapping onto a 3D subject moving in real-time. It uses depth data to compute real-time surface normals via central differences. It then wraps/UV-maps a secondary `video_b_in` texture over the geometry. It includes dynamic simulated ambient lighting responding to the surface normals, and a stylistic Fresnel holographic edge glow.

---

## What It Does NOT Do

- It does NOT track the camera physically (it assumes a fixed imaginary point light source).
- It does NOT rely on ray-tracing. It computes purely in screen-space.

---

## Public Interface

```python
from vjlive3.plugins.api import PluginBase, PluginContext

METADATA = {
    "name": "Depth Video Projection",
    "description": "Wraps a secondary video texture onto depth-derived surface normals.",
    "version": "1.0.0",
    "parameters": [
        {"name": "projection_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "depth_contour", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "uv_scale", "type": "float", "min": 0.1, "max": 5.0, "default": 1.0},
        {"name": "uv_scroll_x", "type": "float", "min": -1.0, "max": 1.0, "default": 0.0},
        {"name": "uv_scroll_y", "type": "float", "min": -1.0, "max": 1.0, "default": 0.0},
        {"name": "normal_lighting", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "mask_tightness", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "hologram_glow", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthVideoProjectionPlugin(PluginBase):
    def __init__(self) -> None: ...
    def initialize(self, context: PluginContext) -> None: ...
    def process(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Source base video feed |
| `video_b_in` | GL Texture | Texture to project onto the depth normals. If missing, falls back to `video_in`. |
| `depth_in` | GL Texture | Used to compute 3D normals |
| `video_out`| GL Texture | Output |

---

## Edge Cases and Error Handling

- **Missing Depth Input**: Bypasses the projection logic entirely, restoring the original video stream (SAFETY RAIL #7).
- **Missing Secondary Video**: Projects the primary video back onto itself, creating a neat feedback-style visual echo without crashing.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_projection_manifest` | Verifies Pydantic manifest structure. |
| `test_projection_missing_depth` | Verifies graceful bypass when depth is absent. |
| `test_projection_fallback_video_b` | Checks the `video_b_in` fallback logic. |
| `test_projection_parameter_clamping` | Validates bound constraints. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD18: Depth Video Projection`
- [ ] BOARD.md updated
