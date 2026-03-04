# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/SMOKE-1_Fluid_Simulation.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: SMOKE-1 — FluidSim Effect (Smoke Simulation)

## Description

The FluidSim effect is a GPU-accelerated 2D Navier-Stokes fluid simulation designed for live visual performance. It implements Jos Stam's stable fluids algorithm with vorticity confinement, pressure projection, and buoyancy. The effect simulates realistic fluid dynamics including velocity advection, diffusion, and force injection, rendering the results as colorful smoke-like patterns. This is not a toy—it's a serious physics simulation that VJs can manipulate in real-time to create organic, flowing visuals.

The effect uses a feedback-based approach: each frame reads the previous velocity and dye fields, performs a physics simulation step, and outputs the updated fields. Multiple injection modes (orbit, spray, pulse, vortex pair, chaos) allow for diverse visual styles. Audio reactivity enables the fluid to respond to music, making it perfect for VJ performances.

## What This Module Does

- Simulates 2D incompressible fluid dynamics using Navier-Stokes equations
- Implements velocity advection, diffusion, pressure projection, and vorticity confinement
- Injects forces and dye (color) into the simulation field
- Renders the fluid as colorful smoke with multiple visualization modes
- Supports audio reactivity (bass, mid, treble, energy)
- Provides 5 injection modes: orbit, multi-point spray, central pulse, vortex pair, chaos
- Offers 7 render modes: dye, velocity field, vorticity, pressure, psychedelic
- Uses OpenGL shaders for GPU acceleration (60 FPS at 1080p)
- Maintains simulation state across frames via feedback textures

## What This Module Does NOT Do

- Does NOT simulate 3D fluids (2D only)
- Does NOT include temperature simulation beyond buoyancy
- Does NOT handle multiple fluid types (single fluid)
- Does NOT provide obstacle collision detection (only implicit via injection)
- Does NOT store simulation state to disk (ephemeral per session)
- Does NOT provide CPU fallback (GPU required)
- Does NOT implement advanced rendering (volumetric lighting, caustics)

---

## Detailed Behavior

### Physics Pipeline

The fluid simulation follows the standard stable fluids approach:

1. **Advection**: Move velocity and dye fields along the velocity vector
   ```glsl
   vec2 vel = get_velocity(uv - texel * vel * dt);
   vel = mix(vel, get_velocity(uv), 0.5); // Bilinear interpolation
   new_velocity = vel;
   new_dye = get_dye(uv - texel * vel * dt);
   ```

2. **External Forces**: Apply injected forces (from injection modes) and audio
   ```glsl
   vel += inject_force * inject_mask;
   vel += audio_bass * audio_force;
   ```

3. **Diffusion**: Apply viscosity (Gaussian blur on velocity)
   ```glsl
   // Implicit diffusion via Jacobi iteration (simplified)
   vel = (neighbor_sum) / 4.0 + viscosity * dt;
   ```

4. **Pressure Projection**: Make velocity divergence-free (incompressible)
   ```glsl
   float div = (vel_r.x - vel_l.x + vel_u.y - vel_d.y) * 0.5;
   float pressure = (p_l + p_r + p_d + p_u - div) * 0.25;
   vel -= gradient(pressure);
   ```

5. **Vorticity Confinement**: Enhance swirling details
   ```glsl
   float curl = (curl_r - curl_l) - (curl_u - curl_d);
   vec2 curl_grad = normalize(gradient(abs(curl)));
   vel += curl_grad * curl * vorticity * dt;
   ```

6. **Buoyancy**: Apply vertical forces based on dye (hot rises, cool sinks)
   ```glsl
   vel.y += buoyancy * dye * 0.01;
   ```

7. **Dissipation**: Fade dye over time
   ```glsl
   dye = max(dye * dissipation, inject_dye);
   ```

8. **Velocity Decay**: Dampen velocity to prevent explosion
   ```glsl
   vel *= velocity_decay;
   ```

### Injection Modes

The `inject_mode` parameter (0-10 range, mapped to discrete modes):

- **0 (Orbit)**: Single injector orbits center, emitting dye and velocity tangentially
- **1 (Multi-point spray)**: 4 injectors spray from edges toward center
- **2 (Central pulse)**: Center emits radially, audio-reactive (bass)
- **3 (Vortex pair)**: Two counter-rotating vortices
- **4-9 (Variants)**: Intermediate blends
- **10 (Chaos)**: Simplex noise-driven random injection everywhere

### Render Modes

The `render_mode` parameter controls output visualization:

- **0 (Dye)**: Show dye concentration (colored smoke)
- **3 (Velocity)**: Visualize velocity field magnitude
- **5 (Vorticity)**: Show curl/rotation
- **7 (Pressure)**: Display pressure field
- **10 (Psychedelic)**: Multi-channel feedback with hue cycling

### Audio Reactivity

Audio analyzer provides:
- `audio_bass` (0.0-1.0) — Low frequencies
- `audio_mid` (0.0-1.0) — Mid frequencies
- `audio_high` (0.0-1.0) — High frequencies
- `audio_energy` (0.0-1.0) — Overall energy

These modulate:
- Injection force (especially in pulse mode)
- Color intensity
- Glow amount
- Turbulence

### Shader Architecture

The effect uses a single fragment shader that reads from and writes to a framebuffer texture (feedback). The texture stores:
- `rgb`: Dye (color)
- `a`: Velocity (packed as vec2? Actually velocity stored in separate texture or packed)

In practice, velocity and dye are often stored in separate textures or packed into RGBA channels. The legacy code shows `tex0` as the previous frame with velocity in RGB? and pressure in alpha? Need to verify.

---

## Public Interface

```python
class FluidSimEffect(Effect):
    def __init__(self) -> None: ...
    def set_audio_analyzer(self, analyzer: AudioAnalyzer) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
    def get_parameters(self) -> Dict[str, float]: ...
    def set_parameter(self, name: str, value: float) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (used for mixing/compositing) |
| **Output** | `np.ndarray` | Rendered fluid simulation (HxWxC, RGB) |

The effect is self-contained; it doesn't really need an input but accepts one for pipeline compatibility.

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `viscosity` | float | 0.5 | 0.0 - 10.0 | Fluid thickness (0=water, 10=honey) |
| `vorticity` | float | 0.5 | 0.0 - 10.0 | Swirl strength (0=none, 10=extreme) |
| `dissipation` | float | 0.5 | 0.0 - 10.0 | Dye fade rate (0=slow, 10=fast) |
| `velocity_decay` | float | 0.5 | 0.0 - 10.0 | Velocity damping (0=stop, 10=preserve) |
| `pressure_iter` | float | 0.5 | 0.0 - 10.0 | Pressure solver iterations (5-80) |
| `turbulence` | float | 0.5 | 0.0 - 10.0 | Random force injection |
| `buoyancy` | float | 0.5 | 0.0 - 10.0 | Vertical force from dye (-2 to 2) |
| `inject_radius` | float | 0.5 | 0.0 - 10.0 | Force/dye injection radius |
| `inject_force` | float | 0.5 | 0.0 - 10.0 | Injection velocity strength |
| `inject_mode` | float | 0.0 | 0.0 - 10.0 | Injection pattern (0=orbit, 10=chaos) |
| `inject_hue` | float | 0.5 | 0.0 - 1.0 | Base hue of injected dye |
| `inject_hue_speed` | float | 0.5 | 0.0 - 10.0 | Hue cycling speed |
| `render_mode` | float | 0.0 | 0.0 - 10.0 | Visualization mode |
| `color_intensity` | float | 0.5 | 0.0 - 10.0 | Color amplification |
| `glow_amount` | float | 0.5 | 0.0 - 10.0 | Bloom/glow strength |
| `background_hue` | float | 0.0 | 0.0 - 1.0 | Background color hue (0=black) |
| `flow_distort` | float | 0.0 | 0.0 - 10.0 | Self-distortion feedback |
| `edge_wrap` | float | 0.0 | 0.0 - 10.0 | Boundary handling (0=clamp, 5=wrap, 10=mirror) |

**Note**: Many parameters use 0-10 range that maps internally to physical values (e.g., viscosity 0.00001 to 0.01). The effect handles this remapping in the shader.

---

## State Management

**Persistent State:**
- `_velocity_texture: int` — GPU texture storing velocity field (RG? or RGBA)
- `_dye_texture: int` — GPU texture storing dye (color) field
- `_pressure_texture: int` — GPU texture storing pressure field (optional, may be in alpha)
- `_framebuffer: Framebuffer` — FBO for feedback rendering
- `_shader: ShaderProgram` — Compiled simulation shader
- `_parameters: dict` — Current parameter values
- `_audio_analyzer: Optional[AudioAnalyzer]` — Audio feature source
- `_frame_width: int`, `_frame_height: int` — Resolution

**Per-Frame State:**
- None (stateless between frames; all state in textures)

**Initialization:**
- Create textures and FBO with current resolution
- Initialize velocity and dye to zero (or small random noise)
- Compile shader

**Cleanup:**
- Delete all textures (`glDeleteTextures`)
- Delete FBO
- Delete shader

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Velocity texture | GL_TEXTURE_2D | GL_RG16F or GL_RGBA16F | frame size | Created init, persists |
| Dye texture | GL_TEXTURE_2D | GL_RGBA16F | frame size | Created init, persists |
| Pressure texture | GL_RGBA16F (in alpha) | frame size | Created init, persists |
| Framebuffer | GL_FRAMEBUFFER | — | frame size | Created init, persists |
| Shader program | GLSL program | vertex + fragment | N/A | Init once |

**Memory Budget (1080p):**
- Each RGBA16F texture: 1920 × 1080 × 8 bytes = ~16.6 MB
- 3 textures = ~49.8 MB
- FBO overhead: negligible
- Total: ~50 MB

This is a high-memory effect (GPU VRAM intensive).

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Texture/FBO creation fails | `RuntimeError("Out of GPU memory")` | Reduce resolution or abort |
| Shader compilation fails | `ShaderCompilationError` | Log error, effect becomes no-op |
| Audio analyzer not set | `RuntimeError("No audio analyzer")` (if audio used) | Set via `set_audio_analyzer()` |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Resolution too large | May cause OOM | Warn if >4K |
| Feedback loop broken | FBO incomplete | Check FBO status after creation |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread with the OpenGL context. The simulation state (textures) is mutated each frame, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (1080p):**
- Advection (velocity + dye): ~2-3 ms
- Force injection: ~0.5 ms
- Diffusion (implicit): ~1-2 ms (depends on `pressure_iter`)
- Pressure projection: ~2-4 ms (Jacobi iterations)
- Vorticity confinement: ~1 ms
- Buoyancy: ~0.2 ms
- Rendering: ~1-2 ms
- **Total**: ~7-12 ms on discrete GPU, ~15-25 ms on integrated GPU

**Optimization Strategies:**
- Use half-float (`GL_RG16F`, `GL_RGBA16F`) for textures to reduce bandwidth
- Reduce `pressure_iter` for faster but less accurate pressure solve
- Use lower resolution for simulation (e.g., half-res) and upsample for display
- Early-out if `inject_force` and `audio_energy` are zero (no changes)
- Consider using texture arrays to reduce FBO switches if multiple fluids

---

## Integration Checklist

- [ ] Effect instantiated and shader compiled successfully
- [ ] Textures and FBO created with correct format
- [ ] Audio analyzer set if audio reactivity desired
- [ ] Parameters initialized to defaults
- [ ] `process_frame()` called each frame (maintains feedback loop)
- [ ] `cleanup()` called on shutdown to release GPU resources
- [ ] Resolution matches pipeline (or effect handles resizing)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes, textures/FBO created |
| `test_shader_compilation` | Shader compiles without errors |
| `test_set_audio_analyzer` | Audio analyzer stored correctly |
| `test_parameter_set_get` | All parameters can be set and retrieved |
| `test_parameter_clamping` | Out-of-range values clamped or rejected |
| `test_process_frame_basic` | Returns frame of correct shape and type |
| `test_simulation_step` | Velocity and dye change over time with injection |
| `test_injection_modes` | Each mode produces distinct patterns |
| `test_render_modes` | Each render mode outputs different visualization |
| `test_audio_reactivity` | Audio values affect injection/rendering |
| `test_viscosity` | Higher viscosity slows fluid motion |
| `test_vorticity` | Higher vorticity increases swirls |
| `test_buoyancy` | Positive buoyancy makes dye rise |
| `test_dissipation` | Higher dissipation fades dye faster |
| `test_velocity_decay` | Higher decay slows fluid faster |
| `test_edge_wrapping` | Different boundary conditions affect flow |
| `test_cleanup` | All GPU resources released |
| `test_no_memory_leak` | Repeated init/cleanup cycles don't leak |
| `test_resolution_change` | Effect handles resolution changes (if supported) |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 1000 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] SMOKE-1: fluid_sim` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/fluid_sim.py` — Original VJLive fluid simulation implementation
- `core/shaders/fluid_sim.frag` (if exists) — Shader code
- `assets/gists/fluid_sim.json` — Gist metadata and controls

Design decisions inherited:
- Jos Stam stable fluids algorithm
- Velocity and dye stored in separate textures (or packed)
- Feedback loop via FBO
- Parameters use 0-10 range with internal remapping
- Injection modes: orbit, spray, pulse, vortex, chaos
- Render modes: dye, velocity, vorticity, pressure, psychedelic
- Audio reactivity via uniform injection
- Simplex noise for turbulence

---

## Notes for Implementers

1. **Algorithm**: The stable fluids algorithm is well-documented. Key steps: advection, force, diffusion, pressure, vorticity, buoyancy. Implement in a single shader pass or multiple passes. The legacy code appears to do it all in one fragment shader with feedback.

2. **Texture Storage**: You need to store velocity (vec2) and dye (vec3) plus pressure (float). Common approaches:
   - Separate textures: velocity (RG16F), dye (RGBA16F), pressure (R16F)
   - Packed: velocity in RG, dye in B? Actually legacy uses RGBA with velocity in RGB? Check code.
   The legacy code shows `tex0` with velocity in RGB? and pressure in alpha? Need to inspect more.

3. **Feedback Loop**: Use a Framebuffer Object (FBO) to render the simulation result to textures, then sample from those textures in the next frame. This is a ping-pong approach: you need two sets of textures and swap each frame, or use a single set and ensure you're not reading and writing the same texture simultaneously (undefined behavior). Typically use `glBindFramebuffer` to draw to texture A while sampling from texture B, then swap.

4. **Advection**: Advect velocity along itself (self-advection) and dye along velocity. Use semi-Lagrangian method: trace back along velocity vector, sample at that position. This is unconditionally stable but introduces numerical diffusion. Use higher-order interpolation (bilinear) for quality.

5. **Pressure Projection**: The pressure solve is the most expensive part. The Jacobi method is simple but requires many iterations. The legacy code uses `pressure_iter` parameter (0-10 maps to 5-80 iterations). Consider using a fixed number like 20 for quality/speed tradeoff.

6. **Vorticity Confinement**: This adds small-scale swirls that would otherwise be damped out. Compute curl (vorticity) from velocity, then apply force along the gradient of the curl magnitude. This is crucial for realistic-looking smoke.

7. **Buoyancy**: Hot fluid rises. Use dye concentration as a proxy for temperature. Add upward force proportional to dye. Can be negative for cooling (sinking).

8. **Turbulence**: Add random forces using Simplex noise. This keeps the simulation from becoming too smooth and adds fine details.

9. **Injection Modes**: These determine where and how forces/dye are added each frame. Implement each mode as a separate function in the shader. The `inject_mode` uniform selects which one to use.

10. **Render Modes**: After simulation, you need to output something. The simplest is to output dye directly. Velocity field can be visualized by mapping speed to brightness. Vorticity and pressure are scalar fields; map to false color. Psychedelic mode likely uses feedback with hue cycling.

11. **Audio Reactivity**: The audio analyzer provides four values (0.0-1.0). These are passed as uniforms and can modulate injection force, color intensity, etc. Ensure the effect's `set_audio_analyzer()` method stores the analyzer and updates uniforms each frame.

12. **Boundary Conditions**: The `edge_wrap` parameter controls what happens at edges: clamp (0), wrap (5), mirror (10). Implement by adjusting UV coordinates when sampling: `uv_wrapped = fract(uv)` for wrap, `uv = abs(uv)` for mirror, etc.

13. **Performance**: The simulation is heavy. At 1080p, you may need to run at half-resolution (960×540) and upscale. Consider using `GL_RG16F` for velocity (2x16-bit floats) and `GL_RGBA16F` for dye (4x16-bit floats). These are supported on most GPUs from ~2010 onward.

14. **Numerical Stability**: Use small time steps (dt ~ 0.016 for 60 FPS). The stable fluids algorithm is conditionally stable; ensure your advection and diffusion parameters don't cause blow-up. Clamp velocity after each step.

15. **Initialization**: Start with zero velocity and zero dye. Optionally seed with small random noise to avoid perfect stillness.

16. **Debugging**: Provide a debug mode that outputs intermediate fields (velocity magnitude, pressure, curl) to tune parameters.

17. **Memory**: The effect uses ~50 MB of GPU memory for 1080p. This is acceptable for modern GPUs but may be too much for integrated graphics. Consider allowing lower precision (GL_RG16F for dye too) or resolution scaling.

18. **Shader Code**: The legacy shader is ~200 lines. It will be complex. Study it carefully. Key functions: `get_velocity()`, `get_dye()`, `advect()`, `project()`, `inject()`.

19. **Testing**: Create synthetic tests: inject a single Gaussian blob and watch it advect, diffuse, and dissipate. Verify vorticity confinement creates swirls. Test buoyancy by injecting hot (rising) and cool (sinking) dye.

20. **Audio Integration**: The effect should accept an `AudioAnalyzer` object with methods like `get_feature('bass')`. Call this each frame to get current values and pass to shader.

---
-

## References

- Jos Stam's Stable Fluids: https://www.dgp.toronto.edu/people/stam/reality/Research/pdf/stable.pdf
- Real-Time Fluid Dynamics for Games: https://www.dgp.toronto.edu/people/stam/reality/Research/fluids.html
- GPU Gems 3: Chapter 30 (Fluid Simulation): https://developer.nvidia.com/gpugems/GPUGems3/gpugems3_ch30.html
- OpenGL Framebuffer Objects: https://learnopengl.com/Advanced-OpenGL/Framebuffers
- Simplex Noise: https://github.com/stegu/webgl-noise/

---

## Implementation Tips

1. **Shader Structure**:
   ```glsl
   // Uniforms
   uniform sampler2D u_velocity_tex;
   uniform sampler2D u_dye_tex;
   uniform float u_time;
   uniform vec2 u_resolution;
   uniform float u_viscosity;
   uniform float u_vorticity;
   uniform float u_dissipation;
   uniform float u_velocity_decay;
   uniform float u_pressure_iter;
   uniform float u_turbulence;
   uniform float u_buoyancy;
   uniform float u_inject_radius;
   uniform float u_inject_force;
   uniform float u_inject_mode;
   uniform float u_inject_hue;
   uniform float u_inject_hue_speed;
   uniform float u_render_mode;
   uniform float u_color_intensity;
   uniform float u_glow_amount;
   uniform float u_background_hue;
   uniform float u_flow_distort;
   uniform float u_edge_wrap;
   uniform float u_audio_bass;
   uniform float u_audio_mid;
   uniform float u_audio_high;
   uniform float u_audio_energy;
   
   // Output
   layout (location = 0) out vec4 frag_color;
   
   void main() {
       vec2 uv = gl_FragCoord.xy / u_resolution;
       vec2 texel = 1.0 / u_resolution;
       
       // 1. Advect velocity
       vec2 vel = advect_velocity(uv, texel);
       
       // 2. Apply forces (injection + audio)
       vec2 force = get_injection(uv, texel, u_inject_mode, u_inject_force, u_inject_radius);
       force += audio_force * u_audio_energy;
       vel += force;
       
       // 3. Diffuse (implicit)
       vel = diffuse(vel, uv, texel, u_viscosity);
       
       // 4. Pressure projection
       vel = project(vel, uv, texel, u_pressure_iter);
       
       // 5. Vorticity confinement
       vel += vorticity_confine(vel, uv, texel, u_vorticity);
       
       // 6. Buoyancy
       float dye = texture(u_dye_tex, uv).r; // or get from separate
       vel.y += u_buoyancy * dye * 0.01;
       
       // 7. Velocity decay
       vel *= u_velocity_decay;
       
       // 8. Advect dye
       float new_dye = advect_dye(uv, texel, vel);
       
       // 9. Dissipate and inject dye
       new_dye = max(new_dye * u_dissipation, get_dye_injection(uv, texel, u_inject_mode));
       
       // 10. Render
       vec3 color = render(uv, new_dye, vel, u_render_mode, u_inject_hue, u_color_intensity);
       
       frag_color = vec4(color, 1.0);
   }
   ```

2. **Ping-Pong Buffers**: You need two sets of textures (A and B). Frame N reads from A, writes to B. Next frame, swap. In code:
   ```python
   self._velocity_tex_A, self._velocity_tex_B
   self._dye_tex_A, self._dye_tex_B
   # Each frame:
   glBindFramebuffer(self._fbo_B)
   glBindTexture(self._velocity_tex_A)  # read from A
   glBindTexture(self._dye_tex_A)
   draw_quad()
   # Swap references
   self._velocity_tex_A, self._velocity_tex_B = self._velocity_tex_B, self._velocity_tex_A
   self._dye_tex_A, self._dye_tex_B = self._dye_tex_B, self._dye_tex_A
   ```

3. **Pressure Solver**: The Jacobi iteration is:
   ```
   p_new = (p_left + p_right + p_down + p_up - div) / 4
   ```
   Do this `pressure_iter` times per frame. Store pressure in a separate texture or in the alpha channel of velocity texture.

4. **Vorticity**: Compute curl as `(vel_right.x - vel_left.x) - (vel_up.y - vel_down.y)`. Then compute gradient of |curl| and apply force along that gradient to amplify swirls.

5. **Audio Integration**: In `process_frame()`, get audio features and set uniforms:
   ```python
   if self._audio_analyzer:
       bass = self._audio_analyzer.get_feature('bass')
       # ... set uniforms
   ```

6. **Parameter Remapping**: The 0-10 range maps to physical values. Define constants:
   ```python
   VISCOSITY_MAP = {0: 0.00001, 10: 0.01}  # log scale?
   # Or linear: value = min + (max-min) * (param/10)
   ```

7. **Testing with Mocks**: Since the simulation is complex, test with known initial conditions. For example, set velocity to zero and inject a single dye blob; verify it diffuses and dissipates but doesn't move. Then inject a force and verify advection.

8. **Performance Profiling**: Use GPU timers (glBeginQuery/glEndQuery) to measure time spent in each shader stage. This helps identify bottlenecks (usually pressure projection).

9. **Fallback**: If the GPU can't handle the resolution, automatically downscale. Provide a `quality` parameter that controls resolution (0.5, 0.75, 1.0).

10. **Documentation**: Document the physics parameters clearly. VJs need to understand what `vorticity` and `buoyancy` do. Provide example presets: "Water", "Honey", "Smoke", "Fire", "Plasma".

---

## Conclusion

The FluidSim effect is a centerpiece for organic, physics-based visuals. It requires careful implementation of Navier-Stokes on the GPU, but the results are stunning and highly controllable. By following the stable fluids algorithm and providing intuitive parameters, this effect will become a staple in VJ sets for creating living, breathing smoke and fluid visuals.

---
