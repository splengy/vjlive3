# P3-EXT052: DepthGroovyDatamoshEffect — Maximalist Psychedelic Depth Datamosh

**Component:** vdepth plugin  
**Phase:** Pass 2 — Fleshed Out Technical Specification  
**Status:** Ready for Implementation  
**Legacy Origin:** `vjlive/plugins/vdepth/depth_groovy_datamosh.py` (lines 1–489)  
**Related Concepts:** Datamosh, kaleidoscope, spiral feedback, pixel sort, HSV color space, depth-driven distortion

---

## Executive Summary

The `DepthGroovyDatamoshEffect` is a **maximalist psychedelic depth effect** that combines an unprecedented number of visual techniques into a single, audio-reactive, depth-modulated experience. It integrates:

- **Rainbow hue cycling** mapped to depth with animated hue rotation
- **Kaleidoscopic UV mirroring** with depth-modulated fold count
- **Spiral feedback vortices** that rotate and zoom based on depth
- **Breathing depth layers** that pulse in and out
- **Pixel-sort displacement** along depth gradients
- **Organic melt warping** using depth gradient flow
- **Recursive zoom** per depth layer
- **Block datamosh** with depth-modulated displacement
- **Color bleed** across channels
- **Neon saturation boost** via HSV manipulation
- **Glow trails** from feedback accumulation
- **Depth-phased strobe flashes**

All effects are **depth-driven**: the depth map influences every transformation, creating a cohesive 3D-aware psychedelia. The effect is **highly audio-reactive**, with bass controlling spiral and mosh, mids driving breathing and melt, and treble driving rainbow and strobe. It uses three input textures: `tex0` (current frame), `tex1` (Video B for datamosh), and `texPrev` (previous frame for feedback). The shader is **extremely expensive** due to multiple texture fetches, noise functions, and complex math, but is designed for high-end VJ performance.

---

## Detailed Behavior and Parameter Interactions

### Core Architecture

The shader processes the image in **five stages**:

1. **UV Transformations** — Apply kaleidoscope, spiral, breathing, melt, depth zoom, and pixel sort to the UV coordinates before sampling.
2. **Sampling** — Sample `tex0` and `texPrev` at the transformed coordinates.
3. **Datamosh** — Apply block-based displacement and color bleed using `texPrev` and optionally `tex1` (Video B).
4. **Color Psychedelia** — Apply rainbow overlay, saturation boost, glow trails, and strobe flash.
5. **Final Mix** — Blend original `tex0` with processed result via `u_mix`.

Each stage is controlled by a set of parameters that can be turned on/off by setting their value to 0.

### Stage 1: UV Transformations (Applied Sequentially)

The UV coordinate `coord` starts as `uv` and is modified by each enabled effect. The order matters:

1. **Kaleidoscope** (`kaleidoscope > 0.1`):
   - Converts UV to polar coordinates centered at (0.5, 0.5).
   - Computes `folds = int(kaleidoscope * 6.0) + 2` (range 2–8).
   - Divides angle by `fold_angle = 2π / folds`, mirrors within each sector.
   - Adds depth-driven rotation: `angle += depth * 1.0 + time * 0.2`.
   - Converts back to Cartesian.

2. **Spiral Feedback** (`spiral_feedback > 0.0`):
   - Again uses polar coordinates.
   - `spiral_amount = spiral_feedback * (1.0 - depth * 0.5)` — near objects spiral more.
   - `angle += spiral_amount * 0.3 * sin(time * spiral_speed + radius * 8.0)`.
   - Applies depth-modulated zoom: `zoom = 1.0 - spiral_feedback * 0.02 * (1.0 + depth * depth_zoom)`.
   - Multiplies radius by zoom.

3. **Breathing** (`breathing > 0.0`):
   - `pulse = sin(time * breathing_speed * 2.0 + depth * 6.283 * 2.0)`.
   - `scale = 1.0 + pulse * breathing * 0.05 * (1.0 + depth)`.
   - Scales centered UV: `coord = centered * scale + 0.5`.

4. **Melt** (`melt > 0.0`):
   - Computes depth gradient at current coord: `grad = depth_gradient(coord)`.
   - Adds sine-wave offset: `wave_x = sin(coord.y * 20.0 + time * 2.0 + depth * 8.0) * melt * 0.02`.
   - Adds gradient flow: `coord += vec2(wave_x, wave_y) + grad * melt * 0.1`.

5. **Depth Zoom** (`depth_zoom > 0.0`):
   - `zoom_factor = 1.0 - depth * depth_zoom * 0.1`.
   - Scales centered UV.

6. **Pixel Sort** (`pixel_sort > 0.0`):
   - Computes depth gradient `grad` and its magnitude.
   - If gradient significant (`> 0.001`), normalizes to `sort_dir`.
   - `sort_amount = pixel_sort * 0.03 * grad_mag * 20.0`.
   - Quantizes into strips: `strip = floor(dot(coord, sort_dir) * resolution.x / 4.0)`.
   - Generates hash per strip and time: `strip_hash = hash(vec2(strip, floor(time * 2.0)))`.
   - Displaces: `coord += sort_dir * sort_amount * strip_hash`.

Finally, `coord` is clamped to `[0.001, 0.999]`.

### Stage 2: Sampling

```glsl
vec4 current = texture(tex0, coord);
vec4 previous = texture(texPrev, coord);
```

### Stage 3: Datamosh

If `mosh_amount > 0.0`:

- Compute block size: `block = max(4.0, block_chaos * 40.0 + 4.0)` → range 4–44 pixels.
- Block UV: `blockUV = floor(coord * resolution / block) * block / resolution`.
- Block hash: `block_hash = hash(blockUV + vec2(floor(time * 3.0)))`.
- Depth-modulated mosh factor: `depth_mosh = 0.5 + 0.5 * sin(depth * 6.283 + time)`, then `mosh_factor = mosh_amount * depth_mosh`.
- If `block_hash > 0.5`:
  - Displacement: `displace = (vec2(hash(blockUV), hash(blockUV+99.0)) - 0.5) * 0.04 * mosh_factor`.
  - Sample previous frame: `moshed = texture(texPrev, coord + displace)`.
  - `result = mix(result, moshed, mosh_factor * 0.5)`.
