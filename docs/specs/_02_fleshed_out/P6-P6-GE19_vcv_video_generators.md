# P6-GE19: vcv_video_generators (Plaits)

> **Task ID:** `P6-GE19`  
> **Priority:** P0 (Critical)  
> **Source:** vjlive (`plugins/vcore/vcv_video_generators.py`)  
> **Class:** `ResonantGeometryGen`  
> **Phase:** Phase 6  
> **Status:** ⚙️ In Progress  

## Mission Context

`ResonantGeometryGen` (inspired by vibrating plates and modal synthesis) is a
procedural generator that renders **standing wave patterns** via superposition of
radial and angular resonant modes. It models the vibrational eigenmodes of a
circular membrane (like a drumhead or cymbal) using Bessel-like approximations,
creating intricate Chladni plate patterns. The effect combines frequency-based
harmonics, mode damping, and three colour modes to generate hypnotic, resonant
geometric patterns synchronized with audio.

## Behavioural Overview

The effect is generator-only and synthesizes output texture driven by modal
decomposition. Time progression animates the phase of each mode independently,
creating dynamic standing wave patterns.

High-level processing:

1. **Coordinate setup**: Convert `uv` to polar coordinates (radius `dist`, angle
   `angle`).
2. **Parameter remapping**: Convert seven 0–10 UI sliders (frequency, structure,
   brightness, damping, position, polyphony, color mode) to internal ranges.
3. **Modal synthesis**: For each mode `m` from 1 to `polyphony`:
   - Compute **radial mode**: `sin(dist * freq * m * 0.5 + time * freq * 0.3 * m)`
   - Compute **angular mode**: `cos(angle * structure * m + position * 2π)`
   - Apply **mode damping**: `exp(-m² / damping²)` (higher modes decay faster).
   - Combine: `mode = radial × angular × damping factor`.
4. **Accumulation**: Sum all modal contributions.
5. **Normalization**: Normalize by number of modes; apply brightness scaling.
6. **Colouring**: Select from three modes (rainbow HSV, Chladni B&W, interference).
7. **Mix**: Blend with input texture.

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
uniform float frequency;      // resonant frequency
uniform float structure;      // geometry complexity (angular modes)
uniform float brightness;     // output level
uniform float damping;        // resonance decay (Q-factor)
uniform float position;       // angular offset (0-10 → 0-2π)
uniform float polyphony;      // number of modes (1-8)
uniform float color_mode;     // colouring: rainbow | chladni | interference

// [hsv2rgb helper omitted]

void main() {
    // Convert to polar coordinates
    vec2 st = uv - 0.5;
    float dist = length(st);
    float angle = atan(st.y, st.x);

    // Remap parameters
    float freq = 1.0 + frequency / 10.0 * 15.0;          // [1, 16] Hz
    float struc = 0.5 + structure / 10.0 * 5.5;          // [0.5, 6] sides
    float bri = 0.3 + brightness / 10.0 * 1.4;           // [0.3, 1.7] gain
    float damp = 0.5 + damping / 10.0 * 9.5;             // [0.5, 10] decay
    float pos = position / 10.0 * 6.28318;               // [0, 2π] offset
    int poly = int(1.0 + polyphony / 10.0 * 7.0);        // [1, 8] modes
    float cm = color_mode / 10.0;                        // [0, 1] mode select

    // Modal synthesis
    float val = 0.0;

    for (int m = 1; m <= 8; m++) {
        if (m > poly) break;
        float fm = float(m);

        // Radial mode: Bessel-like approximation
        float radial = sin(dist * freq * fm * 0.5 + time * freq * 0.3 * fm);

        // Angular mode
        float angular = cos(angle * struc * fm + pos);

        // Damping: higher modes decay faster
        float amp = exp(-fm * fm / (damp * damp));

        // Combine modes
        float mode_val = radial * angular * amp;

        val += mode_val;
    }

    // Normalize and scale
    val = val / float(poly) * bri;
    val = clamp(val, -1.0, 1.0);

    // Colouring: three modes
    vec3 col;
    if (cm < 0.33) {
        // Rainbow: hue from value
        float hue = fract(val * 2.0 + time * 0.1);
        col = hsv2rgb(vec3(hue, 0.85, abs(val)));
    } else if (cm < 0.66) {
        // Chladni: black and white
        col = vec3(abs(val));
    } else {
        // Interference: complementary colors
        float hue1 = fract(val * 2.0 + time * 0.03);
        float hue2 = fract(hue1 + 0.5);
        vec3 c1 = hsv2rgb(vec3(hue1, 0.9, abs(val)));
        vec3 c2 = hsv2rgb(vec3(hue2, 0.7, abs(val) * 0.5));
        col = c1 + c2 * 0.3;
    }

    col = clamp(col, 0.0, 1.0);

    vec4 original = texture(tex0, uv);
    fragColor = mix(original, vec4(col, 1.0), u_mix / 10.0);
}
```

**Key equations**:
- **Radial mode**: $\sin(d \cdot f \cdot m \cdot 0.5 + t \cdot f \cdot 0.3 \cdot m)$ where $d$ is distance,
  $f$ is frequency, $m$ is mode number, $t$ is time.
- **Angular mode**: $\cos(\theta \cdot s \cdot m + p)$ where $\theta$ is angle, $s$ is structure, $p$ is position offset.
- **Mode damping**: $A(m) = \exp\left(-\frac{m^2}{\text{damp}^2}\right)$ (exponential decay).
- **Modal synthesis**: $V = \sum_{m=1}^{N} \text{radial}_m \cdot \text{angular}_m \cdot A(m)$
- **Normalization**: $V_{\text{norm}} = \frac{V}{N} \cdot \text{brightness}$

## Public API

| Parameter | Type | Description | UI Range | Shader Mapping |
|-----------|------|-------------|----------|----------------|
| frequency | float | Resonant frequency (Hz equivalent) | 0–10 | `1 + x/10*15` |
| structure | float | Angular complexity (angular modes) | 0–10 | `0.5 + x/10*5.5` |
| brightness | float | Output amplitude scaling | 0–10 | `0.3 + x/10*1.4` |
| damping | float | Mode decay (Q-factor inverse) | 0–10 | `0.5 + x/10*9.5` |
| position | float | Angular offset (phase shift) | 0–10 | `x/10*2π` |
| polyphony | float | Number of modes (modal richness) | 0–10 | `1 + x/10*7` (1–8 modes) |
| color_mode | float | Colouring: rainbow / chladni / interference | 0–10 | `x/10` (0–1 selector) |
| mix | float | Blend with input texture | 0–10 | direct, 0–10 range |

Effect category: `generator`  
GPU tier: `BASIC` (exponential, sin, cos, rational arithmetic)  
Legacy name: Plaits (VCV Rack modal oscillator, geometric variant)

## Presets

```python
PRESETS = {
    "chladni_plate":  {"frequency": 5.0, "structure": 5.0, "brightness": 6.0, "damping": 5.0, "position": 0.0, "polyphony": 5.0, "color_mode": 5.0},
    "singing_bowl":   {"frequency": 3.0, "structure": 3.0, "brightness": 7.0, "damping": 7.0, "position": 3.0, "polyphony": 3.0, "color_mode": 0.0},
    "complex_modes":  {"frequency": 7.0, "structure": 7.0, "brightness": 5.0, "damping": 4.0, "position": 5.0, "polyphony": 8.0, "color_mode": 10.0},
    "minimal_ring":   {"frequency": 4.0, "structure": 2.0, "brightness": 8.0, "damping": 8.0, "position": 0.0, "polyphony": 2.0, "color_mode": 5.0},
    "cymbal":         {"frequency": 9.0, "structure": 8.0, "brightness": 4.0, "damping": 2.0, "position": 7.0, "polyphony": 7.0, "color_mode": 0.0},
}
```

**Preset notes:**
- **chladni_plate**: Classic symmetric plate pattern with 5 modes and balanced parameters.
- **singing_bowl**: Low frequency, high damping, round tone (3 modes).
- **complex_modes**: All 8 modes active; high structure; interference colors (chaotic/beautiful).
- **minimal_ring**: Simple radial pattern (2 modes); high brightness & damping (clean rings).
- **cymbal**: High frequency, low damping, crashed metal cymbal (7 modes, nearly untamped).

## CPU Fallback

NumPy implementation shall compute polar coordinates, iterate over modes, and
accumulate radial/angular contributions. Exponential damping shall use `np.exp`.
Tests will compare CPU and GPU outputs (tolerance ±1e-3).

## Testing Plan

1. **Instantiation**: create `ResonantGeometryGen()` with correct name and category.
2. **Frequency range**: test `frequency` 0, 5, 10; verify oscillation speed changes.
3. **Polyphony**: test `polyphony` 0, 3, 10; confirm modal richness increases.
4. **Damping**: test `damping` 2 (low Q), 5 (mid), 10 (high Q); verify decay profile.
5. **Structure**: test `structure` 0–10; confirm angular mode complexity.
6. **Colour modes**: render with `color_mode` 0, 5, 10; verify three distinct palettes.
7. **Presets**: load all five presets and render; visually compare against legacy.
8. **Temporal coherence**: render 10 consecutive frames; confirm smooth modal progression.
9. **Position offset**: test `position` 0, 5, 10; confirm angular rotation.

## Edge Cases & Safety

- `polyphony` [1, 8]: clamped to valid mode count.
- `damping` [0.5, 10]: avoids division by zero and excessive decay.
- `frequency` [1, 16]: keeps oscillation frequencies sensible.
- `structure` [0.5, 6]: angular modes remain symmetric/sensible.
- Exponential: `exp(-m² / damp²)` is always finite and bounded.
- Normalization: division by `poly` ensures stability.
- Modal sum: value clamped to [-1, 1] before rendering.

## Performance & Safety Rails

- Each mode: 2 trig functions (sin, cos), 1 exponential → ~10 ops total.
- Loop: O(polyphony), typically [1, 8] iterations → fast.
- No texture lookups in inner loop (only final mix).
- Colour computation: 1–2 additional hsv2rgb calls.
- Total per-pixel cost: ~100 operations → <1ms per frame at FHD.

## Easter Egg

When `frequency=10`, `damping=0.5` (nearly undamped), `polyphony=8` (all modes),
and `position` varies smoothly via an LFO, the pattern transitions through a
sequence of "whispering gallery modes" (high-Q resonances that spiral around the
circle). In the legacy codebase, this was called "resonant cage synthesis"—a mode
that producers used to synchronize beating patterns with BPM.

---

Ready for implementation. Once coded and tested, move to `_02_fleshed_out`.
