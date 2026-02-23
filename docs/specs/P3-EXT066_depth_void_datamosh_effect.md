# P3-EXT066: Depth Void Datamosh Effect

## What This Module Does
Creates a void-like datamosh effect where depth values determine areas of digital corruption and emptiness, simulating a descent into a black hole of glitched reality where deeper depths consume the visual information.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Depth Void Datamosh",
    "id": "P3-EXT066",
    "category": "depth_effects",
    "description": "Void-themed datamosh where depth creates consuming corruption zones",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "DatamoshCore"],
    "test_coverage": 85
}
```

### Parameters
- `void_intensity` (float): Strength of void corruption (0.0-1.0, default: 0.6)
- `depth_void_mapping` (str): How depth creates void: "deep_void", "shallow_void", "mid_void", "gradient_void"
- `void_expansion` (float): Rate void spreads from deep areas (0.0-1.0, default: 0.3)
- `void_color` (list[int]): RGB color of void corruption [0-255, 0-255, 0-255], default: [0, 0, 0]
- `void_edge_glow` (bool): Enable glowing edges around void zones (default: True)
- `edge_glow_intensity` (float): Edge glow strength (0.0-1.0, default: 0.5)
- `temporal_decay` (float): How quickly void recedes (0.0-1.0, default: 0.2)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Void-corrupted output [B, 3, H, W]

## What It Does NOT Do
- Does NOT create actual black holes (visual metaphor only)
- Does NOT simulate gravitational lensing (simple void expansion)
- Does NOT preserve video quality (intentionally corrupts)
- Does NOT support 3D volumetric voids (2D screen-space only)
- Does NOT handle void persistence across scenes (frame-local)

## Test Plan

### Unit Tests
1. `test_void_datamosh_initialization()`
   - Verify METADATA constants
   - Test parameter validation (void_intensity 0-1, void_expansion 0-1, edge_glow_intensity 0-1)
   - Test default void_color

2. `test_depth_void_mapping()`
   - Test all depth_void_mapping modes: deep_void, shallow_void, mid_void, gradient_void
   - Create synthetic depth map with varying regions
   - Verify void zones appear at correct depths

3. `test_void_expansion()`
   - Test void_expansion: 0.0, 0.3, 1.0
   - Verify void spreads from initial zones
   - Test expansion rate and saturation

4. `test_void_color_and_edge_glow()`
   - Test void_color parameter with custom RGB values
   - Enable/disable void_edge_glow
   - Verify edge glow intensity scaling
   - Test edge glow color (typically complementary to void)

5. `test_temporal_decay()`
   - Test temporal_decay: 0.0, 0.2, 1.0
   - Verify void recedes over time
   - Test decay smoothness

6. `test_void_intensity_scaling()`
   - Test void_intensity: 0.0, 0.6, 1.0
   - Verify corruption strength
   - Test intensity vs quality tradeoff

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with void_intensity=0.6
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_real_depth_void_creation()`
   - Feed real depth map from MiDaS/DPT
   - Verify void zones align with depth structure
   - Test with complex scenes (multiple depth layers)

3. `test_void_dynamics()`
   - Animate void_expansion and temporal_decay
   - Verify void grows and recedes realistically
   - Test with moving depth maps

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Use `DatamoshCore` from legacy vjlive plugins
- Implement void as depth-based mask: void_mask = f(depth, depth_void_mapping)
- Apply void corruption: output = video × (1 - void_mask) + void_color × void_mask × void_intensity
- Implement void expansion by dilating void_mask over time
- Implement temporal decay by reducing void_mask each frame

### Performance Optimizations
- Use GPU for void mask computation (CUDA)
- Precompute void expansion kernel
- Use temporal buffer for decay state
- Optimize datamosh operations for void regions only

### Memory Management
- Allocate void buffer same size as frame (1920×1080×3 = 6MB)
- Use temporal buffer for decay state (1 frame)
- Profile memory with 4K input, enforce < 4GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce void_intensity ≤ 1.0, void_expansion ≤ 1.0, edge_glow_intensity ≤ 1.0
- Clamp temporal_decay to [0.0, 1.0]
- Validate void_color as valid RGB [0-255]
- Fallback to simple corruption if depth missing

## Deliverables
1. `src/vjlive3/effects/depth_void_datamosh_effect.py` - Main effect
2. `tests/effects/test_depth_void_datamosh_effect.py` - Tests
3. `docs/effects/depth_void_datamosh_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Void zones correctly map to depth
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
