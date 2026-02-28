# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD41_DepthParticle3DEffect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD41 — DepthParticle3DEffect

## Description

The DepthParticle3DEffect is a 3D particle system that emits particles from depth surfaces, creating dynamic volumetric effects that respond to the geometry of the scene. Particles are spawned at depth pixels corresponding to objects, with initial velocities and colors. They then evolve according to physics (gravity, damping, depth attraction) before fading away. The effect can also emit particles from areas of motion (depth changes), adding an extra layer of reactivity.

This effect transforms static depth data into a living, breathing particle cloud that swirls around objects, falls under gravity, and is attracted back to the depth surfaces. It's ideal for creating magical auras, floating debris, or ethereal particle trails that follow people and objects in the depth field.

## What This Module Does

- Emits particles from depth map pixels where objects are present
- Optionally emits particles from regions with depth motion
- Simulates particle physics: gravity, damping, depth attraction
- Manages particle lifecycle (spawn, update, death, respawn)
- Renders particles as 3D point sprites with size and color
- Supports configurable particle count, size, lifetime, emission rate
- Integrates with `DepthEffect` base class for depth source
- GPU-accelerated using vertex buffers and point sprite rendering

## What This Module Does NOT Do

- Does NOT support particle collisions (particles pass through each other)
- Does NOT implement spatial partitioning (O(N) update, N = particle count)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT handle particle texturing (only solid color points)
- Does NOT support particle forces beyond gravity and depth attraction
- Does NOT implement LOD (all particles rendered at same size)

---

## Detailed Behavior

### Particle Emission

Particles are emitted from depth pixels based on two modes:

1. **Object emission** (`emit_from_objects`): Sample depth map at regular intervals (or randomly). For each sampled pixel with valid depth (and optionally depth within range), spawn a particle at that 3D position. The particle's initial velocity can be random or outward from surface.

2. **Motion emission** (`emit_from_motion`): Compare current depth frame with previous frame. Compute absolute difference. Where difference exceeds `emit_threshold`, spawn particles. This creates particles from moving objects.

Emission rate controls how many particles are spawned per frame (or per second). The system maintains a pool of up to `max_particles` particles. When a particle dies (lifetime expires), it is respawned immediately if emission is active.

### Particle Physics

Each particle has:
- Position `p` (vec3)
- Velocity `v` (vec3)
- Lifetime `t` (float, seconds)
- Color `c` (vec4)

Per-frame update (dt = 1/60 s):

```python
# Apply gravity
v += gravity * dt

# Apply damping (air resistance)
v *= damping

# Depth attraction: pull particles toward nearest depth surface
if depth_frame is not None:
    # Sample depth at particle's projected 2D position
    u = int(p.x * fx + cx)
    v = int(p.y * fy + cy)
    if in_bounds(u, v):
        surface_z = depth_frame[v, u]
        if surface_z valid:
            # Convert to world
            surface_world = project_to_world(u, v, surface_z)
            # Attract toward surface (simple spring)
            force = (surface_world - p) * depth_attraction
            v += force * dt

# Update position
p += v * dt

# Age particle
t -= dt
```

If `t <= 0`, particle dies and is respawned.

### 3D Position from Depth

When spawning a particle at depth pixel (u, v) with depth value `d`:

```
z = near_clip + d * (far_clip - near_clip)
x = (u - cx) * z / fx
y = (v - cy) * z / fy
```

This gives 3D position in camera space. Optionally apply a model-view-projection matrix for rendering.

### Rendering

Particles are rendered as point sprites using `GL_POINTS`:

- Vertex shader computes `gl_Position` from particle position
- Sets `gl_PointSize` based on `particle_size` parameter (can be attenuated by distance)
- Fragment shader draws a circular point (discard corners) and applies particle color

**Vertex Shader**:
```glsl
uniform mat4 u_mvp;
uniform float u_point_size;
uniform float u_near_clip, u_far_clip;  // For size attenuation

in vec3 a_position;
in vec4 a_color;
in float a_lifetime;  // Could modulate alpha

out vec4 v_color;

void main() {
    gl_Position = u_mvp * vec4(a_position, 1.0);
    gl_PointSize = u_point_size;
    // Optional: size attenuation
    // float dist = length(camera_space_position);
    // gl_PointSize = u_point_size * (u_near_clip / max(dist, 0.1));
    v_color = a_color;
}
```

**Fragment Shader**:
```glsl
in vec4 v_color;
out vec4 frag_color;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) discard;  // Circle
    frag_color = v_color;
}
```

### Particle Color

Particles can have colors based on:
- Depth (near vs far)
- Velocity
- Lifetime (age)
- Random

The legacy implementation likely uses depth-based coloring: near particles are one color, far particles another, or a gradient.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `max_particles` | int | 10000 | 1000-50000 | Maximum number of particles (pool size) |
| `num_particles` | int | 0 (auto) | 0-max_particles | Active particle count (0 = use all) |
| `particle_size` | float | 2.0 | 0.5-20.0 | Point size in pixels |
| `particle_lifetime` | float | 3.0 | 0.1-10.0 | Particle lifetime in seconds |
| `emit_from_objects` | bool | True | — | Emit particles from depth objects |
| `emit_from_motion` | bool | True | — | Emit particles from motion |
| `emit_threshold` | float | 0.1 | 0.01-1.0 | Motion detection threshold (depth diff) |
| `particles_per_object` | int | 10 | 1-100 | Particles per emission event |
| `emission_rate` | float | 100.0 | 10.0-1000.0 | Particles emitted per second |
| `gravity_x`, `gravity_y`, `gravity_z` | float | 0.0, -0.001, 0.0 | any | Gravity vector |
| `damping` | float | 0.98 | 0.9-1.0 | Velocity damping per second |
| `depth_attraction` | float | 0.5 | 0.0-2.0 | Strength of attraction to depth surfaces |

---

## Public Interface

```python
class DepthParticle3DEffect(DepthEffect):
    def __init__(self) -> None: ...
    def set_max_particles(self, n: int) -> None: ...
    def get_max_particles(self) -> int: ...
    def set_particle_size(self, size: float) -> None: ...
    def get_particle_size(self) -> float: ...
    def set_particle_lifetime(self, lifetime: float) -> None: ...
    def get_particle_lifetime(self) -> float: ...
    def set_emit_from_objects(self, enabled: bool) -> None: ...
    def get_emit_from_objects(self) -> bool: ...
    def set_emit_from_motion(self, enabled: bool) -> None: ...
    def get_emit_from_motion(self) -> bool: ...
    def set_emit_threshold(self, threshold: float) -> None: ...
    def get_emit_threshold(self) -> float: ...
    def set_particles_per_object(self, n: int) -> None: ...
    def get_particles_per_object(self) -> int: ...
    def set_emission_rate(self, rate: float) -> None: ...
    def get_emission_rate(self) -> float: ...
    def set_gravity(self, x: float, y: float, z: float) -> None: ...
    def get_gravity(self) -> Tuple[float, float, float]: ...
    def set_damping(self, damping: float) -> None: ...
    def get_damping(self) -> float: ...
    def set_depth_attraction(self, strength: float) -> None: ...
    def get_depth_attraction(self) -> float: ...
    def render_3d_depth_scene(self, resolution: Tuple[int, int], time: float) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (optional) |
| **Output** | `np.ndarray` | Rendered particles (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_max_particles: int` — Pool size
- `_particle_size: float` — Point size
- `_particle_lifetime: float` — Max lifetime
- `_emit_from_objects: bool` — Object emission enabled
- `_emit_from_motion: bool` — Motion emission enabled
- `_emit_threshold: float` — Motion threshold
- `_particles_per_object: int` — Emission batch size
- `_emission_rate: float` — Particles per second
- `_gravity: np.ndarray` — Gravity vector (3)
- `_damping: float` — Damping factor
- `_depth_attraction: float` — Attraction strength
- `_positions: np.ndarray` — (max_particles, 3) float32
- `_velocities: np.ndarray` — (max_particles, 3) float32
- `_lifetimes: np.ndarray` — (max_particles,) float32
- `_colors: np.ndarray` — (max_particles, 4) float32
- `_num_particles: int` — Currently active count
- `_prev_depth_frame: Optional[np.ndarray]` — For motion detection
- `_vao: int` — Vertex array
- `_vbo_positions: int` — Position buffer
- `_vbo_colors: int` — Color buffer
- `_shader: ShaderProgram` — Shader

