# Spec Template — P3-VD03 Depth Portal Composite

**File naming:** `docs/specs/P3-VD03_depth_portal_composite.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD03 — Depth Portal Composite

**Phase:** Phase 3
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module ports the "Depth Portal Composite" plugin from VJlive-2. It acts as a "green screen without the green screen", using the Astra depth camera to isolate a performer from the background by depth thresholds. It then composites the isolated performer onto a secondary video feed. 

---

## What It Does NOT Do

- It does NOT rely on color-based chroma keying (e.g. looking for green/blue).
- It does NOT do 3D point cloud rendering (this is purely a 2D composite using the depth map as an alpha matte).

---

## Public Interface

```python
import numpy as np
from vjlive3.plugins.api import Plugin, VJLiveAPI
from vjlive3.plugins.registry import PluginManifest

# Must include METADATA mirroring params for self-documentation (PRIME DIRECTIVE #2)
METADATA = {
    "name": "Depth Portal Composite",
    "description": "Isolates performer using depth and composites onto a new background.",
    "version": "1.0.0",
    "parameters": [
        {"name": "slice_near", "type": "float", "min": 0.0, "max": 10.0, "default": 1.5, "description": "Near depth threshold in meters"},
        {"name": "slice_far", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0, "description": "Far depth threshold in meters"},
        {"name": "edge_softness", "type": "float", "min": 0.0, "max": 10.0, "default": 4.0},
        {"name": "spill_suppress", "type": "float", "min": 0.0, "max": 10.0, "default": 3.0},
        {"name": "bg_opacity", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
        {"name": "fg_scale", "type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
        {"name": "fg_offset_x", "type": "float", "min": -1.0, "max": 1.0, "default": 0.0},
        {"name": "fg_offset_y", "type": "float", "min": -1.0, "max": 1.0, "default": 0.0}
    ],
    "inputs": ["video_in", "background_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthPortalCompositePlugin(Plugin):
    """Depth-based chroma-key compositing effect."""
    def __init__(self, api: VJLiveAPI) -> None: ...
    def on_load(self) -> None: ...
    def process(self, context) -> None: ...
    def on_unload(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Foreground performer video (RGB) |
| `background_in` | GL Texture | Replacement background video (RGB) |
| `depth_in` | GL Texture | Depth map used as alpha matte |
| `video_out`| GL Texture | Final composite |

---

## Edge Cases and Error Handling

- **Missing Background**: If `background_in` is not connected, the effect must fall back to a black background or pass through the original background gracefully. It must NOT crash or return a blank black texture for the whole frame.
- **Depth Map Absence**: If `depth_in` is empty or missing, the effect should either bypass itself entirely or fall back to displaying `video_in` at 100% opacity.
- **Shader Compilation**: Standard shader compilation error handling must be used to ensure typos don't crash the engine (SAFETY RAIL #7).

---

## Dependencies

- OpenGL Context (ModernGL / PyOpenGL).
- VJLive3 Plugin API.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_portal_composite_manifest` | Validates plugin manifest structure and expected parameters. |
| `test_portal_composite_missing_bg` | Supplying `None` to the background input results in a valid shader execution without crashes. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD03: Depth Portal Composite`
- [ ] BOARD.md updated
