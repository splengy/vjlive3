# P3-EXT059: Depth Parallel Universe Datamosh Effect

## What This Module Does
Implements a psychedelic datamosh effect that creates multiple parallel reality layers based on depth values, with each depth range representing a different temporal/visual universe that glitches and merges independently.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Depth Parallel Universe Datamosh",
    "id": "P3-EXT059",
    "category": "depth_effects",
    "description": "Creates multiple parallel reality layers from depth values with independent datamosh glitching",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "DatamoshCore"],
    "test_coverage": 85
}
```

### Parameters
- `universe_count` (int): Number of parallel reality layers (3-12, default: 5)
- `depth_ranges` (list[float]): Depth thresholds separating universes [0.0-1.0], length = universe_count-1
- `glitch_intensity` (float): Datamosh corruption per universe (0.0-1.0, default: 0.4)
- `reality_bleed` (float): Cross-contamination between universes (0.0-1.0, default: 0.15)
- `temporal_phase` (float): Phase offset per universe (0.0-1.0, animated)
- `merge_mode` (str): How universes combine: "additive", "multiply", "screen", "difference"

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Glitched multi-universe output [B, 3, H, W]

## What It Does NOT Do
- Does NOT create actual parallel dimensions (visual metaphor only)
- Does NOT preserve original video quality (intentionally corrupts)
- Does NOT support 3D stereoscopic depth (single depth map only)
- Does NOT perform temporal coherence across frames (each universe glitches independently)
- Does NOT handle HDR content (SDR only, 8-bit)

## Test Plan

### Unit Tests
1. `test_parallel_universe_initialization()`
   - Verify METADATA constants
   - Test parameter validation (universe_count 3-12, glitch_intensity 0-1)
   - Test default depth_ranges auto-generation

2. `test_universe_segmentation()`
   - Create synthetic depth map with 5 distinct regions
   - Verify each depth range maps to correct universe index
   - Test edge cases at depth threshold boundaries

3. `test_datamosh_per_universe()`
   - Apply glitch effect to each universe separately
   - Verify different glitch seeds per universe
   - Test glitch_intensity scaling

4. `test_reality_bleed()`
   - Set reality_bleed > 0, verify cross-universe contamination
   - Test bleed amount scaling
   - Ensure bleed respects depth boundaries

5. `test_merge_modes()`
   - Test all merge_mode options: additive, multiply, screen, difference
   - Verify numerical stability (no NaN/Inf)
   - Test merge with 2+ universes

6. `test_temporal_phase_animation()`
   - Animate temporal_phase parameter
   - Verify phase offset creates per-universe time shifts
   - Test phase wrapping at 1.0

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_depth_driven_universes()`
   - Feed real depth map from MiDaS/DPT
   - Verify universes align with depth structure
   - Test with gradient, discrete steps, noisy depth

3. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged with context

## Implementation Notes

### Architecture
- Build on existing `DepthEffect` base class from P3-VD35
- Reuse `DatamoshCore` from legacy vjlive datamosh plugins
- Implement universe segmentation as depth thresholding + label assignment
- Each universe gets independent glitch RNG with seed = universe_index + frame_seed

### Performance Optimizations
- Precompute universe lookup table for depth values (256 bins)
- Batch process all universes in parallel using vectorized operations
- Use CUDA kernels for glitch operations if GPU available
- Cache glitch patterns for static glitch_intensity settings

### Memory Management
- Allocate one buffer per universe (max 12) → 12x memory overhead worst-case
- Use in-place operations where possible
- Free universe buffers immediately after merge
- Profile memory with 4K input, enforce < 4GB peak

### Safety Rails
- Enforce universe_count ≤ 12 (memory limit)
- Clamp glitch_intensity to [0, 1] with warning log if exceeded
- Validate depth range [0, 1] with clear error message
- Fallback to single universe if merge fails

## Deliverables
1. `src/vjlive3/effects/depth_parallel_universe_datamosh.py` - Main effect implementation
2. `tests/effects/test_depth_parallel_universe_datamosh.py` - Unit + integration tests
3. `docs/effects/depth_parallel_universe_datamosh.md` - User documentation
4. Update `MODULE_MANIFEST.md` with new plugin entry

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Zero safety rail violations (memory, errors, silent failures)
- ✅ Works with real depth maps from MiDaS/DPT
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
