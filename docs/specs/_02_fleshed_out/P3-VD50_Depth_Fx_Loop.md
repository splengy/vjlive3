# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD50_Depth_Fx_Loop.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD50 — DepthFXLoopEffect

## Description

The DepthFXLoopEffect creates effects send/return routing with feedback, analogous to a modular synthesizer's effects bus. It enables explicit routing loops in the node graph where an FX Send outputs to external effects, and an FX Return inputs the processed signal back. The effect supports depth-gated mixing, 4 blend modes, temporal feedback with decay, and hue drift. This modular approach allows for complex effect chains and feedback loops that are controlled by depth.

This effect is ideal for creating sophisticated effect routing where depth determines which parts of the image go through the effects chain. It's perfect for VJ performances that need flexible signal routing, feedback loops, and modular effect design. The effect acts as a gateway between the main signal and external processing, with depth-based gating and blending.

## What This Module Does

- Implements FX Send/Return architecture for modular routing
- Routes signal to external effects via Send output
- Receives processed signal from external effects via Return input
- Depth-gated mixing: only certain depth ranges participate in the loop
- Supports 4 blend modes: add, multiply, screen, overlay
- Temporal feedback with configurable decay
- Hue drift: gradually shifts colors over time in the feedback loop
- GPU-accelerated with fragment shader

## What This Module Does NOT Do

- Does NOT include built-in effects (only routing)
- Does NOT manage external effect instances (user must connect)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT handle loopback protection (user must avoid infinite loops)
- Does NOT implement audio reactivity (may be added later)

---

## Detailed Behavior

### FX Loop Architecture

```
[Input] → [Mix: Original vs Return] → [Send] → [External Effects] → [Return] → [Feedback] → [Next Frame]
      ↑                                                                      │
      └──────────────────────────────────────────────────────────────────────┘
```

1. **Mix Input**: Blend between original signal and Return signal:
   ```
   mixed = blend(original, return_signal, blend_mode, mix_amount)
   ```

2. **Send**: Output the mixed signal to external effects:
   ```
   send_output = mixed * depth_gate
   ```

3. **Return**: Receive processed signal from external effects:
   ```
   return_input = external_processed_signal
   ```

4. **Feedback**: Blend current return with previous frame's send:
   ```
   feedback_signal = mix(return_input, previous_send, feedback_amount)
   ```

5. **Hue Drift**: Gradually shift colors in the feedback loop:
   ```
   feedback_signal = hue_shift(feedback_signal, hue_drift_rate)
   ```

6. **Depth Gate**: Only process pixels within specified depth range:
   ```
   depth_value = texture(depth_tex, uv).r
   in_gate = (depth_value >= depth_min) && (depth_value <= depth_max)
   ```

### Blend Modes

The effect supports 4 blend modes for mixing original and return signals:

| Mode | Formula | Description |
|------|---------|-------------|
| Add | `a + b` | Additive blending (brightens) |
| Multiply | `a * b` | Multiplicative blending (darks) |
| Screen | `1 - (1-a)*(1-b)` | Screen blending (lightens) |
| Overlay | `a<0.5 ? 2*a*b : 1-2*(1-a)*(1-b)` | Overlay blending (contrast boost) |

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `mixAmount` | float | 1.0 | 0.0-10.0 | Blend between original and return (0=all original, 10=all return) |
| `blendMode` | int | 0 | 0-3 | 0=add, 1=multiply, 2=screen, 3=overlay |
| `depthMin` | float | 0.0 | 0.0-10.0 | Minimum depth for gating (normalized) |
| `depthMax` | float | 10.0 | 0.0-10.0 | Maximum depth for gating |
| `feedbackAmount` | float | 0.5 | 0.0-10.0 | Amount of feedback (0=none, 10=full) |
| `feedbackDecay` | float | 0.9 | 0.0-10.0 | Decay rate per frame (maps to 0-1) |
| `hueDrift` | float | 0.0 | 0.0-10.0 | Rate of hue shift per frame (degrees/second) |
| `sendSaturation` | float | 1.0 | 0.0-10.0 | Saturation boost on send (maps to 0-2) |
| `returnSaturation` | float | 1.0 | 0.0-10.0 | Saturation boost on return |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthFXLoopEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray, return_frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| `return_frame` | `np.ndarray` | Return signal from external effects (HxWxC, RGB) |
| **Output** | `np.ndarray` | Send signal to external effects (HxWxC, RGB) |

**Note**: The effect has two video inputs: the main signal and the return from external processing. The output is the send signal to external effects.

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_parameters: dict` — Loop parameters
- `_shader: ShaderProgram` — Compiled shader
- `_previous_send_texture: int` — Texture storing previous send frame for feedback
- `_feedback_framebuffer: int` — FBO for feedback

**Per-Frame:**
- Update depth data from source
- Upload depth texture
- Bind previous send texture for feedback sampling
- Render send output with shader
- Store current send in previous send texture (for next frame)
- Return processed signal via separate input (not in this effect's processing)

**Initialization:**
- Create depth texture (lazy)
- Create previous send texture (ping-pong)
- Create framebuffer for feedback
- Compile shader
- Default parameters: mixAmount=1.0, blendMode=0, depthMin=0.0, depthMax=10.0, feedbackAmount=0.5, feedbackDecay=0.9, hueDrift=0.0, sendSaturation=1.0, returnSaturation=1.0

**Cleanup:**
- Delete depth texture
- Delete previous send texture
- Delete framebuffer
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Previous send texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame (ping-pong) |
| Feedback framebuffer | GL_FRAMEBUFFER | N/A | frame size | Persistent |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Depth texture: 307,200 bytes
- Previous send texture: 640×480×3 = 921,600 bytes
- Framebuffer: negligible
- Shader: ~10-50 KB
- Total: ~1.2 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Use full-frame depth gate (all pixels pass) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Previous send texture missing | Initialize with current frame | Normal first frame |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Return frame missing | Use original signal as return | Normal operation |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and texture updates must occur on the thread with the OpenGL context. The depth texture and previous send texture are updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Shader execution (blend, feedback, hue drift): ~2-4 ms
- Texture copy for feedback: ~0.5-1 ms
- Total: ~3-6 ms on GPU

**Optimization Strategies:**
- Reduce shader complexity (simpler blend modes)
- Use lower resolution for feedback texture
- Implement feedback in compute shader
- Use texture arrays for ping-pong
- Cache depth texture if depth hasn't changed

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Loop parameters configured (mix, blend mode, depth gate, feedback, hue drift)
- [ ] External effects connected to Send and Return
- [ ] `process_frame()` called each frame with return_frame from external effects
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | Parameters can be set and clamped |
| `test_get_parameter` | Parameters can be retrieved |
| `test_blend_modes` | Each blend mode produces correct mixing |
| `test_depth_gate` | Only pixels within depth range are processed |
| `test_feedback` | Feedback creates recursive loops |
| `test_feedback_decay` | Decay controls persistence of feedback |
| `test_hue_drift` | Colors gradually shift over time |
| `test_saturation_boost` | Send/return saturation adjustments work |
| `test_process_frame` | Send output and feedback update correctly |
| `test_no_return_frame` | Falls back to original when return missing |
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
- [ ] Git commit with `[Phase-3] P3-VD50: depth_fx_loop_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_fx_loop.py` — VJLive Original implementation
- `plugins/core/depth_fx_loop/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_fx_loop/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthFXLoopEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_fx_loop`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for depth gating
- Parameters: `mixAmount`, `blendMode`, `depthMin`, `depthMax`, `feedbackAmount`, `feedbackDecay`, `hueDrift`, `sendSaturation`, `returnSaturation`
- Allocates GL resources: depth texture, previous send texture, framebuffer
- Shader implements blend modes, feedback, hue drift, saturation adjustment
- FX Send/Return architecture for modular routing

---

## Notes for Implementers

1. **FX Send/Return Pattern**: This effect is designed to be used in pairs or chains:
   - One instance as **Send** (outputs to external effects)
   - Another instance as **Return** (inputs from external effects)
   - Or a single instance that both sends and receives (loop within)

2. **Depth Gating**: The depth gate determines which pixels participate in the feedback loop:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float in_gate = step(depthMin, depth) * step(depth, depthMax);
   ```

3. **Blend Modes**: Implement 4 blend modes in shader:
   ```glsl
   vec3 blend_add(vec3 a, vec3 b) { return a + b; }
   vec3 blend_multiply(vec3 a, vec3 b) { return a * b; }
   vec3 blend_screen(vec3 a, vec3 b) { return 1.0 - (1.0-a)*(1.0-b); }
   vec3 blend_overlay(vec3 a, vec3 b) {
       return a < 0.5 ? 2.0*a*b : 1.0 - 2.0*(1.0-a)*(1.0-b);
   }
   ```

4. **Feedback Loop**: Store previous send frame and blend with current return:
   ```glsl
   vec4 previous_send = texture(prev_send_tex, uv);
   vec4 feedback = mix(return_frame, previous_send, feedbackAmount * feedbackDecay);
   ```

5. **Hue Drift**: Convert to HSV, shift hue, convert back:
   ```glsl
   vec3 hsv = rgb2hsv(feedback.rgb);
   hsv.x += hueDrift * delta_time;  // hue in [0,1]
   feedback.rgb = hsv2rgb(hsv);
   ```

6. **Saturation Adjustment**: Pre-send and post-return saturation boosts:
   ```glsl
   // On send
   vec3 hsv = rgb2hsv(send_output);
   hsv.y *= sendSaturation * 2.0;  // Scale 0-10 to 0-2
   send_output = hsv2rgb(hsv);
   
   // On return (if this effect also processes return)
   vec3 hsv2 = rgb2hsv(return_input);
   hsv2.y *= returnSaturation * 2.0;
   return_input = hsv2rgb(hsv2);
   ```

7. **Shader Uniforms**:
   ```glsl
   uniform sampler2D tex0;          // Original frame
   uniform sampler2D depth_tex;     // Depth texture
   uniform sampler2D texReturn;     // Return signal from external effects
   uniform sampler2D texPrev;       // Previous send frame
   uniform vec2 resolution;
   uniform float u_mix;
   
   uniform float mixAmount;
   uniform int blendMode;
   uniform float depthMin, depthMax;
   uniform float feedbackAmount;
   uniform float feedbackDecay;
   uniform float hueDrift;
   uniform float sendSaturation;
   uniform float returnSaturation;
   uniform float time;
   uniform float delta_time;
   ```

8. **Ping-Pong Textures**: Use two textures for previous send, swapping each frame:
   ```python
   # Two textures: send_tex_A and send_tex_B
   # Frame N: read from A, render to B
   # Frame N+1: read from B, render to A
   ```

9. **Framebuffer**: Use FBO to render send output to texture:
   ```python
   glBindFramebuffer(GL_FRAMEBUFFER, feedback_fbo)
   glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, current_send_tex, 0)
   # Render shader
   glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Back to screen
   ```

10. **Process Flow**:
    - `process_frame(frame, return_frame)`:
      1. Upload depth texture
      2. Set shader uniforms (including return_frame texture)
      3. Render to feedback framebuffer (output = send signal)
      4. Store rendered send in current send texture
      5. Return send signal as output (for external effects)
    - Next frame: previous send texture contains last frame's send

11. **External Effects Connection**: The effect doesn't manage external effects. The user must:
    - Connect Send output to external effect input
    - Connect external effect output to Return input
    - Ensure proper ordering in the node graph

12. **Parameter Ranges**: All parameters use 0-10 range from UI:
    - `mixAmount`: 0-10 (maps to 0-1 blend factor: `/10.0`)
    - `blendMode`: 0-3 (integer)
    - `depthMin`, `depthMax`: 0-10 (normalized depth)
    - `feedbackAmount`: 0-10 (maps to 0-1: `/10.0`)
    - `feedbackDecay`: 0-10 (maps to 0-1: `/10.0`, where 1.0 = no decay)
    - `hueDrift`: 0-10 (degrees per second, convert to [0,1] per second: `/360.0`)
    - `sendSaturation`, `returnSaturation`: 0-10 (maps to 0-2: `*0.2`)

13. **HSV Conversion**: Need RGB↔HSV conversion functions in shader:
    ```glsl
    vec3 rgb2hsv(vec3 c) {
        vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
        vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
        vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
        float d = q.x - min(q.w, q.y);
        float e = 1.0e-10;
        return vec3(abs(q.z + (q.w - q.y)/(6.0*d + e)), d/(q.x + e), q.x);
    }
    vec3 hsv2rgb(vec3 c) {
        vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
        vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
        return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
    }
    ```

14. **Performance**: The effect is moderate cost. Main operations: depth texture upload, shader execution, texture copy for feedback. All on GPU.

15. **Testing**: Create a simple loop: Send → Blur → Return. Verify:
    - Signal routes correctly through external effect
    - Depth gate filters which pixels participate
    - Feedback creates recursive blurring
    - Hue drift shifts colors over time
    - Blend modes produce different mixing

16. **Future Extensions**:
    - Add multiple feedback taps
    - Add depth-based feedback amount
    - Add audio reactivity to feedback
    - Add preset system for common configurations
    - Add loop time limit to prevent infinite recursion

---
-

## References

- Effects send/return: https://en.wikipedia.org/wiki/Send_(audio)
- Feedback: https://en.wikipedia.org/wiki/Feedback
- Blend modes: https://en.wikipedia.org/wiki/Blend_modes
- HSV color space: https://en.wikipedia.org/wiki/HSL_and_HSV
- VJLive legacy: `plugins/vdepth/depth_fx_loop.py`

---

## Implementation Tips

1. **Shader Code**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;          // Original frame
   uniform sampler2D depth_tex;     // Depth texture
   uniform sampler2D texReturn;     // Return signal
   uniform sampler2D texPrev;       // Previous send frame
   uniform vec2 resolution;
   uniform float u_mix;
   
   uniform float mixAmount;         // 0-10 -> 0-1
   uniform int blendMode;           // 0=add,1=mult,2=screen,3=overlay
   uniform float depthMin, depthMax;
   uniform float feedbackAmount;    // 0-10 -> 0-1
   uniform float feedbackDecay;     // 0-10 -> 0-1 (1=no decay)
   uniform float hueDrift;          // degrees/sec
   uniform float sendSaturation;    // 0-10 -> 0-2
   uniform float returnSaturation;  // 0-10 -> 0-2
   uniform float time;
   uniform float delta_time;
   
   vec3 blend_add(vec3 a, vec3 b) { return a + b; }
   vec3 blend_multiply(vec3 a, vec3 b) { return a * b; }
   vec3 blend_screen(vec3 a, vec3 b) { return 1.0 - (1.0-a)*(1.0-b); }
   vec3 blend_overlay(vec3 a, vec3 b) {
       return a < 0.5 ? 2.0*a*b : 1.0 - 2.0*(1.0-a)*(1.0-b);
   }
   
   vec3 rgb2hsv(vec3 c) {
       vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
       vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
       vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
       float d = q.x - min(q.w, q.y);
       float e = 1.0e-10;
       return vec3(abs(q.z + (q.w - q.y)/(6.0*d + e)), d/(q.x + e), q.x);
   }
   
   vec3 hsv2rgb(vec3 c) {
       vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
       vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
       return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
   }
   
   void main() {
       vec4 original = texture(tex0, uv);
       vec4 return_signal = texture(texReturn, uv);
       float depth = texture(depth_tex, uv).r;
       
       // Depth gate
       float in_gate = step(depthMin, depth) * step(depth, depthMax);
       
       // Apply return saturation
       if (returnSaturation != 1.0) {
           vec3 hsv = rgb2hsv(return_signal.rgb);
           hsv.y *= returnSaturation * 2.0;
           hsv.y = clamp(hsv.y, 0.0, 1.0);
           return_signal.rgb = hsv2rgb(hsv);
       }
       
       // Blend original and return
       float mix_factor = mixAmount / 10.0;
       vec3 blended;
       if (blendMode == 0) blended = blend_add(original.rgb, return_signal.rgb);
       else if (blendMode == 1) blended = blend_multiply(original.rgb, return_signal.rgb);
       else if (blendMode == 2) blended = blend_screen(original.rgb, return_signal.rgb);
       else blended = blend_overlay(original.rgb, return_signal.rgb);
       vec4 mixed = vec4(mix(original.rgb, blended, mix_factor), original.a);
       
       // Apply depth gate to mixed signal
       vec4 send_signal = mixed * in_gate;
       
       // Apply send saturation
       if (sendSaturation != 1.0) {
           vec3 hsv = rgb2hsv(send_signal.rgb);
           hsv.y *= sendSaturation * 2.0;
           hsv.y = clamp(hsv.y, 0.0, 1.0);
           send_signal.rgb = hsv2rgb(hsv);
       }
       
       // Feedback: blend with previous send
       vec4 previous_send = texture(texPrev, uv);
       float feedback = feedbackAmount / 10.0;
       float decay = feedbackDecay / 10.0;  // 0-1
       vec4 feedback_signal = mix(send_signal, previous_send, feedback * decay);
       
       // Hue drift
       if (hueDrift > 0.0) {
           vec3 hsv = rgb2hsv(feedback_signal.rgb);
           float hue_shift = hueDrift * delta_time / 360.0;  // degrees to [0,1]
           hsv.x = fract(hsv.x + hue_shift);
           feedback_signal.rgb = hsv2rgb(hsv);
       }
       
       // Output send signal
       fragColor = feedback_signal;
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthFXLoopEffect(Effect):
       def __init__(self):
           super().__init__("depth_fx_loop", DEPTH_FX_LOOP_FRAGMENT)
           self.depth_source = None
           self.depth_frame = None
           self.depth_texture = 0
           self.parameters = {
               'mixAmount': 1.0,
               'blendMode': 0,
               'depthMin': 0.0,
               'depthMax': 10.0,
               'feedbackAmount': 0.5,
               'feedbackDecay': 0.9,
               'hueDrift': 0.0,
               'sendSaturation': 1.0,
               'returnSaturation': 1.0,
           }
           self.shader = None
           self.prev_send_tex = 0
           self.feedback_fbo = 0
           self.current_tex = 0  # Ping-pong index
           
       def _ensure_textures(self, width, height):
           if self.prev_send_tex == 0:
               self.prev_send_tex = glGenTextures(2)
               self.send_tex_A, self.send_tex_B = self.prev_send_tex, self.prev_send_tex+1
               
               for tex in [self.send_tex_A, self.send_tex_B]:
                   glBindTexture(GL_TEXTURE_2D, tex)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                   glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
               
               self.feedback_fbo = glGenFramebuffers(1)
               
           if self.shader is None:
               self.shader = ShaderProgram(vertex_src, fragment_src)
               
       def process_frame(self, frame, return_frame):
           h, w = frame.shape[:2]
           self._ensure_textures(w, h)
           
           # Upload depth
           self._upload_depth_texture()
           
           # Determine ping-pong
           read_tex = self.send_tex_A if self.current_tex == 0 else self.send_tex_B
           write_tex = self.send_tex_B if self.current_tex == 0 else self.send_tex_A
           
           # Render to framebuffer
           glBindFramebuffer(GL_FRAMEBUFFER, self.feedback_fbo)
           glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, write_tex, 0)
           
           self.shader.use()
           self._apply_uniforms(time, (w,h))
           
           # Bind textures
           glActiveTexture(GL_TEXTURE0)
           glBindTexture(GL_TEXTURE_2D, frame_tex)  # frame converted to texture
           self.shader.set_uniform("tex0", 0)
           
           glActiveTexture(GL_TEXTURE1)
           glBindTexture(GL_TEXTURE_2D, self.depth_texture)
           self.shader.set_uniform("depth_tex", 1)
           
           glActiveTexture(GL_TEXTURE2)
           glBindTexture(GL_TEXTURE_2D, return_frame_tex)
           self.shader.set_uniform("texReturn", 2)
           
           glActiveTexture(GL_TEXTURE3)
           glBindTexture(GL_TEXTURE_2D, read_tex)
           self.shader.set_uniform("texPrev", 3)
           
           # Draw fullscreen quad
           draw_fullscreen_quad()
           
           glBindFramebuffer(GL_FRAMEBUFFER, 0)
           
           # Read back send signal (for external routing)
           send_signal = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
           
           # Swap ping-pong
           self.current_tex = 1 - self.current_tex
           
           return send_signal
   ```

3. **Parameter Clamping**:
   ```python
   def set_parameter(self, name, value):
       if name == 'mixAmount':
           self.parameters['mixAmount'] = max(0.0, min(10.0, value))
       elif name == 'blendMode':
           self.parameters['blendMode'] = max(0, min(3, int(value)))
       elif name == 'depthMin':
           self.parameters['depthMin'] = max(0.0, min(10.0, value))
       elif name == 'depthMax':
           self.parameters['depthMax'] = max(0.0, min(10.0, value))
       elif name == 'feedbackAmount':
           self.parameters['feedbackAmount'] = max(0.0, min(10.0, value))
       elif name == 'feedbackDecay':
           self.parameters['feedbackDecay'] = max(0.0, min(10.0, value))
       elif name == 'hueDrift':
           self.parameters['hueDrift'] = max(0.0, min(10.0, value))
       elif name in ('sendSaturation', 'returnSaturation'):
           self.parameters[name] = max(0.0, min(10.0, value))
   ```

4. **Depth Texture Upload**: Same as other depth effects.

5. **PRESETS**: Define useful configurations:
   ```python
   PRESETS = {
       "subtle_loop": {
           "mixAmount": 5.0, "blendMode": 2, "depthMin": 0.0, "depthMax": 10.0,
           "feedbackAmount": 2.0, "feedbackDecay": 8.0, "hueDrift": 0.0,
           "sendSaturation": 1.0, "returnSaturation": 1.0,
       },
       "aggressive_feedback": {
           "mixAmount": 8.0, "blendMode": 0, "depthMin": 2.0, "depthMax": 8.0,
           "feedbackAmount": 7.0, "feedbackDecay": 5.0, "hueDrift": 3.0,
           "sendSaturation": 2.0, "returnSaturation": 2.0,
       },
       "depth_gated_echo": {
           "mixAmount": 6.0, "blendMode": 3, "depthMin": 0.0, "depthMax": 4.0,
           "feedbackAmount": 6.0, "feedbackDecay": 7.0, "hueDrift": 1.0,
           "sendSaturation": 1.5, "returnSaturation": 1.5,
       },
   }
   ```

6. **Usage Pattern**: In a node graph:
   ```
   [Video Source] → [DepthFXLoop (Send)] → [External Effect] → [DepthFXLoop (Return)] → [Output]
   ```
   The two DepthFXLoop instances should share state (e.g., same feedback texture) to create a closed loop. This may require a shared feedback buffer managed externally.

7. **Alternative Design**: Instead of two separate instances, a single instance could have both send and return inputs:
   ```python
   def process_frame(self, frame, return_frame=None):
       # If return_frame is None, use original or previous feedback
   ```
   This simplifies routing but is less modular.

8. **Loop Prevention**: To prevent infinite feedback loops, the `feedbackDecay` should be < 1.0. Document that setting it to 10 (maps to 1.0) will cause infinite recursion.

9. **Delta Time**: Need to track time between frames for hue drift. Pass `delta_time` as uniform:
   ```python
   delta_time = current_time - self.last_time
   self.last_time = current_time
   self.shader.set_uniform("delta_time", delta_time)
   ```

10. **Testing**: Create a simple loop: Send → Blur → Return. Verify:
    - Blur effect accumulates over time (feedback)
    - Hue drift gradually shifts colors
    - Depth gate restricts effect to certain depths
    - Blend modes produce different mixing

---

## Conclusion

The DepthFXLoopEffect provides a modular, synth-like effects send/return bus for video processing. By routing signals through external effects with depth-gated mixing, temporal feedback, and hue drift, it enables complex, evolving effect chains that respond to depth. This effect is a powerful tool for creating sophisticated, recursive visuals in VJ performances, offering flexibility and creative control over signal routing.

---
