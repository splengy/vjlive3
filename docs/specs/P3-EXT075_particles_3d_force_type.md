# P3-EXT075: Particles 3D Force Type

## What This Module Does
Defines force types and behaviors for 3D particle systems, providing configurable force fields and interactions that affect particle motion based on depth information and spatial relationships.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Particles 3D Force Type",
    "id": "P3-EXT075",
    "category": "depth_effects",
    "description": "Configurable force types and behaviors for 3D particle systems",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "ParticleEngine3D"],
    "test_coverage": 85
}
```

### Parameters
- `force_type` (str): Force field type: "gravity", "vortex", "turbulence", "wind", "magnetic", "depth_field", "attractor", "repulsor"
- `force_strength` (float): Base force strength (0.0-10.0, default: 1.0)
- `force_falloff` (str): Force falloff type: "linear", "inverse_square", "exponential", "none"
- `force_radius` (float): Force influence radius (0.1-20.0, default: 5.0)
- `force_position` (list[float]): Force position in 3D space [x, y, z]
- `force_direction` (list[float]): Force direction vector [dx, dy, dz]
- `force_noise` (float): Force noise amount (0.0-1.0, default: 0.1)
- `depth_force_mapping` (str): How depth affects force: "near_stronger", "far_stronger", "mid_stronger", "uniform"
- `force_animation` (str): Force animation type: "static", "oscillate", "rotate", "pulse"

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Video with force-affected particles [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform particle collisions with force fields (force only)
- Does NOT support force field instancing (single force per effect)
- Does NOT handle force field culling (always active)
- Does NOT support force field animation beyond basic types
- Does NOT perform force field optimization for large numbers of particles

## Test Plan

### Unit Tests
1. `test_force_type_initialization()`
   - Verify METADATA constants
   - Test parameter validation (force_strength 0-10.0, force_radius 0.1-20.0, force_noise 0-1)
   - Test default parameter values

2. `test_force_types()`
   - Test all force_type options: gravity, vortex, turbulence, wind, magnetic, depth_field, attractor, repulsor
   - Verify each force produces correct particle acceleration
   - Test force_type switching

3. `test_force_parameters()`
   - Test force_strength: 0.0, 1.0, 10.0
   - Test force_radius: 0.1, 5.0, 20.0
   - Test force_falloff: linear, inverse_square, exponential, none
   - Verify force calculation

4. `test_force_position_and_direction()`
   - Test force_position [x, y, z] in 3D space
   - Test force_direction [dx, dy, dz] for directional forces
   - Verify force vector calculation
   - Test position/direction switching

5. `test_force_noise()`
   - Test force_noise: 0.0, 0.1, 1.0
   - Verify organic noise in force
   - Test noise quality vs performance

6. `test_depth_force_mapping()`
   - Test all depth_force_mapping modes: near_stronger, far_stronger, mid_stronger, uniform
   - Create synthetic depth map with varying regions
   - Verify force strength varies with depth

7. `test_force_animation()`
   - Test all force_animation options: static, oscillate, rotate, pulse
   - Verify force animation smoothness
   - Test animation switching

8. `test_force_field_interactions()`
   - Test multiple force types together
   - Verify force vector addition
   - Test force priority and blending

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with force_type="gravity"
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_real_depth_force_fields()`
   - Feed real depth map from MiDaS/DPT
   - Verify depth-based force variations
   - Test with complex scenes (people, objects, backgrounds)

3. `test_force_animation_performance()`
   - Test force_animation options
   - Measure FPS vs animation complexity
   - Identify performance bottlenecks

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `ParticleEngine3D` from VJlive-2
- Implement force types as particle acceleration strategies
- Use depth-driven force strength: force_strength = base_strength × depth_factor
- Support force falloff calculations for distance-based attenuation
- Implement force animation for dynamic effects

### Performance Optimizations
- Use GPU for force calculation (CUDA)
- Precompute force lookup tables for depth values
- Use shared memory for force buffer access
- Implement force LOD for distance

### Memory Management
- Allocate force buffer: max_particles × 12 bytes (force vector)
- Use temporal buffer for force animation (1 frame)
- Profile memory with 100000 particles, enforce < 2GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce force_strength ≤ 10.0, force_radius ≤ 20.0, force_noise ≤ 1.0
- Validate force_type, force_falloff, depth_force_mapping, force_animation as valid options
- Clamp force_position and force_direction to reasonable ranges
- Fallback to simple force if depth missing

## Deliverables
1. `src/vjlive3/effects/particles_3d_force_type.py` - Main effect
2. `tests/effects/test_particles_3d_force_type.py` - Tests
3. `docs/effects/particles_3d_force_type.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p with 10000 particles on RTX 4070 Ti Super
- ✅ All force types work correctly
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
