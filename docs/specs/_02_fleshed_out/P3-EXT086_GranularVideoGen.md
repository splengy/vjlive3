# P3-EXT086 — GranularVideoGen

## Executive Summary

**GranularVideoGen** is a video generator that implements granular synthesis principles in the visual domain. It scatters overlapping grain particles across the screen, each sampling from an input texture at a specific location. The collective effect reconstructs the input image through a cloud of fragments, creating a pointillist, dreamlike, or pixelated aesthetic depending on parameters. This effect is part of the VCV Rack → Video generator family, translating the Mutable Instruments Clouds concept (granular audio synthesis) into video processing.

**Category:** Generator/Effect hybrid (requires tex0 input for meaningful output)  
**Legacy Location:** `core/effects/vcv_generators.py` (lines 568-620)  
**Shader Type:** GLSL 330 core fragment shader  
**Presets:** 5 (soft_cloud, pointillist, frozen_grains, dense_scatter, sparse_bokeh)

---

## Detailed Behavior and Parameter Interactions

### Overview

GranularVideoGen breaks the input video into a cloud of small grain particles. Each grain:
- Has a random position within a scatter radius around a central `position` parameter
- Samples the input texture at a location determined by its birth position and a small random offset
- Has a finite lifespan (birth → fade out)
- Contributes to the final color via weighted accumulation

The result is a dynamic, particle-based reconstruction of the input that can range from soft, cloud-like overlays to sharp, pointillist mosaics.

### Parameter System

All parameters use the standard 0.0–10.0 UI rail, remapped internally to shader-specific ranges.

1. **density** (0-10 → 4-64 grains)
   - Controls the number of grain particles active simultaneously
   - Higher values increase computational cost linearly (loop iterations)
   - Presets: soft_cloud=5, pointillist=8, frozen_grains=6, dense_scatter=10, sparse_bokeh=3

2. **grain_size** (0-10 → 0.02-0.32 normalized UV)
   - Size of each grain particle in UV space
   - Smaller values create finer pointillist effects; larger values create bokeh-like blobs
   - Grain shape: smooth Gaussian (exp(-d²)) or sharp circle (step) based on `texture_param`

3. **position** (0-10 → 0-1 UV)
   - Central spawn position for grain cloud on the texture
   - Grains scatter around this point with `spread` amplitude
   - Default 5.0 = center (0.5, 0.5) in UV space

4. **texture_param** (0-10 → 0-1)
   - Controls grain texture sharpness: 0 = smooth Gaussian, 10 = sharp circular
   - Also affects grain envelope smoothness
   - Presets: soft_cloud=0 (smooth), pointillist=8 (sharp), frozen_grains=3

5. **spread** (0-10 → 0-0.5 UV)
   - Spatial scatter radius around `position`
   - Higher values disperse grains over a larger area
   - Presets: soft_cloud=5 (0.25), pointillist=7 (0.35), dense_scatter=9 (0.45)

6. **freeze** (0-10 → 0-1)
   - Time freeze factor: 0 = normal motion, 10 = nearly frozen
   - Scales time: `t = time * (1.0 - frz * 0.9)`
   - When frozen, grain birth times and phases become static, creating a still image
   - Presets: frozen_grains=8 (80% freeze)

7. **color_scatter** (0-10 → 0-1)
   - Per-grain color randomization amount
   - Adds hue shift to each grain's sampled color
   - Creates chromatic dispersion or pointillist color variation
   - Presets: pointillist=3 (0.3), dense_scatter=5 (0.5)

### Core Algorithm

```glsl
// Remap UI parameters
int nGrains = 4 + int(density / 10.0 * 60.0);  // 4-64
float gSize = 0.02 + grain_size / 10.0 * 0.3;   // 0.02-0.32
float pos = position / 10.0;                     // 0-1
float tex_sharp = texture_param / 10.0;           // 0-1
float spr = spread / 10.0 * 0.5;                 // 0-0.5
float frz = freeze / 10.0;                       // 0-1
float csc = color_scatter / 10.0;                // 0-1

float t = time * (1.0 - frz * 0.9);  // time scaling

vec3 acc = vec3(0.0);
float totalWeight = 0.0;

for (int i = 0; i < 64; i++) {
    if (i >= nGrains) break;

    float fi = float(i);
    float seed = hash1(fi + 0.1);  // pseudo-random per-grain seed

    // Grain lifecycle
    float lifespan = 0.3 + seed * 2.0;           // 0.3-2.3 seconds
    float birthTime = fi * 0.1 + seed * 3.0;    // staggered births
    float phase = mod(t - birthTime, lifespan) / lifespan;  // 0-1 normalized age

    // Grain position: scatter around central `pos`
    vec2 grainCenter = vec2(
        pos + (hash(vec2(fi, 0.0)) - 0.5) * spr * 2.0,
        0.5 + (hash(vec2(fi, 1.0)) - 0.5) * spr * 2.0
    );

    // Subtle motion over lifetime
    grainCenter += vec2(
        sin(t * 0.5 + fi) * 0.02,
        cos(t * 0.3 + fi * 1.7) * 0.02
    );

    // Distance from current pixel to grain center
    float d = length(p - grainCenter) / gSize;

    // Envelope: fade in/out using sine wave (0 at birth/death, 1 at midlife)
    float env = sin(phase * 3.14159);

    // Grain shape: smooth Gaussian or sharp circle
    float grain = mix(
        exp(-d * d * 3.0),      // Gaussian: exp(-3*d²)
        step(d, 1.0),            // Sharp: 1 inside circle, 0 outside
        tex_sharp
    );

    grain *= env;  // apply lifecycle envelope

    // Sample input texture at grain's "source" position (slightly offset)
    vec2 samplePos = grainCenter + (hash(vec2(fi, 2.0)) - 0.5) * 0.1;
    samplePos = clamp(samplePos, 0.0, 1.0);
    vec3 grainColor = texture(tex0, samplePos).rgb;

    // Color scatter: add small random hue shift
    float hueShift = (hash(vec2(fi, 3.0)) - 0.5) * csc * 0.3;
    grainColor = grainColor + vec3(hueShift, -hueShift * 0.5, hueShift * 0.3);

    // Accumulate weighted color
    acc += grainColor * grain;
    totalWeight += grain;
}

// Normalize by total weight (avoid division by zero)
vec3 result = totalWeight > 0.01 ? acc / totalWeight : vec3(0.0);
result = clamp(result, 0.0, 1.0);

// Mix with original
fragColor = mix(original, vec4(result, 1.0), u_mix / 10.0);
```

### Mix Behavior

`u_mix` controls blending between input texture and granular output:
- `u_mix = 0`: output = original (grains invisible)
- `u_mix = 10`: output = pure granular reconstruction
- Intermediate values create composite overlay

---

## Public Interface

### Class: `GranularVideoGen`

**Inherits from:** `Effect` (shader_base.py)  
**Category:** `"generator"` (but requires tex0 input for meaningful output)  
**Tags:** `["generator", "granular", "particles", "clouds"]`

### Constructor

```python
def __init__(self):
    super().__init__("granular_video", GRANULAR_VIDEO_FRAGMENT)
    self.parameters = {
        'density': 5.0,
        'grain_size': 5.0,
        'position': 5.0,
        'texture_param': 0.0,
        'spread': 5.0,
        'freeze': 0.0,
        'color_scatter': 0.0,
    }
    for p in self.parameters:
        self.set_parameter_range(p, 0.0, 10.0)
```

### Methods

- `set_parameter(name: str, value: float)` — Set parameter value (clamped to [0, 10])
- `get_parameter(name: str) -> float` — Retrieve current parameter value
- `apply_uniforms(time_val: float, resolution: tuple, audio_reactor=None, semantic_layer=None)` — Upload uniforms to shader
- `get_parameter_range(name: str) -> Optional[Tuple[float, float]]` — Return (min, max) for parameter

### Presets

```python
PRESETS = {
    "soft_cloud":    {"density": 5.0, "grain_size": 5.0, "position": 5.0, "texture_param": 0.0, "spread": 5.0, "freeze": 0.0, "color_scatter": 0.0},
    "pointillist":   {"density": 8.0, "grain_size": 2.0, "position": 5.0, "texture_param": 8.0, "spread": 7.0, "freeze": 0.0, "color_scatter": 3.0},
    "frozen_grains": {"density": 6.0, "grain_size": 4.0, "position": 3.0, "texture_param": 3.0, "spread": 4.0, "freeze": 8.0, "color_scatter": 0.0},
    "dense_scatter": {"density": 10.0, "grain_size": 3.0, "position": 5.0, "texture_param": 5.0, "spread": 9.0, "freeze": 0.0, "color_scatter": 5.0},
    "sparse_bokeh":  {"density": 3.0, "grain_size": 8.0, "position": 5.0, "texture_param": 0.0, "spread": 6.0, "freeze": 2.0, "color_scatter": 1.0},
}
```

---

## Inputs and Outputs

### Inputs

- **tex0** (sampler2D): Source texture to sample from. This effect **requires** a valid texture bound to produce meaningful output. If tex0 is black or uninitialized, the result will be black.
- **resolution** (vec2): Viewport resolution in pixels
- **time** (float): Global time in seconds
- **u_mix** (float): Blend amount between input and granular output (0-10)

### Outputs

- **fragColor** (vec4): RGBA color. Alpha is always 1.0 in the granular result; when mixing, the alpha is effectively 1.0 but color is blended.

### Data Flow

```
[Uniforms: time, resolution, u_mix, 7 parameters]
         ↓
[Fragment Shader: GranularVideoGen]
  1. Remap UI parameters to shader ranges
  2. Compute time with freeze factor
  3. For each grain (up to 64, break when i >= nGrains):
     a. Generate pseudo-random seed from hash functions
     b. Compute grain lifecycle (birthTime, lifespan, phase)
     c. Determine grain center position (scatter around `position`)
     d. Add subtle motion offset
     e. Compute distance from current pixel to grain center
     f. Calculate grain envelope (sin(phase*π))
     g. Compute grain shape (Gaussian or sharp circle)
     h. Sample tex0 at grain's source position (with random offset)
     i. Apply color scatter (hue shift)
     j. Accumulate color * grain weight
  4. Normalize accumulated color by total weight
  5. Clamp result to [0,1]
  6. Mix with original texture using u_mix
         ↓
[Output: fragColor]
```

---

## Edge Cases and Error Handling

### Edge Cases

1. **Zero or negative resolution**: Shader assumes positive resolution; zero dimensions cause undefined behavior in aspect ratio (though not explicitly used here). The Python wrapper should validate resolution.

2. **No texture bound (tex0 = 0)**: `texture(tex0, samplePos)` returns (0,0,0,1) by GLSL spec. The granular result will be black, and mixing with original will just show the original. This is a valid use case if `u_mix` is low.

3. **Extreme density**: `density=10` → 64 grains; `density=0` → 4 grains (minimum enforced by shader). The loop always runs up to 64 iterations but breaks early. Performance scales with actual grain count due to early exit.

4. **Grain size extremes**: `grain_size=0` → 0.02 (minimum); `grain_size=10` → 0.32. Very small grains can cause aliasing; very large grains can overlap heavily, reducing effective resolution.

5. **Spread extremes**: `spread=0` → grains tightly clustered; `spread=10` → 0.5 UV spread, grains cover entire screen. Large spread with high density can cause heavy overlap and over-brightening before normalization.

6. **Freeze parameter**: `freeze=10` → time scaled by 0.1 (90% slowdown). Not truly frozen; for complete freeze, host would need to stop time updates. The effect is extremely slow motion.

7. **Color scatter overflow**: `color_scatter=10` → hue shift up to ±0.15 (since `csc * 0.3`). This can push colors outside [0,1] before clamping. The `grainColor + vec3(hueShift, -hueShift*0.5, hueShift*0.3)` may produce negative values; `clamp(result, 0.0, 1.0)` handles this.

8. **Division by zero**: `totalWeight > 0.01` check prevents division by zero. If all grains have zero weight (e.g., all grains outside screen with zero envelope), result is black.

9. **Hash function collisions**: The `hash(vec2)` and `hash1(float)` are simple and may produce correlations, but this is acceptable for visual effects.

10. **Lifespan and birth time**: `lifespan = 0.3 + seed * 2.0` ensures at least 0.3s; `birthTime = fi * 0.1 + seed * 3.0` staggers births. With `freeze=0`, grains cycle continuously. No negative time issues.

### Error Handling

- **Shader compilation**: Handled by base `Effect` class; failure raises exception with GLSL error log.
- **Uniform location**: Base class handles missing uniforms with warnings.
- **Parameter clamping**: `set_parameter()` clamps to [0, 10]; no exceptions.
- **Texture binding**: Assumes tex0 bound to unit 0; base class manages texture units.

---

## Mathematical Formulations

### Parameter Remapping

| UI Parameter | Shader Variable | Formula | Shader Range |
|--------------|-----------------|---------|--------------|
| density | nGrains | `4 + int(density / 10.0 * 60.0)` | [4, 64] |
| grain_size | gSize | `0.02 + grain_size / 10.0 * 0.3` | [0.02, 0.32] |
| position | pos | `position / 10.0` | [0, 1] |
| texture_param | tex_sharp | `texture_param / 10.0` | [0, 1] |
| spread | spr | `spread / 10.0 * 0.5` | [0, 0.5] |
| freeze | frz | `freeze / 10.0` | [0, 1] |
| color_scatter | csc | `color_scatter / 10.0` | [0, 1] |

### Grain Lifecycle

For grain `i` with seed `s`:

- **Lifespan**: `L = 0.3 + s * 2.0` seconds
- **Birth time**: `B = i * 0.1 + s * 3.0` seconds
- **Phase (normalized age)**: `φ = ((t - B) mod L) / L` ∈ [0, 1]
- **Envelope**: `E = sin(φ * π)` — sinusoidal fade in/out, peaks at midlife

### Grain Position

- **Base center**: `(pos, 0.5)` in UV coordinates
- **Scatter**: `Δx = (hash(i,0) - 0.5) * spr * 2.0`, `Δy = (hash(i,1) - 0.5) * spr * 2.0`
- **Motion offset**: `(sin(t*0.5 + i)*0.02, cos(t*0.3 + i*1.7)*0.02)`
- **Final center**: `C = (pos + Δx, 0.5 + Δy) + motion_offset`

### Grain Shape

- **Distance**: `d = length(p - C) / gSize` (normalized by grain size)
- **Gaussian**: `G = exp(-d² * 3.0)`
- **Sharp circle**: `S = step(d, 1.0)`
- **Blend**: `grain = mix(G, S, tex_sharp)`
- **Final weight**: `w = grain * E`

### Color Sampling

- **Sample position**: `S = C + (hash(i,2) - 0.5) * 0.1` (clamped to [0,1])
- **Base color**: `C_base = texture(tex0, S).rgb`
- **Hue shift**: `h = (hash(i,3) - 0.5) * csc * 0.3`
- **Shifted color**: `C_shift = C_base + vec3(h, -h*0.5, h*0.3)`
- **Accumulation**: `acc += C_shift * w`, `totalWeight += w`

### Final Output

```
result = (totalWeight > 0.01) ? acc / totalWeight : vec3(0.0)
result = clamp(result, 0.0, 1.0)
fragColor = mix(original, vec4(result, 1.0), u_mix / 10.0)
```

---

## Performance Characteristics

### Computational Cost

- **Loop iterations:** Up to 64 per fragment, but early exit when `i >= nGrains`. Average iterations = `nGrains / 2` (if density uniformly distributed).
- **Arithmetic:** ~100 FLOPs per grain (hash, position, envelope, shape, sampling math)
- **Texture fetches:** 1 per grain (sampling tex0) + 1 for original texture in mix
- **Hash functions:** 4 per grain (2D hash for position, 1D for seed, 2D for sample offset, 2D for hue shift)
- **Trigonometry:** 2 `sin`, 1 `cos` per grain (motion offset)
- **Branching:** Loop with break; inside loop, no branches except `mix` (conditional blend)

### Memory Footprint

- **Uniforms:** 10 floats + 1 sampler2D
  - time, resolution (vec2), u_mix
  - 7 parameters: density, grain_size, position, texture_param, spread, freeze, color_scatter
- **Shader code size:** ~3.5 KB (fragment shader string)
- **No framebuffer feedback:** Pure feed-forward

### Bottlenecks

1. **Texture bandwidth:** Each grain samples tex0 once. With density=10 (64 grains), that's 64 texture fetches per fragment, plus the final mix fetch. This is extremely expensive and will be texture-bandwidth bound.
2. **Hash function cost:** The `hash(vec2)` uses `fract(sin(dot(...)) * 43758.5453)`, which involves a `dot`, `sin`, `fract`. 4 hashes per grain = many trig calls.
3. **Loop unrolling:** The loop is bounded (64), so compiler may unroll partially, but still 64× work per fragment.

### Performance Estimates

On a mid-range GPU (NVIDIA GTX 1060, AMD RX 580) at 1080p:

- **Density = 5 (≈32 grains average):** ~2-3 ms/frame (texture-bound)
- **Density = 10 (64 grains):** ~4-6 ms/frame (texture-bound, possibly exceeding 16ms budget for 60 FPS)
- **4K resolution:** Multiply by ~4× (pixel count), likely >16ms even at low density

**Conclusion:** This effect is **extremely expensive** and should be used sparingly or at lower resolutions. It is not suitable for full-screen real-time at high densities without powerful GPU.

### Optimization Opportunities

- **Reduce grain count:** The 4-64 range is already limited; further reduction needed for performance.
- **Simplify hash:** Replace `sin(dot(...))` with a faster pseudo-random function (e.g., polynomial hash).
- **Early discard:** If grain weight is near zero, skip texture fetch (but weight computed after shape, which already uses d; could compute weight before texture fetch).
- **Lower precision:** Use `mediump` floats if targeting mobile (GLSL ES).

---

## Test Plan

### Unit Tests (Python)

**Target coverage:** ≥80% of `GranularVideoGen` class methods.

**Test cases:**

1. **Constructor validation**
   - Verify `name == "granular_video"`
   - Verify all 7 parameters exist with default values
   - Verify parameter ranges set to (0.0, 10.0)
   - Verify `effect_category == "generator"`
   - Verify tags include "generator", "granular", "particles", "clouds"

2. **Parameter getters/setters**
   - Set each parameter to boundary (0, 10) and mid (5); verify `get_parameter()` returns clamped value
   - Set out-of-range values (-10, 20); verify clamped to [0, 10]

3. **Preset validation**
   - Verify each preset contains all 7 parameters
   - Verify preset values within [0, 10]
   - Apply preset and check parameters update correctly

4. **Parameter descriptions**
   - Verify `_parameter_descriptions` has entries for all 7 parameters
   - Verify descriptions are non-empty strings

5. **Chaos ratings**
   - Verify `_chaos_rating` has entries for all 7 parameters
   - Verify ratings are floats in [0, 1]

6. **Shader compilation**
   - Instantiate effect; verify no exception
   - Verify `self.shader` is not None

**Example:**
```python
class TestGranularVideoGen(unittest.TestCase):
    def test_constructor(self):
        effect = GranularVideoGen()
        self.assertEqual(effect.name, "granular_video")
        self.assertEqual(effect.effect_category, "generator")
        self.assertIn("granular", effect.effect_tags)

    def test_density_remap(self):
        effect = GranularVideoGen()
        # Test shader uniform remapping indirectly via parameter set
        effect.set_parameter('density', 0.0)
        # The shader will interpret as 4 grains; we can't test without GL context
        # But we can test that parameter is clamped
        self.assertEqual(effect.parameters['density'], 0.0)
        effect.set_parameter('density', 10.0)
        self.assertEqual(effect.parameters['density'], 10.0)
```

### Integration Tests (OpenGL)

1. **Rendering with known texture**
   - Create a test texture (e.g., solid red)
   - Set `density=10`, `grain_size=0.1`, `spread=0`, `freeze=0`
   - Render and verify output is approximately red (within tolerance)
   - Increase `spread` and verify grains scatter

2. **Density scaling**
   - Render with density=0, 5, 10; measure fragment shader execution time (via GPU timer)
   - Verify time increases roughly linearly with grain count

3. **Freeze behavior**
   - Set `freeze=10`, render two frames with increasing time
   - Compare frames; they should be nearly identical (tiny motion remains due to 0.9 factor)

4. **Color scatter**
   - Set `color_scatter=10`, render; verify color variance across grains (compute variance in output)
   - Set `color_scatter=0`, verify uniform color (if input texture uniform)

5. **Mix behavior**
   - Bind distinct texture (e.g., checkerboard), set `u_mix=0` → output checkerboard
   - Set `u_mix=10` → output granular pattern (not checkerboard)
   - Set `u_mix=5` → blended result

### Visual Regression

- Render frames at each preset
- Compare against golden images (allow small differences due to hash randomness; use statistical comparison)
- Flag large deviations (>2% pixel difference)

### Shader Compilation

- Compile `GRANULAR_VIDEO_FRAGMENT` in isolation
- Verify no GLSL errors
- Check all uniform locations are valid

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT086: GranularVideoGen` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

**Primary source:** `/home/happy/Desktop/claude projects/vjlive/core/effects/vcv_generators.py`

- Lines 400-520: `GRANULAR_VIDEO_FRAGMENT` shader string
- Lines 568-620: `GranularVideoGen` class definition

**Related test files:**

- `tests/test_vcv_generators.py` — unit tests for `GranularVideoGen` (lines 49-68)
- `core/matrix/node_effect_vcv_gen.py` — `GranularVideoNode` wrapper (type='EFFECT')
- `core/matrix/node_effect_video_gen.py` (vjlive-2) — duplicate node wrapper

**Legacy lookup snippets:** 10 code snippets covering:
- Effect registration in `__init__.py`
- Node class definitions
- Test cases
- Shader fragment

---

## Migration Considerations (WebGPU)

### WGSL Translation

The GLSL shader will need conversion to WGSL. Key aspects:

1. **Uniform bind group:**
   ```wgsl
   struct Uniforms {
       time: f32,
       resolution: vec2<f32>,
       u_mix: f32,
       density: f32,  // but remapped to int in shader
       grain_size: f32,
       position: f32,
       texture_param: f32,
       spread: f32,
       freeze: f32,
       color_scatter: f32,
   }
   @group(0) @binding(0) var<uniform> uniforms: Uniforms;
   @group(0) @binding(1) var tex0: texture_2d<f32>;
   @group(0) @binding(2) var samp0: sampler;
   ```

2. **Integer remapping:** WGSL requires explicit integer conversion. `nGrains = 4 + i32(uniforms.density / 10.0 * 60.0)`.

3. **Hash functions:** Need to reimplement `hash(vec2<f32>)` and `hash1(f32)` in WGSL using similar math (sin, dot, fract). WGSL `sin` and `fract` are available.

4. **Texture sampling:** Use `textureSample(tex0, samp0, samplePos)`.

5. **Loop bounds:** WGSL requires loop bounds to be compile-time constants or values from uniform/constant. The `for (var i: i32 = 0; i < 64; i++)` is fine; `if (i >= nGrains) break;` is allowed.

6. **Performance:** The high texture fetch count (64 per fragment) will be equally expensive on WebGPU. Consider reducing max grains for WebGPU deployment.

### WebGPU-Specific Notes

- **Bind group layout:** Ensure uniform buffer is 16-byte aligned; pad if necessary.
- **Workgroup size:** Not applicable (fragment shader).
- **Sampler:** Use linear filtering for smooth grains; nearest for sharp.

---

## Open Questions / [NEEDS RESEARCH]

- **Audio reactivity:** The `apply_uniforms` signature includes `audio_reactor=None` but the shader does not use audio data. Is audio reactivity intended? Could modulate `density`, `spread`, or `color_scatter` with audio amplitude. **Status:** [NEEDS RESEARCH]
- **Semantic layer support:** `semantic_layer` parameter is unused. Could depth or optical flow modulate grain position or size. **Status:** [NEEDS RESEARCH]
- **Generator vs Effect classification:** The class is marked `"generator"` but it samples `tex0` heavily, making it more of an effect. The node wrapper in legacy code sets `type = 'EFFECT'` for `GranularVideoNode`. This inconsistency should be resolved. **Status:** [NEEDS RESEARCH] — likely should be `"effect"` category.

---
