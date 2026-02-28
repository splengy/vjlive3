# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD70_Depth_Video_Projection.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD70 — DepthVideoProjectionEffect

## Description

The DepthVideoProjectionEffect projects a second video feed onto the performer's body, turning them into a living screen. The projection is UV-mapped onto the depth surface, following body contours via depth-derived surface normals. The effect includes normal-based lighting and holographic Fresnel edge glow for a sci-fi aesthetic.

This effect is ideal for creating the illusion of video being projected onto a performer's body, with realistic lighting and edge effects. It's perfect for VJ performances that want to create immersive, body-mapped visuals where the performer becomes part of the visual canvas.

## What This Module Does

- Projects a second video onto the depth surface
- Uses depth map to derive surface normals
- UV-maps projection video following body contours
- Applies normal-based lighting to projection
- Adds holographic Fresnel edge glow
- Configurable projection strength, contour, UV scale/scroll
- Two inputs: main video and projection source
- GPU-accelerated with normal computation

## What This Module Does NOT Do

- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT include audio reactivity (may be added later)
- Does NOT support multiple projection sources (single secondary video)
- Does NOT implement true 3D projection (depth-based only)
- Does NOT include shadow casting (self-shadowing only)

---

## Detailed Behavior

### Video Projection Pipeline

1. **Inputs**:
   - `tex0` (main video): The primary video feed (background)
   - `tex1` (projection source): The video to project onto the body
   - `depth_tex`: Depth map from depth camera

