# P3-EXT258: DepthVisualizationMode

## What This Module Does

This specification defines the `DepthVisualizationMode` enum and its surrounding implementation context within `DepthEffect` derived classes. Ported from the legacy `VJlive-2/plugins/vdepth/depth_effects.py`, this enum dictates the OpenGL rendering path for raw depth arrays, expanding standard 2D displacement shaders into fully GPU-accelerated volumetric 3D scenes. It works in tandem with `color_mode` maps (`depth`, `rgb`, `velocity`, `distance`).

## What It Does NOT Do

- Does not handle depth data acquisition or preprocessing
- Does not manage camera calibration or intrinsic parameters
- Does not provide physics simulation or collision detection
- Does not support non-depth-based 3D rendering modes

## Public Interface

```python
from enum import Enum
from typing import Tuple, Optional, Dict, Any
import numpy as np

class DepthVisualizationMode(Enum):
    """Visualization modes for depth data."""
    POINT_CLOUD = "point_cloud"
    MESH = "mesh"
    CONTOUR = "contour"
    GRADIENT = "gradient"
    VOLUMETRIC = "volumetric"
    PARTICLE_INTEGRATION = "particle_integration"

class DepthEffect:
    """Base class for 3D depth-based effects with advanced visualization capabilities."""
    
    def __init__(self, name: str) -> None: ...
    
    def set_depth_source(self, source: Optional[DepthDataSource]) -> None: ...
    def update_depth_data(self) -> None: ...
    def render_3d_depth_scene(self, resolution: Tuple[int, int], time: float) -> None: ...
    
    # Parameter management
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    
    # Visualization configuration
    def set_visualization_mode(self, mode: DepthVisualizationMode) -> None: ...
    def set_color_mode(self, mode: str) -> None: ...
    def set_point_density(self, density: float) -> None: ...
    def set_point_size(self, size: float) -> None: ...
    
    # Camera controls (for 3D modes)
    def set_camera_distance(self, distance: float) -> None: ...
    def set_camera_angle_x(self, angle: float) -> None: ...
    def set_camera_angle_y(self, angle: float) -> None: ...
    
    # Mesh-specific controls
    def set_mesh_smoothing(self, enabled: bool) -> None: ...
    def set_mesh_resolution(self, resolution: float) -> None: ...
    def set_mesh_wireframe(self, enabled: bool) -> None: ...
    
    # Contour-specific controls
    def set_contour_intervals(self, intervals: int) -> None: ...
    def set_contour_thickness(self, thickness: float) -> None: ...
    def set_contour_animation(self, enabled: bool) -> None: ...
    def set_animation_speed(self, speed: float) -> None: ...
    
    # Audio reactivity
    def enable_proximity_audio(self, enabled: bool) -> None: ...
    def set_proximity_audio_scale(self, scale: float) -> None: ...
    def set_velocity_audio_scale(self, scale: float) -> None: ...
    def set_min_proximity_distance(self, distance: float) -> None: ...
    def set_max_proximity_distance(self, distance: float) -> None: ...
```

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `visualization_mode` | `DepthVisualizationMode` | Selected rendering methodology | One of: POINT_CLOUD, MESH, CONTOUR, GRADIENT, VOLUMETRIC, PARTICLE_INTEGRATION |
| `color_mode` | `str` | Color mapping strategy | One of: "depth", "rgb", "velocity", "distance", "confidence" |
| `point_density` | `float` | Sampling density for point cloud | Range: 0.01 (sparse) to 1.0 (full resolution) |
| `point_size` | `float` | Point size in pixels | Range: 0.1 to 20.0 |
| `min_depth` | `float` | Minimum depth for rendering | Range: 0.1 to 10.0 meters |
| `max_depth` | `float` | Maximum depth for rendering | Range: 0.1 to 10.0 meters |
| `camera_distance` | `float` | 3D camera distance from origin | Range: 0.5 to 10.0 meters |
| `camera_angle_x` | `float` | Camera X-axis rotation | Range: -π to π radians |
| `camera_angle_y` | `float` | Camera Y-axis rotation | Range: -π to π radians |
| `mesh_resolution` | `float` | Triangle size in world units | Range: 0.005 to 0.1 |
| `contour_intervals` | `int` | Number of contour levels | Range: 1 to 50 |
| `contour_thickness` | `float` | Line thickness in pixels | Range: 0.5 to 10.0 |

## Edge Cases and Error Handling

- **Missing depth data**: If `depth_frame` is None, rendering functions return immediately without errors
- **Invalid depth values**: NaN/Inf values in depth data are detected and filtered out with warning logs
- **Zero depth range**: If `max_depth == min_depth`, rendering defaults to a safe fallback visualization
- **Insufficient points for mesh**: If fewer than 3 valid points exist, mesh reconstruction is skipped
- **OpenGL context loss**: All GL resources are recreated if context is lost during runtime
- **Memory allocation failures**: Buffer creation failures are caught and logged, with graceful degradation

## Dependencies

- **External libraries needed (and what happens if they are missing):**
  - `numpy` — used for numerical operations — fallback: raises ImportError
  - `OpenGL` — used for GPU rendering — fallback: raises ImportError
  - `cv2` (optional) — used for depth processing — fallback: depth processing disabled
  - `scipy.spatial` (optional) — used for Delaunay triangulation — fallback: grid mesh fallback

- **Internal modules this depends on:**
  - `vjlive3.video_sources.DepthDataSource` — provides depth frames and object tracking
  - `vjlive3.camera_config_manager` — provides camera calibration and depth ranges
  - `vjlive3.shader_base.Effect` — base class for shader effects

## Mathematical Formulations

### 3D Point Cloud Projection

For each valid depth pixel (x, y, depth):
```
world_x = (x - cx) * depth / focal_length
world_y = (y - cy) * depth / focal_length
world_z = depth
```

Where:
- `focal_length = 570.0` pixels (legacy pseudo-focal length multiplier)
- `cx, cy = width/2, height/2` (principal point at image center)
- `depth` in meters (filtered to [min_depth, max_depth] range)

### Camera Projection Matrices

**Perspective Projection Matrix:**
```
[ f/aspect   0          0                0         ]
[   0       f          0                0         ]
[   0       0    (far+near)/(near-far)  (2*far*near)/(near-far) ]
[   0       0         -1                0         ]
```

Where:
- `f = 1.0 / tan(fov/2)` with `fov = 60°`
- `aspect = width / height`
- `near = 0.1`, `far = 10.0`

**View Matrix (Camera Orbit):**
```
camera_pos = [
    distance * sin(angle_y) * cos(angle_x),
    distance * sin(angle_x),
    distance * cos(angle_y) * cos(angle_x)
]
```

### Mesh Reconstruction

**Delaunay Triangulation:**
- Projects 3D points to 2D (x, y) for triangulation
- Uses `scipy.spatial.Delaunay` for robust triangulation
- Fallback to grid-based mesh if triangulation fails

**Adaptive Sampling:**
```
step = max(1, int(mesh_resolution * 570.0 / 0.02))
```

### Contour Generation

**Static Contours:**
```
level = min_depth + depth_range * (i + 0.5) / contour_intervals
```

**Animated Contours:**
```
phase = time * animation_speed * 0.1
level = min_depth + depth_range * (i + 0.5 + sin(phase + i * 0.5)) / contour_intervals
```

## Performance Characteristics

### Memory Layout

**Point Cloud:**
- VBO: `GL_ARRAY_BUFFER` with interleaved [x, y, z, r, g, b, a] floats
- VAO: Single vertex array object
- Memory: ~28 bytes per point (7 floats × 4 bytes)

**Mesh:**
- VBO: Vertex positions and colors
- EBO: Triangle indices (GL_ELEMENT_ARRAY_BUFFER)
- Memory: ~28 bytes per vertex + 4 bytes per index

**Contour Lines:**
- VBO: Line vertices with colors
- EBO: Line segment indices
- Memory: ~28 bytes per vertex

### Performance Constraints

**Frame Rate Targets:**
- Point Cloud: 60 FPS at 640×480 with density=0.1
- Mesh: 30 FPS at 640×480 with adaptive resolution
- Contour: 45 FPS at 640×480 with 10 intervals

**Buffer Management:**
- Pre-allocate maximum buffer sizes to avoid GC during rendering
- Use `GL_DYNAMIC_DRAW` for frequently updated data
- Implement double-buffering for smooth transitions

**GPU Resource Limits:**
- Maximum 1 million points per frame (configurable)
- Maximum 500,000 triangles for mesh mode
- Texture size limited to 4096×4096 for depth/color maps

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_point_cloud_rendering` | 3D point cloud renders correctly with various densities |
| `test_mesh_reconstruction` | Delaunay triangulation produces valid meshes |
| `test_contour_generation` | Contour lines are generated at correct depth intervals |
| `test_camera_controls` | 3D camera navigation works without visual artifacts |
| `test_color_modes` | All color mapping modes produce expected results |
| `test_audio_reactivity` | Proximity-based audio effects trigger correctly |
| `test_performance_stress` | Maintains target FPS under maximum load |
| `test_error_handling` | Graceful degradation on missing/invalid data |
| `test_memory_management` | No memory leaks during mode switching |
| `test_parameter_validation` | All parameters are clamped to valid ranges |

**Minimum coverage:** 85% before task is marked done.

## Definition of Done

- [x] Spec reviewed and matches legacy implementation
- [x] All mathematical formulations are precise and tested
- [x] Performance characteristics are documented
- [x] Edge cases and error handling are comprehensive
- [x] Test plan covers all major functionality
- [x] Memory layouts and buffer management are specified
- [x] Dependencies and fallbacks are clearly defined
- [x] Git commit with `[P3-EXT258] DepthVisualizationMode: complete spec`
- [x] BOARD.md updated with implementation status
- [x] Lock released for next task
- [x] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/depth_effects.py`, `core/effects/depth/`
- **Architectural Soul**: The legacy implementation uses this enum to instantly swap the visualizer between a pinhole-camera mapped `world_z = depth` point cloud and a Delaunay-triangulated mesh. The projection natively utilizes a 570.0 pseudo-focal length multiplier.

### Key Algorithms & Integration
1. **POINT_CLOUD Mode**: Triggers `_render_point_cloud_3d()`. Loops over the depth matrix skipping pixels iteratively based on `pointDensity`, rendering via `GL_POINTS` with GLSL circular clipping `if (dot(coord, coord) > 0.25) discard;`.
2. **MESH Mode**: Projects depth into interconnected `GL_TRIANGLES` using Delaunay triangulation.
3. **Audio-Reactive Coordinates**: Across all modes, objects tracked inside the `DepthDataBus` broadcast proximity coordinates that the shaders use to emit `velocity` or `distance` colors.

### Optimization Constraints & Safety Rails
- **Memory Footprint**: (Safety Rail #1) The legacy codebase allocates `glGenBuffers(1)` conditionally inside render loops. VJLive3 dictates that buffer sizes must be pre-allocated to maximum grid density to guarantee smooth performance. Switching `DepthVisualizationMode` MUST NOT trigger garbage collection or reallocation.
- **Performance**: (Safety Rail #2) All rendering paths must maintain 60 FPS minimum at 640×480 resolution with default parameters.
- **Robustness**: (Safety Rail #3) All rendering functions must handle missing depth data gracefully without crashing.
- **Resource Management**: (Safety Rail #4) All OpenGL resources must be properly cleaned up in `__del__` to prevent memory leaks.