# P3-EXT084: ML GPU Effects ML Depth Estimation Effect

## What This Module Does
Performs depth estimation using GPU-accelerated machine learning models, generating depth maps from 2D video input with optional depth refinement and temporal smoothing for high-quality depth estimation in real-time.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "ML GPU Effects ML Depth Estimation Effect",
    "id": "P3-EXT084",
    "category": "depth_effects",
    "description": "GPU-accelerated depth estimation using ML models with async inference",
    "inputs": ["video"],
    "outputs": ["depth"],
    "priority": 0,
    "dependencies": ["MLGPUEngine"],
    "test_coverage": 85
}
```

### Parameters
- `model_name` (str): Depth estimation model: "midas", "dpt", "boosted_depth", "custom"
- `input_resolution` (int): Model input resolution (256-1024, default: 512)
- `output_resolution` (int): Output depth resolution (same as input, 2x, default: 1x)
- `temporal_smoothing` (float): Temporal smoothing factor (0.0-1.0, default: 0.3)
- `confidence_threshold` (float): Depth confidence threshold (0.0-1.0, default: 0.5)
- `refinement_passes` (int): Number of refinement passes (0-3, default: 1)
- `async_inference` (bool): Use async inference (default: True)
- `gpu_memory_limit` (float): GPU memory limit in GB (1.0-8.0, default: 4.0)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]

### Outputs
- `depth` (torch.Tensor[float]): Estimated depth buffer [B, 1, H, W] normalized 0-1

## What It Does NOT Do
- Does NOT perform real-time depth estimation at 4K resolution (performance limit)
- Does NOT support all depth estimation models (limited to supported architectures)
- Does NOT guarantee depth accuracy for all scenes (model-dependent)
- Does NOT handle depth estimation for transparent objects (limited accuracy)
- Does NOT perform depth estimation for multiple cameras (monocular only)

## Test Plan

### Unit Tests
1. `test_ml_depth_estimation_initialization()`
   - Verify METADATA constants
   - Test parameter validation (input_resolution 256-1024, refinement_passes 0-3, gpu_memory_limit 1-8)
   - Test default parameter values

2. `test_model_loading()`
   - Test valid model_name values: midas, dpt, boosted_depth, custom
   - Test model loading errors
   - Test model switching

3. `test_resolution_scaling()`
   - Test input_resolution: 256, 512, 1024
   - Test output_resolution: 1x, 2x
   - Verify resolution scaling quality

4. `test_temporal_smoothing()`
   - Test temporal_smoothing: 0.0, 0.3, 1.0
   - Verify temporal coherence
   - Test smoothing artifacts

5. `test_confidence_threshold()`
   - Test confidence_threshold: 0.0, 0.5, 1.0
   - Verify confidence filtering
   - Test threshold impact

6. `test_refinement_passes()`
   - Test refinement_passes: 0, 1, 3
   - Verify depth quality improvement
   - Test refinement performance impact

7. `test_async_inference()`
   - Enable/disable async_inference
   - Verify non-blocking inference
   - Test async queue management

8. `test_gpu_memory_management()`
   - Test gpu_memory_limit: 1.0, 4.0, 8.0
   - Verify memory allocation respects limit
   - Test OOM handling

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with input_resolution=512
   - Verify FPS ≥ 60 on test hardware
   - Monitor GPU memory < gpu_memory_limit

2. `test_real_video_depth_estimation()`
   - Feed real video from various sources
   - Verify depth estimation produces reasonable results
   - Test with different scene types (indoor, outdoor, people, objects)

3. `test_model_comparison()`
   - Test all model_name options
   - Compare depth quality and performance
   - Identify best model for use case

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing video
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `MLGPUEngine` from VJlive-2
- Implement depth estimation using pre-trained models (MiDaS, DPT)
- Support async inference with CUDA streams
- Add temporal smoothing for coherence
- Implement depth refinement with bilateral filter or similar

### Performance Optimizations
- Use TensorRT for optimized inference
- Implement async CUDA streams for non-blocking execution
- Use mixed precision (FP16) for speed
- Cache model outputs for temporal smoothing

### Memory Management
- Model size: ~100-500MB per model
- Inference buffers: batch_size × input_resolution²
- Output depth buffer: H × W × 4 bytes
- Profile GPU memory, enforce gpu_memory_limit
- Free unused models from cache

### Safety Rails
- Enforce input_resolution 256-1024, refinement_passes 0-3
- Clamp gpu_memory_limit to [1.0, 8.0]
- Validate model_name and confidence_threshold
- Fallback to CPU inference if GPU unavailable

## Deliverables
1. `src/vjlive3/effects/ml_gpu_effects_ml_depth_estimation_effect.py` - Main effect
2. `tests/effects/test_ml_gpu_effects_ml_depth_estimation_effect.py` - Tests
3. `docs/effects/ml_gpu_effects_ml_depth_estimation_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p with input_resolution=512 on RTX 4070 Ti Super
- ✅ Depth estimation quality comparable to MiDaS/DPT
- ✅ Zero safety rail violations
- ✅ Works with real video input
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
