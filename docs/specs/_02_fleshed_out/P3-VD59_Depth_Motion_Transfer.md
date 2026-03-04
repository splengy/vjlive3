# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD59_Depth_Motion_Transfer.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD59 — DepthMotionTransferEffect

## Description

The DepthMotionTransferEffect uses frame-to-frame depth differences to extract the performer's kinetic energy and transfers that motion to displace a second video feed. It computes a motion field from depth changes between consecutive frames, then uses those motion vectors to warp the second video. Movement toward the camera pushes the video outward (expansion), while movement away pulls it inward (contraction). The motion field accumulates in a persistent buffer with configurable decay, creating lasting trails and motion echoes.

This effect is ideal for creating organic, motion-driven distortion where the performer's movements directly manipulate secondary visuals. It's perfect for VJ performances that want to translate dance or physical motion into visual displacement effects. The accumulation buffer means that even after movement stops, the displaced video retains echoes of that motion, creating fluid, trailing effects.

## What This Module Does

- Computes frame-to-frame depth difference (motion field)
- Converts depth changes into 2D displacement vectors
- Applies displacement to a second video feed
- Accumulates motion in a persistent buffer with decay
- Supports motion blur, color smearing, and thresholding
- Configurable motion scale, decay, and feedback
- GPU-accelerated with ping-pong buffers for accumulation

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions (accumulation resets on restart)
- Does NOT include audio reactivity (may be added later)
- Does NOT support multiple independent motion sources (single depth source)
- Does NOT implement 3D motion reconstruction (2D screen-space only)
- Does NOT include external effect routing (self-contained)

---

## Detailed Behavior

### Motion Extraction Pipeline

1. **Capture current depth frame**: `depth_current`
2. **Retrieve previous depth frame**: `depth_previous` (from buffer)
3. **Compute depth difference**:
   ```
   depth_diff = depth_current - depth_previous
   ```
4. **Compute motion gradient**: Use `dFdx` and `dFdy` on `depth_diff` to get motion vectors:
   ```
   motion_x = dFdx(depth_diff)
   motion_y = dFdy(depth_diff)
   motion = vec2(motion_x, motion_y)
   ```
5. **Scale motion**: Multiply by `motionScale`:
   ```
   motion *= motionScale
   ```
6. **Accumulate motion**: Add to persistent motion buffer with decay:
   ```
   motion_buffer = motion_buffer * decayRate + motion * (1.0 - decayRate)
   ```
7. **Displace second video**: Use accumulated motion to offset UV coordinates:
   ```
   uv_displaced = uv + motion_buffer
   displaced_video = texture(second_video, uv_displaced)
   ```
8. **Apply effects**: Motion blur, color smear, thresholding
9. **Final mix**: Blend with original video

### Motion Direction Semantics

- **Positive depth change** (object moving toward camera): `depth_diff > 0`
  - Motion vector direction depends on gradient sign
  - Typically, objects moving toward camera appear to expand outward
- **Negative depth change** (object moving away): `depth_diff < 0`
  - Contraction effect
- The actual displacement direction is determined by the spatial gradient of depth change, not just the sign.

### Accumulation Buffer

The effect maintains a persistent motion buffer (texture) that accumulates motion vectors over time. Each frame:
- The buffer is scaled by `decayRate` (0-1) to gradually fade old motion
- New motion is added, scaled by `(1 - decayRate)` or a separate factor
- This creates trails: motion persists and fades slowly

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `motionScale` | float | 6.0 | 0.0-10.0 | Overall strength of motion displacement |
| `decayRate` | float | 5.0 | 0.0-10.0 | How quickly motion fades (0=instant, 10=never) |
| `motionBlur` | float | 4.0 | 0.0-10.0 | Amount of motion blur applied |
| `forceDirection` | float | 0.0 | 0.0-10.0 | Force motion to specific direction (0=auto) |
| `colorSmear` | float | 3.0 | 0.0-10.0 | Color smearing along motion direction |
| `threshold` | float | 2.0 | 0.0-10.0 | Minimum depth change to trigger motion |
| `accumulate` | float | 7.0 | 0.0-10.0 | How much new motion accumulates (vs replace) |
| `feedback` | float | 3.0 | 0.0-10.0 | Feedback strength (re-apply motion to result) |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthMotionTransferEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def set_second_video_source(self, source) -> None: ...  # If separate
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray, second_video: np.ndarray) -> np.ndarray: ...
    def reset_accumulation(self) -> None: ...  # Clear motion buffer
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) — also used for depth |
| `second_video` | `np.ndarray` | Second video to be displaced (HxWxC, RGB) |
| **Output** | `np.ndarray` | Motion-displaced second video (HxWxC, RGB) |

**Note**: The effect may use the same frame for depth and as the first video, or accept separate inputs. The legacy suggests it displaces "the second video feed", implying two video inputs.

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_prev_depth_frame: Optional[np.ndarray]` — Previous depth frame for differencing
- `_motion_buffer_texture: int` — GL texture storing accumulated motion vectors (vec2)
- `_motion_fbo: int` — Framebuffer for motion buffer
- `_parameters: dict` — Motion transfer parameters
- `_shader: ShaderProgram` — Compiled shader
- `_second_video_texture: int` — Texture for second video
- `_temp_textures: List[int]` — For ping-pong rendering if needed

**Per-Frame:**
- Update current depth from source
- Compute depth difference with previous depth
- Render motion field to motion buffer (with accumulation/decay)
- Render second video displaced by motion buffer
- Store current depth as previous for next frame
- Return result

**Initialization:**
- Create motion buffer texture (vec2, floating point)
- Create motion buffer FBO
- Create second video texture
- Compile shader
- Default parameters: motionScale=6.0, decayRate=5.0, motionBlur=4.0, forceDirection=0.0, colorSmear=3.0, threshold=2.0, accumulate=7.0, feedback=3.0
- Initialize `_prev_depth_frame` to None (first frame no motion)

**Cleanup:**
- Delete motion buffer texture
- Delete motion buffer FBO
- Delete second video texture
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Motion buffer texture | GL_TEXTURE_2D | GL_RG32F (vec2) | frame size | Updated each frame |
| Motion buffer FBO | GL_FRAMEBUFFER | N/A | frame size | Persistent |
| Second video texture | GL_TEXTURE_2D | GL_RGBA8 | second_video size | Updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Motion buffer: 640×480×2×4 = 2,457,600 bytes (RG32F)
- Second video texture: 921,600 bytes
- Shader: ~30-50 KB
- Total: ~3.4 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use zero motion | Normal operation |
| No second video provided | Use first video or raise error | Document requirement |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Motion buffer FBO incomplete | `RuntimeError("FBO error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and FBO operations must occur on the thread with the OpenGL context. The motion buffer is updated each frame in a read-modify-write sequence, and concurrent `process_frame()` calls will cause race conditions and corrupted accumulation. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Motion computation (depth diff + gradient): ~2-4 ms
- Motion buffer update (FBO render): ~1-2 ms
- Second video displacement render: ~2-4 ms
- Total: ~5.5-11 ms on GPU

**Optimization Strategies:**
- Reduce motion buffer resolution (half-res)
- Use simpler gradient computation (central differences)
- Disable expensive effects (motion blur, color smear)
- Combine motion computation and displacement in single pass
- Use compute shader for parallel motion accumulation

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Second video source configured
- [ ] Motion parameters configured (scale, decay, etc.)
- [ ] Optional effects configured (blur, smear, threshold)
- [ ] `process_frame()` called each frame with both videos
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_motion_computation` | Depth difference yields motion vectors |
| `test_motion_scale` | Motion magnitude controlled by scale |
| `test_decay_rate` | Motion buffer decays over time |
| `test_accumulation` | Motion accumulates across frames |
| `test_threshold` | Small depth changes ignored |
| `test_motion_blur` | Blur applied along motion direction |
| `test_color_smear` | Colors smear along motion |
| `test_force_direction` | Motion can be forced to specific direction |
| `test_reset_accumulation` | Motion buffer can be cleared |
| `test_process_frame_first` | First frame produces no motion |
| `test_process_frame_motion` | Subsequent frames produce displacement |
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
- [ ] Git commit with `[Phase-3] P3-VD59: depth_motion_transfer_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_motion_transfer.py` — VJLive Original implementation
- `plugins/core/depth_motion_transfer/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_motion_transfer/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthMotionTransferEffect` allocates `glGenTextures` and must free them
- `assets/gists/depth_motion_transfer.json` — Gist documentation

Design decisions inherited:
- Effect name: `depth_motion_transfer`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for motion extraction (frame-to-frame difference)
- Parameters: `motionScale`, `decayRate`, `motionBlur`, `forceDirection`, `colorSmear`, `threshold`, `accumulate`, `feedback`
- Allocates GL resources: motion buffer texture (vec2), motion buffer FBO, second video texture
- Shader implements motion computation, accumulation, and displacement
- Motion field accumulates with decay, creating trails

---

## Notes for Implementers

1. **Core Concept**: This effect extracts motion from depth changes between consecutive frames and uses that motion to displace a second video. It's essentially an optical flow algorithm simplified to depth differences.

2. **Motion Field Computation**:
   - Need to store previous depth frame
   - Compute difference: `depth_diff = current_depth - previous_depth`
   - Compute gradient of `depth_diff` to get motion vectors:
     ```glsl
     float diff = texture(depth_tex, uv).r - texture(prev_depth_tex, uv).r;
     vec2 motion = vec2(dFdx(diff), dFdy(diff));
     ```
   - The gradient points in direction of increasing depth difference, which corresponds to motion direction.

3. **Motion Accumulation**:
   - Maintain a motion buffer texture (stores vec2 motion vectors per pixel)
   - Each frame:
     ```glsl
     vec2 accumulated_motion = texture(motion_buffer_tex, uv).rg;
     accumulated_motion = accumulated_motion * decayRate + new_motion * (1.0 - decayRate);
     ```
   - Or using parameters: `accumulation = mix(new_motion, accumulated_motion, accumulate/10.0)`
   - Write back to motion buffer via FBO

4. **Displacement**:
   - Sample second video with UV offset by accumulated motion:
     ```glsl
     vec2 displaced_uv = uv + accumulated_motion * motionScale;
     vec4 displaced = texture(second_video_tex, displaced_uv);
     ```

5. **Motion Blur**:
   - Could be implemented as a multi-tap blur along motion direction:
     ```glsl
     if (motionBlur > 0.0) {
         vec3 blurred = vec3(0.0);
         float total = 0.0;
         for (int i = -2; i <= 2; i++) {
             float weight = exp(-i*i / (2.0 * motionBlur));
             blurred += texture(second_video_tex, uv + accumulated_motion * i).rgb * weight;
             total += weight;
         }
         color = blurred / total;
     }
     ```

6. **Color Smear**:
   - Smear colors along motion direction:
     ```glsl
     if (colorSmear > 0.0) {
         vec3 smeared = vec3(0.0);
         for (int i = 0; i <= 2; i++) {
             smeared += texture(second_video_tex, uv + accumulated_motion * i * colorSmear).rgb;
         }
         color = smeared / 3.0;
     }
     ```

7. **Threshold**:
   - Ignore small depth changes:
     ```glsl
     if (abs(depth_diff) < threshold * 0.01) {
         new_motion = vec2(0.0);
     }
     ```

8. **Force Direction**:
   - If `forceDirection > 0`, override motion direction with a fixed vector (e.g., radial from center, or along a specific axis). Could be used to create directional motion regardless of actual movement.

9. **Feedback**:
   - The `feedback` parameter might control how much the displaced result feeds back into the motion buffer or into the final output. Could be:
     ```glsl
     // After displacement
     if (feedback > 0.0) {
         displaced = mix(displaced, previous_output, feedback/10.0);
     }
     ```

10. **Shader Uniforms**:
    ```glsl
    uniform sampler2D tex0;           // Input frame (for depth)
    uniform sampler2D depth_tex;      // Depth texture (current)
    uniform sampler2D prev_depth_tex; // Previous depth texture
    uniform sampler2D second_tex;     // Second video
    uniform sampler2D motion_buffer_tex;  // Accumulated motion (read/write)
    uniform vec2 resolution;
    uniform float u_mix;
    uniform float time;
    
    uniform float motionScale;       // 0-10
    uniform float decayRate;         // 0-10 (mapped to 0-1)
    uniform float motionBlur;        // 0-10
    uniform float forceDirection;    // 0-10 (maybe angle or axis)
    uniform float colorSmear;        // 0-10
    uniform float threshold;         // 0-10 (mapped to depth diff)
    uniform float accumulate;        // 0-10 (mapped to mix ratio)
    uniform float feedback;          // 0-10 (mapped to mix ratio)
    ```

11. **Two-Pass Rendering**:
    - **Pass 1**: Compute new motion and update motion buffer
      - Render to motion buffer FBO
      - Read: previous motion buffer, current depth, previous depth
      - Write: new motion buffer
    - **Pass 2**: Displace second video using motion buffer
      - Render to screen or output FBO
      - Read: second video, motion buffer
      - Write: final color
    - Also need to copy motion buffer for next frame (ping-pong)

12. **Ping-Pong Motion Buffer**:
    ```python
    self.motion_tex = glGenTextures(2)
    self.motion_fbo = glGenFramebuffers(2)
    self.current_motion = 0
    
    def _update_motion_buffer(self):
        read_idx = self.current_motion
        write_idx = 1 - self.current_motion
        # Render to motion_fbo[write_idx] using motion_tex[read_idx] as input
        self.current_motion = write_idx
    ```

13. **Parameter Mapping**:
    - `motionScale`: 0-10 → multiplier (e.g., 0.1 per unit)
    - `decayRate`: 0-10 → 0.0-1.0 (divide by 10). 10 = 1.0 (no decay)
    - `motionBlur`: 0-10 → blur radius or tap count
    - `forceDirection`: 0-10 → maybe angle in radians (0-2π) or direction vector
    - `colorSmear`: 0-10 → smear distance multiplier
    - `threshold`: 0-10 → depth difference threshold (e.g., 0.001 * value)
    - `accumulate`: 0-10 → mix ratio (0=replace, 10=full accumulate) /10
    - `feedback`: 0-10 → feedback mix ratio /10

14. **PRESETS**:
    ```python
    PRESETS = {
        "clean": {
            "motionScale": 0.0, "decayRate": 10.0,  # No motion, instant decay
            "motionBlur": 0.0, "forceDirection": 0.0,
            "colorSmear": 0.0, "threshold": 0.0,
            "accumulate": 0.0, "feedback": 0.0,
        },
        "motion_transfer": {
            "motionScale": 6.0, "decayRate": 5.0,
            "motionBlur": 4.0, "forceDirection": 0.0,
            "colorSmear": 3.0, "threshold": 2.0,
            "accumulate": 7.0, "feedback": 3.0,
        },
        "long_trails": {
            "motionScale": 5.0, "decayRate": 2.0,  # Slow decay
            "motionBlur": 6.0, "forceDirection": 0.0,
            "colorSmear": 5.0, "threshold": 1.0,
            "accumulate": 9.0, "feedback": 5.0,
        },
        "sharp_motion": {
            "motionScale": 8.0, "decayRate": 8.0,  # Fast decay
            "motionBlur": 2.0, "forceDirection": 0.0,
            "colorSmear": 1.0, "threshold": 3.0,
            "accumulate": 5.0, "feedback": 2.0,
        },
        "directional_force": {
            "motionScale": 7.0, "decayRate": 6.0,
            "motionBlur": 3.0, "forceDirection": 5.0,  # e.g., 5/10*2π = π rad (leftward)
            "colorSmear": 4.0, "threshold": 2.0,
            "accumulate": 6.0, "feedback": 4.0,
        },
    }
    ```

15. **Testing Strategy**:
    - Simulate depth sequences with known motion (e.g., depth ramp moving left/right)
    - Verify motion vectors point in expected direction
    - Test accumulation: motion should persist and decay
    - Test threshold: small changes ignored
    - Test motion blur: smooths along motion direction
    - Test color smear: colors stretch along motion
    - Test force direction: overrides natural motion

16. **Performance**: The effect requires multiple render passes and texture uploads. Optimize by:
    - Using half-resolution motion buffer
    - Combining passes into single shader if possible (but need ping-pong for accumulation)
    - Using compute shader for motion update
    - Reducing blur/smear tap counts

17. **Future Extensions**:
    - Add audio reactivity to motion scale
    - Add multiple motion sources (blend depths from multiple cameras)
    - Add motion vector visualization (debug mode)
    - Add per-channel motion (separate RGB displacement)
    - Add motion-based color grading

---
-

## References

- Optical flow: https://en.wikipedia.org/wiki/Optical_flow
- Motion estimation: https://en.wikipedia.org/wiki/Motion_estimation
- Frame differencing: https://en.wikipedia.org/wiki/Frame_differencing
- Accumulation buffer: https://en.wikipedia.org/wiki/Accumulation_buffer
- Motion blur: https://en.wikipedia.org/wiki/Motion_blur
- VJLive legacy: `plugins/vdepth/depth_motion_transfer.py`

---

## Implementation Tips

1. **Full Shader (Two-Pass)**:

   **Pass 1: Motion Update** (render to motion buffer FBO):
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec2 fragColor;  // Motion vector (rg)
   
   uniform sampler2D motion_buffer_tex;  // Previous motion
   uniform sampler2D depth_tex;          // Current depth
   uniform sampler2D prev_depth_tex;     // Previous depth
   uniform vec2 resolution;
   uniform float time;
   
   uniform float motionScale;
   uniform float decayRate;      // 0-1
   uniform float threshold;      // 0-10 -> depth diff threshold
   uniform float accumulate;     // 0-1
   
   void main() {
       vec2 prev_motion = texture(motion_buffer_tex, uv).rg;
       
       float depth_curr = texture(depth_tex, uv).r;
       float depth_prev = texture(prev_depth_tex, uv).r;
       
       float diff = depth_curr - depth_prev;
       
       // Threshold
       if (abs(diff) < threshold * 0.001) {
           // No motion, just decay previous
           fragColor = prev_motion * decayRate;
           return;
       }
       
       // Compute motion from gradient of diff
       float dx = dFdx(diff);
       float dy = dFdy(diff);
       vec2 new_motion = vec2(dx, dy) * motionScale * 100.0;  // Scale up
       
       // Accumulate
       fragColor = mix(prev_motion * decayRate, new_motion, accumulate);
   }
   ```

   **Pass 2: Displacement** (render to screen):
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D second_tex;       // Second video
   uniform sampler2D motion_buffer_tex; // Accumulated motion
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float motionScale;
   uniform float motionBlur;
   uniform float colorSmear;
   uniform float feedback;
   
   void main() {
       vec2 motion = texture(motion_buffer_tex, uv).rg;
       
       // Apply motion scale (could be applied in pass1 instead)
       motion *= motionScale * 0.01;
       
       // Base displaced sample
       vec4 color = texture(second_tex, uv + motion);
       
       // Motion blur
       if (motionBlur > 0.0) {
           vec3 blurred = vec3(0.0);
           float total = 0.0;
           int taps = 2 + int(motionBlur * 3.0);  // 2-8 taps
           for (int i = -taps; i <= taps; i++) {
               float weight = exp(-float(i*i) / (2.0 * motionBlur * motionBlur + 1e-5));
               vec2 offset = motion * float(i) * 0.5;
               blurred += texture(second_tex, uv + offset).rgb * weight;
               total += weight;
           }
           color.rgb = blurred / total;
       }
       
       // Color smear
       if (colorSmear > 0.0) {
           vec3 smeared = vec3(0.0);
           int taps = 2;
           for (int i = 0; i <= taps; i++) {
               float t = float(i) / float(taps);
               smeared += texture(second_tex, uv + motion * t * colorSmear).rgb;
           }
           color.rgb = smeared / float(taps + 1);
       }
       
       // Feedback (if we had previous output, could blend)
       // Not implemented here; would need another texture
       
       // Mix with original (maybe original is first video?)
       // For now, output directly
       fragColor = color;
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthMotionTransferEffect(Effect):
       def __init__(self):
           super().__init__("depth_motion_transfer", MOTION_TRANSFER_VERTEX, MOTION_TRANSFER_FRAGMENT)
           
           self.depth_source = None
           self.depth_frame = None
           self.prev_depth_frame = None
           
           self.second_video_source = None
           self.second_video_frame = None
           
           self.motion_buffer_tex = [0, 0]  # ping-pong
           self.motion_fbo = [0, 0]
           self.current_motion = 0
           
           self.parameters = {
               'motionScale': 6.0,
               'decayRate': 5.0,
               'motionBlur': 4.0,
               'forceDirection': 0.0,
               'colorSmear': 3.0,
               'threshold': 2.0,
               'accumulate': 7.0,
               'feedback': 3.0,
           }
           
           self.shader = None
           
       def _ensure_motion_buffer(self, width, height):
           if self.motion_buffer_tex[0] == 0:
               for i in range(2):
                   self.motion_buffer_tex[i] = glGenTextures(1)
                   glBindTexture(GL_TEXTURE_2D, self.motion_buffer_tex[i])
                   glTexImage2D(GL_TEXTURE_2D, 0, GL_RG32F, width, height, 0, GL_RG, GL_FLOAT, None)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                   
                   self.motion_fbo[i] = glGenFramebuffers(1)
                   glBindFramebuffer(GL_FRAMEBUFFER, self.motion_fbo[i])
                   glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.motion_buffer_tex[i], 0)
                   glBindFramebuffer(GL_FRAMEBUFFER, 0)
                   
       def _ensure_second_video_texture(self):
           if self.second_video_texture == 0:
               self.second_video_texture = glGenTextures(1)
               # ... setup
   ```

3. **Process Frame**:
   ```python
   def process_frame(self, frame, second_video):
       h, w = frame.shape[:2]
       self._ensure_resources(w, h)
       
       # Update depth
       self._update_depth()  # Sets self.depth_frame
       
       # Upload current depth
       self._upload_depth_texture()
       
       # Upload second video
       second_tex = self._texture_from_array(second_video)
       
       # Pass 1: Update motion buffer
       glBindFramebuffer(GL_FRAMEBUFFER, self.motion_fbo[self.current_motion])
       
       self.shader_motion.use()
       self._apply_motion_uniforms(time)
       # Bind: motion_buffer_tex[prev], depth_tex, prev_depth_tex
       # Draw fullscreen quad
       
       glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       # Swap motion buffer
       self.current_motion = 1 - self.current_motion
       
       # Pass 2: Displace second video
       glBindFramebuffer(GL_FRAMEBUFFER, 0)  # or output FBO
       
       self.shader_display.use()
       self._apply_display_uniforms(time)
       # Bind: second_tex, motion_buffer_tex[current_motion]
       # Draw fullscreen quad
       
       # Read result
       result = self._read_pixels()
       
       # Store current depth as previous
       self.prev_depth_frame = self.depth_frame.copy()
       
       return result
   ```

4. **Depth Texture Management**: Need to keep previous depth texture on GPU. Could store as texture and just update each frame, or upload both current and previous from CPU. Simpler: keep `prev_depth_frame` as numpy, upload each frame.

5. **Motion Buffer Initialization**: First frame, `prev_depth_frame` is None → set to current depth, motion = 0.

6. **Parameter Smoothing**: Motion can be jittery. Consider smoothing the motion buffer or applying a low-pass filter.

7. **Testing**: Create synthetic depth sequences:
   - Depth ramp moving right: should produce rightward motion vectors
   - Circle expanding: should produce outward radial motion
   - Verify accumulation: motion persists after movement stops

8. **Performance**: Two-pass rendering doubles shader cost. Could combine into single pass if using compute shader or if we don't need separate motion buffer visualization. But accumulation requires separate pass.

9. **Debug Visualization**: Add debug mode to show motion buffer as color (motion.x, motion.y, 0, 1) or magnitude.

10. **Force Direction**: Could be implemented as:
    ```glsl
    if (forceDirection > 0.0) {
        float angle = forceDirection * 6.28318;  // 0-2π
        new_motion = vec2(cos(angle), sin(angle)) * length(new_motion);
    }
    ```
    Or force to a specific axis: `new_motion.x = forceDirection * 10.0;` etc. Need to clarify from legacy.

---

## Conclusion

The DepthMotionTransferEffect translates physical motion into visual displacement, creating organic, movement-driven distortion. By computing motion from depth differences and accumulating it with decay, it produces fluid trails and echoes of movement. This effect turns the performer's kinetic energy into a direct manipulation of secondary visuals, making it a powerful tool for interactive VJ performances where motion is the primary control.

---
