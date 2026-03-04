# P7-VE76: vibrant_retro_styles

> **Task ID:** `P7-VE76`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/vstyle/vibrant_retro_styles.py`)
> **Class:** `RioAestheticEffect`
> **Phase:** Phase 7
> **Status:** □ In Progress

---

## What This Module Does

The `vibrant_retro_styles` module implements the `RioAestheticEffect` - a comprehensive visual effect that transforms video input into vibrant, retro-inspired aesthetic styles. It provides a collection of stylized filters and transformations that emulate classic video effects, CRT displays, VHS artifacts, and retro gaming visuals. The module processes video frames through multiple aesthetic pipelines including color grading, scanline effects, noise patterns, and vintage distortions to create authentic retro visual experiences.

This effect draws inspiration from the golden age of video gaming and analog television, providing VJ performers with tools to create nostalgic, vibrant visual content that resonates with retro aesthetics while maintaining modern performance standards.

**What This Module Does NOT Do**

- Handle file I/O or persistent storage operations
- Process audio streams or provide sound-reactive capabilities
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context
- Generate procedural content beyond the defined retro effect parameters

---

## Public Interface

```python
class RioAestheticEffect:
    def __init__(self, width: int, height: int, fps: int) -> None: ...
    
    def set_parameter(self, param_name: str, value: float) -> None: ...
    def get_parameter(self, param_name: str) -> float: ...
    
    def process_frame(self, input_frame: np.ndarray) -> np.ndarray: ...
    
    def enable_effect(self, effect_name: str, enabled: bool) -> None: ...
    def is_effect_enabled(self, effect_name: str) -> bool: ...
    
    def set_color_grade(self, grade_name: str) -> None: ...
    def set_vintage_mode(self, mode_name: str) -> None: ...
    
    def reset_to_defaults(self) -> None: ...
    def get_current_parameters(self) -> dict: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `width` | `int` | Frame width in pixels | 64 ≤ width ≤ 4096 |
| `height` | `int` | Frame height in pixels | 64 ≤ height ≤ 4096 |
| `fps` | `int` | Target frame rate | 24 ≤ fps ≤ 120 |
| `input_frame` | `np.ndarray` | RGB video frame (H×W×3) | Values 0-255 |
| `param_name` | `str` | Parameter identifier | Valid parameter names |
| `value` | `float` | Parameter value | 0.0 ≤ value ≤ 10.0 |
| `effect_name` | `str` | Effect identifier | Valid effect names |
| `enabled` | `bool` | Enable/disable state | True/False |
| `grade_name` | `str` | Color grade preset | Valid grade names |
| `mode_name` | `str` | Vintage mode preset | Valid mode names |

---

## Edge Cases and Error Handling

- **Invalid frame dimensions**: Raises ValueError if width/height < 64 or > 4096
- **Unsupported color formats**: Converts non-RGB input to RGB or raises TypeError
- **Missing shader resources**: Fallback to CPU implementation with reduced quality
- **Parameter out of range**: Clamps values to 0.0-10.0 range with warning
- **Invalid effect names**: Raises KeyError with list of valid effects
- **Memory allocation failure**: Graceful degradation to lower resolution processing
- **Concurrent access**: Thread-safe parameter updates with mutex locking

---

## Dependencies

- **External Libraries**:
  - `numpy` for array operations and pixel processing
  - `opencv-python` for video frame manipulation
  - `pillow` for image processing and format conversion
  - `pyopencl` for GPU acceleration (optional)
- **Internal Dependencies**:
  - `vjlive3.core.effects.effect_base` for base effect functionality
  - `vjlive3.render.shader_manager` for shader compilation and management
  - `vjlive3.utils.color_processing` for color space conversions
  - `vjlive3.plugins.registry` for plugin registration and discovery

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if GPU is absent or unavailable |
| `test_basic_operation` | Core rendering function produces valid output when given a clean input frame |
| `test_parameter_range_validation` | All parameter inputs are clamped to 0.0–10.0 range and rejected outside bounds |
| `test_color_grade_switching` | Switching between color grades changes output appearance correctly |
| `test_vintage_mode_switching` | Vintage mode changes produce expected visual characteristics |
| `test_effect_enable_disable` | Individual effects can be toggled on/off without affecting others |
| `test_scanline_effect` | Scanline patterns are visible and proportional to input values |
| `test_noise_effect` | Noise patterns are correctly applied and configurable |
| `test_performance_60fps` | Maintains 60 FPS minimum at 1080p resolution |
| `test_invalid_frame_size` | Invalid frame sizes raise appropriate exceptions without crashing |
| `test_legacy_compatibility` | Output matches expected visual characteristics of original implementation |
| `test_parameter_set_get_cycle` | Dynamic parameter updates via set/get methods reflect real-time changes in output |
| `test_thread_safety` | Concurrent parameter updates do not cause race conditions or crashes |
| `test_memory_usage` | Memory usage stays within acceptable bounds for long-running operation |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-7] P7-VE76: vibrant_retro_styles - port from VJlive-2` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
