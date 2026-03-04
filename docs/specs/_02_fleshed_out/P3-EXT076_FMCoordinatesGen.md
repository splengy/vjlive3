# P3-EXT076 — FMCoordinatesGen

## Executive Summary

**FMCoordinatesGen** is a pure generator effect that translates FM (Frequency Modulation) audio synthesis principles into 2D coordinate warping patterns. It generates complex spatial interference patterns by simulating two FM operators (carrier and modulator) whose interaction creates intricate visual structures reminiscent of Lissajous figures and Moiré patterns. The effect is part of the VCV Rack → Video generator family, which reimagines audio synthesis concepts as parameter-driven visual generators.

**Category:** Generator (no video input required)  
**Legacy Location:** `core/effects/vcv_generators.py` (lines 250-310)  
**Shader Type:** GLSL 330 core fragment shader  
**Presets:** 5 (simple_fm, metallic, bell_tones, chaos, gentle_warp)

---

## Detailed Behavior and Parameter Interactions

### Overview

FMCoordinatesGen maps the mathematical principles of FM synthesis onto 2D spatial coordinates. Instead of generating audio waveforms, it generates visual patterns where the carrier and modulator operators warp the UV coordinate space based on distance from center and angular position. The result is a family of organic, interference-rich patterns that respond to parameter changes in ways analogous to FM audio timbre.

### Parameter System

All parameters use the standard 0.0–10.0 UI rail, internally remapped to shader-specific ranges via the `_map_param()` pattern (though this effect uses direct division in the shader). The eight parameters are:

1. **carrier_freq** (0-10 → 1-31 Hz equivalent)
   - Controls the base frequency of the carrier operator
   - Higher values create finer spatial structures
   - Interacts with mod_freq to determine pattern complexity

2. **mod_freq** (0-10 → 0.5-20.5 Hz equivalent)
   - Controls the modulator frequency
   - Creates sideband-like spatial patterns
   - Ratio with carrier_freq determines harmonic structure

3. **mod_index** (0-10 → 0-10)
   - FM modulation depth
   - Higher values increase pattern complexity and "metallic" character
   - Directly controls amplitude of frequency sidebands in spatial domain

4. **feedback** (0-10 → 0-3)
   - Operator self-modulation amount
   - Adds recursive complexity, creating fractal-like detail
   - High values can cause chaotic patterns

5. **algorithm** (0-10 → 0-1)
   - Selects operator routing topology:
     - 0.0-0.33: Serial (modulator → carrier)
     - 0.33-0.66: Parallel (independent operators mixed)
     - 0.66-1.0: Cross-modulated (mutual modulation)

6. **ratio** (0-10 → 0.5-4.5)
   - Frequency ratio between operators
   - Non-integer ratios create inharmonic, metallic textures
   - Integer ratios create harmonic, bell-like patterns

7. **brightness** (0-10 → 0.3-1.0)
   - Output brightness curve exponent: `pow(val, 1.5 - bri)`
   - Lower values (darker) increase contrast; higher values flatten response

8. **color_mode** (0-10 → 0-1)
   - 0.0-0.33: Rainbow (HSV hue from FM value)
   - 0.33-0.66: Monochrome (grayscale)
   - 0.66-1.0: Thermal (false color heatmap)

### Core Algorithm

The shader implements FM synthesis in spatial coordinates:

```glsl
// Convert UV to centered coordinates with aspect correction
vec2 p = (uv - 0.5) * 2.0;
float aspect = resolution.x / resolution.y;
p.x *= aspect;

// Polar coordinates
float dist = length(p);
float angle = atan(p.y, p.x);

// Operator 2 (modulator) generates modulation signal
float op2 = sin(dist * mf * rat + time * 2.0 + angle * 3.0);
op2 += sin(op2 * fb + time * 0.7) * fb * 0.3;  // feedback

// Operator 1 (carrier) is modulated by op2
float fm_amount = op2 * mi;

// Algorithm selection determines routing
if (alg < 0.33) {
    // Serial: op2 modulates carrier directly
    op1 = sin(dist * cf + fm_amount + time);
} else if (alg < 0.66) {
    // Parallel: both operators contribute independently
    op1 = sin(dist * cf + time) * 0.5 + sin(angle * mf + fm_amount + time * 0.5) * 0.5;
} else {
    // Cross: mutual modulation creates recursive complexity
    float op1_raw = sin(dist * cf + fm_amount + time);
    op2 += op1_raw * mi * 0.3;
    op1 = sin(dist * cf + op2 * mi + time);
}

// Final value with brightness curve
float val = op1 * 0.5 + 0.5;
val = pow(val, 1.5 - bri);
```

The pattern evolves over time via `time` uniform, creating slow morphing animations.

### Mix Behavior

The effect blends with the input texture (tex0) using the `u_mix` uniform (0-10 range):

```glsl
vec4 original = texture(tex0, uv);
fragColor = mix(original, vec4(col, 1.0), u_mix / 10.0);
```

When `u_mix = 0`, the output is the original texture unchanged. When `u_mix = 10`, the output is pure generated pattern. Intermediate values create composite overlays.

---

## Public Interface

### Class: `FMCoordinatesGen`

**Inherits from:** `Effect` (shader_base.py)  
**Category:** `"generator"`  
**Tags:** `["generator", "fm", "synthesis", "modulation"]`

### Constructor

```python
def __init__(self):
    super().__init__("fm_coordinates", FM_COORDINATES_FRAGMENT)
    self.parameters = {
        'carrier_freq': 3.0,
        'mod_freq': 5.0,
        'mod_index': 3.0,
        'feedback': 0.0,
        'algorithm': 0.0,
        'ratio': 5.0,
        'brightness': 5.0,
        'color_mode': 0.0,
    }
    for p in self.parameters:
        self.set_parameter_range(p, 0.0, 10.0)
```

### Methods

- `set_parameter(name: str, value: float)` — Set parameter value (clamped to range)
- `get_parameter(name: str) -> float` — Retrieve current parameter value
- `apply_uniforms(time_val: float, resolution: tuple, audio_reactor=None, semantic_layer=None)` — Upload uniforms to shader
- `get_parameter_range(name: str) -> Optional[Tuple[float, float]]` — Return (min, max) for parameter

### Presets

```python
PRESETS = {
    "simple_fm":       {"carrier_freq": 3.0, "mod_freq": 5.0, "mod_index": 3.0, "feedback": 0.0, "algorithm": 0.0, "ratio": 5.0, "brightness": 5.0, "color_mode": 0.0},
    "metallic":        {"carrier_freq": 7.0, "mod_freq": 7.0, "mod_index": 7.0, "feedback": 3.0, "algorithm": 5.0, "ratio": 7.0, "brightness": 6.0, "color_mode": 5.0},
    "bell_tones":      {"carrier_freq": 5.0, "mod_freq": 8.0, "mod_index": 4.0, "feedback": 1.0, "algorithm": 0.0, "ratio": 3.0, "brightness": 7.0, "color_mode": 0.0},
    "chaos":           {"carrier_freq": 9.0, "mod_freq": 9.0, "mod_index": 9.0, "feedback": 8.0, "algorithm": 10.0, "ratio": 8.0, "brightness": 4.0, "color_mode": 10.0},
    "gentle_warp":     {"carrier_freq": 2.0, "mod_freq": 3.0, "mod_index": 2.0, "feedback": 0.5, "algorithm": 3.0, "ratio": 4.0, "brightness": 8.0, "color_mode": 0.0},
}
```

---

## Inputs and Outputs

### Inputs

- **tex0** (sampler2D): Optional background texture to composite with generated pattern. If no texture bound, the shader still generates valid output (black background).
- **resolution** (vec2): Viewport resolution in pixels
- **time** (float): Global time in seconds
- **u_mix** (float): Mix amount between input texture and generated pattern (0-10)

### Outputs

- **fragColor** (vec4): RGBA color. Alpha is always 1.0 for generated patterns; when compositing, alpha is effectively 1.0 but color is mixed with tex0.

### Data Flow

```
[Uniforms: time, resolution, u_mix, 8 parameters]
         ↓
[Fragment Shader: FMCoordinatesGen]
  1. Convert UV to centered coordinates
  2. Compute polar coordinates (dist, angle)
  3. Generate modulator operator (op2) with optional feedback
  4. Generate carrier operator (op1) with FM from op2
  5. Apply algorithm-specific routing
  6. Compute final value with brightness curve
  7. Map to color via color_mode
  8. Mix with tex0 using u_mix
         ↓
[Output: fragColor]
```

---

## Edge Cases and Error Handling

### Edge Cases

1. **Zero or negative resolution**: Shader assumes positive resolution; zero dimensions cause division by zero in aspect ratio calculation. The Python wrapper should validate resolution before upload.

2. **Extreme parameter values**: Although parameters are clamped to 0-10 in Python, the shader remaps to wider ranges. Extremes (e.g., carrier_freq=10 → 31 Hz) can produce high-frequency aliasing artifacts. This is expected behavior, not an error.

3. **Feedback saturation**: When `feedback > 0`, the recursive term `sin(op2 * fb + time * 0.7) * fb * 0.3` can cause op2 to exceed [-1,1] range. The shader does not clamp op2, allowing values to grow. This is intentional for chaotic behavior but can produce numeric instability at very high feedback (8-10). The `chaos` preset pushes this boundary.

4. **Algorithm boundary conditions**: The algorithm selection uses `<` comparisons on a continuous 0-1 range. Values exactly at 0.33 or 0.66 are deterministic (first branch wins). No special handling needed.

5. **Color mode transitions**: Color mode is a continuous float; values near boundaries (0.33, 0.66) create blended color schemes that may not be intended. Users should snap to 0, 5, or 10 for clean modes.

6. **Texture binding**: If tex0 is not bound (texture unit 0 empty), `texture(tex0, uv)` returns (0,0,0,1) by GLSL spec. The mix operation then blends black with generated color, effectively darkening the output. This is a valid use case (generator as dark overlay).

7. **Time wrap**: `time` is a float that will eventually lose precision after ~24 days of continuous operation. For VJ use (hours), this is not a concern. If needed, the host should mod time to a smaller range.

### Error Handling

- **Missing shader compilation**: The Effect base class handles shader compilation errors during `__init__`. If `FM_COORDINATES_FRAGMENT` fails to compile, an exception is raised with the GLSL error log.
- **Uniform location failures**: `apply_uniforms` uses `glGetUniformLocation`. If a uniform is not found (e.g., removed from shader), the base class logs a warning but continues.
- **Parameter validation**: `set_parameter()` clamps values to the registered range (0-10). No exceptions for out-of-range values.
- **Texture unit**: Assumes tex0 is bound to unit 0. The base Effect class manages texture unit assignment.

---

## Mathematical Formulations

### Parameter Remapping

All UI parameters `p_ui ∈ [0, 10]` are remapped to shader parameters `p_sh` as follows:

| Parameter | Shader Variable | Remapping Formula | Shader Range |
|-----------|----------------|-------------------|--------------|
| carrier_freq | cf | `1.0 + p_ui / 10.0 * 30.0` | [1, 31] |
| mod_freq | mf | `0.5 + p_ui / 10.0 * 20.0` | [0.5, 20.5] |
| mod_index | mi | `p_ui / 10.0 * 10.0` | [0, 10] |
| feedback | fb | `p_ui / 10.0 * 3.0` | [0, 3] |
| algorithm | alg | `p_ui / 10.0` | [0, 1] |
| ratio | rat | `0.5 + p_ui / 10.0 * 4.0` | [0.5, 4.5] |
| brightness | bri | `0.3 + p_ui / 10.0 * 0.7` | [0.3, 1.0] |
| color_mode | cm | `p_ui / 10.0` | [0, 1] |

### FM Synthesis Mathematics

The core is a two-operator FM algorithm:

**Modulator (Operator 2):**
```
op2(t) = sin(dist * mf * rat + time * ω_m + angle * k_m) + feedback_term
feedback_term = sin(op2 * fb + time * ω_fb) * fb * 0.3
```

**Carrier (Operator 1):**
```
fm_amount = op2 * mi

Serial (alg < 0.33):
op1 = sin(dist * cf + fm_amount + time * ω_c)

Parallel (0.33 ≤ alg < 0.66):
op1 = 0.5 * sin(dist * cf + time * ω_c) + 0.5 * sin(angle * mf + fm_amount + time * 0.5)

Cross (alg ≥ 0.66):
op1_raw = sin(dist * cf + fm_amount + time)
op2 += op1_raw * mi * 0.3
op1 = sin(dist * cf + op2 * mi + time)
```

Where:
- `dist` = radial distance from center (scaled by aspect ratio)
- `angle` = polar angle `atan(p.y, p.x)`
- `cf`, `mf`, `rat` = carrier frequency, modulator frequency, frequency ratio
- `mi` = modulation index
- `fb` = feedback amount
- `ω` terms are implicit time multipliers (2.0 for modulator, 1.0 for carrier, 0.7 for feedback, 0.5 for parallel second term)

**Final value:**
```
val = op1 * 0.5 + 0.5  // map [-1,1] → [0,1]
val = pow(val, 1.5 - bri)  // brightness curve
```

### Color Mapping

**Rainbow mode (cm < 0.33):**
```
hue = fract(val + time * 0.05)
col = hsv2rgb(vec3(hue, 0.9, val))
```

**Monochrome mode (0.33 ≤ cm < 0.66):**
```
col = vec3(val)
```

**Thermal mode (cm ≥ 0.66):**
```
col = vec3(val * 1.5, val * val, val * val * val * 0.5)
col = clamp(col, 0.0, 1.0)
```

### Mix Operation

```
fragColor = mix(original, vec4(col, 1.0), u_mix / 10.0)
```

---

## Performance Characteristics

### Computational Cost

- **Arithmetic operations:** ~50 FLOPs per fragment (excluding trig functions)
- **Trigonometric functions:** 2-4 `sin()` calls per fragment (varies by algorithm)
- **Texture fetch:** 1 sample (tex0) if mixing, 0 if pure generator
- **Branching:** One `if-else` chain for algorithm selection (3 branches, mutually exclusive)
- **Looping:** None

### Memory Footprint

- **Uniforms:** 11 floats + 1 sampler2D
  - time, resolution (vec2), u_mix
  - 8 parameters: carrier_freq, mod_freq, mod_index, feedback, algorithm, ratio, brightness, color_mode
- **Shader code size:** ~3.5 KB (full fragment shader string)
- **No framebuffer feedback:** This is a feed-forward generator, no intermediate textures needed

### Bottlenecks

1. **Trigonometric functions** (`sin`, `cos` via `atan`): These are the most expensive operations. On modern GPUs, `sin` is reasonably fast but still dominates cost.
2. **Fragment shading rate:** As a full-screen effect, cost scales with resolution × framerate.
3. **Texture bandwidth:** When mixing with tex0, one extra texture fetch per fragment.

### Optimization Opportunities

- **Approximate `atan`**: Could replace with fast approximation or precomputed lookup if precision not critical.
- **Reduce `sin` calls**: The cross-modulated algorithm uses 3+ sin calls; could be optimized by reusing intermediate values.
- **Algorithm pre-selection**: If algorithm is fixed for a performance-critical use, a specialized shader could eliminate branching.

### Expected Performance

On a mid-range GPU (e.g., NVIDIA GTX 1060, AMD RX 580):
- **1080p @ 60 FPS**: ~0.3-0.5 ms/frame (fill-rate bound)
- **4K @ 60 FPS**: ~1.0-1.5 ms/frame (fill-rate bound)

The effect is **fill-rate limited** (every pixel shaded) rather than compute limited.

---

## Test Plan

### Unit Tests (Python)

**Target coverage:** ≥80% of `FMCoordinatesGen` class methods.

**Test cases:**

1. **Constructor validation**
   - Verify `name == "fm_coordinates"`
   - Verify all 8 parameters exist with default values
   - Verify parameter ranges set to (0.0, 10.0)
   - Verify `effect_category == "generator"`
   - Verify tags include "generator", "fm", "synthesis", "modulation"

2. **Parameter getters/setters**
   - Set each parameter to boundary values (0, 10) and mid-range (5)
   - Verify `get_parameter()` returns set value
   - Set out-of-range value (e.g., -5, 15) and verify clamped to [0, 10]

3. **Preset loading**
   - Verify each preset key exists in `PRESETS`
   - Verify each preset has all 8 parameters
   - Verify preset values are within [0, 10]
   - Apply preset and verify parameters update correctly

4. **Parameter descriptions**
   - Verify `_parameter_descriptions` has entries for all 8 parameters
   - Verify descriptions are non-empty strings

5. **Chaos ratings**
   - Verify `_chaos_rating` has entries for all 8 parameters
   - Verify ratings are floats in [0, 1]

6. **Shader compilation**
   - Instantiate effect; verify no exception raised
   - Verify `self.shader` is not None

**Example test structure:**
```python
import unittest
from unittest.mock import patch, MagicMock
from core.effects.vcv_generators import FMCoordinatesGen

class TestFMCoordinatesGen(unittest.TestCase):
    def setUp(self):
        self.effect = FMCoordinatesGen()

    def test_constructor(self):
        self.assertEqual(self.effect.name, "fm_coordinates")
        self.assertEqual(self.effect.effect_category, "generator")
        self.assertIn("generator", self.effect.effect_tags)

    def test_parameter_ranges(self):
        for param in self.effect.parameters:
            self.assertIn(param, self.effect.parameter_ranges)
            min_val, max_val = self.effect.parameter_ranges[param]
            self.assertEqual(min_val, 0.0)
            self.assertEqual(max_val, 10.0)

    def test_set_parameter_clamping(self):
        self.effect.set_parameter('carrier_freq', 15.0)
        self.assertEqual(self.effect.parameters['carrier_freq'], 10.0)
        self.effect.set_parameter('carrier_freq', -3.0)
        self.assertEqual(self.effect.parameters['carrier_freq'], 0.0)

    def test_presets(self):
        for preset_name, values in self.effect.PRESETS.items():
            for param, val in values.items():
                self.assertIn(param, self.effect.parameters)
                self.assertTrue(0.0 <= val <= 10.0)
```

### Integration Tests

1. **Shader rendering**
   - Create OpenGL context (headless via `pyglet` or `moderngl`)
   - Instantiate `FMCoordinatesGen`, set parameters, call `apply_uniforms()`
   - Render to framebuffer, read pixels, verify:
     - Output is not all zeros (unless u_mix=0 and tex0 is black)
     - Output changes when parameters change
     - No GL errors

2. **Parameter remapping verification**
   - Set parameter to 0, 5, 10; capture shader uniform values via `glGetUniformfv`
   - Verify remapped values match expected formulas

3. **Mix behavior**
   - Bind a known texture (e.g., solid red), set u_mix=0 → output red
   - Set u_mix=10 → output pattern (not red)
   - Set u_mix=5 → blended result

4. **Algorithm switching**
   - Set algorithm to 0, 5, 10; verify visual output differs in expected ways:
     - 0: smooth, single-source patterns
     - 5: blended dual-source patterns
     - 10: complex, recursive patterns

5. **Color mode switching**
   - Set color_mode to 0, 5, 10; verify output color spaces:
     - 0: multi-colored rainbow
     - 5: grayscale
     - 10: thermal (red-yellow-blue)

### Visual Regression Tests

- Render frames at preset parameter combinations
- Compare pixel-wise against golden images (tolerance: small per-pixel differences due to GPU precision)
- Flag significant deviations (>1% pixel difference)

### Shader Compilation Tests

- Compile `FM_COORDINATES_FRAGMENT` in isolation
- Verify no GLSL errors or warnings
- Check uniform locations are valid for all declared uniforms

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT076: FMCoordinatesGen` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

**Primary source:** `/home/happy/Desktop/claude projects/vjlive/core/effects/vcv_generators.py`

- Lines 1-89: Module docstring, imports, `HARMONIC_PATTERNS_FRAGMENT` (for context)
- Lines 90-180: `FM_COORDINATES_FRAGMENT` shader string (lines 90-180 approx)
- Lines 250-310: `FMCoordinatesGen` class definition

**Related test files:**

- `tests/test_vcv_generators.py` — contains unit tests for `FMCoordinatesGen` (lines 33-52 in legacy)
- `core/matrix/node_effect_vcv_gen.py` — Matrix node wrapper `FMCoordinatesNode`
- `core/matrix/node_effect_video_gen.py` (vjlive-2) — duplicate node wrapper

**Legacy lookup snippets:** 10 code snippets retrieved via `legacy_lookup.py "FMCoordinatesGen"` covering:
- Effect registration in `__init__.py`
- Node class definitions
- Test cases
- Shader fragment

---

## Migration Considerations (WebGPU)

### WGSL Translation

The GLSL 330 shader will need conversion to WGSL for WebGPU. Key changes:

1. **Uniform bind group layout:**
   ```wgsl
   struct Uniforms {
       time: f32,
       resolution: vec2<f32>,
       u_mix: f32,
       carrier_freq: f32,
       mod_freq: f32,
       mod_index: f32,
       feedback: f32,
       algorithm: f32,
       ratio: f32,
       brightness: f32,
       color_mode: f32,
   }
   @group(0) @binding(0) var<uniform> uniforms: Uniforms;
   @group(0) @binding(1) var tex0: texture_2d<f32>;
   ```

2. **Trig functions:** WGSL has `sin`, `cos`, `atan` with same signatures.

3. **Texture sampling:** `textureLoad` or `textureSample` depending on sampler setup.

4. **Precision:** Use `f32` consistently; no significant precision issues.

5. **Entry point:** `@fragment fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32>`

### Performance on WebGPU

- Compute cost similar to OpenGL ES 3.0
- No expected regressions; WGSL may be faster due to better compiler optimizations
- Memory layout: uniform buffer should be 16-byte aligned; pad if needed

---

## Open Questions / [NEEDS RESEARCH]

- **Audio reactivity:** The skeleton mentions audio reactor integration, but the legacy `FMCoordinatesGen` does not implement `set_audio_analyzer()` or use audio data. The base `Effect` class may provide hooks. **Status:** [NEEDS RESEARCH] — verify if audio reactivity is intended but missing, or if this generator is purely parameter-driven.
- **Semantic layer support:** The `apply_uniforms` signature includes `semantic_layer=None` but the implementation does not use it. **Status:** [NEEDS RESEARCH] — determine if semantic layers (e.g., depth, optical flow) are meant to modulate parameters.
- **Depth camera integration:** Some generators in the codebase connect to depth buses. `FMCoordinatesGen` does not. **Status:** [NEEDS RESEARCH] — confirm this is a pure 2D pattern generator with no depth input.

---