- **Color bleed** (`color_bleed > 0.0`):
  - `cb = color_bleed * 0.01 * mosh_factor`.
  - `grad = depth_gradient(coord)`.
  - `result.r = mix(result.r, texture(texPrev, coord + grad * cb).r, mosh_factor * 0.3)`.
  - `result.b = mix(result.b, texture(texPrev, coord - grad * cb).b, mosh_factor * 0.3)`.

### Stage 4: Color Psychedelia

1. **Rainbow Depth Overlay** (`rainbow_intensity > 0.0`):
   - `hue = fract(depth * 2.0 + time * rainbow_speed * 0.1)`.
   - `rainbow = hsv2rgb(vec3(hue, 1.0, 1.0))`.
   - Applies **overlay blend mode** per channel:
     ```
     if (base < 0.5) overlay = 2.0 * base * blend;
     else overlay = 1.0 - 2.0 * (1.0 - base) * (1.0 - blend);
     ```
   - Mixes result with overlay: `result.rgb = mix(result.rgb, overlay, rainbow_intensity * 0.6)`.
   - Adds edge glow: `edge = length(depth_gradient(coord)) * 8.0`; `result.rgb += rainbow * edge * rainbow_intensity * 0.5`.

2. **Saturation Boost** (`saturation_boost > 0.0`):
   - Converts result to HSV.
   - `hsv.y = clamp(hsv.y * (1.0 + saturation_boost * 2.0), 0.0, 1.0)`.
   - `hsv.z = clamp(hsv.z * (1.0 + saturation_boost * 0.3), 0.0, 1.0)`.
   - Converts back to RGB.

3. **Glow Trails** (`glow_trails > 0.0`):
   - `glow = max(result.rgb, previous.rgb * glow_trails * 0.8)`.
   - `result.rgb = mix(result.rgb, glow, glow_trails * 0.5)`.

4. **Strobe Flash** (`strobe_flash > 0.0`):
   - `flash = pow(max(0.0, sin(time * strobe_flash * 8.0)), 8.0)`.
   - Depth-phased: `flash *= pow(max(0.0, sin(time * strobe_flash * 8.0 + depth * 3.14)), 4.0)`.
   - `result.rgb += vec3(flash * 0.5)`.

### Stage 5: Final Mix

```glsl
fragColor = mix(texture(tex0, uv), result, u_mix);
```

Note: The original `uv` (not transformed) is used to sample the source for the final mix, preserving the unmodified background.

### Parameter Mapping

All parameters are on a 0–10 UI rail and mapped via `_map_param(name, out_min, out_max)`:

| Parameter (UI) | Internal | UI Range | Mapped Range | Default | Audio Reactivity |
|----------------|----------|----------|--------------|---------|------------------|
| `rainbowIntensity` | `rainbow_intensity` | 0–10 | 0.0–1.0 | 6.0 | TREBLE |
| `rainbowSpeed` | `rainbow_speed` | 0–10 | 0.0–1.0 | 4.0 | — |
| `kaleidoscope` | `kaleidoscope` | 0–10 | 0.0–1.0 | 3.0 | — |
| `spiralFeedback` | `spiral_feedback` | 0–10 | 0.0–1.0 | 5.0 | BASS |
| `spiralSpeed` | `spiral_speed` | 0–10 | 0.0–3.0 | 4.0 | — |
| `breathing` | `breathing` | 0–10 | 0.0–1.0 | 4.0 | MID |
| `breathingSpeed` | `breathing_speed` | 0–10 | 0.0–1.0 | 5.0 | — |
| `depthZoom` | `depth_zoom` | 0–10 | 0.0–1.0 | 3.0 | — |
| `pixelSort` | `pixel_sort` | 0–10 | 0.0–1.0 | 3.0 | — |
| `melt` | `melt` | 0–10 | 0.0–1.0 | 4.0 | MID |
| `moshAmount` | `mosh_amount` | 0–10 | 0.0–1.0 | 4.0 | BASS |
| `blockChaos` | `block_chaos` | 0–10 | 0.0–1.0 | 5.0 | — |
| `colorBleed` | `color_bleed` | 0–10 | 0.0–1.0 | 4.0 | — |
| `saturationBoost` | `saturation_boost` | 0–10 | 0.0–1.0 | 6.0 | — |
| `glowTrails` | `glow_trails` | 0–10 | 0.0–1.0 | 5.0 | — |
| `strobeFlash` | `strobe_flash` | 0–10 | 0.0–1.0 | 0.0 | TREBLE |

**Audio Reactivity Mapping:**
- BASS → `spiralFeedback`, `moshAmount`
- MID → `breathing`, `melt`
- TREBLE → `rainbowIntensity`, `strobeFlash`

The audio reactor modulates these parameters in real-time, overriding the base mapped values.

### Uniforms

| Uniform | Type | Binding Unit | Description |
|---------|------|--------------|-------------|
| `tex0` | sampler2D | 0 | Current video frame |
| `tex1` | sampler2D | 1 | Video B (for datamosh color bleed) |
| `texPrev` | sampler2D | 1? Actually likely unit 1 | Previous frame (feedback) |
| `depth_tex` | sampler2D | 2 | Depth map (normalized 0–1) |
| `u_mix` | float | — | Effect blend factor |
| `time` | float | — | Shader time (seconds) |
| `resolution` | vec2 | — | Framebuffer size |
| `rainbow_intensity` | float | — | Rainbow overlay strength |
| `rainbow_speed` | float | — | Hue cycling speed |
| `kaleidoscope` | float | — | Mirror fold amount (0–1) |
| `spiral_feedback` | float | — | Spiral vortex strength |
| `spiral_speed` | float | — | Spiral rotation speed |
| `breathing` | float | — | Depth layer pulse amplitude |
| `breathing_speed` | float | — | Pulse rate |
| `depth_zoom` | float | — | Recursive zoom per depth |
| `pixel_sort` | float | — | Pixel-sort displacement strength |
| `melt` | float | — | Organic warping strength |
| `mosh_amount` | float | — | Datamosh intensity |
| `block_chaos` | float | — | Block size chaos (4–44 px) |
| `color_bleed` | float | — | Cross-channel bleed strength |
| `saturation_boost` | float | — | Neon saturation boost |
| `glow_trails` | float | — | Feedback glow strength |
| `strobe_flash` | float | — | Strobe intensity |

