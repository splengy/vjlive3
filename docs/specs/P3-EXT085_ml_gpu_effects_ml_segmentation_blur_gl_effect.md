# P3-EXT085: ML GPU Effects ML Segmentation Blur GL Effect

## What This Module Does
Applies depth-aware blur effects using ML-based semantic segmentation, where depth values and segmentation masks combine to create selective blurring that respects scene depth and object boundaries for realistic depth-of-field and focus effects.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "ML GPU Effects ML Segmentation Blur GL Effect",
    "id": "P3-EXT085",
    "category": "depth_effects",
    "description": "Segmentation-based blur with depth integration using GPU-accelerated ML",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "MLGPUEngine", "SegmentationEngine"],
    "test_coverage": 85
}
```

### Parameters
- `segmentation_model` (str): Segmentation model: "deeplabv3", "maskrcnn", "yolact", "custom"
- `blur_radius` (int): Blur radius in pixels (1-50, default: 10)
- `blur_type` (str): Blur algorithm: "gaussian", "bilateral", "anisotropic", "tilt_shift"
- `depth_blend_factor` (float): How much depth affects blur (0.0-1.0, default: 0.5)
- `segmentation_confidence` (float): Segmentation confidence threshold (0.0-1.0, default: 0.7)
- `edge_preservation` (float): Edge preservation strength (0.0-1.0, default: 0.8)
- `async_inference` (bool): Use async segmentation (default: True)
- `gpu_memory_limit` (float): GPU memory limit in GB (1.0-8.0, default: 4.0)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): Blurred output [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform real-time segmentation at 4K resolution (performance limit)
- Does NOT support all segmentation models (limited to supported architectures)
- Does NOT guarantee segmentation accuracy for all objects (model-dependent)
- Does NOT handle segmentation for transparent objects (limited accuracy)
- Does NOT preserve original video quality (blur modifies)

## Test Plan

### Unit Tests
1. `test_segmentation_blur_initialization()`
   - Verify METADATA constants
   - Test parameter validation (blur_radius 1-50, segmentation_confidence 0-1, depth_blend_factor 0-1)
   - Test default parameter values

2. `test_segmentation_model_loading()`
   - Test valid segmentation_model values: deeplabv3, maskrcnn, yolact, custom
   - Test model loading errors
   - Test model switching

3. `test_blur_parameters()`
   - Test blur_radius: 1, 10, 50
   - Test all blur_type options: gaussian, bilateral, anisotropic, tilt_shift
   - Verify blur quality vs performance

4. `test_depth_blend_factor()`
   - Test depth_blend_factor: 0.0, 0.5, 1.0
   - Verify depth influences blur strength
   - Test blend quality

5. `test_segmentation_confidence()`
   - Test segmentation_confidence: 0.0, 0.7, 1.0
   - Verify confidence thresholding
   - Test false positives/negatives

6. `test_edge_preservation()`
   - Test edge_preservation: 0.0, 0.8, 1.0
   - Verify edge preservation in blur
   - Test edge detection quality

7. `test_async_inference()`
   - Enable/disable async_inference
   - Verify non-blocking segmentation
   - Test async queue management

8. `test_gpu_memory_management()`
   - Test gpu_memory_limit: 1.0, 4.0, 8.0
   - Verify memory allocation respects limit
   - Test OOM handling

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with blur_radius=10
   - Verify FPS ≥ 60 on test hardware
   - Monitor GPU memory < gpu_memory_limit

2. `test_real_depth_segmentation_blur()`
   - Feed real depth map from MiDaS/DPT
   - Verify depth-aware blur with segmentation
   - Test with complex scenes (people, objects, backgrounds)

3. `test_blur_type_comparison()`
   - Test all blur_type options
   - Compare quality and performance
   - Identify best blur for use case

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth/segmentation
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `MLGPUEngine` and `SegmentationEngine` from VJlive-2
- Perform semantic segmentation to get object masks
- Combine depth and segmentation masks for selective blur
- Apply blur only to background or specific depth ranges
- Use GPU-accelerated blur algorithms

### Performance Optimizations
- Use async CUDA streams for segmentation inference
- Implement bilateral/anisotropic blur on GPU
- Cache segmentation results for temporal coherence
- Use mixed precision for ML models

### Memory Management
- Segmentation model: ~100-500MB
- Segmentation mask: H × W × 1 byte
- Blur buffers: H × W × 3 bytes
- Profile GPU memory, enforce gpu_memory_limit
- Free unused models from cache

### Safety Rails
- Enforce blur_radius ≤ 50, segmentation_confidence 0-1
- Clamp depth_blend_factor to [0.0, 1.0], edge_preservation to [0.0, 1.0]
- Validate segmentation_model and blur_type
- Fallback to simple blur if segmentation fails

## Deliverables
1. `src/vjlive3/effects/ml_gpu_effects_ml_segmentation_blur_gl_effect.py` - Main effect
2. `tests/effects/test_ml_gpu_effects_ml_segmentation_blur_gl_effect.py` - Tests
3. `docs/effects/ml_gpu_effects_ml_segmentation_blur_gl_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Segmentation-based blur respects object boundaries
- ✅ Zero safety rail violations
- ✅ Works with real depth maps and video
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
