# P3-EXT059 Depth Raver Datamosh Effect

## What This Module Does

Depth Raver Datamosh Effect creates high-energy, beat-synchronized datamosh effects that respond to depth information, producing rave-style visual corruption with depth-aware characteristics. The effect combines traditional datamosh with rhythmic, pulsating patterns that vary based on depth, creating an intense, club-ready glitch aesthetic that feels both chaotic and controlled.

## Public Interface

```python
METADATA = {
    "name": "Depth Raver Datamosh Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Creates beat-synchronized rave-style datamosh with depth modulation",
    "category": "Depth Effects",
    "tags": ["depth", "datamosh", "rave", "beat", "rhythmic"],
    "inputs": ["video", "depth", "audio_beat"],
    "outputs": ["video"],
    "parameters": {
        "rave_intensity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.7,
            "description": "Overall intensity of rave effect"
        },
        "beat_sync": {
            "type": "boolean",
            "default": true,
            "description": "Sync datamosh to audio beats"
        },
        "beat_threshold": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Threshold for beat detection"
        },
        "beat_response": {
            "type": "enum",
            "options": ["immediate", "attack", "release", "pulse"],
            "default": "pulse",
            "description": "How beats trigger datamosh"
        },
        "attack_time": {
            "type": "float",
            "min": 0.001,
            "max": 1.0,
            "default": 0.01,
            "description": "Attack time for beat response"
        },
        "release_time": {
            "type": "float",
            "min": 0.01,
            "max": 5.0,
            "default": 0.2,
            "description": "Release time for beat response"
        },
        "pulse_speed": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 4.0,
            "description": "Speed of pulse modulation"
        },
        "depth_response": {
            "type": "enum",
            "options": ["linear", "exponential", "logarithmic", "squared", "cubic"],
            "default": "linear",
            "description": "How depth affects rave intensity"
        },
        "depth_exponent": {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "default": 1.0,
            "description": "Exponent for depth response curve"
        },
        "glitch_pattern": {
            "type": "enum",
            "options": ["random", "scanline", "block", "pixel_sort", "compression", "all"],
            "default": "all",
            "description": "Type of glitch pattern"
        },
        "glitch_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Amount of glitch corruption"
        },
        "color_shift": {
            "type": "float",
            "min": -180.0,
            "max": 180.0,
            "default": 0.0,
            "description": "Hue shift for rave effect"
        },
        "color_cycle_speed": {
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "default": 2.0,
            "description": "Speed of color cycling"
        },
        "feedback_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Amount of feedback in rave system"
        },
        "feedback_mode": {
            "type": "enum",
            "options": ["additive", "multiply", "screen", "difference", "xor"],
            "default": "additive",
            "description": "Blending mode for feedback"
        },
        "strobe_enable": {
            "type": "boolean",
            "default": false,
            "description": "Enable stroboscopic effect"
        },
        "strobe_frequency": {
            "type": "float",
            "min": 1.0,
            "max": 30.0,
            "default": 10.0,
            "description": "Frequency of strobe effect"
        },
        "strobe_intensity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Intensity of strobe effect"
        },
        "seed": {
            "type": "integer",
            "min": 0,
            "max": 1000000,
            "default": 42,
            "description": "Random seed for rave patterns"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform audio analysis (requires audio_beat input)
- Does not support external beat sources (internal sync only)
- Does not handle infinite recursion (limited by feedback)

## Test Plan

1. **Rave Intensity Tests:**
   - Test with zero rave intensity (no effect)
   - Test with maximum rave intensity (full effect)
   - Test with different rave intensities

2. **Beat Sync Tests:**
   - Test with beat sync enabled
   - Test with beat sync disabled
   - Test with different beat thresholds
   - Test with different beat responses

3. **Response Time Tests:**
   - Test with fast attack (immediate response)
   - Test with slow attack (gradual response)
   - Test with fast release (quick decay)
   - Test with slow release (sustained response)
   - Test with pulse mode

4. **Depth Response Tests:**
   - Test linear depth response
   - Test exponential depth response
   - Test logarithmic depth response
   - Test different exponent values

5. **Glitch Pattern Tests:**
   - Test different glitch patterns
   - Test with "all" pattern (mixed)
   - Test with different glitch amounts

6. **Color Tests:**
   - Test with no color shift
   - Test with different color shifts
   - Test with different color cycle speeds

7. **Feedback Tests:**
   - Test with no feedback
   - Test with different feedback amounts
   - Test with different feedback modes

8. **Strobe Tests:**
   - Test with strobe disabled
   - Test with different strobe frequencies
   - Test with different strobe intensities

9. **Performance Tests:**
   - Measure FPS with different rave intensities
   - Test with various resolutions
   - Verify GPU memory usage

10. **Quality Tests:**
    - Check for visual artifacts
    - Verify smooth rave transitions
    - Test with moving objects
    - Test with static scenes

## Implementation Notes

- Use GPU shader for real-time rave calculation
- Implement efficient beat-synchronized datamosh modulation
- Support real-time parameter adjustment
- Provide rave preview mode
- Include depth visualization for debugging

## Deliverables

- `src/vjlive3/plugins/depth_raver_datamosh.py` - Main plugin implementation
- `tests/plugins/test_depth_raver_datamosh.py` - Comprehensive test suite
- `docs/plugins/depth_raver_datamosh.md` - User documentation
- `shaders/depth_raver_datamosh.glsl` - GPU shader for rave processing

## Success Criteria

- ✅ Beat-synchronized rave-style datamosh with depth modulation
- ✅ Multiple beat response modes and timing controls
- ✅ Real-time performance with minimal FPS impact
- ✅ Configurable glitch patterns and color effects
- ✅ Optional strobe effect
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails