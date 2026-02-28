# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD42_DepthDistortionEffect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD42 — DepthDistortionEffect

## Description

The DepthDistortionEffect applies depth-aware distortion to video frames, creating effects like depth-based blur, focus, and displacement. It uses depth data to determine how much each pixel should be distorted, enabling effects such as depth-of-field simulation, depth-based displacement, and depth-aware blur. The effect samples the depth texture to calculate a distortion amount for each pixel based on its distance from a focus plane, then applies the distortion to the video frame.

The effect is particularly useful for creating cinematic depth-of-field effects, depth-based displacement maps, and depth-aware blur effects that respond to the 3D structure of the scene. It can simulate camera focus effects, create depth-based motion blur, and generate artistic depth distortions.

## What This Module Does

- Applies depth-aware distortion to video frames based on depth data
- Simulates depth-of-field effects with focus distance and aperture controls
- Implements depth-based blur using Gaussian sampling
- Supports configurable focus distance, aperture, max blur, and blur samples
- Integrates with `DepthEffect` base class for depth source management
- GPU-accelerated using fragment shader with depth texture sampling
- Provides depth-aware displacement and distortion effects

## What This Module Does NOT Do

- Does NOT implement 3D mesh distortion (only 2D image distortion)
- Does NOT support real-time depth generation (requires depth source)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT implement advanced bokeh shapes (only Gaussian blur)
- Does NOT support depth-based color grading (only distortion)

---

## Detailed Behavior

### Depth-Based Distortion Algorithm

The effect applies distortion based on the difference between each pixel's depth and a focus distance:

1. **Sample depth**: For each pixel (u,v), sample the depth texture to get depth value `d`:
   ```
   depth = texture(depth_tex, uv).r * 4.0 + 0.3  // Convert to meters
   ```
   The depth is normalized from [0,1] to [0.3, 4.0] meters.

2. **Calculate depth difference**: Compute difference from focus plane:
   ```
   depth_diff = abs(depth - focus_distance)
   ```

3. **Calculate blur amount**: Scale depth difference by aperture, clamp to max:
   ```
   blur_amount = min(depth_diff * aperture, max_blur)
   ```
   Where `aperture` controls how strongly depth affects blur.

4. **Apply distortion**: Use blur amount to sample neighboring pixels:
   ```
   blurred = gaussian_blur(tex0, uv, blur_amount)
   ```
   The `gaussian_blur` function samples tex0 at offsets around uv, weighted by Gaussian kernel.

### Gaussian Blur Implementation

The fragment shader implements a separable Gaussian blur:

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

This samples a square kernel around each pixel, with weights following a Gaussian distribution. The `blur_samples` parameter controls kernel size (4-32), and `blur_amount` controls kernel radius.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `focus_distance` | float | 2.0 | 0.5-10.0 | Depth distance (meters) that should be in focus |
| `aperture` | float | 0.1 | 0.01-1.0 | Depth sensitivity (higher = more blur for out-of-focus) |
| `max_blur` | float | 0.05 | 0.001-0.1 | Maximum blur radius in pixels |
| `blur_samples` | int | 8 | 4-32 | Number of samples for Gaussian blur |

**Inherited from DepthEffect**: `min_depth`, `max_depth`, `near_clip`, `far_clip`, `depth_scale`, `invert_depth`

### Shader Architecture

