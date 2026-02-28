# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD32_Depth_Distance_Filter.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD32 — DepthDistanceFilterEffect

## Description

The Depth Distance Filter is a fundamental utility effect that isolates pixels based on their depth values, enabling depth-based compositing, virtual green screen effects, and selective processing. It acts as a depth-powered matte generator, allowing users to include or exclude specific depth ranges with soft, anti-aliased edges.

This effect is essential for building depth-aware workflows where different depth layers need to be treated separately. For example, you can isolate a foreground subject (near depth) and blur the background (far depth), or create a virtual green screen by making everything beyond a certain distance transparent.

## What This Module Does

- Filters video based on depth range: includes only pixels within a configurable near/far window
- Supports soft edge blending with configurable feather width for smooth transitions
- Provides multiple fill modes for excluded regions: transparent, solid color, blur, or secondary video input
- Includes mask refinement options: erosion, dilation, and feathering
- Integrates with `DepthEffect` base class for depth source management
- Uses GPU-accelerated fragment shaders for real-time performance at 60 FPS
- Can be used as a building block for more complex depth-based effects

## What This Module Does NOT Do

- Does NOT generate depth maps (requires external `AstraDepthSource`)
- Does NOT perform advanced matting (no edge detection, only depth-based)
- Does NOT handle multiple depth ranges simultaneously (single near/far window only)
- Does NOT provide CPU fallback (requires GPU for shader-based processing)
- Does NOT manage node graph connections (caller must route depth source and video)
- Does NOT store persistent state across sessions (all parameters in-memory)
- Does NOT implement temporal smoothing (per-frame only)

---

## Detailed Behavior

### Depth Range Filtering

The core functionality is to create a binary mask based on depth:

```
mask = 1.0 if (depth >= near_threshold) and (depth <= far_threshold) else 0.0
```

The mask is then used to composite the input video with the fill mode output.

### Soft Edges

To avoid hard boundaries, the effect applies feathering around the threshold edges using `softness` parameter:

```glsl
float near_edge = smoothstep(near_threshold - softness, near_threshold + softness, depth);
float far_edge = 1.0 - smoothstep(far_threshold - softness, far_threshold + softness, depth);
float mask = near_edge * far_edge;
```

This creates smooth transitions between included and excluded regions.

### Fill Modes

When pixels are outside the depth range (mask = 0), the effect replaces them according to `fill_mode`:

- **`transparent`**: Output alpha = 0, RGB unchanged (or set to 0). Allows downstream nodes to see through.
- **`color`**: Replace with solid color specified by `fill_color` (RGBA).
- **`blur`**: Apply a Gaussian blur to the input frame in excluded regions only (requires separate blur pass).
- **`secondary`**: Replace with pixels from a secondary video input (requires second input texture).

### Mask Refinement

Additional post-processing on the mask:

- **Erosion** (`erode`): Shrinks the included region by N pixels, useful for tightening the mask.
- **Dilation** (`dilate`): Expands the included region by N pixels, useful for including fringe areas.
- **Feather** (`feather`): Additional smoothness applied after erosion/dilation.

These operations are applied in order: erode → dilate → feather.

### Processing Pipeline

Each frame:

1. **Depth Fetch**: Sample depth map from depth source texture
2. **Range Test**: Compute base mask based on `near_threshold` and `far_threshold`
3. **Softness**: Apply smoothstep feathering using `softness` parameter
4. **Refinement**: Apply erosion, dilation, and additional feathering
5. **Fill**: For mask < 1.0, replace with fill mode output
6. **Output**: Return composited frame

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `near_threshold` | float | 0.3 | 0.0 - 1.0 | Minimum depth to include (0 = near plane) |
| `far_threshold` | float | 0.7 | 0.0 - 1.0 | Maximum depth to include (1 = far plane) |
| `softness` | float | 0.05 | 0.0 - 0.5 | Feather width around thresholds (normalized) |
| `fill_mode` | str | "transparent" | "transparent", "color", "blur", "secondary" | What to put in excluded regions |
| `fill_color` | tuple[float, float, float, float] | (0.0, 0.0, 0.0, 0.0) | RGBA 0-1 | Solid color when fill_mode="color" |
| `erode` | int | 0 | 0 - 10 | Erode mask by N pixels (morphological operation) |
| `dilate` | int | 0 | 0 - 10 | Dilate mask by N pixels |
| `feather` | float | 0.0 | 0.0 - 10.0 | Additional feathering after erosion/dilation |
| `invert` | bool | False | — | If true, invert mask (exclude inside range, include outside) |

---

## Public Interface

```python
class DepthDistanceFilterEffect:
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_secondary_input(self, texture: int) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame (HWC, 3 or 4 channels) | dtype: uint8 or float32 |
| `depth_source` | `AstraDepthSource` | Depth map provider | Must implement `get_depth_frame()` |
| `secondary_input` (optional) | `np.ndarray` or texture ID | Secondary video for fill_mode="secondary" | Must match frame resolution |

**Output**: `np.ndarray` — Filtered frame with depth-based masking applied, same shape/format as input (except alpha may be modified if fill_mode="transparent")

---

## State Management

**Persistent State:**
- `parameters: dict` — Current parameter values (see table above)
- `_depth_source: Optional[AstraDepthSource]` — Depth map provider
- `_depth_frame: Optional[np.ndarray]` — Cached depth map (updated each frame)
- `_depth_texture: int` — OpenGL texture ID for depth map
- `_shader: ShaderProgram` — Compiled fragment shader
- `_secondary_texture: int` — OpenGL texture ID for secondary input (if used)
- `_frame_width: int` — Current frame width
- `_frame_height: int` — Current frame height

**Per-Frame State:**
- Temporary shader uniform values
- Intermediate framebuffer bindings (if using blur fill mode)

**Initialization:**
- Depth texture created on first `update_depth_data()` or `process_frame()`
- Shader compiled in `__init__()`
- Secondary texture created when `set_secondary_input()` is called

**Cleanup:**
- Delete depth texture (`glDeleteTextures`)
- Delete secondary texture if allocated
- Delete shader program

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_R8 or GL_RGBA8 | frame size | Created on first depth update |
| Secondary texture (optional) | GL_TEXTURE_2D | GL_RGBA8 | frame size | Created when secondary input set |
| Main shader | GLSL program | vertex + fragment | N/A | Init once |
| Blur FBO (if blur fill) | Framebuffer | RGBA8 | frame size | Init on demand |

**Memory Budget (1080p):**
- Depth texture: ~2.1 MB (GL_R8)
- Secondary texture: ~8.3 MB (RGBA8)
- Blur FBO: ~8.3 MB (if used)
- Total: ~10.5 - 18.6 MB depending on fill mode

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth source not set | `RuntimeError("No depth source")` | Call `set_depth_source()` before `process_frame()` |
| Depth frame missing | `RuntimeError("Depth data not available")` | Ensure depth source is providing frames |
| Shader compilation failure | `ShaderCompilationError` | Log error, effect becomes no-op |
| Texture creation fails | `RuntimeError` | Propagate to caller; may indicate out of GPU memory |
| Invalid fill_mode | `ValueError("Invalid fill_mode")` | Validate against allowed modes |
| Secondary input not set when fill_mode="secondary" | `RuntimeError("Secondary input required")` | Call `set_secondary_input()` before processing |
| `near_threshold >= far_threshold` | Undefined behavior (empty range) | Validate `near_threshold < far_threshold` in `apply_uniforms()` |
| `softness` too large for range | Overlap causes full mask | Warn if `softness * 2 >= far_threshold - near_threshold` |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread owning the OpenGL context. The `_depth_frame` cache is per-instance and mutated each frame, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (1080p):**
- Depth lookup and mask computation: ~0.5 ms
- Erosion/dilation (if used): ~0.5-1 ms (depends on kernel size)
- Blur fill mode: ~2-3 ms additional (separate Gaussian blur pass)
- Secondary input blend: ~0.5 ms
- Total: ~1-2 ms (basic), ~3-5 ms (with blur), on discrete GPU

**Optimization Strategies:**
- Use `GL_R8` for depth texture to minimize memory bandwidth
- Implement erosion/dilation with separable filters (horizontal + vertical) for O(N) instead of O(N²)
- For blur fill mode, use a separable Gaussian blur (two passes) instead of full convolution
- Cache depth texture between frames; only update if depth source provides new data
- Early-out if `softness=0` and `erode=dilate=feather=0` (skip mask refinement)

---

## Integration Checklist

- [ ] Depth source is connected via `set_depth_source()` before processing
- [ ] Depth map resolution matches frame resolution (or effect handles resizing)
- [ ] Shader compiles successfully on all target platforms
- [ ] Parameters are validated before being sent to shader
- [ ] If using fill_mode="secondary", secondary input texture is set before `process_frame()`
- [ ] `cleanup()` is called when effect is destroyed to release GPU resources
- [ ] Pipeline orchestrator calls `update_depth_data()` each frame to refresh depth texture

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect instantiates without errors |
| `test_set_depth_source` | Depth source is stored correctly |
| `test_update_depth_data` | Depth texture is created/updated with valid data |
| `test_process_frame_no_depth` | Raises error if depth source not set |
| `test_process_frame_basic` | Basic filtering with hard edges works |
| `test_softness` | `softness` creates smooth transitions at thresholds |
| `test_fill_mode_transparent` | Excluded regions become transparent (alpha=0) |
| `test_fill_mode_color` | Excluded regions replaced with `fill_color` |
| `test_fill_mode_blur` | Excluded regions blurred (requires blur shader) |
| `test_fill_mode_secondary` | Excluded regions show secondary input |
| `test_erode_dilate` | Erosion and dilation correctly shrink/expand mask |
| `test_invert` | Invert flag reverses mask logic |
| `test_edge_cases` | `near=0, far=1` includes all; `near=1, far=0` includes none |
| `test_cleanup` | All GPU resources released |
| `test_secondary_input_set` | Secondary texture set correctly via `set_secondary_input()` |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD32: depth_distance_filter` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_distance_filter.py` — Original VJLive implementation
- `plugins/core/depth_distance_filter/__init__.py` — VJLive-2 version
- `plugins/vdepth/__init__.py` — Registration in depth plugin module
- `gl_leaks.txt` — Notes on texture allocation (missing `glDeleteTextures`)

Design decisions inherited:
- Effect name: `"depth_distance_filter"`
- Core parameters: `near_threshold`, `far_threshold`, `softness`
- Fill modes: "transparent", "color", "blur", "secondary"
- Mask refinement: erode, dilate, feather
- Uses `DEPTH_DISTANCE_FILTER_FRAGMENT` shader
- Texture resource management: allocates with `glGenTextures`, must free with `glDeleteTextures` (noted as missing in legacy)
- Inherits from base `Effect` class (not `DepthEffect` specifically, though it uses depth source)

---

## Notes for Implementers

1. **Depth Normalization**: The depth source may provide 16-bit or floating-point values. Normalize to [0,1] before threshold comparison. Use `depth_min` and `depth_max` parameters if the depth range is not 0-1.

2. **Softness Implementation**: Use `smoothstep` for anti-aliased edges:
   ```glsl
   float near_mask = smoothstep(near - softness, near + softness, depth);
   float far_mask = 1.0 - smoothstep(far - softness, far + softness, depth);
   float mask = near_mask * far_mask;
   ```

3. **Erosion/Dilation**: Implement as morphological operations on the mask. For efficiency, use a small kernel (3x3 or 5x5) and separable filters. Alternatively, use signed distance fields if precomputed.

4. **Blur Fill Mode**: This requires an additional rendering pass:
   - First pass: Render input frame to temporary FBO with Gaussian blur
   - Second pass: Composite blurred result with original using mask
   Consider using a separable blur (horizontal + vertical) for better performance.

5. **Secondary Fill Mode**: The secondary input is a separate video texture. It must be bound to a different texture unit and sampled in the shader when mask < 1.0.

6. **Transparent Fill Mode**: Set output alpha to `mask` and RGB to `input_rgb * mask`. This allows downstream nodes to blend with other layers.

7. **Color Fill Mode**: Output RGB = `fill_color.rgb` when mask < 1, else input RGB. Alpha can be 1.0 or mask.

8. **Performance**: This effect should be very fast (<1ms) for basic mode. Blur mode is the most expensive. Consider optimizing by:
   - Using `mediump` precision for mask calculations
   - Early-out if mask is exactly 0 or 1 (skip blur sampling)
   - Caching blurred frame if secondary input doesn't change

9. **Use Cases**: This effect is a building block. Common combinations:
   - Depth Distance Filter + Blur = depth-of-field effect
   - Depth Distance Filter + Color Grade = selective color correction by depth
   - Depth Distance Filter + Composite = foreground/background separation

10. **Audio Reactivity**: While not in the legacy spec, consider allowing audio to modulate thresholds:
    - `BEAT_INTENSITY` → `softness` (beats cause softer edges)
    - `ENERGY` → `near_threshold`/`far_threshold` (energy shifts depth window)

---

## Easter Egg Idea

When the `near_threshold` is set exactly to 0.333 and `far_threshold` to exactly to 0.666, and `softness` to exactly 0.0 (hard edges), and the depth map contains a perfect gradient, the mask briefly forms a hidden "rule of thirds" pattern where the included region exactly matches the golden ratio divisions for exactly 3.33 seconds before returning to normal. The pattern is visible only in the mask's alpha channel and requires a debug view to see, but subtly influences the filter's behavior in a way that VJs can feel rather than see.

---

## References

- VJLive1 legacy codebase: `vjlive1/plugins/depth_distance_filter.py` (if exists)
- Depth-based compositing: https://learnopengl.com/Advanced-Lighting/SSAO
- Morphological operations: https://en.wikipedia.org/wiki/Morphological_image_processing
- Gaussian blur: https://en.wikipedia.org/wiki/Gaussian_blur

---

## Implementation Tips

1. **Shader Structure**:
   ```glsl
   uniform sampler2D u_depth_texture;
   uniform sampler2D u_secondary_texture; // if needed
   uniform float u_near;
   uniform float u_far;
   uniform float u_softness;
   uniform int u_erode;
   uniform int u_dilate;
   uniform float u_feather;
   uniform int u_fill_mode; // 0=transparent, 1=color, 2=blur, 3=secondary
   uniform vec4 u_fill_color;
   
   void main() {
       float depth = texture(u_depth_texture, uv).r;
       float mask = compute_mask(depth);
       mask = apply_morphology(mask, u_erode, u_dilate);
       mask = apply_feather(mask, u_feather);
       vec4 color = apply_fill_mode(mask, u_fill_mode, u_fill_color, u_secondary_texture);
       fragColor = color;
   }
   ```

2. **Morphology**: For erosion/dilation, use a loop over a small kernel:
   ```glsl
   float erode(vec2 uv, float radius) {
       float min_val = 1.0;
       for (int i = -radius; i <= radius; i++) {
           for (int j = -radius; j <= radius; j++) {
               float sample = texture(mask_texture, uv + vec2(i,j)*pixel_size).r;
               min_val = min(min_val, sample);
           }
       }
       return min_val;
   }
   ```
   But this is expensive. Consider precomputing mask in a separate pass or using separable filters.

3. **Blur Optimization**: If blur fill mode is needed, consider using a two-pass separable blur:
   - Pass 1: Horizontal blur into temporary FBO
   - Pass 2: Vertical blur from temporary to final
   This reduces complexity from O(N²) to O(2N).

4. **Testing**: Create synthetic depth maps (gradient, steps, circles) to verify thresholding works correctly.

5. **Debug Mode**: Provide a debug output that shows the mask as a grayscale image to help users tune parameters.

6. **Resource Management**: The legacy code notes missing `glDeleteTextures`. Ensure your `cleanup()` deletes all textures and FBOs.

---
>>>>>>> REPLACE