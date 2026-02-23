# P3-VD32: Depth Distance Filter Effect

## What This Module Does
Applies distance-based filtering to the video stream using depth information. Creates effects like fog, atmospheric perspective, or distance-based blur by filtering pixels based on their distance from the camera. Useful for creating realistic depth cues and atmospheric effects.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthDistanceFilter",
    "version": "3.0.0",
    "description": "Distance-based filtering using depth buffer",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "filter",
    "tags": ["depth", "distance", "filter", "fog", "atmosphere"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `filter_type: str` (default: "fog", options: ["fog", "blur", "contrast", "saturation", "brightness"]) - Type of distance-based filter
- `near_distance: float` (default: 0.0, min: 0.0, max: 1.0) - Start of distance effect
- `far_distance: float` (default: 1.0, min: 0.0, max: 1.0) - End of distance effect
- `filter_strength: float` (default: 0.5, min: 0.0, max: 1.0) - Intensity of the filter
- `fog_color: list[float]` (default: [0.7, 0.8, 1.0]) - Fog color (RGB 0-1, only for fog type)
- `blur_radius: int` (default: 5, min: 1, max: 20) - Blur radius (only for blur type)
- `contrast_shift: float` (default: 0.0, min: -1.0, max: 1.0) - Contrast shift (only for contrast type)
- `saturation_shift: float` (default: 0.0, min: -1.0, max: 1.0) - Saturation shift (only for saturation type)
- `brightness_shift: float` (default: 0.0, min: -1.0, max: 1.0) - Brightness shift (only for brightness type)

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)

### Outputs
- `video: Frame` (same format as input) - Filtered video frame

## What It Does NOT Do
- Does NOT perform full 3D atmospheric scattering (simple distance-based)
- Does NOT support HDR tone mapping or advanced color grading
- Does NOT include motion blur or temporal effects
- Does NOT handle multi-layer depth compositing
- Does NOT support custom filter kernels beyond basic types
- Does NOT include auto-exposure or adaptive filtering

## Test Plan
1. Unit tests for distance-based filtering
2. Verify filter strength varies correctly with depth
3. Test all filter_type options produce expected results
4. Performance: ≥ 60 FPS at 1080p with filter_strength=0.5
5. Memory: < 50MB additional RAM
6. Visual: verify distance effects create realistic depth cues

## Implementation Notes
- Compute distance weight: w = clamp((depth - near_distance) / (far_distance - near_distance), 0, 1)
- For fog: color = lerp(color, fog_color, w * filter_strength)
- For blur: apply blur with radius = w * filter_strength * blur_radius
- For contrast: apply contrast multiplier based on w and filter_strength
- For saturation: adjust saturation based on w and filter_strength
- For brightness: adjust brightness based on w and filter_strength
- Optimize with vectorized operations; avoid per-pixel loops
- Follow SAFETY_RAILS: clamp all values, handle edge cases

## Deliverables
- `src/vjlive3/effects/depth_distance_filter.py`
- `tests/effects/test_depth_distance_filter.py`
- `docs/plugins/depth_distance_filter.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Distance-based filtering works correctly
- [x] All filter_type options functional
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations