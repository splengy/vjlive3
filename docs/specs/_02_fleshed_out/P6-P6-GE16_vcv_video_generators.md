# P6-GE16: vcv_video_generators (FM-OP)

> **Task ID:** `P6-GE16`  
> **Priority:** P0 (Critical)  
> **Source:** vjlive (`plugins/vcore/vcv_video_generators.py`)  
> **Class:** `FMCoordinatesGen`  
> **Phase:** Phase 6  
> **Status:** ⚙️ In Progress  

## Mission Context

`FMCoordinatesGen` (the FM-OP module in VCV Rack terminology) is a procedural
generator that applies **frequency modulation (FM) synthesis** to 2D coordinate
space. It renders evolving, bell‑like and metallic patterns by computing
sinusoidal modulation of a carrier wave using polar coordinates (distance and
angle), operator feedback, and variable routing algorithms. The result is rich,
non‑repeating geometry perfect for musical synchronisation and visual
performance contexts.

Unlike harmonic patterns (which draw concentric rings), FM coordinates produces
intricate **beat patterns and quasi‑periodic warping** that responds to carrier
frequency, modulator frequency, modulation index, and feedback ratio.

## Behavioural Overview

The effect is **generator‑only** by default but supports input texture blending
via the **mix** parameter.  Time progression continuously animates the pattern
via the modulator and feedback oscillations.

High‑level processing:

1. **Coordinate setup**: map `uv` from [0,1] to [-1,1], apply aspect correction.
2. **Parameter remapping**: convert eight 0‑10 UI sliders into typed variables
   with specific ranges (carrier and modulator frequencies, modulation index,
   feedback depth, algorithm selector, frequency ratio, brightness, colourmap).
3. **Operator 2 (modulator)**: compute sinusoidal modulation at `mod_freq`,
   scaled by distance and angle, with time‑based animation.
4. **Operator 1 (carrier)**: compute sinusoidal carrier at `carrier_freq`,
   modulated by operator 2's output (FM depth), with self‑feedback.
5. **Colouring**: map output amplitude or phase to hue; apply colourmap
   selection (rainbow, monochrome, thermal).
6. **Mix**: blend generated colour with original texture.

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
uniform float carrier_freq;   // carrier frequency
uniform float mod_freq;       // modulator frequency
uniform float mod_index;      // FM depth (modulation index)
uniform float feedback;       // operator self-modulation
uniform float algorithm;      // routing selector (0-10 → different mixes)
uniform float ratio;          // frequency ratio between operators
uniform float brightness;     // output brightness scale
uniform float color_mode;     // 0=rainbow, 5=monochrome, 10=thermal

// [hsv2rgb helper omitted for brevity]

void main() {
    // coordinate setup
    vec2 p = (uv - 0.5) * 2.0;
    float aspect = resolution.x / resolution.y;
    p.x *= aspect;

    // parameter remapping
    float cf = 1.0 + carrier_freq / 10.0 * 30.0;   // [1, 31]
    float mf = 0.5 + mod_freq / 10.0 * 20.0;       // [0.5, 20.5]
    float mi = mod_index / 10.0 * 10.0;             // [0, 10]
    float fb = feedback / 10.0 * 3.0;               // [0, 3]
    float alg = algorithm / 10.0;                   // [0, 1] (selector)
    float rat = 0.5 + ratio / 10.0 * 4.0;           // [0.5, 4.5]
    float bri = 0.3 + brightness / 10.0 * 0.7;     // [0.3, 1.0]
    float cm = color_mode / 10.0;                   // [0, 1] (selector)

    // FM synthesis in 2D coordinate space
    float dist = length(p);
    float angle = atan(p.y, p.x);

    // Operator 2 (modulator): generates modulation signal
    float op2 = sin(dist * mf * rat + time * 2.0 + angle * 3.0);

    // Operator 1 (carrier): modulated by op2
    // FM equation: y = sin( cf * angle + mi * op2 + time + fb * prev )
    // Here we apply feedback by mixing op2 back into the carrier phase
    float op1 = sin(cf * angle + mi * op2 * dist + time + fb * op2);

    // Mix operators based on algorithm selector (0-1 interpolation)
    float val = mix(op1, op2, alg);

    // Clamp and apply brightness
    val = clamp(val * bri, 0.0, 1.0);

    // Apply colouring based on color_mode
    vec3 col;
    if (cm < 0.33) {
        // Rainbow: hue from FM value
        float hue = fract(val + time * 0.05);
        col = hsv2rgb(vec3(hue, 0.9, val));
    } else if (cm < 0.66) {
        // Monochrome
        col = vec3(val);
    } else {
        // Thermal: pseudo‑thermal false colour
        col = vec3(val * 1.5, val * val, val * val * val * 0.5);
        col = clamp(col, 0.0, 1.0);
    }

    vec4 original = texture(tex0, uv);
    fragColor = mix(original, vec4(col, 1.0), u_mix / 10.0);
}
```

**Key equations**:
- Operator 2 drives modulation: phase = `dist * mf * rat + time * 2.0 + angle * 3.0`
- Operator 1 (carrier): phase = `cf * angle + mi * op2 * dist + time + fb * op2`
- Mixing: `val = lerp( op1, op2, algorithm / 10 )`
- Brightness scaling and clamping ensure numerical stability.

## Public API

| Parameter | Type | Description | UI Range | Shader Mapping |
|-----------|------|-------------|----------|----------------|
| carrier_freq | float | Carrier oscillation frequency | 0–10 | `1 + x/10*30` |
| mod_freq | float | Modulator oscillation frequency | 0–10 | `0.5 + x/10*20` |
| mod_index | float | FM depth (modulation intensity) | 0–10 | `x/10*10` |
| feedback | float | Self‑feedback depth | 0–10 | `x/10*3` |
| algorithm | float | Operator routing selector | 0–10 | `x/10` (linear for mix) |
| ratio | float | Frequency ratio (mod ÷ carrier) | 0–10 | `0.5 + x/10*4` |
| brightness | float | Output amplitude scale | 0–10 | `0.3 + x/10*0.7` |
| color_mode | float | Colourmap mode (rainbow/mono/thermal) | 0–10 | `x/10` (selector) |
| mix | float | Blend with input texture | 0–10 | direct, 0–10 range |

Effect category: `generator`  
GPU tier: `BASIC`  
Legacy name: FM-OP (VCV Rack module)

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

## CPU Fallback

NumPy-based reference implementation shall mirror the GLSL code exactly,
computing each pixel's four‑component color. Unit tests will compare CPU and
GPU paths for numerical agreement (tolerence ±1e-5).

## Testing Plan

1. **Instantiation**: create `FMCoordinatesGen()` with correct name and category.
2. **Parameter ranges**: verify each 0‑10 slider maps to internal remapped value.
3. **GPU/CPU consistency**: render identical pixel with both paths; mean error < 1e-5.
4. **Algorithm selector**: test `algorithm=0`, `5`, `10` and confirm mixing behavior.
5. **Colouring modes**: test `color_mode` transitions (rainbow → mono → thermal).
6. **Presets**: load each preset and verify parameters match table.
7. **Time animation**: advance time by known steps; confirm non‑static output.

## Edge Cases & Safety

- All frequencies (cf, mf) are positive; no division by zero.
- Feedback is clamped to [0,3] to avoid divergence.
- Brightness scale [0.3,1.0] prevents over/underflow.
- Modulation index [0,10] avoids extreme FM sidebands that could alias.
- Algorithm [0,1] interpolation is linear and well‑defined.
- Colourmode selector: cm < 0.33 → rainbow; 0.33–0.66 → mono; > 0.66 → thermal.

## Performance & Safety Rails

- Inner loops compute sin() and basic arithmetic only; no expensive lookups.
- Clamping at the output prevents NaN propagation.
- All math uses standard `float` precision.
