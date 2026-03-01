# VJLive3 Depth Parallel Universe Module Specification

## Overview

The Depth Parallel Universe module extends VJLive3's effect system by introducing multi-universe branching and depth-based reality selection. This module creates three parallel processing chains (Universe A, B, and C) that process video frames with distinct datamosh effects, then merge them based on depth priority. Each universe operates independently with its own parameter set and can route to external processing chains, creating a complex, layered visual experience where foreground and background follow different laws of corruption.

The effect simulates a quantum superposition of realities: at each pixel, the depth map determines which universe's reality dominates, creating impossible visual transitions where close objects are aggressively glitched while distant objects are softly blurred. This creates a psychological effect of multiple realities coexisting in the same space.

## What This Module Does

The Depth Parallel Universe effect:

1. **Processes three independent datamosh chains** in parallel:
   - **Universe A (Near-field)**: Aggressive, block-based datamosh with high chaos
   - **Universe B (Mid-field)**: Smooth temporal blending with motion blur
   - **Universe C (Far-field)**: Glitch artifacts with RGB splitting and corruption

2. **Uses a depth map as a reality selector** to determine which universe's output dominates at each pixel location. The depth map acts as a continuous selector between the three universes, creating smooth transitions rather than hard boundaries.

3. **Supports four merge modes**:
   - `depth_priority`: The universe whose depth range contains the pixel's depth dominates
   - `additive`: All three universes are blended together
   - `multiply`: Universes are multiplied together (creates dark, dense effects)
   - `max`: The maximum value from all three universes is selected

4. **Enables external loop integration** where each universe can route its output to an external processing chain (e.g., another effect or a feedback loop) before merging.

5. **Creates cross-contamination** between universes via the `crossbleed` parameter, allowing one universe's artifacts to subtly influence others.

6. **Introduces quantum uncertainty** to create unpredictable, organic transitions between universes.

## What This Module Does NOT Do

- Does NOT generate depth maps (relies on external depth estimation)
- Does NOT perform audio analysis (purely visual)
- Does NOT handle video decoding or texture loading (relies on external texture manager)
- Does NOT provide a UI for parameter control (parameters set via set_parameter)
- Does NOT implement 3D rendering (2D full-screen effect)
- Does NOT manage feedback buffers (caller must provide texPrev)

---

## Detailed Behavior and Parameter Interactions

### Texture Inputs

The effect uses up to 6 texture units:

- `tex0` (unit 0): Primary video input (Video A). This is the source for all universes.
- `tex1` (unit 1): Secondary video input (Video B). Used as an alternative source for datamoshing.
- `texPrev` (unit 2): Previous frame buffer. Used for temporal effects in all universes.
- `depth_tex` (unit 3): Depth map. Used to determine which universe dominates at each pixel.
- `universe_a_return` (unit 4): External loop output for Universe A. Optional.
- `universe_b_return` (unit 5): External loop output for Universe B. Optional.
- `universe_c_return` (unit 6): External loop output for Universe C. Optional.

The effect checks if external loop textures are valid by sampling their center; if all channels sum to near zero, they're considered absent.

### Universe Processing

Each universe processes the input frame independently using a dedicated fragment shader function:

#### Universe A: Near-field Aggressive Datamosh

- **Purpose**: Creates aggressive, blocky corruption for foreground objects.
- **Mechanism**:
  - Divides screen into blocks based on `universe_a_block_size` (4-44 pixels)
  - Samples previous frame at block coordinates
  - Computes motion difference between current and previous frame
  - Applies chaotic displacement using hash functions
  - Blends displaced frame with original based on motion intensity
- **Parameters**:
  - `universe_a_depth_min`: 0.0-1.0, minimum depth for this universe (default 0.0)
  - `universe_a_depth_max`: 0.0-1.0, maximum depth for this universe (default 0.3)
  - `universe_a_mosh_intensity`: 0.0-1.0, strength of datamosh effect (default 0.8)
  - `universe_a_block_size`: 0.0-1.0, block size multiplier (0.0→4px, 1.0→44px)
  - `universe_a_chaos`: 0.0-1.0, randomness in displacement (default 0.5)
  - `universe_a_enable_loop`: 0 or 1, enable external loop (default 0)
  - `universe_a_loop_mix`: 0.0-1.0, blend between loop output and processed output (default 0.5)

#### Universe B: Mid-field Smooth Temporal Blend

- **Purpose**: Creates smooth, flowing transitions for mid-ground objects.
- **Mechanism**:
  - Blends current frame with previous frame using `universe_b_temporal_blend`
  - Applies motion blur by sampling 16 points in a circular pattern around each pixel
  - Uses golden angle sampling for even distribution
  - Blends blur with temporal blend
- **Parameters**:
  - `universe_b_depth_min`: 0.0-1.0, minimum depth for this universe (default 0.3)
  - `universe_b_depth_max`: 0.0-1.0, maximum depth for this universe (default 0.7)
  - `universe_b_mosh_intensity`: 0.0-1.0, strength of datamosh effect (default 0.5)
  - `universe_b_temporal_blend`: 0.0-1.0, blend between current and previous frame (default 0.6)
  - `universe_b_blur`: 0.0-1.0, blur radius and samples (default 0.7)
  - `universe_b_enable_loop`: 0 or 1, enable external loop (default 0)
  - `universe_b_loop_mix`: 0.0-1.0, blend between loop output and processed output (default 0.5)

#### Universe C: Far-field Glitch Artifacts

- **Purpose**: Creates glitchy, corrupted effects for background objects.
- **Mechanism**:
  - Uses temporal glitch triggers based on time and depth
  - Applies RGB splitting: shifts red and blue channels horizontally
  - Adds corruption: randomly replaces pixels with noise
- **Parameters**:
  - `universe_c_depth_min`: 0.0-1.0, minimum depth for this universe (default 0.7)
  - `universe_c_depth_max`: 0.0-1.0, maximum depth for this universe (default 1.0)
  - `universe_c_glitch_freq`: 0.0-1.0, frequency of glitch triggers (default 0.8)
  - `universe_c_rgb_split`: 0.0-1.0, horizontal offset for RGB channels (default 0.6)
  - `universe_c_corruption`: 0.0-1.0, intensity of pixel corruption (default 0.7)
  - `universe_c_enable_loop`: 0 or 1, enable external loop (default 0)
  - `universe_c_loop_mix`: 0.0-1.0, blend between loop output and processed output (default 0.5)

### Reality Merging

After processing, the three universes are merged based on the depth map and merge mode:

1. **Depth Priority (default)**:
   - For each pixel, determine which universe's depth range contains the pixel's depth
   - If depth is between `universe_a_depth_min` and `universe_a_depth_max`, use Universe A
   - If depth is between `universe_b_depth_min` and `universe_b_depth_max`, use Universe B
   - If depth is between `universe_c_depth_min` and `universe_c_depth_max`, use Universe C
   - If depth falls in multiple ranges, use the universe with the highest priority (A > B > C)
   - Uses `reality_threshold` to control sharpness of transitions between universes

2. **Additive**:
   - Sum the RGB values from all three universes
   - Clamp result to [0,1]
   - `crossbleed` parameter adds a small amount of each universe's output to the others

3. **Multiply**:
   - Multiply the RGB values from all three universes
   - This creates dark, dense effects
   - `crossbleed` parameter adds a small amount of each universe's output to the others

4. **Max**:
   - Select the maximum RGB value from all three universes
   - This creates bright, high-contrast effects
   - `crossbleed` parameter adds a small amount of each universe's output to the others

### Crossbleed and Quantum Uncertainty

- **Crossbleed**: A small amount of each universe's output is added to the others, creating subtle contamination. For example, Universe A's glitch might slightly influence Universe B's output, creating a "bleed" effect.
- **Quantum Uncertainty**: Adds random noise to the depth-based selection, creating unpredictable transitions between universes. This prevents the effect from feeling too mechanical.

### External Loop Integration

Each universe can route its output to an external processing chain:

1. The universe processes the input frame as normal
2. The output is sent to the external loop texture (e.g., another effect)
3. The external loop processes the frame and returns it
4. The returned texture is blended with the original universe output using `universe_x_loop_mix`

This allows for complex chains like:
- Universe A → Color Grade → Merge
- Universe B → Feedback Loop → Merge
- Universe C → Noise Generator → Merge

---

## Integration

### VJLive3 Pipeline Integration

`DepthParallelUniverseEffect` is an **Effect** that composites over the input framebuffer. It expects textures to be bound to specific units before rendering. The effect should be added to the effects chain and rendered with the appropriate texture bindings.

**Typical usage**:

```python
# Initialize
effect = DepthParallelUniverseEffect(
    texture0="video_a_tex_id",  # or path
    texture1="video_b_tex_id",  # optional
    depth_map="depth_tex_id"    # required
)

# Each frame:
# 1. Bind textures to units:
glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, tex0_id)
glActiveTexture(GL_TEXTURE1); glBindTexture(GL_TEXTURE_2D, tex1_id)  # if available
glActiveTexture(GL_TEXTURE2); glBindTexture(GL_TEXTURE_2D, prev_tex_id)  # previous frame
glActiveTexture(GL_TEXTURE3); glBindTexture(GL_TEXTURE_2D, depth_tex_id)  # required
glActiveTexture(GL_TEXTURE4); glBindTexture(GL_TEXTURE_2D, universe_a_return_id)  # optional
glActiveTexture(GL_TEXTURE5); glBindTexture(GL_TEXTURE_2D, universe_b_return_id)  # optional
glActiveTexture(GL_TEXTURE6); glBindTexture(GL_TEXTURE_2D, universe_c_return_id)  # optional

# 2. Set parameters
effect.set_parameter("universe_a_mosh_intensity", 0.8)
effect.set_parameter("universe_b_temporal_blend", 0.6)
effect.set_parameter("merge_mode", "depth_priority")
# ... etc.

# 3. Render (calls apply_uniforms and draws full-screen quad)
effect.render(time, resolution)
```

The effect requires an OpenGL context and a valid shader program.

### Texture Management

The effect does not own the textures; it expects them to be provided and bound. The `texture0`, `texture1`, `depth_map`, and loop textures can be either OpenGL texture IDs or paths that the texture manager can resolve. The effect should store these IDs and bind them in the correct order during `apply_uniforms`.

The `texPrev` texture is a feedback buffer: after rendering, the current frame should be copied to a texture for use in the next frame. This is managed by the caller.

---

## Performance

### Computational Cost

This effect is **GPU-bound** with a heavy fragment shader:

- The shader performs multiple texture lookups (up to 7 per pixel: tex0, tex1, texPrev, depth_tex, and up to 3 loop textures)
- It includes complex calculations for each universe (block processing, blur sampling, glitch triggers)
- At 1080p (2M pixels), the shader is expensive but should run at 60 Hz on modern GPUs. The biggest cost is the blur sampling in Universe B (16 samples per pixel) and the block processing in Universe A.

### Memory Usage

- **GPU**: Shader program (< 100 KB). No additional buffers.
- **CPU**: Small parameter storage (< 1 KB).

### Optimization Strategies

- Use lower resolution for the effect if performance is an issue (render to smaller FBO and upscale).
- Ensure texture units are cached and not re-bound unnecessarily.
- Consider using compute shaders for the blur sampling in Universe B.

### Platform-Specific Considerations

- **Desktop**: Should run fine on any GPU with OpenGL 3.3+.
- **Embedded**: May struggle with multiple texture fetches and complex calculations; consider simplifying effects or reducing resolution.
- **Mobile**: Use with caution; test on target devices.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without OpenGL context raises appropriate error |
| `test_basic_rendering` | Effect produces output without errors when all textures are valid |
| `test_missing_depth` | Effect fails gracefully if depth_map is not provided |
| `test_missing_tex1` | Effect works correctly when tex1 is not provided |
| `test_external_loop_missing` | Effect works correctly when external loop textures are not provided |
| `test_parameter_clamping` | All parameters are clamped to [0.0, 1.0] and out-of-range values are corrected |
| `test_universe_a_processing` | Universe A produces aggressive blocky corruption in near-field |
| `test_universe_b_processing` | Universe B produces smooth temporal blending in mid-field |
| `test_universe_c_processing` | Universe C produces RGB splitting and corruption in far-field |
| `test_depth_priority_merge` | Merge mode "depth_priority" selects correct universe based on depth |
| `test_additive_merge` | Merge mode "additive" correctly sums all universes |
| `test_multiply_merge` | Merge mode "multiply" correctly multiplies all universes |
| `test_max_merge` | Merge mode "max" correctly selects maximum values |
| `test_crossbleed_effect` | Crossbleed parameter adds subtle contamination between universes |
| `test_quantum_uncertainty` | Quantum uncertainty creates unpredictable transitions |
| `test_external_loop_integration` | External loop output is correctly blended with universe output |
| `test_cleanup` | All OpenGL resources (shader, FBOs if any) are released on stop() |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

