# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD61_Depth_Particle_Shred.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD61 — DepthParticleShredEffect

## Description

The DepthParticleShredEffect converts depth camera data into a live particle cloud that can explode outward ("shred") and reassemble. It creates the dramatic body-disintegrating-into-particles look by converting the depth image into thousands of particles that can be animated with physics-like behavior. The effect uses depth data to position particles in 3D space, then applies forces to create explosive disintegration and gradual reassembly.

This effect is ideal for creating dramatic, physics-based particle effects that respond to depth. It's perfect for VJ performances that want to create the illusion of performers disintegrating into particles or for creating dynamic, depth-aware particle systems. The "shred" parameter controls the intensity of the explosion, while other parameters control particle size, velocity, color, and reassembly behavior.

## What This Module Does

- Converts depth image to 3D particle cloud
- Applies explosive "shred" force to particles
- Animates particles with velocity, gravity, and color shift
- Supports particle trails and reassembly
- GPU-accelerated with particle shader
- Configurable particle size, velocity, and physics parameters

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT include audio reactivity (may be added later)
- Does NOT support external particle systems (self-contained)
- Does NOT implement 3D physics engine (simplified particle motion)
- Does NOT include collision detection (particles pass through each other)
- Does NOT support particle lifetime management (particles persist)

---

## Detailed Behavior

### Particle Generation Pipeline

1. **Capture depth frame**: `depth_current` (HxW, 0-1 depth values)
2. **Sample depth points**: For each pixel (or sampled subset):
   - If depth > threshold, create particle
   - Particle position: `(x, y, depth)` in screen space
   - Particle color: sampled from video frame at `(x, y)`
3. **Store particle data**: Position, color, velocity (initially 0)
4. **Apply shred force**: If `shredAmount > 0`, add outward velocity:
   - Compute center of mass of particles
   - For each particle: `velocity = (position - center) * shredAmount`
5. **Animate particles**: Each frame:
   - Update position: `position += velocity`
   - Apply gravity: `velocity.y -= gravity`
   - Apply color shift: `color += colorShift * time`
   - Apply trail: blend with previous position
6. **Reassemble**: If `reassemble > 0`, gradually return particles to original positions
7. **Render particles**: Draw as points or small quads

### Shred Force Direction

The shred force is typically outward from the center of mass:
- Compute centroid: `center = mean(positions)`
- For each particle: `direction = normalize(position - center)`
- `velocity = direction * shredAmount * velocityScale`

Alternative: shred along Z-axis (depth), creating depth explosion.

### Particle Physics

- **Velocity**: Controlled by `shredAmount` and `velocityScale`
- **Gravity**: Constant downward acceleration (`gravity` parameter)
- **Color Shift**: Gradual color change over time (`colorShift` parameter)
- **Trail**: Particle leaves visual trail behind (`trailLength` parameter)
- **Reassembly**: Particles gradually return to original positions (`reassemble` parameter)

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `shredAmount` | float | 0.0 | 0.0-10.0 | Intensity of particle explosion |
| `particleSize` | float | 3.0 | 0.0-10.0 | Size of rendered particles |
| `velocityScale` | float | 5.0 | 0.0-10.0 | Multiplier for shred velocity |
| `colorShift` | float | 2.0 | 0.0-10.0 | Color change rate over time |
| `gravity` | float | 1.0 | 0.0-10.0 | Downward acceleration |
| `reassemble` | float | 5.0 | 0.0-10.0 | Rate of particle reassembly |
| `trailLength` | float | 0.0 | 0.0-10.0 | Length of particle trails |
| `particleDensity` | float | 5.0 | 0.0-10.0 | Sampling density (0=sparse, 10=dense) |
| `depthThreshold` | float | 2.0 | 0.0-10.0 | Minimum depth to create particle |
| `velocityNoise` | float | 1.0 | 0.0-10.0 | Random velocity variation |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthParticleShredEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def reset_particles(self) -> None: ...  # Clear all particles
    def trigger_shred(self) -> None:  # Force immediate shred
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) — also used for particle colors |
| **Output** | `np.ndarray` | Particle-shredded output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_particles: List[Particle]` — Active particles (position, color, velocity, original_position)
- `_particle_texture: int` — GL texture for particle data
- `_parameters: dict` — All particle parameters
- `_shader: ShaderProgram` — Compiled particle shader
- `_trail_texture: int` — For particle trails (if enabled)
- `_trail_fbo: int` — Framebuffer for trail rendering

**Per-Frame:**
- Update depth data from source
- Generate/update particles based on depth
- Apply shred force if active
- Animate particles (velocity, gravity, color shift)
- Render particles to screen
- Update trail texture if enabled
- Return result

**Initialization:**
- Create particle texture (dynamic)
- Create trail texture/FBO (if trail enabled)
- Compile particle shader
- Default parameters: shredAmount=0.0, particleSize=3.0, velocityScale=5.0, colorShift=2.0, gravity=1.0, reassemble=5.0, trailLength=0.0, particleDensity=5.0, depthThreshold=2.0, velocityNoise=1.0
- Initialize empty particle list

**Cleanup:**
- Delete particle texture
- Delete trail texture/FBO
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Particle texture | GL_TEXTURE_2D | GL_RGBA32F (vec4) | particle_count × 4 | Updated each frame |
| Trail texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame (if trail enabled) |
| Trail FBO | GL_FRAMEBUFFER | N/A | frame size | Persistent (if trail enabled) |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480, moderate density):**
- Particle texture: ~100-500 KB (depends on particle count)
- Trail texture: 921,600 bytes
- Shader: ~20-30 KB
- Total: ~1.1-1.4 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use zero depth (no particles) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and shader compilation must occur on the thread with the OpenGL context. The particle system updates particle positions and colors each frame, and concurrent `process_frame()` calls will cause race conditions and corrupted particle states. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Particle generation/update: ~2-5 ms (depends on particle count)
- Particle rendering: ~3-8 ms (depends on particle count and size)
- Trail update: ~1-2 ms (if enabled)
- Total: ~6.5-16 ms on GPU

**Optimization Strategies:**
- Reduce particle density for performance
- Use instanced rendering for particles
- Disable expensive features (trail, color shift)
- Use compute shader for particle physics
- Reduce particle size
- Use lower resolution for depth sampling

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Particle parameters configured
- [ ] Optional features configured (trail, reassemble, etc.)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_particle_generation` | Particles created from depth data |
| `test_shred_force` | Shred creates outward particle motion |
| `test_velocity_scale` | Shred velocity controlled by scale |
| `test_gravity` | Particles fall downward over time |
| `test_color_shift` | Particle colors change over time |
| `test_trail` | Particles leave visual trails |
| `test_reassemble` | Particles return to original positions |
| `test_particle_density` | Sampling density affects particle count |
| `test_depth_threshold` | Depth threshold filters particles |
| `test_velocity_noise` | Random velocity variation applied |
| `test_reset_particles` | Particle list can be cleared |
| `test_trigger_shred` | Immediate shred can be forced |
| `test_process_frame_no_depth` | Falls back to no particles |
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
- [ ] Git commit with `[Phase-3] P3-VD61: depth_particle_shred_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_particle_shred.py` — VJLive Original implementation
- `plugins/core/depth_particle_shred/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_particle_shred/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthParticleShredEffect` allocates `glGenTextures` and must free them
- `assets/gists/depth_particle_shred.json` — Gist documentation

Design decisions inherited:
- Effect name: `depth_particle_shred`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for particle positioning
- Parameters: `shredAmount`, `particleSize`, `velocityScale`, `colorShift`, `gravity`, `reassemble`, `trailLength`, `particleDensity`, `depthThreshold`, `velocityNoise`
- Allocates GL resources: particle texture, trail texture/FBO
- Shader implements particle generation, physics, and rendering
- Method `_ensure_gpu_resources()` creates GPU resources
- Method `_update_particles()` updates particle positions

---

## Notes for Implementers

1. **Core Concept**: This effect converts depth data into a particle cloud and applies physics-like forces to create explosive disintegration and reassembly. It's essentially a particle system driven by depth data.

2. **Particle Data Structure**: Each particle needs:
   ```python
   class Particle:
       def __init__(self, x, y, depth, color):
           self.position = np.array([x, y, depth], dtype=np.float32)
           self.color = color  # RGB
           self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32)
           self.original_position = np.array([x, y, depth], dtype=np.float32)
           self.age = 0.0
   ```

3. **Particle Generation**:
   - Sample depth frame at regular intervals (based on `particleDensity`)
   - For each sample point:
     ```python
     if depth > depth_threshold:
         particles.append(Particle(x, y, depth, frame[y, x]))
     ```
   - Or use all pixels for maximum density (expensive)

4. **Shred Force**:
   - Compute center of mass: `center = mean([p.position for p in particles])`
   - For each particle: `direction = normalize(p.position - center)`
   - `p.velocity = direction * shredAmount * velocityScale`
   - Add random variation: `p.velocity += random_vector() * velocityNoise`

5. **Animation Loop**:
   ```python
   for p in particles:
       # Update position
       p.position += p.velocity
       
       # Apply gravity
       p.velocity[1] -= gravity * dt
       
       # Apply color shift
       p.color = p.color + colorShift * dt
       
       # Apply reassembly
       if reassemble > 0.0:
           p.position = p.position * (1.0 - reassemble * dt) + p.original_position * reassemble * dt
   ```

6. **Trail Rendering**:
   - Use a separate texture to store previous particle positions
   - Each frame: blend current particles with previous trail
   - Fade trail over time based on `trailLength`

7. **Shader Structure**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D particle_tex;  // Particle data (position, color, etc.)
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   uniform float particleSize;
   uniform float trailLength;
   
   void main() {
       // For each pixel, find nearest particle
       // Or use point rendering with geometry shader
       
       // Simple approach: render particles as points
       // More complex: compute particle contribution per pixel
   }
   ```

8. **Particle Rendering**: Two main approaches:
   - **Point rendering**: Use `glDrawArrays(GL_POINTS, ...)` with point size
   - **Quad rendering**: For each particle, draw a small quad
   - **Compute shader**: Modern approach, but more complex

9. **Parameter Ranges**:
   - `shredAmount`: 0-10 → force multiplier (0 = no shred)
   - `particleSize`: 0-10 → point size in pixels (0 = invisible)
   - `velocityScale`: 0-10 → velocity multiplier
   - `colorShift`: 0-10 → color change rate (0 = no change)
   - `gravity`: 0-10 → downward acceleration (0 = no gravity)
   - `reassemble`: 0-10 → reassembly rate (0 = no reassembly)
   - `trailLength`: 0-10 → trail persistence (0 = no trail)
   - `particleDensity`: 0-10 → sampling density (0 = very sparse, 10 = very dense)
   - `depthThreshold`: 0-10 → depth threshold (0 = all particles, 10 = only near objects)
   - `velocityNoise`: 0-10 → random velocity variation (0 = deterministic)

10. **PRESETS**:
    ```python
    PRESETS = {
        "clean": {
            "shredAmount": 0.0, "particleSize": 1.0, "velocityScale": 0.0,
            "colorShift": 0.0, "gravity": 0.0, "reassemble": 0.0,
            "trailLength": 0.0, "particleDensity": 0.0, "depthThreshold": 0.0,
        },
        "mild_shred": {
            "shredAmount": 2.0, "particleSize": 2.0, "velocityScale": 3.0,
            "colorShift": 1.0, "gravity": 0.5, "reassemble": 3.0,
            "trailLength": 1.0, "particleDensity": 5.0, "depthThreshold": 2.0,
        },
        "explosion": {
            "shredAmount": 8.0, "particleSize": 4.0, "velocityScale": 8.0,
            "colorShift": 3.0, "gravity": 2.0, "reassemble": 6.0,
            "trailLength": 3.0, "particleDensity": 8.0, "depthThreshold": 1.0,
        },
        "slow_motion": {
            "shredAmount": 5.0, "particleSize": 3.0, "velocityScale": 2.0,
            "colorShift": 2.0, "gravity": 0.5, "reassemble": 8.0,
            "trailLength": 5.0, "particleDensity": 6.0, "depthThreshold": 3.0,
        },
        "colorful_burst": {
            "shredAmount": 7.0, "particleSize": 5.0, "velocityScale": 6.0,
            "colorShift": 5.0, "gravity": 1.0, "reassemble": 4.0,
            "trailLength": 4.0, "particleDensity": 7.0, "depthThreshold": 2.0,
        },
    }
    ```

11. **Testing Strategy**:
    - Test with synthetic depth (gradient, circle, etc.)
    - Verify particles created at correct positions
    - Test shred: particles should move outward from center
    - Test gravity: particles should fall over time
    - Test reassembly: particles should return to original positions
    - Test color shift: particle colors should change
    - Test trail: particles should leave visual trails

12. **Performance**: The main cost is particle count. Optimize by:
    - Using lower `particleDensity`
    - Using instanced rendering
    - Using compute shader for physics
    - Reducing `particleSize`
    - Disabling expensive features (trail, color shift)

13. **Future Extensions**:
    - Add audio reactivity to shred amount
    - Add particle lifetime (particles die after time)
    - Add collision detection (particles bounce off edges)
    - Add particle shape variation (not just points)
    - Add depth-based particle color

---
-

## References

- Particle system: https://en.wikipedia.org/wiki/Particle_system
- Point cloud: https://en.wikipedia.org/wiki/Point_cloud
- Physics simulation: https://en.wikipedia.org/wiki/Physics_simulation
- Z-buffer: https://en.wikipedia.org/wiki/Z-buffering
- VJLive legacy: `plugins/vdepth/depth_particle_shred.py`

---

## Implementation Tips

1. **Particle Generation**: Use a sampling strategy to control density:
   ```python
   def _generate_particles(self, depth_frame):
       h, w = depth_frame.shape
       particles = []
       density = self.parameters["particleDensity"] / 10.0
       step = max(1, int(1.0 / (density * 0.1)))
       
       for y in range(0, h, step):
           for x in range(0, w, step):
               depth = depth_frame[y, x]
               if depth > self.parameters["depthThreshold"] / 10.0:
                   color = self.video_frame[y, x] if self.video_frame is not None else [1.0, 1.0, 1.0]
                   particles.append(Particle(x, y, depth, color))
       
       return particles
   ```

2. **Shred Force**:
   ```python
   def _apply_shred(self):
       if self.parameters["shredAmount"] < 0.01:
           return
       
       # Compute center of mass
       if not self.particles:
           return
       
       center = np.mean([p.position for p in self.particles], axis=0)
       
       for p in self.particles:
           direction = p.position - center
           distance = np.linalg.norm(direction)
           if distance > 0.01:
               direction = direction / distance
           else:
               direction = np.random.randn(3)
               direction = direction / np.linalg.norm(direction)
           
           velocity = direction * self.parameters["shredAmount"] * self.parameters["velocityScale"]
           velocity += np.random.randn(3) * self.parameters["velocityNoise"]
           p.velocity = velocity
   ```

3. **Animation**:
   ```python
   def _animate_particles(self, dt):
       for p in self.particles:
           # Update position
           p.position += p.velocity * dt
           
           # Apply gravity
           p.velocity[1] -= self.parameters["gravity"] * dt
           
           # Apply color shift
           p.color = np.clip(p.color + self.parameters["colorShift"] * dt, 0.0, 1.0)
           
           # Apply reassembly
           if self.parameters["reassemble"] > 0.01:
               p.position = p.position * (1.0 - self.parameters["reassemble"] * dt) + \
                           p.original_position * self.parameters["reassemble"] * dt
   ```

4. **Trail Rendering**: Use a separate texture to store previous particle positions:
   ```python
   def _render_trail(self):
       if self.parameters["trailLength"] < 0.01:
           return np.zeros_like(self.video_frame)
       
       # Blend current particles with previous trail
       trail = self.trail_texture.copy()
       # ... blend logic
       return trail
   ```

5. **Shader for Particle Rendering**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D particle_tex;  // Particle data
   uniform vec2 resolution;
   uniform float particleSize;
   uniform float time;
   
   void main() {
       // For each pixel, find nearest particle
       vec2 pixel = gl_FragCoord.xy;
       vec2 best_uv = vec2(0.0);
       float best_dist = 1e6;
       
       // This would need to be implemented differently
       // Could use compute shader or point rendering
       
       // Simple approach: render particles as points
       // More complex: compute particle contribution per pixel
   }
   ```

