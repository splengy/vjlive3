# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P3-EXT078_fire_particles_effect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT078 — Fire Particles Effect

**Phase:** Phase 3 / P3-EXT078
**Assigned To:** Antigravity
**Spec Written By:** Antigravity
**Date:** 2026-02-23

---

## What This Module Does

This module implements the `FireParticles` effect, ported from the legacy `VJlive-2/plugins/core/generator_particles_extra/shadertoy_particles.py` codebase. It combines a CPU-side physics simulation with a GPU-side GLSL fragment shader to generate an audio-reactive, convection-driven particle system. Unlike basic particle systems, the vertical rising motion ("fire"), horizontal turbulence, and particle "energy" (brightness/color) are directly modulated by real-time audio features (Volume, Bass, Mid, Treble, Beat), creating a highly dynamic, organic flame effect that "dances" to the frequency spectrum. 

---

## What It Does NOT Do

- **It does not utilize compute shaders.** The physics simulation (position, velocity, energy) runs entirely on the CPU in a NumPy array loop. Hardware-accelerated GPGPU simulation is explicitly out of scope for this task to maintain strict legacy parity.
- It does not modify global audio configurations. It merely consumes audio features passed to it via the universal `apply_uniforms` context.

---

## Legacy References

- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/core/generator_particles_extra/shadertoy_particles.py`
- **Class Names**: `FireParticles` (inherits from `ShadertoyParticles`)
- **Key Methods**: `_update_particles`, `_get_fragment_shader`, `_resize_particles`, `apply_uniforms`, `post_render`
- **Architectural Soul**: The legacy implementation dynamically generates `GL_TEXTURE_2D` buffers *every frame* to pass `(pos.x, pos.y, vel.x, vel.y)` and `(energy, type)` arrays to the fragment shader. 

---

## Public Interface

```python
import numpy as np
from core.effects.shader_base import EffectPlugin

class FireParticlesEffect(EffectPlugin):
    """
    Audio-reactive fire particle system utilizing CPU physics and a 
    multipass shader. Ported from VJLive-2 ShadertoyParticles.
    """
    
    METADATA = {
        "particle_count": 200,          # Base particle count
        "color_hue": 0.08,             # Orange/red baseline
        "color_saturation": 0.8,
        "particle_size": 0.005,
        "trail_length": 0.95,
        "attraction_strength": 0.2,
        "repulsion_strength": 0.1,
        "velocity_damping": 0.98,
        "audio_sensitivity": 1.0,
        "volume_mix": 1.0,
        "bass_mix": 1.0,
        "mid_mix": 1.0,
        "treble_mix": 1.0,
        "beat_mix": 1.0
    }

    def __init__(self) -> None: ...
    def _get_fragment_shader(self) -> str: ...
    def _resize_particles(self) -> None: ...
    def apply_uniforms(self, time: float, resolution: tuple, 
                       audio_reactor=None, semantic_layer=None) -> None: ...
    def _update_particles(self, time: float, volume: float, bass: float, 
                          mid: float, treble: float, beat: float) -> None: ...
    def post_render(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `particle_count` | `int` | Number of active particles | 50 to 1000 (Legacy capped at 500 in shader loops to prevent GLSL timeout) |
| `color_hue` | `float` | Base hue of the fire | 0.0 to 1.0 |
| `color_saturation`| `float` | Base saturation of the fire | 0.0 to 2.0 |
| `audio_sensitivity`| `float` | Global multiplier for audio reactivity | 0.1 to 3.0 |
| `(Array Buffers)` | `Texture` | Particle states packed into `sampler2D` textures | Passed explicitly to `tex1` and `tex2` slots |

---

## Edge Cases and Error Handling

- **Memory Leak Risk (Legacy Bug):** The legacy `apply_uniforms` generated new OpenGL textures for particle data *every single frame* (`glGenTextures`) and attempted to delete them in `post_render`. We must explicitly refactor this to initialize the FBO textures *once* and dynamically update them via `glTexSubImage2D` to prevent severe memory leaks.
- **GLSL Loop Timeouts (Safety Rail #1):** The shader contains an explicit `for` loop over `min(particle_count, 500)`. This strict bound must be preserved to prevent GPU watchdog timeouts on lower-tier hardware.
- What happens if the `audio_reactor` is missing? → (Fallback: All audio features default to `0.0`, resulting in a calm, non-reactive flame).

---

## Dependencies

- External libraries needed:
  - `numpy` — Critical for vectorized array initializations and physics updates.
  - `OpenGL.GL` — Required for `glTexSubImage2D` and `GL_RGBA32F` texture updates.
- Internal modules this depends on:
  - `vjlive3.effects.EffectPlugin` (Base capability routing).
  - `vjlive3.audio.constants.AudioFeature` (Volume, Bass, Mid, Treble, Beat constants).

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_fire_particles_init` | Initializes without crashing and sets up default NumPy arrays |
| `test_fire_particles_resize` | Dynamically increasing `particle_count` correctly rebuilds NumPy arrays |
| `test_fire_particles_audio_reactivity` | Passing mock audio to `apply_uniforms` alters the underlying `_update_particles` physics vectors |
| `test_fbo_leak_prevention` | Ensures `glGenTextures` is only called during initialization, not on every frame render loop. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT078: Fire Particles Effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
