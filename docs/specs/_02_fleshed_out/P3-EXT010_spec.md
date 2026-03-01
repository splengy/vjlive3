# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT010_audio_reactive_effects.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT010 — AudioReactiveEffects (AudioSpectrumTrails)

## Description

The `AudioSpectrumTrails` module (legacy: `AudioParticleSystem`) implements real-time visual effects driven by audio spectrum analysis, specifically rendering dynamic trails based on frequency bands. It translates audio input into visual elements such as colored particle trails that respond to bass, mid, and treble levels, providing a responsive and immersive visual experience during live performance or playback. The module uses a particle system architecture where each particle's position, velocity, and energy are modulated by audio features, creating organic, flowing visual patterns that react to the audio signal in real-time. Particles are assigned to frequency bands and their movement is influenced by the corresponding audio energy, creating a visualization where different frequency ranges drive different particle groups.

## What This Module Does

- Generates audio-reactive visual trails using particle systems with up to 100 simultaneous particles
- Maps audio frequency bands (bass, mid, treble, volume) to visual parameters (particle size, color, position, energy)
- Implements particle physics with velocity updates based on audio features, time, and particle index
- Provides configurable particle properties (size, speed, trail_length, color_sensitivity, frequency_bands)
- Handles audio analyzer integration for real-time spectrum data via set_audio_analyzer()
- Supports GPU-based rendering with OpenGL shaders and fallback to CPU-only operation
- Includes parameter validation and bounds checking for all configurable properties
- Maintains internal state for particle positions, velocities, and energies with dynamic resizing
- Updates particle behavior every frame in apply_uniforms() based on current audio input
- Renders particles as point sprites with distance-based trails and energy-modulated alpha

## What This Module Does NOT Do

- Handle audio input directly (relies on external audio analyzer providing frequency bands)
- Implement complex particle physics beyond basic velocity updates (no collision, gravity, or forces)
- Provide persistent particle configurations or presets
- Handle video file I/O or persistence of particle states
- Implement advanced audio analysis beyond basic frequency band extraction
- Support multi-threading for performance optimization
- Provide automatic scene detection or content-aware effect application
- Manage particle lifecycle beyond energy decay (no birth/death system)
- Support more than 100 particles without reallocation (hard limit in shader uniforms)

## Integration

This module integrates with the VJLive3 node graph as a visual effect generator that connects to:

- **Audio Analyzer**: Receives real-time audio spectrum data (bass, mid, treble, volume) for reactivity via set_audio_analyzer()
- **Shader System**: Outputs particle rendering data to fragment shaders for final visual composition using point sprites
- **Parameter System**: Exposes configurable properties (num_particles, particle_size, particle_speed, trail_length, color_sensitivity, frequency_bands) via set_parameter/get_parameter
- **Node Graph**: Functions as a standalone visual effect that can be composited with other effects using standard blending

The module expects to be called within the main render loop and receives audio signals through an integrated AudioAnalyzer instance. It manages internal particle state and outputs visual data that can be rendered using standard OpenGL shaders with point sprite support. The particle positions are updated in apply_uniforms() which should be called each frame before rendering.

## Performance

- **Particle Count**: Supports up to 100 simultaneous particles (configurable 10-200, default 100)
- **CPU Usage**: Particle physics and position updates run on CPU with O(n) complexity; velocity updates use numpy vector operations
- **GPU Usage**: Rendering uses point sprites with texture mapping for efficient GPU instancing; uniform upload for 100 particles × 2D positions + energies
- **Memory Usage**: ~100KB for particle state arrays (positions: 100×2×4 bytes, velocities: 100×2×4 bytes, energies: 100×4 bytes) + shader uniforms
- **Frame Rate**: Target 60fps with 100 particles on mid-range hardware; linear scaling with particle count
- **Audio Processing**: Lightweight feature extraction; audio analyzer queried once per frame in apply_uniforms()
- **Scalability**: Performance scales linearly with particle count; recommended limit 200 particles for 60fps on modern hardware
- **Fallback**: Can operate without audio analyzer (defaults to zero values for all audio features); shader compilation failure handled by base Effect class

---

## Public Interface

```python
class AudioSpectrumTrails(Effect):
    def __init__(self) -> None:
        super().__init__("audio_spectrum_trails", self._get_fragment_shader())
        
        # Initialize effect parameters
        self.num_particles = 100
        self.particle_size = 0.01
        self.particle_speed = 0.5
        self.trail_length = 0.8
        self.color_sensitivity = 1.0
        self.frequency_bands = 8

        # Audio reactivity state
        self.audio_analyzer = None
        self.particle_positions = np.random.uniform(0, 1, (self.num_particles, 2)).astype(np.float32)
        self.particle_velocities = np.random.uniform(-0.01, 0.01, (self.num_particles, 2)).astype(np.float32)
        self.particle_energies = np.ones(self.num_particles, dtype=np.float32)

    def _get_fragment_shader(self) -> str:
        """Returns the GLSL fragment shader code for rendering audio-reactive trails."""
        return """
#version 330 core

uniform vec2 resolution;
uniform float time;
uniform float u_mix;
uniform sampler2D tex0;

// Particle uniforms
uniform int num_particles;
uniform float particle_size;
uniform float trail_length;
uniform float color_sensitivity;
uniform vec2 particle_positions[100];
uniform float particle_energies[100];

// Audio uniforms
uniform float bass_level;
uniform float mid_level;
uniform float treble_level;
uniform float volume_level;

out vec4 fragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec4 original = texture(tex0, uv);
    vec3 color = original.rgb;

    // Render particles with trails
    for (int i = 0; i < num_particles; i++) {
        vec2 particle_pos = particle_positions[i];
        float energy = particle_energies[i];

        // Distance from current pixel to particle
        vec2 diff = uv - particle_pos;
        float dist = length(diff);

        // Particle size based on energy and audio
        float size = particle_size * (1.0 + energy * volume_level * 2.0);

        if (dist < size) {
            // Particle color based on frequency bands
            vec3 particle_color = vec3(
                bass_level * color_sensitivity,
                mid_level * color_sensitivity,
                treble_level * color_sensitivity
            );

            // Apply fade over trail length
            float fade = 1.0 - smoothstep(0.0, trail_length, dist);
            fragColor = vec4(particle_color * fade, 1.0);
            return;
        }
    }

    // Default fallback if no particles are active
    fragColor = original;
}
"""
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `audio_analyzer` | `AudioAnalyzer` | Provides real-time audio spectrum data (bass, mid, treble, volume) | Must be set before first update; if missing, effect defaults to zero values |
| `particle_positions` | `np.ndarray[shape=(N,2), dtype=np.float32]` | Initial positions of particles in normalized screen space | N = 100; must be within [0,1] range for both x and y |
| `particle_energies` | `np.ndarray[shape=(N,), dtype=np.float32]` | Energy levels of each particle (used to scale size and visibility) | Values ≥ 0.0; initialized to 1.0 |
| `bass_level`, `mid_level`, `treble_level`, `volume_level` | `float` | Audio spectrum values from analyzer, scaled between [0,1] | Must be in range [0,1]; updated every frame |
| `resolution` | `vec2` | Screen resolution for normalization | Always passed via uniform; used to normalize UV coordinates |
| `time` | `float` | Time elapsed since start (in seconds) | Used as a time-based modulation parameter (not currently used in logic) |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for particle state storage and manipulation — fallback: use list-based arrays with performance penalty
  - `OpenGL.GL` — required to bind textures and render shaders — fallback: no rendering, effect is disabled silently
- Internal modules this depends on:
  - `vjlive1.core.effects.shader_base.Effect` — base class for all visual effects
  - `vjlive1.core.audio_analyzer.AudioAnalyzer` — provides audio spectrum data (bass, mid, treble, volume)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if audio analyzer is not available; defaults to zero values for audio bands |
| `test_basic_operation` | Core rendering function produces visible trails when audio input is provided and valid spectrum data is present |
| `test_error_handling` | Invalid or out-of-range audio values (e.g., >1.0) are clamped safely without crashing the effect |
| `test_cleanup` | No memory leaks; particle state is properly released during shutdown (if stop() method exists) |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT010: audio_reactive_effects (AudioSpectrumTrails)` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

--- 

## LEGACY CODE REFERENCES  
See references in original `vjlive1/core/effects/audio_reactive_effects.py`:

- Lines 1–20: Base class structure and import setup for audio-reactive effects.
- Lines 17–36: Initialization of parameters including particle count, size, speed, trail length, color sensitivity, frequency bands, and initial positions/velocities.
- Lines 33–52: Fragment shader definition with uniforms for particles and audio data.
- Lines 49–68: Uniform declarations for `bass_level`, `mid_level`, `treble_level`, `volume_level`.
- Lines 65–84: Particle rendering loop using distance-based visibility, size scaling via energy and volume, and color derived from frequency bands.

