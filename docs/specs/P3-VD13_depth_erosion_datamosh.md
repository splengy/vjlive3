# Spec Template — P3-VD13 Depth Erosion Datamosh

**File naming:** `docs/specs/P3-VD13_depth_erosion_datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD13 — Depth Erosion Datamosh

**Phase:** Phase 3
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module ports the "Depth Erosion Datamosh" effect from VJlive-2. It performs morphological operations (erosion, dilation, opening, closing) on incoming depth maps to create organic boundaries, which then drive datamosh feedback artifacts. The result is a cellular, dissolving/growing glitch aesthetic mapped to physical scene topology.

---

## What It Does NOT Do

- It does NOT rely on motion estimation (optical flow) for the glitch.
- It does NOT compute morphology via CPU arrays. Morphology must be implemented in the fragment shader.

---

## Public Interface

```python
from vjlive3.plugins.api import Plugin, VJLiveAPI

METADATA = {
    "name": "Depth Erosion Datamosh",
    "description": "Morphological depth-driven organic feedback datamosh.",
    "version": "1.0.0",
    "parameters": [
        {"name": "morph_radius", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5, "description": "Size of morphology kernel"},
        {"name": "morph_mode", "type": "int", "min": 0, "max": 3, "default": 0, "description": "0=Erode, 1=Dilate, 2=Open, 3=Close"},
        {"name": "mosh_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "feedback_decay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.95}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthErosionDatamoshPlugin(Plugin):
    """Morphological feedback datamosh."""
    def __init__(self, api: VJLiveAPI) -> None: ...
    def on_load(self) -> None: ...
    def process(self, context) -> None: ...
    def on_unload(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Source Video A (base) |
| `video_b_in` | GL Texture | Source Video B (what gets moshed/displaced) |
| `depth_in` | GL Texture | Depth map used for morphology |
| `video_out`| GL Texture | Output |

---

## Edge Cases and Error Handling

- **Missing Inputs**: If `video_b_in` is missing, it falls back to moshing `video_in`. If `depth_in` is missing, it bypasses the morphology stage and applies a flat feedback pass or bypasses completely (SAFETY RAIL #7).
- **Performance Budget**: Morphology requires neighborhood sampling. A 3x3 or 5x5 max tap count must be strictly enforced in the shader to keep FPS stable at 60 (SAFETY RAIL #1).
- **FBO Cleanup**: Requires `texPrev` feedback FBOs. Must tear down on unload (SAFETY RAIL #8).

---

## Dependencies

- OpenGL Context.
- VJLive3 Plugin API.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_erosion_datamosh_manifest` | Verifies Pydantic manifest structure. |
| `test_erosion_datamosh_missing_inputs` | Verifies that missing video_b or depth_in does not crash the shader. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD13: Depth Erosion Datamosh`
- [ ] BOARD.md updated
