# Spec: P6-GE12 — Plasma Generator

**File naming:** `docs/specs/P6-P6-GE12_generators.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-GE12 — generators

**What This Module Does**  
`PlasmaEffect` synthesizes classic demo‑scene plasma patterns by summing multiple drifting sine waves and mapping the result through several color palettes. It produces a smoothly animated, high‑contrast texture ideal for backdrops and datamosh effects.

**What This Module Does NOT Do**  
- Decode video or audio input  
- Perform any 3‑D rendering or geometry processing  
- Load external images or textures (pattern is fully procedural)  
- Expose OSC/MIDI control directly (handled by host layer)  
- Provide GPU compute beyond a simple fragment shader; no compute buffers

---

## Public Interface

```python
class PlasmaEffect:
    def __init__(self, frame_width: int, frame_height: int) -> None: ...
    def process_frame(self, input_frame: np.ndarray) -> np.ndarray: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def reset(self) -> None: ...
    def stop(self) -> None: ...
```

Parameters are the same strings used in the original vjlive code. The effect will also expose a `set_palette(List[Tuple[float,float,float]])` helper for user‑supplied palettes.

---

## Inputs and Outputs

| Name         | Type       | Description                                     | Constraints                          |
|--------------|------------|-------------------------------------------------|--------------------------------------|
| `frame_width`  | `int`      | Width of video buffer                           | 64–4096                              |
| `frame_height` | `int`      | Height of video buffer                          | 64–4096                              |
| `input_frame`  | `np.ndarray` | RGB input image                                 | uint8, (H,W,3)                       |
| `speed`        | `float`    | Animation time multiplier                       | 0.0–10.0 → maps to 0.0–3.0 factor    |
| `scale`        | `float`    | Spatial frequency multiplier                    | 0.0–10.0 → 1.0–20.0 units            |
| `complexity`   | `float`    | Number of sine layers                           | 0.0–10.0 → 2–12 (integer)            |
| `color_speed`  | `float`    | Palette animation rate                          | 0.0–10.0 → 0.0–3.0 Hz                |
| `distortion`   | `float`    | Warp amplitude applied to coordinates           | 0.0–10.0 → 0.0–2.0 units             |
| `palette`      | `float`    | Palette selector                                | 0.0–10.0 (0‑5 classic/HSV, 5‑10 neon, 10 fire)
| `mix`          | `float`    | Blend amount with `input_frame`                 | 0.0–1.0                              |

---

## Detailed Behavior

Let `uv = (x,y)` be the normalized texture coordinate with origin at the lower-left and range [0,1].

1. **Pre‑warp coordinates**
   \[
   p = (uv - 0.5) \cdot S,
   \] where
   \(S = 1 + 19\cdot(\text{scale}/10)\) maps the `scale` slider to a spatial frequency between 1 and 20 cycles per unit.

   If distortion \(D = 2\cdot(\text{distortion}/10)\) is nonzero then
   \[
   p \mathrel{+}= D \begin{pmatrix}
       \sin(p.y + \omega t) \\ 
       \sin(p.x + \omega t)
   \end{pmatrix},
   \] with \(\omega = 3\cdot(\text{speed}/10)\) and time \(t\) in seconds.  This produces the characteristic warping of the grid.

2. **Wave summation**
   Let \(N = 2 + \left\lfloor 10 \cdot \frac{\text{complexity}}{10} \right\rfloor\) be the integer layer count (range 2–12).  Then compute
   \[
   v = \frac{1}{4N} \sum_{k=1}^{N} 
        \Big[ \sin(k \cdot p_x + \omega t) 
            + \sin(k \cdot p_y + \alpha_k \omega t) 
            + \sin(k(p_x+p_y) + \beta_k \omega t) 
            + \sin(\sqrt{p_x^2+p_y^2}\, k + \gamma_k \omega t)
        \Big],
   \] where coefficients \(\alpha_k,\beta_k,\gamma_k\) are fixed irrational offsets (e.g., 1.3, 0.7, 2.1) hard‑coded in the original shader to break symmetry.  The result \(v\) lies in \([-1,1]\); we remap to \([0,1]\) via
   \( 	exttt{val} = 0.5 + 0.5 v. \)

3. **Color computation**
   A second time variable \(c = 3\cdot(\text{color
t_speed}/10)\) drives palette cycling. The default palette range is HSV:
   \[
   \texttt{hue} = \operatorname{fract}(\texttt{val} + c t),
   \texttt{color} = \operatorname{hsv2rgb}(\texttt{hue},1,1).
   \]

   If `palette` falls between 5 and 10 a _neon_ scheme is used: the HSV value is desaturated and boosted with a sinusoidal glow.
   When `palette == 10` the shader selects the fire palette:
   \[
   \texttt{color} = 
       \begin{pmatrix}
       \operatorname{smoothstep}(0.0,0.4,\texttt{val}) \\ 
       0.8\operatorname{smoothstep}(0.2,0.7,\texttt{val}) \\ 
       0.5\operatorname{smoothstep}(0.5,1.0,\texttt{val})
       \end{pmatrix}
       + 0.05\sin(c t)\begin{pmatrix}1\\0\\0\end{pmatrix}.
   \]
   The shader linearly interpolates between palette zones based on the fractional part of the `palette` slider.

4. **Final blending**
   The fragment color is mixed with the input texture:
   \[ 	exttt{fragColor} = \texttt{mix}( \texttt{input
t_color}, \texttt{vec4(color,1)}, \texttt{mix} ). \]

All of the above happens entirely in a single GLSL fragment program; the CPU side merely forwards uniforms.  A CPU fallback computes identical math with NumPy when no GPU is available.

---

## Edge Cases and Error Handling

- **Missing GPU**: fall back to pure‑Python loop using NumPy; results identical to shader within floating‑point precision.
- **Parameter clamping**: `scale` or `complexity` outside [0,10] are clamped; `complexity` < 0 yields 2 layers, >10 yields 12.
- **Zero dimensions**: `frame_width` or `frame_height` ≤0 ⇒ `ValueError`.
- **Palette slider**: values <0 or >10 are clamped to [0,10].
- **Cleanup**: `stop()` releases shader program and any GPU resources; idempotent.

---

## Dependencies

- **External**
  - `numpy` — for CPU fallback and tests.  Already part of base environment; if missing, plugin disables CPU mode and raises `RuntimeError` on instantiation.
- **Internal**
  - `vjlive3.render.shader_utils.hsv2rgb` (inlined in shader for speed)
  - `vjlive3.plugins.base.Effect` base class for uniform management and I/O.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_gpu` | Object constructs without GPU, CPU math path used |
| `test_parameter_mapping` | Slider values map to correct internal constants |
| `test_scale_and_complexity` | Spatial frequency increases, more waves appear |
| `test_distortion` | Nonzero distortion warps pattern as expected |
| `test_palette_zones` | Switching palette slider yields HSV→neon→fire colors |
| `test_color_animation` | color_speed causes hue/time progression |
| `test_speed_animation` | pattern drifts at speed multiplier |
| `test_mix_blend` | mix blends with dummy input frame |
| `test_invalid_dimensions` | raises `ValueError` on zero/negative sizes |
| `test_cleanup_idempotent` | calling `stop()` twice is safe |
| `test_shader_gpu_matches_cpu` | Rendered frame from GPU equals CPU fallback within epsilon |
| `test_legacy_visual_match` | output matches saved reference image from vjlive1

_Mandatory coverage_: ≥80 % lines exercised.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] File <750 lines
- [ ] No stubs
- [ ] Verification checkpoint checked
- [ ] Git commit `[Phase-6] P6-GE12: generators - port plasma from vjlive/plugins/vcore/generators.py`
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note
- [ ] Easter Egg submitted

---

## Legacy Code References

### GLSL fragment (excerpts from `vjlive/plugins/vcore/generators.py`)
```glsl
// uniform declarations as seen earlier
uniform float speed;       // 0-10 → 0-3 time mult
uniform float scale;       // 0-10 → 1-20 frequency
uniform float complexity;  // 0-10 → 2-12 wave layers
uniform float color_speed; // 0-10 → 0-3 palette anim speed
uniform float distortion;  // 0-10 → 0-2 wave warping
uniform float palette;     // 0-10 → 0=classic,5=neon,10=fire

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0,2.0/3.0,1.0/3.0,3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    vec4 input_color = texture(tex0, uv);
    float t = time * (speed/10.0 * 3.0);
    float S = 1.0 + (scale/10.0 * 19.0);
    int N = int(complexity/10.0 * 10.0 + 2.0);
    float cs = color_speed/10.0 * 3.0;
    float D = distortion/10.0 * 2.0;

    vec2 p = (uv - 0.5) * S;
    if (D > 0.0) {
        p += D * vec2(sin(p.y + t), sin(p.x + t));
    }

    float val = 0.0;
    for (int i=1; i<=N; ++i) {
        float fi = float(i);
        val += sin(p.x * fi + t);
        val += sin(p.y * fi + t * 1.3);
        val += sin((p.x+p.y) * fi + t * 0.7);
        val += sin(length(p) * fi + t * 2.1);
    }
    val = val / (4.0 * float(N));
    val = val * 0.5 + 0.5;

    vec3 color;
    if (palette < 5.0) {
        float hue = fract(val + cs * t);
        color = hsv2rgb(vec3(hue, 1.0, 1.0));
    } else if (palette < 10.0) {
        float hue = fract(val + cs * t);
        color = hsv2rgb(vec3(hue, 0.5, 1.0));
        color *= 1.2 + 0.2 * sin(t * cs);
    } else {
        color = vec3(
            smoothstep(0.0,0.4,val),
            smoothstep(0.2,0.7,val)*0.8,
            smoothstep(0.5,1.0,val)*0.5
        );
        color += vec3(0.05,0.0,0.0) * sin(t * cs);
    }

    fragColor = mix(input_color, vec4(color,1.0), u_mix);
}
```

### Python class snippet
```python
class PlasmaEffect(Effect):
    """Plasma — multi-frequency interference with palette control."""

    def __init__(self):
        super().__init__("plasma", PLASMA_FRAGMENT)
        self.parameters = {
            "speed": 1.0,
            "scale": 3.0,
            "complexity": 4.0,
            "color_speed": 1.0,
            "distortion": 0.0,
            "palette": 0.0,
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

