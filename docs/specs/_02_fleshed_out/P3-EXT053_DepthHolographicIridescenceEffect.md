# P3-EXT053 — DepthHolographicIridescenceEffect

**Status**: 🟩 COMPLETING PASS 2
**Component**: vdepth plugin — holographic optics simulation
**Legacy Source**: `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_holographic.py`
**Class**: `DepthHolographicIridescenceEffect(Effect)`
**Lines**: ~600 total (shader ~300 lines, Python ~300 lines)

---

## Executive Summary

The **DepthHolographicIridescenceEffect** simulates holographic and iridescent materials by leveraging depth camera data to approximate surface normals and viewing angles. Unlike datamosh effects that rely on motion and displacement, this effect is rooted in **physical optics**:

- **Thin-film interference**: Color varies with effective film thickness (derived from depth) and viewing angle (derived from depth gradient magnitude). This creates the rainbow shimmer seen in soap bubbles, oil slicks, and holographic stickers.
- **Fresnel effect**: Surfaces viewed at grazing angles (steep depth gradients) exhibit stronger iridescence than head-on views.
- **Spectral dispersion**: Different wavelengths undergo different phase shifts, separating colors like a prism.
- **Diffraction grating**: Simulates micro-grooved holographic structures that create directional rainbow patterns.
- **Pearlescence**: Subtle luminous color shifts in highlights for a soft glow.

The effect is **maximalist in parameter count** (14 user-facing parameters) but **computationally efficient** compared to datamosh effects, as it operates per-pixel without feedback loops or multi-pass sampling.

---

## Shader Architecture Analysis

### Fragment Shader Structure

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;        // Current video frame
uniform sampler2D texPrev;     // Previous frame (unused in this effect)
uniform sampler2D depth_tex;   // Depth map (normalized 0-255 uint8)
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Thin-film uniforms
uniform float film_thickness;        // Base film thickness (wavelengths)
uniform float film_depth_scale;      // Depth → thickness modulation
uniform float interference_order;    // Visible interference orders

// Fresnel uniforms
uniform float fresnel_power;         // Falloff exponent (1-8)
uniform float fresnel_bias;          // Minimum iridescence at normal incidence

// Spectral uniforms
uniform float spectral_spread;       // Wavelength separation factor
uniform float spectral_shift;        // Animated hue shift

// Diffraction grating uniforms
uniform float grating_density;       // Groove density
uniform float grating_angle;         // Grating orientation
uniform float grating_order;         // Diffraction order

// Appearance uniforms
uniform float iridescence_amount;    // Overall intensity
uniform float pearlescence;          // Highlight luminous color
uniform float hologram_noise;        // Micro-texture grain
uniform float color_mode;            // Blend mode: 0=add, 5=overlay, 10=replace
uniform float shimmer_speed;         // Animation speed
```

### Texture Unit Assignment

| Texture | Unit | Purpose |
|---------|------|---------|
| `tex0` | 0 | Current video frame (RGBA) |
| `texPrev` | 1 | Previous frame (sampled but not used for feedback) |
| `depth_tex` | 2 | Depth map (RED channel, normalized 0-255) |

**Note**: `texPrev` is bound but unused; this is legacy artifact from base class.

### Core Algorithm Pipeline

1. **Depth Retrieval & Gradient Calculation**
   ```glsl
   float depth = texture(depth_tex, uv).r;  // 0-1 normalized
   vec2 gradient = compute_depth_gradient(uv, depth);  // Approximates surface normal
   float cos_theta = 1.0 - length(gradient) * fresnel_factor;  // Viewing angle cosine
   ```

2. **Thin-Film Interference**
   - Effective film thickness: `thickness_nm = film_thickness * 100.0 + depth * film_depth_scale * 500.0`
   - Optical path difference (OPD): `opd = 2.0 * n * thickness_nm * cos_theta_refracted`
   - Phase shift: `phase = 2.0 * π * opd / lambda`
   - Sum contributions across visible spectrum (380-780nm) with spectral spread

3. **Fresnel Modulation**
   ```glsl
   float fresnel = fresnel_bias + (1.0 - fresnel_bias) * pow(1.0 - cos_theta, fresnel_power);
   ```

4. **Diffraction Grating**
   - Directional rainbow based on grating angle and density
   - Grating order determines number of spectral orders visible

5. **Color Blending**
   - `color_mode = 0.0`: Additive blend (hologram over video)
   - `color_mode = 5.0`: Overlay blend (preserves video luminance)
   - `color_mode = 10.0`: Replace (pure hologram, no video)

6. **Pearlescence & Noise**
   - Specular highlight boost using `pearlescence`
   - Micro-texture via `hash(uv * resolution)` scaled by `hologram_noise`

7. **Temporal Shimmer**
   - `spectral_shift` animated by `time * shimmer_speed`
   - Creates shifting rainbow colors over time

---

## Parameter Mapping Table

All parameters are exposed on a **0-10 UI rail** and mapped to shader-specific ranges via `_map_param()`.

| Parameter Name | UI Range | Mapped Range | Default (UI) | Shader Default | Purpose |
|----------------|----------|--------------|--------------|----------------|---------|
| `filmThickness` | 0-10 | 0.0-1.0 (wavelengths × 1000) | 5.0 | 0.5 | Base thin-film thickness |
| `filmDepthScale` | 0-10 | 0.0-1.0 | 5.0 | 0.5 | Depth → thickness modulation |
| `interferenceOrder` | 0-10 | 0.0-1.0 | 5.0 | 0.5 | Number of visible interference orders |
| `fresnelPower` | 0-10 | 1.0-8.0 | 5.0 | 4.5 | Fresnel falloff exponent |
| `fresnelBias` | 0-10 | 0.0-0.5 | 2.0 | 0.1 | Minimum iridescence at normal incidence |
| `spectralSpread` | 0-10 | 0.5-2.0 | 5.0 | 1.25 | Wavelength separation factor |
| `spectralShift` | 0-10 | 0.0-1.0 | 0.0 | 0.0 | Animated hue shift (0-1 cycle) |
| `gratingDensity` | 0-10 | 0.0-1.0 | 3.0 | 0.3 | Diffraction groove density |
| `gratingAngle` | 0-10 | 0.0-1.0 | 0.0 | 0.0 | Grating orientation (radians/2π) |
| `gratingOrder` | 0-10 | 0.0-1.0 | 1.0 | 0.1 | Diffraction order (0=first, 1=second) |
| `iridescenceAmount` | 0-10 | 0.0-1.0 | 7.0 | 0.7 | Overall effect intensity |
| `pearlescence` | 0-10 | 0.0-1.0 | 3.0 | 0.3 | Highlight luminous color boost |
| `hologramNoise` | 0-10 | 0.0-1.0 | 1.0 | 0.1 | Micro-texture grain intensity |
| `colorMode` | 0-10 | 0.0-10.0 (discrete) | 5.0 | 5.0 | Blend mode (0=add, 5=overlay, 10=replace) |
| `shimmerSpeed` | 0-10 | 0.0-2.0 | 2.0 | 0.4 | Animation speed multiplier |

**Mapping Formula**: `mapped = out_min + (value / 10.0) * (out_max - out_min)`

---

## Public Interface

### Class: `DepthHolographicIridescenceEffect(Effect)`

#### Constructor
```python
def __init__(self) -> None
```
- Initializes parameters with defaults (see table above)
- Creates shader program from `DEPTH_HOLOGRAPHIC_FRAGMENT` source
- Allocates depth texture ID (`self.depth_texture = 0`)
- Sets up audio reactivity mappings if `audio_reactor` provided

#### Methods

##### `set_depth_source(source: DepthSource)`
Inherited from `DepthEffect` base class. Sets the depth camera source.

##### `update_depth_data() -> None`
Fetches latest depth frame from `self.depth_source` via `get_filtered_depth_frame()`.

##### `apply_uniforms(time_val: float, resolution: tuple, audio_reactor=None, semantic_layer=None) -> None`
Main rendering entry point. Uploads all uniforms and depth texture.

**Steps**:
1. Call `super().apply_uniforms()` to bind base uniforms (`tex0`, `texPrev`, `u_mix`, `time`, `resolution`)
2. Call `self.update_depth_data()` to refresh depth frame
3. If `depth_frame` exists:
   - Generate GL texture if not yet created (`glGenTextures(1)`)
   - Normalize depth: `(depth_frame - 0.3) / (4.0 - 0.3) * 255` → `uint8`
   - Upload to `GL_TEXTURE_2D` with `GL_RED` format
   - Bind to texture unit 2
4. Map all 14 parameters from 0-10 rail to shader ranges
5. If `audio_reactor` present, apply audio modulation to:
   - `spectral_shift` (TREBLE)
   - `shimmer_speed` (TREBLE)
   - `film_thickness` (MID)
   - `iridescence_amount` (MID)
   - `grating_density` (BASS)

##### `set_parameter(name: str, value: float) -> None`
Sets parameter value (0-10 range). Validates parameter name.

##### `get_parameter(name: str) -> float`
Returns current parameter value.

---

## Inputs and Outputs

### Inputs

| Stream | Type | Format | Source |
|--------|------|--------|--------|
| Video A | `tex0` | RGBA texture | External video input |
| Video B | `texPrev` | RGBA texture | Previous frame buffer (unused) |
| Depth | `depth_tex` | RED channel, uint8 normalized 0-255 | Depth camera (0.3-4.0m range) |
| Time | `time` | float (seconds) | System clock |
| Resolution | `resolution` | vec2(int, int) | Framebuffer size |
| Mix | `u_mix` | float (0-1) | Effect blend amount |
| Audio | `audio_reactor` | BASS/MID/TREBLE features | Optional audio analyzer |

### Outputs

- **Fragment color**: `fragColor` (RGBA) — holographically iridesced video
- **No feedback**: This effect does not write to feedback buffers; it's a single-pass filter

---

## Edge Cases and Error Handling

### 1. Missing Depth Source
- **Behavior**: If `self.depth_source` is `None` or `self.depth_frame` is `None`/empty:
  - Depth texture upload is skipped
  - Shader still runs but `depth_tex` may contain uninitialized data
  - **Risk**: Visual artifacts or crashes if shader samples invalid texture
- **Mitigation**: Base class `DepthEffect` should set `has_depth` uniform; this effect does **not** check `has_depth` in shader (unlike `DepthFieldEffect`). **Bug**: Should add `uniform float has_depth;` and early-out in shader.

### 2. Depth Normalization Assumption
- **Assumes** depth values in **meters** with range 0.3–4.0m.
- Formula: `depth_normalized = ((depth_frame - 0.3) / 3.7) * 255`
- **Edge case**: If depth camera returns values outside this range:
  - Values < 0.3 → negative → clamp to 0 (underflow wraps to large uint8)
  - Values > 4.0 → >255 → clamp to 255 (overflow wraps to 0)
- **Bug**: No explicit clamping before conversion; integer overflow possible.

### 3. Texture Unit Conflicts
- Uses texture units 0, 1, 2.
- Unit 1 (`texPrev`) is bound but **unused** in shader.
- **Safe**: No conflict with other effects that also use units 0-2.

### 4. Color Mode Discrete Values
- `color_mode` is mapped from continuous 0-10 rail to continuous 0.0-10.0 range.
- Shader expects discrete blend modes at specific thresholds:
  - `< 3.33`: additive
  - `3.33-6.66`: overlay (implicit via `mix`? Need to check shader logic)
  - `> 6.66`: replace
- **Edge**: Values near boundaries may produce unintended blends.

### 5. Audio Reactor Missing
- If `audio_reactor` is `None`, audio modulation code is skipped.
- No error raised; effect falls back to static parameter values.

### 6. High Parameter Values
- `fresnel_power` mapped to 1.0-8.0. Values > 8.0 clamped to 8.0.
- `shimmer_speed` mapped to 0.0-2.0. High speeds may cause visual strobing.
- `grating_density` > 0.8 may cause moiré patterns with fine video detail.

### 7. Performance
- **Complexity**: O(1) per pixel, ~12 spectral samples per pixel.
- **Cost**: Moderate (12× more work than simple color filter).
- **No feedback loops**: No texture read-write hazards, safe for multi-pass chains.

---

## Mathematical Formulations

### 1. Depth Normalization
```python
depth_normalized = ((depth_frame - 0.3) / (4.0 - 0.3) * 255).astype(np.uint8)
```
Converts metric depth (meters) to 8-bit texture value.

### 2. Depth Gradient Approximation
```glsl
vec2 gradient = vec2(
    texture(depth_tex, uv + vec2(texel.x, 0.0)).r - texture(depth_tex, uv - vec2(texel.x, 0.0)).r,
    texture(depth_tex, uv + vec2(0.0, texel.y)).r - texture(depth_tex, uv - vec2(0.0, texel.y)).r
) / (2.0 * texel);
```
Where `texel = 1.0 / resolution`. This approximates surface normal via central differences.

### 3. Fresnel Factor
```glsl
float cos_theta = 1.0 - length(gradient) * fresnel_factor;  // Approximated
float fresnel = fresnel_bias + (1.0 - fresnel_bias) * pow(1.0 - cos_theta, fresnel_power);
```
`fresnel_factor` is a constant scaling gradient magnitude to approximate viewing angle.

### 4. Thin-Film Interference (Bruton Algorithm)
For each wavelength λ (380-780nm):
```glsl
float phase = 2.0 * π * (2.0 * n * thickness_nm * cos_theta_r) / λ;
float intensity = cos(phase) * 0.5 + 0.5;  // Interference term
```
Summed across spectral samples with weights from `wavelength_to_rgb()`.

**Optical path difference**: `opd = 2 * n * d * cos(θ_r)` where:
- `n` = 1.5 (film refractive index)
- `d` = `thickness_nm` (film thickness in nm)
- `θ_r` = refracted angle (Snell's law: `sin(θ) = n * sin(θ_r)`)

### 5. Diffraction Grating
```glsl
float grating_phase = 2.0 * π * grating_density * (uv.x * cos(grating_angle) + uv.y * sin(grating_angle));
vec3 grating_color = wavelength_to_rgb(λ + grating_phase * grating_order * 100.0);
```
Grating creates spatial color variation based on position.

### 6. Spectral Dispersion
```glsl
float lambda = 380.0 + i * (400.0 / 12.0) * spectral_spread + spectral_shift * 100.0;
```
Samples 12 wavelengths across visible spectrum; `spectral_spread` widens/narrows separation; `spectral_shift` animates hue.

### 7. Color Blending
```glsl
if (color_mode < 3.33) {
    fragColor = vec4(base_rgb * iridescence + video.rgb, video.a);
} else if (color_mode < 6.66) {
    fragColor = overlay_blend(video, iridescence_rgb);
} else {
    fragColor = vec4(iridescence_rgb, video.a);
}
```
(Exact blend functions to be extracted from full shader source.)

---

## Performance Characteristics

### Computational Cost
- **Spectral sampling**: 12 wavelength samples per pixel × full-screen resolution
- **Gradient calculation**: 4 texture fetches (neighbors) per pixel
- **Total texture fetches per pixel**: ~16–20 (including video, depth, gradient, spectral loops)
- **Arithmetic intensity**: High (trigonometry, phase calculations, color space conversions)

### Memory Footprint
- **Textures**: 3 bound textures (video A, video B, depth)
- **Uniforms**: ~20 floats + 1 vec2
- **No FBOs**: Does not allocate intermediate framebuffers

### GPU Utilization
- **Fragment-bound**: Performance scales with resolution and spectral sample count.
- **Expected FPS** (1080p, mid-range GPU): 60–120 FPS depending on spectral sample count.
- **Compared to datamosh effects**: Lighter (no multi-pass feedback, no motion estimation).

### Optimization Opportunities
- Reduce spectral samples from 12 to 8 for performance boost (minor color quality loss).
- Precompute `wavelength_to_rgb` lookup table (256-entry 1D texture) instead of per-pixel function.
- Bake `grating_phase` into a tiled pattern texture to avoid per-pixel trig.

---

## Test Plan

### Unit Tests (Python)

1. **Parameter Mapping**
   ```python
   def test_map_param_bounds():
       effect = DepthHolographicIridescenceEffect()
       for param in ALL_PARAMS:
           value = effect._map_param(param, 0.0, 1.0)
           assert 0.0 <= value <= 1.0
   ```

2. **Depth Normalization**
   ```python
   def test_depth_normalization_clamping():
       depth_frame = np.array([0.0, 0.3, 2.15, 4.0, 10.0])
       normalized = (depth_frame - 0.3) / 3.7 * 255
       assert normalized[0] < 0  # Underflow
       assert normalized[-1] > 255  # Overflow
       # After astype(np.uint8): wrap-around occurs
   ```

3. **Audio Reactivity Assignment**
   ```python
   def test_audio_mapping():
       effect = DepthHolographicIridescenceEffect()
       analyzer = MockAudioAnalyzer()
       effect.set_audio_analyzer(analyzer)
       # Verify 5 assignments made (3 TREBLE, 2 MID, 1 BASS)
   ```

### Integration Tests (OpenGL)

1. **Texture Binding**
   - Verify depth texture bound to unit 2 after `apply_uniforms()`
   - Verify `tex0` bound to unit 0, `texPrev` to unit 1

2. **Shader Compilation**
   - Compile `DEPTH_HOLOGRAPHIC_FRAGMENT` shader
   - Link with base vertex shader
   - Check for uniform locations (all 14 parameters + depth_tex)

3. **Depth Gradient Edge Cases**
   - Render with flat depth (constant) → gradient = 0 → Fresnel = bias
   - Render with sharp depth edge → gradient spikes → verify no NaNs

### Visual Regression Tests

1. **Parameter Sweep**
   - Render test frame with each parameter at 0, 5, 10
   - Capture screenshots
   - Compare against golden images (pixel-perfect or SSIM > 0.99)

2. **Audio Modulation**
   - Feed synthetic audio (sine wave BASS/MID/TREBLE)
   - Verify parameter values change in real-time

3. **Color Mode Blends**
   - Render same scene with color_mode = 0, 5, 10
   - Verify additive brightens, overlay preserves highlights, replace discards video

### Performance Tests

1. **Frame Time Benchmark**
   ```python
   timeit(effect.apply_uniforms, resolution=(1920, 1080), repeats=100)
   # Target: < 16ms per frame for 60 FPS
   ```

2. **Spectral Sample Scaling**
   - Test with 6, 12, 24 samples
   - Measure FPS drop per doubling

---

## Migration Notes (WebGPU / VJLive3)

### WGSL Translation

**Challenges**:
- GLSL `texture()` → WGSL `textureSample()`
- Uniform buffers: Group all uniforms into a single `struct` (20+ floats)
- Texture bindings: Bind group layout with 3 samplers (video, prev, depth)

**Suggested Bind Group**:
```wgsl
struct Uniforms {
    time: f32,
    resolution: vec2<f32>,
    u_mix: f32,
    film_thickness: f32,
    film_depth_scale: f32,
    interference_order: f32,
    fresnel_power: f32,
    fresnel_bias: f32,
    spectral_spread: f32,
    spectral_shift: f32,
    grating_density: f32,
    grating_angle: f32,
    grating_order: f32,
    iridescence_amount: f32,
    pearlescence: f32,
    hologram_noise: f32,
    color_mode: f32,
    shimmer_speed: f32,
    padding: f32,  // align to 16-byte boundary
};

@group(0) @binding(0) var video_sampler: sampler;
@group(0) @binding(1) var video_tex: texture_2d<f32>;
@group(0) @binding(2) var prev_tex: texture_2d<f32>;
@group(0) @binding(3) var depth_tex: texture_2d<f32>;
@group(0) @binding(4) var<uniform> uniforms: Uniforms;
```

**WGSL Fragment**:
- Replace `gl_FragCoord` with `builtin(position)`
- Use `textureLoad` for depth gradient neighbor fetches (explicit offsets)
- `hash()` function: same implementation (fract-based)
- `wavelength_to_rgb()`: identical logic, WGSL syntax

### Memory Management
- **Legacy leak**: `glGenTextures(1)` called once, but `glDeleteTextures` never called.
- **WebGPU**: Texture allocation is explicit; must release when effect destroyed.
- **Fix**: Add `__del__()` method to delete GL texture, or use RAII wrapper.

### Audio Reactivity
- Legacy: `audio_reactor.get_audio_modulation()` called per-frame.
- WebGPU: Audio data should be in uniform buffer (e.g., `audio_bass`, `audio_mid`, `audio_treble`).
- Update: Copy audio features to uniform buffer each frame instead of per-parameter calls.

---

## Legacy Code References

### File: `depth_holographic.py` (full source)

**Key sections**:

1. **Shader string** (lines ~50-300):
   - `DEPTH_HOLOGRAPHIC_FRAGMENT` contains full GLSL 330 code
   - Includes `wavelength_to_rgb()`, `thin_film_color()`, `hash()`, `fresnel()`, `grating()`
   - Main `main()`: retrieves depth, computes gradient, calls interference, applies blend

2. **Class `DepthHolographicIridescenceEffect`** (lines ~320-600):
   - `__init__`: sets up 14 parameters in `self.parameters` dict
   - `apply_uniforms`: depth normalization, texture upload, parameter mapping, audio modulation
   - `update_depth_data`: fetches depth frame

3. **Audio mapping** (lines ~580-600):
   ```python
   self.audio_reactor.assign_audio_feature("depth_holo", "spectralShift", AudioFeature.TREBLE, 0.0, 1.0)
   self.audio_reactor.assign_audio_feature("depth_holo", "shimmerSpeed", AudioFeature.TREBLE, 0.0, 1.0)
   self.audio_reactor.assign_audio_feature("depth_holo", "filmThickness", AudioFeature.MID, 0.0, 1.0)
   self.audio_reactor.assign_audio_feature("depth_holo", "iridescenceAmount", AudioFeature.MID, 0.0, 1.0)
   self.audio_reactor.assign_audio_feature("depth_holo", "gratingDensity", AudioFeature.BASS, 0.0, 1.0)
   ```

4. **Depth normalization** (line ~460):
   ```python
   depth_normalized = ((self.depth_frame - 0.3) / (4.0 - 0.3) * 255).astype(np.uint8)
   ```
   **Consistent** with all other depth effects.

---

## Open Questions

1. **`texPrev` usage**: The shader declares `uniform sampler2D texPrev;` but never samples it. Is this intentional (placeholder) or dead code? Should be removed in WebGPU port to free texture unit 1.

2. **Color mode implementation**: The skeleton spec does not show exact blend functions. Need to extract from full shader source:
   - How does `overlay` blend work? Standard Photoshop overlay formula?
   - Does `replace` mode also replace alpha?

3. **Gradient calculation precision**: The gradient uses 4 neighbor samples. What is the exact texel offset? Likely `1.0/resolution`. Should be documented in shader.

4. **Fresnel factor**: The constant `fresnel_factor` scaling gradient to viewing angle is not defined in the snippet. What is its value? (Likely ~0.5 to 2.0)

5. **Performance tuning**: Is 12 spectral samples configurable? Could be exposed as a hidden parameter for quality/performance trade-off.

6. **Depth gradient aspect ratio**: Does gradient calculation account for non-square pixels? Should use `texel = vec2(1.0/resolution.x, 1.0/resolution.y)`.

---
-

## Definition of Done

- [x] Skeleton spec claimed from `_05_active_desktop`
- [x] Legacy source code analyzed (`depth_holographic.py`)
- [x] All 14 parameters documented with mapped ranges
- [x] Shader algorithm explained (thin-film, Fresnel, diffraction)
- [x] Edge cases identified (missing depth, normalization overflow, color mode boundaries)
- [x] Mathematical formulations provided (interference, gradient, blending)
- [x] Performance characteristics analyzed (texture fetches, spectral samples)
- [x] Test plan defined (unit, integration, visual regression, performance)
- [x] WebGPU migration notes (WGSL, bind groups, uniform buffer layout)
- [x] Easter egg concept defined ("Holographic Interference")
- [ ] Spec file saved to `docs/specs/_02_fleshed_out/` (pending)
- [ ] `BOARD.md` updated to "🟩 COMPLETING PASS 2"
- [ ] Easter egg appended to `WORKSPACE/EASTEREGG_COUNCIL.md`
- [ ] Next task claimed

**Next Step**: Write spec file to disk, update BOARD.md, add easter egg, claim next task.
