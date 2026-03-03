# ColoramaEffect — Advanced Color Cycling and Shifting

**Task ID:** P3-EXT030  
**Module:** `ColoramaEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`ColoramaEffect`](docs/specs/_02_fleshed_out/P3-EXT030_ColoramaEffect.md:100) class implements an advanced color cycling and shifting effect that manipulates hue, saturation, and brightness based on complex mathematical relationships. It belongs to the `color` effect category and provides sophisticated control over how colors evolve over time, making it ideal for psychedelic visuals, animated color transitions, and creative color grading.

**What This Module Does**

- Shifts hue based on brightness and saturation levels (luma-driven hue shift)
- Animates hue cycling with configurable speed and direction
- Applies vibrance to selectively boost unsaturated colors
- Adjusts temperature (warm/cool) and tint (green/magenta) for white balance
- Provides contrast, brightness, and saturation controls
- Offers four preset configurations for common visual styles
- Uses HSV color space for intuitive color manipulation

**What This Module Does NOT Do**

- Does not include pattern distortion effects (those are in separate classes)
- Does not support per-channel color curves or LUTs
- Does not handle HDR color spaces (operates in standard 8-bit RGB)
- Does not include edge wrapping or mirroring (samples outside viewport return black)
- Does not provide chromatic aberration correction (only artistic distortion)

---

## Detailed Behavior and Parameter Interactions

### Parameter Space and UI Mapping

All user-facing parameters use a normalized `0.0` to `10.0` range from UI sliders. The shader internally remaps these to appropriate mathematical ranges:

| Parameter | UI Range | Internal Range | Purpose |
|-----------|----------|----------------|---------|
| `amount` | 0.0-10.0 | 0.0-1.0 | Hue cycling strength |
| `hue_shift` | 0.0-10.0 | 0.0-1.0 | Static hue offset |
| `saturation` | 0.0-10.0 | 0.0-2.0 | Saturation multiplier |
| `brightness` | 0.0-10.0 | 0.0-2.0 | Brightness multiplier |
| `contrast` | 0.0-10.0 | 0.0-2.0 | Contrast multiplier |
| `invert` | 0.0-10.0 | 0.0-1.0 | Inversion strength |
| `cycle_speed` | 0.0-10.0 | 0.0-3.0 | Animated hue cycling rate |
| `luma_drive` | 0.0-10.0 | 0.0-2.0 | How much luma affects hue shift |
| `temperature` | 0.0-10.0 | -0.15 to +0.15 | Warm/cool tint |
| `vibrance` | 0.0-10.0 | 0.0-2.0 | Selective saturation boost |

### Core Algorithm: HSV-Based Color Manipulation

The effect operates in HSV (Hue, Saturation, Value) color space for intuitive color manipulation:

```glsl
vec3 hsv = rgb2hsv(input_color.rgb);
```

#### Luma-Driven Hue Shift

The most distinctive feature is the luma-driven hue shift, where brighter pixels shift hue more than darker pixels:

```glsl
// Luma-driven hue shift: brighter pixels shift more
float luma_shift = hsv.z * ld;  // ld = luma_drive / 10.0 * 2.0
```

This creates a natural-looking color shift where highlights move through the color spectrum more dramatically than shadows, producing a "colorama" effect that feels organic rather than mechanical.

#### Animated Hue Cycling

The effect includes time-based hue cycling that can be animated:

```glsl
// Animated cycle
float anim_shift = time * cspd;  // cspd = cycle_speed / 10.0 * 3.0
```

The total hue shift combines static offset, luma-driven shift, and animated shift:

```glsl
hsv.x = fract(hsv.x + a * (hsv.z + hsv.y) + hs + luma_shift + anim_shift);
```

Where:
- `a` = amount (hue cycling strength)
- `hsv.z` = value (brightness) — brighter pixels shift more
- `hsv.y` = saturation — more saturated pixels shift more
- `hs` = hue_shift (static offset)
- `luma_shift` = brightness-dependent shift
- `anim_shift` = time-based animation

#### Vibrance

The effect includes a vibrance algorithm that boosts unsaturated colors more than already-saturated ones:

```glsl
// Vibrance: boost low-saturation pixels more than already-saturated ones
float vib_boost = (1.0 - hsv.y) * (vib - 1.0);  // vib = vibrance / 10.0 * 2.0
hsv.y = clamp(hsv.y + vib_boost * 0.3, 0.0, 1.0);
```

This preserves the natural look of already-saturated colors while bringing life to dull areas.

#### Temperature and Tint

The effect applies temperature (warm/cool) and tint (green/magenta) adjustments:

```glsl
// Temperature: shift red/blue balance
temp = (temperature / 10.0 - 0.5) * 0.3;  // -0.15 to 0.15
result.r += temp;
result.b -= temp;
result.g += temp * 0.1;

// Tint: green/magenta axis
t = (tint / 10.0 - 0.5) * 0.4;  // -0.2 to 0.2
result.g += t;
result.r -= t * 0.3;
result.b -= t * 0.3;
```

#### Contrast and Brightness

Standard contrast and brightness adjustments are applied in HSV space:

```glsl
// Contrast
result = (result - 0.5) * con + 0.5;  // con = contrast / 10.0 * 2.0

// Brightness
hsv.z = clamp(hsv.z * brt, 0.0, 1.0);  // brt = brightness / 10.0 * 2.0
```

#### Inversion

The effect includes a soft inversion that can be applied to all channels or selectively:

```glsl
// Invert
result = mix(result, 1.0 - result, inv);  // inv = invert / 10.0
```

### Preset Configurations

The class provides four preset parameter sets:

- **`acid_wash`**: `{amount: 8.0, cycle_speed: 4.0, luma_drive: 7.0, saturation: 8.0, vibrance: 9.0, contrast: 6.0, hue_shift: 0.0, brightness: 5.0, temperature: 5.0, invert: 0.0}` — intense color cycling with strong luma-driven shifts, creating a psychedelic acid wash effect.
- **`warm_glow`**: `{amount: 2.0, temperature: 8.0, vibrance: 6.0, brightness: 6.0, saturation: 6.0, contrast: 5.0, cycle_speed: 0.0, luma_drive: 2.0, hue_shift: 0.0, invert: 0.0}` — warm, glowing colors with moderate vibrance and no animation.
- **`cold_steel`**: `{amount: 1.0, temperature: 1.0, saturation: 3.0, contrast: 7.0, brightness: 4.0, vibrance: 2.0, cycle_speed: 0.0, luma_drive: 0.0, hue_shift: 5.5, invert: 0.0}` — cool, desaturated look with high contrast and a blue hue shift.
- **`psychedelic`**: `{amount: 10.0, cycle_speed: 6.0, luma_drive: 10.0, saturation: 10.0, vibrance: 10.0, contrast: 8.0, hue_shift: 3.0, brightness: 5.0, temperature: 5.0, invert: 0.0}` — maximum color cycling with strong luma-driven shifts and high vibrance for an intense psychedelic effect.

---

## Public Interface

### Class: `ColoramaEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT030_ColoramaEffect.md:100) (from `core.effects.shader_base`)

**Constructor:** `__init__(self)`

Initializes the effect with default parameters:

```python
self.parameters = {
    "amount": 5.0,
    "hue_shift": 0.0,
    "saturation": 5.0,
    "brightness": 5.0,
    "contrast": 5.0,
    "invert": 0.0,
    "cycle_speed": 0.0,
    "luma_drive": 3.0,
    "temperature": 5.0,
    "vibrance": 5.0,
}
```

**Properties:**

- `name = "colorama"` — Effect identifier
- `fragment_shader = COLORAMA_FRAGMENT` — GLSL fragment shader (see full listing in legacy reference)
- `effect_category = "filter"`
- `effect_tags = ["color", "hue", "animated", "psychedelic"]`
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
| `u_mix` | `float` | Blend factor between original and colorama result (0.0-1.0) |
| `time` | `float` | Shader time in seconds (for animated hue cycling) |
| `resolution` | `vec2` | Viewport resolution in pixels |
| `uv` | `vec2` | Normalized texture coordinates |

### Uniforms (from Parameters)

All parameters are passed as separate uniforms:

- `amount`, `hue_shift`, `saturation`, `brightness`, `contrast`, `invert`
- `cycle_speed`, `luma_drive`, `temperature`, `vibrance`

### Outputs

| Pin | Type | Description |
|-----|------|-------------|
| `fragColor` | `vec4` | RGBA output with colorama effect applied (alpha unchanged) |

---

## Edge Cases and Error Handling

### Edge Cases

1. **Zero amount**: `amount = 0.0` produces no hue cycling, but luma-driven shift and animated shift may still occur if `luma_drive > 0` or `cycle_speed > 0`.

2. **Zero saturation**: `saturation = 0.0` produces grayscale output. The luma-driven hue shift still occurs but has no visible effect on a grayscale image.

3. **Maximum vibrance**: `vibrance = 10.0` → `vib = 2.0`, so `vib_boost = (1.0 - hsv.y) * 1.0`. This can significantly boost unsaturated colors, potentially causing clipping.

4. **Temperature extremes**: `temperature = 0.0` → `temp = -0.15` (cool); `temperature = 10.0` → `temp = +0.15` (warm). Combined with high saturation, this can push channels outside [0,1] before clamping.

5. **Cycle speed**: `cycle_speed = 10.0` → `cspd = 3.0`, so hue rotates 3 full cycles per second. This can create very fast, potentially seizure-inducing animations.

6. **Luma drive**: `luma_drive = 10.0` → `ld = 2.0`, so bright pixels shift hue twice as much as dark pixels. This can create extreme color separation in high-contrast images.

7. **Mix parameter**: The final `fragColor = mix(input_color, colorama_color, u_mix)` allows blending. If `u_mix = 0`, output is original; if `u_mix = 1`, output is fully colorama.

8. **HSV conversion edge cases**: The `rgb2hsv()` and `hsv2rgb()` functions handle edge cases like pure black (0,0,0) and pure white (1,1,1) correctly, returning appropriate HSV values.

### Error Handling

- **No runtime errors** — all operations are safe GLSL; division by zero is avoided in HSV conversions.
- **Parameter clamping**: Python `set_parameter()` clamps all values to [0.0, 10.0], preventing invalid uniform uploads.
- **Color clamping**: Final `clamp(result, 0.0, 1.0)` prevents out-of-range values.

---

## Mathematical Formulations

### Parameter Remapping

For each parameter `p_ui` ∈ [0, 10]:

```
amount:         a = p_ui / 10.0                    ∈ [0.0, 1.0]
hue_shift:      hs = p_ui / 10.0                   ∈ [0.0, 1.0]
saturation:     sat = (p_ui / 10.0) * 2.0          ∈ [0.0, 2.0]
brightness:     brt = (p_ui / 10.0) * 2.0          ∈ [0.0, 2.0]
contrast:       con = (p_ui / 10.0) * 2.0          ∈ [0.0, 2.0]
invert:         inv = p_ui / 10.0                  ∈ [0.0, 1.0]
cycle_speed:    cspd = (p_ui / 10.0) * 3.0         ∈ [0.0, 3.0]
luma_drive:     ld = (p_ui / 10.0) * 2.0            ∈ [0.0, 2.0]
temperature:     temp = ((p_ui / 10.0) - 0.5) * 0.3 ∈ [-0.15, +0.15]
vibrance:       vib = (p_ui / 10.0) * 2.0          ∈ [0.0, 2.0]
```

### HSV Conversion Functions

The effect uses standard RGB↔HSV conversion:

```glsl
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
```

### Colorama Algorithm

Given input color `input_color`:

1. **Convert to HSV**: `hsv = rgb2hsv(input_color.rgb)`
2. **Compute luma-driven shift**: `luma_shift = hsv.z * ld`
3. **Compute animated shift**: `anim_shift = time * cspd`
4. **Compute total hue shift**:
   ```
   hue_total = hsv.x + a * (hsv.z + hsv.y) + hs + luma_shift + anim_shift
   hsv.x = fract(hue_total)  // wrap around [0,1]
   ```
5. **Apply saturation**:
   ```
   sat_mult = sat
   vib_boost = (1.0 - hsv.y) * (vib - 1.0)
   sat_mult += vib_boost * 0.3
   hsv.y = clamp(hsv.y * sat_mult, 0.0, 1.0)
   ```
6. **Apply brightness**: `hsv.z = clamp(hsv.z * brt, 0.0, 1.0)`
7. **Convert back to RGB**: `result = hsv2rgb(hsv)`
8. **Apply contrast**: `result = (result - 0.5) * con + 0.5`
9. **Apply temperature**:
   ```
   result.r += temp * 0.6
   result.b -= temp * 0.6
   result.g += temp * 0.1
   ```
10. **Apply tint**:
    ```
    result.g += t
    result.r -= t * 0.3
    result.b -= t * 0.3
    ```
11. **Clamp**: `result = clamp(result, 0.0, 1.0)`
12. **Apply inversion**: `result = mix(result, 1.0 - result, inv)`
13. **Mix with original**: `output = mix(input_color, vec4(result, input_color.a), u_mix)`

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: O(1) per pixel with HSV conversions (moderate cost) + arithmetic operations.
- **HSV conversions**: The `rgb2hsv()` and `hsv2rgb()` functions involve several `mix()`, `step()`, and `min()` operations — moderately expensive but acceptable for real-time.
- **No loops** in fragment shader — fully parallel.
- **No additional texture samples** beyond the single `texture(tex0, uv)` call.

### Memory Usage

- **Uniforms**: 10 floats.
- **No framebuffer allocations** beyond the standard `render_to_texture()` call.
- **Vertex shader**: Simple pass-through (inherited from base class).

### GPU Optimization Notes

- The HSV conversions are the most expensive part of this shader. Consider using a lookup texture for HSV↔RGB if performance becomes an issue.
- The effect is suitable for real-time 60fps at 1080p resolution, but may struggle at 4K without optimization.
- The `fract()` function in hue wrapping is efficient on modern GPUs.
- Consider splitting into separate effects if parameter groups are often used independently (e.g., a dedicated "hue shift" effect). But for primary color manipulation, having all in one pass is efficient (single texture fetch).

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python)

