# P3-EXT071: Dolly Zoom Datamosh Effect

## What This Module Does
Combines the classic dolly zoom (Vertigo effect) with depth-based datamosh glitching, creating a disorienting effect where the camera appears to move through the scene while depth layers glitch and distort independently.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Dolly Zoom Datamosh",
    "id": "P3-EXT071",
    "category": "depth_effects",
    "description": "Dolly zoom effect combined with depth-driven datamosh for disorienting perspective warping",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "DollyZoomEngine", "DatamoshCore"],
    "test_coverage": 85
}
```

### Parameters
- `zoom_speed` (float): Rate of zoom change (-5.0 to 5.0, default: 1.0)
- `dolly_speed` (float): Rate of dolly movement (-5.0 to 5.0, default: -1.0)
- `depth_zoom_mapping` (str): How depth affects zoom: "near_zoom", "far_zoom", "mid_zoom", "uniform"
- `datamosh_intensity` (float): Glitch strength (0.0-1.0, default: 0.4)
- `glitch_layer_separation` (bool): Glitch depth layers independently (default: True)
- `perspective_shift` (float): Additional perspective distortion (0.0-1.0, default: 0.2)
- `motion_blur` (float): Motion blur amount (0.0-1.0, default: 0.3)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Dolly-zoomed glitched output [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform actual camera movement (simulated via perspective transform)
- Does NOT support stereoscopic dolly zoom (2D only)
- Does NOT preserve video quality (intentionally distorts)
- Does NOT handle complex 3D scene geometry (simple depth-based warping)
- Does NOT support dolly zoom for fisheye lenses (rectilinear only)

## Test Plan

### Unit Tests
1. `test_dolly_zoom_initialization()`
   - Verify METADATA constants
   - Test parameter validation (zoom_speed -5 to 5, dolly_speed -5 to 5, datamosh_intensity 0-1)
   - Test default parameter values

2. `test_zoom_and_dolly_parameters()`
   - Test zoom_speed: -2.0, 0.0, 2.0
   - Test dolly_speed: -2.0, 0.0, 2.0
   - Verify zoom and dolly combine correctly
   - Test extreme values

3. `test_depth_zoom_mapping()`
   - Test all depth_zoom_mapping modes: near_zoom, far_zoom, mid_zoom, uniform
   - Create synthetic depth map with varying regions
   - Verify zoom strength varies with depth

4. `test_dolly_zoom_perspective_transform()`
   - Verify perspective matrix calculation
   - Test focal length simulation
   - Test perspective center point

5. `test_datamosh_integration()`
   - Test datamosh_intensity: 0.0, 0.4, 1.0
   - Verify glitch appears after perspective transform
   - Test glitch quality vs performance

6. `test_glitch_layer_separation()`
   - Enable/disable glitch_layer_separation
   - Verify depth layers glitch independently when enabled
   - Test uniform glitch when disabled

7. `test_perspective_shift()`
   - Test perspective_shift: 0.0, 0.2, 1.0
   - Verify additional perspective distortion
   - Test shift direction and magnitude

8. `test_motion_blur()`
   - Test motion_blur: 0.0, 0.3, 1.0
   - Verify motion blur effect
   - Test blur quality vs performance

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with zoom_speed=1.0, dolly_speed=-1.0
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_real_depth_dolly_zoom()`
   - Feed real depth map from MiDaS/DPT
   - Verify dolly zoom effect with real depth
   - Test with complex scenes (people, objects, backgrounds)

3. `test_dolly_zoom_animation()`
   - Animate zoom_speed and dolly_speed over time
   - Verify smooth perspective transitions
   - Test with different depth_zoom_mapping modes

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `DollyZoomEngine` from VJlive-2 if available
- Use `DatamoshCore` from legacy vjlive plugins
- Implement perspective transform: compute homography from zoom + dolly parameters
- Apply depth-driven zoom variation: zoom_per_pixel = base_zoom × depth_factor
- Apply datamosh after perspective transform if glitch_layer_separation=False
- Apply datamosh per depth layer if glitch_layer_separation=True

### Performance Optimizations
- Use GPU for perspective transform (CUDA)
- Precompute perspective transformation matrices
- Use shared memory for depth-based zoom lookup
- Batch process datamosh operations

### Memory Management
- Allocate transform buffer same size as frame (1920×1080×3 = 6MB)
- Use layer buffers if glitch_layer_separation=True (max 8 layers × 6MB = 48MB)
- Profile memory with 4K input, enforce < 4GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce zoom_speed and dolly_speed within [-5.0, 5.0]
- Clamp datamosh_intensity to [0.0, 1.0], perspective_shift to [0.0, 1.0]
- Validate depth_zoom_mapping as valid option
- Fallback to simple zoom if depth missing

## Deliverables
1. `src/vjlive3/effects/dolly_zoom_datamosh_effect.py` - Main effect
2. `tests/effects/test_dolly_zoom_datamosh_effect.py` - Tests
3. `docs/effects/dolly_zoom_datamosh_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Dolly zoom effect works with depth variation
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
