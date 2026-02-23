# P3-EXT058: Depth Parallel Universe Datamosh Effect

## What This Module Does
Creates a datamosh effect that simulates "parallel universe" splitting based on depth. The effect generates multiple parallel versions of the video, each with different datamosh parameters, and blends them together based on depth values. Creates a multi-reality, glitchy aesthetic where different depth regions appear to exist in alternate realities.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthParallelUniverseDatamosh",
    "version": "3.0.0",
    "description": "Multi-reality datamosh with depth-based splitting",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "datamosh",
    "tags": ["depth", "datamosh", "parallel", "universe", "multi"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `num_universes: int` (default: 3, min: 2, max: 5) - Number of parallel realities
- `universe_params: list[dict]` (default: []) - Per-universe datamosh parameters
- `depth_split_points: list[float]` (default: [0.33, 0.66]) - Depth boundaries between universes
- `blend_edges: bool` (default: True) - Smooth blending at universe boundaries
- `blend_width: float` (default: 0.1, min: 0.01, max: 0.3) - Blend transition width
- `universe_shift: float` (default: 0.1, min: 0.0, max: 0.5) - Temporal offset per universe
- `glitch_intensity: float` (default: 0.3, min: 0.0, max: 1.0) - Base glitch amount
- `color_shift_per_universe: bool` (default: True) - Each universe has distinct color

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `previous_frames: list[Frame]` (optional) - Frame history for datamosh

### Outputs
- `video: Frame` (same format as input) - Multi-universe datamoshed video

## What It Does NOT Do
- Does NOT support infinite universes (hard limit of 5)
- Does NOT perform true parallel processing (sequential rendering)
- Does NOT include universe-specific audio processing
- Does NOT handle HDR metadata preservation
- Does NOT support dynamic universe count changes
- Does NOT include universe visualization or debugging

## Test Plan
1. Unit tests for universe splitting logic
2. Verify depth boundaries correctly separate universes
3. Test blend edge smoothness
4. Performance: ≥ 60 FPS at 1080p with num_universes=3
5. Memory: < 250MB additional RAM (multiple buffers)
6. Visual: verify parallel universe effect creates distinct layers

## Implementation Notes
- Divide depth range into num_universes segments using depth_split_points
- For each universe i:
  - Create mask for depth values in that universe's range
  - Apply datamosh with parameters from universe_params[i] (or defaults)
  - If color_shift_per_universe: apply unique color offset to each universe
  - Apply universe_shift as temporal offset (use different frame from history)
- If blend_edges: feather masks at boundaries using blend_width
- Composite all universes using additive or alpha blending
- Apply glitch_intensity as random corruption
- Optimize by sharing frame buffers and processing only masked regions
- Follow SAFETY_RAILS: validate universe count, handle edge cases

## Deliverables
- `src/vjlive3/effects/depth_parallel_universe_datamosh.py`
- `tests/effects/test_depth_parallel_universe_datamosh.py`
- `docs/plugins/depth_parallel_universe_datamosh.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Multiple universes render correctly
- [x] Depth splitting works as expected
- [x] 60 FPS at 1080p with 3 universes
- [x] Test coverage ≥ 80%
- [x] No safety rail violations