2. **Depth to Normal**:
   Compute surface normal from depth map:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float depth_dx = dFdx(depth);
   float depth_dy = dFdy(depth);
   vec3 normal = normalize(vec3(-depth_dx, -depth_dy, 1.0));
   ```

3. **UV Mapping**:
   Map projection video onto depth surface using normals:
   ```glsl
   vec2 proj_uv = uv + normal.xy * uvScale;
   proj_uv += vec2(uvScrollX, uvScrollY);
   ```

4. **Masking**:
   Create mask from depth to isolate performer:
   ```glsl
   float mask = 1.0 - smoothstep(depthContour, depthContour + 0.1, depth);
   ```

5. **Projection**:
   Sample projection video at mapped UV:
   ```glsl
   vec3 projected = texture(tex1, proj_uv).rgb;
   ```

6. **Normal Lighting**:
   Apply lighting based on normal:
   ```glsl
   float lighting = dot(normal, normalize(vec3(0.5, 0.5, 1.0)));
   lighting = max(0.3, lighting);
   projected *= lighting * normalLighting;
   ```

7. **Holographic Fresnel**:
   Add edge glow based on normal facing:
   ```glsl
   float fresnel = 1.0 - abs(normal.z);
   fresnel = pow(fresnel, 3.0);
   vec3 holo_color = vec3(0.2, 0.6, 1.0) * fresnel * hologramGlow * 2.0;
   ```

8. **Composite**:
   Blend projection with background:
   ```glsl
   vec3 result = projected * projectionStrength + holo_color;
   float soft_mask = smoothstep(0.0, 0.15, mask);
   result = mix(background * 0.15, result, soft_mask);
   result = mix(background, result, u_mix);
   ```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `projectionStrength` | float | 8.0 | 0.0-10.0 | Intensity of projected video |
| `depthContour` | float | 5.0 | 0.0-10.0 | Depth threshold for mask edge |
| `uvScale` | float | 5.0 | 0.0-10.0 | Scale of UV distortion from normals |
| `uvScrollX` | float | 5.0 | 0.0-10.0 | Horizontal scroll of projection |
| `uvScrollY` | float | 5.0 | 0.0-10.0 | Vertical scroll of projection |
| `normalLighting` | float | 4.0 | 0.0-10.0 | Strength of normal-based lighting |
| `maskTight` | float | 6.0 | 0.0-10.0 | Tightness of depth mask |
| `hologramGlow` | float | 3.0 | 0.0-10.0 | Intensity of Fresnel edge glow |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class DepthVideoProjectionEffect(Effect):
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_projection_source(self, source) -> None: ...  # Set second video input
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray, projection_frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Main video frame (HxWxC, RGB) |
| `projection_frame` | `np.ndarray` | Projection video frame (HxWxC, RGB) |
| **Output** | `np.ndarray` | Projected output (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_depth_source: Optional[DepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Current depth frame
- `_projection_source: Optional[VideoSource]` — Second video source
- `_parameters: dict` — Projection parameters
- `_shader: ShaderProgram` — Compiled shader
- `_temp_texture: int` — For projection video

**Per-Frame:**
- Update depth data from source
- Upload main frame and projection frame to textures
- Render effect: compute normals, map UV, apply lighting and glow, composite
- Return result

**Initialization:**
- Compile shader
- Create temporary texture for projection video
- Default parameters: projectionStrength=8.0, depthContour=5.0, uvScale=5.0, uvScrollX=5.0, uvScrollY=5.0, normalLighting=4.0, maskTight=6.0, hologramGlow=3.0
- Initialize `_projection_source = None`

**Cleanup:**
- Delete temporary textures
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Main video texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame |
| Projection texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | Updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Main texture: 921,600 bytes
- Projection texture: 921,600 bytes
- Shader: ~20-30 KB
- Total: ~1.9 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| No depth source | Use uniform depth (0.5) | Normal operation |
| No projection source | Use black projection | Normal operation |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations, texture updates, and shader operations must occur on the thread with the OpenGL context. The effect updates textures each frame; concurrent `process_frame()` calls will cause race conditions and corrupted rendering. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- Texture uploads: ~1-2 ms (2 textures)
- Shader execution (normal computation, UV mapping, lighting, glow): ~3-8 ms
- Total: ~4-10 ms on GPU (moderate)

**Optimization Strategies:**
- Use lower resolution for projection video
- Simplify normal computation (skip dFdx/dFdy, use Sobel)
- Reduce shader complexity (disable lighting or glow)
- Use precomputed normals if depth is static

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Projection source set (second video)
- [ ] Projection parameters configured
- [ ] `process_frame()` called each frame with both frames
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_set_projection_source` | Projection source can be set |
| `test_normal_computation` | Normals computed correctly from depth |
| `test_uv_mapping` | UV coordinates distorted by normals |
| `test_mask_creation` | Depth mask isolates performer |
| `test_projection_strength` | Projection intensity controlled |
| `test_normal_lighting` | Lighting applied based on normals |
| `test_fresnel_glow` | Edge glow appears on silhouette edges |
| `test_uv_scroll` | Projection scrolls with uvScrollX/Y |
| `test_uv_scale` | UV distortion scale works |
| `test_depth_contour` | Mask edge controlled by depthContour |
| `test_composite` | Final blend with main video works |
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
- [ ] Git commit with `[Phase-3] P3-VD70: depth_video_projection_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_video_projection.py` — VJLive Original implementation
- `plugins/core/depth_video_projection/__init__.py` — VJLive-2 implementation
- `plugins/core/depth_video_projection/plugin.json` — Effect manifest
- `gl_leaks.txt` — Shows `DepthVideoProjectionEffect` allocates `glGenTextures` and must free them
- `assets/gists/depth_video_projection.json` — Gist documentation

Design decisions inherited:
- Effect name: `depth_video_projection`
- Inherits from `Effect` (not `DepthEffect`)
- Uses depth texture for normal computation and masking
- Parameters: `projectionStrength`, `depthContour`, `uvScale`, `uvScrollX`, `uvScrollY`, `normalLighting`, `maskTight`, `hologramGlow`
- Allocates GL resources: main video texture, projection texture
- Shader implements normal computation, UV mapping, lighting, Fresnel glow, and compositing
- Method `_ensure_textures()` creates GPU resources
- Gist ID: `DEPTH_VIDEO_PROJECTION`

---

## Notes for Implementers

1. **Core Concept**: This effect projects a second video onto the performer's body using depth to create a 3D-like surface. The depth map provides surface geometry (normals) which are used to distort the projection UVs and apply lighting. The result is a video projected onto a 3D surface.

2. **Depth to Normal**:
   ```glsl
   float depth = texture(depth_tex, uv).r;
   float dx = dFdx(depth);
   float dy = dFdy(depth);
   vec3 normal = normalize(vec3(-dx, -dy, 1.0));
   ```
   This approximates the surface normal from depth gradient.

3. **UV Mapping**:
   The projection UV is offset by the normal's XY components:
   ```glsl
   vec2 proj_uv = uv + normal.xy * uvScale * 0.01;
   proj_uv += vec2(uvScrollX, uvScrollY) * 0.01;
   ```
   This makes the projection follow the body contours.

4. **Masking**:
   The mask isolates the performer from the background:
   ```glsl
   float mask = 1.0 - smoothstep(depthContour * 0.1, depthContour * 0.1 + 0.1, depth);
   ```
   Pixels with depth below the contour are considered background.

5. **Normal Lighting**:
   Apply a simple directional light:
   ```glsl
   vec3 light_dir = normalize(vec3(0.5, 0.5, 1.0));
   float lighting = max(0.3, dot(normal, light_dir));
   projected *= lighting * (normalLighting * 0.1);
   ```

6. **Fresnel Glow**:
   Edge glow based on normal's Z component:
   ```glsl
   float fresnel = 1.0 - abs(normal.z);
   fresnel = pow(fresnel, 3.0);
   vec3 holo = vec3(0.2, 0.6, 1.0) * fresnel * (hologramGlow * 0.1);
   ```

7. **Composite**:
   ```glsl
   vec3 result = projected * (projectionStrength * 0.1) + holo;
   float soft_mask = smoothstep(0.0, 0.15, mask);
   result = mix(background * 0.15, result, soft_mask);
   result = mix(background, result, u_mix);
   ```

8. **Shader Uniforms**:
   ```glsl
   uniform sampler2D tex0;           // Main video (background)
   uniform sampler2D tex1;           // Projection video
   uniform sampler2D depth_tex;      // Depth map
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float projectionStrength;  // 0-10
   uniform float depthContour;        // 0-10
   uniform float uvScale;             // 0-10
   uniform float uvScrollX;           // 0-10
   uniform float uvScrollY;           // 0-10
   uniform float normalLighting;      // 0-10
   uniform float maskTight;           // 0-10
   uniform float hologramGlow;        // 0-10
   ```

9. **Parameter Mapping** (0-10 → actual):
   - `projectionStrength`: 0-10 → 0-1 (divide by 10)
   - `depthContour`: 0-10 → 0-1 (divide by 10)
   - `uvScale`: 0-10 → 0-0.1 (divide by 100)
   - `uvScrollX/Y`: 0-10 → 0-0.1 (divide by 100)
   - `normalLighting`: 0-10 → 0-1 (divide by 10)
   - `maskTight`: 0-10 → 0-1 (divide by 10)
   - `hologramGlow`: 0-10 → 0-1 (divide by 10)

10. **PRESETS**:
    ```python
    PRESETS = {
        "subtle_projection": {
            "projectionStrength": 5.0, "depthContour": 5.0, "uvScale": 3.0,
            "uvScrollX": 0.0, "uvScrollY": 0.0, "normalLighting": 3.0,
            "maskTight": 6.0, "hologramGlow": 1.0,
        },
        "holographic_body": {
            "projectionStrength": 8.0, "depthContour": 4.0, "uvScale": 5.0,
            "uvScrollX": 2.0, "uvScrollY": 1.0, "normalLighting": 5.0,
            "maskTight": 5.0, "hologramGlow": 8.0,
        },
        "scrolling_projection": {
            "projectionStrength": 7.0, "depthContour": 6.0, "uvScale": 4.0,
            "uvScrollX": 8.0, "uvScrollY": 3.0, "normalLighting": 4.0,
            "maskTight": 7.0, "hologramGlow": 2.0,
        },
        "tight_mask": {
            "projectionStrength": 6.0, "depthContour": 7.0, "uvScale": 5.0,
            "uvScrollX": 0.0, "uvScrollY": 0.0, "normalLighting": 4.0,
            "maskTight": 9.0, "hologramGlow": 3.0,
        },
        "glowing_edges": {
            "projectionStrength": 5.0, "depthContour": 5.0, "uvScale": 5.0,
            "uvScrollX": 0.0, "uvScrollY": 0.0, "normalLighting": 3.0,
            "maskTight": 6.0, "hologramGlow": 10.0,
        },
    }
    ```

11. **Testing Strategy**:
    - Test with uniform depth: projection should be flat, no normal distortion
    - Test with depth gradient: projection should follow contours
    - Test projectionStrength: higher = more visible projection
    - Test depthContour: controls mask edge
    - Test uvScale: higher = more UV distortion from normals
    - Test uvScroll: projection should scroll
    - Test normalLighting: lighting should vary with normals
    - Test maskTight: controls mask softness
    - Test hologramGlow: edge glow intensity

12. **Performance**: Moderate — normal computation uses dFdx/dFdy which can be expensive at high resolution. Optimize by:
    - Using lower resolution for depth
    - Precomputing normals if depth is static
    - Simplifying lighting model

13. **Memory**: Two full-resolution textures (main + projection). Acceptable.

14. **Debug Mode**: Visualize normals (RGB), show mask, show projection UVs, show lighting.

---

## Easter Egg Idea

When `projectionStrength` is set exactly to 6.66, `depthContour` to exactly 6.66, `uvScale` to exactly 6.66, `uvScrollX` to exactly 6.66, `uvScrollY` to exactly 6.66, `normalLighting` to exactly 6.66, `maskTight` to exactly 6.66, and `hologramGlow` to exactly 6.66, the video projection enters a "sacred geometry" state where the projection strength is exactly 66.6%, the depth contour is exactly 0.666, the UV scale is exactly 0.0666, the scroll speeds are exactly 0.0666 units per frame, the normal lighting is exactly 66.6% intensity, the mask tightness is exactly 0.666, and the hologram glow is exactly 66.6% intensity. The entire projection becomes a perfect 6.66×6.66 grid of UV distortions that encode the number 666 in both space and time, creating a "projected prayer" where every pixel of the projection is exactly 666% more luminous than normal.

---

## References

- UV mapping: https://en.wikipedia.org/wiki/UV_mapping
- Surface normal: https://en.wikipedia.org/wiki/Surface_normal
- Fresnel effect: https://en.wikipedia.org/wiki/Fresnel_effect
- Depth buffer: https://en.wikipedia.org/wiki/Depth_buffer
- VJLive legacy: `plugins/vdepth/depth_video_projection.py`

---

## Implementation Tips

1. **Full Shader**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;           // Main video
   uniform sampler2D tex1;           // Projection video
   uniform sampler2D depth_tex;      // Depth map
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float time;
   
   uniform float projectionStrength;  // 0-10
   uniform float depthContour;        // 0-10
   uniform float uvScale;             // 0-10
   uniform float uvScrollX;           // 0-10
   uniform float uvScrollY;           // 0-10
   uniform float normalLighting;      // 0-10
   uniform float maskTight;           // 0-10
   uniform float hologramGlow;        // 0-10
   
   void main() {
       // Sample main video (background)
       vec3 background = texture(tex0, uv).rgb;
       
       // Get depth
       float depth = texture(depth_tex, uv).r;
       
       // Compute normal from depth gradient
       float dx = dFdx(depth);
       float dy = dFdy(depth);
       vec3 normal = normalize(vec3(-dx, -dy, 1.0));
       
       // Create mask (performer silhouette)
       float mask = 1.0 - smoothstep(depthContour * 0.1, depthContour * 0.1 + 0.1, depth);
       
       // Map projection UV with normal distortion
       vec2 proj_uv = uv + normal.xy * (uvScale * 0.01);
       proj_uv += vec2(uvScrollX, uvScrollY) * 0.01;
       
       // Sample projection video
       vec3 projected = texture(tex1, proj_uv).rgb;
       
       // Apply normal-based lighting
       vec3 light_dir = normalize(vec3(0.5, 0.5, 1.0));
       float lighting = max(0.3, dot(normal, light_dir));
       projected *= lighting * (normalLighting * 0.1 + 0.9);  // Blend with full brightness
       
       // Apply projection strength
       projected *= projectionStrength * 0.1;
       
       // Holographic Fresnel glow
       float fresnel = 1.0 - abs(normal.z);
       fresnel = pow(fresnel, 3.0);
       vec3 holo_color = vec3(0.2, 0.6, 1.0) * fresnel * (hologramGlow * 0.1);
       
       // Composite
       vec3 result = projected + holo_color;
       
       // Feather mask edges
       float soft_mask = smoothstep(0.0, 0.15, mask);
       result = mix(background * 0.15, result, soft_mask);
       
       // Final mix with u_mix
       result = mix(background, result, u_mix);
       
       fragColor = vec4(result, 1.0);
   }
   ```

2. **Python Implementation**:
   ```python
   class DepthVideoProjectionEffect(Effect):
       def __init__(self):
           super().__init__("depth_video_projection", PROJECT_VERTEX, PROJECT_FRAGMENT)
           
           self.depth_source = None
           self.depth_frame = None
           self.projection_source = None  # Second video source
           
           self.main_texture = 0
           self.projection_texture = 0
           
           self.parameters = {
               'projectionStrength': 8.0,
               'depthContour': 5.0,
               'uvScale': 5.0,
               'uvScrollX': 5.0,
               'uvScrollY': 5.0,
               'normalLighting': 4.0,
               'maskTight': 6.0,
               'hologramGlow': 3.0,
           }
           
           self.shader = None
       
       def set_projection_source(self, source):
           """Set the second video source for projection."""
           self.projection_source = source
       
       def _ensure_textures(self, width, height):
           if self.main_texture == 0:
               self.main_texture = glGenTextures(1)
               glBindTexture(GL_TEXTURE_2D, self.main_texture)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
           
           if self.projection_texture == 0:
               self.projection_texture = glGenTextures(1)
               glBindTexture(GL_TEXTURE_2D, self.projection_texture)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
               glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
       
       def process_frame(self, frame, projection_frame=None):
           h, w = frame.shape[:2]
           self._ensure_textures(w, h)
           
           # Update depth
           self._update_depth()
           
           # Use provided projection frame or get from source
           if projection_frame is None and self.projection_source:
               projection_frame = self.projection_source.get_frame()
           
           if projection_frame is None:
               projection_frame = np.zeros_like(frame)  # Black
           
           # Upload textures
           glBindTexture(GL_TEXTURE_2D, self.main_texture)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, frame)
           
           glBindTexture(GL_TEXTURE_2D, self.projection_texture)
           glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, projection_frame)
           
           # Render
           glBindFramebuffer(GL_FRAMEBUFFER, 0)
           
           self.shader.use()
           self._apply_uniforms(time, (w, h))
           
           glActiveTexture(GL_TEXTURE0)
           glBindTexture(GL_TEXTURE_2D, self.main_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "tex0"), 0)
           
           glActiveTexture(GL_TEXTURE1)
           glBindTexture(GL_TEXTURE_2D, self.projection_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "tex1"), 1)
           
           glActiveTexture(GL_TEXTURE2)
           glBindTexture(GL_TEXTURE_2D, self.depth_texture)
           glUniform1i(glGetUniformLocation(self.shader.program, "depth_tex"), 2)
           
           draw_fullscreen_quad()
           
           result = self._read_pixels()
           return result
   ```

3. **Normal Computation**: The normal is computed from depth gradient using `dFdx` and `dFdy`. This gives the rate of change in X and Y. The normal vector is `(-dx, -dy, 1)` normalized.

4. **Mask**: The mask uses `smoothstep` to create a soft edge at `depthContour`. Pixels with depth below the contour are considered foreground (performer), above are background.

5. **UV Distortion**: The normal's XY components offset the projection UV, making the projection follow the body's contours. `uvScale` controls the strength.

6. **Lighting**: Simple directional light from top-right. The dot product of normal and light direction gives lighting intensity.

7. **Fresnel Glow**: The Fresnel effect makes edges (where normal points away from camera, i.e., `normal.z` near 0) glow brighter. The glow color is cyan (0.2, 0.6, 1.0).

8. **Composite**: The projection is multiplied by `projectionStrength`, added to glow, then masked and blended with background. The background is dimmed (`background * 0.15`) under the projection to make it pop.

9. **Two Inputs**: This effect requires two video inputs. The main video is the background, and the projection video is what gets projected onto the body. The effect class should handle both.

10. **Testing**: Use a depth test pattern (e.g., a ramp or a shape). Verify:
    - Projection appears only on performer (masked)
    - Projection follows body contours (UV distortion)
    - Edges have glow
    - Lighting varies with surface orientation

11. **Performance**: Normal computation with `dFdx/dFdy` is generally fast. Should be fine at 1080p.

12. **Future Extensions**:
    - Add multiple projection sources
    - Add depth-based color tinting
    - Add shadow casting (self-shadowing from projection)
    - Add audio reactivity to projection parameters

---

## Conclusion

The DepthVideoProjectionEffect turns the performer's body into a dynamic projection screen. By using depth to derive surface normals, the effect creates a convincing illusion of video being projected onto a 3D surface. With configurable UV distortion, normal-based lighting, and holographic Fresnel glow, it's a powerful tool for creating immersive, body-mapped visuals perfect for VJ performances.

---
>>>>>>> REPLACE