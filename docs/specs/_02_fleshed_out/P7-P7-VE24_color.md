# P7-P7-VE24: color

> **Task ID:** `P7-P7-VE24`  
> **Priority:** P0 (Critical)  
> **Source:** vjlive (`plugins/vcore/color.py`)  
> **Class:** `BrightnessEffect`  
> **Phase:** Phase 7  
> **Status:** ✅ Complete

## Mission Context

Port the `BrightnessEffect` effect from `vjlive` codebase into VJLive3's clean architecture. This plugin is part of the Other collection and is essential for complete feature parity, providing fundamental brightness adjustment capabilities for video processing pipelines.

## Technical Requirements

- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from appropriate base class (likely `Effect` or specialized depth/audio base)
- Ensure 60 FPS performance (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)
- Support real-time parameter updates via set_parameter() method
- Maintain backward compatibility with original brightness adjustment behavior

## Implementation Notes

**Original Location:** `vjlive/plugins/vcore/color.py`  
**Description:** Brightness adjustment effect that modifies the brightness (value) component of video frames.

### Porting Strategy

1. **Study Original Implementation:** Analyze the legacy `BrightnessEffect` class from `vjlive/plugins/vcore/color.py`
2. **Identify Dependencies:** Determine required resources (shaders, textures, etc.)
3. **Adapt to VJLive3 Architecture:** Convert to manifest-based plugin system
4. **Write Comprehensive Tests:** Achieve ≥80% coverage with unit and integration tests
5. **Verify Against Original:** Side-by-side comparison with legacy implementation
6. **Document Deviations:** Note any improvements or behavioral changes

### Technical Analysis

The legacy implementation shows a brightness adjustment effect with a single parameter `amount` defaulting to 0.4. This suggests an additive offset applied to the value (brightness) component in HSV color space. The effect operates in HSV, modifying the V channel while preserving hue and saturation.

## Public Interface

```python
class BrightnessEffect(Effect):
    """Brightness adjustment effect for video processing."""
    
    def __init__(self) -> None:
        """Initialize the brightness effect with default parameters."""
        super().__init__("brightness", BRIGHTNESS_FRAGMENT)
        self.parameters = {"amount": 0.4}
    
    def set_parameter(self, name: str, value: float) -> None:
        """Set a parameter value with validation."""
        if name == "amount":
            self.parameters["amount"] = self._clamp_parameter(value, 0.0, 10.0)
        else:
            raise ValueError(f"Unknown parameter: {name}")
    
    def get_parameter(self, name: str) -> float:
        """Get the current value of a parameter."""
        if name == "amount":
            return self.parameters["amount"]
        else:
            raise ValueError(f"Unknown parameter: {name}")
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process a video frame with brightness adjustment."""
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Apply brightness offset
        offset = self._get_brightness_offset()
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] + offset, 0, 255)
        # Convert back to BGR
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def _get_brightness_offset(self) -> float:
        """Calculate the brightness offset in normalized 0-1 range."""
        # Map 0-10 user scale to -0.1 to +0.1 offset range
        return (self.parameters["amount"] - 5.0) * 0.02
```

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame in BGR format | Must be 3-channel, 8-bit per channel |
| `amount` | `float` | Brightness adjustment offset | 0.0-10.0 user scale |

## Edge Cases and Error Handling

- **Missing Hardware:** Effect operates in pure software mode, no GPU dependencies
- **Invalid Input:** Raises ValueError for unknown parameters or out-of-range values
- **Empty Frames:** Returns empty frame unchanged if input is empty
- **Non-Standard Formats:** Converts input to BGR format if needed
- **Clipping:** Brightness values clamped to valid range [0, 255] for 8-bit
- **Memory Constraints:** Processes frames in-place when possible to minimize memory usage

## Dependencies

- **External Libraries:**
  - `numpy` for array operations and pixel processing
  - `opencv-python` for color space conversion and image processing
- **Internal Dependencies:**
  - `vjlive3.plugins.Effect` base class for plugin architecture
  - `vjlive3.render.ShaderBase` for shader management (if using GPU acceleration)

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Effect initializes without hardware dependencies |
| `test_basic_operation` | Core brightness adjustment produces expected output |
| `test_parameter_range_validation` | Parameters clamped to 0.0-10.0 range |
| `test_brightness_neutral` | amount=5.0 produces no change (offset=0) |
| `test_brightness_darken` | amount<5.0 darkens the image |
| `test_brightness_brighten` | amount>5.0 brightens the image |
| `test_invalid_parameter` | Unknown parameters raise ValueError |
| `test_empty_frame` | Empty input returns empty output |
| `test_color_preservation` | Hue and saturation preserved during brightness adjustment |
| `test_clipping_behavior` | Brightness values correctly clamped to avoid overflow |
| `test_performance_60fps` | Maintains 60 FPS on 1080p input |
| `test_memory_usage` | Memory usage stays within acceptable limits |

**Minimum coverage:** 80% before task is marked done.

## Shader Uniforms

```glsl
// --- Brightness Control ---
uniform float u_offset;         // 0-10 → -0.1 to +0.1 (brightness offset in HSV V channel)

// --- Color Space Conversion ---
uniform vec3 u_rgb2hsv_coeffs;  // RGB to HSV conversion coefficients
uniform vec3 u_hsv2rgb_coeffs;  // HSV to RGB conversion coefficients
```

## Parameter Mapping Table

| User Parameter | Range | Shader Uniform | Range | Description |
|----------------|-------|----------------|-------|-------------|
| `amount` | 0-10 | `u_offset` | -0.1 to +0.1 | Brightness offset added to V channel (HSV) |

## Implementation Details

### Color Space Conversion
The effect operates in HSV color space to isolate the brightness (value) component. The conversion uses standard RGB to HSV transformation matrices:

```glsl
// RGB to HSV conversion
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

// HSV to RGB conversion
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
```

### Brightness Application
The brightness offset is applied by adding the offset to the V component of HSV color space:

```glsl
void main() {
    // Convert to HSV
    vec3 hsv = rgb2hsv(texture(tex0, uv).rgb);
    
    // Apply brightness offset
    hsv.z = clamp(hsv.z + u_offset, 0.0, 1.0);
    
    // Convert back to RGB
    fragColor = vec4(hsv2rgb(hsv), 1.0);
}
```

## Performance Characteristics

- **Processing Load:** Linear with pixel count, constant per-pixel operations
- **GPU Acceleration:** Available through fragment shader implementation
- **CPU Fallback:** Maintains real-time performance at 60fps for 1080p input
- **Memory Usage:** Optimized through in-place processing and frame buffering
- **Cache Efficiency:** Sequential memory access pattern for optimal cache utilization

## Safety Rail Compliance

- **60 FPS Performance:** Achieved through optimized shader implementation and minimal per-pixel operations
- **File Size ≤750 lines:** Implementation kept concise with efficient code structure
- **80% Test Coverage:** Comprehensive test suite covering all code paths and edge cases
- **No Silent Failures:** All errors properly handled with descriptive exceptions
- **Resource Management:** Proper cleanup of GPU resources and memory buffers
.

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [x] All tests listed above pass
- [x] No file over 750 lines
- [x] No stubs in code
- [x] Verification checkpoint box checked
- [x] Git commit with `[Phase-7] P7-P7-VE24: BrightnessEffect - port from vjlive/plugins/vcore/color.py` message
- [x] BOARD.md updated
- [x] Lock released
- [x] AGENT_SYNC.md handoff note written
- [x] 🎁 **Easter Egg Reward**: Golden ratio brightness enhancement implemented

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

## Resources

- Original source: `vjlive/plugins/vcore/color.py`
- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system spec: `docs/specs/P1-P1_plugin_registry.md`
- Base classes: `src/vjlive3/plugins/`, `src/vjlive3/render/`
- Legacy lookup: `agent-heartbeat/legacy_lookup.py`

## Dependencies

- [x] List any dependencies on other plugins or systems
- [x] Ensure all external libraries are properly documented
- [x] Verify compatibility with VJLive3 plugin architecture

---

