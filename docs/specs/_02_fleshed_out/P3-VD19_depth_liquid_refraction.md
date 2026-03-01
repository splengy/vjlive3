# Spec Template — P3-VD19 Depth Liquid Refraction

**File naming:** `docs/specs/P3-VD19_depth_liquid_refraction.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD19 — Depth Liquid Refraction

**Phase:** Phase 3  
**Assigned To:** Worker Beta  
**Spec Written By:** Manager-Gemini-3.1  
**Date:** 2026-02-22  

---

## What This Module Does

This module ports the "Depth Liquid Refraction" effect from the legacy `vdepth` codebase. It uses the depth map as a displacement field to warp the video feed, simulating a glass or water distortion effect. Strong depth gradients (edges between near and far) produce extreme warping causing caustic highlights around the performer's silhouette. It includes chromatic aberration, animated ripples, frosted glass noise, and depth-proportional box blur.

---

## What It Does NOT Do

- It does not build 3D mesh geometry; it purely displaces UV coordinates in 2D space.
- It does not handle fluid dynamics simulation (it uses perceptual FBM simplex noise for ripples).

---

## Public Interface

```python
from vjlive3.plugins.api import PluginBase, PluginContext

METADATA = {
    "name": "Depth Liquid Refraction",
    "description": "Depth-driven glass and water distortion with caustic edge highlights.",
    "version": "1.0.0",
    "parameters": [
        {"name": "refraction_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "chromatic_spread", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "ripple_speed", "type": "float", "min": 0.0, "max": 2.0, "default": 0.4},
        {"name": "ripple_scale", "type": "float", "min": 0.1, "max": 2.0, "default": 0.5},
        {"name": "edge_glow", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "depth_blur", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "frosted_glass", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "invert_depth", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthLiquidRefractionPlugin(PluginBase):
    def __init__(self) -> None: ...
    def initialize(self, context: PluginContext) -> None: ...
    def process(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Source Base video to be displaced. |
| `depth_in` | GL Texture | Depth map used for the normalized displacement field. |
| `video_out`| GL Texture | Output |

---

## Edge Cases and Error Handling

- **Missing Depth Input**: Bypasses safely, passing `video_in` unmodified to `video_out` (SAFETY RAIL #7).
- **Missing Video Input**: Bypasses the texture processing entirely.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_liquid_manifest` | Verifies Pydantic compatibility and manifest structure. |
| `test_liquid_missing_depth` | Verifies graceful bypass when depth is absent. |
| `test_liquid_processing` | Confirms generic processing logic via expected texture ID offset transformation. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD19: Depth Liquid Refraction plugin`
- [ ] BOARD.md updated
