# Spec: P5-DM13 — MeltEffect

**File naming:** `docs/specs/P5-P5-DM13_datamosh.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P5-DM13 — MeltEffect

**What This Module Does**  
The `MeltEffect` module simulates video compression artifacts and temporal distortion through mathematical manipulation of pixel data. It creates visual glitches by selectively freezing frames, introducing motion vectors, and applying chaos-based randomization to create organic-looking datamoshing effects. The module processes video frames in real-time, producing artifacts that mimic corrupted video streams while maintaining smooth performance at 60 FPS.

**What This Module Does NOT Do**  
- Handle file I/O or persistent storage operations
- Process audio streams or provide sound-reactive capabilities
- Implement real-time 3D transformations or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context

**Detailed Behavior**  
The module processes video frames through several stages:
1. **Frame Analysis**: Analyzes current frame against previous frame to detect motion vectors
2. **Temporal Manipulation**: Applies selective frame freezing based on motion thresholds
3. **Chaos Injection**: Introduces controlled randomness to motion vectors and pixel positions
4. **Compression Simulation**: Applies block-based artifact generation to simulate compression errors
5. **Motion Vector Processing**: Calculates and applies directional distortion based on detected motion

Key behavioral characteristics:
- Frame freezing occurs when motion falls below threshold (0.0-1.0 range)
- Chaos mode introduces random vector offsets proportional to chaos parameter
- Block artifacts are generated using 8x8 pixel grid patterns
- Motion vectors are calculated using optical flow approximation
- Temporal coherence is maintained through frame history buffer

**Integration Notes**  
The module integrates with the VJLive3 node graph through:
- Input: Video frames via standard VJLive3 frame ingestion pipeline
- Output: Processed frames with datamosh artifacts that maintain original dimensions
- Parameter Control: All parameters can be dynamically updated via set_parameter() method
- Dependency Relationships: Connects to shader_base for fundamental rendering operations

**Performance Characteristics**  
- Processing load scales linearly with frame resolution and block density
- GPU acceleration available through optional pyopencl integration
- CPU fallback implementation maintains real-time performance at 60fps for 1080p input
- Memory usage optimized through frame history reuse and block caching
- Latency kept under 16ms for 60fps target

---

## Public Interface

```python
# Paste planned class/function signatures here before coding

class MeltEffect:
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
| `intensity` | `float` | Overall effect strength | 0.0-1.0 |
| `freeze_threshold` | `float` | Motion threshold for frame freezing | 0.0-1.0 |
| `chaos` | `float` | Randomness intensity | 0.0-1.0 |
| `block_size` | `float` | Compression block size | 1.0-64.0 |
| `motion_sensitivity` | `float` | Motion detection sensitivity | 0.0-1.0 |

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
  - `vjlive3.plugins.vcore.melt_effect.py` for legacy implementation reference

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing if hardware (GPU) is absent or unavailable |
| `test_basic_operation` | Core rendering function produces valid output when given a clean input frame |
| `test_parameter_range_validation` | All parameter inputs are clamped to 0.0–1.0 range and rejected outside bounds |
| `test_frame_freezing` | Frame freezing activates correctly when motion falls below threshold |
| `test_chaos_mode` | Chaos parameter introduces appropriate randomness without breaking frame coherence |
| `test_block_artifacts` | Compression artifacts are generated with correct block sizes and patterns |
| `test_motion_vectors` | Motion vector calculation produces reasonable directional distortion |
| `test_parameter_set_get_cycle` | Dynamic parameter updates via set/get methods reflect real-time changes in output |
| `test_grayscale_input_handling` | Input in grayscale is correctly interpreted for motion analysis |
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
- [ ] Git commit with `[Phase-5] P5-DM13: melt_effect - port from vjlive/plugins/vcore/datamosh.py` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  
Use these to fill in the spec. These are the REAL implementations:

### vjlive/plugins/vcore/datamosh.py (L1-20)  
```python
"""
Datamosh Effect — Simulate video compression artifacts and temporal distortion.

This effect creates visual glitches by selectively freezing frames, introducing motion vectors, and applying chaos-based randomization to create organic-looking datamoshing effects.

Parameters use 0.0-1.0 range.
"""
```

### vjlive/plugins/vcore/datamosh.py (L17-36)  
```python
in vec2 uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform float time;
uniform vec2 resolution;
uniform float u_intensity;

// --- Temporal Controls ---
uniform float u_freeze_threshold;    // 0-1 → 0 to 0.5 (motion threshold for frame freezing)
uniform float u_chaos;               // 0-1 → 0 to 0.3 (randomness intensity)
uniform float u_block_size;          // 0-1 → 1 to 64 (compression block size)
uniform float u_motion_sensitivity;  // 0-1 → 0 to 1 (motion detection sensitivity)

// --- Motion Vector Processing ---
uniform float u_vector_strength;     // 0-1 → 0 to 0.5 (motion vector strength)
uniform float u_vector_jitter;       // 0-1 → 0 to 0.2 (random vector jitter)
uniform float u_vector_smooth;       // 0-1 → 0 to 0.8 (vector smoothing)
```

### vjlive/plugins/vcore/datamosh.py (L33-52)  
```

// --- Chaos Injection ---
uniform float u_chaos_seed;          // 0-1 → 0 to 1000 (random seed for chaos)
uniform float u_chaos_frequency;     // 0-1 → 0.1 to 10 (chaos update frequency)
uniform float u_chaos_amplitude;     // 0-1 → 0 to 0.5 (chaos displacement amplitude)

// --- Compression Simulation ---
uniform float u_compression_error;   // 0-1 → 0 to 0.3 (compression error rate)
uniform float u_block_artifacts;     // 0-1 → 0 to 1 (block artifact intensity)
uniform float u_color_shift;         // 0-1 → 0 to 0.2 (color channel shifting)

// --- Frame History ---
uniform float u_history_blend;       // 0-1 → 0 to 1 (frame history blending)
uniform float u_history_fade;        // 0-1 → 0 to 0.5 (history fade rate)
```

### vjlive/plugins/vcore/datamosh.py (L49-68)  
```

// --- Frame Analysis ---
float calculate_motion(vec2 uv, sampler2D current, sampler2D previous) {
    vec3 current_color = texture(current, uv).rgb;
    vec3 previous_color = texture(previous, uv).rgb;
    float motion = distance(current_color, previous_color);
    return motion;
}

// --- Chaos Function ---
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

// --- Motion Vector Calculation ---
vec2 calculate_vector(vec2 uv, float time) {
    vec2 motion_vector = vec2(0.0);
    // Optical flow approximation
    vec2 offset = vec2(hash(uv + time * 0.1) - 0.5, hash(uv + time * 0.2) - 0.5);
    motion_vector += offset * u_vector_strength;
    return motion_vector;
}

// --- Block Artifact Generation ---
vec3 apply_block_artifacts(vec3 color, vec2 uv, float block_size) {
    vec2 block_coord = floor(uv * resolution / block_size) * block_size / resolution;
    vec3 block_color = texture(tex0, block_coord).rgb;
    return mix(color, block_color, u_block_artifacts);
}
```

### vjlive/plugins/vcore/datamosh.py (L65-84)  
```

void main() {
    // Calculate motion
    float motion = calculate_motion(uv, tex0, texPrev);
    
    // Apply frame freezing
    float freeze = step(u_freeze_threshold, motion);
    vec3 current_color = texture(tex0, uv).rgb;
    vec3 previous_color = texture(texPrev, uv).rgb;
    vec3 final_color = mix(previous_color, current_color, freeze);
    
    // Apply chaos injection
    float chaos_offset = hash(uv + u_chaos_seed) * u_chaos_amplitude;
    vec2 chaos_uv = uv + vec2(chaos_offset, chaos_offset * 0.5);
    final_color = texture(tex0, chaos_uv).rgb;
    
    // Apply motion vectors
    vec2 motion_vector = calculate_vector(uv, time);
    vec2 distorted_uv = uv + motion_vector;
    final_color = texture(tex0, distorted_uv).rgb;
    
    // Apply block artifacts
    final_color = apply_block_artifacts(final_color, uv, u_block_size * 8.0);
    
    fragColor = vec4(final_color, 1.0);
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

