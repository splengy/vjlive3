# Spec Template — P3-VD16 Depth Edge Glow

**File naming:** `docs/specs/P3-VD16_depth_edge_glow.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD16 — Depth Edge Glow

**Phase:** Phase 3
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module ports the "Depth Edge Glow" effect from VJlive-2. It extracts structural boundaries from the depth map using edge detection (Sobel) and renders them as glowing neon lines. It supports topographic contour lines at regular depth intervals, per-band color cycling, and blending the neon geometry over the original source video.

---

## What It Does NOT Do

- It does NOT rely on image/color-based edge detection. It specifically searches for geometric depth discontinuities.

---

## Public Interface

```python
from vjlive3.plugins.api import Plugin, VJLiveAPI

METADATA = {
    "name": "Depth Edge Glow",
    "description": "Neon depth contour visualization.",
    "version": "1.0.0",
    "parameters": [
        {"name": "edge_threshold", "type": "float", "min": 0.0, "max": 1.0, "default": 0.1},
        {"name": "edge_thickness", "type": "float", "min": 0.0, "max": 10.0, "default": 2.0},
        {"name": "glow_radius", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "contour_intervals", "type": "int", "min": 1, "max": 64, "default": 8},
        {"name": "color_cycle_speed", "type": "float", "min": 0.0, "max": 5.0, "default": 1.0},
        {"name": "bg_dimming", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthEdgeGlowPlugin(Plugin):
    """Neon structural edge detector."""
    def __init__(self, api: VJLiveAPI) -> None: ...
    def on_load(self) -> None: ...
    def process(self, context) -> None: ...
    def on_unload(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Source Video (used for background) |
| `depth_in` | GL Texture | Depth map used for contour extraction |
| `video_out`| GL Texture | Output |

---

## Edge Cases and Error Handling

- **Missing Depth Input**: Bypasses contour extraction and simply dims or passes through `video_in` based on `bg_dimming` (SAFETY RAIL #7).
- **Performance Budget**: Sobel edge detection and multi-tap Gaussian glow require careful optimization in the fragment shader. Maintain strict tap limits to ensure 60 FPS (SAFETY RAIL #1).

---

## Dependencies

- OpenGL Context.
- VJLive3 Plugin API.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_edge_glow_manifest` | Verifies Pydantic manifest structure. |
| `test_edge_glow_missing_depth` | Prevents crash when depth texture is absent. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD16: Depth Edge Glow`
- [ ] BOARD.md updated
