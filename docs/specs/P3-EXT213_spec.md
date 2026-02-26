# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT213_audio_spectrum_trails.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT213 — audio_spectrum_trails

### Description

The `AudioSpectrumTrails` effect creates a particle system where particles move and glow in response to audio frequency data. Each particle is assigned to one of eight frequency bands (bass, mid, treble subdivided), and its color, size, and velocity are modulated by the energy in that band. The effect renders particles as glowing spots with soft halos, creating a trail-like visual that pulses and dances with the music.

The system uses a hybrid CPU/GPU architecture: the CPU updates particle positions, velocities, and energies each frame based on audio analysis, then uploads this data to shader uniform arrays. The GPU fragment shader loops over all particles for each pixel, drawing a bright core and a larger dim halo around each particle. The result is a lightweight, real-time effect suitable for VJ performances.

The legacy implementation from `vjlive1/core/effects/audio_reactive.py` provides the reference behavior. This spec preserves the original's approach while clarifying incomplete aspects such as position updates, velocity damping, and energy computation.

**What This Module Does**

- Renders up to 100 particles whose colors reflect audio frequency bands (bass=red, mid=green, treble=blue)
- Updates particle positions and velocities each frame based on audio-driven forces
- Computes particle energies from frequency band energy and overall volume
- Draws each particle as a circular core plus a radial halo (misleadingly called "trail")
- Accepts audio data via an `AudioAnalyzer` or `AudioReactor` interface
- Exposes UI parameters mapped to internal ranges (particle count, size, speed, halo size, color sensitivity)

**What This Module Does NOT Do**

- Does NOT implement collisions, gravity, or advanced particle physics
- Does NOT support more than 100 particles (shader uniform array limit)
- Does NOT store or replay audio; uses only current frame's spectrum
- Does NOT provide 3D depth; particles are 2D screen-space
- Does NOT include its own UI; parameters are set via `set_parameter`
- Does NOT handle audio analysis; relies on external `AudioAnalyzer`

---

## Detailed Behavior and Parameter Interactions

### Particle System Architecture

The effect uses a hybrid CPU/GPU approach:

1. **CPU side**:
   - Maintains arrays: `particle_positions` (Nx2), `particle_velocities` (Nx2), `particle_energies` (N)
   - Each frame, `update(delta_time)` is called:
     - For each particle, compute audio influence from its assigned frequency band
     - Update velocity: add a small force in the direction of `(cos(angle), sin(angle))` where `angle = time * speed + particle_index * offset`
     - Update position: `pos += vel * dt`
     - Apply damping: `vel *= 0.99` to prevent unbounded growth
     - Wrap positions to [0,1] (toroidal space) to keep particles on screen
   - Upload particle data to shader uniforms: `particle_positions[100]`, `particle_energies[100]`
   - Set audio level uniforms: `bass_level`, `mid_level`, `treble_level`, `volume_level`

2. **GPU side (fragment shader)**:
   - For each pixel, loop over all particles (up to `num_particles`)
   - For each particle, compute distance from pixel to particle position
   - If within `particle_size`, draw a bright spot with color derived from audio bands: `(bass, mid, treble) * color_sensitivity`
   - Also draw a radial halo: if pixel is within `size * trail_length` distance from particle, add a dimmer contribution
   - Composite over background using `u_mix` (effect blend factor)

### Parameters

The effect exposes the following parameters (0-10 range, mapped to internal values in `apply_uniforms`):

| Parameter (UI) | Internal | Default | Description |
|----------------|----------|---------|-------------|
| `num_particles` | int (10-100) | 5.0 → 100 | Number of particles to render (mapped from 0-10 to 10-100) |
| `particle_size` | float (0.001-0.1) | 5.0 → 0.051 | Base particle radius in normalized screen space |
| `particle_speed` | float (0.1-2.0) | 5.0 → 1.0 | Angular speed of particle orbit (radians per second) |
| `trail_length` | float (0.1-2.0) | 8.0 → 1.9 | Halo size multiplier (larger = bigger glow) |
| `color_sensitivity` | float (0.1-5.0) | 5.0 → 2.5 | Multiplier for audio-driven color intensity |

The mapping from UI value (0-10) to internal is linear:
- `num_particles = int(10 + (value/10)*90)` (clamped to 100)
- `particle_size = 0.001 + (value/10)*0.099`
- `particle_speed = 0.1 + (value/10)*1.9`
- `trail_length = 0.1 + (value/10)*1.9`
- `color_sensitivity = 0.1 + (value/10)*4.9`

### Audio Reactivity

The effect uses an `AudioAnalyzer` to obtain:
- `bass_level` (0.0-1.0)
- `mid_level` (0.0-1.0)
- `volume_level` (0.0-1.0)

These are used in two ways:

1. **CPU update**: Each particle is assigned a frequency band (0-7, since `frequency_bands = 8`). The particle's energy is computed as `band_energy * volume`, where `band_energy` is the average of the spectrum in that band. The velocity is then perturbed in a direction based on time and particle index, scaled by `audio_influence = band_energy * volume * 2.0`.

2. **GPU rendering**: Particle color is set to `(bass_level, mid_level, treble_level) * color_sensitivity`. Particle size is scaled by `(1.0 + energy * volume_level * 2.0)`. This makes particles larger and brighter on loud beats.

### Particle Motion Details

The `update(delta_time)` method implements stable particle motion:
- For each particle `i`:
  - `freq_band = i % 8` (assign to one of 8 frequency bands)
  - `band_energy = get_frequency_band_energy(freq_band, analyzer)`
  - `energy = band_energy * volume` (fresh value each frame, not cumulative)
  - `angle = time * particle_speed + i * 0.1`
  - `audio_influence = band_energy * volume * 2.0`
  - `velocity[i] += (cos(angle), sin(angle)) * audio_influence * 0.01`
  - `velocity[i] *= 0.99` (damping to prevent explosion)
  - `position[i] += velocity[i] * delta_time`
  - If `position[i]` outside [0,1], wrap to [0,1] (toroidal space)

This ensures particles stay on screen and move smoothly without accumulating excessive velocity.

### Shader Uniforms

The fragment shader expects:
- `resolution` (vec2)
- `time` (float)
- `u_mix` (float, blend factor)
- `tex0` (sampler2D, background)
- `num_particles` (int)
- `particle_size` (float)
- `trail_length` (float)
- `color_sensitivity` (float)
- `particle_positions[100]` (array of vec2)
- `particle_energies[100]` (array of float)
- `bass_level`, `mid_level`, `treble_level`, `volume_level` (floats)

---

## Integration

### VJLive3 Pipeline Integration

`AudioSpectrumTrails` is an **Effect** that composites over the input framebuffer. It should be added to the effects chain and rendered as a source or overlay.

**Typical usage**:

```python
# Initialize
trails = AudioSpectrumTrails()
trails.set_audio_analyzer(analyzer)  # optional, can also pass via apply_uniforms

# Each frame:
trails.update(delta_time)  # updates particle positions and energies
# The effect's render() will call apply_uniforms and draw full-screen quad
```

The effect requires an OpenGL context. The base `Effect` class handles the full-screen quad and shader management.

### Audio Integration

The effect can be provided an `AudioAnalyzer` via `set_audio_analyzer`, or the caller can pass an `audio_reactor` to `apply_uniforms`. The `update` method uses the analyzer to get frequency band energies and volume. The `apply_uniforms` method sets the audio level uniforms for the shader.

---

## Performance

### Computational Cost

- **CPU**: For N particles (≤100), each update:
  - Compute band energy (O(1) per particle, using precomputed spectrum bands)
  - Update velocity and position: ~10 FLOPs per particle
  - Total: ~1000 FLOPs, negligible.
- **GPU**: Fragment shader loops over up to 100 particles per pixel. At 1080p (2M pixels), that's 200M particle checks per frame. Each check does a distance calculation, size comparison, and possibly color mixing. This is moderate but should be okay on modern GPUs (200M simple ops ~ 0.2ms at 1 TFLOP). However, the loop is unrolled? 100 iterations is a lot for a fragment shader; could be a performance bottleneck at high resolution. Consider reducing particle count or using a different technique (e.g., render particles to a separate buffer and blur). But legacy uses this approach, so we'll keep it.

### Memory Usage

- **CPU**: Arrays for 100 particles: positions (200 floats), velocities (200 floats), energies (100 floats) ≈ 2 KB.
- **GPU**: Uniform arrays: 100 vec2 + 100 float ≈ 1.2 KB. Shader program < 50 KB.
- **No textures** required.

### Optimization Strategies

- Reduce `num_particles` on low-end hardware.
- Use a lower resolution for the effect (render to a smaller FBO and upscale).
- Consider using a compute shader or point sprites instead of full-screen loop for better performance.

### Platform-Specific Considerations

- **Desktop**: Should run fine at 60 Hz with 100 particles at 1080p.
- **Embedded**: May need to limit to 50 particles or lower resolution.
- **Mobile**: Use with caution; test performance.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_audio_analyzer` | Effect initializes without crashing if no analyzer provided |
| `test_set_audio_analyzer` | Setting analyzer stores it correctly |
| `test_update_with_valid_spectrum` | update() processes spectrum and updates particle positions/energies without error |
| `test_update_with_empty_spectrum` | update() handles empty spectrum gracefully (particles remain stable) |
| `test_shader_uniforms_correctly_bound` | All uniforms (arrays, floats) are set before rendering |
| `test_particle_energy_modulation_by_bass_treble` | Particle energies reflect frequency band energy |
| `test_parameter_mapping` | UI parameters (0-10) correctly map to internal values |
| `test_particle_count_clamping` | num_particles is clamped to max 100 |
| `test_cleanup` | No OpenGL resource leaks on destruction |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT213: audio_spectrum_trails implementation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/core/effects/audio_reactive.py (L1-20)
```python
"""
Audio-Reactive Effects for VJLive
Real-time visual effects driven by audio analysis.
Ported from plugins/vaudio_reactive.
"""

import logging
import numpy as np
from typing import Tuple, Optional
from OpenGL.GL import (glGenTextures, glBindTexture, glTexParameteri, glTexImage2D,
                     glActiveTexture, GL_TEXTURE_2D, GL_LINEAR, GL_CLAMP_TO_EDGE,
                     GL_R32F, GL_RED, GL_FLOAT, GL_TEXTURE0,
                     GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, 
                     GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T)

from core.effects.shader_base import Effect
from core.audio_analyzer import AudioAnalyzer

logger = logging.getLogger(__name__)
```

### vjlive1/core/effects/audio_reactive.py (L17-36)
```python
from core.effects.shader_base import Effect
from core.audio_analyzer import AudioAnalyzer

logger = logging.getLogger(__name__)

DUMMY_FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;
void main() { FragColor = vec4(1.0, 0.0, 1.0, 1.0); }
"""

# ═══════════════════════════════════════════════════════════════
# Audio Particle System
# ═══════════════════════════════════════════════════════════════

class AudioParticleSystem(Effect):
    """Particles modulated by audio amplitude and frequency."""

    def __init__(self):
        super().__init__("audio_particle_system", self._get_fragment_shader())
```

### vjlive1/core/effects/audio_reactive.py (L33-52)
```python
    """Particles modulated by audio amplitude and frequency."""

    def __init__(self):
        super().__init__("audio_particle_system", self._get_fragment_shader())

        # Parameters (0-10 range handled in node/apply_uniforms)
        self.parameters = {
            "num_particles": 5.0,
            "particle_size": 5.0,
            "particle_speed": 5.0,
            "trail_length": 8.0,
            "color_sensitivity": 5.0,
        }

        self._num_particles = 100
        self.particle_positions = np.random.uniform(0, 1, (self._num_particles, 2)).astype(np.float32)
        self.particle_velocities = np.random.uniform(-0.01, 0.01, (self._num_particles, 2)).astype(np.float32)
        self.particle_energies = np.ones(self._num_particles, dtype=np.float32)
        self.frequency_bands = 8
        self.audio_analyzer = None
```

### vjlive1/core/effects/audio_reactive.py (L49-68)
```python
        self.particle_velocities = np.random.uniform(-0.01, 0.01, (self._num_particles, 2)).astype(np.float32)
        self.particle_energies = np.ones(self._num_particles, dtype=np.float32)
        self.frequency_bands = 8
        self.audio_analyzer = None

    def _get_fragment_shader(self):
        return """
        #version 330 core

        uniform vec2 resolution;
        uniform float time;
        uniform float u_mix;
        uniform sampler2D tex0;

        uniform int num_particles;
        uniform float particle_size;
        uniform float trail_length;
        uniform float color_sensitivity;
        uniform vec2 particle_positions[100];
        uniform float particle_energies[100];
```

### vjlive1/core/effects/audio_reactive.py (L65-84)
```python
        uniform float trail_length;
        uniform float color_sensitivity;
        uniform vec2 particle_positions[100];
        uniform float particle_energies[100];

        uniform float bass_level;
        uniform float mid_level;
        uniform float treble_level;
        uniform float volume_level;

        out vec4 fragColor;
        in vec2 uv;

        void main() {
            vec4 original = texture(tex0, uv);
            vec3 color = original.rgb;

            for (int i = 0; i < num_particles; i++) {
                vec2 particle_pos = particle_positions[i];
                float energy = particle_energies[i];
```

### vjlive1/core/effects/audio_reactive.py (L81-100)
```python
                float energy = particle_energies[i];

                vec2 diff = uv - particle_pos;
                float dist = length(diff);

                float size = particle_size * (1.0 + energy * volume_level * 2.0);

                if (dist < size) {
                    vec3 particle_color = vec3(
                        bass_level * color_sensitivity,
                        mid_level * color_sensitivity,
                        treble_level * color_sensitivity
                    );

                    float alpha = (1.0 - dist / size) * energy * u_mix;
                    color = mix(color, particle_color, alpha);
                }
```

### vjlive1/core/effects/audio_reactive.py (L97-116)
```python
                    float alpha = (1.0 - dist / size) * energy * u_mix;
                    color = mix(color, particle_color, alpha);
                }

                vec2 trail_dir = normalize(uv - particle_pos);
                float trail_dist = dist;
                if (trail_dist < size * trail_length) {
                    float trail_alpha = (1.0 - trail_dist / (size * trail_length)) * energy * 0.3 * u_mix;
                    vec3 particle_color = vec3(bass_level, mid_level, treble_level) * color_sensitivity;
                    color = mix(color, particle_color * 0.5, trail_alpha);
                }
            }

            fragColor = vec4(color, original.a);
        }
        """
```

### vjlive1/core/effects/audio_reactive.py (L113-132)
```python
            fragColor = vec4(color, original.a);
        }
        """

    def _resize_particles(self, count):
        self._num_particles = min(100, max(0, count)) # Hard limit 100 for shader
        self.particle_positions = np.random.uniform(0, 1, (self._num_particles, 2)).astype(np.float32)
        self.particle_velocities = np.random.uniform(-0.01, 0.01, (self._num_particles, 2)).astype(np.float32)
        self.particle_energies = np.ones(self._num_particles, dtype=np.float32)
```

### vjlive1/core/effects/audio_reactive.py (L129-148)
```python
        self.particle_energies = np.ones(self._num_particles, dtype=np.float32)

    def _get_frequency_band_energy(self, band_idx: int, analyzer: AudioAnalyzer) -> float:
        spectrum = analyzer.get_spectrum_data()
        if len(spectrum) == 0: return 0.0
        
        band_size = len(spectrum) // self.frequency_bands
        start_idx = band_idx * band_size
        end_idx = min(start_idx + band_size, len(spectrum))
        
        if start_idx >= len(spectrum): return 0.0
        return np.mean(spectrum[start_idx:end_idx])
```

### vjlive1/core/effects/audio_reactive.py (L145-164)
```python
        if start_idx >= len(spectrum): return 0.0
        return np.mean(spectrum[start_idx:end_idx])

    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None, semantic_layer=None):
        super().apply_uniforms(time, resolution, audio_reactor, semantic_layer)

        # Use passed audio_reactor if available, else local
        analyzer = audio_reactor if audio_reactor else self.audio_analyzer
        
        p = self.parameters
        num_particles = int(10 + (p.get('num_particles', 5.0) / 10.0) * 90) # Limit to 100
        particle_size = 0.001 + (p.get('particle_size', 5.0) / 10.0) * 0.099
        particle_speed = 0.1 + (p.get('particle_speed', 5.0) / 10.0) * 1.9
        trail_length = 0.1 + (p.get('trail_length', 8.0) / 10.0) * 1.9
        color_sensitivity = 0.1 + (p.get('color_sensitivity', 5.0) / 10.0) * 4.9

        if num_particles != self._num_particles:
            self._resize_particles(num_particles)

        if analyzer:
            bass = analyzer.get_feature_value(AudioAnalyzer.AudioFeature.BASS)
            mid = analyzer.get_feature_value(AudioAnalyzer.AudioFeature.MID)
            treble = analyzer.get_feature_value(AudioAnalyzer.AudioFeature.TREBLE)
            volume = analyzer.get_feature_value(AudioAnalyzer.AudioFeature.VOLUME)

            for i in range(self._num_particles):
                freq_band = i % self.frequency_bands
                band_energy = self._get_frequency_band_energy(freq_band, analyzer)

                angle = time * particle_speed + i * 0.1
                audio_influence = band_energy * volume * 2.0
                
                self.particle_velocities[i] += np.array([
                    np.cos(angle) * audio_influence * 0.01,
                    np.sin(angle) * audio_influence * 0.01
                ])
```

---

## Public Interface

```python
class AudioSpectrumTrails(Effect):
    def __init__(self) -> None:
        """Initialize the effect with default parameters."""
    
    def set_audio_analyzer(self, analyzer: AudioAnalyzer) -> None:
        """
        Set the audio analyzer to use for frequency data.
        
        Args:
            analyzer: An AudioAnalyzer instance that provides get_spectrum_data() and get_feature_value().
        """
    
    def update(self, delta_time: float) -> None:
        """
        Update particle positions and energies based on current audio spectrum.
        
        Args:
            delta_time: Time since last frame in seconds.
        """
    
    def apply_uniforms(self, time: float, resolution: Tuple[int, int],
                       audio_reactor: Optional[AudioReactor] = None,
                       semantic_layer: Optional[SemanticLayer] = None) -> None:
        """
        Apply shader uniforms and render the effect.
        
        Args:
            time: Current time in seconds.
            resolution: Screen resolution (width, height).
            audio_reactor: Optional audio context; if provided, overrides internal analyzer.
            semantic_layer: Unused.
        """
    
    # Inherited from Effect:
    # - render() (calls apply_uniforms)
    # - set_parameter(name, value)
    # - get_parameter(name)
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `analyzer` | `AudioAnalyzer` | Audio source providing spectrum and features | Must implement `get_spectrum_data()` and `get_feature_value()` |
| `delta_time` | `float` | Time delta for animation | ≥ 0.0 |
| `time` | `float` | Current playback time | ≥ 0.0 |
| `resolution` | `Tuple[int, int]` | Screen dimensions | width, height > 0 |
| `audio_reactor` | `Optional[AudioReactor]` | Alternative audio source | May be None |
| `num_particles` | `int` | Actual particle count (derived from UI param) | 10 ≤ N ≤ 100 |
| `particle_size` | `float` | Base particle radius in normalized coords | 0.001 - 0.1 |
| `particle_speed` | `float` | Angular speed for velocity perturbation | 0.1 - 2.0 rad/s |
| `trail_length` | `float` | Halo size multiplier | 0.1 - 2.0 |
| `color_sensitivity` | `float` | Color intensity multiplier | 0.1 - 5.0 |
| `bass_level`, `mid_level`, `treble_level`, `volume_level` | `float` | Audio features (0.0-1.0) | - |

---

## Dependencies

- External libraries:
  - `numpy` — required for particle arrays and audio spectrum processing
  - `OpenGL.GL` — required for shader rendering and uniform setting
- Internal modules:
  - `vjlive3.core.effects.shader_base.Effect` — base class
  - `vjlive3.core.audio_analyzer.AudioAnalyzer` — for audio features
  - `vjlive3.core.audio.AudioReactor` — optional alternative audio source

---

## Configuration Schema

```python
METADATA = {
  "params": [
    {"id": "num_particles", "name": "Particle Count", "default": 5.0, "min": 0.0, "max": 10.0, "type": "float", "description": "UI parameter (0-10) mapped to actual particle count (10-100)"},
    {"id": "particle_size", "name": "Particle Size", "default": 5.0, "min": 0.0, "max": 10.0, "type": "float", "description": "UI parameter (0-10) mapped to size (0.001-0.1)"},
    {"id": "particle_speed", "name": "Particle Speed", "default": 5.0, "min": 0.0, "max": 10.0, "type": "float", "description": "UI parameter (0-10) mapped to angular speed (0.1-2.0 rad/s)"},
    {"id": "trail_length", "name": "Trail Length", "default": 8.0, "min": 0.0, "max": 10.0, "type": "float", "description": "UI parameter (0-10) mapped to halo size multiplier (0.1-2.0)"},
    {"id": "color_sensitivity", "name": "Color Sensitivity", "default": 5.0, "min": 0.0, "max": 10.0, "type": "float", "description": "UI parameter (0-10) mapped to color intensity (0.1-5.0)"}
  ]
}
```

---

## State Management

- **Per-frame state**: `particle_positions`, `particle_velocities`, `particle_energies` are updated each `update(dt)`.
- **Persistent state**: Parameters (`num_particles`, `particle_size`, `particle_speed`, `trail_length`, `color_sensitivity`) and `audio_analyzer` reference.
- **Init-once state**: Shader program, uniform locations.
- **Thread safety**: Not thread-safe; must be called from rendering thread with OpenGL context.

---

## GPU Resources

- **Fragment shader**: The main effect shader.
- **Uniform arrays**: `particle_positions[100]` (vec2), `particle_energies[100]` (float), plus several floats.
- **No textures** required (unless using a background `tex0`).
- **No VBO/VAO** needed (full-screen quad handled by base Effect).
