# P3-EXT065: Depth Slit Scan Datamosh Effect

## What This Module Does
Combines slit scan photography techniques with depth-based datamosh effects, creating temporal distortions where different depth ranges are scanned at different rates, producing surreal time-warp effects that vary with scene depth.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Depth Slit Scan Datamosh",
    "id": "P3-EXT065",
    "category": "depth_effects",
    "description": "Slit scan photography with depth-based temporal distortions and datamosh effects",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "SlitScanEngine", "DatamoshCore"],
    "test_coverage": 85
}
```

### Parameters
- `slit_position` (float): Vertical slit position (0.0-1.0, default: 0.5)
- `scan_speed` (float): Base scan speed multiplier (0.1-10.0, default: 1.0)
- `depth_speed_mapping` (str): How depth affects scan speed: "near_faster", "far_faster", "mid_faster", "uniform"
- `scan_direction` (str): Scan direction: "vertical", "horizontal", "diagonal"
- `datamosh_intensity` (float): Datamosh corruption strength (0.0-1.0, default: 0.4)
- `temporal_blend` (float): Temporal blending factor (0.0-1.0, default: 0.3)
- `feedback_amount` (float): Feedback loop amount (0.0-1.0, default: 0.2)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Slit-scanned output [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform real-time slit scanning at 4K resolution (performance limit)
- Does NOT support 3D slit scanning (2D only)
- Does NOT handle audio synchronization (video-only)
- Does NOT preserve original video quality (intentionally distorts)
- Does NOT support multi-pass scanning (single pass only)

## Test Plan

### Unit Tests
1. `test_slitscan_initialization()`
   - Verify METADATA constants
   - Test parameter validation (slit_position 0-1, scan_speed 0.1-10.0, datamosh_intensity 0-1)
   - Test default parameter values

2. `test_slit_position_and_direction()`
   - Test slit_position: 0.0, 0.5, 1.0
   - Test scan_direction: vertical, horizontal, diagonal
   - Verify slit position affects scan region

3. `test_depth_speed_mapping()`
   - Test depth_speed_mapping: near_faster, far_faster, mid_faster, uniform
   - Create synthetic depth map with varying regions
   - Verify scan speed varies with depth

4. `test_scan_speed_scaling()`
   - Test scan_speed: 0.1, 1.0, 10.0
   - Verify scan rate scaling
   - Test extreme speed values

5. `test_datamosh_integration()`
   - Test datamosh_intensity: 0.0, 0.4, 1.0
   - Verify datamosh corruption appears
   - Test datamosh quality vs performance

6. `test_temporal_blending()`
   - Test temporal_blend: 0.0, 0.3, 1.0
   - Verify temporal smoothing
   - Test blending artifacts

7. `test_feedback_loop()`
   - Test feedback_amount: 0.0, 0.2, 1.0
   - Verify feedback creates recursive effects
   - Test feedback stability

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with scan_speed=1.0
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_real_depth_slitscan()`
   - Feed real depth map from MiDaS/DPT
   - Verify depth-based speed variations
   - Test with complex scenes (people, objects, backgrounds)

3. `test_performance_scaling()`
   - Test scan_speed scaling: 0.1, 1.0, 10.0
   - Verify FPS degradation is linear
   - Test memory scaling

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `SlitScanEngine` from VJlive-2 if available
- Use `DatamoshCore` from legacy vjlive plugins
- Implement depth-driven scan speed: scan_speed_per_pixel = base_speed × depth_factor
- Depth factor depends on depth_speed_mapping: near_faster → factor = 1 + depth, far_faster → factor = 1 + (1-depth)
- Implement temporal blending using frame history buffer
- Implement feedback loop using previous output as input

### Performance Optimizations
- Use GPU for slit scanning operations (CUDA)
- Implement scan line caching for temporal blending
- Use scan line buffer for feedback loop
- Precompute depth factors for each pixel

### Memory Management
- Allocate scan buffer same size as frame (1920×1080×3 = 6MB)
- Use temporal buffer for blending (2 frames)
- Use feedback buffer for recursive effects (1 frame)
- Profile memory with 4K input, enforce < 4GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce scan_speed ≥ 0.1, datamosh_intensity ≤ 1.0
- Clamp temporal_blend to [0.0, 1.0]
- Validate feedback_amount to prevent instability
- Fallback to simple scan if depth missing

## Deliverables
1. `src/vjlive3/effects/depth_slitscan_datamosh_effect.py` - Main effect
2. `tests/effects/test_depth_slitscan_datamosh_effect.py` - Tests
3. `docs/effects/depth_slitscan_datamosh_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Depth-based speed variations work correctly
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
