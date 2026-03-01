# Spec Template — P3-VD02 Depth Parallel Universe

**File naming:** `docs/specs/P3-VD02_depth_parallel_universe.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD02 — Depth Parallel Universe

**Phase:** Phase 3
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module ports the "Depth Parallel Universe Datamosh" plugin from VJlive-2. It splits the input signal into three "parallel universes" (near-field, mid-field, far-field), each possessing its own datamosh processing chain and external loop returns. The depth map acts as a reality selector, determining which universe dominates at each pixel.

---

## What It Does NOT Do

- It does NOT calculate depth itself; it maps an incoming depth texture to determine the split thresholds for the 3 universes.
- It does NOT manage graph UI topology.

---

## Public Interface

```python
import numpy as np
from vjlive3.plugins.api import Plugin, VJLiveAPI
from vjlive3.plugins.registry import PluginManifest

# Must include METADATA mirroring params for self-documentation (PRIME DIRECTIVE #2)
METADATA = {
    "name": "Depth Parallel Universe",
    "description": "Splits signal into 3 depth-based universes with independent FX chains.",
    "version": "1.0.0",
    "parameters": [
        {"name": "depth_split_near", "type": "float", "min": 0.0, "max": 1.0, "default": 0.33},
        {"name": "depth_split_far", "type": "float", "min": 0.0, "max": 1.0, "default": 0.66},
        {"name": "universe_a_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "universe_b_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "universe_c_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
    ],
    "inputs": ["video_in", "depth_in", "universe_a_return", "universe_b_return", "universe_c_return"],
    "outputs": ["video_out", "universe_a_send", "universe_b_send", "universe_c_send"]
}

class DepthParallelUniversePlugin(Plugin):
    """Multi-universe routing effect."""
    def __init__(self, api: VJLiveAPI) -> None: ...
    def on_load(self) -> None: ...
    def process(self, context) -> None: ...
    def on_unload(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| Inputs | GL Textures | Main video, depth map, and 3 optional returns per universe. |
| Outputs | GL Textures | Main merged output, and 3 send textures representing the separated signals. |

---

## Edge Cases and Error Handling

- **Missing Returns**: Like the loop injection plugin, if a universe's return texture is not connected, the internal shader must fallback to using the local datamoshed signal rather than rendering black.
- **Overlapping Depth Splits**: If `depth_split_near` > `depth_split_far`, the shader should internally clamp/swap them to prevent logical collapse.
- **Resource Management**: 3 independent feedback FBOs must be instantiated and properly released on unload (SAFETY RAIL #8).

---

## Dependencies

- OpenGL Context (ModernGL / PyOpenGL).
- VJLive3 Plugin API.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_parallel_universe_manifest` | Plugin manifest validates and includes `METADATA`. |
| `test_parallel_universe_split_clamp` | Parameter updates that try to cross split thresholds are handled gracefully. |
| `test_parallel_universe_fbo_cleanup` | Unloading the plugin releases all 3 sets of ping-pong FBOs without memory leaks. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD02: Depth Parallel Universe` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
