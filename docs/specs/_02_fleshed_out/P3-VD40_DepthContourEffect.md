# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD40_DepthContourEffect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD40 — DepthContourEffect

## Description

The DepthContourEffect extracts iso-depth contour lines from a depth map, treating the depth image as a topographic surface and drawing lines where the depth equals specific values. Like elevation lines on a topographic map, these contours reveal the shape of the scene in a stylized, wireframe-like visualization. The effect traces continuous contour lines at regular depth intervals and renders them as 3D lines positioned in world space, creating a "depth elevation map" aesthetic.

The effect supports animated contours that shift over time, giving the impression of flowing elevation lines. It's particularly effective for revealing the 3D structure of a scene in an abstract, artistic way, and can be combined with other depth effects for rich visual compositions.

## What This Module Does

- Extracts contour lines from a depth map at specified depth intervals
- Uses a contour tracing algorithm (similar to marching squares) to find continuous lines
- Converts 2D contour points to 3D world coordinates using camera model
- Renders contour lines as 3D line segments with depth-based coloring
- Supports animated contours that shift depth levels over time
- Provides parameters for contour density, smoothing, thickness, and animation speed
- Integrates with `DepthEffect` base class for depth source management
- GPU-accelerated line rendering using vertex buffers

## What This Module Does NOT Do

- Does NOT fill contour regions (only lines)
- Does NOT perform edge detection on color (depth only)
- Does NOT support arbitrary contour levels (only regular intervals)
- Does NOT provide smooth curves (contours are pixel-accurate, not Bezier)
- Does NOT implement CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT handle contour labeling or measurement

---

## Detailed Behavior

### Contour Extraction Algorithm

The effect extracts contour lines at multiple depth levels. For each contour level `z_i`:

1. **Quantize depth**: For each pixel, check if depth is within a threshold of the contour level:
   ```
   if |depth(x,y) - z_i| < threshold:
       mask(x,y) = 1
   else:
       mask(x,y) = 0
   ```
   The threshold is derived from `contour_smoothing` parameter.

2. **Trace connected components**: Find connected regions in the binary mask. Each connected component is a contour line (or blob). To get line-like contours (not blobs), use a thin mask (e.g., morphological thinning) or trace edges.

   The legacy implementation uses a simple 8-connected flood fill / line tracing:
   - Start at a pixel where mask=1 and not visited
   - Follow neighboring pixels (8-connected) that are also in mask
   - Record the (x,y) coordinates as a polyline
   - Mark visited to avoid reprocessing

3. **Multiple intervals**: The `contour_intervals` parameter determines how many distinct depth levels to extract, evenly spaced between `min_depth` and `max_depth`.

4. **Animation**: If `contour_animation` is enabled, the contour levels shift over time:
   ```
   z_i(t) = z_i0 + animation_speed * time
   ```
   This causes contours to appear to flow or scroll.

### 3D Reconstruction

Each contour point (x, y) from the 2D mask is associated with a depth value (the contour level `z_i`). To convert to 3D world coordinates:

```
z = z_i  # depth in camera space (meters)
x_world = (x - cx) * z / fx
y_world = (y - cy) * z / fy
```

Where `(fx, fy, cx, cy)` are camera intrinsics. The result is a 3D point in camera space. Optionally apply a model-view-projection transformation for rendering.

### Rendering Pipeline

1. **Update depth data**: Get latest depth frame from source
2. **Generate contour lines**: For each contour level, trace connected pixels to form polylines
3. **Convert to 3D**: Transform each 2D point to 3D world coordinates
4. **Create vertex buffer**: Flatten all contour lines into a single vertex array
5. **Create index buffer**: Define line segments (GL_LINES) connecting consecutive points in each polyline
6. **Upload to GPU**: Update VBO and EBO each frame (contours change with depth and animation)
7. **Render**: `glDrawElements(GL_LINES, index_count, GL_UNSIGNED_INT, 0)`

### Shader

Simple shader that passes through position and color:

**Vertex**:
```glsl
uniform mat4 u_mvp;
in vec3 a_position;
in vec3 a_color;
out vec3 v_color;

void main() {
    gl_Position = u_mvp * vec4(a_position, 1.0);
    v_color = a_color;
}
```

**Fragment**:
```glsl
in vec3 v_color;
out vec4 frag_color;

void main() {
    frag_color = vec4(v_color, 1.0);
}
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `contour_intervals` | int | 10 | 1-50 | Number of distinct contour levels between min and max depth |
| `contour_smoothing` | float | 0.5 | 0.0-1.0 | Threshold for contour detection (0=tight, 1=loose) |
| `contour_thickness` | float | 2.0 | 0.5-10.0 | Line thickness in pixels (OpenGL dependent) |
| `contour_animation` | bool | True | — | Enable animated shifting of contour levels |
| `animation_speed` | float | 1.0 | 0.1-5.0 | Speed of contour animation (Hz or depth units/sec) |

**Inherited from DepthEffect**: `min_depth`, `max_depth`, `near_clip`, `far_clip`, `depth_scale`, `invert_depth`

### Color Scheme

Contour lines are colored based on their depth value:
```
t = (depth - min_depth) / (max_depth - min_depth)
color = (t, 0.5, 1.0 - t)  # Blue (far) to red (near)
```
This provides visual depth cueing. Could be made configurable.

---

## Public Interface

```python
class DepthContourEffect(DepthEffect):
    def __init__(self) -> None: ...
    def set_contour_intervals(self, n: int) -> None: ...
    def get_contour_intervals(self) -> int: ...
    def set_contour_smoothing(self, s: float) -> None: ...
    def get_contour_smoothing(self) -> float: ...
    def set_contour_thickness(self, t: float) -> None: ...
    def get_contour_thickness(self) -> float: ...
    def set_contour_animation(self, enabled: bool) -> None: ...
    def get_contour_animation(self) -> bool: ...
    def set_animation_speed(self, speed: float) -> None: ...
    def get_animation_speed(self) -> float: ...
    def render_3d_depth_scene(self, resolution: Tuple[int, int], time: float) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (optional, for compositing) |
| **Output** | `np.ndarray` | Rendered contour lines (HxWxC, RGB) |

---

## State Management

**Persistent State:**
- `_contour_intervals: int` — Number of contour levels
- `_contour_smoothing: float` — Detection threshold
- `_contour_thickness: float` — Line width
- `_contour_animation: bool` — Animation enabled
- `_animation_speed: float` — Animation speed
- `_vao: int` — Vertex array object
- `_vbo: int` — Vertex buffer (positions + colors)
- `_ebo: int` — Index buffer (line segments)
- `_vertex_count: int` — Number of vertices
- `_index_count: int` — Number of indices
- `_shader: ShaderProgram` — Compiled shader
- `_depth_texture: int` — From base class (optional)

**Per-Frame:**
- Generate contour lines from current depth (and animation offset)
- Convert to 3D vertices
- Upload vertex/index buffers
- Render

**Initialization:**
- Create VAO, VBO, EBO
- Compile shader
- Default intervals: 10
- Default smoothing: 0.5
- Default thickness: 2.0
- Default animation: enabled, speed 1.0

**Cleanup:**
- Delete VAO, VBO, EBO
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| VAO | GL_VERTEX_ARRAY | — | 1 | Init, persists |
| VBO | GL_ARRAY_BUFFER | positions (vec3) + colors (vec3) | dynamic | Init, updated each frame |
| EBO | GL_ELEMENT_ARRAY_BUFFER | GL_UNSIGNED_INT | dynamic | Init, updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget:**
- Vertex size: 6 floats = 24 bytes
- Number of vertices: depends on depth complexity; could be 10K-100K
- Index size: 2 vertices per line segment = 2 indices per segment
- Total: highly variable, but typically < 10 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | `RuntimeError("No depth data")` | Call `update_depth_data()` first |
| No contours found | Render nothing (empty) | Normal operation |
| Buffer upload fails | `RuntimeError("GPU error")` | Check GL errors, retry or abort |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range or raise `ValueError` | Document valid ranges |
| Line width unsupported | Use default 1.0 | Query `GL_LINE_WIDTH` range |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and buffer updates must occur on the thread with the OpenGL context. The VBO and EBO are mutated each frame, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480 depth, moderate contours):**
- Contour tracing (CPU): ~2-5 ms (depends on number of intervals and complexity)
- Vertex buffer update: ~1-2 ms
- Rendering (GL_LINES): ~1-3 ms
- Total: ~4-10 ms on CPU+GPU

**Optimization Strategies:**
- Reduce `contour_intervals` to trace fewer levels
- Downsample depth before contour detection (e.g., 2× or 4×)
- Cache contour lines if depth hasn't changed significantly
- Use a compute shader for contour tracing on GPU (advanced)
- Limit maximum vertices per contour level to avoid explosion

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Camera intrinsics set (fx, fy, cx, cy)
- [ ] Depth range (min_depth, max_depth) configured
- [ ] Contour parameters set (intervals, smoothing, thickness)
- [ ] Animation settings configured (enabled, speed)
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_contour_intervals` | Intervals can be set and clamped |
| `test_set_contour_smoothing` | Smoothing updates correctly |
| `test_set_contour_thickness` | Thickness updates |
| `test_set_contour_animation` | Animation toggle works |
| `test_set_animation_speed` | Speed updates |
| `test_generate_contours_no_depth` | Raises error if no depth |
| `test_generate_contours_plane` | Extracts single contour from constant depth |
| `test_generate_contours_multiple` | Multiple intervals produce multiple lines |
| `test_contour_tracing` | Traced lines are continuous and closed/open as expected |
| `test_3d_reconstruction` | Contour points converted to correct 3D positions |
| `test_animation_offset` | Animation shifts contour levels over time |
| `test_vertex_buffer_population` | Vertices and indices correctly formatted |
| `test_render_contours` | Renders visible contour lines |
| `test_color_by_depth` | Contour colors vary with depth |
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
- [ ] Git commit with `[Phase-3] P3-VD40: depth_contour_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/depth/contour.py` — VJLive-2 implementation of `DepthContourEffect`
- `plugins/vdepth/depth_effects.py` — Registers `DepthContourEffect` in `DEPTH_EFFECTS`
- `gl_leaks.txt` — Shows `DepthContourEffect` allocates `glGenVertexArrays`, `glGenBuffers` and must free them

Design decisions inherited:
- Effect name: `DepthContourEffect`
- Inherits from `DepthEffect` (base class for depth effects)
- Uses CPU-side contour tracing (not GPU)
- Renders with `GL_LINES` using vertex/index buffers
- Parameters: `contour_intervals`, `contour_smoothing`, `contour_thickness`, `contour_animation`, `animation_speed`
- Color based on depth (blue far → red near)
- Supports animation of contour levels over time
- Allocates GL resources: VAO, VBO, EBO

---

## Notes for Implementers

1. **Contour Tracing Algorithm**: The legacy uses a simple 8-connected flood fill to trace contour lines. This works but may produce blobs instead of thin lines. Consider:
   - Using morphological thinning (skeletonization) to get 1-pixel wide lines
   - Using marching squares to extract iso-lines directly (more accurate)
   - The current approach: create binary mask `|depth - level| < threshold`, then find connected components and trace their boundaries. This gives closed loops or open lines depending on topology.

2. **Binary Mask Creation**: For each contour level `z_i`, create a binary mask:
   ```python
   mask = np.abs(depth - z_i) < (contour_smoothing * depth_scale)
   ```
   The `contour_smoothing` parameter controls the width of the band around the level.

3. **Tracing**: For each connected component in the mask, trace its boundary. The legacy code uses a simple neighbor-walk. This may produce self-intersecting or messy lines. A better approach: use `cv2.findContours` (if OpenCV available) which returns clean polygonal contours.

4. **Animation**: If `contour_animation` is True, offset the contour levels by `animation_speed * time`:
   ```python
   offset = (time * animation_speed) % (depth_range / contour_intervals)
   levels = np.linspace(min_depth + offset, max_depth + offset, contour_intervals, endpoint=False)
   ```
   This makes contours scroll through depth range.

5. **3D Conversion**: For each contour point (x, y), the depth is the contour level `z_i`. Convert to world coordinates using camera intrinsics. Ensure you use the same intrinsics as the depth source.

6. **Vertex Format**: Use interleaved array:
   ```python
   # Each vertex: position (3 floats) + color (3 floats)
   vertices = []
   for line in contour_lines:
       for (x, y, z) in line:
           world_x, world_y, world_z = project_to_world(x, y, z)
           r, g, b = depth_to_color(z)
           vertices.extend([world_x, world_y, world_z, r, g, b])
   ```
   Size: 24 bytes per vertex.

7. **Index Buffer**: For each polyline with N points, create N-1 line segments:
   ```python
   indices = []
   vertex_offset = 0
   for line in contour_lines:
       for i in range(len(line) - 1):
           indices.append(vertex_offset + i)
           indices.append(vertex_offset + i + 1)
       vertex_offset += len(line)
   ```
   Use `GL_LINES` primitive.

8. **Line Thickness**: `glLineWidth` controls thickness, but support varies (often 1-5px). Set once during init or before draw. The parameter is a hint; actual width may be clamped.

9. **Performance**: Contour tracing on CPU can be slow for many intervals at high resolution. Optimizations:
   - Downsample depth before tracing (e.g., 320×240)
   - Limit `contour_intervals` to <= 20
   - Use OpenCV's `findContours` if available (fast)
   - Cache results if depth hasn't changed much (compare frame hash)

10. **Shader**: Keep it simple. MVP matrix can be from base class. Color is passed from CPU; no need to compute in shader.

11. **Memory**: Vertex/index buffers need to be reallocated if contour complexity changes dramatically. Use `glBufferData` with new size each frame, or allocate a large enough buffer and use `glBufferSubData` with actual size.

12. **Testing**: Create synthetic depth with simple shapes (sphere, box) and verify contours appear at expected depths. Test animation by checking that contour levels shift over time.

13. **Debugging**: Provide a debug mode that outputs the binary mask or contour lines in 2D to verify tracing. Also visualize depth range to ensure min/max are correct.

14. **Future Extensions**:
    - Allow custom color maps (not just blue-red)
    - Add contour smoothing (spline interpolation) for anti-aliased lines
    - Support closed vs open contour rendering (with caps)
    - Add glow/post-processing to contours
    - Combine with point cloud or mesh for hybrid visualization

---
-

## References

- Marching squares: https://en.wikipedia.org/wiki/Marching_squares
- Contour line extraction: https://docs.opencv.org/master/d4/d73/tutorial_py_contours_begin.html
- OpenGL lines: https://learnopengl.com/Advanced-OpenGL/Geometry-Shader
- VJLive legacy: `core/effects/depth/contour.py` (DepthContourEffect)

---

## Implementation Tips

1. **Contour Extraction with OpenCV** (if available):
   ```python
   import cv2
   def extract_contours(depth, level, threshold):
       # Create binary mask
       mask = np.abs(depth - level) < threshold
       mask = mask.astype(np.uint8) * 255
       # Find contours (external only, no hierarchy)
       contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
       # contours is list of (N,1,2) arrays; convert to list of (x,y) points
       lines = [c.squeeze().tolist() for c in contours if len(c) >= 2]
       return lines
   ```
   This is much cleaner than manual tracing.

2. **Without OpenCV**: Implement a simple connected component tracer:
   ```python
   def trace_contours(mask):
       h, w = mask.shape
       visited = np.zeros_like(mask, dtype=bool)
       lines = []
       for y in range(h):
           for x in range(w):
               if mask[y, x] and not visited[y, x]:
                   line = flood_fill_8connected(mask, visited, x, y)
                   if len(line) >= 2:
                       lines.append(line)
       return lines
   
   def flood_fill_8connected(mask, visited, x, y):
       line = []
       stack = [(x, y)]
       while stack:
           cx, cy = stack.pop()
           if not (0 <= cx < mask.shape[1] and 0 <= cy < mask.shape[0]):
               continue
           if visited[cy, cx] or not mask[cy, cx]:
               continue
           visited[cy, cx] = True
           line.append((float(cx), float(cy)))
           for dx in (-1, 0, 1):
               for dy in (-1, 0, 1):
                   if dx == 0 and dy == 0:
                       continue
                   stack.append((cx + dx, cy + dy))
       return line
   ```
   This gives blobs; you'd need to extract boundary only. Better: use a boundary-following algorithm like Moore-neighbor tracing.

3. **Moore-Neighbor Tracing** (for clean lines):
   - Start at a boundary pixel (mask=1 with a neighbor that is 0)
   - Walk around the boundary using a standard algorithm
   - Returns a closed or open polyline
   This is more complex but yields nicer results.

4. **Animation**:
   ```python
   def get_contour_levels(self, time):
       depth_range = self.max_depth - self.min_depth
       if self.contour_animation:
           offset = (time * self.animation_speed) % (depth_range / self.contour_intervals)
       else:
           offset = 0.0
       levels = np.linspace(self.min_depth + offset, self.max_depth + offset, self.contour_intervals, endpoint=False)
       return levels
   ```

5. **Vertex Buffer Update**:
   ```python
   vertices = np.array(vertices_list, dtype=np.float32)  # shape (N, 6)
   indices = np.array(indices_list, dtype=np.uint32)    # shape (M,)
   
   glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
   glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)
   
   glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
   glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_DYNAMIC_DRAW)
   
   self._vertex_count = len(vertices)
   self._index_count = len(indices)
   ```

6. **Rendering**:
   ```python
   glUseProgram(self._shader.program)
   self.shader.set_uniform('u_mvp', self._mvp_matrix)
   glBindVertexArray(self._vao)
   glLineWidth(self._contour_thickness)
   glDrawElements(GL_LINES, self._index_count, GL_UNSIGNED_INT, None)
   glBindVertexArray(0)
   ```

7. **Color Mapping**:
   ```python
   def depth_to_color(self, depth):
       t = (depth - self.min_depth) / (self.max_depth - self.min_depth)
       t = max(0.0, min(1.0, t))
       return (t, 0.5, 1.0 - t)  # (r,g,b)
   ```

8. **Handling Empty Contours**: If no contours are found for a level, simply skip adding vertices/indices. The buffers can be empty; rendering with count=0 is safe.

9. **Performance Profiling**: The contour tracing (CPU) is likely the bottleneck. Profile with different `contour_intervals` and depth resolutions. Consider downsampling depth to 320×240 before tracing, then upscale the 2D points when converting to 3D (or just accept lower resolution).

10. **Line Smoothing**: For anti-aliased lines, enable `glEnable(GL_LINE_SMOOTH)` and use `glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)`. However, this may be slow and not well-supported. Better to render to a higher-resolution framebuffer and downsample, or use a post-processing blur.

---

## Conclusion

The DepthContourEffect provides an artistic, topographic visualization of depth data by extracting and rendering iso-depth lines. It combines CPU-side contour tracing with GPU line rendering to deliver smooth, animated contour visualizations. The effect is relatively lightweight and can be used as a standalone visual or combined with other depth effects for complex VJ performances.

---
