````markdown
# P6-P302: Advanced Particle 3D System

> **Task ID:** `P6-P302`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`core/effects/particles_3d.py`)
> **Class:** `AdvancedParticle3DSystem`
> **Phase:** Phase 6
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete, unambiguous Pass 2 specification for the `AdvancedParticle3DSystem`—
a GPU-accelerated 3D particle simulator that creates dynamic, real-time visual effects
using instanced geometry and compute shaders. The system supports configurable spawning,
physics (gravity, damping, collision), and optional audio reactivity. The objective is to
document exact shader math, particle lifecycle equations, parameter remaps, presets, CPU
fallback, and comprehensive tests for feature parity with VJLive-2.

## Technical Requirements
- Implement as a VJLive3 generator plugin (produces visual output)
- Support ≥10,000 particles per frame at 60 FPS on consumer GPU (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep core implementation <750 lines (Safety Rail 4)
- Graceful fallback to CPU particle updates when GPU unavailable (Safety Rail 7)
- No silent failures; emit clear error messages for configuration issues

## Implementation Notes / Porting Strategy
1. Reuse the legacy compute shader pattern or rewrite as vertex shader instancing
   for maximum compatibility.
2. Implement GPU particle buffer management (position, velocity, life, color SSBOs or
   VBOs with dynamic updates).
3. Provide deterministic NumPy-based CPU fallback for headless rendering and testing.
4. Add audio reactivity hooks (optional; maps audio energy to spawn rate or color).
5. Include automated performance profiling tests to validate 10k+ particle capacity.

## Public Interface
```python
class AdvancedParticle3DSystem(Effect):
    """
    GPU-accelerated 3D particle system with physics.
    
    Simulates thousands of particles in real-time using instanced rendering
    and optional compute shaders. Supports gravity, damping, collisions, and
    audio-reactive behavior.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 max_particles: int = 10000, use_compute_shader: bool = True):
        """
        Initialize the particle system.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            max_particles: Maximum simultaneous particles (typically 10k-50k).
            use_compute_shader: If True, use compute shaders; else CPU updates.
        """
        super().__init__("Advanced Particle 3D", PARTICLE_VERTEX_SHADER, 
                         PARTICLE_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "generator"
        self.effect_tags = ["particle", "3d", "physics", "dynamic"]
        self.features = ["GPU_INSTANCING", "PHYSICS_SIM", "AUDIO_REACTIVE"]
        self.usage_tags = ["GENERATES_GEOMETRY"]
        
        self.max_particles = max_particles
        self.use_compute_shader = use_compute_shader
        self.particle_buffer = None  # GPU buffer (SSBOs or dynamic VBO)
        self.particle_count = 0
        self.accumulated_time = 0.0

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'spawn_rate': (0.0, 10.0),         # particles/frame
            'particle_life': (0.0, 10.0),      # lifetime in seconds
            'velocity_range': (0.0, 10.0),     # magnitude variation
            'size': (0.0, 10.0),               # particle size in pixels
            'gravity': (0.0, 10.0),            # downward acceleration
            'damping': (0.0, 10.0),            # velocity decay
            'color_mode': (0.0, 10.0),         # color assignment scheme
            'audio_drive': (0.0, 10.0),        # audio reactivity strength
            'turbulence': (0.0, 10.0),         # noise-driven perturbation
            'expansion': (0.0, 10.0),          # spawn radius growth
        }

        # Default parameter values (middle of ranges for most)
        self.parameters = {
            'spawn_rate': 5.0,
            'particle_life': 6.0,
            'velocity_range': 4.0,
            'size': 5.0,
            'gravity': 3.0,
            'damping': 7.0,
            'color_mode': 5.0,
            'audio_drive': 2.0,
            'turbulence': 2.0,
            'expansion': 3.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'spawn_rate': "Particles spawned per frame (0=none, 10=max burst)",
            'particle_life': "Particle lifetime before fade (0=instant, 10=very long)",
            'velocity_range': "Initial velocity magnitude (0=static, 10=fast)",
            'size': "Particle size on screen (0=tiny, 10=large)",
            'gravity': "Downward acceleration (0=none, 10=fast fall)",
            'damping': "Velocity decay per frame (0=no decay, 10=quick stop)",
            'color_mode': "Color assignment: 0=constant, 5=gradient, 10=rainbow",
            'audio_drive': "Audio input modulation (0=off, 10=full reactivity)",
            'turbulence': "Perlin noise applied to trajectories",
            'expansion': "Radius of spawn region growth over life"
        }

        # Sweet spot presets
        self._sweet_spots = {
            'spawn_rate': [3.0, 5.0, 7.0],
            'particle_life': [4.0, 6.0, 8.0],
            'gravity': [2.0, 5.0, 7.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render particles to framebuffer object.
        
        Args:
            tex_in: Optional background texture (for particle blending).
            extra_textures: Optional (audio_texture, if audio_drive > 0).
            chain: Rendering chain context.
            
        Returns:
            Framebuffer texture handle containing rendered particles.
        """
        # Particle update loop (GPU or CPU based on use_compute_shader)
        # Setup VAO/VBO for instanced particle rendering
        # Issue draw call: glDrawArraysInstanced(GL_TRIANGLE_STRIP, 0, 4, particle_count)
        # Return result texture handle
        pass

    def update_particles(self, dt: float, audio_reactor = None):
        """
        Update particle positions, velocities, and lifetimes.
        
        Args:
            dt: Delta time (seconds since last frame).
            audio_reactor: Optional AudioReactor instance for audio input.
        """
        # If use_compute_shader: dispatch compute shader
        # Else: update positions on CPU
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms with proper parameter validation.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input for spawn modulation.
            semantic_layer: Optional semantic input.
        """
        # Map UI (0—10) parameters to internal ranges
        # Bind computed uniforms to shader
        # Handle audio reactivity if enabled
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `spawn_rate` (float, UI 0—10) → internal `S` = map_linear(x, 0,10, 0.0, 500.0)
  - Particles spawned per frame; 10 = ~500 particles/frame at 60fps
  - Sweet spots: 3 (30/frame), 5 (250/frame), 7 (350/frame)
- `particle_life` (float, UI 0—10) → internal `L` = map_linear(x, 0,10, 0.1, 10.0)
  - Lifetime in seconds before fade-out starts
- `velocity_range` (float, UI 0—10) → internal `V` = map_linear(x, 0,10, 0.5, 15.0)
  - Initial velocity magnitude (units/sec in virtual 3D space)
- `size` (float, UI 0—10) → internal `Z` = map_linear(x, 0,10, 1.0, 32.0)
  - Particle billboard size in pixels
- `gravity` (float, UI 0—10) → internal `G` = map_linear(x, 0,10, 0.0, 30.0)
  - Downward acceleration in units/sec²
- `damping` (float, UI 0—10) → internal `D` = map_linear(x, 0,10, 0.0, 0.99)
  - Velocity multiplier per frame: `v_new = v_old * D`
- `color_mode` (float, UI 0—10) → internal mode selection (int 0—10)
  - 0–3: Single color (RGBA)
  - 4–6: Gradient (age-based interpolation)
  - 7–10: Rainbow HSV cycle
- `audio_drive` (float, UI 0—10) → internal `A` = x / 10.0
  - Modulates spawn rate: `actual_S = S * (1.0 + A * audio_energy)`
- `turbulence` (float, UI 0—10) → internal `T` = map_linear(x, 0,10, 0.0, 2.0)
  - Perlin noise frequency and amplitude applied to velocity perturbation
- `expansion` (float, UI 0—10) → internal `E` = map_linear(x, 0,10, 0.0, 5.0)
  - Spawn radius multiplier over lifetime: `r(t) = r_0 * (1.0 + E * (t/L))`

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float spawn_rate;`          // particles/frame (remapped)
- `uniform float particle_life;`       // max lifetime (seconds)
- `uniform float velocity_range;`      // initial velocity magnitude
- `uniform float gravity;`             // downward acceleration
- `uniform float damping;`             // velocity decay
- `uniform int color_mode;`            // 0=single, 5=gradient, 10=rainbow
- `uniform float time;`                // current elapsed time
- `uniform sampler2D audio_texture;`   // optional audio input
- `uniform float audio_drive;`         // audio modulation strength
- `uniform float turbulence;`          // noise perturbation
- `uniform float expansion;`           // spawn region growth
- `uniform float size;`                // particle size (pixels)

## Effect Math (concise, GPU/CPU-consistent)

All math is written to be implementable identically in GLSL (compute + fragment shaders)
and NumPy (CPU particle engine).

### 1) Particle Spawning

Each frame, emit `S` new particles (where `S = spawn_rate` remapped).
If `audio_drive > 0`, modulate spawn rate:
```
S_actual = S * (1.0 + audio_drive * audio_energy)
```

For each new particle:
- **Position**: origin (e.g., center of screen or random within spawn_region)
- **Velocity**: random direction (uniform on unit sphere) × `velocity_range`
- **Life**: initialized to `L` seconds
- **Color**: based on `color_mode` (see below)
- **Age**: 0.0

### 2) Particle Update (per frame, dt = 1/60 sec)

For each particle:

a) **Apply forces**:
   ```
   vel += gravity * downward_vector * dt
   vel *= damping        // exponential decay
   ```

b) **Apply turbulence** (if turbulence > 0):
   ```
   noise_vec = perlin3d(pos / turbulence_scale, time)
   vel += noise_vec * turbulence * dt
   ```

c) **Update position**:
   ```
   pos += vel * dt
   ```

d) **Update life**:
   ```
   life -= dt
   age = (L - life) / L    // normalized age [0,1]
   ```

e) **Expansion** (optional radius growth):
   ```
   spawn_distance = distance(pos, origin)
   spawn_distance *= (1.0 + expansion * age)
   ```

### 3) Color Assignment

- **Mode 0–3** (single color): Use constant RGBA (e.g., white or red)
- **Mode 4–6** (gradient): Interpolate between two colors based on age:
  ```
  color = mix(color_start, color_end, age)
  ```
- **Mode 7–10** (rainbow): Convert age to HSV hue, saturation = 1.0, value = 1.0:
  ```
  hue = age * 360.0
  color = hsv_to_rgb(hue, 1.0, 1.0)
  ```

### 4) Particle Fade-Out

As life approaches 0, linearly fade alpha:
```
alpha = 1.0 - (age > 0.8 ? (age - 0.8) / 0.2 : 0.0)
// Fade starts at 80% lifetime, reaches 0 at death
```

### 5) Rendering (GPU path)

- Bind particle SSBOs (positions, ages, colors)
- Instanced draw of quad-per-particle with billboard orientation
- Fragment shader samples color from SSBO and applies alpha

CPU path uses NumPy:
- Maintain `positions`, `velocities`, `ages`, `colors` as float32 arrays (N, 3)
- Loop over particles, apply the math above per-frame
- Use PIL/cv2 to rasterize quads onto output frame

## CPU Fallback (NumPy sketch)

```python
def particles_cpu_update(particles, dt, frame_width, frame_height):
    """
    Updates particle positions, velocities, and lifetimes.
    
    particles: dict with keys 'positions', 'velocities', 'ages', 'colors', 'sizes'
               each with shape (N, *)
    """
    # Apply gravity
    particles['velocities'][:, 1] -= gravity * dt  # downward
    
    # Apply damping
    particles['velocities'] *= damping
    
    # Update positions
    particles['positions'] += particles['velocities'] * dt
    
    # Update ages
    particles['ages'] += dt / particle_life
    
    # Remove dead particles
    mask = particles['ages'] < 1.0
    for key in particles:
        particles[key] = particles[key][mask]
    
    # Compute alpha fade
    fade_alpha = np.where(particles['ages'] > 0.8,
                          1.0 - (particles['ages'] - 0.8) / 0.2,
                          1.0)
    particles['colors'][:, 3] = fade_alpha
    
    # Rasterize to output frame
    for i, (pos, color, size) in enumerate(zip(...)):
        # Convert 3D pos to screen coords (project)
        # Draw quad/circle at that position
        pass
```

