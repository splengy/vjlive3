# Spec: P6-GE14 — Silver Visions Path Generator

**File naming:** `docs/specs/P6-P6-GE14_silver_visions.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-GE14 — silver_visions

**What This Module Does**  
`PathGeneratorEffect` paints a moving point along a computed path; the point's X/Y position is encoded into color so that downstream effects can visualize or modulate by trajectory. Four path modes (scanning, boustrophedon, spiral, random) are selectable, with adjustable speed, resolution, and polarity. The effect mimics the classic SilverVisions video synth behavior by generating voltages for an oscilloscope-style display.

**What This Module Does NOT Do**  
- Accept external audio or sensor input  
- Perform arbitrary vector graphics beyond single‑point paths  
- Persist paths between frames (stateless)  
- Provide true randomness beyond the simple GLSL `rand()` generator  

---

## Public Interface

```python
class PathGeneratorEffect:
    def __init__(self, frame_width: int, frame_height: int) -> None: ...
    def process_frame(self, input_frame: np.ndarray) -> np.ndarray: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def reset(self) -> None: ...
    def stop(self) -> None: ...
```

Internally the effect exposes parameter setters mapping to uniforms `uMode, uSpeed, uResolution, uXYPolarity`.  The `apply_uniforms` override adds `uTime` every frame.

---

## Inputs and Outputs

| Name           | Type       | Description                                        | Constraints                          |
|----------------|------------|----------------------------------------------------|--------------------------------------|
| `frame_width`    | `int`      | Width of output buffer                              | 64–4096                              |
| `frame_height`   | `int`      | Height of output buffer                             | 64–4096                              |
| `input_frame`    | `np.ndarray` | RGB image to mix with path color                  | uint8, (H,W,3)                       |
| `mode`           | `float`    | Path algorithm selector                            | 0.0=scan,1.0=boustrophedon,2.0=spiral,3.0=random (slider 0–10 maps to 0–3) |
| `speed`          | `float`    | Path rate multiplier                               | 0.0–10.0 → 0.0–? (raw multiplies time) |
| `resolution`     | `float`    | Grid resolution (side length)                      | 0.0–10.0 → 1–1000 (internally value*100) |
| `xy_polarity`    | `bool`     | Unipolar (false) or bipolar (true) voltage mapping | 0 or 1 (slider 0–10 maps <5 false, ≥5 true) |
| `mix`            | `float`    | Blend amount with input                            | 0.0–1.0                              |

---

## Detailed Behavior

The shader executed per particle is reproduced exactly from legacy code:

1. **Uniform setup**: `res = uResolution`; `mode = uMode`; `speed = uSpeed`; `t = uTime`.
2. **Path calculation** (pseudocode):
   ```glsl
   float x_position = 0.0;
   float y_position = 0.0;
   if (mode == 0.0) { // scanning
       x_position = mod(t * speed, res);
       y_position = floor((t * speed) / res) * speed;
   } else if (mode == 1.0) { // boustrophedon
       float scan_line = floor((t * speed) / res);
       if (mod(scan_line,2.0)==0.0) {
           x_position = mod(t*speed, res);
       } else {
           x_position = res - mod(t*speed, res);
       }
       y_position = scan_line * speed;
   } else if (mode == 2.0) { // spiral
       x_position = res*0.5 + sin(t*speed)*res*0.4;
       y_position = res*0.5 + cos(t*speed)*res*0.4;
   } else if (mode == 3.0) { // random
       if (fract(t*speed) < 0.01) {
           x_position = rand(t) * res;
           y_position = rand(t+1.0) * res;
       }
   }
   ```
   `rand(n)` uses `fract(sin(n)*43758.5453)`.
3. **Voltagelike mapping**: convert coordinates into -5..+5 range if bipolar, otherwise 0..10:
   ```glsl
   float x_volt = 10.0 * x_position / res;
   float y_volt = 10.0 * y_position / res;
   if (!uXYPolarity) { x_volt -= 5.0; y_volt -= 5.0; }
   vec4 path_color = vec4(x_volt/10.0 + 0.5, y_volt/10.0 + 0.5, 0.0, 1.0);
   ```
4. **Output**: mix with input texture via uniform `u_mix`.

The Python side clamps slider inputs, maps them (mode wraps to 0–3, resolution scales by 100), and passes them as uniforms every frame.  `apply_uniforms` also sets `uTime` and converts XY polarity to integer.

---

## Edge Cases and Error Handling

- **GPU missing**: CPU fallback replicates shader math using NumPy; logs warning.
- **Invalid sliders**: `mode` clipped into [0,3] even if slider >3 by wrapping with mod; `resolution` clamped ≥1 and scaled; `xy_polarity` thresholded.
- **Zero resolution**: if `uResolution` <1 after mapping raise `ValueError`.
- **Frame dims zero**: `ValueError` on instantiation.
- **Cleanup**: `stop()` frees shader; safe to call multiple times.

---

## Dependencies

- **External**
  - `numpy` for CPU fallback and tests (fatal if missing).
- **Internal**
  - `vjlive3.render.shader_base.Effect` for base class.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_gpu` | builds with CPU-only environment |
| `test_mode_mapping` | slider correctly selects four modes |
| `test_scanning_path` | x moves linearly, y steps after res units |
| `test_boustrophedon_path` | alternating x direction each line |
| `test_spiral_path` | coordinates oscillate sinusoidally around center |
| `test_random_path` | occasional jumps occur (probabilistic, force by setting t) |
| `test_resolution_scaling` | resolution slider maps to 1–1000 correctly |
| `test_xy_polarity` | output voltage offset toggles correctly |
| `test_mix_blending` | mixing with dummy frame works |
| `test_invalid_params` | errors on negative dimensions or zero res |
| `test_shader_gpu_matches_cpu` | GPU output matches NumPy version to 1e-6 |
| `test_legacy_visual_match` | rendered trajectory matches reference frames |

Coverage ≥80%.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] File <750 lines
- [ ] No stubs
- [ ] Verification checkpoint checked
- [ ] Git commit `[Phase-6] P6-GE14: silver_visions - port PathGeneratorEffect from VJlive-2/silver_visions.py`
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note
- [ ] Easter Egg submitted

---

## Legacy Code References

### GLSL fragment from VJlive-2
```glsl
uniform float uMode;           // 0: scanning, 1: boustrophedon, 2: spiral, 3: random
uniform float uSpeed;          // Speed control
uniform float uResolution;     // Resolution (side length)
uniform bool uXYPolarity;      // Bipolar or unipolar position
uniform float uTime;           // Time for animation
uniform vec2 resolution;       // Screen resolution
uniform float u_mix;
uniform sampler2D tex0;

float rand(float n) { return fract(sin(n)*43758.5453); }

void main() {
    float x_position=0.0, y_position=0.0;
    float mode=uMode, speed=uSpeed, res=uResolution;
    if (mode==0.0) {
        x_position = mod(uTime*speed, res);
        y_position = floor((uTime*speed)/res) * speed;
    } else if (mode==1.0) {
        float scan_line = floor((uTime*speed)/res);
        if (mod(scan_line,2.0)==0.0) {
            x_position = mod(uTime*speed, res);
        } else {
            x_position = res - mod(uTime*speed, res);
        }
        y_position = scan_line * speed;
    } else if (mode==2.0) {
        x_position = res*0.5 + sin(uTime*speed)*res*0.4;
        y_position = res*0.5 + cos(uTime*speed)*res*0.4;
    } else if (mode==3.0) {
        if (fract(uTime*speed) < 0.01) {
            x_position = rand(uTime) * res;
            y_position = rand(uTime+1.0) * res;
        }
    }
    float x_volt = 10.0*x_position/res;
    float y_volt = 10.0*y_position/res;
    if (!uXYPolarity) { x_volt -= 5.0; y_volt -= 5.0; }
    vec4 path_color = vec4(x_volt/10.0+0.5, y_volt/10.0+0.5, 0.0, 1.0);
    vec4 original = texture(tex0, uv);
    FragColor = mix(original, path_color, u_mix);
}
```

### Python portion
```python
class PathGeneratorEffect(Effect):
    def __init__(self):
        super().__init__("PathGenerator", FRAGMENT_SHADER)
        self.parameters = {
             "uMode": 0.0,          # 0: scanning, 1: boustrophedon, 2: spiral, 3: random
             "uSpeed": 1.0,
             "uResolution": 150.0,
             "uXYPolarity": 0.0,
        }
    def set_parameter(self, name, value):
        if name=="uMode":
            self.parameters["uMode"] = float(int(max(0.0,min(3.0,value))))
        elif name=="uResolution":
            self.parameters["uResolution"] = max(1.0, value*100.0)
        else:
            super().set_parameter(name,value)
    def apply_uniforms(self, time_val,resolution,*,...):
        super().apply_uniforms(time_val,resolution,...)
        self.shader.set_uniform("uTime", time_val)
        self.shader.set_uniform("uMode", self.parameters["uMode"])
        self.shader.set_uniform("uSpeed", self.parameters["uSpeed"])
        self.shader.set_uniform("uResolution", self.parameters["uResolution"])
        self.shader.set_uniform("uXYPolarity", int(self.parameters["uXYPolarity"]>0.5))
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

