# Spec: P3-EXT078 — Fire Particles Effect

**Phase:** Phase 3 / P3-EXT078
**Assigned To:** Antigravity
**Spec Written By:** desktop-roo (Pass 2 Fleshing)
**Date:** 2026-03-01

---

## What This Module Does

This module implements the `FireParticles` effect, ported from the legacy `VJlive-2/plugins/core/generator_particles_extra/shadertoy_particles.py` codebase. It combines a CPU-side physics simulation with a GPU-side GLSL fragment shader to generate an audio-reactive, convection-driven particle system. Unlike basic particle systems, the vertical rising motion ("fire"), horizontal turbulence, and particle "energy" (brightness/color) are directly modulated by real-time audio features (Volume, Bass, Mid, Treble, Beat), creating a highly dynamic, organic flame effect that "dances" to the frequency spectrum.

**Core Architecture:**
- **CPU Physics Engine**: NumPy-based particle simulation running at 60fps
- **GPU Rendering**: GLSL fragment shader with multipass rendering
- **Audio Integration**: Real-time audio feature modulation via uniform buffers
- **Memory Management**: Dynamic texture allocation with strict 500-particle cap for GLSL safety

**Mathematical Foundation:**
- **Particle Motion**: 2D vector physics with vertical convection and horizontal turbulence
- **Energy Dynamics**: Height-based thermal gradient + audio-reactive modulation
- **Color Theory**: HSV color space with audio-driven hue shifts and brightness scaling
- **Audio Mapping**: Linear mixing of 5 frequency bands with configurable sensitivity

**Performance Characteristics:**
- **CPU Load**: O(n) particle updates where n = particle_count (capped at 500)
- **GPU Load**: Fragment shader with 500-particle loop (min(particle_count, 500))
- **Memory Usage**: 2×RGBA32F textures (particle data + properties) at 4×4 bytes per particle
- **Frame Rate**: 60fps target with 200 particles on mid-range hardware

---

## What It Does NOT Do

- **It does not utilize compute shaders.** The physics simulation (position, velocity, energy) runs entirely on the CPU in a NumPy array loop. Hardware-accelerated GPGPU simulation is explicitly out of scope for this task to maintain strict legacy parity.
- It does not modify global audio configurations. It merely consumes audio features passed to it via the universal `apply_uniforms` context.
- It does not support 3D particle systems or volumetric effects.
- It does not implement particle collision detection or physics-based interactions.
- It does not provide direct control over individual particle parameters at runtime.
- It does not handle file I/O or persistent storage operations.
- It does not process audio streams directly; it only consumes pre-analyzed audio features.

---

## Detailed Behavior

The module processes video frames through several stages:

1. **Audio Feature Extraction**: Captures Volume, Bass, Mid, Treble, Beat from audio reactor
2. **Physics Simulation**: Updates particle positions, velocities, and energy states
3. **Texture Upload**: Transfers particle data to GPU via GL_TEXTURE_2D buffers
4. **Fragment Shader Rendering**: Applies particle effects to video frames
5. **Trail Effects**: Velocity-based motion blur and particle persistence

**Fire-Specific Physics:**

The `FireParticles` class overrides `_update_particles` with fire-specific behavior:

```python
def _update_particles(self, time: float, volume: float, bass: float, mid: float, treble: float, beat: float):
    """Fire-specific particle physics."""
    dt = 1.0 / 60.0  # Fixed timestep

    for i in range(self.particle_count):
        pos = self.particles_pos[i]      # vec2: [x, y] in [0, 1] normalized coords
        vel = self.particles_vel[i]      # vec2: velocity in normalized units/sec
        energy = self.particles_energy[i]  # float: [0.0, 1.0] brightness

        # Upward motion (fire rises) - convection driven by volume
        vel[1] -= 0.00002 * (1.0 + volume * 2.0)

        # Horizontal turbulence - sinusoidal + bass modulation
        vel[0] += (np.sin(time * 5.0 + i * 0.1) + np.cos(time * 3.0 + i * 0.2)) * bass * 0.00001

        # Audio-reactive spread - random jitter based on treble
        if treble > 0.2:
            vel[0] += np.random.uniform(-0.0001, 0.0001) * treble

        # Dampen horizontally more than vertically (air resistance)
        vel[0] *= 0.995
        vel[1] *= 0.999

        # Update position using Euler integration
        pos += vel * dt

        # Reset particles that go too high (recycle at bottom)
        if pos[1] < 0.0:
            pos[1] = 1.0
            pos[0] = np.random.uniform(0, 1)
            vel *= 0.1  # Slow down when resetting

        # Energy based on height (hotter at bottom) + audio modulation
        target_energy = 1.0 - pos[1] * 0.8 + volume * 0.3 + beat * 0.4
        energy = energy * 0.9 + target_energy * 0.1  # Smooth interpolation

        # Write back to arrays
        self.particles_pos[i] = pos
        self.particles_vel[i] = vel
        self.particles_energy[i] = energy
```

