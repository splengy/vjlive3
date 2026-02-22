# Spec Template — P3-VD23 Depth Vector Field Datamosh

**File naming:** `docs/specs/P3-VD23_depth_vector_field_datamosh.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD23 — Depth Vector Field Datamosh

**Phase:** Phase 3  
**Assigned To:** Worker Beta  
**Spec Written By:** Manager-Gemini-3.1  
**Date:** 2026-02-22  

---

## What This Module Does

This module ports the "Depth Vector Field Datamosh" effect from the legacy `vdepth` codebase. This effect treats frame-to-frame depth changes as motion vectors, driving a classic datamosh P-frame propagation where pixels smear along the depth gradient. It also provides block quantization, chromatic drift, color bleed, and temporal accumulation. 

---

## What It Does NOT Do

- It does not calculate the Sobel spatial gradients in Python; that is assumed reserved for the shader implementation (or offset validation simulation in this plugin wrapper).
- It does not process audio natively inside the plugin. Audio reactivity must be driven externally by modulating the exposed standard parameters.
- It does not manually allocate GL textures for the depth buffer history. In the VJLive3 integration, texture binding offsets are managed by the pipeline.

---

## Public Interface

```python
from vjlive3.plugins.api import PluginBase, PluginContext

METADATA = {
    "name": "Depth Vector Field Datamosh",
    "description": "Translates depth velocity into motion vectors, causing pixels to smear along Z-axis changes.",
    "version": "1.0.0",
    "parameters": [
        {"name": "vector_scale", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "temporal_blend", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "propagation_decay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "depth_threshold", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_size", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_chaos", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "chromatic_drift", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "color_bleed", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "feedback_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "accumulation", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthVectorFieldDatamoshPlugin(PluginBase):
    def __init__(self) -> None: ...
    def initialize(self, context: PluginContext) -> None: ...
    def process(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Current frame feed (tex0) |
| `video_b_in` | GL Texture | Optional second layer to merge datamosh into (tex1). |
| `depth_in` | GL Texture | Depth field whose frame-to-frame delta drives the vectors. |
| `video_out`| GL Texture | Output |

---

## Edge Cases and Error Handling

- **Missing Depth Input**: Bypasses safely, passing `video_in` unmodified to `video_out` (SAFETY RAIL #7).
- **Missing Secondary Video**: Projects cleanly by falling back onto itself or defaulting to bypass structure.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_vfd_manifest` | Verifies Pydantic compatibility and parameter dimensions. |
| `test_vfd_missing_depth` | Verifies graceful bypass when depth is lacking. |
| `test_vfd_processing` | Confirms generic processing logic via structural texture offset logic (adds +18000). |
| `test_vfd_fallback_video_b` | Validates it behaves appropriately with or without `video_b_in` supplied. |
| `test_vfd_missing_video` | Verifies the safety check prevents operations on non-existent source. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD23: Depth Vector Field Datamosh plugin`
- [ ] BOARD.md updated
