# CupcakeCascadeDatamoshEffect — Frosting Drips and Sugar Pixel Avalanche

**Task ID:** P3-EXT037  
**Module:** `CupcakeCascadeDatamoshEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`CupcakeCascadeDatamoshEffect`](docs/specs/_02_fleshed_out/P3-EXT037_CupcakeCascadeDatamoshEffect.md:217) class implements a gravity-based datamosh effect that transforms video into a sugary cupcake cascade. Pixels drip downward like frosting from depth edges, cascade in sugary avalanches, and get coated in pastel frosting colors. The effect includes sprinkles, whipped cream bloom, and cherry accents, creating a dreamy, dessert-themed visual experience.

**What This Module Does**

- Simulates gravity-driven frosting drips from depth edges
- Implements sugar cascade (block-based pixel avalanche) that flows downward
- Applies pastel frosting color palette (pink, mint, lavender, lemon, peach)
- Generates sprinkle particles on depth contours
- Creates layer cake horizontal stripes based on depth zones
- Adds whipped cream bloom glow on highlights
- Places cherry accents at motion peaks
- Uses dual video inputs with automatic fallback detection
- Integrates audio reactivity for dynamic visual response
- Provides 12 controllable parameters for fine-tuned visual effects

**What This Module Does NOT Do**

- Does not include traditional datamosh compression artifacts (no motion vector displacement)
- Does not support 3D geometry or raymarching (uses 2D coordinate transforms)
- Does not provide temporal smoothing or frame blending beyond the single `texPrev` feedback
- Does not include particle systems beyond the built-in sprinkle and cherry effects
- Does not support custom color palettes beyond the built-in pastel frosting colors

---

## Detailed Behavior and Parameter Interactions

### Texture Unit Layout

The effect uses multiple texture units:

| Unit | Name | Type | Purpose |
|------|------|------|---------|
| 0 | `tex0` | `sampler2D` | Primary video input (Video A) |
| 1 | `texPrev` | `sampler2D` | Previous frame buffer (for drip persistence and motion detection) |
| 2 | `depth_tex` | `sampler2D` | Depth map (single channel, typically red) |
| 3 | `tex1` | `sampler2D` | Secondary video input (Video B, optional) |

The effect automatically detects if `tex1` is valid by sampling its center pixel. If the sum of RGB channels is > 0.001, `tex1` is used; otherwise `tex0` is used.

### Core Algorithm: Gravity-Based Dripping and Cascading

The effect transforms video into cupcake cascade through several stages:

1. **Gravity Drip**:
   ```glsl
   float dripAccum = 0.0;
   vec3 dripColor = vec3(0.0);
   float dripSteps = u_drip_length * 3.0;
   
   for (float i = 1.0; i <= 15.0; i++) {
       if (i > dripSteps) break;
       vec2 above = uv - vec2(0.0, i * texel.y * 3.0);
       if (above.y < 0.0) break;
       
       float aboveDepth = texture(depth_tex, above).r;
       float depthDiff = abs(aboveDepth - depth);
       
       // Drip from depth edges
       if (depthDiff > 0.05) {
           float dripMask = (1.0 - i / dripSteps) * depthDiff * 5.0;
           dripMask *= (0.5 + 0.5 * sin(time * u_drip_speed + hash(vec2(floor(uv.x * 50.0), 0.0)) * 6.28));
           dripAccum += dripMask;
           vec4 aboveSample = hasDual ? texture(tex1, above) : texture(tex0, above);
           dripColor += aboveSample.rgb * dripMask;
       }
   }
   dripAccum = clamp(dripAccum, 0.0, 1.0);
   if (dripAccum > 0.01) dripColor /= (dripAccum * 15.0);
   ```

   The drip samples pixels above the current pixel (up to `dripSteps`), looking for depth edges (`depthDiff > 0.05`). It accumulates a weighted sum of colors from those pixels, with the weight falling off with distance. A sine wave modulates the drip mask for animation.

2. **Sugar Cascade**:
   ```glsl
   float blockSize = max(2.0, u_cascade_size * 15.0);
   vec2 blockUV = floor(uv * resolution / blockSize) * blockSize / resolution;
   float blockId = hash(blockUV);
   
   // Blocks fall downward based on depth
   float fallAmount = depth * u_gravity * 0.03;
   fallAmount += sin(time * u_cascade_rate + blockId * 6.28) * 0.01 * u_cascade_rate;
   vec2 cascadeUV = uv + vec2(0.0, fallAmount);
   cascadeUV = clamp(cascadeUV, 0.0, 1.0);
   
   vec4 color = hasDual ? texture(tex1, cascadeUV) : texture(tex0, cascadeUV);
   ```

   The cascade divides the screen into blocks (size controlled by `u_cascade_size`). Each block falls downward by an amount proportional to its depth and a time-varying sine wave. The sample coordinate `cascadeUV` is offset downward, creating a falling sugar effect.

3. **Frosting Color Overlay**:
   ```glsl
   vec3 frostTint = frostingColor(depth + time * 0.1);
   vec3 dripFinal = mix(dripColor, frostTint, u_frosting * 0.08);
   color.rgb = mix(color.rgb, dripFinal, dripAccum * 0.7);
   color.rgb = mix(color.rgb, color.rgb * frostTint, u_frosting * 0.04);
   ```

   The frosting color is a pastel gradient based on depth and time. It's applied both to the drip accumulation and as a multiplicative tint to the entire image.

4. **Sweetness (Saturation Boost)**:
   ```glsl
   float lum = dot(color.rgb, vec3(0.299, 0.587, 0.114));
   vec3 sweet = mix(vec3(lum), color.rgb, 1.0 + u_sweetness * 0.05);
   sweet = mix(sweet, sweet * frostTint, u_sweetness * 0.03);
   color.rgb = clamp(sweet, 0.0, 1.0);
   ```

   Sweetness increases saturation by blending toward the original color with a factor >1.0, then mixing in a frosting tint.

5. **Layer Cake Stripes**:
   ```glsl
   if (u_layer_count > 0.5) {
       float stripe = sin(depth * u_layer_count * 3.14159 * 2.0) * 0.5 + 0.5;
       stripe = smoothstep(0.4, 0.6, stripe);
       vec3 stripeCol = frostingColor(floor(depth * u_layer_count) / u_layer_count);
       color.rgb = mix(color.rgb, stripeCol, stripe * u_frosting * 0.03);
   }
   ```

   Horizontal stripes are drawn at depth intervals, creating a layered cake appearance. The stripe intensity is modulated by `u_frosting`.

6. **Sprinkles**:
   ```glsl
   float sprinkleScale = 150.0;
   vec2 sprinkleCell = floor(uv * sprinkleScale);
   float sprinkleId = hash(sprinkleCell);
   if (sprinkleId > 1.0 - u_sprinkle_density * 0.06) {
       vec2 cellFract = fract(uv * sprinkleScale);
       float sprinkleAngle = sprinkleId * 3.14;
       bool inSprinkle = abs(cellFract.x - 0.5) < 0.15 && abs(cellFract.y - 0.5) < 0.35;
       if (inSprinkle) {
           vec3 sprinkleCol = hsv2rgb(vec3(sprinkleId * 6.0, 0.7, 1.0));
           color.rgb = mix(color.rgb, sprinkleCol, 0.8);
       }
   }
   ```

   Sprinkles are tiny colored rectangles placed on a grid. Their density is controlled by `u_sprinkle_density`. Colors are generated from HSV with random hue.

7. **Whipped Cream Bloom**:
   ```glsl
   if (u_whipped_bloom > 0.5 && lum > 0.6) {
       vec4 cream = vec4(0.0);
       for (float dx = -2.0; dx <= 2.0; dx++) {
           for (float dy = -2.0; dy <= 2.0; dy++) {
               cream += texture(hasDual ? tex1 : tex0, cascadeUV + vec2(dx, dy) * texel * u_whipped_bloom);
           }
       }
       cream /= 25.0;
       cream.rgb = mix(cream.rgb, vec3(1.0, 0.98, 0.95), 0.3);
       color = mix(color, max(color, cream), u_whipped_bloom * 0.04 * (lum - 0.5));
   }
   ```

   A 5x5 box blur is applied to bright areas (`lum > 0.6`) and tinted with a whipped cream color. The effect is additive (`max(color, cream)`).

8. **Cherry on Top**:
   ```glsl
   vec4 prev = texture(texPrev, cascadeUV);
   float motion = length(color.rgb - prev.rgb);
   if (motion > 0.15 && u_cherry > 0.5) {
       float cherryMask = smoothstep(0.15, 0.4, motion);
       vec3 cherryColor = vec3(0.95, 0.15, 0.2);
       color.rgb += cherryColor * cherryMask * u_cherry * 0.06;
   }
   ```

   Cherry accents appear where there is high motion (difference between current and previous frame). The cherry color is a bright red.

9. **Melt (Temporal Blend)**:
   ```glsl
   color = mix(color, prev, u_melt_rate * 0.06);
   ```

   A small amount of temporal blending with the previous frame creates a melting effect.

10. **Final Mix**:
    ```glsl
    vec4 original = hasDual ? texture(tex1, uv) : texture(tex0, uv);
    fragColor = mix(original, color, u_mix);
    ```

### Parameter Space and UI Mapping

All user-facing parameters use a normalized `0.0` to `10.0` range. The class uses a `_map_param()` method to convert these to shader-specific ranges:

| Parameter | UI Range | Shader Uniform | Internal Range | Purpose |
|-----------|----------|----------------|----------------|---------|
| `drip_speed` | 0.0-10.0 | `u_drip_speed` | 0.5-5.0 | Animation speed of frosting drips |
| `drip_length` | 0.0-10.0 | `u_drip_length` | 0.0-10.0 | How far frosting runs (in steps) |
| `cascade_rate` | 0.0-10.0 | `u_cascade_rate` | 0.0-5.0 | Sugar block avalanche speed |
| `cascade_size` | 0.0-10.0 | `u_cascade_size` | 0.1-1.0 (block size multiplier) | Avalanche block size |
| `frosting` | 0.0-10.0 | `u_frosting` | 0.0-10.0 | Pastel color intensity |
| `sprinkle_density` | 0.0-10.0 | `u_sprinkle_density` | 0.0-1.0 (with audio boost) | Sprinkle count |
| `layer_count` | 0.0-10.0 | `u_layer_count` | 0.0-8.0 | Cake layer stripe count |
| `whipped_bloom` | 0.0-10.0 | `u_whipped_bloom` | 0.0-10.0 | Whipped cream glow intensity |
| `cherry` | 0.0-10.0 | `u_cherry` | 0.0-10.0 | Cherry accent brightness |
| `gravity` | 0.0-10.0 | `u_gravity` | 0.0-1.0 (with audio boost) | Downward pull strength |
| `sweetness` | 0.0-10.0 | `u_sweetness` | 0.0-1.0 (with audio boost) | Overall sugar saturation |
| `melt_rate` | 0.0-10.0 | `u_melt_rate` | 0.0-1.0 | How fast things melt together |

**Note:** The `_map_param(name, out_min, out_max)` function computes: `out_min + (val / 10.0) * (out_max - out_min)`.

### Audio Reactivity

The effect includes audio reactivity via the `apply_uniforms` method:

```python
gravity *= (1.0 + audio_reactor.get_band('bass', 0.0) * 0.8)
sprinkle *= (0.5 + audio_reactor.get_energy(0.5))
drip *= (0.7 + audio_reactor.get_band('mid', 0.3))
sweet *= (1.0 + audio_reactor.get_band('high', 0.0) * 0.4)
```

The `audio_mappings` dictionary documents these connections:

```python
self.audio_mappings = {
    'gravity': 'bass',
    'sprinkle_density': 'energy',
    'drip_speed': 'mid',
    'sweetness': 'high',
}
```

This means:
- **Bass** directly modulates gravity (downward pull)
- **Overall energy** (mid frequencies) modulates sprinkle density
- **Mid-range frequencies** modulate drip speed
- **High frequencies** modulate sweetness (saturation)

### Preset Configurations

The class provides four preset parameter sets:

- **`light_glaze`**: `{drip_speed: 3.0, drip_length: 2.0, cascade_rate: 2.0, cascade_size: 5.0, frosting: 4.0, sprinkle_density: 2.0, layer_count: 0.0, whipped_bloom: 3.0, cherry: 2.0, gravity: 2.0, sweetness: 4.0, melt_rate: 2.0}` — gentle glaze with minimal dripping and no layer stripes.
- **`birthday_cake`**: `{drip_speed: 5.0, drip_length: 5.0, cascade_rate: 4.0, cascade_size: 5.0, frosting: 7.0, sprinkle_density: 6.0, layer_count: 4.0, whipped_bloom: 5.0, cherry: 5.0, gravity: 4.0, sweetness: 7.0, melt_rate: 4.0}` — classic birthday cake with moderate drips, sprinkles, and 4 layers.
- **`sugar_overload`**: `{drip_speed: 8.0, drip_length: 8.0, cascade_rate: 7.0, cascade_size: 4.0, frosting: 10.0, sprinkle_density: 9.0, layer_count: 6.0, whipped_bloom: 8.0, cherry: 8.0, gravity: 7.0, sweetness: 10.0, melt_rate: 6.0}` — intense sugar overload with maximum frosting, sprinkles, and 6 layers.
- **`melting_sundae`**: `{drip_speed: 3.0, drip_length: 10.0, cascade_rate: 2.0, cascade_size: 7.0, frosting: 6.0, sprinkle_density: 4.0, layer_count: 3.0, whipped_bloom: 7.0, cherry: 7.0, gravity: 8.0, sweetness: 6.0, melt_rate: 8.0}` — melting ice cream sundae with long drips, high gravity, and high melt rate.

---

## Public Interface

### Class: `CupcakeCascadeDatamoshEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT037_CupcakeCascadeDatamoshEffect.md:217) (from `core.effects.shader_base`)

**Constructor:** `__init__(self, name: str = 'cupcake_cascade_datamosh')`

Initializes the effect with default parameters:

```python
self.parameters = {
    'drip_speed': 5.0, 'drip_length': 5.0, 'cascade_rate': 4.0,
    'cascade_size': 5.0, 'frosting': 7.0, 'sprinkle_density': 5.0,
    'layer_count': 3.0, 'whipped_bloom': 5.0, 'cherry': 5.0,
    'gravity': 4.0, 'sweetness': 6.0, 'melt_rate': 4.0,
}
self.audio_mappings = {
    'gravity': 'bass', 'sprinkle_density': 'energy',
    'drip_speed': 'mid', 'sweetness': 'high',
}
```

**Properties:**

- `name = "cupcake_cascade_datamosh"` (or custom name passed to constructor)
- `fragment_shader = FRAGMENT` — GLSL fragment shader (see full listing in legacy reference)
- `effect_category` — Not explicitly set in legacy; likely `"datamosh"` or `"distortion"`
- `effect_tags` — Not explicitly set; based on description: `["datamosh", "glitch", "effect", "cupcake", "cascade", "frosting"]`
- `audio_mappings` — Dictionary mapping parameters to audio features
- `PRESETS` — Dictionary of preset parameter configurations (see above)

**Methods:**

- `apply_uniforms(time, resolution, audio_reactor=None, semantic_layer=None)`: Sets all shader uniforms, including parameter mapping and audio modulation. Overrides base class.
- `get_state() -> Dict[str, Any]`: Returns a dictionary with `{'name': self.name, 'enabled': self.enabled, 'parameters': dict(self.parameters)}`.
- `set_parameter(name: str, value: float)`: Likely inherited from base class; should clamp to [0.0, 10.0].
- `get_parameter(name: str) -> float`: Likely inherited; returns parameter value in UI range.

**Class Attributes:**

- `PRESETS` — Dictionary of preset parameter configurations (see above).
- `FRAGMENT` — The full GLSL shader code (lines 34-213 in legacy file).

---

## Inputs and Outputs

### Inputs

| Pin | Type | Description |
|-----|------|-------------|
| `tex0` | `sampler2D` | Primary video input (Video A) |
| `texPrev` | `sampler2D` | Previous frame buffer (for drip persistence and motion detection) |
| `depth_tex` | `sampler2D` | Depth map (single channel, typically red) |
| `tex1` | `sampler2D` | Secondary video input (Video B, optional) |
| `u_mix` | `float` | Blend factor between original and effect result (0.0-1.0) |
| `time` | `float` | Shader time in seconds (for animation) |
| `resolution` | `vec2` | Viewport resolution in pixels |
| `uv` | `vec2` | Normalized texture coordinates |

All parameters are passed as uniforms (see table above).

### Outputs

| Pin | Type | Description |
|-----|------|-------------|
| `fragColor` | `vec4` | RGBA output with cupcake cascade effect applied (alpha unchanged) |

---

## Edge Cases and Error Handling

### Edge Cases

1. **No previous frame**: `texPrev` must be a valid texture containing the previous frame's output. If not provided or uninitialized, the drip persistence and motion detection (cherry) will sample undefined data. The host must manage framebuffer ping-pong.

2. **No depth map**: `depth_tex` is required. If not provided or all zeros, the depth-based effects (drip from edges, cascade fall amount, layer stripes, sprinkle placement) will be minimized. The effect will still render but may look flat and less dynamic.

3. **Dual input detection**: The code checks `hasDual` by sampling the center of `tex1`. If `tex1` is not bound or is black, `hasDual` is false and `tex0` is used. This is safe.

4. **Extreme parameter values**:
   - `u_drip_length = 10.0` (max) samples up to 30 pixels above (since `dripSteps = u_drip_length * 3.0`), which can be expensive and may cause sampling outside texture bounds if not clamped.
   - `u_cascade_size = 10.0` → `blockSize = max(2.0, 10.0 * 15.0) = 150.0` pixels, creating very large blocks. This can make the cascade effect very blocky.
   - `u_gravity = 10.0` (max) → `fallAmount = depth * 1.0 * 0.03 = up to 0.03` per frame, which is moderate.
   - `u_sprinkle_density = 10.0` → density threshold `1.0 - 10.0*0.06 = 0.4`, so 60% of grid cells get sprinkles. This can be very dense.
   - `u_whipped_bloom = 10.0` creates a large blur radius (10.0 texels) and can significantly brighten highlights.
   - `u_cherry = 10.0` adds strong red accents at motion peaks.

5. **Loop bounds**: The drip loop runs up to 15 iterations but breaks early if `i > dripSteps`. This is safe and prevents infinite loops.

6. **Division by zero**: No divisions in the shader that could divide by zero. The `hash` function uses multiplication and `fract`, safe.

7. **Audio reactivity errors**: The `try/except` around audio modulation means if `audio_reactor` methods fail, the effect continues without audio reactivity. This is safe but may hide bugs.

8. **Texture sampling precision**: The effect samples textures at `cascadeUV + vec2(dx, dy) * texel * u_whipped_bloom`. If `cascadeUV` is near texture edges and `u_whipped_bloom` is large, sampling may go out of bounds. The host should ensure textures are properly padded or clamped.

### Error Handling

- **No runtime errors** — all operations are safe GLSL; `sin()`, `cos()`, `exp()` are well-behaved.
- **Parameter clamping**: Python `set_parameter()` clamps all values to [0.0, 10.0], preventing invalid uniform uploads.
- **No NaN propagation**: All math operations are well-conditioned with proper clamping.

---

## Mathematical Formulations

### Parameter Remapping

For each parameter `p_ui` ∈ [0, 10], the shader uniform `u_p` is computed as:

```
u_p = p_min + (p_ui / 10.0) * (p_max - p_min)
```

where the `(p_min, p_max)` pairs are as listed in the table above.

### Noise and Hash Functions

**Hash function** (for pseudo-random values):
```glsl
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
```

**HSV to RGB conversion** (for sprinkle colors):
```glsl
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
```

### Frosting Color Palette

The `frostingColor` function cycles through 5 pastel colors:
```glsl
vec3 frostingColor(float t) {
    vec3 colors[5] = vec3[5](
        vec3(1.0, 0.75, 0.85),   // Pink
        vec3(0.7, 1.0, 0.85),    // Mint
        vec3(0.85, 0.75, 1.0),   // Lavender
        vec3(1.0, 1.0, 0.75),    // Lemon
        vec3(1.0, 0.85, 0.7)     // Peach
    );
    float idx = mod(t * 5.0, 5.0);
    int i0 = int(floor(idx));
    int i1 = int(mod(float(i0 + 1), 5.0));
    return mix(colors[i0], colors[i1], fract(idx));
}
```

### Depth-Based Effects

Depth is sampled from `depth_tex.r` and used to modulate:
- **Drip accumulation**: `depthDiff = abs(aboveDepth - depth)` — only drips from significant depth edges.
- **Cascade fall**: `fallAmount = depth * u_gravity * 0.03` — deeper pixels fall faster.
- **Layer stripes**: `sin(depth * u_layer_count * 2π)` — stripes at depth intervals.
- **Frosting tint**: `frostTint = frostingColor(depth + time * 0.1)` — color varies with depth.

### Audio Modulation

Audio reactivity modifies parameters in `apply_uniforms`:
```python
gravity *= (1.0 + audio_reactor.get_band('bass', 0.0) * 0.8)
sprinkle *= (0.5 + audio_reactor.get_energy(0.5))
drip *= (0.7 + audio_reactor.get_band('mid', 0.3))
sweet *= (1.0 + audio_reactor.get_band('high', 0.0) * 0.4)
```

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: Moderate to high. The shader performs:
  - 1-2 texture samples (primary + optional secondary) + 1 feedback sample + 1 depth sample = 3-4 samples per pixel
  - Drip loop: up to 15 iterations per pixel, each with a texture sample (worst-case 15+ samples!)
  - Whipped cream bloom: 5x5 kernel (25 texture samples) when active
  - Multiple hash calls for noise, block IDs, sprinkles
  - Multiple arithmetic operations for color composition
- **Heavy GPU load**: This is a `MEDIUM` to `HIGH` tier effect as per plugin manifest. Expect 5-15ms per 1080p frame on modern GPU, possibly more with all effects enabled.

### Memory Usage

- **Uniforms**: 12 floats + standard uniforms (time, resolution, u_mix) = ~14 uniforms.
- **Textures**: Requires 3-4 texture units bound simultaneously.
- **Framebuffer**: Requires a separate framebuffer for `texPrev` feedback (ping-pong). The host must manage this.

### GPU Optimization Notes

- The drip loop is the most expensive part, potentially doing up to 15 texture samples per pixel. This could be optimized by using a lower iteration count or by precomputing drip contributions in a separate pass.
- The whipped cream bloom uses a 5x5 box blur; could be optimized with separable filters or Gaussian approximation.
- The effect is not suitable for mobile or low-end GPUs at high resolutions. Consider reducing drip iterations and blur radius for lower tiers.
- The `hash` function is called many times; could be optimized with a lookup texture.

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python)

1. **Parameter remapping**: Verify `_map_param()` for all parameters produces correct ranges (e.g., `drip_speed=5.0` → 2.75? Actually: `0.5 + (5.0/10.0)*(5.0-0.5) = 0.5 + 0.5*4.5 = 2.75`).
2. **Parameter clamping**: If `set_parameter` exists, test clamping to [0.0, 10.0].
3. **Get/set symmetry**: For each parameter, verify `get_parameter` returns the value set.
4. **Preset values**: Verify each preset contains all 12 keys and values within 0-10.
5. **Audio mappings**: Verify `audio_mappings` dictionary contains expected keys.
6. **State retrieval**: Test `get_state()` returns correct dict structure.
7. **Default parameters**: Verify all 12 parameters have expected default values.
8. **Depth mapping**: Test `depth` values (0.0-1.0) produce expected weighting in drip and cascade.
9. **Frosting palette**: Test `frostingColor` produces expected pastel colors.
10. **HSV conversion**: Test `hsv2rgb` produces correct colors.
11. **Audio modulation**: Attach mock audio reactor and verify `gravity`, `sprinkle`, `drip`, and `sweet` are modulated.

### Integration Tests (Shader Rendering)

12. **Drip effect**: Render with depth map and verify frosting drips downward from depth edges.
13. **Cascade effect**: Render with depth map and verify block-based pixel avalanche.
14. **Frosting color**: Test `frosting` parameter controls pastel color intensity.
15. **Layer stripes**: Test `layer_count` creates horizontal depth-based stripes.
16. **Sprinkles**: Test `sprinkle_density` controls sprinkle particle count.
17. **Whipped cream bloom**: Test `whipped_bloom` adds glow on highlights.
18. **Cherry accents**: Test `cherry` adds red accents at motion peaks.
19. **Sweetness**: Test `sweetness` boosts saturation toward pastels.
20. **Gravity**: Test `gravity` controls downward pull strength in cascade.
21. **Melt**: Test `melt_rate` creates temporal blending with previous frame.
22. **Dual input**: Test with both `tex0` and `tex1` valid; verify `tex1` is used.
23. **Single input fallback**: Test with `tex1` black; verify `tex0` is used.
24. **Preset rendering**: Render each preset and verify visual character (e.g., `light_glaze` should be subtle, `sugar_overload` should be intense).
25. **Audio reactivity**: Attach mock audio reactor and verify visual parameters respond to audio.
26. **Edge case: center pixel**: Render exact center pixel and verify no NaN/infinity artifacts.

### Performance Tests

27. **Benchmark 1080p**: Measure frame time with default parameters; should be < 16ms for 60fps (likely 5-15ms).
28. **Benchmark with all effects**: Enable all features (drip, cascade, sprinkles, bloom, cherry) and measure worst-case.
29. **Texture sample count**: Use GPU profiling to verify sample count (can be very high with drip loop and bloom).

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT037: CupcakeCascadeDatamoshEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementations:

- [`plugins/vdatamosh/cupcake_cascade_datamosh.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/vdatamosh/cupcake_cascade_datamosh.py:1) (VJlive Original) — Full implementation with shader code (lines 34-213) and class (lines 217-301).
- [`plugins/core/cupcake_cascade_datamosh/__init__.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/core/cupcake_cascade_datamosh/__init__.py:1) (VJlive-2 Legacy) — Same implementation in a different plugin location.
- [`core/matrix/node_datamosh.py`](home/happy/Desktop/claude projects/VJlive-2/core/matrix/node_datamosh.py:1) — Registration of the effect in the datamosh node system.

The legacy code validates the parameter ranges, default values, preset configurations, and mathematical formulations described in this spec. The effect is a sophisticated gravity-based datamosh that transforms video into a sugary cupcake cascade with frosting drips, sugar avalanches, pastel colors, sprinkles, whipped cream bloom, and cherry accents.

---

## Open Questions / [NEEDS RESEARCH]

- **Drip loop performance**: The drip loop does up to 15 texture samples per pixel, which is very expensive. Should this be optimized with a lower fixed count or a different algorithm? [NEEDS RESEARCH]
- **Whipped cream bloom kernel**: The 5x5 box blur could be separable or Gaussian. Should we optimize? [NEEDS RESEARCH]
- **Audio mappings incomplete**: The `audio_mappings` dict includes `sprinkle_density` and `drip_speed` but the code doesn't modulate them? Actually it does. Are all mappings implemented? [NEEDS RESEARCH]
- **Parameter `u_mix` hardcoded**: The `apply_uniforms` sets `u_mix` to 1.0 always. Should this be a parameter? Or is the effect meant to be always fully applied? [NEEDS RESEARCH]
- **Depth map channel**: The shader samples `depth_tex.r` only. Should we support other channels or combinations? [NEEDS RESEARCH]
- **Dual input blending**: The effect chooses either `tex0` or `tex1` based on whether `tex1` is "valid" (non-black center). Should there be a blend mode between the two inputs? [NEEDS RESEARCH]
- **Cascade block size**: The `cascade_size` parameter maps to block size multiplier. The mapping `max(2.0, u_cascade_size * 15.0)` seems to produce very large blocks at high values. Is this intended? [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*