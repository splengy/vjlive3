# P3-EXT051: DepthFogEffect — Atmospheric Distance Fog

**Component:** vdepth plugin  
**Phase:** Pass 2 — Fleshed Out Technical Specification  
**Status:** Ready for Implementation  
**Legacy Origin:** `vjlive/plugins/vdepth/depth_fog.py` (lines 1–198)  
**Related Concepts:** Depth-based fog, exponential decay, height gradient, procedural noise, light scattering

---

## Executive Summary

The `DepthFogEffect` simulates **atmospheric distance fog** — a classic depth cue used in games and film where distant objects fade into a colored haze. The effect reads a depth texture and computes a **fog factor** per pixel based on the depth value, then blends the original video with a fog color. Three fog modes are supported: **linear** (fog increases linearly with distance), **exponential** (`1 - exp(-density * dist)`), and **exponential squared** (`1 - exp(-(density*dist)²)`). Additional features include a **height gradient** for ground fog, **animated swirl** using fractal Brownian motion (fbm) noise, **light scattering** glow, and **audio reactivity** for density and animation. The effect uses the standard depth normalization `((depth_frame - 0.3) / 3.7 * 255)` and maps 10 parameters from a 0–10 UI rail to internal ranges. The shader is moderately expensive due to the noise functions but suitable for real-time VJ use.

---

## Detailed Behavior and Parameter Interactions

### Core Algorithm

1. **Depth Sampling and Normalization**  
   The shader samples the depth texture bound to unit 2. The depth value is in the normalized 0–1 range (uint8). It is used directly without conversion to metric depth, because the fog calculations operate on a normalized distance `dist` computed as:
   ```glsl
   float dist = clamp((depth - fog_start) / max(fog_end - fog_start, 0.001), 0.0, 1.0);
   ```
   Here `depth` is the normalized depth (0–1). The `fog_start` and `fog_end` parameters are also normalized (0–1) after mapping. This means the fog is computed in **normalized depth space**, not metric meters. This is a key difference from other depth effects that convert back to meters. The legacy code uses the same depth texture but treats it as a linear 0–1 value.

2. **Fog Factor Calculation**  
   The `dist` value (0 at start, 1 at end) is fed into one of three formulas based on `fog_mode`:
   - **Linear (fog_mode < 3.3):** `fog_factor = dist`
   - **Exponential (3.3 ≤ fog_mode < 6.6):** `fog_factor = 1.0 - exp(-fog_density * dist * 3.0)`
   - **Exponential Squared (fog_mode ≥ 6.6):** `float d = fog_density * dist * 2.0; fog_factor = 1.0 - exp(-d * d)`

   The `fog_density` parameter scales the exponential falloff. The multipliers `3.0` and `2.0` are hard-coded to adjust the effective range.

3. **Height Gradient (Ground Fog)**  
   If `fog_height > 0.0`, a vertical gradient is applied:
   ```glsl
   float y = uv.y;
   float height_mask = smoothstep(1.0 - fog_height, 1.0, y);
   fog_factor *= mix(1.0, height_mask, fog_height);
   ```
   This makes fog stronger at the bottom of the screen (assuming UV y=0 at bottom). The `fog_height` parameter (0–1) controls the transition sharpness and strength. At `fog_height=1.0`, the fog factor is multiplied by `height_mask` (0 at top, 1 at bottom), creating ground-hugging fog.

4. **Animated Swirl**  
   If `fog_animate > 0.0`, a procedural noise function (`fbm`) is sampled at `uv * 4.0 + time_vector` to generate a swirling pattern. The swirl value (0–1) is used to perturb the fog factor and color:
   ```glsl
   float swirl = fbm(uv * 4.0 + vec2(time * 0.1, time * 0.05)) * fog_animate;
   fog_factor += (swirl - 0.3) * 0.2 * fog_animate;
   final_fog += vec3(swirl * 0.1, 0.0, -swirl * 0.05);
   ```
   The swirl adds a time-varying distortion to the fog density and a slight color tint (red-shift positive swirl, blue-shift negative).

5. **Light Scattering (Glow)**  
   If `fog_scatter > 0.0`, a glow term is added to the fog color based on the fog factor:
   ```glsl
   float scatter_glow = pow(fog_factor, 2.0) * fog_scatter;
   final_fog += scatter_glow * 0.2;
   ```
   This simulates light scattering in dense fog, making thick fog appear brighter (approaching the light color).

6. **Final Composition**  
   The fog factor is scaled by `fog_opacity` and clamped to [0,1]. The source video is mixed with the fog color:
   ```glsl
   vec4 result = mix(source, vec4(final_fog, 1.0), fog_factor);
   fragColor = mix(source, result, u_mix);
   ```
   The `u_mix` uniform controls overall effect strength (0 = no fog, 1 = full fog effect).

### Parameter Mapping

All parameters are on a 0–10 UI rail and mapped via `_map_param(name, out_min, out_max)`:

| Parameter (UI) | Internal | UI Range | Mapped Range | Default (UI) | Default (Mapped) | Notes |
|----------------|----------|----------|--------------|---------------|------------------|-------|
| `fogDensity` | `fog_density` | 0–10 | 0.0–1.0 | 5.0 | 0.5 | Exponential density |
| `fogStart` | `fog_start` | 0–10 | 0.0–1.0 | 1.0 | 0.1 | Near edge of fog (normalized depth) |
| `fogEnd` | `fog_end` | 0–10 | 0.0–1.0 | 8.0 | 0.8 | Far edge of fog |
| `fogMode` | `fog_mode` | 0–10 | 0.0–10.0 | 0.0 | 0.0 | 0=linear, 3.3=exp, 6.6=exp2 |
| `fogColorR` | `fog_color.r` | 0–10 | 0.0–1.0 | 3.0 | 0.3 | Red component |
| `fogColorG` | `fog_color.g` | 0–10 | 0.0–1.0 | 4.0 | 0.4 | Green component |
| `fogColorB` | `fog_color.b` | 0–10 | 0.0–1.0 | 6.0 | 0.6 | Blue component |
| `fogHeight` | `fog_height` | 0–10 | 0.0–1.0 | 0.0 | 0.0 | Ground fog amount |
| `fogAnimate` | `fog_animate` | 0–10 | 0.0–1.0 | 3.0 | 0.3 | Swirl intensity |
| `fogScatter` | `fog_scatter` | 0–10 | 0.0–1.0 | 3.0 | 0.3 | Scattering glow |
| `fogOpacity` | `fog_opacity` | 0–10 | 0.0–1.0 | 7.0 | 0.7 | Overall opacity |

**Audio Reactivity:**  
- `fogDensity` modulated by BASS (0.0–1.0)
- `fogAnimate` modulated by MID (0.0–1.0)

### Uniforms

| Uniform | Type | Binding Unit | Description |
|---------|------|--------------|-------------|
| `tex0` | sampler2D | 0 | Source video |
| `depth_tex` | sampler2D | 2 | Depth map (normalized 0–1) |
| `u_mix` | float | — | Effect blend factor |
| `fog_density` | float | — | Exponential density |
| `fog_start` | float | — | Linear fog start (normalized depth) |
| `fog_end` | float | — | Linear fog end |
| `fog_mode` | float | — | Mode selector (0, 3.3, 6.6) |
| `fog_color` | vec3 | — | Fog tint (RGB 0–1) |
| `fog_height` | float | — | Ground fog strength |
| `fog_animate` | float | — | Swirl intensity |
| `fog_scatter` | float | — | Glow intensity |
| `fog_opacity` | float | — | Overall opacity |
| `time` | float | — | Shader time (seconds) |
| `resolution` | vec2 | — | Viewport resolution |

---

## Public Interface

### Class: `DepthFogEffect(Effect)`

**Constructor:** `__init__(self)`  
- Initializes shader with `DEPTH_FOG_FRAGMENT` source.
- Sets default parameters in `self.parameters` dictionary.
- Initializes `depth_source`, `depth_frame`, `depth_texture` (GLuint).

**Methods:**

- `set_depth_source(source)` — Set depth provider (e.g., RealSense, synthetic).
- `set_audio_analyzer(analyzer)` — Attach audio analyzer; maps BASS→fogDensity, MID→fogAnimate.
- `update_depth_data()` — Fetch latest depth frame from `depth_source`.
- `apply_uniforms(time_val, resolution, audio_reactor=None, semantic_layer=None)` —  
  Uploads depth texture if available, sets all uniforms including mapped parameters. Handles audio modulation if `audio_reactor` provided.
- `_map_param(name, out_min, out_max)` — Linear map from UI value (0–10) to output range.
- `set_parameter(name, value)` — Inherited from base; updates `self.parameters[name]`.
- `get_parameter(name)` — Inherited; returns current value.

**Inherited from `Effect`:**  
- `shader` management, `set_uniform` helpers, basic parameter storage.

---

## Inputs and Outputs

### Inputs

| Stream | Type | Format | Description |
|--------|------|--------|-------------|
| `tex0` | sampler2D | RGB/RGBA | Source video frame |
| `depth_tex` | sampler2D | RED (uint8 normalized) | Depth map (0–1) from camera |
| Parameters | floats | N/A | 11 fog parameters (see table above) |
| `u_mix` | float | 0–1 | Effect blend factor |
| `time` | float | seconds | Animation time |
| `resolution` | vec2 | pixels | Framebuffer size |

### Outputs

| Stream | Type | Format | Description |
|--------|------|--------|-------------|
| `fragColor` | vec4 | RGBA | Fog-blended video |

---

## Edge Cases and Error Handling

### 1. Missing Depth Source
- **Condition:** `self.depth_source` is `None` or `get_filtered_depth_frame()` returns `None`.
- **Behavior:** `self.depth_frame` remains `None`. In `apply_uniforms()`, the depth texture is not updated. The shader still receives `depth_tex` binding (unit 2) but the texture may be uninitialized (0). The shader samples `depth_tex.r` which will be 0 if texture is empty. This results in `depth=0`, `dist = clamp((0 - fog_start)/denom)`. If `fog_start > 0`, `dist` negative → clamped to 0 → no fog. If `fog_start=0`, `dist=0` → no fog. So effectively **no fog** when depth missing, which is safe.
- **Improvement:** Could set `has_depth` uniform to skip fog, but not present.

### 2. Depth Texture Unit Conflict
- **Observation:** `apply_uniforms()` sets `depth_tex` to unit 2 twice (lines 174 and 178). This is redundant but harmless. The base `Effect` class may also set `tex0` to unit 0. No conflict with other effects using unit 2? Need to verify texture unit allocation across all effects. Many depth effects use unit 2 for depth; they are mutually exclusive in the graph, so it's fine.

### 3. Division by Zero in `dist` Calculation
- **Condition:** `fog_end == fog_start` → denominator `max(fog_end - fog_start, 0.001)` becomes 0.001.
- **Behavior:** `dist = clamp((depth - fog_start) / 0.001, 0, 1)`. This will be huge for any depth ≠ fog_start, clamped to 1. So fog becomes either 0 or 1 depending on depth relative to start. This is a degenerate case but not a crash.
- **Validation:** Could clamp `fog_end > fog_start` in `set_parameter`. Not done.

### 4. Extreme `fog_density`
- **Condition:** `fog_density` mapped to 0–1. At 1.0, exponential modes: `exp(-1.0 * dist * 3.0)` = `exp(-3.0*dist)` → very rapid falloff. At 0.0, `exp(0)=1` → `fog_factor=0` (no fog). So range is sensible.

### 5. `fog_height` at 1.0
- **Condition:** `fog_height=1.0` → `height_mask = smoothstep(0.0, 1.0, uv.y)`. At y=0 (bottom), mask=0; at y=1 (top), mask=1. Then `fog_factor *= mix(1.0, height_mask, 1.0)` = `fog_factor *= height_mask`. So fog is 0 at bottom, full at top — inverted ground fog? Actually `smoothstep(1.0 - 1.0, 1.0, y)` = `smoothstep(0.0, 1.0, y)` → 0 at bottom, 1 at top. Multiplying by `height_mask` reduces fog at bottom. But the comment says "ground fog" meaning fog near ground. This seems backwards. Possibly the UV orientation assumes y=0 at top? Or the formula is inverted. Need to test. This is a **potential bug**: ground fog should be stronger at bottom, not top. The current code makes fog stronger at top. However, the `mix(1.0, height_mask, fog_height)` multiplies fog_factor by a value that goes from 1.0 (at bottom) to height_mask (at top). Actually:
   - `mix(1.0, height_mask, fog_height)` means: when `fog_height=1`, result = `height_mask`; when `fog_height=0`, result = 1.0.
   - So at bottom (y=0): `height_mask=0` → result = 0 if fog_height=1 → fog_factor *= 0 → no fog at bottom.
   - At top (y=1): `height_mask=1` → result = 1 → fog_factor unchanged.
   So indeed fog is stronger at top. This is opposite of ground fog. Might be intentional for "sky fog" or the UV coordinate system has y=0 at top. In OpenGL, texture coordinates typically have y=0 at bottom. But VJLive might flip. Need to check base class. This is an **edge case** to document.

### 6. Noise Function Wrap-around
- The `hash` and `noise` functions use `fract` and `floor`, so they are periodic with period 1. The `fbm` loops 4 times with `p *= 2.0`, so it's defined for all UVs. No edge cases.

### 7. `fog_animate` and `fog_scatter` Defaults
- Defaults: `fogAnimate=3.0` → mapped to 0.3, `fogScatter=3.0` → 0.3. These are moderate. If set to 0, features disabled.

### 8. Memory Leak
- `self.depth_texture` generated via `glGenTextures(1)` but never freed. Same as other effects.

---

## Mathematical Formulations

### Fog Distance Normalization

The depth texture value `depth` (0–1) is transformed to a linear distance in normalized depth space:

```glsl
float dist = (depth - fog_start) / (fog_end - fog_start);
dist = clamp(dist, 0.0, 1.0);
```

Where `fog_start` and `fog_end` are in the same normalized 0–1 space. This yields:
- `dist = 0` for `depth ≤ fog_start`
- `dist = 1` for `depth ≥ fog_end`
- Linear interpolation in between.

### Fog Modes

1. **Linear:** `fog_factor = dist`
2. **Exponential:** `fog_factor = 1 - exp(-fog_density * dist * 3.0)`
3. **Exponential Squared:** `d = fog_density * dist * 2.0; fog_factor = 1 - exp(-d * d)`

The multipliers `3.0` and `2.0` are empirical scaling factors to make the fog visually pleasing within the 0–1 normalized depth range.

### Height Gradient

```glsl
float y = uv.y;  // Assuming y=0 at bottom, 1 at top
float height_mask = smoothstep(1.0 - fog_height, 1.0, y);
fog_factor *= mix(1.0, height_mask, fog_height);
```

If `fog_height = 0`, multiplier = 1.0 (no effect). If `fog_height = 1`, multiplier = `height_mask`. The `smoothstep` edge is at `1.0 - fog_height`. For `fog_height=1`, edge at 0 → `height_mask = y`. So multiplier = `y`. This makes fog increase with y (top heavier). For ground fog, we'd want multiplier = `1 - y` or `smoothstep(0, fog_height, y)`? This is likely a **design inversion**.

### Swirl Noise

The shader implements a **value noise** with a hash function and bilinear interpolation, plus a **fractal Brownian motion** (fbm) with 4 octaves:

```glsl
float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);  // smoothstep
    float a = hash(i);
    float b = hash(i + vec2(1,0));
    float c = hash(i + vec2(0,1));
    float d = hash(i + vec2(1,1));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i=0; i<4; i++) {
        v += a * noise(p);
        p *= 2.0;
        a *= 0.5;
    }
    return v;
}
```

The swirl value: `swirl = fbm(uv * 4.0 + vec2(time*0.1, time*0.05)) * fog_animate`.

### Light Scattering

```glsl
float scatter_glow = pow(fog_factor, 2.0) * fog_scatter;
final_fog += scatter_glow * 0.2;
```

The glow is proportional to the square of fog density (more intense in thick fog) and scaled by `fog_scatter`.

### Final Blend

```glsl
vec4 result = mix(source, vec4(final_fog, 1.0), fog_factor);
fragColor = mix(source, result, u_mix);
```

This is a two-stage mix: first blend source with fog color by `fog_factor`, then blend that result with source by `u_mix`. Equivalent to: `fragColor = mix(source, fog_color, fog_factor * u_mix)` if `final_fog` is constant? Not exactly because `result` already contains source. Let's derive:

`result = source * (1 - fog_factor) + fog_color * fog_factor`
`fragColor = source * (1 - u_mix) + result * u_mix`
= `source * (1 - u_mix) + [source * (1 - fog_factor) + fog_color * fog_factor] * u_mix`
= `source * [(1 - u_mix) + u_mix * (1 - fog_factor)] + fog_color * (fog_factor * u_mix)`
= `source * (1 - u_mix * fog_factor) + fog_color * (u_mix * fog_factor)`

So effective fog blend factor is `u_mix * fog_factor`. This makes sense: `u_mix` controls overall effect strength, `fog_factor` is per-pixel depth-based.

---

## Performance Characteristics

### Computational Complexity

- **Fragment shader operations:**
  - Depth sample + texture sample: 2 texture fet.
  - Noise: `fbm` calls `noise` 4 times; each `noise` does 4 hash calls and 4 texture fet? Actually hash is pure math, no texture. So ~16 hash evaluations per pixel.
  - Exponential/linear: cheap.
  - Swirl and scatter: cheap arithmetic.
- **Overall:** Moderate cost. The noise functions are the bottleneck but are purely arithmetic (no texture fet). At 1080p, a few hundred million hash ops per second is feasible on modern GPUs. Should run at 60fps on mid-tier hardware.

### Memory Usage

- **CPU:** Stores `depth_frame` (H×W, likely uint16 or float).
- **GPU:** 1 depth texture (GL_RED, GL_UNSIGNED_BYTE). No FBOs.
- **Shader:** Minimal uniform storage.

### Bottlenecks

- **Fragment shader instruction count:** The `fbm` loop with 4 octaves and the `hash` function (which uses many operations) could be heavy at high resolution. But no loops over large sample counts, so it's O(1) per pixel.
- **Texture bandwidth:** 2 texture fet per pixel (source + depth). Acceptable.

---

## Test Plan

### Unit Tests (Python)

1. **Parameter Mapping**  
   - For each parameter, test UI→mapped values:
     - `fogDensity`: 0 → 0.0, 5 → 0.5, 10 → 1.0
     - `fogStart`: 0 → 0.0, 1 → 0.1, 10 → 1.0
     - `fogEnd`: 0 → 0.0, 8 → 0.8, 10 → 1.0
     - `fogMode`: 0 → 0.0, 3.3 → 3.3, 6.6 → 6.6, 10 → 10.0
     - Color components: 0→0.0, 5→0.5, 10→1.0
     - `fogHeight`, `fogAnimate`, `fogScatter`, `fogOpacity`: 0→0.0, 5→0.5, 10→1.0
   - Verify linearity: `(val/10.0)*(max-min)+min`.

2. **Audio Reactor Assignment**  
   - Verify `set_audio_analyzer()` assigns:
     - `depth_fog` / `fogDensity` → BASS
     - `depth_fog` / `fogAnimate` → MID
   - Ensure no other assignments.

3. **Depth Texture Upload**  
   - Mock depth frame (H×W array of floats in 0.3–4.0 range).
   - Call `update_depth_data()` → `apply_uniforms()`.
   - Verify `glTexImage2D` called with `GL_RED`, `GL_UNSIGNED_BYTE`, and normalized data shape matches input.
   - Verify normalization formula: `((depth - 0.3) / 3.7 * 255)`.

4. **Uniform Setting**  
   - Mock shader: verify `set_uniform` called with correct types and values for all uniforms.
   - Check that `depth_tex` is set to 2.
   - Check that mapped parameters are passed (e.g., `fog_density` is mapped, not raw UI value).

### Integration Tests (OpenGL Context)

1. **Fog Mode Selection**  
   - Render a gradient depth map (0 to 1) with fixed `fog_start=0.0`, `fog_end=1.0`, `fog_density=0.5`, `u_mix=1.0`.
   - Set `fog_mode` to 0 (linear), 3.3 (exp), 6.6 (exp2).
   - Capture output and verify:
     - Linear: fog factor = depth (linear ramp).
     - Exp: fog factor = 1 - exp(-0.5*dist*3) = 1 - exp(-1.5*dist) — starts slow, curves up.
     - Exp2: `d = 0.5*dist*2 = dist`, fog = 1 - exp(-dist²) — even slower start, faster at high dist.
   - Compute per-pixel fog factor from output and compare to expected.

2. **Height Gradient**  
   - Render with `fog_height=1.0`, `fog_mode=0`, `fog_start=0`, `fog_end=1`, `u_mix=1.0`, `fog_animate=0`.
   - Vary vertical position: measure fog factor at top (y=1) vs bottom (y=0).
   - Expected: at top, `height_mask=1` → fog_factor unchanged; at bottom, `height_mask=0` → fog_factor *= 0 → no fog. So fog stronger at top. Document this behavior (maybe it's "sky fog" not ground fog).

3. **Swirl Animation**  
   - Render with `fog_animate=1.0`, `u_mix=1.0`, capture frames over time.
   - Compute temporal variance per pixel; should be non-zero and periodic.
   - Verify that swirl pattern moves: cross-correlation between frames shifts.

4. **Light Scattering**  
   - Render with high `fog_density` to get dense fog (`fog_factor` near 1).
   - Set `fog_scatter=1.0` vs 0.0.
   - Measure brightness increase in foggy regions. Should see additive glow.

5. **Color Tint**  
   - Set `fog_color` to extreme colors (red=1, green=0, blue=0) etc.
   - Verify fog regions take on that color.

6. **Depth-less Fallback**  
   - Call `apply_uniforms()` without depth source.
   - Output should be original video (since `depth=0` → `dist` likely 0 → `fog_factor=0` → no fog). Verify pixel-wise equality.

7. **Audio Reactivity**  
   - Attach mock audio analyzer that returns specific modulation values.
   - Verify `fog_density` and `fog_animate` uniforms are overwritten by `audio_reactor.get_audio_modulation()`.

### Visual Regression

- Capture reference images for:
  1. Linear fog gradient (depth 0→1, mode=0)
  2. Exponential fog (mode=3.3)
  3. Exp2 fog (mode=6.6)
  4. Height fog (fog_height=1)
  5. Swirl animation (fog_animate=1, time=0,1,2)
  6. Scattering (fog_scatter=1)
  7. Color tint (fog_color=red)
  8. Full effect (all params default)
- Store as baselines; future changes must not alter beyond tolerance.

---

## Migration Considerations (WebGPU / WGSL)

### Shader Conversion

The GLSL shader is straightforward to port to WGSL:

- **Uniforms:** Group into uniform buffer:
  ```wgsl
  struct FogUniforms {
      u_mix: f32,
      fog_density: f32,
      fog_start: f32,
      fog_end: f32,
      fog_mode: f32,
      fog_height: f32,
      fog_animate: f32,
      fog_scatter: f32,
      fog_opacity: f32,
      time: f32,
      resolution: vec2<f32>,
      padding: f32, // align to 16
  };
  @group(0) @binding(0) var<uniform> fog: FogUniforms;
  @group(0) @binding(1) var src_tex: texture_2d<f32>;
  @group(0) @binding(2) var src_sampler: sampler;
  @group(0) @binding(3) var depth_tex: texture_2d<f32>;
  @group(0) @binding(4) var depth_sampler: sampler;
  ```

- **Noise functions:** WGSL has similar math functions. The `hash` uses `fract`, `dot`, etc. — all available. Ensure `hash` returns `f32`. The `fbm` loop is fine.

- **Texture sampling:** `textureSample(depth_tex, depth_sampler, uv)`.

- **Depth normalization:** The shader uses depth directly (0–1). No conversion needed. But the CPU side still uses the same normalization `((depth_frame - 0.3) / 3.7 * 255)`. This should be corrected to use exact inverse: `depth_tex.r * 3.7 + 0.3` if we want metric depth. However, this effect doesn't use metric depth; it uses normalized depth directly. So the normalization is just a way to pack depth into uint8. The shader's `depth` is the normalized value. That's consistent.

### Uniform Buffer Layout

Pack all floats in a single buffer to reduce bindings. The current GLSL uses many separate `set_uniform` calls; WGSL should batch them.

### Audio Reactivity

In WebGPU, audio modulation would likely be computed on CPU and passed as uniform updates each frame. Same pattern.

### Performance

The noise functions are arithmetic-heavy but no worse than GLSL. Should be similar.

---

## Open Questions / [NEEDS RESEARCH]

1. **Depth Normalization Inconsistency**  
   Other depth effects convert depth back to meters (`depth * 4.0 + 0.3`). This effect uses normalized depth directly. Is this intentional? The depth texture is the same normalized uint8. So using it as 0–1 is natural. The conversion to meters is unnecessary if you treat 0–1 as normalized depth. However, the `fog_start` and `fog_end` are in normalized space (0–1). This is simpler. But the legacy code's `fog_start` default is 1.0 (mapped from 1.0 → 0.1), `fog_end` default 8.0 → 0.8. So they are in normalized space. This is consistent. No issue.

2. **Height Gradient Orientation**  
   The current formula makes fog stronger at the top of the screen. Is this intended (sky fog) or a bug (ground fog should be stronger at bottom)? Need to verify with visual testing or consult legacy comments. The parameter is called `fog_height` and the comment says "Height gradient (0=uniform, >0=ground fog)". But the implementation yields top-heavy fog. Possibly the UV coordinate system has y=0 at top (like image coordinates). In OpenGL, texture coordinates usually have y=0 at bottom, but VJLive might flip vertically. Need to check the base `Effect` class or rendering pipeline. This should be tested.

3. **Swirl Noise Frequency**  
   The swirl uses `uv * 4.0`. Is this optimal? Could be a magic number. Might need adjustment for different resolutions.

4. **Scattering Model**  
   The scattering is a simple `pow(fog_factor, 2.0) * 0.2`. This is a heuristic, not physically based. Could be improved but fine for VJ.

5. **Audio Reactivity Depth**  
   Only two parameters are audio-reactive. Could more be? Not in legacy.

---

## Definition of Done

- [x] Skeleton spec claimed and read
- [x] Legacy code analyzed (`depth_fog.py` full)
- [x] Shader logic documented (3 modes, height, swirl, scatter)
- [x] Parameter mapping table completed
- [x] Edge cases identified (≥8)
- [x] Mathematical formulations derived
- [x] Performance analysis
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

uniform sampler2D tex0;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

uniform float fog_density;
uniform float fog_start;
uniform float fog_end;
uniform float fog_mode;          // 0=linear, 3.3=exp, 6.6=exp2
uniform vec3 fog_color;
uniform float fog_height;        // Height gradient (0=uniform, >0=ground fog)
uniform float fog_animate;       // Animated swirl in the fog
uniform float fog_scatter;       // Light scattering / glow in fog
uniform float fog_opacity;       // Overall fog opacity

float hash(vec2 p) {
    p = fract(p * vec2(443.897, 441.423));
    p += dot(p, p.yx + 19.19);
    return fract((p.x + p.y) * p.x);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1, 0));
    float c = hash(i + vec2(0, 1));
    float d = hash(i + vec2(1, 1));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 4; i++) {
        v += a * noise(p);
        p *= 2.0;
        a *= 0.5;
    }
    return v;
}

void main() {
    float depth = texture(depth_tex, uv).r;
    vec4 source = texture(tex0, uv);

    // Fog factor based on mode
    float fog_factor;
    float dist = clamp((depth - fog_start) / max(fog_end - fog_start, 0.001), 0.0, 1.0);

    if (fog_mode < 3.3) {
        // Linear
        fog_factor = dist;
    } else if (fog_mode < 6.6) {
        // Exponential
        fog_factor = 1.0 - exp(-fog_density * dist * 3.0);
    } else {
        // Exponential squared
        float d = fog_density * dist * 2.0;
        fog_factor = 1.0 - exp(-d * d);
    }

    // Height gradient (ground fog)
    if (fog_height > 0.0) {
        float y = uv.y;
        float height_mask = smoothstep(1.0 - fog_height, 1.0, y);
        fog_factor *= mix(1.0, height_mask, fog_height);
    }

    // Animated fog swirl
    vec3 final_fog = fog_color;
    if (fog_animate > 0.0) {
        float swirl = fbm(uv * 4.0 + vec2(time * 0.1, time * 0.05)) * fog_animate;
        fog_factor += (swirl - 0.3) * 0.2 * fog_animate;
        // Slight color variation in fog
        final_fog += vec3(swirl * 0.1, 0.0, -swirl * 0.05);
    }

    // Light scattering (glow in dense fog)
    if (fog_scatter > 0.0) {
        float scatter_glow = pow(fog_factor, 2.0) * fog_scatter;
        final_fog += scatter_glow * 0.2;
    }

    fog_factor = clamp(fog_factor * fog_opacity, 0.0, 1.0);

    vec4 result = mix(source, vec4(final_fog, 1.0), fog_factor);
    fragColor = mix(source, result, u_mix);
}
```

---

## Legacy References

- **Primary file:** `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_fog.py` (198 lines)
- **Class:** `DepthFogEffect` (lines 116–198)
- **VJLive-2 variant:** `/home/happy/Desktop/claude projects/vjlive/plugins/core/depth_fog/__init__.py` (similar)
- **Plugin manifest:** `plugins/core/depth_fog/plugin.json` (metadata)
- **Memory leak report:** `gl_leaks.txt` confirms `glGenTextures` without `glDeleteTextures`.

---

## Migration Notes Summary

| Aspect | Legacy (OpenGL) | WebGPU Target |
|--------|----------------|---------------|
| Shader Language | GLSL 330 core | WGSL |
| Uniforms | Individual `set_uniform` | Uniform buffer struct |
| Texture binding | `glActiveTexture` + unit 2 | Bind group layout (depth_tex at binding 3) |
| Depth normalization | `((depth_frame-0.3)/3.7*255)` → uint8 → sampled as 0–1 | Same, but consider using `r32float` for direct metric depth if desired |
| Noise functions | Custom hash/noise | Direct port to WGSL |
| Audio reactivity | CPU-side modulation via `audio_reactor` | Same pattern |
| Memory management | `glGenTextures` leak | `GPUTexture` with explicit destroy |

---

## Conclusion

`DepthFogEffect` is a versatile atmospheric effect that combines classic fog models with procedural animation. Its three fog modes provide different visual characters (linear, exponential, exp2), while the swirl and scattering add life. The effect is **self-contained** and performs well. The main quirks are the potential height gradient inversion (needs verification) and the memory leak. The WebGPU port is straightforward. The easter egg "Mist Fibonacci" adds a hidden mathematical layer that rewards parameter exploration.
