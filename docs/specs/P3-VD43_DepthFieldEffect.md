# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD43_DepthFieldEffect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD43 — DepthFieldEffect

## Description

The DepthFieldEffect simulates depth-of-field (bokeh) effects using depth data, creating cinematic focus effects where objects at a specific distance are sharp while objects nearer or farther are blurred. This effect mimics the optical properties of camera lenses, providing a professional-grade depth blur that responds to the 3D structure of the scene.

The effect uses depth information to calculate a blur amount for each pixel based on its distance from a focus plane. Pixels at the focus distance remain sharp; pixels away from the focus plane are blurred with a Gaussian kernel whose radius increases with depth difference. The result is a realistic depth-of-field effect that can be used to draw attention to specific subjects or create artistic focus effects.

## What This Module Does

- Simulates depth-of-field (bokeh) effect using depth data
- Applies Gaussian blur to out-of-focus regions based on depth
- Supports configurable focus distance, aperture, max blur, and blur samples
- Uses depth texture to determine per-pixel blur amount
- GPU-accelerated fragment shader with Gaussian sampling
- Integrates with depth source for real-time depth data

## What This Module Does NOT Do

- Does NOT implement true bokeh (only Gaussian blur, not lens aperture shapes)
- Does NOT support real-time depth generation (requires depth source)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT implement chromatic aberration or other lens effects
- Does NOT support motion blur integration

---

## Detailed Behavior

### Depth-of-Field Algorithm

1. **Sample depth**: For each pixel (u,v), sample the depth texture:
   ```
   depth = texture(depth_tex, uv).r * 4.0 + 0.3  // Convert to meters
   ```
   The depth is normalized from [0,1] to [0.3, 4.0] meters.

2. **Calculate depth difference**: Compute absolute difference from focus plane:
   ```
   depth_diff = abs(depth - focus_distance)
   ```

3. **Calculate blur radius**: Scale depth difference by aperture, clamp to max:
   ```
   blur_amount = min(depth_diff * aperture, max_blur)
   ```
   Where:
   - `aperture` controls depth sensitivity (higher = more blur)
   - `max_blur` limits maximum blur radius (in pixels)

4. **Apply Gaussian blur**: Sample the source image with Gaussian weights:
   ```
   blurred = gaussian_blur(tex0, uv, blur_amount)
   ```

5. **Blend**: Mix between original and blurred based on `u_mix`:
   ```
   fragColor = mix(original, blurred, u_mix)
   ```

### Gaussian Blur

The effect uses a 2D Gaussian kernel:

```glsl
vec4 gaussian_blur(sampler2D tex, vec2 uv, float blur_amount) {
    vec4 result = vec4(0.0);
    float total_weight = 0.0;
    
    int samples = int(min(float(blur_samples), 16.0));
    float sigma = blur_amount * 10.0;
    
    for (int i = -samples/2; i <= samples/2; i++) {
        for (int j = -samples/2; j <= samples/2; j++) {
            vec2 offset = vec2(float(i), float(j)) * blur_amount / resolution;
            float weight = exp(-(float(i*i) + float(j*j)) / (2.0 * sigma * sigma));
            result += texture(tex, uv + offset) * weight;
            total_weight += weight;
        }
    }
    
    return result / total_weight;
}
```

The kernel size is `blur_samples × blur_samples` (square). The `sigma` parameter controls the spread of the Gaussian and is proportional to `blur_amount`.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `focus_distance` | float | 2.0 | 0.5-10.0 | Distance (meters) that should be in focus |
| `aperture` | float | 0.1 | 0.01-1.0 | Depth sensitivity (higher = more blur for out-of-focus) |
| `max_blur` | float | 0.02 | 0.001-0.1 | Maximum blur radius in pixels |
| `blur_samples` | int | 16 | 4-32 | Number of samples per dimension for Gaussian blur |

**Inherited from Effect**: `u_mix`, `resolution`, etc.

---

## Public Interface

```python
class DepthFieldEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_focus_distance(self, distance: float) -> None: ...
    def get_focus_distance(self) -> float: ...
    def set_aperture(self, aperture: float) -> None: ...
    def get_aperture(self) -> float: ...
    def set_max_blur(self, max_blur: float) -> None: ...
    def get_max_blur(self) -> float: ...
    def set_blur_samples(self, samples: int) -> None: ...
    def get_blur_samples(self) -> int: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Depth-of-field blurred frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_depth_texture: int` — GL texture for depth data
- `_focus_distance: float` — Focus plane distance (meters)
- `_aperture: float` — Depth sensitivity
- `_max_blur: float` — Maximum blur radius (pixels)
- `_blur_samples: int` — Gaussian kernel size
- `_shader: ShaderProgram` — Compiled shader

**Per-Frame:**
- Update depth data from source
- Upload depth texture to GPU
- Apply uniforms to shader
- Render frame with depth-of-field

**Initialization:**
- Create depth texture (lazy)
- Compile shader
- Default parameters: focus_distance=2.0, aperture=0.1, max_blur=0.02, blur_samples=16

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

**Memory Budget:**
- Depth texture: W×H×1 byte (e.g., 640×480 = 307,200 bytes)
- Shader: ~10-50 KB
- Total: < 1 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | Render original frame (no blur) | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Blur samples too high | Clamp to 32 | Document max samples |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread with the OpenGL context. The depth texture is updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480, blur_samples=16):**
- Depth texture upload: ~0.5-1 ms
- Gaussian blur (16×16 kernel): ~3-6 ms
- Total: ~3.5-7 ms on GPU

**Optimization Strategies:**
- Reduce `blur_samples` for faster blur (4-8)
- Use separable blur (horizontal + vertical) to reduce from O(N²) to O(2N)
- Implement blur in compute shader for better parallelism
- Cache depth texture if depth hasn't changed
- Use lower resolution for blur (downsample, blur, upsample)

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Depth range configured (min_depth, max_depth)
- [ ] Focus distance set appropriately
- [ ] Aperture and max blur tuned
- [ ] Blur samples balanced for performance/quality
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_depth_source` | Depth source can be connected |
| `test_set_focus_distance` | Focus distance updates correctly |
| `test_set_aperture` | Aperture updates correctly |
| `test_set_max_blur` | Max blur updates correctly |
| `test_set_blur_samples` | Blur samples updates correctly |
| `test_update_depth_data` | Depth frame updates correctly |
| `test_apply_uniforms` | Uniforms passed to shader correctly |
| `test_process_frame_no_depth` | Renders original frame when no depth |
| `test_process_frame_with_depth` | Applies blur when depth available |
| `test_depth_conversion` | Depth normalized to meters correctly |
| `test_blur_amount_calculation` | Blur amount computed from depth difference |
| `test_focus_plane` | Pixels at focus distance have minimal blur |
| `test_depth_gradient` | Blur increases with distance from focus |
| `test_max_blur_clamp` | Blur amount clamped to max_blur |
| `test_gaussian_blur` | Gaussian blur produces smooth results |
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
- [ ] Git commit with `[Phase-3] P3-VD43: depth_field_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/depth/distortion.py` — VJLive-2 implementation of `DepthFieldEffect` (lines ~225-244+)
- `plugins/vdepth/depth_effects.py` — Registers `DepthFieldEffect` in `DEPTH_EFFECTS`
- `gl_leaks.txt` — Shows `DepthFieldEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_field`
- Inherits from `Effect` (not `DepthEffect` in legacy)
- Uses depth texture for depth data
- Implements depth-based Gaussian blur for depth-of-field
- Parameters: `focus_distance`, `aperture`, `max_blur`, `blur_samples`
- Allocates GL resources: depth texture
- Shader includes `gaussian_blur` function

---

## Notes for Implementers

1. **Depth Texture Upload**: The legacy code normalizes depth from [0.3, 4.0] meters to [0,1]:
   ```python
   depth_normalized = (self.depth_frame - 0.3) / (4.0 - 0.3)
   depth_normalized = np.clip(depth_normalized, 0.0, 1.0)
   depth_uint8 = (depth_normalized * 255).astype(np.uint8)
   glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, ..., GL_RED, GL_UNSIGNED_BYTE, depth_uint8)
   ```
   Adjust depth range to match your depth source.

2. **Shader Uniforms**: Ensure these uniforms are set:
   - `depth_tex` (int) — texture unit for depth
   - `focus_distance` (float)
   - `aperture` (float)
   - `max_blur` (float)
   - `blur_samples` (int)
   - `has_depth` (float) — 1.0 if depth available, 0.0 otherwise
   - `resolution` (vec2)

3. **Gaussian Blur Optimization**: The current implementation is O(N²) per pixel. For better performance:
   - Use separable blur: horizontal pass + vertical pass (O(2N))
   - Or use a compute shader with shared memory
   - Or use a precomputed Gaussian kernel texture

4. **Blur Samples**: The legacy clamps to 16 in the shader (`int(min(float(blur_samples), 16.0))`). Consider limiting to 16 or 32 to avoid excessive loops.

5. **Depth Range**: The focus distance is in meters. Ensure your depth data is in the same units. The legacy uses [0.3, 4.0] meters.

6. **Mix Control**: The `u_mix` uniform controls blend between original and blurred. Set to 1.0 for full effect, 0.0 for original.

7. **Testing**: Create a synthetic depth gradient (e.g., a ramp from 0.5m to 4.0m) and verify:
   - At focus_distance, blur is minimal
   - As depth increases or decreases, blur increases
   - Blur is clamped at max_blur

8. **Performance Profiling**: The Gaussian blur is the bottleneck. Profile with different `blur_samples` values. Consider implementing separable blur if performance is insufficient.

9. **Future Extensions**:
   - Add bokeh shape control (hexagon, circle, custom kernel)
   - Add chromatic aberration based on depth
   - Add vignette effect
   - Add depth-based color grading integration
   - Support multiple focus planes

---

## Easter Egg Idea

When `focus_distance` is set exactly to 6.66, `aperture` to exactly 0.666, `max_blur` to exactly 0.0666, and `blur_samples` to exactly 13, and the depth map contains a perfect sphere, the Gaussian kernel subtly transforms into a logarithmic spiral pattern for exactly 6.66 seconds, causing the out-of-focus regions to swirl in a Fibonacci pattern. The effect creates a "sacred geometry" bokeh that VJs can feel as a harmonic resonance in the visual field.

---

## References

- Depth of field: https://en.wikipedia.org/wiki/Depth_of_field
- Gaussian blur: https://en.wikipedia.org/wiki/Gaussian_blur
- OpenGL fragment shader: https://www.khronos.org/opengl/wiki/Fragment_Shader
- VJLive legacy: `core/effects/depth/distortion.py` (DepthFieldEffect)

---

## Implementation Tips

1. **Shader Code**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;
   uniform sampler2D depth_tex;
   uniform float u_mix;
   uniform vec2 resolution;
   uniform float has_depth;
   uniform float focus_distance;
   uniform float aperture;
   uniform float max_blur;
   uniform int blur_samples;
   
   vec4 gaussian_blur(sampler2D tex, vec2 uv, float blur_amount) {
       vec4 result = vec4(0.0);
       float total_weight = 0.0;
       
       int samples = int(min(float(blur_samples), 16.0));
       float sigma = blur_amount * 10.0;
       
       for (int i = -samples/2; i <= samples/2; i++) {
           for (int j = -samples/2; j <= samples/2; j++) {
               vec2 offset = vec2(float(i), float(j)) * blur_amount / resolution;
               float weight = exp(-(float(i*i) + float(j*j)) / (2.0 * sigma * sigma));
               result += texture(tex, uv + offset) * weight;
               total_weight += weight;
           }
       }
       
       return result / total_weight;
   }
   
   void main() {
       vec4 original = texture(tex0, uv);
       
       if (has_depth > 0.0) {
           float depth = texture(depth_tex, uv).r * 4.0 + 0.3;
           float depth_diff = abs(depth - focus_distance);
           float blur_amount = min(depth_diff * aperture, max_blur);
           vec4 blurred = gaussian_blur(tex0, uv, blur_amount);
           fragColor = mix(original, blurred, u_mix);
       } else {
           fragColor = original;
       }
   }
   ```

2. **Depth Texture Upload**:
   ```python
   def _upload_depth_texture(self):
       if self.depth_frame is None or self.depth_frame.size == 0:
           return
       
       # Normalize to [0,1] (adjust range as needed)
       depth_min, depth_max = 0.3, 4.0
       depth_norm = (self.depth_frame - depth_min) / (depth_max - depth_min)
       depth_norm = np.clip(depth_norm, 0.0, 1.0)
       depth_uint8 = (depth_norm * 255).astype(np.uint8)
       
       if self._depth_texture == 0:
           self._depth_texture = glGenTextures(1)
           glBindTexture(GL_TEXTURE_2D, self._depth_texture)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
       
       glBindTexture(GL_TEXTURE_2D, self._depth_texture)
       glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, depth_uint8.shape[1],
                    depth_uint8.shape[0], 0, GL_RED, GL_UNSIGNED_BYTE,
                    depth_uint8)
   ```

3. **Apply Uniforms**:
   ```python
   def apply_uniforms(self, time, resolution, audio_reactor=None):
       super().apply_uniforms(time, resolution, audio_reactor)
       
       self._upload_depth_texture()
       
       self.shader.set_uniform("depth_tex", 1)
       self.shader.set_uniform("focus_distance", self.focus_distance)
       self.shader.set_uniform("aperture", self.aperture)
       self.shader.set_uniform("max_blur", self.max_blur)
       self.shader.set_uniform("blur_samples", self.blur_samples)
       self.shader.set_uniform("has_depth", 1.0 if self.depth_frame is not None else 0.0)
       self.shader.set_uniform("resolution", resolution)
   ```

4. **Parameter Clamping**:
   ```python
   def set_focus_distance(self, distance):
       self.focus_distance = max(0.5, min(10.0, distance))
   
   def set_aperture(self, aperture):
       self.aperture = max(0.01, min(1.0, aperture))
   
   def set_max_blur(self, max_blur):
       self.max_blur = max(0.001, min(0.1, max_blur))
   
   def set_blur_samples(self, samples):
       self.blur_samples = int(max(4, min(32, samples)))
   ```

5. **Separable Blur (Optional Optimization)**:
   Implement two-pass blur: horizontal then vertical. This reduces complexity from O(N²) to O(2N). Requires two shader programs or a ping-pong framebuffer setup.

6. **Depth Range**: The depth conversion `depth = texture(depth_tex, uv).r * 4.0 + 0.3` assumes depth in [0.3, 4.0] meters. Adjust if your depth source uses different range.

---

## Conclusion

The DepthFieldEffect provides cinematic depth-of-field blur using depth data. By calculating per-pixel blur based on distance from a focus plane, it creates realistic bokeh effects that enhance visual storytelling in VJ performances. The effect is GPU-accelerated and configurable, allowing VJs to fine-tune the focus and blur characteristics to match their artistic vision.

---
>>>>>>> REPLACE