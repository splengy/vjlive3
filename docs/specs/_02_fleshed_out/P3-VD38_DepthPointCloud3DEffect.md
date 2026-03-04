# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD38_DepthPointCloud3DEffect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD38 — DepthPointCloud3DEffect

## Description

The DepthPointCloud3DEffect is an advanced point cloud renderer that combines depth map geometry with RGB color from a synchronized color camera. It extends the basic `DepthPointCloudEffect` by projecting color texture coordinates onto the 3D points, enabling fully colored point clouds that match the real-world scene. This effect is essential for creating vibrant, photorealistic volumetric visualizations where each point carries both position and color information.

The effect reconstructs 3D points from depth, then samples the corresponding color frame (using camera calibration to map depth pixel to color pixel) to assign per-point colors. The result is a dense, colored point cloud that can be further transformed and rendered with various visualization modes.

## What This Module Does

- Reconstructs 3D points from depth map (same as `DepthPointCloudEffect`)
- Synchronizes with a color camera to obtain RGB values for each point
- Maps depth pixel coordinates to color pixel coordinates using camera extrinsics/intrinsics
- Supports multiple rendering modes: colored points, size-by-depth, color-by-depth, etc.
- Handles color frame resolution differences (depth and color may have different resolutions)
- Integrates with `DepthEffect` base class and requires both depth and color sources
- GPU-accelerated rendering with point sprites or geometry shader

## What This Module Does NOT Do

- Does NOT perform color space conversion (assumes color frame is RGB)
- Does NOT handle color camera exposure/white balance (relies on color source)
- Does NOT perform point cloud segmentation or classification
- Does NOT support per-point custom colors (only from color frame)
- Does NOT implement texture mapping onto 3D geometry (point sprites only)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions

---

## Detailed Behavior

### Depth + Color Fusion

The effect requires two synchronized sources:
- `AstraDepthSource` — Provides depth map (2D, single channel)
- `AstraColorSource` (or compatible) — Provides color frame (2D, 3-channel RGB)

Both sources must be from the same physical camera system to ensure spatial alignment. The effect calls `get_depth_frame()` and `get_color_frame()` each frame.

### Coordinate Mapping

Depth and color cameras may have different:
- Resolution (e.g., depth 640×480, color 1920×1080)
- Intrinsics (fx, fy, cx, cy)
- Extrinsics (relative pose)

To map a depth pixel (u_d, v_d) to the corresponding color pixel (u_c, v_c), you need the camera transformation. If the depth and color cameras are rigidly mounted with known relative pose, you can compute:

1. Reconstruct 3D point in depth camera space:
   ```
   z_d = depth_value (in camera space, meters)
   x_d = (u_d - cx_d) * z_d / fx_d
   y_d = (v_d - cy_d) * z_d / fy_d
   P_d = [x_d, y_d, z_d, 1]^T
   ```

2. Transform to color camera space:
   ```
   P_c = T_color_from_depth * P_d
   ```
   Where `T_color_from_depth` is a 4×4 transformation matrix (from depth camera to color camera coordinate system).

3. Project to color pixel coordinates:
   ```
   u_c = (fx_c * P_c.x / P_c.z) + cx_c
   v_c = (fy_c * P_c.y / P_c.z) + cy_c
   ```

If the depth and color cameras are the same (e.g., RealSense RGB-D sensor), the mapping may be identity or a simple scale/offset. The effect should allow setting a custom mapping function or matrix.

### Color Sampling

Once (u_c, v_c) is computed, sample the color frame:
```python
color = color_frame[v_c, u_c]  # (BGR or RGB)
```

If the coordinates are out of bounds, use nearest neighbor or clamp. If the depth point is invalid (z=0 or NaN), skip color assignment.

### Rendering Pipeline

The vertex shader processes each depth pixel (full-screen quad approach):

1. Sample depth at (u_d, v_d)
2. Reconstruct 3D point in depth camera space
3. Transform to world space (using view/projection matrices)
4. Compute color by mapping to color frame and sampling RGB
5. Pass color to fragment shader
6. Set point size (with optional size-by-depth)
7. Output `gl_Position`

Fragment shader:
- For point sprites, use `gl_PointCoord` to shape the point
- Output the interpolated color (or apply shading)

### Visualization Modes

Similar to `DepthPointCloudEffect` but with color:

- **0 (Colored)**: Use color from color frame (default)
- **1 (Spheres + Color)**: Sphere shading with color texture
- **2 (Size by Depth + Color)**: Point size varies with distance, color from frame
- **3 (Color by Depth)**: Override color with depth-based gradient (ignore color frame)
- **4-10 (Variants)**: Additional modes (e.g., normal-based, texture-mapped)

### Shader Uniforms

Additional uniforms beyond `DepthPointCloudEffect`:

| Uniform | Type | Description |
|---------|------|-------------|
| `u_color_texture` | `sampler2D` | Color camera frame texture |
| `u_color_width` | `int` | Color frame width |
| `u_color_height` | `int` | Color frame height |
| `u_color_intrinsics` | `vec4` | (fx_c, fy_c, cx_c, cy_c) |
| `u_T_color_from_depth` | `mat4` | Transformation from depth to color camera space |
| `u_color_mapping_mode` | `int` | How to map depth→color: 0=direct, 1=calibrated, etc. |

---

## Public Interface

```python
class DepthPointCloud3DEffect(DepthPointCloudEffect):
    def __init__(self) -> None: ...
    def set_color_source(self, source: ColorCameraSource) -> None: ...
    def get_color_source(self) -> Optional[ColorCameraSource]: ...
    def set_color_intrinsics(self, fx: float, fy: float, cx: float, cy: float) -> None: ...
    def get_color_intrinsics(self) -> Tuple[float, float, float, float]: ...
    def set_color_transform(self, T: np.ndarray) -> None: ...
    def get_color_transform(self) -> np.ndarray: ...
    def set_color_mapping_mode(self, mode: int) -> None: ...
    def get_color_mapping_mode(self) -> int: ...
    def update_color_data(self) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (optional) |
| **Output** | `np.ndarray` | Rendered colored point cloud (HxWxC, RGB) |

---

## Parameters

Inherits all parameters from `DepthPointCloudEffect`:
- `point_size` (float, default 3.0, range 0.1-20.0)
- `visualization_mode` (int, default 0, range 0-10)
- `near_clip`, `far_clip`, `depth_scale`, `invert_depth`
- `color_near`, `color_far` (for depth-based coloring fallback)

Additional parameters:

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `color_mapping_mode` | int | 0 | 0-2 | 0=direct (identity), 1=calibrated (use T matrix), 2=approximate (scale/offset) |
| `color_alpha` | float | 1.0 | 0.0-1.0 | Opacity of color frame (for blending with depth-only color) |

---

## State Management

**Persistent State (in addition to base class):**
- `_color_source: Optional[ColorCameraSource]` — Color camera provider
- `_color_frame: Optional[np.ndarray]` — Cached color frame (HxWx3)
- `_color_texture: int` — OpenGL texture for color frame
- `_color_intrinsics: Tuple[float, float, float, float]` — fx_c, fy_c, cx_c, cy_c
- `_color_transform: np.ndarray` — 4×4 matrix (depth→color)
- `_color_mapping_mode: int` — Mapping mode

**Per-Frame:**
- Update color texture if color frame changed
- Map depth pixels to color coordinates and sample color

**Initialization:**
- Color texture initially 0 (created on first update)
- Default color intrinsics: same as depth intrinsics (assume same camera)
- Default color transform: identity matrix
- Default color mapping mode: 0 (direct)

**Cleanup:**
- Delete color texture if `_color_texture != 0`
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_R8/GL_R16 | depth size | From base class |
| Color texture | GL_TEXTURE_2D | GL_RGBA8 | color size | Created on first color update |
| Shader program | GLSL | vertex + fragment | N/A | Init once |
| Vertex buffer | GL_ARRAY_BUFFER | full-screen quad | 6 vertices | Init once |

**Memory Budget (1080p color, 640×480 depth):**
- Depth texture: ~0.3 MB (GL_R8, 640×480)
- Color texture: ~8.3 MB (GL_RGBA8, 1920×1080)
- Total: ~8.6 MB + overhead

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Color source not set | Use depth-only fallback (white points) | Call `set_color_source()` |
| Color frame missing | Use white points, log warning | Ensure color source is providing |
| Color texture creation fails | `RuntimeError` (OOM) | Reduce resolution or abort |
| Intrinsics mismatch | Points may be misaligned | Set correct intrinsics for both cameras |
| Transform not set | Use identity (may misalign) | Set `_color_transform` if cameras are not coincident |
| Color coordinates out of bounds | Clamp to color frame edges | Check mapping logic |
| Color frame resolution change | Recreate color texture | Handle resize in `update_color_data()` |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and state mutations must occur on the thread with the OpenGL context. The `_color_frame` and `_depth_frame` caches are mutated each frame, so concurrent calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (1080p color, VGA depth, ~300K points):**
- Vertex shader (depth→3D + color mapping): ~3-4 ms
- Fragment shader (colored point sprites): ~1-2 ms
- Color texture upload (if updated): ~1-2 ms
- Total: ~5-8 ms on discrete GPU, ~12-18 ms on integrated GPU

**Optimization Strategies:**
- Only update color texture if color frame changed (compare frame counters)
- Use `GL_RGBA8` for color (standard) or `GL_RGB8` if alpha not needed
- Downsample color frame if high resolution not required
- Precompute color mapping lookup table if intrinsics/transform are constant
- Use point sprites (hardware `gl_PointSize`) for simplicity

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Color source set and providing color frames
- [ ] Depth camera intrinsics set (fx_d, fy_d, cx_d, cy_d)
- [ ] Color camera intrinsics set (fx_c, fy_c, cx_c, cy_c)
- [ ] Color transform matrix set if cameras are not identical
- [ ] Color mapping mode selected (0=direct, 1=calibrated)
- [ ] Visualization mode set appropriately (0=colored, 1=spheres+color, etc.)
- [ ] `process_frame()` called each frame after `update_depth_data()` and `update_color_data()`
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_color_source` | Color source stored and can be retrieved |
| `test_set_color_intrinsics` | Color intrinsics stored correctly |
| `test_set_color_transform` | Transform matrix stored |
| `test_set_color_mapping_mode` | Mode can be changed |
| `test_update_color_data_no_source` | Handles missing color source gracefully |
| `test_update_color_data_with_source` | Color texture created/updated |
| `test_process_frame_no_color` | Falls back to white points without crashing |
| `test_color_mapping_direct` | Direct mode: depth pixel → same pixel in color frame |
| `test_color_mapping_calibrated` | Calibrated mode: uses transform and intrinsics |
| `test_color_sampling` | Color values correctly sampled from color frame |
| `test_invalid_depth_culling` | Points with invalid depth not rendered |
| `test_visualization_modes` | Colored, spheres+color, size+depth+color modes work |
| `test_color_texture_upload` | Color texture uploaded with correct format/size |
| `test_color_frame_resize` | Color texture recreated on resolution change |
| `test_cleanup` | All GPU resources released (depth + color textures) |
| `test_no_memory_leak` | Repeated init/cleanup cycles don't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD38: depth_point_cloud_3d_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/depth_effects.py` — Contains `DepthPointCloud3DEffect` (VJLive-2)
- `plugins/vdepth/depth_effects.py` — Original VJLive depth effects
- `tests/test_depth_restoration.py` — Tests showing RGB color mode support
- `core/shader_pipeline_verifier.py` — References `DepthPointCloudEffect` and `DepthPointCloud3DEffect` as separate classes

Design decisions inherited:
- Effect name: `DepthPointCloud3DEffect`
- Inherits from `DepthPointCloudEffect` (which inherits from `DepthEffect`)
- Requires both depth and color sources
- Supports `color_mode` parameter (default 1.0 for RGB)
- Uses color frame to color points (as opposed to depth-only point cloud)
- May have additional uniforms for color texture and mapping

---

## Notes for Implementers

1. **Inheritance**: This class should inherit from `DepthPointCloudEffect` and extend it with color support. Override `__init__` to add color-related state, and override `process_frame()` to also update color data.

2. **Color Source Interface**: The color source should provide `get_color_frame()` returning an HxWx3 numpy array (RGB, uint8 or float32). It may be the same physical camera as depth (e.g., RealSense) or a separate color camera.

3. **Synchronization**: Depth and color frames must be temporally synchronized. The pipeline should ensure that when `process_frame()` is called, the depth and color sources provide frames from the same moment. If not, timestamps should be checked and frames dropped to maintain sync.

4. **Color Texture Format**: Use `GL_RGBA8` for color (even if source is RGB, add alpha=255). Upload with `glTexImage2D` using `GL_RGBA` format. Convert numpy array to contiguous bytes.

5. **Color Mapping Modes**:
   - Mode 0 (Direct): `u_c = u_d`, `v_c = v_d` (assumes same resolution and alignment)
   - Mode 1 (Calibrated): Use `_color_transform` and intrinsics to compute (u_c, v_c)
   - Mode 2 (Approximate): Simple scale/offset if cameras are roughly aligned
   Implement as a function in the vertex shader or on CPU (CPU mapping slower).

