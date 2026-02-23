# P3-EXT048: Depth FXLoop Effect

## What This Module Does
Creates a feedback loop effect that processes the video through a series of depth-based effects in a cyclic manner. The output is fed back into the input with optional mixing, creating evolving and recursive visual patterns. Depth information controls the feedback strength and effect parameters, leading to organic, psychedelic results.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthFXLoop",
    "version": "3.0.0",
    "description": "Recursive depth effect feedback loop",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "feedback",
    "tags": ["depth", "feedback", "loop", "recursive"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `loop_iterations: int` (default: 3, min: 1, max: 10) - Number of feedback passes
- `feedback_strength: float` (default: 0.5, min: 0.0, max: 1.0) - How much to mix previous output
- `depth_feedback_scale: float` (default: 1.0, min: 0.0, max: 2.0) - Depth's influence on feedback
- `effect_chain: list[str]` (default: ["blur", "color_grade"]) - Effects to apply each loop
- `effect_params: dict` (default: {}) - Parameters for each effect in chain
- `mix_mode: str` (default: "additive", options: ["additive", "alpha", "screen", "multiply"]) - How to blend feedback
- `initial_input_mix: float` (default: 1.0, min: 0.0, max: 1.0) - Original video contribution
- `clamp_values: bool` (default: True) - Clamp output to valid range after each iteration

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `previous_frame: Frame` (optional) - Previous output for feedback (if not using internal buffer)

### Outputs
- `video: Frame` (same format as input) - Processed video frame

## What It Does NOT Do
- Does NOT support infinite loops (hard limit on iterations)
- Does NOT perform automatic convergence detection
- Does NOT include effect-specific optimizations for feedback
- Does NOT handle HDR metadata preservation through loops
- Does NOT support dynamic effect chain changes mid-loop
- Does NOT include loop visualization or debugging tools

## Test Plan
1. Unit tests for feedback buffer management
2. Verify loop iterations produce expected results
3. Test mix_mode variations
4. Performance: ≥ 60 FPS at 1080p with loop_iterations=3
5. Memory: < 200MB additional RAM (buffers)
6. Visual: verify feedback creates smooth, evolving patterns

## Implementation Notes
- Maintain a buffer for feedback (previous output)
- For iteration i from 0 to loop_iterations-1:
  - If i == 0: input = original_video * initial_input_mix + feedback * feedback_strength
  - Else: input = previous_output
  - Apply effect_chain to input using effect_params
  - Modulate effect parameters with depth if needed
  - Store output as feedback for next iteration
  - Mix with accumulated result using mix_mode
- Use depth to modulate feedback_strength per-pixel: effective_strength = feedback_strength * (depth * depth_feedback_scale)
- If clamp_values: clamp each iteration's output to prevent overflow
- Optimize by reusing buffers and minimizing copies
- Follow SAFETY_RAILS: cap iterations, handle edge cases

## Deliverables
- `src/vjlive3/effects/depth_fx_loop.py`
- `tests/effects/test_depth_fx_loop.py`
- `docs/plugins/depth_fx_loop.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Feedback loop works correctly
- [x] Depth modulates feedback as expected
- [x] 60 FPS at 1080p with 3 iterations
- [x] Test coverage ≥ 80%
- [x] No safety rail violations