# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD39_DepthMeshEffect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD39 — DepthMeshEffect

## Description

The DepthMeshEffect transforms a 2D depth map into a 3D triangular mesh, creating a continuous surface representation of the scene geometry. Unlike point clouds that render individual samples, this effect connects adjacent depth pixels into triangles, producing a solid, shaded surface that can be lit, textured, and viewed from arbitrary angles. It's the foundation for realistic 3D reconstruction from depth cameras, enabling VJs to create volumetric visuals with proper surface continuity.

The effect uses a standard grid topology: each 2×2 pixel block forms two triangles, connecting neighboring depth samples. The mesh vertices are positioned in 3D using the camera model, and the mesh is rendered with optional wireframe, flat shading, or smooth shading. The result is a dense, real-time 3D mesh that can be further transformed, lit, and combined with other effects.

## What This Module Does

- Converts depth map to 3D mesh using regular grid connectivity
- Generates vertex positions from depth via camera model
- Creates triangle indices (two triangles per pixel quad)
- Supports multiple render modes: solid, wireframe, points, normals
- Provides basic lighting (flat or smooth shading)
- Integrates with `DepthEffect` base class for depth source management
- GPU-accelerated using vertex/index buffers and standard OpenGL pipeline

## What This Module Does NOT Do

- Does NOT perform mesh simplification or LOD (full resolution mesh)
- Does NOT handle mesh topology optimization (regular grid only)
- Does NOT compute smooth vertex normals (can compute per-face or simple)
- Does NOT perform texture mapping (could be added later)
- Does NOT support arbitrary mesh topology (only grid)
- Does NOT provide CPU fallback (GPU required)
- Does NOT store persistent state across sessions
- Does NOT perform hole filling (invalid depth pixels create gaps)

---

## Detailed Behavior

### Mesh Topology

For a depth map of size `W × H`, the mesh has:
- **Vertices**: `W × H` vertices, one per depth pixel
- **Triangles**: `(W-1) × (H-1) × 2` triangles

Each 2×2 pixel block (4 vertices) forms two triangles:

```
v00 ── v10
│  ┌──│  │
│  │  │  │
│  └──│  │
v01 ── v11
```

Triangle indices (assuming row-major vertex ordering):
- Triangle 1: `(v00, v01, v10)`
- Triangle 2: `(v10, v01, v11)`

Or using vertex indices:
```python
def generate_indices(width, height):
    indices = []
    for y in range(height - 1):
        for x in range(width - 1):
            i0 = y * width + x
            i1 = i0 + 1
            i2 = i0 + width
            i3 = i2 + 1
            # Two triangles
            indices.extend([i0, i1, i2])  # Triangle 1
            indices.extend([i2, i1, i3])  # Triangle 2
    return np.array(indices, dtype=np.uint32)
```

### Vertex Attributes

Each vertex has:
- **Position** (`vec3`): 3D coordinates in camera space (or world space after model transform)
- **Normal** (`vec3`): Surface normal (computed from depth gradient or per-face flat)
- **TexCoord** (`vec2`): Optional, maps to depth pixel coordinates (u, v)

### 3D Position Reconstruction

Same as `DepthPointCloudEffect`:
```python
z = near_clip + depth * (far_clip - near_clip)
x = (u - cx) * z / fx
y = (v - cy) * z / fy
```

Where (u, v) are pixel coordinates.

### Normal Computation

Normals can be computed in several ways:

1. **Per-face flat normals**: Compute normal from triangle vertices using cross product. Each triangle gets one normal; vertices share the face normal. This gives a faceted look.

2. **Smooth normals (averaged)**: For each vertex, average the normals of all adjacent faces. This gives a smooth appearance but may be incorrect at depth discontinuities.

3. **Depth gradient**: Compute normal directly from depth map using Sobel filters:
   ```python
   dzdx = (depth[x+1, y] - depth[x-1, y]) * 0.5
   dzdy = (depth[x, y+1] - depth[x, y-1]) * 0.5
   normal = normalize(vec3(-dzdx, -dzdy, 1.0))
   ```
   This is fast and gives reasonable results, but may be noisy.

The effect should support at least flat and smooth shading modes.

### Rendering Pipeline

1. **Update depth data**: Call `update_depth_data()` to get latest depth frame
2. **Generate vertex buffer**: For each depth pixel, compute 3D position (and optionally normal)
3. **Index buffer**: Precomputed or generated once (static for given resolution)
4. **Upload to GPU**: Use `glBufferSubData` or `glMapBuffer` to update vertex buffer each frame
5. **Render**: `glDrawElements(GL_TRIANGLES, num_indices, GL_UNSIGNED_INT, 0)`

### Render Modes

- **0 (Solid)**: Fill triangles with a base color (white or depth-based)
- **1 (Wireframe)**: Render triangle edges only (`glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)`)
- **2 (Points)**: Render vertices as points (like point cloud)
- **3 (Normals)**: Visualize normals as RGB (x,y,z → r,g,b)
- **4 (Depth)**: Color vertices by depth value
- **5 (Lit)**: Apply simple directional lighting using normals

### Shader Architecture

**Vertex Shader**:
```glsl
uniform mat4 u_model_matrix;
uniform mat4 u_view_matrix;
uniform mat4 u_projection_matrix;
uniform int u_visualization_mode;

in vec3 a_position;  // 3D vertex position (camera or world space)
in vec3 a_normal;    // Vertex normal (if smooth shading)
in vec2 a_texcoord;  // Depth pixel coordinates

out vec3 v_normal;
out vec3 v_position;
out float v_depth;

void main() {
    vec4 world_pos = u_model_matrix * vec4(a_position, 1.0);
    v_position = world_pos.xyz;
    v_normal = mat3(transpose(inverse(u_model_matrix))) * a_normal;  // Transform normal
    v_depth = a_texcoord.x;  // Or compute from position
    
    gl_Position = u_projection_matrix * u_view_matrix * world_pos;
}
```

**Fragment Shader**:
```glsl
uniform int u_visualization_mode;
uniform vec3 u_light_dir;  // For lit mode
uniform vec3 u_base_color;

in vec3 v_normal;
in vec3 v_position;
in float v_depth;

out vec4 frag_color;

void main() {
    if (u_visualization_mode == 0) {
        // Solid
        frag_color = vec4(u_base_color, 1.0);
    } else if (u_visualization_mode == 1) {
        // Wireframe handled by glPolygonMode, but fragment still runs
        frag_color = vec4(u_base_color, 1.0);
    } else if (u_visualization_mode == 3) {
        // Normal visualization
        frag_color = vec4(normalize(v_normal) * 0.5 + 0.5, 1.0);
    } else if (u_visualization_mode == 4) {
        // Depth
        float t = v_depth;  // 0-1
        frag_color = vec4(mix(vec3(0.0, 0.0, 1.0), vec3(1.0, 0.0, 0.0), t), 1.0);
    } else if (u_visualization_mode == 5) {
        // Lit
        vec3 n = normalize(v_normal);
        float diff = max(dot(n, normalize(u_light_dir)), 0.0);
        vec3 color = u_base_color * (0.3 + 0.7 * diff);  // Ambient + diffuse
        frag_color = vec4(color, 1.0);
    }
}
```

### Handling Invalid Depth

Depth pixels with value 0, NaN, or outside [near, far] should be treated as holes. Options:
- **Skip triangles**: If any vertex of a triangle has invalid depth, don't render that triangle (remove from index buffer or use `glDrawElements` with a subset)
- **Cull in shader**: In vertex shader, if depth invalid, set position to far clip and let rasterizer discard; but triangles still processed
- **Generate index buffer dynamically**: Each frame, generate index buffer only for valid triangles (expensive)

Simplest: generate full index buffer once, but each frame mark invalid vertices and use `glDrawElements` with a primitive restart or generate a compact index buffer. For performance, it's acceptable to render invalid triangles if they're culled by depth test or if they're at far clip.

Better: In vertex shader, if depth invalid, set `gl_Position.w` to a very large value so triangle is clipped. But still wastes vertex processing.

Best: Generate a per-frame index buffer that only includes triangles where all 3 vertices have valid depth. This requires checking depth and building index list on CPU (or compute shader). For VJ use, the simpler approach (render all, invalid vertices at far clip) may be acceptable if invalid regions are small.

### Performance Considerations

- Vertex count: `W × H` (e.g., 640×480 = 307,200 vertices)
- Triangle count: `(W-1)×(H-1)×2` (e.g., 307,198 triangles)
- This is a dense mesh. At 1080p (1920×1080), that's ~2M vertices and ~4M triangles — very heavy.
- Consider downsampling: run effect at lower resolution (e.g., 640×480) and let the GPU upscale or just accept lower poly count.
- Use `GL_TRIANGLES` with index buffer for efficiency.
- Vertex buffer updates each frame: use `GL_DYNAMIC_DRAW` or `GL_STREAM_DRAW`.

---

## Public Interface

```python
class DepthMeshEffect(DepthEffect):
    def __init__(self) -> None: ...
    def set_render_mode(self, mode: int) -> None: ...
    def get_render_mode(self) -> int: ...
    def set_wireframe_color(self, color: Tuple[float, float, float]) -> None: ...
    def set_base_color(self, color: Tuple[float, float, float]) -> None: ...
    def set_light_direction(self, dir: Tuple[float, float, float]) -> None: ...
    def compute_normals(self, mode: str) -> None:  # 'flat', 'smooth', 'gradient'
    def update_mesh(self) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (optional, for compositing) |
| **Output** | `np.ndarray` | Rendered mesh (HxWxC, RGB) |

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `render_mode` | int | 0 | 0-5 | 0=solid, 1=wireframe, 2=points, 3=normals, 4=depth, 5=lit |
| `base_color_r`, `base_color_g`, `base_color_b` | float | 1.0, 1.0, 1.0 | 0.0-1.0 | Color for solid/wireframe modes |
| `light_dir_x`, `light_dir_y`, `light_dir_z` | float | 0.0, 0.0, 1.0 | any | Directional light vector (for lit mode) |
| `normal_mode` | int | 0 | 0=flat, 1=smooth, 2=gradient | How to compute vertex normals |
| `downsample_factor` | int | 1 | 1,2,4 | Reduce mesh resolution by factor (1=full) |
| `wireframe_width` | float | 1.0 | 0.1-5.0 | Line width for wireframe mode (OpenGL dependent) |

**Inherited from DepthEffect**: `near_clip`, `far_clip`, `depth_scale`, `invert_depth`

---

## State Management

**Persistent State:**
- `_depth_width: int`, `_depth_height: int` — Depth frame dimensions
- `_vertex_buffer: int` — GL_ARRAY_BUFFER for vertex data
- `_index_buffer: int` — GL_ELEMENT_ARRAY_BUFFER for indices
- `_vertex_count: int` — Number of vertices (W×H)
- `_index_count: int` — Number of indices (triangles×3)
- `_render_mode: int` — Current render mode
- `_base_color: Tuple[float, float, float]` — Base color
- `_light_dir: Tuple[float, float, float]` — Light direction
- `_normal_mode: int` — Normal computation mode
- `_downsample_factor: int` — Downsampling factor
- `_depth_texture: int` — From base class (optional, for reference)
- `_shader: ShaderProgram` — Compiled shader

**Per-Frame:**
- Update vertex buffer with new positions (and optionally normals)
- If normals are computed from depth gradient, recompute each frame

**Initialization:**
- Create vertex and index buffers
- Generate index buffer based on current depth resolution (and downsample)
- Compile shader
- Default render mode: 0 (solid)
- Default base color: white (1,1,1)
- Default light direction: (0,0,1) (down +Z)
- Default normal mode: 0 (flat)
- Default downsample: 1

**Cleanup:**
- Delete vertex buffer (`glDeleteBuffers(1, [_vertex_buffer])`)
- Delete index buffer
- Delete shader
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Vertex buffer | GL_ARRAY_BUFFER | interleaved (pos:vec3, normal:vec3, tex:vec2) | `num_vertices` | Init, updated each frame |
| Index buffer | GL_ELEMENT_ARRAY_BUFFER | GL_UNSIGNED_INT | `num_indices` | Init, static (unless resolution changes) |
| Shader program | GLSL | vertex + fragment | N/A | Init once |
| Depth texture (optional) | GL_TEXTURE_2D | from base class | depth size | Read-only, from base |

**Memory Budget (640×480):**
- Vertex size: 3+3+2 = 8 floats = 32 bytes
- Vertices: 307,200 × 32 = ~9.8 MB
- Indices: 614,400 × 4 bytes = ~2.4 MB
- Total: ~12.2 MB

**At 1080p (1920×1080) downsampled 2× → 960×540:**
- Vertices: 518,400 × 32 = ~16.6 MB
- Indices: 1,036,800 × 4 = ~4.1 MB
- Total: ~20.7 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth frame missing | `RuntimeError("No depth data")` | Call `update_depth_data()` first |
| Depth resolution changed | Recreate vertex/index buffers | Handle in `update_mesh()` |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Buffer creation fails | `RuntimeError("Out of GPU memory")` | Reduce resolution or downsample |
| Invalid render mode | Clamp to [0,5] or raise `ValueError` | Document valid modes |
| Wireframe width unsupported | Use default 1.0 | Query `GL_LINE_WIDTH` range |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations and buffer updates must occur on the thread with the OpenGL context. The vertex buffer is mutated each frame, so concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480, ~300K vertices, ~600K triangles):**
- Vertex buffer update (stream): ~2-3 ms
- Vertex shader (300K vertices): ~2-4 ms
- Fragment shader (600K triangles, fill-rate bound): ~4-8 ms
- Total: ~8-15 ms on discrete GPU, ~20-35 ms on integrated GPU

**At 960×540 (downsampled 1080p):** ~1.5× slower.

**Optimization Strategies:**
- Use `GL_STREAM_DRAW` for vertex buffer (hint: update every frame)
- Only update vertices that changed (if depth changes slowly, but usually all change)
- Use `glMapBuffer` with `GL_MAP_UNSYNCHRONIZED` for async updates
- Downsample aggressively (factor 2 or 4) to keep poly count manageable
- For wireframe mode, use `GL_LINES` with `glPolygonMode` or geometry shader to generate wireframe
- Consider using `GL_TRIANGLE_STRIP` per row to reduce index count (but more complex)

---

## Integration Checklist

- [ ] Depth source set and providing depth frames
- [ ] Camera intrinsics set (fx, fy, cx, cy)
- [ ] Near/far clip planes configured appropriately
- [ ] Render mode selected based on desired visual
- [ ] Base color and light direction set (for lit mode)
- [ ] Normal mode chosen (flat/smooth/gradient)
- [ ] Downsample factor set to balance quality/performance
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_render_mode` | Mode can be changed and clamped |
| `test_set_base_color` | Color updates correctly |
| `test_set_light_direction` | Light direction stored |
| `test_compute_normals_flat` | Flat normals computed (per-face) |
| `test_compute_normals_smooth` | Smooth normals averaged |
| `test_compute_normals_gradient` | Normals from depth gradient |
| `test_generate_indices` | Index buffer has correct count and pattern |
| `test_update_mesh_no_depth` | Raises error if no depth |
| `test_update_mesh_basic` | Vertex buffer populated with positions |
| `test_mesh_topology` | Vertices and triangles match expected counts |
| `test_invalid_depth_handling` | Invalid depth vertices placed at far clip or skipped |
| `test_downsampling` | Vertex count reduced by factor² |
| `test_process_frame_solid` | Renders solid mesh with base color |
| `test_process_frame_wireframe` | Renders wireframe (line mode) |
| `test_process_frame_points` | Renders as points (like point cloud) |
| `test_process_frame_normals` | Colors vertices by normal |
| `test_process_frame_depth` | Colors vertices by depth |
| `test_process_frame_lit` | Applies directional lighting |
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
- [ ] Git commit with `[Phase-3] P3-VD39: depth_mesh_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/depth_effects.py` — Contains `DepthMeshEffect` (VJLive-2)
- `plugins/vdepth/depth_effects.py` — Original VJLive depth effects
- `core/shader_pipeline_verifier.py` — References `DepthMeshEffect` as requiring `projection_matrix`, `view_matrix`, `model_matrix`
- `gl_leaks.txt` — Shows `DepthMeshEffect` allocates `glGenVertexArrays`, `glGenBuffers` and must free them

Design decisions inherited:
- Effect name: `DepthMeshEffect`
- Inherits from `DepthEffect` (or `Effect` in legacy)
- Uses vertex buffer and index buffer (VAO, VBO, EBO)
- Supports multiple render modes (solid, wireframe, points, normals, depth, lit)
- Requires MVP matrices for 3D transformation
- May support normal computation modes: flat, smooth, gradient
- Allocates GL resources: vertex arrays, buffers

---

## Notes for Implementers

1. **Vertex Format**: Define a structured vertex format:
   ```c
   struct Vertex {
       float position[3];   // x, y, z
       float normal[3];     // nx, ny, nz
       float texcoord[2];   // u, v
   };
   ```
   Size: 8 floats = 32 bytes. Use `glVertexAttribPointer` with appropriate strides and offsets.

2. **Index Buffer**: Generate once (or when resolution changes). Use `GL_UNSIGNED_INT`. For 640×480, indices count = 614,400. This fits in 32-bit.

3. **Vertex Buffer Update**: Each frame, compute new vertex positions (and normals if gradient-based). Use `glBufferSubData` or `glMapBufferRange`. Since all vertices change, you can orphan the buffer with `glBufferData(..., NULL, GL_STREAM_DRAW)` then `glBufferSubData`.

4. **Normal Computation**:
   - **Flat**: For each triangle, compute face normal, assign to its 3 vertices. This requires iterating over triangles and setting vertex normals accordingly. You'll need to compute per-vertex normals by averaging adjacent face normals if you want flat shading but per-vertex normals (for smooth interpolation). Actually for flat shading in OpenGL, you can compute normal in fragment shader using `dFdx`/`dFdy` or use `flat` qualifier. Simpler: compute face normal and set all 3 vertices to that normal; then in fragment, use `flat` interpolation to keep it constant per triangle.
   - **Smooth**: For each vertex, collect all adjacent triangles, compute their face normals, average and normalize. This requires building an adjacency structure (list of triangles per vertex). Can be done on CPU each frame (expensive) or precomputed if topology is static (it is, only positions change). Since topology is fixed, you can precompute a "smooth normal" lookup: for each vertex, which triangles share it? Then each frame, average the normals of those triangles (using current positions). This is doable but adds CPU cost.
   - **Gradient**: Compute normal from depth map using Sobel. This is fast and doesn't depend on mesh connectivity. In vertex shader, you could compute from depth texture if you pass depth as attribute? But we have depth value already. Compute on CPU: for each vertex (pixel), sample neighbors in depth map, compute gradient, derive normal. This is O(W×H) and simple.

   Recommendation: Implement gradient normals first (fast, easy). Then add flat normals (requires face normal computation). Smooth normals are optional (nice to have).

5. **Shader**: Use a simple shader that takes position, normal, and applies MVP. For lit mode, compute diffuse lighting. For wireframe, you can either:
   - Use `glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)` before drawing, then restore.
   - Or render with `GL_LINES` using edge index buffer (more complex).
   The first is simplest.

6. **Handling Invalid Depth**: When generating vertices, if depth is invalid (0, NaN, or outside range), set vertex position to a far clip point (e.g., `(0,0, far*2)`) so it's outside view frustum and gets clipped. This ensures triangles involving invalid vertices are clipped away. However, if a triangle has 2 invalid vertices and 1 valid, it may still produce a degenerate triangle that gets clipped. That's fine.

   Alternatively, you could generate a dynamic index buffer that skips triangles with any invalid vertex. This is more efficient but requires per-frame index regeneration. For simplicity, use the far-clip method.

7. **MVP Matrices**: The effect needs projection, view, and model matrices. These should be provided via `set_matrices()` or inherited from base class. The base `DepthEffect` may already handle these. Check legacy.

8. **Resolution Changes**: If depth frame size changes (e.g., camera switched), you must:
   - Update `_depth_width`, `_depth_height`
   - Recreate vertex buffer (size = width*height)
   - Regenerate index buffer (based on new width/height)
   - Recompute any normal adjacency if using smooth normals

9. **Downsampling**: If `downsample_factor > 1`, treat the depth map as lower resolution:
   - Effective width = `ceil(depth_width / factor)`
   - Effective height = `ceil(depth_height / factor)`
   - When sampling depth, use nearest neighbor on the original depth map at `(x*factor, y*factor)`
   - This reduces vertex count by factor².

10. **Testing**: Create synthetic depth maps:
    - Plane at constant depth: all vertices at same z, normals should be (0,0,1) for gradient method.
    - Sphere: depth varies, normals point outward.
    - Check that index buffer generates correct triangle count.
    - Render and verify mesh appears correctly.

11. **Performance Profiling**: The bottleneck is likely vertex processing and fragment shading. Use GPU timers to measure. If too slow, increase downsample factor.

12. **Wireframe Width**: `glLineWidth` may be limited (often 1-5 pixels). Query `GL_ALIASED_LINE_WIDTH_RANGE` or `GL_SMOOTH_LINE_WIDTH_RANGE`. Don't rely on wide lines.

13. **Lighting**: For lit mode, you need normals. If using gradient normals, they may be noisy. Consider smoothing or using flat shading for a low-poly look.

14. **Color**: Base color can be uniform or vary by depth (like point cloud). Could add a `color_by_depth` parameter.

15. **Future Extensions**:
    - Texture mapping: add UV coordinates (could be same as depth pixel coords)
    - Mesh simplification: reduce triangle count while preserving shape
    - Hole filling: interpolate across invalid regions
    - Backface culling: enable `glEnable(GL_CULL_FACE)` for solid mode
    - Depth buffer: enable depth test for proper occlusion

---
-

## References

- Triangle mesh topology: https://en.wikipedia.org/wiki/Polygon_mesh
- OpenGL vertex buffers: https://learnopengl.com/Advanced-OpenGL/Meshes
- Normal computation: https://en.wikipedia.org/wiki/Vertex_normal
- Depth map to mesh: https://pointclouds.org/documentation/tutorials/mesh_creation.php
- VJLive legacy: `core/effects/depth_effects.py` (DepthMeshEffect)

---

## Implementation Tips

1. **Vertex Structure**:
   ```python
   vertices = np.zeros((height, width, 8), dtype=np.float32)  # 3 pos + 3 normal + 2 uv
   # Fill positions
   for v in range(height):
       for u in range(width):
           depth = depth_map[v, u]
           if depth_valid:
               z = near + depth * (far - near)
               x = (u - cx) * z / fx
               y = (v - cy) * z / fy
           else:
               x, y, z = 0, 0, far*2  # far clip
           vertices[v, u, 0:3] = [x, y, z]
           vertices[v, u, 5:7] = [u / width, v / height]  # uv
   # Compute normals later
   vertices_flat = vertices.reshape(-1, 8)
   ```

2. **Index Generation**:
   ```python
   def generate_grid_indices(w, h):
       indices = []
       for y in range(h - 1):
           for x in range(w - 1):
               i0 = y * w + x
               i1 = i0 + 1
               i2 = i0 + w
               i3 = i2 + 1
               indices.extend([i0, i1, i2])
               indices.extend([i2, i1, i3])
       return np.array(indices, dtype=np.uint32)
   ```

3. **Normal Computation (Gradient)**:
   ```python
   def compute_gradient_normals(depth, fx, fy):
       h, w = depth.shape
       normals = np.zeros((h, w, 3), dtype=np.float32)
       # Sobel kernels
       sobelx = cv2.Sobel(depth, cv2.CV_32F, 1, 0, ksize=3)
       sobely = cv2.Sobel(depth, cv2.CV_32F, 0, 1, ksize=3)
       # Convert depth gradient to normal: n = (-dz/dx, -dz/dy, 1)
       normals[..., 0] = -sobelx
       normals[..., 1] = -sobely
       normals[..., 2] = 1.0
       # Normalize
       norms = np.linalg.norm(normals, axis=2, keepdims=True)
       normals /= np.maximum(norms, 1e-6)
       return normals
   ```

4. **Normal Computation (Flat)**:
   ```python
   def compute_flat_normals(vertices, indices):
       # vertices: (N, 3), indices: (M, 3)
       normals = np.zeros_like(vertices)
       for i in range(0, len(indices), 3):
           i0, i1, i2 = indices[i:i+3]
           v0 = vertices[i0]
           v1 = vertices[i1]
           v2 = vertices[i2]
           # Face normal
           edge1 = v1 - v0
           edge2 = v2 - v0
           n = np.cross(edge1, edge2)
           n_norm = np.linalg.norm(n)
           if n_norm > 1e-6:
               n /= n_norm
           # Assign to vertices (will be averaged if smooth later)
           normals[i0] += n
           normals[i1] += n
           normals[i2] += n
       # Normalize per-vertex
       norms = np.linalg.norm(normals, axis=1, keepdims=True)
       normals /= np.maximum(norms, 1e-6)
       return normals
   ```

5. **OpenGL Setup**:
   ```python
   # Create VAO
   glGenVertexArrays(1, [self._vao])
   glBindVertexArray(self._vao)
   
   # Create VBO
   glGenBuffers(1, [self._vbo])
   glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
   glBufferData(GL_ARRAY_BUFFER, max_vertices * 32, None, GL_DYNAMIC_DRAW)  # allocate
   
   # Create EBO
   glGenBuffers(1, [self._ebo])
   glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
   glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
   
   # Set attrib pointers
   # location 0: position (3 floats)
   glEnableVertexAttribArray(0)
   glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
   # location 1: normal (3 floats)
   glEnableVertexAttribArray(1)
   glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))
   # location 2: texcoord (2 floats)
   glEnableVertexAttribArray(2)
   glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(24))
   
   glBindVertexArray(0)
   ```

6. **Per-Frame Update**:
   ```python
   def update_mesh(self):
       depth = self.get_depth_frame()
       if depth is None:
           raise RuntimeError("No depth")
       h, w = depth.shape
       # Compute vertices
       vertices = np.zeros((h*w, 8), dtype=np.float32)
       for idx, (v, u) in enumerate(np.ndindex(h, w)):
           d = depth[v, u]
           if d > 0 and not np.isnan(d):
               z = self._near_clip + d * (self._far_clip - self._near_clip)
               x = (u - self._cx) * z / self._fx
               y = (v - self._cy) * z / self._fy
           else:
               x, y, z = 0, 0, self._far_clip * 2
           vertices[idx, 0:3] = [x, y, z]
           vertices[idx, 5:7] = [u / w, v / h]
       # Compute normals
       if self._normal_mode == 2:  # gradient
           normals = compute_gradient_normals(depth, self._fx, self._fy)
           vertices[:, 3:6] = normals.reshape(-1, 3)
       elif self._normal_mode == 0:  # flat
           # Compute face normals and assign to vertices (will be flat-shaded)
           normals = compute_flat_normals(vertices[:, :3], self._indices)
           vertices[:, 3:6] = normals
       # else smooth: would need precomputed adjacency; skip for now
       
       # Upload
       glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
       glBufferSubData(GL_ARRAY_BUFFER, 0, vertices.nbytes, vertices)
   ```

7. **Rendering**:
   ```python
   def render(self):
       glUseProgram(self._shader.program)
       set_uniforms(...)
       glBindVertexArray(self._vao)
       if self._render_mode == 1:  # wireframe
           glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
           glLineWidth(self._wireframe_width)
       glDrawElements(GL_TRIANGLES, self._index_count, GL_UNSIGNED_INT, None)
       if self._render_mode == 1:
           glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
       glBindVertexArray(0)
   ```

8. **Memory**: The vertex buffer is large. Consider using `GL_HALF_FLOAT` for normals and texcoords if precision allows, to reduce bandwidth.

---

## Conclusion

The DepthMeshEffect provides a solid, continuous surface representation of depth data, enabling realistic 3D visualization with proper lighting and shading. By constructing a regular grid mesh and rendering it with standard OpenGL pipelines, it delivers high-quality volumetric visuals suitable for VJ performances. The effect requires careful management of vertex buffers and normal computation but offers a rich set of render modes to explore.

---
