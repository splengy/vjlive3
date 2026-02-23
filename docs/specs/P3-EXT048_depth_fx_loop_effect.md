# P3-EXT048 Depth FX Loop Effect

## What This Module Does

Depth FX Loop Effect creates feedback loops where the video output is fed back into the input with depth-based modulation, creating complex recursive visual patterns. The depth information controls how the feedback is processed, creating evolving, self-generating visual systems that respond to the depth structure of the scene.

## Public Interface

```python
METADATA = {
    "name": "Depth FX Loop Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Creates depth-modulated feedback loops for recursive visuals",
    "category": "Depth Effects",
    "tags": ["depth", "feedback", "loop", "recursive"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "feedback_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Amount of feedback in the loop"
        },
        "feedback_mode": {
            "type": "enum",
            "options": ["additive", "multiply", "screen", "difference", "xor"],
            "default": "additive",
            "description": "Blending mode for feedback"
        },
        "depth_response": {
            "type": "enum",
            "options": ["linear", "exponential", "logarithmic", "squared", "cubic"],
            "default": "linear",
            "description": "How depth affects feedback intensity"
        },
        "depth_exponent": {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "default": 1.0,
            "description": "Exponent for depth response curve"
        },
        "loop_delay": {
            "type": "float",
            "min": 0.0,
            "max": 5.0,
            "default": 0.0,
            "description": "Delay in seconds for feedback loop"
        },
        "loop_count": {
            "type": "integer",
            "min": 1,
            "max": 10,
            "default": 3,
            "description": "Number of feedback iterations"
        },
        "motion_sensitivity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Sensitivity to motion in feedback"
        },
        "color_shift": {
            "type": "float",
            "min": -180.0,
            "max": 180.0,
            "default": 0.0,
            "description": "Hue shift for feedback frames"
        },
        "contrast_adjust": {
            "type": "float",
            "min": -1.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Contrast adjustment for feedback"
        },
        "brightness_adjust": {
            "type": "float",
            "min": -1.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Brightness adjustment for feedback"
        },
        "feedback_filter": {
            "type": "enum",
            "options": ["none", "blur", "sharpen", "emboss", "edge_detect"],
            "default": "none",
            "description": "Filter applied to feedback frames"
        },
        "filter_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Intensity of feedback filter"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform audio-reactive feedback timing
- Does not support external feedback sources
- Does not handle infinite recursion (limited by loop_count)

## Test Plan

1. **Feedback Amount Tests:**
   - Test with zero feedback (pass-through)
   - Test with maximum feedback (full recursion)
   - Test with different feedback amounts

2. **Feedback Mode Tests:**
   - Test additive feedback (accumulation)
   - Test multiply feedback (intensity multiplication)
   - Test screen feedback (lighten blend)
   - Test difference feedback (pixel difference)
   - Test XOR feedback (bitwise operation)

3. **Depth Response Tests:**
   - Test linear depth response
   - Test exponential depth response
   - Test logarithmic depth response
   - Test different exponent values

4. **Loop Delay Tests:**
   - Test with zero delay (instant feedback)
   - Test with various delay times
   - Test with maximum delay

5. **Loop Count Tests:**
   - Test with single iteration (no feedback)
   - Test with multiple iterations
   - Test with maximum iterations

6. **Filter Tests:**
   - Test with no filter
   - Test with blur filter
   - Test with sharpen filter
   - Test with emboss filter
   - Test with edge detection filter

7. **Performance Tests:**
   - Measure FPS with different feedback amounts
   - Test with various resolutions
   - Verify memory usage with multiple iterations

8. **Quality Tests:**
   - Check for visual artifacts
   - Verify smooth feedback transitions
   - Test with moving objects
   - Test with static scenes

## Implementation Notes

- Use frame buffer ping-pong for feedback accumulation
- Implement efficient depth-based feedback modulation
- Support real-time parameter adjustment
- Provide feedback preview mode
- Include depth visualization for debugging

## Deliverables

- `src/vjlive3/plugins/depth_fx_loop.py` - Main plugin implementation
- `tests/plugins/test_depth_fx_loop.py` - Comprehensive test suite
- `docs/plugins/depth_fx_loop.md` - User documentation
- `shaders/depth_fx_loop.glsl` - GPU shader for feedback processing

## Success Criteria

- ✅ Depth-modulated feedback loops with configurable intensity
- ✅ Multiple feedback modes and blending options
- ✅ Real-time performance with minimal FPS impact
- ✅ Configurable delay and iteration count
- ✅ Various filter options for feedback processing
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails