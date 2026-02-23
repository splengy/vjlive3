# P3-VD28: Depth Blur Effect

## What This Module Does
Implements a depth-based blur effect that selectively blurs regions of the image based on depth values. Creates realistic depth-of-field effects where objects at certain depth ranges are blurred while others remain sharp. Supports multiple blur types and smooth transitions between focused and blurred regions.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthBlur",
    "version": "3.0.0",
    "description": "Selective blur based on depth buffer values",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "blur",
    "tags": ["depth", "blur", "dof", "focus"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `blur_radius: int` (default: 5, min: 1, max: 50) - Maximum blur kernel size
- `focus_start: float` (default: 0.3, min: 0.0, max: 1.0) - Near bound of focused region
- `focus_end: float` (default: 0.7, min: 0.0, max: 1.0) - Far bound of focused region
- `transition_smoothness: float` (default: 0.1, min: 0.01, max: 0.5) - Blur transition width
- `blur_type: str` (default: "gaussian", options: ["gaussian", "bokeh", "motion", "anisotropic"]) - Blur algorithm
- `bokeh_shape: str` (default: "circular", options: ["circular", "hexagonal", "octagonal"]) - For bokeh blur
- `anisotropic_scale: float` (default: 1.0, min: 0.1, max: 5.0) - Anisotropy factor for directional blur

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)

### Outputs
- `video: Frame` (same format as input) - Blurred video frame

## What It Does NOT Do
- Does NOT perform edge-aware smoothing (uses pure depth-based masking)
- Does NOT support multi-plane occlusion (single-layer depth only)
- Does NOT include lens aberration simulation beyond basic bokeh
- Does NOT handle temporal consistency (per-frame only)
- Does NOT support HDR metadata preservation
- Does NOT include auto-focus algorithms (manual focus range only)

## Test Plan
1. Unit tests for depth mask generation
2. Verify blur strength varies correctly with depth
3. Test all blur_type options produce expected results
4. Performance test: ≥ 60 FPS at 1080p with blur_radius=25
5. Memory test: < 100MB additional RAM
6. Visual quality: compare against reference depth-of-field images

## Implementation Notes
- Create smooth mask from depth using focus_start/focus_end/transition_smoothness
- Apply separable Gaussian filter for gaussian blur type
- For bokeh, use disc-shaped kernel with hexagonal/octagonal options
- For anisotropic, apply directional blur based on gradient (optional)
- Optimize with FFT-based convolution or SIMD for large kernels
- Must maintain 60 FPS; consider pyramid-based approximation for large radii
- Follow SAFETY_RAILS: proper error handling, no silent failures

## Deliverables
- `src/vjlive3/effects/depth_blur.py`
- `tests/effects/test_depth_blur.py`
- `docs/plugins/depth_blur.md`
- Optional: `shaders/depth_blur.frag` for GPU acceleration

## Success Criteria
- [x] Plugin loads via METADATA discovery
- [x] Accepts video + depth inputs
- [x] All parameters functional
- [x] 60 FPS at 1080p with blur_radius=25 on reference hardware
- [x] Smooth transitions between focused/blurred regions
- [x] Test coverage ≥ 80%
- [x] Zero safety rail violations