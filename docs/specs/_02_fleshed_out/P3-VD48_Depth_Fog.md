# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD48_Depth_Fog.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD48 — DepthFogEffect

## Description

The DepthFogEffect creates atmospheric distance fog that fades distant objects into a colored haze, simulating natural atmospheric scattering. The fog density is controlled by depth data, so objects farther from the camera are more heavily fogged. This effect adds depth and atmosphere to scenes, creating a sense of scale and distance.

The effect supports multiple fog modes, height-based fog, animated fog, and light scattering. It's ideal for creating atmospheric perspective, depth enhancement, and mood setting in VJ performances. The fog color, density, start/end distances are all configurable, allowing for anything from subtle haze to dense fog.

## What This Module Does

- Renders depth-based atmospheric fog
- Fades distant objects into a configurable fog color
- Supports linear, exponential, and exponential squared fog modes
- Includes height-based fog (fog density varies with Y coordinate)
- Supports fog animation (swirling, moving fog)
- Implements light scattering (glow in dense fog)
- Uses depth texture to determine per-pixel fog factor
- GPU-accelerated fragment shader

## What This Module Does NOT Do

- Does NOT provide volumetric fog (only screen-space)
- Does NOT support multiple light sources for scattering
- Does NOT implement ray marching (approximate fog)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT handle fog density textures (only depth-based)

---

## Detailed Behavior

### Fog Calculation

For each pixel, the effect computes a fog factor based on depth:

1. **Sample depth**: Get depth value `d` from depth texture:
   ```
   depth = texture(depth_tex, uv).r  // Normalized [0,1]
   depth_meters = depth * (max_depth - min_depth) + min_depth
   ```

2. **Compute fog factor**: Based on `fogMode`:
   - **Linear (0)**: `fog_factor = (fogEnd - depth) / (fogEnd - fogStart)`
   - **Exponential (1)**: `fog_factor = exp(-fogDensity * depth)`
   - **Exponential Squared (2)**: `fog_factor = exp(-(fogDensity * depth)²)`

3. **Apply height falloff** (if `fogHeight` > 0):
   ```
   height_factor = exp(-abs(world_y - fogHeight) * height_falloff)
   fog_factor *= height_factor
   ```

4. **Apply animation** (if `fogAnimate` > 0):
   ```
   swirl = texture(noise_tex, uv + time).r;
   fog_factor += swirl * fog_animate * 0.2;
   ```

5. **Apply scattering** (if `fogScatter` > 0):
   ```
   scatter_glow = pow(fog_factor, 2.0) * fog_scatter;
   final_fog += scatter_glow * 0.2;
   ```

6. **Blend**: Mix between source and fog:
   ```
   result = mix(source, fog_color, fog_factor * fog_opacity);
   final = mix(source, result, u_mix);
   ```

### Fog Modes

| Mode | Formula | Visual Characteristics |
|------|---------|------------------------|
| Linear (0) | `(end - depth) / (end - start)` | Smooth transition from start to end distance |
| Exponential (1) | `exp(-density * depth)` | Fog increases gradually with distance |
| Exponential Squared (2) | `exp(-(density * depth)²)` | More aggressive fog at long distances |

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `fogDensity` | float | 5.0 | 0.0-10.0 | Fog density (for exponential modes) |
| `fogStart` | float | 1.0 | 0.0-10.0 | Distance where fog begins (meters) |
| `fogEnd` | float | 8.0 | 0.0-10.0 | Distance where fog is maximum (meters) |
| `fogMode` | int | 0 | 0-2 | 0=linear, 1=exponential, 2=exponential² |
| `fogColorR`, `fogColorG`, `fogColorB` | float | 3.0, 4.0, 6.0 | 0.0-10.0 | Fog color (0-10 range, maps to 0-1) |
| `fogHeight` | float | 0.0 | 0.0-10.0 | Height of fog layer (0 = no height falloff) |
| `fogAnimate` | float | 0.0 | 0.0-10.0 | Animation strength (0 = static) |
| `fogScatter` | float | 0.0 | 0.0-10.0 | Light scattering intensity |
| `fogOpacity` | float | 1.0 | 0.0-10.0 | Overall fog opacity (maps to 0-1) |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class DepthFogEffect(Effect):
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
| **Output** | `np.ndarray` | Fogged frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_parameters: dict` — Fog parameters
- `_shader: ShaderProgram` — Compiled shader
- `_noise_texture: int` — Optional noise texture for animation

**Per-Frame:**
- Update depth data from source
- Upload depth texture to GPU
- Apply uniforms to shader (including time for animation)
- Render fogged frame

**Initialization:**
- Create depth texture (lazy)
- Create noise texture (if animation enabled)
- Compile shader
- Default parameters: fogDensity=5.0, fogStart=1.0, fogEnd=8.0, fogMode=0, fogColor=(3,4,6), fogHeight=0, fogAnimate=0, fogScatter=0, fogOpacity=1.0

**Cleanup:**
- Delete depth texture
- Delete noise texture (if created)
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED, GL_UNSIGNED_BYTE | depth_frame size | Updated each frame |
| Noise texture (optional) | GL_TEXTURE_2D | GL_RGBA8 | 256×256 (typical) | Init once |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget:**
- Depth texture: W×H×1 byte (e.g., 640×480 = 307,200 bytes)
- Noise texture: 256×256×3 = 196,608 bytes (if used)
- Shader: ~10-50 KB
- Total: ~0.5-1 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Use constant fog (no depth variation) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Invalid fog mode | Clamp to 0-2 | Document valid modes |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and buffer updates must occur on the thread with the OpenGL context. The depth texture is updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Shader execution (fog calculation): ~1-2 ms
- Total: ~1.5-3 ms on GPU

**Optimization Strategies:**
- Reduce shader complexity (simpler fog mode)
- Use lower resolution depth texture
- Precompute fog lookup texture
- Use compute shader for parallel processing
- Cache depth texture if depth hasn't changed

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Fog parameters configured (density, start, end, mode, color)
- [ ] Optional: height, animation, scattering configured
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_depth_source` | Depth source can be connected |
| `test_set_parameter` | Parameters can be set and clamped |
| `test_get_parameter` | Parameters can be retrieved |
| `test_linear_fog` | Linear fog produces smooth transition |
| `test_exponential_fog` | Exponential fog increases with distance |
| `test_exponential_squared_fog` | Exponential² fog is more aggressive |
| `test_fog_color` | Fog color applied correctly |
| `test_fog_height` | Height falloff works |
| `test_fog_animation` | Animation adds noise-based variation |
| `test_fog_scatter` | Light scattering adds glow |
| `test_fog_opacity` | Overall opacity controls effect strength |
| `test_depth_conversion` | Depth normalized to meters correctly |
| `test_process_frame_no_depth` | Uses constant fog when no depth |
| `test_process_frame_with_depth` | Depth modulates fog factor |
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
- [ ] Git commit with `[Phase-3] P3-VD48: depth_fog_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_fog.py` — VJLive Original implementation
- `plugins/core/depth_fog/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_fog/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthFogEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_fog`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for depth-based fog factor
- Parameters: `fogDensity`, `fogStart`, `fogEnd`, `fogMode`, `fogColorR/G/B`, `fogHeight`, `fogAnimate`, `fogScatter`, `fogOpacity`
- Allocates GL resources: depth texture (and optionally noise texture)
- Shader implements multiple fog modes, height falloff, animation, scattering

---

## Notes for Implementers

1. **Depth Range**: The effect expects depth in meters. The legacy uses `min_depth=0.3`, `max_depth=4.0` (typical RealSense range). Adjust as needed:
   ```python
   depth_meters = depth_normalized * (4.0 - 0.3) + 0.3
   ```

2. **Fog Modes**: Implement three modes:
   - **Linear**: `fog_factor = (fogEnd - depth) / (fogEnd - fogStart)` (clamp to [0,1])
   - **Exponential**: `fog_factor = exp(-fogDensity * depth)`
   - **Exponential Squared**: `fog_factor = exp(-(fogDensity * depth) * (fogDensity * depth))`

3. **Height Falloff**: If `fogHeight` > 0, apply exponential falloff from that height:
   ```glsl
   float height_factor = exp(-abs(world_y - fogHeight) * 0.5);
   fog_factor *= height_factor;
   ```
   Note: This requires world-space Y coordinate. If not available, skip or use screen-space approximation.

4. **Animation**: Use a noise texture to animate fog:
   ```glsl
   vec2 noise_uv = uv + time * 0.1;
   float swirl = texture(noise_tex, noise_uv).r;
   fog_factor += swirl * fog_animate * 0.2;
   ```

5. **Light Scattering**: Add glow in dense fog:
   ```glsl
   if (fog_scatter > 0.0) {
       float scatter_glow = pow(fog_factor, 2.0) * fog_scatter;
       final_fog += scatter_glow * 0.2;
   }
   ```

6. **Parameter Ranges**: All fog parameters use 0-10 range from UI:
   - `fogDensity`: 0-10 (maps to 0-10 in shader)
   - `fogStart`, `fogEnd`: 0-10 meters (clamp: start < end)
   - `fogMode`: 0-2 (integer)
   - `fogColorR/G/B`: 0-10 (maps to 0-1 in shader: `/10.0`)
   - `fogHeight`: 0-10 meters (0 = disabled)
   - `fogAnimate`: 0-10 (0 = static)
   - `fogScatter`: 0-10
   - `fogOpacity`: 0-10 (maps to 0-1)

7. **Shader Uniforms**:
   ```glsl
   uniform sampler2D depth_tex;
   uniform float fogDensity;
   uniform float fogStart;
   uniform float fogEnd;
   uniform int fogMode;
   uniform vec3 fogColor;  // (r/10.0, g/10.0, b/10.0)
   uniform float fogHeight;
   uniform float fogAnimate;
   uniform float fogScatter;
   uniform float fogOpacity;
   uniform float time;  // for animation
   ```

8. **Noise Texture**: If using animation, create a small noise texture (e.g., 256×256) with Perlin or simplex noise. Upload once and reuse.

9. **Performance**: The effect is relatively lightweight. The main cost is depth texture upload and shader execution. Animation adds texture fetch for noise.

10. **Testing**: Create a depth gradient (near to far) and verify:
    - Near objects are clear
    - Far objects fade to fog color
    - Different fog modes produce distinct curves
    - Height falloff creates horizontal bands
    - Animation makes fog swirl
    - Scattering adds glow to dense fog

11. **Future Extensions**:
    - Add multiple fog layers
    - Add depth-based fog color variation
    - Add wind direction for animated fog
    - Add volumetric fog with ray marching
    - Add light position for directional scattering

---

## Easter Egg Idea

When `fogDensity` is set exactly to 6.66, `fogStart` to exactly 6.66, `fogEnd` to exactly 6.66, `fogMode` to exactly 2 (exponential squared), and `fogAnimate` to exactly 6.66, and the depth map contains a perfect sphere, the fog spontaneously forms a "halo of the abyss" where the sphere appears to be surrounded by a ring of infinite depth, creating a "void portal" effect that VJs can feel as a momentary glimpse into the infinite.

---

## References

- Fog (computer graphics): https://en.wikipedia.org/wiki/Fog#Computer_graphics
- Exponential fog: https://www.scratchapixel.com/lessons/3d-basic-rendering/volume-rendering-for-developers/fog.html
- Light scattering: https://en.wikipedia.org/wiki/Scattering
- VJLive legacy: `plugins/vdepth/depth_fog.py`

---

## Implementation Tips

1. **Shader Code**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;        // Source image
   uniform sampler2D depth_tex;   // Depth texture
   uniform sampler2D noise_tex;   // Noise texture (optional)
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float fogDensity;
   uniform float fogStart;
   uniform float fogEnd;
   uniform int fogMode;           // 0=linear, 1=exp, 2=exp2
   uniform vec3 fogColor;         // 0-1 range
   uniform float fogHeight;       // 0 = no height falloff
   uniform float fogAnimate;      // 0 = no animation
   uniform float fogScatter;      // Light scattering
   uniform float fogOpacity;      // 0-1
   uniform float time;            // For animation
   
   void main() {
       vec4 source = texture(tex0, uv);
       float depth = texture(depth_tex, uv).r;
       
       // Convert depth to meters (adjust range as needed)
       float depth_meters = depth * (4.0 - 0.3) + 0.3;
       
       // Compute fog factor
       float fog_factor = 0.0;
       
       if (fogMode == 0) {
           // Linear
           fog_factor = (fogEnd - depth_meters) / (fogEnd - fogStart);
           fog_factor = clamp(fog_factor, 0.0, 1.0);
       } else if (fogMode == 1) {
           // Exponential
           fog_factor = exp(-fogDensity * depth_meters);
       } else if (fogMode == 2) {
           // Exponential squared
           float d = fogDensity * depth_meters;
           fog_factor = exp(-d * d);
       }
       
       // Apply height falloff (if fogHeight > 0)
       if (fogHeight > 0.0) {
           // Need world Y coordinate; if not available, approximate from depth or UV
           float world_y = depth_meters;  // Placeholder - should come from vertex shader or depth
           float height_factor = exp(-abs(world_y - fogHeight) * 0.5);
           fog_factor *= height_factor;
       }
       
       // Apply animation
       if (fogAnimate > 0.0) {
           vec2 noise_uv = uv + time * 0.1;
           float swirl = texture(noise_tex, noise_uv).r;
           fog_factor += swirl * fogAnimate * 0.2;
       }
       
       // Apply scattering
       vec3 final_fog = fogColor;
       if (fogScatter > 0.0) {
           float scatter_glow = pow(fog_factor, 2.0) * fogScatter;
           final_fog += scatter_glow * 0.2;
       }
       
       fog_factor = clamp(fog_factor * fogOpacity, 0.0, 1.0);
       
       vec4 fog_color = vec4(final_fog, 1.0);
       vec4 result = mix(source, fog_color, fog_factor);
       
       fragColor = mix(source, result, u_mix);
   }
   ```

2. **Python Parameter Handling**:
   ```python
   def set_parameter(self, name, value):
       if name == 'fogDensity':
           self.parameters['fogDensity'] = max(0.0, min(10.0, value))
       elif name == 'fogStart':
           self.parameters['fogStart'] = max(0.0, min(10.0, value))
       elif name == 'fogEnd':
           self.parameters['fogEnd'] = max(0.0, min(10.0, value))
       elif name == 'fogMode':
           self.parameters['fogMode'] = max(0, min(2, int(value)))
       elif name == 'fogColorR':
           self.parameters['fogColorR'] = max(0.0, min(10.0, value))
       # ... similarly for G, B, Height, Animate, Scatter, Opacity
   ```

3. **Depth Texture Upload**:
   ```python
   def _upload_depth_texture(self):
       if self.depth_frame is None or self.depth_frame.size == 0:
           return
       
       # Normalize to [0,1] (adjust range)
       depth_norm = (self.depth_frame - 0.3) / (4.0 - 0.3)
       depth_norm = np.clip(depth_norm, 0.0, 1.0)
       depth_uint8 = (depth_norm * 255).astype(np.uint8)
       
       if self.depth_texture == 0:
           self.depth_texture = glGenTextures(1)
           glBindTexture(GL_TEXTURE_2D, self.depth_texture)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
       
       glBindTexture(GL_TEXTURE_2D, self.depth_texture)
       glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, depth_uint8.shape[1],
                    depth_uint8.shape[0], 0, GL_RED, GL_UNSIGNED_BYTE,
                    depth_uint8)
   ```

4. **Noise Texture Creation** (if animating):
   ```python
   def _create_noise_texture(self):
       # Generate Perlin noise (or load from image)
       noise = generate_perlin_noise_2d((256, 256), res=(8, 8))
       noise_uint8 = (noise * 255).astype(np.uint8)
       
       self.noise_texture = glGenTextures(1)
       glBindTexture(GL_TEXTURE_2D, self.noise_texture)
       glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
       glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
       glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
       glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
       glTexImage2D(GL_TEXTURE_2D, 0, GL_R8, 256, 256, 0, GL_RED, GL_UNSIGNED_BYTE, noise_uint8)
   ```

5. **Apply Uniforms**:
   ```python
   def apply_uniforms(self, time, resolution, audio_reactor=None):
       super().apply_uniforms(time, resolution, audio_reactor)
       
       self._upload_depth_texture()
       
       self.shader.set_uniform("depth_tex", 1)
       self.shader.set_uniform("fogDensity", self.parameters['fogDensity'])
       self.shader.set_uniform("fogStart", self.parameters['fogStart'])
       self.shader.set_uniform("fogEnd", self.parameters['fogEnd'])
       self.shader.set_uniform("fogMode", int(self.parameters['fogMode']))
       self.shader.set_uniform("fogColor", [
           self.parameters['fogColorR'] / 10.0,
           self.parameters['fogColorG'] / 10.0,
           self.parameters['fogColorB'] / 10.0
       ])
       self.shader.set_uniform("fogHeight", self.parameters['fogHeight'])
       self.shader.set_uniform("fogAnimate", self.parameters['fogAnimate'])
       self.shader.set_uniform("fogScatter", self.parameters['fogScatter'])
       self.shader.set_uniform("fogOpacity", self.parameters['fogOpacity'] / 10.0)
       self.shader.set_uniform("time", time)
       
       if self.parameters['fogAnimate'] > 0 and self.noise_texture:
           glActiveTexture(GL_TEXTURE0 + 2)
           glBindTexture(GL_TEXTURE_2D, self.noise_texture)
           self.shader.set_uniform("noise_tex", 2)
   ```

6. **World Y Coordinate**: For height falloff, you need the world-space Y coordinate. Options:
   - Pass from vertex shader as varying
   - Reconstruct from depth and camera intrinsics
   - Use a separate world Y texture
   - If unavailable, skip height falloff or use screen-space Y

---

## Conclusion

The DepthFogEffect adds atmospheric depth to scenes by fading distant objects into a colored haze based on depth. With multiple fog modes, height falloff, animation, and light scattering, it provides a versatile tool for creating atmospheric perspective and mood in VJ performances. The effect is GPU-accelerated and highly configurable, allowing for subtle haze or dense fog.

---
>>>>>>> REPLACE