# P3-EXT068: Dimension Splice Datamosh Effect

## What This Module Does
Creates a multi-dimensional datamosh effect that splices together different visual dimensions based on depth, simulating a reality-warping effect where different depth layers exist in separate dimensional planes that merge and fracture.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Dimension Splice Datamosh",
    "id": "P3-EXT068",
    "category": "depth_effects",
    "description": "Multi-dimensional reality splicing with depth-based dimension separation and datamosh corruption",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "DatamoshCore"],
    "test_coverage": 85
}
```

### Parameters
- `dimension_count` (int): Number of dimensions to splice (2-8, default: 4)
- `depth_splitting` (str): How depth maps to dimensions: "discrete_layers", "continuous", "gradient_split", "random_assign"
- `splice_intensity` (float): Strength of dimension boundary effects (0.0-1.0, default: 0.5)
- `dimensional_drift` (float): How much dimensions drift apart (0.0-1.0, default: 0.3)
- `datamosh_per_dimension` (bool): Apply unique datamosh per dimension (default: True)
- `reintegration_mode` (str): How dimensions recombine: "smooth", "hard_edge", "glitch_edge", "morph"
- `temporal_phase` (float): Animation phase for dimensional movement (0.0-1.0, animated)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Dimension-spliced output [B, 3, H, W]

## What It Does NOT Do
- Does NOT create actual parallel dimensions (visual effect only)
- Does NOT support true 4D+ spatial manipulation (limited to 2D screen)
- Does NOT preserve video quality (intentionally corrupts)
- Does NOT handle dimensional persistence across scenes (frame-local)
- Does NOT support user navigation between dimensions (automatic splicing only)

## Test Plan

### Unit Tests
1. `test_dimension_splice_initialization()`
   - Verify METADATA constants
   - Test parameter validation (dimension_count 2-8, splice_intensity 0-1, dimensional_drift 0-1)
   - Test default parameter values

2. `test_depth_to_dimension_mapping()`
   - Test all depth_splitting modes: discrete_layers, continuous, gradient_split, random_assign
   - Create synthetic depth map with known regions
   - Verify dimension assignment matches mapping strategy

3. `test_dimension_count_scaling()`
   - Test dimension_count: 2, 4, 8
   - Verify correct number of dimension zones
   - Test performance vs dimension count

4. `test_splice_intensity()`
   - Test splice_intensity: 0.0, 0.5, 1.0
   - Verify boundary effect strength
   - Test splice artifact visibility

5. `test_dimensional_drift()`
   - Test dimensional_drift: 0.0, 0.3, 1.0
   - Verify dimensions separate over time
   - Test drift animation smoothness

6. `test_datamosh_per_dimension()`
   - Enable/disable datamosh_per_dimension
   - Verify unique glitch patterns per dimension
   - Test datamosh intensity variation

7. `test_reintegration_modes()`
   - Test all reintegration_mode options: smooth, hard_edge, glitch_edge, morph
   - Verify dimension boundary rendering
   - Test mode switching

8. `test_temporal_phase_animation()`
   - Animate temporal_phase parameter
   - Verify dimensional movement over time
   - Test phase wrapping at 1.0

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with dimension_count=4
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_real_depth_dimension_splicing()`
   - Feed real depth map from MiDaS/DPT
   - Verify dimensions align with scene depth structure
   - Test with complex scenes (multiple depth layers)

3. `test_dimensional_drift_animation()`
   - Animate dimensional_drift over time
   - Verify dimensions drift and separate
   - Test with moving depth maps

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Use `DatamoshCore` from legacy vjlive plugins
- Implement depth-to-dimension mapping based on depth_splitting strategy
- Create dimension buffers: one per dimension (max 8)
- Apply datamosh per dimension if datamosh_per_dimension=True
- Implement reintegration by blending dimension buffers with splice boundaries
- Use temporal_phase to animate dimensional drift

### Performance Optimizations
- Use GPU for depth-to-dimension mapping (CUDA)
- Batch process dimension buffers in parallel
- Precompute dimension lookup table for depth values
- Use shared memory for dimension buffer access

### Memory Management
- Allocate dimension buffers: dimension_count × frame_size (max: 8 × 6MB = 48MB)
- Use temporal buffer for drift state (1 frame)
- Profile memory with 4K input, enforce < 4GB peak
- Free dimension buffers immediately after reintegration

### Safety Rails
- Enforce dimension_count ≤ 8 (memory limit)
- Clamp splice_intensity, dimensional_drift to [0.0, 1.0]
- Validate depth_splitting and reintegration_mode as valid options
- Fallback to 2 dimensions if memory constrained

## Deliverables
1. `src/vjlive3/effects/dimension_splice_datamosh_effect.py` - Main effect
2. `tests/effects/test_dimension_splice_datamosh_effect.py` - Tests
3. `docs/effects/dimension_splice_datamosh_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p with dimension_count=4 on RTX 4070 Ti Super
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
