# Spec Template — P3-VD17 Depth Mosaic

**File naming:** `docs/specs/P3-VD17_depth_mosaic.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD17 — Depth Mosaic

**Phase:** Phase 3
**Assigned To:** Worker Beta
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module ports the "Depth Mosaic" effect from the legacy `vjlive` codebase. It uses depth data to control the localized resolution/tessellation of the video feed. Near objects are rendered as large, bold geometric tiles (square, hex, circle, or voronoi), while far objects are rendered with fine detail or pass through unaffected.

---

## What It Does NOT Do

- It does not create 3D geometry; it is a 2D screen-space pixel shader.
- It does not generate the tile patterns heavily via CPU; it relies on GLSL for grid generation and voronoi noise.

---

## Public Interface

```python
from vjlive3.plugins.api import PluginBase, PluginContext

METADATA = {
    "name": "Depth Mosaic",
    "description": "Depth-controlled video tessellation and quantization.",
    "version": "1.0.0",
    "parameters": [
        {"name": "cell_size_min", "type": "float", "min": 1.0, "max": 20.0, "default": 2.0},
        {"name": "cell_size_max", "type": "float", "min": 10.0, "max": 120.0, "default": 64.0},
        {"name": "tile_style", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0, "description": "0=Square, 0.33=Hex, 0.66=Circle, 1=Voronoi"},
        {"name": "depth_invert", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "gap_width", "type": "float", "min": 0.0, "max": 5.0, "default": 2.0},
        {"name": "gap_color", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "color_quantize", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "rotate_by_depth", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthMosaicPlugin(PluginBase):
    def __init__(self) -> None: ...
    def initialize(self, context: PluginContext) -> None: ...
    def process(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Source Video (to be tessellated) |
| `depth_in` | GL Texture | Depth map used for cell dimension |
| `video_out`| GL Texture | Output |

---

## Edge Cases and Error Handling

- **Missing Depth Input**: Bypasses the mosaic effect safely, passing `video_in` directly to `video_out` (SAFETY RAIL #7).
- **Zero Cell Size**: Prevented via parameter clamp mapping; min clamp is physically 1.0 to prevent divide-by-zero layout errors in the shader.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_mosaic_manifest` | Verifies Pydantic manifest structure. |
| `test_mosaic_missing_depth` | Verifies graceful bypass when depth is absent. |
| `test_mosaic_process_routing` | Verifies parameter mapping and texture offset passing. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD17: Depth Mosaic`
- [ ] BOARD.md updated