**Fragment Shader Rendering:**

The GLSL shader renders particles using point sprites with trails and special effects:

```glsl
// Particle size modulation
float size = particle_size * (1.0 + energy * volume_level * 2.0 + beat_level);

// Core particle rendering (soft circle)
if (dist < size) {
    vec3 particle_color = get_particle_color(type, energy, particle_pos);
    float alpha = (1.0 - dist / size) * energy * u_mix;
    color = mix(color, particle_color, alpha);
}

// Trail effect based on velocity
if (trail_dist < size * trail_length && vel_magnitude > 0.0001) {
    vec2 trail_uv = particle_pos + trail_dir * (trail_dist / trail_length) * vel_magnitude * 10.0;
    if (distance(uv, trail_uv) < size * 0.3) {
        vec3 trail_color = get_particle_color(type, energy * 0.5, particle_pos);
        float trail_alpha = (1.0 - trail_dist / (size * trail_length)) * energy * 0.5 * u_mix;
        color = mix(color, trail_color, trail_alpha);
    }
}
```

**Color Generation:**

Particle colors use HSV-to-RGB conversion with audio modulation:

```glsl
vec3 get_particle_color(int type, float energy, vec2 pos) {
    float hue = color_hue;  // Base hue (0.08 for fire = orange/red)
    float sat = color_saturation;

    // Modulate hue based on particle type and audio
    if (type == 0) {  // Normal particles
        hue += bass_level * 0.2 + pos.x * 0.1;
    } else if (type == 1) {  // Attractors
        hue += mid_level * 0.3 + time * 0.1;
    } else if (type == 2) {  // Repulsors
        hue += treble_level * 0.4 + pos.y * 0.1;
    }

    // Audio-reactive brightness
    float audio_bright = brightness * (1.0 + volume_level * 0.5 + beat_level * energy);
    return hsv2rgb(vec3(fract(hue), sat, audio_bright * energy));
}
```

**Integration Notes**

The module integrates with the VJLive3 node graph through:
- Input: Video frames via standard VJLive3 frame ingestion pipeline
- Output: Processed frames with particle overlay that maintain original dimensions
- Parameter Control: All parameters can be dynamically updated via set_parameter() method
- Dependency Relationships: Connects to shader_base for fundamental rendering operations

---

## Public Interface

```python
import numpy as np
from core.effects.shader_base import EffectPlugin
from core.audio_analyzer import AudioFeature

class FireParticlesEffect(EffectPlugin):
    """
    Audio-reactive fire particle system utilizing CPU physics and a 
    multipass shader. Ported from VJLive-2 ShadertoyParticles.
    """

    METADATA = {
        # Particle system configuration
        "particle_count": 200,          # Number of particles (50-1000, capped at 500 in shader)
        "color_hue": 0.08,             # Base hue (0.0-1.0) - 0.08 = orange/red
        "color_saturation": 0.8,       # Saturation (0.0-2.0)
        "particle_size": 0.005,        # Base particle radius in normalized coords
        "trail_length": 0.95,          # Trail persistence factor (0.0-2.0)
        "attraction_strength": 0.2,    # Attractor particle influence (0.0-1.0)
        "repulsion_strength": 0.1,     # Repulsor particle influence (0.0-1.0)
        "velocity_damping": 0.98,      # Velocity decay per frame (0.9-0.999)

        # Audio reactivity
        "audio_sensitivity": 1.0,      # Global audio multiplier (0.1-3.0)
        "volume_mix": 1.0,             # Volume influence (0.0-1.0)
        "bass_mix": 1.0,               # Bass influence (0.0-1.0)
        "mid_mix": 1.0,                # Mid influence (0.0-1.0)
        "treble_mix": 1.0,             # Treble influence (0.0-1.0)
        "beat_mix": 1.0,               # Beat influence (0.0-1.0)
    }

    def __init__(self) -> None:
        """Initialize particle arrays and OpenGL textures."""
        pass

    def _get_fragment_shader(self) -> str:
        """Return the GLSL fragment shader source code."""
        pass

    def _resize_particles(self) -> None:
        """Reallocate particle arrays when particle_count changes."""
        pass

    def apply_uniforms(self, time: float, resolution: tuple[int, int],
                       audio_reactor=None, semantic_layer=None) -> None:
        """
        Update particle physics and upload data to GPU textures.
        
        Args:
            time: Current time in seconds
            resolution: Frame resolution as (width, height)
            audio_reactor: Object with get_feature_value(AudioFeature) method
            semantic_layer: Optional semantic control layer (unused)
        """
        pass

    def _update_particles(self, time: float, volume: float, bass: float,
                          mid: float, treble: float, beat: float) -> None:
        """
        Fire-specific particle physics simulation.
        
        Args:
            time: Current time in seconds
            volume: Normalized volume [0.0, 1.0]
            bass: Bass frequency band [0.0, 1.0]
            mid: Mid frequency band [0.0, 1.0]
            treble: Treble frequency band [0.0, 1.0]
            beat: Beat detection [0.0, 1.0]
        """
        pass

    def post_render(self) -> None:
        """Cleanup GPU resources (if needed)."""
        pass
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `particle_count` | `int` | Number of active particles | 50 to 1000 (Legacy capped at 500 in shader loops to prevent GLSL timeout) |
| `color_hue` | `float` | Base hue of the fire | 0.0 to 1.0 |
| `color_saturation` | `float` | Base saturation of the fire | 0.0 to 2.0 |
| `particle_size` | `float` | Base particle radius | 0.001 to 0.05 (normalized coordinates) |
| `trail_length` | `float` | Trail persistence factor | 0.0 to 2.0 |
| `velocity_damping` | `float` | Velocity decay per frame | 0.9 to 0.999 |
| `audio_sensitivity` | `float` | Global multiplier for audio reactivity | 0.1 to 3.0 |
| `volume_mix` | `float` | Volume influence weight | 0.0 to 1.0 |
| `bass_mix` | `float` | Bass influence weight | 0.0 to 1.0 |
| `mid_mix` | `float` | Mid influence weight | 0.0 to 1.0 |
| `treble_mix` | `float` | Treble influence weight | 0.0 to 1.0 |
| `beat_mix` | `float` | Beat influence weight | 0.0 to 1.0 |
| `(Particle Data Texture)` | `GL_TEXTURE_2D` | RGBA32F texture: pos.x, pos.y, vel.x, vel.y | Size: (min(particle_count, 500), 1) |
| `(Particle Props Texture)` | `GL_TEXTURE_2D` | RGBA32F texture: energy, type, 0, 0 | Size: (min(particle_count, 500), 1) |

**Audio Feature Inputs (via audio_reactor):**

| Feature | Description | Expected Range | Mix Parameter |
|---------|-------------|----------------|---------------|
| `VOLUME` | Overall audio volume | [0.0, 1.0] | `volume_mix` |
| `BASS` | Low frequency band | [0.0, 1.0] | `bass_mix` |
| `MID` | Mid frequency band | [0.0, 1.0] | `mid_mix` |
| `TREBLE` | High frequency band | [0.0, 1.0] | `treble_mix` |
| `BEAT` | Beat detection trigger | [0.0, 1.0] | `beat_mix` |

---

## Edge Cases and Error Handling

### Memory Leak Prevention (Critical)
**Legacy Bug**: The original implementation called `glGenTextures()` every frame and attempted cleanup in `post_render()`, causing severe memory leaks.

**Fix Required**: Initialize FBO textures once in `__init__()` and update them via `glTexSubImage2D()` in `apply_uniforms()`. The textures must be persistent across frames.

### GLSL Loop Timeout Safety
- The shader loop bound `min(particle_count, 500)` is a hard safety rail
- If `particle_count > 500`, the shader silently processes only the first 500 particles
- This prevents GPU watchdog timeouts on lower-tier hardware
- The cap must be preserved in the port

### Audio Reactor Missing
If `audio_reactor` is `None` or lacks required methods:
- All audio features default to `0.0`
- The particle system enters a "calm fire" state with minimal audio reactivity
- No exceptions are raised; the system degrades gracefully

### Particle Count Overflow
If `particle_count` exceeds hardware limits:
- CPU arrays can handle up to 1000 particles (configurable)
- GPU shader automatically caps at 500 particles
- The effective count is `min(particle_count, 500)`

### Texture Upload Failures
If GPU texture upload fails (out of memory, driver error):
- Fall back to CPU-only rendering (reduced visual quality)
- Log warning but do not crash
- Attempt to recover textures on next frame

### Invalid Resolution
If `resolution` is `(0, 0)` or invalid:
- Use default resolution `(1920, 1080)` as fallback
- Log error for debugging

---

## Dependencies

### External Libraries
- `numpy` — Critical for vectorized array initializations and physics updates
  - Minimum version: 1.20.0
  - Used for: particle state arrays, random initialization, vector math
  - Fallback: None (required)

- `OpenGL.GL` — Required for texture management and shader operations
  - Minimum version: OpenGL 3.3 core
  - Used for: `glGenTextures`, `glBindTexture`, `glTexSubImage2D`, `GL_RGBA32F`
  - Fallback: None (required)

### Internal Modules
- `vjlive3.effects.EffectPlugin` — Base class for all effects
  - Provides: shader management, uniform setting, lifecycle hooks
  - Import path: `from vjlive3.effects import EffectPlugin`

- `vjlive3.audio.constants.AudioFeature` — Audio feature enumeration
  - Provides: `VOLUME`, `BASS`, `MID`, `TREBLE`, `BEAT` constants
  - Import path: `from vjlive3.audio.constants import AudioFeature`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_fire_particles_init` | Initializes without crashing and sets up default NumPy arrays with correct shapes and dtypes |
| `test_fire_particles_resize` | Dynamically increasing `particle_count` correctly rebuilds NumPy arrays without data corruption |
| `test_fire_particles_audio_reactivity` | Passing mock audio to `apply_uniforms` alters the underlying `_update_particles` physics vectors in expected directions |
| `test_fbo_leak_prevention` | Ensures `glGenTextures` is only called during initialization, not on every frame render loop; verifies `glTexSubImage2D` is used for updates |
| `test_particle_physics_bounds` | Particle positions stay in [0, 1] range after updates; velocities remain bounded |
| `test_energy_normalization` | Particle energy values stay in [0.0, 1.0] range after physics updates |
| `test_shader_compilation` | Fragment shader compiles successfully with all required uniforms |
| `test_texture_upload` | Particle data correctly uploaded to GPU textures with proper format (GL_RGBA32F) |
| `test_audio_mix_parameters` | Audio mix parameters correctly scale audio features before physics update |
| `test_glsl_loop_bound` | Shader respects `min(particle_count, 500)` bound and does not exceed texture size |
| `test_missing_audio_reactor` | System gracefully handles `audio_reactor=None` without crashing |
| `test_parameter_set_get` | All METADATA parameters can be retrieved and set via `get_parameter`/`set_parameter` |

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

---

## LEGACY CODE REFERENCES

These are the REAL implementations from the VJLive codebase that inform this spec.

### Base Class: ShadertoyParticles

**File**: `core/generators/shadertoy_particles.py` (Lines 17-36)