**Per-Frame:**
- Update particle physics (positions, velocities, lifetimes)
- Emit new particles based on depth and motion
- Upload position and color buffers to GPU
- Render with `glDrawArrays(GL_POINTS, ...)`

**Initialization:**
- Allocate particle arrays of size `max_particles`
- Initialize all lifetimes to 0 (dead)
- Create VAO, VBOs
- Compile shader
- Default parameters as above

**Cleanup:**
- Delete VAO, VBOs
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| VAO | GL_VERTEX_ARRAY | — | 1 | Init, persists |
| VBO positions | GL_ARRAY_BUFFER | vec3 (float32) | max_particles | Init, updated each frame |
| VBO colors | GL_ARRAY_BUFFER | vec4 (float32) | max_particles | Init, updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (max_particles=10000):**
- Positions: 10000 × 12 bytes = 120 KB
- Colors: 10000 × 16 bytes = 160 KB
- Total: ~280 KB (very lightweight)

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Skip emission, particles drift | Normal operation |
| Motion detection fails (no prev) | Skip motion emission | Store prev for next frame |
| Buffer upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Particle count exceeds max | Clamp emission rate or increase max | Adjust parameters |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and particle array mutations must occur on the thread with the OpenGL context. The `_positions`, `_velocities`, `_lifetimes`, `_colors` arrays are mutated each frame, and the VBOs are updated, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (max_particles=10000):**
- Particle update (CPU, O(N)): ~1-2 ms
- Emission (sampling depth): ~0.5-1 ms
- Buffer upload (2 VBOs): ~0.5-1 ms
- Rendering (GL_POINTS, 10000 points): ~0.5-1 ms
- Total: ~2.5-5 ms on CPU+GPU

**Scaling**: Linear with particle count. 50000 particles may take 10-15 ms.

**Optimization Strategies:**
- Reduce `max_particles` if not all used
- Emit only from regions of interest (e.g., center, or depth threshold)
- Downsample depth for emission sampling
- Use `glMapBuffer` with `GL_MAP_UNSYNCHRONIZED` for async buffer updates
- Consider compute shader for particle update (GPU-side) for very high counts

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Camera intrinsics set (fx, fy, cx, cy)
- [ ] Depth range (min_depth, max_depth) configured
- [ ] Particle parameters set (count, size, lifetime, etc.)
- [ ] Physics parameters set (gravity, damping, attraction)
- [ ] Emission modes selected (objects, motion)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_max_particles` | Max particles can be set and clamped |
| `test_set_particle_size` | Size updates |
| `test_set_particle_lifetime` | Lifetime updates |
| `test_set_emit_from_objects` | Object emission toggle |
| `test_set_emit_from_motion` | Motion emission toggle |
| `test_set_emit_threshold` | Threshold updates |
| `test_set_emission_rate` | Rate updates |
| `test_set_gravity` | Gravity vector updates |
| `test_set_damping` | Damping updates |
| `test_set_depth_attraction` | Attraction strength updates |
| `test_particle_emit_objects` | Particles spawn from depth objects |
| `test_particle_emit_motion` | Particles spawn from motion |
| `test_particle_physics` | Gravity, damping, attraction affect motion |
| `test_particle_lifetime` | Particles die after lifetime expires |
| `test_particle_respawn` | Dead particles respawn when emission active |
| `test_update_buffers` | Position and color buffers updated correctly |
| `test_render_particles` | Renders visible points |
| `test_motion_detection` | Depth difference computed correctly |
| `test_depth_attraction` | Particles move toward depth surfaces |
| `test_cleanup` | All GPU resources released |
| `test_no_memory_leak` | Repeated init/cleanup cycles don't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD41: depth_particle_3d_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/depth/particles.py` — VJLive-2 implementation of `DepthParticle3DEffect`
- `plugins/vdepth/depth_effects.py` — Registers `DepthParticle3DEffect` in `DEPTH_EFFECTS`
- `gl_leaks.txt` — Shows `DepthParticle3DEffect` allocates `glGenVertexArrays`, `glGenBuffers` and must free them
- `core/effects/particle_datamosh_trails.py` — Extends `DepthParticle3DEffect` for datamosh trails

