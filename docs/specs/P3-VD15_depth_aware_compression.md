# Spec Template — P3-VD15 Depth Aware Compression

**File naming:** `docs/specs/P3-VD15_depth_aware_compression.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD15 — Depth Aware Compression

**Phase:** Phase 3
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module ports the "Depth Aware Compression" effect from VJlive-2. It simulates digital video compression artifacts (like JPEG macroblocking and bit-crushing), but modulates the intensity and scale of these artifacts based on the depth map. For example, background elements can be heavily macroblocked and color-quantized while foreground subjects remain crisp and high-fidelity.

---

## What It Does NOT Do

- It does NOT rely on motion estimation (optical flow). It's a spatial block/compression simulator, not a temporal P-frame datamosh.
- It does NOT actually compress the video stream for network transport.

---

## Public Interface

```python
from vjlive3.plugins.api import Plugin, VJLiveAPI

METADATA = {
    "name": "Depth Aware Compression",
    "description": "Video compression artifacts modulated by depth layers.",
    "version": "1.0.0",
    "parameters": [
        {"name": "block_size", "type": "float", "min": 1.0, "max": 64.0, "default": 16.0},
        {"name": "quality", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "color_quantization", "type": "float", "min": 2.0, "max": 256.0, "default": 16.0},
        {"name": "depth_compression_ratio", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "block_size_by_depth", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthAwareCompressionPlugin(Plugin):
    """Depth-modulated digital artifact simulator."""
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
| `depth_in` | GL Texture | Depth map controlling artifact intensity |
| `video_out`| GL Texture | Output |

---

## Edge Cases and Error Handling

- **Missing Depth Input**: If `depth_in` is missing, applies uniform compression across the entire frame based on base `quality` and `block_size` values (SAFETY RAIL #7).
- **Float Quantization Math**: `color_quantization` must not reach 0 to prevent divide-by-zero errors in the shader. Clamp safely within GLSL.

---

## Dependencies

- OpenGL Context.
- VJLive3 Plugin API.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_depth_compression_manifest` | Verifies Pydantic manifest structure. |
| `test_depth_compression_bypass` | Works cleanly when `depth_in` is not provided. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD15: Depth Aware Compression`
- [ ] BOARD.md updated
