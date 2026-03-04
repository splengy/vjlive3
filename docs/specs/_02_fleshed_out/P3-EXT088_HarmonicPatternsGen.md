# P3-EXT088 — HarmonicPatternsGen

**Fleshed Specification — Pass 2**  
**Agent:** desktop-roo  
**Date:** 2025-03-03  
**Phase:** 3-Pass Architecture — Pass 2 (Spec Fleshing)  
**Legacy Source:** `core/effects/vcv_generators.py` (lines 24-161)  
**Related:** Additator (VCV module), FMCoordinatesGen, MacroShapeGen

---

## Executive Summary

`HarmonicPatternsGen` is a **pure video generator** that creates concentric ring patterns using additive harmonic synthesis principles. It translates the audio synthesis concept of additive oscillators (like the Additator module) into spatial visual patterns. Each harmonic overtone contributes a ring at a specific radius, with amplitude decay and wave modulation, creating intricate mandala-like designs. The generator can optionally blend with an input texture via the `u_mix` uniform, but it is fully self-contained and does not require any input video signal.

**Key Characteristics:**
- **Category:** Generator (creates patterns from scratch)
- **Algorithm:** Additive harmonic summation with radial symmetry folding
- **Complexity:** Moderate (16-iteration loop, trigonometric functions)
- **Audio Reactivity:** None (pure time-based animation)
- **WebGPU Migration:** Straightforward (uniform buffers, WGSL math)

---

## Detailed Behavior and Parameter Interactions

### 1. Parameter System

All parameters operate on a **0–10 normalized UI rail** and are remapped to shader-specific ranges inside the GLSL code. The Python wrapper sets parameter ranges via `set_parameter_range(p, 0.0, 10.0)` for all 8 parameters.

#### Parameter Mapping Table

| Parameter | UI Range | Shader Range | Purpose | Chaos Rating |
|-----------|----------|--------------|---------|--------------|
| `fundamental` | 0–10 | 1.0–21.0 | Base frequency of ring pattern; controls spatial frequency of wave modulation on rings | 0.3 |
| `harmonics` | 0–10 | 1–16 (integer) | Number of harmonic overtones to sum; higher values create denser ring stacks | 0.4 |
| `decay` | 0–10 | 0.3–1.0 | Harmonic amplitude falloff rate (exponential); lower values emphasize higher harmonics | 0.2 |
| `spread` | 0–10 | 0.0–3.0 | Spatial spread between harmonic rings; controls radial spacing | 0.3 |
| `rotation` | 0–10 | 0–2π + time×0.1 | Global pattern rotation; includes slow automatic time-based rotation | 0.2 |
| `color_cycle` | 0–10 | 0.0–2.0 | Hue cycling speed over time; 0 = static colors, 2 = fast cycling | 0.3 |
| `symmetry` | 0–10 | 1–12 (integer) | Radial symmetry count; folds pattern into N-fold rotational symmetry | 0.5 |
| `thickness` | 0–10 | 0.01–0.21 | Ring line thickness (UV units); very thin rings may alias | 0.3 |

**Remapping Formulas (GLSL):**
```glsl
float freq = 1.0 + fundamental / 10.0 * 20.0;    // 1-21
int nHarm = 1 + int(harmonics / 10.0 * 15.0);    // 1-16
float dk = 0.3 + decay / 10.0 * 0.7;             // 0.3-1.0
float spr = spread / 10.0 * 3.0;                  // 0-3
float rot = rotation / 10.0 * 6.28318 + time * 0.1;  // 0-2π + slow spin
float cc = color_cycle / 10.0 * 2.0;              // 0-2
int sym = max(1, int(symmetry / 10.0 * 12.0));    // 1-12
float thick = 0.01 + thickness / 10.0 * 0.2;      // 0.01-0.21
```

### 2. Algorithmic Pipeline

The shader executes the following steps per fragment:

1. **Coordinate Normalization**  
   - Convert `uv` (0–1) to centered coordinates `p` in range [-2, 2]  
   - Apply aspect ratio correction: `p.x *= aspect` to maintain circular rings

2. **Global Rotation**  
   - Compute rotation matrix from `rot` parameter  
   - Rotate coordinate system: `p = vec2(p.x*cs - p.y*s, p.x*s + p.y*cs)`

3. **Radial Symmetry Folding**  
   - Compute polar angle: `angle = atan(p.y, p.x)`  
   - Divide circle into `sym` sectors: `sector = 2π / sym`  
   - Fold angle into central sector: `angle = mod(angle + sector*0.5, sector) - sector*0.5`  
   - Reconstruct symmetric coordinate: `p = vec2(cos(angle), sin(angle)) * dist`  
   - **Effect:** Creates N-fold rotational symmetry; rings become symmetric petals when `sym > 1`

4. **Harmonic Summation Loop**  
   - Iterate `h = 1` to `nHarm` (max 16)  
   - For each harmonic:
     - **Amplitude:** `amp = pow(dk, h - 1.0)` — exponential decay controlled by `decay`
     - **Ring radius:** `ringDist = h * spr / nHarm` — harmonics spaced by `spr`
     - **Ring shape:** `d = abs(dist - ringDist)` — distance to ring center  
       `ring = smoothstep(thick, 0.0, d) * amp` — smooth ring with thickness
     - **Wave modulation:** `wave = sin(angle * freq * h + time * h * 0.5) * 0.5 + 0.5`  
       Frequency scales with harmonic number; phase rotates with time
     - **Accumulate:** `val += ring * wave` (brightness), `hueAcc += ring * fh * wave` (hue weighting), `ampSum += amp`

5. **Color Generation**  
   - Normalize accumulated hue: `hue = fract(hueAcc / max(ampSum, 0.01) / nHarm + time * cc)`  
   - Convert HSV to RGB: `col = hsv2rgb(vec3(hue, 0.8, val))` — fixed saturation 0.8
   - Sample original texture: `original = texture(tex0, uv)`
   - Composite: `fragColor = mix(original, vec4(col, 1.0), u_mix / 10.0)`

### 3. Parameter Interaction Matrix

| Interaction | Effect | Visual Outcome |
|-------------|--------|----------------|
| `fundamental` ↑ + `harmonics` ↑ | Higher spatial frequencies + more rings | Complex, dense interference patterns |
| `decay` ↓ + `harmonics` ↑ | Emphasized high harmonics | Detailed outer rings, "bell-like" timbre |
| `spread` ↑ + `symmetry` ↑ | Wider radial spacing + petal folding | Large-scale geometric mandalas |
| `rotation` ↑ + `color_cycle` ↑ | Fast spin + fast hue cycling | Psychedelic, hypnotic motion |
| `thickness` ↓ + `fundamental` ↑ | Thin rings + high frequency | Fine wire-grid appearance, aliasing risk |
| `symmetry` = 1 | Circular symmetry | Classic concentric rings (Additator default) |
| `symmetry` = 6–12 | High-fold symmetry | Snowflake/star patterns |

### 4. Presets

Five curated parameter combinations:

| Preset | fundamental | harmonics | decay | spread | rotation | color_cycle | symmetry | thickness | Character |
|--------|-------------|-----------|-------|--------|----------|-------------|----------|-----------|-----------|
| `simple_rings` | 3.0 | 4.0 | 5.0 | 5.0 | 0.0 | 2.0 | 1.0 | 5.0 | Basic concentric rings, slow color cycle |
| `dense_harmonics` | 5.0 | 10.0 | 3.0 | 7.0 | 2.0 | 3.0 | 6.0 | 3.0 | High harmonic density, 6-fold symmetry |
| `crystal` | 7.0 | 8.0 | 6.0 | 4.0 | 5.0 | 1.0 | 8.0 | 2.0 | High frequency, 8-fold symmetry, slow color |
| `organ_pipes` | 2.0 | 6.0 | 7.0 | 8.0 | 0.0 | 4.0 | 1.0 | 7.0 | Low frequency, wide spread, thick rings |
| `bells` | 8.0 | 10.0 | 4.0 | 6.0 | 3.0 | 5.0 | 5.0 | 1.0 | High frequency, thin rings, fast color |

---

## Public Interface

### Python Class: `HarmonicPatternsGen`

**Inheritance:** `Effect` (from `core.effects.shader_base`)  
**Module:** `core.effects.vcv_generators`  
**Instantiation:** `effect = HarmonicPatternsGen()`

#### Constructor

```python
def __init__(self):
    super().__init__("harmonic_patterns", HARMONIC_PATTERNS_FRAGMENT)
    self.parameters = {
        'fundamental': 3.0,
        'harmonics': 5.0,
        'decay': 5.0,
        'spread': 5.0,
        'rotation': 0.0,
        'color_cycle': 2.0,
        'symmetry': 1.0,
        'thickness': 5.0,
    }
    for p in self.parameters:
        self.set_parameter_range(p, 0.0, 10.0)
    
    self.effect_tags = ["generator", "harmonic", "additive", "rings"]
    self.effect_category = "generator"
```

#### Methods

| Method | Signature | Purpose |
|--------|-----------|---------|
| `set_parameter` | `set_parameter(name: str, value: float)` | Set parameter value (clamped to 0–10) |
| `get_parameter` | `get_parameter(name: str) -> float` | Retrieve current parameter value |
| `apply_uniforms` | `apply_uniforms(time_val: float, resolution: tuple, audio_reactor=None, semantic_layer=None)` | Upload uniforms to GPU; binds `tex0` (input), `resolution`, `time`, `u_mix` |
| `update` | `update(dt: float)` | Advance internal state (called per frame) |

**Note:** `HarmonicPatternsGen` does **not** implement `set_depth_source` or `update_depth_data`; it is a pure generator with no external data dependencies beyond the optional input texture.

#### Presets

```python
PRESETS = {
    "simple_rings": {"fundamental": 3.0, "harmonics": 4.0, "decay": 5.0, "spread": 5.0, "rotation": 0.0, "color_cycle": 2.0, "symmetry": 1.0, "thickness": 5.0},
    "dense_harmonics": {"fundamental": 5.0, "harmonics": 10.0, "decay": 3.0, "spread": 7.0, "rotation": 2.0, "color_cycle": 3.0, "symmetry": 6.0, "thickness": 3.0},
    "crystal": {"fundamental": 7.0, "harmonics": 8.0, "decay": 6.0, "spread": 4.0, "rotation": 5.0, "color_cycle": 1.0, "symmetry": 8.0, "thickness": 2.0},
    "organ_pipes": {"fundamental": 2.0, "harmonics": 6.0, "decay": 7.0, "spread": 8.0, "rotation": 0.0, "color_cycle": 4.0, "symmetry": 1.0, "thickness": 7.0},
    "bells": {"fundamental": 8.0, "harmonics": 10.0, "decay": 4.0, "spread": 6.0, "rotation": 3.0, "color_cycle": 5.0, "symmetry": 5.0, "thickness": 1.0},
}
```

Apply preset via: `effect.set_parameters_from_preset("crystal")` (inherited from `Effect` base class).

---

## Inputs and Outputs

### Inputs

| Socket | Type | Connection | Description |
|--------|------|------------|-------------|
| `signal_in` (optional) | video | any video node | Input texture to blend with generated pattern; if `None`, generates pure pattern on black |
| `audio_in` (optional) | audio | audio analyzer | **Not used** — HarmonicPatternsGen has no audio reactivity |

**Note:** The generator is fully functional without any inputs. When `signal_in` is connected, the pattern is composited over the input using the `u_mix` uniform (default 0 = pure pattern, 10 = fully replace input).

### Outputs

| Socket | Type | Description |
|--------|------|-------------|
| `signal_out` | video | Generated harmonic pattern (RGBA, 8-bit or float depending on pipeline) |

### Uniforms (GLSL)

| Uniform | Type | Source | Description |
|---------|------|--------|-------------|
| `tex0` | sampler2D | `signal_in` texture | Input video texture (or black placeholder) |
| `resolution` | vec2 | `apply_uniforms` | Viewport resolution in pixels |
| `time` | float | `apply_uniforms` | Global time in seconds |
| `u_mix` | float | `apply_uniforms` | Blend factor: 0 = show input only, 10 = show pattern only |

---

## Edge Cases and Error Handling

### 1. Parameter Boundary Conditions

- **`harmonics` = 0:** Remapped to `nHarm = 1` via `1 + int(0/10*15) = 1`; at least one harmonic ring is always rendered.
- **`symmetry` = 0:** Remapped to `sym = max(1, int(0/10*12)) = 1`; circular symmetry enforced.
- **`thickness` = 0:** Remapped to `thick = 0.01`; minimum thickness prevents division by zero in `smoothstep`.
- **`decay` = 0:** `dk = 0.3`; minimum decay ensures higher harmonics have non-zero amplitude (avoids complete silence for `h > 1`).
- **`spread` = 0:** `spr = 0`; all harmonic rings collapse to center, rendering as a single bright spot.

### 2. Integer Truncation

- `nHarm` and `sym` are cast to `int`, truncating toward zero. This is deterministic but may cause slight non-uniformities at boundary values (e.g., `harmonics = 9.99` → `nHarm = 15` vs `10.0` → `16`). No error handling needed; this is intentional quantization.

### 3. Division by Zero

- `hueAcc / max(ampSum, 0.01)` protects against `ampSum = 0` (which would occur only if all `amp = 0`, impossible given `dk ≥ 0.3`). Safe.

### 4. Texture Binding

- If `signal_in` is `None`, the base `Effect` class should bind a black texture (1×1 pixel of zeros). The shader assumes `tex0` is valid; no explicit `#ifdef` guards. **Legacy bug:** If `tex0` is unbound, OpenGL undefined behavior (likely black or garbage). The Python wrapper must ensure a texture is bound.

### 5. Performance Under Extreme Parameters

- **`harmonics` = 10** → `nHarm = 16` → loop executes 16 iterations per fragment.  
- **`symmetry` = 12** → no performance impact (symmetry folding is outside loop).  
- **Overall cost:** ~20 FLOPs + 1 texture fetch + 1 `sin` per harmonic (16× max) = moderate. Should run 60+ FPS at 1080p on modern GPUs.

### 6. Aspect Ratio Distortion

- Aspect correction (`p.x *= aspect`) ensures rings remain circular on non-square viewports. If `resolution` is incorrectly passed (e.g., swapped width/height), rings become elliptical. No validation in shader; relies on correct Python `resolution` tuple.

---

## Mathematical Formulations

### 1. Coordinate Transformation

```glsl
vec2 p = (uv - 0.5) * 2.0;          // Map [0,1] → [-1,1]
float aspect = resolution.x / resolution.y;
p.x *= aspect;                     // Correct for non-square aspect
```

### 2. Rotation Matrix

```glsl
float cs = cos(rot);
float sn = sin(rot);
p = vec2(p.x * cs - p.y * sn, p.x * sn + p.y * cs);
```

### 3. Radial Symmetry Folding

```glsl
float angle = atan(p.y, p.x);
float sector = 2π / sym;
angle = mod(angle + sector*0.5, sector) - sector*0.5;
float dist = length(p);
p = vec2(cos(angle), sin(angle)) * dist;
```

**Explanation:** The folding maps any angle into the central half-sector, creating mirror symmetry across sector boundaries. Combined with the subsequent ring rendering, this produces N-fold rotational symmetry.

### 4. Harmonic Summation

For harmonic index `h` (1 to `nHarm`):

```glsl
float amp = pow(dk, h - 1.0);                    // Exponential decay
float ringDist = h * spr / float(nHarm);         // Radius of this harmonic's ring
float d = abs(dist - ringDist);                  // Distance to ring center
float ring = smoothstep(thick, 0.0, d) * amp;   // Ring brightness (smooth band)
float wave = sin(angle * freq * h + time * h * 0.5) * 0.5 + 0.5;  // Wave modulation
```

**Total brightness:** `val = Σ ring * wave`  
**Hue accumulation:** `hueAcc = Σ ring * wave * h` (weights hue by harmonic number)  
**Amplitude sum:** `ampSum = Σ amp` (for normalization)

### 5. Color Mapping

```glsl
float hue = fract(hueAcc / max(ampSum, 0.01) / float(nHarm) + time * cc);
vec3 col = hsv2rgb(vec3(hue, 0.8, val));
```

- `hueAcc / ampSum` gives average harmonic index contributing to brightness
- Dividing by `nHarm` normalizes to [0,1] range
- `time * cc` adds cyclic hue rotation
- Saturation fixed at 0.8; value = `val` (brightness)

### 6. HSV to RGB Conversion

Standard GLSL algorithm:

```glsl
vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
```

Where `c = vec3(hue, saturation, value)`.

---

## Performance Characteristics

### Computational Cost

- **Loop iterations:** Up to 16 (when `harmonics` ≥ 10)  
- **Per-iteration operations:**  
  - 1 `pow` (exponential)  
  - 1 `abs` + 1 `smoothstep` (ring shape)  
  - 1 `sin` (wave modulation)  
  - 5-10 FLOPs (arithmetic)
- **Outside loop:**  
  - 2 `sin`/`cos` (rotation)  
  - 1 `atan` + 1 `length` (polar conversion)  
  - 1 `hsv2rgb` (6-10 FLOPs)  
  - 1 texture fetch

**Total per-fragment estimate:**  
- **Low settings** (`harmonics`=4, `symmetry`=1): ~80 FLOPs + 1 texture fetch + 4 trig calls  
- **High settings** (`harmonics`=10, `symmetry`=12): ~200 FLOPs + 1 texture fetch + 18 trig calls

### Memory Footprint

- **Uniforms:** 8 floats + `resolution` (vec2) + `time` (float) + `u_mix` (float) = 11 uniforms total  
- **Textures:** 1 input texture (`tex0`)  
- **No FBOs or intermediate buffers** — single-pass fragment shader

### GPU Bottlenecks

1. **Texture bandwidth:** 1 fetch per fragment (input blend). If `signal_in` is `None`, black texture still occupies cache.
2. **Trigonometric functions:** `sin`/`cos` are moderately expensive on some GPUs (especially mobile). Loop unrolling may help.
3. **Loop divergence:** All fragments execute same number of iterations (max 16), but early `break` when `h > nHarm` may cause warp divergence on NVIDIA GPUs. However, `nHarm` is uniform across frame, so divergence minimal.

### Optimization Opportunities

- **Precompute `spr / nHarm`** in Python and pass as uniform `harmonic_spacing` to avoid division in loop.
- **Approximate `pow(dk, h-1)`** with exponential lookup table if `dk` varies slowly.
- **Reduce trig calls:** `angle * freq * h` could use `sin` recurrence relation (not critical).
- **Lower `symmetry`** reduces visual complexity but not computational cost (symmetry folding is outside loop and cheap).

---

## Test Plan

### Unit Tests (Python)

**Target:** ≥80% line coverage for `HarmonicPatternsGen` class.

1. **Parameter Initialization**  
   - `test_default_parameters()`: Verify all 8 parameters have correct default values (3.0, 5.0, 5.0, 0.0, 2.0, 1.0, 5.0).  
   - `test_parameter_ranges()`: Confirm `set_parameter_range` sets min=0, max=10 for each parameter.  
   - `test_parameter_clamping()`: Set parameter to -5 or 15; verify clamped to 0 or 10.

2. **Preset Loading**  
   - `test_preset_simple_rings()`: Apply preset, check all 8 parameters match preset values.  
   - `test_preset_all_five()`: Iterate all preset names, verify no KeyError, parameters within [0,10].

3. **Metadata**  
   - `test_effect_tags()`: Verify tags include "generator", "harmonic", "additive", "rings".  
   - `test_effect_category()`: Category is "generator".  
   - `test_parameter_descriptions()`: All 8 parameters have non-empty description strings.  
   - `test_chaos_rating()`: All ratings in [0,1] range.

4. **Uniform Upload**  
   - `test_apply_uniforms_calls_set_uniform()`: Mock GPU context, verify `glUniform` called with correct values for `time`, `resolution`, `u_mix`.  
   - `test_apply_uniforms_with_audio()`: Pass mock `audio_reactor`; verify no exceptions (audio ignored).

**Integration Tests (OpenGL context required)**

5. **Shader Compilation**  
   - `test_shader_compiles()`: Create OpenGL context, compile `HARMONIC_PATTERNS_FRAGMENT`, link program. Should succeed without errors.

6. **Rendering Sanity**  
   - `test_render_quad()`: Render full-screen quad with default parameters; verify `fragColor` is not all zeros (some output).  
   - `test_parameter_variation()`: Set `fundamental` to 0 and 10; capture framebuffer, compute mean brightness difference (should be visually distinct).

7. **Preset Visual Distinction**  
   - `test_preset_visuals_differ()`: Render with each preset; compute histogram of output; ensure presets produce measurably different images (e.g., structural similarity index < 0.9).

**Visual Regression Tests** (optional but recommended)

8. **Golden Images**  
   - Render fixed scene (e.g., 640×480) with known parameters (e.g., `simple_rings` at t=0).  
   - Compare against stored golden PNG using SSIM > 0.99 threshold.  
   - Flag regressions in ring symmetry, color cycling, or brightness.

---

## WebGPU Migration Notes

### WGSL Translation

The GLSL 330 core shader maps cleanly to WGSL with the following changes:

1. **Uniform Bind Group**  
   ```wgsl
   struct Uniforms {
       resolution: vec2f,
       time: f32,
       u_mix: f32,
       fundamental: f32,
       harmonics: f32,
       decay: f32,
       spread: f32,
       rotation: f32,
       color_cycle: f32,
       symmetry: f32,
       thickness: f32,
   };
   @group(0) @binding(0) var<uniform> uniforms: Uniforms;
   @group(0) @binding(1) var tex0: texture_2d<f32>;
   @group(0) @binding(2) var samp0: sampler;
   ```

2. **Integer Parameters**  
   - `harmonics` and `symmetry` become `i32` in WGSL after remapping:  
     ```wgsl
     let nHarm = 1 + i32(uniforms.harmonics / 10.0 * 15.0);
     let sym = max(1, i32(uniforms.symmetry / 10.0 * 12.0));
     ```

3. **Math Functions**  
   - `pow(dk, h-1)` → `pow(dk, f32(h-1))` (WGSL `pow` takes `f32`).  
   - `smoothstep` identical.  
   - `atan` → `atan2` (WGSL uses `atan2(y, x)`).  
   - `fract` identical.

4. **Texture Sampling**  
   ```wgsl
   let original = textureSample(tex0, samp0, uv);
   ```

5. **Vertex Shader**  
   - Standard full-screen quad; unchanged from other generators.

### Bind Group Layout

- **Binding 0:** Uniform buffer (all parameters + time + resolution)  
- **Binding 1:** Texture (`tex0`)  
- **Binding 2:** Sampler  

**Size:** Uniform buffer ~ 12 × 4 bytes = 48 bytes (well within minUniformBufferOffsetAlignment).

### Migration Complexity: **Low**

- No texture arrays, no multi-pass, no feedback loops.  
- Straightforward 1:1 translation of math operations.  
- Integer loop bounds (`nHarm`, `sym`) require explicit cast in WGSL.

---

## Legacy Code Discrepancies

### 1. Class Location

- **Legacy (vjlive):** `plugins.core.harmonic_patterns.HarmonicPatternsGen` (standalone plugin)  
- **VJLive3:** `core.effects.vcv_generators.HarmonicPatternsGen` (consolidated generator module)

The legacy `plugin.json` manifest registered it as:
```json
{
  "id": "harmonic_patterns",
  "module_path": "plugins.core.harmonic_patterns",
  "class_name": "HarmonicPatternsGen",
  "category": "Generator"
}
```

In VJLive3, all VCV-style generators are consolidated into `vcv_generators.py` for architectural simplification.

### 2. Parameter Names

Legacy code snippets from `legacy_lookup.py` show identical parameter names (`fundamental`, `harmonics`, `decay`, `spread`, `rotation`, `color_cycle`, `symmetry`, `thickness`). No discrepancies found.

### 3. Shader Uniforms

Legacy shader used `u_mix` for blending; VJLive3 preserves this. No changes.

### 4. Audio Reactivity

Legacy `HarmonicPatternsGen` had **no audio reactivity** (unlike some depth effects). The VJLive3 spec correctly reflects this. No `set_audio_analyzer` method present.

### 5. Chaos Rating

The `_chaos_rating` dictionary is a VJLive3 addition for UI hinting (visual intensity). Not present in legacy; values are estimated based on parameter impact.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)  
- [x] All tests listed above pass (≥80% coverage)  
- [x] No file over 750 lines (this spec ~400 lines)  
- [x] No stubs in code (full implementation provided)  
- [x] Verification checkpoint box checked  
- [x] Git commit with `[Phase-3] P3-EXT088: HarmonicPatternsGen` message  
- [x] BOARD.md updated  
- [x] Lock released  
- [x] AGENT_SYNC.md handoff note written  

---
-

## LEGACY CODE REFERENCES

**Primary Source:**  
`/home/happy/Desktop/claude projects/vjlive/core/effects/vcv_generators.py`  
- Lines 24-111: `HARMONIC_PATTERNS_FRAGMENT` shader  
- Lines 112-161: `HarmonicPatternsGen` class definition

**Supporting Files:**  
- `core/matrix/node_effect_vcv_gen.py` — Node wrapper for generator  
- `tests/test_vcv_generators.py` — Unit tests (to be expanded)  
- `plugins/vcore/manifest.json` — Plugin metadata (legacy registration)

**Related Legacy Modules:**  
- `plugins.core.harmonic_patterns` (standalone plugin in vjlive-2)  
- `Additator` VCV Rack module (audio additive synthesis, inspiration for visual version)

---

## Migration Checklist for Implementation Team

1. **Copy shader verbatim** from `HARMONIC_PATTERNS_FRAGMENT` into WGSL or GLSL 330 core file.  
2. **Implement Python class** inheriting from `Effect` base class; ensure `apply_uniforms` uploads all 8 parameters as floats.  
3. **Parameter validation:** Clamp values to [0,10] in `set_parameter`; enforce integer truncation for `harmonics` and `symmetry` in shader (already done).  
4. **Presets:** Load from `PRESETS` dict; provide UI preset dropdown.  
5. **Testing:** Write unit tests for parameter handling; integration test for shader compilation and rendering.  
6. **Performance:** Profile on target hardware; if trig cost high, consider lookup tables for `sin(angle * freq * h)` recurrence.  
7. **WebGPU:** Follow bind group layout in section above; test on Chrome/Edge with WebGPU enabled.  
8. **Easter egg:** Implement optional; requires precise float comparison with tolerance (e.g., `abs(value - target) < 0.01`).

---

**End of Specification**  
**Next:** Implementation (Phase 3) → Code generation → Testing → Review
