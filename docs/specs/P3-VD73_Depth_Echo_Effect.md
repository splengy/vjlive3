# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD73_Depth_Echo_Effect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD73 — DepthEchoEffect

## Description

The DepthEchoEffect is a depth-based temporal echo and trail effect that creates ghostly afterimages and motion-based persistence. It uses depth information to control how previous frames are blended with the current frame, creating echoes that respect the 3D structure of the scene. This effect is ideal for creating ethereal, dreamlike visuals where depth determines the persistence of motion.

This effect is perfect for VJ performances that want to create haunting, atmospheric visuals with depth-aware trails. The effect is particularly effective for creating ghostly apparitions, motion blur that respects depth, and surreal temporal distortions.

## What This Module Does

- Creates temporal echoes based on depth values
- Uses depth gradients to drive optical flow simulation
- Smears pixels where depth change is low (flat areas)
- Refreshes pixels where depth is high (edges)
- Provides feedback persistence control (decay)
- Adds optional noise for chaotic displacement
- GPU-accelerated with real-time performance
- Depth-aware: respects 3D structure of the scene

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT include audio reactivity in base implementation
- Does NOT produce 3D geometry (2D effect only)
- Does NOT include color correction (only temporal blending)
- Does NOT support multiple independent echo layers (single feedback loop)

---

## Detailed Behavior

### Depth Echo Pipeline

1. **Capture current frame**: `current_frame` (HxWxC, RGB)
2. **Capture depth map**: `depth_frame` (HxW, normalized 0-1)
3. **Compute optical flow**: From depth gradients (depth change between pixels)
4. **Sample previous frame**: Using flow-based offset
5. **Compute mix factor**: Based on depth change and decay
6. **Blend**: Mix previous and current frames
7. **Store result**: As feedback for next frame

### Core Concept: Depth-Driven Moshing

The effect creates a "moshing" behavior where pixels are either smeared from previous frames or refreshed with current content. The decision is based on depth:

- **Low depth change** (flat areas): Smear previous pixels → creates trails/echoes
- **High depth change** (edges): Refresh with current pixel → prevents excessive smearing

```glsl
vec2 flow = compute_flow_from_depth(depth_tex, uv);  // Depth gradient → displacement
vec2 lookup = uv - flow * flow_strength;
vec4 prev = texture(texPrev, lookup);  // Sample previous frame with offset
vec4 curr = texture(tex0, uv);         // Sample current frame

float diff = length(flow);  // Magnitude of depth change
float mixFactor = smoothstep(depth_threshold, depth_threshold + 0.1, diff);

// Always refresh a bit to avoid total stagnation
mixFactor = max(mixFactor, 0.05);

// Apply decay: higher decay = more persistence
mixFactor = mix(mixFactor, 1.0, 1.0 - decay);

// Blend
fragColor = mix(prev, curr, mixFactor);
```

### Optical Flow from Depth

The flow vector is derived from depth gradients:

```glsl
vec2 depth_grad = compute_gradient(depth_tex, uv);
vec2 flow = depth_grad * flow_strength;
```

The gradient indicates how depth changes across the image. In flat areas (low gradient), the flow is small, causing the lookup to be close to the current position, which smears nearby pixels. In edges (high gradient), the flow is large, causing the lookup to sample from farther away, which refreshes the pixel.

### Decay and Persistence

The `decay` parameter controls how long echoes persist:

- `decay = 0.0`: Instant fade (no persistence)
- `decay = 10.0`: Infinite persistence (never fully fade)

The mix factor is adjusted by decay:

```glsl
mixFactor = mix(mixFactor, 1.0, 1.0 - decay);
```

Higher decay means the previous frame contributes more, creating longer trails.

### Noise

Optional noise can be added to the flow to create chaotic, glitchy behavior:

```glsl
vec2 noise = random2(uv) * noise_amount * 0.1;
lookup += noise;
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `flow_strength` | float | 5.0 | 0.0-10.0 | Intensity of depth-driven displacement (how far to look back) |
| `depth_threshold` | float | 2.0 | 0.0-10.0 | Sensitivity to depth edges (lower = more edges trigger refresh) |
| `decay` | float | 9.0 | 0.0-10.0 | Feedback persistence (0=instant fade, 10=infinite) |
| `noise_amount` | float | 1.0 | 0.0-10.0 | Random chaotic displacement added to flow |
| `u_mix` | float | 10.0 | 0.0-10.0 | Overall mix with original (10 = full effect) |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class DepthEchoEffect(Datamosh3DEffect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray, depth_frame: np.ndarray, prev_frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Current video frame (HxWxC, RGB) |
| `depth_frame` | `np.ndarray` | Depth map (HxW, normalized 0-1) |
| `prev_frame` | `np.ndarray` | Previous processed frame (for feedback) |
| **Output** | `np.ndarray` | Echo-processed frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_prev_frame: Optional[np.ndarray]` — Previous output (feedback buffer)
- `_parameters: dict` — Echo parameters
- `_shader: ShaderProgram` — Compiled shader
- `_fbo: int` — Framebuffer for feedback rendering
- `_feedback_texture: int` — Texture storing previous frame

**Per-Frame:**
- Update depth data from source
- Bind current frame to `tex0`
- Bind previous frame to `texPrev`
- Render to feedback texture
- Swap feedback texture for next frame
- Return result

**Initialization:**
- Compile shader
- Create framebuffer and feedback texture
- Initialize `_prev_frame = None`
- Default parameters: `flow_strength=5.0`, `depth_threshold=2.0`, `decay=9.0`, `noise_amount=1.0`
- Allocate feedback texture matching frame size

**Cleanup:**
- Delete framebuffer
- Delete feedback texture
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Shader program | GLSL | vertex + fragment | N/A | Init once |
| Framebuffer | GL_FRAMEBUFFER | N/A | N/A | Init once |
| Feedback texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Init once, updated per-frame |

**Memory Budget (640×480):**
- Shader: ~30-40 KB
- Framebuffer: ~1 KB
- Feedback texture: ~1.2 MB
- Total: ~2.5 MB (moderate)

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use uniform depth (0.5) | Normal operation |
| No previous frame | Use current frame as previous | Normal operation (first frame) |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Framebuffer incomplete | `RuntimeError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Texture size mismatch | Reallocate feedback texture | Resize on next frame |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and shader operations must occur on the thread with the OpenGL context. The effect updates state each frame (feedback texture swap); concurrent `process_frame()` calls will cause race conditions and corrupted rendering. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Shader execution (flow computation, blending): ~4-8 ms
- Framebuffer operations: ~1-2 ms
- Total: ~5-10 ms on GPU (moderate)

**Optimization Strategies:**
- Reduce `flow_strength` (less displacement)
- Increase `depth_threshold` (fewer edges)
- Disable noise (`noise_amount = 0`)
- Use lower resolution for depth processing
- Simplify gradient computation

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Previous frame buffer initialized
- [ ] Echo parameters configured
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_flow_strength` | Flow strength controls displacement magnitude |
| `test_depth_threshold` | Depth threshold controls refresh sensitivity |
| `test_decay` | Decay controls persistence length |
| `test_noise` | Noise adds chaotic displacement |
| `test_feedback_loop` | Previous frame influences current output |
| `test_depth_modulation` | Depth modulates echo behavior |
| `test_edge_refresh` | Edges refresh more than flat areas |
| `test_flat_smear` | Flat areas smear previous content |
| `test_first_frame` | First frame uses current as previous |
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
- [ ] Git commit with `[Phase-3] P3-VD73: depth_echo_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdatamosh/datamosh_3d.py` — VJLive Original implementation (mode=2)
- `plugins/core/datamosh_3d/__init__.py` — VJLive-2 implementation
- `plugins/core/datamosh_3d/plugin.json` — Effect manifest
- `core/effects/datamosh_3d.py` — Base class with shader

Design decisions inherited:
- Effect name: `depth_echo`
- Inherits from `Datamosh3DEffect` (base class with feedback loop)
- Uses mode parameter: `self.parameters['mode'] = 2`
- Shader implements feedback loop with `texPrev` and depth-based flow
- Parameters: `flow_strength`, `depth_threshold`, `decay`, `noise_amount`
- Allocates GL resources: framebuffer, feedback texture
- Method `apply_uniforms()` binds depth texture to unit 2
- Presets: "subtle_echo", "long_trails", "edge_refresh", "glitch_echo"

---

## Notes for Implementers

1. **Core Concept**: This effect creates temporal echoes where previous frames are smeared into the current frame based on depth. Flat areas (low depth gradient) smear more, creating trails. Edges (high depth gradient) refresh more, preventing excessive smearing.

2. **Depth-Driven Flow**: The optical flow is computed from depth gradients. The gradient indicates how depth changes; this drives the offset for sampling the previous frame.

3. **Feedback Loop**: The effect requires a feedback buffer (previous frame texture). Each frame, the current output becomes the previous frame for the next iteration.

4. **Decay**: Controls how much the previous frame contributes. High decay = long trails. Low decay = short trails.

5. **Flow Strength**: Controls how far to offset the previous frame sample. Higher = more displacement, longer trails.

6. **Depth Threshold**: Controls the sensitivity of edge detection. Lower = more pixels refresh (shorter trails). Higher = fewer pixels refresh (longer trails).

7. **Noise**: Adds random displacement to the flow, creating glitchy, chaotic echoes.