Design decisions inherited:
- Effect name: `depth_particles_3d`
- Inherits from `DepthEffect`
- Uses CPU-side particle simulation (positions, velocities, lifetimes)
- Renders with `GL_POINTS` using separate VBOs for positions and colors
- Parameters: `max_particles`, `particle_size`, `particle_lifetime`, `emit_from_objects`, `emit_from_motion`, `emit_threshold`, `particles_per_object`, `emission_rate`, `gravity`, `damping`, `depth_attraction`
- Allocates GL resources: VAO, VBO (positions), VBO (colors)
- Supports dynamic resizing of particle arrays

---

## Notes for Implementers

1. **Particle Representation**: Use numpy arrays for efficient CPU-side simulation:
   ```python
   self._positions = np.zeros((max_particles, 3), dtype=np.float32)
   self._velocities = np.zeros((max_particles, 3), dtype=np.float32)
   self._lifetimes = np.zeros(max_particles, dtype=np.float32)
   self._colors = np.zeros((max_particles, 4), dtype=np.float32)
   ```

2. **Particle Pool**: Use a fixed-size pool. Keep track of active count (`_num_particles`). When emitting, find dead particles (lifetime <= 0) and respawn them. If all particles are active, you can either skip emission or respawn oldest.

3. **Emission from Objects**: Sample depth map at grid points or random locations:
   ```python
   for _ in range(emission_count):
       u = random.randint(0, width-1)
       v = random.randint(0, height-1)
       d = depth_frame[v, u]
       if d > 0 and not np.isnan(d):
           # Spawn particle
           pos = project_to_world(u, v, d)
           vel = random_direction() * initial_speed
           lifetime = particle_lifetime * random.uniform(0.8, 1.2)
           color = depth_to_color(d)
           # Assign to a particle slot
   ```

4. **Emission from Motion**: Compute absolute depth difference:
   ```python
   if self._prev_depth_frame is not None:
       diff = np.abs(depth_frame - self._prev_depth_frame)
       mask = diff > emit_threshold
       # Find nonzero pixels in mask, spawn particles there
   self._prev_depth_frame = depth_frame.copy()
   ```

5. **Depth Attraction**: For each particle, you need to find the nearest depth surface. Simplest: sample depth at particle's projected 2D coordinates. This gives the surface depth at that (x,y). Compute force as `(surface_world - particle_pos) * strength`. This pulls particles toward the surface directly below them.

   More advanced: use a 3D distance field or search nearby pixels. But sampling depth texture is fast.

6. **GPU Upload**: After updating particle arrays, upload to VBOs:
   ```python
   glBindBuffer(GL_ARRAY_BUFFER, self._vbo_positions)
   glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_DYNAMIC_DRAW)
   glBindBuffer(GL_ARRAY_BUFFER, self._vbo_colors)
   glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_DYNAMIC_DRAW)
   ```
   Use `GL_DYNAMIC_DRAW` hint.

7. **Rendering**: Use `glDrawArrays(GL_POINTS, 0, num_active_particles)`. Ensure VAO is bound and shader active.

8. **Point Size**: Set `gl_PointSize` in vertex shader. Can be constant or attenuated by distance. If using attenuation, compute distance in camera space and divide.

9. **Color**: Could be based on depth, velocity, or lifetime. The legacy likely uses depth-based coloring. Implement a simple mapping:
   ```python
   t = (depth - min_depth) / (max_depth - min_depth)
   color = (t, 0.5, 1.0-t, 1.0)  # RGBA
   ```

10. **Performance**: The CPU simulation is O(N). For 10K particles, it's fine. For 50K, may be borderline on Python. Consider using Numba or Cython if needed, or move simulation to GPU via transform feedback/compute shader.

11. **Memory**: The particle arrays are small (280 KB for 10K). No issue.

12. **Testing**: Create a synthetic depth map (e.g., a sphere) and verify particles emit from its surface. Test gravity by checking particles fall. Test depth attraction by placing a depth surface and seeing particles move toward it.

13. **Debugging**: Provide debug mode that renders particles as larger points or with different colors based on state (e.g., red for dead, green for alive). Also visualize emission sources.

14. **Future Extensions**:
    - Add particle textures (sprite sheets)
    - Add forces: wind, vortex, noise
    - Add collision with depth surfaces (kill or bounce)
    - Add particle size variation
    - Add color gradients over lifetime
    - Use geometry shader to expand points into quads with orientation

---

## Easter Egg Idea

When `max_particles` is set exactly to 1337, `particle_lifetime` to exactly 6.66, `gravity` to exactly (0, 0, 0), and `depth_attraction` to exactly 1.618, and the depth map contains a perfect sphere, the particles spontaneously arrange themselves into a perfect Fibonacci sphere distribution that rotates slowly for exactly 6.66 seconds before returning to normal behavior. The particles glow with a golden hue during this time, creating a "sacred geometry" moment that VJs can feel as a harmonic convergence.

---

## References

- Particle systems: https://developer.nvidia.com/gpugems/GPUGems3/gpugems3_ch16.html
- OpenGL point sprites: https://learnopengl.com/Advanced-OpenGL/Point-Sprites
- Depth-based particle emission: VJLive legacy `core/effects/depth/particles.py`
- Physics integration: Euler method (simple) vs RK4 (advanced)

---

## Implementation Tips

1. **Particle Update Loop**:
   ```python
   def _update_particles(self, dt):
       # Apply physics
       self._velocities[:self._num_particles] += self._gravity * dt
       self._velocities[:self._num_particles] *= self._damping
       
       # Depth attraction
       if self._depth_attraction > 0 and self.depth_frame is not None:
           for i in range(self._num_particles):
               pos = self._positions[i]
               # Project to 2D
               u = int((pos.x * self._fx) + self._cx)
               v = int((pos.y * self._fy) + self._cy)
               if 0 <= u < width and 0 <= v < height:
                   d = self.depth_frame[v, u]
                   if d > 0:
                       surface_z = self._near_clip + d * (self._far_clip - self._near_clip)
                       surface_x = (u - self._cx) * surface_z / self._fx
                       surface_y = (v - self._cy) * surface_z / self._fy
                       force = np.array([surface_x, surface_y, surface_z]) - pos
                       self._velocities[i] += force * self._depth_attraction * dt
       
       # Integrate
       self._positions[:self._num_particles] += self._velocities[:self._num_particles] * dt
       self._lifetimes[:self._num_particles] -= dt
       
       # Kill dead particles
       dead = np.where(self._lifetimes[:self._num_particles] <= 0)[0]
       for idx in dead:
           self._num_particles -= 1
           # Swap with last active particle to keep array compact
           if idx < self._num_particles:
               self._positions[idx] = self._positions[self._num_particles]
               self._velocities[idx] = self._velocities[self._num_particles]
               self._lifetimes[idx] = self._lifetimes[self._num_particles]
               self._colors[idx] = self._colors[self._num_particles]
   ```

2. **Emission**:
   ```python
   def _emit_particles(self, dt):
       if not (self._emit_from_objects or self._emit_from_motion):
           return
       
       # Compute how many to emit this frame
       emit_count = int(self._emission_rate * dt)
       
       # Object emission: sample depth grid
       if self._emit_from_objects:
           step = max(1, int(np.sqrt(self._max_particles / emit_count)))  # coarse grid
           for v in range(0, height, step):
               for u in range(0, width, step):
                   if emit_count <= 0: break
                   d = self.depth_frame[v, u]
                   if d > 0 and not np.isnan(d):
                       self._spawn_particle(u, v, d)
                       emit_count -= 1
       
       # Motion emission
       if self._emit_from_motion and self._prev_depth_frame is not None:
           diff = np.abs(self.depth_frame - self._prev_depth_frame)
           # Find pixels above threshold (could use np.where)
           # For each, spawn particle
           # ...
       
       self._prev_depth_frame = self.depth_frame.copy()
   ```

