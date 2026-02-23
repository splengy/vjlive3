# P3-EXT070: Dithering Effect

## What This Module Does
Applies dithering algorithms to video frames using depth information to create stylized, low-color-count visual effects with depth-based dithering patterns, producing retro or artistic visual styles.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Dithering",
    "id": "P3-EXT070",
    "category": "depth_effects",
    "description": "Depth-driven dithering algorithms for stylized low-color visual effects",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "DitherEngine"],
    "test_coverage": 85
}
```

### Parameters
- `dither_algorithm` (str): Dithering algorithm: "floyd_steinberg", "atkinson", "burkes", "sierra", "ordered_4x4", "ordered_8x8"
- `color_depth` (int): Target color depth (1-8 bits per channel, default: 4)
- `depth_dither_mapping` (str): How depth affects dithering: "near_more", "far_more", "mid_more", "uniform"
- `dither_intensity` (float): Dithering strength (0.0-1.0, default: 0.7)
- `ordered_matrix_size` (int): Ordered dither matrix size (2, 4, 8, default: 4)
- `random_seed` (int): Random seed for error diffusion (default: 0)
- `preserve_luminance` (bool): Preserve luminance during dithering (default: True)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Dithered output [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform color quantization (requires pre-quantized input)
- Does NOT support dithering for transparent objects (limited accuracy)
- Does NOT preserve original video quality (intentionally reduces color)
- Does NOT handle dithering for complex scenes with many colors (limited palette)
- Does NOT support dithering for HDR content (SDR only)

## Test Plan

### Unit Tests
1. `test_dithering_initialization()`
   - Verify METADATA constants
   - Test parameter validation (color_depth 1-8, ordered_matrix_size 2,4,8, dither_intensity 0-1)
   - Test default parameter values

2. `test_dither_algorithms()`
   - Test all dither_algorithm options: floyd_steinberg, atkinson, burkes, sierra, ordered_4x4, ordered_8x8
   - Verify each algorithm produces distinct dithering patterns
   - Test algorithm switching mid-stream

3. `test_color_depth_scaling()`
   - Test color_depth: 1, 2, 4, 8
   - Verify color reduction accuracy
   - Test palette size vs quality tradeoff

4. `test_depth_dither_mapping()`
   - Test all depth_dither_mapping modes: near_more, far_more, mid_more, uniform
   - Create synthetic depth map with varying regions
   - Verify dithering strength varies with depth

5. `test_ordered_dither_matrices()`
   - Test ordered_matrix_size: 2, 4, 8
   - Verify ordered dither patterns
   - Test matrix size vs quality tradeoff

6. `test_dither_intensity()`
   - Test dither_intensity: 0.0, 0.7, 1.0
   - Verify dithering strength
   - Test intensity vs quality tradeoff

7. `test_random_seed()`
   - Test random_seed parameter with different values
   - Verify reproducible dithering patterns
   - Test seed switching

8. `test_luminance_preservation()`
   - Enable/disable preserve_luminance
   - Verify luminance preservation
   - Test with different color_depth values

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with color_depth=4, dither_algorithm="floyd_steinberg"
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_real_depth_dithering()`
   - Feed real depth map from MiDaS/DPT
   - Verify depth-based dithering patterns
   - Test with complex scenes (people, objects, backgrounds)

3. `test_dither_algorithm_performance()`
   - Test all dither_algorithm options
   - Measure FPS vs quality tradeoff
   - Identify performance bottlenecks

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `DitherEngine` from VJlive-2 if available
- Implement multiple dithering algorithms: error diffusion (Floyd-Steinberg, Atkinson, Burkes, Sierra) and ordered dither (4x4, 8x8 matrices)
- Add depth-driven dithering strength: dither_strength = base_strength × depth_factor
- Implement color quantization with palette reduction
- Use temporal coherence for smooth dithering

### Performance Optimizations
- Use GPU for dithering operations (CUDA)
- Precompute ordered dither matrices
- Use shared memory for dithering buffer access
- Implement dithering LOD for distance

### Memory Management
- Allocate dither buffer same size as frame (1920×1080×3 = 6MB)
- Use temporal buffer for error diffusion (1 frame)
- Profile memory with 4K input, enforce < 4GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce color_depth 1-8 bits per channel
- Clamp dither_intensity to [0.0, 1.0]
- Validate dither_algorithm and depth_dither_mapping as valid options
- Fallback to simple dithering if depth missing

## Deliverables
1. `src/vjlive3/effects/dithering_effect.py` - Main effect
2. `tests/effects/test_dithering_effect.py` - Tests
3. `docs/effects/dithering_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ All dithering algorithms work correctly
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