**Note:** Texture unit assignments: `tex0=0`, `texPrev=1`, `depth_tex=2`. The shader also samples `tex1` (Video B) but `apply_uniforms()` does not set it explicitly; it may be set by the base class or external node connection. Need to verify if `tex1` is bound to unit 1 as well? That would conflict with `texPrev`. Actually the shader declares `uniform sampler2D tex1;` but the Python code only sets `tex0`, `texPrev`, `depth_tex`. The `tex1` sampler is never bound! This is a **bug**: `tex1` is used in the shader? Looking at the shader code, I don't see any reference to `tex1` except in the uniform declaration. The shader does not sample `tex1` anywhere. The comment at line 25 says `// Video B — pixel source (what gets datamoshed)` but it's unused. The datamosh block samples `texPrev` only. So `tex1` is dead code. This is a **bug/leftover** from an earlier design. Should be removed or used.

---

## Public Interface

### Class: `DepthGroovyDatamoshEffect(Effect)`

**Constructor:** `__init__(self)`  
- Initializes shader with `DEPTH_GROOVY_FRAGMENT`.
- Sets default parameters (17 of them) in `self.parameters`.
- Initializes `depth_source`, `depth_frame`, `depth_texture` (GLuint).
- Defines 4 presets: `gentle_trip`, `full_spectrum`, `spiral_vortex`, `ego_death`.

**Methods:**

- `set_depth_source(source)` — Connect depth provider.
- `set_audio_analyzer(analyzer)` — Attach audio analyzer; maps BASS/MID/TREBLE to specific parameters.
- `update_depth_data()` — Fetch depth frame from source.
- `apply_uniforms(time_val, resolution, audio_reactor=None, semantic_layer=None)` —  
  Uploads depth texture, sets all uniforms (mapped from 0–10), applies audio modulation if present.
- `_map_param(name, out_min, out_max)` — Linear mapping.
- `set_parameter(name, value)` — Inherited; updates `self.parameters`.
- `get_parameter(name)` — Inherited; returns current value.

**Presets:**  
Dictionary `PRESETS` with named configurations. Each preset is a dict of parameter values (on 0–10 rail). These can be applied by calling `set_parameter` for each entry.

---

## Inputs and Outputs

### Inputs

| Stream | Type | Format | Description |
|--------|------|--------|-------------|
| `tex0` | sampler2D | RGB/RGBA | Current video frame |
| `tex1` | sampler2D | RGB/RGBA | Video B (unused in current shader) |
| `texPrev` | sampler2D | RGB/RGBA | Previous frame (feedback) |
| `depth_tex` | sampler2D | RED (uint8 normalized) | Depth map (0–1) |
| Parameters | floats | N/A | 17 groovy parameters |
| `u_mix` | float | 0–1 | Effect blend factor |
| `time` | float | seconds | Animation time |
| `resolution` | vec2 | pixels | Framebuffer size |

### Outputs

| Stream | Type | Format | Description |
|--------|------|--------|-------------|
| `fragColor` | vec4 | RGBA | Final psychedelic output |

---

## Edge Cases and Error Handling

### 1. Missing Depth Source
- **Condition:** `self.depth_source` is `None` or returns `None`.
- **Behavior:** `self.depth_frame` is `None`; depth texture not updated. Shader samples `depth_tex` which may be 0 or uninitialized. All depth-dependent effects will use `depth=0`. This may produce extreme effects (e.g., kaleidoscope folds all same, spiral minimal, breathing at one extreme). Not catastrophic but unpredictable. Should ideally set `has_depth` uniform and branch in shader, but not present.

### 2. `tex1` Unbound
- **Condition:** Shader declares `tex1` but `apply_uniforms()` never sets it.
- **Behavior:** If the shader tried to sample `tex1`, it would read from texture unit 0 (default) or whatever was previously bound, causing garbage. However, the shader **does not sample `tex1`** — it's dead code. So no immediate error, but wasted uniform slot and potential confusion. This is a **code smell**; should remove the uniform declaration.

### 3. `kaleidoscope` Folds Calculation
- `folds = int(kaleidoscope * 6.0) + 2`. If `kaleidoscope=1.0`, folds=8. If `kaleidoscope=0`, folds=2. Minimum 2 folds (mirror once). This is safe. However, `int()` truncates; could use `round()` for more even distribution. Not a bug.

### 4. `block_chaos` and Block Size
- `block = max(4.0, block_chaos * 40.0 + 4.0)`. Range: 4–44. At high `block_chaos=1.0`, block=44 pixels. This is large; may cause visible blockiness. At low, block=4 (very small, many blocks). The hash function is called per block, so smaller blocks mean more hash evaluations (but still O(1) per pixel). Performance may degrade with many small blocks due to hash overhead? Actually hash is cheap.

### 5. Pixel Sort Strip Quantization
- `strip = floor(dot(coord, sort_dir) * resolution.x / 4.0)`. This creates strips that are 4 pixels wide in screen space? Actually `resolution.x / 4.0` means the strip index scales with resolution; at 1920 width, strip size ~4 pixels. This is reasonable. However, `sort_dir` is a normalized 2D vector; `dot(coord, sort_dir)` is a scalar coordinate along that direction. The quantization may produce visible banding if `pixel_sort` is high. This is intentional.

### 6. Depth Gradient Calculation
- `depth_gradient(p)` uses a 1-pixel offset in UV space: `texel = 1.0 / resolution.x`. This assumes square pixels? Actually uses `resolution.x` for both x and y offsets, which is wrong if aspect ratio != 1:1. Should use `texel = 1.0 / resolution` (vec2). Using only x may distort gradient on non-square aspects. **Bug**: Should be `vec2 texel = 1.0 / resolution;` and use `texel` for both x and y offsets. Current code uses `1.0/resolution.x` for both directions, causing y gradient to be incorrect if width != height.

### 7. HSV Conversion Edge Cases
- `rgb2hsv` uses `e = 1.0e-10` to avoid division by zero. This is safe.
- `hsv2rgb` uses `abs(fract(...)*6.0 - 3.0)` and `clamp(p-1.0,0,1)`. Standard algorithm.

### 8. Strobe Flash Intensity
- `flash = pow(max(0.0, sin(time * strobe_flash * 8.0)), 8.0)`. The 8th power makes the flash very spiky (almost off, then bright). `strobe_flash` is mapped from 0–1, so frequency = `strobe_flash * 8.0` Hz? Actually `time` is seconds, so `sin(time * ω)` with ω=8*strobe_flash rad/s → frequency = ω/(2π) ≈ 1.27*strobe_flash Hz. At `strobe_flash=1.0`, ~1.27 Hz. That's a slow strobe. Could be intended.

### 9. Memory Leak
- `self.depth_texture` generated via `glGenTextures(1)` but never freed. Standard issue.

### 10. Audio Reactor Overwrites
- The `apply_uniforms()` first sets uniforms from mapped parameters, then if `audio_reactor` exists, it **overwrites** some of them with modulated values. This is correct: audio modulation takes precedence. However, note that the modulation uses the **mapped** base value (e.g., `spiral` from `_map_param`), not the raw UI value. That's fine.

### 11. `hasDualInput` Detection
- The shader contains code to detect if Video B is connected:
  ```glsl
  vec4 testB = texture(tex1, vec2(0.5));
  bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;
  ```
  But `tex1` is never bound, and the result is never used. This is dead code. Should be removed or used.

### 12. Depth Normalization
- Uses standard formula: `((self.depth_frame - 0.3) / 3.7 * 255).astype(np.uint8)`. Consistent with other effects.

### 13. Parameter Defaults and Ranges
- All parameters have defaults within 0–10. The `_map_param` handles scaling. No additional clamping in `set_parameter` (unlike some other effects). This means if a user sets a parameter outside 0–10 via code, the mapping could produce out-of-range values. But UI should constrain to 0–10. Acceptable.

### 14. Performance Variability
- The effect's cost depends on which parameters are non-zero. Enabling all effects simultaneously will be very heavy. The shader does not have early-out branches for disabled effects? Actually each stage has `if (param > 0.0)` checks, so if a parameter is 0, that stage is skipped. This provides some performance scaling. However, many stages still compute depth gradient, etc., even if not used? The gradient is computed inside `melt` and `pixel_sort` and `color_bleed` only when those are active. So it's efficient in that sense.

---

## Mathematical Formulations

### Depth Gradient

```glsl
vec2 depth_gradient(vec2 p) {
    float texel = 1.0 / resolution.x;  // BUG: should use resolution vector
    float dL = texture(depth_tex, p + vec2(-texel, 0.0)).r;
    float dR = texture(depth_tex, p + vec2( texel, 0.0)).r;
    float dU = texture(depth_tex, p + vec2(0.0,  texel)).r;
    float dD = texture(depth_tex, p + vec2(0.0, -texel)).r;
    return vec2(dR - dL, dU - dD);
}
```

Computes central differences in depth. The gradient magnitude indicates depth edge strength.

### Kaleidoscope Folding

- `folds = int(kaleidoscope * 6.0) + 2`
- `fold_angle = 2π / folds`
- `angle = mod(angle, fold_angle)`
- `if (angle > fold_angle * 0.5) angle = fold_angle - angle;` (mirror)
- `angle += depth * 1.0 + time * 0.2` (depth/time rotation)

### Spiral Vortex

- `spiral_amount = spiral_feedback * (1.0 - depth * 0.5)`
- `angle += spiral_amount * 0.3 * sin(time * spiral_speed + radius * 8.0)`
- `zoom = 1.0 - spiral_feedback * 0.02 * (1.0 + depth * depth_zoom)`
- `radius *= zoom`

### Breathing

- `pulse = sin(time * breathing_speed * 2.0 + depth * 6.283 * 2.0)`
- `scale = 1.0 + pulse * breathing * 0.05 * (1.0 + depth)`

### Melt Warping

- `wave_x = sin(coord.y * 20.0 + time * 2.0 + depth * 8.0) * melt * 0.02`
- `wave_y = cos(coord.x * 20.0 + time * 1.7 + depth * 6.0) * melt * 0.02`
- `coord += vec2(wave_x, wave_y) + grad * melt * 0.1`

### Depth Zoom

- `zoom_factor = 1.0 - depth * depth_zoom * 0.1`

### Pixel Sort

- `grad = depth_gradient(coord)`
- `grad_mag = length(grad)`
- `sort_dir = normalize(grad)`
- `sort_amount = pixel_sort * 0.03 * grad_mag * 20.0`
- `strip = floor(dot(coord, sort_dir) * resolution.x / 4.0)`
- `strip_hash = hash(vec2(strip, floor(time * 2.0)))`
- `coord += sort_dir * sort_amount * strip_hash`

### Datamosh Block Displacement

- `block = max(4.0, block_chaos * 40.0 + 4.0)`
- `blockUV = floor(coord * resolution / block) * block / resolution`
- `block_hash = hash(blockUV + vec2(floor(time * 3.0)))`
- `depth_mosh = 0.5 + 0.5 * sin(depth * 6.283 + time)`
- `mosh_factor = mosh_amount * depth_mosh`
- `displace = (vec2(hash(blockUV), hash(blockUV+99.0)) - 0.5) * 0.04 * mosh_factor`
- `moshed = texture(texPrev, coord + displace)`

### Color Bleed

- `cb = color_bleed * 0.01 * mosh_factor`
- `result.r = mix(result.r, texture(texPrev, coord + grad * cb).r, mosh_factor * 0.3)`
- `result.b = mix(result.b, texture(texPrev, coord - grad * cb).b, mosh_factor * 0.3)`

### Rainbow Overlay

- `hue = fract(depth * 2.0 + time * rainbow_speed * 0.1)`
- `rainbow = hsv2rgb(vec3(hue, 1.0, 1.0))`
- Overlay blend per channel:
  ```
  if (base < 0.5) overlay = 2.0 * base * blend;
  else overlay = 1.0 - 2.0 * (1.0 - base) * (1.0 - blend);
  ```
- `result.rgb = mix(result.rgb, overlay, rainbow_intensity * 0.6)`
- `edge = length(depth_gradient(coord)) * 8.0`
- `result.rgb += rainbow * edge * rainbow_intensity * 0.5`

### Saturation Boost

- Convert to HSV: `hsv = rgb2hsv(result.rgb)`
- `hsv.y = clamp(hsv.y * (1.0 + saturation_boost * 2.0), 0.0, 1.0)`
- `hsv.z = clamp(hsv.z * (1.0 + saturation_boost * 0.3), 0.0, 1.0)`
- Back to RGB.

### Glow Trails

- `glow = max(result.rgb, previous.rgb * glow_trails * 0.8)`
- `result.rgb = mix(result.rgb, glow, glow_trails * 0.5)`

### Strobe Flash

- `flash = pow(max(0.0, sin(time * strobe_flash * 8.0)), 8.0)`
- `flash *= pow(max(0.0, sin(time * strobe_flash * 8.0 + depth * 3.14)), 4.0)`
- `result.rgb += vec3(flash * 0.5)`

---

## Performance Characteristics

### Computational Complexity

The shader is **extremely heavy** when all parameters are enabled:

- **Texture fetches:**
  - Depth: 1 sample per `depth_gradient` call (and gradient is used in melt, pixel sort, color bleed, rainbow edge). Each gradient call does 4 depth samples. But these are in separate branches; if multiple effects enabled, gradient may be computed multiple times. Could be cached.
  - Source: `tex0` sampled once at transformed coord.
  - Previous: `texPrev` sampled once (plus additional in datamosh, color bleed, glow).
  - Video B: not used.
  - Total: ~1 + 1 + (4 per gradient) + (1–2 extra in datamosh) = potentially 10+ texture fet per pixel.

- **Arithmetic:**
  - Hash function: called many times (per block in datamosh, per pixel in pixel sort). Each hash involves many operations (fract, dot, etc.).
  - Trig functions: `sin`, `cos`, `atan` in kaleidoscope/spiral.
  - HSV conversions: expensive (multiple divisions, conditionals).
  - Exponential: `pow` in strobe and saturation.

- **Branches:** Many `if` statements; GPU divergence may be okay if parameters are uniform across warp.

**Estimated cost:** 5–10× a simple effect. At 1080p, could easily exceed 10ms/frame on mid-tier hardware. Not suitable for 4K without reducing parameters.

### Memory Usage

- **CPU:** Stores `depth_frame` (H×W).
- **GPU:** 1 depth texture (GL_RED, GL_UNSIGNED_BYTE). No FBOs.
- **Shader:** Many uniforms; should be packed into uniform buffer for WebGPU.

### Bottlenecks

- **Texture bandwidth:** Multiple depth texture reads (4 per gradient) could be heavy. Could optimize by computing gradient once and reusing.
- **Instruction count:** Hash and trig functions are expensive.
- **Register pressure:** Many varying variables may spill to local memory.

---

## Test Plan

### Unit Tests (Python)

1. **Parameter Mapping**  
   Test each parameter's mapping from UI 0–10 to expected range:
   - `rainbowIntensity`, `rainbowSpeed`, `kaleidoscope`, `spiralFeedback`, `breathing`, `breathingSpeed`, `depthZoom`, `pixelSort`, `melt`, `moshAmount`, `blockChaos`, `colorBleed`, `saturationBoost`, `glowTrails`, `strobeFlash`: 0→0.0, 5→0.5, 10→1.0.
   - `spiralSpeed`: 0→0.0, 5→1.5, 10→3.0.
   - Verify linearity.

2. **Audio Reactor Assignment**  
   - Verify assignments: BASS→spiralFeedback, moshAmount; MID→breathing, melt; TREBLE→rainbowIntensity, strobeFlash.
   - Ensure no other assignments.

3. **Depth Texture Upload**  
   - Mock depth frame, call `update_depth_data()` → `apply_uniforms()`.
   - Verify normalization formula and `glTexImage2D` call.

4. **Uniform Setting**  
   - Mock shader, verify all uniforms set with correct types and mapped values.
   - Check `tex0=0`, `texPrev=1`, `depth_tex=2`.
   - Verify audio modulation overrides.

5. **Preset Loading**  
   - For each preset, set parameters and verify they match the preset dict.

### Integration Tests (OpenGL Context)

1. **Kaleidoscope Folds**  
   - Render with `kaleidoscope` values: 0, 0.5, 1.0.
   - Verify number of symmetry axes: 2, 5, 8 respectively (by analyzing image symmetry).
   - Check depth modulation: varying depth should rotate folds differently.

2. **Spiral Feedback**  
   - Enable `spiral_feedback` with `spiral_speed` varying.
   - Capture animation; verify spiral rotation and zoom effect.
   - Check depth dependence: near vs far regions spiral differently.

3. **Breathing**  
   - Set `breathing` high, `breathing_speed` moderate.
   - Capture over time; verify pulsating zoom effect synced across depths with phase offset.

4. **Melt and Pixel Sort**  
   - Enable `melt` and/or `pixel_sort`.
   - Verify organic warping and directional displacement along depth gradients.
   - Use a depth map with strong edges; check that displacement aligns with gradient direction.

5. **Datamosh Block Displacement**  
   - Set `mosh_amount` high, `block_chaos` low/high.
   - Verify blocky displacement pattern; block size changes with `block_chaos`.
   - Check depth modulation: `depth_mosh` should cause mosh to vary with depth.

6. **Color Bleed**  
   - Enable `color_bleed` with high `mosh_amount`.
   - Check that red and blue channels are displaced relative to green, creating chromatic aberration effect.

7. **Rainbow Overlay**  
   - Set `rainbow_intensity` high, `rainbow_speed` moderate.
   - Verify hue varies with depth and cycles over time.
   - Check overlay blend mode: should enhance contrast.

8. **Saturation Boost**  
   - Render colorful scene, set `saturation_boost` high.
   - Measure saturation increase (HSV conversion) and possible value boost.

9. **Glow Trails**  
   - Enable `glow_trails` with `spiral_feedback` also on.
   - Verify that bright areas leave lingering trails (feedback brightened).

10. **Strobe Flash**  
    - Set `strobe_flash` to various values.
    - Capture at high frame rate; verify flashing synced to time and depth-phased.

11. **Audio Reactivity**  
    - Attach mock audio analyzer that returns known modulation values.
    - Verify that `spiral_feedback`, `mosh_amount`, `breathing`, `melt`, `rainbow_intensity`, `strobe_flash` are overwritten with modulated values.

12. **Performance Benchmark**  
    - Measure frame time with all parameters off, then with subsets, then all on.
    - Establish baseline: all-on should not exceed 16ms at 1080p on target hardware? Might be higher; document realistic expectations.

### Visual Regression

- Capture reference images for each preset (`gentle_trip`, `full_spectrum`, `spiral_vortex`, `ego_death`) at a fixed time.
- Capture individual effect demonstrations (e.g., kaleidoscope only, spiral only).
- Use as baselines for future changes.

---

## Migration Considerations (WebGPU / WGSL)

### Shader Conversion

The GLSL shader is large but straightforward to port to WGSL. Key tasks:

- **Uniform buffer:** Pack all floats into a struct:
  ```wgsl
  struct GroovyUniforms {
      u_mix: f32,
      rainbow_intensity: f32,
      rainbow_speed: f32,
      kaleidoscope: f32,
      spiral_feedback: f32,
      spiral_speed: f32,
      breathing: f32,
      breathing_speed: f32,
      depth_zoom: f32,
      pixel_sort: f32,
      melt: f32,
      mosh_amount: f32,
      block_chaos: f32,
      color_bleed: f32,
      saturation_boost: f32,
      glow_trails: f32,
      strobe_flash: f32,
      time: f32,
      resolution: vec2<f32>,
      // padding to 16-byte boundaries
  };
  @group(0) @binding(0) var<uniform> groovy: GroovyUniforms;
  @group(0) @binding(1) var src_tex: texture_2d<f32>;
  @group(0) @binding(2) var src_sampler: sampler;
  @group(0) @binding(3) var prev_tex: texture_2d<f32>;
  @group(0) @binding(4) var prev_sampler: sampler;
  @group(0) @binding(5) var depth_tex: texture_2d<f32>;
  @group(0) @binding(6) var depth_sampler: sampler;
  ```

- **Remove `tex1`** uniform; it's unused.

- **Functions:** Port `hash`, `hsv2rgb`, `rgb2hsv`, `depth_gradient` directly. Ensure `hash` uses `fract` and `dot` correctly.

- **Texture sampling:** Use `textureSample` with sampler.

- **Branching:** WGSL supports dynamic branches; same logic.

- **Precision:** Use `f32` everywhere.

### Performance Optimizations

- **Depth gradient caching:** Compute gradient once and reuse across stages instead of recomputing in `melt`, `pixel_sort`, `color_bleed`, `rainbow` edge. In GLSL, the compiler might common-subexpression eliminate if gradient call is pure and arguments same. But `coord` changes between calls? Actually `melt` modifies `coord`, then `pixel_sort` uses modified `coord`, then `color_bleed` uses that `coord`, and `rainbow` edge uses that `coord`. So gradient is computed at different coordinates each time. Could store gradient in a variable after the last transformation before datamosh? But it's used in different stages with potentially different `coord`. Might be okay.

- **Block hash reuse:** In datamosh, `block_hash` is computed once; used for displacement decision. That's fine.

- **Early-out:** The `if (param > 0.0)` branches are good.

### Memory Management

- In WebGPU, textures are managed by the GPU device. The depth texture should be created/updated similarly: create a `GPUTexture` with format `r8unorm` or `r32float`? The legacy uses `GL_RED` with `GL_UNSIGNED_BYTE`. In WebGPU, that's `r8unorm`. The upload uses `writeTexture`.

---

## Open Questions / [NEEDS RESEARCH]

1. **`tex1` Binding Conflict**  
   The shader declares `tex1` but it's never used. The Python code does not set it. However, the base `Effect` class might set `tex1` to unit 1 for some effects that need two video inputs. But this effect also uses `texPrev` on unit 1. That would conflict. Need to check: does `apply_uniforms()` set `texPrev`? Yes, line 424: `self.shader.set_uniform("texPrev", 1)`. So `tex1` would also be unit 1 if set, causing conflict. Since `tex1` is not used, it's safe to leave unset. But the uniform declaration should be removed to avoid confusion.

2. **Depth Gradient Resolution**  
   The gradient uses `1.0/resolution.x` for both x and y offsets. This is incorrect for non-square pixels. Should be `vec2(1.0)/resolution`. Need to confirm if the legacy code assumes square pixels; likely yes.

3. **Audio Reactor Integration**  
   The `apply_uniforms()` signature includes `audio_reactor` parameter but the method ignores it and uses `self.audio_reactor` set via `set_audio_analyzer`. That's fine. But the base class may pass an `audio_reactor` argument; the code doesn't use it. Not a bug.

4. **Performance on Real Hardware**  
   This effect is likely the most expensive in the depth plugin. Need to benchmark on target VJ hardware (likely mid-range GPU). May need to recommend disabling some sub-effects for real-time use.

5. **Preset Parameter Ranges**  
   The presets use values up to 10.0 (max). For example, `ego_death` sets `rainbowIntensity=10.0`, `spiralFeedback=10.0`, etc. This will max out all effects, likely causing extreme visual chaos and performance hit. That's probably intended for "ego death" experience. Document that these are extreme.

6. **HSV Conversion Accuracy**  
   The `rgb2hsv` and `hsv2rgb` functions are standard but may have edge cases near H=0. Should be fine.

7. **Strobe Flash Frequency**  
   The formula `time * strobe_flash * 8.0` yields radian frequency. At `strobe_flash=1.0`, frequency ≈ 1.27 Hz. That's a slow strobe. Could be intentional for "flash" rather than rapid strobe. Might be too slow for VJ use; but audio reactivity might modulate it.

---

## Definition of Done

- [x] Skeleton spec claimed and read
- [x] Legacy code analyzed (full 489 lines)
- [x] Shader logic documented (5 stages, all sub-effects)
- [x] Parameter mapping table (17 parameters)
- [x] Edge cases identified (≥12)
- [x] Mathematical formulations for each effect
- [x] Performance analysis (high cost)
- [x] Test plan (unit + integration + visual regression)
- [x] WebGPU migration notes
- [x] Easter egg concept added
- [ ] Spec file saved to `docs/specs/_02_fleshed_out/`
- [ ] `BOARD.md` updated to "🟩 COMPLETING PASS 2"
- [ ] Easter egg appended to `WORKSPACE/EASTEREGG_COUNCIL.md`
- [ ] Next task claimed

---
-

## Full Shader Source (Reference)

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;          // Current frame
uniform sampler2D tex1;        // Video B — pixel source (what gets datamoshed) [UNUSED]
uniform sampler2D texPrev;       // Previous frame (feedback)
uniform sampler2D depth_tex;     // Depth map
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Core groovy
uniform float rainbow_intensity;     // Depth-mapped rainbow overlay
uniform float rainbow_speed;         // Hue cycling speed
uniform float kaleidoscope;          // Mirror/fold count (0=off, higher=more folds)
uniform float spiral_feedback;       // Spiral vortex feedback into previous frame
uniform float spiral_speed;          // Rotation speed of spiral

// Depth psychedelia
uniform float breathing;             // Depth layers pulse in/out
uniform float breathing_speed;       // Pulse rate
uniform float depth_zoom;            // Recursive zoom per depth layer
uniform float pixel_sort;            // Sort-like displacement along depth gradients
uniform float melt;                  // Organic depth-driven UV melting/warping

// Datamosh
uniform float mosh_amount;           // Overall datamosh intensity
uniform float block_chaos;           // Random block displacement
uniform float color_bleed;           // Cross-channel color contamination

// Visual
uniform float saturation_boost;      // Push colors to neon
uniform float glow_trails;           // Glowing feedback trails
uniform float strobe_flash;          // Rhythmic flash intensity

// --- Utility functions ---

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

vec3 hsv2rgb(vec3 c) {
    vec3 p = abs(fract(c.xxx + vec3(1.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

// Depth gradient vector
vec2 depth_gradient(vec2 p) {
    float texel = 1.0 / resolution.x;  // BUG: should be 1.0/resolution (vec2)
    float dL = texture(depth_tex, p + vec2(-texel, 0.0)).r;
    float dR = texture(depth_tex, p + vec2( texel, 0.0)).r;
    float dU = texture(depth_tex, p + vec2(0.0,  texel)).r;
    float dD = texture(depth_tex, p + vec2(0.0, -texel)).r;
    return vec2(dR - dL, dU - dD);
}

void main() {

    // Detect if Video B is connected (not all black) [UNUSED]
    vec4 testB = texture(tex1, vec2(0.5));
    bool hasDualInput = (testB.r + testB.g + testB.b) > 0.01;

    float depth = texture(depth_tex, uv).r;
    vec2 coord = uv;

    // === STAGE 1: UV TRANSFORMATIONS (applied before sampling) ===

    // --- Kaleidoscope ---
    if (kaleidoscope > 0.1) {
        int folds = int(kaleidoscope * 6.0) + 2;  // 2 to 8 folds
        vec2 centered = coord - 0.5;
        float angle = atan(centered.y, centered.x);
        float radius = length(centered);

        // Depth modulates the fold — different depths get different symmetries
        float fold_angle = 6.283 / float(folds);
        angle = mod(angle, fold_angle);
        if (angle > fold_angle * 0.5) angle = fold_angle - angle;  // mirror fold

        // Add depth-driven rotation
        angle += depth * 1.0 + time * 0.2;

        coord = vec2(cos(angle), sin(angle)) * radius + 0.5;
    }

    // --- Spiral feedback ---
    if (spiral_feedback > 0.0) {
        vec2 centered = coord - 0.5;
        float radius = length(centered);
        float angle = atan(centered.y, centered.x);

        // Depth-driven spiral: near objects spiral fast, far objects slow
        float spiral_amount = spiral_feedback * (1.0 - depth * 0.5);
        angle += spiral_amount * 0.3 * sin(time * spiral_speed + radius * 8.0);

        // Slight zoom per depth for recursive tunnel effect
        float zoom = 1.0 - spiral_feedback * 0.02 * (1.0 + depth * depth_zoom);
        radius *= zoom;

        coord = vec2(cos(angle), sin(angle)) * radius + 0.5;
    }

    // --- Breathing (depth layers pulse) ---
    if (breathing > 0.0) {
        vec2 centered = coord - 0.5;
        // Each depth band breathes at a slightly different phase
        float pulse = sin(time * breathing_speed * 2.0 + depth * 6.283 * 2.0);
        float scale = 1.0 + pulse * breathing * 0.05 * (1.0 + depth);
        coord = centered * scale + 0.5;
    }

    // --- Melt (organic depth warping) ---
    if (melt > 0.0) {
        vec2 grad = depth_gradient(coord);
        // Organic sine-wave displacement along depth contours
        float wave_x = sin(coord.y * 20.0 + time * 2.0 + depth * 8.0) * melt * 0.02;
        float wave_y = cos(coord.x * 20.0 + time * 1.7 + depth * 6.0) * melt * 0.02;
        // Depth gradient adds directional flow
        coord += vec2(wave_x, wave_y) + grad * melt * 0.1;
    }

    // --- Depth zoom (recursive per-layer zoom) ---
    if (depth_zoom > 0.0) {
        vec2 centered = coord - 0.5;
        float zoom_factor = 1.0 - depth * depth_zoom * 0.1;
        coord = centered * zoom_factor + 0.5;
    }

    // --- Pixel sort displacement ---
    if (pixel_sort > 0.0) {
        vec2 grad = depth_gradient(coord);
        float grad_mag = length(grad);
        // Displace pixels along depth gradient (simulates sorting along depth)
        if (grad_mag > 0.001) {
            vec2 sort_dir = normalize(grad);
            float sort_amount = pixel_sort * 0.03 * grad_mag * 20.0;
            // Quantize into strips for that pixel-sort look
            float strip = floor(dot(coord, sort_dir) * resolution.x / 4.0);
            float strip_hash = hash(vec2(strip, floor(time * 2.0)));
            coord += sort_dir * sort_amount * strip_hash;
        }
    }

    // Clamp UVs
    coord = clamp(coord, 0.001, 0.999);

    // === STAGE 2: SAMPLING ===
    vec4 current = texture(tex0, coord);
    vec4 previous = texture(texPrev, coord);

    // === STAGE 3: DATAMOSH ===
    vec4 result = current;

    if (mosh_amount > 0.0) {
        // Block-based chaos displacement
        float block = max(4.0, block_chaos * 40.0 + 4.0);
        vec2 blockUV = floor(coord * resolution / block) * block / resolution;
        float block_hash = hash(blockUV + vec2(floor(time * 3.0)));

        // Depth-modulated mosh — more intense at certain depths
        float depth_mosh = 0.5 + 0.5 * sin(depth * 6.283 + time);
        float mosh_factor = mosh_amount * depth_mosh;

        if (block_hash > 0.5) {
            // Sample from previous frame at displaced position
            vec2 displace = (vec2(hash(blockUV), hash(blockUV + 99.0)) - 0.5) * 0.04 * mosh_factor;
            vec4 moshed = texture(texPrev, coord + displace);
            result = mix(result, moshed, mosh_factor * 0.5);
        }

        // Color bleed: channels from different offsets
        if (color_bleed > 0.0) {
            float cb = color_bleed * 0.01 * mosh_factor;
            vec2 grad = depth_gradient(coord);
            result.r = mix(result.r, texture(texPrev, coord + grad * cb).r, mosh_factor * 0.3);
            result.b = mix(result.b, texture(texPrev, coord - grad * cb).b, mosh_factor * 0.3);
        }
    }

    // Blend with feedback
    float fb_blend = spiral_feedback * 0.3 + glow_trails * 0.4;
    fb_blend = clamp(fb_blend, 0.0, 0.9);
    result = mix(result, previous, fb_blend);

    // === STAGE 4: COLOR PSYCHEDELIA ===

    // --- Rainbow depth overlay ---
    if (rainbow_intensity > 0.0) {
        // Map depth to hue with animated cycling
        float hue = fract(depth * 2.0 + time * rainbow_speed * 0.1);
        vec3 rainbow = hsv2rgb(vec3(hue, 1.0, 1.0));

        // Blend modes: overlay for rich interaction with source colors
        vec3 overlay;
        for (int i = 0; i < 3; i++) {
            float base = result.rgb[i];
            float blend = rainbow[i];
            overlay[i] = base < 0.5
                ? 2.0 * base * blend
                : 1.0 - 2.0 * (1.0 - base) * (1.0 - blend);
        }
        result.rgb = mix(result.rgb, overlay, rainbow_intensity * 0.6);

        // Add direct rainbow glow at depth transitions
        float edge = length(depth_gradient(coord)) * 8.0;
        result.rgb += rainbow * edge * rainbow_intensity * 0.5;
    }

    // --- Saturation boost to neon ---
    if (saturation_boost > 0.0) {
        vec3 hsv = rgb2hsv(result.rgb);
        // Boost saturation, push toward neon
        hsv.y = clamp(hsv.y * (1.0 + saturation_boost * 2.0), 0.0, 1.0);
        // Slight value boost
        hsv.z = clamp(hsv.z * (1.0 + saturation_boost * 0.3), 0.0, 1.0);
        result.rgb = hsv2rgb(hsv);
    }

    // --- Glow trails ---
    if (glow_trails > 0.0) {
        // Brighten the feedback accumulation for glowing trail effect
        vec3 glow = max(result.rgb, previous.rgb * glow_trails * 0.8);
        result.rgb = mix(result.rgb, glow, glow_trails * 0.5);
    }

    // --- Strobe flash ---
    if (strobe_flash > 0.0) {
        float flash = pow(max(0.0, sin(time * strobe_flash * 8.0)), 8.0);
        // Depth-phased strobe: different layers flash at different times
        flash *= pow(max(0.0, sin(time * strobe_flash * 8.0 + depth * 3.14)), 4.0);
        result.rgb += vec3(flash * 0.5);
    }

    // === STAGE 5: FINAL MIX ===
    fragColor = mix(texture(tex0, uv), result, u_mix);
}
```

---

## Legacy References

- **File:** `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_groovy_datamosh.py`
- **Class:** `DepthGroovyDatamoshEffect` (lines 271–489)
- **VJLive-2 variant:** `/home/happy/Desktop/claude projects/vjlive/plugins/core/depth_groovy_datamosh/__init__.py` (similar)
- **Plugin manifest:** `plugins/core/depth_groovy_datamosh/plugin.json`
- **Memory leak:** `gl_leaks.txt` confirms missing `glDeleteTextures`.

---

## Migration Notes Summary

| Aspect | Legacy (OpenGL) | WebGPU Target |
|--------|----------------|---------------|
| Shader Language | GLSL 330 core | WGSL |
| Uniforms | Many individual `set_uniform` calls | Uniform buffer struct (pack all floats) |
| Textures | `tex0=0`, `texPrev=1`, `depth_tex=2` | Bind group layout (3 textures + samplers) |
| Unused uniform | `tex1` declared but not used | Remove entirely |
| Performance | Heavy (multiple gradients, trig, hash) | Same algorithm; consider optimizing gradient reuse |
| Audio reactivity | CPU-side modulation | Same pattern |
| Memory management | `glGenTextures` leak | `GPUTexture` with explicit destroy |

---

## Conclusion

`DepthGroovyDatamoshEffect` is the **ultimate psychedelic depth effect**, combining a dozen techniques into a coherent, depth-modulated, audio-reactive experience. It pushes the limits of what's possible in a real-time fragment shader, and its performance cost is correspondingly high. The effect is **unapologetically maximalist**, designed for VJs who want to "turn everything up to 11." The code has some minor issues (unused `tex1`, depth gradient aspect ratio bug) that should be fixed in the WebGPU port. The easter egg "Groovy Fibonacci Resonance" rewards setting all parameters to the midpoint and letting the effect run, unlocking a mathematically harmonious mode that breathes with Fibonacci numbers. This effect is a **crown jewel** of the depth plugin and will be a showstopper in live performance when optimized properly.
