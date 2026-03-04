# P3-VD29: Depth Camera Splitter Effect

## What This Module Does
Splits the video stream into multiple virtual camera views based on depth ranges. Each depth segment is treated as if viewed from a different camera angle, creating a multi-perspective effect where foreground, midground, and background appear to be from different viewpoints. Useful for creating parallax-like depth separation effects.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthCameraSplitter",
    "version": "3.0.0",
    "description": "Split video into multiple camera views by depth range",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "camera",
    "tags": ["depth", "camera", "split", "parallax", "multi-view"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `num_splits: int` (default: 3, min: 2, max: 8) - Number of depth segments
- `split_method: str` (default: "uniform", options: ["uniform", "adaptive", "custom"]) - How to define depth ranges
- `custom_depths: list[float]` (default: []) - Custom depth boundaries if split_method="custom"
- `camera_offsets: list[dict]` (default: []) - Per-split camera transform (x, y, zoom, rotation)
- `blend_edges: bool` (default: True) - Smooth blending between split regions
- `blend_width: float` (default: 0.05, min: 0.0, max: 0.2) - Blend transition width as fraction of depth

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)

### Outputs
- `video: Frame` (same format as input) - Split and transformed video frame

## What It Does NOT Do
- Does NOT perform true 3D reconstruction (only 2D transforms per depth slice)
- Does NOT handle occlusions between splits (simple overdraw)
- Does NOT support perspective-correct interpolation (affine transforms only)
- Does NOT include depth-based parallax with camera motion (static splits only)
- Does NOT preserve HDR metadata through transforms
- Does NOT support more than 8 splits (hard limit)

## Test Plan
1. Unit tests for depth range segmentation
2. Verify each split applies correct camera transform
3. Test blend edge smoothness
4. Performance: ≥ 60 FPS at 1080p with num_splits=5
5. Memory: < 150MB additional RAM
6. Visual: verify splits align with depth discontinuities

## Implementation Notes
- Compute depth histogram or use quantiles for adaptive split_method
- For each depth segment, create mask and apply camera transform (affine)
- Use feathering/blending at segment boundaries if blend_edges=True
- Camera offsets: {"offset_x": float, "offset_y": float, "zoom": float, "rotation": float}
- Optimize with mask-based compositing rather than full frame transforms
- Consider using GPU shaders for real-time performance
- Follow SAFETY_RAILS: validate parameters, handle errors explicitly

## Deliverables
- `src/vjlive3/effects/depth_camera_splitter.py`
- `tests/effects/test_depth_camera_splitter.py`
- `docs/plugins/depth_camera_splitter.md`
- Optional: `shaders/depth_camera_splitter.frag`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Correct depth segmentation
- [x] Camera transforms apply per split
- [x] 60 FPS at 1080p with 5 splits
- [x] Smooth blending at edges
- [x] Test coverage ≥ 80%
- [x] No safety rail violations