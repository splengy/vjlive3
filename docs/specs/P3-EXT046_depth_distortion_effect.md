# P3-EXT046: Depth Distortion Effect

## What This Module Does
Applies various distortion effects to the video based on depth values. Creates warping, bulging, pinching, and other geometric transformations that are controlled by the depth buffer. Useful for creating surreal visual effects where depth influences the shape and geometry of the image.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthDistortionEffect",
    "version": "3.0.0",
    "description": "Depth-based geometric distortion",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "distortion",
    "tags": ["depth", "distortion", "warp", "geometry"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `distortion_type: str` (default: "bulge", options: ["bulge", "pinch", "twist", "wave", "ripple", "custom"]) - Distortion pattern
- `distortion_strength: float` (default: 0.5, min: 0.0, max: 2.0) - Intensity of distortion
- `center_x: float` (default: 0.5, min: 0.0, max: 1.0) - X coordinate of distortion center (normalized)
- `center_y: float` (default: 0.5, min: 0.0, max: 1.0) - Y coordinate of distortion center (normalized)
- `radius: float` (default: 0.5, min: 0.1, max: 1.0) - Radius of distortion effect (normalized)
- `falloff: str` (default: "smooth", options: ["linear", "smooth", "constant"]) - Distortion falloff from center
- `depth_influence: float` (default: 1.0, min: 0.0, max: 2.0) - How much depth modulates distortion
- `animate: bool` (default: False) - Animate distortion over time
- `animation_speed: float` (default: 1.0, min: 0.1, max: 10.0) - Animation speed
- `wave_frequency: int` (default: 2, min: 1, max: 10) - Frequency for wave/ripple types

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `timestamp: float` (optional) - Current time for animation

### Outputs
- `video: Frame` (same format as input) - Distorted video frame

## What It Does NOT Do
- Does NOT perform 3D geometry transformations (2D image warping only)
- Does NOT support arbitrary displacement maps (depth-driven only)
- Does NOT include mesh-based deformation (pixel-level remapping)
- Does NOT handle HDR metadata preservation
- Does NOT support multiple distortion centers
- Does NOT include distortion vector visualization

## Test Plan
1. Unit tests for distortion vector field generation
2. Verify each distortion_type produces expected pattern
3. Test falloff variations
4. Performance: ≥ 60 FPS at 1080p with distortion_strength=1.0
5. Memory: < 100MB additional RAM
6. Visual: verify distortion creates smooth, expected warping

## Implementation Notes
- Compute distortion offset for each pixel based on its distance from center
- For bulge: push pixels away from center, strength proportional to distance
- For pinch: pull pixels toward center
- For twist: rotate pixels around center based on distance
- For wave/ripple: apply sinusoidal displacement based on distance
- Use depth to modulate distortion_strength: effective_strength = distortion_strength * (depth ^ depth_influence)
- Apply falloff: linear = distance/radius, smooth = smoothstep, constant = 1 within radius
- If animate: modulate strength or center with timestamp
- Implement using coordinate remap: output[x,y] = input[x+dx, y+dy]
- Optimize with precomputed distortion maps for static parameters
- Follow SAFETY_RAILS: handle edge cases, no silent failures

## Deliverables
- `src/vjlive3/effects/depth_distortion.py`
- `tests/effects/test_depth_distortion.py`
- `docs/plugins/depth_distortion.md`
- Optional: `shaders/depth_distortion.frag`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] All distortion types work correctly
- [x] Depth modulates distortion as expected
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations