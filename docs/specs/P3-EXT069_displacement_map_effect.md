# P3-EXT069: Displacement Map Effect

## What This Module Does
Applies displacement mapping using depth information to create geometric distortions where depth values control the amount and direction of pixel displacement, producing effects like water ripples, heat distortion, or depth-based warping.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Displacement Map",
    "id": "P3-EXT069",
    "category": "depth_effects",
    "description": "Depth-driven displacement mapping for geometric distortions and warping effects",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "DisplacementEngine"],
    "test_coverage": 85
}
```

### Parameters
- `displacement_strength` (float): Base displacement strength (0.0-1.0, default: 0.3)
- `depth_displacement_mapping` (str): How depth affects displacement: "near_more", "far_more", "mid_more", "uniform"
- `displacement_direction` (str): Displacement direction: "normal", "x_only", "y_only", "radial", "circular"
- `wave_frequency` (float): Wave frequency for animated displacement (0.0-10.0, default: 1.0)
- `wave_speed` (float): Wave animation speed (0.0-5.0, default: 1.0)
- `wave_amplitude` (float): Wave amplitude multiplier (0.0-1.0, default: 0.5)
- `displacement_noise` (float): Noise amount for organic displacement (0.0-1.0, default: 0.2)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Displaced output [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform 3D mesh displacement (2D screen-space only)
- Does NOT support displacement map export (visual effect only)
- Does NOT handle displacement for transparent objects (limited accuracy)
- Does NOT preserve video quality (intentionally distorts)
- Does NOT support displacement for complex geometry (simple displacement only)

## Test Plan

### Unit Tests
1. `test_displacement_initialization()`
   - Verify METADATA constants
   - Test parameter validation (displacement_strength 0-1, wave_frequency 0-10.0, wave_speed 0-5.0)
   - Test default parameter values

2. `test_depth_displacement_mapping()`
   - Test all depth_displacement_mapping modes: near_more, far_more, mid_more, uniform
   - Create synthetic depth map with varying regions
   - Verify displacement strength varies with depth

3. `test_displacement_direction()`
   - Test all displacement_direction options: normal, x_only, y_only, radial, circular
   - Verify displacement vector calculation
   - Test direction switching

4. `test_wave_animation()`
   - Test wave_frequency: 0.0, 1.0, 10.0
   - Test wave_speed: 0.0, 1.0, 5.0
   - Test wave_amplitude: 0.0, 0.5, 1.0
   - Verify wave animation smoothness

5. `test_displacement_noise()`
   - Test displacement_noise: 0.0, 0.2, 1.0
   - Verify organic noise in displacement
   - Test noise quality vs performance

6. `test_displacement_strength()`
   - Test displacement_strength: 0.0, 0.3, 1.0
   - Verify displacement magnitude
   - Test strength vs quality tradeoff

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with displacement_strength=0.3
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_real_depth_displacement()`
   - Feed real depth map from MiDaS/DPT
   - Verify depth-based displacement patterns
   - Test with complex scenes (people, objects, backgrounds)

3. `test_wave_animation_performance()`
   - Animate wave_frequency and wave_speed
   - Verify animation smoothness
   - Test with different displacement_direction modes

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `DisplacementEngine` from VJlive-2 if available
- Implement depth-driven displacement: displacement = f(depth, depth_displacement_mapping) × displacement_strength
- Add wave animation: displacement += wave_function(wave_frequency, wave_speed, wave_amplitude)
- Add noise: displacement += noise(displacement_noise)
- Implement displacement direction vectors based on displacement_direction

### Performance Optimizations
- Use GPU for displacement calculation (CUDA)
- Precompute displacement lookup table for depth values
- Use shared memory for displacement buffer access
- Implement displacement LOD for distance

### Memory Management
- Allocate displacement buffer same size as frame (1920×1080×2 = 4MB for x,y offsets)
- Use temporal buffer for wave animation (1 frame)
- Profile memory with 4K input, enforce < 4GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce displacement_strength ≤ 1.0, wave_frequency ≤ 10.0, wave_speed ≤ 5.0
- Clamp displacement_noise to [0.0, 1.0]
- Validate depth_displacement_mapping and displacement_direction as valid options
- Fallback to simple displacement if depth missing

## Deliverables
1. `src/vjlive3/effects/displacement_map_effect.py` - Main effect
2. `tests/effects/test_displacement_map_effect.py` - Tests
3. `docs/effects/displacement_map_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Depth-based displacement patterns work correctly
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
