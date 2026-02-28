# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD55_Depth_Modular_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD55 — DepthModularDatamoshEffect

## Description

The DepthModularDatamoshEffect is the first datamosh effect with built-in effects insert points, providing a truly modular datamosh architecture. It features a two-stage processing pipeline where Stage 1 performs depth analysis and displacement, then sends the signal out through a LOOP SEND to external effects. The processed signal returns via LOOP RETURN and enters Stage 2, which applies block corruption, I-frame loss, temporal feedback, color quantization, and scanline corruption. Whatever effects you route through the loop get baked directly into the datamosh corruption layer, creating unique compound effects.

This effect is designed for advanced VJs who want to inject their own processing directly into the datamosh algorithm. By routing color grading, distortion, or other effects through the loop, you can control exactly how the datamosh corrupts your signal. The effect is highly audio-reactive, with all corruption metrics responding to audio input.

## What This Module Does

- Implements two-stage datamosh pipeline with explicit loop point
- Stage 1: Depth analysis + displacement (pre-corruption)
- Stage 2: Block corruption, I-frame loss, temporal feedback, color quantization, scanlines
- Provides LOOP SEND and LOOP RETURN for external effect injection
- Depth-weighted composite: near objects get less corruption, far objects get more
- Audio reactivity across all corruption metrics
- GPU-accelerated fragment shader with modular routing

## What This Module Does NOT Do

- Does NOT include built-in effects in the loop (only routing)
- Does NOT manage external effect instances (user must connect)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT implement multiple loop points (single loop only)
- Does NOT include loopback protection (user must avoid infinite loops)

---

## Detailed Behavior

### Processing Pipeline

```
[Input]
   |
   v
Stage 1: Depth Analysis + Displacement
   |
   v
LOOP SEND → [External Effect] → LOOP RETURN
   |
   v
Stage 2: Corruption + Feedback
   |
   v
[Output]
```

#### Stage 1: Depth Analysis & Displacement

1. **Compute depth gradient**:
   ```
   dx = dFdx(depth)
   dy = dFdy(depth)
   grad = vec2(dx, dy)
   ```

2. **Depth-weighted displacement**: Displace pixels along depth gradient:
   ```
   displacement = grad * displacement_strength
   uv_displaced = uv + displacement
   ```

3. **Optional motion from depth**: Simulate motion blur based on depth change:
   ```
   motion = (depth - previous_depth) * motion_strength
   uv_displaced += motion
   ```

4. **Sample displaced frame**:
   ```
   color = texture(tex0, uv_displaced)
   ```

5. **Send to LOOP**: Output this pre-corruption signal to external effects via LOOP SEND.

#### Loop Injection

- **LOOP SEND**: The Stage 1 output is sent to external effects.
- **LOOP RETURN**: The external effects' output is received.
- **Mix**: The returned signal is mixed with Stage 1 output (wet/dry control).
- **If loop disabled**: Stage 1 output passes directly to Stage 2.

#### Stage 2: Corruption & Feedback

1. **Block corruption** (datamosh):
   - Quantize UV to block grid
   - Shift blocks based on corruption strength
   - Simulate I-frame loss by freezing blocks

2. **Temporal feedback**:
   - Blend current frame with previous frame's output
   - Feedback amount controls recursion
   - Feedback decay controls persistence

3. **Color quantization**:
   - Reduce color bit depth (posterization)
   - Creates banding artifacts

4. **Scanline corruption**:
   - Simulate CRT scanline issues
   - Drop lines, add noise

5. **Depth-weighted composite**:
   - Near objects (low depth) get less corruption
   - Far objects (high depth) get more corruption
   - Controlled by `depthComposite` parameter

6. **Final mix**: Blend with original input.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `displacementStrength` | float | 5.0 | 0.0-10.0 | Strength of depth-based displacement |
| `motionStrength` | float | 3.0 | 0.0-10.0 | Motion blur from depth changes |
| `loopEnable` | float | 0.0 | 0.0-10.0 | Enable loop (0=off, >0=on) |
| `loopMix` | float | 5.0 | 0.0-10.0 | Wet/dry mix for loop (0=dry, 10=wet) |
| `blockCorruption` | float | 6.0 | 0.0-10.0 | Intensity of block datamosh |
| `iframeLoss` | float | 4.0 | 0.0-10.0 | Simulated I-frame loss (freezing) |
| `feedbackAmount` | float | 0.5 | 0.0-10.0 | Feedback loop strength |
| `feedbackDecay` | float | 0.9 | 0.0-10.0 | Feedback decay per frame |
| `colorQuantization` | float | 3.0 | 0.0-10.0 | Color bit depth reduction |
| `scanlineIntensity` | float | 2.0 | 0.0-10.0 | Scanline corruption strength |
| `depthComposite` | float | 5.0 | 0.0-10.0 | Depth-weighted corruption (0=uniform, 10=depth-driven) |
| `audioReactivity` | float | 5.0 | 0.0-10.0 | How much audio modulates corruption |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthModularDatamoshEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray, loop_return: Optional[np.ndarray] = None) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| `loop_return` | `np.ndarray` (optional) | Return from external effect (HxWxC, RGB) |
| **Output** | `np.ndarray` | Datamosh output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_parameters: dict` — All modular datamosh parameters
- `_shader: ShaderProgram` — Compiled shader
- `_previous_frame_texture: int` — For temporal feedback
- `_framebuffer: int` — For rendering
- `_previous_depth: Optional[np.ndarray]` — For motion calculation

**Per-Frame:**
- Update depth data from source
- Upload depth texture
- Set shader uniforms (including audio level if available)
- Render Stage 1 (depth displacement)
- If loop enabled and return provided, mix with return
- Render Stage 2 (corruption + feedback)
- Store output in previous frame texture for next frame
- Return final result

**Initialization:**
- Create depth texture (lazy)
- Create previous frame texture (ping-pong)
- Create framebuffer
- Compile shader
- Default parameters: displacementStrength=5.0, motionStrength=3.0, loopEnable=0.0, loopMix=5.0, blockCorruption=6.0, iframeLoss=4.0, feedbackAmount=0.5, feedbackDecay=0.9, colorQuantization=3.0, scanlineIntensity=2.0, depthComposite=5.0, audioReactivity=5.0

**Cleanup:**
- Delete depth texture
- Delete previous frame texture
- Delete framebuffer
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Previous frame texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame |
| Framebuffer | GL_FRAMEBUFFER | N/A | frame size | Persistent |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Depth texture: 307,200 bytes
- Previous frame texture: 921,600 bytes
- Framebuffer: negligible
- Shader: ~30-60 KB (complex)
- Total: ~1.2 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Use zero gradient (no displacement) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Loop return size mismatch | Resize or raise `ValueError` | Ensure consistent sizing |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and texture updates must occur on the thread with the OpenGL context. The depth texture and previous frame texture are updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Shader execution (Stage 1 + Stage 2): ~6-12 ms
- Texture copy for feedback: ~0.5-1 ms
- Total: ~7-14 ms on GPU

**Optimization Strategies:**
- Reduce block corruption resolution (larger blocks = faster)
- Disable expensive stages (set intensity=0)
- Use simpler shader branches for disabled effects
- Lower scanline resolution
- Cache depth texture if depth hasn't changed
- Use compute shader for parallel processing

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Modular datamosh parameters configured
- [ ] Loop enabled if using external effects
- [ ] External effect connected to loop return (if loop enabled)
- [ ] `process_frame()` called each frame with loop_return if loop enabled
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_stage1_displacement` | Depth gradient displaces pixels correctly |
| `test_stage1_motion` | Depth change creates motion blur |
| `test_loop_routing` | Loop send/return works correctly |
| `test_loop_mix` | Wet/dry mix blends Stage 1 output with loop return |
| `test_block_corruption` | Block datamosh creates artifacts |
| `test_iframe_loss` | I-frame loss freezes blocks |
| `test_feedback` | Temporal feedback creates recursion |
| `test_color_quantization` | Reduces color depth (posterization) |
| `test_scanlines` | Scanline corruption adds line artifacts |
| `test_depth_composite` | Depth modulates corruption intensity |
| `test_audio_reactivity` | Audio level modulates corruption |
| `test_process_frame_no_loop` | Loop bypassed = Stage 1 → Stage 2 |
| `test_process_frame_with_loop` | Loop return mixed into Stage 2 |
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
- [ ] Git commit with `[Phase-3] P3-VD55: depth_modular_datamosh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_modular_datamosh.py` — VJLive Original implementation
- `plugins/core/depth_modular_datamosh/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_modular_datamosh/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthModularDatamoshEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_modular_datamosh`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for displacement and depth-weighted composite
- Single loop point (not multiple)
- Parameters: `displacementStrength`, `motionStrength`, `loopEnable`, `loopMix`, `blockCorruption`, `iframeLoss`, `feedbackAmount`, `feedbackDecay`, `colorQuantization`, `scanlineIntensity`, `depthComposite`, `audioReactivity`
- Allocates GL resources: depth texture, previous frame texture, framebuffer
- Shader implements Stage 1 (displacement) and Stage 2 (corruption) with loop injection
- Audio reactive across corruption metrics

---

## Notes for Implementers

1. **Two-Stage Pipeline**: The key innovation is the explicit loop between Stage 1 and Stage 2. Stage 1 does depth-based displacement; Stage 2 does corruption. The loop allows you to inject effects between these stages, so whatever you route through the loop gets baked into the datamosh.

2. **Stage 1: Depth Displacement**:
   - Compute depth gradient
   - Displace UV coordinates along gradient
   - Optionally add motion from depth changes (temporal derivative)
   - Sample displaced frame
   - Send to loop

3. **Loop Injection**:
   - If `loopEnable > 0` and `loop_return` provided:
     ```python
     stage1_output = ...  # from displacement
     looped = mix(stage1_output, loop_return, loopMix / 10.0)
     ```
   - If loop disabled, `looped = stage1_output`

4. **Stage 2: Corruption**:
   - **Block corruption**: Divide image into blocks (e.g., 8×8), randomly shift blocks based on `blockCorruption` strength. Simulates macroblock errors.
   - **I-frame loss**: Freeze certain blocks for several frames (don't update from current frame).
   - **Temporal feedback**: Blend current frame with previous output:
     ```
     feedback = mix(looped, previous_frame, feedbackAmount * feedbackDecay)
     ```
   - **Color quantization**: Reduce color precision:
     ```
     levels = pow(2, 8 - colorQuantization * 0.5)  # e.g., 8 levels
     color = floor(color * levels) / levels
     ```
   - **Scanline corruption**: Drop or corrupt alternating lines based on `scanlineIntensity`.
   - **Depth-weighted composite**: Blend original with corrupted based on depth:
     ```
     depth_weight = mix(1.0, depth, depthComposite / 10.0)
     final = mix(looped, corrupted, depth_weight)
     ```

5. **Audio Reactivity**: Map audio level (0-1) to corruption intensities:
   ```glsl
   float audio = get_audio_level();  // Provided by framework
   float block_strength = blockCorruption * (1.0 + audioReactivity * audio);
   float feedback_strength = feedbackAmount * (1.0 + audioReactivity * audio);
   // etc.
   ```

6. **Shader Structure**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;        // Input frame
   uniform sampler2D depth_tex;   // Depth texture
   uniform sampler2D texPrev;     // Previous frame (feedback)
   uniform sampler2D texLoopRet;  // Loop return (optional)
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   uniform float audio_level;  // 0-1
   
   // Parameters (0-10 range)
   uniform float displacementStrength;
   uniform float motionStrength;
   uniform float loopEnable;     // 0 or 1
   uniform float loopMix;        // 0-1 (mapped)
   uniform float blockCorruption;
   uniform float iframeLoss;
   uniform float feedbackAmount;
   uniform float feedbackDecay;
   uniform float colorQuantization;
   uniform float scanlineIntensity;
   uniform float depthComposite;
   uniform float audioReactivity;
   
   // Random function
   float random(vec2 st) {
       return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
   }
   
   void main() {
       vec4 source = texture(tex0, uv);
       float depth = texture(depth_tex, uv).r;
       
       // ===== STAGE 1: DEPTH DISPLACEMENT =====
       float dx = dFdx(depth);
       float dy = dFdy(depth);
       vec2 displacement = vec2(dx, dy) * displacementStrength * 0.01;
       
       // Motion from depth change (need previous depth)
       // Could store previous depth in texture or compute from prev frame
       // For simplicity, skip or approximate
       
       vec2 uv_displaced = uv + displacement;
       vec4 stage1 = texture(tex0, uv_displaced);
       
       // Loop injection
       vec4 looped = stage1;
       if (loopEnable > 0.5) {
           vec4 loop_return = texture(texLoopRet, uv);
           looped = mix(stage1, loop_return, loopMix);
       }
       
       // ===== STAGE 2: CORRUPTION =====
       vec4 corrupted = looped;
       
       // Block corruption
       if (blockCorruption > 0.0) {
           vec2 block_size = vec2(8.0, 8.0);  // Could be parameter
           vec2 block_uv = floor(uv * resolution / block_size) * block_size / resolution;
           float block_random = random(block_uv);
           if (block_random < blockCorruption * 0.1) {
               // Shift block
               vec2 shift = (vec2(random(block_uv + time), random(block_uv + time + 1.0)) - 0.5) * block_size / resolution;
               corrupted = texture(tex0, block_uv + shift);
           }
       }
       
       // I-frame loss (freeze blocks)
       if (iframeLoss > 0.0) {
           // Similar block logic, but skip update if block is "frozen"
           // Need to store which blocks are frozen from previous frame
           // Simplified: just skip corruption for some blocks
       }
       
       // Temporal feedback
       if (feedbackAmount > 0.0) {
           vec4 prev = texture(texPrev, uv);
           float decay = feedbackDecay * 0.1;  // 0-1
           corrupted = mix(corrupted, prev, feedbackAmount * decay);
       }
       
       // Color quantization
       if (colorQuantization > 0.0) {
           float levels = pow(2.0, 8.0 - colorQuantization * 0.5);  // 8 to 4 levels
           corrupted.rgb = floor(corrupted.rgb * levels) / levels;
       }
       
       // Scanline corruption
       if (scanlineIntensity > 0.0) {
           float line_y = floor(uv.y * resolution.y);
           float line_random = random(vec2(uv.x, line_y));
           if (line_random < scanlineIntensity * 0.05) {
               corrupted.rgb = 1.0 - corrupted.rgb;  // Invert line
           }
       }
       
       // Depth-weighted composite
       if (depthComposite > 0.0) {
           float depth_weight = mix(1.0, depth, depthComposite * 0.1);
           corrupted.rgb = mix(looped.rgb, corrupted.rgb, depth_weight);
       }
       
       // Final mix with source
       fragColor = mix(source, corrupted, u_mix);
   }
   ```

7. **Parameter Mapping**:
   - `displacementStrength`: 0-10 → multiply by 0.01
   - `motionStrength`: 0-10 → multiply by 0.01
   - `loopEnable`: 0-10 → 0.0 or 1.0 (threshold >0)
   - `loopMix`: 0-10 → 0.0-1.0 (divide by 10)
   - `blockCorruption`: 0-10 → probability multiplier (0.1)
   - `iframeLoss`: 0-10 → probability multiplier
   - `feedbackAmount`: 0-10 → 0.0-1.0 (divide by 10)
   - `feedbackDecay`: 0-10 → 0.0-1.0 (divide by 10)
   - `colorQuantization`: 0-10 → levels reduction (max 4 bits)
   - `scanlineIntensity`: 0-10 → probability multiplier (0.05)
   - `depthComposite`: 0-10 → 0.0-1.0 (multiply by 0.1)
   - `audioReactivity`: 0-10 → multiplier for audio modulation

8. **Previous Frame Feedback**: Need to store previous output. Use ping-pong textures:
   ```python
   self.prev_tex = glGenTextures(2)
   self.current_prev = 0
   
   # Each frame:
   read_tex = self.prev_tex[self.current_prev]
   write_tex = self.prev_tex[1 - self.current_prev]
   # Render to write_tex
   self.current_prev = 1 - self.current_prev
   ```

9. **I-Frame Loss**: To properly simulate I-frame loss, you need to track which blocks are frozen across frames. This requires a block state texture or buffer. Simplified version: just randomly skip updating some blocks (they'll persist from previous frame via feedback).

10. **Audio Reactivity**: The effect should accept an audio level (0-1) via `apply_uniforms` or a separate method. Map this to corruption intensities:
    ```python
    audio = audio_reactor.get_level() if audio_reactor else 0.0
    self.shader.set_uniform('audio_level', audio)
    ```

11. **PRESETS**:
    ```python
    PRESETS = {
        "clean": {
            "displacementStrength": 0.0, "motionStrength": 0.0,
            "loopEnable": 0.0, "loopMix": 0.0,
            "blockCorruption": 0.0, "iframeLoss": 0.0,
            "feedbackAmount": 0.0, "feedbackDecay": 0.9,
            "colorQuantization": 0.0, "scanlineIntensity": 0.0,
            "depthComposite": 0.0, "audioReactivity": 0.0,
        },
        "mild_datamosh": {
            "displacementStrength": 3.0, "motionStrength": 2.0,
            "loopEnable": 0.0, "loopMix": 0.0,
            "blockCorruption": 3.0, "iframeLoss": 2.0,
            "feedbackAmount": 0.3, "feedbackDecay": 0.8,
            "colorQuantization": 2.0, "scanlineIntensity": 1.0,
            "depthComposite": 3.0, "audioReactivity": 3.0,
        },
        "full_corruption": {
            "displacementStrength": 8.0, "motionStrength": 6.0,
            "loopEnable": 1.0, "loopMix": 7.0,
            "blockCorruption": 8.0, "iframeLoss": 6.0,
            "feedbackAmount": 0.8, "feedbackDecay": 0.7,
            "colorQuantization": 6.0, "scanlineIntensity": 5.0,
            "depthComposite": 8.0, "audioReactivity": 8.0,
        },
        "loop_injector": {
            "displacementStrength": 5.0, "motionStrength": 3.0,
            "loopEnable": 1.0, "loopMix": 5.0,  # 50% wet
            "blockCorruption": 5.0, "iframeLoss": 3.0,
            "feedbackAmount": 0.5, "feedbackDecay": 0.9,
            "colorQuantization": 3.0, "scanlineIntensity": 2.0,
            "depthComposite": 5.0, "audioReactivity": 5.0,
        },
    }
    ```

12. **Testing**: Test each stage independently:
    - Set all corruption to 0, enable displacement → see depth-based warping
    - Enable block corruption → see block artifacts
    - Enable feedback → see recursive blur/trail
    - Enable color quantization → see posterization
    - Enable scanlines → see line artifacts
    - Enable loop and provide return → see external effect baked in
    - Vary depth composite → near vs far corruption difference

13. **Performance**: The shader does a lot. Consider:
    - Early exits for disabled effects
    - Using `#define` to compile out unused features
    - Reducing block size for faster corruption (larger blocks = fewer iterations)
    - Simplifying scanline effect

14. **Future Extensions**:
    - Add multiple loop points (like P3-VD54)
    - Add per-corruption-method audio reactivity controls
    - Add preset system with more options
    - Add ability to save/load custom corruption chains

---

## Easter Egg Idea

When `displacementStrength` is set exactly to 6.66, `blockCorruption` to exactly 6.66, `feedbackAmount` to exactly 0.666, `colorQuantization` to exactly 6.66, `scanlineIntensity` to exactly 6.66, `depthComposite` to exactly 6.66, and the loop return contains a perfect mandala, the datamosh enters a "sacred corruption" state where the block artifacts align into a perfect 6.66 Hz pulsing pattern, the feedback creates a self-similar fractal, and the depth composite causes the corruption to radiate from the center in concentric waves that match the mandala's geometry. VJs describe this as "watching the universe datamosh itself into existence."

---

## References

- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- I-frames: https://en.wikipedia.org/wiki/Video_compression_picture_types
- Temporal feedback: https://en.wikipedia.org/wiki/Feedback
- Color quantization: https://en.wikipedia.org/wiki/Color_quantization
- Scanlines: https://en.wikipedia.org/wiki/Scanline
- VJLive legacy: `plugins/vdepth/depth_modular_datamosh.py`

---

## Implementation Tips

1. **Shader Optimization**: The shader will be large. Use:
   ```glsl
   #ifdef BLOCK_CORRUPTION
   // block corruption code
   #endif
   ```
   And compile with defines based on enabled features.

2. **Block Corruption Algorithm**:
   ```glsl
   vec2 block_uv = floor(uv * resolution / block_size) * block_size / resolution;
   float r = random(block_uv + floor(time * 10.0));
   if (r < blockCorruption * 0.1) {
       // Shift this block
       vec2 offset = (vec2(random(block_uv), random(block_uv + 1.0)) - 0.5) * block_size / resolution * 2.0;
       color = texture(tex0, block_uv + offset);
   }
   ```

3. **I-Frame Loss**: To simulate I-frame loss, you need to freeze blocks for multiple frames. Store a "freeze until" timestamp per block in a separate texture or uniform buffer. Simpler: just skip updating some blocks (they'll persist from previous frame via feedback).

4. **Scanline Corruption**:
   ```glsl
   float line_y = floor(uv.y * resolution.y);
   float line_r = random(vec2(uv.x, line_y / 10.0));  // Coherent per line
   if (line_r < scanlineIntensity * 0.05) {
       // Drop line (copy from above or below)
       float offset = 1.0 / resolution.y;
       color = texture(tex0, uv + vec2(0.0, offset));
   }
   ```

5. **Color Quantization**:
   ```glsl
   float levels = exp2(8.0 - colorQuantization * 0.5);  // 256 down to 4
   color.rgb = floor(color.rgb * levels) / levels;
   ```

6. **Depth Composite**:
   ```glsl
   float depth_weight = mix(1.0, depth, depthComposite * 0.1);
   // depth_weight = 1.0 means full corruption, 0.0 means original
   color.rgb = mix(looped.rgb, corrupted.rgb, depth_weight);
   ```

7. **Audio Reactivity**: Pass audio level as uniform each frame:
   ```python
   audio = audio_reactor.get_level() if audio_reactor else 0.0
   shader.set_uniform('audio_level', audio)
   ```

8. **Process Frame**:
   ```python
   def process_frame(self, frame, loop_return=None):
       h, w = frame.shape[:2]
       self._ensure_resources(w, h)
       
       # Upload depth
       self._upload_depth_texture()
       
       # Create textures
       frame_tex = self._texture_from_array(frame)
       loop_ret_tex = self._texture_from_array(loop_return) if loop_return is not None else 0
       
       # Render to framebuffer
       glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
       
       self.shader.use()
       self._apply_uniforms(time, (w, h), audio_reactor)
       
       # Bind textures
       glActiveTexture(GL_TEXTURE0)
       glBindTexture(GL_TEXTURE_2D, frame_tex)
       self.shader.set_uniform("tex0", 0)
       
       glActiveTexture(GL_TEXTURE1)
       glBindTexture(GL_TEXTURE_2D, self.depth_texture)
       self.shader.set_uniform("depth_tex", 1)
       
       glActiveTexture(GL_TEXTURE2)
       glBindTexture(GL_TEXTURE_2D, self.prev_tex[self.current_prev])
       self.shader.set_uniform("texPrev", 2)
       
       if loop_ret_tex:
           glActiveTexture(GL_TEXTURE3)
           glBindTexture(GL_TEXTURE_2D, loop_ret_tex)
           self.shader.set_uniform("texLoopRet", 3)
       
       # Draw fullscreen quad
       draw_fullscreen_quad()
       
       glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       # Read result
       result = self._read_pixels()
       
       # Store in previous texture for next frame
       self._copy_to_texture(result, self.prev_tex[1 - self.current_prev])
       self.current_prev = 1 - self.current_prev
       
       return result
   ```

9. **Loop Enable Logic**: In shader:
   ```glsl
   float loop_on = step(0.5, loopEnable);  // 0 or 1
   vec4 after_loop = mix(stage1_output, loop_return, loopMix * loop_on);
   ```

10. **Audio Reactivity Mapping**:
    ```glsl
    float audio_mod = 1.0 + audioReactivity * audio_level * 0.5;  // 1.0 to 1.5x
    float block_strength = blockCorruption * audio_mod;
    // etc.
    ```

11. **Testing with External Effects**: Create a simple external effect (e.g., invert colors) and route it through the loop. Verify that the inversion gets baked into the datamosh corruption.

12. **Performance**: The effect is moderately heavy. If all corruption methods are enabled, it could be 10-15 ms. Consider:
    - Using `mediump` precision
    - Reducing texture fetches
    - Early-out for low corruption values

---

## Conclusion

The DepthModularDatamoshEffect revolutionizes datamosh by making it modular. With an explicit loop point between depth displacement and corruption stages, it allows external effects to be baked directly into the datamosh algorithm. This creates unique compound effects where your color grading, distortion, or other processing becomes part of the corruption itself. Combined with audio reactivity and depth-weighted composite, it's a powerful tool for creating organic, responsive datamosh in VJ performances.

---
>>>>>>> REPLACE