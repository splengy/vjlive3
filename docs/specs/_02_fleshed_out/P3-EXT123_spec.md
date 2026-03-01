# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT123_particles_3d.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT123 — particles_3d (ParticleState)

**What This Module Does**

The `Particle3DSystem` module implements a high-performance 3D particle system inspired by TouchDesigner, capable of simulating thousands of particles with physics-based behavior and real-time audio reactivity. The system uses GPU instancing via OpenGL vertex buffer objects (VBOs) to render particles efficiently, while particle physics (position, velocity, life) are computed on the CPU for deterministic control and ease of integration.

The particle system supports:
- **GPU instanced rendering**: Thousands of particles rendered in a single draw call using OpenGL instancing
- **Physics simulation**: Gravity, drag, turbulence, and force fields (attractors, vortex) affect particle motion
- **Dynamic emission**: Continuous particle emission from a configurable emitter with position, velocity, spread, and rate
- **Particle lifecycle**: Each particle has a finite lifespan, size interpolation (start to end), and color gradient
- **Audio reactivity**: Particle emission rate, force strength, and visual properties can be modulated by audio features (bass, mid, treble, beat)
- **Camera perspective**: 3D-to-2D projection using a configurable camera (position, target, up, FOV)
- **Multiple render modes**: Points, textured quads, lines, or mesh (wireframe) rendering
- **Texture support**: Optional particle texture for soft-edged particles

The system maintains particle state in CPU-side NumPy arrays for easy manipulation and transfers data to GPU via VBOs each frame. This hybrid approach balances performance with flexibility.

**What This Module Does NOT Do**

- Does not implement compute shaders (physics is CPU-side)
- Does not support particle-to-particle collisions
- Does not provide fluid dynamics or SPH (smoothed particle hydrodynamics)
- Does not include particle caching or playback of recorded simulations
- Does not support multi-pass rendering or depth-of-field effects
- Does not provide built-in particle textures (must be supplied externally)
- Does not handle scene graph or hierarchical transformations
- Does not include advanced lighting (particles are unlit, additive or blended)

---

## Detailed Behavior and Parameter Interactions

### Particle State Structure

Each particle has the following state (14 floats total):

| Component | Type | Description |
|-----------|------|-------------|
| `pos` | vec3 | Current position (x, y, z) in world space |
| `vel` | vec3 | Current velocity (vx, vy, vz) |
| `life` | float | Current remaining life in seconds |
| `max_life` | float | Initial lifespan when spawned (seconds) |
| `size_start` | float | Initial size when spawned |
| `size_now` | float | Current size (interpolated from start to end) |
| `rotation` | float | Current rotation angle (radians) |
| `color` | vec4 | RGBA color (r, g, b, a) |

The particle arrays are stored as separate NumPy arrays for efficient vectorized operations:

```python
self.pos: (N, 3) float32  # positions
self.vel: (N, 3) float32  # velocities
self.life: (N,) float32   # current life
self.props: (N, 4) float32  # [max_life, size_start, size_now, rotation]
self.colors: (N, 4) float32  # [r, g, b, a]
```

### Emitter

The emitter controls how new particles are created:

- **Emit position** (`emit_position`): World-space origin of emitted particles
- **Emit radius** (`emit_radius`): Particles spawn within a sphere of this radius around `emit_position`
- **Emit velocity** (`emit_velocity`): Initial velocity vector for emitted particles
- **Emit spread** (`emit_spread`): Random deviation from `emit_velocity` (0 = exact direction, 1 = isotropic)
- **Emit rate** (`emit_rate`): Number of particles to emit per second (not per frame; must scale with `dt`)

When emitting, for each particle:
1. Position = `emit_position` + random point in sphere of radius `emit_radius`
2. Velocity = `emit_velocity` + random vector with magnitude up to `emit_spread`
3. Life = random between `particle_life_min` and `particle_life_max`
4. Size = `particle_size_start`
5. Color = `color_start` (will interpolate to `color_end` over life)

### Physics Update

Each frame, for each active particle:

1. **Apply gravity**: `vel += gravity * dt`
2. **Apply drag**: `vel *= drag` (per-frame multiplicative damping)
3. **Apply turbulence** (if enabled): Add Perlin-like noise based on position and time
4. **Apply force fields**:
   - **Attractor**: `direction = attractor_pos - pos; force = normalize(direction) * attractor_strength / (distance^2 + epsilon); vel += force * dt`
   - **Vortex**: `to_center = pos - vortex_pos; tangent = cross(vortex_axis, to_center); vel += tangent * vortex_strength * dt`
5. **Update position**: `pos += vel * dt`
6. **Update life**: `life -= dt`
7. **Update size**: Interpolate from `size_start` to `size_end` based on `life / max_life`
8. **Update color**: Interpolate from `color_start` to `color_end` based on `life / max_life`
9. **Update rotation**: Could add angular velocity, but not in legacy; rotation is static or could be time-based

Particles with `life <= 0` are deactivated (removed from active list). The system uses a "sparse" approach where active particles are packed to the front of the arrays, with `active_count` tracking how many are alive.

### Audio Reactivity

The system integrates with an `AudioAnalyzer` to provide real-time audio features:

- `audio_bass`: Low-frequency energy (20-250 Hz)
- `audio_mid`: Mid-frequency energy (250-4000 Hz)
- `audio_treble`: High-frequency energy (4000-20000 Hz)
- `audio_beat`: Beat detection signal (0.0-1.0, transient on beats)

Audio features modulate:
- **Emission rate**: `effective_rate = emit_rate * (1.0 + audio_sensitivity * (bass + mid + treble) / 3.0)`
- **Attractor strength**: `effective_attractor = attractor_strength * (1.0 + audio_sensitivity * beat * beat_multiplier)`
- **Particle size**: In vertex shader: `size = props.y * (1.0 + audio_mid * 0.5)`
- **Particle displacement**: In vertex shader: `pos.y += audio_bass * 0.1 * sin(pos.x * 5.0 + time)`

The `audio_sensitivity` parameter scales the overall influence of audio.

### Camera and Projection

The camera is defined by:
- `camera_position`: Eye point in world space
- `camera_target`: Look-at point
- `camera_up`: Up vector (usually (0,1,0))
- `fov`: Field of view in degrees (vertical)

The system computes a view matrix (look-at) and projection matrix (perspective) each frame, combining them into an MVP matrix that is sent to the vertex shader. The vertex shader transforms particle positions from world space to clip space:

```glsl
gl_Position = mvp_matrix * vec4(pos, 1.0);
```

The `gl_PointSize` is set based on the particle's size attribute and perspective division:

```glsl
gl_PointSize = max(1.0, size * (100.0 / gl_Position.w));
```

This ensures particles appear smaller when farther away.

### Render Modes

The system supports multiple rendering modes via the `render_mode` enum:

- **POINTS**: Render each particle as a GL_POINT sprite (default). The fragment shader draws a circular point with optional texture.
- **TEXTURED**: Render particles as textured quads (requires geometry shader or instanced quads; not shown in legacy snippet)
- **LINES**: Render particles as lines (could be used for trails)
- **MESH**: Render as wireframe mesh (unlikely for particles; maybe for debugging)

The legacy code shows POINTS mode with a simple fragment shader that samples a texture if `use_texture` is true, otherwise outputs a solid color with alpha.

### GPU Instancing

The system uses OpenGL's instanced rendering to draw all particles in one call:

- **VAO**: Vertex array object that stores attribute bindings
- **VBO_pos**: Vertex buffer for particle positions (3 floats per particle)
- **VBO_color**: Vertex buffer for colors (4 floats per particle)
- **VBO_props**: Vertex buffer for properties (4 floats per particle: life, size, rotation, unused)

The vertex shader uses `gl_VertexID` or an instance ID to index into these buffers. The legacy code likely uses `glDrawArraysInstanced(GL_POINTS, 0, 1, active_count)` or similar, where each "vertex" is a single point but the attributes are per-instance.

### Particle Lifecycle Management

The `update(dt)` method handles:
- Emitting new particles (adding to active arrays)
- Physics integration for all active particles
- Deactivating dead particles (compacting arrays)
- Uploading updated particle data to GPU VBOs

The system maintains a "free list" or simply packs active particles to the front and uses `active_count`. New particles are added at index `active_count` and then `active_count` is incremented. When particles die, the last active particle is moved into the gap (swap-and-pop) to keep the active region contiguous.

---

## Integration

### VJLive3 Pipeline Integration

The `Particle3DSystem` is a **generator/effect** that produces visual output. It integrates as a frame processor:

```
[Audio Input] → [Particle3DSystem] → [Rendered Output]
```

**Position**: Can be placed anywhere in the effects chain, but typically after any 2D effects that should be overlaid on the 3D scene.

**Frame Processing**:

1. The pipeline calls `system.update(dt)` once per frame with the frame's delta time.
2. The system updates particle physics, emits new particles, removes dead ones.
3. The system uploads particle data to GPU VBOs (using `glBufferSubData` or `glMapBuffer`).
4. The pipeline calls `system.render()` to draw the particles.
5. The system sets up shader uniforms (MVP matrix, audio levels, time, etc.) and issues the instanced draw call.
6. The output is rendered directly to the framebuffer (or to a texture if using FBO).

**Audio Integration**: The system can optionally receive an `AudioAnalyzer` instance. If provided, it queries audio features each frame and uses them to modulate parameters. The audio analyzer should be updated separately by the audio pipeline.

**Camera Setup**: The camera parameters should be set to match the VJLive3 scene camera. If the system is used as a standalone effect, it may provide its own camera. If used within a larger 3D scene, the camera may be controlled externally and the particle system should adopt the scene's view/projection matrices.

**Shader Management**: The system includes its own vertex and fragment shaders. It should compile them at initialization and reuse. Uniform locations should be cached.

---

## Performance

### Computational Cost

The system is **mixed CPU/GPU**:

- **CPU side**: Physics simulation for up to 10,000 particles per frame. Each particle requires ~20 FLOPs (gravity, drag, force fields, life decay, interpolation). At 10,000 particles, that's ~200,000 FLOPs per frame, which is negligible on modern CPUs (< 0.1 ms). The main CPU cost is memory bandwidth for updating NumPy arrays and uploading to VBOs.
- **GPU side**: Instanced rendering of 10,000 points. This is extremely fast on any GPU since it's a single draw call with minimal vertex processing. Fragment shader runs per-pixel for each point that covers a pixel; with small point sizes, this is cheap.

**Expected performance**:
- 1,000 particles: < 0.5 ms total
- 10,000 particles: < 2 ms total
- 100,000 particles: ~10-20 ms (may be limited by VBO upload bandwidth)

### Memory Usage

- **CPU memory**: 
  - Particle arrays: `pos` (10k × 3 × 4 = 120 KB), `vel` (120 KB), `life` (40 KB), `props` (160 KB), `colors` (160 KB) = ~600 KB total
  - VBO handles and shaders: negligible
- **GPU memory**: 
  - VBOs: same size as above, stored in GPU memory (~600 KB)
  - Shaders: < 100 KB

### Optimization Strategies

1. **VBO streaming**: Use `glBufferSubData` with `GL_DYNAMIC_DRAW` or `glMapBufferRange` with `GL_MAP_WRITE_BIT` to efficiently upload particle data each frame.
2. **Culling**: Optionally cull particles that are behind the camera or too far away to reduce GPU load.
3. **LOD**: Reduce particle count or size at lower performance tiers.
4. **Fixed timestep**: Use a fixed physics timestep (e.g., 60 Hz) and accumulate `dt` to avoid instability when frame rate varies.
5. **Particle pooling**: Reuse particle slots instead of deallocating; already done via swap-and-pop.
6. **Shader simplicity**: Keep vertex/fragment shaders minimal; avoid heavy math in fragment shader.

### Platform-Specific Considerations

- **Desktop**: No issues; OpenGL 3.3+ required.
- **Embedded (Raspberry Pi)**: May struggle with >10,000 particles due to limited GPU bandwidth. Consider reducing `max_particles` or using simpler shaders.
- **Headless/CPU-only**: The system can run in CPU-only mode by not creating OpenGL resources; it would still compute particle state but not render. Useful for simulation-only use cases.

### Performance Testing Recommendations

- Benchmark with varying particle counts (1k, 5k, 10k, 50k, 100k)
- Measure CPU time for `update()` and GPU time for `render()` separately
- Test with all audio reactivity enabled vs disabled
- Profile memory bandwidth using tools like `nvidia-smi` or `glxinfo`
- Verify that VBO uploads are not stalling the GPU pipeline (use persistent mapping if needed)

---

## Test Plan (Expanded)

The existing test plan is minimal. Expand with:

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | System initializes without crashing if OpenGL context is missing; falls back gracefully or raises clear error |
| `test_basic_operation` | update() advances particle positions correctly; particles move according to velocity and gravity |
| `test_emission` | New particles are created at correct rate and with correct initial state |
| `test_particle_death` | Particles with expired life are removed from active list; active_count decreases appropriately |
| `test_force_field_attractor` | Attractor pulls particles toward its position; strength scales correctly |
| `test_force_field_vortex` | Vortex imparts tangential velocity around axis; particles orbit correctly |
| `test_turbulence` | Turbulence adds random jitter to positions; scales with strength and speed |
| `test_audio_reactivity` | Audio features (bass, mid, treble, beat) modulate emission rate, size, and displacement as expected |
| `test_camera_projection` | Camera matrices correctly transform 3D positions to 2D clip space; FOV affects point size |
| `test_render_modes` | Switching render modes changes output (points vs textured) without crashing |
| `test_texture_upload` | If a texture is provided, it is bound and used in the fragment shader |
| `test_parameter_bounds` | Setting parameters outside valid ranges clamps or raises errors (e.g., negative emit_rate) |
| `test_particle_state_query` | `get_particle_state(index)` returns correct values for active particles; inactive or invalid index raises IndexError |
| `test_active_count_consistency` | After many update cycles, active_count never exceeds max_particles and matches number of alive particles |
| `test_cleanup` | OpenGL resources (VAO, VBOs, texture) are deleted on destruction; no memory leaks |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

