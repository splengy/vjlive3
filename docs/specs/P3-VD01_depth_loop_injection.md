# Spec Template — P3-VD01 Depth Loop Injection

**File naming:** `docs/specs/P3-VD01_depth_loop_injection.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD01 — Depth Loop Injection

**Phase:** Phase 3
**Assigned To:** (Pending Manager Assignment)
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module ports the "Depth Loop Injection Datamosh" plugin from VJlive-2 into VJLive3's modernized plugin system. It implements a multi-stage datamosh shader that exposes explicit send/return "loop points" in the rendering pipeline. This acts as a modular routing hub, allowing users to inject other node graph effects at different stages:
1. `PRE_LOOP` (Before depth modulation)
2. `DEPTH_LOOP` (After depth modulation)
3. `MOSH_LOOP` (After datamosh)
4. `POST_LOOP` (After feedback)

---

## What It Does NOT Do

- It does NOT manage the node graph connections themselves (that's handled by P1-N1). It simply exposes the texture inputs/outputs required for those connections.
- It does NOT calculate the actual depth map (it requires a depth texture as an input).

---

## Public Interface

```python
import numpy as np
from vjlive3.plugins.api import Plugin, VJLiveAPI
from vjlive3.plugins.registry import PluginManifest

# Must include METADATA mirroring params for self-documentation (PRIME DIRECTIVE #2)
METADATA = {
    "name": "Depth Loop Injection",
    "description": "Routeable datamosh with explicit send/return loops.",
    "version": "1.0.0",
    "parameters": [
        {"name": "pre_loop_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "depth_loop_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "mosh_loop_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "post_loop_mix", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "datamosh_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "feedback_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
    ],
    "inputs": ["video_in", "depth_in", "pre_return", "depth_return", "mosh_return", "post_return"],
    "outputs": ["video_out", "pre_send", "depth_send", "mosh_send", "post_send"]
}

class DepthLoopInjectionPlugin(Plugin):
    """Modular routing hub effect."""
    def __init__(self, api: VJLiveAPI) -> None: ...
    def on_load(self) -> None: ...
    def process(self, context) -> None: ...
    def on_unload(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| Inputs | GL Textures | Main video, depth map, and 4 optional return textures. |
| Outputs | GL Textures | Main output, and 4 send textures for the loop points. |

---

## Edge Cases and Error Handling

- **Missing Returns**: If a loop has a `mix` > 0.0 but no texture is connected to its return port, the shader MUST fall back to bypassing that loop (using the send texture directly) to avoid black screens or undefined behavior. (SAFETY RAIL #7).
- **Feedback Loops**: The datamosh relies on an internal feedback FBO. This FBO must be properly ping-ponged. On shutdown, these FBOs and textures must be deleted (SAFETY RAIL #8).

---

## Dependencies

- OpenGL Context (ModernGL / PyOpenGL).
- VJLive3 Plugin API.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_depth_loop_injection_manifest` | Plugin manifest validates against Pydantic schema and includes required METADATA. |
| `test_depth_loop_bypassed` | Processing without return textures gracefully ignores mix parameters and renders without crashing. |
| `test_depth_loop_fbo_cleanup` | Unloading the plugin explicitly deletes its ping-pong FBOs. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD01: Depth Loop Injection` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
