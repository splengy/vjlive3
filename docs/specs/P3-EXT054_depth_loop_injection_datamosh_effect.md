# P3-EXT054: Depth Loop Injection Datamosh Effect

## What This Module Does
Creates a datamosh effect that injects looped patterns based on depth information. The effect creates repeating, glitchy patterns that are modulated by depth, producing a sense of depth-based rhythmic corruption. Useful for creating hypnotic, looping datamosh visuals.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthLoopInjectionDatamosh",
    "version": "3.0.0",
    "description": "Loop-based datamosh with depth modulation",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "datamosh",
    "tags": ["depth", "datamosh", "loop", "injection", "rhythmic"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `loop_period: int` (default: 30, min: 5, max: 120) - Loop length in frames
- `injection_strength: float` (default: 0.5, min: 0.0, max: 1.0) - How strongly loops are injected
- `depth_modulation: float` (default: 0.7, min: 0.0, max: 1.0) - Depth's influence on injection pattern
- `glitch_probability: float` (default: 0.1, min: 0.0, max: 0.5) - Chance of random glitches per frame
- `pattern_scale: int` (default: 8, min: 2, max: 32) - Size of datamosh blocks
- `loop_blend_mode: str` (default: "additive", options: ["additive", "alpha", "multiply"]) - How loops blend
- `phase_shift: float` (default: 0.0, min: 0.0, max: 1.0) - Phase offset for loop start
- `depth_threshold: float` (default: 0.3, min: 0.0, max: 1.0) - Minimum depth for injection

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `frame_count: int` (optional) - Current frame number for loop synchronization

### Outputs
- `video: Frame` (same format as input) - Video with loop injection datamosh

## What It Does NOT Do
- Does NOT support arbitrary loop lengths beyond frame-based period
- Does NOT perform audio-synced looping (frame count only)
- Does NOT include loop point editing or manual control
- Does NOT handle HDR metadata preservation
- Does NOT support multiple simultaneous loops
- Does NOT include loop visualization or debugging

## Test Plan
1. Unit tests for loop buffer management
2. Verify injection pattern follows depth modulation
3. Test loop_period and phase_shift interactions
4. Performance: ≥ 60 FPS at 1080p
5. Memory: < 150MB additional RAM (loop buffers)
6. Visual: verify looping creates rhythmic datamosh patterns

## Implementation Notes
- Maintain a circular buffer of previous frames of size loop_period
- For each frame, compute injection weight based on depth and loop phase
- Loop phase = ((frame_count + phase_shift) % loop_period) / loop_period
- For each macroblock of size pattern_scale:
  - If depth > depth_threshold and injection_weight > random:
    - Replace with frame from loop buffer at phase offset
    - Apply glitch effects if glitch_probability triggers
- Blend injected blocks with original using loop_blend_mode
- Use depth_modulation to scale injection_strength based on depth
- Optimize with block-based processing and buffer reuse
- Follow SAFETY_RAILS: cap buffer size, handle edge cases

## Deliverables
- `src/vjlive3/effects/depth_loop_injection_datamosh.py`
- `tests/effects/test_depth_loop_injection_datamosh.py`
- `docs/plugins/depth_loop_injection_datamosh.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Loop injection works with depth modulation
- [x] Looping behavior is consistent
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations