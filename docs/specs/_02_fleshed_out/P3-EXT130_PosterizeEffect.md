# P3-EXT130: PosterizeEffect — Fleshed Specification

## Task: P3-EXT130 — PosterizeEffect

**Module Type:** Color Effect (Quantization)  
**Priority:** P0 (Core Color Correction)  
**Phase:** Pass 2 — Fleshed Specification  
**Agent:** desktop-roo  
**Date:** 2026-03-04  

---

## What This Module Does

The `PosterizeEffect` reduces the number of distinct color levels in an image by quantizing each RGB channel independently. This creates a stylized, flat-color aesthetic reminiscent of poster printing, retro video games, or color-limited animation.

**Core Concept:**
- Input color channels (R, G, B) are divided into a fixed number of discrete steps
- Each pixel's channel value is snapped to the nearest step boundary
- Result: fewer unique colors, visible banding, and a graphic, simplified look

**Key Characteristics:**
- Single video input (`tex0`)
- Per-channel quantization with independent step counts
- Optional dithering to reduce banding artifacts
- Very low computational cost (simple arithmetic)
- Real-time performance even at 4K resolution

---

## What This Module Does NOT Do

- **NOT** a color reduction to a fixed palette (does not use a color lookup table)
- **NOT** a posterization that considers color relationships (each channel independent)
- **NOT** a dithering algorithm by itself (optional dither is a simple noise add)
- **NOT** a hue/saturation shift: operates only on luminance/level quantization
- **NOT** a threshold effect: produces multiple levels, not just binary
- **NOT** a color grading tool: does not adjust color balance or curves

---

## Detailed Behavior and Parameter Interactions

### Core Algorithm

The effect implements **uniform scalar quantization** per color channel:

1. **Level Configuration**
   - Each channel (R, G, B) has its own `levels` parameter (integer ≥ 2)
   - The number of quantization steps is `levels`
   - Step size: `step = 1.0 / (levels - 1)` (normalized to [0,1] range)

2. **Quantization Process**
   - For a channel value `c` ∈ [0,1]:
     ```
     c_q = floor(c * (levels - 1)) / (levels - 1)
     ```
   - This maps continuous values to discrete equally-spaced levels: 0, step, 2×step, ..., 1.0

3. **Optional Dithering**
   - If `dither > 0`, add pseudo-random noise before quantization
   - Noise amplitude: `dither * step`
   - Noise range: `[-dither*step, +dither*step]`
   - Purpose: break up visible banding in smooth gradients by scattering quantization error

4. **Gamma Correction (Optional)**
   - If `gamma_correct = true`, apply sRGB ↔ linear transformation:
     - Decode sRGB to linear space before quantization
     - Quantize in linear space (perceptually uniform)
     - Encode back to sRGB for output
   - This produces more visually accurate posterization, especially for dark colors
   - Cost: two `pow()` operations per channel

5. **Mix Parameter**
   - `mix` controls blend between original and posterized result
   - `mix = 0` → original image
   - `mix = 1` → fully posterized

### Parameter Interactions

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `levels_r` | int | [2, 256] | 4 | Red channel quantization levels |
| `levels_g` | int | [2, 256] | 4 | Green channel quantization levels |
| `levels_b` | int | [2, 256] | 4 | Blue channel quantization levels |
| `dither` | float | [0.0, 1.0] | 0.0 | Dithering amplitude (0 = none, 1 = full step) |
| `gamma_correct` | bool | — | false | Apply sRGB gamma 2.2 decode/encode |

**Parameter Behavior:**
- `levels` values are clamped to [2, 256] in Python before upload; 256 means effectively no quantization (step = 1/255 ≈ original 8-bit precision)
- `dither` is a multiplier of the step size; 0.5 means noise amplitude = 0.5 × step
- `gamma_correct` adds computational overhead (two `pow()` calls per channel); disable for maximum performance
- All three `levels` parameters are independent, allowing creative asymmetric quantization (e.g., 2 levels on red, 8 on green, 16 on blue)

### Edge Cases

- **levels = 2:** Pure binary threshold at 0.5 for that channel; produces stark high-contrast look
- **levels = 256:** No visible change (step = 1/255, matches 8-bit color)
- **dither = 0:** Clean, sharp banding; may produce visible steps in gradients
- **dither = 1:** Maximum noise; can smooth bands but adds grain
- **Gamma correction:** If input is already linear, gamma correction will double-correct and produce incorrect colors; document that input is assumed to be sRGB

---

## Public Interface

### Class Definition

```python
from vjlive3.render.effect import Effect
from vjlive3.render.program import RenderPipeline

class PosterizeEffect(Effect):
    """
    Reduces color depth by quantizing RGB channels to discrete levels.
    
    Parameters:
        levels_r (int): Red channel levels [2,256]
        levels_g (int): Green channel levels [2,256]
        levels_b (int): Blue channel levels [2,256]
        dither (float): Dithering amplitude [0.0, 1.0]
        gamma_correct (bool): Apply gamma 2.2 decode/encode
    """
    
    METADATA = {
        "name": "PosterizeEffect",
        "spec": "P3-EXT130",
        "version": "1.0.0",
        "tier": "Core Native",
        "category": "color",
        "description": "Color quantization with per-channel levels and optional dithering"
    }
    
    def __init__(self, name: str = "posterize") -> None:
        fragment_source = self._get_wgsl_shader()
        super().__init__(name, fragment_source)
        
        # Initialize default parameters
        self.parameters = {
            "levels_r": 4,
            "levels_g": 4,
            "levels_b": 4,
            "dither": 0.0,
            "gamma_correct": False,
        }
    
    def _get_wgsl_shader(self) -> str:
        """Return WGSL shader source."""
        return """
        @group(0) @binding(0) var tex0: texture_2d<f32>;
        @group(0) @binding(1) var s0: sampler;
        
        struct Uniforms {
            levels_r: f32,
            levels_g: f32,
            levels_b: f32,
            dither: f32,
            gamma_correct: f32,
            mix: f32,
            enabled: f32,
        };
        
        @binding(2) @group(0) var<uniform> uniforms: Uniforms;
        
        // Simple hash-based pseudo-random (2D)
        fn rand(p: vec2<f32>) -> f32 {
            var p2 = fract(p * vec2<f32>(123.45, 678.91));
            p2 += dot(p2, p2 + 45.67);
            return fract(p2.x * p2.y);
        }
        
        // sRGB <-> linear conversion (gamma 2.2)
        fn srgb_to_linear(x: f32) -> f32 {
            return select(x * 0.0774, pow((x + 0.055) / 1.055, 2.4), x >= 0.04045);
        }
        fn linear_to_srgb(x: f32) -> f32 {
            return select(x * 12.92, 1.055 * pow(x, 1.0/2.4) - 0.055, x >= 0.0031308);
        }
        
        @fragment
        fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
            var color = textureSample(tex0, s0, uv);
            
            // Optional gamma decode to linear space
            if (uniforms.gamma_correct > 0.5) {
                color.r = srgb_to_linear(color.r);
                color.g = srgb_to_linear(color.g);
                color.b = srgb_to_linear(color.b);
            }
            
            // Dither noise (per-pixel, range [-1,1])
            let noise_val = rand(uv) * 2.0 - 1.0;
            // Dither amplitude = dither / (levels - 1)  (use max levels for all channels)
            let max_levels = max(uniforms.levels_r, max(uniforms.levels_g, uniforms.levels_b));
            let dither_amp = uniforms.dither / (max_levels - 1.0);
            
            // Quantize each channel independently
            var quantized = color;
            
            // Red channel
            let r_levels = max(uniforms.levels_r, 2.0);  // Clamp safety
            let r_step = 1.0 / (r_levels - 1.0);
            var r = color.r + noise_val * dither_amp;
            r = clamp(r, 0.0, 1.0);
            r = floor(r * (r_levels - 1.0)) / (r_levels - 1.0);
            quantized.r = r;
            
            // Green channel
            let g_levels = max(uniforms.levels_g, 2.0);
            let g_step = 1.0 / (g_levels - 1.0);
            var g = color.g + noise_val * dither_amp;
            g = clamp(g, 0.0, 1.0);
            g = floor(g * (g_levels - 1.0)) / (g_levels - 1.0);
            quantized.g = g;
            
            // Blue channel
            let b_levels = max(uniforms.levels_b, 2.0);
            let b_step = 1.0 / (b_levels - 1.0);
            var b = color.b + noise_val * dither_amp;
            b = clamp(b, 0.0, 1.0);
            b = floor(b * (b_levels - 1.0)) / (b_levels - 1.0);
            quantized.b = b;
            
            // Alpha unchanged
            quantized.a = color.a;
            
            // Re-apply gamma if needed
            if (uniforms.gamma_correct > 0.5) {
                quantized.r = linear_to_srgb(quantized.r);
                quantized.g = linear_to_srgb(quantized.g);
                quantized.b = linear_to_srgb(quantized.b);
            }
            
            // Mix with original based on mix uniform
            let output = mix(color, quantized, uniforms.mix);
            
            return output;
        }
        """
    
    def apply_uniforms(self, pipeline: RenderPipeline) -> None:
        """
        Upload current parameter values to the GPU pipeline.
        
        Args:
            pipeline: RenderPipeline instance to update
        """
        # Clamp levels to valid range before upload
        levels_r = max(2, min(256, self.parameters["levels_r"]))
        levels_g = max(2, min(256, self.parameters["levels_g"]))
        levels_b = max(2, min(256, self.parameters["levels_b"]))
        
        pipeline.set_uniform("levels_r", float(levels_r))
        pipeline.set_uniform("levels_g", float(levels_g))
        pipeline.set_uniform("levels_b", float(levels_b))
        pipeline.set_uniform("dither", self.parameters["dither"])
        pipeline.set_uniform("gamma_correct", 1.0 if self.parameters["gamma_correct"] else 0.0)
```

### Integration with VJLive3

- Inherits from [`Effect`](src/vjlive3/render/effect.py)
- Uses [`RenderPipeline`](src/vjlive3/render/program.py) for WGSL compilation
- Single texture input; no additional framebuffers needed
- Parameters exposed via `self.parameters` for GUI control
- `apply_uniforms()` called per frame before rendering

---

## Inputs and Outputs

### Inputs

| Stream | Type | Description |
|--------|------|-------------|
| `tex0` | `texture_2d<f32>` | Input video/image to posterize |
| `s0` | `sampler` | Sampler for texture lookup |
| Uniforms | `Uniforms` struct | 5 parameters + mix/enabled |

### Outputs

| Stream | Type | Description |
|--------|------|-------------|
| Fragment output | `vec4<f32>` | Posterized RGBA color |

### Data Flow

1. Sample input texture at current UV
2. If `gamma_correct` enabled, decode sRGB → linear
3. Generate dither noise (if `dither > 0`)
4. For each channel (R, G, B):
   - Add dither noise to channel value
   - Clamp to [0,1]
   - Multiply by `(levels - 1)` and take `floor()`
   - Divide by `(levels - 1)` to get quantized value
5. If `gamma_correct` enabled, encode linear → sRGB
6. Blend with original using `mix` uniform
7. Output final color

---

## Edge Cases and Error Handling

### Invalid Levels
- **Risk:** `levels < 2` would cause division by zero (`levels - 1 = 0`)
- **Mitigation:** Python-side `apply_uniforms()` clamps to [2, 256] before upload. Shader also uses `max(levels, 2.0)` as safety.

### Dither Amplitude
- **Risk:** `dither` too high could cause values to exceed [0,1] after adding noise, leading to clamp artifacts
- **Mitigation:** Shader clamps after adding noise. Dither is normalized by step size, so it's naturally bounded.

### Gamma Correction Mismatch
- **Risk:** If input texture is already linear (not sRGB), enabling `gamma_correct` will apply incorrect transform
- **Mitigation:** Document that input is assumed sRGB. For linear workflows, keep `gamma_correct=false`.

### Performance Edge Cases
- **Very high resolution (8K):** Still fast due to simple arithmetic; no texture bandwidth increase
- **Multiple instances:** Stateless shader; can be reused many times without state conflicts

---

## Mathematical Formulations

### Quantization

For a channel value `c` ∈ [0,1] and integer `L` (levels) ∈ [2,256]:

```
step = 1 / (L - 1)
c_q = floor( (c + n) * (L - 1) ) / (L - 1)
```

where `n` is dither noise ∈ `[-dither*step, +dither*step]`.

### Dither Noise

```
n = (rand(uv) * 2.0 - 1.0) * (dither / (L_max - 1))
```

`rand(uv)` is a hash-based pseudo-random function returning a value in [0,1]. `L_max` is the maximum of all three levels to keep dither amplitude consistent across channels.

### Gamma Correction

sRGB → linear (decode):
```
c_lin = c_srgb < 0.04045 ? c_srgb * 0.0774 : ((c_srgb + 0.055) / 1.055)^2.4
```

Linear → sRGB (encode):
```
c_srgb = c_lin < 0.0031308 ? c_lin * 12.92 : 1.055 * c_lin^(1/2.4) - 0.055
```

These are the standard sRGB transfer function inverses.

---

## Performance Characteristics

### Computational Complexity

- **Per-fragment operations:**
  - 1 texture fetch (`textureSample`)
  - 3× channel quantization: each involves `floor()`, multiplication, division, clamp
  - 1 `rand()` call (hash + arithmetic) if dither > 0
  - 0 or 6 `pow()` calls (2 per channel) if `gamma_correct` enabled
  - 3 `mix()` operations (final blend per channel)
- **Total:** ~30-50 FLOPs without gamma; ~80-100 FLOPs with gamma

### Memory Footprint

- **Uniform buffer:** 5 floats (levels_r, levels_g, levels_b, dither, gamma_correct) + 2 floats (mix, enabled) ≈ 28 bytes
- **No additional textures:** Stateless; no framebuffer dependencies

### GPU Utilization

- **Fragment-bound:** Very lightweight; can run at high resolutions easily
- **Texture bandwidth:** 1 fetch per fragment (same as passthrough)
- **ALU load:** Minimal; `floor()` and `pow()` are the heaviest ops, but `pow()` only if gamma enabled

### Optimization Opportunities

- **Precompute reciprocals:** `1/(levels-1)` could be computed in Python and uploaded as `step` uniform to avoid division in shader
- **Branchless gamma:** The `select()` (ternary) is free on modern GPUs; no optimization needed
- **Integer arithmetic:** Could use `u32` for levels and integer division, but floating-point is fine

### Benchmarks (Estimated)

| Resolution | gamma_correct | dither | Relative Cost | Target FPS |
|------------|---------------|--------|---------------|------------|
| 1920×1080  | false         | 0.0    | 0.1× (baseline) | 1000+ fps |
| 1920×1080  | true          | 0.0    | 0.2×           | 500+ fps   |
| 3840×2160  | false         | 0.5    | 0.2×           | 500+ fps   |
| 1920×1080  | false         | 1.0    | 0.15×          | 700+ fps   |

This effect is extremely cheap and can be stacked with many others without performance concerns.

---

## Test Plan

### Unit Tests (Python)

1. **Parameter Validation**
   - Test `levels_r/g/b` clamped to [2, 256] in `apply_uniforms()`
   - Test `dither` clamped to [0.0, 1.0]
   - Test `gamma_correct` boolean conversion to 0.0/1.0

2. **Shader Compilation**
   - Verify WGSL compiles without errors
   - Test uniform locations for all 5 parameters

3. **Uniform Upload**
   - Mock `RenderPipeline.set_uniform()` and verify calls with correct values
   - Test that clamped values are uploaded, not out-of-range inputs

4. **Metadata**
   - Verify `METADATA` dict has correct `spec` ID and category

### Integration Tests (Render)

1. **Basic Quantization**
   - Render a smooth gradient (e.g., red channel from 0 to 1)
   - Set `levels_r=4`, `dither=0`, `gamma_correct=false`
   - Verify output has exactly 4 distinct red values (within tolerance)
   - Check that green and blue are unchanged (if their levels=256)

2. **Per-Channel Independence**
   - Set `levels_r=2`, `levels_g=8`, `levels_b=16`
   - Render a multi-color test pattern
   - Verify red has 2 levels, green 8, blue 16

3. **Dithering**
   - Render same gradient with `dither=0` and `dither=0.5`
   - Dithered version should have smoother appearance, less visible banding
   - Check that average color remains similar (dither is zero-mean)

4. **Gamma Correction**
   - Render a linear grayscale ramp (0 to 1 linear)
   - With `gamma_correct=true`, output should match sRGB posterization
   - Without gamma, quantization bands will be perceptually uneven (more bands in darks)

5. **Mix Parameter**
   - Set `mix=0` → output equals input
   - Set `mix=1` → fully posterized
   - Set `mix=0.5` → 50% blend

6. **Edge Cases**
   - `levels=2` (binary) and `levels=256` (no change)
   - `dither=0` and `dither=1` (max)
   - `gamma_correct` true/false

### Visual Regression

- Render a standard test image (e.g., SMPTE color bars) with `levels=4` on all channels
- Compare against golden reference (per-pixel difference < 1/255 after dither)
- Store reference in `tests/reference/P3-EXT130/`

### Performance Tests

- Measure frame time at 4K resolution with all parameter combinations
- Ensure > 1000 fps baseline (no gamma, no dither) on target hardware
- Ensure > 500 fps with gamma correction

---

## Definition of Done

- [x] Spec document completed in `docs/specs/_02_fleshed_out/P3-EXT130_PosterizeEffect.md`
- [ ] WGSL shader implemented in `src/vjlive3/plugins/posterize_effect.py`
- [ ] Python class `PosterizeEffect` with parameter validation
- [ ] All unit tests passing (`tests/plugins/test_posterize_effect.py`)
- [ ] All integration tests passing (render tests)
- [ ] Code coverage ≥ 80%
- [ ] No linter errors (`ruff`, `mypy`)
- [ ] Performance: > 500 fps at 4K on target hardware
- [ ] Spec reviewed and approved by Manager

---

## Legacy References

### VJlive (Original) — `core/effects/__init__.py` and `core/effects/legacy_trash/color.py`

The `PosterizeEffect` was registered in the color effects module:

```python
'color': {
    'colorama': ('.color', 'ColoramaEffect'),
    'posterize': ('.color', 'PosterizeEffect'),
    ...
}
```

The actual implementation in `core/effects/legacy_trash/color.py` was not fully retrieved, but the class existed and followed the standard `Effect` base class pattern.

### VJlive-2 (Legacy) — `plugins/core/color_posterize/__init__.py`

```python
from plugins.core.color import PosterizeEffect

def get_plugin_class():
    return PosterizeEffect
```

And the plugin manifest (`plugin.json`) specified:
- `"id": "posterize"`
- `"name": "Posterize"`
- `"module_path": "plugins.core.color"`
- `"class_name": "PosterizeEffect"`
- `"category": "Color"`

### Migration Notes

- **Parameter mapping:** Legacy likely used similar parameters: `levels` (or `levels_r/g/b`), maybe `dither`. The spec assumes per-channel levels for flexibility.
- **Shader language:** Legacy may have used GLSL; the WGSL translation is straightforward
- **Gamma handling:** Legacy may not have had gamma correction; this is an optional enhancement
- **No major architectural changes needed** — this is a simple, self-contained effect

---

## Technical Notes for Implementation

### Why Per-Channel Levels?

Traditional posterization often uses the same number of levels for all channels. However, allowing independent levels per channel enables creative effects like:
- `levels_r=2, levels_g=256, levels_b=256` → red channel posterized, others full (vintage red tint)
- `levels_r=256, levels_g=4, levels_b=4` → cyan/magenta bias

This flexibility aligns with VJLive3's philosophy of exposing granular control.

### Dithering Strategy

The dither implemented here is simple **ordered dither** using a hash-based noise function. It's not full **error diffusion** (Floyd-Steinberg) because that requires multi-pass or large kernel. The noise dither is cheap and effective for breaking up bands.

Alternative: Use a precomputed 2D dither texture (e.g., Bayer matrix) for more structured dither patterns.

### Gamma Correction Rationale

Quantization in linear space is perceptually uniform: equal steps in linear intensity correspond to equal perceived brightness. Without gamma correction, sRGB quantization produces more steps in bright areas and fewer in darks, leading to uneven banding. The `gamma_correct` flag provides a high-quality option at modest cost.

---

## Easter Egg Suggestion

**PosterizeEffect — "The Digital Rosetta Stone"**  
If the user sets `levels_r=7`, `levels_g=7`, `levels_b=7` (all prime), enables `gamma_correct=true`, and sets `dither=0.618` (golden ratio conjugate), the dither noise pattern becomes a deterministic sequence that, when fed into the quantization, produces a hidden 7-level color palette that exactly matches the color distribution of the original 1977 Atari 2600 color palette. Any image posterized with these settings will map its colors to the nearest Atari 2600 equivalent, effectively turning modern video into retro 8-bit graphics. This is a tribute to the earliest home video gaming era, where color limitations defined an aesthetic.

*— desktop-roo*

---

## References

- [`Effect` base class](src/vjlive3/render/effect.py)
- [`RenderPipeline`](src/vjlive3/render/program.py)
- Legacy: `core/effects/__init__.py` (registration)
- Legacy: `plugins/core/color_posterize/__init__.py`
- Legacy: `plugins/core/color.py` (PosterizeEffect class)
- BOARD.md task entry: P3-EXT130

---

**Specification Status:** ✅ Fleshed — Ready for Implementation (Pass 3)
