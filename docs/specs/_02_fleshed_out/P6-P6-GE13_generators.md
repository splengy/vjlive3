# Spec: P6-GE13 — Perlin Noise Generator

**File naming:** `docs/specs/P6-P6-GE13_generators.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-GE13 — generators

**What This Module Does**  
`PerlinEffect` produces smooth gradient noise (Perlin noise) with optional ridging, billowing, and turbulence. The output is a tileable procedural texture used for organic backgrounds, displacement maps, or blending in other effects.

**What This Module Does NOT Do**  
- Generate deterministic pseudo‑random numbers outside of noise
- Provide 3‑D noise; strictly 2‑D pattern generation
- Load or sample external textures
- Offer audio analysis or direct MIDI control

---

## Public Interface

```python
class PerlinEffect:
    def __init__(self, frame_width: int, frame_height: int) -> None: ...
    def process_frame(self, input_frame: np.ndarray) -> np.ndarray: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def reset(self) -> None: ...
    def stop(self) -> None: ...
```

Helpers:
```python
    def set_palette(self, hue: float) -> None: ...  # convenience for color_hue mapping
```

---

## Inputs and Outputs

| Name         | Type       | Description                                             | Constraints                          |
|--------------|------------|---------------------------------------------------------|--------------------------------------|
| `frame_width`  | `int`      | Output buffer width                                     | 64–4096                              |
| `frame_height` | `int`      | Output buffer height                                    | 64–4096                              |
| `input_frame`  | `np.ndarray` | RGB input for compositing                              | uint8, shape (H,W,3)                 |
| `speed`        | `float`    | Animation velocity                                       | 0.0–10.0 → 0.0–2.0 multiplier        |
| `scale`        | `float`    | Spatial frequency                                        | 0.0–10.0 → 0.5–30.0 units            |
| `octaves`      | `float`    | Number of noise layers                                   | 0.0–10.0 → 1–8 (integer)             |
| `persistence`  | `float`    | Amplitude falloff between octaves                        | 0.0–10.0 → 0.1–0.9                   |
| `ridging`      | `float`    | Ridge/billow control (0=smooth,5=ridged,10=billowed)    | 0.0–10.0                             |
| `turbulence`   | `float`    | Domain distortion amplitude                              | 0.0–10.0 → 0.0–2.0                   |
| `color_hue`    | `float`    | Base hue for HSV mapping                                 | 0.0–10.0 → 0.0–1.0                   |
| `mix`          | `float`    | Blend ratio with input color                             | 0.0–1.0                              |

---

## Detailed Behavior

Let `uv = (x,y)` ∈ [0,1]^2. The shader computes Perlin noise `n(uv)` with the following steps:

1. **Time and coordinate scaling**
   \[ t = time \cdot (\frac{speed}{10} \cdot 2) \]
   \[ p = uv \cdot (0.5 + scale/10 \cdot 29.5) \]
   making spatial range [0.5,30].

2. **Turbulence warp**
   If `T = turbulence/10 \cdot 2` > 0, then apply
   \[ p += T \cdot \nabla n(p + t) \] approximated in shader via successive noise samples offset by sin/cos to create swirling distortions; this increases apparent complexity.

3. **Octave summation**
   Choose integer \(O = \lfloor 1 + octaves/10 \cdot 7 \rfloor\) ∈ [1,8].
   \[
   n = 0,\quad amp = 1,\quad freq = 1
   \\
   	ext{for }i=1..O:\qquad n += amp \cdot perlin(p \cdot freq + t)
   \\
   amp *= persistence/10 \cdot 0.8 + 0.2
   \\
   freq *= 2
   \]
   `perlin()` returns value in [-1,1]; after loop `n` is normalized to [0,1].

4. **Ridging/billowing**
   Let `R = ridging/10`. The shader implements:
   \[
   	ext{if }R < 0.5:\quad n = mix(n, 1-abs(2n-1), 2R) \quad	ext{(smooth→ridged)}
   \\
   	ext{else}:\quad n = mix(n, abs(2n-1), 2(R-0.5)) \quad	ext{(ridged→billowed)}
   \]
   (This matches classical ridged and billowed Perlin transforms.)

5. **Color mapping**
   Hue offset \(h = color
t_hue/10\) is added to the normalized noise value in HSV space:
   \[
   color = hsv2rgb(\begin{pmatrix}n + h \\ 0.6 + 0.4 n \\ n\end{pmatrix}).
   \]
   The shader iterates `for (int i=0;i<3;i++)` to tint three overlapping channels, producing teal‑pink gradients.

6. **Output blending**
   \[ fragColor = mix(input
t_color, vec4(color,1.0), mix); \]

The CPU fallback executes identical math with NumPy's `linspace`, `sin`, `cos` and a pure‑Python Perlin implementation; results are bit‑for‑bit equal within floating‑point error.

---

## Edge Cases and Error Handling

- **Missing `numpy`**: raise `RuntimeError` during instantiation; plugin refuses to load.
- **GPU unavailable**: automatically use CPU path. Performance warning logged.
- **Parameter clamping**: any slider out of range is silently clamped then logged (e.g., `scale` > 10 ⇒ 10).
- **Zero-size buffers**: `ValueError` thrown if width or height ≤0.
- **Turbulence severe warp**: if distortion exceeds internal threshold, noise sample coordinates are clipped to avoid NaNs.
- **Cleanup**: `stop()` frees GPU program; repeated calls no-op.

---

## Dependencies

- **External**
  - `numpy` — used for CPU fallback and tests.  If absent plugin fails to initialize.
- **Internal**
  - `vjlive3.render.perlin` (utility module providing perlin_gradient, fade, etc.)
  - `vjlive3.plugins.base.Effect`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_gpu` | CPU fallback produces output without crash |
| `test_parameter_map` | Slider values map correctly to scale/octaves/etc. |
| `test_octaves_persistence` | increasing octaves adds detail; persistence attenuates amplitude |
| `test_ridging_billowing` | transitions between smooth, ridged, billowed noise |
| `test_turbulence_distortion` | noise domain warps when turbulence nonzero |
| `test_color_mapping` | color_hue shifts hue linearly |
| `test_mix_blend` | mix parameter blends with dummy frame |
| `test_invalid_dims` | errors on zero or negative dimensions |
| `test_missing_numpy` | instantiation fails without numpy installed |
| `test_shader_match_cpu` | GPU output matches CPU to 1e-6 for random coords |
| `test_legacy_visual_match` | compare rendered frames to legacy reference images |

Coverage target: ≥80 %.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] File <750 lines
- [ ] No stubs
- [ ] Verification checkpoint checked
- [ ] Git commit `[Phase-6] P6-GE13: generators - port Perlin from vjlive/plugins/vcore/generators.py`
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note
- [ ] Easter Egg submitted

---

## Legacy Code References

### Shader excerpt (v1 code)
```glsl
uniform float speed;       // 0-10 → 0-2
uniform float scale;       // 0-10 → 0.5-30
uniform float octaves;     // 0-10 → 1-8
uniform float persistence; // 0-10 → 0.1-0.9
uniform float ridging;     // 0-10 → 0=smooth, 5=ridged, 10=billowed
uniform float turbulence;  // 0-10 → 0-2 domain distortion
uniform float color_hue;   // 0-10 → 0-1 hue

float perlin(vec2 p);

void main() {
    vec4 input_color = texture(tex0, uv);
    float t = time * (speed/10.0 * 2.0);
    float S = 0.5 + scale/10.0 * 29.5;
    int O = int(octaves/10.0 * 7.0 + 1.0);
    float P = persistence/10.0 * 0.8 + 0.2;
    float R = ridging/10.0;
    float T = turbulence/10.0 * 2.0;
    float h = color_hue/10.0;

    vec2 p = uv * S;
    if (T > 0.0) {
        vec2 ngrad = vec2(
            perlin(p + vec2(1.7,9.2)) - perlin(p - vec2(3.3,4.7)),
            perlin(p + vec2(5.1,2.8)) - perlin(p - vec2(2.2,7.6))
        );
        p += T * ngrad;
    }

    float n = 0.0;
    float amp = 1.0;
    float freq = 1.0;
    for (int i=0;i<O;i++) {
        n += amp * perlin(p * freq + t);
        amp *= P;
        freq *= 2.0;
    }
    n = n * 0.5 + 0.5;

    if (R < 0.5) {
        n = mix(n, 1.0 - abs(2.0*n - 1.0), R*2.0);
    } else {
        n = mix(n, abs(2.0*n - 1.0), (R-0.5)*2.0);
    }

    vec3 color;
    for (int i=0;i<3;i++) {
        float hue = fract(n + h + float(i)*0.3);
        color += hsv2rgb(vec3(hue, 0.6 + n*0.4, n));
    }
    color /= 3.0;

    fragColor = mix(input_color, vec4(color,1.0), u_mix);
}
```

### Python class snippet
```python
class PerlinEffect(Effect):
    """Perlin noise — gradient noise with ridging, billowing, turbulence."""

    def __init__(self):
        super().__init__("perlin", PERLIN_FRAGMENT)
        self.parameters = {
            "speed": 0.6,
            "scale": 2.0,
            "octaves": 5.0,
            "persistence": 5.0,
            "ridging": 0.0,
            "turbulence": 0.0,
            "color_hue": 0.0,
        }
```

---

## Verification Checkpoints

- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum
- [ ] Test coverage ≥80%
- [ ] No safety rail violations
- [ ] Original functionality verified (side-by-side comparison)

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

---