**Fragment Shader**:
```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;        // Video frame
uniform sampler2D depth_tex;   // Depth texture
uniform float u_mix;           // Mix factor (0=original, 1=distorted)
uniform vec2 resolution;        // Frame resolution
uniform float has_depth;       // 0 if no depth, 1 if depth available
uniform float focus_distance;  // Focus plane distance
uniform float aperture;        // Depth sensitivity
uniform float max_blur;        // Max blur radius
uniform int blur_samples;      // Gaussian kernel size

// Gaussian blur function (as above)

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

### Depth Texture Format

The depth texture is expected to be in normalized format [0,1], where:
- 0 = near clip (0.3 meters)
- 1 = far clip (4.0 meters)

Conversion in shader:
```
depth_meters = depth_normalized * 4.0 + 0.3
```

### Integration with DepthEffect

The effect inherits from `DepthEffect` and integrates depth data:

1. **Depth source**: Connect to a depth source via `set_depth_source()`
2. **Update depth**: Call `update_depth_data()` to get latest depth frame
3. **Upload depth texture**: Convert depth frame to texture and upload to GPU
4. **Apply uniforms**: Pass depth texture and parameters to shader

---

## Public Interface

```python
class DepthDistortionEffect(Effect):
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
| **Output** | `np.ndarray` | Distorted frame (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Latest depth frame
- `_objects: List[DetectedObject]` — Detected objects (if any)
- `_depth_texture: int` — GL texture for depth data
- `_focus_distance: float` — Focus plane distance
- `_aperture: float` — Depth sensitivity
- `_max_blur: float` — Maximum blur radius
- `_blur_samples: int` — Gaussian kernel size
- `_shader: ShaderProgram` — Compiled shader

**Per-Frame:**
- Update depth data from source
- Upload depth texture to GPU
- Apply uniforms to shader
- Render distorted frame

**Initialization:**
- Create depth texture (if needed)
- Compile shader with fragment shader
- Default parameters: focus_distance=2.0, aperture=0.1, max_blur=0.05, blur_samples=8

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
| Depth frame missing | Skip distortion, render original | Normal operation |
| Depth texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Blur samples too high | Clamp to 32 | Document max samples |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and buffer updates must occur on the thread with the OpenGL context. The depth texture is updated each frame, and the shader is used for rendering, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Depth texture upload: ~0.5-1 ms
- Gaussian blur (8×8 kernel): ~2-4 ms
- Total: ~2.5-5 ms on GPU

**Optimization Strategies:**
- Reduce `blur_samples` for faster blur
- Use separable blur (horizontal + vertical passes) to reduce samples from N² to 2N
- Implement blur in compute shader for better performance
- Use mipmaps for depth texture if available
- Cache depth texture if depth hasn't changed significantly

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Camera intrinsics set (fx, fy, cx, cy)
- [ ] Depth range (min_depth, max_depth) configured
- [ ] Distortion parameters set (focus_distance, aperture, max_blur, blur_samples)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_depth_source` | Depth source can be connected |
| `test_set_focus_distance` | Focus distance updates |
| `test_set_aperture` | Aperture updates |
| `test_set_max_blur` | Max blur updates |
| `test_set_blur_samples` | Blur samples updates |
| `test_update_depth_data` | Depth frame updates correctly |
| `test_apply_uniforms` | Uniforms passed to shader |
| `test_process_frame_no_depth` | Renders original when no depth |
| `test_process_frame_with_depth` | Applies distortion when depth available |
| `test_depth_conversion` | Depth normalized to meters correctly |
| `test_blur_amount_calculation` | Blur amount computed from depth difference |
| `test_gaussian_blur` | Gaussian blur produces smooth results |
| `test_focus_plane` | Pixels at focus distance have minimal blur |
| `test_depth_gradient` | Pixels at different depths have appropriate blur |
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
- [ ] Git commit with `[Phase-3] P3-VD42: depth_distortion_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/depth/distortion.py` — VJLive-2 implementation of `DepthDistortionEffect`
- `plugins/vdepth/depth_effects.py` — Registers `DepthDistortionEffect` in `DEPTH_EFFECTS`
- `gl_leaks.txt` — Shows `DepthDistortionEffect` allocates `glGenTextures` and must free them

Design decisions inherited:
- Effect name: `depth_distortion`
- Inherits from `Effect` (not `DepthEffect` in legacy, but should inherit from `DepthEffect`)
- Uses depth texture for depth data
- Implements depth-based Gaussian blur
- Parameters: `focus_distance`, `aperture`, `max_blur`, `blur_samples`
- Allocates GL resources: depth texture
- Supports depth-aware distortion effects

---

## Notes for Implementers

1. **Depth Texture Upload**: The legacy converts depth frame to normalized [0,1] and uploads as GL_RED texture:
   ```python
   depth_normalized = ((self.depth_frame - 0.3) / (4.0 - 0.3) * 255).astype(np.uint8)
   glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, depth_normalized.shape[1],
                depth_normalized.shape[0], 0, GL_RED, GL_UNSIGNED_BYTE,
                depth_normalized)
   ```
   This assumes depth range [0.3, 4.0] meters.

2. **Shader Integration**: The effect should inherit from `DepthEffect` to get depth source management, then override `apply_uniforms` to upload depth texture and set distortion parameters.

3. **Blur Implementation**: The legacy uses a simple 2D Gaussian blur. For better performance, consider separable blur:
   ```glsl
   // Horizontal pass
   vec4 horizontal_blur(sampler2D tex, vec2 uv, float blur_amount) {
       vec4 result = vec4(0.0);
       float total_weight = 0.0;
       int samples = blur_samples;
       float sigma = blur_amount * 10.0;
       
       for (int i = -samples/2; i <= samples/2; i++) {
           vec2 offset = vec2(float(i) * blur_amount / resolution.x, 0.0);
           float weight = exp(-(float(i*i)) / (2.0 * sigma * sigma));
           result += texture(tex, uv + offset) * weight;
           total_weight += weight;
       }
       return result / total_weight;
   }
   
   // Vertical pass (similar)
   ```
   Then combine in two passes for better performance.

4. **Focus Distance**: The focus distance is in meters (camera space). It should be configurable and clamped to [0.5, 10.0] meters.

5. **Aperture**: Controls how strongly depth affects blur. Higher aperture = more blur for out-of-focus objects. Typical values: 0.01-0.1.

6. **Max Blur**: Maximum blur radius in pixels. Prevents excessive blur for very far objects. Typical values: 0.001-0.1 pixels.

7. **Blur Samples**: Number of samples for Gaussian kernel. Higher = smoother blur but slower. Typical values: 4-32.

8. **Performance**: Gaussian blur is expensive. Consider:
   - Using lower `blur_samples` (4-8)
   - Implementing separable blur
   - Using compute shader for blur
   - Caching results if depth hasn't changed

9. **Testing**: Create synthetic depth with known focus plane and verify blur amount. Test with different focus distances and apertures.

10. **Future Extensions**:
    - Add bokeh shape control (not just Gaussian)
    - Add depth-based displacement (not just blur)
    - Add motion blur integration
    - Add depth-based color grading
    - Add real-time depth generation fallback

---

## Easter Egg Idea

When `focus_distance` is set exactly to 6.66, `aperture` to exactly 0.666, `max_blur` to exactly 0.0666, and `blur_samples` to exactly 13, and the depth map contains a perfect sphere, the distortion effect spontaneously creates a "depth vortex" that causes all out-of-focus pixels to swirl around the focus point for exactly 6.66 seconds before returning to normal Gaussian blur. The effect subtly influences the blur kernel to follow a logarithmic spiral pattern, which VJs can feel as a "sacred geometry" resonance.

---

## References

- Depth-of-field simulation: https://en.wikipedia.org/wiki/Depth_of_field
- Gaussian blur: https://en.wikipedia.org/wiki/Gaussian_blur
- OpenGL texture upload: https://www.khronos.org/opengl/wiki/Texture_Storage
- VJLive legacy: `core/effects/depth/distortion.py` (DepthDistortionEffect)

---

## Implementation Tips

1. **Depth Texture Upload**:
   ```python
   def _upload_depth_texture(self):
       if self.depth_frame is None or self.depth_frame.size == 0:
           return
       
       # Normalize depth to [0,1] where 0.3m = 0, 4.0m = 1
       depth_normalized = (self.depth_frame - 0.3) / (4.0 - 0.3)
       depth_normalized = np.clip(depth_normalized, 0.0, 1.0)
       depth_uint8 = (depth_normalized * 255).astype(np.uint8)
       
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

2. **Shader Setup**:
   ```python
   FRAGMENT_SHADER = """
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
   """
   ```

3. **Apply Uniforms**:
   ```python
   def apply_uniforms(self, time, resolution, audio_reactor=None):
       super().apply_uniforms(time, resolution, audio_reactor)
       
       # Upload depth texture
       self._upload_depth_texture()
       
       # Set shader uniforms
       self.shader.set_uniform("depth_tex", 1)  # Texture unit 1
       self.shader.set_uniform("focus_distance", self.focus_distance)
       self.shader.set_uniform("aperture", self.aperture)
       self.shader.set_uniform("max_blur", self.max_blur)
       self.shader.set_uniform("blur_samples", self.blur_samples)
       self.shader.set_uniform("has_depth", 1.0 if self.depth_frame is not None else 0.0)
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

5. **Performance Optimization**: Consider separable blur for better performance:
   ```glsl
   // Horizontal pass
   vec4 horizontal_blur(sampler2D tex, vec2 uv, float blur_amount) {
       vec4 result = vec4(0.0);
       float total_weight = 0.0;
       int samples = blur_samples;
       float sigma = blur_amount * 10.0;
       
       for (int i = -samples/2; i <= samples/2; i++) {
           vec2 offset = vec2(float(i) * blur_amount / resolution.x, 0.0);
           float weight = exp(-(float(i*i)) / (2.0 * sigma * sigma));
           result += texture(tex, uv + offset) * weight;
           total_weight += weight;
       }
       return result / total_weight;
   }
   
   // Then in main:
   vec4 blurred = horizontal_blur(tex0, uv, blur_amount);
   // Then vertical pass on blurred result
   ```

6. **Testing**: Create a synthetic depth gradient and verify blur amount increases with distance from focus plane. Test with different focus distances to ensure correct behavior.

---

## Conclusion

The DepthDistortionEffect provides depth-aware image distortion, enabling cinematic depth-of-field effects and depth-based blur. By combining depth data with Gaussian blur, it creates realistic focus effects that respond to the 3D structure of the scene. The effect is particularly useful for creating professional-looking video with depth-based focus and blur effects.

---
>>>>>>> REPLACE