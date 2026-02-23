# P3-EXT055: Depth Effects Depth Mesh Effect

## What This Module Does
Generates a 3D mesh from depth information, where depth values determine vertex positions, creating a deformable mesh surface that represents the scene's depth structure and can be manipulated in real-time.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Depth Mesh Effect",
    "id": "P3-EXT055",
    "category": "depth_effects",
    "description": "Generates and manipulates 3D mesh from depth map with real-time deformation",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "MeshEngine"],
    "test_coverage": 85
}
```

### Parameters
- `mesh_resolution` (int): Mesh grid resolution (16-256, default: 64)
- `depth_scale` (float): Depth to mesh Z-scale multiplier (0.1-10.0, default: 1.0)
- `mesh_smoothing` (float): Laplacian smoothing factor (0.0-1.0, default: 0.3)
- `displacement_strength` (float): Additional displacement strength (0.0-2.0, default: 0.5)
- `wireframe` (bool): Render as wireframe (default: False)
- `shading_mode` (str): Shading: "flat", "smooth", "depth", "normal"
- `vertex_color` (bool): Enable vertex coloring (default: True)
- `texture_mapping` (str): Texture mapping: "none", "depth", "video", "normal"

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Rendered mesh [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform high-resolution mesh generation at 4K (performance limit)
- Does NOT support mesh export to OBJ/STL (visual only)
- Does NOT implement advanced mesh algorithms (simplified grid)
- Does NOT handle mesh collisions with scene (deformation only)
- Does NOT support mesh animation beyond depth-driven deformation

## Test Plan

### Unit Tests
1. `test_mesh_effect_initialization()`
   - Verify METADATA constants
   - Test parameter validation (mesh_resolution 16-256, depth_scale 0.1-10.0, displacement_strength 0-2)
   - Test default parameter values

2. `test_mesh_generation()`
   - Test mesh_resolution: 16, 64, 256
   - Verify vertex count matches resolution²
   - Test mesh topology (grid connectivity)

3. `test_depth_to_mesh_projection()`
   - Test depth_scale: 0.1, 1.0, 10.0
   - Verify Z coordinate from depth
   - Test X,Y coordinates from pixel grid

4. `test_mesh_smoothing()`
   - Test mesh_smoothing: 0.0, 0.3, 1.0
   - Verify Laplacian smoothing applied
   - Test smoothing quality vs performance

5. `test_displacement()`
   - Test displacement_strength: 0.0, 0.5, 2.0
   - Verify additional displacement applied
   - Test displacement direction

6. `test_shading_modes()`
   - Test all shading_mode options: flat, smooth, depth, normal
   - Verify shading calculations
   - Test shading quality

7. `test_wireframe_rendering()`
   - Enable/disable wireframe
   - Verify wireframe lines rendered correctly
   - Test line thickness

8. `test_texture_mapping()`
   - Test all texture_mapping options: none, depth, video, normal
   - Verify texture coordinates and mapping
   - Test texture quality

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with mesh_resolution=64
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 1GB

2. `test_real_depth_mesh_generation()`
   - Feed real depth map from MiDaS/DPT
   - Verify mesh represents scene geometry
   - Test with various depth ranges

3. `test_mesh_performance_scaling()`
   - Test mesh_resolution scaling: 16, 64, 256
   - Verify FPS degradation is quadratic
   - Test memory scaling

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `MeshEngine` from VJlive-2 if available
- Generate regular grid mesh (resolution × resolution vertices)
- Project depth to Z coordinate, X,Y from pixel positions
- Apply smoothing and displacement
- Render using OpenGL mesh rendering

### Performance Optimizations
- Use GPU for mesh generation and deformation (CUDA)
- Precompute mesh connectivity (index buffer)
- Use VBO for mesh vertex data
- Implement mesh LOD based on distance

### Memory Management
- Vertex count = resolution² (max: 256² = 65536 vertices)
- Each vertex: position (3 floats) + normal (3 floats) + texcoord (2 floats) = 32 bytes
- 65536 vertices × 32 bytes = 2MB per mesh
- Index buffer: 2× triangles × 3 indices × 4 bytes = ~1.5MB for 256 resolution
- Profile memory with 4K input, enforce < 2GB peak

### Safety Rails
- Enforce mesh_resolution ≤ 256 (memory/performance)
- Clamp depth_scale to [0.1, 10.0], displacement_strength to [0.0, 2.0]
- Validate shading_mode and texture_mapping as valid options
- Fallback to simple mesh if resolution too high

## Deliverables
1. `src/vjlive3/effects/depth_mesh_effect.py` - Main effect
2. `tests/effects/test_depth_mesh_effect.py` - Tests
3. `docs/effects/depth_mesh_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p with mesh_resolution=64 on RTX 4070 Ti Super
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
