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

