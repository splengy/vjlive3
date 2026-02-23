# P3-EXT072: VTemPi Duty Cycle Mode

## What This Module Does
Implements a duty cycle modulation effect for VTemPi (Visual Tempo) system, where depth values control the duty cycle of visual rhythms and patterns, creating depth-aware tempo variations and rhythmic visual effects.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "VTemPi Duty Cycle Mode",
    "id": "P3-EXT072",
    "category": "depth_effects",
    "description": "Depth-driven duty cycle modulation for VTemPi visual rhythms and tempo variations",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "VTemPiEngine"],
    "test_coverage": 85
}
```

### Parameters
- `duty_cycle_base` (float): Base duty cycle (0.0-1.0, default: 0.5)
- `depth_duty_mapping` (str): How depth affects duty cycle: "near_long", "far_long", "mid_long", "uniform"
- `duty_cycle_variation` (float): Duty cycle variation amount (0.0-0.5, default: 0.2)
- `tempo_base` (float): Base tempo in BPM (30-180, default: 60)
- `depth_tempo_mapping` (str): How depth affects tempo: "near_fast", "far_fast", "mid_fast", "uniform"
- `tempo_variation` (float): Tempo variation amount (0.0-50.0, default: 20.0)
- `rhythm_pattern` (str): Rhythm pattern: "straight", "swing", "shuffle", "syncopated"

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): VTemPi modulated output [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform actual audio tempo detection (visual tempo only)
- Does NOT support complex polyrhythms (simple duty cycle modulation)
- Does NOT preserve video quality (intentionally modulates)
- Does NOT handle VTemPi pattern generation (only duty cycle modulation)
- Does NOT support VTemPi for 3D scenes (2D screen-space only)

## Test Plan

### Unit Tests
1. `test_vtempi_duty_cycle_initialization()`
   - Verify METADATA constants
   - Test parameter validation (duty_cycle_base 0-1, tempo_base 30-180, duty_cycle_variation 0-0.5)
   - Test default parameter values

2. `test_duty_cycle_parameters()`
   - Test duty_cycle_base: 0.0, 0.5, 1.0
   - Test duty_cycle_variation: 0.0, 0.2, 0.5
   - Verify duty cycle calculation
   - Test extreme values

3. `test_depth_duty_mapping()`
   - Test all depth_duty_mapping modes: near_long, far_long, mid_long, uniform
   - Create synthetic depth map with varying regions
   - Verify duty cycle varies with depth

4. `test_tempo_parameters()`
   - Test tempo_base: 30, 60, 180
   - Test tempo_variation: 0.0, 20.0, 50.0
   - Verify tempo calculation
   - Test BPM scaling

5. `test_depth_tempo_mapping()`
   - Test all depth_tempo_mapping modes: near_fast, far_fast, mid_fast, uniform
   - Create synthetic depth map with varying regions
   - Verify tempo varies with depth

6. `test_rhythm_patterns()`
   - Test all rhythm_pattern options: straight, swing, shuffle, syncopated
   - Verify rhythm pattern generation
   - Test pattern switching

7. `test_duty_cycle_and_tempo_interaction()`
   - Test combined duty cycle and tempo modulation
   - Verify synchronized modulation
   - Test with different depth mappings

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with duty_cycle_base=0.5, tempo_base=60
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_real_depth_vtempi_modulation()`
   - Feed real depth map from MiDaS/DPT
   - Verify depth-based duty cycle and tempo variations
   - Test with complex scenes (people, objects, backgrounds)

3. `test_rhythm_pattern_variation()`
   - Test all rhythm_pattern options
   - Verify distinct rhythmic patterns
   - Test with different depth mappings

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `VTemPiEngine` from VJlive-2 if available
- Implement duty cycle modulation: duty_cycle = base + depth_factor × variation
- Implement tempo modulation: tempo = base + depth_factor × variation
- Add rhythm pattern generation based on duty cycle and tempo
- Use depth-driven modulation for both duty cycle and tempo

### Performance Optimizations
- Use GPU for duty cycle and tempo calculation (CUDA)
- Precompute depth factor lookup table
- Use shared memory for modulation buffer access
- Implement modulation LOD for distance

### Memory Management
- Allocate modulation buffer same size as frame (1920×1080×1 = 2MB for duty/tempo)
- Use temporal buffer for rhythm pattern (1 frame)
- Profile memory with 4K input, enforce < 4GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce duty_cycle_base 0-1, tempo_base 30-180, duty_cycle_variation 0-0.5
- Clamp tempo_variation to [0.0, 50.0]
- Validate depth_duty_mapping and depth_tempo_mapping as valid options
- Fallback to uniform modulation if depth missing

## Deliverables
1. `src/vjlive3/effects/vtempi_duty_cycle_mode.py` - Main effect
2. `tests/effects/test_vtempi_duty_cycle_mode.py` - Tests
3. `docs/effects/vtempi_duty_cycle_mode.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Depth-based duty cycle and tempo variations work correctly
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
