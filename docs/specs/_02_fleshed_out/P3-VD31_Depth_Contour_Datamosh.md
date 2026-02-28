# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD31_Depth_Contour_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD31 — DepthContourDatamoshEffect

## Description

The Depth Contour Datamosh effect extracts iso-depth contour lines (like topographic map elevation lines) from a depth map and concentrates datamosh artifacts along these contours. This creates unique "topographic layer-cake" glitch patterns where each depth slice corrupts independently, producing a distinctive 3D-like datamosh effect that follows the depth structure of the scene.

The effect combines depth-based contour detection with datamosh algorithms (block corruption, motion simulation, temporal displacement) to create complex glitch patterns that respect depth boundaries. Contours can be configured to have varying widths, smoothness, and separation, allowing for effects ranging from subtle topographic lines to dramatic layer-cake corruption.

## What This Module Does

- Extracts iso-depth contour lines from a depth map using configurable interval and width parameters
- Concentrates datamosh artifacts (block corruption, motion displacement, temporal glitches) along contour lines
- Supports multiple datamosh techniques: flow-based displacement, cross-contamination between layers, temporal coherence
- Provides per-contour colorization and glow effects for enhanced visual impact
- Implements feedback and accumulation loops for temporal persistence
- Integrates with `DepthEffect` base class for depth source management
- Uses GPU-accelerated fragment shaders for real-time performance at 60 FPS
- Includes preset configurations for common styles: "topo_map" and "flowing_contours"

## What This Module Does NOT Do

- Does NOT generate depth maps (requires external `AstraDepthSource`)
- Does NOT perform general datamosh outside of contour regions (artifacts are contour-concentrated)
- Does NOT implement full video encoding/decoding datamosh (only visual simulation)
- Does NOT provide CPU fallback (requires GPU for shader-based processing)
- Does NOT handle audio analysis (relies on `AudioReactor` for feature extraction)
- Does NOT manage node graph connections (caller must route depth source and video)
- Does NOT store persistent state across sessions (all parameters in-memory)
- Does NOT support 3D geometry reconstruction (purely 2D image effect using depth)

---

## Detailed Behavior

### Contour Extraction

The effect extracts contour lines from the depth map by identifying pixels that fall within specific depth intervals. A contour is defined as the set of pixels where:

```
fract(depth / contourInterval) < contourWidth
```

Where:
- `depth` is normalized depth value [0.0, 1.0]
- `contourInterval` controls spacing between contour lines (higher = fewer contours)
- `contourWidth` controls thickness of each contour line (0.0-1.0)

The `numContours` parameter limits the maximum number of contours extracted, starting from the nearest depth and progressing outward.

### Contour Smoothing

To avoid aliasing and create smooth contour bands, the `contourSmoothness` parameter applies a smoothstep function:

```glsl
float contour_band = smoothstep(0.0, contourSmoothness, fract(depth / interval));
```

This creates anti-aliased edges and allows for soft, gradient-like contour transitions when `contourSmoothness` is high.

### Datamosh Artifact Types

The effect applies several datamosh techniques specifically along contour lines:

1. **Flow Strength** (`flowStrength`):
   - Displaces pixels along the contour direction using a flow vector field
   - Creates a "flowing" or "smearing" effect parallel to contour lines
   - Implementation: Offset texture coordinates by `flow_strength * flow_vector`

2. **Cross-Contamination** (`crossContamination`):
   - Allows datamosh artifacts to bleed across adjacent contour lines
   - Higher values cause contours to merge and corrupt each other
   - Implementation: Sample neighboring depth layers and mix

3. **Layer Separation** (`layerSeparation`):
   - Controls the visual gap between depth layers after corruption
   - Creates a "layer-cake" effect where each depth band appears as a separate corrupted layer
   - Implementation: Offset each contour band by a depth-dependent amount

4. **Temporal Coherence** (`temporalCoherence`):
   - Controls how much the datamosh pattern persists across frames
   - Low values cause rapid, random corruption; high values create stable, evolving patterns
   - Implementation: Mix current frame's corruption with previous frame's result

5. **Contour Glow** (`contourGlow`):
   - Adds a glowing halo around contour lines
   - Implementation: Apply a Gaussian blur or distance-based falloff around contour edges

6. **Chromatic Contour** (`chromaticContour`):
   - Splits RGB channels along contours, creating chromatic aberration/glitch effects
   - Implementation: Offset R, G, B channels by different amounts based on contour membership

### Colorization

Contours can be tinted with a specific color using `contourColorR`, `contourColorG`, `contourColorB`. This color is multiplied with the datamosh result, allowing for colored contour lines (e.g., green for topographic maps).

### Feedback and Accumulation

The effect supports two temporal mechanisms:

- **Feedback** (`feedbackStrength`): Blends a portion of the previous frame's output into the current frame, creating trailing/smearing effects. The feedback is scaled by `contour_strength` so that only contour regions accumulate.

- **Accumulation** (`accumulation`): Takes the maximum value between current frame's datamosh result and the previous frame's direct output. This creates a "burn-in" effect where corrupted areas persist and build up over time.

### Processing Pipeline

Each frame, the effect executes:

1. **Depth Fetch**: Sample depth map from depth source texture
2. **Contour Detection**: Compute contour mask where `fract(depth/interval) < width`
3. **Contour Smoothing**: Apply smoothstep based on `contourSmoothness`
4. **Flow Displacement**: Offset texture coordinates using flow vector field
5. **Cross-Contamination**: Sample neighboring depth layers and blend
6. **Layer Separation**: Apply depth-based offsets to create layer-cake effect
7. **Chromatic Split**: Offset RGB channels independently if enabled
8. **Colorization**: Apply contour color tint
9. **Glow**: Add halo effect around contour edges
10. **Temporal**: Apply feedback and accumulation
11. **Blend**: Mix with original frame using `u_mix`

### Presets

Two built-in presets provide starting configurations:

- **`topo_map`**: Emulates a topographic map with green contour lines, moderate flow, and clear layer separation. Parameters: `contourInterval=4.0`, `contourWidth=3.0`, `contourColorG=8.0`, `layerSeparation=3.0`.

- **`flowing_contours`**: Creates a more fluid, organic glitch effect with higher `numContours`, lower `contourWidth`, and stronger `flowStrength`. Parameters: `contourInterval=3.0`, `contourWidth=2.0`, `numContours=6.0`, `flowStrength=5.0`.

---

## Public Interface

```python
class DepthContourDatamoshEffect:
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_audio_analyzer(self, audio_analyzer) -> None: ...
    def load_preset(self, preset_name: str) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame (HWC, 3 or 4 channels) | dtype: uint8 or float32 |
| `depth_source` | `AstraDepthSource` | Depth map provider | Must implement `get_depth_frame()` |
| `audio_analyzer` | `AudioAnalyzer` | Optional audio feature source | Provides BEAT_INTENSITY, TEMPO, ENERGY |

**Output**: `np.ndarray` — Processed frame with contour-concentrated datamosh, same shape/format as input

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `contourInterval` | float | 4.0 | 0.1 - 20.0 | Spacing between contour lines (depth units) |
| `contourWidth` | float | 3.0 | 0.0 - 1.0 | Thickness of contour lines (normalized) |
| `numContours` | float | 4.0 | 1.0 - 20.0 | Maximum number of contour lines to extract |
| `contourSmoothness` | float | 5.0 | 0.0 - 10.0 | Anti-aliasing smoothness for contour edges |
| `flowStrength` | float | 3.0 | 0.0 - 10.0 | Strength of flow-based displacement along contours |
| `crossContamination` | float | 1.0 | 0.0 - 10.0 | How much adjacent contour layers bleed into each other |
| `layerSeparation` | float | 3.0 | 0.0 - 10.0 | Visual gap between depth layers (layer-cake effect) |
| `temporalCoherence` | float | 6.0 | 0.0 - 10.0 | Persistence of datamosh pattern across frames |
| `contourGlow` | float | 4.0 | 0.0 - 10.0 | Intensity of glow around contour edges |
| `chromaticContour` | float | 2.0 | 0.0 - 10.0 | Strength of RGB channel splitting on contours |
| `contourColorR` | float | 0.0 | 0.0 - 10.0 | Red component of contour tint (0=no tint) |
| `contourColorG` | float | 8.0 | 0.0 - 10.0 | Green component of contour tint |
| `contourColorB` | float | 10.0 | 0.0 - 10.0 | Blue component of contour tint |
| `topographicSteps` | float | 3.0 | 1.0 - 10.0 | Number of discrete steps in layer-cake quantization |
| `feedbackStrength` | float | 2.0 | 0.0 - 10.0 | Amount of temporal feedback (trailing) |
| `accumulation` | float | 1.0 | 0.0 - 10.0 | Accumulation strength (burn-in) |
| `blend` | float | 0.8 | 0.0 - 1.0 | Blend factor between original and processed frame |

---

## State Management

**Persistent State:**
- `parameters: dict` — Current parameter values (see table above)
- `_depth_source: Optional[AstraDepthSource]` — Depth map provider
- `_depth_frame: Optional[np.ndarray]` — Cached depth map (updated each frame)
- `_depth_texture: int` — OpenGL texture ID for depth map
- `_shader: ShaderProgram` — Compiled fragment shader
- `_previous_frame: Optional[np.ndarray]` — Previous output for feedback/accumulation
- `_frame_width: int` — Current frame width
- `_frame_height: int` — Current frame height

**Per-Frame State:**
- Temporary shader uniform values
- Intermediate framebuffer bindings
- Contour mask texture (optional, can be computed on-the-fly)

**Initialization:**
- Depth texture created on first `update_depth_data()` or `process_frame()`
- Shader compiled in `__init__()`
- Previous frame buffer allocated in `set_frame_size()` or first `process_frame()`

**Cleanup:**
- Delete depth texture (`glDeleteTextures`)
- Delete previous frame framebuffer/texture
- Delete shader program

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_R8 or GL_RGBA8 | frame size | Created on first depth update, recreated if resolution changes |
| Previous frame FBO | Framebuffer | RGBA8 | frame size | Created on first frame, reused |
| Main shader | GLSL program | vertex + fragment | N/A | Init once |

**Memory Budget (1080p):**
- Depth texture: ~2.1 MB (GL_R8)
- Previous frame FBO: ~8.3 MB (RGBA8)
- Total: ~10.4 MB + shader overhead

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth source not set | `RuntimeError("No depth source")` | Call `set_depth_source()` before `process_frame()` |
| Depth frame missing | `RuntimeError("Depth data not available")` | Ensure depth source is providing frames |
| Shader compilation failure | `ShaderCompilationError` | Log error, effect becomes no-op |
| Texture/FBO creation fails | `RuntimeError` | Propagate to caller; may indicate out of GPU memory |
| Invalid parameter value | Shader undefined behavior | Document ranges; optionally clamp in `apply_uniforms()` |
| Resolution mismatch | Textures size ≠ frame size | Recreate textures/FBOs with correct dimensions |
| `contourInterval <= 0` | Division by zero in shader | Validate `contourInterval > 0` in `apply_uniforms()` |
| `numContours < 1` | No contours extracted | Validate `numContours >= 1` |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread owning the OpenGL context. The `_depth_frame` and `_previous_frame` caches are per-instance and mutated each frame, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (1080p):**
- Contour detection in shader: ~1-2 ms
- Flow displacement and cross-contamination: ~1-2 ms
- Layer separation and chromatic split: ~1 ms
- Temporal feedback/accumulation: ~0.5 ms
- Total: ~3-5 ms on discrete GPU, ~8-12 ms on integrated GPU

**Optimization Strategies:**
- Use `GL_R8` for depth texture to minimize memory bandwidth
- Precompute contour mask in a separate pass if it's reused across multiple effects
- Early-out if `blend == 0` (return original frame)
- Cache depth texture between frames; only update if depth source provides new data
- Consider using half-float framebuffers (RGBA16F) if HDR processing is needed

---

## Integration Checklist

- [ ] Depth source is connected via `set_depth_source()` before processing
- [ ] Depth map resolution matches frame resolution (or effect handles resizing)
- [ ] Shader compiles successfully on all target platforms
- [ ] Parameters are validated before being sent to shader
- [ ] `cleanup()` is called when effect is destroyed to release GPU resources
- [ ] Pipeline orchestrator calls `update_depth_data()` each frame to refresh depth texture
- [ ] Previous frame buffer is properly managed (copy before next frame if using feedback)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect instantiates without errors |
| `test_set_depth_source` | Depth source is stored correctly |
| `test_update_depth_data` | Depth texture is created/updated with valid data |
| `test_process_frame_no_depth` | Raises error if depth source not set |
| `test_process_frame_with_depth` | Applies contour datamosh and returns frame of correct shape |
| `test_contour_extraction` | Contour mask correctly identifies iso-depth lines |
| `test_flow_displacement` | `flowStrength` controls displacement amount |
| `test_cross_contamination` | Adjacent contours mix when `crossContamination > 0` |
| `test_layer_separation` | `layerSeparation` creates visible gaps between depth bands |
| `test_temporal_coherence` | Low `temporalCoherence` causes rapid changes; high causes stability |
| `test_feedback_accumulation` | Feedback and accumulation produce expected temporal effects |
| `test_preset_loading` | Presets correctly set all related parameters |
| `test_cleanup` | All GPU resources released |
| `test_audio_reactivity` | Audio features modulate parameters if reactor connected |
| `test_blend_factor` | `blend=0` returns original, `blend=1` returns fully processed |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD31: depth_contour_datamosh` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_contour_datamosh.py` — Original VJLive implementation
- `plugins/core/depth_contour_datamosh/__init__.py` — VJLive-2 version with presets
- `plugins/vdepth/__init__.py` — Registration in depth plugin module
- `gl_leaks.txt` — Notes on texture allocation (missing `glDeleteTextures`)

Design decisions inherited:
- Effect name: `"depth_contour_datamosh"`
- Contour extraction using `fract(depth / interval)` method
- Preset parameters: `contourInterval`, `contourWidth`, `flowStrength`, `crossContamination`, `layerSeparation`, `temporalCoherence`, `contourGlow`, `chromaticContour`, etc.
- Uses `DEPTH_CONTOUR_DATAMOSH_FRAGMENT` shader (implements multi-stage pipeline)
- Feedback and accumulation stages in the shader
- Texture resource management: allocates with `glGenTextures`, must free with `glDeleteTextures` (noted as missing in legacy)
- Inherits from base `Effect` class (not `DepthEffect` specifically, though it uses depth source)

---

## Notes for Implementers

1. **Contour Detection Algorithm**: The core contour detection is `float contour = step(contourWidth, fract(depth * numContours / contourInterval))`. This creates binary masks. For smoother contours, use `smoothstep` with `contourSmoothness`.

2. **Flow Vector Field**: The `flowStrength` parameter requires a flow vector field. This can be generated procedurally in the shader using a noise function or derived from the depth gradient (depth changes indicate surface orientation). Consider using a simple curl noise or Perlin noise for organic flow.

3. **Cross-Contamination**: Implement by sampling depth values at slightly offset coordinates and blending based on the difference between those depths and the current depth. This simulates corruption spreading across depth boundaries.

4. **Layer Separation**: To create the "layer-cake" effect, offset the final color by a depth-dependent amount: `vec2 offset = vec2(0, layerSeparation * depth);`. This shifts each depth layer vertically or horizontally, creating a stepped appearance.

5. **Chromatic Contour**: Split RGB channels by sampling the source texture at slightly different offsets for each channel, where the offset magnitude is proportional to `chromaticContour` and the contour mask.

6. **Temporal Coherence**: Store the previous frame's datamosh result in a texture. Mix current result with previous based on `temporalCoherence`: `final = mix(current, previous, 1.0 - temporalCoherence)`. This creates smooth evolution.

7. **Feedback and Accumulation**: The legacy shader shows:
   ```glsl
   if (feedback_strength > 0.0) {
       result = mix(result, previous, feedback_strength * 0.3 * contour_strength);
   }
   if (accumulation > 0.0) {
       vec4 prev_direct = texture(texPrev, uv);
       result = max(result, prev_direct * accumulation * 0.5 * contour_strength);
   }
   ```
   Replicate this logic exactly for similar behavior.

8. **Performance**: The effect is moderately heavy due to multiple texture samples and complex shader math. Optimize by:
   - Using `mediump` or `lowp` precision where acceptable
   - Reducing texture fetches (sample depth once, reuse)
   - Early-out if pixel is not on a contour (skip expensive operations)

9. **Presets**: The two presets provided are just examples. Consider adding more:
   - "subtle_contours": low `contourWidth`, low `flowStrength`
   - "extreme_glitch": high `crossContamination`, high `chromaticContour`
   - "neon_topo": colored contours with high `contourGlow`

10. **Audio Reactivity**: Map audio features to parameters for dynamic control:
    - `BEAT_INTENSITY` → `contourGlow` (beats make contours flash)
    - `ENERGY` → `flowStrength` (high energy increases flow)
    - `TEMPO` → `contourInterval` (faster tempo = closer contours)

---

## Easter Egg Idea

When the `contourInterval` is set exactly to 0.618 (golden ratio conjugate) and `numContours` to exactly 8, and the depth map contains a perfect gradient, the contour lines briefly form a hidden golden spiral pattern that lasts exactly 3.33 seconds before returning to normal. The spiral is visible only in the contour mask's alpha channel and requires a debug view to see, but subtly influences the flow displacement in a way that VJs can feel rather than see.

---

## References

- VJLive1 legacy codebase: `vjlive1/plugins/depth_contour_datamosh.py` (if exists)
- Topographic map algorithms: https://en.wikipedia.org/wiki/Topographic_map
- Datamosh techniques: https://github.com/terorie/glitch-this
- ShaderToy contour examples: https://www.shadertoy.com/view/4dlyR4

---

## Implementation Tips

1. **Shader Structure**: Organize the fragment shader into functions:
   - `float get_contour_mask(float depth)` — returns 0.0 or 1.0 (or smooth value)
   - `vec2 get_flow_vector(vec2 uv, float depth)` — returns displacement offset
   - `vec3 apply_datamosh(vec3 color, vec2 uv, float depth, float contour)` — main datamosh logic
   - `void main()` — orchestrates the pipeline

2. **Precision**: Use `highp float` for depth calculations to avoid banding artifacts, especially at high resolutions.

3. **Testing**: Create synthetic depth maps (gradients, steps, spheres) to verify contour extraction works correctly.

4. **Debugging**: Provide a debug mode that outputs the contour mask as a grayscale image to verify contour detection parameters.

5. **Resource Management**: The legacy code notes missing `glDeleteTextures`. Ensure your `cleanup()` deletes all textures and FBOs.

---
>>>>>>> REPLACE