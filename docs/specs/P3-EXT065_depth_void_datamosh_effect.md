# P3-EXT065 Depth Void Datamosh Effect

## What This Module Does

Depth Void Datamosh Effect creates dark, abyssal datamosh effects that simulate voids, emptiness, and null-space corruption. The effect uses depth information to create areas of visual void where the video is consumed by darkness and datamosh corruption, with deeper regions experiencing more intense void effects. This creates a haunting, existential visual style that feels like the video is being erased by cosmic voids.

## Public Interface

```python
METADATA = {
    "name": "Depth Void Datamosh Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Creates abyssal void effects with depth-based corruption",
    "category": "Depth Effects",
    "tags": ["depth", "void", "datamosh", "dark", "abyssal"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "void_intensity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Overall intensity of void effect"
        },
        "void_color": {
            "type": "color",
            "default": "#000000",
            "description": "Base color of void regions"
        },
        "void_scale": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 1.0,
            "description": "Scale of void pattern"
        },
        "depth_response": {
            "type": "enum",
            "options": ["linear", "exponential", "logarithmic", "squared", "cubic"],
            "default": "linear",
            "description": "How depth affects void intensity"
        },
        "depth_exponent": {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "default": 1.0,
            "description": "Exponent for depth response curve"
        },
        "void_threshold": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Depth threshold for void appearance"
        },
        "void_softness": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Softness of void edges"
        },
        "corruption_strength": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.4,
            "description": "Strength of datamosh corruption in voids"
        },
        "corruption_pattern": {
            "type": "enum",
            "options": ["static", "noise", "wave", "fractal", "void_walk"],
            "default": "noise",
            "description": "Pattern of corruption within voids"
        },
        "corruption_speed": {
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "default": 1.0,
            "description": "Speed of corruption animation"
        },
        "edge_glow": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Glow at void edges"
        },
        "edge_color": {
            "type": "color",
            "default": "#ff00ff",
            "description": "Color of void edge glow"
        },
        "void_pulse": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Pulsing intensity of voids"
        },
        "pulse_speed": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 1.0,
            "description": "Speed of void pulsing"
        },
        "void_feedback": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Amount of feedback in void system"
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
            "description": "Random seed for void patterns"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform audio-reactive void pulsing
- Does not support external void sources
- Does not handle infinite recursion (limited by feedback)

## Test Plan

1. **Void Intensity Tests:**
   - Test with zero void intensity (no effect)
   - Test with maximum void intensity (full void)
   - Test with different void intensities

2. **Void Color Tests:**
   - Test with black void (default)
   - Test with colored voids
   - Test with gradient void colors

3. **Depth Response Tests:**
   - Test linear depth response
   - Test exponential depth response
   - Test logarithmic depth response
   - Test different exponent values

4. **Void Threshold Tests:**
   - Test with low threshold (voids appear everywhere)
   - Test with high threshold (voids only in deep regions)
   - Test with different threshold values

5. **Void Softness Tests:**
   - Test with sharp void edges (0.0)
   - Test with soft void edges (1.0)
   - Test with different softness values

6. **Corruption Tests:**
   - Test with no corruption
   - Test with different corruption strengths
   - Test with different corruption patterns
   - Test with different corruption speeds

7. **Edge Glow Tests:**
   - Test with no edge glow
   - Test with different edge glow intensities
   - Test with different edge colors

8. **Pulse Tests:**
   - Test with no pulsing
   - Test with different pulse intensities
   - Test with different pulse speeds

9. **Feedback Tests:**
   - Test with no feedback
   - Test with different feedback amounts
   - Test with different feedback modes

10. **Performance Tests:**
    - Measure FPS with different void intensities
    - Test with various resolutions
    - Verify GPU memory usage

11. **Quality Tests:**
    - Check for visual artifacts
    - Verify smooth void transitions
    - Test with moving objects
    - Test with static scenes

## Implementation Notes

- Use GPU shader for real-time void calculation
- Implement efficient depth-based void modulation
- Support real-time parameter adjustment
- Provide void preview mode
- Include depth visualization for debugging

## Deliverables

- `src/vjlive3/plugins/depth_void_datamosh.py` - Main plugin implementation
- `tests/plugins/test_depth_void_datamosh.py` - Comprehensive test suite
- `docs/plugins/depth_void_datamosh.md` - User documentation
- `shaders/depth_void_datamosh.glsl` - GPU shader for void processing

## Success Criteria

- ✅ Abyssal void effects with depth-based corruption
- ✅ Configurable void color, scale, and threshold
- ✅ Multiple corruption patterns and animation options
- ✅ Edge glow and pulsing effects
- ✅ Real-time performance with minimal FPS impact
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails