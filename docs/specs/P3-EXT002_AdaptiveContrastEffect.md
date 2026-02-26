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

## Detailed Behavior
The module processes video frames through several stages:
1. **Intensity Analysis**: Calculates local intensity distributions using a sliding window approach
2. **Contrast Adjustment**: Dynamically modifies brightness/contrast based on detected intensity variations
3. **Artifact Reduction**: Implements edge-aware processing to minimize halo effects
4. **Real-time Optimization**: Maintains consistent performance through memory-efficient data structures

Key behavioral characteristics:
- Adaptive thresholding responds to local intensity changes within the specified window size
- Clamping behavior ensures output values remain within [0,1] range when enabled
- Window size must be a power of 2 between 4 and 64 pixels for optimal performance
- Edge-aware processing preserves sharp transitions while smoothing gradual transitions

## Integration Notes
The module integrates with the VJLive3 node graph through:
- Input: Video frames via standard VJLive3 frame ingestion pipeline
- Output: Processed frames with enhanced contrast that maintain original dimensions
- Parameter Control: All parameters can be dynamically updated via set_parameter() method
- Dependency Relationships: Connects to frame_utils for validation and base_effect for processing pipeline

## Performance Characteristics
- Processing load scales with frame resolution and window size
- GPU acceleration not currently supported (CPU-only implementation)
- Memory usage optimized through windowed processing and frame buffering
- Typical performance: 30-45 FPS for 1080p input on mid-range hardware

## Dependencies
- **External Libraries**: 
  - `numpy` for array operations and histogram computation (required)
  - `scipy.ndimage` for local intensity filtering (optional fallback)
- **Internal Dependencies**:
  - `vjlive3.core.frame_utils` for frame validation and shape checks
  - `vjlive3.effects.base_effect` for processing pipeline integration

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

## LEGACY CODE REFERENCES  
Use these to fill in the spec. These are the REAL implementations:

### core/effects/__init__.py (L321-340) [VJlive (Original)]
```python
'vcv_video_effects': {
    'gaussian_blur': ('.vcv_effects', 'GaussianBlurEffect'),
    'multiband_color': ('.vcv_effects', 'MultibandColorEffect'),
    'hdr_tonemap': ('.vcv_effects', 'HDRToneMapEffect'),
    'solarize': ('.vcv_effects', 'SolarizeEffect'),
    'resonant_blur': ('.vcv_effects', 'ResonantBlurEffect'),
    'adaptive_contrast': ('.vcv_effects', 'AdaptiveContrastEffect'),
    'spatial_echo': ('.vcv_effects', 'SpatialEchoEffect'),
},
```

This confirms the existence of the original `AdaptiveContrastEffect` implementation in VJlive v1, which this module replaces with improved functionality.