# P3-EXT067 Displacement Map Effect

## What This Module Does

Displacement Map Effect uses a displacement map (which can be generated from depth or other sources) to geometrically distort the video image. Pixels are displaced based on the values in the displacement map, creating warping, refraction, and other geometric distortions. This effect is a general-purpose displacement tool that can use depth as the displacement source or other inputs.

## Public Interface

```python
METADATA = {
    "name": "Displacement Map Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Applies geometric displacement using a displacement map",
    "category": "Depth Effects",
    "tags": ["displacement", "map", "warp", "geometry"],
    "inputs": ["video", "displacement_map"],
    "outputs": ["video"],
    "parameters": {
        "displacement_source": {
            "type": "enum",
            "options": ["depth", "external", "generated"],
            "default": "depth",
            "description": "Source of displacement map"
        },
        "displacement_scale": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Overall scale of displacement"
        },
        "displacement_direction": {
            "type": "enum",
            "options": ["horizontal", "vertical", "both", "radial", "angular"],
            "default": "both",
            "description": "Direction of displacement"
        },
        "center_x": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "X coordinate for radial/angular displacement"
        },
        "center_y": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Y coordinate for radial/angular displacement"
        },
        "map_scale": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 1.0,
            "description": "Scale of displacement map values"
        },
        "map_offset": {
            "type": "float",
            "min": -1.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Offset added to displacement map values"
        },
        "interpolation": {
            "type": "enum",
            "options": ["nearest", "bilinear", "bicubic"],
            "default": "bilinear",
            "description": "Interpolation method for displacement"
        },
        "edge_behavior": {
            "type": "enum",
            "options": ["clamp", "wrap", "reflect", "background"],
            "default": "clamp",
            "description": "How to handle displaced pixels at edges"
        },
        "background_color": {
            "type": "color",
            "default": "#000000",
            "description": "Background color for edge holes (if edge_behavior=background)"
        },
        "temporal_smoothing": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Smoothing of displacement over time"
        },
        "generate_pattern": {
            "type": "enum",
            "options": ["none", "waves", "ripples", "noise", "gradient"],
            "default": "none",
            "description": "Pattern to generate if displacement_source=generated"
        },
        "generate_scale": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 1.0,
            "description": "Scale of generated pattern"
        },
        "generate_speed": {
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "default": 1.0,
            "description": "Animation speed for generated pattern"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video when displacement_source=depth (requires depth input)
- Does not perform complex 3D reconstruction (2D displacement only)
- Does not support multiple displacement maps (single map only)
- Does not handle animated displacement maps (static or generated only)

## Test Plan

1. **Displacement Source Tests:**
   - Test with depth as source
   - Test with external map as source
   - Test with generated pattern as source

2. **Displacement Scale Tests:**
   - Test with zero scale (no displacement)
   - Test with maximum scale (extreme displacement)
   - Test with different scales

3. **Direction Tests:**
   - Test horizontal displacement
   - Test vertical displacement
   - Test both directions
   - Test radial displacement
   - Test angular displacement

4. **Center Tests:**
   - Test with different center positions for radial/angular
   - Verify radial displacement radiates correctly

5. **Map Scale/Offset Tests:**
   - Test with different map scales
   - Test with different map offsets
   - Test with combined scale and offset

6. **Interpolation Tests:**
   - Test nearest neighbor (blocky)
   - Test bilinear (smooth)
   - Test bicubic (smoothest)

7. **Edge Behavior Tests:**
   - Test clamp (pixels clamped to edge)
   - Test wrap (pixels wrap around)
   - Test reflect (pixels reflected)
   - Test background (fill with background color)

8. **Generated Pattern Tests:**
   - Test with different pattern types
   - Test with different pattern scales
   - Test with different pattern speeds

9. **Performance Tests:**
   - Measure FPS with different displacement scales
   - Test with various resolutions
   - Verify GPU memory usage

10. **Quality Tests:**
    - Check for visual artifacts
    - Verify smooth displacement
    - Test with moving objects
    - Test with static scenes

## Implementation Notes

- Use GPU shader for real-time displacement
- Implement efficient map sampling with interpolation
- Support real-time parameter adjustment
- Provide displacement preview mode
- Include map visualization for debugging

## Deliverables

- `src/vjlive3/plugins/displacement_map.py` - Main plugin implementation
- `tests/plugins/test_displacement_map.py` - Comprehensive test suite
- `docs/plugins/displacement_map.md` - User documentation
- `shaders/displacement_map.glsl` - GPU shader for displacement

## Success Criteria

- ✅ Flexible displacement mapping with multiple sources
- ✅ Multiple displacement directions and interpolation methods
- ✅ Configurable edge handling and background fill
- ✅ Generated pattern support for creative effects
- ✅ Real-time performance with minimal FPS impact
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails