# P3-EXT062 Depth Effects Depth Point Cloud Effect

## What This Module Does

Depth Point Cloud Effect creates simplified 3D point cloud visualizations from depth information, optimized for performance while maintaining visual impact. This effect converts depth maps into point clouds with efficient rendering, making it suitable for real-time applications where full particle systems would be too heavy. The point cloud responds to depth values and can be animated and colored based on various inputs.

## Public Interface

```python
METADATA = {
    "name": "Depth Point Cloud Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Simplified 3D point cloud visualization from depth information",
    "category": "Depth Effects",
    "tags": ["depth", "point_cloud", "3d", "volumetric", "optimized"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "point_density": {
            "type": "float",
            "min": 0.01,
            "max": 1.0,
            "default": 0.2,
            "description": "Density of points in the point cloud"
        },
        "max_points": {
            "type": "integer",
            "min": 1000,
            "max": 200000,
            "default": 50000,
            "description": "Maximum number of points to generate"
        },
        "point_size": {
            "type": "float",
            "min": 0.5,
            "max": 5.0,
            "default": 1.5,
            "description": "Size of each point"
        },
        "depth_scale": {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "default": 1.0,
            "description": "Scale factor for depth values"
        },
        "depth_offset": {
            "type": "float",
            "min": -1.0,
            "max": 1.0,
            "default": 0.0,
            "description": "Offset added to depth values"
        },
        "color_mode": {
            "type": "enum",
            "options": ["depth", "video", "solid", "gradient", "depth_gradient"],
            "default": "depth",
            "description": "Color mode for points"
        },
        "point_color": {
            "type": "color",
            "default": "#00ffff",
            "description": "Solid color for points (if color_mode=solid)"
        },
        "gradient_colors": {
            "type": "array",
            "items": {"type": "color"},
            "default": ["#0000ff", "#00ff00", "#ff0000"],
            "description": "Gradient colors for depth-based coloring"
        },
        "opacity": {
            "type": "float",
            "min": 0.1,
            "max": 1.0,
            "default": 0.7,
            "description": "Base point opacity"
        },
        "depth_fade": {
            "type": "boolean",
            "default": true,
            "description": "Fade points based on depth"
        },
        "fade_near": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Near depth for fade start"
        },
        "fade_far": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.8,
            "description": "Far depth for fade end"
        },
        "blend_mode": {
            "type": "enum",
            "options": ["normal", "additive", "screen"],
            "default": "additive",
            "description": "Point blending mode"
        },
        "animation_enable": {
            "type": "boolean",
            "default": true,
            "description": "Enable point animation"
        },
        "animation_type": {
            "type": "enum",
            "options": ["wave", "pulse", "rotate", "drift"],
            "default": "wave",
            "description": "Type of point animation"
        },
        "animation_speed": {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "default": 1.0,
            "description": "Speed of animation"
        },
        "animation_amplitude": {
            "type": "float",
            "min": 0.0,
            "max": 0.5,
            "default": 0.1,
            "description": "Amplitude of animation"
        },
        "rotation_speed": {
            "type": "float",
            "min": 0.0,
            "max": 2.0,
            "default": 0.5,
            "description": "Rotation speed for rotate animation"
        },
        "drift_direction": {
            "type": "enum",
            "options": ["up", "down", "left", "right", "random"],
            "default": "up",
            "description": "Direction for drift animation"
        },
        "drift_speed": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Speed of drift animation"
        },
        "culling_enable": {
            "type": "boolean",
            "default": true,
            "description": "Enable frustum culling for performance"
        },
        "lod_enable": {
            "type": "boolean",
            "default": true,
            "description": "Enable level-of-detail based on distance"
        },
        "lod_thresholds": {
            "type": "array",
            "items": {"type": "float", "min": 0.0, "max": 1.0},
            "default": [0.3, 0.6, 0.9],
            "description": "LOD distance thresholds"
        },
        "lod_reductions": {
            "type": "array",
            "items": {"type": "float", "min": 0.0, "max": 1.0},
            "default": [0.5, 0.25, 0.1],
            "description": "Point reduction factors for each LOD level"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform full 3D physics simulation
- Does not support point-point interactions
- Does not handle infinite point counts (limited by max_points)

## Test Plan

1. **Point Density Tests:**
   - Test with minimum density (very sparse)
   - Test with maximum density (very dense)
   - Test with different densities

2. **Point Count Tests:**
   - Test with minimum 1000 points
   - Test with maximum 200,000 points
   - Test with different point counts

3. **Point Size Tests:**
   - Test with small point size
   - Test with large point size
   - Test with default size

4. **Depth Scale/Offset Tests:**
   - Test with different depth scales
   - Test with different depth offsets
   - Test with combined scale and offset

5. **Color Mode Tests:**
   - Test depth-based coloring
   - Test video-based coloring
   - Test solid color
   - Test gradient coloring
   - Test depth gradient coloring

6. **Opacity and Fade Tests:**
   - Test with different base opacities
   - Test with depth fade enabled/disabled
   - Test with different fade near/far values

7. **Blend Mode Tests:**
   - Test normal blending
   - Test additive blending
   - Test screen blending

8. **Animation Tests:**
   - Test with animation disabled
   - Test with different animation types
   - Test with different animation speeds
   - Test with different animation amplitudes
   - Test rotation animation
   - Test drift animation with different directions

9. **LOD Tests:**
   - Test with LOD disabled
   - Test with LOD enabled
   - Test with different LOD thresholds
   - Test with different LOD reduction factors

10. **Performance Tests:**
    - Measure FPS with different point counts
    - Test with various resolutions
    - Verify GPU memory usage
    - Test with culling enabled/disabled
    - Test with LOD enabled/disabled

11. **Quality Tests:**
    - Check for visual artifacts
    - Verify smooth point animation
    - Test with moving objects
    - Test with static scenes

## Implementation Notes

- Use GPU-based point cloud rendering with instancing for performance
- Implement efficient depth-to-3D conversion on GPU
- Support real-time parameter adjustment
- Provide point cloud preview mode
- Include depth visualization for debugging
- Use compute shaders for large point counts

## Deliverables

- `src/vjlive3/plugins/depth_point_cloud.py` - Main plugin implementation
- `tests/plugins/test_depth_point_cloud.py` - Comprehensive test suite
- `docs/plugins/depth_point_cloud.md` - User documentation
- `shaders/depth_point_cloud.glsl` - GPU shader for point rendering

## Success Criteria

- ✅ Efficient 3D point cloud generation from depth information
- ✅ Configurable point density, size, and count with performance optimization
- ✅ Multiple color modes and blending options
- ✅ Various animation types with smooth motion
- ✅ LOD support for performance scaling
- ✅ Real-time performance with minimal FPS impact
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails