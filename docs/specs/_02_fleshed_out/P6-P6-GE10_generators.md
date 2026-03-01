# Spec: P6-GE10 — Gradient Generator

**File naming:** `docs/specs/P6-P6-GE10_generators.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-GE10 — generators

**What This Module Does**  
The `GradientEffect` module generates smooth color gradients across the video frame using multiple interpolation modes, creating dynamic backgrounds and blended overlays. It produces multi-color gradients using linear, radial, angular, and diamond-shaped geometries with full control over color anchor points, interpolation curves, and temporal animation. The module transforms video input through gradient overlays, enabling smooth color transitions from point-to-point with procedurally-timed animation and optional frame oscillation.

**What This Module Does NOT Do**  
- Handle file I/O or persistent storage operations  
- Process audio streams or provide direct sound input  
- Implement 3D geometry or volumetric effects  
- Provide direct MIDI or OSC control interfaces  
- Support custom texture loading (procedural only)  

**Detailed Behavior**  
The module processes video frames through several stages:
1. **Gradient Type Selection**: Chooses interpolation geometry (linear, radial, angular, diamond)
2. **Color Stop Definition**: Creates N color stops at normalized positions along gradient path
3. **Distance/Angle Calculation**: Computes normalized position for each pixel relative to gradient axis
4. **Color Interpolation**: Uses selected interpolation curve (linear, smooth, step) to blend between color stops
5. **Temporal Animation**: Applies time-based rotation, shift, or scale to gradient position
6. **Output Compositing**: Blends gradient with input frame using mix ratio

Key mathematical characteristics:
- Gradient angle: `θ = angle / 10 * 360°` (0-360°)
- Gradient scale: `s = scale / 10 * 5.0` (0.2-5.0x)
- Linear gradient position: `t = (uv · direction) + offset`
- Radial gradient position: `t = distance(uv, center) / radius`
- Angular gradient position: `t = (atan2(uv.y - center.y, uv.x - center.x) + π) / (2π)`
- Diamond gradient position: `t = |uv.x - center.x| + |uv.y - center.y|`
- Smooth interpolation (Hermite): `s(t) = 3t^2 - 2t^3` (for 0 ≤ t ≤ 1)
- Color stop evaluation: `color(t) = interpolate(colors[i], colors[i+1], (t - stops[i]) / (stops[i+1] - stops[i]))`
- Temporal modulation: `angle_animated = angle + time * rotation_speed / 10 * 360°`
- Radial scale animation: `radius_animated = radius * (1.0 + pulsation * sin(time * pulsation_speed / 10 * π))`

**Integration Notes**  
The module integrates with the VJLive3 node graph through:
- Input: Video frames via standard VJLive3 frame ingestion pipeline
- Output: Processed frames with gradient overlay maintaining original dimensions
- Parameter Control: All parameters dynamically updatable via set_parameter() method
- Dependency Relationships: Connects to shader_base for color interpolation and framebuffer compositing

**Performance Characteristics**  
- Processing load: O(frame_pixels) — single pass per pixel regardless of color stop count
- GPU acceleration via GLSL fragment shader (texture-based color stops)
- CPU fallback using NumPy vectorized operations
- Real-time 60fps achievable at all frame sizes on modern GPU
- Memory usage: O(num_color_stops) minimal, independent of frame resolution
- Latency kept under 16ms for 60fps target via single-pass computation

---

## Public Interface

```python
class GradientEffect:
    def __init__(self, frame_width: int, frame_height: int) -> None: ...
    def process_frame(self, input_frame: np.ndarray) -> np.ndarray: ...
    def set_parameter(self, param_name: str, value: float) -> None: ...
    def get_parameter(self, param_name: str) -> float: ...
    def set_color_stop(self, index: int, position: float, color: tuple) -> None: ...
    def reset(self) -> None: ...
    def stop(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame_width` | `int` | Input frame width in pixels | 64-4096 |
| `frame_height` | `int` | Input frame height in pixels | 64-4096 |
| `input_frame` | `np.ndarray` | RGB frame data (HxWx3) | uint8, 0-255 |
| `gradient_type` | `float` | Geometry type | 0=linear, 3.33=radial, 6.67=angular, 10=diamond |
| `angle` | `float` | Gradient direction angle | 0.0-10.0 (maps to 0-360°) |
| `scale` | `float` | Gradient size multiplier | 0.0-10.0 (maps to 0.2-5.0x) |
| `rotation_speed` | `float` | Temporal angle modulation | 0.0-10.0 |
| `pulsation` | `float` | Radial scale oscillation magnitude | 0.0-10.0 |
| `pulsation_speed` | `float` | Oscillation frequency | 0.0-10.0 |
| `interpolation` | `float` | Curve type | 0=linear, 5=smooth Hermite, 10=step |
| `saturation` | `float` | Color saturation multiplier | 0.0-10.0 |
| `mix` | `float` | Output mix ratio (gradient vs input) | 0.0-1.0 |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → (CPU fallback using NumPy vectorized interpolation)
- What happens on bad input? → (raise ValueError with parameter name and valid range)
- What is the cleanup path? → (close() releases GPU resources)
- What if frame dimensions are invalid? → (raise ValueError with dimension constraints)
- What if color_stops is empty? → (fall back to grayscale 0→1 gradient)

---

## Dependencies

- **External Libraries**: 
  - `numpy` for array operations and color interpolation
  - `scipy.interpolate` for higher-order spline interpolation (optional)
  - `pyopencl` for GPU acceleration (optional)
- **Internal Dependencies**:
  - `vjlive3.core.effects.shader_base` for fundamental shader operations
  - `vjlive3.plugins.vcore.generators.py` for legacy implementation reference

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without GPU; uses CPU fallback |
| `test_basic_operation` | Core gradient generation produces valid output |
| `test_parameter_range_validation` | All parameters clamped to 0.0–10.0; out-of-range raises ValueError |
| `test_gradient_type_linear` | Linear gradient renders horizontal/vertical stripes correctly |
| `test_gradient_type_radial` | Radial gradient produces concentric circles from center point |
| `test_gradient_type_angular` | Angular gradient creates rotational color sweep |
| `test_gradient_type_diamond` | Diamond gradient produces Manhattan-distance-based pattern |
| `test_angle_rotation` | angle parameter correctly rotates gradient direction |
| `test_scale_magnitude` | scale parameter correctly stretches/compresses gradient |
| `test_rotation_animation` | rotation_speed produces smooth continuous rotation |
| `test_pulsation_oscillation` | pulsation creates smooth radial breathing effect |
| `test_interpolation_linear` | Linear interpolation produces sharp color boundaries |
| `test_interpolation_smooth` | Smooth interpolation produces soft Hermite curves |
| `test_interpolation_step` | Step interpolation produces hard color transitions |
| `test_color_stop_positions` | Color stops at correct normalized positions along gradient |
| `test_color_stop_interpolation` | Colors correctly interpolated between stops |
| `test_saturation_control` | saturation parameter correctly scales color intensity |
| `test_mix_ratio` | mix parameter correctly blends gradient with input |
| `test_invalid_frame_size` | Invalid dimensions raise appropriate exceptions |
| `test_smooth_temporal_continuity` | Temporal animations produce smooth frame-to-frame transitions |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-GE10: generators - port from vjlive/plugins/vcore/generators.py` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: Submit creative Easter Egg to `WORKSPACE/EASTEREGG_COUNCIL.md`

---

## LEGACY CODE REFERENCES  
Use these to fill in the spec. These are the REAL implementations:

### vjlive/plugins/vcore/generators.py (L1-20)  
```python
"""
Generator effects — create patterns from scratch.
Gradient-based color field generation with multiple interpolation modes.

All parameters use 0.0-10.0 range from UI sliders.
Shaders remap internally to the values the math needs.
Supports linear, radial, angular, and diamond gradient types.
"""
```

### vjlive/plugins/vcore/generators.py (L300-350)  
```glsl
// Smooth Hermite interpolation
float smoothstep3(float t) {
    return t * t * (3.0 - 2.0 * t);
}

// Evaluate color from gradient stops
vec3 gradient_color(float t, vec3 colors[8], float stops[8], int num_stops, int interp_type) {
    // Clamp t to [0, 1]
    t = clamp(t, 0.0, 1.0);
    
    // Find surrounding color stops
    for (int i = 0; i < MAX_STOPS; i++) {
        if (i >= num_stops - 1) break;
        
        if (t >= stops[i] && t <= stops[i+1]) {
            float local_t = (t - stops[i]) / (stops[i+1] - stops[i]);
            
            if (interp_type == 0) {
                // Linear interpolation
                return mix(colors[i], colors[i+1], local_t);
            } else if (interp_type == 1) {
                // Smooth Hermite interpolation
                float smooth_t = smoothstep3(local_t);
                return mix(colors[i], colors[i+1], smooth_t);
            } else {
                // Step interpolation
                return local_t < 0.5 ? colors[i] : colors[i+1];
            }
        }
    }
    return colors[num_stops - 1];
}

// Calculate normalized position along gradient axis
float gradient_position(vec2 uv, int grad_type, vec2 center, float angle, float scale) {
    vec2 dir = normalize(vec2(cos(angle), sin(angle)));
    
    if (grad_type == 0) {
        // Linear: dot product with direction
        return dot(uv - center, dir) * scale;
    } else if (grad_type == 1) {
        // Radial: distance from center
        return distance(uv, center) * scale;
    } else if (grad_type == 2) {
        // Angular: atan2-based angle
        float ang = atan(uv.y - center.y, uv.x - center.x);
        return fract(ang / 6.28318 + angle / 6.28318);
    } else {
        // Diamond: Manhattan distance
        return (abs(uv.x - center.x) + abs(uv.y - center.y)) * scale;
    }
}
```

### vjlive/plugins/vcore/generators.py (L351-400)  
```glsl
void main() {
    vec4 input_color = texture(tex0, uv);
    
    // Remap parameters
    int grad_type = int(gradient_type / 10.0 * 3.0);
    int interp_type = int(interpolation / 10.0 * 2.0);
    float ang = angle / 10.0 * 6.28318;
    float sc = scale / 10.0 * 4.8 + 0.2;
    float rot_speed = rotation_speed / 10.0 * 3.0;
    float puls = pulsation / 10.0;
    float puls_speed = pulsation_speed / 10.0 * 5.0;
    
    // Animated angle for rotation
    float anim_angle = ang + time * rot_speed;
    
    // Animated scale for pulsation
    float anim_scale = sc * (1.0 + puls * sin(time * puls_speed * 6.28318));
    
    // Gradient center (default: frame center)
    vec2 gradient_center = vec2(0.5, 0.5);
    
    // Calculate position along gradient
    float t = gradient_position(uv, grad_type, gradient_center, anim_angle, anim_scale);
    
    // Setup default color stops (black to white)
    vec3 colors[8];
    float stops[8];
    int num_stops = 2;
    
    colors[0] = vec3(0.0);
    stops[0] = 0.0;
    colors[1] = vec3(1.0);
    stops[1] = 1.0;
    
    // Evaluate gradient color at position t
    vec3 grad_color = gradient_color(t, colors, stops, num_stops, interp_type);
    
    // Apply saturation
    vec3 hsv = rgb2hsv(grad_color);
    hsv.y *= saturation / 10.0 * 2.0;
    grad_color = hsv2rgb(hsv);
    
    // Final compositing
    fragColor = mix(input_color, vec4(grad_color, 1.0), u_mix);
}
```

### vjlive/plugins/vcore/generators.py (L400-440)  
```python
class GradientEffect(Effect):
    """Gradient generator — smooth color interpolation with multiple geometries."""

    def __init__(self):
        super().__init__("gradient", GRADIENT_FRAGMENT)
        self.parameters = {
            "gradient_type": 0.0,     # 0=linear
            "angle": 0.0,
            "scale": 5.0,
            "rotation_speed": 0.0,
            "pulsation": 0.0,
            "pulsation_speed": 0.0,
            "interpolation": 0.0,     # 0=linear
            "saturation": 5.0,
        }
        self.color_stops = [
            {"position": 0.0, "color": (0.0, 0.0, 0.0)},  # Black
            {"position": 1.0, "color": (1.0, 1.0, 1.0)},  # White
        ]
```

---

## Verification Checkpoints

- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum
- [ ] Test coverage ≥80%
- [ ] No safety rail violations
- [ ] Original functionality verified (side-by-side comparison)
- [ ] Gradient mathematics verified for all types
- [ ] Color stop interpolation mathematically exact

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

---

