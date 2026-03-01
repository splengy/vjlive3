# P3-VD31: Depth Contour Datamosh Effect

## What This Module Does
Creates contour-based datamosh effects using depth information. Extracts depth contours/contours and uses them to create glitchy, fragmented visual effects. The contours are treated as boundaries for datamosh operations, creating organic-looking distortions that follow depth edges and shapes.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthContourDatamosh",
    "version": "3.0.0",
    "description": "Contour-based datamosh using depth edges",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "datamosh",
    "tags": ["depth", "contour", "datamosh", "glitch", "edge"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `contour_threshold: float` (default: 0.1, min: 0.01, max: 0.5) - Depth difference for contour detection
- `contour_smoothness: int` (default: 2, min: 0, max: 10) - Contour smoothing iterations
- `datamosh_intensity: float` (default: 0.5, min: 0.0, max: 1.0) - Strength of datamosh effect
- `fragment_size: int` (default: 8, min: 2, max: 32) - Size of datamosh fragments
- `glitch_probability: float` (default: 0.1, min: 0.0, max: 1.0) - Chance of random glitches
- `preserve_edges: bool` (default: True) - Keep contour edges sharp
- `color_shift: float` (default: 0.2, min: 0.0, max: 1.0) - Color aberration on fragments

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)

### Outputs
- `video: Frame` (same format as input) - Datamoshed video frame

## What It Does NOT Do
- Does NOT perform full edge detection (only depth-based contours)
- Does NOT support 3D mesh extraction from contours
- Does NOT include audio-reactive datamosh (depth-only)
- Does NOT handle temporal consistency (per-frame only)
- Does NOT support HDR metadata preservation
- Does NOT include advanced glitch effects beyond basic datamosh

## Test Plan
1. Unit tests for contour extraction from depth
2. Verify datamosh fragments align with depth contours
3. Test all parameter combinations produce expected results
4. Performance: ≥ 60 FPS at 1080p with datamosh_intensity=0.5
5. Memory: < 100MB additional RAM
6. Visual: verify contours create organic-looking distortions

## Implementation Notes
- Compute depth gradient magnitude to find contours
- Apply smoothing to contours if contour_smoothness > 0
- For each contour region, apply datamosh by copying fragments from other frames
- Use fragment_size to control datamosh block size
- Apply color_shift to fragments for chromatic aberration effect
- Preserve contour edges if preserve_edges=True
- Optimize with contour-based masking rather than full frame processing
- Follow SAFETY_RAILS: handle edge cases, no silent failures

## Deliverables
- `src/vjlive3/effects/depth_contour_datamosh.py`
- `tests/effects/test_depth_contour_datamosh.py`
- `docs/plugins/depth_contour_datamosh.md`
- Optional: `shaders/depth_contour_datamosh.frag`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Depth contours extracted correctly
- [x] Datamosh fragments align with contours
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations