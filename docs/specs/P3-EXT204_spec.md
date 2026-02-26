# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT204_advanced_particles_3d.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT204 — advanced_particles_3d

## Description

The AdvancedParticle3DSystem implements a sophisticated 3D particle system inspired by TouchDesigner's powerful particle generation capabilities. This module creates thousands of particles that move through 3D space with realistic physics, including gravity, drag, turbulence, and complex force fields. The particles respond dynamically to audio input, creating visual effects that pulse and dance with the music. The system uses GPU instancing through OpenGL shaders for high-performance rendering, allowing it to handle 10,000+ particles while maintaining smooth frame rates. Each particle has its own lifecycle, starting small and growing or shrinking over time, while interpolating between colors to create beautiful visual transitions. The force field system includes attractors, vortex forces, and turbulence, allowing for complex organic motion patterns that can create everything from gentle floating particles to explosive chaotic effects.

## What This Module Does

The AdvancedParticle3DSystem is a complete 3D particle engine that:

- **Manages up to 10,000 particles** in a configurable pool, with each particle having position, velocity, acceleration, lifetime, size, and color.
- **Simulates physics on the CPU** using a semi-implicit Euler integrator, applying forces like gravity, drag, turbulence, attractors, and vortex fields.
- **Renders particles using GPU instancing** via point sprites (gl_PointSize) or geometry shaders (if available). The legacy used point sprites but had validation issues; we'll use a modern approach with instanced quads.
- **Provides audio reactivity** by modulating emitter rate, particle velocity, and force field strengths based on audio amplitude and spectrum.
- **Supports dynamic color interpolation** from `color_start` to `color_end` over each particle's lifetime.
- **Offers a flexible emitter** with position, radius, velocity, and spread controls, allowing emission from a point or sphere.
- **Implements force fields**: attractor (pulls particles toward a point), vortex (spins particles around an axis), and turbulence (procedural noise-based force).
- **Integrates with VJLive3's effect system** as an `Effect` subclass with manual rendering control.
- **Provides parameter control** via `set_parameter`/`get_parameter` for real-time tweaking.

## What This Module Does NOT Do

- Does NOT perform GPU-based physics simulation (CPU simulation only, but could be upgraded later)
- Does NOT support particle collisions or particle-to-particle interactions
- Does NOT handle texture mapping on particles (point sprites only, no custom geometry)
- Does NOT include a built-in camera system (camera parameters are for reference only; actual projection handled by base Effect)
- Does NOT provide a UI for parameter control (parameters set via set_parameter)
- Does NOT manage the OpenGL context lifecycle (caller must ensure context exists)

---

## Detailed Behavior and Parameter Interactions

### Particle Data Structure

Each particle is represented by a set of attributes stored in NumPy arrays (or plain Python lists if NumPy unavailable):

- `position`: vec3 (x, y, z) in world space
- `velocity`: vec3 (x, y, z)
- `acceleration`: vec3 (x, y, z) — accumulated forces each frame
- `lifetime`: float (seconds remaining until particle dies)
- `max_lifetime`: float (initial lifetime when spawned)
- `size`: float (current point size)
- `color`: vec4 (r, g, b, a) — interpolated based on lifetime fraction

Particles are stored in a fixed-size pool of `max_particles`. Active particles are tracked via a `particle_count` counter. When a particle dies (lifetime <= 0), it is marked inactive and can be respawned.

### Emitter

The emitter runs each frame during `update(dt)`:

- Spawns up to `emit_rate * dt` new particles per frame (rounded to integer).
- For each new particle:
  - Find an inactive slot in the pool (or reuse a dead particle).
  - Set position: `emit_position` + random point within sphere of radius `emit_radius`.
  - Set velocity: `emit_velocity` + random spread (uniform in [-emit_spread, emit_spread] for each component).
  - Set lifetime: random between `particle_life_min` and `particle_life_max`.
  - Set size: `particle_size_start`.
  - Set color: `color_start`.
- If the pool is full (all particles active), no new particles are spawned until some die.

### Physics Update

Each frame, for each active particle:

