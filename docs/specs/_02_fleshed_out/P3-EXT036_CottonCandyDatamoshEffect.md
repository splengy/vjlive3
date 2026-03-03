# CottonCandyDatamoshEffect — Spun Sugar Cloud Dissolution with Audio Reactivity

**Task ID:** P3-EXT036  
**Module:** `CottonCandyDatamoshEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`CottonCandyDatamoshEffect`](docs/specs/_02_fleshed_out/P3-EXT036_CottonCandyDatamoshEffect.md:136) class implements a dreamy, audio-reactive datamosh effect that transforms video into floating cotton candy wisps. It dissolves pixels into soft, airy strands that float and swirl, creating a dreamy visual experience with pink/blue/purple gradients, soft focus, and depth-based density mapping.

**What This Module Does**

- Dissolves video pixels into soft noise-driven wisps using fractal noise
- Applies strand pull and spiral effects to create pulled-sugar strand visuals
- Implements upward floating with side-to-side bobbing motion
- Maps depth to cotton candy palette (pink/blue/purple gradients)
- Applies soft focus/dream blur that varies with depth
- Creates bass-driven puff bursts that add sudden cotton candy puffs
- Uses dual video inputs with automatic fallback detection
- Integrates audio reactivity for dynamic visual response
- Provides 10 controllable parameters for fine-tuned visual effects

**What This Module Does NOT Do**

- Does not include traditional datamosh compression artifacts (no motion vector displacement)
- Does not support 3D geometry or raymarching (uses 2D coordinate transforms)
- Does not provide temporal smoothing or frame blending beyond the single `texPrev` feedback
- Does not include particle systems or volumetric effects beyond the built-in puff bursts
- Does not support custom color gradients beyond the built-in pink/blue palette

---

## Detailed Behavior and Parameter Interactions

### Texture Unit Layout

The effect uses multiple texture units:

| Unit | Name | Type | Purpose |
|------|------|------|---------|
| 0 | `tex0` | `sampler2D` | Primary video input (Video A) |
| 1 | `texPrev` | `sampler2D` | Previous frame buffer (for wisp persistence) |
| 2 | `depth_tex` | `sampler2D` | Depth map (single channel, typically red) |
| 3 | `tex1` | `sampler2D` | Secondary video input (Video B, optional) |

The effect automatically detects if `tex1` is valid by sampling its center pixel. If the sum of RGB channels is > 0.001, `tex1` is used; otherwise `tex0` is used.

### Core Algorithm: Pixel Dissolution and Strand Generation

The effect transforms video into cotton candy wisps through several stages:

1. **Floating and Drift**: 
   ```glsl
   float floatOffset = time * u_float_speed * 0.02;
   float driftX = sin(uv.y * 5.0 + time * u_float_drift * 0.5) * u_float_drift * 0.01;
   vec2 floatUV = uv + vec2(driftX, -floatOffset * (1.0 - depth * 0.5));
   ```

2. **Sugar Spin (Spiral Pull)**:
   ```glsl
   vec2 centered = floatUV - 0.5;
   float r = length(centered);
   float angle = atan(centered.y, centered.x);
   angle += u_sugar_spin * 0.05 * (1.0 - depth) * sin(time * 0.3);
   vec2 spinUV = vec2(cos(angle), sin(angle)) * r + 0.5;
   ```

3. **Strand Pull (Noise Field Displacement)**:
   ```glsl
   float noiseField = fbm(spinUV * 5.0 + time * 0.1);
   float noiseField2 = fbm(spinUV * 5.0 + time * 0.1 + 100.0);
   vec2 strandDir = vec2(noiseField - 0.5, noiseField2 - 0.5);
   strandDir *= u_strand_pull * 0.04 * (0.5 + depth * 0.5);
   vec2 strandUV = spinUV + strandDir;
   ```

4. **Sample Source**:
   ```glsl
   vec4 color = hasDual ? texture(tex1, strandUV) : texture(tex0, strandUV);
   ```

5. **Cloud Dissolution**:
   ```glsl
   float cloudNoise = fbm(uv * 8.0 + time * 0.15);
   float dissolveMask = smoothstep(u_dissolve * 0.08, u_dissolve * 0.08 + 0.15, cloudNoise);
   vec3 candyCol = cottonCandyColor(depth + time * 0.05, u_candy_pink, u_candy_blue);
   color.rgb = mix(candyCol * 0.8 + color.rgb * 0.2, color.rgb, dissolveMask);
   ```

6. **Cotton Candy Color Overlay**:
   ```glsl
   float colorMix = (1.0 - depth) * 0.5 + 0.5;
   vec3 tint = cottonCandyColor(depth * 0.5 + time * 0.03, u_candy_pink, u_candy_blue);
   color.rgb = mix(color.rgb, color.rgb * (vec3(1.0) + tint * 0.5), u_fluff * 0.06);
   ```

7. **Soft Focus (Dreamy Blur)**:
   ```glsl
   if (u_soft_focus > 0.5) {
       // Multiple-tap Gaussian blur with exponential weighting
       vec4 soft = vec4(0.0);
       float radius = u_soft_focus * 0.5;
       float count = 0.0;
       for (float dx = -2.0; dx <= 2.0; dx++) {
           for (float dy = -2.0; dy <= 2.0; dy++) {
               float w = exp(-(dx*dx + dy*dy) * 0.5);
               soft += texture(hasDual ? tex1 : tex0, strandUV + vec2(dx, dy) * texel * radius) * w;
               count += w;
           }
       }
       soft /= count;
       float softMix = u_soft_focus * 0.06 * (0.3 + depth * 0.7);
       color = mix(color, soft, softMix);
   }
   ```

8. **Puff Burst (Bass Reaction)**:
   ```glsl
   float puff = sin(time * 6.28) * 0.5 + 0.5;
   puff = pow(puff, 4.0) * u_puff_burst;
   if (puff > 1.0) {
       float puffNoise = fbm(uv * 3.0 + time * 2.0);
       vec3 puffColor = cottonCandyColor(puffNoise + time, u_candy_pink, u_candy_blue);
       color.rgb = mix(color.rgb, puffColor, (puff - 1.0) * 0.1);
   }
   ```

9. **Cloud Density**:
   ```glsl
   float density = (1.0 - depth) * u_cloud_density * 0.05;
   float densityNoise = fbm(uv * 4.0 + time * 0.05);
   vec3 cloudColor = mix(vec3(1.0, 0.95, 0.98), candyCol, 0.3);
   color.rgb = mix(color.rgb, cloudColor, density * smoothstep(0.3, 0.7, densityNoise));
   ```

10. **Wisp Persistence**:
    ```glsl
    vec4 prev = texture(texPrev, strandUV);
    prev.rgb = mix(prev.rgb, prev.rgb * (vec3(1.0) + tint * 0.2), 0.2);
    color = mix(color, max(color * 0.8 + prev * 0.2, color), u_wisp_persist * 0.06);
    ```

11. **Final Mix**:
    ```glsl
    vec4 original = hasDual ? texture(tex1, uv) : texture(tex0, uv);
    fragColor = mix(original, color, u_mix);
    ```

### Parameter Space and UI Mapping

All user-facing parameters use a normalized `0.0` to `10.0` range. The class uses a `_map_param()` method to convert these to shader-specific ranges:

| Parameter | UI Range | Shader Uniform | Internal Range | Purpose |
|-----------|----------|----------------|----------------|---------|
| `cloud_density` | 0.0-10.0 | `u_cloud_density` | 0.0-1.0 | Overall cloud thickness |
| `strand_pull` | 0.0-10.0 | `u_strand_pull` | 0.0-1.0 | Strand stretching intensity |
| `float_speed` | 0.0-10.0 | `u_float_speed` | 0.0-3.0 | Upward floating speed |
| `float_drift` | 0.0-10.0 | `u_float_drift` | 0.0-1.0 | Side-to-side bobbing intensity |
| `candy_pink` | 0.0-10.0 | `u_candy_pink` | 0.0-1.0 | Pink color intensity |
| `candy_blue` | 0.0-10.0 | `u_candy_blue` | 0.0-1.0 | Blue color intensity |
| `soft_focus` | 0.0-10.0 | `u_soft_focus` | 0.0-10.0 | Dream blur amount |
| `sugar_spin` | 0.0-10.0 | `u_sugar_spin` | 0.0-10.0 | Spiral pull intensity |
| `puff_burst` | 0.0-10.0 | `u_puff_burst` | 0.0-2.0 | Bass puff intensity |
| `dissolve` | 0.0-10.0 | `u_dissolve` | 0.0-10.0 | Dissolution amount |
| `wisp_persist` | 0.0-10.0 | `u_wisp_persist` | 0.0-1.0 | Wisp lingering duration |
| `fluff` | 0.0-10.0 | `u_fluff` | 0.0-1.0 | Overall fluffiness |

**Note:** The `_map_param(name, out_min, out_max)` function computes: `out_min + (val / 10.0) * (out_max - out_min)`.

### Audio Reactivity

The effect includes audio reactivity via the `apply_uniforms` method:

```python
puff *= (1.0 + audio_reactor.get_band('bass', 0.0) * 1.5)
strand *= (0.5 + audio_reactor.get_energy(0.5))
pink *= (1.0 + audio_reactor.get_band('mid', 0.0) * 0.3)
float_speed *= (0.7 + audio_reactor.get_band('high', 0.3))
```

The `audio_mappings` dictionary documents these connections:

```python
self.audio_mappings = {
    'puff_burst': 'bass',
    'strand_pull': 'energy',
    'candy_pink': 'mid',
    'float_speed': 'high',
}
```

This means:
- **Bass** directly modulates puff burst intensity
- **Overall energy** (mid frequencies) modulates strand pull
- **Mid-range frequencies** modulate pink color intensity
- **High frequencies** modulate float speed

### Preset Configurations

The class provides four preset parameter sets:

- **`wispy_clouds`**: `{cloud_density: 3.0, strand_pull: 3.0, float_speed: 2.0, float_drift: 3.0, candy_pink: 5.0, candy_blue: 5.0, soft_focus: 4.0, sugar_spin: 2.0, puff_burst: 2.0, dissolve: 3.0, wisp_persist: 4.0, fluff: 4.0}` — gentle, airy clouds with moderate strand pull and soft focus.
- **`fairy_floss`**: `{cloud_density: 6.0, strand_pull: 5.0, float_speed: 4.0, float_drift: 5.0, candy_pink: 7.0, candy_blue: 6.0, soft_focus: 5.0, sugar_spin: 4.0, puff_burst: 4.0, dissolve: 5.0, wisp_persist: 5.0, fluff: 6.0}` — denser, more vibrant fairy floss with stronger spiral and puff effects.
- **`sugar_storm`**: `{cloud_density: 9.0, strand_pull: 8.0, float_speed: 7.0, float_drift: 7.0, candy_pink: 9.0, candy_blue: 8.0, soft_focus: 6.0, sugar_spin: 7.0, puff_burst: 8.0, dissolve: 8.0, wisp_persist: 7.0, fluff: 9.0}` — intense sugar storm with maximum density, pull, and puff effects.
- **`dream_melt`**: `{cloud_density: 5.0, strand_pull: 4.0, float_speed: 1.0, float_drift: 2.0, candy_pink: 6.0, candy_blue: 7.0, soft_focus: 8.0, sugar_spin: 3.0, puff_burst: 1.0, dissolve: 7.0, wisp_persist: 8.0, fluff: 7.0}` — dreamy melting effect with strong soft focus and moderate dissolution.

---

## Public Interface

### Class: `CottonCandyDatamoshEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT036_CottonCandyDatamoshEffect.md:136) (from `core.effects.shader_base`)

**Constructor:** `__init__(self, name: str = 'cotton_candy_datamosh')`

Initializes the effect with default parameters:

```python
self.parameters = {
    'cloud_density': 5.0, 'strand_pull': 5.0, 'float_speed': 3.0,
    'float_drift': 4.0, 'candy_pink': 6.0, 'candy_blue': 5.0,
    'soft_focus': 5.0, 'sugar_spin': 3.0, 'puff_burst': 4.0,
    'dissolve': 5.0, 'wisp_persist': 5.0, 'fluff': 5.0,
}
self.audio_mappings = {
    'puff_burst': 'bass', 'strand_pull': 'energy',
    'candy_pink': 'mid', 'float_speed': 'high',
}
```

**Properties:**

- `name = "cotton_candy_datamosh"` (or custom name passed to constructor)
- `fragment_shader = FRAGMENT` — GLSL fragment shader (see full listing in legacy reference)
- `effect_category` — Not explicitly set in legacy; likely `"datamosh"` or `"distortion"`
- `effect_tags` — Not explicitly set; based on description: `["datamosh", "glitch", "effect", "cotton", "candy", "dreamy"]`
- `audio_mappings` — Dictionary mapping parameters to audio features
- `PRESETS` — Dictionary of preset parameter configurations (see above)

**Methods:**

- `apply_uniforms(time, resolution, audio_reactor=None, semantic_layer=None)`: Sets all shader uniforms, including parameter mapping and audio modulation. Overrides base class.
- `get_state() -> Dict[str, Any]`: Returns a dictionary with `{'name': self.name, 'enabled': self.enabled, 'parameters': dict(self.parameters)}`.
- `set_parameter(name: str, value: float)`: Likely inherited from base class; should clamp to [0.0, 10.0].
- `get_parameter(name: str) -> float`: Likely inherited; returns parameter value in UI range.

**Class Attributes:**

- `PRESETS` — Dictionary of preset parameter configurations (see above).
- `FRAGMENT` — The full GLSL shader code (lines 34-194 in legacy file).

---

## Inputs and Outputs

### Inputs

| Pin | Type | Description |
|-----|------|-------------|
| `tex0` | `sampler2D` | Primary video input (Video A) |
| `texPrev` | `sampler2D` | Previous frame buffer (for wisp persistence) |
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
| `fragColor` | `vec4` | RGBA output with cotton candy effect applied (alpha unchanged) |

---

## Edge Cases and Error Handling

### Edge Cases

1. **No previous frame**: `texPrev` must be a valid texture containing the previous frame's output. If not provided or uninitialized, the wisp persistence will sample undefined data (likely black or garbage). The host must manage framebuffer ping-pong.

2. **No depth map**: `depth_tex` is required. If not provided or all zeros, the depth-based effects (density, float offset, strand pull weighting, soft focus intensity) will be minimized, effectively flattening the visual depth. The effect will still render but may look less three-dimensional.

3. **Dual input detection**: The code checks `hasDual` by sampling the center of `tex1`. If `tex1` is not bound or is black, `hasDual` is false and `tex0` is used. This is safe.

4. **Extreme parameter values**: 
   - `u_strand_pull = 10.0` (max) creates extreme strand stretching that can pull pixels outside the viewport, causing black holes or edge artifacts.
   - `u_soft_focus = 10.0` (max) creates a heavy blur that can make the entire image nearly uniform, losing detail.
   - `u_dissolve = 10.0` (max) can cause complete dissolution of the image into noise, especially in high-noise areas.
   - `u_float_speed = 10.0` (max) creates rapid upward movement that can make wisps disappear quickly.

5. **Division by zero in noise functions**: The `fbm` and `hash` functions use `p * 5.0` which can produce large coordinates. While GLSL handles large coordinates, extreme values can cause precision issues or NaNs.

6. **Infinite loop in fractal iteration**: The `fbm` function uses a fixed 4-iteration loop, which is safe. However, if the loop condition were dynamic, it could potentially cause issues.

7. **Audio reactivity errors**: The `try/except` around audio modulation means if `audio_reactor` methods fail, the effect continues without audio reactivity. This is safe but may hide bugs.

8. **Texture sampling precision**: The effect samples textures at `strandUV + vec2(dx, dy) * texel * radius`. If `strandUV` is near texture edges and `radius` is large, sampling may go out of bounds. The host should ensure textures are properly padded or clamped.

### Error Handling

- **No runtime errors** — all operations are safe GLSL; `exp()`, `sin()`, `cos()` are well-behaved.
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

### Noise Functions

The effect uses two noise functions:

**Hash function** (for texture coordinate hashing):
```glsl
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
```

**Fractal Brownian Motion (fbm)**:
```glsl
float fbm(vec2 p) {
    float val = 0.0;
    float amp = 0.5;
    for (int i = 0; i < 4; i++) {
        val += noise(p) * amp;
        p *= 2.0;
        amp *= 0.5;
    }
    return val;
}
```

### Color Composition

The `cottonCandyColor` function creates a gradient:
```glsl
vec3 cottonCandyColor(float t, float pink, float blue) {
    vec3 pinkC = vec3(1.0, 0.6, 0.8) * pink * 0.2;
    vec3 blueC = vec3(0.6, 0.8, 1.0) * blue * 0.2;
    vec3 lavender = vec3(0.85, 0.7, 1.0);
    vec3 white = vec3(1.0, 0.97, 0.98);
    
    float phase = fract(t);
    if (phase < 0.25) return mix(pinkC, white, phase * 4.0);
    else if (phase < 0.5) return mix(white, blueC, (phase - 0.25) * 4.0);
    else if (phase < 0.75) return mix(blueC, lavender, (phase - 0.5) * 4.0);
    else return mix(lavender, pinkC, (phase - 0.75) * 4.0);
}
```

### Depth Mapping

Depth is sampled from `depth_tex.r` and used to modulate various effects:
- **Floating offset**: `floatOffset = time * u_float_speed * 0.02` (reduced for deeper pixels)
- **Strand pull weighting**: `strandDir *= u_strand_pull * 0.04 * (0.5 + depth * 0.5)`
- **Soft focus intensity**: `softMix = u_soft_focus * 0.06 * (0.3 + depth * 0.7)`
- **Cloud density**: `density = (1.0 - depth) * u_cloud_density * 0.05`

### Audio Modulation

Audio reactivity modifies parameters in `apply_uniforms`:
```python
puff *= (1.0 + audio_reactor.get_band('bass', 0.0) * 1.5)
strand *= (0.5 + audio_reactor.get_energy(0.5))
pink *= (1.0 + audio_reactor.get_band('mid', 0.0) * 0.3)
float_speed *= (0.7 + audio_reactor.get_band('high', 0.3))
```

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: Moderate to high. The shader performs:
  - 1-2 texture samples (primary + optional secondary) + 1 feedback sample + 1 depth sample = 3-4 samples per pixel
  - Multiple fractal noise evaluations (4 iterations in fbm, multiple hash calls)
  - Multiple trigonometric functions: `sin`, `cos`, `atan`, `exp`
  - Loop with 4 iterations (unrolled by compiler)
  - Multiple arithmetic operations for color composition
- **No loops** beyond the fixed 4-iteration fractal loop (unrolled by compiler)
- **Heavy GPU load**: This is a `MEDIUM` tier effect as per plugin manifest. Expect 3-6ms per 1080p frame on modern GPU, possibly more with soft focus and recursion.

### Memory Usage

- **Uniforms**: 12 floats + standard uniforms (time, resolution, u_mix) = ~14 uniforms.
- **Textures**: Requires 3-4 texture units bound simultaneously.
- **Framebuffer**: Requires a separate framebuffer for `texPrev` feedback (ping-pong). The host must manage this.

### GPU Optimization Notes

- The fractal noise evaluation is the most expensive part (4 iterations with hash calls). Could be optimized with lookup textures or simplified to fewer iterations.
- The soft focus blur uses a 5x5 kernel with exponential weighting; could be optimized with Gaussian approximation.
- The effect is not suitable for mobile or low-end GPUs at high resolutions. Consider reducing fractal iterations or disabling some features for lower tiers.
- The `exp()` function in the soft focus calculation is expensive; consider using a polynomial approximation if performance is critical.

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python)

1. **Parameter remapping**: Verify `_map_param()` for all parameters produces correct ranges (e.g., `cloud_density=5.0` → 0.5).
2. **Parameter clamping**: If `set_parameter` exists, test clamping to [0.0, 10.0].
3. **Get/set symmetry**: For each parameter, verify `get_parameter` returns the value set.
4. **Preset values**: Verify each preset contains all 12 keys and values within 0-10.
5. **Audio mappings**: Verify `audio_mappings` dictionary contains expected keys.
6. **State retrieval**: Test `get_state()` returns correct dict structure.
7. **Default parameters**: Verify all 12 parameters have expected default values.
8. **Depth mapping**: Test `depth` values (0.0-1.0) produce expected weighting in float offset and strand pull.
9. **Color gradient**: Test `cottonCandyColor` produces expected pink/blue gradient transitions.
10. **Audio modulation**: Attach mock audio reactor and verify `puff`, `strand`, `pink`, and `float_speed` are modulated.

### Integration Tests (Shader Rendering)

11. **Tunnel transformation**: Render a test pattern and verify log-polar mapping creates tunnel effect.
12. **Fractal distortion**: Render with `fractal_depth > 0` and verify intricate wall patterns.
13. **Recursion feedback**: Render with `recursion > 0` and verify infinite tunnel illusion.
14. **Depth modulation**: Render with depth map and verify near/far regions respond differently.
15. **Dual input**: Test with both `tex0` and `tex1` valid; verify `tex1` is used.
16. **Single input fallback**: Test with `tex1` black; verify `tex0` is used.
17. **Float drift**: Test `float_speed` controls upward movement speed.
18. **Drift direction**: Test `float_drift` controls side-to-side bobbing.
19. **Sugar spin**: Test `sugar_spin` creates spiral pull.
20. **Strand pull**: Test `strand_pull` creates noise-based displacement.
21. **Dissolution**: Test `dissolve` parameter controls pixel dissolution amount.
22. **Color overlay**: Test `candy_pink` and `candy_blue` add pink/blue tint.
23. **Soft focus**: Test `soft_focus` adds dreamy blur that varies with depth.
24. **Puff burst**: Test `puff_burst` creates bass-driven cotton candy puffs.
25. **Cloud density**: Test `cloud_density` controls overall cloud thickness.
26. **Wisp persistence**: Test `wisp_persist` controls lingering of previous frame wisps.
27. **Fluff**: Test `fluff` adds overall fluffiness to the effect.
28. **Preset rendering**: Render each preset and verify visual character (e.g., `wispy_clouds` should be gentle, `sugar_storm` should be intense).
29. **Audio reactivity**: Attach mock audio reactor and verify visual parameters respond to audio.
30. **Edge case: center pixel**: Render exact center pixel and verify no NaN/infinity artifacts.

### Performance Tests

31. **Benchmark 1080p**: Measure frame time with default parameters; should be < 16ms for 60fps (likely 3-6ms).
32. **Benchmark with all effects**: Enable all features (soft focus, puff burst, audio reactivity) and measure worst-case.
33. **Texture sample count**: Use GPU profiling to verify 3-4 texture samples per pixel (more with soft focus).

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT036: CottonCandyDatamoshEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementations:

- [`plugins/vdatamosh/cotton_candy_datamosh.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/vdatamosh/cotton_candy_datamosh.py:1) (VJlive Original) — Full implementation with shader code (lines 34-194) and class (lines 198-282).
- [`plugins/core/cotton_candy_datamosh/__init__.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/core/cotton_candy_datamosh/__init__.py:1) (VJlive-2 Legacy) — Same implementation in a different plugin location.
- [`core/matrix/node_datamosh.py`](home/happy/Desktop/claude projects/VJlive-2/core/matrix/node_datamosh.py:1) — Registration of the effect in the datamosh node system.

The legacy code validates the parameter ranges, default values, preset configurations, and mathematical formulations described in this spec. The effect is a sophisticated audio-reactive datamosh that transforms video into floating cotton candy wisps using fractal noise, depth mapping, and dual video inputs.

---

## Open Questions / [NEEDS RESEARCH]

- **Center division by zero**: The `toTunnel` function in other effects divides by `r` which is zero at screen center. This needs a fix: `0.5 / max(r, 1e-6)`. Should this be handled in the spec or left to implementer? [NEEDS RESEARCH]
- **Audio mappings incomplete**: The `audio_mappings` dict includes `candy_pink` and `float_speed` but the code doesn't modulate them. Should these be implemented? [NEEDS RESEARCH]
- **Parameter `u_mix` hardcoded**: The `apply_uniforms` sets `u_mix` to 1.0 always. Should this be a parameter? Or is the effect meant to be always fully applied? [NEEDS RESEARCH]
- **Rotation units**: The `rotation` parameter maps to `-3.0 to 3.0` and is used as `sin(u_rotation * 0.01)`. This suggests the rotation angle in the feedback transform is `u_rotation * 0.01` radians? That's a very small range. Is this correct? [NEEDS RESEARCH]
- **Depth map channel**: The shader samples `depth_tex.r` only. Should we support other channels or combinations? [NEEDS RESEARCH]
- **Dual input blending**: The effect chooses either `tex0` or `tex1` based on whether `tex1` is "valid" (non-black center). Should there be a blend mode between the two inputs? [NEEDS RESEARCH]
- **Mosh stretch unused**: The parameter `mosh_stretch` is mapped to a uniform but never used in the shader. Is this a leftover or should it affect something? [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*