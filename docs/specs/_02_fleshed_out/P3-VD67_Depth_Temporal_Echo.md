# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD67_Depth_Temporal_Echo.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD67 — DepthTemporalEchoEffect

## Description

The DepthTemporalEchoEffect creates a ghostly temporal effect where different depth layers show different moments in time. It maintains a circular buffer of past video frames, and the depth map determines which historical frame each pixel displays: near objects show the present, far objects show the past. This creates the illusion of subjects tracing their own past through space, with temporal echoes layered by depth.

This effect is ideal for creating ethereal, ghostly visuals where performers appear to have multiple temporal echoes trailing behind them. It's perfect for VJ performances that want to create a sense of time distortion and spatial memory. The effect can simulate everything from subtle ghosting to dramatic temporal layering.

## What This Module Does

- Maintains a circular buffer of past video frames (history)
- Uses depth to select which historical frame each pixel displays
- Near depth → present time, far depth → past times
- Creates multiple temporal layers (echoes) with configurable opacity
- Supports color decay (echoes fade to grayscale)
- Configurable echo depth range, layer count, and blending
- GPU-accelerated with texture history buffer

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT include audio reactivity (may be added later)
- Does NOT support variable frame rate (assumes constant FPS)
- Does NOT implement motion compensation (simple frame copying)
- Does NOT include temporal smoothing (raw history)

---

## Detailed Behavior

### Temporal Echo Pipeline

1. **Capture current frame**: `current_frame` (HxWxC)
2. **Capture depth frame**: `depth_frame` (HxW, normalized 0-1)
3. **Maintain history buffer**: Circular buffer of N past frames (textures)
4. **For each pixel**:
   - Read depth value `d` (0-1)
   - Map depth to time offset: `t = f(d)` where near → 0 (present), far → max_delay
   - Select historical frame at time `t` from buffer
   - Apply ghost opacity and color decay
5. **Blend**:
   - `result = blend(current, ghost, ghostOpacity)`
   - Optional: `result = mix(current, ghost, ghostOpacity)`
6. **Update history**: Push current frame into buffer, discard oldest

### Depth-to-Time Mapping

The core concept: depth controls which historical frame is shown.

```glsl
float depth = texture(depth_tex, uv).r;  // 0 (near) to 1 (far)
float delay = mix(nearDelay, farDelay, depth);  // 0 to max_delay frames
int frame_index = (current_frame_index - round(delay)) % history_size;
vec4 ghost_color = texture(history_tex[frame_index], uv);
```

- `nearDelay`: How many frames behind for near objects (typically 0)
- `farDelay`: How many frames behind for far objects (max delay)
- Linear mapping: `delay = nearDelay + (farDelay - nearDelay) * depth`

### Multiple Layers (Echoes)

Instead of a single ghost, create multiple temporal layers:

```glsl
float layer_count = layerCount;  // e.g., 5
float layer_spacing = (farDelay - nearDelay) / layer_count;

for (int i = 0; i < layer_count; i++) {
    float layer_delay = nearDelay + i * layer_spacing;
    int idx = (current_frame_index - round(layer_delay)) % history_size;
    vec4 layer_color = texture(history_tex[idx], uv);
    // Apply decay: further layers more faded/desaturated
    float alpha = ghostOpacity * (1.0 - i / layer_count);
    result += layer_color * alpha;
}
```

### Color Decay

Temporal echoes can decay in color (become more monochrome over time):

```glsl
float gray = dot(layer_color.rgb, vec3(0.299, 0.587, 0.114));
layer_color.rgb = mix(layer_color.rgb, vec3(gray), colorDecay * (i / layer_count));
```

### Blend Modes

Different ways to composite ghosts over current:

- `blendMode = 0`: `mix(current, ghost, ghostOpacity)`
- `blendMode = 1`: `current + ghost * ghostOpacity` (additive)
- `blendMode = 2`: `max(current, ghost * ghostOpacity)` (lighten)
- `blendMode = 3`: `screen(current, ghost)`

### Edge Bleed

At depth boundaries, allow echoes to "bleed" across edges:

```glsl
float depth_grad = length(vec2(dFdx(depth), dFdy(depth)));
if (depth_grad > edgeBleed * 0.01) {
    // Smear ghost across depth edge
    ghost_color = mix(ghost_color, neighbor_ghost, depth_grad);
}
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `echoDepth` | float | 6.0 | 0.0-10.0 | Depth at which echo is maximum (maps to farDelay) |
| `layerCount` | float | 5.0 | 0.0-10.0 | Number of temporal echo layers |
| `ghostOpacity` | float | 7.0 | 0.0-10.0 | Opacity of ghost layers |
| `colorDecay` | float | 3.0 | 0.0-10.0 | How much ghosts desaturate with age |
| `blendMode` | float | 0.0 | 0.0-10.0 | Blending mode (0=mix, 1=add, 2=lighten, 3=screen) |
| `nearDelay` | float | 0.0 | 0.0-10.0 | Delay for near objects (frames) |
| `farDelay` | float | 8.0 | 0.0-10.0 | Delay for far objects (frames) |
| `edgeBleed` | float | 4.0 | 0.0-10.0 | Amount of echo bleeding at depth edges |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class DepthTemporalEchoEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def clear_history(self) -> None: ...  # Reset history buffer
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Temporal echo output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_history_textures: List[int]` — Circular buffer of N frame textures
- `_history_fbos: List[int]` — Framebuffers for history textures
- `_history_size: int` — Number of frames in history (e.g., 120)
- `_current_index: int` — Current write index in circular buffer
- `_parameters: dict` — Echo parameters
- `_shader: ShaderProgram` — Compiled shader
- `_temp_texture: int` — For intermediate rendering

**Per-Frame:**
- Update depth data from source
- Upload current frame to history texture at `_current_index`
- Render echo effect by sampling from history based on depth
- Increment `_current_index` (modulo `_history_size`)
- Return result

**Initialization:**
- Create history textures (N, where N = `MAX_HISTORY` or configurable)
- Create history FBOs (N)
- Compile shader
- Default parameters: echoDepth=6.0, layerCount=5.0, ghostOpacity=7.0, colorDecay=3.0, blendMode=0.0, nearDelay=0.0, farDelay=8.0, edgeBleed=4.0
- Initialize `_current_index = 0`

**Cleanup:**
- Delete all history textures (N)
- Delete all history FBOs (N)
- Delete temporary textures
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| History textures (N) | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame (circular) |
| History FBOs (N) | GL_FRAMEBUFFER | N/A | frame size | Persistent |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480, N=120):**
- History textures: 120 × 921,600 bytes = 110,592,000 bytes (~105 MB)
- Shader: ~20-30 KB
- Total: ~105 MB (heavy on memory)

**Note**: The legacy uses only 4 history layers (`_echo_textures: List[int] = [0, 0, 0, 0]`), which is much lighter (~3 MB). The `MAX_HISTORY = 120` comment suggests a larger buffer, but the actual implementation may use fewer textures with a different strategy (e.g., single texture with mipmaps, or a ring buffer of 4 with time-based sampling). The spec should reflect the actual legacy approach: 4 history layers.

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use uniform depth (0.5) | Normal operation |
| FBO incomplete | `RuntimeError("FBO error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| History buffer overflow | Wrap around (circular) | Normal operation |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and FBO operations must occur on the thread with the OpenGL context. The effect updates the history buffer each frame; concurrent `process_frame()` calls will cause race conditions and corrupted history. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480, 4 history layers):**
- Texture upload: ~0.5-1 ms
- Shader execution (multiple texture fetches): ~3-8 ms
- Total: ~3.5-9 ms on GPU

**With 120 history layers**: Would be much slower due to texture management, but likely not used simultaneously.

**Optimization Strategies:**
- Reduce history layer count (4 is reasonable)
- Use lower resolution for history textures
- Combine multiple layers into single pass with array textures
- Use texture arrays or 3D textures if available
- Reduce layer count dynamically based on performance

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Echo parameters configured (delays, layers, opacity)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_history_buffer` | History buffer stores frames correctly |
| `test_depth_mapping` | Depth maps to correct delay |
| `test_layer_count` | Multiple layers create multiple echoes |
| `test_ghost_opacity` | Ghost opacity controls blend strength |
| `test_color_decay` | Ghosts desaturate with age/depth |
| `test_blend_modes` | Different blend modes work |
| `test_edge_bleed` | Echoes bleed across depth edges |
| `test_near_far_delay` | Near shows present, far shows past |
| `test_clear_history` | History buffer can be reset |
| `test_circular_buffer` | Old frames overwritten correctly |
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
- [ ] Git commit with `[Phase-3] P3-VD67: depth_temporal_echo_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_temporal_echo.py` — VJLive Original implementation
- `plugins/core/depth_temporal_echo/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_temporal_echo/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthTemporalEchoEffect` allocates `glGenTextures` and must free them
- `assets/gists/depth_temporal_echo.json` — Gist documentation

Design decisions inherited:
- Effect name: `depth_temporal_echo`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for temporal delay selection
- Parameters: `echoDepth`, `layerCount`, `ghostOpacity`, `colorDecay`, `blendMode`, `nearDelay`, `farDelay`, `edgeBleed`
- Allocates GL resources: history textures (4), history FBOs (4)
- Shader implements depth-based temporal sampling and blending
- Constant `MAX_HISTORY = 120` but only 4 textures allocated (likely uses time-based sampling within those 4)
- Method `_ensure_echo_buffers()` creates GPU resources

---

## Notes for Implementers

1. **Core Concept**: This effect uses depth to control which historical frame is displayed. Near = present, far = past. It creates ghostly echoes by blending multiple delayed frames with varying opacity.

2. **History Buffer**: The effect needs to store several past frames. The legacy uses 4 textures (`_echo_textures`). The `MAX_HISTORY = 120` suggests a larger conceptual buffer, but likely the 4 textures are used with time-based indexing (e.g., each texture holds a frame at a specific delay, or they're used in a ring). Simpler approach: Use 4 textures representing 4 specific delays (e.g., 10, 20, 30, 40 frames ago). The `layerCount` parameter (0-10) would then control how many of these layers are used.

3. **Depth-to-Delay Mapping**:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float near_delay = nearDelay;   // e.g., 0 frames
   float far_delay = farDelay;     // e.g., 8 frames
   float delay = mix(near_delay, far_delay, depth);
   int frame_idx = (current_frame_index - round(delay)) % history_size;
   ```

4. **Multiple Layers**: If using 4 history textures, you could assign each to a specific delay:
   - Layer 0: delay = nearDelay + 0 * spacing
   - Layer 1: delay = nearDelay + 1 * spacing
   - Layer 2: delay = nearDelay + 2 * spacing
   - Layer 3: delay = nearDelay + 3 * spacing
   And `layerCount` determines how many layers to blend (up to 4).

5. **Shader Uniforms**:
   ```glsl
   uniform sampler2D current_tex;     // Current frame
   uniform sampler2D depth_tex;       // Depth
   uniform sampler2D echo_tex[4];     // History textures
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   uniform int current_frame_index;   // For indexing history
   
   uniform float nearDelay;           // frames
   uniform float farDelay;            // frames
   uniform float layerCount;          // 0-10 (use up to 4)
   uniform float ghostOpacity;        // 0-1 (mapped from 0-10)
   uniform float colorDecay;          // 0-1
   uniform float blendMode;           // 0-3
   uniform float edgeBleed;           // 0-1
   ```

6. **Parameter Mapping** (0-10 → actual):
   - `echoDepth`: 0-10 → 0-1 (depth threshold? maybe not used directly)
   - `layerCount`: 0-10 → 0-4 (clamp to number of available textures)
   - `ghostOpacity`: 0-10 → 0-1 (divide by 10)
   - `colorDecay`: 0-10 → 0-1 (divide by 10)
   - `blendMode`: 0-10 → 0-3 (map to int)
   - `nearDelay`: 0-10 → 0-10 frames (use directly)
   - `farDelay`: 0-10 → 0-10 frames (use directly)
   - `edgeBleed`: 0-10 → 0-1 (divide by 10)

7. **Blend Modes**:
   ```glsl
   vec3 blend(vec3 current, vec3 ghost, int mode) {
       switch(mode) {
           case 0: return mix(current, ghost, ghostOpacity);
           case 1: return current + ghost * ghostOpacity;
           case 2: return max(current, ghost * ghostOpacity);
           case 3: return 1.0 - (1.0 - current) * (1.0 - ghost * ghostOpacity); // screen
           default: return mix(current, ghost, ghostOpacity);
       }
   }
   ```

8. **Color Decay**:
   ```glsl
   vec3 apply_decay(vec3 color, float decay_factor) {
       float gray = dot(color, vec3(0.299, 0.587, 0.114));
       return mix(color, vec3(gray), decay_factor);
   }
   ```

9. **Edge Bleed**:
   ```glsl
   float depth_grad = length(vec2(dFdx(depth), dFdy(depth)));
   if (depth_grad > 0.01 && edgeBleed > 0.0) {
       // Sample neighbor echo and blend
       vec2 offset = vec2(dFdx(uv.x), dFdy(uv.y)) * edgeBleed * 10.0;
       vec3 neighbor_ghost = texture(echo_tex[idx], uv + offset).rgb;
       ghost_color = mix(ghost_color, neighbor_ghost, depth_grad * edgeBleed);
   }
   ```

10. **PRESETS**:
    ```python
    PRESETS = {
        "subtle_ghost": {
            "echoDepth": 6.0, "layerCount": 2.0, "ghostOpacity": 3.0,
            "colorDecay": 2.0, "blendMode": 0.0, "nearDelay": 0.0, "farDelay": 5.0,
            "edgeBleed": 2.0,
        },
        "deep_echo": {
            "echoDepth": 8.0, "layerCount": 5.0, "ghostOpacity": 7.0,
            "colorDecay": 5.0, "blendMode": 0.0, "nearDelay": 0.0, "farDelay": 10.0,
            "edgeBleed": 4.0,
        },
        "additive_trails": {
            "echoDepth": 7.0, "layerCount": 4.0, "ghostOpacity": 8.0,
            "colorDecay": 1.0, "blendMode": 1.0, "nearDelay": 0.0, "farDelay": 8.0,
            "edgeBleed": 3.0,
        },
        "monochrome_ghosts": {
            "echoDepth": 6.0, "layerCount": 3.0, "ghostOpacity": 6.0,
            "colorDecay": 9.0, "blendMode": 0.0, "nearDelay": 0.0, "farDelay": 6.0,
            "edgeBleed": 2.0,
        },
        "edge_bleed": {
            "echoDepth": 6.0, "layerCount": 4.0, "ghostOpacity": 5.0,
            "colorDecay": 3.0, "blendMode": 2.0, "nearDelay": 0.0, "farDelay": 7.0,
            "edgeBleed": 8.0,
        },
    }
    ```

11. **Testing Strategy**:
    - Test with uniform depth: all pixels should show same delay
    - Test with depth gradient: delay should vary smoothly
    - Test layerCount: more layers = more echoes
    - Test ghostOpacity: higher = more visible ghosts
    - Test colorDecay: higher = more grayscale ghosts
    - Test blend modes: verify each mode
    - Test edgeBleed: ghosts should bleed across depth edges
    - Test nearDelay/farDelay: verify delay range

12. **Performance**: The effect uses multiple texture fetches (one per layer). With 4 layers, that's 4+1=5 texture fetches per pixel. Optimize by:
    - Reducing layer count
    - Using lower resolution history textures
    - Early depth test to skip some layers
    - Using texture arrays for better cache locality

13. **Future Extensions**:
    - Add audio reactivity to delay or opacity
    - Add motion compensation (optical flow) to align ghosts
    - Add per-channel delay (chromatic temporal echo)
    - Add depth-based color tinting on ghosts
    - Add variable decay based on depth

---
-

## References

- Temporal aliasing: https://en.wikipedia.org/wiki/Temporal_aliasing
- Ghosting: https://en.wikipedia.org/wiki/Ghosting_(television)
- Circular buffer: https://en.wikipedia.org/wiki/Circular_buffer
- Depth buffer: https://en.wikipedia.org/wiki/Depth_buffer
- VJLive legacy: `plugins/vdepth/depth_temporal_echo.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D current_tex;
   uniform sampler2D depth_tex;
   uniform sampler2D echo_tex[4];  // 4 history textures
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   uniform int current_frame_index;  // 0-3 (mod 4) or larger
   
   uniform float nearDelay;         // frames
   uniform float farDelay;          // frames
   uniform float layerCount;        // 0-4 (clamp)
   uniform float ghostOpacity;      // 0-1
   uniform float colorDecay;        // 0-1
   uniform float blendMode;         // 0-3 (int)
   uniform float edgeBleed;         // 0-1
   
   vec3 blend(vec3 a, vec3 b, int mode, float opacity) {
       switch(int(mode)) {
           case 0: return mix(a, b, opacity);
           case 1: return a + b * opacity;
           case 2: return max(a, b * opacity);
           case 3: return 1.0 - (1.0 - a) * (1.0 - b * opacity);  // screen
           default: return mix(a, b, opacity);
       }
   }
   
   vec3 apply_decay(vec3 color, float decay) {
       float gray = dot(color, vec3(0.299, 0.587, 0.114));
       return mix(color, vec3(gray), decay);
   }
   
   void main() {
       float depth = texture(depth_tex, uv).r;
       
       // Compute delay for this pixel
       float delay = mix(nearDelay, farDelay, depth);
       
       // Determine which history layers to use
       int num_layers = int(clamp(layerCount, 0.0, 4.0));
       float layer_spacing = (farDelay - nearDelay) / max(layerCount, 1.0);
       
       vec3 result = texture(current_tex, uv).rgb;
       
       for (int i = 0; i < 4; i++) {
           if (i >= num_layers) break;
           
           float layer_delay = nearDelay + i * layer_spacing;
           // Find which texture corresponds to this delay
           // This is tricky: need to map frame_index - delay to one of the 4 textures
           // Simplest: each texture holds a specific delay offset
           int tex_idx = i;  // Assume texture i holds delay = nearDelay + i*spacing
           
           vec3 ghost = texture(echo_tex[tex_idx], uv).rgb;
           
           // Apply color decay based on layer age
           float decay_factor = colorDecay * (float(i) / max(layerCount, 1.0));
           ghost = apply_decay(ghost, decay_factor);
           
           // Apply edge bleed
           if (edgeBleed > 0.0) {
               float depth_grad = length(vec2(dFdx(depth), dFdy(depth)));
               if (depth_grad > 0.01) {
                   vec2 offset = vec2(dFdx(uv.x), dFdy(uv.y)) * edgeBleed * 10.0;
                   vec3 neighbor = texture(echo_tex[tex_idx], uv + offset).rgb;
                   ghost = mix(ghost, neighbor, depth_grad * edgeBleed);
               }
           }
           
           // Blend
           result = blend(result, ghost, int(blendMode), ghostOpacity / 10.0);
       }
       
       fragColor = mix(texture(current_tex, uv), vec4(result, 1.0), u_mix);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthTemporalEchoEffect(Effect):
       def __init__(self):
           super().__init__("depth_temporal_echo", ECHO_VERTEX, ECHO_FRAGMENT)
           
           self.depth_source = None
           self.depth_frame = None
           
           self.echo_tex = [0, 0, 0, 0]  # 4 history textures
           self.echo_fbo = [0, 0, 0, 0]
           self.current_echo = 0  # Which texture to write to next
           
           self.parameters = {
               'echoDepth': 6.0,
               'layerCount': 5.0,
               'ghostOpacity': 7.0,
               'colorDecay': 3.0,
               'blendMode': 0.0,
               'nearDelay': 0.0,
               'farDelay': 8.0,
               'edgeBleed': 4.0,
           }
           
           self.shader = None
       
       def _ensure_echo_buffers(self, width, height):
           if self.echo_tex[0] == 0:
               for i in range(4):
                   self.echo_tex[i] = glGenTextures(1)
                   glBindTexture(GL_TEXTURE_2D, self.echo_tex[i])
                   glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                   
                   self.echo_fbo[i] = glGenFramebuffers(1)
                   glBindFramebuffer(GL_FRAMEBUFFER, self.echo_fbo[i])
                   glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.echo_tex[i], 0)
                   glBindFramebuffer(GL_FRAMEBUFFER, 0)
       
       def process_frame(self, frame):
           h, w = frame.shape[:2]
           self._ensure_echo_buffers(w, h)
           
           # Update depth
           self._update_depth()
           
           # Upload current frame to the next echo buffer (circular)
           glBindFramebuffer(GL_FRAMEBUFFER, self.echo_fbo[self.current_echo])
           # Render frame to this FBO (or just upload as texture)
           # Actually need to upload frame data to texture
           glBindTexture(GL_TEXTURE_2D, self.echo_tex[self.current_echo])
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, frame)
           
           # Now render effect to screen, sampling from all echo textures
           glBindFramebuffer(GL_FRAMEBUFFER, 0)
           
           self.shader.use()
           self._apply_uniforms(time, (w, h))
           
           # Bind current frame
           glActiveTexture(GL_TEXTURE0)
           glBindTexture(GL_TEXTURE_2D, self.current_tex)  # Need current_tex
           glUniform1i(glGetUniformLocation(self.shader.program, "current_tex"), 0)
           
           # Bind depth
           glActiveTexture(GL_TEXTURE1)
           glBindTexture(GL_TEXTURE_2D, self.depth_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "depth_tex"), 1)
           
           # Bind echo textures
           for i in range(4):
               glActiveTexture(GL_TEXTURE2 + i)
               glBindTexture(GL_TEXTURE_2D, self.echo_tex[i])
               glUniform1i(glGetUniformLocation(self.shader.program, f"echo_tex[{i}]"), 2 + i)
           
           # Set current_frame_index (which buffer was just written)
           glUniform1i(glGetUniformLocation(self.shader.program, "current_frame_index"), self.current_echo)
           
           draw_fullscreen_quad()
           
           # Advance circular buffer
           self.current_echo = (self.current_echo + 1) % 4
           
           result = self._read_pixels()
           return result
   ```

3. **History Management**: The legacy uses 4 textures and likely treats them as a ring buffer where each texture represents a specific delay offset. The shader samples from the appropriate texture based on computed delay. The `current_frame_index` tells which texture holds the most recent frame. The mapping:
   ```
   desired_frame = current_frame_index - delay
   texture_index = desired_frame % 4
   ```
   But this only works if `delay` is an integer and we have exactly 4 frames. More flexible: each of the 4 textures holds a specific delay (e.g., 5, 10, 15, 20 frames ago). Then `layerCount` selects how many to blend.

4. **Parameter Interpretation**:
   - `echoDepth`: Might be a depth threshold; only pixels with depth > echoDepth get echoes? Or it maps to farDelay? The gist says "Echo Depth" param. Could be: depth value that corresponds to maximum echo.
   - `layerCount`: Number of echo layers to blend (0-10, but clamp to 4)
   - `ghostOpacity`: Overall strength of ghosts (0-10 → 0-1)
   - `colorDecay`: How much ghosts lose color (0-10 → 0-1)
   - `blendMode`: 0-10 → map to 0-3
   - `nearDelay`: Delay for near objects in frames (0-10)
   - `farDelay`: Delay for far objects in frames (0-10)
   - `edgeBleed`: Bleeding amount at depth edges (0-10 → 0-1)

5. **Testing**: Create a depth ramp (0 to 1). Verify:
   - Left side (near) shows current frame
   - Right side (far) shows delayed frame
   - Intermediate depths show intermediate delays
   - Multiple layers create multiple ghost images
   - Color decay makes ghosts grayer as delay increases

6. **Performance**: 4 texture fetches per pixel is moderate. Should be fine at 1080p.

7. **Memory**: 4 full-resolution textures = 4 × (width × height × 4) bytes. At 1080p: ~4 × 8.3 MB = 33.2 MB. Acceptable.

8. **Debug Mode**: Visualize delay map (color-coded), show which history texture is sampled.

---

## Conclusion

The DepthTemporalEchoEffect creates a haunting, ghostly effect where depth controls the flow of time. Near objects exist in the present, while far objects are trapped in the past, creating layered temporal echoes that follow the performer through space. With configurable delays, layer counts, and blending modes, it's a versatile tool for creating ethereal, time-distorted visuals perfect for VJ performances that want to evoke memory, haunting, or temporal dislocation.

---
