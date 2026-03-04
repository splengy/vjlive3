# P3-EXT125 — PerlinEffect

**Specification Status:** 🟩 COMPLETING PASS 2  
**Agent:** desktop-roo  
**Date:** 2026-03-04  
**Tier:** Pro-Tier Native  
**Phase:** Pass 2 — Fleshed Out  

---

## Task: P3-EXT125 — PerlinEffect

### What This Module Does

`PerlinEffect` generates procedural Perlin noise textures in real-time. Perlin noise is a gradient noise function developed by Ken Perlin that produces smooth, natural-looking random patterns. The effect implements classic Perlin noise with multiple octaves, allowing for fractal-like detail at different scales.

The effect is categorized as a **generator** effect, meaning it creates visual content from mathematical functions rather than processing existing video. It can be used as a standalone texture source or mixed with other video effects via the `u_mix` parameter.

Key capabilities:
- Multi-octave Perlin noise with configurable persistence
- Ridging and turbulence modifiers for different noise characteristics
- Color hue shifting for palette variation
- Time-based animation for evolving patterns
- Seamless integration with VJLive3's effect pipeline

### What This Module Does NOT Do

- Does NOT generate simplex noise (different algorithm)
- Does NOT perform audio analysis or react to audio inputs (though parameters can be modulated)
- Does NOT create 3D volumetric noise (2D only)
- Does NOT include domain warping or fBM (fractal Brownian motion) beyond basic octaves
- Does NOT handle texture caching or pre-computation (pure real-time generation)

---

## Detailed Behavior and Parameter Interactions

### Overview

The effect uses a fragment shader that computes Perlin noise for each pixel based on UV coordinates and time. The noise value (typically in range [-1, 1] or [0, 1]) is then mapped to a color output, optionally with hue shifting.

The shader implements:
1. **Gradient noise**: Random gradient vectors at grid points, interpolated
2. **Octave layering**: Multiple noise frequencies combined with persistence
3. **Ridging**: Absolute value transformation for sharp ridges
4. **Turbulence**: Domain distortion using additional noise
5. **Color mapping**: Noise value → color with optional hue shift

### Parameters

| Parameter | WGSL Uniform | Range | Default | Audio Source | Description |
|-----------|--------------|-------|---------|--------------|-------------|
| `speed` | `u_speed` | 0.0–10.0 | 0.6 | None | Animation speed (time multiplier). Higher values make noise evolve faster. |
| `scale` | `u_scale` | 0.1–100.0 | 2.0 | None | Base noise frequency. Higher values = finer detail (zoomed out). |
| `octaves` | `u_octaves` | 1.0–8.0 | 5.0 | None | Number of noise layers. More octaves = more detail but higher GPU cost. |
| `persistence` | `u_persistence` | 0.1–1.0 | 0.5 | None | Amplitude reduction per octave. Controls roughness (lower = smoother). |
| `ridging` | `u_ridging` | 0.0–1.0 | 0.0 | None | Apply `abs(noise)` to create sharp ridges instead of smooth blobs. |
| `turbulence` | `u_turbulence` | 0.0–1.0 | 0.0 | None | Domain warping amount. Distorts UV coordinates with additional noise. |
| `color_hue` | `u_color_hue` | 0.0–1.0 | 0.0 | None | Hue rotation for color output. 0 = default grayscale, 1 = full hue cycle. |
| `u_mix` | `u_mix` | 0.0–1.0 | 1.0 | None | Blend factor with background video (if composited). |

### Parameter Interactions

- **Octaves + Persistence**: Together control the fractal appearance. Typical values: octaves=5, persistence=0.5 gives balanced detail. Higher octaves with low persistence create fine-grained texture; high persistence creates dominant low-frequency patterns.
- **Scale + Speed**: Scale affects spatial frequency; speed affects temporal frequency. They are independent but both influence perceived complexity.
- **Ridging + Turbulence**: Can be combined for dramatic, sharp, warped patterns. Ridging creates peaks; turbulence adds swirl distortion.
- **Color Hue**: Applied after noise generation; can be animated independently for psychedelic color cycling.

---

## Public Interface

### Class: `PerlinEffect`

**Inherits from:** `Effect` (base class for all VJLive3 effects)

**Metadata:**
```python
METADATA = {
    "spec": "P3-EXT125",
    "tier": "Pro-Tier Native",
    "version": "1.0.0",
    "category": "generators",
    "tags": ["noise", "procedural", "perlin", "fractal"]
}
```

**Constructor:**
```python
def __init__(self) -> None:
    """Initialize Perlin noise generator with default parameters."""
```

**Key Methods:**

- `get_fragment_shader() -> str`  
  Returns WGSL fragment shader implementing Perlin noise with octaves, ridging, turbulence, and color mapping.

- `apply_uniforms(time, resolution, audio_reactor=None, semantic_layer=None) -> None`  
  Dispatches all parameters to GPU via `self.set_uniform(name, value)`.  
  No audio reactivity in base implementation (parameters are static unless modulated by host).

- `get_state() -> Dict[str, Any]`  
  Serializes current parameter values for preset saving/loading.

**Uniforms Set:**
- `u_speed` (float)
- `u_scale` (float)
- `u_octaves` (float, cast to int in shader)
- `u_persistence` (float)
- `u_ridging` (float)
- `u_turbulence` (float)
- `u_color_hue` (float)
- `u_mix` (float)
- `u_time` (float, inherited from base)
- `u_resolution` (vec2<f32>, inherited from base)

---

## Inputs and Outputs

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `tex0` | `texture_2d<f32>` | Background video (optional; used for mixing) |
| `samp` | `sampler` | Linear filtering sampler |

**Note:** PerlinEffect is a generator and does not require input textures for its core noise computation. The `tex0` input is only used when blending with background video via `u_mix`.

### Outputs

- **Fragment shader output** (`fragColor`): RGBA color representing the generated noise pattern
- If `u_mix < 1.0` and `tex0` provided: `fragColor = mix(noise_color, background_color, u_mix)`

### Data Flow

```
UV coordinates → Perlin noise function (with octaves) → ridging/turbulence → color mapping → output
```

The noise computation is purely mathematical; no texture lookups needed (except for optional background blend).

---

## Edge Cases and Error Handling

### Edge Cases

1. **Octaves = 0 or negative**  
   - Clamp to 1 (minimum one octave)  
   - Log warning: `"PerlinEffect: octaves must be ≥1, clamping from {value}"`

2. **Persistence > 1.0**  
   - Clamp to 1.0 (persistence > 1 causes amplitude explosion)  
   - Log warning if out-of-range

3. **Scale extremely high (e.g., 1000)**  
   - May cause aliasing artifacts due to insufficient resolution  
   - Recommend upper bound of 100.0; clamp and warn

4. **Time overflow**  
   - `u_time` may become very large; use `fract(time * speed)` or modulo to avoid floating-point precision loss  
   - Shader should use `time = fract(u_time * u_speed)` for smooth looping

5. **Ridging + low persistence**  
   - Can produce high-contrast, almost binary patterns  
   - Not an error but may be unexpected; document in spec

6. **Turbulence domain warping**  
   - Recursive noise calls can be expensive (2-3x cost)  
   - If `u_octaves > 5` and `u_turbulence > 0.5`, consider performance impact

### Error Handling

- **Shader compilation failure**: Raise `RuntimeError` with WGSL error log; fallback to simple gradient shader if available
- **Invalid uniform types**: Catch `ValueError` when setting uniforms; log error but continue
- **Memory allocation**: No dynamic memory; all buffers are static

---

## Mathematical Formulations

### Classic Perlin Noise (2D)

Perlin noise at point `p`:

```
function perlin(p):
    i = floor(p)          // grid cell integer coordinates
    f = fract(p)          // fractional part within cell
    
    // Generate pseudo-random gradient at each corner
    g00 = random_hash(i + vec2(0, 0))
    g01 = random_hash(i + vec2(0, 1))
    g10 = random_hash(i + vec2(1, 0))
    g11 = random_hash(i + vec2(1, 1))
    
    // Compute dot products between gradient and offset vectors
    d00 = dot(g00, f - vec2(0, 0))
    d01 = dot(g01, f - vec2(0, 1))
    d10 = dot(g10, f - vec2(1, 0))
    d11 = dot(g11, f - vec2(1, 1))
    
    // Smooth interpolation (using fade function)
    u = fade(f.x)
    v = fade(f.y)
    
    // Bilinear interpolation
    nx0 = mix(d00, d10, u)
    nx1 = mix(d01, d11, u)
    n = mix(nx0, nx1, v)
    
    return n  // range [-1, 1] typically
```

Where `fade(t) = t * t * t * (t * (t * 6 - 15) + 10)` (Ken Perlin's easing polynomial).

### Fractal Noise (Octaves)

```
function fractal_noise(p, octaves, persistence):
    total = 0.0
    amplitude = 1.0
    frequency = 1.0
    max_value = 0.0
    
    for i in 0..octaves:
        total += perlin(p * frequency) * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= 2.0
    
    return total / max_value  // normalize to [-1, 1]
```

### Ridging

```
if ridging > 0:
    n = abs(n)  // create ridges
    // Optionally invert: n = 1.0 - n for valleys
```

### Turbulence (Domain Warping)

```
if turbulence > 0:
    warp_offset = fractal_noise(p + vec2(123.45, 678.90), 3, 0.5) * turbulence
    p = p + warp_offset
    // Then compute noise on warped coordinates
```

### Color Mapping

```
noise_value = fractal_noise(uv * scale + time * speed, octaves, persistence)

if ridging > 0:
    noise_value = abs(noise_value)

if turbulence > 0:
    uv_warped = uv + fractal_noise(uv + offset, 3, 0.5) * turbulence
    noise_value = fractal_noise(uv_warped * scale + time * speed, octaves, persistence)

// Map to color
gray = (noise_value + 1.0) * 0.5  // [-1,1] → [0,1]

if color_hue > 0:
    hue = fract(gray * color_hue + time * 0.1)
    rgb = hsv2rgb(vec3(hue, 0.8, 0.9))
else:
    rgb = vec3(gray)

fragColor = vec4(rgb, 1.0)
```

---

## Performance Characteristics

### Computational Complexity

- **Base Perlin noise**: O(1) per pixel (constant 4 gradient evaluations, 16 dot products, multiple interpolations)
- **Octaves**: O(octaves) multiplier. 5 octaves ≈ 5× base cost.
- **Turbulence**: Adds 1-2 additional fractal_noise calls (recursive), so 2-3× cost when enabled.
- **Total**: Roughly `base_cost * octaves * (1 + 2*turbulence)` operations per fragment.

### Benchmarks (estimated, WGSL on modern GPU)

| Octaves | Turbulence | Resolution | Expected FPS (RTX 4060) | Shader Cost (relative) |
|---------|------------|------------|------------------------|-----------------------|
| 1 | 0.0 | 1920×1080 | 300+ FPS | 1× |
| 5 | 0.0 | 1920×1080 | 120–180 FPS | 5× |
| 5 | 0.5 | 1920×1080 | 60–90 FPS | 15× |
| 8 | 1.0 | 1920×1080 | 30–45 FPS | 24× |

### Optimization Strategies

1. **Octave limit**: Clamp to 8 octaves (diminishing returns beyond 8)
2. **Turbulence optimization**: Pre-warp with lower-octave noise (3 octaves) instead of full octaves
3. **Resolution scaling**: For background effects, render at ½ resolution and upscale
4. **Static frames**: If `speed = 0`, skip time-based computation and cache result (not applicable for animated use)

---

## Test Plan

### Unit Tests (Minimum 80% Coverage)

**Test 1: Parameter Defaults**  
```python
def test_default_parameters():
    effect = PerlinEffect()
    assert effect.params["speed"] == 0.6
    assert effect.params["scale"] == 2.0
    assert effect.params["octaves"] == 5.0
    assert effect.params["persistence"] == 0.5
    assert effect.params["ridging"] == 0.0
    assert effect.params["turbulence"] == 0.0
    assert effect.params["color_hue"] == 0.0
```

**Test 2: Parameter Clamping**  
```python
def test_parameter_clamping():
    effect = PerlinEffect()
    effect.params["octaves"] = 0.0  # should clamp to 1
    effect.params["persistence"] = 1.5  # should clamp to 1.0
    effect.params["scale"] = -5.0  # should clamp to 0.1 (min)
    
    effect.apply_uniforms(0.0, (1920, 1080))
    # Verify uniforms set within valid ranges
```

**Test 3: Shader Compilation**  
```python
def test_shader_compiles():
    effect = PerlinEffect()
    shader = effect.get_fragment_shader()
    assert "perlin" in shader.lower() or "fractal" in shader.lower()
    # Compile through RenderPipeline (mock or real)
    pipeline = RenderPipeline(shader, "test_perlin")
    assert pipeline is not None
```

**Test 4: Noise Output Range**  
```python
def test_noise_output_range():
    # Render a small texture and sample values
    effect = PerlinEffect()
    # ... render to framebuffer, read pixels
    # Verify all color values in [0, 1] range (no NaN/Inf)
```

**Test 5: Octave Scaling**  
```python
def test_octave_effect():
    effect1 = PerlinEffect()
    effect1.params["octaves"] = 1.0
    effect2 = PerlinEffect()
    effect2.params["octaves"] = 5.0
    
    # Render both; effect2 should have more high-frequency detail
    # Compare variance or FFT of output textures
```

**Test 6: Ridging Transformation**  
```python
def test_ridging():
    effect = PerlinEffect()
    effect.params["ridging"] = 1.0
    # Verify output has more high-contrast peaks than non-ridged version
```

**Test 7: Turbulence Distortion**  
```python
def test_turbulence():
    effect = PerlinEffect()
    effect.params["turbulence"] = 0.8
    # Verify output is visibly warped compared to turbulence=0
```

**Test 8: Color Hue Cycling**  
```python
def test_color_hue():
    effect = PerlinEffect()
    effect.params["color_hue"] = 0.0  # grayscale
    effect.params["color_hue"] = 1.0  # full hue cycle
    # Verify hue=0 produces grayscale, hue=1 produces colored output
```

**Test 9: Mix Parameter**  
```python
def test_mix():
    effect = PerlinEffect()
    effect.params["u_mix"] = 0.0  # full noise
    effect.params["u_mix"] = 1.0  # full background
    # Render with background texture; verify blend
```

**Test 10: Time Animation**  
```python
def test_time_animation():
    effect = PerlinEffect()
    effect.params["speed"] = 1.0
    # Render at t=0 and t=1; should be different (animated)
```

### Integration Tests

- **Test with audio modulation**: Connect `AudioReactor` and modulate `speed` or `scale` via audio features
- **Test resolution independence**: Render at 1080p and 4K; noise should scale correctly with `u_resolution`
- **Test performance**: 1000 frames at 1920×1080 with octaves=5 should average >60 FPS on target hardware

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT125: PerlinEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### VJlive (Original) Implementation

**File:** `core/effects/legacy_trash/generators.py` (lines 721–756)  
**Registration:** `core/effects/__init__.py` (generators category)  
**Class:** `PerlinEffect(Effect)`

The original implementation used GLSL and followed this pattern:

```python
class PerlinEffect(Effect):
    """Perlin noise — gradient noise with ridging, billowing, turbulence."""

    def __init__(self):
        super().__init__("perlin", PERLIN_FRAGMENT)
        self.parameters = {
            "speed": 0.6,
            "scale": 2.0,
            "octaves": 5.0,
            "persistence": 5.0,  # Note: legacy used 5.0, but typical is 0.5
            "ridging": 0.0,
            "turbulence": 0.0,
            "color_hue": 0.0,
        }
```

**Key differences for VJLive3:**
- Convert GLSL → WGSL
- Parameter `persistence` in legacy appears mis-scaled (5.0); VJLive3 should use [0.1–1.0] range
- Add proper uniform struct and `apply_uniforms()` method
- Integrate with `RenderPipeline` and `Effect` base class
- Ensure `u_mix` parameter for blending with background

### Related Effects

- **P6-GE06** `FractalGenerator` — similar fractal noise pattern, may share code
- **P6-GE08** `NoiseEffect` — simpler noise (white/value noise) for comparison
- **P6-GE09** `VoronoiEffect` — cellular noise, different algorithm
- **P6-GE10** `GradientEffect` — linear gradient generator (simplest generator)

---

## Implementation Notes for Phase 3

1. **Shader language**: WGSL (WebGPU). Implement Perlin noise using hash functions and smooth interpolation.
2. **Hash function**: Use a pseudo-random hash like `fract(sin(dot(coord, vec2(12.9898, 78.233))) * 43758.5453)` in WGSL.
3. **Octave loop**: Use WGSL `for` loop with `loop {}` or unroll up to 8 octaves.
4. **Performance**: Avoid recursion; turbulence can be implemented with a separate lower-resolution noise call.
5. **Uniform naming**: Follow convention `u_<parameter>`; all floats except `u_resolution` (vec2).
6. **Time handling**: Use `u_time` from base class; multiply by `u_speed` inside shader.
7. **Color output**: Default to grayscale; apply HSV→RGB conversion when `u_color_hue > 0`.

---

**End of Spec**  
✅ Ready for Phase 3 implementation
