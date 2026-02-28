# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD68_Depth_Temporal_Strat.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD68 — DepthTemporalStratEffect

## Description

The DepthTemporalStratEffect slices the video into discrete depth strata (layers), where each stratum runs at a different time offset. Near strata show the present, far strata show the past. The stratum boundaries produce natural datamosh artifacts from temporal discontinuities. The effect features per-layer hue rotation, temporal freezing, strobe flicker, and motion-vector block displacement at seams.

This effect creates a layered temporal distortion where depth defines separate time streams. It's ideal for creating psychedelic, glitchy visuals where different depth planes appear to be moving through time at different rates. The datamosh artifacts at depth boundaries add a raw, corrupted aesthetic.

## What This Module Does

- Divides depth range into discrete strata (layers)
- Each stratum has its own time offset (temporal layer)
- Near strata = present, far strata = past
- Datamosh artifacts at stratum boundaries
- Per-stratum hue rotation
- Temporal freezing and strobe flicker
- Motion-vector block displacement at seams
- GPU-accelerated with multiple history buffers

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT include audio reactivity (may be added later)
- Does NOT support arbitrary number of strata (limited by texture units)
- Does NOT implement motion estimation (uses simple block displacement)
- Does NOT include smooth interpolation between strata (hard boundaries)

---

## Detailed Behavior

### Temporal Stratification Pipeline

1. **Capture depth frame**: `depth_frame` (HxW, normalized 0-1)
2. **Define strata**: Divide depth range [0,1] into N discrete intervals
   - Strata boundaries: `b0=0, b1, b2, ..., bN=1`
   - Each pixel belongs to exactly one stratum based on depth
3. **Assign time offset per stratum**:
   - Strata 0 (nearest): offset = 0 (present)
   - Strata 1: offset = delay1
   - Strata 2: offset = delay2
   - ...
   - Strata N-1 (farthest): offset = delayN-1
4. **Sample historical frame** for each pixel based on its stratum's offset
5. **Apply per-stratum effects**:
   - Hue rotation
   - Temporal freezing (freeze some frames)
   - Strobe flicker
6. **Detect stratum boundaries** (where depth crosses from one stratum to another)
7. **Apply datamosh at boundaries**:
   - Block displacement using motion vectors
   - Brightness boost for seam visibility
8. **Composite** with original via `u_mix`

### Strata Definition

The depth range is divided into equal or custom intervals:

```glsl
int stratum = int(depth * float(num_strata));
stratum = clamp(stratum, 0, num_strata - 1);
```

Or with custom boundaries:
```glsl
float stratum = 0.0;
if (depth < b1) stratum = 0.0;
else if (depth < b2) stratum = 1.0;
...
```

### Time Offsets per Stratum

Each stratum has a delay (in frames):

```glsl
float delays[num_strata] = {0.0, 2.0, 4.0, 6.0, 8.0};  // Example
float delay = delays[stratum];
int history_index = (current_frame_index - round(delay)) % history_size;
vec4 color = texture(history_tex[history_index], uv);
```

### Datamosh at Boundaries

At stratum boundaries (where depth changes rapidly), introduce block corruption:

```glsl
float depth_grad = length(vec2(dFdx(depth), dFdy(depth)));
float seam_factor = smoothstep(threshold, threshold + 0.02, depth_grad);

if (seam_factor > 0.0) {
    // Motion vector block displacement
    vec2 motion = compute_motion_vector(uv, delay);  // From optical flow or simple difference
    vec2 block_offset = floor(motion * block_size) / block_size;
    color = texture(history_tex[history_index], uv + block_offset * seam_datamosh);
    
    // Brightness boost
    color.rgb += seam_factor * 0.08 * seam_datamosh;
}
```

### Per-Stratum Effects

- **Hue rotation**: Rotate colors by stratum-specific angle
  ```glsl
  float hue_angle = hueRotate * stratum;  // Or per-stratum param
  color.rgb = rotate_hue(color.rgb, hue_angle);
  ```
- **Temporal freezing**: Some frames are frozen (no update)
  ```glsl
  if (freeze_pattern[stratum] > 0.0 && frame_is_frozen) {
      color = previous_color;  // Hold
  }
  ```
- **Strobe flicker**: Rapid on/off for stratum
  ```glsl
  if (strobe_pattern[stratum] > 0.0 && sin(time * freq) < 0.0) {
      color = vec3(0.0);  // Black out
  }
  ```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `strata` | float | 5.0 | 1.0-10.0 | Number of depth strata (layers) |
| `stratumDelays` | float[10] | [0,2,4,6,8,...] | 0.0-10.0 | Delay per stratum (frames) |
| `hueRotate` | float | 0.0 | 0.0-10.0 | Hue rotation per stratum (degrees×10) |
| `freeze` | float | 0.0 | 0.0-10.0 | Temporal freezing probability per stratum |
| `strobe` | float | 0.0 | 0.0-10.0 | Strobe flicker intensity per stratum |
| `seamDatamosh` | float | 5.0 | 0.0-10.0 | Datamosh intensity at stratum boundaries |
| `blockSize` | float | 8.0 | 1.0-20.0 | Block size for motion displacement |
| `seamThreshold` | float | 0.01 | 0.0-0.1 | Depth gradient threshold for seam detection |
| `moshDecay` | float | 3.0 | 0.0-10.0 | How much datamosh decays with stratum depth |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class DepthTemporalStratEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def set_stratum_delay(self, stratum: int, delay: float) -> None: ...
    def get_stratum_delay(self, stratum: int) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def clear_history(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Temporal stratified output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_history_textures: List[int]` — Circular buffer of historical frames (N textures)
- `_history_fbos: List[int]` — Framebuffers for history textures
- `_history_size: int` — Number of frames in history (e.g., 60-120)
- `_current_index: int` — Current write index in circular buffer
- `_parameters: dict` — Strat parameters
- `_shader: ShaderProgram` — Compiled shader
- `_stratum_delays: List[float]` — Per-stratum delay values
- `_num_strata: int` — Number of strata (from `strata` param)

**Per-Frame:**
- Update depth data from source
- Upload current frame to history texture at `_current_index`
- Render effect: for each pixel, determine stratum, sample appropriate history frame, apply effects, handle seams
- Increment `_current_index` (modulo `_history_size`)
- Return result

**Initialization:**
- Create history textures (N, where N = max delay + 1, or configurable)
- Create history FBOs (N)
- Compile shader
- Default parameters: strata=5, stratumDelays=[0,2,4,6,8], hueRotate=0, freeze=0, strobe=0, seamDatamosh=5, blockSize=8, seamThreshold=0.01, moshDecay=3
- Initialize `_stratum_delays` based on `stratumDelays` or auto-distribute
- Initialize `_current_index = 0`

**Cleanup:**
- Delete all history textures and FBOs
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| History textures (N) | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame (circular) |
| History FBOs (N) | GL_FRAMEBUFFER | N/A | frame size | Persistent |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480, N=60):**
- History textures: 60 × 921,600 bytes = 55,296,000 bytes (~52.7 MB)
- Shader: ~30-50 KB
- Total: ~53 MB

**Note**: The number of history textures needed depends on maximum delay. If max delay = 10 frames, need at least 11 textures. The legacy may use a smaller ring buffer with time-based sampling or a single texture with mipmaps.

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use uniform depth (0.5) | Normal operation |
| FBO incomplete | `RuntimeError("FBO error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| History buffer too small | Increase buffer or clamp delays | Normal operation |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and FBO operations must occur on the thread with the OpenGL context. The effect updates the history buffer each frame; concurrent `process_frame()` calls will cause race conditions and corrupted history. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480, 5 strata, 60 history textures):**
- Texture upload: ~0.5-1 ms
- Shader execution (multiple texture fetches, seam detection, datamosh): ~8-15 ms
- Total: ~8.5-16 ms on GPU (heavy)

**Optimization Strategies:**
- Reduce number of strata
- Reduce history buffer size (use fewer textures with larger delays)
- Simplify datamosh (no motion vectors, just color shift)
- Use lower resolution for history textures
- Early depth test to skip some strata processing
- Use texture arrays for better cache locality

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Strata count and delays configured
- [ ] Per-stratum effects configured (hue, freeze, strobe)
- [ ] Seam datamosh parameters configured
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_strata_count` | Depth divided into correct number of strata |
| `test_stratum_assignment` | Pixels assigned correct stratum based on depth |
| `test_delay_mapping` | Each stratum uses correct time offset |
| `test_hue_rotation` | Per-stratum hue rotation applied |
| `test_freeze` | Temporal freezing works per stratum |
| `test_strobe` | Strobe flicker works per stratum |
| `test_seam_detection` | Stratum boundaries detected correctly |
| `test_datamosh_at_seams` | Datamosh artifacts appear at boundaries |
| `test_motion_displacement` | Block displacement along motion vectors |
| `test_seam_brightness` | Seam brightness boost applied |
| `test_history_buffer` | History buffer stores and retrieves frames correctly |
| `test_clear_history` | History buffer can be reset |
| `test_cleanup` | All GPU resources released |
| `test_no_memory_leak` | Repeated init/cleanup cycles don't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD68: depth_temporal_strat_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_temporal_strat.py` — VJLive Original implementation
- `plugins/core/depth_temporal_strat/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_temporal_strat/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthTemporalStratEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_temporal_strat`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for stratum assignment
- Parameters: `strata`, `stratumDelays`, `hueRotate`, `freeze`, `strobe`, `seamDatamosh`, `blockSize`, `seamThreshold`, `moshDecay`
- Allocates GL resources: history textures (N), history FBOs (N)
- Shader implements temporal stratification, per-stratum effects, seam detection, and datamosh
- Method `_ensure_history_buffers()` creates GPU resources

---

## Notes for Implementers

1. **Core Concept**: This effect divides depth into discrete strata, each with its own time offset. Near strata show the present, far strata show the past. At stratum boundaries, datamosh artifacts appear, creating a glitchy, stratified temporal effect.

2. **Strata vs Layers**: Unlike `DepthTemporalEcho` which blends multiple ghost layers, `DepthTemporalStrat` assigns each pixel to exactly one stratum, creating hard depth boundaries. Each stratum is a distinct temporal layer.

3. **History Buffer**: Need to store enough historical frames to cover the maximum delay. If max delay = 10 frames, need at least 11 textures (or a ring buffer of 11). The legacy may use a fixed-size ring (e.g., 60 frames) and sample from it based on delay.

4. **Stratum Assignment**:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   int stratum = int(depth * float(num_strata));
   stratum = clamp(stratum, 0, num_strata - 1);
   ```

5. **Delay Lookup**:
   ```glsl
   float delay = stratum_delays[stratum];
   int frame_idx = (current_frame_index - int(round(delay))) % history_size;
   vec4 color = texture(history_tex[frame_idx], uv);
   ```

6. **Per-Stratum Effects**: These can be uniform arrays in the shader:
   ```glsl
   uniform float hueRotate[10];      // Per-stratum hue rotation (degrees)
   uniform float freezeProb[10];     // Freeze probability
   uniform float strobeIntensity[10]; // Strobe strength
   ```

7. **Hue Rotation**:
   ```glsl
   vec3 rotate_hue(vec3 color, float angle) {
       // Convert to HSV, rotate H, convert back
       // Or use approximate matrix rotation
   }
   ```

8. **Temporal Freezing**:
   ```glsl
   if (freezeProb[stratum] > 0.0 && random(uv, time) < freezeProb[stratum] * 0.1) {
       // Use previous frame instead of historical
       color = texture(history_tex[current_frame_index], uv);  // Or hold last
   }
   ```

9. **Strobe Flicker**:
   ```glsl
   if (strobeIntensity[stratum] > 0.0 && sin(time * 20.0) < 0.0) {
       color = vec3(0.0);  // Or flash to white
   }
   ```

10. **Seam Detection**:
    ```glsl
    float depth_grad = length(vec2(dFdx(depth), dFdy(depth)));
    float seam = smoothstep(seamThreshold, seamThreshold + 0.02, depth_grad);
    ```

11. **Datamosh at Seams**:
    - Compute motion vector (could be from optical flow or simple difference between current and historical)
    - Quantize motion to block size
    - Displace color sample by block motion
    - Add brightness boost

    ```glsl
    if (seam > 0.0 && seamDatamosh > 0.0) {
        vec2 motion = get_motion_vector(uv, frame_idx);
        vec2 block_offset = floor(motion * blockSize) / blockSize;
        vec2 sample_uv = uv + block_offset * seam * seamDatamosh * 0.1;
        color = texture(history_tex[frame_idx], sample_uv);
        color.rgb += seam * 0.08 * seamDatamosh;
    }
    ```

12. **Shader Uniforms**:
    ```glsl
    uniform sampler2D current_tex;
    uniform sampler2D depth_tex;
    uniform sampler2D history_tex[MAX_HISTORY];  // Array of textures
    uniform vec2 resolution;
    uniform float u_mix;
    uniform float time;
    uniform int current_frame_index;
    
    uniform int num_strata;                 // 1-10
    uniform float stratum_delays[10];       // Delay per stratum (frames)
    uniform float hue_rotate[10];           // Hue rotation per stratum (degrees)
    uniform float freeze_prob[10];          // Freeze probability per stratum
    uniform float strobe_intensity[10];     // Strobe intensity per stratum
    uniform float seam_datamosh;            // Seam datamosh strength
    uniform float block_size;               // Block size for motion
    uniform float seam_threshold;           // Seam detection threshold
    uniform float mosh_decay;               // Decay with stratum depth
    ```

13. **Parameter Mapping**:
    - `strata`: 0-10 → 1-10 (integer number of strata)
    - `stratumDelays`: array of 10 floats, each 0-10 → frames (use directly)
    - `hueRotate`: 0-10 → 0-360 degrees (multiply by 36)
    - `freeze`: 0-10 → 0-1 probability (divide by 10)
    - `strobe`: 0-10 → 0-1 intensity (divide by 10)
    - `seamDatamosh`: 0-10 → 0-1 strength (divide by 10)
    - `blockSize`: 1-20 → pixels (use directly)
    - `seamThreshold`: 0-0.1 (use directly, maybe from 0-10 scaled)
    - `moshDecay`: 0-10 → 0-1 (divide by 10)

14. **PRESETS**:
    ```python
    PRESETS = {
        "gentle_strat": {
            "strata": 3.0, "stratumDelays": [0.0, 3.0, 6.0],
            "hueRotate": 0.0, "freeze": 0.0, "strobe": 0.0,
            "seamDatamosh": 2.0, "blockSize": 8.0, "seamThreshold": 0.01, "moshDecay": 1.0,
        },
        "glitchy_strat": {
            "strata": 5.0, "stratumDelays": [0.0, 2.0, 4.0, 6.0, 8.0],
            "hueRotate": 5.0, "freeze": 3.0, "strobe": 2.0,
            "seamDatamosh": 7.0, "blockSize": 4.0, "seamThreshold": 0.02, "moshDecay": 5.0,
        },
        "rainbow_strat": {
            "strata": 7.0, "stratumDelays": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "hueRotate": 10.0, "freeze": 0.0, "strobe": 0.0,
            "seamDatamosh": 3.0, "blockSize": 8.0, "seamThreshold": 0.01, "moshDecay": 2.0,
        },
        "frozen_strat": {
            "strata": 4.0, "stratumDelays": [0.0, 2.0, 4.0, 6.0],
            "hueRotate": 0.0, "freeze": 8.0, "strobe": 5.0,
            "seamDatamosh": 4.0, "blockSize": 8.0, "seamThreshold": 0.01, "moshDecay": 3.0,
        },
        "heavy_datamosh": {
            "strata": 6.0, "stratumDelays": [0.0, 2.0, 4.0, 6.0, 8.0, 10.0],
            "hueRotate": 2.0, "freeze": 1.0, "strobe": 1.0,
            "seamDatamosh": 10.0, "blockSize": 2.0, "seamThreshold": 0.005, "moshDecay": 8.0,
        },
    }
    ```

15. **Testing Strategy**:
    - Test with uniform depth: all pixels should use same stratum and delay
    - Test with depth ramp: strata should be clearly separated
    - Test stratum boundaries: verify hard edges between strata
    - Test delays: each stratum should show correct historical frame
    - Test hue rotation: each stratum should have distinct hue shift
    - Test freeze: some frames should freeze randomly
    - Test strobe: stratum should flicker
    - Test seam datamosh: at boundaries, blocks should be displaced
    - Test seam brightness: boundaries should be slightly brighter

16. **Performance**: The effect requires multiple texture fetches (one per stratum? Actually each pixel fetches one history frame based on its stratum, so only 1 fetch per pixel, but need many history textures). The main cost is managing many textures and seam detection. Optimize by:
    - Reducing number of strata
    - Using smaller history buffer (if delays are small)
    - Simplifying datamosh (no motion vectors)
    - Using compute shader for parallel stratum assignment

17. **Future Extensions**:
    - Add audio reactivity to stratum delays or effects
    - Add smooth interpolation between strata (anti-aliasing)
    - Add per-stratum opacity/weight
    - Add depth-based color tinting per stratum
    - Add motion estimation for better datamosh

---

## Easter Egg Idea

When `strata` is set exactly to 6.66, all `stratumDelays` to exactly 6.66, `hueRotate` to exactly 6.66, `freeze` to exactly 6.66, `strobe` to exactly 6.66, `seamDatamosh` to exactly 6.66, `blockSize` to exactly 6.66, `seamThreshold` to exactly 6.66, and `moshDecay` to exactly 6.66, the temporal stratification enters a "sacred geometry" state where the depth range is divided into exactly 6.66 strata (rounding to 6 or 7), each stratum runs exactly 6.66 frames behind the present, the hue rotation creates exactly 6.66 distinct color bands, the freeze probability is exactly 66.6%, the strobe flickers at exactly 6.66 Hz, the seam datamosh creates exactly 6.66-pixel blocks, the seam threshold is exactly 0.0666, and the decay creates exactly 6.66 distinct brightness levels. The entire scene becomes a perfect 6.66×6.66 grid of temporal layers that encode the number 666 in both depth and time, creating a "stratified prayer" where each stratum is exactly 666 milliseconds old.

---

## References

- Temporal stratification: https://en.wikipedia.org/wiki/Stratification_(temporal)
- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- Motion estimation: https://en.wikipedia.org/wiki/Motion_estimation
- Depth buffer: https://en.wikipedia.org/wiki/Depth_buffer
- VJLive legacy: `plugins/vdepth/depth_temporal_strat.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D current_tex;
   uniform sampler2D depth_tex;
   uniform sampler2D history_tex[MAX_HISTORY];  // Array of textures
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   uniform int current_frame_index;
   
   uniform int num_strata;
   uniform float stratum_delays[10];
   uniform float hue_rotate[10];
   uniform float freeze_prob[10];
   uniform float strobe_intensity[10];
   uniform float seam_datamosh;
   uniform float block_size;
   uniform float seam_threshold;
   uniform float mosh_decay;
   
   // Simple pseudo-random
   float random(vec2 uv, float seed) {
       return fract(sin(dot(uv, vec2(12.9898, 78.233)) + seed) * 43758.5453);
   }
   
   // Hue rotation (simplified)
   vec3 rotate_hue(vec3 color, float angle) {
       const vec3 k = vec3(0.57735, 0.57735, 0.57735);
       float cos_angle = cos(angle);
       return cos_angle * color + cross(k, color) * sin(angle) + k * dot(k, color) * (1.0 - cos_angle);
   }
   
   // Motion vector (simple: difference between current and historical)
   vec2 motion_vector(vec2 uv, int hist_idx) {
       vec4 current = texture(current_tex, uv);
       vec4 historical = texture(history_tex[hist_idx], uv);
       // Simple difference in RGB as motion proxy
       vec3 diff = current.rgb - historical.rgb;
       // Could use more sophisticated method
       return vec2(diff.r, diff.g) * 0.1;  // Scale down
   }
   
   void main() {
       float depth = texture(depth_tex, uv).r;
       
       // Assign stratum
       int stratum = int(depth * float(num_strata));
       stratum = clamp(stratum, 0, num_strata - 1);
       
       // Get delay for this stratum
       float delay = stratum_delays[stratum];
       int hist_idx = (current_frame_index - int(round(delay))) % MAX_HISTORY;
       
       // Sample historical frame
       vec4 color = texture(history_tex[hist_idx], uv);
       
       // Apply hue rotation
       if (hue_rotate[stratum] > 0.0) {
           float angle = hue_rotate[stratum] * 3.14159 / 180.0;  // Convert to radians
           color.rgb = rotate_hue(color.rgb, angle);
       }
       
       // Temporal freezing
       if (freeze_prob[stratum] > 0.0) {
           float freeze_threshold = freeze_prob[stratum] * 0.1;
           if (random(uv, time) < freeze_threshold) {
               // Hold previous frame (could use another history buffer)
               color = texture(history_tex[current_frame_index], uv);  // Simplified
           }
       }
       
       // Strobe flicker
       if (strobe_intensity[stratum] > 0.0) {
           float strobe = sin(time * 30.0) * 0.5 + 0.5;  // 30 Hz
           if (strobe < 0.5) {
               color = mix(color, vec4(0.0), strobe_intensity[stratum] * 0.5);
           }
       }
       
       // Seam detection and datamosh
       float depth_grad = length(vec2(dFdx(depth), dFdy(depth)));
       float seam = smoothstep(seam_threshold, seam_threshold + 0.02, depth_grad);
       
       if (seam > 0.0 && seam_datamosh > 0.0) {
           vec2 motion = motion_vector(uv, hist_idx);
           vec2 block_offset = floor(motion * block_size) / block_size;
           vec2 sample_uv = uv + block_offset * seam * seam_datamosh * 0.1;
           color = texture(history_tex[hist_idx], sample_uv);
           color.rgb += seam * 0.08 * seam_datamosh;
           
           // Apply decay based on stratum depth
           float decay_factor = mosh_decay * 0.1 * (float(stratum) / float(num_strata));
           color.rgb *= (1.0 - decay_factor * seam);
       }
       
       fragColor = mix(texture(current_tex, uv), color, u_mix);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthTemporalStratEffect(Effect):
       def __init__(self):
           super().__init__("depth_temporal_strat", STRAT_VERTEX, STRAT_FRAGMENT)
           
           self.depth_source = None
           self.depth_frame = None
           
           self.history_tex = []
           self.history_fbo = []
           self.history_size = 60  # Configurable
           self.current_index = 0
           
           self.parameters = {
               'strata': 5.0,
               'stratumDelays': [0.0, 2.0, 4.0, 6.0, 8.0],  # Will need to handle as array
               'hueRotate': 0.0,
               'freeze': 0.0,
               'strobe': 0.0,
               'seamDatamosh': 5.0,
               'blockSize': 8.0,
               'seamThreshold': 0.01,
               'moshDecay': 3.0,
           }
           
           self.shader = None
           self.num_strata = 5
           self.stratum_delays = [0.0, 2.0, 4.0, 6.0, 8.0]
       
       def _ensure_history_buffers(self, width, height):
           if not self.history_tex:
               for i in range(self.history_size):
                   tex = glGenTextures(1)
                   glBindTexture(GL_TEXTURE_2D, tex)
                   glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                   self.history_tex.append(tex)
                   
                   fbo = glGenFramebuffers(1)
                   glBindFramebuffer(GL_FRAMEBUFFER, fbo)
                   glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)
                   glBindFramebuffer(GL_FRAMEBUFFER, 0)
                   self.history_fbo.append(fbo)
       
       def process_frame(self, frame):
           h, w = frame.shape[:2]
           self._ensure_history_buffers(w, h)
           
           # Update depth
           self._update_depth()
           
           # Upload current frame to history buffer at current_index
           glBindFramebuffer(GL_FRAMEBUFFER, self.history_fbo[self.current_index])
           # Upload frame data to texture
           glBindTexture(GL_TEXTURE_2D, self.history_tex[self.current_index])
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, frame)
           
           # Render effect to screen
           glBindFramebuffer(GL_FRAMEBUFFER, 0)
           
           self.shader.use()
           self._apply_uniforms(time, (w, h))
           
           # Bind current frame
           glActiveTexture(GL_TEXTURE0)
           glBindTexture(GL_TEXTURE_2D, self.current_tex)
           glUniform1i(glGetUniformLocation(self.shader.program, "current_tex"), 0)
           
           # Bind depth
           glActiveTexture(GL_TEXTURE1)
           glBindTexture(GL_TEXTURE_2D, self.depth_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "depth_tex"), 1)
           
           # Bind history textures (array)
           for i in range(min(10, self.history_size)):  # Max 10 in shader
               glActiveTexture(GL_TEXTURE2 + i)
               glBindTexture(GL_TEXTURE_2D, self.history_tex[i])
               glUniform1i(glGetUniformLocation(self.shader.program, f"history_tex[{i}]"), 2 + i)
           
           glUniform1i(glGetUniformLocation(self.shader.program, "current_frame_index"), self.current_index)
           glUniform1i(glGetUniformLocation(self.shader.program, "num_strata"), self.num_strata)
           
           # Set stratum delays array
           delay_loc = glGetUniformLocation(self.shader.program, "stratum_delays")
           glUniform1fv(delay_loc, len(self.stratum_delays), self.stratum_delays)
           
           # Set other arrays similarly...
           
           draw_fullscreen_quad()
           
           # Advance circular buffer
           self.current_index = (self.current_index + 1) % self.history_size
           
           result = self._read_pixels()
           return result
   ```

3. **Stratum Delays**: The `stratumDelays` parameter is an array. In the UI, this might be represented as multiple sliders or a single "delay spread" parameter that auto-distributes. The legacy uses `stratumDelays` as a list.

4. **Seam Detection**: The `seamThreshold` is a small value (0.01) representing depth gradient magnitude. Pixels where depth changes rapidly are considered on a seam.

5. **Motion Vectors**: Computing true motion vectors requires optical flow, which is expensive. The effect might use a simpler proxy: the difference between current and historical frames, or just random displacement. The legacy mentions "motion-vector block displacement" but may use a simplified approach.

6. **History Size**: The `MAX_HISTORY` in the legacy is 120, but they only allocate 4 textures for `DepthTemporalEcho`. For `DepthTemporalStrat`, they might allocate a larger ring buffer. The spec should allow configurable history size based on maximum delay needed.

7. **Testing**: Create a depth test pattern with clear strata (e.g., horizontal bands). Verify:
   - Each band shows a different time offset
   - Boundaries show datamosh artifacts
   - Hue rotation varies per band
   - Freeze/strobe affect specific bands

8. **Performance**: The shader does multiple texture fetches (one for history, plus maybe for motion estimation). The main cost is the large history buffer management. Optimize by:
   - Using fewer strata
   - Using smaller history textures (if delays are small)
   - Simplifying seam datamosh

---

## Conclusion

The DepthTemporalStratEffect creates a striking visual where depth slices the scene into separate temporal streams. Each depth stratum runs at its own time offset, creating a layered, ghostly effect with hard boundaries that produce datamosh artifacts. With per-stratum hue rotation, freezing, and strobe effects, it's a powerful tool for creating psychedelic, glitchy visuals that manipulate time itself across the depth dimension.

---
>>>>>>> REPLACE