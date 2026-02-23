# P3-EXT045: Depth Displacement Effect

## What This Module Does
Applies displacement mapping to the video using depth information as the displacement source. Creates warping and distortion effects where depth values control the amount and direction of pixel displacement. Useful for creating ripple effects, heat haze, or other depth-based distortions.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthDisplacementEffect",
    "version": "3.0.0",
    "description": "Displace video using depth as displacement map",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "distortion",
    "tags": ["depth", "displacement", "warp", "distortion"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `displacement_scale: float` (default: 0.1, min: 0.0, max: 1.0) - Maximum displacement amount
- `displacement_axis: str` (default: "both", options: ["horizontal", "vertical", "both"]) - Direction of displacement
- `displacement_source: str` (default: "depth", options: ["depth", "depth_inverted", "depth_gradient"]) - What to use as displacement map
- `wrap_mode: str` (default: "clamp", options: ["clamp", "wrap", "mirror"]) - How to handle displaced pixels outside bounds
- `filter_mode: str` (default: "bilinear", options: ["nearest", "bilinear", "bicubic"]) - Interpolation for displaced pixels
- `animate: bool` (default: False) - Animate displacement over time
- `animation_speed: float` (default: 1.0, min: 0.1, max: 10.0) - Speed of animation when animate=True
- `animation_type: str` (default: "sine", options: ["sine", "cosine", "sawtooth", "triangle"]) - Animation waveform

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `timestamp: float` (optional) - Current time for animation

### Outputs
- `video: Frame` (same format as input) - Displaced video frame

## What It Does NOT Do
- Does NOT perform 3D displacement (only 2D image warping)
- Does NOT support arbitrary displacement maps (depth only)
- Does NOT include temporal smoothing or motion compensation
- Does NOT handle HDR metadata preservation
- Does NOT support multi-layer displacement
- Does NOT include displacement vector visualization

## Test Plan
1. Unit tests for displacement vector calculation
2. Verify displacement amount matches scale parameter
3. Test all wrap_mode options
4. Performance: ≥ 60 FPS at 1080p with displacement_scale=0.2
5. Memory: < 50MB additional RAM
6. Visual: verify displacement creates expected warping

## Implementation Notes
- Compute displacement vectors from depth:
  - If displacement_source="depth": use depth directly
  - If "depth_inverted": use 1.0 - depth
  - If "depth_gradient": use gradient magnitude of depth
- For axis="horizontal": displace x by scale * depth
- For axis="vertical": displace y by scale * depth
- For axis="both": displace x and y by scale * depth (or gradient components)
- If animate: modulate displacement_scale with animation waveform based on timestamp
- Apply displacement using remap operation: output[x,y] = input[x+dx, y+dy]
- Handle out-of-bounds according to wrap_mode
- Use filter_mode for interpolation
- Optimize with vectorized operations; consider GPU shader
- Follow SAFETY_RAILS: validate parameters, handle edge cases

## Deliverables
- `src/vjlive3/effects/depth_displacement.py`
- `tests/effects/test_depth_displacement.py`
- `docs/plugins/depth_displacement.md`
- Optional: `shaders/depth_displacement.frag`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Displacement works correctly
- [x] All parameters functional
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations