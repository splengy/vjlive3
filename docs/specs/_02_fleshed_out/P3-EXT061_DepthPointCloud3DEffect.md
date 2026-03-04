# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT061_DepthPointCloud3DEffect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

## Task: P3-EXT061 — DepthPointCloud3DEffect

**What This Module Does**
- Converts depth camera data into 3D point cloud visualizations
- Implements real-time depth-to-point mapping with GPU acceleration
- Supports multiple depth sensor types (LiDAR, RGB-D cameras)

**What This Module Does NOT Do**
- Does not handle raw depth data preprocessing
- Does not include UI components for visualization
- Does not implement post-processing effects

## Detailed Behavior and Parameter Interactions
- Depth data is normalized to [0,1] range before point cloud generation
- Point density is controlled by `point_density` parameter (default: 1000 points/m²)
- Color mapping uses `depth_to_color` function with configurable colormap

## Public Interface
```python
def create_depth_point_cloud(depth_data: np.ndarray, params: dict) -> PointCloud:
    ...

class DepthPointCloudEffect:
    def __init__(self, config: dict):
        ...

    def process_frame(self, frame: Frame) -> Frame:
        ...
```

## Inputs and Outputs
**Inputs**
- `depth_data`: 2D numpy array of depth values (shape: HxW)
- `params`: Configuration dictionary with:
  - `point_density`: float (points per square meter)
  - `color_map`: str (e.g., 'viridis', 'plasma')
  - `max_depth`: float (meters)

**Outputs**
- `PointCloud` object with:
  - `positions`: 3D coordinates (Nx3 array)
  - `colors`: RGB values (Nx3 array)
  - `intensity`: Optional intensity values (N array)

## Edge Cases and Error Handling
- If depth_data contains NaN values, they are interpolated using nearest valid neighbor
- If point_density exceeds 10,000 points/m², automatic downsampling is triggered
- Invalid color_map values trigger fallback to 'viridis'

## Mathematical Formulations
- Depth-to-3D conversion uses pinhole camera model:
  ```
  x = (u - cx) * depth / fx
  y = (v - cy) * depth / fy
  z = depth
  ```
- Point density calculation:
  ```
  points_per_pixel = point_density / (fx * fy)
  ```

## Performance Characteristics
- GPU acceleration reduces processing time by 70% compared to CPU
- Memory usage: ~200MB per 1080p frame at 1000 points/m²
- Frame rate: Maintains 60fps on mid-range GPUs

## Test Plan
- Unit tests for point cloud generation (80% coverage)
- Integration tests with depth camera drivers
- Performance benchmarking across different GPUs

## Definition of Done
- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT061: DepthPointCloud3DEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
- Based on P3-EXT253_DepthPointCloud3DEffect.md
- References P3-EXT254_DepthPointCloudEffect.md
- Uses P3-EXT255_DepthRaverDatamoshEffect.md for color mapping

---