## Presets (recommended)
- `Gentle Cascade`:
  - `spawn_rate` 2.0, `particle_life` 4.0, `velocity_range` 3.0,
    `gravity` 1.5, `damping` 8.0, `size` 6.0, `color_mode` 5.0
- `Chaotic Burst`:
  - `spawn_rate` 8.0, `particle_life` 3.0, `velocity_range` 8.0,
    `gravity` 5.0, `damping` 5.0, `size` 8.0, `color_mode` 10.0, `turbulence` 5.0
- `Sparkle Trail`:
  - `spawn_rate` 3.5, `particle_life` 7.0, `velocity_range` 2.0,
    `gravity` 0.5, `damping` 9.5, `size` 3.0, `color_mode` 8.0, `expansion` 2.0
- `Audio Reactive Fountain`:
  - `spawn_rate` 4.0, `particle_life` 5.0, `velocity_range` 6.0,
    `gravity` 6.0, `damping` 6.0, `size` 5.0, `audio_drive` 8.0, `color_mode` 7.0

## Edge Cases and Error Handling
- **GPU unavailable**: Fall back to CPU particle engine (NumPy-based updates
  + PIL rasterization). May run at reduced framerate; acceptable for testing.
- **Particle explosion** (spawn_rate too high): Clamp to `max_particles` limit.
  Silently drop excess spawns or reuse oldest dead particles.
- **Out-of-bounds particles**: Cull particles that move far from viewport
  (e.g., y > height + 500 pixels). Prevents memory leaks.
- **Invalid color_mode**: Clamp to valid range [0, 10].
- **NaN/Inf** in physics: Guard against division by zero in noise sampling.

## Test Plan (minimum ≥80% coverage)
- `test_particle_spawn_rate` — verify spawn count matches remapped rate
- `test_particle_lifecycle` — particles spawn, age, and die on schedule
- `test_gravity_application` — downward movement proportional to gravity param
- `test_damping_decay` — velocity decays exponentially per damping value
- `test_color_mode_transitions` — all color modes produce valid output
- `test_audio_drive_modulation` — audio energy modulates spawn rate when enabled
- `test_turbulence_perturbation` — particles deviate from ballistic path when turbulence > 0
- `test_max_particle_limit` — system respects max_particles cap
- `test_cpu_vs_gpu_parity` — CPU and GPU paths produce pixel-diff comparable output
- `test_performance_10k_particles` — sustain ≥60 FPS at 1080p with 10k particles
- `test_preset_visual_consistency` — each preset renders recognizable pattern
- `test_edge_case_zero_life` — particles with life=0 are culled immediately

## Verification Checkpoints
- [ ] `AdvancedParticle3DSystem` class registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly to shader uniforms
- [ ] GPU particle buffer (SSBO or VBO) allocates and updates correctly
- [ ] CPU fallback produces output without crashing (headless mode)
- [ ] Presets load and render at intended visual styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 10,000+ particles sustained at ≥60 FPS (1080p, moderate GPU)
- [ ] No safety rail violations (file size, error handling, etc.)

## Implementation Handoff Notes
- Choose GPU particle update strategy:
  - **Compute Shader**: Highest perf, modern GPU requirement (GL 4.3+)
  - **Vertex Shader Instancing**: Lower perf, better compatibility (GL 3.1+)
  - **Transform Feedback**: Middle ground (GL 3.0+)
  
- For maximum fidelity match with VJLive-2, prioritize instanced quad rendering
  (4 vertices per particle, position from SSBO, size from uniform).

- Audio reactivity: Connect to `AudioReactor` instance if available; check
  `audio_reactor` param in `apply_uniforms()` and `update_particles()`.

## Resources
- Reference (similar VJ systems): MilkdropEffect (shader-based), Shadertoy examples
- Performance tuning: GPU profiler (RenderDoc), frame capture analysis
- Test framework: pytest + OpenGL headless contexts (osmesa or EGL)

````
