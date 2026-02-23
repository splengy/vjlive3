# P3-EXT063 Depth Simulator Effect

## What This Module Does

Depth Simulator Effect generates synthetic depth information from 2D video using various depth estimation techniques. This plugin creates depth maps from monocular video, allowing depth-based effects to be applied to videos that don't have native depth data. The simulator uses multiple algorithms to estimate depth from visual cues like perspective, motion, and object recognition.

## Public Interface

```python
METADATA = {
    "name": "Depth Simulator Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Generates synthetic depth from 2D video using estimation algorithms",
    "category": "Depth Effects",
    "tags": ["depth", "simulation", "estimation", "synthetic"],
    "inputs": ["video"],
    "outputs": ["video", "depth"],
    "parameters": {
        "estimation_method": {
            "type": "enum",
            "options": ["perspective", "motion", "object_recognition", "hybrid", "ml_based"],
            "default": "hybrid",
            "description": "Method for depth estimation"
        },
        "depth_range": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 1.0,
            "description": "Range of depth values to generate"
        },
        "depth_scale": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 1.0,
            "description": "Scale factor for depth values"
        },
        "smoothing": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Smoothing applied to depth map"
        },
        "edge_enhancement": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Enhancement of depth edges"
        },
        "temporal_smoothing": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Smoothing across time frames"
        },
        "motion_sensitivity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.7,
            "description": "Sensitivity to motion for depth estimation"
        },
        "object_size_prior": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Prior on object sizes for depth estimation"
        },
        "perspective_convergence": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.8,
            "description": "Strength of perspective-based depth"
        },
        "depth_invert": {
            "type": "boolean",
            "default": false,
            "description": "Invert depth values"
        },
        "depth_offset": {
            "type": "float",
            "min": -1.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Offset added to depth values"
        },
        "output_depth_scale": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 1.0,
            "description": "Final output depth scale"
        },
        "debug_visualization": {
            "type": "boolean",
            "default": false,
            "description": "Show depth estimation debug info"
        }
    }
}
```

## What It Does NOT Do

- Does not match quality of true stereo/ToF depth sensors
- Does not perform real-time ML inference on CPU (requires GPU for ML-based)
- Does not handle transparent/reflective surfaces well
- Does not provide metric depth (relative depth only)

## Test Plan

1. **Estimation Method Tests:**
   - Test perspective-based estimation
   - Test motion-based estimation
   - Test object recognition-based estimation
   - Test hybrid method
   - Test ML-based method (if available)

2. **Depth Range Tests:**
   - Test with small depth range (0.1)
   - Test with large depth range (10.0)
   - Test with different depth ranges

3. **Smoothing Tests:**
   - Test with no smoothing (0.0)
   - Test with maximum smoothing (1.0)
   - Test with different smoothing levels

4. **Edge Enhancement Tests:**
   - Test with no edge enhancement
   - Test with maximum edge enhancement
   - Test with different edge enhancement levels

5. **Temporal Smoothing Tests:**
   - Test with no temporal smoothing
   - Test with maximum temporal smoothing
   - Test with different temporal smoothing levels

6. **Motion Sensitivity Tests:**
   - Test with low motion sensitivity
   - Test with high motion sensitivity
   - Test with different motion sensitivities

7. **Perspective Tests:**
   - Test with different perspective convergence values
   - Test with perspective disabled
   - Test with maximum perspective

8. **Depth Transformation Tests:**
   - Test with depth invert enabled/disabled
   - Test with different depth offsets
   - Test with different output depth scales

9. **Performance Tests:**
   - Measure FPS with different estimation methods
   - Test with various resolutions
   - Verify GPU memory usage (especially for ML-based)

10. **Quality Tests:**
    - Check depth map quality
    - Verify depth continuity
    - Test with moving objects
    - Test with static scenes
    - Compare with ground truth depth if available

## Implementation Notes

- Use GPU acceleration for all estimation methods
- Implement multiple depth estimation algorithms
- Support real-time parameter adjustment
- Provide depth preview mode
- Include debug visualization for tuning

## Deliverables

- `src/vjlive3/plugins/depth_simulator.py` - Main plugin implementation
- `tests/plugins/test_depth_simulator.py` - Comprehensive test suite
- `docs/plugins/depth_simulator.md` - User documentation
- `shaders/depth_simulator_*.glsl` - GPU shaders for estimation methods

## Success Criteria

- ✅ Generates plausible depth from 2D video using multiple algorithms
- ✅ Configurable depth range, scale, and transformation
- ✅ Smoothing and edge enhancement options
- ✅ Real-time performance with minimal FPS impact
- ✅ Reasonable depth quality for effect applications
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails