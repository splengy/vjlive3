# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT002_AdaptiveContrastEffect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT002 — AdaptiveContrastEffect

**What This Module Does**

The `AdaptiveContrastEffect` module implements an adaptive contrast enhancement algorithm that dynamically adjusts brightness and contrast based on local pixel intensity distributions within a video frame. It replaces the legacy VJlive `adaptive_contrast_effect` with improved performance, reduced artifacts, and better real-time responsiveness in VJLive3. The output is a processed video frame with enhanced dynamic range suitable for live visual effects.

## Description

The `AdaptiveContrastEffect` provides sophisticated contrast enhancement by analyzing local neighborhoods in each frame to automatically stretch luminance ranges. Unlike global contrast adjustments that affect the entire image uniformly, this effect adapts to local brightness variations, revealing detail in both shadow and highlight regions simultaneously. The algorithm works by examining pixel intensity distributions within a configurable window around each pixel, then applying localized contrast stretching based on the local histogram.

This effect is inspired by audio dynamics processors like Mutable Instruments Streams, translating concepts of compression and expansion from audio to image processing. The `threshold` parameter controls sensitivity to local contrast changes, while `window_size` determines the analysis neighborhood size, creating a spectrum from global auto-leveling to highly localized enhancement. The result is a natural-looking contrast enhancement that preserves overall image character while bringing out hidden details in challenging lighting conditions.

---

## Public Interface

```python
class AdaptiveContrastEffect:
    def __init__(self, threshold: float = 0.1, window_size: int = 16, clamp_range: bool = True) -> None:
        """
        Initialize the adaptive contrast effect.
        
        Args:
            threshold: Minimum intensity difference to trigger contrast adjustment (0.0–1.0)
            window_size: Size of local neighborhood for intensity analysis (must be power of 2)
            clamp_range: Whether to clip output values to [0, 1] after processing
        """
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply adaptive contrast to a single video frame.
        
        Args:
            frame: Input frame as numpy array (H x W x 3 or H x W x 4)
            
        Returns:
            Processed frame with enhanced contrast (same shape and dtype as input)
        """
```

---

## What This Module Does

- Performs adaptive contrast enhancement using local pixel neighborhood analysis
- Automatically stretches luminance ranges to reveal detail in shadows and highlights
- Supports both RGB and RGBA frame formats (3 or 4 channels)
- Processes frames in real-time suitable for live VJ performance
- Uses numpy for efficient array operations with optional scipy.ndimage fallback
- Validates input frame shape and dtype before processing
- Clamps output to valid range when `clamp_range=True`
- Works with uint8 and float32 dtypes

## What This Module Does NOT Do

- Does NOT perform temporal smoothing or frame-to-frame coherence (purely spatial)
- Does NOT handle HDR values >1.0 (SDR only)
- Does NOT include noise reduction (may amplify noise in flat regions)
- Does NOT provide color grading or hue shifting (luminance-only adaptation)
- Does NOT support GPU acceleration out of the box (CPU implementation)
- Does NOT handle video I/O, file reading, or persistence
- Does NOT implement edge-aware sampling (uses uniform window)
- Does NOT provide presets or parameter automation (raw effect only)

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `threshold` | `float` | Minimum intensity difference to detect local contrast changes | 0.0 ≤ threshold ≤ 1.0 |
| `window_size` | `int` | Local neighborhood size for histogram analysis | Must be power of 2; 4 ≤ window_size ≤ 64 |
| `clamp_range` | `bool` | Whether output pixel values are clamped to [0, 1] | True or False |
| `frame` | `np.ndarray` | Input video frame (H x W x 3 or H x W x 4) | Must be uint8 or float32; shape must be valid for processing |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for array operations and histogram computation — fallback: no operation, return original frame
  - `scipy.ndimage` — used for local intensity filtering — fallback: use simple sliding window with linear interpolation
- Internal modules this depends on:
  - `vjlive3.core.frame_utils` — for frame validation and shape checks  
  - `vjlive3.effects.base_effect` — base class for effect processing pipeline

---

## Legacy Context

The `AdaptiveContrastEffect` originates from the VJlive codebase's `core/effects/analog_emulation.py` (also present in VJlive-2). In the legacy implementation, the effect was used through `AnalogContrastNode` with the following parameter mapping:

- `strength` (0.0–10.0): Overall contrast enhancement intensity
- `locality` (0.0–10.0): Size of local neighborhood for analysis
- `black_point` (0.0–10.0): Shadow adjustment level
- `white_point` (0.0–10.0): Highlight adjustment level
- `saturation` (0.0–10.0): Color saturation boost
- `detail` (0.0–10.0): Fine detail enhancement

The first-pass spec simplified this to three core parameters (`threshold`, `window_size`, `clamp_range`) to provide a more focused, easier-to-use interface. The legacy implementation used a local histogram equalization approach with configurable black and white point stretching.

**Key Implementation Details from Legacy:**
- The effect operates in luminance space (converts to YUV/YCbCr, processes Y channel, converts back)
- Uses sliding window histogram computation with optional scipy.ndimage.gaussian_filter for smoothing
- Applies contrast stretching: `output = (input - black_point) / (white_point - black_point)`
- Includes saturation preservation by applying adjustments only to luminance while maintaining chroma

## Integration

The AdaptiveContrastEffect integrates into the VJLive3 node graph as an effect node:

- **Node Type:** `ANALOG_CONTRAST` (EFFECT category)
- **Input Ports:**
  - `signal_in` (SignalType.VIDEO): Accepts RGB or RGBA frames
- **Output Ports:**
  - `signal_out` (SignalType.VIDEO): Processed frame with enhanced contrast
- **Parameter Mapping:** When used in a node graph, the node's parameters map to effect parameters:
  - Node parameter `str` → `threshold`
  - Node parameter `local` → `window_size`
  - Node parameter `black` → `black_point` (if using legacy 6-param interface)
  - Node parameter `white` → `white_point` (if using legacy 6-param interface)
  - Node parameter `sat` → `saturation` (if using legacy 6-param interface)
  - Node parameter `detail` → `detail` (if using legacy 6-param interface)

**Audio Reactivity:** This effect is NOT audio-reactive by default. It can be made audio-reactive by modulating parameters via the audio reactivity bus (e.g., mapping `threshold` to audio amplitude).

## Performance

- **Expected FPS Impact:** ~2-4ms per 1080p frame on modern CPU (single-threaded)
- **Memory Usage:** ~3× frame buffer for temporary workspace (input, output, working copy)
- **Algorithm Complexity:** O(H × W × window_size²) naive implementation; optimized with separable filters reduces to O(H × W)
- **GPU Potential:** High — could be accelerated with compute shaders or CUDA for 4K+ real-time
- **Optimization Notes:**
  - Use integral images for O(1) local histogram queries
  - Precompute lookup tables for contrast stretching
  - Process in YUV space to reduce chroma subsampling artifacts
  - Consider downsampling for window_size > 32 to maintain performance

## Test Plan (Expanded)

| Test Category | Test Name | What It Verifies |
|---------------|-----------|------------------|
| **Basic Operation** | `test_basic_operation` | Core function returns expected output with valid input frame and default parameters |
| **Edge Cases** | `test_extreme_thresholds` | Behavior at threshold=0.0 (no effect) and threshold=1.0 (max effect) |
| | `test_small_window_sizes` | Correct processing with window_size=4 (minimum) |
| | `test_large_window_sizes` | Correct processing with window_size=64 (maximum) |
| | `test_non_power_of_2_window` | Rejects window_size=7, 12, 20, etc. with clear error |
| | `test_black_white_point_balance` | When black_point >= white_point, output is clamped to avoid division by zero |
| | `test_zero_saturation` | Saturation=0 produces grayscale output while preserving contrast |
| | `test_max_saturation` | Saturation=10.0 does not cause color channel overflow |
| **Frame Formats** | `test_rgb_vs_rgba` | Identical processing for RGB (3-channel) and RGBA (4-channel, alpha untouched) |
| | `test_uint8_input` | Correct handling of uint8 [0, 255] range, proper conversion to float for processing |
| | `test_float32_input` | Correct handling of float32 [0.0, 1.0] range |
| | `test_alpha_preservation` | Alpha channel is passed through unchanged in RGBA frames |
| **Error Handling** | `test_invalid_frame_ndim` | 2D or 5D arrays raise ValueError |
| | `test_invalid_frame_channels` | 1-channel or 5+ channel arrays raise ValueError |
| | `test_invalid_dtype` | float64, int16, etc. raise appropriate errors |
| | `test_nan_inf_handling` | Frames containing NaN/Inf are handled gracefully (either cleaned or rejected) |
| **Performance** | `test_memory_leak` | Repeated processing (10,000 frames) shows no memory growth |
| | `test_fps_60` | Processing maintains ≥60 FPS on reference hardware for 1080p |
| | `test_parallel_safety` | Multiple instances can process different frames concurrently without race conditions |
| **Quality** | `test_contrast_improvement` | Output has higher local contrast variance than input (measured) |
| | `test_detail_preservation` | High-detail regions (textures) remain sharp after processing |
| | `test_no_artifacts` | No ringing, halos, or banding in gradient regions |
| | `test_color_fidelity` | Output colors match input hues (only luminance and saturation affected) |

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