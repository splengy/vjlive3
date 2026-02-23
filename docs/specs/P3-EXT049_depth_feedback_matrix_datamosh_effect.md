# P3-EXT049: Depth Feedback Matrix Datamosh Effect

## What This Module Does
Creates a datamosh effect that uses a feedback matrix architecture where depth values control the feedback routing and mixing. The effect maintains a matrix of previous frames and combines them in complex ways based on depth patterns, creating intricate, evolving glitch patterns that follow depth structure.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthFeedbackMatrixDatamosh",
    "version": "3.0.0",
    "description": "Matrix-based datamosh with depth-controlled feedback",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "datamosh",
    "tags": ["depth", "datamosh", "feedback", "matrix", "glitch"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `matrix_size: int` (default: 4, min: 2, max: 8) - Size of feedback matrix (NxN)
- `feedback_decay: float` (default: 0.9, min: 0.5, max: 0.99) - Decay factor per iteration
- `depth_routing_strength: float` (default: 0.7, min: 0.0, max: 1.0) - How much depth controls routing
- `glitch_intensity: float` (default: 0.3, min: 0.0, max: 1.0) - Random glitch probability
- `mix_mode: str` (default: "additive", options: ["additive", "multiply", "screen", "difference"]) - Matrix mixing mode
- `routing_algorithm: str` (default: "depth_proportional", options: ["depth_proportional", "threshold", "quantized"]) - How depth routes feedback
- `quantization_levels: int` (default: 4, min: 2, max: 16) - Levels for quantized routing
- `temporal_blend: float` (default: 0.5, min: 0.0, max: 1.0) - Blend with previous output

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `previous_frames: list[Frame]` (optional) - Previous frames for feedback matrix

### Outputs
- `video: Frame` (same format as input) - Datamoshed video frame

## What It Does NOT Do
- Does NOT support infinite feedback (matrix size limits recursion)
- Does NOT perform automatic glitch pattern generation (depth-driven only)
- Does NOT include audio-reactive routing (depth-only)
- Does NOT handle HDR metadata preservation
- Does NOT support custom routing algorithms beyond the three provided
- Does NOT include matrix visualization or debugging tools

## Test Plan
1. Unit tests for feedback matrix management
2. Verify depth-based routing works correctly
3. Test all mix_mode options
4. Performance: ≥ 60 FPS at 1080p with matrix_size=4
5. Memory: < 300MB additional RAM (matrix buffers)
6. Visual: verify feedback creates complex, evolving glitch patterns

## Implementation Notes
- Maintain a matrix of size (matrix_size x matrix_size) of previous frames
- Each matrix cell contains a delayed/processed version of the video
- Use depth to determine which matrix cells contribute to current output:
  - For depth_proportional: weight = depth value, route to multiple cells
  - For threshold: binarize depth into quantization_levels discrete values
  - For quantized: map depth to one of matrix_size*matrix_size cells
- Apply feedback_decay to each cell's contribution
- Mix matrix cells according to mix_mode
- Apply glitch_intensity as random corruption (frame drops, color shifts)
- Blend result with previous output using temporal_blend
- Optimize with shared buffers and minimal copying
- Follow SAFETY_RAILS: cap matrix size, handle edge cases

## Deliverables
- `src/vjlive3/effects/depth_feedback_matrix_datamosh.py`
- `tests/effects/test_depth_feedback_matrix_datamosh.py`
- `docs/plugins/depth_feedback_matrix_datamosh.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Feedback matrix operates correctly
- [x] Depth routing functions as expected
- [x] 60 FPS at 1080p with 4x4 matrix
- [x] Test coverage ≥ 80%
- [x] No safety rail violations