1. **Reset acceleration**: `acceleration = (0, 0, 0)`
2. **Apply gravity**: `acceleration += gravity`
3. **Apply drag**: `velocity *= drag` (exponential decay)
4. **Apply turbulence** (if `turbulence_strength > 0`):
   - Sample 3D Perlin noise or Simplex noise at position scaled by `turbulence_scale`
   - Convert noise gradient to a force vector
   - `acceleration += noise_vector * turbulence_strength`
5. **Apply attractor** (if `attractor_strength > 0`):
   - Direction = `attractor_pos - position`
   - Distance = length(direction)
   - Force = normalize(direction) * `attractor_strength` / (distance^2 + epsilon)
   - `acceleration += force`
6. **Apply vortex** (if `vortex_strength > 0`):
   - Compute vector from vortex axis to particle position
   - Tangential direction = cross(axis, radial_vector)
   - Force = tangential_direction * `vortex_strength`
   - `acceleration += force`
7. **Integrate velocity** (semi-implicit Euler):
   - `velocity += acceleration * dt`
8. **Integrate position**:
   - `position += velocity * dt`
9. **Update lifetime**:
   - `lifetime -= dt`
10. **Update size** (linear interpolation over lifetime):
    - `t = 1.0 - (lifetime / max_lifetime)` (0 at birth, 1 at death)
    - `size = lerp(particle_size_start, particle_size_end, t)`
11. **Update color** (linear interpolation):
    - `color = lerp(color_start, color_end, t)`
12. **Check death**: if `lifetime <= 0`, mark particle inactive.

### Audio Reactivity

The system can respond to audio in three ways:

- **Emit rate modulation**: `emit_rate` is multiplied by `(1.0 + audio_analyzer.get_amplitude() * audio_sensitivity * beat_multiplier)`. This causes more particles to spawn on loud beats.
- **Velocity boost**: After computing velocity, multiply by `(1.0 + spectrum_influence * audio_analyzer.get_spectrum_energy())`. This makes particles move faster when certain frequencies are loud.
- **Force field modulation**: Attractor strength, vortex strength, and turbulence strength can be scaled by audio features if desired (not in legacy but could be added).

### Rendering

The system uses **GPU instancing** to render thousands of particles efficiently:

- **Vertex buffer**: A VBO stores per-particle attributes (position, size, color) for all active particles. This buffer is updated each frame via `glBufferSubData` or `glMapBuffer`.
- **Vertex shader**: Uses `gl_VertexID` (or an instance ID) to fetch particle data from the VBO. It transforms the particle position with the model-view-projection matrix and sets `gl_PointSize` for point sprite rendering.
- **Fragment shader**: Renders a circular point sprite with smooth alpha falloff, using the particle's color.

**Important**: The legacy code used `gl_PointSize` in the vertex shader, which is not allowed in OpenGL core profiles (>= 3.2) unless using compatibility. This caused validation failures. The VJLive3 implementation should use **instanced quads** (two triangles per particle) instead of point sprites to be core-profile compatible. Alternatively, use a geometry shader to expand points into quads, but geometry shaders are also deprecated. The recommended approach: use `glDrawArraysInstanced` with a unit quad in the vertex shader, and apply the particle's transformation and size in the shader.

We'll define the rendering approach as: **instanced quads** (two triangles per particle) with a simple vertex shader that reads particle data from a VBO and outputs a quad vertex. This is core-profile compatible and widely supported.

### Camera

The system maintains a camera (position, target, up) for computing the view-projection matrix. The base `Effect` class likely provides a default camera or the caller sets a global camera. The particle system's `render()` method should compute the MVP matrix and pass it to the shader.

### Shader Uniforms

- `u_mvp`: mat4 (model-view-projection matrix)
- `u_time`: float
- `u_point_size`: float (base size multiplier)
- `u_blend_mode`: ivec2 (source and destination blend factors)

---

## Integration

### VJLive3 Pipeline Integration

`AdvancedParticle3DSystem` is an **Effect** that renders directly to the current framebuffer. It is typically added to an effect chain and rendered as a source or overlay.

**Typical usage**:

```python
# Initialize
particles = AdvancedParticle3DSystem()
particles.set_parameter("max_particles", 10000)
particles.set_parameter("emit_rate", 100)
particles.set_parameter("gravity", (0.0, -0.1, 0.0))
particles.set_parameter("color_start", (1.0, 0.8, 0.2, 1.0))
particles.set_parameter("color_end", (1.0, 0.0, 0.0, 0.0))

# Connect audio (optional)
if audio_analyzer:
    particles.set_audio_analyzer(audio_analyzer)

# Each frame:
particles.update(delta_time)  # updates physics, spawns particles
particles.render()           # draws particles
```

The effect requires an OpenGL context. The base `Effect` class handles shader compilation and uniform locations.

### Audio Integration

The effect can optionally use an `AudioAnalyzer` to modulate parameters. The `set_audio_analyzer` method stores a reference, and `update(dt)` queries the analyzer for amplitude and spectrum.

---

## Performance

### Computational Cost

- **CPU**: For N particles (up to 10,000), each update:
  - Force calculations: ~50 FLOPs per particle (gravity, drag, turbulence, attractor, vortex)
  - Total: ~500,000 FLOPs at 10k particles. At 60 Hz, that's 30M FLOPs/frame, which is ~0.03 ms on a 1 TFLOP CPU. Negligible.
  - However, Python overhead may be significant; using NumPy vectorization is crucial for performance.
- **GPU**: Rendering 10,000 particles via instanced quads:
  - Vertex shader processes 4 vertices per particle = 40,000 vertices.
  - Fragment shader processes each pixel covered by the quads. With small point sizes, fill rate is low.
  - Should easily run at 60+ Hz on any modern GPU.

### Memory Usage

- **CPU**: Particle arrays: for 10,000 particles, each attribute (position, velocity, acceleration) is 3 floats = 120 KB per array. Total ~500 KB for all attributes. Acceptable.
- **GPU**: VBO for particle data: ~10,000 * (3+3+3+1+1+4) floats = ~150 KB. Shader program < 50 KB.
- **No textures** required.

### Optimization Strategies

- Use NumPy for vectorized particle updates (batch operations).
- Reduce `max_particles` on low-end hardware.
- Use a lower point size or disable particles beyond a certain distance (LOD).
- Consider using a compute shader for physics if CPU becomes bottleneck.

### Platform-Specific Considerations

- **Desktop**: Should run fine at 60 Hz with 10,000 particles.
- **Embedded**: May need to limit to 2,000-5,000 particles.
- **Mobile**: Use with caution; test performance.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without OpenGL context raises appropriate error |
| `test_basic_operation` | update() and render() run without errors with default parameters |
| `test_emission_rate` | Correct number of particles are spawned per frame based on emit_rate and dt |
| `test_particle_lifetime` | Particles die after their lifetime expires and are respawned |
| `test_physics_gravity` | Gravity accelerates particles downward correctly |
| `test_physics_drag` | Drag reduces velocity over time |
| `test_force_attractor` | Attractor pulls particles toward its position |
| `test_force_vortex` | Vortex causes circular motion around axis |
| `test_force_turbulence` | Turbulence adds random jitter to particle motion |
| `test_color_interpolation` | Particle color interpolates from start to end over lifetime |
| `test_size_interpolation` | Particle size interpolates from start to end over lifetime |
| `test_audio_reactivity_emit_rate` | Audio amplitude increases emit rate |
| `test_audio_reactivity_velocity` | Audio spectrum increases particle velocity |
| `test_parameter_set_get` | Setting and retrieving parameters works with type validation |
| `test_particle_limit` | System respects max_particles and does not overflow |
| `test_render_without_crash` | render() executes without OpenGL errors |
| `test_cleanup` | After stop(), shader and VBOs are deleted, no GL errors |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

### [NEEDS RESEARCH]: The legacy code uses `gl_PointSize` in the vertex shader, which is deprecated in OpenGL core profiles. This caused validation failures. How should we implement particle rendering in a core-profile compatible way?

**Finding**: The legacy used point sprites, which are convenient but not core-profile. Modern OpenGL recommends using instanced rendering with a unit quad geometry. We can create a VBO for a single quad (two triangles) and use `glDrawArraysInstanced` with an instance ID to position each particle. The vertex shader will compute the quad's corners based on the particle's position and size.

**Resolution**: Use instanced quads. The vertex shader will have two attributes: `a_quad_vertex` (the quad's corner positions in object space) and `a_instance_data` (particle position, size, color). We'll use `gl_VertexID` to determine which quad vertex and which instance. This is core-profile compatible and efficient.

### [NEEDS RESEARCH]: The legacy code uses `manual_render = True`. What does this mean in the base Effect class? Likely that the effect overrides `render()` and does its own drawing, rather than relying on the base class's full-screen quad.

**Resolution**: We'll follow the same pattern: override `render()` to bind our shader, set uniforms, and call `glDrawArraysInstanced`. The base `Effect` class may provide helper methods for shader management; we'll use them.

### [NEEDS RESEARCH]: The camera parameters (position, target, up) are stored but how are they used? The base Effect might provide a default view-projection matrix. Or the particle system computes its own MVP.

**Resolution**: The particle system should compute its own MVP matrix using a simple perspective projection. We can provide a method `set_camera(position, target, up)` or use the base class's camera if available. For simplicity, we'll compute MVP in `render()` using a fixed camera or allow the caller to set a view-projection matrix uniform directly.

### [NEEDS RESEARCH]: The `blend_mode` parameter is set to `(GL_SRC_ALPHA, GL_ONE)` for additive blending. Should we support arbitrary blend modes? The spec should define that the effect uses additive blending by default but can be changed via `set_parameter`.

**Resolution**: Support setting blend mode as a tuple of two GL enum values. The `render()` method should call `glBlendFunc` accordingly. This allows additive, alpha blending, etc.

### [NEEDS RESEARCH]: The `update(dt, audio_analyzer)` signature includes `audio_analyzer` as a parameter, but the public interface in the skeleton spec shows `update(dt)` only. Which is correct?

**Resolution**: The legacy shows `update(self, dt)` and the audio analyzer is stored via `set_audio_analyzer`. We'll follow that: `set_audio_analyzer(analyzer)` stores it, and `update(dt)` uses it if present. This matches the pattern used in other audio-reactive effects.

---

## Configuration Schema

```python
from typing import Tuple, Optional
from pydantic import BaseModel

class AdvancedParticle3DParameters(BaseModel):
    # System limits
    max_particles: int = 10000
    num_particles: int = 2000  # initial active count? Actually this is the spawn count? Clarify: it's the number to emit initially? The legacy used num_particles as current count? Actually it was used as the current number of particles? Let's define: max_particles is pool size; initial active count is 0; emitter spawns over time.
    
    # Physics
    gravity: Tuple[float, float, float] = (0.0, -0.05, 0.0)
    drag: float = 0.98
    turbulence_strength: float = 0.5
    turbulence_scale: float = 1.0
    turbulence_speed: float = 0.5
    
    # Emitter
    emit_rate: float = 50.0  # particles per second
    emit_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    emit_radius: float = 0.5
    emit_velocity: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    emit_spread: float = 0.5
    particle_life_min: float = 2.0
    particle_life_max: float = 5.0
    particle_size_start: float = 1.0
    particle_size_end: float = 0.0
    
    # Visual
    color_start: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    color_end: Tuple[float, float, float, float] = (0.0, 0.5, 1.0, 0.0)
    blend_mode: Tuple[int, int] = (GL_SRC_ALPHA, GL_ONE)  # additive
    point_size: float = 5.0  # base size multiplier (in pixels)
    
    # Audio
    audio_sensitivity: float = 1.0
    beat_multiplier: float = 2.0
    spectrum_influence: float = 0.5
    
    # Force fields
    attractor_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    attractor_strength: float = 0.0
    vortex_strength: float = 0.0
    vortex_axis: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    
    # Camera (optional)
    camera_position: Tuple[float, float, float] = (0.0, 0.0, 5.0)
    camera_target: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    camera_up: Tuple[float, float, float] = (0.0, 1.0, 0.0)
```

All float parameters have sensible ranges; validation should clamp where appropriate (e.g., drag between 0 and 1, emit_rate >= 0, etc.).

---

## State Management

- **Per-frame state**: None beyond uniform updates and VBO data upload.
- **Persistent state**: All parameters listed above, plus the audio_analyzer reference.
- **Init-once state**: Shader program, VBO/VAO, uniform locations.
- **Thread safety**: Not thread-safe; must be called from rendering thread with OpenGL context.

---

## GPU Resources

- **Vertex shader**: Instanced rendering shader that reads particle data and outputs quad vertices.
- **Fragment shader**: Simple point sprite or quad fragment shader with color and alpha.
- **VBO**: Buffer for particle attributes (position, size, color). Size = max_particles * stride.
- **VAO**: Vertex array object for instanced rendering setup.
- **No textures** required.

---

## Public Interface

```python
class AdvancedParticle3DSystem(Effect):
    def __init__(self) -> None:
        """Initialize the 3D particle system with default settings."""
    
    def set_audio_analyzer(self, analyzer: AudioAnalyzer) -> None:
        """
        Set the audio analyzer to use for reactivity.
        
        Args:
            analyzer: An AudioAnalyzer instance.
        """
    
    def update(self, dt: float) -> None:
        """
        Update the state of all particles over a time delta.
        
        Args:
            dt: Time step in seconds (used for physics simulation).
        """
    
    def render(self) -> None:
        """
        Render the particle system using OpenGL instanced rendering.
        This method should be called after update() each frame.
        """
    
    def set_parameter(self, name: str, value: Any) -> None:
        """
        Set a configurable parameter.
        
        Args:
            name: Parameter name (e.g. "gravity", "emit_rate").
            value: New value for the parameter; type must match expected.
        
        Raises:
            ValueError: If parameter name unknown or value type invalid.
        """
    
    def get_parameter(self, name: str) -> Any:
        """
        Retrieve current value of a parameter.
        
        Args:
            name: Parameter name.
            
        Returns:
            Current value of the parameter.
        
        Raises:
            ValueError: If name unknown.
        """
    
    # Inherited from Effect:
    # - apply_uniforms() may be overridden to set shader uniforms
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `dt` | `float` | Time delta in seconds for physics update | Must be ≥ 0.0; typically 1/60 or 1/120 |
| `audio_analyzer` | `AudioAnalyzer` | Source of real-time audio features | Optional; if None, audio reactivity disabled |
| `name` | `str` | Parameter name to set/get | Must be one of the defined parameters |
| `value` | `Any` | New value for parameter | Must match expected type and range |
| `output` | `None` (rendering) | Visual output via OpenGL rendering pipeline | No direct return; renders to current framebuffer |

---

## Dependencies

- External libraries:
  - `numpy` — used for particle array operations (fallback: use Python lists with performance degradation)
  - `OpenGL.GL` — required for GPU rendering and VBO management (fallback: not available; effect would fail)
- Internal modules:
  - `vjlive3.core.effects.shader_base.Effect` — base class
  - `vjlive3.core.audio_analyzer.AudioAnalyzer` — for audio features
  - `vjlive3.core.audio_reactor.AudioReactor` — optional audio modulation

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without OpenGL context raises appropriate error |
| `test_basic_operation` | update() and render() run without errors with default parameters |
| `test_emission_rate` | Correct number of particles spawned per frame based on emit_rate and dt |
| `test_particle_lifetime` | Particles die after lifetime expires and are respawned |
| `test_physics_gravity` | Gravity accelerates particles downward correctly |
| `test_physics_drag` | Drag reduces velocity over time |
| `test_force_attractor` | Attractor pulls particles toward its position |
| `test_force_vortex` | Vortex causes circular motion around axis |
| `test_force_turbulence` | Turbulence adds random jitter to particle motion |
| `test_color_interpolation` | Particle color interpolates from start to end over lifetime |
| `test_size_interpolation` | Particle size interpolates from start to end over lifetime |
| `test_audio_reactivity_emit_rate` | Audio amplitude increases emit rate |
| `test_audio_reactivity_velocity` | Audio spectrum increases particle velocity |
| `test_parameter_set_get` | Setting and retrieving parameters works with type validation |
| `test_particle_limit` | System respects max_particles and does not overflow |
| `test_render_without_crash` | render() executes without OpenGL errors |
| `test_cleanup` | After stop(), shader and VBOs are deleted, no GL errors |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT204: advanced_particles_3d implementation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/core/generators/particles_3d.py (L1-20)
```python
"""
Advanced 3D Particle System.
Ported from plugins/vparticles/particles_3d.py.
"""

import math
import numpy as np
from typing import Tuple, Optional, Any
import logging
from OpenGL.GL import *
from core.effects.shader_base import Effect
from core.audio_analyzer import AudioAnalyzer, AudioFeature
from core.audio_reactor import AudioReactor

logger = logging.getLogger(__name__)

class AdvancedParticle3DSystem(Effect):
    """
    TouchDesigner-inspired 3D Particle System.
```

### vjlive1/core/generators/particles_3d.py (L17-36)
```python
class AdvancedParticle3DSystem(Effect):
    """
    TouchDesigner-inspired 3D Particle System.
    Features:
    - GPU Instancing for 10,000+ particles
    - Compute-shader style physics (CPU simulated for now, mapped to VBOs)
    - Force fields: Attractors, Repulsors, Vortex, Turbulence
    - Texture mapping support
    """
    def __init__(self):
        super().__init__("advanced_particles_3d", self._get_fragment_shader(), self._get_vertex_shader())
        self.manual_render = True
        
        # System Limits
        self.max_particles = 10000
        self.num_particles = 2000
        self.enabled = True
        self.initialized = False
```

### vjlive1/core/generators/particles_3d.py (L33-52)
```python
        self.num_particles = 2000
        self.enabled = True
        self.initialized = False
        
        # Physics Parameters
        self.gravity = (0.0, -0.05, 0.0)
        self.drag = 0.98
        self.turbulence_strength = 0.5
        self.turbulence_scale = 1.0
        self.turbulence_speed = 0.5
        
        # Emitter Parameters
        self.emit_rate = 50  # Particles per frame
        self.emit_position = (0.0, 0.0, 0.0)
        self.emit_radius = 0.5
        self.emit_velocity = (0.0, 1.0, 0.0)
        self.emit_spread = 0.5
        self.particle_life_min = 2.0
        self.particle_life_max = 5.0
        self.particle_size_start = 1.0
```

### vjlive1/core/generators/particles_3d.py (L49-68)
```python
        self.emit_spread = 0.5
        self.particle_life_min = 2.0
        self.particle_life_max = 5.0
        self.particle_size_start = 1.0
        self.particle_size_end = 0.0
        
        # Visual Parameters
        self.color_start = (1.0, 1.0, 1.0, 1.0)
        self.color_end = (0.0, 0.5, 1.0, 0.0)
        self.blend_mode = (GL_SRC_ALPHA, GL_ONE) # Additive
        self.point_size = 5.0
        
        # Audio Reactivity
        self.audio_sensitivity = 1.0
        self.beat_multiplier = 2.0
        self.spectrum_influence = 0.5
        
        # Force Fields
        self.attractor_pos = (0.0, 0.0, 0.0)
        self.attractor_strength = 0.0
```

### vjlive1/core/generators/particles_3d.py (L65-84)
```python
        # Force Fields
        self.attractor_pos = (0.0, 0.0, 0.0)
        self.attractor_strength = 0.0
        self.vortex_strength = 0.0
        self.vortex_axis = (0.0, 1.0, 0.0)
        
        # Camera
        self.camera_position = np.array([0.0, 0.0, 5.0], dtype=np.float32)
        self.camera_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.camera_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
```

### vjlive1/core/generators/particles_3d.py (L81-100)
```python
    def _get_vertex_shader(self):
        return """
        #version 330 core
        layout(location = 0) in vec3 a_position;
        layout(location = 1) in float a_size;
        layout(location = 2) in vec4 a_color;
        
        uniform mat4 u_mvp;
        uniform float u_point_size;
        
        out vec4 v_color;
        
        void main() {
            gl_Position = u_mvp * vec4(a_position, 1.0);
            gl_PointSize = a_size * u_point_size;
            v_color = a_color;
        }
        """
```

### vjlive1/core/generators/particles_3d.py (L97-116)
```python
    def _get_fragment_shader(self):
        return """
        #version 330 core
        in vec4 v_color;
        out vec4 fragColor;
        
        void main() {
            vec2 coord = gl_PointCoord - vec2(0.5);
            float dist = length(coord);
            if (dist > 0.5) discard;
            float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
            fragColor = vec4(v_color.rgb, v_color.a * alpha);
        }
        """
```

### vjlive1/core/generators/particles_3d.py (L113-132)
```python
    def _get_fragment_shader(self):
        return """
        #version 330 core
        in vec4 v_color;
        out vec4 fragColor;
        
        void main() {
            vec2 coord = gl_PointCoord - vec2(0.5);
            float dist = length(coord);
            if (dist > 0.5) discard;
            float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
            fragColor = vec4(v_color.rgb, v_color.a * alpha);
        }
        """
    
    def _resize_particles(self, new_max):
        # Reallocate particle arrays if max_particles changes
        pass
```

### vjlive1/core/generators/particles_3d.py (L129-148)
```python
    def _resize_particles(self, new_max):
        # Reallocate particle arrays if max_particles changes
        pass
    
    def update(self, dt):
        # Spawn new particles
        to_spawn = int(self.emit_rate * dt)
        for i in range(to_spawn):
            if self.particle_count < self.max_particles:
                # Initialize particle
                idx = self.particle_count
                self.particle_positions[idx] = self.emit_position + np.random.uniform(-self.emit_radius, self.emit_radius, 3)
                self.particle_velocities[idx] = self.emit_velocity + np.random.uniform(-self.emit_spread, self.emit_spread, 3)
                self.particle_lifetimes[idx] = np.random.uniform(self.particle_life_min, self.particle_life_max)
                self.particle_sizes[idx] = self.particle_size_start
                self.particle_colors[idx] = self.color_start
                self.particle_count += 1
        
        # Update active particles
        for i in range(self.particle_count):
            # Physics integration
            # ... (forces, integration, etc.)
            pass
```

### vjlive1/core/generators/particles_3d.py (L145-164)
```python
            # ... (forces, integration, etc.)
            pass
        
        # Upload particle data to VBO
        if self.initialized:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, self.particle_data, GL_DYNAMIC_DRAW)
        
    def render(self):
        if not self.initialized:
            self._init_gl()
        glUseProgram(self.program)
        # Set uniforms, bind VBO, draw instanced
        glDrawArraysInstanced(GL_POINTS, 0, 1, self.particle_count)
```

---

## Easter Egg

**Easter Egg**: If the user sets `particle_size_start` to exactly `6.28` and `vortex_strength` to `3.14`, the particles form a perfect torus knot that rotates in time with the audio beat. This hidden "Sacred Geometry" mode is a nod to the mathematical beauty underlying particle systems. Triggered only when `u_mix` is exactly `0.618` (the golden ratio conjugate). The effect renders the particles as glowing golden wireframe instead of sprites.

---

## Additional Notes

- The legacy code used `gl_PointSize` which is deprecated. The VJLive3 implementation must use a core-profile compatible method (instanced quads) to avoid validation errors.
- The `manual_render = True` flag indicates the effect handles its own rendering; the base `Effect` class should not draw a full-screen quad automatically.
- The particle system is a **generator** effect, meaning it creates visual content from parameters rather than processing an input video. It should be added to the effect chain as a source node.
- The `num_particles` parameter in the legacy was ambiguous; we clarify that `max_particles` is the pool size, and the emitter spawns particles up to that limit. The current active count is `particle_count`.
- The `update()` method should be called every frame regardless of whether the effect is enabled? Typically, if disabled, skip update and render. We'll follow that pattern.

This spec provides a complete blueprint for implementing a high-performance, audio-reactive 3D particle system that meets VJLive3's requirements and avoids the pitfalls of the legacy implementation.