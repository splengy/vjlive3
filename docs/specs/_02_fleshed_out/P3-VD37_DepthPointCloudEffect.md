# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD37_DepthPointCloudEffect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD37 — DepthPointCloudEffect

## Description

The DepthPointCloudEffect renders a 3D point cloud from a depth map, transforming 2D depth data into a volumetric point-based visualization. It projects depth pixels into 3D space using camera intrinsics and extrinsics, then renders the resulting point cloud with a full 3D pipeline (model-view-projection matrices). This effect is the foundation for 3D depth visualization in VJLive3, enabling subjects to be represented as clouds of glowing particles that can be manipulated in 3D space.

The effect supports multiple visualization modes (points, spheres, size-by-depth, color-by-depth) and integrates with the standard depth effect base class. It's GPU-accelerated using geometry shaders or vertex shaders with point sprites, capable of rendering millions of points at 60 FPS.

## What This Module Does

- Converts 2D depth map to 3D point cloud using camera projection model
- Applies model-view-projection transformations for 3D positioning
- Renders points as screen-space sprites or 3D spheres
- Supports depth-based point sizing and coloring
- Provides culling (near/far clipping) and optional point filtering
- Integrates with `DepthEffect` base class for depth source management
- Uses OpenGL vertex/geometry/fragment shaders for high performance

## What This Module Does NOT Do

- Does NOT perform mesh reconstruction (point cloud only)
- Does NOT support per-point attributes beyond position, size, color
- Does NOT implement LOD (level of detail) for distant points
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT handle point cloud animation (that's for wrappers/controllers)
- Does NOT perform point cloud segmentation or classification

---

## Detailed Behavior

### Depth to 3D Reconstruction

The effect reconstructs 3D points from a depth map using the pinhole camera model. For each pixel (u, v) with depth value z (in camera space, positive forward), the 3D point in camera space is:

```
x_camera = (u - cx) * z / fx
y_camera = (v - cy) * z / fy
z_camera = z
```

Where:
- `fx, fy` — focal lengths (in pixels)
- `cx, cy` — principal point (image center)
- `u, v` — pixel coordinates (0 to width-1, 0 to height-1)

The depth value z is obtained from the normalized depth map (0-1) using `near_clip` and `far_clip`:

```
z = near_clip + depth * (far_clip - near_clip)
```

Or using a depth scale if the depth map is in arbitrary units.

### 3D Transformation Pipeline

The point cloud is transformed by a series of matrices:

1. **Model Matrix** (`model_matrix`): Places the point cloud in world space (e.g., rotate, translate, scale)
2. **View Matrix** (`view_matrix`): Camera pose (inverse of camera world transform)
3. **Projection Matrix** (`projection_matrix`): Perspective or orthographic projection

The combined MVP matrix is `projection * view * model`. Each point's position is transformed:

```
gl_Position = MVP * vec4(x_camera, y_camera, z_camera, 1.0)
```

### Rendering Modes

The `visualization_mode` parameter controls how points are drawn:

- **0 (Points)**: Simple `gl_PointSize` squares, no shading
- **1 (Spheres)**: Point sprites with radial shading to simulate spheres
- **2 (Size by Depth)**: Point size inversely proportional to distance (closer = bigger)
- **3 (Color by Depth)**: Point color varies with depth (e.g., near=red, far=blue)
- **4-10 (Variants)**: Additional modes (e.g., normal-based shading, texture-mapped sprites)

### Point Size

The `point_size` parameter controls the base size of points (in pixels). In size-by-depth mode, the actual size is:

```
size = point_size * (near / z)  // or some function of distance
```

### Shader Architecture

The effect uses a vertex shader to generate point positions and a fragment shader to shade them. Optionally a geometry shader can expand points into quads (sprites). The basic pipeline:

**Vertex Shader**:
```glsl
uniform sampler2D u_depth_texture;
uniform float u_near_clip, u_far_clip;
uniform float u_point_size;
uniform int u_visualization_mode;
uniform mat4 u_projection_matrix;
uniform mat4 u_view_matrix;
uniform mat4 u_model_matrix;

in vec2 a_tex_coord;  // Full-screen quad vertices

out float v_depth;    // Pass depth to fragment
out vec3 v_position;  // Pass world position

void main() {
    // Sample depth at this pixel
    float depth = texture(u_depth_texture, a_tex_coord).r;
    v_depth = depth;
    
    // Reconstruct 3D point in camera space
    float z = u_near_clip + depth * (u_far_clip - u_near_clip);
    float x = (a_tex_coord.x - u_cx) * z / u_fx;
    float y = (a_tex_coord.y - u_cy) * z / u_fy;
    
    // Transform to world space
    vec4 world_pos = u_model_matrix * vec4(x, y, z, 1.0);
    v_position = world_pos.xyz;
    
    // Apply view-projection
    gl_Position = u_projection_matrix * u_view_matrix * world_pos;
    
    // Set point size
    gl_PointSize = u_point_size;
    if (u_visualization_mode == 2) {
        gl_PointSize *= u_near_clip / max(z, 0.1);  // Size inversely proportional to distance
    }
}
```

**Fragment Shader**:
```glsl
in float v_depth;
in vec3 v_position;

uniform int u_visualization_mode;
uniform vec3 u_color_near;  // Color for near points
uniform vec3 u_color_far;   // Color for far points

out vec4 frag_color;

void main() {
    // For point sprites, gl_PointCoord gives coordinate within the point
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) discard;  // Circle shape
    
    // Shade based on mode
    if (u_visualization_mode == 1) {
        // Sphere shading
        float z = 1.0 - dist * 2.0;  // Simple hemisphere
        frag_color = vec4(z, z, z, 1.0);
    } else if (u_visualization_mode == 3) {
        // Color by depth
        float t = v_depth;  // 0-1
        frag_color = vec4(mix(u_color_near, u_color_far, t), 1.0);
    } else {
        // Simple white point
        frag_color = vec4(1.0, 1.0, 1.0, 1.0);
    }
}
```

### Camera Intrinsics

The effect needs the camera's intrinsic matrix (fx, fy, cx, cy). These can be provided as separate uniforms or as a 3x3 matrix. They are essential for correct 3D reconstruction. The values depend on the depth camera (Astra, RealSense, etc.) and must be calibrated.

### Culling

Points outside the near/far clipping planes are discarded in the vertex shader or via depth test. Additionally, points with invalid depth (e.g., 0 or NaN) should be culled.

---

## Public Interface

```python
class DepthPointCloudEffect(DepthEffect):
    def __init__(self) -> None: ...
    def set_camera_intrinsics(self, fx: float, fy: float, cx: float, cy: float) -> None: ...
    def get_camera_intrinsics(self) -> Tuple[float, float, float, float]: ...
    def set_matrices(self, projection: np.ndarray, view: np.ndarray, model: np.ndarray) -> None: ...
    def get_matrices(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]: ...
    def set_visualization_mode(self, mode: int) -> None: ...
    def get_visualization_mode(self) -> int: ...
    def set_point_size(self, size: float) -> None: ...
    def get_point_size(self) -> float: ...
    def set_color_gradient(self, near_color: Tuple[float, float, float], far_color: Tuple[float, float, float]) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (optional, for compositing) |
| **Output** | `np.ndarray` | Rendered point cloud (HxWxC, RGB) |

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `point_size` | float | 3.0 | 0.1 - 20.0 | Base point size in pixels |
| `visualization_mode` | int | 0 | 0-4 | Rendering mode: 0=points, 1=spheres, 2=size-by-depth, 3=color-by-depth |
| `near_clip` | float | 0.1 | 0.0 - 1.0 | Near clipping distance (normalized) |
| `far_clip` | float | 1.0 | 0.0 - 1.0 | Far clipping distance (normalized) |
| `depth_scale` | float | 1.0 | 0.1 - 10.0 | Depth multiplier |
| `color_near_r`, `color_near_g`, `color_near_b` | float | 1.0, 0.0, 0.0 | 0.0-1.0 | Color for near points (red) |
| `color_far_r`, `color_far_g`, `color_far_b` | float | 0.0, 0.0, 1.0 | 0.0-1.0 | Color for far points (blue) |

**Inherited from DepthEffect**: `near_clip`, `far_clip`, `depth_scale`, `invert_depth`

---

## State Management

**Persistent State:**
- `_camera_intrinsics: Tuple[float, float, float, float]` — fx, fy, cx, cy
- `_projection_matrix: np.ndarray` — 4x4 projection matrix
- `_view_matrix: np.ndarray` — 4x4 view matrix
- `_model_matrix: np.ndarray` — 4x4 model matrix
- `_point_size: float` — Point size parameter
- `_visualization_mode: int` — Current rendering mode
- `_color_near: Tuple[float, float, float]` — Near color
- `_color_far: Tuple[float, float, float]` — Far color
- `_depth_texture: int` — From base class
- `_shader: ShaderProgram` — Compiled shader

**Initialization:**
- Default intrinsics: fx=fy=500, cx=width/2, cy=height/2 (must be updated)
- Default matrices: identity
- Default point size: 3.0
- Default visualization mode: 0 (points)

**Cleanup:**
- Delete shader
- Call `super().cleanup()` to release depth texture

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_R8/GL_R16 | frame size | From base class |
| Shader program | GLSL | vertex + fragment | N/A | Init once |
| Vertex buffer (optional) | GL_ARRAY_BUFFER | full-screen quad | 6 vertices (2 triangles) | Init once |

**Memory Budget (1080p):**
- Depth texture: ~2.1 MB (GL_R8)
- Shader: negligible
- Total: ~2.1 MB + overhead

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Camera intrinsics not set | Use defaults (may be wrong) | Call `set_camera_intrinsics()` |
| Matrices not set | Use identity matrices | Set proper matrices for scene |
| Depth texture missing | `RuntimeError("No depth data")` | Call `update_depth_data()` first |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid visualization mode | Clamp to [0,4] or raise `ValueError` | Document valid modes |
| Point size too large | May cause rendering artifacts | Clamp to reasonable max (e.g., 100) |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread with the OpenGL context. The `_depth_texture` is shared with base class and updated each frame, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (1080p, ~2M points):**
- Vertex shader (full-screen quad, per-pixel point generation): ~2-3 ms
- Fragment shader (per-point shading): ~1-2 ms
- Total: ~3-5 ms on discrete GPU, ~8-12 ms on integrated GPU

**Optimization Strategies:**
- Use point sprites (hardware `gl_PointSize`) instead of geometry shader for simplicity
- Early fragment kill if point is outside circle (for sphere mode)
- Use `GL_R8` for depth texture to reduce bandwidth
- Consider downsampling depth for lower point count (e.g., every other pixel)
- Use instanced rendering if points are pre-computed (but depth changes each frame)

---

## Integration Checklist

- [ ] Camera intrinsics (fx, fy, cx, cy) are set correctly for the depth camera
- [ ] Projection, view, and model matrices are provided each frame (or updated when changed)
- [ ] Depth source is connected and providing data
- [ ] `process_frame()` is called after `update_depth_data()`
- [ ] Visualization mode and point size are set appropriately
- [ ] Color gradient is defined if using color-by-depth mode
- [ ] `cleanup()` is called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_camera_intrinsics` | Intrinsics are stored and can be retrieved |
| `test_set_matrices` | Matrices are stored correctly |
| `test_set_visualization_mode` | Mode can be changed and clamped |
| `test_set_point_size` | Point size updates |
| `test_set_color_gradient` | Colors are stored |
| `test_process_frame_no_depth` | Raises error if depth source not set |
| `test_process_frame_basic` | Returns frame of correct shape |
| `test_point_generation` | Points are generated for valid depth |
| `test_point_count` | Number of points matches depth map non-zero pixels |
| `test_3d_reconstruction` | Points have correct 3D positions (synthetic depth) |
| `test_visualization_modes` | Each mode produces distinct output |
| `test_size_by_depth` | Closer points appear larger |
| `test_color_by_depth` | Near points are near_color, far points are far_color |
| `test_culling` | Points outside near/far are not rendered |
| `test_invalid_depth` | Zero/NaN depth pixels are culled |
| `test_matrix_transformation` | Points are correctly transformed by MVP |
| `test_cleanup` | All GPU resources released |
| `test_no_memory_leak` | Repeated init/cleanup doesn't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD37: depth_point_cloud_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/depth_effects.py` — Contains `DepthPointCloudEffect` (VJLive-2)
- `plugins/vdepth/depth_effects.py` — Original VJLive depth effects
- `core/shader_pipeline_verifier.py` — References required uniforms: `min_depth`, `max_depth`, `point_size`, `visualization_mode`, `projection_matrix`, `view_matrix`, `model_matrix`
- `JUNK/one_off_scripts/test_depth_import.py` — Test showing instantiation and parameter usage

Design decisions inherited:
- Effect name: `DepthPointCloudEffect`
- Inherits from `DepthEffect` (or `Effect` in legacy)
- Requires camera intrinsics (fx, fy, cx, cy)
- Uses MVP matrices for 3D transformation
- Parameters: `point_size`, `visualization_mode`, `min_depth`, `max_depth`
- Supports multiple visualization modes (points, spheres, size/depth, color/depth)
- Vertex shader generates points from depth map (full-screen quad)

---

## Notes for Implementers

1. **Full-Screen Quad Approach**: The simplest implementation renders a full-screen quad where each fragment generates a point. The vertex shader passes texture coordinates; the fragment shader samples depth, reconstructs 3D, and outputs a point via `gl_Position` and `gl_PointSize`. This is a fragment-shader-based point generation (like a compute shader but using rasterization). However, this approach has limitations: you can't easily cull points before fragment shading, and you're shading every pixel even if depth is invalid.

2. **Vertex Buffer Approach**: Alternatively, pre-compute a list of valid points (where depth is valid) and render with `glDrawArrays(GL_POINTS)`. This requires generating a vertex buffer each frame (or using a compute shader). The full-screen quad method is simpler but less efficient for sparse depth.

3. **Depth Validation**: Many depth pixels may be invalid (0, NaN, or sentinel value). These should be culled. In the fragment approach, you can `discard` early. In the vertex buffer approach, only include valid points.

4. **Camera Intrinsics**: The depth camera's intrinsic matrix is crucial. It's usually a 3x3 matrix:
   ```
   [fx,  0, cx]
   [ 0, fy, cy]
   [ 0,  0,  1]
   ```
   You can store as four floats (fx, fy, cx, cy) or as a uniform mat3. Provide a method `set_camera_intrinsics(fx, fy, cx, cy)`.

5. **Matrices**: The effect needs three 4x4 matrices:
   - `projection_matrix`: Typically perspective from camera intrinsics: `f = 1/tan(fov/2)`, but you can compute from fx, fy, near, far.
   - `view_matrix`: Camera world-to-local transform (inverse of camera pose)
   - `model_matrix`: Object/world transform (usually identity for point cloud in camera space)
   Provide a method `set_matrices(projection, view, model)`.

6. **Visualization Modes**:
   - Mode 0: `gl_PointSize = point_size; frag_color = white;`
   - Mode 1: Sphere shading using `gl_PointCoord` to compute distance from center, apply radial gradient.
   - Mode 2: `gl_PointSize = point_size * (near / z)`; clamp to reasonable range.
   - Mode 3: `color = mix(near_color, far_color, depth)`; pass depth from vertex to fragment.

7. **Shader Precision**: Use `highp` for depth and matrix calculations to avoid artifacts. Point size is integer but can be float.

8. **Performance**: The full-screen quad approach processes every pixel (2M for 1080p). If only 50% of pixels have valid depth, you're wasting half the fragments. Consider using a compute shader or vertex buffer for better efficiency. But for VJ use, full-screen is simpler and may be fast enough.

9. **Alternative: Geometry Shader**: You can use a geometry shader to expand points into quads, but geometry shaders are slow on some GPUs. Better to use point sprites (`gl_PointSize`) and fragment shader.

10. **Testing**: Create synthetic depth maps:
    - Plane at constant depth: all points at same z
    - Sphere: depth varies with distance from center
    - Gradient: linear depth ramp
    Verify that 3D positions are correct by projecting back or checking known values.

11. **Matrix Computation**: You can compute the projection matrix from intrinsics:
    ```python
    fx, fy, cx, cy = intrinsics
    near, far = 0.1, 100.0
    P = np.array([
        [fx/cx, 0, 0, 0],
        [0, fy/cy, 0, 0],
        [0, 0, -(far+near)/(far-near), -2*far*near/(far-near)],
        [0, 0, -1, 0]
    ])
    ```
    But it's easier to let the pipeline provide a standard OpenGL projection matrix.

12. **Coordinate System**: Be clear about coordinate conventions. Typically:
    - Camera space: X right, Y up, Z forward (right-handed)
    - Depth map: u right, v down (image coordinates)
    - OpenGL NDC: X right, Y up, Z [-1,1] (right-handed clip space)
    Ensure your matrices match.

13. **Debugging**: Provide a debug mode that outputs depth as color, or point count overlay, to verify correct reconstruction.

14. **Audio Reactivity**: This effect doesn't directly use audio, but point size or color could be modulated by audio features. Consider adding optional audio reactivity.

15. **Future Extensions**: Could add:
    - Point cloud animation (rotate, translate, scale over time)
    - Per-point color from source video (project video texture onto points)
    - Point size attenuation based on distance
    - LOD: skip points based on screen-space size

---

## Easter Egg Idea

When `point_size` is set exactly to 3.33, `visualization_mode` to exactly 7 (which is out of range but clamped to 4), and the camera intrinsics have `fx/fy` exactly equal to the golden ratio (1.618), and the depth map contains a perfect gradient, the point cloud briefly forms a perfect golden spiral in 3D space that lasts exactly 6.66 seconds before returning to normal. The spiral is visible only in sphere mode with a specific color gradient but subtly influences the point distribution in a way that VJs can feel as a "harmonic convergence."

---

## References

- Pinhole camera model: https://en.wikipedia.org/wiki/Pinhole_camera_model
- OpenGL point sprites: https://learnopengl.com/Advanced-OpenGL/Point-Sprites
- Depth camera intrinsics: Intel RealSense, Azure Kinect documentation
- VJLive legacy: `core/effects/depth_effects.py` (DepthPointCloudEffect)

---

## Implementation Tips

1. **Vertex Shader (Full-Screen Quad)**:
   ```glsl
   #version 330 core
   layout (location = 0) in vec2 a_position;  // Full-screen quad vertices
   layout (location = 1) in vec2 a_tex_coord;
   
   out float v_depth;
   out vec3 v_world_pos;
   
   uniform sampler2D u_depth_texture;
   uniform float u_near_clip, u_far_clip;
   uniform float u_fx, u_fy, u_cx, u_cy;
   uniform mat4 u_model_matrix;
   uniform mat4 u_view_matrix;
   uniform mat4 u_projection_matrix;
   uniform float u_point_size;
   uniform int u_visualization_mode;
   
   void main() {
       float depth = texture(u_depth_texture, a_tex_coord).r;
       v_depth = depth;
       
       // Skip invalid depth
       if (depth <= 0.0) {
           gl_Position = vec4(0.0, 0.0, 2.0, 1.0);  // Clip space outside
           return;
       }
       
       // Reconstruct camera-space point
       float z = u_near_clip + depth * (u_far_clip - u_near_clip);
       float x = (a_tex_coord.x * u_frame_width - u_cx) * z / u_fx;
       float y = (a_tex_coord.y * u_frame_height - u_cy) * z / u_fy;
       
       // Transform to world
       vec4 world_pos = u_model_matrix * vec4(x, y, z, 1.0);
       v_world_pos = world_pos.xyz;
       
       // MVP
       gl_Position = u_projection_matrix * u_view_matrix * world_pos;
       
       // Point size
       gl_PointSize = u_point_size;
       if (u_visualization_mode == 2) {
           gl_PointSize = u_point_size * (u_near_clip / max(z, 0.1));
       }
   }
   ```

2. **Fragment Shader**:
   ```glsl
   #version 330 core
   in float v_depth;
   in vec3 v_world_pos;
   
   uniform int u_visualization_mode;
   uniform vec3 u_color_near;
   uniform vec3 u_color_far;
   
   out vec4 frag_color;
   
   void main() {
       if (u_visualization_mode == 0) {
           frag_color = vec4(1.0, 1.0, 1.0, 1.0);
       } else if (u_visualization_mode == 1) {
           // Sphere
           vec2 coord = gl_PointCoord - vec2(0.5);
           float dist = length(coord);
           if (dist > 0.5) discard;
           float shade = 1.0 - dist * 2.0;
           frag_color = vec4(shade, shade, shade, 1.0);
       } else if (u_visualization_mode == 2) {
           frag_color = vec4(1.0, 1.0, 1.0, 1.0);
       } else if (u_visualization_mode == 3) {
           float t = v_depth;
           frag_color = vec4(mix(u_color_near, u_color_far, t), 1.0);
       }
   }
   ```

3. **Python Setup**:
   ```python
   class DepthPointCloudEffect(DepthEffect):
       def __init__(self):
           super().__init__("depth_point_cloud", POINT_CLOUD_VERTEX, POINT_CLOUD_FRAGMENT)
           self._point_size = 3.0
           self._visualization_mode = 0
           self._color_near = (1.0, 0.0, 0.0)
           self._color_far = (0.0, 0.0, 1.0)
           # Default intrinsics (should be updated)
           self._fx, self._fy, self._cx, self._cy = 500.0, 500.0, 320.0, 240.0
           # Matrices
           self._projection_matrix = np.eye(4, dtype=np.float32)
           self._view_matrix = np.eye(4, dtype=np.float32)
           self._model_matrix = np.eye(4, dtype=np.float32)
       
       def process_frame(self, frame):
           self.update_depth_data()
           self.shader.set_uniform('u_depth_texture', self.get_depth_texture())
           self.shader.set_uniform('u_fx', self._fx)
           self.shader.set_uniform('u_fy', self._fy)
           self.shader.set_uniform('u_cx', self._cx)
           self.shader.set_uniform('u_cy', self._cy)
           self.shader.set_uniform('u_point_size', self._point_size)
           self.shader.set_uniform('u_visualization_mode', self._visualization_mode)
           self.shader.set_uniform('u_color_near', self._color_near)
           self.shader.set_uniform('u_color_far', self._color_far)
           self.shader.set_uniform('u_projection_matrix', self._projection_matrix)
           self.shader.set_uniform('u_view_matrix', self._view_matrix)
           self.shader.set_uniform('u_model_matrix', self._model_matrix)
           # Render full-screen quad
           self.render_fullscreen_quad()
           return self.get_output()
   ```

4. **Full-Screen Quad**: You need a vertex buffer with 6 vertices (two triangles) covering the entire screen, with texture coordinates. This can be created once and reused.

5. **Depth Culling**: In the vertex shader, if depth is invalid, set `gl_Position` to a point outside clip space (e.g., `vec4(0,0,2,1)` which maps to z=1 in NDC, beyond far plane). Or use `discard` in fragment after checking `v_depth`.

6. **Point Size Limit**: OpenGL has a maximum point size (often 64 or 256 pixels). Query with `GL_POINT_SIZE_RANGE` and clamp if needed.

7. **Matrix Order**: Ensure you're multiplying matrices in the correct order: `projection * view * model * position`. OpenGL uses column-major order; numpy is row-major by default. Transpose or use `glUniformMatrix4fv` with `transpose=True` if needed.

8. **Testing with Known Data**: Create a depth map with a single plane at z=1.0. With identity matrices and correct intrinsics, the points should all land at the same depth in NDC. Check that `gl_Position.z` is consistent.

9. **Performance**: The full-screen quad approach is fill-rate bound. At 1080p, 2M fragments per frame. If point size is large, fragment shader runs more. Should still be okay on modern GPUs.

10. **Documentation**: Clearly document the required camera intrinsics and how to obtain them from the depth camera's calibration. Provide defaults for common cameras (Astra: fx=fy~570, cx~320, cy~240 for 640x480).

---

## Conclusion

The DepthPointCloudEffect is a fundamental building block for 3D depth visualization. By reconstructing 3D points from depth and rendering them with standard graphics pipelines, it enables a wide range of volumetric effects. The effect must be carefully implemented to handle camera calibration, matrix transformations, and efficient rendering. With proper intrinsics and matrices, it produces stunning point cloud visuals that can be further enhanced with audio reactivity and post-processing.

---
>>>>>>> REPLACE