6. **Shader Changes**: The vertex shader needs to:
   - Sample color texture at mapped coordinates
   - Pass color to fragment shader as `out vec3 v_color`
   - Possibly handle color frame resolution differences (pass `u_color_width/height`)

7. **Color Frame Resolution**: The color frame may be larger or smaller than depth frame. The mapping should account for this. If using calibrated mode, the intrinsics already encode resolution via `cx, cy`. For direct mode, you may need to scale coordinates: `u_c = u_d * (color_width / depth_width)`.

8. **Performance**: Mapping depth→color for every pixel (full-screen quad) is cheap (a few arithmetic ops). The main cost is color texture upload if the color frame changes every frame. Use a frame counter or timestamp to avoid unnecessary uploads.

9. **Testing**: Create synthetic test where depth is a plane and color is a known gradient. Verify that points get correct colors after mapping. Test with offset/scale to simulate misalignment and ensure transform corrects it.

10. **Debugging**: Provide a debug mode that visualizes the color mapping (e.g., output mapped UV coordinates as color) to verify alignment.

11. **Fallback**: If color source is not set or returns None, the effect should still work (render white or depth-colored points) rather than crash. This allows using the same effect in setups without a color camera.

12. **Memory**: The color texture can be large (e.g., 8 MB for 1080p). Consider allowing a lower resolution mode for performance.

13. **Color Space**: Assume sRGB. If color frame is in a different color space, conversion may be needed (but usually handled upstream).

14. **Audio Reactivity**: Not directly used, but point size or color intensity could be modulated by audio. Consider adding optional audio reactivity like parent classes.

15. **Future Extensions**: Could add:
    - Per-point alpha from depth (e.g., farther points more transparent)
    - Color correction (brightness, contrast, saturation)
    - Chroma key to make certain colors transparent
    - Point size based on color intensity

---
-

## References

- Pinhole camera model and stereo rectification: https://en.wikipedia.org/wiki/Stereo_camera
- OpenGL texture upload: https://learnopengl.com/Advanced-OpenGL/Cubemaps
- Depth camera calibration: Intel RealSense SDK, Azure Kinect SDK
- VJLive legacy: `core/effects/depth_effects.py` (DepthPointCloud3DEffect)

---

## Implementation Tips

1. **Class Structure**:
   ```python
   class DepthPointCloud3DEffect(DepthPointCloudEffect):
       def __init__(self):
           super().__init__()
           self._color_source = None
           self._color_frame = None
           self._color_texture = 0
           self._color_intrinsics = (500.0, 500.0, 320.0, 240.0)  # defaults
           self._color_transform = np.eye(4, dtype=np.float32)
           self._color_mapping_mode = 0  # 0=direct, 1=calibrated
       
       def set_color_source(self, source):
           self._color_source = source
       
       def update_color_data(self):
           if self._color_source is None:
               return  # Will use white fallback
           color = self._color_source.get_color_frame()
           if color is None:
               return
           self._color_frame = color
           self._update_color_texture(color)
       
       def _update_color_texture(self, color: np.ndarray):
           if self._color_texture == 0:
               glGenTextures(1, [self._color_texture])
           glBindTexture(GL_TEXTURE_2D, self._color_texture)
           # Set parameters, upload with glTexImage2D or glTexSubImage2D
           # ...
       
       def process_frame(self, frame):
           # Update depth (from parent) and color
           self.update_depth_data()
           self.update_color_data()
           
           # Set shader uniforms
           self.shader.set_uniform('u_depth_texture', self.get_depth_texture())
           if self._color_texture != 0:
               self.shader.set_uniform('u_color_texture', self._color_texture)
           self.shader.set_uniform('u_color_intrinsics', self._color_intrinsics)
           self.shader.set_uniform('u_T_color_from_depth', self._color_transform)
           self.shader.set_uniform('u_color_mapping_mode', self._color_mapping_mode)
           
           # Call parent to set other uniforms and render
           super().process_frame(frame)
       
       def cleanup(self):
           if self._color_texture != 0:
               glDeleteTextures(1, [self._color_texture])
               self._color_texture = 0
           super().cleanup()
   ```

2. **Vertex Shader Extension**:
   ```glsl
   uniform sampler2D u_color_texture;
   uniform vec4 u_color_intrinsics;  // fx, fy, cx, cy
   uniform mat4 u_T_color_from_depth;
   uniform int u_color_mapping_mode;
   uniform int u_color_width, u_color_height;
   
   out vec3 v_color;
   
   void main() {
       // ... (depth reconstruction from parent)
       
       // Compute color texture coordinates
       vec2 color_uv;
       if (u_color_mapping_mode == 0) {
           // Direct: use same UV (assuming same resolution)
           color_uv = a_tex_coord;
       } else {
           // Calibrated: transform 3D point to color camera and project
           vec4 P_color = u_T_color_from_depth * vec4(x_camera, y_camera, z, 1.0);
           // Perspective divide
           P_color.xyz /= P_color.w;
           // Project to color pixel
           float u_c = (P_color.x * u_color_intrinsics.x / P_color.z) + u_color_intrinsics.z;
           float v_c = (P_color.y * u_color_intrinsics.y / P_color.z) + u_color_intrinsics.w;
           // Normalize to [0,1] for texture sampling
           color_uv = vec2(u_c / u_color_width, v_c / u_color_height);
       }
       
       // Sample color
       vec3 color = texture(u_color_texture, color_uv).rgb;
       v_color = color;
       
       // ... (rest: MVP, point size, etc.)
   }
   ```

3. **Color Frame Synchronization**: The effect should ideally check that depth and color frames are from the same timestamp. If the sources provide timestamps, compare them and skip if out of sync. This is more of a pipeline concern.

4. **Handling Missing Color**: If `_color_texture` is 0 or color source not set, the vertex shader should output a default color (white or depth-based). You can set a uniform `u_use_color` to toggle.

5. **Performance**: The color texture upload can be a bottleneck if the color camera runs at high resolution and frame rate. Consider using a Pixel Buffer Object (PBO) for asynchronous uploads if needed.

6. **Testing with Real Data**: If you have access to a RealSense or Astra, test with real depth+color streams to verify alignment. The calibration is critical; even a few pixels of offset will be noticeable.

7. **Debug Visualization**: Add a debug mode that outputs `color_uv` as color to verify mapping. Or output the color frame directly to see if it's being sampled correctly.

8. **Matrix Convention**: Ensure the transformation matrix `T_color_from_depth` transforms points from depth camera coordinates to color camera coordinates. This is typically obtained from camera calibration ( extrinsic parameters). OpenGL uses column-major; numpy is row-major; be consistent.

9. **Color Frame Format**: Accept both uint8 (0-255) and float32 (0.0-1.0). When uploading to GL texture, convert to appropriate format. For float, use `GL_RGBA32F`; for uint8, use `GL_RGBA8`.

10. **Documentation**: Clearly document the required camera setup: both cameras must be rigidly mounted and calibrated. Provide example intrinsics for common devices (RealSense D415: depth fx~615, color fx~640, etc.).

---

## Conclusion

The DepthPointCloud3DEffect elevates point cloud visualization by adding photorealistic color from an RGB camera. By carefully aligning depth and color data through camera calibration, it produces stunning volumetric video effects that are essential for VJ performances using depth cameras. The effect builds upon the solid foundation of `DepthPointCloudEffect` and extends it with color texture mapping, requiring precise camera geometry but delivering rich, colored point clouds.

---
