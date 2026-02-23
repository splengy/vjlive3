# P3-EXT063: Depth Raver Datamosh Effect

## What This Module Does
Creates an intense, rhythmic datamosh effect synchronized to audio beats, where depth values control the intensity and pattern of the glitch, producing a rave-like visual experience that pulses with the music.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Depth Raver Datamosh",
    "id": "P3-EXT063",
    "category": "depth_effects",
    "description": "Beat-synchronized datamosh effect with depth-driven glitch patterns for rave visuals",
    "inputs": ["video", "depth", "audio_beat"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "DatamoshCore", "BeatDetector"],
    "test_coverage": 85
}
```

### Parameters
- `glitch_intensity` (float): Base datamosh strength (0.0-1.0, default: 0.6)
- `beat_response` (float): How strongly beats trigger glitches (0.0-1.0, default: 0.8)
- `depth_glitch_mapping` (str): How depth affects glitch: "near_more", "far_more", "mid_more", "uniform"
- `decay_time` (float): Glitch decay after beat in seconds (0.1-2.0, default: 0.5)
- `rave_mode` (str): Glitch style: "acid", "hardcore", "psychedelic", "industrial"
- `color_shift` (bool): Enable RGB shift during glitches (default: True)
- `block_size` (int): Datamosh block size in pixels (2-32, default: 8)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1
- `audio_beat` (torch.Tensor[float]): Beat trigger signal [B, 1] or [B] with values 0.0-1.0

### Outputs
- `video` (torch.Tensor[uint8]): Glitched rave output [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform real-time beat detection (requires external audio_beat input)
- Does NOT support multi-band audio analysis (single beat trigger only)
- Does NOT handle audio-to-video latency compensation (assumes sync)
- Does NOT preserve video quality (intentionally corrupts)
- Does NOT support 3D audio spatialization (mono beat trigger)

## Test Plan

### Unit Tests
1. `test_raver_datamosh_initialization()`
   - Verify METADATA constants
   - Test parameter validation (glitch_intensity 0-1, beat_response 0-1, decay_time 0.1-2.0)
   - Test default rave_mode behavior

2. `test_beat_synchronized_glitch()`
   - Simulate beat triggers with audio_beat tensor
   - Verify glitch intensity spikes on beat
   - Test beat_response scaling
   - Verify decay curve after beat

3. `test_depth_glitch_mapping()`
   - Test all depth_glitch_mapping modes: near_more, far_more, mid_more, uniform
   - Create synthetic depth map with varying regions
   - Verify glitch distribution matches mapping

4. `test_rave_mode_variations()`
   - Test all rave_mode options: acid, hardcore, psychedelic, industrial
   - Verify each mode produces distinct glitch patterns
   - Test mode switching mid-stream

5. `test_color_shift_effect()`
   - Enable/disable color_shift parameter
   - Verify RGB shift appears during glitches
   - Test color shift intensity

6. `test_block_size_impact()`
   - Test block_size: 2, 8, 16, 32
   - Verify blocky artifact scale
   - Test performance vs quality tradeoff

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with synthetic beat triggers
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_audio_beat_integration()`
   - Feed real beat triggers from BeatDetector
   - Verify glitches align with music beats
   - Test with different music genres (EDM, hip-hop, rock)

3. `test_depth_driven_glitch_patterns()`
   - Feed real depth map from MiDaS/DPT
   - Verify depth regions glitch differently based on depth_glitch_mapping
   - Test with complex scenes (multiple depth layers)

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth or beat
   - Ensure all exceptions are logged with context

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `BeatDetector` from audio engine for beat timing
- Use `DatamoshCore` from legacy vjlive plugins
- Implement beat-triggered glitch envelope: intensity = base + beat_response × envelope × depth_factor
- Envelope decays exponentially: intensity(t) = intensity_peak × exp(-t / decay_time)

### Performance Optimizations
- Precompute glitch patterns for each rave_mode
- Use CUDA kernels for block-based datamosh operations
- Cache beat envelope state between frames
- Use async beat trigger processing to avoid audio blocking

### Memory Management
- Allocate glitch buffer same size as frame (1920×1080×3 = 6MB)
- Use ring buffer for glitch pattern history (3 frames)
- Profile memory with 4K input, enforce < 4GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce glitch_intensity ≤ 1.0, beat_response ≤ 1.0
- Clamp decay_time to [0.1, 2.0] seconds
- Validate block_size as power of 2 between 2-32
- Fallback to simple glitch if beat input missing (use last known beat)

## Deliverables
1. `src/vjlive3/effects/depth_raver_datamosh_effect.py` - Main effect
2. `tests/effects/test_depth_raver_datamosh_effect.py` - Tests
3. `docs/effects/depth_raver_datamosh_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Glitches perfectly sync to audio beats (latency < 10ms)
- ✅ Zero safety rail violations
- ✅ Works with real depth maps and audio beats
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
