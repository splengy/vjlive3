# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P4-COR149_audio_spectrum_trails.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-COR149 — Audio Spectrum Trails

**Phase:** Phase 4 / P4-COR149
**Assigned To:** Antigravity
**Spec Written By:** Antigravity
**Date:** 2026-02-23

---

## What This Module Does

This module implements the `AudioSpectrumTrails` effect (and its corresponding Matrix Node `AudioTrailsNode`), ported from the legacy `VJlive-2/core/core_plugins/audio_spectrum_trails.py` codebase. It visualizes raw 512-bin audio spectrum data as a persistent, trailing waveform rendering directly on the GPU. Using an explicit custom fragment shader and `texPrev` (ping-pong FBO feedback), it generates "waterfall-like" spectral histories colored by dynamic frequency mapping strategies (Rainbow, Heat, or Blue-Red). 

---

## What It Does NOT Do

- **It does not perform FFT or audio analysis itself.** It relies completely on the shared `AudioAnalyzer` (via `vjlive3.audio.audio_reactor`) to stream the raw `np.ndarray` float buffer.
- It does not process video or spatial inputs. It generates its own visual imagery over existing backgrounds (or black).

---

## Legacy References

- **Source Codebase**: `VJlive-2`
- **File Paths**: `core/core_plugins/audio_spectrum_trails.py`, `core/matrix/node_effect_audio.py`
- **Class Names**: `AudioSpectrumTrails`, `AudioTrailsNode` 
- **Key Methods**: `render`, `create_texture_1d`, `get_color` (GLSL function)
- **Architectural Soul**: The legacy component has a fatal design flaw: it calls `glGenTextures(1)` and `glDeleteTextures(1, [spectrum_tex])` mathematically bounded inside the `render()` loop, creating and destroying OpenGL texture handles 60 times a second. This churn causes driver context exhaustion. The VJLive3 port MUST fix this by allocating a single `GL_TEXTURE_1D` buffer during initialization and updating it exclusively via `glTexSubImage1D`.

---

## Public Interface

```python
import numpy as np
from core.effects.shader_base import EffectPlugin

class AudioSpectrumTrailsEffect(EffectPlugin):
    """
    Audio-reactive spectrum visualization with temporal decay (trails).
    Ported from VJLive-2 AudioSpectrumTrails.
    """
    
    METADATA = {
        "trail_decay": 0.95,      # Decay rate for fading trails
        "color_mapping": 0,       # 0=Rainbow, 1=Heat, 2=Blue-Red
        "energy_threshold": 0.1,  # Minimum amplitude threshold
        "trail_length": 0.8       # Amplitude scalar multiplier
    }

    def __init__(self) -> None: ...
    def _get_fragment_shader(self) -> str: ...
    def apply_uniforms(self, time: float, resolution: tuple, 
                       audio_reactor=None, semantic_layer=None) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `trail_decay` | `float` | Retention multiplier for previous frames (`texPrev`) | 0.8 to 0.999 |
| `color_mapping` | `int` | Shader index routing switch | 0, 1, or 2 |
| `energy_threshold`| `float` | Gate minimum before drawing spectral bar | 0.0 to 1.0 |
| `trail_length`| `float` | Multiplier dictating Y-axis reach of the visualization | 0.1 to 2.0 |
| `spectrum_tex` | `GL_TEXTURE_1D` | Reusable pre-allocated hardware 1D buffer | 512 `GL_R32F` floats |

---

## Edge Cases and Error Handling

- **Optimization Constraint (Safety Rail #1):** Eliminate the immediate mode churn found in the legacy legacy `render` method wrapper. Rely on the overarching `UnifiedShaderManager` for standard GLSL compilation and use `apply_uniforms` to push the data into a static `self.spectrum_tex_id` via `glTexSubImage1D`.
- What happens if the `audio_reactor` is missing? → It behaves gracefully, filling the `spectrum_tex` with `0.0`s resulting in a slow fade-out based on `trail_decay` followed by persistent black.
- **Cleanup Requirement (Safety Rail #8):** The single `self.spectrum_tex_id` must be explicitly freed in a custom `.cleanup()` method to prevent memory leakage upon effect deletion/hotswapping.

---

## Dependencies

- External libraries needed:
  - `numpy` — Structuring the 512-float spectrum arrays.
  - `OpenGL.GL` — For 1D textures (`GL_TEXTURE_1D`, `glTexSubImage1D`).
- Internal modules this depends on:
  - `vjlive3.effects.EffectPlugin` (Standard base interface).

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_st_init_preallocates_tex` | Validates that a static 1D texture handle is generated in `__init__` |
| `test_st_audio_missing_safeties` | Pipeline doesn't crash if `audio_reactor=None` is passed to `apply_uniforms` |
| `test_st_glTexSubImage1D_called` | Simulating audio correctly uploads the spectrum array using sub-image routing |
| `test_st_cleanup_routine` | The pre-allocated texture handle is safely deleted via OpenGL calls in `cleanup()` |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR149: Audio Spectrum Trails Spec & Port` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
