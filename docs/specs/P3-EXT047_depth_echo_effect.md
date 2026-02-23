# P3-EXT047: Depth Echo Effect

## What This Module Does
Creates echo/trailing effects based on depth information. The effect produces multiple delayed copies of the input video, with each copy's offset and opacity controlled by depth values. Creates ghostly afterimages that follow depth contours, producing a sense of depth-based motion blur or temporal smearing.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthEchoEffect",
    "version": "3.0.0",
    "description": "Depth-based echo/trailing effect",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "temporal",
    "tags": ["depth", "echo", "trail", "ghost", "temporal"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `num_echoes: int` (default: 3, min: 1, max: 10) - Number of echo copies
- `echo_delay: float` (default: 0.1, min: 0.01, max: 0.5) - Time delay between echoes (seconds)
- `echo_decay: float` (default: 0.7, min: 0.1, max: 1.0) - Opacity decay per echo
- `max_offset: int` (default: 20, min: 1, max: 100) - Maximum pixel offset for echoes
- `depth_scale: float` (default: 1.0, min: 0.1, max: 5.0) - How much depth affects offset
- `depth_offset: float` (default: 0.0, min: -1.0, max: 1.0) - Depth bias for offset calculation
- `direction: str` (default: "radial", options: ["radial", "horizontal", "vertical", "depth"]) - Echo direction
- `blend_mode: str` (default: "additive", options: ["additive", "alpha", "screen"]) - Echo blending

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `timestamp: float` (optional) - Current time for echo animation

### Outputs
- `video: Frame` (same format as input) - Video with depth-based echoes

## What It Does NOT Do
- Does NOT perform full temporal processing (simple frame buffering only)
- Does NOT support motion estimation or optical flow
- Does NOT include audio-reactive echo (depth-only)
- Does NOT handle HDR metadata preservation through echoes
- Does NOT support custom echo patterns beyond basic offsets
- Does NOT include echo decay curve customization

## Test Plan
1. Unit tests for echo buffer management
2. Verify depth-based offset calculation
3. Test all direction options
4. Performance: ≥ 60 FPS at 1080p with num_echoes=5
5. Memory: < 150MB additional RAM (echo buffers)
6. Visual: verify echoes create smooth trailing effect

## Implementation Notes
- Maintain a ring buffer of previous frames (size = num_echoes)
- For each echo i (0 to num_echoes-1):
  - offset = i * echo_delay * fps (in frames)
  - Retrieve frame from buffer at appropriate offset
  - Compute depth-based offset: depth_offset_pixels = max_offset * (depth * depth_scale + depth_offset)
  - Apply directional offset: horizontal, vertical, radial, or depth-based
  - Apply decay: opacity = echo_decay ^ i
  - Blend with output using blend_mode
- For radial: offset direction points away from center
- For depth: offset magnitude controlled by depth value, direction based on gradient
- Optimize with shared buffer and minimal copying
- Follow SAFETY_RAILS: cap buffer size, handle missing frames

## Deliverables
- `src/vjlive3/effects/depth_echo.py`
- `tests/effects/test_depth_echo.py`
- `docs/plugins/depth_echo.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Echo effect works with depth modulation
- [x] All parameters functional
- [x] 60 FPS at 1080p with 5 echoes
- [x] Test coverage ≥ 80%
- [x] No safety rail violations