# P3-EXT053: Depth Holographic Iridescence Effect

## What This Module Does
Creates a holographic iridescence effect where depth values control the interference patterns and color shifting. Simulates the appearance of holographic surfaces that shift colors based on viewing angle and depth. Produces shimmering, rainbow-like effects that follow depth contours.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthHolographicIridescence",
    "version": "3.0.0",
    "description": "Holographic iridescence controlled by depth",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "holographic",
    "tags": ["depth", "holographic", "iridescence", "rainbow", "interference"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `iridescence_intensity: float` (default: 0.5, min: 0.0, max: 1.0) - Strength of iridescence effect
- `color_shift_speed: float` (default: 1.0, min: 0.1, max: 5.0) - Speed of color shifting
- `depth_scale: float` (default: 1.0, min: 0.1, max: 5.0) - How much depth affects color
- `wave_frequency: float` (default: 10.0, min: 1.0, max: 50.0) - Frequency of interference pattern
- `wave_amplitude: float` (default: 1.0, min: 0.1, max: 3.0) - Amplitude of color waves
- `base_color: list[float]` (default: [0.5, 0.5, 0.5]) - Base color before iridescence
- `specular_highlight: float` (default: 0.3, min: 0.0, max: 1.0) - Strength of specular highlights
- `animate: bool` (default: True) - Enable animation
- `view_angle: float` (default: 0.0, min: 0.0, max: 360.0) - Simulated viewing angle

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `timestamp: float` (optional) - Current time for animation

### Outputs
- `video: Frame` (same format as input) - Holographic iridescent video

## What It Does NOT Do
- Does NOT perform full hologram reconstruction (only color effects)
- Does NOT support physical-based rendering of holographic materials
- Does NOT include 3D light field computation
- Does NOT handle HDR metadata preservation
- Does NOT support custom interference patterns beyond sine waves
- Does NOT include hologram animation beyond color shifting

## Test Plan
1. Unit tests for iridescence color calculation
2. Verify depth modulates color shifting correctly
3. Test animation speed and continuity
4. Performance: ≥ 60 FPS at 1080p
5. Memory: < 100MB additional RAM
6. Visual: verify holographic shimmer effect

## Implementation Notes
- Compute iridescence color using thin-film interference simulation
- Use depth to modulate phase shift: phase = depth * depth_scale * wave_frequency
- Generate color from phase using cosine-based palette: color = base_color + wave_amplitude * cos(phase + view_angle)
- Animate by adding timestamp * color_shift_speed to phase
- Add specular_highlight based on depth gradient magnitude
- Blend with original video using iridescence_intensity
- Optimize with precomputed color lookup tables
- Follow SAFETY_RAILS: handle edge cases, no silent failures

## Deliverables
- `src/vjlive3/effects/depth_holographic_iridescence.py`
- `tests/effects/test_depth_holographic_iridescence.py`
- `docs/plugins/depth_holographic_iridescence.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Holographic iridescence works with depth
- [x] Animation smooth and controllable
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations