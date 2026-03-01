# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT207_silver_visions.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT207 — silver_visions (SilverVisionsEffect)

**What This Module Does**

The `SilverVisionsEffect` is a high-fidelity 3D particle system with a chrome/metallic aesthetic, built on top of `AdvancedParticle3DSystem`. It generates dense, responsive particles using a spherical emitter and turbulence forces, rendered as billboards with color interpolation from bright silver/white to cyan fade-out. The system is designed to be highly audio-reactive, pulsing with the beat and responding to frequency bands. It provides three macro-control parameters ("turbulence", "density", "flow_speed") that map to multiple underlying system settings for easy performance control.

The effect is ideal for creating shimmering, metallic particle fields that dance with music, suitable for VJ performances with electronic or ambient music.

**What This Module Does NOT Do**

- Does NOT implement its own particle physics (inherits from AdvancedParticle3DSystem)
- Does NOT support custom color schemes (fixed silver/cyan palette)
- Does NOT provide per-emitter or per-force control (uses a single emitter and noise force)
- Does NOT implement advanced rendering like mesh particles or lines (billboards only)
- Does NOT handle audio analysis itself (relies on external audio features)
- Does NOT support multiple render targets or post-processing (outputs to screen/FBO)

---

## Detailed Behavior and Parameter Interactions

### Inheritance Architecture

`SilverVisionsEffect` extends `AdvancedParticle3DSystem` and overrides its configuration to provide a curated aesthetic. The base class provides:
- Particle physics (gravity, drag, turbulence, attractor, vortex)
- Emission system (emitter parameters)
- Rendering pipeline (OpenGL with VBOs, shaders)
- Audio reactivity infrastructure

The subclass configures a specific preset and provides simplified macro-parameter mapping.

### Default Configuration

Upon initialization, `SilverVisionsEffect` sets up:

1. **Single Sphere Emitter**:
   - Type: Sphere (particles spawn within a spherical volume)
   - Emission rate: 500 particles per frame (high density)
   - Particle lifetime: 4.0 seconds (average)
   - Initial speed: 0.5 units/sec
   - Speed variation: ±20% randomness
   - Size range: 0.5 to 2.5 units (random per particle)
   - Position: (0, 0, 0) — center of scene
   - Color gradient: from silver/white `(0.9, 0.9, 1.0, 1.0)` to cyan fade-out `(0.0, 0.8, 0.9, 0.0)`
   - Emit on beat: When `audio_beat` signal is high, extra particles are emitted (pulse effect)

2. **Single Noise Force (Turbulence)**:
   - Type: Noise (procedural 3D noise field)
   - Strength: 0.5 (moderate chaotic motion)
   - Noise scale: 2.0 (frequency of noise variations)
   - Noise speed: 0.5 (how fast noise evolves over time)

3. **Rendering**:
   - Mode: `BILLBOARDS` (particles always face camera)
   - Point size: 3.0 pixels (base size, perspective-scaled in shader)
   - Blend mode: Additive (for glowing effect)
   - Texture: Optional particle sprite (if provided)

4. **Audio Reactivity**:
   - Audio sensitivity: 2.0 (higher than default, making particles more responsive)
   - Beat pulse: Emitter emits extra particles when beat is detected
   - Shader uniforms: `audio_bass`, `audio_mid`, `audio_treble`, `audio_beat` affect particle size and vertical displacement

### Macro-Parameter Mapping

The `set_parameter(name, value)` method maps user-friendly controls to internal system parameters:

| Macro Name | Mapping | Value Range (input) | Internal Effect |
|------------|---------|---------------------|-----------------|
| `turbulence` | `forces[0].strength = value * 2.0` | 0.0-1.0 → 0.0-2.0 | Increases noise force strength, making particles jitter more |
| `density` | `emitters[0].rate = value * 200.0` | 0.0-1.0 → 0-200 particles/frame | Controls emission rate (density of particle field) |
| `flow_speed` | `forces[0].noise_speed = value`<br>`emitters[0].initial_speed = value * 0.5` | 0.0-1.0 → 0.0-1.0 (noise)<br>0.0-0.5 (speed) | Speeds up noise evolution and particle initial velocity |

The `get_parameter(name)` method returns the normalized macro value (0.0-1.0) by reversing the mapping.

### Audio Reactivity Details

The system integrates with an audio analyzer (external) that provides four features per frame:
- `bass` (0.0-1.0): Low-frequency energy
- `mid` (0.0-1.0): Mid-frequency energy
- `treble` (0.0-1.0): High-frequency energy
- `beat` (0.0 or 1.0): Beat detection flag

These values are used in two ways:

1. **CPU-side**: The `emit_on_beat` flag on the emitter causes extra emission when `beat == 1`. The number of extra particles could be a multiplier on `rate`.

2. **GPU-side (vertex shader)**:
   - Particle Y position gets displaced: `pos.y += audio_bass * 0.1 * sin(pos.x * 5.0 + time)`
   - Particle size gets scaled: `size = props.y * (1.0 + audio_mid * 0.5)`
   - These create a throbbing, vibrating effect synchronized to music.

### Rendering Pipeline

The system uses GPU instancing via OpenGL:
- CPU updates particle positions, velocities, colors, sizes in NumPy arrays.
- Each frame, the active particle data is uploaded to VBOs (position, color, props).
- Vertex shader transforms particles with MVP matrix, applies audio displacement, computes point size.
- Fragment shader renders either circular points or textured sprites (if `use_texture=True`).
- Additive blending creates a glowing, metallic look.

The billboard rendering ensures particles always face the camera, giving a 2D sprite-like appearance in 3D space.

---

## Integration

### VJLive3 Pipeline Integration

`SilverVisionsEffect` is a **self-contained generator** that renders directly to the current framebuffer. It does not take input textures. It should be added to the effects chain as a source that other effects can composite over.

**Typical usage**:

```python
# Initialize
silver = SilverVisionsEffect()
silver.set_audio_features(bass=0.5, mid=0.3, treble=0.2, beat=1.0)  # Each frame
silver.update(delta_time)
silver.render()  # Draws to screen or current FBO
```

The effect requires an active OpenGL context with a valid camera and projection matrix set via the base class methods.

### Audio Integration

The effect expects audio features to be provided each frame via `set_audio_features(bass, mid, treble, beat)`. These values should come from an `AudioAnalyzer` instance that processes the audio input in real-time. The effect does not analyze audio itself.

---

## Performance

### Computational Cost

The system is **mixed CPU/GPU**, inheriting performance characteristics from `AdvancedParticle3DSystem`:

- **CPU**: Physics update for up to 10,000 particles. With default emission (500/frame) and lifetime (4s), active count ~2000. Each particle update: ~30 FLOPs. Total ~60,000 FLOPs/frame, negligible.
- **GPU**: Vertex shader for ~2000 particles, plus fragment shader for point sprites. Memory bandwidth: uploading ~2000 × 11 floats ≈ 88 KB per frame. Very light.

**Expected performance**: 60+ fps easily on integrated graphics; 2000 particles is conservative; can go up to 10,000 with care.

### Memory Usage

- **CPU**: NumPy arrays for max_particles (10,000) × (3+3+1+4+4) floats ≈ 150 KB
- **GPU**: VBOs ≈ 150 KB, shaders < 50 KB, optional texture ~16 KB
- **Total**: < 1 MB

### Optimization Strategies

- Use `glBufferSubData` with `GL_DYNAMIC_DRAW` for VBO updates.
- Consider using `glMapBuffer` for async updates if needed.
- Reduce `max_particles` on low-end hardware.

### Platform-Specific Considerations

- **Desktop**: No issues; OpenGL 3.3+ required.
- **Embedded (Raspberry Pi)**: May need to lower `max_particles` and `emit_rate`.
- **Mobile**: Use lower particle counts and avoid heavy turbulence.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without crashing if OpenGL context missing; raises clear error |
| `test_silver_presets_applied` | After init, emitter rate=500, noise strength=0.5, render mode=BILLBOARDS, colors set correctly |
| `test_macro_parameter_turbulence` | Setting `turbulence` from 0.0-1.0 scales `forces[0].strength` linearly 0.0-2.0 |
| `test_macro_parameter_density` | Setting `density` from 0.0-1.0 scales `emitters[0].rate` linearly 0-200 |
| `test_macro_parameter_flow_speed` | Setting `flow_speed` sets `forces[0].noise_speed` directly and `emitters[0].initial_speed` to value*0.5 |
| `test_get_parameter_returns_normalized` | `get_parameter("turbulence")` returns `forces[0].strength / 2.0` etc. |
| `test_audio_reactivity_emission` | When `audio_beat` is high, extra particles are emitted (check active_count increase) |
| `test_audio_reactivity_shader` | Audio uniforms affect vertex shader (size increase with audio_mid, Y displacement with audio_bass) |
| `test_color_gradient` | Particles spawn with colors interpolating from start to end over lifetime |
| `test_billboard_rendering` | Particles are rendered as screen-facing quads (check vertex shader output) |
| `test_inherited_functionality` | Base class methods (set_gravity, set_drag, etc.) still work |
| `test_cleanup` | All OpenGL resources released on stop() |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