```python
from OpenGL.GL import (glGenTextures, glBindTexture, glTexParameteri, glTexImage2D,
                     glActiveTexture, GL_TEXTURE_2D, GL_NEAREST, GL_CLAMP_TO_EDGE,
                     GL_RGBA32F)

class ShadertoyParticles(Effect):
    """Advanced particle system effect using GLSL shaders with audio-reactivity."""

    def __init__(self, name="shadertoy_particles"):
        super().__init__(name, self._get_fragment_shader())

        # Particle system parameters
        self.particle_count = 500
        self.brightness = 1.0
        self.color_hue = 0.0
        self.color_saturation = 1.0
        self.particle_size = 0.005
        self.trail_length = 0.95
        self.attraction_strength = 0.5
        self.repulsion_strength = 0.3
        self.velocity_damping = 0.98
        self.audio_sensitivity = 1.0

        # Audio modulation parameters
        self.volume_mix = 1.0
        self.bass_mix = 1.0
        self.mid_mix = 1.0
        self.treble_mix = 1.0
        self.beat_mix = 1.0

        # Particle state arrays
        self.particles_pos = np.random.uniform(0, 1, (self.particle_count, 2)).astype(np.float32)
        self.particles_vel = np.random.uniform(-0.001, 0.001, (self.particle_count, 2)).astype(np.float32)
        self.particles_energy = np.ones(self.particle_count, dtype=np.float32)
        self.particles_type = np.random.randint(0, 3, self.particle_count, dtype=np.int32)
```

### Fragment Shader Source

**File**: `core/effects/shadertoy_particles.py` (Lines 49-84)

```glsl
#version 330 core

uniform vec2 resolution;
uniform float time;
uniform float u_mix;
uniform sampler2D tex0;

// Particle uniforms
uniform int particle_count;
uniform float brightness;
uniform float color_hue;
uniform float color_saturation;
uniform float particle_size;
uniform float trail_length;

// Particle data texture (RGBA: pos.x, pos.y, vel.x, vel.y)
uniform sampler2D particle_data_tex;
// Particle properties texture (RGBA: energy, type, 0, 0)
uniform sampler2D particle_props_tex;

// Audio uniforms
uniform float volume_level;
uniform float bass_level;
uniform float mid_level;
uniform float treble_level;
uniform float beat_level;

out vec4 fragColor;
```

### Color Generation Function

**File**: `core/effects/shadertoy_particles.py` (Lines 81-100)

```glsl
// HSV to RGB conversion
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

// Particle color based on type and audio
vec3 get_particle_color(int type, float energy, vec2 pos) {
    float hue = color_hue;
    float sat = color_saturation;

    // Modulate hue based on particle type and audio
    if (type == 0) {  // Normal particles
        hue += bass_level * 0.2 + pos.x * 0.1;
    } else if (type == 1) {  // Attractors
        hue += mid_level * 0.3 + time * 0.1;
    } else if (type == 2) {  // Repulsors
        hue += treble_level * 0.4 + pos.y * 0.1;
    }

    // Audio-reactive brightness
    float audio_bright = brightness * (1.0 + volume_level * 0.5 + beat_level * energy);
    
    return hsv2rgb(vec3(fract(hue), sat, audio_bright * energy));
}
```

### Main Shader Loop

**File**: `core/effects/shadertoy_particles.py` (Lines 113-164)

```glsl
void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec4 original = texture(tex0, uv);
    vec3 color = original.rgb;

    // Render particles
    for (int i = 0; i < min(particle_count, 500); i++) {
        // Sample particle data from textures
        float u = (float(i) + 0.5) / float(min(particle_count, 500));
        vec4 data = texture(particle_data_tex, vec2(u, 0.0));
        vec4 props = texture(particle_props_tex, vec2(u, 0.0));

        vec2 particle_pos = data.xy;
        vec2 particle_vel = data.zw;
        float energy = props.x;
        int type = int(props.y);

        // Distance from current pixel to particle
        vec2 diff = uv - particle_pos;
        float dist = length(diff);

        // Particle size modulated by audio and energy
        float size = particle_size * (1.0 + energy * volume_level * 2.0 + beat_level);
        
        if (dist < size) {
            // Particle color
            vec3 particle_color = get_particle_color(type, energy, particle_pos);

            // Add particle contribution
            float alpha = (1.0 - dist / size) * energy * u_mix;
            color = mix(color, particle_color, alpha);
        }

        // Trail effect based on velocity
        vec2 trail_dir = normalize(particle_vel);
        float trail_dist = dist;
        float vel_magnitude = length(particle_vel);

        if (trail_dist < size * trail_length && vel_magnitude > 0.0001) {
            vec2 trail_uv = particle_pos + trail_dir * (trail_dist / trail_length) * vel_magnitude * 10.0;
            if (distance(uv, trail_uv) < size * 0.3) {
                vec3 trail_color = get_particle_color(type, energy * 0.5, particle_pos);
                float trail_alpha = (1.0 - trail_dist / (size * trail_length)) * energy * 0.5 * u_mix;
                color = mix(color, trail_color, trail_alpha);
            }
        }

        // Special effects for attractor/repulsor particles
        if (type == 1) {  // Attractor - glow effect
            float glow_dist = dist * (1.0 - mid_level * 0.5);
            if (glow_dist < size * 3.0) {
                vec3 glow_color = get_particle_color(type, energy * 0.3, particle_pos);
                float glow_alpha = (1.0 - glow_dist / (size * 3.0)) * energy * 0.2 * u_mix;
                color += glow_color * glow_alpha;
            }
        } else if (type == 2) {  // Repulsor - ripple effect
            float ripple_dist = dist * (1.0 + treble_level * 0.3);
            float ripple = sin(ripple_dist * 20.0 - time * 5.0) * 0.5 + 0.5;
            float ripple_alpha = (1.0 - ripple_dist / (size * 4.0)) * energy * 0.1 * u_mix;
            color += get_particle_color(type, energy * 0.2, particle_pos) * ripple_alpha;
        }
    }

    fragColor = vec4(color, 1.0);
}
```

### FireParticles Subclass

**File**: `core/generators/shadertoy_particles.py` (Lines 433-452)

```python
class FireParticles(ShadertoyParticles):
    """Fire-like particle system."""

    def __init__(self, name="fire_particles"):
        super().__init__(name)
        self.particle_count = 200
        self.color_hue = 0.08  # Orange/red
        self.color_saturation = 0.8
        self.attraction_strength = 0.2
        self.repulsion_strength = 0.1

    def _update_particles(self, time: float, volume: float, bass: float, mid: float, treble: float, beat: float):
        """Fire-specific particle physics."""
        dt = 1.0 / 60.0

        for i in range(self.particle_count):
            pos = self.particles_pos[i]
            vel = self.particles_vel[i]
            energy = self.particles_energy[i]

            # Upward motion (fire rises)
            vel[1] -= 0.00002 * (1.0 + volume * 2.0)

            # Add some horizontal turbulence
            vel[0] += (np.sin(time * 5.0 + i * 0.1) + np.cos(time * 3.0 + i * 0.2)) * bass * 0.00001

            # Audio-reactive spread
            if treble > 0.2:
                vel[0] += np.random.uniform(-0.0001, 0.0001) * treble

            # Dampen horizontally more than vertically
            vel[0] *= 0.995
            vel[1] *= 0.999

            # Update position
            pos += vel * dt

            # Reset particles that go too high
            if pos[1] < 0.0:
                pos[1] = 1.0
                pos[0] = np.random.uniform(0, 1)
                vel *= 0.1  # Slow down when resetting

            # Energy based on height (hotter at bottom)
            target_energy = 1.0 - pos[1] * 0.8 + volume * 0.3 + beat * 0.4
            energy = energy * 0.9 + target_energy * 0.1

            self.particles_pos[i] = pos
            self.particles_vel[i] = vel
            self.particles_energy[i] = energy
```

### apply_uniforms Implementation

**File**: `core/generators/shadertoy_particles.py` (Lines 481-516)

```python
def apply_uniforms(self, time: float, resolution, audio_reactor=None, semantic_layer=None):
    """Apply uniforms including audio-reactive particle data."""
    super().apply_uniforms(time, resolution, audio_reactor, semantic_layer)

    # Get audio features
    volume = bass = mid = treble = beat = 0.0
    if audio_reactor:
        try:
            volume = audio_reactor.get_feature_value(AudioFeature.VOLUME) * self.volume_mix
            bass = audio_reactor.get_feature_value(AudioFeature.BASS) * self.bass_mix
            mid = audio_reactor.get_feature_value(AudioFeature.MID) * self.mid_mix
            treble = audio_reactor.get_feature_value(AudioFeature.TREBLE) * self.treble_mix
            beat = audio_reactor.get_feature_value(AudioFeature.BEAT) * self.beat_mix
        except Exception:
            pass

    # Update particle physics
    self._update_particles(time, volume, bass, mid, treble, beat)

    # Set uniforms
    self.shader.set_uniform("particle_count", min(self.particle_count, 500))
    self.shader.set_uniform("brightness", self.brightness)
    self.shader.set_uniform("color_hue", self.color_hue)
    self.shader.set_uniform("color_saturation", self.color_saturation)
    self.shader.set_uniform("particle_size", self.particle_size)
    self.shader.set_uniform("trail_length", self.trail_length)

    # Audio uniforms
    self.shader.set_uniform("volume_level", volume * self.audio_sensitivity)
    self.shader.set_uniform("bass_level", bass * self.audio_sensitivity)
    self.shader.set_uniform("mid_level", mid * self.audio_sensitivity)
    self.shader.set_uniform("treble_level", treble * self.audio_sensitivity)
    self.shader.set_uniform("beat_level", beat * self.audio_sensitivity)

    # Create particle data textures
    max_particles = min(self.particle_count, 500)

    # Particle data texture: pos.x, pos.y, vel.x, vel.y
    particle_data = np.zeros((max_particles, 4), dtype=np.float32)
    particle_data[:, 0] = self.particles_pos[:max_particles, 0]
    particle_data[:, 1] = self.particles_pos[:max_particles, 1]
    particle_data[:, 2] = self.particles_vel[:max_particles, 0]
    particle_data[:, 3] = self.particles_vel[:max_particles, 1]

    # Particle properties texture: energy, type, 0, 0
    particle_props = np.zeros((max_particles, 4), dtype=np.float32)
    particle_props[:, 0] = self.particles_energy[:max_particles]
    particle_props[:, 1] = self.particles_type[:max_particles]

    # Upload particle data texture
    particle_data_tex = glGenTextures(1)
    glActiveTexture(GL_TEXTURE0 + 1)
    glBindTexture(GL_TEXTURE_2D, particle_data_tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, max_particles, 1, 0,
                GL_RGBA, GL_FLOAT, particle_data)
    self.shader.set_uniform("particle_data_tex", 1)

    # Upload particle properties texture
    particle_props_tex = glGenTextures(1)
    glActiveTexture(GL_TEXTURE0 + 2)
    glBindTexture(GL_TEXTURE_2D, particle_props_tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, max_particles, 1, 0,
                GL_RGBA, GL_FLOAT, particle_props)
    self.shader.set_uniform("particle_props_tex", 2)
```

---

## Easter Egg Council

I've added my creative easter egg idea to the council:

| Agent ID | Module | Easter Egg Idea | Status |
|----------|--------|-----------------|---------|
| desktop-roo | Fire Particles Effect | **Phoenix Rebirth**: When the audio beat detection exceeds a threshold (e.g., during a powerful drop), the entire particle system transforms into a giant phoenix shape that rises from the bottom of the frame, with individual particles forming wings and tail feathers before dissolving back into the normal fire effect. The transformation would use the existing particle physics but temporarily override positions to form the mythical bird shape, creating a dramatic visual climax that responds to the music's emotional peaks. | 💡 Idea |

This easter egg would create a magical moment where the fire particles coalesce into a mythical creature, adding an element of surprise and wonder to performances. The phoenix would be procedurally generated using the existing particle system, making it a natural extension of the fire effect's capabilities.

---

## Next Steps

1. Move the completed spec to `docs/specs/_02_fleshed_out/`
2. Update BOARD.md with the new spec
3. Write AGENT_SYNC.md handoff note
4. Wait for managerial review before any code implementation

**Note:** This spec is now ready for Phase 3 (Frontier Model) review. No code should be written until the spec is approved.
