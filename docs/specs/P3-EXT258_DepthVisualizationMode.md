# P3-EXT258: DepthVisualizationMode

## Description

The core structural enumeration defining how 16-bit physical camera depth data is translated into 3D rendering methodologies across the VJLive3 node graph.

## What This Module Does

This specification defines the `DepthVisualizationMode` enum and its surrounding implementation context within `DepthEffect` derived classes. Ported from the legacy `VJlive-2/plugins/vdepth/depth_effects.py`, this enum dictates the OpenGL rendering path for raw depth arrays, expanding standard 2D displacement shaders into fully GPU-accelerated volumetric 3D scenes. It works in tandem with `color_mode` maps (`depth`, `rgb`, `velocity`, `distance`).

## Public Interface

```python
class DepthVisualizationMode(Enum):
    """Visualization modes for depth data."""
    POINT_CLOUD = "point_cloud"
    MESH = "mesh"
    CONTOUR = "contour"
    GRADIENT = "gradient"
    VOLUMETRIC = "volumetric"
    PARTICLE_INTEGRATION = "particle_integration"
```

## Inputs and Outputs

*   **Inputs**: Internal State Enum representing the user-selected projection methodology.
*   **Outputs**: Routes the execution flow of `render_3d_depth_scene()` into specific OpenGL drawing methods (e.g., `GL_POINTS`, `GL_TRIANGLES`, `GL_LINES`).

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/depth_effects.py`
- **Architectural Soul**: The legacy implementation uses this enum to instantly swap the visualizer between a pinhole-camera mapped `world_z = depth` point cloud and a Delaunay-triangulated mesh. The projection natively utilizes a 570.0 pseudo-focal length multiplier.

### Key Algorithms & Integration
1. **POINT_CLOUD Mode**: Triggers `_render_point_cloud_3d()`. Loops over the depth matrix skipping pixels iteratively based on `pointDensity`, rendering via `GL_POINTS` with GLSL circular clipping `if (dot(coord, coord) > 0.25) discard;`.
2. **MESH Mode**: Projects depth into interconnected `GL_TRIANGLES`.
3. **Audio-Reactive Coordinates**: Across all modes, objects tracked inside the `DepthDataBus` broadcast proximity coordinates that the shaders use to emit `velocity` or `distance` colors.

### Optimization Constraints & Safety Rails
- **Memory Footprint**: (Safety Rail #1) The legacy codebase allocates `glGenBuffers(1)` conditionally inside render loops. VJLive3 dictates that buffer sizes must be pre-allocated to maximum grid density to guarantee smooth performance. Switching `DepthVisualizationMode` MUST NOT trigger garbage collection or reallocation.

## Test Plan

*   **Logic (Pytest)**: Ensure the Enum correctly serializes and deserializes from node preset dictionaries without string-matching errors.
*   **Visual Check**: Switching between `POINT_CLOUD` and `MESH` in real-time must preserve the identical `cameraAngleX` and `cameraDistance` transforms.
*   **Performance Constraints**: Changing modes mid-render should cause 0 frame drops, heavily reliant on pre-allocating the `GL_ARRAY_BUFFER`.

## Deliverables

1.  Implemented `DepthVisualizationMode` enumeration inside `src/vjlive3/ml/depth/types.py`.
2.  Integration into the core `DepthEffect` base class ensuring robust routing.
