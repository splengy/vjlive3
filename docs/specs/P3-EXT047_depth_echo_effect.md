# P3-EXT047 Depth Echo Effect

## What This Module Does

Depth Echo Effect creates trailing echo effects where objects leave visual trails that fade over time, with the echo intensity and behavior varying based on depth. Closer objects leave stronger, longer-lasting echoes while distant objects have fainter, shorter trails. This creates a sense of motion and depth with temporal persistence.

## Public Interface

```python
METADATA = {
    "name": "Depth Echo Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Creates depth-based echo trails with temporal persistence",
    "category": "Depth Effects",
    "tags": ["depth", "echo", "trail", "temporal"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "echo_count": {
            "type": "integer",
            "min": 1,
            "max": 10,
            "default": 3,
            "description": "Number of echo layers"
        },
        "echo_decay": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.7,
            "description": "Decay rate for echo intensity"
        },
        "depth_response": {
            "type": "enum",
            "options": ["linear", "exponential", "logarithmic", "squared", "cubic"],
            "default": "linear",
            "description": "How depth affects echo intensity"
        },
        "depth_exponent": {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "default": 1.0,
            "description": "Exponent for depth response curve"
        },
        "echo_speed": {
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "default": 1.0,
            "description": "Speed of echo movement"
        },
        "echo_direction": {
            "type": "enum",
            "options": ["forward", "backward", "both", "radial_out", "radial_in"],
            "default": "forward",
            "description": "Direction of echo movement"
        },
        "echo_color": {
            "type": "color",
            "default": "#ffffff",
            "description": "Base color for echo trails"
        },
        "color_fade": {
            "type": "boolean",
            "default": true,
            "description": "Fade echo color over time"
        },
        "motion_blur": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Motion blur amount for echoes"
        },
        "echo_blend": {
            "type": "enum",
            "options": ["additive", "screen", "multiply", "overlay"],
            "default": "additive",
            "description": "Blending mode for echo trails"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform motion detection (uses depth for motion cues)
- Does not support echo persistence across scene changes
- Does not handle audio-reactive echo timing

## Test Plan

1. **Echo Count Tests:**
   - Test with 1 echo layer (simple trail)
   - Test with maximum 10 echo layers
   - Test with different echo counts

2. **Decay Tests:**
   - Test with fast decay (short trails)
   - Test with slow decay (long trails)
   - Test with zero decay (permanent trails)
   - Test with maximum decay (instant fade)

3. **Depth Response Tests:**
   - Test linear depth response
   - Test exponential depth response
   - Test logarithmic depth response
   - Test different exponent values

4. **Direction Tests:**
   - Test forward echo movement
   - Test backward echo movement
   - Test both directions
   - Test radial echo patterns

5. **Color Tests:**
   - Test with different echo colors
   - Test color fading over time
   - Test with color cycling
   - Test with monochrome echoes

6. **Performance Tests:**
   - Measure FPS with different echo counts
   - Test with various resolutions
   - Verify memory usage with multiple echo layers

7. **Quality Tests:**
   - Check for visual artifacts
   - Verify smooth echo transitions
   - Test with moving objects
   - Test with static scenes

## Implementation Notes

- Use frame buffer ping-pong for echo accumulation
- Implement efficient depth-based echo intensity calculation
- Support real-time parameter adjustment
- Provide echo preview mode
- Include depth visualization for debugging

## Deliverables

- `src/vjlive3/plugins/depth_echo.py` - Main plugin implementation
- `tests/plugins/test_depth_echo.py` - Comprehensive test suite
- `docs/plugins/depth_echo.md` - User documentation
- `shaders/depth_echo.glsl` - GPU shader for echo processing

## Success Criteria

- ✅ Depth-based echo trails with configurable intensity
- ✅ Multiple echo layers with smooth decay
- ✅ Real-time performance with minimal FPS impact
- ✅ Various echo movement directions and patterns
- ✅ Configurable color and blending options
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails