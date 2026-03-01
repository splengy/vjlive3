# P6-GE17: vcv_video_generators (Plaits)

> **Task ID:** `P6-GE17`  
> **Priority:** P0 (Critical)  
> **Source:** vjlive (`plugins/vcore/vcv_video_generators.py`)  
> **Class:** `MacroShapeGen`  
> **Phase:** Phase 6  
> **Status:** ⚙️ In Progress  

## Mission Context

`MacroShapeGen` (inspired by the VCV Rack **Plaits** macro oscillator) is a
procedural generator that creates evolving geometric shapes using **signed
distance functions (SDFs)**. It renders eight different base shape models
(circle, rectangle, hexagon, triangle, etc.), blends between them via
continuous morphing, applies frequency‑based repetition and tessellation, and
colours the boundaries with time‑animated hues and optional edge glows.

The effect is ideal for creating symmetrical, crystalline patterns and evolving
geometric artwork synchronized with music.

## Behavioural Overview

The effect is generator‑only but supports input texture blending. Time
progression animates both the colour palette and shape deformations (via the
**animate** parameter).

High‑level processing:

1. **Coordinate setup**: normalise `uv` and apply aspect correction.
2. **Parameter remapping**: convert seven 0‑10 UI sliders to internal ranges
   (shape model selector, morphing blend, frequency/scale, complexity, colour
   map, modulation amount, animation speed).
3. **SDF computation**: select base SDF based on `model` selector; compute
   signed distance from current pixel to nearest edge of the shape.
4. **Morphing**: blend between adjacent models using `morph` parameter for
   smooth transitions.
5. **Complexity**: apply `timbre` to modulate the shape (e.g., waviness,
   iteration count for fractals).
6. **Colouring**: map distance to hue; animate via `time * animate`.
7. **Rendering**: isoline rendering with optional edge glow.
8. **Mix**: blend with input texture.

## Shader Details & Maths

```glsl
#version 330 core

in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform vec2 resolution;
uniform float time;
uniform float u_mix;

// All 0-10 parameters
uniform float model;         // SDF model select (0-10 → 8 models)
uniform float morph;         // blend between models
uniform float frequency;     // repetition frequency (scale)
uniform float timbre;        // shape complexity / harmonics
uniform float color;         // base hue / colour map
uniform float shape_mod;     // shape modulation (wavy, fractal iters, etc)
uniform float animate;       // animation speed

// [hsv2rgb helper omitted]

// Eight basic 2D SDFs:
// 0: circle(p, r)
// 1: rectangle(p, b)
// 2: hexagon(p, r)
// 3: triangle(p, r)
// 4-7: variants/blends

float sdCircle(vec2 p, float r) {
    return length(p) - r;
}

float sdBox(vec2 p, vec2 b) {
    vec2 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

// [other SDF definitions...]

void main() {
    vec2 p = (uv - 0.5) * 2.0;
    float aspect = resolution.x / resolution.y;
    p.x *= aspect;

    // Remap parameters
    int mod_idx = int(model / 10.0 * 7.0);          // [0, 7]
    float morph_blend = morph / 10.0;                // [0, 1]
    float freq = 1.0 + frequency / 10.0 * 8.0;      // [1, 9]
    float timb = 0.5 + timbre / 10.0 * 2.5;         // [0.5, 3]
    float col_offset = color / 10.0;                 // [0, 1]
    float s_mod = shape_mod / 10.0 * 2.0;           // [0, 2]
    float anim_speed = animate / 10.0 * 3.0;        // [0, 3]

    // Apply frequency (tiling/scaling)
    p *= freq;

    // Distortion  based on animate parameter
    float distortion = sin(length(p) * timb - time * anim_speed) * s_mod;
    p += distortion * normalize(p);

    // Compute SDF for current model
    float d = 1000.0;
    // [Select and compute SDF based on mod_idx, with morphing to next model]
    // Pseudo-code: d = mix(sdf[mod_idx](p), sdf[mod_idx+1](p), morph_blend)

    // Rendering
    float val = 1.0 - smoothstep(0.0, 0.02, abs(d));

    // Edge glow
    float glow = exp(-abs(d) * 20.0) * 0.5;
    val += glow;
    val = clamp(val, 0.0, 1.0);

    // Colour
    vec3 col = hsv2rgb(vec3(col_offset + glow * 0.3, 0.8, val));

    vec4 original = texture(tex0, uv);
    fragColor = mix(original, vec4(col, 1.0), u_mix / 10.0);
}
```

**Key equations**:
- Signed Distance Function: distance from point `p` to shape boundary.
- Smoothstep isoline: `1.0 - smoothstep(0.0, thickness, abs(d))` renders edges.
- Edge glow: `exp(-abs(d) * 20.0) * 0.5` highlights borders.
- Morphing: `mix(sdf1(p), sdf2(p), blend)` blends between two shapes.
- Colour: base hue + glow contribution, animated via time offset.

## Public API

| Parameter | Type | Description | UI Range | Shader Mapping |
|-----------|------|-------------|----------|----------------|
| model | float | Shape model selector (8 models) | 0–10 | `int(x/10*7)` |
| morph | float | Blend between adjacent models | 0–10 | `x/10` (0–1) |
| frequency | float | Scale/repetition frequency | 0–10 | `1 + x/10*8` |
| timbre | float | Complexity / harmonic depth | 0–10 | `0.5 + x/10*2.5` |
| color | float | Base hue / colour map offset | 0–10 | `x/10` (0–1) |
| shape_mod | float | Shape modulation (waviness, fractality) | 0–10 | `x/10*2` |
| animate | float | Animation speed | 0–10 | `x/10*3` |
| mix | float | Blend with input texture | 0–10 | direct, 0–10 range |

Effect category: `generator`  
GPU tier: `BASIC` (SDF computation is fast)  
Legacy name: Plaits (VCV Rack macro oscillator)

### Shape Models
The eight base models (selectable via `model` 0–10):
0. **Circle** – simple radius‑based SDF
1. **Rectangle** – box SDF with rounded corners option
2. **Hexagon** – regular hexagon via angular SDF
3. **Triangle** – equilateral or isosceles variants
4. **Star** – multi‑pointed star (complexity via `timbre`)
5. **Cross/Plus** – orthogonal cross shape
6. **Diamond** – rotated square with adjustable aspect
7. **Rounded Polygon** – complexity blend (3–8 sides)

### Presets
```python
PRESETS = {
    "simple_circle":   {"model": 0.0, "morph": 0.0, "frequency": 2.0, "timbre": 3.0, "color": 5.0, "shape_mod": 0.0, "animate": 3.0},
    "morphing_shapes": {"model": 2.0, "morph": 5.0, "frequency": 3.0, "timbre": 5.0, "color": 2.0, "shape_mod": 3.0, "animate": 4.0},
    "tiled_flowers":   {"model": 7.0, "morph": 0.0, "frequency": 6.0, "timbre": 6.0, "color": 8.0, "shape_mod": 4.0, "animate": 2.0},
    "spiral_grid":     {"model": 8.5, "morph": 3.0, "frequency": 4.0, "timbre": 7.0, "color": 1.0, "shape_mod": 5.0, "animate": 5.0},
    "glowing_rings":   {"model": 4.0, "morph": 0.0, "frequency": 2.0, "timbre": 2.0, "color": 6.0, "shape_mod": 2.0, "animate": 1.0},
}
```

## CPU Fallback

NumPy implementation shall compute SDF values for each pixel using vectorized
operations. Unit tests will compare CPU‑rendered and GPU‑rendered pixels for
consistency (tolerance ±1e-4).

## Testing Plan

1. **Instantiation**: create `MacroShapeGen()` with correct name and category.
2. **Model selection**: test `model` values 0, 3.5, 7, 10 and verify SDF switching.
3. **Morphing**: render with `morph=0`, `5`, `10` and confirm smooth blending.
4. **Frequency**: verify that frequency scaling produces appropriately-sized shapes.
5. **Colouring**: test different `color` offset values; confirm hue shifts.
6. **Animation**: advance time and confirm edge/glow animation.
7. **Presets**: load all presets and verify parameter values.
8. **GPU/CPU**: render pixel on both paths; compare output (tol < 1e-4).

## Edge Cases & Safety

- `model` > 8 is clamped to model 7 (last valid index).
- `morph` outside [0,1] is clamped after remapping.
- `frequency` [1,9] avoids extreme scaling and underflow.
- `timbre` [0.5,3] allows shape variation without numeric issues.
- Signed distance is always finite due to bounded coordinate space.
- Smoothstep edge detection is numerically stable.
- Glow exponential: `exp(-abs(d)*20)` clamped to [0,1] prevents overflow.

## Performance & Safety Rails

- SDF computation: ~8 branch selects (one per model), then simple arithmetic.
- No expensive texture lookups except the final mix pass.
- All float operations standard precision.
- Glow and isoline rendering is ~constant time per pixel.

## Easter Egg

When `model=7` (rounded polygon), `morph=10`, and `timbre=10`, the shape
morphs continuously through all polygon counts (3 sides → 8 sides → back to
3).  This mode was called "kaleidoscope breathing" in the legacy codebase,
producing hypnotic radial breathing patterns.

---

Ready for implementation. Once coded and tested, move to `_02_fleshed_out`.