8. **Shader Uniforms**:
   ```glsl
   uniform sampler2D tex0;           // Current frame
   uniform sampler2D texPrev;        // Previous frame (feedback)
   uniform sampler2D texDepth;       // Depth map
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float flow_strength;      // 0-10
   uniform float depth_threshold;    // 0-10
   uniform float decay;              // 0-10
   uniform float noise_amount;       // 0-10
   ```

9. **Parameter Mapping** (0-10 → actual):
   - `flow_strength`: 0-10 → 0-0.5 (divide by 20) or similar scaling
   - `depth_threshold`: 0-10 → 0-0.2 (divide by 50) or similar
   - `decay`: 0-10 → 0-1 (divide by 10) but used as `1.0 - decay/10.0`
   - `noise_amount`: 0-10 → 0-0.1 (divide by 100)

10. **PRESETS**:
    ```python
    PRESETS = {
        "subtle_echo": {
            "flow_strength": 2.0, "depth_threshold": 3.0, "decay": 7.0,
            "noise_amount": 0.5,
        },
        "long_trails": {
            "flow_strength": 8.0, "depth_threshold": 1.0, "decay": 9.8,
            "noise_amount": 0.2,
        },
        "edge_refresh": {
            "flow_strength": 4.0, "depth_threshold": 5.0, "decay": 6.0,
            "noise_amount": 0.0,
        },
        "glitch_echo": {
            "flow_strength": 6.0, "depth_threshold": 2.0, "decay": 8.0,
            "noise_amount": 5.0,
        },
    }
    ```

11. **Testing Strategy**:
    - Test with uniform depth: should create uniform smearing
    - Test with depth ramp: edges should refresh more
    - Test flow_strength: higher = more displacement
    - Test depth_threshold: lower = more refresh (shorter trails)
    - Test decay: higher = longer trails
    - Test noise: adds random glitches
    - Test feedback: previous frame affects current
    - Test first frame: no crash when no previous frame

12. **Performance**: Light to moderate — single texture fetch for previous frame, gradient computation, simple blending.

13. **Memory**: Moderate — needs feedback texture (same size as frame).

14. **Debug Mode**: Visualize flow vectors, depth gradient, mix factor.

---

## Easter Egg Idea

When `flow_strength` is set exactly to 6.66, `depth_threshold` to exactly 6.66, `decay` to exactly 6.66, and `noise_amount` to exactly 6.66, the depth echo enters a "sacred echo" state where the feedback loop creates exactly 666 layers of temporal persistence, each layer offset by exactly 6.66 pixels, the depth threshold creates exactly 666 distinct edge zones, the decay creates exactly 666.6% persistence (negative decay), the noise creates exactly 666 random seeds per frame, the flow vectors form exactly 666 perfect spirals, and the entire effect creates a "temporal prayer" where every echo is exactly 666% more haunted than normal. The framebuffer fills with exactly 666 ghostly afterimages that each last exactly 6.66 seconds, creating a perfect 6.66×6.66 grid of sacred temporal geometry.

---

## References

- Temporal aliasing: https://en.wikipedia.org/wiki/Temporal_aliasing
- Motion blur: https://en.wikipedia.org/wiki/Motion_blur
- Feedback buffer: https://en.wikipedia.org/wiki/Feedback
- Optical flow: https://en.wikipedia.org/wiki/Optical_flow
- VJLive legacy: `plugins/vdatamosh/datamosh_3d.py` (mode=2)

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;           // Current frame
   uniform sampler2D texPrev;        // Previous frame (feedback)
   uniform sampler2D texDepth;       // Depth map
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float flow_strength;      // 0-10
   uniform float depth_threshold;    // 0-10
   uniform float decay;              // 0-10
   uniform float noise_amount;       // 0-10
   
   // Pseudo-random
   float random(vec2 uv) {
       return fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
   }
   
   vec2 random2(vec2 uv) {
       return vec2(random(uv), random(uv + vec2(123.45, 67.89)));
   }
   
   // Compute depth gradient (Sobel)
   vec2 depth_gradient(sampler2D depth_tex, vec2 uv) {
       vec2 texel = 1.0 / resolution;
       float d00 = texture(depth_tex, uv).r;
       float d10 = texture(depth_tex, uv + vec2(texel.x, 0.0)).r;
       float d01 = texture(depth_tex, uv + vec2(0.0, texel.y)).r;
       
       float dx = d10 - d00;
       float dy = d01 - d00;
       
       return vec2(dx, dy);
   }
   
   void main() {
       // Get depth gradient
       vec2 depth_grad = depth_gradient(texDepth, uv);
       
       // Compute flow from depth gradient
       vec2 flow = depth_grad * flow_strength * 0.1;
       
       // Add noise if enabled
       if (noise_amount > 0.0) {
           flow += random2(uv) * noise_amount * 0.01;
       }
       
       // Sample previous frame with offset
       vec2 lookup = uv - flow;
       vec4 prev = texture(texPrev, lookup);
       
       // Sample current frame
       vec4 curr = texture(tex0, uv);
       
       // Compute mix factor based on depth change
       float diff = length(depth_grad);
       float mixFactor = smoothstep(depth_threshold * 0.01, depth_threshold * 0.01 + 0.02, diff);
       
       // Always refresh a bit to avoid total stagnation
       mixFactor = max(mixFactor, 0.05);
       
       // Apply decay: higher decay = more persistence
       float decay_factor = 1.0 - decay * 0.1;
       mixFactor = mix(mixFactor, 1.0, decay_factor);
       
       // Blend
       fragColor = mix(prev, curr, mixFactor);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthEchoEffect(Datamosh3DEffect):
       def __init__(self):
           super().__init__("depth_echo")
           self.parameters['mode'] = 2
           
           # Override defaults for echo-specific parameters
           self.parameters.update({
               'flow_strength': 5.0,
               'depth_threshold': 2.0,
               'decay': 9.0,
               'noise_amount': 1.0,
           })
       
       def init_feedback(self, width, height):
           """Initialize feedback texture and framebuffer."""
           self.feedback_texture = glGenTextures(1)
           glBindTexture(GL_TEXTURE_2D, self.feedback_texture)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
           
           self.fbo = glGenFramebuffers(1)
           glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
           glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.feedback_texture, 0)
           
           if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
               raise RuntimeError("Feedback framebuffer incomplete")
           
           glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       def process_frame(self, frame, depth_frame):
           h, w = frame.shape[:2]
           
           # Initialize feedback on first frame
           if not hasattr(self, 'feedback_texture'):
               self.init_feedback(w, h)
           
           # Update depth texture
           glActiveTexture(GL_TEXTURE2)
           glBindTexture(GL_TEXTURE_2D, self.depth_texture)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RED, GL_UNSIGNED_BYTE, depth_frame)
           
           # Bind current frame to tex0
           glActiveTexture(GL_TEXTURE0)
           glBindTexture(GL_TEXTURE_2D, self.current_tex)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, frame)
           
           # Bind previous frame to texPrev
           glActiveTexture(GL_TEXTURE3)
           glBindTexture(GL_TEXTURE_2D, self.feedback_texture)
           
           # Render to feedback texture
           glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
           
           self.shader.use()
           self.apply_uniforms(time, (w, h))
           
           glUniform1i(glGetUniformLocation(self.shader.program, "tex0"), 0)
           glUniform1i(glGetUniformLocation(self.shader.program, "texPrev"), 3)
           glUniform1i(glGetUniformLocation(self.shader.program, "texDepth"), 2)
           
           draw_fullscreen_quad()
           
           # Read result from framebuffer
           glBindFramebuffer(GL_FRAMEBUFFER, 0)
           result = self._read_pixels_from_fbo(self.fbo, w, h)
           
           # Swap: result becomes next frame's previous
           # (Already in feedback_texture via FBO)
           
           return result
   ```

3. **Feedback Management**: The effect uses a ping-pong buffer approach. The feedback texture is both read (as previous frame) and written (as current output). After rendering, the feedback texture contains the current output for the next frame.

4. **Depth Gradient**: Compute using Sobel or simple central differences. The gradient indicates depth edges.

5. **Flow Calculation**: `flow = depth_gradient * flow_strength`. The flow offsets the UV for sampling the previous frame.

6. **Mix Factor**: Determines how much to blend previous vs current. Based on depth gradient magnitude: high gradient = refresh (mixFactor → 1), low gradient = smear (mixFactor → 0.05 minimum).

7. **Decay**: Adjusts mixFactor toward 1.0. Higher decay means less adjustment, so previous frame contributes more.

8. **Noise**: Optional random offset added to flow for glitchy effect.

9. **Performance**: The effect requires an extra framebuffer and texture, but the shader is relatively simple. Should run at 60+ fps at 1080p on modern GPUs.

10. **Testing**: Use a moving object with depth. Verify:
    - Moving object leaves trails
    - Edges refresh quickly (shorter trails)
    - Flat areas have long trails
    - Decay controls trail length
    - Flow strength controls trail offset
    - Noise adds random glitches

11. **Future Extensions**:
    - Add audio reactivity to decay or flow
    - Add multiple feedback layers
    - Add color-based echo (separate channels)
    - Add directional flow (not just from depth)

---

## Conclusion

The DepthEchoEffect is a depth-aware temporal echo that creates ghostly trails and motion persistence. By using depth gradients to drive optical flow, it respects the 3D structure of the scene: flat areas smear into long trails, while edges refresh to maintain clarity. This creates ethereal, dreamlike visuals perfect for atmospheric VJ performances. With configurable flow strength, depth threshold, decay, and noise, the effect offers a wide range of temporal distortion possibilities.

---
>>>>>>> REPLACE