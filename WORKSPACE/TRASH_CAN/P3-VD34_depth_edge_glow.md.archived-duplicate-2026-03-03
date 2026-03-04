# P3-VD34: Depth Edge Glow Effect

## What This Module Does
Creates glowing edge effects based on depth discontinuities. Detects depth edges and applies glow/blur effects to them, creating atmospheric lighting effects that emphasize depth boundaries. Useful for creating rim lighting, depth-based highlights, or atmospheric glow effects.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthEdgeGlow",
    "version": "3.0.0",
    "description": "Glow effects on depth edges",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "glow",
    "tags": ["depth", "edge", "glow", "rim", "highlight"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `glow_intensity: float` (default: 0.5, min: 0.0, max: 2.0) - Strength of glow effect
- `glow_radius: int` (default: 3, min: 1, max: 15) - Blur radius for glow
- `edge_threshold: float` (default: 0.1, min: 0.01, max: 0.5) - Depth difference for edge detection
- `glow_color: list[float]` (default: [1.0, 0.8, 0.2]) - Glow color (RGB 0-1)
- `glow_falloff: str` (default: "linear", options: ["linear", "exponential", "gaussian"]) - Glow falloff function
- `glow_only: bool` (default: False) - Show only glow, no original image
- `edge_smoothness: int` (default: 2, min: 0, max: 5) - Edge smoothing iterations

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)

### Outputs
- `video: Frame` (same format as input) - Video with edge glow

## What It Does NOT Do
- Does NOT perform full edge detection (only depth-based edges)
- Does NOT support color-based edge detection
- Does NOT include motion-based edge detection
- Does NOT handle HDR metadata preservation
- Does NOT support custom glow shapes or patterns
- Does NOT include advanced glow compositing modes

## Test Plan
1. Unit tests for depth edge detection
2. Verify glow applies correctly to depth edges
3. Test all glow_falloff options
4. Performance: ≥ 60 FPS at 1080p with glow_radius=5
5. Memory: < 100MB additional RAM
6. Visual: verify glow creates atmospheric effects

## Implementation Notes
- Compute depth gradient magnitude to find edges
- Apply smoothing to edges if edge_smoothness > 0
- Create edge mask from gradient magnitude > edge_threshold
- Apply blur to edge mask with glow_radius
- Multiply blurred mask by glow_color and glow_intensity
- Composite with original video (unless glow_only=True)
- For glow_falloff: linear = mask, exponential = exp(-x), gaussian = exp(-x²)
- Optimize with separable blur for large radii
- Follow SAFETY_RAILS: handle edge cases, no silent failures

## Deliverables
- `src/vjlive3/effects/depth_edge_glow.py`
- `tests/effects/test_depth_edge_glow.py`
- `docs/plugins/depth_edge_glow.md`
- Optional: `shaders/depth_edge_glow.frag`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Depth edges detected correctly
- [x] Glow applies to edges
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations