# P6-GE15: vcv_video_generators

> **Task ID:** `P6-GE15`  
> **Priority:** P0 (Critical)  
> **Source:** vjlive (`plugins/vcore/vcv_video_generators.py`)  
> **Class:** `HarmonicPatternsGen`  
> **Phase:** Phase 6  
> **Status:** ⬜ Todo  

## Mission Context

`HarmonicPatternsGen` (formerly *Additator* in the vjlive codebase) is a purely
procedural generator that paints concentric rings corresponding to the harmonic
series of a fundamental frequency.  Rings are modulated by sinusoidal waves,
radial symmetry and colour cycling, producing organ‑pipe, bell‑like and crystal
patterns that are popular in VCV rack performance patches.  It lives under the
**vcv_video_generators** category and must be ported intact to achieve full
feature parity with VJLive‑2.

## Behavioural Overview

The effect ignores any input texture by default – it is a generator – but when
a source is supplied it blends between the original image and the synthesized
pattern according to the **mix** parameter.  Time progresses the animation
(e.g. rotation and colour cycling) ensuring non‑static output.

At a high level the fragment shader performs the following steps:

1. **Normalize coordinates**: map `uv` from [0,1]→[-1,1] and correct for aspect
   ratio.
2. **Parameter remapping**: convert eight 0‑10 UI knobs into typed shader
   variables (frequencies, counts, geometric constants) with suitable ranges.
3. **Rotation & symmetry**: rotate the coordinate plane and fold the angle into
   `sym` equal sectors to achieve kaleidoscopic symmetry.
4. **Harmonic summation**: iterate through `nHarm` harmonics, drawing a thin
   ring at each harmonic's radius and modulating its intensity with a sin wave.
5. **Colouring**: accumulate hue weights, normalize by amplitude sum and
   apply the current colour‑cycle offset.
6. **Mix**: overlay the generated colour on top of the original texture.

A CPU fallback mirrors the GLSL code verbatim using NumPy; the two paths are
unit‑tested for agreement.

## Shader Details & Maths

Below is a lightly annotated version of the original GLSL fragment (stripped of
line‑breaking escapes) used as the cognitive reference during porting:

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform vec2 resolution;
uniform float time;
uniform float u_mix;

// All 0‑10 parameters coming from the UI
uniform float fundamental; // base frequency
uniform float harmonics;   // how many harmonics to draw
uniform float decay;       // harmonic amplitude falloff
uniform float spread;      // spatial spread of harmonics
uniform float rotation;    // overall rotation speed/angle
uniform float color_cycle; // hue drift rate
uniform float symmetry;    // number of symmetry sectors
uniform float thickness;   // ring thickness

void main() {
    // coordinate setup
    vec2 p = (uv - 0.5) * 2.0;
    float aspect = resolution.x / resolution.y;
    p.x *= aspect;

    // parameter remapping (all formulas derived from original source)
    float freq = 1.0 + fundamental / 10.0 * 20.0;    // [1,21]
    int nHarm = 1 + int(harmonics / 10.0 * 15.0);    // [1,16]
    float dk = 0.3 + decay / 10.0 * 0.7;             // [0.3,1.0]
    float spr = spread / 10.0 * 3.0;                  // [0,3]
    float rot = rotation / 10.0 * 6.28318 + time * 0.1; // adds slow spin
    float cc = color_cycle / 10.0 * 2.0;             // [0,2]
    int sym = max(1, int(symmetry / 10.0 * 12.0));   // [1,12]
    float thick = 0.01 + thickness / 10.0 * 0.2;     // [0.01,0.21]

    // rotate coordinates
    float cs = cos(rot);
    float sn = sin(rot);
    p = vec2(p.x * cs - p.y * sn, p.x * sn + p.y * cs);

    // apply radial symmetry by folding the angle into `sym` sectors
    float angle = atan(p.y, p.x);
    float sector = 6.28318 / float(sym);
    angle = mod(angle + sector * 0.5, sector) - sector * 0.5;
    float dist = length(p);
    p = vec2(cos(angle), sin(angle)) * dist;

    // accumulate harmonics
    float val = 0.0;
    float hueAcc = 0.0;
    float ampSum = 0.0;
    for (int h = 1; h <= 16; h++) {
        if (h > nHarm) break;
        float fh = float(h);
        float amp = pow(dk, fh - 1.0);

        // ring at harmonic distance
        float ringDist = fh * spr / float(nHarm);
        float d = abs(dist - ringDist);
        float ring = smoothstep(thick, 0.0, d) * amp;

        // wave modulation along ring circumference
        float wave = sin(angle * freq * fh + time * fh * 0.5) * 0.5 + 0.5;
        ring *= wave;

        val += ring;
        hueAcc += ring * fh;
        ampSum += amp;
    }

    val = clamp(val, 0.0, 1.0);

    // compute colour from weighted harmonic index
    float hue = fract(hueAcc / max(ampSum, 0.01) / float(nHarm) + time * cc);
    vec3 col = hsv2rgb(vec3(hue, 0.8, val));

    vec4 original = texture(tex0, uv);
    fragColor = mix(original, vec4(col, 1.0), u_mix / 10.0);
}
```

The CPU implementation should replicate every calculation in the loop exactly
(using `numpy` for vector operations) so that unit tests can compare a single
pixel output with the GLSL path.

## Public API

| Property | Type | Description | UI range | Shader mapping |
|----------|------|-------------|----------|----------------|
| fundamental | float | Base frequency (controls ring spacing) | 0–10 | `1.0 + x/10*20` |
| harmonics | float | Number of harmonics to render | 0–10 | `1 + int(x/10*15)` |
| decay | float | Exponential amplitude falloff | 0–10 | `0.3 + x/10*0.7` |
| spread | float | Spatial spread of rings | 0–10 | `x/10*3.0` |
| rotation | float | Rotation amount (also drifts with time) | 0–10 | `x/10*2π + time*0.1` |
| color_cycle | float | Speed of hue cycling | 0–10 | `x/10*2` |
| symmetry | float | Number of radial mirror sectors | 0–10 | `max(1,int(x/10*12))` |
| thickness | float | Ring thickness | 0–10 | `0.01 + x/10*0.2` |
| mix | float | Blend with original input texture | 0–10 | `u_mix` |

`Effect` base class will automatically expose these parameters with the
standardized 0–10 UI slider.

The effect category is `generator` and GPU tier is `BASIC`.

### Presets
Derived from the legacy Python class:
```python
PRESETS = {
    "simple_rings":     {"fundamental": 3.0, "harmonics": 4.0, "decay": 5.0, "spread": 5.0, "rotation": 0.0, "color_cycle": 2.0, "symmetry": 1.0, "thickness": 5.0},
    "dense_harmonics":  {"fundamental": 5.0, "harmonics": 10.0, "decay": 3.0, "spread": 7.0, "rotation": 2.0, "color_cycle": 3.0, "symmetry": 6.0, "thickness": 3.0},
    "crystal":          {"fundamental": 7.0, "harmonics": 8.0, "decay": 6.0, "spread": 4.0, "rotation": 5.0, "color_cycle": 1.0, "symmetry": 8.0, "thickness": 2.0},
    "organ_pipes":      {"fundamental": 2.0, "harmonics": 6.0, "decay": 7.0, "spread": 8.0, "rotation": 0.0, "color_cycle": 4.0, "symmetry": 1.0, "thickness": 7.0},
    "bells":            {"fundamental": 8.0, "harmonics": 10.0, "decay": 4.0, "spread": 6.0, "rotation": 3.0, "color_cycle": 5.0, "symmetry": 5.0, "thickness": 1.0},
}
```

These presets should be registered by the new effect class in the same manner
as earlier generators (see e.g. `PerlinEffect` spec).

## CPU Fallback

The Python fallback (used when OpenGL is not available) must compute the
fragColor for each pixel with NumPy.  The algorithm is a direct translation of
the GLSL listing above; the unit tests will exercise the CPU path to
validate each parameter mapping and loop iteration.

## Testing Plan

1. **Instantiation**: create `HarmonicPatternsGen()` and assert
   `name == "harmonic_patterns"` and effect_category is `generator`.
2. **Parameter boundaries**: set each parameter to 0, 5, and 10 and verify the
   internal remapped value lies within expected range.
3. **Consistency**: render a 4×4 image with the GPU shader and with the CPU
   fallback; compute mean absolute difference < 1e-5.
4. **Symmetry invariants**: for given parameters, flip horizontal/vertical
   coordinates and ensure symmetry parameter >1 restores equality.
5. **Animation**: advance `time` by known increments, check that rotation and
   colour cycle produce non‑identical frames.
6. **Presets**: load each preset and verify the corresponding named dictionary
   matches the class `PRESETS` table.

## Edge Cases & Safety

- `harmonics` U.I. at 0 still produces one ring (mapping ensures ≥1).  The
  loop robustly breaks when `h > nHarm`.
- `decay` at 0 results in `dk=0.3` – prevents division by zero / negative
  powers.
- `symmetry` < 1 is clamped to 1 so no divide‑by‑zero in sector computation.
- `thickness` has a lower bound of 0.01 to avoid `smoothstep(0.0,0.0,…)` edge
  case.
- `mix` outside [0,10] should be clamped by the `Effect` base class.
- Overly large `nHarm` is capped at 16 by both remap and loop condition.

## Performance & Safety Rail Notes

- The inner harmonic loop iterates a maximum of 16 times; branch on
  `nHarm` prevents unnecessary work.
- Most math uses `float` operations; no expensive texture lookups except the
  final mix with `tex0`.
- Default parameter ranges guarantee numerical stability.
