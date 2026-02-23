# P3-EXT055: Depth Mesh Effect

## What This Module Does
Generates a 3D mesh from the depth buffer and renders it with various visual effects. Creates a wireframe or solid mesh representation of the depth geometry, useful for visualizing depth structure or creating stylized 3D effects. The mesh can be rendered with different materials, lighting, and animation.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthMeshEffect",
    "version": "3.0.0",
    "description": "3D mesh generation from depth buffer",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "mesh",
    "tags": ["depth", "mesh", "3d", "wireframe", "geometry"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `mesh_type: str` (default: "wireframe", options: ["wireframe", "solid", "points", "hidden_line"]) - Mesh rendering style
- `mesh_density: float` (default: 0.5, min: 0.1, max: 1.0) - Vertex density (higher = more triangles)
- `depth_scale: float` (default: 1.0, min: 0.1, max: 10.0) - Z-axis scaling
- `mesh_color: list[float]` (default: [0.0, 1.0, 0.0]) - Mesh color (RGB 0-1)
- `line_width: int` (default: 1, min: 1, max: 5) - Line width for wireframe
- `enable_lighting: bool` (default: False) - Enable simple lighting
- `light_direction: list[float]` (default: [0.0, 0.0, 1.0]) - Light direction
- `enable_animation: bool` (default: False) - Animate mesh rotation
- `rotation_speed: float` (default: 1.0, min: 0.1, max: 10.0) - Rotation speed when animated
- `fill_opacity: float` (default: 0.3, min: 0.0, max: 1.0) - Opacity for solid mesh fill

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame (optional background)
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `timestamp: float` (optional) - Current time for animation

### Outputs
- `video: Frame` (same format as input) - Video with 3D mesh overlay

## What It Does NOT Do
- Does NOT perform full 3D mesh reconstruction (simple height field only)
- Does NOT support texture mapping or complex materials
- Does NOT include advanced lighting models (simple directional only)
- Does NOT handle HDR metadata preservation
- Does NOT support mesh editing or deformation
- Does NOT include mesh export functionality

## Test Plan
1. Unit tests for mesh vertex generation from depth
2. Verify mesh density affects triangle count correctly
3. Test all mesh_type options
4. Performance: ≥ 60 FPS at 1080p with mesh_density=0.5
5. Memory: < 150MB additional RAM
6. Visual: verify mesh represents depth structure accurately

## Implementation Notes
- Convert depth buffer to height map
- Generate vertices on a regular grid, with Z = depth * depth_scale
- Create triangles by connecting adjacent vertices (two triangles per grid cell)
- For wireframe: render triangle edges as lines
- For solid: render filled triangles with optional fill_opacity
- For points: render vertices as points
- For hidden_line: render wireframe with hidden line removal
- Apply simple lighting if enabled: intensity = dot(normal, light_direction)
- If enable_animation: rotate mesh around Y axis based on timestamp * rotation_speed
- Render mesh over original video (or on black background if video is None)
- Optimize with indexed vertex buffers and batch rendering
- Follow SAFETY_RAILS: cap mesh density, handle edge cases

## Deliverables
- `src/vjlive3/effects/depth_mesh.py`
- `tests/effects/test_depth_mesh.py`
- `docs/plugins/depth_mesh.md`
- Optional: `shaders/depth_mesh.vert` and `shaders/depth_mesh.frag`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Mesh generates from depth correctly
- [x] All mesh_type options render properly
- [x] 60 FPS at 1080p with moderate mesh density
- [x] Test coverage ≥ 80%
- [x] No safety rail violations