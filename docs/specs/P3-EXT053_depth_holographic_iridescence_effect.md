# P3-EXT053 Depth Holographic Iridescence Effect

## What This Module Does

Depth Holographic Iridescence Effect creates shimmering, rainbow-like holographic effects that respond to depth information. The effect produces iridescent color shifts that vary based on depth, creating a sense of ethereal, otherworldly visuals where different depth planes exhibit different holographic properties. This effect simulates light interference patterns with depth-based modulation.

## Public Interface

```python
METADATA = {
    "name": "Depth Holographic Iridescence Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Creates depth-based holographic iridescence effects",
    "category": "Depth Effects",
    "tags": ["depth", "holographic", "iridescence", "rainbow", "interference"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "iridescence_intensity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Overall intensity of iridescence effect"
        },
        "iridescence_scale": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 1.0,
            "description": "Scale of iridescence pattern"
        },
        "color_shift_speed": {
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "default": 1.0,
            "description": "Speed of color shifting animation"
        },
        "depth_response": {
            "type": "enum",
            "options": ["linear", "exponential", "logarithmic", "squared", "cubic"],
            "default": "linear",
            "description": "How depth affects iridescence intensity"
        },
        "depth_exponent": {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "default": 1.0,
            "description": "Exponent for depth response curve"
        },
        "hologram_strength": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Strength of holographic shimmer"
        },
        "hologram_speed": {
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "default": 2.0,
            "description": "Speed of holographic shimmer"
        },
        "interference_scale": {
            "type": "float",
            "min": 0.001,
            "max": 0.1,
            "default": 0.01,
            "description": "Scale of interference pattern"
        },
        "interference_strength": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Strength of interference pattern"
        },
        "fresnel_effect": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Strength of Fresnel edge effect"
        },
        "fresnel_power": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 2.0,
            "description": "Power of Fresnel falloff"
        },
        "scanline_enable": {
            "type": "boolean",
            "default": false,
            "description": "Enable holographic scanlines"
        },
        "scanline_density": {
            "type": "float",
            "min": 10.0,
            "max": 500.0,
            "default": 100.0,
            "description": "Density of scanlines"
        },
        "scanline_strength": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Strength of scanline effect"
        },
        "glitch_enable": {
            "type": "boolean",
            "default": false,
            "description": "Enable holographic glitches"
        },
        "glitch_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.1,
            "description": "Amount of glitch effect"
        },
        "glitch_speed": {
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "default": 1.0,
            "description": "Speed of glitch animation"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform full volumetric holography (surface effect only)
- Does not support 3D holographic reconstruction
- Does not handle multiple holographic layers (single layer only)

## Test Plan

1. **Iridescence Intensity Tests:**
   - Test with zero iridescence (no effect)
   - Test with maximum iridescence (full rainbow)
   - Test with different iridescence intensities

2. **Scale Tests:**
   - Test with small scale (fine patterns)
   - Test with large scale (broad patterns)
   - Test with different scales

3. **Color Shift Tests:**
   - Test with no color shifting
   - Test with fast color shifting
   - Test with maximum color shifting

4. **Depth Response Tests:**
   - Test linear depth response
   - Test exponential depth response
   - Test logarithmic depth response
   - Test different exponent values

5. **Hologram Tests:**
   - Test with no hologram effect
   - Test with different hologram strengths
   - Test with different hologram speeds

6. **Interference Tests:**
   - Test with no interference
   - Test with different interference scales
   - Test with different interference strengths

7. **Fresnel Tests:**
   - Test with no Fresnel effect
   - Test with different Fresnel strengths
   - Test with different Fresnel powers

8. **Scanline Tests:**
   - Test with scanlines disabled
   - Test with different scanline densities
   - Test with different scanline strengths

9. **Glitch Tests:**
   - Test with glitches disabled
   - Test with different glitch amounts
   - Test with different glitch speeds

10. **Performance Tests:**
    - Measure FPS with different effect intensities
    - Test with various resolutions
    - Verify GPU memory usage

11. **Quality Tests:**
    - Check for visual artifacts
    - Verify smooth color transitions
    - Test with moving objects
    - Test with static scenes

## Implementation Notes

- Use GPU shader for real-time holographic calculation
- Implement efficient depth-based iridescence modulation
- Support real-time parameter adjustment
- Provide holographic preview mode
- Include depth visualization for debugging

## Deliverables

- `src/vjlive3/plugins/depth_holographic_iridescence.py` - Main plugin implementation
- `tests/plugins/test_depth_holographic_iridescence.py` - Comprehensive test suite
- `docs/plugins/depth_holographic_iridescence.md` - User documentation
- `shaders/depth_holographic_iridescence.glsl` - GPU shader for holographic effect

## Success Criteria

- ✅ Depth-based holographic iridescence with configurable parameters
- ✅ Multiple iridescence patterns and color shifting options
- ✅ Real-time performance with minimal FPS impact
- ✅ Configurable holographic shimmer and interference effects
- ✅ Optional scanlines and glitch effects
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails