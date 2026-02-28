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

### [NEEDS RESEARCH]: How exactly is `emit_rate` interpreted? Particles per frame or per second?

**Finding**: The legacy code sets `self.emit_rate = 50` and comments "Particles per frame". In the update loop (not shown), it likely spawns exactly `emit_rate` particles each call. However, if `update(dt)` is called with variable dt, spawning per frame independent of dt could cause inconsistent emission when frame rate changes. Better to interpret as particles per second and spawn `emit_rate * dt`. But the comment says per frame. We'll follow legacy: per frame.

**Resolution**: `emit_rate` is particles per frame. The `update(dt)` method will spawn exactly that many particles each call, regardless of dt. This means emission rate is tied to frame rate; if you want time-based emission, you need to adjust `emit_rate` based on expected fps. We'll document this quirk.

### [NEEDS RESEARCH]: How is turbulence noise implemented?

**Finding**: The legacy mentions `turbulence_strength`, `turbulence_scale`, `turbulence_speed` but the actual noise function is not in the snippets. Likely uses a simple hash-based noise or Perlin. The update would do: `noise_val = noise3D(pos * scale + time * speed)` and add to velocity.

**Resolution**: Implement a simple 3D noise function (e.g., value noise with interpolation) or use a library. For simplicity, we can use `np.sin` combinations or a precomputed 3D texture. Since the spec needs to be implementable, we'll describe the interface and leave implementation details to the developer, but note that a noise function is required.

### [NEEDS RESEARCH]: How are force fields combined? Are they additive?

**Finding**: Not shown. Likely each force field contributes a vector to the acceleration, summed together.

**Resolution**: Forces are additive: total_acceleration = gravity + attractor_force + vortex_force + turbulence_force. Then `vel += total_acceleration * dt`.

### [NEEDS RESEARCH]: What is the exact vertex attribute layout and VBO update pattern?

**Finding**: The legacy shows separate VBOs for pos, color, props. The update likely uses `glBufferSubData` or `glMapBuffer` to upload only active particles. There may be a `dirty` flag to avoid uploading if no changes.

**Resolution**: We'll define that the system updates all VBOs every frame after physics. It uses `glBufferData` with `GL_DYNAMIC_DRAW` to upload the full arrays (or only active portion using `glBufferSubData`). The vertex format:
- location 0: vec3 position
- location 1: vec4 color
- location 2: vec4 props (life, size, rotation, unused)

### [NEEDS RESEARCH]: How is the MVP matrix computed and set?

**Finding**: The system has camera parameters and likely computes a view-projection matrix. The skeleton spec doesn't mention a render method that takes a matrix. We need to define the interface.

**Resolution**: Add a `set_camera(position, target, up, fov)` method and a `set_projection_matrix(proj)` method, or compute internally. The `render()` method will use the current camera and projection to set the `mvp_matrix` uniform. We'll include these in the public interface.

---

## Configuration Schema

```python
METADATA = {
  "params": [
    # System limits
    {"id": "max_particles", "name": "Max Particles", "default": 10000, "min": 100, "max": 100000, "type": "int", "description": "Maximum number of particles the system can manage"},
    {"id": "num_particles", "name": "Initial Particles", "default": 2000, "min": 1, "max": 10000, "type": "int", "description": "Number of particles to emit initially (or per frame?) Actually this is emit_rate"},
    
    # Physics
    {"id": "gravity", "name": "Gravity", "default": (0.0, -0.05, 0.0), "type": "vec3", "description": "Gravity vector applied to all particles"},
    {"id": "drag", "name": "Drag", "default": 0.98, "min": 0.9, "max": 1.0, "type": "float", "description": "Velocity damping per frame (1.0 = no drag)"},
    {"id": "turbulence_strength", "name": "Turbulence Strength", "default": 0.5, "min": 0.0, "max": 5.0, "type": "float"},
    {"id": "turbulence_scale", "name": "Turbulence Scale", "default": 1.0, "min": 0.1, "max": 10.0, "type": "float"},
    {"id": "turbulence_speed", "name": "Turbulence Speed", "default": 0.5, "min": 0.0, "max": 5.0, "type": "float"},
    
    # Emitter
    {"id": "emit_rate", "name": "Emit Rate", "default": 50, "min": 0, "max": 1000, "type": "int", "description": "Particles emitted per frame"},
    {"id": "emit_position", "name": "Emit Position", "default": (0.0, 0.0, 0.0), "type": "vec3"},
    {"id": "emit_radius", "name": "Emit Radius", "default": 0.5, "min": 0.0, "max": 10.0, "type": "float"},
    {"id": "emit_velocity", "name": "Emit Velocity", "default": (0.0, 1.0, 0.0), "type": "vec3"},
    {"id": "emit_spread", "name": "Emit Spread", "default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
    {"id": "particle_life_min", "name": "Life Min", "default": 2.0, "min": 0.1, "max": 60.0, "type": "float"},
    {"id": "particle_life_max", "name": "Life Max", "default": 5.0, "min": 0.1, "max": 60.0, "type": "float"},
    {"id": "particle_size_start", "name": "Size Start", "default": 1.0, "min": 0.1, "max": 100.0, "type": "float"},
    {"id": "particle_size_end", "name": "Size End", "default": 0.0, "min": 0.0, "max": 100.0, "type": "float"},
    
    # Visual
    {"id": "color_start", "name": "Color Start", "default": (1.0, 1.0, 1.0, 1.0), "type": "vec4"},
    {"id": "color_end", "name": "Color End", "default": (0.0, 0.5, 1.0, 0.0), "type": "vec4"},
    {"id": "blend_mode_src", "name": "Blend Src", "default": GL_SRC_ALPHA, "type": "int"},
    {"id": "blend_mode_dst", "name": "Blend Dst", "default": GL_ONE, "type": "int"},
    {"id": "point_size", "name": "Point Size", "default": 5.0, "min": 1.0, "max": 100.0, "type": "float"},
    {"id": "use_texture", "name": "Use Texture", "default": False, "type": "bool"},
    {"id": "render_mode", "name": "Render Mode", "default": 0, "min": 0, "max": 3, "type": "int", "description": "0=Points, 1=Textured, 2=Lines, 3=Mesh"},
    
    # Audio
    {"id": "audio_sensitivity", "name": "Audio Sensitivity", "default": 1.0, "min": 0.0, "max": 5.0, "type": "float"},
    {"id": "beat_multiplier", "name": "Beat Multiplier", "default": 2.0, "min": 0.5, "max": 3.0, "type": "float"},
    {"id": "spectrum_influence", "name": "Spectrum Influence", "default": 0.5, "min": 0.0, "max": 1.0, "type": "float"},
    
    # Force Fields
    {"id": "attractor_pos", "name": "Attractor Position", "default": (0.0, 0.0, 0.0), "type": "vec3"},
    {"id": "attractor_strength", "name": "Attractor Strength", "default": 0.0, "min": 0.0, "max": 10.0, "type": "float"},
    {"id": "vortex_strength", "name": "Vortex Strength", "default": 0.0, "min": 0.0, "max": 10.0, "type": "float"},
    {"id": "vortex_axis", "name": "Vortex Axis", "default": (0.0, 1.0, 0.0), "type": "vec3"},
    
    # Camera
    {"id": "camera_position", "name": "Camera Position", "default": (0.0, 0.0, 5.0), "type": "vec3"},
    {"id": "camera_target", "name": "Camera Target", "default": (0.0, 0.0, 0.0), "type": "vec3"},
    {"id": "camera_up", "name": "Camera Up", "default": (0.0, 1.0, 0.0), "type": "vec3"},
    {"id": "fov", "name": "Field of View", "default": 60.0, "min": 10.0, "max": 120.0, "type": "float"},
  ]
}
```

---

## State Management

- **Per-frame state**: `active_count`, particle arrays (pos, vel, life, props, colors) are updated each `update(dt)`.
- **Persistent state**: All configuration parameters (gravity, drag, emitter settings, force fields, camera, audio sensitivity, visual params). These can be changed at runtime.
- **Init-once state**: OpenGL objects (VAO, VBOs, shader program, texture). Initialized in `__init__` or first `update`.
- **Thread safety**: Not thread-safe. `update()` and `render()` must be called from the same thread with an active OpenGL context.

---

## GPU Resources

This effect is **GPU-accelerated** and requires OpenGL 3.3+. It uses:

- **Vertex shader**: Transforms particles, applies audio displacement, computes point size.
- **Fragment shader**: Outputs particle color, optionally samples texture.
- **VAO + 3 VBOs**: For position (vec3), color (vec4), props (vec4).
- **Texture**: Optional particle sprite (if `use_texture=True`).
- **Uniforms**: mvp_matrix, time, audio features, texture flags.

If GPU resources are exhausted, the effect should raise an exception during initialization.

---

## Public Interface

```python
class AdvancedParticle3DSystem:
    def __init__(self, max_particles: int = 10000, initial_count: int = 2000) -> None:
        """
        Initialize the particle system.
        
        Args:
            max_particles: Maximum number of particles the system can manage
            initial_count: Initial number of particles to allocate (default 2000)
        """
    
    def update(self, dt: float) -> None:
        """
        Update particle physics and emit new particles.
        
        Args:
            dt: Time delta in seconds
        """
    
    def render(self) -> None:
        """Render active particles using the current shader and camera."""
    
    def set_emitter_position(self, x: float, y: float, z: float) -> None:
        """Set the emitter position."""
    
    def set_emitter_parameters(self, radius: float, velocity: Tuple[float, float, float], spread: float) -> None:
        """Set emitter shape and velocity."""
    
    def set_emit_rate(self, rate: int) -> None:
        """Set particles emitted per frame."""
    
    def set_force_field_attractor(self, pos: Tuple[float, float, float], strength: float) -> None:
        """Set an attractor force field."""
    
    def set_force_field_vortex(self, axis: Tuple[float, float, float], strength: float, center: Tuple[float, float, float] = (0,0,0)) -> None:
        """Set a vortex force field."""
    
    def set_turbulence(self, strength: float, scale: float, speed: float) -> None:
        """Set turbulence parameters."""
    
    def set_gravity(self, gravity: Tuple[float, float, float]) -> None:
        """Set gravity vector."""
    
    def set_drag(self, drag: float) -> None:
        """Set drag coefficient (0.9-1.0)."""
    
    def set_particle_lifetime(self, min: float, max: float) -> None:
        """Set particle lifetime range."""
    
    def set_particle_size(self, start: float, end: float) -> None:
        """Set particle size interpolation."""
    
    def set_particle_color(self, start: Tuple[float, float, float, float], end: Tuple[float, float, float, float]) -> None:
        """Set color interpolation (RGBA)."""
    
    def set_audio_reactivity(self, sensitivity: float, beat_multiplier: float, spectrum_influence: float) -> None:
        """
        Configure audio reactivity.
        
        Args:
            sensitivity: Overall audio influence multiplier
            beat_multiplier: Emission boost on beat detection
            spectrum_influence: How much frequency spectrum affects particles
        """
    
    def set_audio_features(self, bass: float, mid: float, treble: float, beat: float) -> None:
        """
        Provide current audio features (call each frame before update/render).
        
        Args:
            bass: Low-frequency energy (0.0-1.0)
            mid: Mid-frequency energy (0.0-1.0)
            treble: High-frequency energy (0.0-1.0)
            beat: Beat detection strength (0.0 or 1.0)
        """
    
    def set_camera(self, position: Tuple[float, float, float], target: Tuple[float, float, float], up: Tuple[float, float, float], fov: float) -> None:
        """Set camera parameters for MVP matrix computation."""
    
    def set_projection_matrix(self, proj: np.ndarray) -> None:
        """Set projection matrix (4x4). Alternatively, compute from fov and aspect."""
    
    def set_render_mode(self, mode: int) -> None:
        """Set render mode: 0=Points, 1=Textured, 2=Lines, 3=Mesh."""
    
    def set_texture(self, texture_id: int) -> None:
        """Set OpenGL texture ID for particle sprite (if use_texture=True)."""
    
    def enable(self, enabled: bool) -> None:
        """Enable or disable the entire system (pause emission and physics)."""
    
    def get_particle_count(self) -> int:
        """Return current number of active particles."""
    
    def get_metadata(self) -> dict:
        """Return effect metadata for UI."""
        return {
            "tags": ["particles", "3d", "physics", "audio-reactive", "generative"],
            "mood": ["energetic", "dynamic", "immersive"],
            "visual_style": ["point-cloud", "flow", "explosive"]
        }
    
    def stop(self) -> None:
        """Release OpenGL resources and clean up."""
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `dt` | `float` | Time delta for physics update | Must be ≥ 0.0 |
| `x, y, z` | `float` | Emitter position coordinates | Typically in range [-10, 10] |
| `pos` | `(float, float, float)` | Attractor/vortex position | Same range |
| `strength` | `float` | Force field strength | ≥ 0.0, max ~10.0 |
| `radius` | `float` | Emitter radius | ≥ 0.0 |
| `velocity` | `(float, float, float)` | Emit velocity vector | Any |
| `spread` | `float` | Emit spread randomness | [0.0, 1.0] |
| `rate` | `int` | Emit rate (particles per frame) | [0, 1000] |
| `life_min`, `life_max` | `float` | Particle lifetime range (seconds) | ≥ 0.1 |
| `size_start`, `size_end` | `float` | Particle size at spawn/death | ≥ 0.0 |
| `color_start`, `color_end` | `(float, float, float, float)` | RGBA colors | components [0,1] |
| `gravity` | `(float, float, float)` | Gravity vector | Any |
| `drag` | `float` | Velocity damping per frame | [0.9, 1.0] |
| `turbulence_strength`, `scale`, `speed` | `float` | Turbulence parameters | strength ≥ 0, scale > 0, speed ≥ 0 |
| `audio_sensitivity`, `beat_multiplier`, `spectrum_influence` | `float` | Audio reactivity params | sensitivity [0,5], beat_mult [0.5,3], spectrum [0,1] |
| `bass, mid, treble, beat` | `float` | Audio features (0.0-1.0) | beat is 0 or 1 typically |
| `camera_position`, `target`, `up` | `(float, float, float)` | Camera parameters | any |
| `fov` | `float` | Camera field of view (degrees) | [10, 120] |
| `proj` | `np.ndarray[4x4]` | Projection matrix | Must be valid 4x4 float32 |
| `texture_id` | `int` | OpenGL texture ID | Must be valid GL texture |
| `enabled` | `bool` | System active state | - |
| `max_particles` | `int` | Maximum capacity | [100, 100000] |
| `return` (from get_particle_count) | `int` | Active particle count | ≤ max_particles |

---

## Dependencies

- External libraries:
  - `numpy` — required for particle array operations
  - `OpenGL.GL` — required for rendering
- Internal modules:
  - `vjlive3.core.effects.shader_base.Effect` — base class providing shader compilation
  - `vjlive3.core.audio_analyzer.AudioAnalyzer` — optional, for audio features
  - `vjlive3.utils.math_utils` — for matrix math, noise functions

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

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT206: particles_3d implementation` message
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
        
        # System Limits
        self.max_particles = 10000
        self.num_particles = 2000
        self.enabled = True
        self.initialized = False
```

### vjlive1/core/generators/particles_3d.py (L17-36)
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

### vjlive1/core/generators/particles_3d.py (L33-52)
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

### vjlive1/core/generators/particles_3d.py (L49-68)
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
        self.fov = 60.0
        
        # Particle Data Arrays (CPU side for logic)
        # Structure: [x, y, z, vx, vy, vz, life, max_life, size, r, g, b, a, angle]
        # Optimized with separate arrays for numpy speed
        self.pos = np.zeros((self.max_particles, 3), dtype=np.float32)
        self.vel = np.zeros((self.max_particles, 3), dtype=np.float32)
        self.life = np.zeros(self.max_particles, dtype=np.float32)
        self.props = np.zeros((self.max_particles, 4), dtype=np.float32) # max_life, size_start, size_now, rotation
```

### vjlive1/core/generators/particles_3d.py (L65-84)
```python
        self.pos = np.zeros((self.max_particles, 3), dtype=np.float32)
        self.vel = np.zeros((self.max_particles, 3), dtype=np.float32)
        self.life = np.zeros(self.max_particles, dtype=np.float32)
        self.props = np.zeros((self.max_particles, 4), dtype=np.float32) # max_life, size_start, size_now, rotation
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

### vjlive1/core/generators/particles_3d.py (L81-100)
```python
        self.use_textures = False
        
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

### vjlive1/core/generators/particles_3d.py (L97-116)
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

### vjlive1/core/generators/particles_3d.py (L113-132)
```python
            vec4 col = v_color;
            
            if (use_texture > 0.5 && render_mode == 1) {
                // Textured point sprite
                vec2 uv = gl_PointCoord;
                // Apply rotation to uv if needed
                col = texture(particle_texture, uv) * v_color;
            } else {
                // Simple circular point
                vec2 uv = gl_PointCoord - vec2(0.5);
                float dist = length(uv);
                if (dist > 0.5) discard;
                col.a *= 1.0 - dist*2.0;
            }
            
            // Fade based on life
            col.a *= v_life;  // Assuming life is normalized 0-1? Actually life is remaining life; need to normalize by max_life
            fragColor = col;
        }
        """
```

[NEEDS RESEARCH]: The full update() method and VBO update logic are not shown in the snippets. The spec assumes a typical implementation but the exact details (e.g., how inactive particles are tracked, whether a free list is used) should be verified. Additionally, the fragment shader's life fading uses `v_life` directly; but `v_life` is the remaining life, not normalized. The shader likely expects normalized life (0-1). The CPU should pass normalized life in props.x, or the shader should divide by max_life (which is also in props). This needs clarification.
