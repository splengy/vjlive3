# P3-EXT081: Fractal Generator Fractal Generator

## What This Module Does
Generates fractal patterns and visuals using depth information to influence fractal parameters, creating complex, depth-driven fractal imagery that responds to scene depth for dynamic visual effects.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Fractal Generator Fractal Generator",
    "id": "P3-EXT081",
    "category": "depth_effects",
    "description": "Depth-driven fractal generation with multiple fractal types and parameters",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "FractalEngine"],
    "test_coverage": 85
}
```

### Parameters
- `fractal_type` (str): Fractal type: "mandelbrot", "julia", "burning_ship", "tricorn", "newton", "custom"
- `depth_fractal_mapping` (str): How depth affects fractal: "zoom", "offset", "rotation", "color", "all"
- `max_iterations` (int): Maximum fractal iterations (10-500, default: 100)
- `color_scheme` (str): Color scheme: "grayscale", "rainbow", "fire", "ice", "custom"
- `custom_color_map` (list[list[int]]): Custom color map for color_scheme="custom" (256×3 RGB values)
- `smooth_coloring` (bool): Enable smooth coloring (default: True)
- `depth_scale` (float): Depth influence multiplier (0.0-5.0, default: 1.0)
- `animation_speed` (float): Fractal animation speed (0.0-2.0, default: 0.5)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Fractal output [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform high-resolution fractal rendering at 4K (performance limit)
- Does NOT support arbitrary fractal types (limited to predefined)
- Does NOT handle fractal zoom to arbitrary precision (limited by float)
- Does NOT preserve video quality (fractal generation replaces)
- Does NOT support fractal export to image formats (visual only)

## Test Plan

### Unit Tests
1. `test_fractal_generator_initialization()`
   - Verify METADATA constants
   - Test parameter validation (max_iterations 10-500, depth_scale 0-5, animation_speed 0-2)
   - Test default parameter values

2. `test_fractal_types()`
   - Test all fractal_type options: mandelbrot, julia, burning_ship, tricorn, newton, custom
   - Verify each fractal produces correct patterns
   - Test fractal switching

3. `test_depth_fractal_mapping()`
   - Test all depth_fractal_mapping modes: zoom, offset, rotation, color, all
   - Create synthetic depth map with varying regions
   - Verify fractal parameters vary with depth

4. `test_max_iterations_scaling()`
   - Test max_iterations: 10, 100, 500
   - Verify fractal detail vs performance tradeoff
   - Test iteration count impact

5. `test_color_schemes()`
   - Test all color_scheme options: grayscale, rainbow, fire, ice, custom
   - Verify color mapping correctness
   - Test custom color map loading

6. `test_smooth_coloring()`
   - Enable/disable smooth_coloring
   - Verify smooth vs banded coloring
   - Test smooth coloring quality

7. `test_depth_scale_and_animation()`
   - Test depth_scale: 0.0, 1.0, 5.0
   - Test animation_speed: 0.0, 0.5, 2.0
   - Verify animation smoothness

8. `test_fractal_calculation()`
   - Test fractal escape time algorithm
   - Verify iteration counts correct
   - Test with different complex plane regions

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with max_iterations=100
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 500MB

2. `test_real_depth_fractal_modulation()`
   - Feed real depth map from MiDaS/DPT
   - Verify depth-based fractal variations
   - Test with complex scenes (people, objects, backgrounds)

3. `test_fractal_performance_scaling()`
   - Test max_iterations scaling: 10, 100, 500
   - Verify FPS degradation is linear
   - Test memory scaling

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `FractalEngine` from VJlive-2 if available
- Implement escape-time fractal algorithms for each type
- Add depth-driven parameter modulation: zoom, offset, rotation, color
- Use depth to control fractal parameters dynamically
- Implement smooth coloring using normalized iteration counts

### Performance Optimizations
- Use GPU for fractal calculation (CUDA)
- Precompute fractal lookup tables for common parameters
- Use shared memory for iteration buffer
- Implement fractal LOD for distance

### Memory Management
- Allocate iteration buffer: H × W × 4 bytes (int32)
- Use temporal buffer for animation (1 frame)
- Profile memory with 4K input, enforce < 2GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce max_iterations 10-500
- Clamp depth_scale to [0.0, 5.0], animation_speed to [0.0, 2.0]
- Validate fractal_type and depth_fractal_mapping as valid options
- Fallback to mandelbrot if fractal type invalid

## Deliverables
1. `src/vjlive3/effects/fractal_generator_fractal_generator.py` - Main effect
2. `tests/effects/test_fractal_generator_fractal_generator.py` - Tests
3. `docs/effects/fractal_generator_fractal_generator.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p with max_iterations=100 on RTX 4070 Ti Super
- ✅ Depth-based fractal variations work correctly
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