3. **Spawn Particle**:
   ```python
   def _spawn_particle(self, u, v, depth):
       if self._num_particles >= self._max_particles:
           # Recycle oldest (or skip)
           return
       
       # 3D position
       z = self._near_clip + depth * (self._far_clip - self._near_clip)
       x = (u - self._cx) * z / self._fx
       y = (v - self._cy) * z / self._fy
       
       # Velocity: small random outward or upward
       vel = np.random.uniform(-0.001, 0.001, 3)
       
       # Lifetime with variation
       lifetime = self._particle_lifetime * np.random.uniform(0.8, 1.2)
       
       # Color based on depth
       t = (depth - self.min_depth) / (self.max_depth - self.min_depth)
       color = np.array([t, 0.5, 1.0-t, 1.0], dtype=np.float32)
       
       # Assign to next slot
       idx = self._num_particles
       self._positions[idx] = [x, y, z]
       self._velocities[idx] = vel
       self._lifetimes[idx] = lifetime
       self._colors[idx] = color
       self._num_particles += 1
   ```

4. **Buffer Update**:
   ```python
   def _upload_buffers(self):
       glBindBuffer(GL_ARRAY_BUFFER, self._vbo_positions)
       glBufferData(GL_ARRAY_BUFFER, self._positions.nbytes, self._positions, GL_DYNAMIC_DRAW)
       glBindBuffer(GL_ARRAY_BUFFER, self._vbo_colors)
       glBufferData(GL_ARRAY_BUFFER, self._colors.nbytes, self._colors, GL_DYNAMIC_DRAW)
   ```

5. **Shader Setup**:
   ```python
   VERTEX_SHADER = """
   #version 330 core
   uniform mat4 u_mvp;
   uniform float u_point_size;
   layout(location=0) in vec3 a_position;
   layout(location=1) in vec4 a_color;
   out vec4 v_color;
   void main() {
       gl_Position = u_mvp * vec4(a_position, 1.0);
       gl_PointSize = u_point_size;
       v_color = a_color;
   }
   """
   FRAGMENT_SHADER = """
   #version 330 core
   in vec4 v_color;
   out vec4 frag_color;
   void main() {
       vec2 c = gl_PointCoord - vec2(0.5);
       if (length(c) > 0.5) discard;
       frag_color = v_color;
   }
   """
   ```

6. **VAO Setup**:
   ```python
   glGenVertexArrays(1, [self._vao])
   glBindVertexArray(self._vao)
   
   glGenBuffers(1, [self._vbo_positions])
   glBindBuffer(GL_ARRAY_BUFFER, self._vbo_positions)
   glEnableVertexAttribArray(0)
   glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
   
   glGenBuffers(1, [self._vbo_colors])
   glBindBuffer(GL_ARRAY_BUFFER, self._vbo_colors)
   glEnableVertexAttribArray(1)
   glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, None)
   
   glBindVertexArray(0)
   ```

7. **Resizing**: When `max_particles` changes, reallocate numpy arrays and optionally reallocate GPU buffers (or just let next upload resize).

8. **Depth Sampling**: For depth attraction, you need to sample the depth texture on CPU. You can either:
   - Keep a copy of depth frame as numpy array (already have it)
   - Or use `glGetTexImage` to read from GPU texture (slow)
   So keep CPU copy.

9. **Performance**: The per-particle depth attraction requires sampling depth frame for each particle. That's O(N) memory accesses. Could be slow if depth is large. Optimize by downsampling depth for attraction queries or using a spatial hash.

10. **Initial State**: All particles start dead (lifetime=0). They will be spawned as emission occurs.

---

## Conclusion

The DepthParticle3DEffect brings depth data to life by emitting a dynamic swarm of particles that interact with the scene. It's a versatile effect that can produce anything from subtle atmospheric particles to aggressive motion trails. With careful tuning of physics parameters, VJs can create captivating volumetric visuals that respond to the 3D structure of their performance space.

---
>>>>>>> REPLACE