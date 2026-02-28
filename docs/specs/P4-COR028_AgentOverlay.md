# P4-COR028_AgentOverlay.md

**Phase:** Phase 4 / P4-COR028  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR028 — AgentOverlay

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `VJlive-2/core/text_overlay.py`  
**Legacy Class:** `AgentOverlay`  

---

## What This Module Does

`AgentOverlay` is a specialized subsystem extending `TextOverlayManager` specifically to render the "Neural Link" HUD for audience visibility. It continuously polls the `AgentPerformanceBridge` to extract real-time AI metrics (`intent`, `adrenaline`, `success_metric`, `interaction_mode`) and projects them onto the screen as stylized ASCII text elements. Moreover, it actively modifies the output video frame buffer via a global OpenCV Additive Blend, tinting the output feed based on the AI's current point on the Mood Manifold.

---

## What It Does NOT Do

- Does NOT mutate or update agent state—it is a strictly read-only subscriber to `AgentPerformanceBridge`.
- Does NOT execute LLM prompts or generate strings; it merely formats precalculated `state` integers/strings.
- Does NOT use the NodeGraph pipeline. It bypasses WebGL shaders entirely to run global OpenCV math overlays at the tail-end of the `frame` render cycle.

---

## Public Interface

```python
import numpy as np
from typing import Any, Optional
from vjlive3.plugins.base import BasePlugin

# Assumes TextOverlayManager inheritance exists in the VJLive3 core utilities

class AgentOverlay(BasePlugin): # Specifically extending TextOverlayManager equivalent
    """
    Specialized Heads-Up Display for visualizing Agent internals (Neural Link),
    including text readouts and global frame mood-tinting.
    """
    
    METADATA = {
        "id": "AgentOverlay",
        "type": "overlay",
        "version": "1.0.0",
        "legacy_ref": "text_overlay (AgentOverlay)"
    }
    
    def __init__(self, agent_bridge: Optional[Any] = None, max_elements: int = 10) -> None:
        """Initializes the fixed HUD indices (Intent, Mood, Control Balance)."""
        pass
        
    def update(self, current_time: float, width: int, height: int) -> None:
        """Extracts metrics from `agent_bridge` and updates the text layer models."""
        pass
        
    def render(self, frame: np.ndarray) -> np.ndarray:
        """
        Applies OpenCV additive blending to the raw NumPy frame based on the mood manifold,
        draws the Symbiotic Link visualizer bar, and invokes the parent text renderer.
        """
        pass
```

---

## Inputs and Outputs

### Constructor Parameters

| Name | Type | Description |
|------|------|-------------|
| `agent_bridge` | `Any` | Polled reference for state. Must implement `get_agent_state()`. |
| `max_elements` | `int` | Cap passed to the standard `TextOverlayManager`. Default `10`. |

### `AgentBridge` Polling Keys

The `update` method expects `agent_bridge.get_agent_state()` to yield a `Dict` with the following expected (but fallback-safe) keys:
- `'intent'`: Format to `INTENT: {intent.upper()}`
- `'adrenaline'`: Flot scalar affecting color red/blue interpolation.
- `'success_metric'`: Display as `SYNC: {success:.2f}`
- `'interaction_mode'`: Parsed to display specific override texts (`PILOT`, `AUTONOMOUS`, `COLLABORATE`).
- `'effective_influence'`: Float bounding the Collaborative ratio.
- `'manifold_position'`: `List[float]` of length 16. Used during `render()`.

### `render(frame: np.ndarray)` Outputs
- **Input:** Raw `HxWx4` BGRA or `HxWx3` BGR numpy array depending on pipeline.
- **Output:** Mutated `numpy.ndarray`. 

#### Mood Tinting Mathematics
Indexes `manifold_position`:
1. `energy = mood[0]`: Scales Red channel max `50`
2. `ethereal = mood[1]`: Scales Blue channel max `50`
3. `complex_val = mood[2]`: Scales Green channel max `30`

Applies tint *in-place* to prevent array allocations using OpenCV: `cv2.add(frame[:,:,x], np.array([intensity], dtype=np.uint8), dst=frame[:,:,x])`

---

## Edge Cases and Error Handling

### Missing Dependencies
- If `agent_bridge` is `None` or not provided, both `update()` and `render()` must short-circuit and exit early, skipping state parsing and tinting completely without crashing the render loop.
- If `agent_bridge.get_agent_state()` returns an empty dictionary, `dict.get()` fallbacks must be robust: `intent` defaults to `'unknown'`, `adrenaline` to `0.0`, etc.
- If `manifold_position` is missing from the state dictionary, it defaults to a neutral `[0.5]*16` list to prevent index out of bounds on `mood[0]`.

### Invalid Parameters
- The OpenCV `cv2.add` function intrinsically handles `uint8` 255-clipping. Do NOT utilize `numpy` direct scalar addition (`frame[:,:,0] += b`) as Python/numpy wraps `255 + 1` to `0`, causing psychedelic graphical shearing (noted as a legacy critical bug in the file comments). Explicitly rely on `cv2.add` saturation math.

---

## Dependencies

### External Libraries
- `numpy` (array matrices)
- `cv2` (OpenCV math utilities `cv2.add`, `cv2.rectangle`, `cv2.line`)

### Internal Modules
- `TextOverlayManager` (legacy text layout manager)
- `AgentPerformanceBridge` reference binding.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_hud_initialization` | The 3 fixed IDs (Intent, Mood, Control) are successfully mapped into the internal text array limits. |
| `test_adrenaline_color_shift` | Passing `adrenaline=1.0` yields a BGR color tuple of `(0, 255, 255)` (Pure red shift) for the Mood text. Passing `0.0` yields `(255, 255, 0)` (Pure blue shift). |
| `test_symbiotic_bar_rendering` | `render()` successfully invokes `cv2.rectangle` without bounds errors when passing a mock frame matrix. |
| `test_additive_blend_clipping` | Supplying a mock frame pixel of `[250, 250, 250]` and an `ethereal` manifold value generating a blue target of `+50` results in a capped output of `[255, 250, 250]`, verifying no modulo wraparound occurs. |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR028: AgentOverlay` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- Preserve the precise text strings and abbreviations. Specifically: `"INTENT: "`, `"ADRENALINE: "`, `"SYNC: "`, `"MODE: SYMBIOTIC PILOT (HUMAN OVERRIDE ACTIVE)"`, `"MODE: FULL AUTONOMY"`. These define the cyberpunk "feeling" of the HUD.
- The `_tint_cache` optimization using an `np.int16` buffer array persists in legacy code to avoid creating numpy scalar arrays for `cv2.add` bounds if the state hasn't changed. While modern numpy is fast, maintaining this cache allocation is considered best practice.

### Architectural Risks
- VJLive3 utilizes a heavy WebGL GLSL node graph wrapper, whereas this legacy overlay injects directly into final CPU-side numpy matrices via OpenCV. Re-verify if VJLive3 handles post-processing through `EffectNodes` asynchronously or if this must be attached to the absolute final Qt GUI painter. If migrating to GLSL, the `cv2.add` must translate directly into a fragment shader `+` operation bounded by a `clamp(x, 0.0, 1.0)`.
