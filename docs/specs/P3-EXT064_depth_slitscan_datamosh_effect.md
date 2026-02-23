# P3-EXT064 Depth Slitscan Datamosh Effect

## What This Module Does

Depth Slitscan Datamosh Effect creates slit-scan style distortions combined with datamosh effects, where depth information controls the slit scanning behavior and datamosh intensity. This produces unique temporal distortions where different depth regions are sampled at different times, creating surreal, time-warped visuals that combine the classic slit-scan aesthetic with modern datamosh corruption.

## Public Interface

```python
METADATA = {
    "name": "Depth Slitscan Datamosh Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Creates slit-scan distortions with depth-modulated datamosh",
    "category": "Depth Effects",
    "tags": ["depth", "slitscan", "datamosh", "temporal", "distortion"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "slit_direction": {
            "type": "enum",
            "options": ["horizontal", "vertical", "radial", "circular", "random"],
            "default": "horizontal",
            "description": "Direction of slit scanning"
        },
        "slit_count": {
            "type": "integer",
            "min": 1,
            "max": 100,
            "default": 10,
            "description": "Number of slits"
        },
        "slit_width": {
            "type": "float",
            "min": 0.001,
            "max": 1.0,
            "default": 0.01,
            "description": "Width of each slit (0-1)"
        },
        "slit_spacing": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.05,
            "description": "Spacing between slits"
        },
        "time_offset": {
            "type": "float",
            "min": -5.0,
            "max": 5.0,
            "default": 0.5,
            "description": "Time offset for slit sampling (seconds)"
        },
        "time_offset_variation": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Variation in time offset across slits"
        },
        "depth_response": {
            "type": "enum",
            "options": ["linear", "exponential", "logarithmic", "squared", "cubic"],
            "default": "linear",
            "description": "How depth affects slit behavior"
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
            "description": "Hue shift for slit regions"
        },
        "blend_mode": {
            "type": "enum",
            "options": ["normal", "additive", "screen", "multiply", "difference"],
            "default": "normal",
            "description": "Blending mode for slit regions"
        },
        "smooth_transition": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Smoothness of transitions between slits"
        },
        "feedback_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.1,
            "description": "Amount of feedback in slit system"
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
            "description": "Random seed for slit patterns"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform audio-reactive slit scanning
- Does not support external time sources
- Does not handle infinite recursion (limited by feedback)

## Test Plan

1. **Slit Direction Tests:**
   - Test horizontal slits
   - Test vertical slits
   - Test radial slits
   - Test circular slits
   - Test random slit directions

2. **Slit Count Tests:**
   - Test with single slit (minimal effect)
   - Test with maximum 100 slits
   - Test with different slit counts

3. **Slit Width Tests:**
   - Test with very narrow slits (0.001)
   - Test with wide slits (1.0)
   - Test with different slit widths

4. **Slit Spacing Tests:**
   - Test with no spacing (touching slits)
   - Test with various spacing values
   - Test with maximum spacing

5. **Time Offset Tests:**
   - Test with negative time offset (past frames)
   - Test with zero time offset (current frame)
   - Test with positive time offset (future frames)
   - Test with maximum time offset

6. **Depth Response Tests:**
   - Test linear depth response
   - Test exponential depth response
   - Test logarithmic depth response
   - Test different exponent values

7. **Datamosh Tests:**
   - Test with no datamosh
   - Test with different datamosh strengths
   - Test with different glitch patterns
   - Test with different glitch amounts

8. **Color and Blend Tests:**
   - Test with different color shifts
   - Test with different blend modes
   - Test with smooth transitions

9. **Feedback Tests:**
   - Test with no feedback
   - Test with different feedback amounts
   - Test with different feedback modes

10. **Performance Tests:**
    - Measure FPS with different slit counts
    - Test with various resolutions
    - Verify GPU memory usage

11. **Quality Tests:**
    - Check for visual artifacts
    - Verify smooth slit transitions
    - Test with moving objects
    - Test with static scenes

## Implementation Notes

- Use GPU shader for real-time slit-scan processing
- Implement efficient depth-based slit modulation
- Support real-time parameter adjustment
- Provide slit preview mode
- Include depth visualization for debugging

## Deliverables

- `src/vjlive3/plugins/depth_slitscan_datamosh.py` - Main plugin implementation
- `tests/plugins/test_depth_slitscan_datamosh.py` - Comprehensive test suite
- `docs/plugins/depth_slitscan_datamosh.md` - User documentation
- `shaders/depth_slitscan_datamosh.glsl` - GPU shader for slit-scan processing

## Success Criteria

- ✅ Slit-scan distortion with depth-based modulation
- ✅ Multiple slit directions and configurations
- ✅ Configurable time offsets and variations
- ✅ Datamosh integration with various patterns
- ✅ Real-time performance with minimal FPS impact
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails