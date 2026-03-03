# ColorCorrectEffect — Comprehensive Color Grading and Correction

**Task ID:** P3-EXT029  
**Module:** `ColorCorrectEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`ColorCorrectEffect`](docs/specs/_02_fleshed_out/P3-EXT029_ColorCorrectEffect.md:1037) class implements a professional-grade, all-in-one color correction tool that combines the most essential color grading parameters into a single, unified effect. It provides fine control over exposure, contrast, saturation, white balance, and tone mapping, making it suitable for both primary color correction and creative color grading workflows.

**What This Module Does**

- Adjusts gamma, brightness, and contrast in a linear pipeline
- Controls saturation with a simple gray-mix approach
- Applies temperature (warm/cool) and tint (green/magenta) adjustments for white balance
- Lifts shadows and compresses highlights for HDR tone mapping
- Uses a single-pass shader with all operations chained together
- Provides five preset configurations for common looks

**What This Module Does NOT Do**

- Does not include advanced color wheels or HSL secondary adjustments
- Does not support LUTs (lookup tables) or film emulation
- Does not have per-channel curves (only global gamma)
- Does not include noise reduction or detail preservation
- Does not support 3D LUTs or ACES color science

---

## Detailed Behavior and Parameter Interactions

### Parameter Space and UI Mapping

All user-facing parameters use a normalized `0.0` to `10.0` range from UI sliders. The shader internally remaps these to appropriate mathematical ranges:

| Parameter | UI Range | Internal Range | Purpose |
|-----------|----------|----------------|---------|
| `gamma` | 0.0-10.0 | 0.4-2.5 | Power curve for midtones (5.0 → 1.0) |
| `brightness` | 0.0-10.0 | -0.5 to +0.5 | Additive brightness offset |
| `contrast` | 0.0-10.0 | 0.5-2.0 | Multiplicative contrast around 0.5 |
| `saturation` | 0.0-10.0 | 0.0-2.0 | Gray-to-color mix (0=grayscale, 2=double sat) |
| `temperature` | 0.0-10.0 | -0.2 to +0.2 | Warm (red) / cool (blue) tint |
| `tint` | 0.0-10.0 | -0.2 to +0.2 | Green/magenta cast correction |
| `shadow_lift` | 0.0-10.0 | 0.0-0.3 | Raise black level (additive to shadows) |
| `highlight_comp` | 0.0-10.0 | 0.0-1.0 | Soft rolloff for blown highlights |

### Processing Pipeline

The shader applies operations in a specific order to ensure mathematically correct results:

1. **Gamma correction** (linear light adjustment)
2. **Brightness** (additive offset)
3. **Contrast** (scale around midpoint 0.5)
4. **Saturation** (mix with luminance)
5. **Temperature** (red/blue shift)
6. **Tint** (green/magenta shift)
7. **Shadow lift** (remap black point)
8. **Highlight compression** (soft rolloff)

This order follows standard color grading practice: first correct the transfer function (gamma), then adjust exposure (brightness), then modify contrast, then work on color saturation and balance, finally fine-tune the tonal range with lift and compression.

### Parameter Details

#### Gamma (`gamma`)

Remapped: `g = 0.4 + gamma / 10.0 * 2.1` → range [0.4, 2.5]

Applied as: `c = pow(input_color.rgb, vec3(g))`

- Values < 1.0 (e.g., 0.4) brighten midtones and lift shadows (low contrast)
- Values > 1.0 (e.g., 2.5) darken midtones and deepen shadows (high contrast)
- Default 4.5 → g ≈ 1.0 (no change)

#### Brightness (`brightness`)

Remapped: `b = (brightness / 10.0 - 0.5)` → range [-0.5, +0.5]

Applied as: `c += b` (additive after gamma)

- Negative values darken the entire image
- Positive values brighten the entire image
- Operates in linear space after gamma decode

#### Contrast (`contrast`)

Remapped: `con = 0.5 + contrast / 10.0 * 1.5` → range [0.5, 2.0]

Applied as: `c = (c - 0.5) * con + 0.5` (scale around midpoint 0.5)

- `con = 1.0` is neutral (no change)
- `con < 1.0` reduces contrast (flatter)
- `con > 1.0` increases contrast (punchier)

#### Saturation (`saturation`)

Remapped: `sat = saturation / 10.0 * 2.0` → range [0.0, 2.0]

Compute luma: `gray = dot(c, vec3(0.299, 0.587, 0.114))`

Applied as: `c = mix(vec3(gray), c, sat)`

- `sat = 0.0` → full grayscale
- `sat = 1.0` → original saturation (neutral)
- `sat > 1.0` → boosted saturation
- `sat < 1.0` → desaturated

#### Temperature (`temperature`)

Remapped: `temp = (temperature / 10.0 - 0.5) * 0.4` → range [-0.2, +0.2]

Applied as:
```
c.r += temp * 0.6;   // red channel gets 60% of shift
c.b -= temp * 0.6;   // blue channel gets -60% (opposite)
c.g += temp * 0.1;   // green gets slight adjustment for smoothness
```

- `temperature < 5.0` (negative temp) → cooler (more blue, less red)
- `temperature > 5.0` (positive temp) → warmer (more red, less blue)
- Default 5.0 → neutral (no change)

#### Tint (`tint`)

Remapped: `t = (tint / 10.0 - 0.5) * 0.4` → range [-0.2, +0.2]

Applied as:
```
c.g += t;           // green channel
c.r -= t * 0.3;     // red channel (opposite, reduced)
c.b -= t * 0.3;     // blue channel (opposite, reduced)
```

- `tint < 5.0` (negative) → magenta cast (reduce green)
- `tint > 5.0` (positive) → green cast (increase green)
- Used for correcting fluorescent lighting or adding creative color casts

#### Shadow Lift (`shadow_lift`)

Remapped: `sl = shadow_lift / 10.0 * 0.3` → range [0.0, 0.3]

Applied as: `c = mix(vec3(sl), vec3(1.0), c)`

This remaps the entire tonal range: black (0) becomes `sl`, white (1) stays 1.0. It's a linear lift of the black point.

- `shadow_lift = 0.0` → no change
- `shadow_lift > 0.0` → raises shadows, making dark areas brighter
- Can create a "washed out" look if overused

#### Highlight Compression (`highlight_comp`)

Remapped: `hc = highlight_comp / 10.0` → range [0.0, 1.0]

Applied as (when `hc > 0.01`):
```
c = mix(c, 1.0 - exp(-c * (2.0 + hc * 3.0)), hc);
```

This is a soft rolloff (similar to Reinhard tone mapping) that gently compresses bright values before they clip to white.

- `highlight_comp = 0.0` → no compression (hard clip at 1.0)
- `highlight_comp > 0.0` → smooths out highlights, preserving detail in bright areas
- The factor `(2.0 + hc * 3.0)` controls the steepness of the rolloff

### Preset Configurations

The class provides five preset parameter sets:

- **`neutral`**: All parameters at default (gamma=4.5, brightness=5.0, contrast=5.5, saturation=5.5, temperature=5.0, tint=5.0, shadow_lift=0.0, highlight_comp=0.0) — no correction applied.
- **`warm_film`**: Slightly warmer (temperature=6.5), increased contrast (5.5) and saturation (5.5), moderate shadow lift (2.0) and highlight compression (4.0) — mimics warm film stock.
- **`cool_cinema`**: Cooler (temperature=3.5), higher contrast (6.0), lower saturation (4.5), moderate shadow lift (1.0) and highlight compression (5.0) — cinematic cool look.
- **`crushed_look`**: Higher gamma (6.0), lower brightness (4.5), high contrast (7.0), low saturation (4.0), moderate shadow lift (3.0) — high-contrast, desaturated "crush" aesthetic.
- **`vivid_pop`**: Lower gamma (4.0), higher brightness (5.5), high contrast (6.0), high saturation (7.0), slight warm (temperature=5.5), moderate highlight compression (2.0) — vibrant, punchy look for pop videos.

---

## Public Interface

### Class: `ColorCorrectEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT029_ColorCorrectEffect.md:1037) (from `core.effects.shader_base`)

**Constructor:** `__init__(self)`

Initializes the effect with default parameters (neutral preset):

```python
self.parameters = {
    "gamma": 4.5,
    "brightness": 5.0,
    "contrast": 5.5,
    "saturation": 5.5,
    "temperature": 5.0,
    "tint": 5.0,
    "shadow_lift": 0.0,
    "highlight_comp": 0.0,
}
```

**Properties:**

- `name = "color_correct"` — Effect identifier
- `fragment_shader = COLOR_CORRECT_FRAGMENT` — GLSL shader code (see full listing in legacy reference)
- `effect_category = "filter"`
- `effect_tags = ["color", "correction", "grading", "professional"]`
- `_parameter_groups = {...}` — Logical grouping of parameters
- `_chaos_rating = {...}` — Chaos potential per parameter (0.0-1.0)

**Methods:**

- `set_parameter(name: str, value: float)`: Set a parameter in the 0-10 UI range. All parameters are clamped to [0.0, 10.0].
- `get_parameter(name: str) -> float`: Retrieve parameter value in 0-10 UI range.
- `render(texture: int, extra_textures: list = None) -> int`: Render the effect to a framebuffer and return the output texture ID.

**Class Attributes:**

- `PRESETS = {...}` — Dictionary of preset parameter configurations (see above).

---

## Inputs and Outputs

### Inputs

| Pin | Type | Description |
|-----|------|-------------|
| `tex0` | `sampler2D` | Input video texture |
| `u_mix` | `float` | Blend factor between original and corrected result (0.0-1.0) |
| `time` | `float` | Shader time in seconds (unused but required by base class) |
| `resolution` | `vec2` | Viewport resolution in pixels |

### Uniforms (from Parameters)

All eight parameters are passed as separate uniforms:

- `gamma`, `brightness`, `contrast`, `saturation`
- `temperature`, `tint`, `shadow_lift`, `highlight_comp`

### Outputs

| Pin | Type | Description |
|-----|------|-------------|
| `fragColor` | `vec4` | RGBA output with corrected colors (alpha unchanged) |

---

## Edge Cases and Error Handling

### Edge Cases

1. **All parameters at neutral (5.0)**: The shader should produce output nearly identical to input. Small differences may occur due to floating-point rounding in the highlight compression formula even when `highlight_comp=0`.

2. **Extreme gamma values**: `gamma=0.0` → g=0.4 (mild brightening); `gamma=10.0` → g=2.5 (strong darkening). Values outside [0.4, 2.5] are prevented by clamping.

3. **Brightness overflow**: `brightness=10.0` → b=+0.5 additive. Combined with high contrast and low gamma, this can push many pixels > 1.0 before clamping. The highlight compression can mitigate this if enabled.

4. **Contrast at extremes**: `contrast=0.0` → con=0.5 (actually reduces contrast by 50%); `contrast=10.0` → con=2.0 (doubles contrast). The midpoint is always 0.5, so high contrast can clip both shadows and highlights.

5. **Saturation zero**: `saturation=0.0` produces grayscale output. The luma calculation uses Rec. 709 coefficients (0.299, 0.587, 0.114).

6. **Temperature and tint combined**: These are additive in the sense they both modify RGB channels. Extreme values in both can cause channel clipping (e.g., very warm + very green). The final `clamp(c, 0.0, 1.0)` prevents out-of-range values.

7. **Shadow lift at maximum**: `shadow_lift=10.0` → sl=0.3. The `mix(vec3(sl), vec3(1.0), c)` remaps black (0) to 0.3, effectively raising the black level to 30% gray. This can make the image look flat if overused.

8. **Highlight compression at maximum**: `highlight_comp=10.0` → hc=1.0, rolloff factor = `2.0 + 1.0*3.0 = 5.0`. The formula `1.0 - exp(-c * 5.0)` is very aggressive and will compress even moderate highlights. Useful for HDR sources.

9. **Mix parameter**: The final `fragColor = mix(input_color, corrected, u_mix)` allows blending. If `u_mix=0`, output is original; if `u_mix=1`, output is fully corrected.

### Error Handling

- **No runtime errors** — all operations are safe GLSL; division by zero is avoided (e.g., in highlight compression, `c` is never negative due to prior clamping).
- **Parameter clamping**: Python `set_parameter()` clamps all values to [0.0, 10.0], preventing invalid uniform uploads.
- **No NaN propagation**: All math operations are well-conditioned; `pow()` with non-negative base is safe.

---

## Mathematical Formulations

### Parameter Remapping

For each parameter `p_ui` ∈ [0, 10]:

```
gamma:          g = 0.4 + (p_ui / 10.0) * 2.1          ∈ [0.4, 2.5]
brightness:     b = (p_ui / 10.0) - 0.5                ∈ [-0.5, +0.5]
contrast:       con = 0.5 + (p_ui / 10.0) * 1.5        ∈ [0.5, 2.0]
saturation:     sat = (p_ui / 10.0) * 2.0              ∈ [0.0, 2.0]
temperature:    temp = ((p_ui / 10.0) - 0.5) * 0.4    ∈ [-0.2, +0.2]
tint:           t = ((p_ui / 10.0) - 0.5) * 0.4       ∈ [-0.2, +0.2]
shadow_lift:    sl = (p_ui / 10.0) * 0.3              ∈ [0.0, 0.3]
highlight_comp: hc = p_ui / 10.0                      ∈ [0.0, 1.0]
```

### Processing Chain

Let `c` = input RGB (after texture sample).

1. **Gamma**: `c ← c^g`
2. **Brightness**: `c ← c + b`
3. **Contrast**: `c ← (c - 0.5) * con + 0.5`
4. **Saturation**: 
   ```
   gray = 0.299*c.r + 0.587*c.g + 0.114*c.b
   c ← mix(gray, c, sat)
   ```
5. **Temperature**:
   ```
   c.r ← c.r + 0.6*temp
   c.b ← c.b - 0.6*temp
   c.g ← c.g + 0.1*temp
   ```
6. **Tint**:
   ```
   c.g ← c.g + t
   c.r ← c.r - 0.3*t
   c.b ← c.b - 0.3*t
   ```
7. **Shadow lift**:
   ```
   c ← mix(vec3(sl), vec3(1.0), c)
   ```
8. **Highlight compression** (if `hc > 0.01`):
   ```
   c ← mix(c, 1.0 - exp(-c * (2.0 + hc*3.0)), hc)
   ```
9. **Clamp**: `c ← clamp(c, 0.0, 1.0)`
10. **Mix**: `output = mix(input_color, vec4(c, input_color.a), u_mix)`

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: O(1) per pixel with a sequence of arithmetic operations and one `pow()` for gamma.
- **No loops** in fragment shader — fully parallel.
- **No additional texture samples** beyond the single `texture(tex0, uv)` call.

### Memory Usage

- **Uniforms**: 8 floats.
- **No framebuffer allocations** beyond the standard `render_to_texture()` call.
- **Vertex shader**: Simple pass-through (inherited from base class).

### GPU Optimization Notes

- The shader is lightweight and suitable for real-time 60fps at 4K resolution.
- The `pow()` operation for gamma is the most expensive single instruction but is unavoidable.
- Highlight compression uses `exp()` which is moderately expensive; however, it's only executed when `hc > 0.01`, so disabling highlight compression eliminates it entirely.
- Consider splitting into separate effects if parameter groups are often used independently (e.g., a dedicated "lift/gain" effect). But for primary correction, having all in one pass is efficient (single texture fetch).

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python)

1. **Parameter remapping**: Verify all UI→internal conversions are correct (e.g., `gamma=5.0` → `g=1.0`).
2. **Parameter clamping**: Test that `set_parameter("gamma", -1.0)` clamps to 0.0, `set_parameter("gamma", 11.0)` clamps to 10.0.
3. **Get/set symmetry**: For each parameter, verify `get_parameter(name)` returns the value set via `set_parameter(name, value)`.
4. **Preset values**: Verify each preset dictionary contains all 8 keys and values are within 0-10.
5. **Parameter groups**: Verify `_parameter_groups` dictionary structure covers all parameters without overlap.
6. **Chaos rating**: Verify `_chaos_rating` dictionary has all parameters and values in [0,1].
7. **Effect metadata**: Verify `effect_category == "filter"` and `effect_tags` contains expected strings.
8. **Neutral preset identity**: Render with `neutral` preset and verify output is within 1/255 of input (accounting for floating-point rounding).
9. **Gamma direction**: Test `gamma=2.0` (darken) vs `gamma=0.5` (brighten) produce expected luma changes.
10. **Temperature sign**: Test `temperature=2.0` (warm) increases red, decreases blue; `temperature=8.0` (cool) does opposite.
11. **Tint sign**: Test `tint=2.0` (green) increases green, decreases red/blue; `tint=8.0` (magenta) does opposite.
12. **Shadow lift effect**: Test `shadow_lift=10.0` raises black point to ~0.3 gray.
13. **Highlight compression**: Test `highlight_comp=10.0` produces smooth rolloff on a gradient from 0.5 to 2.0.
14. **Saturation extremes**: Test `saturation=0.0` produces grayscale; `saturation=10.0` doubles saturation (may clip).
15. **Contrast extremes**: Test `contrast=0.0` flattens image; `contrast=10.0` increases contrast dramatically.

### Integration Tests (Shader Rendering)

16. **Neutral render**: Render a test image with all parameters at 5.0 and verify no visible change.
17. **Gamma curve**: Render a grayscale ramp and verify the output curve matches the gamma setting.
18. **Brightness offset**: Render a mid-gray image and verify additive brightness shifts as expected.
19. **Contrast S-curve**: Render a grayscale ramp and verify contrast stretches or compresses the curve.
20. **Saturation**: Render a colorful image and verify saturation changes without altering hue/luma relationships.
21. **Temperature**: Render a neutral gray image and verify color cast (warm vs cool).
22. **Tint**: Render a neutral gray image and verify green/magenta cast.
23. **Shadow lift**: Render a low-contrast image with deep shadows and verify shadows are raised.
24. **Highlight compression**: Render a high-contrast image with blown highlights and verify smooth rolloff.
25. **Combined presets**: Render with each preset and verify the visual character matches the preset name (e.g., `warm_film` should look warm, `cool_cinema` should look cool).
26. **Mix blending**: Test `u_mix` values 0.0, 0.25, 0.5, 0.75, 1.0 produce correct linear interpolation between input and corrected.

### Performance Tests

27. **Benchmark 1080p**: Measure frame time; should be well under 16ms for 60fps (likely < 2ms).
28. **No texture thrashing**: Verify only one texture sample per pixel.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT029: ColorCorrectEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementation:

- [`core/effects/color.py`](home/happy/Desktop/claude projects/VJlive-2/core/effects/color.py:1) (VJlive Original) — Full implementation of `ColorCorrectEffect` with shader code spanning lines 968-1034 and class definition at lines 1037-1073.

The legacy code validates the parameter ranges, default values, processing order, and mathematical formulations described in this spec. The shader is a single-pass implementation that chains all operations in the order: gamma → brightness → contrast → saturation → temperature → tint → shadow lift → highlight compression → clamp → mix.

---

## Open Questions / [NEEDS RESEARCH]

- **Should we expose the processing order as separate effects?** Some users may want to reorder operations (e.g., contrast before gamma). [NEEDS RESEARCH]
- **Per-channel gamma**: Professional color correctors often have separate RGB gains/offsets. Should we add channel-specific controls? [NEEDS RESEARCH]
- **Color space support**: The current shader assumes sRGB/gamma 2.0. Should we support linear vs. sRGB workflows explicitly? [NEEDS RESEARCH]
- **Curves**: Should we add a full tone curve (like a 1D LUT) for more creative control? [NEEDS RESEARCH]
- **Skin tone preservation**: Some color graders want to protect skin tones from saturation shifts. Could we add a skin tone protection mode? [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*