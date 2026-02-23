# P3-EXT050: Depth Field Effect

## What This Module Does
Simulates camera depth-of-field by blurring regions based on depth values. Creates realistic focus effects where objects at specific depth ranges are sharp while others are blurred. Supports smooth transitions between focused and blurred regions and multiple blur types.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthFieldEffect",
    "version": "3.0.0",
    "description": "Realistic depth-of-field simulation",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "blur",
    "tags": ["depth", "dof", "field", "focus", "blur"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `focus_distance: float` (default: 0.5, min: 0.0, max: 1.0) - Distance at which objects are in focus
- `focal_range: float` (default: 0.2, min: 0.01, max: 1.0) - Range around focus_distance that is acceptably sharp
- `max_blur_radius: int` (default: 10, min: 1, max: 50) - Maximum blur radius for out-of-focus areas
- `blur_type: str` (default: "gaussian", options: ["gaussian", "bokeh", "hexagonal", "octagonal"]) - Blur kernel shape
- `bokeh_ratio: float` (default: 0.8, min: 0.5, max: 1.5) - Bokeh aspect ratio (for elliptical bokeh)
- `bokeh_rotation: float` (default: 0.0, min: 0.0, max: 360.0) - Bokeh rotation in degrees
- `highlight_boost: float` (default: 0.0, min: 0.0, max: 1.0) - Additional brightness for bright out-of-focus areas
- `chromatic_aberration: float` (default: 0.0, min: 0.0, max: 0.01) - Color fringing amount

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)

### Outputs
- `video: Frame` (same format as input) - Video with depth-of-field effect

## What It Does NOT Do
- Does NOT perform lens simulation beyond basic DOF (no vignette, distortion)
- Does NOT support moving focal plane animation (static focus only)
- Does NOT include auto-focus algorithms (manual focus_distance)
- Does NOT handle HDR metadata preservation
- Does NOT support multi-plane occlusion (single depth layer)
- Does NOT include bokeh texture mapping (geometric shapes only)

## Test Plan
1. Unit tests for depth-to-blur mapping
2. Verify focus_distance and focal_range produce correct blur zones
3. Test all blur_type options
4. Performance: ≥ 60 FPS at 1080p with max_blur_radius=20
5. Memory: < 100MB additional RAM
6. Visual: verify DOF creates natural-looking focus transitions

## Implementation Notes
- Compute blur weight: w = clamp((abs(depth - focus_distance) - focal_range/2) / focal_range, 0, 1)
- Blur radius = w * max_blur_radius
- For gaussian: use separable Gaussian kernel with computed radius
- For bokeh shapes: use disc, hexagon, or octagon kernels
- Apply chromatic_aberration by offsetting RGB channels slightly
- Apply highlight_boost to bright areas in blur regions
- Optimize with pyramid-based blur for large radii
- Consider using GPU shader for real-time performance
- Follow SAFETY_RAILS: validate parameters, handle edge cases

## Deliverables
- `src/vjlive3/effects/depth_field.py`
- `tests/effects/test_depth_field.py`
- `docs/plugins/depth_field.md`
- Optional: `shaders/depth_field.frag`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] DOF simulation works correctly
- [x] All parameters functional
- [x] 60 FPS at 1080p with max_blur_radius=20
- [x] Test coverage ≥ 80%
- [x] No safety rail violations