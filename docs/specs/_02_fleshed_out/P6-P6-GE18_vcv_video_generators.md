# P6-GE18: vcv_video_generators (Plaits)

> **Task ID:** `P6-GE18`  
> **Priority:** P0 (Critical)  
> **Source:** vjlive (`plugins/vcore/vcv_video_generators.py`)  
> **Class:** `GranularVideoGen`  
> **Phase:** Phase 6  
> **Status:** ⚙️ In Progress  

## Mission Context

`GranularVideoGen` (inspired by granular synthesis and pointillist painting) is a
procedural texture generator that creates organic, grain-like patterns by
layering and blending semi-random grain particles across the image. Each grain
is seeded from a texture coordinate, assigned a size from noise, and blended
additively with colour scatter and temporal animation. The effect is ideal for
mimicking paint splatters, bokeh dof, cloud formations, and glitchy organic
erosion effects.

## Behavioural Overview

The effect is generator-only and synthesizes output texture. Time progression
animates the grain distribution and colour cycling, creating living, flowing
patterns.

High-level processing:

1. **Coordinate setup**: Normalise `uv` and scale for grain frequency.
2. **Parameter remapping**: Convert seven 0–10 UI sliders (density, grain size,
   position, texture param, spread, freeze, color scatter) to internal ranges.
3. **Grain generation**: Use value/Perlin noise to select grain positions and
   sizes; iterate over multiple layers (Poisson distribution approximation).
4. **Grain rendering**: For each grain, compute distance to centre; render as smooth
   circle via smoothstep with optional color scatter and hue shift.
5. **Temporal animation**: Advance grain phase via `time * animate` (grain_size,
   position, and colour offset change smoothly).
6. **Accumulation**: Accumulate grain contributions (additive blend with colour).
7. **Rendering**: Normalise by accumulated weight; apply tone curve (clamp 0–1).
8. **Mix**: Blend with input texture via `u_mix`.

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
uniform float density;        // grain density (spawn count per frame)
uniform float grain_size;     // base grain size (radius)
uniform float position;       // grain spawn position (texture read offset)
uniform float texture_param;  // grain texture character (smooth → sharp)
uniform float spread;         // spatial spread / variance
uniform float freeze;         // disable animation (0 → 10 = stationary)
uniform float color_scatter;  // per-grain colour randomness

// [hsv2rgb helper function omitted]

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);  // smoothstep interpolation
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    float u = mix(a, b, f.x);
    float v = mix(c, d, f.x);
    return mix(u, v, f.y);
}

void main() {
    vec2 p = uv;

    // Remap parameters
    float dens = 2.0 + density / 10.0 * 30.0;             // [2, 32] grains per frame
    float g_size = 0.005 + grain_size / 10.0 * 0.15;      // [0.005, 0.155] radius
    float pos_offset = position / 10.0;                    // [0, 1] offset
    float tex_sharpness = 0.5 + texture_param / 10.0 * 1.5; // [0.5, 2] sharpness
    float sprd = 0.5 + spread / 10.0 * 3.0;               // [0.5, 3.5] variance
    float anim_speed = (10.0 - freeze) / 10.0 * 2.0;      // [0, 2] (frozen → slow)
    float col_var = color_scatter / 10.0;                 // [0, 1] colour variance

    vec3 acc = vec3(0.0);
    float totalWeight = 0.0;

    // Iterate over grain layer(s)
    for (int i = 0; i < int(dens); i++) {
        // Pseudo-random grain position
        vec2 grain_pos = p + vec2(
            noise(vec2(float(i) * 0.5, time * anim_speed * 0.1)),
            noise(vec2(float(i) * 0.7 + 1.0, time * anim_speed * 0.1))
        ) * sprd;

        // Distance from current pixel to grain
        float dist = length(p - grain_pos);

        // Grain size modulated by time and texture_param
        float g = g_size * (0.8 + noise(vec2(float(i), time * anim_speed * 0.2)) * 0.4);

        // Smooth circle via smoothstep
        float grain = smoothstep(g * tex_sharpness, g * 0.8, dist);

        // Small contribution from texture_param → gaussian-like
        if (tex_sharpness > 1.0) {
            grain = pow(grain, tex_sharpness);
        }

        // Colour scatter
        float hueShift = noise(vec2(float(i) * 1.3, time * anim_speed)) * col_var;
        vec3 grainColor = hsv2rgb(vec3(hueShift, 0.5 + col_var * 0.3, 0.8 + grain * 0.2));

        // Accumulate
        acc += grainColor * grain;
        totalWeight += grain;
    }

    // Normalise and tone curve
    vec3 result = totalWeight > 0.01 ? acc / totalWeight : vec3(0.0);
    result = clamp(result, 0.0, 1.0);

    // Mix with input
    vec4 original = texture(tex0, uv);
    fragColor = mix(original, vec4(result, 1.0), u_mix / 10.0);
}
```

**Key equations**:
- Grain count: `dens = 2.0 + density / 10.0 * 30.0` → [2, 32] grains per iteration.
- Grain radius: `g_size = 0.005 + grain_size / 10.0 * 0.15` → [0.005, 0.155].
- Temporal animation: `time * anim_speed` modulates grain position and colour.
- Grain rendering: `smoothstep(g * sharpness, g * 0.8, dist)` creates soft circles.
- Accumulation: additive colour blending with normalisation.
- Texture character: `texture_param` increases smoothness of grain boundary.

## Public API

| Parameter | Type | Description | UI Range | Shader Mapping |
|-----------|------|-------------|----------|----------------|
| density | float | Grain spawn density (count per iteration) | 0–10 | `2 + x/10*30` |
| grain_size | float | Base radius of each grain | 0–10 | `0.005 + x/10*0.15` |
| position | float | Grain spawn position offset | 0–10 | `x/10` (0–1) |
| texture_param | float | Grain boundary sharpness | 0–10 | `0.5 + x/10*1.5` |
| spread | float | Spatial variance / spread | 0–10 | `0.5 + x/10*3.0` |
| freeze | float | Animation freeze (0→animate, 10→static) | 0–10 | `(10-x)/10*2` |
| color_scatter | float | Per-grain colour randomness | 0–10 | `x/10` (0–1) |
| mix | float | Blend with input texture | 0–10 | direct, 0–10 range |

Effect category: `generator`  
GPU tier: `BASIC` (noise and smoothstep are fast)  
Legacy name: Plaits (VCV Rack macro oscillator, granular variant)

## Presets

```python
PRESETS = {
    "soft_cloud":   {"density": 5.0, "grain_size": 5.0, "position": 5.0, "texture_param": 0.0, "spread": 5.0, "freeze": 0.0, "color_scatter": 0.0},
    "pointillist":  {"density": 8.0, "grain_size": 2.0, "position": 5.0, "texture_param": 8.0, "spread": 7.0, "freeze": 0.0, "color_scatter": 3.0},
    "frozen_grains": {"density": 6.0, "grain_size": 4.0, "position": 3.0, "texture_param": 3.0, "spread": 4.0, "freeze": 8.0, "color_scatter": 0.0},
    "dense_scatter": {"density": 10.0, "grain_size": 3.0, "position": 5.0, "texture_param": 5.0, "spread": 9.0, "freeze": 0.0, "color_scatter": 5.0},
    "sparse_bokeh": {"density": 3.0, "grain_size": 8.0, "position": 5.0, "texture_param": 0.0, "spread": 6.0, "freeze": 2.0, "color_scatter": 1.0},
}
```

## CPU Fallback

NumPy implementation shall compute hash-based noise and iterate over grain
positions for each pixel. Smoothstep rendering will be approximated via NumPy
clip and polynomial interpolation. Tests will compare CPU and GPU outputs
(tolerance ±1e-3).

## Testing Plan

1. **Instantiation**: create `GranularVideoGen()` with correct name and category.
2. **Parameter ranges**: test `density` 0, 5, 10; verify grain count changes.
3. **Grain size**: test `grain_size` 0, 5, 10; confirm radius variance.
4. **Animation**: advance time and confirm grain position/colour animation when
   `freeze < 5`; confirm static when `freeze = 10`.
5. **Texture param**: test `texture_param` 0–10; verify boundary sharpness.
6. **Colour scatter**: test `color_scatter` 0, 5, 10; confirm hue variation.
7. **Presets**: load all five presets and verify parameter values.
8. **Temporal coherence**: render with 8 consecutive time steps; confirm smooth
   transitions.

## Edge Cases & Safety

- `density` > 32 is clamped; grain count remains bounded.
- `grain_size` [0.005, 0.155] avoids underflow and over-scale.
- `freeze` = 10 disables time modulation entirely (animation speed → 0).
- `texture_param` [0.5, 2] maintains numeric stability in smoothstep.
- Hash function is deterministic; same seed produces identical results.
- Accumulation weighting: if `totalWeight < 0.01`, output is black (safety fallback).

## Performance & Safety Rails

- Hash-based noise: ~10 operations per grain.
- Smoothstep and distance: ~5 operations per grain.
- Loop: O(dens), typically [2, 32] iterations → fast.
- No expensive texture lookups in inner loop.
- Accumulation: simple floating-point arithmetic.