6. **Point Rendering**: Use OpenGL point rendering:
   ```python
   def _render_particles(self):
       if not self.particles:
           return
       
       # Upload particle data to VBO
       particle_data = np.array([
           [p.position[0], p.position[1], p.position[2], p.color[0], p.color[1], p.color[2]]
           for p in self.particles
       ], dtype=np.float32)
       
       # Create VBO and VAO
       vbo = glGenBuffers(1)
       glBindBuffer(GL_ARRAY_BUFFER, vbo)
       glBufferData(GL_ARRAY_BUFFER, particle_data.nbytes, particle_data, GL_DYNAMIC_DRAW)
       
       # Set up vertex attributes
       # ...
       
       # Draw as points
       glPointSize(self.parameters["particleSize"])
       glDrawArrays(GL_POINTS, 0, len(self.particles))
   ```

7. **Performance**: The main bottleneck is particle count. Consider:
   - Using `GL_POINT_SPRITE` for textured points
   - Using `GL_VERTEX_SHADER` with `gl_PointSize` for size variation
   - Using compute shader for physics if available
   - Culling particles outside viewport

8. **Debug Mode**: Show particle positions as colored dots or visualize depth as color.

9. **Testing**: Create synthetic depth data and verify:
   - Particles generated at correct positions
   - Shred creates outward motion
   - Gravity affects particles
   - Reassembly works
   - Color shift changes colors

10. **Future Extensions**:
    - Add particle lifetime (particles fade and die)
    - Add collision detection (particles bounce off edges)
    - Add particle shape variation (not just points)
    - Add depth-based particle color
    - Add audio reactivity to particle parameters

---

## Conclusion

The DepthParticleShredEffect creates dramatic particle disintegration effects by converting depth data into a particle cloud and applying physics-like forces. With configurable shred intensity, particle physics, and reassembly behavior, it's perfect for creating the illusion of performers disintegrating into particles or for dynamic, depth-aware particle systems. The effect combines the visual impact of particle systems with the spatial awareness of depth data to create compelling, physics-based visual effects.

---
