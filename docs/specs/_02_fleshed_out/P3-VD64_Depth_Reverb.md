# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD64_Depth_Reverb.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD64 — DepthReverbEffect

## Description

The DepthReverbEffect applies audio reverb concepts to video, using depth to control the "room size" and reverb characteristics. Near objects remain dry and present, while far objects receive echoed, diffused, and trailing reverb. The effect simulates acoustic reverb with early reflections, diffusion blur, damping, and color decay in the reverb tail. Depth modulates the wet/dry mix, creating a sense of spatial depth where distant objects appear to be in a larger, more reverberant space.

This effect is ideal for creating atmospheric, dreamy, or spatially ambiguous visuals. It's perfect for VJ performances that want to add a sense of depth and space to the video, making near objects feel intimate and far objects feel distant and echoey. The effect is particularly powerful when combined with audio reactivity, as the reverb can pulse with the music.

## What This Module Does

- Applies temporal reverb (feedback loop) to video
- Uses depth to modulate wet/dry mix (near=dry, far=wet)
- Configurable decay, damping, and diffusion
- Optional depth inversion (near=wet, far=dry)
- Early reflections and reverb tail processing
- GPU-accelerated with ping-pong framebuffer for feedback
- Color decay in reverb tail (simulates air absorption)

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT include audio reactivity (may be added later)
- Does NOT support 3D audio processing (2D video only)
- Does NOT implement ray-traced acoustics (simplified reverb model)
- Does NOT include convolution reverb (uses feedback delay network)

---

## Detailed Behavior

### Depth-Controlled Reverb Pipeline

1. **Capture current frame**: `current_frame`
2. **Capture depth frame**: `depth_frame` (normalized 0-1)
3. **Compute reverb input**: From previous reverb buffer (ping-pong)
4. **Apply reverb processing**:
   - Early reflections: short delays with scaling
   - Diffusion: blur to smear echoes
   - Damping: high-frequency roll-off in reverb tail
   - Color decay: desaturate/darken reverb tail
5. **Depth-modulated wet/dry mix**:
   - Near depth → dry (more current frame)
   - Far depth → wet (more reverb)
   - Option to invert
6. **Feedback**: Mix reverb output back into reverb buffer with decay
7. **Final output**: Blend with original via `u_mix`

### Reverb Architecture

The effect uses a simple feedback delay network:
- Maintain a "reverb buffer" texture that accumulates delayed frames
- Each frame: `reverb_buffer = reverb_buffer * decay + current_frame * (1 - decay)`
- Apply damping and diffusion to the reverb buffer before mixing
- The reverb buffer is stored in a ping-pong FBO (two textures)

### Depth Modulation

Depth controls the wet/dry ratio per pixel:
```glsl
float depth = texture(depth_tex, uv).r;
float wet_dry = depth * depth_influence;  // 0 (near) to 1 (far)
if (invert_depth > 0.0) {
    wet_dry = 1.0 - wet_dry;
}
vec4 reverbed = mix(current, reverb_signal, wet_dry);
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `decay` | float | 0.95 | 0.0-1.0 | Reverb feedback decay (per frame) |
| `depth_influence` | float | 1.0 | 0.0-1.0 | How much depth modulates wet/dry (1=full) |
| `invert_depth` | float | 0.0 | 0.0-1.0 | Invert depth modulation (0=far=wet, 1=near=wet) |
| `damping` | float | 0.9 | 0.0-1.0 | High-frequency roll-off in reverb tail |
| `diffusion` | float | 0.5 | 0.0-1.0 | Blur amount for reverb smearing |
| `early_reflections` | float | 0.3 | 0.0-1.0 | Strength of early reflections |
| `color_decay` | float | 0.8 | 0.0-1.0 | Color saturation decay in reverb tail |
| `wet_dry` | float | 0.5 | 0.0-1.0 | Overall wet/dry mix (0=dry, 1=wet) |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class DepthReverbEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def reset_reverb(self) -> None: ...  # Clear reverb buffer
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Reverb-processed frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_reverb_textures: List[int]` — Ping-pong reverb buffer textures (2)
- `_reverb_fbos: List[int]` — Framebuffers for reverb buffers
- `_current_reverb: int` — Index of current reverb buffer (0 or 1)
- `_parameters: dict` — Reverb parameters
- `_shader: ShaderProgram` — Compiled shader
- `_temp_texture: int` — For intermediate rendering if needed

**Per-Frame:**
- Update depth data from source
- Upload current frame to texture
- Render reverb update pass (feedback + processing)
- Render final composite pass (depth-modulated mix)
- Swap reverb buffer index
- Return result

**Initialization:**
- Create reverb buffer textures (2, for ping-pong)
- Create reverb buffer FBOs (2)
- Create temporary textures if needed
- Compile shader
- Default parameters: decay=0.95, depth_influence=1.0, invert_depth=0.0, damping=0.9, diffusion=0.5, early_reflections=0.3, color_decay=0.8, wet_dry=0.5
- Initialize `_current_reverb = 0`

**Cleanup:**
- Delete reverb buffer textures (2)
- Delete reverb buffer FBOs (2)
- Delete temporary textures
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Reverb buffer textures (2) | GL_TEXTURE_2D | GL_RGBA16F or GL_RGBA8 | frame size | Updated each frame (ping-pong) |
| Reverb buffer FBOs (2) | GL_FRAMEBUFFER | N/A | frame size | Persistent |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Reverb buffers: 2 × 1,228,800 bytes (RGBA16F) = 2,457,600 bytes
- Shader: ~20-30 KB
- Total: ~2.5 MB

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

The effect is **not thread-safe**. All GPU operations, texture updates, and FBO operations must occur on the thread with the OpenGL context. The effect uses ping-pong buffers and updates them each frame; concurrent `process_frame()` calls will cause race conditions and corrupted reverb. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Texture uploads: ~0.5-1 ms
- Reverb update (feedback + processing): ~3-6 ms
- Final composite: ~1-2 ms
- Total: ~4.5-9 ms on GPU

**Optimization Strategies:**
- Use lower precision texture (RGBA8 instead of RGBA16F)
- Disable expensive processing (diffusion, color decay)
- Reduce reverb buffer resolution (half-res)
- Combine passes into single shader if possible
- Use compute shader for reverb update

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Reverb parameters configured
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_reverb_feedback` | Reverb buffer accumulates with decay |
| `test_depth_modulation` | Depth controls wet/dry mix |
| `test_invert_depth` | Inverts depth modulation |
| `test_damping` | High frequencies attenuated in reverb |
| `test_diffusion` | Reverb is blurred/smeared |
| `test_early_reflections` | Early echoes added to reverb |
| `test_color_decay` | Reverb tail desaturates/darkens |
| `test_wet_dry` | Overall wet/dry mix works |
| `test_reset_reverb` | Reverb buffer can be cleared |
| `test_process_frame_first` | First frame initializes reverb |
| `test_process_frame_accumulation` | Reverb builds over time |
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
- [ ] Git commit with `[Phase-3] P3-VD64: depth_reverb_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/depth_reverb.py` — VJLive Original implementation
- `plugins/vdepth/depth_reverb.py` — VJLive-2 implementation
- `tests/test_depth_reverb.py` — Unit tests
- `gl_leaks.txt` — Shows `DepthReverbEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_reverb`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for wet/dry modulation
- Parameters: `decay`, `depth_influence`, `invert_depth`, `damping`, `diffusion`, `early_reflections`, `color_decay`, `wet_dry`
- Allocates GL resources: reverb buffer textures (2, ping-pong), reverb buffer FBOs (2)
- Shader implements reverb feedback, damping, diffusion, and depth-modulated mix
- Method `_ensure_gpu_resources()` creates GPU resources
- State includes `last_frame_tex` for previous frame

---

## Notes for Implementers

1. **Core Concept**: This effect simulates acoustic reverb on video, where depth controls the amount of reverb (wet vs dry). It's essentially a feedback loop with depth-modulated mixing.

2. **Reverb Buffer**: The effect maintains a persistent "reverb buffer" that stores the accumulated reverb tail. Each frame:
   - The buffer is scaled by `decay` (e.g., 0.95) to gradually fade old content
   - The current frame is added to the buffer (scaled by `1 - decay`)
   - The buffer is processed (damping, diffusion) and mixed with current frame based on depth

3. **Ping-Pong Buffers**: Use two textures/FBOs and swap each frame:
   ```python
   self.reverb_tex = [0, 0]
   self.reverb_fbo = [0, 0]
   self.current = 0
   
   # Each frame:
   read_idx = self.current
   write_idx = 1 - self.current
   # Render to reverb_fbo[write_idx] using reverb_tex[read_idx] as input
   self.current = write_idx
   ```

4. **Shader Structure**:
   - **Pass 1: Reverb Update** (render to reverb buffer FBO):
     ```glsl
     uniform sampler2D current_tex;
     uniform sampler2D prev_reverb_tex;
     uniform float decay;
     uniform float damping;
     uniform float diffusion;
     uniform float early_reflections;
     uniform float color_decay;
     
     void main() {
         vec4 prev = texture(prev_reverb_tex, uv);
         vec4 current = texture(current_tex, uv);
         
         // Feedback
         vec4 reverb = prev * decay + current * (1.0 - decay);
         
         // Damping: reduce high frequencies (simple: blur or multiply)
         // Could use a separable blur or just reduce saturation
         reverb.rgb *= damping;  // Simple damping
         
         // Color decay: desaturate reverb tail
         float gray = dot(reverb.rgb, vec3(0.299, 0.587, 0.114));
         reverb.rgb = mix(reverb.rgb, vec3(gray), 1.0 - color_decay);
         
         // Early reflections: add scaled copy with offset
         if (early_reflections > 0.0) {
             vec2 offset = vec2(0.01, 0.01) * early_reflections;
             vec4 early = texture(prev_reverb_tex, uv + offset);
             reverb += early * 0.5 * early_reflections;
         }
         
         fragColor = reverb;
     }
     ```
   - **Pass 2: Final Composite** (render to screen):
     ```glsl
     uniform sampler2D current_tex;
     uniform sampler2D reverb_tex;
     uniform sampler2D depth_tex;
     uniform float depth_influence;
     uniform float invert_depth;
     uniform float wet_dry;
     uniform float u_mix;
     
     void main() {
         vec4 current = texture(current_tex, uv);
         vec4 reverb = texture(reverb_tex, uv);
         float depth = texture(depth_tex, uv).r;
         
         // Depth-modulated wet/dry
         float wet = depth * depth_influence;
         if (invert_depth > 0.0) {
             wet = 1.0 - wet;
         }
         wet = mix(wet_dry, wet, depth_influence);  // Combine with overall wet_dry
         
         vec4 reverbed = mix(current, reverb, wet);
         
         // Final mix with original (u_mix)
         fragColor = mix(current, reverbed, u_mix);
     }
     ```

5. **Parameter Ranges**:
   - `decay`: 0.0-1.0 (0=instant decay, 1=infinite reverb)
   - `depth_influence`: 0.0-1.0 (0=depth doesn't affect, 1=depth fully controls)
   - `invert_depth`: 0.0-1.0 (0=far=wet, 1=near=wet)
   - `damping`: 0.0-1.0 (0=no damping, 1=full damping)
   - `diffusion`: 0.0-1.0 (0=no diffusion, 1=heavy blur)
   - `early_reflections`: 0.0-1.0 (0=none, 1=strong)
   - `color_decay`: 0.0-1.0 (0=no decay, 1=full grayscale)
   - `wet_dry`: 0.0-1.0 (0=dry only, 1=wet only)
   - Note: The legacy uses 0-10 range for some; map appropriately

6. **Diffusion Implementation**: Could be a simple blur:
   ```glsl
   if (diffusion > 0.0) {
       vec3 blurred = vec3(0.0);
       float total = 0.0;
       for (int i = -2; i <= 2; i++) {
           for (int j = -2; j <= 2; j++) {
               vec2 offset = vec2(i, j) * diffusion * 0.001;
               blurred += texture(reverb_tex, uv + offset).rgb;
               total += 1.0;
           }
       }
       reverb.rgb = blurred / total;
   }
   ```

7. **Damping Implementation**: Simple multiplicative damping reduces overall brightness. More advanced: low-pass filter or frequency-dependent damping.

8. **Early Reflections**: Add scaled copies of the reverb buffer with small offsets to simulate early echoes.

9. **Color Decay**: Desaturate the reverb tail to simulate high-frequency absorption in air:
   ```glsl
   float gray = dot(reverb.rgb, vec3(0.299, 0.587, 0.114));
   reverb.rgb = mix(reverb.rgb, vec3(gray), 1.0 - color_decay);
   ```

10. **PRESETS**:
    ```python
    PRESETS = {
        "clean": {
            "decay": 0.0, "depth_influence": 0.0, "invert_depth": 0.0,
            "damping": 0.0, "diffusion": 0.0, "early_reflections": 0.0,
            "color_decay": 1.0, "wet_dry": 0.0,
        },
        "subtle_depth": {
            "decay": 0.9, "depth_influence": 1.0, "invert_depth": 0.0,
            "damping": 0.8, "diffusion": 0.3, "early_reflections": 0.2,
            "color_decay": 0.9, "wet_dry": 0.3,
        },
        "atmospheric": {
            "decay": 0.95, "depth_influence": 1.0, "invert_depth": 0.0,
            "damping": 0.7, "diffusion": 0.6, "early_reflections": 0.4,
            "color_decay": 0.7, "wet_dry": 0.6,
        },
        "inverted": {
            "decay": 0.92, "depth_influence": 1.0, "invert_depth": 1.0,
            "damping": 0.75, "diffusion": 0.4, "early_reflections": 0.3,
            "color_decay": 0.8, "wet_dry": 0.5,
        },
        "dense_reverb": {
            "decay": 0.98, "depth_influence": 0.8, "invert_depth": 0.0,
            "damping": 0.6, "diffusion": 0.8, "early_reflections": 0.5,
            "color_decay": 0.6, "wet_dry": 0.8,
        },
    }
    ```

11. **Testing Strategy**:
    - Test reverb accumulation: feed a constant signal, verify reverb builds
    - Test decay: after signal stops, reverb should fade
    - Test depth modulation: depth map should control wet/dry per pixel
    - Test invert: near should be wet when inverted
    - Test damping: reverb should be darker/less saturated
    - Test color decay: reverb should desaturate
    - Test early reflections: should see faint echoes

12. **Performance**: The effect uses two render passes and texture uploads. Optimize by:
    - Using lower precision (RGBA8) if quality acceptable
    - Reducing diffusion blur radius
    - Combining passes if possible
    - Using compute shader for reverb update

13. **Future Extensions**:
    - Add audio reactivity to decay/damping
    - Add multiple reverb times (different decay rates per channel)
    - Add modulation (chorus, flanger) on reverb tail
    - Add BPM sync for rhythmic reverb gating

---
-

## References

- Reverb: https://en.wikipedia.org/wiki/Reverb
- Feedback delay network: https://en.wikipedia.org/wiki/Feedback_delay_network
- Digital signal processing: https://en.wikipedia.org/wiki/Digital_signal_processing
- Ping-pong buffer: https://en.wikipedia.org/wiki/Ping-pong_buffer
- VJLive legacy: `core/effects/depth_reverb.py`, `plugins/vdepth/depth_reverb.py`

---

## Implementation Tips

1. **Full Shader (Two-Pass)**:

   **Pass 1: Reverb Update** (render to reverb FBO):
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D current_tex;
   uniform sampler2D prev_reverb_tex;
   uniform float decay;
   uniform float damping;
   uniform float diffusion;
   uniform float early_reflections;
   uniform float color_decay;
   uniform float time;
   
   void main() {
       vec4 current = texture(current_tex, uv);
       vec4 prev = texture(prev_reverb_tex, uv);
       
       // Feedback
       vec4 reverb = prev * decay + current * (1.0 - decay);
       
       // Damping (simple multiplicative)
       reverb.rgb *= damping;
       
       // Color decay: desaturate
       float gray = dot(reverb.rgb, vec3(0.299, 0.587, 0.114));
       reverb.rgb = mix(reverb.rgb, vec3(gray), 1.0 - color_decay);
       
       // Early reflections (simple offset copy)
       if (early_reflections > 0.0) {
           vec2 offset = vec2(0.005, 0.005) * early_reflections;
           vec4 early = texture(prev_reverb_tex, uv + offset);
           reverb += early * 0.3 * early_reflections;
       }
       
       // Diffusion (simple blur)
       if (diffusion > 0.0) {
           vec3 blurred = vec3(0.0);
           float total = 0.0;
           for (int i = -1; i <= 1; i++) {
               for (int j = -1; j <= 1; j++) {
                   vec2 offset = vec2(i, j) * diffusion * 0.002;
                   blurred += texture(prev_reverb_tex, uv + offset).rgb;
                   total += 1.0;
               }
           }
           reverb.rgb = mix(reverb.rgb, blurred / total, diffusion * 0.5);
       }
       
       fragColor = reverb;
   }
   ```

   **Pass 2: Composite** (render to screen):
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D current_tex;
   uniform sampler2D reverb_tex;
   uniform sampler2D depth_tex;
   uniform float depth_influence;
   uniform float invert_depth;
   uniform float wet_dry;
   uniform float u_mix;
   uniform float time;
   
   void main() {
       vec4 current = texture(current_tex, uv);
       vec4 reverb = texture(reverb_tex, uv);
       float depth = texture(depth_tex, uv).r;
       
       // Depth-modulated wet/dry
       float wet = depth * depth_influence;
       if (invert_depth > 0.0) {
           wet = 1.0 - wet;
       }
       // Combine with overall wet_dry control
       wet = mix(wet_dry, wet, depth_influence);
       
       vec4 reverbed = mix(current, reverb, wet);
       
       // Final mix
       fragColor = mix(current, reverbed, u_mix);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthReverbEffect(Effect):
       def __init__(self):
           super().__init__("depth_reverb", REVERB_VERTEX, REVERB_FRAGMENT)
           
           self.depth_source = None
           self.depth_frame = None
           
           self.reverb_tex = [0, 0]
           self.reverb_fbo = [0, 0]
           self.current_reverb = 0
           
           self.parameters = {
               'decay': 0.95,
               'depth_influence': 1.0,
               'invert_depth': 0.0,
               'damping': 0.9,
               'diffusion': 0.5,
               'early_reflections': 0.3,
               'color_decay': 0.8,
               'wet_dry': 0.5,
           }
           
           self.shader = None
       
       def _ensure_reverb_buffers(self, width, height):
           if self.reverb_tex[0] == 0:
               for i in range(2):
                   self.reverb_tex[i] = glGenTextures(1)
                   glBindTexture(GL_TEXTURE_2D, self.reverb_tex[i])
                   glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F, width, height, 0, GL_RGBA, GL_FLOAT, None)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                   
                   self.reverb_fbo[i] = glGenFramebuffers(1)
                   glBindFramebuffer(GL_FRAMEBUFFER, self.reverb_fbo[i])
                   glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.reverb_tex[i], 0)
                   glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       def _ensure_current_texture(self):
           if self.current_tex == 0:
               self.current_tex = glGenTextures(1)
               # ... setup
   ```

3. **Process Frame**:
   ```python
   def process_frame(self, frame):
       h, w = frame.shape[:2]
       self._ensure_reverb_buffers(w, h)
       self._ensure_current_texture()
       
       # Upload current frame
       glBindTexture(GL_TEXTURE_2D, self.current_tex)
       glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, frame)
       
       # Update depth
       self._update_depth()
       
       # Pass 1: Update reverb buffer
       read_idx = self.current_reverb
       write_idx = 1 - self.current_reverb
       
       glBindFramebuffer(GL_FRAMEBUFFER, self.reverb_fbo[write_idx])
       
       self.shader_reverb.use()
       self._apply_reverb_uniforms(time)
       glUniform1i(glGetUniformLocation(self.shader_reverb.program, "current_tex"), 0)
       glUniform1i(glGetUniformLocation(self.shader_reverb.program, "prev_reverb_tex"), 1)
       
       glActiveTexture(GL_TEXTURE0)
       glBindTexture(GL_TEXTURE_2D, self.current_tex)
       glActiveTexture(GL_TEXTURE1)
       glBindTexture(GL_TEXTURE_2D, self.reverb_tex[read_idx])
       
       draw_fullscreen_quad()
       
       glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       # Swap
       self.current_reverb = write_idx
       
       # Pass 2: Final composite
       glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       self.shader_composite.use()
       self._apply_composite_uniforms(time)
       glUniform1i(glGetUniformLocation(self.shader_composite.program, "current_tex"), 0)
       glUniform1i(glGetUniformLocation(self.shader_composite.program, "reverb_tex"), 1)
       glUniform1i(glGetUniformLocation(self.shader_composite.program, "depth_tex"), 2)
       
       glActiveTexture(GL_TEXTURE0)
       glBindTexture(GL_TEXTURE_2D, self.current_tex)
       glActiveTexture(GL_TEXTURE1)
       glBindTexture(GL_TEXTURE_2D, self.reverb_tex[self.current_reverb])
       glActiveTexture(GL_TEXTURE2)
       glBindTexture(GL_TEXTURE_2D, self.depth_texture)
       
       draw_fullscreen_quad()
       
       result = self._read_pixels()
       return result
   ```

4. **Depth Texture**: Upload depth each frame:
   ```python
   def _update_depth(self):
       if self.depth_source:
           try:
               self.depth_frame = self.depth_source.get_filtered_depth_frame()
           except Exception:
               self.depth_frame = None
       
       if self.depth_frame is not None:
           glBindTexture(GL_TEXTURE_2D, self.depth_texture)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, w, h, 0, GL_RED, GL_UNSIGNED_BYTE, self.depth_frame)
   ```

5. **Parameter Smoothing**: Reverb can be jittery. Consider smoothing parameters over time, especially if they're audio-reactive.

6. **Testing**: Create a test pattern (e.g., white square on black). Feed frames and verify:
   - Reverb buffer accumulates the square with decay
   - Depth map controls wet/dry: near region shows sharp square, far region shows blurred echo
   - Inverting swaps the effect

7. **Performance**: Two passes and multiple texture uploads. Optimize by:
   - Using RGBA8 instead of RGBA16F if precision not critical
   - Reducing diffusion blur kernel size
   - Combining passes into one if possible (but need ping-pong)
   - Using compute shader for reverb update

8. **Debug Mode**: Visualize reverb buffer, depth modulation, or wet/dry mask.

---

## Conclusion

The DepthReverbEffect creates a spatial, depth-aware reverb that makes near objects feel intimate and far objects feel distant and echoey. By using a feedback loop with depth-modulated mixing, it simulates the acoustic property that sound (and now video) in the distance has more reverb than up close. This effect adds atmospheric depth and spatial ambiguity to video, making it a powerful tool for creating dreamy, ethereal, or spatially complex visuals in VJ performances.

---
