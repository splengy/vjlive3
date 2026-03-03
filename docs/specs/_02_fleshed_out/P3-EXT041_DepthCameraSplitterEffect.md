# DepthCameraSplitterEffect — Gateway Node for Depth Camera Setups

**Task ID:** P3-EXT041  
**Module:** `DepthCameraSplitterEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`DepthCameraSplitterEffect`](docs/specs/_02_fleshed_out/P3-EXT041_DepthCameraSplitterEffect.md:152) class is a gateway node that takes a depth camera source and splits it into four independent output streams: color (RGB), depth (grayscale), infrared (IR), and colorized depth. Each output can be independently routed through the graph for further processing. The effect provides real-time depth normalization, optional bilateral smoothing, and multiple false-color palettes for depth visualization.

**What This Module Does**

- Accepts a depth camera source providing color, depth, and optionally IR streams
- Normalizes depth values using near/far clip planes and gamma correction
- Outputs four selectable streams: color-enhanced, depth grayscale, IR-enhanced, colorized depth
- Applies optional bilateral smoothing to depth based on color similarity
- Provides three false-color palettes: Turbo, Thermal, Ocean
- Enhances color feed with exposure and saturation controls
- Enhances IR feed with brightness and contrast controls
- Manages OpenGL texture resources for depth and IR data
- Supports audio reactivity (though not used in current implementation)

**What This Module Does NOT Do**

- Does not perform depth camera calibration or intrinsic parameter handling
- Does not generate depth from stereo (requires external depth source)
- Does not support multiple depth cameras simultaneously (single source only)
- Does not provide point cloud generation or 3D reconstruction
- Does not include advanced depth processing like hole filling or edge-aware filtering beyond simple bilateral smoothing
- Does not support audio reactivity in the current implementation (infrastructure present but unused)

---

## Detailed Behavior and Parameter Interactions

### Texture Unit Layout

The effect uses the following texture units:

| Unit | Name | Type | Purpose |
|------|------|------|---------|
| 0 | `tex0` | `sampler2D` | Color video from depth camera |
| 2 | `depth_tex` | `sampler2D` | Depth map (single channel, normalized 0-1) |
| 3 | `ir_tex` | `sampler2D` | Infrared feed (single channel, normalized 0-1) |

**Important:** The depth and IR textures are dynamically updated from the `depth_source` each frame via `update_depth_data()`. The effect binds them to units 2 and 3 respectively.

### Core Algorithm: Multi-Output Depth Camera Processing

The effect operates as a multi-pass single-shader system. The Python class renders the same shader four times (once for each output) by setting `output_select` to 0, 1, 2, or 3. Each render populates a different output texture.

#### Shared Preprocessing: Depth Normalization and Smoothing

Before output selection, the shader normalizes and optionally smooths the depth:

1. **Normalization**:
   ```glsl
   float depth_norm = (depth_raw - depth_min) / max(depth_max - depth_min, 0.001);
   depth_norm = clamp(depth_norm, 0.0, 1.0);
   depth_norm = pow(depth_norm, depth_gamma);
   ```

   Where:
   - `depth_raw` is the raw depth value from `depth_tex.r`
   - `depth_min` and `depth_max` are user-controlled near/far clip planes (in normalized depth units 0-1)
   - `depth_gamma` applies a gamma curve to compress/expand depth ranges

2. **Bilateral Smoothing** (if `depth_smooth > 0`):
   ```glsl
   if (depth_smooth > 0.0) {
       float t = depth_smooth * 3.0 / resolution.x;
       float sum = depth_norm;
       float weight = 1.0;
       for (int x = -1; x <= 1; x++) {
           for (int y = -1; y <= 1; y++) {
               if (x == 0 && y == 0) continue;
               vec2 off = vec2(float(x), float(y)) * t;
               float s = texture(depth_tex, uv + off).r;
               s = clamp((s - depth_min) / max(depth_max - depth_min, 0.001), 0.0, 1.0);
               float color_sim = 1.0 - length(texture(tex0, uv + off).rgb - color) * 2.0;
               color_sim = max(color_sim, 0.1);
               sum += s * color_sim;
               weight += color_sim;
           }
       }
       depth_norm = sum / weight;
   }
   ```

   This is a 3x3 bilateral filter:
   - The sampling radius `t` scales with `depth_smooth` and inverse resolution
   - For each neighbor, it computes a color similarity weight: `color_sim = 1.0 - 2.0 * |color_diff|`
   - The depth sample is weighted by color similarity, preserving edges where color changes
   - This smooths depth while respecting color edges

#### Output Selection

The shader uses `output_select` (float) to choose which output to produce:

- **`output_select < 1.0`** → **COLOR OUT** (enhanced color feed)
- **`1.0 ≤ output_select < 2.0`** → **DEPTH OUT** (normalized grayscale depth)
- **`2.0 ≤ output_select < 3.0`** → **IR OUT** (enhanced infrared)
- **`output_select ≥ 3.0`** → **DEPTH COLORIZED** (false-color depth)

#### Color Output (0)

```glsl
vec3 enhanced = color * pow(2.0, (color_exposure - 0.5) * 2.0);
vec3 hsv = rgb2hsv(clamp(enhanced, 0.0, 1.0));
hsv.y *= color_saturation * 2.0;
hsv.y = clamp(hsv.y, 0.0, 1.0);
fragColor = vec4(hsv2rgb(hsv), 1.0);
```

- Exposure: multiplies color by `2^((exposure-0.5)*2)`. At `exposure=0.5`, factor = 1.0. At `exposure=1.0`, factor = 2^1 = 2.0 (brighter). At `exposure=0.0`, factor = 2^(-1) = 0.5 (darker).
- Saturation: multiplies HSV saturation by `color_saturation * 2.0`. At `saturation=0.5`, factor = 1.0. At `saturation=1.0`, factor = 2.0 (clamped to 1.0 max).

#### Depth Output (1)

```glsl
fragColor = vec4(vec3(depth_norm), 1.0);
```

Simple grayscale output of normalized depth.

#### IR Output (2)

```glsl
float ir = ir_raw * ir_brightness * 2.0;
ir = (ir - 0.5) * (1.0 + ir_contrast * 3.0) + 0.5;
fragColor = vec4(vec3(clamp(ir, 0.0, 1.0)), 1.0);
```

- Brightness: `ir_raw * brightness * 2.0` (double brightness at max)
- Contrast: `(ir - 0.5) * (1 + contrast*3) + 0.5`. At `contrast=0`, identity. At `contrast=1.0`, factor = 4.0, creating high contrast.

#### Colorized Depth Output (3)

```glsl
vec3 colorized;
if (colorize_palette < 3.3) {
    colorized = turbo_colormap(depth_norm);
} else if (colorize_palette < 6.6) {
    colorized = thermal_colormap(depth_norm);
} else {
    colorized = ocean_colormap(depth_norm);
}
fragColor = vec4(colorized, 1.0);
```

Three built-in false-color palettes:
- **Turbo** (0-3.3): Blue → cyan → green → yellow → orange → red
- **Thermal** (3.3-6.6): Dark blue → purple → orange → yellow → white
- **Ocean** (6.6-10.0): Dark blue → light blue → cyan

### Parameter Space and UI Mapping

All user-facing parameters use a normalized `0.0` to `10.0` range, except `output_select` which is an integer 0-3. The class uses `_map_param()` to convert these to shader-specific ranges:

| Parameter | UI Range | Shader Uniform | Internal Range | Purpose |
|-----------|----------|----------------|----------------|---------|
| `depthMin` | 0.0-10.0 | `depth_min` | 0.0-1.0 | Near clip for depth normalization |
| `depthMax` | 0.0-10.0 | `depth_max` | 0.0-1.0 | Far clip for depth normalization |
| `depthGamma` | 0.0-10.0 | `depth_gamma` | 0.2-3.0 | Gamma curve on depth |
| `irBrightness` | 0.0-10.0 | `ir_brightness` | 0.0-1.0 | IR feed brightness boost |
| `irContrast` | 0.0-10.0 | `ir_contrast` | 0.0-1.0 | IR contrast |
| `colorExposure` | 0.0-10.0 | `color_exposure` | 0.0-1.0 | Color feed exposure adjustment |
| `colorSaturation` | 0.0-10.0 | `color_saturation` | 0.0-1.0 | Color feed saturation |
| `colorizePalette` | 0.0-10.0 | `colorize_palette` | 0.0-10.0 | False-color palette selection (0=T, 3.3=Thermal, 6.6=Ocean) |
| `depthSmooth` | 0.0-10.0 | `depth_smooth` | 0.0-1.0 | Bilateral smoothing strength |

**Note:** The `_map_param(name, out_min, out_max)` function computes: `out_min + (val / 10.0) * (out_max - out_min)`.

### Audio Reactivity

The class has an `audio_reactor` attribute and `set_audio_analyzer()` method, but the `apply_uniforms` does **not** modulate any parameters based on audio. The infrastructure is present but unused. [NEEDS RESEARCH: Should audio reactivity be added?]

### Output Selection Mechanism

The effect does not have multiple output pins. Instead, it uses a single output that can be rendered four times with different `output_select` values. The host must call `set_output()` and then render the effect four times to collect all four streams. This is an unusual design but allows a single shader to produce multiple outputs without duplicating code.

---

## Public Interface

### Class: `DepthCameraSplitterEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT041_DepthCameraSplitterEffect.md:152) (from `core.effects.shader_base`)

**Constructor:** `__init__(self)`

Initializes the effect with default parameters and state:

```python
self.depth_source = None
self.depth_frame = None
self.depth_texture = 0
self.ir_texture = 0
self.parameters = {
    'depthMin': 1.0,
    'depthGamma': 5.0,
    'irBrightness': 5.0,
    'irContrast': 5.0,
    'colorExposure': 5.0,
    'colorSaturation': 5.0,
    'colorizePalette': 0.0,
    'depthSmooth': 3.0,
}
self.audio_reactor = None
self._current_output = 0  # 0=color, 1=depth, 2=IR, 3=colorized
```

**Properties:**

- `name = "depth_camera_splitter"`
- `fragment_shader = DEPTH_SPLITTER_FRAGMENT` — GLSL fragment shader (lines 24-148 in legacy file)
- `effect_category` — Not explicitly set; likely `"depth"` or `"utility"`
- `effect_tags` — Not explicitly set; based on description: `["depth", "camera", "splitter", "utility"]`
- `parameters` — Dictionary of 9 parameters (see above)
- `_current_output` — Integer 0-3 selecting which output to render

**Methods:**

- `set_depth_source(source)`: Set the depth camera source object. The source must have a `get_filtered_depth_frame()` method returning a numpy array of depth values (0-1 normalized) with shape (height, width).
- `set_audio_analyzer(analyzer)`: Set an audio analyzer for potential audio reactivity (currently unused).
- `set_output(output_idx)`: Set which output to render: 0=color, 1=depth, 2=IR, 3=colorized.
- `update_depth_data()`: Fetch the latest depth frame from `depth_source` and upload it to the `depth_texture` OpenGL texture. Also uploads IR if available. Called from `apply_uniforms`.
- `apply_uniforms(time_val, resolution, audio_reactor=None, semantic_layer=None)`: Overrides base to:
  - Call `update_depth_data()` to refresh depth/IR textures
  - Bind `tex0` to unit 0, `depth_tex` to unit 2, `ir_tex` to unit 3
  - Set `output_select` uniform to `float(self._current_output)`
  - Set all parameter uniforms via `_map_param`
- `__del__()`: Cleanup OpenGL textures (`glDeleteTextures`).

**Class Attributes:**

- `DEPTH_SPLITTER_FRAGMENT` — The full GLSL shader code (lines 24-148).
- `BASE_VERTEX_SHADER` — Inherited from `Effect`.

---

## Inputs and Outputs

### Inputs

| Pin | Type | Description |
|-----|------|-------------|
| `tex0` | `sampler2D` | Color video from depth camera (RGB) |
| `depth_tex` | `sampler2D` | Depth map (single channel, normalized 0-1) — dynamically updated from `depth_source` |
| `ir_tex` | `sampler2D` | Infrared feed (single channel, normalized 0-1) — dynamically updated from `depth_source` |
| `output_select` | `float` | Which output to produce: 0=color, 1=depth, 2=IR, 3=colorized |
| `depth_min` | `float` | Near clip for depth normalization (0.0-1.0) |
| `depth_max` | `float` | Far clip for depth normalization (0.0-1.0) |
| `depth_gamma` | `float` | Gamma correction for depth (0.2-3.0) |
| `ir_brightness` | `float` | IR brightness boost (0.0-1.0) |
| `ir_contrast` | `float` | IR contrast (0.0-1.0) |
| `color_exposure` | `float` | Color exposure (0.0-1.0) |
| `color_saturation` | `float` | Color saturation (0.0-1.0) |
| `colorize_palette` | `float` | False-color palette selector (0.0-10.0) |
| `depth_smooth` | `float` | Bilateral smoothing strength (0.0-1.0) |
| `time` | `float` | Shader time (unused in current shader) |
| `resolution` | `vec2` | Viewport resolution in pixels |

All parameters are passed as uniforms.

### Outputs

The effect produces a single output stream at a time, selected by `output_select`:

| `output_select` | Output Stream | Description |
|-----------------|---------------|-------------|
| 0.0 | Color (enhanced) | RGB color feed with exposure and saturation adjustments |
| 1.0 | Depth (grayscale) | Normalized depth map as grayscale |
| 2.0 | IR (enhanced) | Infrared feed with brightness and contrast adjustments |
| 3.0 | Depth colorized | False-color depth visualization using selected palette |

The host must render the effect four times (with `set_output(0)`, `set_output(1)`, `set_output(2)`, `set_output(3)`) to obtain all four streams. Each render writes to a separate output texture.

---

## Edge Cases and Error Handling

### Edge Cases

1. **No depth source**: If `depth_source` is `None`, `update_depth_data()` will not update `depth_frame`. The shader will sample `depth_tex` with whatever data was previously bound (likely black or stale data). The effect should still render but depth-based outputs will be invalid. The host should ensure a valid depth source is set before rendering.

2. **Depth frame empty**: If `depth_frame` is `None` or `depth_frame.size == 0`, the depth texture is not updated. Same consequence as above.

3. **Depth texture creation**: The first time depth data is uploaded, `glGenTextures(1)` is called. If OpenGL context is not current, this will fail. The host must ensure OpenGL context is active when calling `apply_uniforms`.

4. **IR not available**: Some depth cameras (e.g., Kinect, RealSense) provide IR; others may not. If `ir_tex` is not bound or is black, the IR output will be black. The host should handle missing IR gracefully.

5. **Depth normalization extremes**:
   - If `depth_min >= depth_max`, the normalization denominator becomes near-zero (clamped to 0.001), causing extreme values. The host should ensure `depth_min < depth_max`.
   - If depth values are outside `[depth_min, depth_max]`, they will be clamped to 0-1 after normalization. This may lose information.
   - `depth_gamma` can be very small (0.2) or large (3.0). Gamma < 1 expands bright depths; gamma > 1 compresses bright depths.

6. **Bilateral smoothing artifacts**: The bilateral filter uses a 3x3 kernel. If `depth_smooth` is high (1.0), the sampling radius `t = depth_smooth * 3.0 / resolution.x` can become large on low-resolution displays. For 1080p width, `t ≈ 3.0/1920*3 ≈ 0.0047` at max smooth, which is small. Actually: `t = 1.0 * 3.0 / 1920 ≈ 0.00156` UV units — very small. This seems too small to have visible effect. Possibly the formula should be `depth_smooth * 0.03` or something. [NEEDS RESEARCH: verify smoothing radius]

7. **Color similarity weighting**: The bilateral weight uses `color_sim = 1.0 - length(color_diff) * 2.0`. If color difference is >0.5, `color_sim` becomes negative, but then clamped to `max(0.1)`. This ensures a minimum weight of 0.1, preventing total exclusion. This is safe.

8. **IR contrast formula**: `(ir - 0.5) * (1.0 + ir_contrast * 3.0) + 0.5`. With `ir_contrast=1.0`, factor = 4.0, so `ir` can easily go outside 0-1, but it's clamped at the end. Safe.

9. **Color exposure**: `color * pow(2.0, (color_exposure - 0.5) * 2.0)`. At `color_exposure=1.0`, factor = 2^1 = 2.0; at `color_exposure=0.0`, factor = 2^(-1) = 0.5. The result is clamped before HSV conversion. Safe.

10. **Palette selection**: The `colorize_palette` parameter is compared against 3.3 and 6.6 to select palette. Values outside 0-10 will still select one of the three palettes (e.g., negative → turbo, >10 → ocean). This is safe.

11. **Texture binding**: The effect binds `tex0` to unit 0, `depth_tex` to unit 2, `ir_tex` to unit 3. The host must ensure these units are available and that the appropriate textures are bound when drawing. The effect manages its own `depth_texture` and `ir_texture` IDs but does not manage `tex0` (that's the input video).

12. **OpenGL resource cleanup**: The `__del__` method attempts to delete `depth_texture` but not `ir_texture` (which is never created separately? Actually `ir_texture` is set to 0 but never generated; the shader samples `ir_tex` but the code does not create a texture for IR. Looking at `apply_uniforms`, it only creates `depth_texture` if needed. It sets `ir_tex` uniform to 3 but does not bind an IR texture. This is a bug: the IR texture is never uploaded. The legacy code likely expects IR to be provided as an extra texture from the host, not generated internally. [NEEDS RESEARCH: verify IR handling]

### Error Handling

- **OpenGL errors**: `glGenTextures`, `glBindTexture`, `glTexImage2D` can fail if OpenGL context is invalid. The code does not check errors. This is typical for performance-critical code but can cause silent failures.
- **Parameter clamping**: The `_map_param` method does not clamp the result to the target range; it relies on the shader to clamp. For most parameters this is fine because the shader uses `clamp` or the math naturally bounds values. However, `color_saturation` multiplies by 2.0 and then clamps; `color_exposure` uses `pow` and then clamps. The Python side should ideally clamp parameter values to [0.0, 10.0] before mapping, but the base class may handle that.
- **No NaN propagation**: All math is well-conditioned with proper clamping.

---

## Mathematical Formulations

### Parameter Remapping

For each parameter `p_ui` ∈ [0, 10], the shader uniform `u_p` is computed as:

```
u_p = p_min + (p_ui / 10.0) * (p_max - p_min)
```

where the `(p_min, p_max)` pairs are:

| Parameter | `p_min` | `p_max` |
|-----------|---------|---------|
| `depthMin` | 0.0 | 1.0 |
| `depthMax` | 0.0 | 1.0 |
| `depthGamma` | 0.2 | 3.0 |
| `irBrightness` | 0.0 | 1.0 |
| `irContrast` | 0.0 | 1.0 |
| `colorExposure` | 0.0 | 1.0 |
| `colorSaturation` | 0.0 | 1.0 |
| `colorizePalette` | 0.0 | 10.0 |
| `depthSmooth` | 0.0 | 1.0 |

### Depth Normalization

```
depth_norm = (depth_raw - depth_min) / (depth_max - depth_min + ε)
depth_norm = clamp(depth_norm, 0.0, 1.0)
depth_norm = depth_norm ^ depth_gamma
```

where `ε = 0.001` to avoid division by zero.

### Bilateral Smoothing

For each neighbor `(x, y)` in a 3x3 grid (excluding center):

```
offset = (x, y) * t   where t = depth_smooth * 3.0 / resolution.x
s = sample(depth_tex, uv + offset)
s_norm = (s - depth_min) / (depth_max - depth_min + ε)
color_diff = |color(uv) - color(uv+offset)|
color_sim = max(1.0 - 2.0 * color_diff, 0.1)
weighted_sum += s_norm * color_sim
total_weight += color_sim
depth_norm_smooth = weighted_sum / total_weight
```

### Color Enhancement

```
enhanced = color * 2^((color_exposure - 0.5) * 2)
HSV = rgb2hsv(enhanced)
HSV.saturation *= color_saturation * 2.0
HSV.saturation = clamp(HSV.saturation, 0.0, 1.0)
output = hsv2rgb(HSV)
```

### IR Enhancement

```
ir = ir_raw * ir_brightness * 2.0
ir = (ir - 0.5) * (1.0 + ir_contrast * 3.0) + 0.5
output = clamp(ir, 0.0, 1.0)
```

### False-Color Palettes

Three piecewise linear gradients:

- **Turbo**: 4 segments (blue→cyan, cyan→green, green→yellow, yellow→orange→red)
- **Thermal**: 3 segments (dark blue→purple, purple→orange, orange→yellow→white)
- **Ocean**: 2 segments (dark blue→light blue, light blue→cyan)

All use `mix` with linear interpolation.

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: Moderate. The shader performs:
  - 3 texture samples: `tex0` (color), `depth_tex`, `ir_tex` (IR may be unused if black)
  - If `depth_smooth > 0`: additional 8 depth samples and 8 color samples in 3x3 loop (total 11 extra samples)
  - Color space conversions: `rgb2hsv` and `hsv2rgb` for color output (expensive: multiple divisions, sqrt-like operations)
  - False-color palette: simple piecewise linear, cheap
- **No loops** beyond the fixed 3x3 smoothing (unrolled by compiler)
- **Moderate GPU load**: This is a `MEDIUM` tier effect as per plugin manifest. Expect 2-5ms per 1080p frame with smoothing disabled; up to 8-12ms with smoothing enabled due to extra texture fetches.

### Memory Usage

- **Uniforms**: 9 floats + `output_select` + standard uniforms (time, resolution) = ~12 uniforms.
- **Textures**: Requires 3 texture units bound simultaneously.
- **Framebuffer**: The effect does not use feedback; no extra framebuffer needed.
- **Dynamic textures**: The effect manages one or two dynamic textures (`depth_texture`, potentially `ir_texture`). In the current code, only `depth_texture` is created and updated; `ir_tex` is not bound to a texture object. This appears to be a bug or incomplete implementation. [NEEDS RESEARCH]

### GPU Optimization Notes

- The bilateral smoothing is the most expensive part (8 extra texture fetches per pixel). Could be optimized with separable filters or by using a lower-resolution depth map.
- The HSV conversions are expensive; could be approximated with polynomial or lookup if performance is critical.
- The effect is suitable for real-time at 1080p on modern GPUs, but may struggle at 4K with smoothing enabled.
- The `output_select` mechanism requires rendering the same geometry four times to get all outputs. This quadruples the cost if all outputs are needed. Consider using multiple render targets (MRT) if available.

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python)

1. **Parameter remapping**: Verify `_map_param()` for all parameters produces correct ranges (e.g., `depthMin=5.0` → 0.5).
2. **Parameter clamping**: If `set_parameter` exists, test clamping to [0.0, 10.0].
3. **Get/set symmetry**: For each parameter, verify `get_parameter` returns the value set.
4. **Default parameters**: Verify all 9 parameters have expected default values.
5. **Output selection**: Test `set_output()` sets `_current_output` correctly.
6. **Depth source**: Test `set_depth_source()` sets the source correctly.
7. **Audio analyzer**: Test `set_audio_analyzer()` sets `audio_reactor`.
8. **Uniform setting**: Test that `apply_uniforms` calls `update_depth_data` and sets all expected uniforms (`tex0`, `depth_tex`, `ir_tex`, `output_select`, and all parameters).
9. **Depth data update**: Mock a depth source and verify `update_depth_data` populates `depth_frame` and creates `depth_texture`.
10. **OpenGL texture creation**: Verify `glGenTextures` is called when depth texture is first created.
11. **Cleanup**: Test that `__del__` attempts to delete `depth_texture`.

### Integration Tests (Shader Rendering)

12. **Color output**: Render with `output_select=0` and verify exposure/saturation adjustments are applied.
13. **Depth output**: Render with `output_select=1` and verify grayscale depth matches normalized depth.
14. **IR output**: Render with `output_select=2` and verify brightness/contrast adjustments.
15. **Colorized depth**: Render with `output_select=3` and verify false-color palettes (test palette selection boundaries).
16. **Depth normalization**: Test `depth_min` and `depth_max` clipping and scaling.
17. **Depth gamma**: Test `depth_gamma` compresses/expands depth range.
18. **Bilateral smoothing**: Test `depth_smooth` reduces depth noise while preserving edges (compare with color edges).
19. **Smoothing radius**: Verify smoothing radius scales with `depth_smooth` and inverse resolution.
20. **All outputs in sequence**: Render all four outputs and verify they are distinct and correct.
21. **Depth source update**: Call `update_depth_data` multiple times and verify texture is updated.
22. **Edge case: no depth source**: Render with `depth_source=None` and verify behavior (likely uses previous texture or black).
23. **Edge case: empty depth frame**: Render with empty `depth_frame` and verify behavior.
24. **Audio reactivity**: Not applicable (not implemented). [NEEDS RESEARCH]

### Performance Tests

25. **Benchmark 1080p**: Measure frame time with default parameters and smoothing disabled/enabled.
26. **Texture sample count**: Use GPU profiling to verify sample count (3 base, +8 with smoothing).
27. **Four-output cost**: Measure total time to render all four outputs (should be ~4x single-output cost).

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT041: DepthCameraSplitterEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementations:

- [`plugins/vdepth/depth_camera_splitter.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/vdepth/depth_camera_splitter.py:1) (VJlive Original) — Full implementation with shader code (lines 24-148) and class (lines 152-243).
- [`plugins/core/depth_camera_splitter/__init__.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/core/depth_camera_splitter/__init__.py:1) (VJlive-2 Legacy) — Same implementation in a different plugin location.
- [`plugins/vdepth/__init__.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/vdepth/__init__.py:1) — Registration of the effect in the depth plugin module.

The legacy code validates the parameter ranges, default values, and multi-output architecture described in this spec. The effect is a critical utility node for depth camera integration, providing normalized depth, enhanced color/IR, and colorized depth visualization.

---

## Open Questions / [NEEDS RESEARCH]

- **IR texture binding**: The `apply_uniforms` sets `ir_tex` uniform to 3 but does not create or bind an `ir_texture` object. The shader samples `ir_tex` but the Python code never uploads IR data. Is IR expected to be provided as an extra texture from the host? Or should the class create an `ir_texture` similar to `depth_texture`? The legacy `depth_source` may provide IR data; the code has `self.ir_texture = 0` but never generates it. This appears to be a bug or incomplete implementation. [NEEDS RESEARCH — check if depth_source.get_filtered_depth_frame() returns both depth and IR, or if there's a separate IR source]
- **Bilateral smoothing radius**: The formula `t = depth_smooth * 3.0 / resolution.x` yields a very small radius (e.g., ~0.0016 at 1080p). Is this intended to be in UV space? Should it be larger? Perhaps it should be `depth_smooth * 3.0` (pixel offset) divided by resolution to convert to UV? That would be `depth_smooth * 3.0 / resolution.x` as written, but `depth_smooth` max 1.0 gives 3/1920 ≈ 0.0016, which is a 3-pixel radius? Actually, if `t` is in UV, then `uv + (x,y)*t` with x,y in {-1,0,1} gives a maximum offset of about 0.0016, which is about 3 pixels at 1920 width (0.0016*1920 ≈ 3). So it is a 3-pixel radius at max smooth. That seems reasonable. But the multiplication by `depth_smooth` means at `depth_smooth=1.0`, radius = 3 pixels; at `depth_smooth=0.5`, radius = 1.5 pixels. This is plausible. However, the code uses `depth_smooth * 3.0 / resolution.x`, and the loop uses `int x = -1; x <= 1`, so the maximum offset is `1 * t`. So the radius in pixels is `t * resolution.x = depth_smooth * 3.0`. So indeed the radius in pixels is `3 * depth_smooth`. At max, 3 pixels. That's a very small smoothing radius; typical bilateral filters use larger kernels (e.g., 5x5 or 7x7). This may be too weak. [NEEDS RESEARCH — verify intended smoothing strength]
- **Audio reactivity**: The class has `set_audio_analyzer` and `audio_reactor` but does not use them in `apply_uniforms`. Should audio modulate any parameters (e.g., depth gamma, color saturation)? [NEEDS RESEARCH]
- **Output selection efficiency**: The design requires four separate renders to get all outputs. Could this be optimized with multiple render targets (MRT) or by outputting all four as a texture array? [NEEDS RESEARCH — but likely out of scope for spec]
- **Depth source interface**: The `depth_source` is expected to have `get_filtered_depth_frame()` returning a numpy array. What is the shape and dtype? Likely (H, W) float32 normalized 0-1. Should also provide IR? The code sets `ir_tex` uniform but never uploads IR data. Perhaps the depth source returns a tuple (depth, ir) or the IR is obtained elsewhere. [NEEDS RESEARCH]
- **Colorize palette options**: Only three palettes are defined. Should more be added? Are the palette boundaries (3.3, 6.6) hardcoded? Could they be parameters? [NEEDS RESEARCH]
- **Missing `u_mix`**: The class does not include `u_mix` in its parameters. The base `Effect` class may handle mixing. Is this correct? [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*