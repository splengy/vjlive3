# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P4-COR157_audio_kaleidoscope.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-COR157 — Audio Kaleidoscope

**Phase:** Phase 4 / P4-COR157
**Assigned To:** Antigravity
**Spec Written By:** Antigravity
**Date:** 2026-02-23

---

## What This Module Does

This module implements the `AudioKaleidoscopeEffect` (and its corresponding Matrix Node `AudioKaleidoscopeNode`), ported from the legacy `VJlive-2/core/core_plugins/audio_kaleidoscope.py` codebase. It behaves as a screen-space UV-transforming procedural fragment shader. It converts Cartesian pixel coordinates into Polar domains (radius, angle) to split the screen into symmetrical, mirrored geometric segments. Furthermore, it explicitly maps incoming audio feature arrays to drive geometric rotation (bass), scaling (mid), mirror-blending (treble), and overall RGB brightness (beat, bass, mid, treble) natively inside the GLSL pass.

---

## What It Does NOT Do

- **It does not perform mesh distortion.** It is a strict 2D image processing effect operating on a pre-rendered texture pipeline.
- It does not calculate audio Fast Fourier Transforms (FFTs) internally. Like all VJLive3 audio effects, it relies on the pre-computed `AudioAnalyzer` variables passed via `apply_uniforms` on the CPU side.

---

## Legacy References

- **Source Codebase**: `VJlive-2`
- **File Paths**: `core/core_plugins/audio_kaleidoscope.py`, `core/matrix/node_effect_audio.py`
- **Class Names**: `AudioKaleidoscope`, `AudioKaleidoscopeNode` 
- **Key Methods**: `_get_fragment_shader`, `kaleidoscope` (GLSL function), `apply_uniforms`
- **Architectural Soul**: The real magic of this effect lies in its GLSL implementation. Instead of relying on multipass geometry, all reflection math `angle_offset`, `segments`, and modulo math `mod(segment_idx, 2.0)` are calculated dynamically per pixel. The port MUST retain the procedural purity of the legacy `kaleidoscope(uv, segments, angle_offset, scale)` GLSL function to maintain the original visual aesthetic. 

---

## Public Interface

```python
from core.effects.shader_base import EffectPlugin

class AudioKaleidoscopeEffect(EffectPlugin):
    """
    Procedural polar-coordinate UI transformation shader.
    Ported from VJLive-2 AudioKaleidoscope.
    """
    
    METADATA = {
        "segments": 8,            # Number of kaleidoscope radial slices
        "angle_offset": 0.0,      # Global rotational offset
        "scale": 1.0,             # Zoom multiplier
        "rotation_speed": 1.0,    # Baseline time-driven rotation
        "mirror_effect": 1.0,     # Blend intensity of geometric reflection
        "audio_sensitivity": 1.0  # Global multiplier for audio reactivity
    }

    def __init__(self) -> None: ...
    def _get_fragment_shader(self) -> str: ...
    def apply_uniforms(self, time: float, resolution: tuple, 
                       audio_reactor=None, semantic_layer=None) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `segments` | `int` | Number of geometric slice reflections | 3 to 32 |
| `angle_offset` | `float` | Base offset for coordinate rotation | 0.0 to 10.0 |
| `scale`| `float` | Spatial coordinate scaling inside the segment | 0.1 to 3.0 |
| `rotation_speed`| `float` | Multiplier against `uniform float time` | -5.0 to 5.0 |
| `mirror_effect`| `float` | Blend interpolation multiplier for the mirrored UVs | 0.0 to 1.0 |
| `audio_sensitivity`| `float` | Global scalar applied against all incoming audio bounds | 0.1 to 3.0 |

---

## Edge Cases and Error Handling

- **Missing Audio Fallback:** If `audio_reactor=None` is explicitly or implicitly passed to `apply_uniforms`, the effect must gracefully default all audio-dependent variables (`bass_level`, `mid_level`, `treble_level`, `beat_level`) to `0.0`. The script must NOT throw an exception, and the kaleidoscope should simply render a static spin unmodulated by audio.
- **GLSL Float Modulo Constraints:** Some strict OpenGL drivers behave erratically with negative float inputs into the `mod()` function. The ported fragment shader should evaluate using `fract()` or absolute clamping where possible if negative space coordinate artifacts appear.

---

## Dependencies

- External libraries needed:
  - None required beyond standard GL bindings for Python. No external array allocations happening here.
- Internal modules this depends on:
  - `vjlive3.effects.EffectPlugin` (Standard base interface).
  - `vjlive3.audio.constants.AudioFeature` (Volume, Bass, Mid, Treble, Beat constants).

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_kaleidoscope_init_defaults` | Validates initialization and `METADATA` property mappings |
| `test_kaleidoscope_graceful_missing_audio` | Passing `audio_reactor=None` avoids crashing `apply_uniforms` |
| `test_kaleidoscope_audio_matrix_routing` | Validating the CPU-to-GPU uniform mapping successfully assigns `bass_level` when mock audio provides bass hits |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR157: Audio Kaleidoscope Spec & Port` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
