# P3-EXT069 Dolly Zoom Datamosh Effect

## What This Module Does

Dolly Zoom Datamosh Effect combines the classic dolly zoom (also known as "Vertigo effect") with datamosh corruption, creating dramatic perspective distortions that vary with depth. The effect simulates the camera moving while zooming in the opposite direction, creating a surreal sense of depth and disorientation, enhanced with depth-modulated datamosh glitches.

## Public Interface

```python
METADATA = {
    "name": "Dolly Zoom Datamosh Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Creates dolly zoom distortion with depth-modulated datamosh",
    "category": "Depth Effects",
    "tags": ["depth", "dolly_zoom", "datamosh", "perspective", "distortion"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "zoom_factor": {
            "type": "float",
            "min": 0.5,
            "max": 3.0,
            "default": 1.5,
            "description": "Zoom factor (1.0 = no zoom)"
        },
        "dolly_speed": {
            "type": "float",
            "min": -2.0,
            "max": 2.0,
            "default": 0.5,
            "description": "Speed of dolly movement (negative = backward)"
        },
        "dolly_direction": {
            "type": "enum",
            "options": ["forward", "backward", "auto"],
            "default": "auto",
            "description": "Direction of dolly movement"
        },
        "center_x": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "X coordinate of zoom center"
        },
        "center_y": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Y coordinate of zoom center"
        },
        "depth_response": {
            "type": "enum",
            "options": ["linear", "exponential", "logarithmic", "squared", "cubic"],
            "default": "linear",
            "description": "How depth affects dolly zoom intensity"
        },
        "depth_exponent": {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "default": 1.0,
            "description": "Exponent for depth response curve"
        },
        "datamosh_strength": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Intensity of datamosh effect"
        },
        "glitch_pattern": {
            "type": "enum",
            "options": ["random", "scanline", "block", "pixel_sort", "compression"],
            "default": "random",
            "description": "Type of glitch pattern"
        },
        "glitch_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Amount of glitch corruption"
        },
        "color_shift": {
            "type": "float",
            "min": -180.0,
            "max": 180.0,
            "default": 0.0,
            "description": "Hue shift for dolly zoom regions"
        },
        "blend_mode": {
            "type": "enum",
            "options": ["normal", "additive", "screen", "multiply", "difference"],
            "default": "normal",
            "description": "Blending mode for dolly zoom"
        },
        "smooth_transition": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Smoothness of transitions"
        },
        "feedback_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.1,
            "description": "Amount of feedback in dolly system"
        },
        "feedback_mode": {
            "type": "enum",
            "options": ["additive", "multiply", "screen", "difference"],
            "default": "additive",
            "description": "Blending mode for feedback"
        },
        "seed": {
            "type": "integer",
            "min": 0,
            "max": 1000000,
            "default": 42,
            "description": "Random seed for dolly patterns"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform audio-reactive dolly zoom
- Does not support external camera control
- Does not handle infinite recursion (limited by feedback)

## Test Plan

1. **Zoom Factor Tests:**
   - Test with zoom = 1.0 (no zoom)
   - Test with zoom < 1.0 (wide angle)
   - Test with zoom > 1.0 (telephoto)
   - Test with extreme zoom values

2. **Dolly Speed Tests:**
   - Test with zero dolly speed (static zoom)
   - Test with positive dolly speed (forward)
   - Test with negative dolly speed (backward)
   - Test with maximum dolly speed

3. **Dolly Direction Tests:**
   - Test forward direction
   - Test backward direction
   - Test auto direction

4. **Center Tests:**
   - Test with different center positions
   - Verify zoom radiates from correct center

5. **Depth Response Tests:**
   - Test linear depth response
   - Test exponential depth response
   - Test logarithmic depth response
   - Test different exponent values

6. **Datamosh Tests:**
   - Test with no datamosh
   - Test with different datamosh strengths
   - Test with different glitch patterns
   - Test with different glitch amounts

7. **Color and Blend Tests:**
   - Test with different color shifts
   - Test with different blend modes
   - Test with smooth transitions

8. **Feedback Tests:**
   - Test with no feedback
   - Test with different feedback amounts
   - Test with different feedback modes

9. **Performance Tests:**
   - Measure FPS with different zoom factors
   - Test with various resolutions
   - Verify GPU memory usage

10. **Quality Tests:**
    - Check for visual artifacts
    - Verify smooth dolly zoom transitions
    - Test with moving objects
    - Test with static scenes

## Implementation Notes

- Use GPU shader for real-time dolly zoom calculation
- Implement efficient depth-based distortion modulation
- Support real-time parameter adjustment
- Provide dolly zoom preview mode
- Include depth visualization for debugging

## Deliverables

- `src/vjlive3/plugins/dolly_zoom_datamosh.py` - Main plugin implementation
- `tests/plugins/test_dolly_zoom_datamosh.py` - Comprehensive test suite
- `docs/plugins/dolly_zoom_datamosh.md` - User documentation
- `shaders/dolly_zoom_datamosh.glsl` - GPU shader for dolly zoom processing

## Success Criteria

- ✅ Dolly zoom distortion with depth-based modulation
- ✅ Configurable zoom factor and dolly movement
- ✅ Real-time performance with minimal FPS impact
- ✅ Datamosh integration with various patterns
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails