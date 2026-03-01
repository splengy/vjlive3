# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT002_AdaptiveContrastEffect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT002 — AdaptiveContrastEffect

## Description

The `AdaptiveContrastEffect` module implements an advanced adaptive contrast enhancement algorithm that dynamically adjusts brightness and contrast based on local pixel intensity distributions within a video frame. This effect analyzes each pixel's neighborhood to determine local contrast characteristics and applies targeted adjustments to enhance visual detail while preserving important image features. The algorithm operates by computing local histograms within a sliding window, identifying intensity variations, and applying contrast modifications that are proportional to the detected local differences.

The module replaces the legacy VJlive `adaptive_contrast_effect` with significant improvements in performance, artifact reduction, and real-time responsiveness. By leveraging modern computational techniques and optimized data structures, it maintains consistent frame rates even at high resolutions while minimizing common artifacts like halos and edge overshoot. The output is a processed video frame with enhanced dynamic range that preserves natural appearance while making subtle but effective contrast improvements suitable for live visual effects in VJ performances.

## What This Module Does

- **Adaptive Contrast Enhancement**: Dynamically adjusts brightness and contrast based on local pixel intensity distributions
- **Local Neighborhood Analysis**: Uses sliding window approach to analyze pixel neighborhoods for contrast detection
- **Real-time Processing**: Maintains consistent performance through optimized histogram computation
- **Artifact Reduction**: Implements edge-aware processing to minimize halo effects and overshoot artifacts
- **Dynamic Range Enhancement**: Improves visual detail while preserving natural appearance
- **Legacy Integration**: Replaces VJlive v1 `adaptive_contrast_effect` with improved performance characteristics

## What This Module Does NOT Do

- Handle file I/O or persistent storage operations
- Process audio streams or provide sound-reactive capabilities
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context

---

## Detailed Behavior

### Adaptive Contrast Enhancement Pipeline

The effect processes each frame through a series of stages designed to enhance local contrast while avoiding common artifacts:

1. **Frame Validation**: Verify input frame is valid (shape, dtype, range)
2. **Local Statistics Computation**: For each pixel, compute mean and standard deviation within a sliding window
3. **Contrast Mapping**: Apply adaptive transformation based on local statistics
4. **Edge-Aware Smoothing**: Reduce artifacts near edges using gradient information
5. **Clipping and Normalization**: Ensure output stays within valid range [0, 1]
6. **Optional Clamping**: Apply additional clamping if enabled

### Algorithm: Local Contrast Enhancement

The core algorithm uses a modified version of adaptive histogram equalization (AHE) with contrast limiting to avoid over-amplification:

```python
def adaptive_contrast(frame, window_size=16, clip_limit=2.0, enable_clamp=True):
    """
    Apply adaptive contrast enhancement.
    
    Args:
        frame: Input frame (HxWxC), float [0, 1] or uint8 [0, 255]
        window_size: Size of sliding window (must be power of 2, 4-64)
        clip_limit: Contrast limiting factor (higher = more contrast)
        enable_clamp: Whether to clamp output to [0, 1]
    
    Returns:
        Enhanced frame (same shape as input)
    """
    # Convert to float if needed
    if frame.dtype == np.uint8:
        frame = frame.astype(np.float32) / 255.0
    
    # Compute local mean and std using uniform filter
    kernel = np.ones((window_size, window_size), dtype=np.float32) / (window_size ** 2)
    
    # Process each channel independently
    output = np.zeros_like(frame)
    for c in range(frame.shape[2]):
        channel = frame[:, :, c]
        
        # Local mean
        mean = scipy.ndimage.convolve(channel, kernel, mode='reflect')
        
        # Local variance/std
        sqr = scipy.ndimage.convolve(channel ** 2, kernel, mode='reflect')
        variance = sqr - mean ** 2
        std = np.sqrt(np.maximum(variance, 1e-8))
        
        # Adaptive contrast stretching
        # Avoid division by zero
        std = np.maximum(std, 1e-8)
        
        # Apply contrast enhancement
        enhanced = (channel - mean) / std
        
        # Apply contrast limiting (clip extreme values)
        if clip_limit > 0:
            clip_threshold = clip_limit * np.median(std)
            enhanced = np.clip(enhanced, -clip_threshold, clip_threshold)
            # Renormalize after clipping
            enhanced = (enhanced - enhanced.min()) / (enhanced.max() - enhanced.min() + 1e-8)
        
        # Scale to original dynamic range
        enhanced = mean + enhanced * std
        
        # Optional: preserve overall brightness
        enhanced = np.clip(enhanced, 0.0, 1.0)
        
        output[:, :, c] = enhanced
    
    if enable_clamp:
        output = np.clip(output, 0.0, 1.0)
    
    return output
```

### Edge-Aware Processing

To minimize halos and overshoot near edges, the algorithm incorporates gradient information:

```python
# Compute gradients
grad_x = np.gradient(channel, axis=1)
grad_y = np.gradient(channel, axis=0)
gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

# Edge detection threshold
edge_threshold = 0.1  # Adjustable parameter

# Reduce contrast enhancement near strong edges
edge_factor = 1.0 / (1.0 + gradient_magnitude / edge_threshold)
enhanced = mean + enhanced * std * edge_factor
```

### Performance Optimizations

The implementation uses several techniques to maintain real-time performance:

- **Sliding Window Histogram**: Instead of recomputing histograms for each pixel, use integral histograms or running sums
- **Downsampling for Statistics**: Compute local statistics at lower resolution and upsample
- **Vectorized Operations**: Leverage NumPy vectorization for all array operations
- **Memory Pre-allocation**: Reuse buffers across frames to avoid allocation overhead
- **Parallel Processing**: Optionally use multi-threading for large frames

### Artifact Reduction

Common artifacts and their mitigation:

| Artifact | Cause | Mitigation |
|----------|-------|------------|
| Halos | Over-enhancement near edges | Edge-aware processing, gradient-based reduction |
| Overshoot | Clipping after contrast stretch | Smooth clipping, gradual roll-off |
| Noise Amplification | Low local std → high gain | Minimum std threshold, noise detection |
| Color Shifts | Independent channel processing | Luminance-preserving mode, HSV space |
| Blocking | Small window size | Minimum window size, overlap processing |

---

## Public Interface

```python
class AdaptiveContrastEffect:
    def __init__(self, window_size: int = 16, clip_limit: float = 2.0, enable_clamp: bool = True) -> None: ...
    def set_window_size(self, size: int) -> None: ...
    def set_clip_limit(self, limit: float) -> None: ...
    def set_enable_clamp(self, enable: bool) -> None: ...
    def get_parameters(self) -> dict: ...
    def set_parameters(self, params: dict) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, uint8 [0-255] or float [0-1]) |
| **Output** | `np.ndarray` | Enhanced frame (same shape and dtype as input) |

---

## State Management

**Persistent State:**
- `_window_size: int` — Sliding window size (power of 2, 4-64)
- `_clip_limit: float` — Contrast limiting factor (0-10)
- `_enable_clamp: bool` — Whether to clamp output to valid range
- `_kernel: Optional[np.ndarray]` — Pre-computed averaging kernel
- `_scratch_buffer: Optional[np.ndarray]` — Reusable buffer for intermediate results

**Per-Frame:**
- Validate input frame
- Convert to float if needed
- For each channel:
  - Compute local mean via convolution
  - Compute local variance/std via convolution
  - Apply adaptive contrast transformation
  - Apply edge-aware smoothing
  - Apply clipping/clamping
- Convert back to original dtype
- Return output

**Initialization:**
- Validate `window_size` is power of 2 between 4 and 64
- Create averaging kernel of shape `(window_size, window_size)`
- Allocate scratch buffer at maximum expected frame size
- Store original dtype preference

**Cleanup:**
- Free scratch buffer
- Delete kernel
- Set state to None

---

## GPU Resources

This effect is **CPU-only** and does not use GPU resources.

**Memory Budget (1920×1080, float32):**
- Input frame: ~8.3 MB
- Output frame: ~8.3 MB
- Scratch buffer: ~8.3 MB
- Kernel: ~4 KB
- Total: ~25 MB (light)

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `window_size` | int | 16 | 4-64 (power of 2) | Size of sliding window for local statistics (pixels) |
| `clip_limit` | float | 2.0 | 0.0-10.0 | Contrast limiting factor (prevents over-enhancement) |
| `enable_clamp` | bool | True | N/A | Whether to clamp output to [0, 1] range |

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Invalid frame shape | `ValueError` | Ensure frame is HxWxC |
| Invalid frame dtype | `ValueError` | Convert to float32 or uint8 |
| Window size not power of 2 | `ValueError` | Use nearest valid size (4,8,16,32,64) |
| Window size out of bounds | `ValueError` | Clamp to [4, 64] |
| Out of memory | `MemoryError` | Reduce resolution or window size |
| SciPy not available | `ImportError` | Fall back to pure NumPy implementation |

---

## Thread Safety

The effect is **not thread-safe**. While the algorithm itself is stateless per frame, the scratch buffer and kernel are shared state. Concurrent `process_frame()` calls will corrupt buffers. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (1920×1080):**
- Local mean computation: ~8-12 ms
- Local std computation: ~8-12 ms
- Contrast transformation: ~5-8 ms
- Edge-aware smoothing: ~4-6 ms
- Total: ~25-38 ms (26-40 fps) on mid-range CPU (4-8 cores)

**Expected Frame Time (640×480):**
- Total: ~4-8 ms (125-250 fps)

**Optimization Strategies:**
- Increase window size (fewer windows = less computation)
- Disable edge-aware smoothing (if halos not problematic)
- Use downsampling for statistics (compute at 1/2 or 1/4 resolution)
- Use integral images for O(1) window statistics
- Process in YUV/HSV space instead of RGB (fewer channels)
- Use Numba/Cython for critical loops

---

## Integration Checklist

- [ ] SciPy installed (optional, fallback to pure NumPy)
- [ ] Window size validated (power of 2, 4-64)
- [ ] Clip limit configured
- [ ] Clamping enabled/disabled as needed
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent |
| `test_basic_operation` | Core function returns expected output with valid input frame and default parameters |
| `test_error_handling` | Invalid frame shape or dtype raises correct exception |
| `test_cleanup` | No memory leaks during repeated processing cycles |
| `test_threshold_range` | Threshold values outside [0.0, 1.0] raise validation error |
| `test_window_size_bounds` | Invalid window sizes rejected with clear message |
| `test_edge_preservation` | Sharp transitions preserved while smoothing gradual transitions |
| `test_real_time_performance` | Maintains 30+ FPS for 1080p input on mid-range hardware |
| `test_memory_efficiency` | Memory usage remains constant during extended processing sessions |
| `test_parameter_interactions` | Multiple parameter changes work correctly without interference |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P3-EXT002: AdaptiveContrastEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `core/effects/__init__.py` — Plugin registry entry for `adaptive_contrast`
- `plugins/vcv_effects.py` (implied) — Original VJLive v1 implementation location

Design decisions inherited:
- Effect name: `adaptive_contrast`
- Class name: `AdaptiveContrastEffect`
- Category: Color/Video effects
- Parameters: window_size, clip_limit, enable_clamp (inferred from algorithm)
- CPU-only implementation (no GPU acceleration in legacy)
- Replaces VJLive v1 `adaptive_contrast_effect` with improved performance

---

## Notes for Implementers

1. **Core Concept**: Adaptive contrast enhancement improves local contrast in an image by analyzing pixel neighborhoods. Unlike global contrast adjustment, this technique adapts to local content, enhancing details in both dark and bright regions without over-exposing or under-exposing.

2. **Algorithm Choice**: The spec describes a local mean/std normalization approach (similar to Contrast Limited Adaptive Histogram Equalization - CLAHE). This is a proven technique that balances enhancement with artifact control.

3. **Window Size**: Must be a power of 2 for performance (enables bit shifts instead of division). Typical values: 8, 16, 32. Smaller windows = more local adaptation but more noise/halos. Larger windows = smoother but less adaptive.

4. **Contrast Limiting**: Critical to prevent over-amplification in flat regions. The clip_limit parameter controls how much contrast can be boosted. Typical values: 1.0-4.0.

5. **Edge-Aware Processing**: To avoid halos near edges, reduce enhancement where gradients are strong. This preserves edge sharpness while still enhancing textures.

6. **Performance**: The algorithm is O(H×W×window²) naively. Use separable filters or integral images to reduce to O(H×W). The implementation above uses convolution which is optimized in SciPy/NumPy.

7. **Memory**: Pre-allocate buffers to avoid per-frame allocation. Reuse scratch buffers across frames.

8. **Data Types**: Support both uint8 [0-255] and float32 [0-1]. Convert to float for processing, then back to original dtype.

9. **Testing**: Use standard test images (Lena, Mandrill) with known contrast issues. Measure PSNR, SSIM to ensure no degradation. Test with synthetic gradients, edges, textures.

10. **PRESETS**:
    ```python
    PRESETS = {
        "default": {"window_size": 16, "clip_limit": 2.0, "enable_clamp": True},
        "subtle": {"window_size": 32, "clip_limit": 1.5, "enable_clamp": True},
        "aggressive": {"window_size": 8, "clip_limit": 3.0, "enable_clamp": True},
        "no_halo": {"window_size": 16, "clip_limit": 2.0, "enable_clamp": True, "edge_aware": True},
        "fast": {"window_size": 32, "clip_limit": 2.0, "enable_clamp": True, "edge_aware": False},
    }
    ```

11. **Fallback**: If SciPy is not available, implement uniform filter using pure NumPy (slower but functional).

12. **Future Extensions**:
    - Add support for YUV/HSV processing (more perceptually uniform)
    - Add temporal smoothing across frames
    - Add region-of-interest masking
    - Add GPU acceleration via CUDA/OpenCL
    - Add multi-scale processing (pyramid)

---

## Easter Egg Idea

When `window_size` is set exactly to 6.66, `clip_limit` to exactly 6.66, and `enable_clamp` is toggled exactly 666 times during a single frame, the Adaptive Contrast Effect enters a "quantum enlightenment" state where the local statistics computation reveals exactly 666 distinct contrast levels within the image, the sliding window becomes exactly 6.66 pixels wide in the quantum realm, the contrast limiting creates exactly 666% more dynamic range, the edge-aware processing detects exactly 666 edge orientations per frame, and the entire effect becomes a "contrast prayer" where every pixel's contrast is exactly 666% more enlightened than normal, creating a perfect 666×666 grid of quantum contrast that can only be perceived by achieving exactly 666 Hz brainwave resonance.

---

## References

- Adaptive Histogram Equalization: https://en.wikipedia.org/wiki/Adaptive_histogram_equalization
- CLAHE: https://en.wikipedia.org/wiki/Contrast_limited_adaptive_histogram_equalization
- Local contrast enhancement: https://www.mathworks.com/discovery/image-enhancement.html
- SciPy ndimage: https://docs.scipy.org/doc/scipy/reference/ndimage.html
- VJLive legacy: `core/effects/__init__.py` plugin registry

---

## Implementation Tips

1. **Python Implementation**:
   ```python
   import numpy as np
   from scipy import ndimage
   
   class AdaptiveContrastEffect:
       def __init__(self, window_size=16, clip_limit=2.0, enable_clamp=True):
           self.set_window_size(window_size)
           self._clip_limit = clip_limit
           self._enable_clamp = enable_clamp
           self._kernel = None
           self._scratch_buffer = None
           self._initialize_kernel()
       
       def _initialize_kernel(self):
           """Create averaging kernel for local statistics."""
           self._kernel = np.ones((self._window_size, self._window_size), dtype=np.float32)
           self._kernel /= self._window_size ** 2
       
       def set_window_size(self, size):
           """Set window size (must be power of 2, 4-64)."""
           if size not in [4, 8, 16, 32, 64]:
               raise ValueError("Window size must be power of 2 between 4 and 64")
           self._window_size = size
           self._initialize_kernel()
       
       def process_frame(self, frame):
           # Validate
           if frame.ndim != 3 or frame.shape[2] != 3:
               raise ValueError("Frame must be HxWxC")
           
           # Convert to float
           is_uint8 = frame.dtype == np.uint8
           if is_uint8:
               frame_float = frame.astype(np.float32) / 255.0
           else:
               frame_float = frame.astype(np.float32)
           
           # Allocate output
           output = np.zeros_like(frame_float)
           
           # Process each channel
           for c in range(3):
               channel = frame_float[:, :, c]
               
               # Local mean
               mean = ndimage.convolve(channel, self._kernel, mode='reflect')
               
               # Local variance/std
               sqr = ndimage.convolve(channel ** 2, self._kernel, mode='reflect')
               variance = sqr - mean ** 2
               std = np.sqrt(np.maximum(variance, 1e-8))
               
               # Adaptive contrast
               std_safe = np.maximum(std, 1e-8)
               enhanced = (channel - mean) / std_safe
               
               # Contrast limiting
               if self._clip_limit > 0:
                   clip_threshold = self._clip_limit * np.median(std)
                   enhanced = np.clip(enhanced, -clip_threshold, clip_threshold)
                   # Renormalize
                   enhanced = (enhanced - enhanced.min()) / (enhanced.max() - enhanced.min() + 1e-8)
               
               # Scale back
               enhanced = mean + enhanced * std
               
               # Edge-aware smoothing (optional)
               if self._edge_aware:
                   grad_x = np.gradient(channel, axis=1)
                   grad_y = np.gradient(channel, axis=0)
                   grad_mag = np.sqrt(grad_x**2 + grad_y**2)
                   edge_factor = 1.0 / (1.0 + grad_mag / self._edge_threshold)
                   enhanced = mean + (enhanced - mean) * edge_factor
               
               output[:, :, c] = np.clip(enhanced, 0.0, 1.0)
           
           # Apply final clamp if enabled
           if self._enable_clamp:
               output = np.clip(output, 0.0, 1.0)
           
           # Convert back
           if is_uint8:
               output = (output * 255).astype(np.uint8)
           
           return output
       
       def cleanup(self):
           self._kernel = None
           self._scratch_buffer = None
   ```

2. **Edge-Aware Smoothing**: The gradient-based reduction factor can be tuned via `edge_threshold` parameter. Lower values = more reduction near edges.

3. **Performance Tips**:
   - Use `scipy.ndimage.uniform_filter` directly instead of manual convolution
   - Consider separable filters: convolve X then Y for O(window) instead of O(window²)
   - Use `numba` to JIT compile the per-channel loop
   - Process in-place when possible to reduce memory copies

4. **Alternative Implementation**: For better performance, use integral images to compute local sums in O(1) per pixel:
   ```python
   integral = cv2.integral(channel)  # OpenCV
   # Then compute sum in window via 4 array lookups
   ```

5. **Testing Strategy**:
   - Create synthetic test images: gradients, step edges, textures
   - Measure contrast improvement using RMS contrast metric
   - Verify no clipping artifacts when `enable_clamp=False`
   - Test with extreme `clip_limit` values (0 and 10)
   - Benchmark with different window sizes

6. **Memory Management**: Pre-allocate a scratch buffer at the maximum expected frame size to avoid repeated allocations. Use `np.memmap` for very large frames if needed.

7. **Error Handling**: Validate all parameters in `__init__` and `set_*` methods. Raise clear exceptions with actionable messages.

8. **Documentation**: Document the algorithm clearly in code comments. Include references to CLAHE and local contrast enhancement.

---

## Conclusion

The AdaptiveContrastEffect provides sophisticated local contrast enhancement suitable for VJLive3 performances. By analyzing local pixel neighborhoods and applying adaptive transformations, it enhances visual detail while controlling artifacts through contrast limiting and edge-aware processing. The CPU-only implementation ensures broad compatibility while maintaining real-time performance at HD resolutions through optimized algorithms and memory management.

---
>>>>>>> REPLACE