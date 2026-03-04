# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT011_background_subtraction.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT011 — background_subtraction (BackgroundSubtractionEffect)

**What This Module Does**

The `BackgroundSubtractionEffect` module implements a real-time motion detection system using background subtraction algorithms. It maintains a statistical model of the static background scene and compares each incoming frame against this model to identify foreground pixels (moving objects). The effect outputs a difference mask where pixel intensity indicates the likelihood of motion, which can be used for VJing applications like automatic mask generation, motion-triggered effects, or interactive installations.

The implementation supports two operational modes:
1. **OpenCV-based**: Uses OpenCV's `cv2.createBackgroundSubtractorMOG2()` or `cv2.createBackgroundSubtractorKNN()` for robust, adaptive background modeling with shadow detection, noise reduction, and automatic model updates.
2. **Fallback mode**: When OpenCV is unavailable, uses a simple frame differencing algorithm with configurable threshold and blur to provide basic motion detection.

The effect is designed as a CPU-bound processor (not GPU-accelerated) that operates on numpy arrays directly. It integrates into VJLive3's effects pipeline as a standard effect node, accepting input frames and producing motion masks that can feed into subsequent effects (e.g., masking, colorization, or glitch activation based on motion).

**What This Module Does NOT Do**

- Does NOT perform object tracking or classification—it only provides per-pixel motion likelihood
- Does NOT handle video I/O, camera capture, or file decoding—it processes frames provided by the pipeline
- Does NOT implement advanced computer vision features like optical flow, pose estimation, or segmentation
- Does NOT provide GPU acceleration—processing happens on CPU via numpy/OpenCV
- Does NOT store or persist background models across sessions—state is reset when the effect is disposed
- Does NOT handle multi-threading internally—the pipeline must manage thread safety if needed
- Does NOT include built-in visualization of the mask (e.g., colorizing motion)—outputs raw difference values; visualization should be done by a separate effect

---

## Detailed Behavior and Parameter Interactions

### Algorithm Selection (`use_opencv`)

The effect can operate in two modes:
- **OpenCV mode (`use_opencv=True`)**: Creates a `cv2.BackgroundSubtractorMOG2` (default) or `cv2.BackgroundSubtractorKNN` instance. These algorithms maintain a running mixture of Gaussians for each pixel, adapt to lighting changes, detect shadows, and handle gradual background changes (e.g., moving shadows, swaying trees). The subtractor's `apply()` method returns a foreground mask where 255 = moving object, 128 = shadow, 0 = background.
- **Fallback mode (`use_opencv=False`)**: Implements a simple running average background model. The background is initialized to the first frame (or a pre-defined color if no frame seen). For each new frame, the background is updated with a learning rate: `background = alpha * frame + (1-alpha) * background`. The foreground mask is computed as `abs(frame - background) > threshold`, optionally blurred to reduce noise.

### Background History (`history_frames`)

This parameter controls the length of the background model's memory:
- **OpenCV mode**: Maps to the `history` parameter of MOG2/KNN (default 500 in OpenCV, but we use 50 as per spec). Higher values make the background model more stable and resistant to false positives from temporary occlusions, but slower to adapt to genuine background changes (e.g., a parked car driving away). Lower values make the model more agile but prone to false positives from slow-moving objects.
- **Fallback mode**: Determines the size of the frame buffer used to compute the running average. A history of 50 means the background is an average of the last 50 frames (or exponentially weighted with a corresponding alpha). Implementation detail: `alpha = 1.0 / (history_frames + 1)`.

### Detection Threshold (`threshold`)

The threshold determines the sensitivity of motion detection:
- **OpenCV mode**: Maps to the `varThreshold` parameter of MOG2/KNN (default 16 in OpenCV). This is the squared Mahalanobis distance threshold for classifying a pixel as foreground. Higher values reduce false positives but may miss subtle motion. The legacy test uses a normalized 0-1 scale, so the implementation should map `threshold` (0-1) to OpenCV's internal range (e.g., `varThreshold = threshold * 100`).
- **Fallback mode**: Directly used as the absolute pixel difference threshold in grayscale space. For a uint8 image, `threshold` should be in [0, 255]. The legacy test suggests a normalized 0-1 scale, so the implementation should map: `pixel_threshold = threshold * 255`.

### Silhouette Color and Visualization

The legacy test references `silhouetteColor_0`, `silhouetteColor_1`, `silhouetteColor_2` (RGB components) and an `opacity` parameter. This suggests the effect can overlay the motion mask on the original frame with a configurable color and alpha. However, the skeleton spec's `process_frame()` returns a motion-difference image, not a composited result. This discrepancy needs resolution:
- **Option A**: The effect returns a single-channel mask (0-255) where higher values indicate stronger motion. The `silhouetteColor` and `opacity` are used by a separate compositing effect.
- **Option B**: The effect returns an RGB image where the silhouette is colored and blended over the original frame according to `opacity` and `silhouetteColor`.

Given the skeleton spec's description ("motion-difference image"), Option A is more likely. The `silhouetteColor` parameters may be vestigial from a previous UI design and can be omitted from the VJLive3 implementation, or they can be used to colorize the mask if the effect is extended to output RGB.

### Effect Mode (`effectMode`)

The legacy test sets `effectMode` to 1. This likely switches between different visualization or processing modes:
- Mode 0: Raw difference mask (grayscale)
- Mode 1: Colored silhouette overlay (using `silhouetteColor` and `opacity`)
- Mode 2: Binary mask (thresholded to 0/255)
- Mode 3: Inverted mask (background as foreground)

Since the skeleton spec doesn't mention `effectMode`, it may be an internal detail that can be omitted or simplified. The VJLive3 implementation can focus on producing a clean motion mask and leave visualization to downstream effects. The `effectMode` parameter can be omitted from the initial implementation.

### Blur (`blur`)

The legacy test includes a `blur` parameter (set to 2.0). This is a Gaussian blur applied to the difference mask to reduce noise and speckles. The blur radius should be an odd integer (e.g., 3, 5, 7) corresponding to kernel size. A value of 2.0 maps to a 5x5 kernel (`kernel_size = 2 * int(blur) + 1`). This parameter is important for smoothing the mask before further processing.

### Edge Cases and Boundary Behavior

- **First frame**: When no background model exists, the first frame initializes the background (fallback mode) or OpenCV's subtractor returns all zeros. The effect should document this behavior.
- **No motion**: Static scene produces an all-zero mask (or near-zero noise).
- **Sudden lighting change**: Causes false positives. OpenCV's MOG2 handles this reasonably; fallback mode struggles. This is a known limitation.
- **Frame size changes**: If input frame size changes, the background model must be reset. The effect should detect this and reinitialize automatically.
- **Parameter validation**: `history_frames` ≥ 1; `threshold` ≥ 0; `blur` ≥ 0. The `use_opencv` flag is read-only after initialization (cannot switch modes without resetting).
- **Memory usage**: For 1920×1080, MOG2 uses ~24-40 MB; fallback uses ~8 MB. Acceptable for desktop but heavy for embedded devices.

---

## Algorithm Details

### OpenCV MOG2/KNN

The MOG2 (Mixture of Gaussians) algorithm models each pixel as a mixture of 3-5 Gaussian distributions. It uses a Bayesian decision criterion to determine the number of components and updates the model with each new frame. Key parameters:
- `history`: How many frames to use for background model (our `history_frames`)
- `varThreshold`: Squared Mahalanobis distance threshold for foreground classification (mapped from our `threshold`)
- `detectShadows`: Should be True to detect shadows (returns 128 for shadow pixels)

KNN (K-Nearest Neighbors) uses a different approach but similar interface.

### Fallback Running Average

The fallback implements an exponential moving average:
```
alpha = 1.0 / (history_frames + 1)
background = alpha * frame + (1 - alpha) * background
mask = np.abs(frame - background) > (threshold * 255)
```
This is simple but less robust to lighting changes and shadows.

---

## Integration

### VJLive3 Pipeline Integration

The `BackgroundSubtractionEffect` integrates as a frame processor in the effects pipeline:

```
[Video Source] → [BackgroundSubtractionEffect] → [Mask Visualization] → [Output]
```

**Position**: Place early in the chain so subsequent effects can use the motion mask to modulate behavior (e.g., glitch intensity, color shift).

**Frame Processing**:

1. Pipeline calls `effect.process_frame(frame)` for each frame.
2. Effect converts frame to grayscale if needed (OpenCV requires single-channel; fallback can process RGB by averaging channels: `gray = np.mean(frame, axis=2)`).
3. Background subtractor (or fallback) computes the foreground mask.
4. If `blur > 0`, apply Gaussian blur: `cv2.GaussianBlur(mask, (kernel_size, kernel_size), 0)` in OpenCV mode; in fallback, use a simple box blur via `cv2.blur` if OpenCV is available for blur only, or implement a manual convolution with numpy (slower).
5. Return mask as numpy array with same spatial dimensions as input. The output is single-channel (H, W) with values 0-255 (uint8). If the input was RGB, the effect may return a 3-channel mask by stacking: `np.stack([mask]*3, axis=2)`, but this is optional.

**Parameter Configuration**: The effect's `__init__(param: dict)` accepts a configuration dictionary. Implementation should extract:
- `use_opencv` (bool, default True) — read-only after init
- `history_frames` (int, default 50, min 1, max 500)
- `threshold` (float, default 0.25, min 0.0, max 1.0) — normalized, internally mapped to 0-255 or OpenCV's varThreshold
- `blur` (float, default 2.0, min 0.0, max 10.0) — kernel radius, converted to odd integer
- `opacity` (float, default 1.0) — optional, for downstream compositing
- `silhouette_color` (list[float], default [1.0, 0.0, 0.0]) — optional, for downstream colorization

The skeleton spec's parameter table is simplified and doesn't include `blur`, `opacity`, `silhouette_color`. These should be added to the spec's "Inputs and Outputs" table.

**State Management**:
- `self.subtractor`: OpenCV BackgroundSubtractor instance (or None in fallback)
- `self.background`: numpy array for fallback running average
- `self.frame_count`: number of frames processed
- `self.last_frame_shape`: to detect resolution changes

`reset()` clears this state, reinitializing the background model. Useful when switching scenes or after a hard cut.

**Dependency Handling**:
- At `__init__`, attempt to import `cv2`. If unavailable, set `self.use_opencv = False` and log a warning.
- If `use_opencv=True` in params but OpenCV is missing, fall back to CPU mode and log an error.
- If `numpy` is missing, raise ImportError at import time.

---

## Performance

### Computational Cost

- **OpenCV mode**: Highly optimized C++ code. 1920×1080 frame takes ~5-15 ms on modern CPU (Intel i5/i7, AMD Ryzen). Real-time capable at 60fps (16.7ms budget). May struggle on low-power embedded CPUs (Raspberry Pi, Orange Pi). Memory bandwidth is the main bottleneck.
- **Fallback mode**: Pure numpy operations (frame averaging, absolute difference, Gaussian blur). Can be 2-5× slower than OpenCV. Gaussian blur is expensive if implemented manually. A simple box blur or median filter could be used instead for speed.

### Memory Usage

- **OpenCV mode**: MOG2 allocates internal buffers for each pixel's Gaussian mixture. Roughly 3-5 floating-point values per pixel × number of Gaussians (typically 3-5). For 1080p (~2M pixels), this is ~24-40 MB. The `history_frames` parameter does not directly control memory—it controls how many frames are used to update the model, but the model size is fixed per algorithm.
- **Fallback mode**: Stores one background frame (same size as input, ~8 MB for 1080p uint8). If using a ring buffer for exact history, additional memory proportional to `history_frames` × frame size.

### Optimization Strategies

1. **Resolution scaling**: Process at lower resolution (e.g., 640×480) and upscale mask if needed. The effect could accept a `scale_factor` parameter or the pipeline could resize frames before processing.
2. **Region of interest (ROI)**: Process only a portion of the frame if motion is relevant only in a specific area. The effect could accept an optional `roi` parameter (x, y, w, h).
3. **Frame skipping**: For very high frame rates, process every Nth frame and interpolate. Not recommended for real-time VJing but could be used for offline analysis.
4. **SIMD and vectorization**: Ensure numpy operations use optimized BLAS/OpenCV libraries (Intel IPP, OpenBLAS). Use numpy's built-in functions (`np.abs`, `np.mean`) which are already vectorized.
5. **Early exit**: If the frame hasn't changed significantly from the previous one (e.g., using a quick hash or sum of absolute differences), skip full processing and return the previous mask. Saves compute when scene is static.

### Platform-Specific Considerations

- **Desktop**: OpenCV typically available via `pip install opencv-python`. Prefer OpenCV mode for best quality and performance.
- **Embedded (OPi5, Raspberry Pi)**: OpenCV may be available but slower due to limited SIMD. Fallback mode might be faster if OpenCV is poorly optimized. The effect could auto-detect performance at startup and choose the fastest mode.
- **No OpenCV**: Fallback mode must work with only numpy. Should not rely on `scipy` or `PIL`. Gaussian blur can be approximated with a simple box blur repeated a few times, or omitted if `blur=0`.

### Performance Testing Recommendations

- Benchmark both modes (OpenCV vs fallback) at various resolutions (480p, 720p, 1080p, 4K)
- Measure time per frame and memory usage with `history_frames` = 10, 50, 100
- Test with static scenes (baseline) and with high motion (peak)
- Verify `reset()` doesn't cause memory leaks (use `tracemalloc` or `valgrind`)
- Check frame rate stability over long runs (no memory growth)

---

## Test Plan (Expanded)

The existing test plan is minimal. Expand with:

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect instantiates even if OpenCV missing; falls back to CPU mode without crashing |
| `test_basic_operation_opencv` | With OpenCV available, process_frame returns valid mask (uint8, same H/W as input) |
| `test_basic_operation_fallback` | Without OpenCV, fallback mode produces plausible mask (non-zero values on motion) |
| `test_parameter_validation` | Invalid `history_frames` (≤0) raises ValueError; invalid `threshold` (<0) raises ValueError |
| `test_reset_clears_state` | After reset(), background model is reinitialized; subsequent frames don't carry old state |
| `test_resolution_change` | Changing frame size automatically triggers reset and continues processing |
| `test_motion_detection` | Synthetic test: two frames with known pixel differences produce mask with those differences |
| `test_static_scene` | With static input (identical frames), output mask is all zeros (or near-zero noise) |
| `test_threshold_sensitivity` | Lower threshold yields more foreground pixels; higher threshold yields fewer |
| `test_history_adaptation` | With a static background then a change, the model eventually adapts if change becomes permanent |
| `test_blur_effect` | When blur > 0, output mask is smoother (fewer isolated pixels) |
| `test_opencv_fallback_switch` | If OpenCV becomes unavailable after init, effect continues in fallback mode (graceful degradation) |

**Minimum coverage**: 80% before task is marked done.

---

## Open Questions and Research Findings

