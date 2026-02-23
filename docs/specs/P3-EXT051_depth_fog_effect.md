# P3-EXT051: Depth Fog Effect

## What This Module Does
Applies exponential fog based on depth values. Creates atmospheric perspective by blending the video with a fog color that increases with distance from the camera. Simulates natural fog, mist, or haze effects that are stronger for distant objects.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthFogEffect",
    "version": "3.0.0",
    "description": "Depth-based atmospheric fog",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "atmosphere",
    "tags": ["depth", "fog", "atmosphere", "haze"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `fog_density: float` (default: 0.5, min: 0.0, max: 2.0) - Fog thickness
- `fog_color: list[float]` (default: [0.7, 0.8, 1.0]) - Fog color (RGB 0-1)
- `fog_start: float` (default: 0.3, min: 0.0, max: 1.0) - Distance where fog begins
- `fog_end: float` (default: 1.0, min: 0.0, max: 1.0) - Distance where fog is fully opaque
- `falloff: str` (default: "exponential", options: ["linear", "exponential", "exponential_squared"]) - Fog falloff curve
- `depth_scale: float` (default: 1.0, min: 0.1, max: 10.0) - Scale depth values before fog calculation
- `depth_offset: float` (default: 0.0, min: -1.0, max: 1.0) - Offset depth values
- `light_direction: list[float]` (default: [0.0, 0.0, 1.0]) - Direction of light for directional fog
- `light_color: list[float]` (default: [1.0, 1.0, 1.0]) - Color of light for light-based fog
- `enable_lighting: bool` (default: False) - Enable light-based fog variation

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)

### Outputs
- `video: Frame` (same format as input) - Fogged video frame

## What It Does NOT Do
- Does NOT perform volumetric ray marching (simple depth-based blending)
- Does NOT support multiple fog layers or volumes
- Does NOT include light scattering simulation (simple lighting only)
- Does NOT handle HDR metadata preservation
- Does NOT support custom fog density maps (depth-driven only)
- Does NOT include fog animation or dynamics

## Test Plan
1. Unit tests for fog factor calculation
2. Verify fog density and color produce expected results
3. Test all falloff curves
4. Performance: ≥ 60 FPS at 1080p
5. Memory: < 50MB additional RAM
6. Visual: verify fog creates natural atmospheric perspective

## Implementation Notes
- Compute fog factor f based on depth d:
  - linear: f = clamp((d - fog_start) / (fog_end - fog_start), 0, 1) * fog_density
  - exponential: f = (1 - exp(-(d * depth_scale + depth_offset) * fog_density)) * fog_factor
  - exponential_squared: f = (1 - exp(-((d * depth_scale + depth_offset) * fog_density)^2))
- If enable_lighting: modulate fog by dot product of depth gradient and light_direction
- Output = lerp(video, fog_color, f)
- If enable_lighting: add light_color contribution based on lighting
- Optimize with vectorized operations
- Follow SAFETY_RAILS: clamp all values, handle edge cases

## Deliverables
- `src/vjlive3/effects/depth_fog.py`
- `tests/effects/test_depth_fog.py`
- `docs/plugins/depth_fog.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Fog effect works correctly
- [x] All parameters functional
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations