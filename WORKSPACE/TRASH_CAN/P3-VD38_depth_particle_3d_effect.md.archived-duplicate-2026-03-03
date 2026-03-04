# P3-VD38: Depth Particle 3D Effect

## What This Module Does
Generates and animates 3D particles that respond to depth information. Particles are positioned in 3D space based on depth values and can interact with the depth buffer to create effects like depth-based particle emission, collision, or attraction. Creates immersive particle systems that exist within the depth field of the video.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthParticle3DEffect",
    "version": "3.0.0",
    "description": "3D particle system driven by depth buffer",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "particle",
    "tags": ["depth", "particle", "3d", "emitter"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `particle_count: int` (default: 1000, min: 100, max: 10000) - Number of particles
- `emission_rate: int` (default: 50, min: 1, max: 500) - Particles emitted per second
- `particle_lifetime: float` (default: 2.0, min: 0.1, max: 10.0) - Particle lifetime in seconds
- `depth_response: str` (default: "emit", options: ["emit", "attract", "repel", "follow"]) - How particles interact with depth
- `depth_scale: float` (default: 1.0, min: 0.1, max: 10.0) - Scale depth values for particle positioning
- `velocity: list[float]` (default: [0.0, 0.0, 0.0]) - Initial particle velocity (x, y, z)
- `gravity: list[float]` (default: [0.0, 0.0, -9.8]) - Gravity vector
- `color_mode: str` (default: "depth", options: ["depth", "uniform", "random", "velocity"]) - Particle coloring
- `particle_color: list[float]` (default: [1.0, 1.0, 1.0]) - Base particle color (RGB 0-1)
- `size_range: list[float]` (default: [1.0, 5.0]) - Min/max particle size in pixels
- `blend_mode: str` (default: "additive", options: ["additive", "alpha", "screen"]) - Particle blending

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `timestamp: float` (optional) - Current time in seconds for particle animation

### Outputs
- `video: Frame` (same format as input) - Video with 3D particles

## What It Does NOT Do
- Does NOT perform full 3D rendering (2D particles with depth positioning)
- Does NOT support complex particle physics (basic velocity/gravity only)
- Does NOT include particle collision with scene geometry
- Does NOT handle HDR metadata preservation
- Does NOT support particle trails or motion blur
- Does NOT include particle system editor or GUI

## Test Plan
1. Unit tests for particle initialization and update
2. Verify depth-based particle emission/attraction works
3. Test all depth_response options
4. Performance: ≥ 60 FPS at 1080p with particle_count=5000
5. Memory: < 200MB additional RAM
6. Visual: verify particles create immersive depth effects

## Implementation Notes
- Use depth buffer to determine particle spawn positions or attraction points
- For emit: spawn particles at depth values above threshold
- For attract: particles move toward depth peaks
- For repel: particles move away from depth valleys
- For follow: particles trace depth contours
- Update particle positions using velocity, gravity, and depth response
- Render particles as 2D sprites with depth-scaled size
- Use depth for coloring if color_mode="depth"
- Apply blend_mode for compositing with video
- Optimize with spatial partitioning for large particle counts
- Follow SAFETY_RAILS: cap particle count, handle depth edge cases

## Deliverables
- `src/vjlive3/effects/depth_particle_3d.py`
- `tests/effects/test_depth_particle_3d.py`
- `docs/plugins/depth_particle_3d.md`
- Optional: `shaders/particle.vert` and `shaders/particle.frag`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Particles respond to depth correctly
- [x] All depth_response options functional
- [x] 60 FPS at 1080p with 5000 particles
- [x] Test coverage ≥ 80%
- [x] No safety rail violations