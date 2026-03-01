# Spec: P6-GE08 — Noise Generator

**File naming:** `docs/specs/P6-P6-GE08_generators.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-GE08 — generators

**What This Module Does**  
The `NoiseEffect` module generates procedurally-synthesized texture and terrain patterns using layered noise functions, creating flowing organic landscapes with infinite variation. It produces continuously-animating noise fields by combining multiple octaves of Perlin/Simplex noise with adjustable scale, octave count, and temporal modulation. The output is a stylized procedural environment that renders live video input through a noise-based distortion, layering, or generative overlay mechanism with full color control and animation.

**What This Module Does NOT Do**  
- Handle file I/O or persistent storage operations  
- Process audio streams or provide direct sound input  
- Implement 3D geometry transformation or volumetric effects  
- Provide direct MIDI or OSC control interfaces  
- Support arbitrary texture loading outside of procedural generation  

**Detailed Behavior**  
The module processes video frames through several mathematical stages:
1. **Noise Field Generation**: Creates multi-octave Perlin/Simplex noise using OpenGL sampler functions or procedural GLSL implementations
2. **Octave Layering**: Combines noise at multiple scales using fractional Brownian motion (fBm) with persistent energy across octaves
3. **Temporal Animation**: Applies time-based offset to noise coordinates, creating smooth flowing effects with adjustable speed
4. **Distortion Mapping**: Uses noise values to displace UV coordinates or modulate color channels
5. **Output Compositing**: Blends generated noise patterns with input frame through mix ratio control

Key mathematical characteristics:
- Noise scale maps 0-10 range to 0.1-10.0 scale factor (s = 0.1 + scale/10 * 9.9)
- Octave count maps 0-10 range to 1-8 octaves (o = ceil(octaves/10 * 7 + 1))
- Octave persistence (lacunarity) maps 0-10 range to 1.5-4.0 (l = 1.5 + persistence/10 * 2.5)
- Frequency multiplier per octave: f_i = 2^i for standard fBm
- Amplitude multiplier per octave: a_i = persistence^i (gain factor)
- Temporal animation: time_offset = time * speed / 10 * π
- Color distortion: hue_shift_amount = distortion / 10 * 360°
- Displacement magnitude: displacement = magnitude / 10 * resolution_factor (typically 0.0-0.2 of frame size)

**Integration Notes**  
The module integrates with the VJLive3 node graph through:
- Input: Video frames via standard VJLive3 frame ingestion pipeline
- Output: Processed frames with noise-based patterns that maintain original dimensions
- Parameter Control: All parameters can be dynamically updated via set_parameter() method
- Dependency Relationships: Connects to shader_base for fundamental rendering operations

**Performance Characteristics**  
- Processing load scales with octave count and displacement magnitude
- GPU acceleration available through GLSL sampler noise functions
- CPU fallback using Python noise libraries (e.g., opensimplex, noise)
- Real-time performance at 60fps for 1080p input achievable with 4-6 octaves
- Memory usage optimized through single-pass noise computation with minimal frame buffering
- Latency kept under 16ms for 60fps target

---

## Public Interface

```python
# Paste planned class/function signatures here before coding

class NoiseEffect:
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
| `noise_scale` | `float` | Base frequency/scale of noise pattern | 0.0-10.0 |
| `octaves` | `float` | Number of noise octaves to layer | 0.0-10.0 (maps to 1-8) |
| `persistence` | `float` | Amplitude falloff per octave (lacunarity control) | 0.0-10.0 |
| `animation_speed` | `float` | Temporal velocity of noise flow | 0.0-10.0 |
| `displacement` | `float` | UV coordinate distortion magnitude | 0.0-10.0 |
| `color_shift` | `float` | Hue rotation of noise pattern | 0.0-10.0 |
| `saturation` | `float` | Color saturation multiplier | 0.0-10.0 |
| `mix` | `float` | Output mix ratio (noise vs input) | 0.0-1.0 |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → (NullDevice pattern / graceful fallback to CPU noise)
- What happens on bad input? → (raise ValueError with message for out-of-range parameters)
- What is the cleanup path? → (close(), __exit__, GPU resource release)

---

## Dependencies

- **External Libraries**: 
  - `numpy` for array operations and pixel processing
  - `opensimplex` or `noise` for CPU-based Simplex noise (fallback)
  - `pyopencl` for GPU acceleration (optional)
- **Internal Dependencies**:
  - `vjlive3.core.effects.shader_base` for fundamental shader operations
  - `vjlive3.plugins.vcore.generators.py` for legacy implementation reference

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing if GPU is absent or unavailable |
| `test_basic_operation` | Core noise generation produces valid output when given a clean input frame |
| `test_parameter_range_validation` | All parameter inputs are clamped to 0.0–10.0 range and rejected outside bounds |
| `test_noise_scale_effect` | Increasing noise_scale produces appropriately finer/coarser patterns |
| `test_octave_count_effect` | Octave parameter correctly increases pattern complexity and detail |
| `test_persistence_lacunarity` | Persistence parameter correctly controls amplitude falloff across octaves |
| `test_animation_continuity` | animation_speed parameter produces smooth temporal variation without discontinuities |
| `test_displacement_magnitude` | displacement parameter correctly distorts UV coordinates proportionally |
| `test_color_shift_hue` | color_shift parameter correctly rotates hue without breaking saturation |
| `test_saturation_scaling` | saturation parameter correctly scales color intensity |
| `test_mix_ratio` | mix parameter correctly blends noise pattern with input frame |
| `test_invalid_frame_size` | Invalid frame sizes (e.g., <64x64) raise appropriate exceptions without crashing |
| `test_fbm_energy_conservation` | fBm combination maintains expected energy decay per octave |
| `test_temporal_smoothness` | Successive frames show smooth transitions without popping or jitter |
| `test_legacy_compatibility` | Output matches expected visual characteristics of legacy noise implementations |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-GE08: generators - port from vjlive/plugins/vcore/generators.py` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 6, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES  
Use these to fill in the spec. These are the REAL implementations:

### vjlive/plugins/vcore/generators.py (L1-20)  
```python
"""
Generator effects — create patterns from scratch.
Professional-grade GLSL noise generators for live VJ performance.

All parameters use 0.0-10.0 range from UI sliders.
Shaders remap internally to the values the math needs.
Includes Perlin, Simplex, Worley noise with octave layering.
"""
```

### vjlive/plugins/vcore/generators.py (L100-130)  
```glsl
// Simplex noise hash function
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float smoothstep_cubic(float t) {
    return t * t * (3.0 - 2.0 * t);
}

// Perlin noise implementation (2D)
float perlin_noise(vec2 uv) {
    vec2 i = floor(uv);
    vec2 f = fract(uv);
    f = f * f * (3.0 - 2.0 * f); // Smoothstep
    
    float n00 = hash(i + vec2(0.0, 0.0));
    float n10 = hash(i + vec2(1.0, 0.0));
    float n01 = hash(i + vec2(0.0, 1.0));
    float n11 = hash(i + vec2(1.0, 1.0));
    
    float nx0 = mix(n00, n10, f.x);
    float nx1 = mix(n01, n11, f.x);
    return mix(nx0, nx1, f.y);
}

// fBm (Fractional Brownian Motion) layering
float fbm(vec2 uv, int octaves, float persistence) {
    float value = 0.0;
    float amplitude = 1.0;
    float frequency = 1.0;
    float max_value = 0.0;
    
    for (int i = 0; i < MAX_OCTAVES; i++) {
        if (i >= octaves) break;
        value += amplitude * perlin_noise(uv * frequency);
        max_value += amplitude;
        amplitude *= persistence;
        frequency *= 2.0;
    }
    return value / max_value;
}
```

### vjlive/plugins/vcore/generators.py (L131-160)  
```glsl
void main() {
    vec4 input_color = texture(tex0, uv);
    
    // Remap parameters from 0-10 to appropriate ranges
    float scale = noise_scale / 10.0 * 9.9 + 0.1;
    int octave_count = int(ceil(octaves / 10.0 * 7.0 + 1.0));
    float persist = persistence / 10.0 * 2.5 + 1.5;
    float speed = animation_speed / 10.0 * 5.0;
    float disp = displacement / 10.0 * 0.2;
    
    // Time-based animation
    vec2 anim_uv = uv + vec2(time * speed);
    
    // Generate base noise field
    float base_noise = fbm(anim_uv * scale, octave_count, persist);
    
    // Optional: apply displacement
    vec2 displaced_uv = uv + vec2(cos(base_noise * 6.28318), sin(base_noise * 6.28318)) * disp;
    vec4 displaced_sample = texture(tex0, displaced_uv);
    
    // Apply color transformation
    vec3 noise_color = mix(vec3(base_noise), vec3(1.0) - vec3(base_noise), color_shift / 10.0);
    float sat = saturation / 10.0 * 2.0;
    
    // HSV saturation boost
    vec3 hsv = rgb2hsv(noise_color);
    hsv.y *= sat;
    noise_color = hsv2rgb(hsv);
    
    // Final compositing
    fragColor = mix(input_color, vec4(noise_color, 1.0), u_mix);
}
```

### vjlive/plugins/vcore/generators.py (L161-180)  
```python
class NoiseEffect(Effect):
    """Procedural noise generator — Perlin/Simplex fBm with temporal animation."""

    def __init__(self):
        super().__init__("noise", NOISE_FRAGMENT)
        self.parameters = {
            "noise_scale": 3.0,
            "octaves": 5.0,
            "persistence": 5.0,
            "animation_speed": 2.0,
            "displacement": 0.0,
            "color_shift": 0.0,
            "saturation": 5.0,
        }
        self.time_accumulator = 0.0
```

---

## Verification Checkpoints

- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum
- [ ] Test coverage ≥80%
- [ ] No safety rail violations
- [ ] Original functionality verified (side-by-side comparison)
- [ ] fBm energy conservation verified mathematically

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

---

