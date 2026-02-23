# P3-EXT067: Depth Effects Depth Visualization Mode

## What This Module Does
Provides multiple visualization modes for depth data, converting depth buffers into visually interpretable representations for debugging, analysis, or artistic purposes.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Depth Visualization Mode",
    "id": "P3-EXT067",
    "category": "depth_effects",
    "description": "Multiple visualization modes for depth data conversion and display",
    "inputs": ["depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer"],
    "test_coverage": 85
}
```

### Parameters
- `visualization_mode` (str): Visualization style: "grayscale", "heatmap", "rainbow", "contour", "3d_isometric", "3d_perspective"
- `min_depth` (float): Minimum depth for visualization (0.0-1.0, default: 0.0)
- `max_depth` (float): Maximum depth for visualization (0.0-1.0, default: 1.0)
- `contour_interval` (float): Contour line interval (0.0-1.0, default: 0.1)
- `3d_rotation_x` (float): 3D rotation X angle (-180 to 180, default: 0)
- `3d_rotation_y` (float): 3D rotation Y angle (-180 to 180, default: 0)
- `3d_rotation_z` (float): 3D rotation Z angle (-180 to 180, default: 0)
- `3d_camera_distance` (float): 3D camera distance (1.0-50.0, default: 10.0)
- `3d_lighting` (bool): Enable 3D lighting (default: True)

### Inputs
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Visualized depth [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform depth estimation (requires input depth buffer)
- Does NOT support depth buffer export (visualization only)
- Does NOT implement advanced 3D rendering (simple projection only)
- Does NOT handle depth buffer compression (raw depth only)
- Does NOT support depth buffer filtering (raw depth only)

## Test Plan

### Unit Tests
1. `test_visualization_initialization()`
   - Verify METADATA constants
   - Test parameter validation (min_depth 0-1, max_depth 0-1, contour_interval 0-1)
   - Test default parameter values

2. `test_visualization_modes()`
   - Test all visualization_mode options: grayscale, heatmap, rainbow, contour, 3d_isometric, 3d_perspective
   - Verify each mode produces distinct visual output
   - Test mode switching mid-stream

3. `test_depth_clamping()`
   - Test min_depth and max_depth parameters
   - Verify depth values clamped to specified range
   - Test depth normalization

4. `test_contour_mode()`
   - Test contour_interval: 0.0, 0.1, 0.5, 1.0
   - Verify contour lines appear at correct intervals
   - Test contour line thickness and color

5. `test_3d_modes()`
   - Test 3d_rotation_x, 3d_rotation_y, 3d_rotation_z individually
   - Verify 3D rotation matrices applied correctly
   - Test 3d_camera_distance scaling
   - Test 3d_lighting enable/disable

6. `test_3d_projection()`
   - Test 3d_isometric vs 3d_perspective modes
   - Verify perspective division
   - Test depth-based scaling in 3D

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with visualization_mode="heatmap"
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 500MB

2. `test_real_depth_visualization()`
   - Feed real depth map from MiDaS/DPT
   - Verify visualization accurately represents depth structure
   - Test with various depth ranges and noise levels

3. `test_3d_visualization_performance()`
   - Test 3d_isometric and 3d_perspective modes
   - Measure FPS impact of 3D rendering
   - Test with different camera distances

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Implement multiple visualization algorithms
- Use color mapping for depth-to-color conversion
- Implement 3D projection for isometric/perspective modes
- Use OpenGL for 3D rendering when available

### Performance Optimizations
- Use GPU for color mapping and 3D projection (CUDA)
- Precompute color lookup tables for each visualization mode
- Implement 3D rendering with OpenGL VBO
- Use depth-based level of detail for 3D modes

### Memory Management
- Allocate visualization buffer same size as frame (1920×1080×3 = 6MB)
- Use 3D buffers for 3D modes (additional 2MB)
- Profile memory with 4K input, enforce < 2GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce min_depth < max_depth with warning
- Clamp contour_interval to [0.0, 1.0]
- Validate 3D rotation angles [-180, 180]
- Fallback to grayscale if 3D rendering fails

## Deliverables
1. `src/vjlive3/effects/depth_visualization_mode.py` - Main effect
2. `tests/effects/test_depth_visualization_mode.py` - Tests
3. `docs/effects/depth_visualization_mode.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ All visualization modes work correctly
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
