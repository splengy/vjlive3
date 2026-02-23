# P3-EXT051 Depth Fog Effect

## What This Module Does

Depth Fog Effect adds atmospheric fog based on depth information, creating realistic depth-based atmospheric effects. Distant objects are obscured by fog while nearby objects remain clear, simulating natural atmospheric conditions. The fog density, color, and falloff are all depth-controlled, creating immersive environmental effects.

## Public Interface

```python
METADATA = {
    "name": "Depth Fog Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Adds atmospheric fog based on depth information",
    "category": "Depth Effects",
    "tags": ["depth", "fog", "atmospheric", "environment"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "fog_color": {
            "type": "color",
            "default": "#808080",
            "description": "Color of the fog"
        },
        "fog_density": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Overall density of the fog"
        },
        "fog_start": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Depth at which fog begins (0-1)"
        },
        "fog_end": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 1.0,
            "description": "Depth at which fog is fully opaque"
        },
        "falloff_curve": {
            "type": "enum",
            "options": ["linear", "exponential", "exponential_squared", "custom"],
            "default": "exponential",
            "description": "Curve for fog falloff"
        },
        "falloff_exponent": {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "default": 1.0,
            "description": "Exponent for exponential falloff curves"
        },
        "depth_scale": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 1.0,
            "description": "Scale factor for depth values"
        },
        "noise_enable": {
            "type": "boolean",
            "default": false,
            "description": "Enable noise variation in fog"
        },
        "noise_scale": {
            "type": "float",
            "min": 0.001,
            "max": 0.1,
            "default": 0.01,
            "description": "Scale of noise pattern"
        },
        "noise_speed": {
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "default": 1.0,
            "description": "Animation speed for noise"
        },
        "noise_strength": {
            "type": "float",
            "min": 0.0,
            "max": 0.5,
            "default": 0.1,
            "description": "Strength of noise variation"
        },
        "light_angle": {
            "type": "float",
            "min": 0.0,
            "max": 360.0,
            "default": 0.0,
            "description": "Angle for directional light effect"
        },
        "light_intensity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Intensity of directional light"
        },
        "light_color": {
            "type": "color",
            "default": "#ffffff",
            "description": "Color of directional light"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform volumetric fog with light scattering (surface fog only)
- Does not handle multiple fog layers (single fog layer only)
- Does not support animated fog parameters (static parameters only)

## Test Plan

1. **Fog Density Tests:**
   - Test with zero fog (clear scene)
   - Test with maximum fog (fully obscured)
   - Test with different fog densities

2. **Fog Start/End Tests:**
   - Test with fog starting at near distance
   - Test with fog starting at far distance
   - Test with narrow fog band (start ≈ end)
   - Test with wide fog band (start << end)

3. **Falloff Curve Tests:**
   - Test linear falloff (straight transition)
   - Test exponential falloff (smooth transition)
   - Test exponential squared falloff (very smooth)
   - Test custom falloff (user-defined)

4. **Noise Tests:**
   - Test with noise disabled (smooth fog)
   - Test with noise enabled (varied fog)
   - Test different noise scales
   - Test different noise speeds
   - Test different noise strengths

5. **Lighting Tests:**
   - Test with no directional light
   - Test with different light angles
   - Test with different light intensities
   - Test with different light colors

6. **Performance Tests:**
   - Measure FPS with different fog densities
   - Test with various resolutions
   - Verify GPU memory usage

7. **Quality Tests:**
   - Check for visual artifacts
   - Verify smooth fog transitions
   - Test with moving objects
   - Test with static scenes

## Implementation Notes

- Use GPU shader for real-time fog calculation
- Implement efficient depth-based fog blending
- Support real-time parameter adjustment
- Provide depth visualization for debugging
- Include noise generation for varied fog

## Deliverables

- `src/vjlive3/plugins/depth_fog.py` - Main plugin implementation
- `tests/plugins/test_depth_fog.py` - Comprehensive test suite
- `docs/plugins/depth_fog.md` - User documentation
- `shaders/depth_fog.glsl` - GPU shader for fog rendering

## Success Criteria

- ✅ Realistic depth-based atmospheric fog with configurable parameters
- ✅ Multiple falloff curves and noise options
- ✅ Directional lighting support for fog
- ✅ Real-time performance with minimal FPS impact
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails