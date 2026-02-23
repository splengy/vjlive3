# P3-EXT062: Depth Effects Depth Point Cloud Effect

## What This Module Does
Generates a simplified point cloud from depth information where each pixel's depth determines its 3D position, creating a volumetric scene representation with efficient rendering for real-time performance.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Depth Point Cloud Effect",
    "id": "P3-EXT062",
    "category": "depth_effects",
    "description": "Simplified point cloud generation from depth map for real-time volumetric visualization",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer"],
    "test_coverage": 85
}
```

### Parameters
- `sampling_rate` (float): Fraction of pixels to sample (0.01-1.0, default: 0.25)
- `depth_multiplier` (float): Scale depth to 3D space (0.1-5.0, default: 1.0)
- `point_size` (int): Point size in pixels (1-10, default: 2)
- `fov` (float): Camera field of view in degrees (30-120, default: 60)
- `rotation` (float): Y-axis rotation in degrees (-180 to 180, default: 0)
- `color_source` (str): Point color from: "depth", "video", "gradient"
- `gradient_start` (list[int]): RGB start color for gradient mode [0-255, 0-255, 0-255]
- `gradient_end` (list[int]): RGB end color for gradient mode [0-255, 0-255, 0-255]

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Rendered point cloud [B, 3, H, W]

## What It Does NOT Do
- Does NOT generate dense point clouds (limited by sampling_rate)
- Does NOT support point cloud export (visualization only)
- Does NOT implement advanced 3D rendering (simple orthographic/perspective projection)
- Does NOT handle point occlusion (all points visible)
- Does NOT support interactive 3D manipulation (rotation only)

## Test Plan

### Unit Tests
1. `test_point_cloud_effect_initialization()`
   - Verify METADATA constants
   - Test parameter validation (sampling_rate 0.01-1.0, depth_multiplier 0.1-5.0)
   - Test default parameter values

2. `test_sampling_mechanism()`
   - Create synthetic depth map
   - Test sampling_rate: 0.01, 0.25, 1.0
   - Verify point count matches sampling_rate × H × W
   - Test sampling pattern uniformity

3. `test_depth_to_3d_projection()`
   - Test depth_multiplier effect on Z coordinate
   - Verify X, Y coordinates from pixel coordinates
   - Test FOV parameter on projection
   - Verify near/far clipping

4. `test_rotation_transform()`
   - Test rotation parameter (-180 to 180)
   - Verify Y-axis rotation matrix applied correctly
   - Test rotation wrapping at ±180

5. `test_color_modes()`
   - Test color_source: "depth", "video", "gradient"
   - Verify depth-based color mapping
   - Test gradient colors with custom start/end

6. `test_point_rendering()`
   - Test point_size parameter (1-10)
   - Verify point sprite rendering
   - Test point shape (square/circle if applicable)

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with sampling_rate=0.25
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 500MB

2. `test_real_depth_visualization()`
   - Feed real depth map from MiDaS/DPT
   - Verify point cloud represents scene structure
   - Test with various depth ranges and noise levels

3. `test_performance_scaling()`
   - Test sampling_rate: 0.01, 0.1, 0.25, 0.5, 1.0
   - Verify FPS and memory scale linearly
   - Identify performance bottleneck

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Implement simplified point cloud without full 3D engine
- Use OpenGL immediate mode or VBO for rendering
- Project 3D points to 2D screen with simple perspective division

### Performance Optimizations
- Use GPU for depth sampling and 3D projection (PyTorch CUDA)
- Preallocate point buffer based on max expected points
- Use OpenGL VBO with GL_POINTS for efficient rendering
- Implement frustum culling for points outside view

### Memory Management
- Max points = H × W × sampling_rate (1920×1080×1.0 = 2M points)
- Each point: position (3 floats) + color (3 floats) = 24 bytes
- 2M points × 24 bytes = 48MB per frame
- Use static allocation with point count as uniform
- Profile memory with 4K input, enforce < 2GB peak

### Safety Rails
- Enforce sampling_rate ≤ 1.0 and ≥ 0.01
- Clamp depth_multiplier to [0.1, 5.0]
- Validate FOV in [30, 120] degrees
- Fallback to wireframe if point rendering fails

## Deliverables
1. `src/vjlive3/effects/depth_point_cloud_effect.py` - Main effect
2. `tests/effects/test_depth_point_cloud_effect.py` - Tests
3. `docs/effects/depth_point_cloud_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p with sampling_rate=0.25 on RTX 4070 Ti Super
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
