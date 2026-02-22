# Spec Template — P3-VD04 Depth Reverb

**File naming:** `docs/specs/P3-VD04_depth_reverb.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD04 — Depth Reverb

**Phase:** Phase 3
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module ports the "Depth Reverb" plugin from VJlive-2. It creates a visual echo/reverb effect where the depth map controls the "room size" and "wetness". Near objects are rendered dry (immediate), while far objects are rendered wet (echoed, trailing, diffused). This relies heavily on temporal feedback buffers.

---

## What It Does NOT Do

- It does NOT do audio reverb. This is strictly a video/pixel effect.
- It does NOT rely on motion estimation (optical flow); it relies solely on combining current frames with previous frames based on depth thresholds.

---

## Public Interface

```python
import numpy as np
from vjlive3.plugins.api import Plugin, VJLiveAPI
from vjlive3.plugins.registry import PluginManifest

METADATA = {
    "name": "Depth Reverb",
    "description": "Visual reverb where depth controls echo persistence.",
    "version": "1.0.0",
    "parameters": [
        {"name": "room_size", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5, "description": "Global wetness scalar"},
        {"name": "decay_time", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8, "description": "Feedback persistence"},
        {"name": "diffusion", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2, "description": "Spatial blur in reverb tail"},
        {"name": "damping", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5, "description": "High frequency loss"}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthReverbPlugin(Plugin):
    """Depth-controlled temporal feedback effect."""
    def __init__(self, api: VJLiveAPI) -> None: ...
    def on_load(self) -> None: ...
    def process(self, context) -> None: ...
    def on_unload(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Live RGB video feed |
| `depth_in` | GL Texture | Depth map controlling reverb wetness per pixel |
| `video_out`| GL Texture | Final reverberated output |

---

## Edge Cases and Error Handling

- **Resolution Changes**: If `video_in` changes resolution at runtime, the internal Ping-Pong FBOs used for the `texPrev` feedback must be automatically resized without crashing.
- **Resource Cleanup**: Temporal effects require persistent texture buffers. These MUST be explicitly destroyed in `on_unload()` to prevent VRAM memory leaks. (SAFETY RAIL #8).
- **Missing Depth**: If `depth_in` is missing, the effect should either apply a uniform flat reverb based on `room_size` or bypass entirely.

---

## Dependencies

- OpenGL Context (ModernGL / PyOpenGL).
- VJLive3 Plugin API.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_depth_reverb_manifest` | Validates plugin manifest structure and expected parameters. |
| `test_depth_reverb_fbo_lifecycle` | Initialization creates FBOs, and unloading explicitly deletes them. |
| `test_depth_reverb_resolution_change` | Simulating a resolution change triggers FBO reallocation without throwing GL errors. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD04: Depth Reverb`
- [ ] BOARD.md updated
