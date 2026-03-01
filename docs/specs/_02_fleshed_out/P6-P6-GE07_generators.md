# Spec: P6-GE07 — Oscillator

**File naming:** `docs/specs/P6-P6-GE07_generators.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-GE07 — generators

**What This Module Does**  
The `Oscillator` module generates synchronized waveform patterns for visual synthesis, creating complex oscillating visuals through mathematical wave manipulation. It produces synchronized visual patterns by manipulating frequency, phase, waveform shape, and color properties across video frames. The module supports multiple waveform types (sine, triangle, sawtooth, square) with smooth morphing between them, phase offsets, and frequency modulation.

**What This Module Does NOT Do**  
- Handle file I/O or persistent storage operations  
- Process audio streams or provide direct sound input  
- Implement 3D geometry transformations or volumetric effects  
- Provide direct MIDI or OSC control interfaces  
- Support arbitrary text rendering outside of video frame context  

**Detailed Behavior**  
The module processes video frames through several mathematical stages:
1. **Waveform Generation**: Creates base waveforms using frequency, phase, and waveform shape parameters
2. **Phase Synchronization**: Applies time-based phase offsets with synchronization multipliers
3. **Waveform Morphing**: Smoothly interpolates between waveform types using waveform parameter
4. **Color Processing**: Applies hue rotation and saturation adjustments based on input parameters
5. **Output Mixing**: Blends generated patterns with input frames using mix ratio

Key mathematical characteristics:
- Frequency maps 0-10 range to 0-200 Hz (f = frequency/10 * 200)
- Phase offset maps 0-10 range to 0-2π (φ = offset/10 * 2π)
- Waveform morphing uses parameter w ∈ [0,10] mapped to interpolation weights
- Color rotation uses hue offset in 0-360° range
- Mix ratio uses linear interpolation between generated and input colors

**Integration Notes**  
The module integrates with the VJLive3 node graph through:
- Input: Video frames via standard VJLive3 frame ingestion pipeline
- Output: Processed frames with oscillating visual patterns that maintain original dimensions
- Parameter Control: All parameters can be dynamically updated via set_parameter() method
- Dependency Relationships: Connects to shader_base for fundamental rendering operations

**Performance Characteristics**  
- Processing load scales with frame resolution and waveform complexity
- GPU acceleration available through optional pyopencl integration
- CPU fallback implementation maintains real-time performance at 60fps for 1080p input
- Memory usage optimized through parameter caching and shader reuse
- Latency kept under 16ms for 60fps target

---

## Public Interface

```python
# Paste planned class/function signatures here before coding

class OscEffect:
    def __init__(self, frame_width: int, frame_height: int) -> None: ...
    def process_frame(self, input_frame: np.ndarray) -> np.ndarray: ...
    def set_parameter(self, param_name: str, value: float) -> None: ...
    def get_parameter(self, param_name: str) -> float: ...
    def reset(self) -> None: ...
    def stop(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame_width` | `int` | Input frame width in pixels | 64-4096 |
| `frame_height` | `int` | Input frame height in pixels | 64-4096 |
| `input_frame` | `np.ndarray` | RGB frame data (HxWx3) | uint8, 0-255 |
| `frequency` | `float` | Base frequency multiplier | 0.0-10.0 |
| `sync` | `float` | Synchronization speed multiplier | 0.0-10.0 |
| `offset` | `float` | Phase offset | 0.0-10.0 |
| `waveform` | `float` | Waveform type (0-3) | 0=sine, 1=triangle, 2=sawtooth, 3=square |
| `thickness` | `float` | Pattern thickness factor | 0.0-10.0 |
| `color_shift` | `float` | Hue rotation amount | 0.0-10.0 |
| `saturation` | `float` | Color saturation multiplier | 0.0-10.0 |
| `mix` | `float` | Output mix ratio | 0.0-1.0 |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → (NullDevice pattern / graceful fallback)
- What happens on bad input? → (raise ValueError with message)
- What is the cleanup path? → (close(), __exit__, resource release)

---

## Dependencies

- **External Libraries**: 
  - `numpy` for array operations and pixel processing
  - `pyopencl` for GPU acceleration (optional)
- **Internal Dependencies**:
  - `vjlive3.core.effects.shader_base` for fundamental shader operations
  - `vjlive3.plugins.vcore.oscillator.py` for legacy implementation reference

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing if hardware (GPU) is absent or unavailable |
| `test_basic_operation` | Core rendering function produces valid output when given a clean input frame |
| `test_parameter_range_validation` | All parameter inputs are clamped to 0.0–10.0 range and rejected outside bounds |
| `test_waveform_morphing` | Waveform parameter correctly interpolates between sine, triangle, sawtooth, and square |
| `test_sync_behavior` | Sync parameter correctly modulates frequency based on time |
| `test_phase_offset` | Offset parameter correctly applies phase shift |
| `test_color_rotation` | Color_shift parameter correctly rotates hue without breaking saturation |
| `test_saturation_scaling` | Saturation parameter correctly scales color intensity |
| `test_mix_ratio` | Mix parameter correctly blends generated pattern with input |
| `test_invalid_frame_size` | Invalid frame sizes (e.g., <64x64) raise appropriate exceptions without crashing |
| `test_legacy_compatibility` | Output matches expected visual characteristics of legacy implementations |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-GE07: generators - port from vjlive/plugins/vcore/generators.py` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES  
Use these to fill in the spec. These are the REAL implementations:

### vjlive/plugins/vcore/generators.py (L1-20)  
```python
"""
Generator effects — create patterns from scratch.
Professional-grade GLSL generators for live VJ performance.

All parameters use 0.0-10.0 range from UI sliders.
Shaders remap internally to the values the math needs.
"""
```

### vjlive/plugins/vcore/generators.py (L17-36)  
```python
out vec4 fragColor;
uniform sampler2D tex0;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

uniform float frequency;   // 0-10 → 0-200 Hz
uniform float sync;        // 0-10 → 0-4 speed multiplier
uniform float offset;      // 0-10 → 0-TWO_PI phase offset
uniform float waveform;    // 0-10 → 0=sine, 3=tri, 6=saw, 9=square
uniform float thickness;   // 0-10 → line thickness / fill blend
uniform float color_shift; // 0-10 → hue rotation 0-360°
uniform float saturation;  // 0-10 → 0-2 sat multiplier
```

### vjlive/plugins/vcore/generators.py (L33-52)  
```python
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
```

### vjlive/plugins/vcore/generators.py (L49-68)  
```
float wave(float x, float wf) {
    float w = wf / 10.0 * 3.0;  // 0-3
    // Morph between sine(0), triangle(1), sawtooth(2), square(3)
    float s = sin(x) * 0.5 + 0.5;
    float t = abs(fract(x / 6.28318) * 2.0 - 1.0);
    float saw = fract(x / 6.28318);
    float sq = step(0.5, fract(x / 6.28318));

    if (w < 1.0) return mix(s, t, w);
    else if (w < 2.0) return mix(t, saw, w - 1.0);
    else return mix(saw, sq, w - 2.0);
}
```

### vjlive/plugins/vcore/generators.py (L65-84)  
```
void main() {
    vec4 input_color = texture(tex0, uv);
    float freq = frequency / 10.0 * 200.0;
    float sy = sync / 10.0 * 4.0;
    float off = offset / 10.0 * 6.28318;
    float hue_rot = color_shift / 10.0;
    float sat = saturation / 10.0 * 2.0;
    float thick = thickness / 10.0;

    float r = wave((uv.x - off / freq + time * sy) * freq, waveform);
    float g = wave((uv.x + time * sy) * freq, waveform);
    float b = wave((uv.x + off / freq + time * sy) * freq, waveform);

    // Apply hue rotation
    vec3 base = vec3(r, g, b);
    float luma = dot(base, vec3(0.299, 0.587, 0.114));
    vec3 shifted = hsv2rgb(vec3(fract(hue_rot + luma * 0.5), sat, length(base)));

    // Mix between fill and line modes
    vec3 fill = base;
    float line_val = smoothstep(thick, thick + 0.02, abs(uv.y - r));
    vec3 line = vec3(1.0 - line_val) * shifted;
    vec3 osc_color = mix(shifted, line, thick);

    fragColor = mix(input_color, vec4(osc_color, 1.0), u_mix);
}
```

### vjlive/plugins/vcore/generators.py (L81-100)  
```python
class OscEffect(Effect):
    """Oscillator — waveform-morphing pattern generator with sync and color control."""

    def __init__(self):
        super().__init__("osc", OSC_FRAGMENT)
        self.parameters = {
            "frequency": 3.0,
            "sync": 0.5,
            "offset": 0.0,
            "waveform": 0.0,
            "thickness": 0.0,
            "color_shift": 0.0,
            "saturation": 5.0,
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