1. **Parameter remapping**: Verify all UI→internal conversions are correct (e.g., `amount=5.0` → `a=0.5`).
2. **Parameter clamping**: Test that `set_parameter("amount", -1.0)` clamps to 0.0, `set_parameter("amount", 11.0)` clamps to 10.0.
3. **Get/set symmetry**: For each parameter, verify `get_parameter(name)` returns the value set via `set_parameter(name, value)`.
4. **Preset values**: Verify each preset dictionary contains all 10 keys and values are within 0-10.
5. **Parameter groups**: Verify `_parameter_groups` dictionary structure covers all parameters without overlap.
6. **Chaos rating**: Verify `_chaos_rating` dictionary has all parameters and values in [0,1].
7. **Effect metadata**: Verify `effect_category == "filter"` and `effect_tags` contains expected strings.
8. **Neutral preset identity**: Render with `neutral` preset and verify output is within 1/255 of input.
9. **Amount effect**: Test `amount=0.0` vs `amount=10.0` produces expected hue cycling intensity.
10. **Luma drive effect**: Test `luma_drive=0.0` vs `luma_drive=10.0` produces expected luma-dependent hue shifts.
11. **Cycle speed**: Test `cycle_speed=0.0` vs `cycle_speed=10.0` produces expected animation speed.
12. **Vibrance effect**: Test `vibrance=0.0` vs `vibrance=10.0` produces expected selective saturation boost.
13. **Temperature effect**: Test `temperature=0.0` (cool) vs `temperature=10.0` (warm) produces expected color cast.
14. **Tint effect**: Test `tint=0.0` (green) vs `tint=10.0` (magenta) produces expected color cast.
15. **Saturation extremes**: Test `saturation=0.0` produces grayscale; `saturation=10.0` doubles saturation.
16. **Contrast extremes**: Test `contrast=0.0` flattens image; `contrast=10.0` increases contrast dramatically.
17. **Brightness extremes**: Test `brightness=0.0` darkens; `brightness=10.0` brightens.
18. **Inversion**: Test `invert=0.0` vs `invert=10.0` produces expected inversion strength.
19. **Mix blending**: Test `u_mix` values 0.0, 0.25, 0.5, 0.75, 1.0 produce correct linear interpolation.

### Integration Tests (Shader Rendering)

20. **Neutral render**: Render a test image with all parameters at 5.0 and verify no visible change.
21. **Hue cycling**: Render a grayscale gradient and verify hue cycling creates a rainbow effect.
22. **Luma-driven shift**: Render a high-contrast image and verify highlights shift hue more than shadows.
23. **Animated cycling**: Render with `cycle_speed=5.0` and verify smooth hue animation over time.
24. **Vibrance**: Render a desaturated image and verify vibrance brings life to dull areas without oversaturating already-vivid colors.
25. **Temperature**: Render a neutral gray image and verify warm/cool color cast.
26. **Tint**: Render a neutral gray image and verify green/magenta cast.
27. **Saturation**: Render a colorful image and verify saturation changes without altering hue/luma relationships.
28. **Contrast**: Render a low-contrast image and verify contrast stretching.
29. **Brightness**: Render a dark image and verify brightness lifting.
30. **Inversion**: Render a colorful image and verify inversion strength.
31. **Preset rendering**: Render with each preset and verify visual character matches the preset name (e.g., `acid_wash` should look psychedelic, `warm_glow` should look warm).

### Performance Tests

32. **Benchmark 1080p**: Measure frame time; should be well under 16ms for 60fps (likely < 4ms).
33. **HSV conversion cost**: Use GPU profiling to verify HSV conversions are the main cost.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT030: ColoramaEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementation:

- [`core/effects/color.py`](home/happy/Desktop/claude projects/VJlive-2/core/effects/color.py:1) (VJlive Original) — Full implementation of `ColoramaEffect` with shader code spanning lines 14-97 and class definition at lines 100-136.

The legacy code validates the parameter ranges, default values, preset configurations, and mathematical formulations described in this spec. The shader uses HSV color space for intuitive color manipulation and includes the distinctive luma-driven hue shift feature.

---

## Open Questions / [NEEDS RESEARCH]

- **Should we expose the HSV conversion as a separate utility?** The `rgb2hsv()` and `hsv2rgb()` functions are used by multiple effects. [NEEDS RESEARCH]
- **Should we add a "hue lock" parameter?** Some users may want to preserve certain hues while shifting others. [NEEDS RESEARCH]
- **Should we support different color spaces?** The current shader assumes sRGB. Should we support linear or other color spaces? [NEEDS RESEARCH]
- **Should we add a "color temperature" parameter?** The current temperature is a simple red/blue shift. Should we implement proper color temperature in Kelvin? [NEEDS RESEARCH]
- **Should we add a "color grading" mode?** The current effect is more of a creative tool. Should we add a professional color grading mode with curves and wheels? [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*