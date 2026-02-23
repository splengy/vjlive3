# P3-EXT060: Depth Effects Depth Particle 3D Effect

## What This Module Does
Implements a 3D particle system where particle behavior is driven by depth information, creating depth-aware particle effects that respond to scene geometry and depth gradients.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Depth Particle 3D Effect",
    "id": "P3-EXT060",
    "category": "depth_effects",
    "description": "3D particle system driven by depth information for depth-aware particle effects",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "ParticleEngine3D"],
    "test_coverage": 85
}
```

### Parameters
- `particle_count` (int): Number of particles (1000-100000, default: 10000)
- `depth_response` (float): How strongly particles respond to depth (0.0-1.0, default: 0.7)
- `particle_size` (float): Base particle size in pixels (1.0-50.0, default: 5.0)
- `depth_gradient_force` (float): Force from depth gradients (0.0-1.0, default: 0.3)
- `particle_lifetime` (float): Base lifetime in seconds (1.0-10.0, default: 3.0)
- `spawn_mode` (str): How particles spawn: "depth_contours", "random", "surface", "volume"
- `particle_shape` (str): Particle visual shape: "point", "quad", "sprite", "mesh"

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Video with rendered particles [B, 3, H, W]

## What It Does NOT Do
- Does NOT simulate physics collisions with scene geometry (particles pass through)
- Does NOT handle particle-object interactions beyond depth-based forces
- Does NOT support volumetric particle rendering (screen-space only)
- Does NOT perform real-time particle physics optimization (CPU-bound by default)
- Does NOT handle particle occlusion beyond basic depth testing

## Test Plan

### Unit Tests
1. `test_particle_system_initialization()`
   - Verify METADATA constants
   - Test parameter validation (particle_count 1000-100000, particle_size 1-50)
   - Test default spawn_mode behavior

2. `test_depth_driven_particle_behavior()`
   - Create synthetic depth map with gradient
   - Verify particles respond to depth changes
   - Test depth_response scaling

3. `test_depth_gradient_force()`
   - Create depth gradient map
   - Verify particles align with depth contours
   - Test gradient force magnitude

4. `test_particle_spawn_modes()`
   - Test all spawn modes: depth_contours, random, surface, volume
   - Verify particle distribution matches spawn mode
   - Test edge cases (empty depth, uniform depth)

5. `test_particle_shapes()`
   - Test all particle shapes: point, quad, sprite, mesh
   - Verify rendering quality and performance
   - Test particle_size scaling

6. `test_particle_lifetime()`
   - Test particle lifetime decay
   - Verify particle recycling
   - Test lifetime variation

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with 10000 particles
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 500MB for 10000 particles

2. `test_real_depth_integration()`
   - Feed real depth map from MiDaS/DPT
   - Verify particles align with scene geometry
   - Test with complex depth scenes (people, objects, backgrounds)

3. `test_performance_scaling()`
   - Test particle_count scaling: 1000, 10000, 50000, 100000
   - Verify FPS degradation is linear
   - Test memory scaling

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged with context

## Implementation Notes

### Architecture
- Build on existing `DepthEffect` base class from P3-VD35
- Integrate with `ParticleEngine3D` from VJlive-2 particle system
- Implement depth-driven forces as additional particle acceleration
- Use GPU compute shaders for particle simulation when available

### Performance Optimizations
- Use compute shaders for particle physics (GPU acceleration)
- Implement spatial partitioning for particle-depth interaction
- Batch particle rendering using instanced rendering
- Use depth buffer for particle occlusion culling

### Memory Management
- Allocate particle buffer: 10000 particles × 32 bytes = 320KB
- Use ring buffer for particle recycling
- Implement particle LOD (Level of Detail) for distance
- Profile memory with 100000 particles, enforce < 2GB peak

### Safety Rails
- Enforce particle_count ≤ 100000 (performance limit)
- Clamp depth_response to [0, 1] with warning log if exceeded
- Validate depth range [0, 1] with clear error message
- Fallback to simple particles if GPU compute unavailable

## Deliverables
1. `src/vjlive3/effects/depth_particle_3d_effect.py` - Main effect implementation
2. `tests/effects/test_depth_particle_3d_effect.py` - Unit + integration tests
3. `docs/effects/depth_particle_3d_effect.md` - User documentation
4. Update `MODULE_MANIFEST.md` with new plugin entry

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p with 10000 particles on RTX 4070 Ti Super
- ✅ Zero safety rail violations (memory, errors, silent failures)
- ✅ Works with real depth maps from MiDaS/DPT
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
