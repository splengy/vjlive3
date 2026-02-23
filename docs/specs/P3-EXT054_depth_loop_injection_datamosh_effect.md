# P3-EXT054 Depth Loop Injection Datamosh Effect

## What This Module Does

Depth Loop Injection Datamosh Effect creates datamosh effects where video frames are looped and injected back into the stream with depth-based modulation. This creates complex temporal distortions where different depth regions experience different loop behaviors, producing unique glitch art with depth-aware temporal manipulation.

## Public Interface

```python
METADATA = {
    "name": "Depth Loop Injection Datamosh Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Creates depth-modulated loop injection datamosh effects",
    "category": "Depth Effects",
    "tags": ["depth", "datamosh", "loop", "temporal", "injection"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "loop_count": {
            "type": "integer",
            "min": 1,
            "max": 10,
            "default": 3,
            "description": "Number of loop iterations"
        },
        "loop_length": {
            "type": "float",
            "min": 0.01,
            "max": 5.0,
            "default": 0.5,
            "description": "Length of each loop in seconds"
        },
        "loop_delay": {
            "type": "float",
            "min": 0.0,
            "max": 5.0,
            "default": 0.0,
            "description": "Delay before loop injection"
        },
        "loop_injection": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Amount of loop injection"
        },
        "depth_response": {
            "type": "enum",
            "options": ["linear", "exponential", "logarithmic", "squared", "cubic"],
            "default": "linear",
            "description": "How depth affects loop intensity"
        },
        "depth_exponent": {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "default": 1.0,
            "description": "Exponent for depth response curve"
        },
        "motion_sensitivity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Sensitivity to motion in loop injection"
        },
        "color_shift": {
            "type": "float",
            "min": -180.0,
            "max": 180.0,
            "default": 0.0,
            "description": "Hue shift for looped frames"
        },
        "contrast_adjust": {
            "type": "float",
            "min": -1.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Contrast adjustment for loops"
        },
        "brightness_adjust": {
            "type": "float",
            "min": -1.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Brightness adjustment for loops"
        },
        "glitch_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Amount of glitch corruption in loops"
        },
        "glitch_pattern": {
            "type": "enum",
            "options": ["random", "scanline", "block", "pixel_sort", "compression"],
            "default": "random",
            "description": "Type of glitch pattern"
        },
        "feedback_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Amount of feedback in loop system"
        },
        "feedback_mode": {
            "type": "enum",
            "options": ["additive", "multiply", "screen", "difference", "xor"],
            "default": "additive",
            "description": "Blending mode for feedback"
        },
        "seed": {
            "type": "integer",
            "min": 0,
            "max": 1000000,
            "default": 42,
            "description": "Random seed for loop patterns"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform audio-reactive loop timing
- Does not support external loop sources
- Does not handle infinite recursion (limited by loop_count)

## Test Plan

1. **Loop Count Tests:**
   - Test with single loop (no repetition)
   - Test with maximum 10 loops
   - Test with different loop counts

2. **Loop Length Tests:**
   - Test with very short loops (0.01s)
   - Test with medium loops (0.5s)
   - Test with long loops (5.0s)
   - Test with different loop lengths

3. **Loop Delay Tests:**
   - Test with no delay (instant injection)
   - Test with various delay times
   - Test with maximum delay

4. **Loop Injection Tests:**
   - Test with zero injection (no effect)
   - Test with maximum injection (full loop)
   - Test with different injection amounts

5. **Depth Response Tests:**
   - Test linear depth response
   - Test exponential depth response
   - Test logarithmic depth response
   - Test different exponent values

6. **Glitch Pattern Tests:**
   - Test random pattern generation
   - Test scanline-based datamosh
   - Test block-based datamosh
   - Test pixel sort datamosh
   - Test compression-based datamosh

7. **Feedback Tests:**
   - Test with no feedback
   - Test with different feedback amounts
   - Test with different feedback modes

8. **Performance Tests:**
   - Measure FPS with different loop counts
   - Test with various resolutions
   - Verify memory usage with multiple loops

9. **Quality Tests:**
   - Check for visual artifacts
   - Verify smooth loop transitions
   - Test with moving objects
   - Test with static scenes

## Implementation Notes

- Use frame buffer ping-pong for loop accumulation
- Implement efficient depth-based loop modulation
- Support real-time parameter adjustment
- Provide loop preview mode
- Include depth visualization for debugging

## Deliverables

- `src/vjlive3/plugins/depth_loop_injection_datamosh.py` - Main plugin implementation
- `tests/plugins/test_depth_loop_injection_datamosh.py` - Comprehensive test suite
- `docs/plugins/depth_loop_injection_datamosh.md` - User documentation
- `shaders/depth_loop_injection_datamosh.glsl` - GPU shader for loop processing

## Success Criteria

- ✅ Depth-modulated loop injection with configurable parameters
- ✅ Multiple loop counts and lengths with smooth transitions
- ✅ Various glitch patterns and feedback options
- ✅ Real-time performance with minimal FPS impact
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails