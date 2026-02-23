# P3-EXT061: Depth Effects Depth Point Cloud 3D Effect

## What This Module Does
Generates a 3D point cloud from depth information, where each pixel's depth value determines the 3D position of a point, creating a volumetric representation of the scene that can be rotated, manipulated, and rendered in 3D space.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Depth Point Cloud 3D Effect",
    "id": "P3-EXT061",
    "category": "depth_effects",
    "description": "Generates 3D point cloud from depth map with interactive manipulation",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "PointCloudEngine"],
    "test_coverage": 85
}
```

### Parameters
- `point_density` (float): Points per pixel (0.1-1.0, default: 0.5)
- `depth_scale` (float): Multiplier for depth values (0.1-10.0, default: 1.0)
- `point_size` (float): Size of rendered points in pixels (1.0-20.0, default: 2.0)
- `rotation_x` (float): X-axis rotation in degrees (-180 to 180, default: 0)
- `rotation_y` (float): Y-axis rotation in degrees (-180 to 180, default: 0)
- `rotation_z` (float): Z-axis rotation in degrees (-180 to 180, default: 0)
- `camera_distance` (float): Distance from camera to point cloud (1.0-50.0, default: 5.0)
- `color_mode` (str): Point coloring: "depth", "original", "normal", "solid"
- `solid_color` (list[int]): RGB color when color_mode="solid" [0-255, 0-255, 0-255]

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Rendered point cloud [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform real-time point cloud reconstruction at 4K resolution (performance limit)
- Does NOT support point cloud export to PLY/OBJ formats (visual only)
- Does NOT implement advanced point shading (simple point sprite rendering)
- Does NOT handle point occlusion beyond basic depth testing
- Does NOT support animated rotation via keyframes (manual parameter control only)

## Test Plan

### Unit Tests
1. `test_point_cloud_initialization()`
   - Verify METADATA constants
   - Test parameter validation (point_density 0.1-1.0, depth_scale 0.1-10.0)
   - Test default rotation values

2. `test_depth_to_point_projection()`
   - Create synthetic depth map with known values
   - Verify 3D point positions match depth + camera intrinsics
   - Test depth_scale multiplier effect

3. `test_point_density_sampling()`
   - Test point_density parameter: 0.1, 0.5, 1.0
   - Verify point count matches expected density
   - Test sampling pattern (random vs grid)

4. `test_rotation_transforms()`
   - Test rotation_x, rotation_y, rotation_z individually
   - Verify 3D rotation matrices applied correctly
   - Test rotation order (XYZ Euler angles)
   - Test negative angles and wrapping

5. `test_camera_distance()`
   - Test camera_distance parameter
   - Verify point cloud scales correctly
   - Test distance clipping (too close/far)

6. `test_color_modes()`
   - Test all color_mode options: depth, original, normal, solid
   - Verify color mapping correctness
   - Test solid_color parameter when color_mode="solid"

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with point_density=0.5
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 1GB for point cloud buffers

2. `test_real_depth_point_cloud()`
   - Feed real depth map from MiDaS/DPT
   - Verify point cloud represents scene structure
   - Test rotation and camera_distance with real data

3. `test_performance_scaling()`
   - Test point_density scaling: 0.1, 0.5, 1.0
   - Verify FPS degradation is linear
   - Test memory scaling with point count

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged with context

## Implementation Notes

### Architecture
- Build on existing `DepthEffect` base class from P3-VD35
- Integrate with `PointCloudEngine` from VJlive-2 if available, else implement simple point cloud
- Use OpenGL point sprites for rendering (GPU-accelerated)
- Implement 3D transformations with PyTorch tensors for GPU compute

### Performance Optimizations
- Use GPU compute for depth-to-point projection (parallel per-pixel)
- Implement point LOD: reduce point count at distance
- Use OpenGL VBO (Vertex Buffer Object) for point cloud rendering
- Batch rotation transforms on GPU

### Memory Management
- Point count = H × W × point_density (max: 1920×1080×1.0 ≈ 2M points)
- Each point: position (3 floats) + color (3 floats) = 24 bytes
- 2M points × 24 bytes = 48MB per frame buffer
- Use double-buffering to avoid allocation stalls
- Profile memory with 4K input, enforce < 2GB peak

### Safety Rails
- Enforce point_density ≤ 1.0 (memory limit)
- Clamp depth_scale to [0.1, 10.0] with warning
- Validate rotation angles [-180, 180] with clear error
- Fallback to wireframe if point rendering fails

## Deliverables
1. `src/vjlive3/effects/depth_point_cloud_3d_effect.py` - Main effect implementation
2. `tests/effects/test_depth_point_cloud_3d_effect.py` - Unit + integration tests
3. `docs/effects/depth_point_cloud_3d_effect.md` - User documentation
4. Update `MODULE_MANIFEST.md` with new plugin entry

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p with point_density=0.5 on RTX 4070 Ti Super
- ✅ Zero safety rail violations (memory, errors, silent failures)
- ✅ Works with real depth maps from MiDaS/DPT
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
