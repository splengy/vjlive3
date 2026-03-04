# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD56_Depth_Modulated_Datamosh.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD56 — DepthModulatedDatamoshEffect

## Description

The DepthModulatedDatamoshEffect applies datamosh corruption where the intensity of corruption is modulated by depth. Unlike uniform datamosh that corrupts the entire image equally, this effect uses depth data to control where and how much corruption occurs. Near objects can be preserved while far objects are heavily corrupted, or vice versa. The effect includes configurable depth range, corruption intensity, thresholding, and modulation strength.

This effect is ideal for creating depth-aware glitch art where the corruption respects the scene's depth structure. It's perfect for VJ performances that need selective datamosh—corrupting backgrounds while keeping performers sharp, or creating depth-based reveal effects. The modulation can be linear, exponential, or stepped based on depth.

## What This Module Does

- Applies datamosh corruption (block shifting, I-frame loss, color quantization)
- Modulates corruption intensity based on depth values
- Configurable depth range (min/max) for modulation
- Adjustable corruption intensity and threshold
- Supports multiple modulation curves (linear, exponential, stepped)
- GPU-accelerated fragment shader
- Audio reactivity optional

## What This Module Does NOT Do

- Does NOT provide multiple loop points (single-stage corruption)
- Does NOT include external effect routing (self-contained)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT implement temporal feedback (single frame corruption)
- Does NOT include audio reactivity by default (may be added)

---

## Detailed Behavior

### Depth Modulation Pipeline

1. **Sample depth**: Get depth value `d` from depth texture
2. **Normalize depth**: Map depth to 0-1 range based on `min_depth` and `max_depth`:
   ```
   d_norm = clamp((d - min_depth) / (max_depth - min_depth), 0.0, 1.0)
   ```
3. **Compute modulation factor**: Apply modulation curve to depth:
   - Linear: `mod = d_norm`
   - Exponential: `mod = pow(d_norm, modulation_strength)`
   - Stepped: `mod = floor(d_norm * steps) / steps`
4. **Apply corruption**: Corruption intensity = `base_intensity * mod`
5. **Render corrupted frame**: Apply datamosh effects with computed intensity

### Corruption Methods

The effect can include one or more datamosh methods:

- **Block corruption**: Shift blocks based on corruption intensity
- **I-frame loss**: Freeze blocks (simulate missing I-frames)
- **Color quantization**: Reduce color bit depth
- **Scanline corruption**: Drop or corrupt scanlines
- **Channel shifting**: Offset RGB channels differently

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `intensity` | float | 5.0 | 0.0-10.0 | Base corruption intensity |
| `threshold` | float | 0.5 | 0.0-1.0 | Depth threshold for modulation |
| `modulationStrength` | float | 1.0 | 0.1-5.0 | How strongly depth modulates corruption |
| `minDepth` | float | 0.3 | 0.0-10.0 | Minimum depth for modulation range |
| `maxDepth` | float | 4.0 | 0.0-10.0 | Maximum depth for modulation range |
| `modulationCurve` | int | 0 | 0-2 | 0=linear, 1=exponential, 2=stepped |
| `steps` | float | 4.0 | 2.0-10.0 | Number of steps for stepped curve |
| `blockSize` | float | 8.0 | 2.0-20.0 | Size of corruption blocks |
| `colorQuantization` | float | 0.0 | 0.0-10.0 | Color bit depth reduction |
| `scanlineIntensity` | float | 0.0 | 0.0-10.0 | Scanline corruption strength |
| `channelShift` | float | 0.0 | 0.0-10.0 | RGB channel separation |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthModulatedDatamoshEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Datamosh output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_parameters: dict` — Modulation and corruption parameters
- `_shader: ShaderProgram` — Compiled shader

**Per-Frame:**
- Update depth data from source
- Upload depth texture
- Set shader uniforms
- Render corrupted frame
- Return result

**Initialization:**
- Create depth texture (lazy)
- Compile shader
- Default parameters: intensity=5.0, threshold=0.5, modulationStrength=1.0, minDepth=0.3, maxDepth=4.0, modulationCurve=0, steps=4.0, blockSize=8.0, colorQuantization=0.0, scanlineIntensity=0.0, channelShift=0.0

**Cleanup:**
- Delete depth texture
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Depth texture: 307,200 bytes
- Shader: ~20-40 KB
- Total: ~0.3-0.4 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Use uniform depth (0.5) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and texture updates must occur on the thread with the OpenGL context. The depth texture is updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Shader execution (corruption + modulation): ~3-7 ms
- Total: ~3.5-8 ms on GPU

**Optimization Strategies:**
- Disable unused corruption methods (set intensity=0)
- Use simpler shader branches for disabled effects
- Reduce block size for faster corruption (larger blocks = fewer)
- Cache depth texture if depth hasn't changed
- Use compute shader for parallel processing

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Depth range configured (minDepth, maxDepth)
- [ ] Corruption parameters configured (intensity, threshold, modulation)
- [ ] Modulation curve selected
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_depth_normalization` | Depth maps correctly to 0-1 range |
| `test_modulation_linear` | Linear curve: corruption ∝ depth |
| `test_modulation_exponential` | Exponential curve: corruption ∝ depth^strength |
| `test_modulation_stepped` | Stepped curve: corruption in discrete levels |
| `test_depth_range` | Only depths within min/max are modulated |
| `test_threshold` | Threshold cuts off low-depth corruption |
| `test_block_corruption` | Block artifacts appear with intensity |
| `test_color_quantization` | Reduces color depth when enabled |
| `test_scanlines` | Scanline corruption adds line artifacts |
| `test_channel_shift` | RGB channels separate based on depth |
| `test_process_frame_no_depth` | Falls back to uniform corruption |
| `test_process_frame_with_depth` | Corruption modulated by depth |
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
- [ ] Git commit with `[Phase-3] P3-VD56: depth_modulated_datamosh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/depth_modulated_datamosh.py` — VJLive Original implementation (VJlive-2)
- `plugins/vdepth/depth_modulated_datamosh.py` — VJLive Original implementation
- `gl_leaks.txt` — Shows `DepthModulatedDatamoshEffect` allocates `glGenTextures` and must free them
- `core/shader_pipeline_verifier.py` — References to uniform requirements and compatibility

Design decisions inherited:
- Effect name: `depth_modulated_datamosh`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for modulation
- Parameters: `intensity`, `threshold`, `modulation_strength`, `min_depth`, `max_depth`, `modulation_curve`, `steps`, plus optional corruption methods
- Allocates GL resources: depth texture
- Shader implements depth-modulated corruption
- Dynamic depth range from camera configuration (`min_depth`, `max_depth`)

---

## Notes for Implementers

1. **Core Concept**: This is a simpler, focused effect compared to P3-VD55 (Modular Datamosh). It's essentially a single-stage datamosh where the corruption intensity is modulated by depth. No loops, no multi-stage pipeline.

2. **Depth Normalization**: Convert raw depth to 0-1 range:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float d_norm = (depth - minDepth) / (maxDepth - minDepth);
   d_norm = clamp(d_norm, 0.0, 1.0);
   ```

3. **Modulation Curves**:
   - **Linear** (0): `mod = d_norm`
   - **Exponential** (1): `mod = pow(d_norm, modulationStrength)`
     - `modulationStrength > 1`: More corruption at far depths
     - `modulationStrength < 1`: More corruption at near depths
   - **Stepped** (2): `mod = floor(d_norm * steps) / steps`
     - Creates discrete corruption levels

4. **Threshold**: Apply a cutoff to modulation:
   ```glsl
   if (d_norm < threshold) {
       mod = 0.0;  // No corruption for shallow depths
   }
   ```

5. **Corruption Intensity**: Final corruption strength:
   ```glsl
   float corruption = intensity * mod * 0.1;  // Scale 0-10 to 0-1
   ```

6. **Block Corruption** (if enabled):
   ```glsl
   if (blockCorruption > 0.0) {
       vec2 block_uv = floor(uv * resolution / blockSize) * blockSize / resolution;
       float r = random(block_uv);
       if (r < corruption) {
           // Shift block
           vec2 offset = (vec2(random(block_uv), random(block_uv+1.0)) - 0.5) * blockSize / resolution;
           color = texture(tex0, block_uv + offset);
       }
   }
   ```

7. **Color Quantization** (if enabled):
   ```glsl
   if (colorQuantization > 0.0) {
       float levels = pow(2.0, 8.0 - colorQuantization * 0.5);  // 256 down to 2
       color.rgb = floor(color.rgb * levels) / levels;
   }
   ```

8. **Scanline Corruption** (if enabled):
   ```glsl
   if (scanlineIntensity > 0.0) {
       float line_y = floor(uv.y * resolution.y);
       float r = random(vec2(uv.x, line_y));
       if (r < scanlineIntensity * 0.05) {
           // Drop line (copy from above)
           color = texture(tex0, uv + vec2(0.0, 1.0/resolution.y));
       }
   }
   ```

9. **Channel Shift** (if enabled):
   ```glsl
   if (channelShift > 0.0) {
       float shift = channelShift * 0.01;
       color.r = texture(tex0, uv + vec2(shift, 0.0)).r;
       color.b = texture(tex0, uv - vec2(shift, 0.0)).b;
   }
   ```

10. **Shader Uniforms**:
    ```glsl
    uniform sampler2D tex0;        // Input frame
    uniform sampler2D depth_tex;   // Depth texture
    uniform vec2 resolution;
    uniform float u_mix;
    
    uniform float intensity;         // 0-10
    uniform float threshold;         // 0-1
    uniform float modulationStrength; // 0.1-5.0
    uniform float minDepth;          // 0-10
    uniform float maxDepth;          // 0-10
    uniform int modulationCurve;     // 0=linear,1=exp,2=stepped
    uniform float steps;             // 2-10
    uniform float blockSize;         // 2-20
    uniform float colorQuantization; // 0-10
    uniform float scanlineIntensity; // 0-10
    uniform float channelShift;      // 0-10
    ```

11. **Parameter Mapping**:
    - `intensity`: 0-10 → corruption multiplier (0.1)
    - `threshold`: 0-1 (already in range)
    - `modulationStrength`: 0.1-5.0 → use directly for pow()
    - `minDepth`, `maxDepth`: 0-10 → use directly (normalized depth)
    - `blockSize`: 2-20 → pixels
    - `colorQuantization`: 0-10 → levels reduction
    - `scanlineIntensity`: 0-10 → probability multiplier (0.05)
    - `channelShift`: 0-10 → pixel offset (0.01 per unit)

12. **Dynamic Depth Range**: The legacy mentions updating depth range from camera config. Provide a method:
    ```python
    def set_depth_range(self, min_depth: float, max_depth: float):
        self.min_depth = min_depth
        self.max_depth = max_depth
    ```

13. **PRESETS**:
    ```python
    PRESETS = {
        "clean": {
            "intensity": 0.0, "threshold": 0.0, "modulationStrength": 1.0,
            "minDepth": 0.0, "maxDepth": 10.0, "modulationCurve": 0,
            "blockSize": 8.0, "colorQuantization": 0.0,
            "scanlineIntensity": 0.0, "channelShift": 0.0,
        },
        "depth_aware_mild": {
            "intensity": 3.0, "threshold": 0.3, "modulationStrength": 1.0,
            "minDepth": 0.5, "maxDepth": 5.0, "modulationCurve": 0,
            "blockSize": 10.0, "colorQuantization": 2.0,
            "scanlineIntensity": 1.0, "channelShift": 1.0,
        },
        "far_corruption": {
            "intensity": 7.0, "threshold": 0.0, "modulationStrength": 2.0,
            "minDepth": 0.0, "maxDepth": 10.0, "modulationCurve": 1,
            "blockSize": 6.0, "colorQuantization": 4.0,
            "scanlineIntensity": 3.0, "channelShift": 3.0,
        },
        "near_corruption": {
            "intensity": 6.0, "threshold": 0.0, "modulationStrength": 0.5,
            "minDepth": 0.0, "maxDepth": 10.0, "modulationCurve": 1,
            "blockSize": 8.0, "colorQuantization": 3.0,
            "scanlineIntensity": 2.0, "channelShift": 2.0,
        },
        "stepped_layers": {
            "intensity": 5.0, "threshold": 0.0, "modulationStrength": 1.0,
            "minDepth": 0.0, "maxDepth": 10.0, "modulationCurve": 2,
            "steps": 4.0, "blockSize": 8.0,
            "colorQuantization": 3.0, "scanlineIntensity": 2.0,
            "channelShift": 2.0,
        },
    }
    ```

14. **Testing Strategy**: Create depth ramps and verify:
    - Linear: corruption increases linearly with depth
    - Exponential: corruption increases exponentially with depth
    - Stepped: corruption jumps at depth thresholds
    - Threshold: depths below threshold get zero corruption
    - Depth range: only depths within range are modulated

15. **Performance**: This is a relatively lightweight effect. Main cost is block corruption (random per block). Optimize by:
    - Using larger blocks (fewer iterations)
    - Early-out if corruption is zero
    - Precomputing random values in texture

16. **Future Extensions**:
    - Add audio reactivity to intensity
    - Add more corruption methods (pixel sort, edge detection)
    - Add depth-based channel shift (different channels at different depths)
    - Add temporal feedback for recursive corruption

---
-

## References

- Datamosh: https://en.wikipedia.org/wiki/Datamosh
- Depth-based effects: https://en.wikipedia.org/wiki/Depth_perception
- Modulation: https://en.wikipedia.org/wiki/Modulation
- VJLive legacy: `plugins/vdepth/depth_modulated_datamosh.py`, `core/effects/depth_modulated_datamosh.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;        // Input frame
   uniform sampler2D depth_tex;   // Depth texture
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   // Parameters
   uniform float intensity;         // 0-10
   uniform float threshold;         // 0-1
   uniform float modulationStrength; // 0.1-5.0
   uniform float minDepth;          // 0-10
   uniform float maxDepth;          // 0-10
   uniform int modulationCurve;     // 0=linear,1=exp,2=stepped
   uniform float steps;             // 2-10
   uniform float blockSize;         // 2-20
   uniform float colorQuantization; // 0-10
   uniform float scanlineIntensity; // 0-10
   uniform float channelShift;      // 0-10
   
   // Random function
   float random(vec2 st) {
       return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
   }
   
   void main() {
       vec4 source = texture(tex0, uv);
       float depth = texture(depth_tex, uv).r;
       
       // Normalize depth to 0-1 range
       float d_norm = (depth - minDepth) / (maxDepth - minDepth);
       d_norm = clamp(d_norm, 0.0, 1.0);
       
       // Apply threshold
       if (d_norm < threshold) {
           d_norm = 0.0;
       }
       
       // Compute modulation factor
       float mod = d_norm;
       if (modulationCurve == 1) {
           // Exponential
           mod = pow(d_norm, modulationStrength);
       } else if (modulationCurve == 2) {
           // Stepped
           mod = floor(d_norm * steps) / steps;
       }
       
       // Final corruption intensity
       float corruption = intensity * mod * 0.1;  // 0-1 range
       
       // Apply corruption to color
       vec4 color = source;
       
       // Block corruption
       if (blockSize > 1.0 && corruption > 0.0) {
           vec2 block_uv = floor(uv * resolution / blockSize) * blockSize / resolution;
           float r = random(block_uv + fract(time * 10.0));
           if (r < corruption) {
               // Shift block
               vec2 offset = (vec2(random(block_uv), random(block_uv + 1.0)) - 0.5) * blockSize / resolution * 2.0;
               color = texture(tex0, block_uv + offset);
           }
       }
       
       // Color quantization
       if (colorQuantization > 0.0) {
           float levels = pow(2.0, 8.0 - colorQuantization * 0.5);
           color.rgb = floor(color.rgb * levels) / levels;
       }
       
       // Scanline corruption
       if (scanlineIntensity > 0.0) {
           float line_y = floor(uv.y * resolution.y);
           float r = random(vec2(uv.x, line_y * 0.1));
           if (r < scanlineIntensity * 0.05) {
               // Drop line (copy from below)
               float offset = 1.0 / resolution.y;
               color = texture(tex0, uv + vec2(0.0, offset));
           }
       }
       
       // Channel shift
       if (channelShift > 0.0) {
           float shift = channelShift * 0.01;
           color.r = texture(tex0, uv + vec2(shift, 0.0)).r;
           color.b = texture(tex0, uv - vec2(shift, 0.0)).b;
       }
       
       // Final mix
       fragColor = mix(source, color, u_mix);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthModulatedDatamoshEffect(Effect):
       def __init__(self):
           super().__init__("depth_modulated_datamosh", DEPTH_MODULATED_FRAGMENT)
           self.depth_source = None
           self.depth_frame = None
           self.depth_texture = 0
           self.parameters = {
               'intensity': 5.0,
               'threshold': 0.5,
               'modulationStrength': 1.0,
               'minDepth': 0.3,
               'maxDepth': 4.0,
               'modulationCurve': 0,
               'steps': 4.0,
               'blockSize': 8.0,
               'colorQuantization': 0.0,
               'scanlineIntensity': 0.0,
               'channelShift': 0.0,
           }
           self.shader = None
           
       def _ensure_resources(self, width, height):
           if self.depth_texture == 0:
               self.depth_texture = glGenTextures(1)
               glBindTexture(GL_TEXTURE_2D, self.depth_texture)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
               
           if self.shader is None:
               self.shader = ShaderProgram(vertex_src, fragment_src)
   ```

3. **Parameter Clamping**:
   ```python
   def set_parameter(self, name, value):
       if name == 'intensity':
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'threshold':
           self.parameters[name] = max(0.0, min(1.0, value))
       elif name == 'modulationStrength':
           self.parameters[name] = max(0.1, min(5.0, value))
       elif name in ('minDepth', 'maxDepth'):
           self.parameters[name] = max(0.0, min(10.0, value))
       elif name == 'modulationCurve':
           self.parameters[name] = max(0, min(2, int(value)))
       elif name == 'steps':
           self.parameters[name] = max(2.0, min(10.0, value))
       elif name == 'blockSize':
           self.parameters[name] = max(2.0, min(20.0, value))
       elif name in ('colorQuantization', 'scanlineIntensity', 'channelShift'):
           self.parameters[name] = max(0.0, min(10.0, value))
   ```

4. **Depth Range Update**: From camera config:
   ```python
   def set_depth_range(self, min_depth, max_depth):
       self.parameters['minDepth'] = min_depth
       self.parameters['maxDepth'] = max_depth
   ```

5. **Process Frame**:
   ```python
   def process_frame(self, frame):
       h, w = frame.shape[:2]
       self._ensure_resources(w, h)
       
       # Upload depth
       self._upload_depth_texture()
       
       # Render
       glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Render to screen
       
       self.shader.use()
       self._apply_uniforms(time, (w, h))
       
       # Bind textures
       glActiveTexture(GL_TEXTURE0)
       glBindTexture(GL_TEXTURE_2D, self._texture_from_array(frame))
       self.shader.set_uniform("tex0", 0)
       
       glActiveTexture(GL_TEXTURE1)
       glBindTexture(GL_TEXTURE_2D, self.depth_texture)
       self.shader.set_uniform("depth_tex", 1)
       
       # Draw fullscreen quad
       draw_fullscreen_quad()
       
       # Read result
       result = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
       
       return result
   ```

6. **Testing**: Create synthetic depth maps:
   - Linear gradient (0 to 1)
   - Step function
   - Circle with radial depth
   Verify corruption matches expected modulation.

7. **Shader Optimization**: Use early returns:
   ```glsl
   if (corruption < 0.01) {
       fragColor = mix(source, source, u_mix);  // No corruption
       return;
   }
   ```

8. **Documentation**: Clearly document the depth range and modulation curve behavior. Provide visual examples of how different settings affect the output.

---

## Conclusion

The DepthModulatedDatamoshEffect provides precise, depth-aware corruption for creating selective glitch effects. By modulating datamosh intensity based on depth, it enables VJs to preserve important foreground elements while corrupting backgrounds, or create depth-based reveal effects. With multiple modulation curves and configurable corruption methods, it's a versatile tool for depth-responsive datamosh.

---
