# P3-EXT083: ML GPU Effects ML Base Async Effect

## What This Module Does
Provides an asynchronous base class for ML GPU effects, enabling non-blocking machine learning inference on GPU with depth integration, allowing ML-powered visual effects to run concurrently with the main rendering pipeline.

## Public Interface

### METADATA
```python
METADATA = {
    "name": "ML GPU Effects ML Base Async Effect",
    "id": "P3-EXT083",
    "category": "depth_effects",
    "description": "Asynchronous ML inference base for GPU-accelerated depth-aware effects",
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "priority": 0,
    "dependencies": ["DepthBuffer", "MLGPUEngine"],
    "test_coverage": 85
}
```

### Parameters
- `model_name` (str): ML model name (e.g., "style_transfer", "depth_estimation", "segmentation")
- `async_batch_size` (int): Async inference batch size (1-8, default: 1)
- `inference_timeout` (float): Max inference wait time in seconds (0.01-1.0, default: 0.1)
- `fallback_effect` (str): Fallback effect when ML unavailable: "passthrough", "blur", "pixelate"
- `depth_ml_mapping` (str): How depth affects ML: "mask", "weight", "bias", "none"
- `gpu_memory_limit` (float): GPU memory limit in GB (1.0-8.0, default: 4.0)
- `model_cache_size` (int): Number of models to cache (1-10, default: 3)

### Inputs
- `video` (torch.Tensor[uint8]): Input video frames [B, 3, H, W]
- `depth` (torch.Tensor[float]): Depth buffer [B, 1, H, W] normalized 0-1

### Outputs
- `video` (torch.Tensor[uint8]): ML-processed output [B, 3, H, W]

## What It Does NOT Do
- Does NOT perform real-time ML training (inference only)
- Does NOT support all ML model formats (limited to ONNX/TensorRT)
- Does NOT guarantee inference latency (async may drop frames)
- Does NOT preserve original video when ML modifies
- Does NOT handle model updates automatically (static models)

## Test Plan

### Unit Tests
1. `test_ml_async_base_initialization()`
   - Verify METADATA constants
   - Test parameter validation (async_batch_size 1-8, inference_timeout 0.01-1.0, gpu_memory_limit 1-8)
   - Test default parameter values

2. `test_model_loading()`
   - Test valid model_name values
   - Test model loading errors
   - Test model caching

3. `test_async_inference_pipeline()`
   - Test async_batch_size: 1, 4, 8
   - Verify non-blocking inference
   - Test inference queue management

4. `test_inference_timeout()`
   - Test inference_timeout: 0.01, 0.1, 1.0
   - Verify timeout behavior
   - Test fallback on timeout

5. `test_fallback_effect()`
   - Test all fallback_effect options: passthrough, blur, pixelate
   - Verify fallback triggers correctly
   - Test fallback quality

6. `test_depth_ml_mapping()`
   - Test all depth_ml_mapping modes: mask, weight, bias, none
   - Create synthetic depth map
   - Verify depth influences ML output

7. `test_gpu_memory_management()`
   - Test gpu_memory_limit: 1.0, 4.0, 8.0
   - Verify memory allocation respects limit
   - Test OOM handling

8. `test_model_cache()`
   - Test model_cache_size: 1, 3, 10
   - Verify model caching and eviction
   - Test cache hit rates

### Integration Tests
1. `test_full_pipeline_60fps()`
   - Process 1000 frames at 1920x1080 with async_batch_size=1
   - Verify FPS ≥ 60 on test hardware
   - Monitor GPU memory < gpu_memory_limit

2. `test_real_depth_ml_inference()`
   - Feed real depth map from MiDaS/DPT
   - Verify depth-based ML effects
   - Test with various ML models

3. `test_async_performance()`
   - Test async_batch_size scaling
   - Measure inference latency and throughput
   - Identify bottlenecks

4. `test_safety_rails_compliance()`
   - Verify no silent failures on invalid inputs
   - Test error handling for missing depth/ML
   - Ensure all exceptions are logged

## Implementation Notes

### Architecture
- Build on `DepthEffect` base class from P3-VD35
- Integrate with `MLGPUEngine` from VJlive-2
- Implement async inference queue with worker threads
- Use CUDA streams for concurrent GPU execution
- Support ONNX and TensorRT models
- Implement model caching and memory management

### Performance Optimizations
- Use async CUDA streams for non-blocking inference
- Implement batch inference for throughput
- Pre-allocate GPU memory pools
- Use TensorRT for optimized inference

### Memory Management
- Model cache: model_cache_size × model_size (varies)
- Inference buffers: batch_size × frame_size
- Profile GPU memory, enforce gpu_memory_limit
- Free unused models from cache

### Safety Rails
- Enforce async_batch_size ≤ 8, inference_timeout ≥ 0.01
- Clamp gpu_memory_limit to [1.0, 8.0]
- Validate fallback_effect and depth_ml_mapping
- Fallback to CPU inference if GPU unavailable

## Deliverables
1. `src/vjlive3/effects/ml_gpu_effects_ml_base_async_effect.py` - Main effect
2. `tests/effects/test_ml_gpu_effects_ml_base_async_effect.py` - Tests
3. `docs/effects/ml_gpu_effects_ml_base_async_effect.md` - Documentation
4. Update `MODULE_MANIFEST.md`

## Success Criteria
- ✅ All unit tests pass (≥ 85% coverage)
- ✅ 60 FPS at 1080p on RTX 4070 Ti Super
- ✅ Async inference does not block main pipeline
- ✅ Zero safety rail violations
- ✅ Works with real depth maps
- ✅ Clean code: ≤ 750 lines, no stubs, full type hints
