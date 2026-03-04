# P3-VD30: Depth Color Grade Effect

## What This Module Does
Applies color grading and correction based on depth values. Different depth ranges can receive distinct color treatments, allowing for atmospheric effects like fog, depth-based tinting, or selective color correction. Creates cinematic depth-of-field color grading where foreground and background have different color characteristics.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthColorGrade",
    "version": "3.0.0",
    "description": "Depth-based color grading and correction",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "color",
    "tags": ["depth", "color", "grade", "correction", "atmosphere"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `grade_curve: str` (default: "linear", options: ["linear", "smooth", "stepped", "custom"]) - Depth-to-color mapping function
- `near_color: list[float]` (default: [1.0, 1.0, 1.0]) - Color multiplier for near objects (RGB 0-1)
- `far_color: list[float]` (default: [0.8, 0.9, 1.0]) - Color multiplier for far objects (RGB 0-1)
- `contrast_boost: float` (default: 0.0, min: -1.0, max: 1.0) - Additional contrast based on depth
- `saturation_shift: float` (default: 0.0, min: -1.0, max: 1.0) - Saturation variation with depth
- `fog_density: float` (default: 0.0, min: 0.0, max: 1.0) - Exponential fog based on depth
- `fog_color: list[float]` (default: [0.7, 0.8, 1.0]) - Fog color (RGB 0-1)
- `transition_point: float` (default: 0.5, min: 0.0, max: 1.0) - Depth where near/far meet

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit float) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)

### Outputs
- `video: Frame` (same format as input) - Color graded video frame

## What It Does NOT Do
- Does NOT perform full LUT-based color grading (only depth-modulated multipliers)
- Does NOT support 3D LUTs or external color profiles
- Does NOT include hue rotation (only RGB scaling)
- Does NOT handle HDR metadata or tone mapping
- Does NOT support per-channel depth curves (single curve for all channels)
- Does NOT include advanced color correction tools (curves, levels, etc.)

## Test Plan
1. Unit tests for depth-based color interpolation
2. Verify near/far colors blend correctly at transition_point
3. Test all grade_curve options produce smooth mappings
4. Performance: ≥ 60 FPS at 1080p
5. Memory: < 50MB additional RAM
6. Color accuracy: verify output color values match expected multipliers

## Implementation Notes
- Compute depth weight: w = (depth - transition_point) / (1 - transition_point) for far, inverted for near
- Apply smooth interpolation using grade_curve (linear, smoothstep, etc.)
- Combine near_color and far_color based on depth weight
- Apply fog: color = lerp(color, fog_color, fog_density * depth)
- Apply contrast_boost and saturation_shift as post-process
- Optimize with vectorized operations; avoid per-pixel loops
- Follow SAFETY_RAILS: clamp all color values to valid range, handle errors

## Deliverables
- `src/vjlive3/effects/depth_color_grade.py`
- `tests/effects/test_depth_color_grade.py`
- `docs/plugins/depth_color_grade.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Depth-based color interpolation works correctly
- [x] All parameters functional
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations