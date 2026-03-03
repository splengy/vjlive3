# ChromaKeyEffect — Professional Chroma Key with Spill Suppression

**Task ID:** P3-EXT027  
**Module:** `ChromaKeyEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`ChromaKeyEffect`](docs/specs/_02_fleshed_out/P3-EXT027_ChromaKeyEffect.md:200) class implements a professional-grade chroma key (green/blue screen) compositing effect with sophisticated spill suppression, edge refinement, and multiple output modes. It operates in HSV color space for perceptually accurate color matching and provides fine-grained control over every aspect of the keying process.

**What This Module Does**

- Performs HSV-space color matching to isolate a target key color (any hue, not just green/blue)
- Applies spill suppression to remove color spill from semi-transparent edges
- Refines matte edges through feathering, erosion, and dilation operations
- Removes colored fringe artifacts via defringing
- Supports three output modes: composite (transparent background), matte view, and spill view
- Provides preset configurations for green screen and blue screen workflows

**What This Module Does NOT Do**

- Does not perform color correction on the foreground subject (only spill suppression)
- Does not support multiple key colors simultaneously (single hue only)
- Does not include garbage matte or rough-selection tools (assumes full-frame key)
- Does not handle temporal coherence or frame-to-frame stabilization (per-frame only)
- Does not support 3D camera solving or perspective correction (2D only)

---

## Detailed Behavior and Parameter Interactions

### Parameter Space and UI Mapping

All user-facing parameters use a normalized `0.0` to `10.0` range from UI sliders. The shader internally remaps these to appropriate mathematical ranges:

| Parameter | UI Range | Internal Range | Purpose |
|-----------|----------|----------------|---------|
| `key_hue` | 0.0-10.0 | 0.0-1.0 (hue wheel) | Target hue to key out (0=red, 0.33=green, 0.66=blue) |
| `hue_tolerance` | 0.0-10.0 | 0.0-0.5 (fraction of hue circle) | How wide a hue band to consider as key color |
| `sat_min` | 0.0-10.0 | 0.0-1.0 | Minimum saturation threshold (low-sat pixels ignored) |
| `luma_min` | 0.0-10.0 | 0.0-1.0 | Minimum brightness to key (shadows preserved) |
| `luma_max` | 0.0-10.0 | 0.0-1.0 | Maximum brightness to key (highlights preserved) |
| `edge_feather` | 0.0-10.0 | 0.0-0.3 (fraction) | Softness of matte edge transition |
| `edge_erode` | 0.0-10.0 | -0.2 to +0.2 | Negative = dilate (shrink key), Positive = erode (expand key) |
| `spill_suppress` | 0.0-10.0 | 0.0-1.0 | Strength of spill color removal on semi-transparent edges |
| `defringe` | 0.0-10.0 | 0.0-1.0 | Amount of neighbor averaging to reduce colored fringes |
| `output_mode` | 0.0-10.0 | 0, 1, or 2 | 0=composite, 1=matte view, 2=spill view |

### Core Algorithm: HSV-Space Keying

The effect converts each pixel from RGB to HSV using the standard conversion:

```glsl
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}
```

The key strength is computed as:

1. **Hue match**: Circular distance between pixel hue and target hue, softened by tolerance and feather:
   ```glsl
   float hue_dist = hue_distance(hsv.x, target_hue);  // circular distance 0-0.5
   float inner_tol = max(0.001, h_tol - feather);
   float hue_match = 1.0 - smoothstep(inner_tol, h_tol, hue_dist);
   ```

2. **Saturation gate**: Low-saturation pixels (grays) should not be keyed even if hue matches:
   ```glsl
   float sat_match = smoothstep(s_min * 0.3, s_min, hsv.y);
   ```

3. **Luma gate**: Very dark or very bright pixels are excluded from keying to preserve shadows/highlights:
   ```glsl
   float luma_match = smoothstep(l_min, l_min + 0.05, hsv.z) 
                    * (1.0 - smoothstep(l_max - 0.05, l_max, hsv.z));
   ```

4. **Combined key strength** (0 = keep foreground, 1 = remove as background):
   ```glsl
   float key = hue_match * sat_match * luma_match;
   ```

### Edge Refinement: Erosion/Dilation

When `edge_erode` is non-zero, a 7×7 neighborhood sampling pass modifies the key:

- **Erosion** (`edge_erode > 5.0`): Expands transparent areas by taking `max(key, neighbor_avg)` — if any neighbor is strongly keyed, the center becomes keyed.
- **Dilation** (`edge_erode < 5.0`): Shrinks transparent areas by taking `min(key, neighbor_avg)` — only key if all neighbors agree.

Radius scales with `abs(erode) * 10.0` pixels.

### Spill Suppression

Spill occurs when reflected key color tints semi-transparent edge pixels. The algorithm:

1. Detect spill-prone pixels: `if (spill > 0.0 && key < 0.95)`
2. Compute spill amount from hue/sat matches: `spill_amount = hue_match * sat_match * spill`
3. Desaturate the spill component: `spill_hsv.y *= (1.0 - spill_amount * 0.8)`
4. Shift hue away from target hue by `spill_amount * 0.05` (randomized direction)
5. Convert back to RGB

This preserves natural color variation while removing green/blue tints.

### Defringing

Colored fringes appear at hard edges due to sampling errors. When `defringe > 0` and `0.01 < key < 0.99`:

1. Sample 4-neighbor pixels (left, right, up, down)
2. Compute luminance-only average: `avg_neighbor = (left + right + up + down) * 0.25`
3. Blend original despilled color toward neighbor average: `despilled = mix(despilled, avg_neighbor, edge_factor * 0.5)`

This smooths high-frequency color artifacts while preserving edge sharpness.

### Output Modes

- **Mode 0 (Composite)**: `fragColor = mix(input_color, vec4(despilled, 1.0-key), u_mix)` — blends between original and keyed result based on `u_mix` parameter (allows wet/dry control).
- **Mode 1 (Matte View)**: `fragColor = vec4(vec3(alpha), 1.0)` — grayscale visualization of the alpha matte.
- **Mode 2 (Spill View)**: `fragColor = vec4(abs(input_color - despilled) * 5.0, 1.0)` — highlights where spill suppression is active.

---

## Public Interface

### Class: `ChromaKeyEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT027_ChromaKeyEffect.md:200) (from `core.effects.shader_base`)

**Constructor:** `__init__(self)`

Initializes the effect with default parameters optimized for green screen:

```python
self.parameters = {
    "key_hue": 3.33,        # Green (120° / 360° * 10)
    "hue_tolerance": 2.0,
    "sat_min": 2.0,
    "luma_min": 1.0,
    "luma_max": 9.5,
    "edge_feather": 3.0,
    "edge_erode": 5.0,      # Neutral (5 = no erode/dilate)
    "spill_suppress": 5.0,
    "defringe": 3.0,
    "output_mode": 0.0,
}
```

**Static Methods:**

- `green_screen_preset() -> dict`: Returns parameters optimized for green screen (key_hue=3.33, slightly higher spill suppression, slight erode).
- `blue_screen_preset() -> dict`: Returns parameters optimized for blue screen (key_hue=6.67, higher sat_min, different feather/erode).

**Properties:**

- `name = "chroma_key"` — Effect identifier
- `fragment_shader = CHROMA_KEY_FRAGMENT` — GLSL shader code (see full listing above)

**No additional public methods** — all logic is in the shader; the Python class only manages parameters.

---

## Inputs and Outputs

### Inputs

| Pin | Type | Description |
|-----|------|-------------|
| `tex0` | `sampler2D` | Input video frame (foreground with key color background) |
| `u_mix` | `float` | Blend factor between original and keyed result (0.0-1.0) |
| `time` | `float` | Shader time in seconds (unused but required by base class) |
| `resolution` | `vec2` | Viewport resolution in pixels |

### Uniforms (from Parameters)

All parameters are passed as separate uniforms to the shader:

- `key_hue`, `hue_tolerance`, `sat_min`, `luma_min`, `luma_max`
- `edge_feather`, `edge_erode`, `spill_suppress`, `defringe`
- `output_mode`

### Outputs

| Pin | Type | Description |
|-----|------|-------------|
| `fragColor` | `vec4` | RGBA output with premultiplied alpha (if composite mode) |

**Output Mode Details:**

- **Composite (0)**: Output has transparent alpha where key color was detected. Foreground colors are despilled.
- **Matte View (1)**: Output is grayscale alpha matte (white=foreground, black=background).
- **Spill View (2)**: Output highlights spill suppression regions (bright = active spill removal).

---

## Edge Cases and Error Handling

### Edge Cases

1. **All parameters at neutral (5.0)**: The effect should produce a reasonable default key for green screen without additional tuning.

2. **Extreme hue tolerance (>9.0)**: May key large portions of the image including non-target colors. The algorithm handles this gracefully but produces poor results — no error raised.

3. **Zero tolerance (0.0)**: Only exact hue matches key. Combined with low `sat_min` and narrow `luma` range, this may produce no keyed pixels (fully opaque output). This is valid behavior.

4. **Inverted luma range** (`luma_min > luma_max`): The `luma_match` becomes zero everywhere, effectively disabling luma gating. The shader does not validate this; it simply produces no key.

5. **High spill suppression with low key strength**: Spill code only runs when `key < 0.95`. If the key is already near 1.0 (fully transparent), spill suppression is skipped to avoid unnecessary computation.

6. **Defringe on fully opaque or fully transparent pixels**: Defringe only runs when `0.01 < key < 0.99` to avoid wasting cycles on pixels where edge refinement doesn't matter.

7. **Erosion/dilation at extreme radii**: The 7×7 kernel loops over up to 49 samples. If `abs(erode) * 10.0 > 3.5`, the radius exceeds kernel size and the loop still iterates over all 49 samples but many fall outside the intended radius. This is harmless but inefficient.

8. **Output mode out of range**: Mode is computed as `int(output_mode / 10.0 * 2.0 + 0.5)`. Values 0-4.9 map to 0, 5-9.9 map to 1, 10+ map to 2. Invalid values default to composite mode (0).

### Error Handling

- **No runtime errors** — the shader is pure functional and handles all edge cases via clamping and conditional guards.
- **Division by zero protection**: `rgb2hsv` uses `e = 1.0e-10` to avoid division by zero when `d` is near zero.
- **Circular hue distance**: `hue_distance` uses `min(d, 1.0-d)` to correctly handle hue wrap-around at 0/1 boundary.
- **Parameter remapping**: All UI sliders are safely remapped without overflow or underflow concerns.

---

## Mathematical Formulations

### HSV Conversion

Standard RGB→HSV and HSV→RGB conversions (see GLSL code). The hue component is normalized to `[0, 1)`.

### Circular Hue Distance

```glsl
float hue_distance(float h1, float h2) {
    float d = abs(h1 - h2);
    return min(d, 1.0 - d);  // shortest path around hue wheel
}
```

### Key Strength Calculation

Let:
- `H` = pixel hue, `H₀` = target hue
- `S` = pixel saturation, `S_min` = `sat_min / 10.0`
- `V` = pixel luma, `V_min` = `luma_min / 10.0`, `V_max` = `luma_max / 10.0`
- `T_h` = `hue_tolerance / 10.0 * 0.5`
- `F` = `edge_feather / 10.0 * 0.3`

Then:

```
hue_dist = min(|H - H₀|, 1 - |H - H₀|)
inner_tol = max(0.001, T_h - F)
hue_match = 1 - smoothstep(inner_tol, T_h, hue_dist)
sat_match = smoothstep(S_min * 0.3, S_min, S)
luma_match = smoothstep(V_min, V_min+0.05, V) * (1 - smoothstep(V_max-0.05, V_max, V))
key = hue_match * sat_match * luma_match
```

### Spill Suppression

When `spill > 0` and `key < 0.95`:

```
spill_amount = hue_match * sat_match * (spill / 10.0)
desaturation_factor = 1.0 - spill_amount * 0.8
hue_shift = spill_amount * 0.05  (direction randomized by comparing distances)
new_sat = S * desaturation_factor
new_hue = (H ± hue_shift) mod 1.0
```

### Defringing

When `defr > 0` and `0.01 < key < 0.99`:

```
edge_factor = key * (defringe / 10.0)
avg_neighbor = average(luminance(RGB of left, right, up, down samples))
despilled = mix(despilled, avg_neighbor, edge_factor * 0.5)
```

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: O(1) per pixel (HSV conversion, hue distance, smoothsteps)
- **Erosion/dilation**: O(k²) per pixel where k = `ceil(abs(erode) * 10.0)`, max k=7 (49 samples)
- **Defringe**: O(1) with 4 additional texture samples
- **Spill suppression**: O(1) (HSV manipulation only)

**Typical worst-case**: With both erosion (`erode=10.0`) and defringe enabled, each pixel requires ~55 texture samples (1 base + 49 neighborhood + 4 defringe). This is expensive but still feasible at 1080p on modern GPUs.

### Memory Usage

- **Uniforms**: 11 floats + 1 sampler2D
- **No framebuffer allocations** — all operations are single-pass
- **No dynamic memory** — all arrays are compile-time constants

### GPU Optimization Notes

- The 7×7 erosion loop is unrolled; the compiler may optimize away samples outside the radius.
- Consider reducing kernel size to 5×5 for better performance on mobile GPUs.
- Spill suppression and defringe are mutually exclusive in practice (both target edges) — could be combined into a single pass.

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python/GLSL validation)

1. **HSV conversion round-trip**: Verify `rgb2hsv` and `hsv2rgb` are inverses across color space.
2. **Hue distance wrap-around**: Test `hue_distance(0.9, 0.1) == 0.2` (crosses 0/1 boundary).
3. **Parameter remapping**: Verify all UI→internal mappings are correct (e.g., `key_hue=3.33` → `0.333`).
4. **Erosion/dilation logic**: Test that `erode > 5.0` uses `max` and `erode < 5.0` uses `min`.
5. **Spill suppression math**: Verify desaturation and hue shift produce expected results.
6. **Defringe neighbor averaging**: Test that defringe blends toward luminance-only average.
7. **Output mode selection**: Test mode 0, 1, 2 produce correct outputs.
8. **Edge condition: zero tolerance**: Ensure `hue_tolerance=0` produces binary key (no smooth transition).
9. **Edge condition: full transparency**: Verify `key=1.0` bypasses spill/defringe.
10. **Edge condition: full opacity**: Verify `key=0.0` produces original color unchanged.

### Integration Tests (Shader rendering)

11. **Green screen test**: Render a test pattern with known green background (RGB=0,1,0) and verify alpha ≈ 1.0 in green regions.
12. **Spill suppression test**: Render a green-screen portrait with semi-transparent hair edges and verify green tint is reduced.
13. **Erosion test**: Render a high-contrast edge and verify matte shrinks/grows appropriately.
14. **Defringe test**: Render a sharp edge with colored fringe and verify fringe is reduced.
15. **Matte view mode**: Verify grayscale output matches computed alpha.
16. **Spill view mode**: Verify bright regions correspond to active spill suppression areas.
17. **Preset validation**: Test `green_screen_preset()` and `blue_screen_preset()` produce reasonable keys on respective test images.

### Performance Tests

18. **Benchmark 1080p**: Measure frame time with all effects disabled, with erosion, with defringe, with both.
19. **Memory bandwidth**: Ensure no texture thrashing or unnecessary allocations.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT027: ChromaKeyEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementations:

- [`core/effects/chroma_key.py`](home/happy/Desktop/claude projects/VJlive-2/core/effects/chroma_key.py:1) (VJlive Original) — Full shader implementation with HSV keying, spill suppression, edge refinement, and output modes.
- [`plugins/vcore/chroma_key.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/vcore/chroma_key.py:1) — Identical implementation in plugin format.

The legacy code validates the parameter ranges, default values, and algorithmic approach described in this spec. The green screen preset uses `key_hue=3.33` (120° green) with `spill_suppress=6.0` and slight erode (`edge_erode=5.2`). The blue screen preset uses `key_hue=6.67` (240° blue) with higher `sat_min=2.5`.

---

## Open Questions / [NEEDS RESEARCH]

- **Temporal smoothing**: The legacy code does not include frame-to-frame coherence. Should we add temporal filtering in VJLive3? [NEEDS RESEARCH]
- **Color spill from multi-colored backgrounds**: Current algorithm assumes single-key-color backgrounds. How does it perform on complex multi-colored screens? [NEEDS RESEARCH]
- **Garbage matte support**: Professional workflows often require rough selection masks. Should we add a `mask_input` pin? [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*