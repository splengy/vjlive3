# ContrastEffect — Advanced Contrast with S-Curve Shaping and Zone Control

**Task ID:** P3-EXT034  
**Module:** `ContrastEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`ContrastEffect`](docs/specs/_02_fleshed_out/P3-EXT034_ContrastEffect.md:315) class implements an advanced contrast adjustment with S-curve shaping, midpoint control, and separate shadow/highlight adjustments. It belongs to the `color` effect category and provides sophisticated control over tonal contrast beyond simple linear scaling.

**What This Module Does**

- Adjusts contrast with a configurable midpoint pivot
- Applies S-curve shaping for natural-looking contrast transitions
- Provides independent shadow lift and highlight push controls
- Uses luma-based masking to apply shadow/highlight adjustments selectively
- Offers four preset configurations for common contrast styles
- Uses a single-pass shader with all operations chained together

**What This Module Does NOT Do**

- Does not include color saturation or hue adjustments (those are separate effects)
- Does not support per-channel contrast (only luminance-based)
- Does not include HDR tone mapping (though highlight compression is available in ColorCorrectEffect)
- Does not support curves or custom transfer functions
- Does not include local contrast or detail enhancement

---

## Detailed Behavior and Parameter Interactions

### Parameter Space and UI Mapping

All user-facing parameters use a normalized `0.0` to `10.0` range from UI sliders. The shader internally remaps these to appropriate mathematical ranges:

| Parameter | UI Range | Internal Range | Purpose |
|-----------|----------|----------------|---------|
| `amount` | 0.0-10.0 | 0.0-4.0 | Contrast multiplier around midpoint |
| `midpoint` | 0.0-10.0 | 0.0-1.0 | Pivot point for contrast (0=black, 1=white) |
| `curve_shape` | 0.0-10.0 | 0.0-1.0 | 0=linear, 0.5=S-curve, 1.0=hard S |
| `shadows` | 0.0-10.0 | -0.5 to +0.5 | Lift or darken shadows |
| `highlights` | 0.0-10.0 | -0.5 to +0.5 | Push or dim highlights |

### Core Algorithm: Contrast with S-Curve and Zone Control

The effect applies contrast in three stages:

1. **Linear contrast scaling** around a configurable midpoint
2. **S-curve shaping** to smooth the transition at extremes
3. **Shadow/highlight adjustments** with luma-based masking

#### Stage 1: Linear Contrast

```glsl
float a = amount / 10.0 * 4.0;      // 0-4
float mid = midpoint / 10.0;        // 0-1
c = (c - mid) * a + mid;
```

This scales pixel values around `mid`. Values above `mid` get brighter (if `a>1`) or darker (if `a<1`); values below `mid` get darker or brighter respectively. The result can exceed [0,1] before clamping.

#### Stage 2: S-Curve Shaping

If `curve_shape > 0.01`, the shader blends the linearly contrasted result with a sigmoid curve:

```glsl
if (curve > 0.01) {
    vec3 sig = 1.0 / (1.0 + exp(-12.0 * (c - 0.5) * (0.5 + curve)));
    c = mix(c, sig, curve);
}
```

The sigmoid function `1/(1+exp(-12*(c-0.5)*(0.5+curve)))` creates a smooth S-shaped curve that compresses extremes. The factor `(0.5+curve)` controls the steepness. This is useful for creating more natural-looking contrast that avoids harsh clipping.

#### Stage 3: Shadow/Highlight Adjustments

These are applied **after** contrast and S-curve, using luma-based masks:

```glsl
float luma = dot(c, vec3(0.299, 0.587, 0.114));

// Shadows lift: add to dark areas only
float shadow_mask = 1.0 - smoothstep(0.0, 0.4, luma);
c += sh * shadow_mask;  // sh = (shadows / 10.0 - 0.5) ∈ [-0.5, +0.5]

// Highlights push: add to bright areas only
float hi_mask = smoothstep(0.6, 1.0, luma);
c += hi * hi_mask;  // hi = (highlights / 10.0 - 0.5) ∈ [-0.5, +0.5]
```

- **Shadow mask**: Pixels with luma < 0.4 get full effect; luma > 0.4 get zero effect (smooth transition).
- **Highlight mask**: Pixels with luma > 0.6 get full effect; luma < 0.6 get zero effect.

This allows independent control over dark and bright regions without affecting midtones.

### Preset Configurations

The class provides four preset parameter sets:

- **`subtle_punch`**: `{amount: 5.5, midpoint: 5.0, curve_shape: 3.0, shadows: 5.0, highlights: 5.0}` — gentle contrast boost with mild S-curve and balanced shadow/highlight adjustments.
- **`crushed_blacks`**: `{amount: 7.0, midpoint: 4.0, curve_shape: 6.0, shadows: 2.0, highlights: 6.0}` — higher contrast with midpoint shifted toward shadows (crushed blacks) and stronger highlight push.
- **`hdr_tone`**: `{amount: 3.0, midpoint: 5.0, curve_shape: 7.0, shadows: 7.0, highlights: 3.0}` — moderate contrast with strong S-curve, lifted shadows, and reduced highlights for an HDR-like look.
- **`hard_clip`**: `{amount: 10.0, midpoint: 5.0, curve_shape: 10.0, shadows: 5.0, highlights: 5.0}` — maximum contrast with hard S-curve (no blending), creating a stark, high-contrast look.

---

## Public Interface

### Class: `ContrastEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT034_ContrastEffect.md:315) (from `core.effects.shader_base`)

**Constructor:** `__init__(self)`

Initializes the effect with default parameters:

```python
self.parameters = {
    "amount": 4.0,
    "midpoint": 5.0,
    "curve_shape": 0.0,
    "shadows": 5.0,
    "highlights": 5.0,
}
```

**Properties:**

- `name = "contrast"` — Effect identifier
- `fragment_shader = CONTRAST_FRAGMENT` — GLSL fragment shader (see full listing in legacy reference)
- `effect_category = "filter"`
- `effect_tags = ["color", "tone", "contrast", "correction"]`
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
| `u_mix` | `float` | Blend factor between original and contrasted result (0.0-1.0) |
| `time` | `float` | Shader time in seconds (unused but required by base class) |
| `resolution` | `vec2` | Viewport resolution in pixels |
| `uv` | `vec2` | Normalized texture coordinates |

### Uniforms (from Parameters)

All five parameters are passed as separate uniforms:

- `amount`, `midpoint`, `curve_shape`, `shadows`, `highlights`

### Outputs

| Pin | Type | Description |
|-----|------|-------------|
| `fragColor` | `vec4` | RGBA output with contrast applied (alpha unchanged) |

---

## Edge Cases and Error Handling

### Edge Cases

1. **Zero amount**: `amount = 0.0` → `a = 0.0`, so `c = (c - mid) * 0 + mid = mid` for all pixels. This collapses the image to the midpoint value (0.5 if `midpoint=5.0`). This is an extreme case, not neutral.

2. **Neutral contrast**: `amount = 5.0` → `a = 2.0`? Wait, let's recalc: `a = 5.0/10.0*4.0 = 2.0`. That's not neutral. Actually, neutral would be `a=1.0` which occurs at `amount = 2.5`. The default `amount=4.0` gives `a=1.6`, which is a moderate contrast boost. The presets use various amounts.

3. **Midpoint extremes**: `midpoint=0.0` → `mid=0.0` (pivot at black); `midpoint=10.0` → `mid=1.0` (pivot at white). These create asymmetric contrast that only affects one side of the tonal range.

4. **S-curve at maximum**: `curve_shape=10.0` → `curve=1.0`, so the sigmoid blend factor is 1.0, fully replacing linear contrast with the S-curve. The sigmoid `1/(1+exp(-12*(c-0.5)*1.5))` is very steep and creates a hard clip-like effect.

5. **Shadows/highlights at extremes**: Both `shadows` and `highlights` map to `[-0.5, +0.5]`. Positive values add brightness to the masked region; negative values subtract. Maximum positive (`10.0`) adds +0.5, which can easily clip to 1.0. Maximum negative (`0.0`) subtracts -0.5, which can clip to 0.0.

6. **Shadow/highlight masks overlap**: The shadow mask covers luma < 0.4, highlight mask covers luma > 0.6. There's a gap (0.4-0.6) where neither mask applies, protecting midtones. This is intentional.

7. **Mix parameter**: The final `fragColor = mix(input_color, contrast_color, u_mix)` allows blending. If `u_mix=0`, output is original; if `u_mix=1`, output is fully contrasted.

### Error Handling

- **No runtime errors** — all operations are safe GLSL; `exp()` is well-behaved for the range of inputs (c ∈ [0,1] after clamping).
- **Parameter clamping**: Python `set_parameter()` clamps all values to [0.0, 10.0], preventing invalid uniform uploads.
- **No NaN propagation**: All math operations are well-conditioned.

---

## Mathematical Formulations

### Parameter Remapping

For each parameter `p_ui` ∈ [0, 10]:

```
amount:       a = (p_ui / 10.0) * 4.0          ∈ [0.0, 4.0]
midpoint:     mid = p_ui / 10.0                 ∈ [0.0, 1.0]
curve_shape:  curve = p_ui / 10.0               ∈ [0.0, 1.0]
shadows:      sh = (p_ui / 10.0) - 0.5          ∈ [-0.5, +0.5]
highlights:   hi = (p_ui / 10.0) - 0.5          ∈ [-0.5, +0.5]
```

### Contrast Pipeline

Given input color `c` (RGB vector):

1. **Linear contrast**:
   ```
   c ← (c - mid) * a + mid
   ```

2. **S-curve blending** (if `curve > 0.01`):
   ```
   sig = 1.0 / (1.0 + exp(-12.0 * (c - 0.5) * (0.5 + curve)))
   c ← mix(c, sig, curve)
   ```

3. **Shadow lift**:
   ```
   luma = 0.299*c.r + 0.587*c.g + 0.114*c.b
   shadow_mask = 1.0 - smoothstep(0.0, 0.4, luma)
   c ← c + sh * shadow_mask
   ```

4. **Highlight push**:
   ```
   highlight_mask = smoothstep(0.6, 1.0, luma)
   c ← c + hi * highlight_mask
   ```

5. **Clamp**: `c ← clamp(c, 0.0, 1.0)`

6. **Mix**: `output = mix(input_color, vec4(c, input_color.a), u_mix)`

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: O(1) per pixel with arithmetic operations, one `dot()` for luma, one `exp()` for S-curve (when enabled), and two `smoothstep()` calls.
- **No loops** in fragment shader — fully parallel.
- **No additional texture samples** beyond the single `texture(tex0, uv)` call.

### Memory Usage

- **Uniforms**: 5 floats.
- **No framebuffer allocations** beyond the standard `render_to_texture()` call.
- **Vertex shader**: Simple pass-through (inherited from base class).

### GPU Optimization Notes

- The `exp()` function in the S-curve is the most expensive operation, but it's only executed when `curve_shape > 0.01`. Disabling S-curve eliminates it.
- The `smoothstep()` calls for shadow/highlight masks are cheap (polynomial approximations).
- The effect is very lightweight and suitable for real-time 60fps at 4K resolution.
- Consider splitting shadow/highlight into separate effects if they are often used independently. But for primary contrast adjustment, having all in one pass is efficient.

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python)

1. **Parameter remapping**: Verify all UI→internal conversions are correct (e.g., `amount=5.0` → `a=2.0`).
2. **Parameter clamping**: Test that `set_parameter("amount", -1.0)` clamps to 0.0, `set_parameter("amount", 11.0)` clamps to 10.0.
3. **Get/set symmetry**: For each parameter, verify `get_parameter(name)` returns the value set via `set_parameter(name, value)`.
4. **Preset values**: Verify each preset dictionary contains all 5 keys and values are within 0-10.
5. **Parameter groups**: Verify `_parameter_groups` dictionary structure covers all parameters without overlap.
6. **Chaos rating**: Verify `_chaos_rating` dictionary has all parameters and values in [0,1].
7. **Effect metadata**: Verify `effect_category == "filter"` and `effect_tags` contains expected strings.
8. **Neutral contrast**: Test `amount=2.5` (a=1.0) with `midpoint=5.0`, `curve=0`, `shadows=5.0`, `highlights=5.0` should produce near-original (shadows/highlights at 0 offset).
9. **Amount extremes**: Test `amount=0.0` collapses to midpoint; `amount=10.0` (a=4.0) creates extreme contrast.
10. **Midpoint effect**: Test `midpoint=0.0` (pivot at black) vs `midpoint=10.0` (pivot at white) produces asymmetric contrast.
11. **S-curve blending**: Test `curve_shape=0.0` (linear) vs `curve_shape=10.0` (full S) produces different tonal response.
12. **Shadows positive/negative**: Test `shadows=10.0` lifts shadows (+0.5); `shadows=0.0` darkens shadows (-0.5).
13. **Highlights positive/negative**: Test `highlights=10.0` pushes highlights (+0.5); `highlights=0.0` dims highlights (-0.5).
14. **Shadow mask coverage**: Verify shadow mask affects luma < 0.4, not luma > 0.6.
15. **Highlight mask coverage**: Verify highlight mask affects luma > 0.6, not luma < 0.4.
16. **Mix blending**: Test `u_mix` values 0.0, 0.25, 0.5, 0.75, 1.0 produce correct linear interpolation.

### Integration Tests (Shader Rendering)

17. **Neutral render**: Render with `amount=2.5`, `midpoint=5.0`, `curve=0`, `shadows=5.0`, `highlights=5.0` and verify output ≈ input.
18. **Contrast ramp**: Render a grayscale ramp and verify `amount` stretches or compresses the curve.
19. **Midpoint pivot**: Render a grayscale ramp and verify changing `midpoint` shifts the pivot point of the contrast curve.
20. **S-curve shaping**: Render a grayscale ramp and verify `curve_shape` smooths the contrast curve, preventing hard clipping.
21. **Shadow lift**: Render a low-contrast image with deep shadows and verify `shadows > 5.0` raises shadow detail.
22. **Highlight push**: Render a high-contrast image with bright highlights and verify `highlights > 5.0` brightens highlights further.
23. **Shadow/highlight separation**: Verify that adjusting shadows does not affect highlights (and vice versa) in the midtone gap.
24. **Preset rendering**: Render with each preset and verify visual character matches the preset name (e.g., `crushed_blacks` should have crushed shadows, `hdr_tone` should look HDR-like).
25. **Extreme values**: Render with `amount=10.0`, `curve=10.0`, `shadows=10.0`, `highlights=10.0` and verify no crashes, though clipping will occur.

### Performance Tests

26. **Benchmark 1080p**: Measure frame time; should be well under 16ms for 60fps (likely < 2ms).
27. **S-curve cost**: Compare performance with `curve=0` vs `curve=10` to measure `exp()` impact.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT034: ContrastEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementation:

- [`core/effects/color.py`](home/happy/Desktop/claude projects/VJlive-2/core/effects/color.py:1) (VJlive Original) — Full implementation of `ContrastEffect` with shader code spanning lines 265-312 and class definition at lines 315-343.

The legacy code validates the parameter ranges, default values, preset configurations, and mathematical formulations described in this spec. The shader implements contrast with S-curve shaping and separate shadow/highlight controls using luma-based masks.

---

## Open Questions / [NEEDS RESEARCH]

- **Should we support per-channel contrast?** Some color graders want separate RGB contrast controls. [NEEDS RESEARCH]
- **Should we add a "contrast protection" mode?** Similar to vibrance, could protect skin tones or specific colors from contrast shifts. [NEEDS RESEARCH]
- **Should we implement a full tone curve?** The current S-curve is a simple parameter. A full 1D LUT curve would give more control. [NEEDS RESEARCH]
- **Should we add local contrast (CLAHE)?** Adaptive histogram equalization could enhance detail without blowing out global contrast. [NEEDS RESEARCH]
- **Should we support different luma coefficients?** The current luma uses Rec. 709 (0.299, 0.587, 0.114). Should we allow custom coefficients for different color spaces? [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*