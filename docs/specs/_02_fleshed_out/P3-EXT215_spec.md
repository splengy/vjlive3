# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT215_bad_trip_datamosh.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT215 — BadTripDatamoshEffect

**What This Module Does**

The `BadTripDatamoshEffect` is a psychedelic, horror-themed video effect that simulates a psychological breakdown through aggressive visual distortions. It combines dual video inputs (primary and secondary) with an optional depth map to produce a wide range of unsettling effects: facial distortion into demonic forms, insect-like crawling noise, screen tearing, paranoia strobes, void gaze, breathing walls, and more. The effect is entirely shader-based and runs in real-time, with each effect's intensity controlled by a uniform parameter (0.0–1.0).

The effect is designed to be used as a VJ tool for creating intense, nightmare-inducing visuals. It is self-contained as a fragment shader that samples multiple textures and applies a sequence of transformations.

**What This Module Does NOT Do**

- Does NOT perform audio analysis (it's purely visual)
- Does NOT handle video decoding or texture loading (relies on external texture management)
- Does NOT provide a UI for parameter control (parameters set via set_parameter)
- Does NOT implement 3D rendering (2D full-screen effect)
- Does NOT include fallback for missing depth map (depth is optional but effects degrade gracefully)

---

## Detailed Behavior and Parameter Interactions

### Texture Inputs

The effect uses up to 4 texture units:

- `tex0` (unit 0): Primary video input (Video A). This is the main source.
- `texPrev` (unit 1): Previous frame buffer. Used for feedback/time loop effect.
- `depth_tex` (unit 2): Depth map (optional). Used for facial distortion and shadow people. If not provided, a default depth (e.g., 1.0) can be used.
- `tex1` (unit 3): Secondary video input (Video B). Used for reality tear effect and as an alternative source when dual mode is active.

The effect checks if `tex1` is valid by sampling its center; if all channels sum to near zero, it's considered absent.

### Effect Pipeline (Shader Order)

The fragment shader processes effects in a specific order:

1. **Breathing Walls**: Warps UV coordinates based on radial distance from center, creating a pulsing, organic distortion.
2. **Demon Face**: If depth indicates a nearby face (depth > 0.2), adds high-frequency horizontal warping and hollows out eye regions.
3. **Insect Crawl**: Adds random, tiny UV offsets based on a hash function, simulating bugs crawling under the skin.
4. **Base Color Selection**: After UV modifications, samples either `tex1` (if dual) or `tex0` as the base color, and also samples `texPrev` for feedback.
5. **Time Loop**: Mixes current frame with previous frame: `color = mix(color, prev, u_time_loop * 0.5)`.
6. **Reality Tear**: Randomly replaces portions of the image with the alternate video (or inverted) based on a hash threshold.
7. **Sickness**: Applies a green/purple tint that oscillates with time.
8. **Shadow People**: Darkens areas where depth is low (background) to create shadowy figures.
9. **Psychosis**: Inverts colors based on parameter: `color.rgb = abs(color.rgb - vec3(u_psychosis * 0.5))`.
10. **Void Gaze**: Applies a vignette that darkens edges, with intensity controlled by `u_void_gaze`.
11. **Doom**: Crushes contrast: `color.rgb = (color.rgb - 0.5) * (1.0 + u_doom) + 0.5`.
12. **Paranoia**: Randomly sets color to black with low probability if `u_paranoia > 0`.
13. **Final Mix**: Multiplies by `u_mix` (blend factor) and outputs.

### Parameter Descriptions

| Uniform | Type | Range | Effect |
|---------|------|-------|--------|
| `u_anxiety` | float | 0.0–1.0 | Controls speed/intensity of jitter and breathing walls frequency |
| `u_demon_face` | float | 0.0–1.0 | Amount of facial distortion (warping, eye hollowing) |
| `u_insect_crawl` | float | 0.0–1.0 | Density of bug-like noise; higher = more frequent UV jumps |
| `u_void_gaze` | float | 0.0–1.0 | Vignette strength; darkens periphery, creates "hole" effect |
| `u_reality_tear` | float | 0.0–1.0 | Probability and intensity of screen tearing revealing alternate video |
| `u_sickness` | float | 0.0–1.0 | Tint strength (green/purple) |
| `u_time_loop` | float | 0.0–1.0 | Feedback amount mixing with previous frame (echo) |
| `u_breathing_walls` | float | 0.0–1.0 | UV warping amplitude for organic pulsing |
| `u_paranoia` | float | 0.0–1.0 | Strobe probability; higher = more frequent black frames |
| `u_shadow_people` | float | 0.0–1.0 | Darkening of background (low depth) areas |
| `u_psychosis` | float | 0.0–1.0 | Color inversion/hue shift intensity |
| `u_doom` | float | 0.0–1.0 | Contrast boost/crush |
| `u_mix` | float | 0.0–1.0 | Overall effect blend (0 = original, 1 = full effect) |

All parameters are settable at runtime via `set_parameter(name, value)`.

### Shader Utilities

The shader includes helper functions:
- `hash(vec2 p)`: pseudo-random hash returning [0,1]
- `noise(vec2 p)`: smooth value noise using bilinear interpolation of hash

These are used for procedural effects (insect crawl, reality tear, paranoia).

---

## Integration

### VJLive3 Pipeline Integration

`BadTripDatamoshEffect` is an **Effect** that composites over the input framebuffer. It expects textures to be bound to specific units before rendering. The effect should be added to the effects chain and rendered with the appropriate texture bindings.

**Typical usage**:

```python
# Initialize
effect = BadTripDatamoshEffect(
    texture0="video_a_tex_id",  # or path
    texture1="video_b_tex_id",  # optional
    depth_map="depth_tex_id"    # optional
)

# Each frame:
# 1. Bind textures to units:
glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, tex0_id)
glActiveTexture(GL_TEXTURE1); glBindTexture(GL_TEXTURE_2D, prev_tex_id)  # previous frame
glActiveTexture(GL_TEXTURE2); glBindTexture(GL_TEXTURE_2D, depth_tex_id)  # if available
glActiveTexture(GL_TEXTURE3); glBindTexture(GL_TEXTURE_2D, tex1_id)  # if available

# 2. Set parameters
effect.set_parameter("u_demon_face", 0.8)
effect.set_parameter("u_insect_crawl", 0.3)
# ... etc.

# 3. Render (calls apply_uniforms and draws full-screen quad)
effect.render(time, resolution)
```

The effect requires an OpenGL context and a valid shader program.

### Texture Management

The effect does not own the textures; it expects them to be provided and bound. The `texture0`, `texture1`, `depth_map` arguments can be either OpenGL texture IDs or paths that the texture manager can resolve. The effect should store these IDs and bind them in the correct order during `apply_uniforms`.

The `texPrev` texture is a feedback buffer: after rendering, the current frame should be copied to a texture for use in the next frame. This is managed by the caller.

---

## Performance

### Computational Cost

This effect is **GPU-bound** with a heavy fragment shader:

- The shader performs multiple texture lookups (up to 5 per pixel: tex0, texPrev, depth_tex, tex1, plus noise functions).
- It includes many conditional branches based on uniform values. However, most uniforms are constant across the frame, so the GPU can optimize.
- At 1080p (2M pixels), the shader is moderately expensive but should run at 60 Hz on modern GPUs. The biggest cost is the texture bandwidth: 5 textures × 2M pixels = 10M texels per frame. That's ~160 MB/s at 60 Hz (assuming 16 bytes per texel read), which is fine.

### Memory Usage

- **GPU**: Shader program (< 100 KB). No additional buffers.
- **CPU**: Small parameter storage (< 1 KB).

### Optimization Strategies

- Use lower resolution for the effect if performance is an issue (render to smaller FBO and upscale).
- Ensure texture units are cached and not re-bound unnecessarily.
- Consider merging some conditionals into a single pass to reduce branching, but not critical.

### Platform-Specific Considerations

- **Desktop**: Should run fine on any GPU with OpenGL 3.3+.
- **Embedded**: May struggle with multiple texture fetches; consider simplifying effects or reducing resolution.
- **Mobile**: Use with caution; test on target devices.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without crashing if OpenGL context missing (should raise error) |
| `test_basic_rendering` | Effect produces output without errors when all textures are valid |
| `test_missing_tex1` | Effect works correctly when tex1 is not provided (reality tear uses fallback) |
| `test_missing_depth` | Effect works without depth map (depth effects degrade gracefully) |
| `test_parameter_clamping` | All parameters are clamped to [0.0, 1.0] and out-of-range values are corrected |
| `test_breathing_walls_effect` | When u_breathing_walls > 0, UVs are warped radially |
| `test_demon_face_effect` | When depth > 0.2 and u_demon_face > 0, UV warping and eye hollowing occur |
| `test_insect_crawl_effect` | When u_insect_crawl > 0, random UV offsets appear |
| `test_time_loop_feedback` | u_time_loop mixes current frame with previous frame |
| `test_reality_tear_effect` | u_reality_tear causes random patches to show alternate video or inversion |
| `test_sickness_tint` | u_sickness applies green/purple tint |
| `test_shadow_people_darken` | u_shadow_people darkens low-depth areas |
| `test_psychosis_inversion` | u_psychosis inverts colors |
| `test_void_gaze_vignette` | u_void_gaze darkens screen edges |
| `test_doom_contrast` | u_doom increases contrast |
| `test_paranoia_strobe` | u_paranoia occasionally sets frame to black |
| `test_cleanup` | All OpenGL resources (shader, FBOs if any) are released on stop() |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

