# P3-EXT078: Face Melt Datamosh Effect

## What This Module Does
Creates a surreal face-melting datamosh effect where depth values control the intensity and pattern of facial distortion, producing psychedelic melting and morphing effects that respond to scene depth.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "Face Melt Datamosh",
    "id": "P3-EXT078",
    "category": "depth_effects",
    "description": "Face-melting datamosh with depth-driven facial distortion and psychedelic morphing",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "FaceDetectionEngine", "DatamoshCore"],
    "test_coverage": 85
}
```

### Parameters
- `melt_intensity` (float): Base melting strength (0.0-1.0, default: 0.6)
- `depth_melt_mapping` (str): How depth affects melting: "near_more", "far_more", "mid_more", "uniform"
- `melt_speed` (float): Melting animation speed (0.0-5.0, default: 1.0)
- `morph_intensity` (float): Morphing strength (0.0-1.0, default: 0.4)
- `face_detection` (bool): Enable face detection for targeted melting (default: True)
- `melt_color_shift` (bool): Enable color shift during melting (default: True)
- `glitch_frequency` (float): Glitch occurrence frequency (0.0-1.0, default: 0.2)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Face-melted output [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform real-time face detection at 4K resolution (performance limit)
- Does NOT support face melting for transparent objects (limited accuracy)
- Does NOT preserve video quality (intentionally distorts)
- Does NOT handle face melting for complex scenes with many faces (simplified)
- Does NOT support face melting for HDR content (SDR only)

## Test Plan

### Unit Tests
1. `test_face_melt_initialization()`
   - Verify METADATA constants
   - Test parameter validation (melt_intensity 0-1, melt_speed 0-5.0, morph_intensity 0-1, glitch_frequency 0-1)
   - Test default parameter values

2. `test_melt_intensity_and_speed()`
   - Test melt_intensity: 0.0, 0.6, 1.0
   - Test melt_speed: 0.0, 1.0, 5.0
   - Verify melting animation smoothness
   - Test extreme values

3. `test_depth_melt_mapping()`
   - Test all depth_melt_mapping modes: near_more, far_more, mid_more, uniform
   - Create synthetic depth map with varying regions
   - Verify melting strength varies with depth

4. `test_morph_intensity()`
   - Test morph_intensity: 0.0, 0.4, 1.0
   - Verify morphing strength
   - Test morph quality vs performance

5. `test_face_detection_integration()`
   - Enable/disable face_detection
   - Verify targeted melting on detected faces
   - Test face detection accuracy

6. `test_color_shift_effect()`
   - Enable/disable melt_color_shift
   - Verify color shift during melting
   - Test color shift intensity

7. `test_glitch_frequency()`
   - Test glitch_frequency: 0.0, 0.2, 1.0
   - Verify glitch occurrence rate
   - Test glitch quality vs performance

8. `test_melt_and_morph_interaction()`
   - Test combined melting and morphing
   - Verify synchronized effects
   - Test with different depth mappings

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with melt_intensity=0.6
   - Verify FPS ≥ 60 on test hardware
   - Monitor memory usage < 2x input size

2. `test_real_depth_face_melting()`
   - Feed real depth map from MiDaS/DPT
   - Verify depth-based melting variations
   - Test with complex scenes (people, objects, backgrounds)

3. `test_face_detection_accuracy()`
   - Test face_detection with various face sizes and angles
   - Verify melting targets correct faces
   - Test detection performance

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `FaceDetectionEngine` from VJlive-2 if available
- Use `DatamoshCore` from legacy vjlive plugins
- Implement face detection for targeted melting
- Add depth-driven melting: melt_strength = base_strength × depth_factor
- Add morphing effects with depth-based intensity
- Implement color shift during melting
- Add glitch effects with frequency control

### Performance Optimizations
- Use GPU for face detection and melting operations (CUDA)
- Precompute melting lookup tables for depth values
- Use shared memory for melting buffer access
- Implement melting LOD for distance

### Memory Management
- Allocate melting buffer same size as frame (1920×1080×3 = 6MB)
- Use temporal buffer for melting animation (1 frame)
- Profile memory with 4K input, enforce < 4GB peak
- Free temporary buffers immediately after use

### Safety Rails
- Enforce melt_intensity ≤ 1.0, melt_speed ≤ 5.0, morph_intensity ≤ 1.0, glitch_frequency ≤ 1.0
- Validate depth_melt_mapping as valid option
- Fallback to uniform melting if depth missing
- Fallback to simple melting if face detection fails

## Deliverables
1. `src/vjlive3/effects/face_melt_datamosh_effect.py` - Main effect
2. `tests/effects/test_face_melt_datamosh_effect.py` - Tests
3. `docs/effects/face_melt_datamosh_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Depth-based melting variations work correctly
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
