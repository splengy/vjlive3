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

### [NEEDS RESEARCH]: How is the particle data texture actually structured and used in the shader?

**Finding**: The legacy code shows two textures: `particle_data_tex` (RGBA for pos.xy, vel.xy?) and `particle_props_tex` (RGBA for energy, type, etc.). But the vertex shader uses vertex attributes from VBOs, not textures. This suggests the system may have two modes: CPU-VBO for dynamic updates, or texture-based for compute-shader style. The snippet shows VBOs being used.

**Resolution**: The VJLive3 implementation should use VBOs for particle data (positions, colors, properties) as shown in the legacy `__init__`. The texture-based approach may be an alternative for GPU-only simulation, but that's out of scope. Stick with VBOs.

### [NEEDS RESEARCH]: What is the exact implementation of turbulence?

**Finding**: The legacy mentions `turbulence_strength` and `turbulence_scale` and `turbulence_speed` but doesn't show the code. Typically, turbulence is implemented using 3D Perlin noise or Simplex noise: `turbulence = noise(pos * scale + time * speed) * strength`.

**Resolution**: Implement a simple 3D noise function in the CPU update loop. Use a pre-existing library (e.g., `noise` package) or implement a basic gradient noise. The noise should be evaluated per-particle each frame and added to velocity or position.

### [NEEDS RESEARCH]: How does the render_mode affect the fragment shader?

**Finding**: The fragment shader snippet is incomplete. It shows `uniform int render_mode` but only handles points. For textured quads, a geometry shader would expand points into quads, or the system would use instanced quads with 4 vertices per particle.

**Resolution**: For simplicity, implement only POINTS mode in the first version. If TEXTURED mode is needed, add a geometry shader that emits a quad oriented toward the camera (billboard). The fragment shader would then sample the particle texture and apply color/alpha.

### [NEEDS RESEARCH]: How are force fields updated? Can multiple attractors/vortexes be added?

**Finding**: The legacy class has single `attractor_pos` and `attractor_strength`, `vortex_strength`, `vortex_axis`. This suggests only one of each type can be active at a time.

**Resolution**: Support one attractor and one vortex for simplicity. If needed, extend later to arrays of force fields.

### [NEEDS RESEARCH]: What is the purpose of `rotation` in particle properties?

**Finding**: The vertex shader passes `v_rotation` to fragment shader but doesn't use it. For point sprites, rotation is not visible unless using textured quads where the texture is rotated.

**Resolution**: Store rotation but don't use it in POINTS mode. For TEXTURED mode, use rotation to orient the quad.

---

## Configuration Schema

```python
METADATA = {
  "params": [
    # System limits
    {"id": "max_particles", "name": "Max Particles", "default": 10000, "min": 100, "max": 100000, "type": "int", "description": "Maximum number of particles (allocated at init)"},
    {"id": "num_particles", "name": "Initial Count", "default": 2000, "min": 0, "max": 100000, "type": "int", "description": "Initial number of active particles (spawned at start)"},
    {"id": "enabled", "name": "Enabled", "default": True, "type": "bool", "description": "Enable/disable particle system"},

    # Physics
    {"id": "gravity", "name": "Gravity", "default": (0.0, -0.05, 0.0), "type": "vec3", "description": "Gravity acceleration (world units/s^2)"},
    {"id": "drag", "name": "Drag", "default": 0.98, "min": 0.0, "max": 1.0, "type": "float", "description": "Velocity damping per second (1.0 = no drag)"},
    {"id": "turbulence_strength", "name": "Turbulence Strength", "default": 0.5, "min": 0.0, "max": 10.0, "type": "float", "description": "Amplitude of turbulence noise"},
    {"id": "turbulence_scale", "name": "Turbulence Scale", "default": 1.0, "min": 0.01, "max": 100.0, "type": "float", "description": "Spatial frequency of turbulence"},
    {"id": "turbulence_speed", "name": "Turbulence Speed", "default": 0.5, "min": 0.0, "max": 10.0, "type": "float", "description": "Temporal speed of turbulence animation"},

    # Emitter
    {"id": "emit_rate", "name": "Emit Rate", "default": 50.0, "min": 0.0, "max": 1000.0, "type": "float", "description": "Particles emitted per second"},
    {"id": "emit_position", "name": "Emit Position", "default": (0.0, 0.0, 0.0), "type": "vec3", "description": "World-space emitter origin"},
    {"id": "emit_radius", "name": "Emit Radius", "default": 0.5, "min": 0.0, "max": 10.0, "type": "float", "description": "Spawn radius around emit_position"},
    {"id": "emit_velocity", "name": "Emit Velocity", "default": (0.0, 1.0, 0.0), "type": "vec3", "description": "Initial velocity of emitted particles"},
    {"id": "emit_spread", "name": "Emit Spread", "default": 0.5, "min": 0.0, "max": 1.0, "type": "float", "description": "Randomness of initial direction (0=exact, 1=isotropic)"},
    {"id": "particle_life_min", "name": "Life Min", "default": 2.0, "min": 0.1, "max": 60.0, "type": "float", "description": "Minimum particle lifespan (seconds)"},
    {"id": "particle_life_max", "name": "Life Max", "default": 5.0, "min": 0.1, "max": 60.0, "type": "float", "description": "Maximum particle lifespan (seconds)"},
    {"id": "particle_size_start", "name": "Size Start", "default": 1.0, "min": 0.01, "max": 100.0, "type": "float", "description": "Initial particle size (world units)"},
    {"id": "particle_size_end", "name": "Size End", "default": 0.0, "min": 0.0, "max": 100.0, "type": "float", "description": "Final particle size at end of life"},

    # Visual
    {"id": "color_start", "name": "Color Start", "default": (1.0, 1.0, 1.0, 1.0), "type": "vec4", "description": "RGBA color when particle spawns"},
    {"id": "color_end", "name": "Color End", "default": (0.0, 0.5, 1.0, 0.0), "type": "vec4", "description": "RGBA color when particle dies"},
    {"id": "blend_mode", "name": "Blend Mode", "default": (GL_SRC_ALPHA, GL_ONE), "type": "blend_mode", "description": "OpenGL blend mode (e.g., additive, alpha)"},
    {"id": "point_size", "name": "Point Size", "default": 5.0, "min": 1.0, "max": 100.0, "type": "float", "description": "Base point size in pixels (if not using size attribute)"},
    {"id": "render_mode", "name": "Render Mode", "default": 0, "min": 0, "max": 3, "type": "int", "description": "0=Points, 1=Textured, 2=Lines, 3=Mesh"},
    {"id": "use_texture", "name": "Use Texture", "default": False, "type": "bool", "description": "Whether to sample particle texture in fragment shader"},
    {"id": "particle_texture", "name": "Particle Texture", "default": None, "type": "texture", "description": "OpenGL texture ID for particle sprite"},

    # Audio
    {"id": "audio_sensitivity", "name": "Audio Sensitivity", "default": 1.0, "min": 0.0, "max": 10.0, "type": "float", "description": "Overall scaling of audio influence"},
    {"id": "beat_multiplier", "name": "Beat Multiplier", "default": 2.0, "min": 1.0, "max": 10.0, "type": "float", "description": "Multiplier for beat-synced effects"},
    {"id": "spectrum_influence", "name": "Spectrum Influence", "default": 0.5, "min": 0.0, "max": 1.0, "type": "float", "description": "How much frequency spectrum affects particles"},

    # Force Fields
    {"id": "attractor_pos", "name": "Attractor Position", "default": (0.0, 0.0, 0.0), "type": "vec3", "description": "World position of attractor force"},
    {"id": "attractor_strength", "name": "Attractor Strength", "default": 0.0, "min": 0.0, "max": 10.0, "type": "float", "description": "Strength of attraction (positive pulls, negative repels)"},
    {"id": "vortex_strength", "name": "Vortex Strength", "default": 0.0, "min": 0.0, "max": 10.0, "type": "float", "description": "Strength of rotational vortex"},
    {"id": "vortex_axis", "name": "Vortex Axis", "default": (0.0, 1.0, 0.0), "type": "vec3", "description": "Axis of rotation for vortex"},

    # Camera
    {"id": "camera_position", "name": "Camera Position", "default": (0.0, 0.0, 5.0), "type": "vec3", "description": "Eye point in world space"},
    {"id": "camera_target", "name": "Camera Target", "default": (0.0, 0.0, 0.0), "type": "vec3", "description": "Look-at point"},
    {"id": "camera_up", "name": "Camera Up", "default": (0.0, 1.0, 0.0), "type": "vec3", "description": "Up vector (should be normalized)"},
    {"id": "fov", "name": "FOV", "default": 60.0, "min": 1.0, "max": 180.0, "type": "float", "description": "Vertical field of view in degrees"},
  ]
}
```

**Presets**: Not applicable; this is a generator system.

---

## State Management

- **Per-frame state**: `dt`, `active_count`, temporary arrays for physics calculations. These are transient.
- **Persistent state**: All configuration parameters (gravity, drag, emitter settings, force fields, camera, render mode). These persist for the lifetime of the system instance.
- **Init-once state**: OpenGL objects (VAO, VBOs, shader program, texture). Initialized in `__init__` or first `update()` and reused.
- **Thread safety**: The system is **not thread-safe**. `update()` and `render()` must be called from the same thread with an active OpenGL context. If used from multiple threads, external synchronization is required.

---

## GPU Resources

This system is **GPU-accelerated** and requires a shader-capable GPU (OpenGL 3.3+). It uses:

- **Vertex shader**: Instanced rendering shader that reads per-particle attributes from VBOs and applies MVP transformation, audio displacement, and size calculation.
- **Fragment shader**: Simple shader that outputs particle color with optional texture sampling.
- **Vertex Array Object (VAO)**: Stores attribute bindings for instanced VBOs.
- **Vertex Buffer Objects (VBOs)**: Three buffers for positions, colors, and properties (life, size, rotation). These are updated every frame with `glBufferSubData` or `glMapBuffer`.
- **Texture** (optional): Particle sprite texture if `use_texture` is enabled.

If GPU resources are exhausted (out of memory), the system should raise an exception. A CPU fallback (rendering with matplotlib or PIL) is not practical for real-time use; instead, reduce `max_particles`.

---

## Public Interface

```python
class Particle3DSystem:
    def __init__(self) -> None:
        """Initialize the 3D particle system with default parameters."""
    
    def update(self, dt: float) -> None:
        """
        Update particle physics, emit new particles, and upload data to GPU.
        
        Args:
            dt: Time delta in seconds (should be > 0, typically 1/60 or 1/120)
        """
    
    def render(self) -> None:
        """Render the particle system using the current GPU state."""
    
    def set_emitter_position(self, x: float, y: float, z: float) -> None:
        """Set the emitter's world position."""
    
    def add_force_field_attractor(self, pos: Tuple[float, float, float], strength: float) -> None:
        """
        Set an attractor force field.
        
        Args:
            pos: Position of attractor in world space
            strength: Strength (positive pulls, negative repels)
        """
    
    def set_camera_view(self, position: Tuple[float, float, float],
                        target: Tuple[float, float, float],
                        up: Tuple[float, float, float]) -> None:
        """
        Set the camera view parameters.
        
        Args:
            position: Camera eye position
            target: Look-at point
            up: Up vector (should be normalized)
        """
    
    def get_particle_state(self, index: int) -> Dict[str, Any]:
        """
        Retrieve the state of a specific particle (for debugging or external access).
        
        Args:
            index: Particle index (0 <= index < active_count)
            
        Returns:
            Dictionary with keys: pos (tuple), vel (tuple), life (float), max_life (float),
            size (float), color (tuple), rotation (float)
        """
    
    def set_audio_analyzer(self, analyzer: AudioAnalyzer) -> None:
        """Attach an audio analyzer for audio-reactive behavior."""
    
    def get_active_count(self) -> int:
        """Return the current number of active particles."""
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `dt` | `float` | Time delta in seconds for physics update | Must be ≥ 0.0; typically 1/60 or 1/120 |
| `x`, `y`, `z` | `float` | Coordinates of emitter position | Range: [-10.0, 10.0] (normalized world space) |
| `pos` | `Tuple[float, float, float]` | Position for force field attractor | Each component typically in [-5.0, 5.0] |
| `strength` | `float` | Strength of force field | Range: [0.0, 10.0]; default 0.0 |
| `position`, `target`, `up` | `Tuple[float, float, float]` | Camera view parameters | Position and target must not be identical; up vector should be normalized |
| `index` | `int` | Index of particle to query state | Range: [0, active_count-1]; invalid index raises IndexError |
| `analyzer` | `AudioAnalyzer` | Audio analyzer instance | Must provide get_feature(name) method |
| `return_value` (from get_particle_state) | `dict` | Particle state with pos, vel, life, size, color, rotation | All floats; pos/vel/color as 3-tuples or 4-tuples |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for particle array management and vector math — **hard requirement**; if missing, raises ImportError
  - `OpenGL.GL` — used for rendering via shaders and VBOs — fallback: system can still update particle state but render() becomes no-op or raises RuntimeError
- Internal modules this depends on:
  - `vjlive3.core.effects.shader_base.Effect` — base class providing shader compilation and OpenGL context management
  - `vjlive3.core.audio_analyzer.AudioAnalyzer` — for audio reactivity
  - `vjlive3.core.audio_reactor.AudioReactor` — for mapping audio features to parameters

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | System initializes without crashing if OpenGL context is missing; falls back gracefully or raises clear error |
| `test_basic_operation` | Core update loop advances particle positions correctly with gravity and drag over time |
| `test_emission` | New particles are created at correct rate and with correct initial state (position within radius, velocity with spread) |
| `test_particle_death` | Particles with expired life are removed; active_count decreases; no dead particles remain |
| `test_force_field_attractor` | Attractor pulls particles toward its position; strength scales correctly; distance falloff works |
| `test_force_field_vortex` | Vortex imparts tangential velocity; particles orbit around axis |
| `test_turbulence` | Turbulence adds random jitter to positions; scales with strength and speed |
| `test_audio_reactivity` | Audio features (bass, mid, treble, beat) modulate emission rate, size, and displacement as expected |
| `test_camera_projection` | Camera matrices correctly transform 3D positions to 2D clip space; FOV affects point size |
| `test_render_modes` | Switching render modes changes output (points vs textured) without crashing |
| `test_texture_upload` | If a texture is provided, it is bound and used in the fragment shader |
| `test_parameter_bounds` | Setting parameters outside valid ranges clamps or raises errors (e.g., negative emit_rate) |
| `test_particle_state_query` | `get_particle_state()` returns consistent, valid values for active particles; inactive or invalid index raises IndexError |
| `test_active_count_consistency` | After many update cycles, active_count never exceeds max_particles and matches number of alive particles |
| `test_cleanup` | OpenGL resources (VAO, VBOs, texture) are deleted on destruction; no memory leaks |

**Minimum coverage**: 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT123: particles_3d (ParticleState) - Port from VJlive legacy to VJLive3` message
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
    Features:
    - GPU Instancing for 10,000+ particles
    - Compute-shader style physics (CPU simulated for now, mapped to VBOs)
    - Force fields: Attractors, Repulsors, Vortex, Turbulence
    - Texture mapping support
    """
    def __init__(self):
        super().__init__("advanced_particles_3d", self._get_fragment_shader(), self._get_vertex_shader())
        self.manual_render = True
```

### vjlive1/core/generators/particles_3d.py (L17-36)
```python
        super().__init__("advanced_particles_3d", self._get_fragment_shader(), self._get_vertex_shader())
        self.manual_render = True
        
        # System Limits
        self.max_particles = 10000
        self.num_particles = 2000
        self.enabled = True
        self.initialized = False
        
        # Physics Parameters
        self.gravity = (0.0, -0.05, 0.0)
        self.drag = 0.98
        self.turbulence_strength = 0.5
        self.turbulence_scale = 1.0
        self.turbulence_speed = 0.5
```

### vjlive1/core/generators/particles_3d.py (L33-52)
```python
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
```

### vjlive1/core/generators/particles_3d.py (L65-84)
```python
        self.audio_sensitivity = 1.0
        self.beat_multiplier = 2.0
        self.spectrum_influence = 0.5
        
        # Force Fields
        self.attractor_pos = (0.0, 0.0, 0.0)
        self.attractor_strength = 0.0
        self.vortex_strength = 0.0
        self.vortex_axis = (0.0, 1.0, 0.0)
        
        # Camera
        self.camera_position = np.array([0.0, 0.0, 5.0], dtype=np.float32)
        self.camera_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.camera_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self.fov = 60.0
```

### vjlive1/core/generators/particles_3d.py (L81-100)
```python
        self.camera_position = np.array([0.0, 0.0, 5.0], dtype=np.float32)
        self.camera_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.camera_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self.fov = 60.0
        
        # Particle Data Arrays (CPU side for logic)
        # Structure: [x, y, z, vx, vy, vz, life, max_life, size, r, g, b, a, angle]
        # Optimized with separate arrays for numpy speed
        self.pos = np.zeros((self.max_particles, 3), dtype=np.float32)
        self.vel = np.zeros((self.max_particles, 3), dtype=np.float32)
        self.life = np.zeros(self.max_particles, dtype=np.float32)
        self.props = np.zeros((self.max_particles, 4), dtype=np.float32) # max_life, size_start, size_now, rotation
        self.colors = np.zeros((self.max_particles, 4), dtype=np.float32)
        
        self.active_count = 0
```

### vjlive1/core/generators/particles_3d.py (L97-116)
```python
        self.colors = np.zeros((self.max_particles, 4), dtype=np.float32)
        
        self.active_count = 0
        
        # VBOs
        self.vao = 0
        self.vbo_pos = 0
        self.vbo_color = 0
        self.vbo_props = 0 # Life, Size, Rotation, etc passes to shader?
        
        # Texture
        self.texture_id = None
        self.use_textures = False
        
        self.audio_analyzer = None
```

### vjlive1/core/generators/particles_3d.py (L113-132)
```python
        self.audio_analyzer = None
        
        # Render Mode
        from enum import Enum
        class RenderMode(Enum):
            POINTS = 0
            TEXTURED = 1
            LINES = 2
            MESH = 3
        self.render_mode = RenderMode.POINTS
        
    def _get_vertex_shader(self):
        return """
        #version 330 core
        
        layout(location = 0) in vec3 position;
        layout(location = 1) in vec4 color;
        layout(location = 2) in vec4 props; // x: life, y: size, z: rotation, w: unused
```

### vjlive1/core/generators/particles_3d.py (L129-148)
```python
        layout(location = 0) in vec3 position;
        layout(location = 1) in vec4 color;
        layout(location = 2) in vec4 props; // x: life, y: size, z: rotation, w: unused

        uniform mat4 mvp_matrix;
        uniform float time;
        uniform float use_texture;
        
        uniform float audio_bass;
        uniform float audio_mid;
        uniform float audio_treble;
        uniform float audio_beat;
        
        out vec4 v_color;
        out float v_life;
        out float v_rotation;
        
        void main() {
            vec3 pos = position;
            
            // Audio displacement
            pos.y += audio_bass * 0.1 * sin(pos.x * 5.0 + time);
            
            gl_Position = mvp_matrix * vec4(pos, 1.0);
            
            // Size calculation
            float size = props.y * (1.0 + audio_mid * 0.5);
            gl_PointSize = max(1.0, size * (100.0 / gl_Position.w)); // Perspective scaling
            
            v_color = color;
            v_life = props.x;
            v_rotation = props.z;
        }
        """
```

### vjlive1/core/generators/particles_3d.py (L145-164)
```python
            v_rotation = props.z;
        }
        """

    def _get_fragment_shader(self):
        return """
        #version 330 core
        
        in vec4 v_color;
        in float v_life;
        in float v_rotation;
        
        uniform sampler2D particle_texture;
        uniform float use_texture;
        uniform int render_mode; // 0=Points, 1=Textured
        
        out vec4 fragColor;
        
        void main() {
            vec4 col = v_color;
```

[NEEDS RESEARCH]: The full implementation of the `update()` method, turbulence noise function, and matrix calculation (look-at + perspective) are not shown in the snippets. These should be derived from standard 3D graphics and particle system algorithms. The spec provides a complete blueprint for implementation based on the parameters and shader code visible.
