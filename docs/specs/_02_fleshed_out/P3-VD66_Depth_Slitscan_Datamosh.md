# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD66_Depth_Slitscan_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD66 — DepthSlitScanDatamoshEffect

## Description

The DepthSlitScanDatamoshEffect combines the classic slit-scan video art technique with depth camera data to create temporal smearing that varies by depth. Near objects scan quickly (more live, less temporal history), while far objects scan slowly (more temporal history, more smearing). Scan lines warp along depth contours, and at depth boundaries, datamosh artifacts erupt from temporal discontinuities. The effect features per-channel chromatic temporal splitting, depth-responsive curvature, and infinite recursive feedback trails.

This effect is ideal for creating psychedelic, time-warping visuals where depth controls the rate of temporal scanning. It's perfect for VJ performances that want to create the illusion of time bending differently at different depths. The slit-scan technique creates characteristic smears and streaks, while the depth modulation adds a 3D-aware temporal distortion.

## What This Module Does

- Applies slit-scan temporal smearing to video
- Depth modulates scan speed (near=fast, far=slow)
- Scan lines warp along depth contours
- Datamosh artifacts at depth boundaries
- Per-channel chromatic temporal splitting (RGB channels scan at different rates)
- Recursive feedback trails
- Configurable scan position, speed, width, direction
- Optional scan glow with depth-based color

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT include audio reactivity (may be added later)
- Does NOT support arbitrary scan shapes (lines only)
- Does NOT implement true 3D slit-scan (2D screen-space with depth modulation)
- Does NOT include motion estimation (uses depth for modulation only)

---

## Detailed Behavior

### Slit-Scan Temporal Smearing

Slit-scan is a technique where a narrow slit scans across the image over time, and the output at each pixel is determined by what was at that pixel when the slit passed over it. This creates temporal smearing: the image becomes a composite of different times.

1. **Define scan line**: A horizontal or vertical line that moves across the screen
2. **For each pixel**:
   - Determine where the scan line was when this pixel's "time" occurred
   - Sample the video at that historical position
   - That becomes the output color

### Depth-Modulated Scanning

Depth controls the scan speed and temporal sampling:
- **Near objects** (small depth): scan quickly → less temporal offset → more "live"
- **Far objects** (large depth): scan slowly → more temporal offset → more history

Implementation:
```glsl
float depth = texture(depth_tex, uv).r;
float scan_speed = base_speed + depth * depth_speed_mod;
float time_offset = scan_coord / scan_speed;  // How far back in time to sample
vec2 historical_uv = get_uv_at_time(time - time_offset);
color = texture(video_tex, historical_uv);
```

### Scan Line Warping

The scan line itself can warp along depth contours:
```glsl
float depth_warp = depthWarp * 0.01;
float scan_coord = scan_position + time * scan_speed;
scan_coord += depth * depth_warp;  // Warp scan line based on depth
```

### Datamosh at Boundaries

At depth boundaries (where depth changes rapidly), introduce datamosh artifacts:
```glsl
float depth_gradient = length(vec2(dFdx(depth), dFdy(depth)));
if (depth_gradient > threshold) {
    // Add block corruption, color shift, or temporal displacement
    color = datamosh(color, depth_gradient);
}
```

### Chromatic Temporal Splitting

Each color channel (R, G, B) can have its own temporal sampling offset, creating chromatic aberration:
```glsl
float channel_offset[3] = {0.0, channel_phase, -channel_phase};
for (int c = 0; c < 3; c++) {
    float t = time - time_offset + channel_offset[c];
    color[c] = texture(video_tex, get_uv_at_time(t))[c];
}
```

### Feedback Trails

Recursive feedback creates infinite trails:
```glsl
vec4 feedback = texture(feedback_tex, uv);
vec4 result = mix(color, feedback, feedback_strength * trail_persistence);
```

### Scan Glow

Add a glowing line at the current scan position:
```glsl
float scan_line_dist = abs(uv.y - scan_coord_normalized);
float glow = exp(-scan_line_dist * scan_width * 10.0) * scan_glow;
vec3 glow_color = mix(warm_color, cool_color, depth);
result.rgb += glow_color * glow;
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `scanPosition` | float | 5.0 | 0.0-10.0 | Initial scan line position (0-1 normalized) |
| `scanSpeed` | float | 2.0 | 0.0-10.0 | Base scan speed |
| `scanWidth` | float | 5.0 | 0.0-10.0 | Width of scan line (affects smearing) |
| `scanDirection` | float | 0.0 | 0.0-10.0 | Scan direction (0=horizontal, 10=vertical) |
| `depthSpeedMod` | float | 3.0 | 0.0-10.0 | How much depth affects scan speed |
| `depthWarp` | float | 2.0 | 0.0-10.0 | Amount of depth-based scan line warping |
| `depthScanOffset` | float | 3.0 | 0.0-10.0 | Depth-based temporal offset |
| `nearFarFlip` | float | 0.0 | 0.0-10.0 | Invert depth modulation (near=slow, far=fast) |
| `chromaticSplit` | float | 1.0 | 0.0-10.0 | RGB channel temporal separation |
| `channelPhase` | float | 5.0 | 0.0-10.0 | Phase offset for chromatic splitting |
| `moshIntensity` | float | 2.0 | 0.0-10.0 | Datamosh artifact intensity at depth boundaries |
| `blockArtifact` | float | 1.0 | 0.0-10.0 | Block corruption size/strength |
| `feedbackStrength` | float | 3.0 | 0.0-10.0 | How much feedback trails contribute |
| `trailPersistence` | float | 4.0 | 0.0-10.0 | How long trails persist (decay rate) |
| `scanGlow` | float | 1.0 | 0.0-10.0 | Intensity of scan line glow |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class DepthSlitScanDatamoshEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def reset_feedback(self) -> None: ...  # Clear feedback buffer
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Slit-scan datamosh output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_video_texture: int` — Current video frame texture
- `_history_textures: List[int]` — Ping-pong history buffers for feedback
- `_history_fbos: List[int]` — Framebuffers for history buffers
- `_current_history: int` — Index of current history buffer
- `_parameters: dict` — All slit-scan parameters
- `_shader: ShaderProgram` — Compiled shader
- `_time_offset: float` — Accumulated time offset for scan position

**Per-Frame:**
- Update depth data from source
- Update scan position based on speed and direction
- Upload current frame to video texture
- Render slit-scan effect with temporal sampling
- Apply datamosh at depth boundaries
- Apply chromatic splitting
- Apply feedback trails
- Apply scan glow
- Swap history buffer
- Return result

**Initialization:**
- Create video texture
- Create history textures (2, ping-pong) for feedback
- Create history FBOs (2)
- Compile shader
- Default parameters from "gentle_scan" preset
- Initialize `_current_history = 0`, `_time_offset = 0.0`

**Cleanup:**
- Delete video texture
- Delete history textures (2)
- Delete history FBOs (2)
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Video texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame |
| History textures (2) | GL_TEXTURE_2D | GL_RGBA8 or GL_RGBA16F | frame size | Updated each frame (ping-pong) |
| History FBOs (2) | GL_FRAMEBUFFER | N/A | frame size | Persistent |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Video texture: 921,600 bytes
- History buffers: 2 × 921,600 = 1,843,200 bytes
- Shader: ~30-50 KB (complex)
- Total: ~2.8 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use uniform depth (0.5) | Normal operation |
| FBO incomplete | `RuntimeError("FBO error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and FBO operations must occur on the thread with the OpenGL context. The effect uses ping-pong buffers and updates them each frame; concurrent `process_frame()` calls will cause race conditions and corrupted rendering. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Texture uploads: ~0.5-1 ms
- Shader execution (complex slit-scan + datamosh + feedback): ~10-20 ms
- Total: ~10.5-21 ms on GPU (heavy effect)

**Optimization Strategies:**
- Reduce history buffer resolution (half-res)
- Disable expensive features (chromatic split, datamosh, feedback)
- Use simpler datamosh (no block artifacts)
- Reduce number of texture fetches in temporal sampling
- Use compute shader for parallel processing
- Lower video resolution

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Slit-scan parameters configured
- [ ] Datamosh parameters configured
- [ ] Feedback parameters configured
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_scan_position` | Scan line position controlled correctly |
| `test_scan_speed` | Scan speed affects temporal offset |
| `test_depth_speed_mod` | Depth modulates scan speed |
| `test_depth_warp` | Scan line warps along depth |
| `test_chromatic_split` | RGB channels have different temporal offsets |
| `test_datamosh_at_boundaries` | Datamosh artifacts appear at depth edges |
| `test_feedback` | Recursive trails persist and decay |
| `test_scan_glow` | Glow appears at scan line position |
| `test_near_far_flip` | Inverts depth modulation |
| `test_reset_feedback` | Feedback buffer can be cleared |
| `test_process_frame_accumulation` | Effect builds up over time |
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
- [ ] Git commit with `[Phase-3] P3-VD66: depth_slitscan_datamosh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_slitscan_datamosh.py` — VJLive Original implementation
- `plugins/core/depth_slitscan_datamosh/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_slitscan_datamosh/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthSlitScanDatamoshEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_slitscan_datamosh`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for scan speed modulation and warping
- Parameters: `scanPosition`, `scanSpeed`, `scanWidth`, `scanDirection`, `depthSpeedMod`, `depthWarp`, `depthScanOffset`, `nearFarFlip`, `chromaticSplit`, `channelPhase`, `moshIntensity`, `blockArtifact`, `feedbackStrength`, `trailPersistence`, `scanGlow`
- Allocates GL resources: video texture, history textures (2), history FBOs (2)
- Shader implements slit-scan temporal sampling, datamosh, chromatic split, feedback, and glow
- Presets: "gentle_scan", "temporal_fracture"

---

## Notes for Implementers

1. **Core Concept**: Slit-scan creates temporal smearing by sampling the video at different times for different pixels. Depth modulates the temporal sampling rate: near = fast scan (less history), far = slow scan (more history). This creates a depth-dependent time warp.

2. **Temporal Sampling**:
   - Need to maintain a history of previous frames (texture buffer or ring buffer)
   - For each pixel, compute a time offset based on scan position and depth
   - Sample the video at that historical time
   - The history can be stored in a feedback buffer (ping-pong)

3. **Scan Line**:
   - The scan line is a 1D line that moves across the 2D image
   - Can be horizontal (varying y) or vertical (varying x)
   - Position controlled by `scanPosition` and `scanSpeed`
   - Direction controlled by `scanDirection` (0=horizontal, 10=vertical)
   - Width controlled by `scanWidth` (affects smearing)

4. **Depth Modulation**:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float speed_mod = 1.0 + depth * depthSpeedMod / 10.0;
   if (nearFarFlip > 0.0) speed_mod = 1.0 + (1.0 - depth) * depthSpeedMod / 10.0;
   float scan_speed = scanSpeed * speed_mod;
   float time_offset = (scan_coord - scanPosition) / scan_speed;
   ```

5. **Scan Warping**:
   ```glsl
   float warp = depth * depthWarp * 0.01;
   scan_coord += warp * sin(uv.x * 10.0);  // Example: warp along x
   ```

6. **Chromatic Splitting**:
   ```glsl
   float phase = channelPhase * 0.1;
   for (int c = 0; c < 3; c++) {
       float channel_offset = (c == 0) ? 0.0 : (c == 1) ? phase : -phase;
       float t = time - time_offset + channel_offset;
       color[c] = sample_video_at_time(t, uv)[c];
   }
   ```

7. **Datamosh at Boundaries**:
   ```glsl
   float depth_grad = length(vec2(dFdx(depth), dFdy(depth)));
   if (depth_grad > moshIntensity * 0.01) {
       // Add block artifacts, color shift, or temporal displacement
       color = apply_datamosh(color, depth_grad, blockArtifact);
   }
   ```

8. **Feedback**:
   - Maintain a feedback texture that stores the previous output
   - Each frame: `output = mix(current_slit_scan, feedback, feedbackStrength * trailPersistence)`
   - Write output to feedback buffer for next frame

9. **Scan Glow**:
   ```glsl
   float scan_line_y = scan_coord_normalized;  // 0-1
   float dist = abs(uv.y - scan_line_y);
   float glow = exp(-dist * scanWidth * 10.0) * scanGlow;
   vec3 glow_color = mix(vec3(1.0, 0.3, 0.1), vec3(0.1, 0.4, 1.0), depth);
   result += glow_color * glow;
   ```

10. **Shader Uniforms**:
    ```glsl
    uniform sampler2D video_tex;       // Current video frame
    uniform sampler2D depth_tex;       // Depth
    uniform sampler2D feedback_tex;    // Previous output (for feedback)
    uniform vec2 resolution;
    uniform float u_mix;
    uniform float time;
    
    uniform float scanPosition;        // 0-1
    uniform float scanSpeed;           // 0-10
    uniform float scanWidth;           // 0-10
    uniform float scanDirection;       // 0-10 (0=horizontal, 10=vertical)
    uniform float depthSpeedMod;       // 0-10
    uniform float depthWarp;           // 0-10
    uniform float depthScanOffset;     // 0-10
    uniform float nearFarFlip;         // 0 or 1
    uniform float chromaticSplit;      // 0-10
    uniform float channelPhase;        // 0-10
    uniform float moshIntensity;       // 0-10
    uniform float blockArtifact;       // 0-10
    uniform float feedbackStrength;    // 0-10
    uniform float trailPersistence;    // 0-10
    uniform float scanGlow;            // 0-10
    ```

11. **Parameter Mapping**:
    - `scanPosition`: 0-10 → 0.0-1.0 (divide by 10)
    - `scanSpeed`: 0-10 → multiplier (e.g., 0.1 per unit)
    - `scanWidth`: 0-10 → width in normalized units (0.01-0.1)
    - `scanDirection`: 0-10 → angle or axis (0=horizontal, 10=vertical)
    - `depthSpeedMod`: 0-10 → speed multiplier (0=no mod, 10=10x)
    - `depthWarp`: 0-10 → warp amplitude
    - `depthScanOffset`: 0-10 → additional time offset
    - `nearFarFlip`: 0-10 → 0 or 1 (threshold >5)
    - `chromaticSplit`: 0-10 → channel offset multiplier
    - `channelPhase`: 0-10 → phase in some unit
    - `moshIntensity`: 0-10 → datamosh strength
    - `blockArtifact`: 0-10 → block size/strength
    - `feedbackStrength`: 0-10 → mix ratio (0-1)
    - `trailPersistence`: 0-10 → decay rate (0=fast decay, 10=slow)
    - `scanGlow`: 0-10 → glow intensity

12. **PRESETS**:
    ```python
    PRESETS = {
        "gentle_scan": {
            "scanPosition": 5.0, "scanSpeed": 2.0, "scanWidth": 5.0,
            "scanDirection": 0.0, "depthSpeedMod": 3.0, "depthWarp": 2.0,
            "depthScanOffset": 3.0, "nearFarFlip": 0.0, "chromaticSplit": 1.0,
            "channelPhase": 5.0, "moshIntensity": 2.0, "blockArtifact": 1.0,
            "feedbackStrength": 3.0, "trailPersistence": 4.0, "scanGlow": 1.0,
        },
        "temporal_fracture": {
            "scanPosition": 5.0, "scanSpeed": 5.0, "scanWidth": 3.0,
            "scanDirection": 0.0, "depthSpeedMod": 5.0, "depthWarp": 4.0,
            "depthScanOffset": 5.0, "nearFarFlip": 0.0, "chromaticSplit": 3.0,
            "channelPhase": 8.0, "moshIntensity": 6.0, "blockArtifact": 4.0,
            "feedbackStrength": 5.0, "trailPersistence": 3.0, "scanGlow": 2.0,
        },
        "chromatic_aberation": {
            "scanPosition": 5.0, "scanSpeed": 3.0, "scanWidth": 4.0,
            "scanDirection": 0.0, "depthSpeedMod": 2.0, "depthWarp": 1.0,
            "depthScanOffset": 2.0, "nearFarFlip": 0.0, "chromaticSplit": 8.0,
            "channelPhase": 7.0, "moshIntensity": 1.0, "blockArtifact": 0.5,
            "feedbackStrength": 2.0, "trailPersistence": 5.0, "scanGlow": 1.5,
        },
        "vertical_warp": {
            "scanPosition": 5.0, "scanSpeed": 4.0, "scanWidth": 6.0,
            "scanDirection": 10.0, "depthSpeedMod": 4.0, "depthWarp": 6.0,
            "depthScanOffset": 4.0, "nearFarFlip": 0.0, "chromaticSplit": 2.0,
            "channelPhase": 6.0, "moshIntensity": 3.0, "blockArtifact": 2.0,
            "feedbackStrength": 4.0, "trailPersistence": 4.0, "scanGlow": 2.0,
        },
        "inverted_depth": {
            "scanPosition": 5.0, "scanSpeed": 3.0, "scanWidth": 5.0,
            "scanDirection": 0.0, "depthSpeedMod": 3.0, "depthWarp": 2.0,
            "depthScanOffset": 3.0, "nearFarFlip": 1.0, "chromaticSplit": 1.0,
            "channelPhase": 5.0, "moshIntensity": 2.0, "blockArtifact": 1.0,
            "feedbackStrength": 3.0, "trailPersistence": 4.0, "scanGlow": 1.0,
        },
    }
    ```

13. **Testing Strategy**:
    - Test with uniform depth: all pixels should have same temporal offset
    - Test with depth gradient: offset should vary smoothly
    - Test nearFarFlip: should invert the relationship
    - Test chromatic split: RGB channels should be offset
    - Test datamosh: should appear at depth edges
    - Test feedback: trails should persist and decay
    - Test scan glow: should appear at scan line position

14. **Performance**: This is a heavy effect due to multiple texture fetches and complex shader. Optimize by:
    - Using lower resolution for feedback buffer
    - Disabling expensive features (chromatic split, datamosh, feedback)
    - Reducing texture fetch count in temporal sampling
    - Using compute shader for parallel processing

15. **Future Extensions**:
    - Add audio reactivity to scan speed
    - Add multiple scan lines
    - Add scan line shape variation (curved, spiral)
    - Add depth-based color tinting
    - Add motion estimation for more accurate temporal sampling

---
-

## References

- Slit-scan photography: https://en.wikipedia.org/wiki/Slit-scan_photography
- Temporal smearing: https://en.wikipedia.org/wiki/Motion_blur
- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- Chromatic aberration: https://en.wikipedia.org/wiki/Chromatic_aberration
- Feedback: https://en.wikipedia.org/wiki/Feedback
- VJLive legacy: `plugins/vdepth/depth_slitscan_datamosh.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D video_tex;       // Current video
   uniform sampler2D depth_tex;       // Depth
   uniform sampler2D feedback_tex;    // Previous output (feedback)
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float scanPosition;        // 0-1
   uniform float scanSpeed;           // 0-10
   uniform float scanWidth;           // 0-10
   uniform float scanDirection;       // 0-10 (0=horizontal, 10=vertical)
   uniform float depthSpeedMod;       // 0-10
   uniform float depthWarp;           // 0-10
   uniform float depthScanOffset;     // 0-10
   uniform float nearFarFlip;         // 0 or 1
   uniform float chromaticSplit;      // 0-10
   uniform float channelPhase;        // 0-10
   uniform float moshIntensity;       // 0-10
   uniform float blockArtifact;       // 0-10
   uniform float feedbackStrength;    // 0-10
   uniform float trailPersistence;    // 0-10
   uniform float scanGlow;            // 0-10
   
   // Function to sample video at a specific time
   // This would need a history buffer or time-varying texture
   vec4 sample_video_at_time(float t, vec2 uv) {
       // In a real implementation, you'd have a ring buffer of frames
       // or a feedback texture that accumulates history
       // For simplicity, assume we can sample from a texture that holds history
       return texture(video_tex, uv);  // Placeholder
   }
   
   // Datamosh function
   vec3 apply_datamosh(vec3 color, float gradient, float intensity) {
       if (gradient < intensity * 0.01) return color;
       // Block corruption: shift color channels
       float shift = floor(gradient * 10.0) * 0.1;
       color.r = texture(video_tex, uv + vec2(shift, 0.0)).r;
       color.b = texture(video_tex, uv - vec2(shift, 0.0)).b;
       return color;
   }
   
   void main() {
       float depth = texture(depth_tex, uv).r;
       
       // Determine scan direction
       bool horizontal = scanDirection < 5.0;  // 0-4.9 = horizontal, 5-10 = vertical
       
       // Compute scan coordinate along the scan line
       float scan_coord = horizontal ? uv.y : uv.x;
       
       // Apply depth-based speed modulation
       float speed_mod = 1.0 + depth * depthSpeedMod / 10.0;
       if (nearFarFlip > 0.5) {
           speed_mod = 1.0 + (1.0 - depth) * depthSpeedMod / 10.0;
       }
       float scan_speed = scanSpeed * speed_mod;
       
       // Apply depth warp
       float warp = depth * depthWarp * 0.01;
       scan_coord += warp * sin((horizontal ? uv.x : uv.y) * 10.0);
       
       // Compute time offset based on scan position and speed
       float scan_pos_norm = scanPosition / 10.0;  // 0-1
       float time_offset = (scan_coord - scan_pos_norm) / max(scan_speed, 0.001);
       time_offset += depth * depthScanOffset * 0.01;
       
       // Chromatic splitting
       float phase = channelPhase * 0.1;
       float offsets[3] = {0.0, phase, -phase};
       
       vec3 color = vec3(0.0);
       for (int c = 0; c < 3; c++) {
           float t = time - time_offset + offsets[c] * (chromaticSplit > 0.0 ? 1.0 : 0.0);
           // Sample video at historical time
           // This is a simplification; real implementation needs history buffer
           vec2 hist_uv = uv;  // Would be computed based on t
           color[c] = texture(video_tex, hist_uv)[c];
       }
       
       // Apply datamosh at depth boundaries
       float depth_grad = length(vec2(dFdx(depth), dFdy(depth)));
       if (moshIntensity > 0.0 && depth_grad > 0.01) {
           color = apply_datamosh(color, depth_grad, moshIntensity);
       }
       
       // Apply feedback
       if (feedbackStrength > 0.0) {
           vec4 feedback = texture(feedback_tex, uv);
           color = mix(color, feedback.rgb, feedbackStrength * trailPersistence / 10.0);
       }
       
       // Apply scan glow
       if (scanGlow > 0.0) {
           float scan_line = scan_pos_norm;  // Current scan line position (normalized)
           float dist = abs(scan_coord - scan_line);
           float glow = exp(-dist * scanWidth * 10.0) * scanGlow;
           vec3 glow_color = mix(vec3(1.0, 0.3, 0.1), vec3(0.1, 0.4, 1.0), depth);
           color += glow_color * glow * 0.3;
       }
       
       fragColor = mix(texture(video_tex, uv), vec4(color, 1.0), u_mix);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthSlitScanDatamoshEffect(Effect):
       def __init__(self):
           super().__init__("depth_slitscan_datamosh", SLITSCAN_VERTEX, SLITSCAN_FRAGMENT)
           
           self.depth_source = None
           self.depth_frame = None
           
           self.video_texture = 0
           
           self.history_tex = [0, 0]
           self.history_fbo = [0, 0]
           self.current_history = 0
           
           self.parameters = {
               'scanPosition': 5.0,
               'scanSpeed': 2.0,
               'scanWidth': 5.0,
               'scanDirection': 0.0,
               'depthSpeedMod': 3.0,
               'depthWarp': 2.0,
               'depthScanOffset': 3.0,
               'nearFarFlip': 0.0,
               'chromaticSplit': 1.0,
               'channelPhase': 5.0,
               'moshIntensity': 2.0,
               'blockArtifact': 1.0,
               'feedbackStrength': 3.0,
               'trailPersistence': 4.0,
               'scanGlow': 1.0,
           }
           
           self.shader = None
           self.scan_time = 0.0
       
       def _ensure_textures(self, width, height):
           if self.video_texture == 0:
               self.video_texture = glGenTextures(1)
               glBindTexture(GL_TEXTURE_2D, self.video_texture)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
           
           if self.history_tex[0] == 0:
               for i in range(2):
                   self.history_tex[i] = glGenTextures(1)
                   glBindTexture(GL_TEXTURE_2D, self.history_tex[i])
                   glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                   
                   self.history_fbo[i] = glGenFramebuffers(1)
                   glBindFramebuffer(GL_FRAMEBUFFER, self.history_fbo[i])
                   glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.history_tex[i], 0)
                   glBindFramebuffer(GL_FRAMEBUFFER, 0)
   ```

3. **Process Frame**:
   ```python
   def process_frame(self, frame):
       h, w = frame.shape[:2]
       self._ensure_textures(w, h)
       
       # Update depth
       self._update_depth()
       
       # Upload current video frame
       glBindTexture(GL_TEXTURE_2D, self.video_texture)
       glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, frame)
       
       # Update scan time
       self.scan_time += 1.0 / 60.0 * self.parameters['scanSpeed'] * 0.1
       
       # Render effect to screen
       glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       self.shader.use()
       self._apply_uniforms(self.scan_time, (w, h))
       
       # Bind textures
       glActiveTexture(GL_TEXTURE0)
       glBindTexture(GL_TEXTURE_2D, self.video_texture)
       glUniform1i(glGetUniformLocation(self.shader.program, "video_tex"), 0)
       
       glActiveTexture(GL_TEXTURE1)
       glBindTexture(GL_TEXTURE_2D, self.depth_texture)
       glUniform1i(glGetUniformLocation(self.shader.program, "depth_tex"), 1)
       
       glActiveTexture(GL_TEXTURE2)
       glBindTexture(GL_TEXTURE_2D, self.history_tex[self.current_history])
       glUniform1i(glGetUniformLocation(self.shader.program, "feedback_tex"), 2)
       
       draw_fullscreen_quad()
       
       # Copy result to history buffer for next frame
       read_idx = self.current_history
       write_idx = 1 - self.current_history
       
       glBindFramebuffer(GL_FRAMEBUFFER, self.history_fbo[write_idx])
       glBindTexture(GL_TEXTURE_2D, self.history_tex[read_idx])
       # Actually need to render current output to history FBO
       # Could use glBlitFramebuffer or render quad again
       
       glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       self.current_history = write_idx
       
       result = self._read_pixels()
       return result
   ```

4. **Temporal Sampling**: The tricky part is sampling the video at historical times. Options:
   - **Ring buffer**: Store N previous frames in textures, index by time offset
   - **Feedback**: Use the feedback texture as an approximation (it contains past outputs, not raw video)
   - **Single frame**: If only current frame available, temporal smearing impossible
   The legacy likely uses a feedback approach where the "history" is the previous output, creating recursive trails.

5. **Scan Direction**: `scanDirection` 0-10 maps to angle or axis. Could be:
   - 0-5: horizontal scan (varying y)
   - 5-10: vertical scan (varying x)
   Or continuous angle: `angle = scanDirection * 0.5π`

6. **Datamosh**: The `blockArtifact` parameter could control block size or corruption strength. Simple approach: shift color channels based on depth gradient.

7. **Feedback**: The `feedbackStrength` and `trailPersistence` control how much previous output feeds back:
   ```glsl
   float feedback_mix = feedbackStrength * trailPersistence / 10.0;
   color = mix(color, feedback_color, feedback_mix);
   ```

8. **Scan Glow**: The glow is a 1D Gaussian along the scan line. The color shifts from warm (near) to cool (far).

9. **Testing**: Create a test pattern with depth gradient. Verify:
   - Near region has less temporal smearing (more current)
   - Far region has more smearing (more history)
   - Scan line moves across screen
   - Chromatic split creates RGB separation
   - Datamosh appears at depth edges

10. **Performance**: The shader is complex with multiple texture fetches. Optimize by:
    - Reducing texture fetch count (combine operations)
    - Using lower precision (mediump)
    - Disabling expensive features via `#ifdef` based on parameter thresholds
    - Using compute shader for parallel temporal sampling

---

## Conclusion

The DepthSlitScanDatamoshEffect is a complex, multi-layered effect that combines slit-scan temporal smearing with depth modulation, datamosh artifacts, chromatic splitting, and recursive feedback. It creates psychedelic, time-warping visuals where depth controls the rate of temporal scanning. With its extensive parameter set and presets, it offers a wide range of temporal distortion effects perfect for VJ performances that want to bend time and space.

---
