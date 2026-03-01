# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P4-COR150_audio_waveform_distortion.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-COR150 — Audio Waveform Distortion

**Phase:** Phase 4 / P4-COR150
**Assigned To:** Antigravity
**Spec Written By:** Antigravity
**Date:** 2026-02-23

---

## What This Module Does

This module implements the `AudioWaveformDistortion` effect, ported from the legacy `VJlive-2/core/core_plugins/audio_waveform_distortion.py` codebase. It is an advanced screen-space deformation shader that directly maps a 1D audio waveform buffer into 2D UV coordinate distortions. By leveraging a single-channel `GL_R32F` OpenGL texture to pass 1024 frames of raw audio samples to the GPU, it creates a visual "tearing" or "waving" scanline effect that is inextricably linked to the music's frequency and bass depth. Additional audio-reactive color shifting (chromatic aberration) is modulated by the bass and global volume.

---

## What It Does NOT Do

- **It does not perform audio analysis itself.** It relies entirely on the `AudioAnalyzer` (or `audio_reactor` in VJLive3) to provide the 1024-length float array of the current waveform.
- It does not calculate optical flow. The distortion is procedurally generated using sine/cosine waves mathematically mixed with the waveform texture values, rather than tracking actual pixel movement.

---

## Legacy References

- **Source Codebase**: `VJlive-2`
- **File Paths**: `core/core_plugins/audio_waveform_distortion.py`
- **Class Names**: `AudioWaveformDistortion` 
- **Key Methods**: `_get_fragment_shader`, `apply_uniforms`, `get_parameter`, `set_parameter`
- **Architectural Soul**: Notably, unlike other legacy plugins that suffered from FBO memory leaks, this specific implementation correctly utilized a pre-allocated `glGenTextures(1)` 1D buffer in `__init__`, updating it via `glTexSubImage2D` in `apply_uniforms`. This critical memory-safe optimization MUST be preserved in the VJLive3 port.

---

## Public Interface

```python
import numpy as np
from core.effects.shader_base import EffectPlugin

class AudioWaveformDistortionEffect(EffectPlugin):
    """
    Screen distortion effect based on raw audio waveform data.
    Ported from VJLive-2 AudioWaveformDistortion.
    """
    
    METADATA = {
        "distortion_strength": 0.05,
        "frequency_scale": 1.0,
        "smoothing": 0.8,
        "color_shift": 0.1
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
| `distortion_strength` | `float` | Base multiplier for UV tearing | 0.0 to 0.5 |
| `frequency_scale` | `float` | Frequency multiplier for sine/cosine procedural displacement | 0.1 to 5.0 |
| `smoothing`| `float` | Reserved metadata (used for easing incoming parameters) | 0.0 to 1.0 |
| `color_shift`| `float` | Intensity of bass-driven RGB aberration | 0.0 to 1.0 |
| `waveform_tex` | `GL_TEXTURE_2D` | Pre-allocated 1D buffer uploaded to GPU via `tex1` | Exactly 1024 samples long |

---

## Edge Cases and Error Handling

- **Safety Rail #8 (FBO Leaking Protocol):** The legacy `__del__` method attempted immediate-mode GL cleanup (`glDeleteTextures`). In VJLive3, this MUST be routed through the explicit `_free_resources` / `cleanup` lifecycle to ensure thread-safe context deletion, or risk crashing the GPU context queue.
- What happens if the `audio_reactor` is missing? → The waveform buffer remains `0.0`. The script must catch `audio_reactor=None` gracefully, continuing to render the pass with zeroed distortion.

---

## Dependencies

- External libraries needed:
  - `numpy` — Array generation for the waveform buffer.
  - `OpenGL.GL` — For `GL_R32F` and texture binding commands.
- Internal modules this depends on:
  - `vjlive3.effects.EffectPlugin` (Standard base).

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_waveform_init_allocates_texture` | Ensures the 1D GL buffer is correctly pre-allocated during `__init__` |
| `test_waveform_graceful_missing_audio` | Passing `audio_reactor=None` doesn't crash the pipeline |
| `test_texsubimage2d_update` | Simulating an audio frame correctly scales the NumPy array to length `1024` and triggers texture update |
| `test_clean_fbo_deletion` | Ensures the `waveform_tex` GL resource is explicitly freed upon effect destruction |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR150: Audio Waveform Distortion Spec & Port` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
