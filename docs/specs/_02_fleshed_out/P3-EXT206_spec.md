# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT206_particles_3d.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT206 — particles_3d (AdvancedParticle3DSystem)

**What This Module Does**

The `AdvancedParticle3DSystem` is a high-performance 3D particle system inspired by TouchDesigner, capable of simulating thousands of particles in real-time with physics-based behavior. It uses GPU instancing via OpenGL to render particles efficiently, with support for force fields (attractors, vortices, turbulence), audio reactivity, and dynamic visual properties (color interpolation, size variation, rotation). The system maintains particle state on the CPU (for physics) and streams it to the GPU via VBOs for rendering.

The particle lifecycle:
1. **Emission**: New particles are spawned at the emitter position with random velocity within a spread cone.
2. **Physics update**: Each particle's velocity and position are updated based on gravity, drag, and force fields.
3. **Aging**: Particle life decreases; when life ≤ 0, the particle is deactivated and recycled.
4. **Rendering**: Active particles are rendered as points (or textured quads) using GPU instancing.

The system is designed for visual effects in VJLive3 performances, with tight integration to audio analysis for reactive behavior.

**What This Module Does NOT Do**

- Does NOT implement compute-shader-based physics (physics is CPU-side in this version)
- Does NOT support 3D mesh rendering (only points or textured sprites)
- Does NOT provide advanced collision detection (particles pass through geometry)
- Does NOT handle scene graph management (it's a self-contained generator)
- Does NOT include audio analysis (relies on external AudioAnalyzer for features)
- Does NOT support particle-to-particle interactions (N-body)
- Does NOT provide a UI for parameter tweaking (controlled via ProgramPage)

---

## Detailed Behavior and Parameter Interactions

### Particle Data Structure

Each particle stores:
- `position`: (x, y, z) float3
- `velocity`: (vx, vy, vz) float3
- `life`: current remaining life (seconds)
- `max_life`: initial lifetime (seconds)
- `size_start`: initial size (at spawn)
- `size_now`: current size (interpolated between start and end)
- `size_end`: final size (at death)
- `color`: (r, g, b, a) float4
- `rotation`: orientation angle (radians)

The system uses separate NumPy arrays for each attribute for efficient vectorized operations.

### Emission

Particles are emitted at a configurable `emit_rate` (particles per frame). When `update(dt)` is called, the system spawns new particles:

```python
def _emit(self, dt):
    num_to_spawn = int(self.emit_rate * dt * self.some_scaling)  # Actually emit_rate is per frame, not per second
    # In legacy, emit_rate is particles per frame, so spawn exactly that many each update call
    for i in range(self.emit_rate):
        if self.active_count >= self.max_particles:
            break
        idx = self._find_inactive_particle()
        self._initialize_particle(idx)
        self.active_count += 1
```

The emitter has:
- `emit_position`: center of emission sphere
- `emit_radius`: particles spawn within this radius
- `emit_velocity`: base velocity vector
- `emit_spread`: randomness factor (0-1) applied to velocity direction

Particle initial velocity is computed as:
```python
direction = self.emit_velocity + random_vector * self.emit_spread
velocity = normalize(direction) * speed  # speed could be a parameter
```

### Physics Update

Each frame, for each active particle:

1. **Apply forces**:
   - Gravity: `vel += gravity * dt`
   - Drag: `vel *= drag` (per-frame multiplicative damping)
   - Attractor: if `attractor_strength != 0`, compute direction to attractor and apply force: `vel += (attractor_pos - pos).normalized() * attractor_strength * dt`
   - Vortex: if `vortex_strength != 0`, compute cross product with vortex axis to create rotational force: `vel += cross(axis, (pos - vortex_center)) * vortex_strength * dt`
   - Turbulence: if `turbulence_strength != 0`, add Perlin-like noise based on position and time: `vel += noise(pos * turbulence_scale + time * turbulence_speed) * turbulence_strength * dt`

2. **Update position**: `pos += vel * dt`

3. **Update life**: `life -= dt`

4. **Update size**: Interpolate between `size_start` and `size_end` based on remaining life fraction: `size_now = lerp(size_end, size_start, life / max_life)`

5. **Update color**: Similarly interpolate between `color_start` and `color_end` based on life fraction.

6. **Deactivate** if `life <= 0`: mark particle as inactive, reset its data, decrement `active_count`.

### Audio Reactivity

The system can respond to audio features (bass, mid, treble, beat) from an `AudioAnalyzer`. These are passed as uniforms to the shader and can also affect particle behavior on the CPU:

- **Emission rate modulation**: `emit_rate` can be scaled by `audio_sensitivity * (bass + mid + treble)` or by `beat_multiplier` on beat detection.
- **Size modulation**: Vertex shader multiplies `props.y` (size) by `(1.0 + audio_mid * 0.5)`.
- **Position displacement**: Vertex shader adds `audio_bass * 0.1 * sin(pos.x * 5.0 + time)` to the Y coordinate.
- **Force field modulation**: Attractor strength could be multiplied by audio_bass.

The legacy code shows audio uniforms in the vertex shader but not all CPU-side usage. We'll define that audio influences emission rate and possibly attractor strength.

### Rendering

The system uses OpenGL with:
- **VAO** (Vertex Array Object) to store attribute pointers
- **VBOs** (Vertex Buffer Objects) for position, color, and props arrays
- **Shader program** with vertex and fragment shaders

Rendering modes:
- **POINTS**: `glDrawArrays(GL_POINTS, ...)`
- **TEXTURED**: `glDrawArrays(GL_POINTS, ...)` with point sprite texture in fragment shader
- (Legacy also mentions LINES and MESH but not implemented)

The vertex shader:
- Transforms position by `mvp_matrix`
- Applies audio-based displacement
- Computes `gl_PointSize` with perspective scaling
- Passes color, life, rotation to fragment shader

The fragment shader:
- If `use_texture` and `render_mode == TEXTURED`, samples particle texture
- Otherwise outputs `v_color` modulated by `v_life` (for fading)

### Camera and MVP

The system maintains a camera (position, target, up, fov) and computes the Model-View-Projection matrix each frame. The particles are in world space; the camera transforms them to clip space.

### Force Fields

- **Attractor**: Point attractor that pulls particles toward a fixed position.
- **Vortex**: Rotational force around an axis; particles orbit the axis.
- **Turbulence**: Procedural noise field that adds chaotic motion.

These are optional and can be enabled/disabled by setting strength > 0.

---

## Integration

### VJLive3 Pipeline Integration

The `AdvancedParticle3DSystem` is a **generator/effect** that renders directly to the screen or to an FBO. It is self-contained and does not take input textures. It can be placed anywhere in the effects chain, but typically it's a source that other effects composite over.

**Typical usage**:

```python
# Initialize
particles = AdvancedParticle3DSystem()
particles.set_emitter_position(0, 0, 0)
particles.set_force_field_attractor((0, 0, 0), strength=2.0)
particles.set_audio_reactivity(sensitivity=1.5, beat_multiplier=2.0, spectrum_influence=0.5)
particles.enable(True)

# In the render loop
particles.update(delta_time)
particles.render(camera, projection_matrix)  # Or particles.draw()
```

The system requires an OpenGL context. It manages its own VBOs and shaders.

### Audio Integration

The system can be connected to an `AudioAnalyzer` instance. The analyzer provides audio feature values (bass, mid, treble, beat). These are passed to the particle system via `set_audio_features` or directly as uniform updates. The particle system uses these to modulate emission rate and shader uniforms.

---

## Performance

### Computational Cost

The system is **mixed CPU/GPU**:

- **CPU side**:
  - Particle physics: For N active particles, each update does ~30 FLOPs (vector adds, multiplies, noise). For 2000 particles, that's ~60,000 FLOPs per frame, negligible on modern CPUs.
  - Emission: Spawning new particles involves array indexing and initialization.
  - Matrix computation for camera: trivial.

- **GPU side**:
  - Vertex shader: per-particle operations (transform, audio displacement, size calc). For 2000 particles, very fast.
  - Fragment shader: per-particle (or per-pixel if points are large). Additive blending is cheap.
  - Memory bandwidth: Uploading VBO data each frame (position, color, props) for all active particles. This is the main cost. For 2000 particles with 3+4+4 floats = 11 floats ≈ 44 bytes, total ~88 KB per frame. At 60 Hz, that's ~5.3 MB/s, trivial.

**Scalability**: The system can handle up to 10,000 particles with ease on modern GPUs. The limiting factor is fill-rate if particles are large, but for point sprites it's fine.

### Memory Usage

- **CPU**: NumPy arrays for max_particles (10,000) × (3+3+1+4+4) floats ≈ 150 KB
- **GPU**: VBOs for same data ≈ 150 KB
- **Shader program**: < 50 KB
- **Texture**: optional particle sprite (e.g., 64x64 RGBA) ≈ 16 KB

Total < 1 MB, very lightweight.

### Optimization Strategies

- Use `glMapBuffer` or `glBufferSubData` to update VBOs efficiently. The legacy likely uses `glBufferData` with `GL_DYNAMIC_DRAW`.
- Use instanced rendering if moving to mesh particles (not needed for points).
- Cull particles behind camera? Not necessary for point sprites.
- Use a compute shader for physics in a future version to offload to GPU.

### Platform-Specific Considerations

- **Desktop**: No issues; requires OpenGL 3.3+
- **Embedded**: 10,000 particles may be heavy; reduce `max_particles` and `num_particles`
- **Mobile**: Use lower particle counts and simpler shaders

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | System initializes without crashing if OpenGL context missing; raises clear error |
| `test_basic_emission` | Particles are spawned when update() is called; active_count increases |
| `test_particle_lifetime` | Particles deactivate when life expires; active_count decreases appropriately |
| `test_physics_gravity` | Gravity affects velocity and position over time |
| `test_physics_drag` | Drag reduces velocity gradually |
| `test_force_field_attractor` | Attractor pulls particles toward its position |
| `test_force_field_vortex` | Vortex imparts rotational motion around axis |
| `test_force_field_turbulence` | Turbulence adds jitter to positions |
| `test_audio_reactivity_emission` | Audio features increase emission rate when sensitivity > 0 |
| `test_audio_reactivity_shader` | Audio uniforms affect particle size and position in vertex shader |
| `test_color_interpolation` | Particle color transitions from start to end over lifetime |
| `test_size_interpolation` | Particle size transitions from start to end over lifetime |
| `test_render_mode_points` | System renders points correctly (no crashes, points appear) |
| `test_render_mode_textured` | When use_texture=True, textured sprites are rendered |
| `test_emitter_parameters` | Changing emit_position, emit_radius, emit_velocity, emit_spread affects spawn behavior |
| `test_particle_count_limits` | System respects max_particles; does not overflow arrays |
| `test_cleanup` | All OpenGL resources (VAO, VBOs, texture, shader) are released on stop() |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

