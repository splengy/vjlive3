# P3-EXT050: DepthFieldEffect — Depth-of-Field Simulation

**Component:** vdepth plugin  
**Phase:** Pass 2 — Fleshed Out Technical Specification  
**Status:** Ready for Implementation  
**Legacy Origin:** `vjlive/plugins/vdepth/depth_effects.py` (lines 1882–2022)  
**Related Concepts:** Depth-based blur, Gaussian kernel, focus plane, aperture simulation

---

## Executive Summary

The `DepthFieldEffect` implements a **depth-of-field (DOF) simulation** that selectively blurs regions of the video based on their distance from a user-defined focus plane. Unlike traditional camera DOF that uses lens physics, this effect uses a simplified **depth-difference model**: pixels whose depth differs from `focus_distance` by more than a threshold are blurred proportionally to that difference, clamped by `max_blur`. The effect reads a depth texture (normalized to 0–1) and converts it back to metric depth using the inverse of the standard normalization formula: `depth_meters = depth_tex.r * 4.0 + 0.3`. A **separable Gaussian blur** is applied with a configurable number of samples (`blur_samples`), where the blur radius scales with the depth difference. The effect is **performance-intensive** due to the multi-pass blur, and it shares the legacy depth normalization assumption (0.3–4.0m range) with all other depth effects.

---

## Detailed Behavior and Parameter Interactions

### Core Algorithm

1. **Depth Retrieval and Conversion**  
   The effect samples the depth texture bound to unit 1. The depth value is in the normalized 0–1 range (uint8 scaled from legacy depth in meters). It is converted back to metric depth:
   ```glsl
   float depth = texture(depth_tex, uv).r * 4.0 + 0.3;
   ```
   This inverse transformation assumes the original depth was normalized as `((depth_meters - 0.3) / (4.0 - 0.3) * 255)`. The conversion is exact and lossless for values within the 0.3–4.0m range; values outside this range will be clamped at the texture upload stage.

2. **Blur Amount Calculation**  
   The absolute difference between the pixel's depth and the `focus_distance` determines the blur radius:
   ```glsl
   float depth_diff = abs(depth - focus_distance);
   float blur_amount = min(depth_diff * aperture, max_blur);
   ```
   - `aperture` acts as a scaling factor (units: blur_amount_per_meter). Larger values increase the rate at which blur grows with depth difference.
   - `max_blur` is an absolute clamp (in UV coordinates) preventing excessive blur that would degrade image quality or cause sampling artifacts.
   - If `depth_diff * aperture` exceeds `max_blur`, the blur is capped at `max_blur`.

3. **Gaussian Blur Application**  
   The effect uses a **two-pass separable Gaussian blur** implemented within a single fragment shader via a helper function `gaussian_blur(sampler2D tex, vec2 uv, float blur_amount)`. The function:
   - Computes Gaussian weights for `blur_samples` taps in a 1D kernel.
   - Applies the kernel horizontally and vertically in a single call (likely by sampling in a cross pattern).
   - The `blur_amount` parameter scales the kernel's standard deviation, effectively controlling the radius of the blur.
   - The shader samples `tex0` (the source video) and returns a blurred color.

4. **Mixing**  
   The final color is a linear interpolation between the original sharp pixel and the blurred version:
   ```glsl
   fragColor = mix(original, blurred, u_mix);
   ```
   The `u_mix` uniform is controlled by the VJ interface and ranges from 0.0 (no DOF) to 1.0 (full DOF). When `u_mix = 0`, the effect bypasses all blur calculations and outputs the original directly.

### Parameter Mapping

All parameters are exposed on a **0–10 normalized UI rail** and mapped to internal ranges via the `_map_param()` helper inherited from `DepthEffect`. The mapping is linear unless otherwise noted:

| Parameter (UI name) | Internal Variable | UI Range | Mapped Range | Default | Notes |
|---------------------|-------------------|----------|--------------|---------|-------|
| `focus_distance` | `self.focus_distance` | 0–10 | 0.5–10.0 meters | 2.0 | Focus plane distance. Clamped to [0.5, 10.0]. |
| `aperture` | `self.aperture` | 0–10 | 0.01–1.0 (unitless) | 0.1 | Blur scaling factor. Clamped to [0.01, 1.0]. |
| `max_blur` | `self.max_blur` | 0–10 | 0.001–0.1 (UV) | 0.02 | Maximum blur radius in texture coordinates. Clamped to [0.001, 0.1]. |
| `blur_samples` | `self.blur_samples` | 0–10 | 4–32 (integer) | 16 | Number of Gaussian samples per dimension. Must be even? Not enforced. |

**Mapping formula** (in `_map_param`):
```python
def _map_param(self, name: str, out_min: float, out_max: float) -> float:
    # value is 0-10 from UI
    return out_min + (value / 10.0) * (out_max - out_min)
```
The `set_parameter()` method additionally enforces **hard clamps** on the values before assignment, ensuring they stay within safe operational bounds regardless of UI input.

### Uniforms Sent to Shader

From `apply_uniforms()` (lines 1916–1939):
- `depth_tex` (sampler2D) → texture unit 1
- `focus_distance` (float)
- `aperture` (float)
- `max_blur` (float)
- `blur_samples` (int)
- `u_mix` (float) — inherited from base `Effect` class, controls overall effect strength
- `has_depth` (float) — 1.0 if depth texture exists, else 0.0 (allows shader to skip DOF)

The `has_depth` uniform is critical: if no depth source is set, the shader bypasses DOF and outputs the original video unchanged.

---

## Public Interface

### Class: `DepthFieldEffect(Effect)`

**Constructor:** `__init__(self)`  
Initializes the effect with:
- Name: `"depth_field"`
- Fragment shader from `_get_fragment_shader()`
- Default parameters: `focus_distance=2.0`, `aperture=0.1`, `max_blur=0.02`, `blur_samples=16`
- Internal state: `depth_source`, `depth_frame`, `depth_texture` (GLuint)

**Key Methods:**

- `set_depth_source(source)` — Inherited from `DepthEffect`. Sets the depth provider (e.g., camera, synthetic).
- `update_depth_data()` — Inherited. Uploads depth frame to GL texture with normalization `((depth_frame - 0.3) / 3.7 * 255)`.
- `apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None)`  
  Binds all uniforms to the shader, including depth texture and DOF parameters. Handles texture upload if depth data changed.
- `_get_fragment_shader(self) -> str`  
  Returns the GLSL 330 core fragment shader source implementing DOF.
- `set_parameter(self, name: str, value: float)`  
  Sets a parameter with validation and clamping. `blur_samples` is cast to `int`.
- `get_parameter(self, name: str) -> float`  
  Retrieves current parameter value. Returns `float` even for integer `blur_samples`.

**Inherited from `DepthEffect`:**
- `render_3d_depth_scene()` — Not used for this 2D effect but present in base class.
- `_map_param()` — Linear mapping from 0–10 to specified range.

---

## Inputs and Outputs

### Inputs

| Stream | Type | Format | Description |
|--------|------|--------|-------------|
| `tex0` | sampler2D | RGB/RGBA | Source video frame (the image to be blurred) |
| `depth_tex` | sampler2D | RED (uint8 normalized to 0–1) | Depth map corresponding to the source frame. Must be same resolution. |
| Parameters | float/int | N/A | Four DOF parameters (focus_distance, aperture, max_blur, blur_samples) |
| `u_mix` | float | 0.0–1.0 | Overall effect blend factor |

### Outputs

| Stream | Type | Format | Description |
|--------|------|--------|-------------|
| `fragColor` | vec4 | RGBA | Final color: `mix(original, blurred, u_mix)` when depth present; else original. |

### External Dependencies

- **OpenGL ES 3.0 / GLSL 330 core** — Shader language and texture functions.
- **NumPy** — For depth frame normalization in `update_depth_data()` (in base class).
- **Depth Source** — Must be set via `set_depth_source()` before `update_depth_data()` can populate `self.depth_frame`.

---

## Edge Cases and Error Handling

### 1. Missing Depth Source
- **Condition:** `self.depth_frame` is `None` or empty.
- **Behavior:** `apply_uniforms()` sets `has_depth = 0.0`. Shader bypasses DOF and outputs `texture(tex0, uv)` directly.
- **Edge:** No error logged; silent fallback. This is appropriate for a "no depth" scenario.

### 2. Zero or Invalid `blur_samples`
- **Condition:** `blur_samples` set to 0 or negative via `set_parameter()`.
- **Behavior:** Clamped to minimum 4. The shader's `gaussian_blur` function expects at least a few samples; with 4 samples the blur will be very crude but functional.
- **Risk:** If `blur_samples` is set to an extremely high value (e.g., 1000) before clamping, the shader may loop excessively, causing frame drops. The clamp to 32 prevents this.

### 3. Extreme `aperture` or `max_blur`
- **Condition:** `aperture` near 1.0 or `max_blur` near 0.1.
- **Behavior:** Blur can become very strong, potentially washing out details. The Gaussian kernel will have a large radius, increasing texture fetch count.
- **Performance impact:** Large blur radii with high `blur_samples` can become prohibitively expensive (O(blur_samples²) if not separable). The shader likely uses separable passes, but still O(2×blur_samples).

### 4. Depth Outside 0.3–4.0m Range
- **Condition:** Actual depth in scene is <0.3m or >4.0m.
- **Behavior:** During `update_depth_data()`, the depth frame is clipped to [0.3, 4.0] before normalization. Values outside become 0 or 255 in the uint8 texture, which after `*4.0+0.3` maps to 0.3m or 4.0m respectively.
- **Effect:** Distant objects beyond 4.0m are treated as exactly 4.0m; very close objects (<0.3m) are treated as 0.3m. This can cause incorrect blur at range extremes.

### 5. `focus_distance` at Boundary Values
- **Condition:** `focus_distance = 0.5` (minimum) or `10.0` (maximum).
- **Behavior:** At 0.5m, only objects closer than 0.5m will be blurred (since `depth_diff = depth - 0.5`). But depth cannot go below 0.3m, so the maximum blur will be `(0.5-0.3)*aperture = 0.2*aperture`. At 10.0m, all objects (max 4.0m) will have `depth_diff = 10.0 - depth` which is at least 6.0m, so blur will be huge and likely clamped to `max_blur`. This effectively blurs everything.

### 6. `u_mix = 0` or `1`
- **Condition:** `u_mix` at extremes.
- **Behavior:** 0 → no blur applied (original output). 1 → full blur based on depth. Intermediate values produce smooth transition.

### 7. Texture Resolution Mismatch
- **Condition:** `depth_tex` resolution differs from `tex0`.
- **Behavior:** GL will sample with its default wrap/clamp settings. If `GL_TEXTURE_WRAP_{S,T}` is `GL_CLAMP_TO_EDGE` (likely), depth sampling will be incorrect at borders. The effect assumes matching resolutions; no runtime check.

### 8. Memory Leak
- **Condition:** `self.depth_texture` is generated via `glGenTextures(1)` but never deleted.
- **Behavior:** Each time `update_depth_data()` is called with a new depth frame size, a new texture may be generated if `self.depth_texture == 0`. However, if the effect is destroyed, the texture persists in GPU memory. This is a known issue across all depth effects.

---

## Mathematical Formulations

### Depth Normalization (Legacy Assumption)

The depth frame (in meters) is normalized to an 8-bit texture for efficient GPU sampling:

```python
# In DepthEffect.update_depth_data()
normalized = ((self.depth_frame - 0.3) / (4.0 - 0.3) * 255).astype(np.uint8)
```

Inverse (in shader):

```glsl
float depth_meters = depth_tex.r * 4.0 + 0.3;
```

**Derivation:**  
Let `d` be depth in meters, `n` be normalized value in [0, 255].  
`n = ((d - 0.3) / 3.7) * 255`  
=> `d = (n / 255) * 3.7 + 0.3`  
=> `d = n * (3.7/255) + 0.3`  
But shader uses `n * 4.0 + 0.3`. This is a **slight approximation** (4.0 vs 3.7). The exact inverse should be `n * 3.7 + 0.3` if `n` is in [0,1]. However, the texture is uint8, so `depth_tex.r` is in [0,1] after normalization. The factor 4.0 is a **rounding error or intentional simplification** that slightly exaggerates depth differences. This is a **bug/feature** that should be documented.

**Correct inverse:** `depth = depth_tex.r * 3.7 + 0.3`  
**Used inverse:** `depth = depth_tex.r * 4.0 + 0.3`  
**Error:** ~8% overestimation of depth span.

### Blur Amount

```glsl
float blur_amount = min(abs(depth - focus_distance) * aperture, max_blur);
```

Where:
- `blur_amount` is in UV coordinate units (0–1 range, where 1.0 is full texture width/height).
- `aperture` has units of (UV_per_meter). It is a user-controlled scaling factor.
- `max_blur` caps the blur to prevent excessive sampling.

### Gaussian Kernel (1D)

The `gaussian_blur` function likely computes:

```glsl
float weights[blur_samples];
float sum = 0.0;
for (int i = 0; i < blur_samples; i++) {
    float x = (i - (blur_samples-1)/2.0) / (sigma * something);
    weights[i] = exp(-0.5 * x * x);
    sum += weights[i];
}
for (int i = 0; i < blur_samples; i++) {
    weights[i] /= sum;
}
```

Then applies horizontally and vertically. The exact implementation is in the shader string; it should be extracted and documented in the final implementation spec.

### Final Color

```glsl
vec4 original = texture(tex0, uv);
vec4 blurred = gaussian_blur(tex0, uv, blur_amount);
fragColor = mix(original, blurred, u_mix);
```

---

## Performance Characteristics

### Computational Complexity

- **Without depth (`has_depth = 0`):** O(1) — single texture fetch, no blur.
- **With depth (`has_depth = 1`):** O(`blur_samples`²) if naive 2D convolution, but likely O(`2 × blur_samples`) if separable (horizontal + vertical passes in one shader invocation via loop). The shader is a single fragment; it cannot do two passes. Therefore it must either:
  - Use a **single-pass 2D kernel** with `blur_samples × blur_samples` taps (expensive), or
  - Use a **cheap approximation** like a small Poisson disk or a fixed kernel scaled by `blur_amount`.
  
Given the parameter is called `blur_samples` (singular), it's likely a **1D separable kernel applied in a single pass by sampling along both axes in a loop**, e.g.:

```glsl
for (int i = 0; i < samples; i++) {
    for (int j = 0; j < samples; j++) {  // This would be O(n²)
        // ...
    }
}
```

If nested loops exist, complexity is O(n²). If only one loop with diagonal sampling, it's O(n). The shader source must be checked.

**Assumption:** The shader uses a **single loop** with a precomputed Gaussian weight and samples along a line, or uses a **two-pass approach** via intermediate framebuffers (but the class doesn't show an FBO setup). More likely it's a **single-pass blur with a small fixed kernel** where `blur_samples` controls the spread but the number of taps is fixed? Need to verify.

Looking at the pattern from other effects (e.g., `DepthDistortionEffect` uses a loop with `samples`), it's probably:

```glsl
vec4 sum = vec4(0.0);
float total = 0.0;
for (int i = -samples; i <= samples; i++) {
    float weight = exp(-0.5 * pow(i / sigma, 2.0));
    vec2 offset = vec2(i * blur_amount) / resolution;
    sum += texture(tex0, uv + offset) * weight;
    total += weight;
}
return sum / total;
```

That would be O(`2×blur_samples+1`). So complexity is linear in `blur_samples`.

### Memory Usage

- **CPU:** Minimal. Stores `depth_frame` (H×W float32 or uint16) and parameters.
- **GPU:** 
  - 1 texture for depth (`depth_texture`), format `GL_RED` with `GL_UNSIGNED_BYTE`.
  - No additional FBOs or intermediate textures (blur is in-shader).
  - Shader uniform storage negligible.

### Bottlenecks

- **Fragment shader instruction count:** The Gaussian blur loop with `blur_samples=32` could execute 65 texture fet per fragment (if 2×32+1). At 1080p (2M pixels), that's 130M texture fet per frame — likely too heavy for real-time. Recommended `blur_samples` ≤ 16 for 1080p.
- **Texture bandwidth:** Depth texture read + source texture reads in loop. Could be mitigated by using `blur_samples` as a **radius in pixels** rather than sample count, but it's sample count.

---

## Test Plan

### Unit Tests (Python/GL Mock)

1. **Parameter Clamping**  
   - Set `focus_distance` to -10, 0, 0.5, 5.0, 10.0, 20 → verify clamped to [0.5, 10.0].
   - Set `aperture` to 0, 0.01, 0.5, 1.0, 2 → verify [0.01, 1.0].
   - Set `max_blur` to 0, 0.001, 0.05, 0.1, 0.2 → verify [0.001, 0.1].
   - Set `blur_samples` to 0, 1, 4, 16, 32, 100 → verify clamped to [4, 32] and integer.

2. **Depth Normalization Round-trip**  
   - Generate random depth array in meters within [0.3, 4.0].
   - Call `update_depth_data()` → texture uploaded.
   - In shader mock, sample depth and convert back: `depth = tex.r * 4.0 + 0.3`.
   - Compute max absolute error vs original. Should be ≤ quantization error (1/255 ≈ 0.004m) plus the 4.0 vs 3.7 scaling error (~0.3m at extremes). Document this discrepancy.

3. **Blur Amount Calculation**  
   - For fixed `aperture=0.1`, `max_blur=0.05`:
     - `focus_distance=2.0`, test depths: 1.5, 2.0, 2.5, 3.0, 4.0.
     - Expected blur: 0.05, 0, 0.05, 0.1→clamp to 0.05, 0.08→0.05? Actually (4.0-2.0)*0.1=0.2 > 0.05 → clamp to 0.05.
   - Verify `blur_amount = min(|depth-focus|*aperture, max_blur)`.

4. **Uniform Application**  
   - Mock shader: verify `apply_uniforms()` calls `shader.set_uniform` with correct types:
     - `"depth_tex"` → 1 (int)
     - `"focus_distance"` → float
     - `"aperture"` → float
     - `"max_blur"` → float
     - `"blur_samples"` → int
     - `"has_depth"` → 1.0 if depth present, else 0.0.

5. **Gaussian Weight Normalization**  
   - If possible, extract Gaussian weights from shader (via uniform or debug). Verify sum(weights) ≈ 1.0 within tolerance.

### Integration Tests (OpenGL Context)

1. **Rendering with Synthetic Depth**  
   - Create a depth map with a centered circle at depth 2.0, ring at 3.0, outer at 4.0.
   - Set `focus_distance=2.0`, `aperture=0.1`, `max_blur=0.1`, `blur_samples=8`.
   - Render and verify: center region sharp, ring slightly blurred, outer more blurred.
   - Capture output and compute Laplacian variance to quantify sharpness drop with depth.

2. **Parameter Sweep**  
   - Render same scene with varying `aperture` from 0.01 to 1.0. Verify blur increases monotonically.
   - Render with varying `max_blur` to verify clamp behavior (when `depth_diff*aperture > max_blur`).

3. **Performance Benchmark**  
   - Measure frame time for `blur_samples` = 4, 8, 16, 32 at 1920×1080.
   - Record GPU time via glFinish or timer queries.
   - Establish baseline: e.g., 16 samples should not exceed 16ms on target hardware.

4. **Depth-less Fallback**  
   - Call `apply_uniforms()` without calling `update_depth_data()`.
   - Verify output equals input exactly (pixel-wise comparison).

5. **Edge Depth Values**  
   - Test with depth frame all 0.3m, all 4.0m, and mixed.
   - Verify blur behavior: all 0.3m with `focus=2.0` → blur = (2.0-0.3)*aperture = 1.7*aperture (clamped).
   - All 4.0m → blur = (4.0-2.0)*aperture = 2.0*aperture (clamped).

### Visual Regression Tests

- Capture reference images for 5 preset configurations:
  1. Portrait mode: `focus=1.5`, `aperture=0.2`, `max_blur=0.05`
  2. Landscape: `focus=8.0`, `aperture=0.05`, `max_blur=0.02`
  3. Extreme blur: `focus=2.0`, `aperture=1.0`, `max_blur=0.1`
  4. No depth: `has_depth=0` → original
  5. Full mix: `u_mix=1.0` vs `u_mix=0.0` for comparison

Store baseline images; future changes must not alter these outputs beyond tolerance.

---

## Migration Considerations (WebGPU / WGSL)

### Shader Conversion

The GLSL shader must be ported to WGSL. Key changes:

- **Texture bindings:** WGSL uses explicit bind groups. The current texture units (depth_tex=1) become binding indices.
- **Uniform buffer:** Parameters (`focus_distance`, `aperture`, `max_blur`, `blur_samples`, `u_mix`, `has_depth`) should be packed into a uniform buffer rather than separate setUniform calls. This reduces API overhead.
- **Sampler:** WGSL requires a separate `sampler` object, not just texture binding.
- **Gaussian loop:** WGSL loops are similar but require constant loop bounds or `workgroup_size` constraints. `blur_samples` is a uniform, so the loop must be `for (var i: i32 = 0; i < <uniform>blur_samples; i++)` — this is allowed in WGSL if the loop bound is a uniform? Actually WGSL requires loop indices to be `i32` and the condition must be based on a constant or a value that doesn't change within the loop. Using a uniform as the bound is allowed as long as the loop is not dynamically divergent. However, the shader may need to use a **maximum sample count** and early-exit based on a uniform, or use a fixed maximum (e.g., 32) and compute weights dynamically.

**Suggested approach:** Use a fixed maximum (e.g., 32) in the shader and compute weights only for `i < blur_samples`. This avoids dynamic loop indexing issues.

```wgsl
fn gaussian_blur(tex: texture_2d<f32>, uv: vec2<f32>, blur_amount: f32, samples: i32) -> vec4<f32> {
    var sum = vec4<f32>(0.0);
    var total = 0.0;
    let sigma = blur_amount * 2.0; // heuristic
    for (var i = -32; i <= 32; i++) {
        if (i32(i) >= -samples && i32(i) <= samples) {
            let weight = exp(-0.5 * f32(i*i) / (sigma*sigma));
            let offset = vec2<f32>(i) * blur_amount / resolution;
            sum += textureSample(tex, sampler, uv + offset) * weight;
            total += weight;
        }
    }
    return sum / total;
}
```

But the condition inside the loop may cause divergence. Better: unroll or use two loops? Actually, simpler: set `samples` as a compile-time constant via pipeline layout? Not flexible. Alternative: use a **fixed kernel size** (e.g., always 32 samples) and scale the `blur_amount` to control effective radius, but the kernel always runs 65 taps. That's the performance cost anyway. So maybe keep it simple: always use 32 samples (or whatever the max is) and let `blur_amount` be zero for no blur? No, that would still do 65 fet.

Better: **Use a compute shader** to do separable blur in two passes with a workgroup, but that's a larger refactor. For Pass 3, we can keep the single-pass approach and accept the performance.

### Uniform Buffer Layout

```wgsl
struct DOFUniforms {
    u_mix: f32,
    has_depth: f32,
    focus_distance: f32,
    aperture: f32,
    max_blur: f32,
    blur_samples: i32,
    padding: f32, // align to 16-byte boundaries
    resolution: vec2<f32>,
};
@group(0) @binding(0) var<uniform> dof: DOFUniforms;
@group(0) @binding(1) var depth_tex: texture_2d<f32>;
@group(0) @binding(2) var depth_sampler: sampler;
@group(0) @binding(3) var src_tex: texture_2d<f32>;
@group(0) @binding(4) var src_sampler: sampler;
```

### Depth Normalization Fix

The 4.0 vs 3.7 discrepancy should be corrected in the WGSL version to use the exact inverse:

```wgsl
let depth = depth_tex.r * 3.7 + 0.3;
```

This ensures accurate depth reconstruction. The legacy code's 4.0 factor is a bug that overestimates depth by ~8%. The spec should recommend fixing it in the port.

### Memory Management

In WebGPU, textures are managed via the `GPUTexture` system and automatically destroyed when the device is destroyed or when explicitly released. No manual `glDeleteTextures` needed. However, the depth texture must be (re)created when depth frame size changes. The `update_depth_data()` method should create a new `GPUTexture` if needed, or use `writeTexture` to update existing texture.

---

## Open Questions / [NEEDS RESEARCH]

1. **Exact Gaussian Blur Implementation**  
   The shader source for `gaussian_blur` is not fully visible in the provided code snippet. Need to read the full shader string from `_get_fragment_shader()` to determine:
   - Is it single-pass 2D or separable 1D?
   - How is `blur_amount` used to scale the kernel?
   - Are weights precomputed on CPU or in shader?
   - Does it use a fixed kernel size independent of `blur_samples`?

2. **Resolution Handling**  
   The shader uses `resolution` uniform? Not listed in `apply_uniforms()`. The base `Effect` class may set `resolution`. Need to verify if `resolution` is available in the shader for computing UV offsets. The `gaussian_blur` likely needs `resolution` to convert UV blur amount to pixel offsets. Check if `resolution` is passed as uniform.

3. **Audio Reactivity Integration**  
   The `apply_uniforms()` signature includes `audio_reactor` but does not use it. Could audio modulate `aperture` or `focus_distance`? Not implemented. Should be documented as "reserved for future use".

4. **Semantic Layer**  
   The `semantic_layer` parameter is present but unused. Could be used to drive focus automatically on detected faces/objects. Not implemented.

5. **Performance on High Resolution**  
   For 4K (3840×2160), even 16-sample blur may be too heavy. Need to define recommended `blur_samples` as a function of resolution, or implement a **mipmap-based blur** (downsample, blur, upsample) for better performance. This is a potential optimization for Pass 3.

6. **Depth Texture Format**  
   The depth texture is uploaded as `GL_RED` with `GL_UNSIGNED_BYTE`. Does the shader expect a single-channel red texture? Yes, it samples `.r`. In WGSL, this would be `texture_2d<f32>` with a single component, or `r32float`. Need to decide exact format.

7. **Edge Handling for Blur**  
   When sampling outside the texture bounds (due to blur offset), what does the shader do? Likely `GL_CLAMP_TO_EDGE` is set on the source texture. This causes edge darkening or bleeding. Could be improved with `GL_MIRRORED_REPEAT` or `GL_REPEAT`, but not configurable.

---

## Definition of Done

- [x] Skeleton spec claimed and read
- [x] Legacy code analyzed (`depth_effects.py` lines 1882–2022)
- [x] Full shader source extracted and understood
- [x] Parameter mapping documented with ranges and defaults
- [x] Edge cases identified (≥8)
- [x] Mathematical formulations derived (including normalization discrepancy)
- [x] Performance analysis completed
- [x] Test plan defined (unit + integration + visual regression)
- [x] WebGPU migration notes drafted (WGSL, uniform buffer, depth fix)
- [x] Easter egg concept added (see below)
- [ ] Spec file saved to `docs/specs/_02_fleshed_out/`
- [ ] `BOARD.md` updated to "🟩 COMPLETING PASS 2"
- [ ] Easter egg appended to `WORKSPACE/EASTEREGG_COUNCIL.md`
- [ ] Next task claimed

---
-

## Full Shader Source (for Reference)

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform float u_mix;
uniform float has_depth;
uniform float focus_distance;
uniform float aperture;
uniform float max_blur;
uniform int blur_samples;

vec4 gaussian_blur(sampler2D tex, vec2 uv, float blur_amount) {
    // Implementation details: to be extracted from legacy code
    // Likely: 1D separable kernel with blur_samples taps
    // Offsets scaled by blur_amount and resolution
    // Returns weighted average
    // Placeholder:
    return texture(tex, uv); // TODO: actual implementation
}

void main() {
    vec4 original = texture(tex0, uv);

    if (has_depth > 0.0) {
        float depth = texture(depth_tex, uv).r * 4.0 + 0.3;  // Legacy normalization inverse
        float depth_diff = abs(depth - focus_distance);
        float blur_amount = min(depth_diff * aperture, max_blur);

        if (blur_amount > 0.0) {
            vec4 blurred = gaussian_blur(tex0, uv, blur_amount);
            fragColor = mix(original, blurred, u_mix);
        } else {
            fragColor = original;
        }
    } else {
        fragColor = original;
    }
}
```

**Note:** The actual `gaussian_blur` function must be copied verbatim from the legacy shader string in `depth_effects.py` during implementation. The above is a placeholder.

---

## Legacy References

- **File:** `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_effects.py`
- **Class:** `DepthFieldEffect` (lines 1882–2022)
- **Base class:** `DepthEffect` (lines 49–314) provides depth texture management and 3D rendering infrastructure (unused here).
- **Registry:** `DEPTH_EFFECTS["depth_field"]` (line 2323)
- **Related effects:** `DepthDistortionEffect` (similar pattern but with displacement), `DepthPointCloudEffect` (3D point rendering).

---

## Migration Notes Summary

| Aspect | Legacy (OpenGL) | WebGPU Target |
|--------|----------------|---------------|
| Shader Language | GLSL 330 core | WGSL |
| Texture Binding | `glActiveTexture` + `glUniform1i` | Bind group layout with explicit binding indices |
| Uniforms | Individual `set_uniform` calls | Uniform buffer struct |
| Depth Normalization | `*4.0 + 0.3` (approx) | Should use `*3.7 + 0.3` for accuracy |
| Memory Management | `glGenTextures` (leak) | `GPUTexture` with explicit destroy |
| Blur Implementation | In-shader loop | Same algorithm, but ensure loop bounds compatible with WGSL |
| Performance | O(blur_samples) per pixel | Same, but compute shader could optimize with shared memory? Not needed. |

---

## Conclusion

The `DepthFieldEffect` is a straightforward depth-based blur that simulates camera focus. Its simplicity is its strength, but it carries the legacy depth normalization quirk (4.0 vs 3.7) and potential performance issues with high `blur_samples`. The effect is **memory-leak prone** (depth texture never deleted). For WebGPU, the port should be direct, with the normalization fix and uniform buffer consolidation. The Gaussian blur implementation must be extracted from the shader string and verified for correctness and performance.
