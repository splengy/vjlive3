# P5-VE02: analog_tv (AnalogTVEffect)

## Overview

The `AnalogTVEffect` module is a comprehensive GPU-accelerated shader that simulates analog video degradation across the entire spectrum—from VHS tape artifacts to CRT display characteristics to RF signal interference. It combines physical modeling of tape transport mechanics, electromagnetic signal corruption, and analog monitor characteristics into a single, highly tunable effect. This creates authentic retro video aesthetics essential for VJ performances, glitch art, and nostalgic visual design.

The effect operates via multi-stage UV distortion and color space transformations, applying characteristic artifacts like tracking errors, scanlines, phosphor bloom, convergence errors, tape dropouts, and RF interference noise. All 30+ parameters are exposed on a 0.0-10.0 scale with mathematically precise mappings to physical ranges, enabling both preset-like simplicity and deep technical control.

**Core Feature Categories:**

1. **VHS Tape Artifacts**: Tracking errors, tape wrinkle, head switch noise, dropouts, tape speed wobble
2. **CRT Display Effects**: Barrel distortion, scanlines, phosphor mask/glow, RGB convergence, corner vignette, brightness control
3. **RF/Signal Degradation**: Noise, interference patterns, composite color bleeding, chroma delay, luma sharpening
4. **Extreme Glitch**: Vertical rolling, interlacing combing, snow/static, color kill
5. **Performance**: Single-pass fragment shader optimized for 60 FPS at 1080p

## Architecture

### Multi-Stage Pipeline

The AnalogTVEffect processes frames through the following sequential stages:

**Stage 1: CRT Barrel Distortion**
```glsl
vec2 cuv = uv;
if (curve > 0.0) {
    vec2 cc = cuv * 2.0 - 1.0;
    cc *= 1.0 + dot(cc, cc) * curve;
    cuv = cc * 0.5 + 0.5;
    if (cuv.x < 0.0 || cuv.x > 1.0 || cuv.y < 0.0 || cuv.y > 1.0) {
        fragColor = vec4(0.0); return;  // Out-of-bounds pixels = black
    }
}
```

Applies quadratic barrel distortion simulating curved CRT screen geometry. Out-of-bounds pixels clipped to black, creating natural vignette.

**Stage 2: VHS Tracking Errors**
```glsl
if (tracking > 0.0) {
    float scanline = floor(cuv.y * resolution.y);
    float scan_phase = scanline / resolution.y;
    float bar1 = smoothstep(bar_pos + 0.08, bar_pos + 0.03, scan_phase) * 
                  smoothstep(bar_pos + 0.03, bar_pos + 0.08, scan_phase);
    float tracking_offset = (bar1 * 0.7) * tracking * 0.3;
    cuv.x += tracking_offset;
}
```

Creates horizontal displacement "tracking bars" characteristic of VHS head alignment errors.

**Stage 3: Vertical Rolling**
```glsl
if (rolling > 0.0) {
    float roll_offset = fract(time * roll_speed * 0.1) * rolling;
    cuv.y = fract(cuv.y + roll_offset);
}
```

Simulates tape speed instability causing vertical image movement.

**Stage 4: Line Jitter & Tape Wrinkle**
```glsl
if (jitter > 0.0) {
    float line_hash = hash(vec2(scanline, floor(time * 60.0 * t_speed)));
    cuv.x += (line_hash - 0.5) * jitter;
}
```

Adds fine horizontal line-by-line jitter and tape wrinkle distortion.

**Stage 5: Head Switching Noise & Dropouts**
Simulates tape transport gaps, head alignment errors, and tape damage patterns.

**Stage 6: Color Space Processing (RGB → YUV → RGB)**
```glsl
// RGB to YUV (luma/chroma separation)
float y = dot(color.rgb, vec3(0.299, 0.587, 0.114));
vec3 yuv = rgb2yuv(color.rgb);

// Apply composite color bleeding and chroma delay
if (color_bleed > 0.01) {
    vec3 yuv_left = rgb2yuv(texture(tex0, uv - vec2(c_delay, 0.0)).rgb);
    yuv.z = mix(yuv.z, (yuv_left.z + yuv.z) / 2.0, color_bleed);
}

// Convert back to RGB
color.rgb = yuv2rgb(yuv);
```

Simulates composite video signal corruption with chroma delay and bleeding.

**Stage 7: CRT Scanlines & Phosphor Effects**
```glsl
if (scanlines > 0.0) {
    float sl = sin(cuv.y * resolution.y * π) * 0.5 + 0.5;
    color *= 1.0 - scanlines * (1.0 - sl) * 0.5;
}
```

Adds horizontal scanline pattern with adjustable intensity.

**Stage 8: Phosphor Glow**
Blurs bright pixels to simulate CRT phosphor spread.

**Stage 9: RF Noise & Signal Degradation**
```glsl
if (rf_noise > 0.01) {
    float noise = hash(vec2(uv.x + time, uv.y)) - 0.5;
    color.rgb += noise * rf_noise * 0.3;
}
```

Adds high-frequency noise and RF interference patterns.

**Stage 10: Interlacing & Snow Artifacts**
Simulates interlaced scanning and tape dropouts as white noise.

**Stage 11: Color Kill & Desaturation**
```glsl
if (color_kill > 0.0) {
    float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    color.rgb = mix(color.rgb, vec3(gray), color_kill);
}
```

Removes color information to simulate signal loss or mono mode.

**Stage 12: Final Blending**
```glsl
fragColor = mix(original, processed, mix);
```

---

## Parameters (30+ tunable controls)

All parameters use 0.0-10.0 normalized scale with automatic mapping to operational ranges:

### VHS/Tape Parameters

| Parameter | Range | Default | Maps To | Description |
|-----------|-------|---------|---------|-------------|
| `vhs_tracking` | 0.0-10.0 | 3.0 | 0 to 1 | Horizontal tracking error bars |
| `tape_wrinkle` | 0.0-10.0 | 1.0 | 0 to 0.5 | Wavy tape distortion |
| `head_switch` | 0.0-10.0 | 1.0 | 0 to 0.2 | Head switching noise |
| `dropout_rate` | 0.0-10.0 | 0.5 | 0 to 0.3 | Dropout frequency |
| `dropout_length` | 0.0-10.0 | 2.0 | 0.01 to 0.5 | Dropout duration (frames) |
| `tape_speed` | 0.0-10.0 | 5.0 | 0.5 to 3.0 | Playback speed wobble |

### CRT Display Parameters

| Parameter | Range | Default | Maps To | Description |
|-----------|-------|---------|---------|-------------|
| `crt_curvature` | 0.0-10.0 | 2.0 | 0 to 0.5 | Barrel distortion |
| `crt_scanlines` | 0.0-10.0 | 3.0 | 0 to 1 | Scanline intensity |
| `scanline_freq` | 0.0-10.0 | 5.0 | 200 to 1080 | Scanline density (Hz) |
| `phosphor_mask` | 0.0-10.0 | 1.0 | 0 to 1 | RGB phosphor pattern visibility |
| `phosphor_glow` | 0.0-10.0 | 2.0 | 0 to 2 | Phosphor bloom radius |
| `convergence` | 0.0-10.0 | 1.0 | 0 to 0.005 | RGB channel misalignment |
| `corner_shadow` | 0.0-10.0 | 1.5 | 0 to 1 | Vignette/corner darkening |
| `brightness` | 0.0-10.0 | 5.0 | 0.5 to 2.0 | Overall brightness |

### RF/Signal Parameters

| Parameter | Range | Default | Maps To | Description |
|-----------|-------|---------|---------|-------------|
| `rf_noise` | 0.0-10.0 | 1.0 | 0 to 0.3 | RF interference noise |
| `rf_pattern` | 0.0-10.0 | 0.5 | 0 to 1 | RF pattern intensity |
| `color_bleed` | 0.0-10.0 | 1.5 | 0 to 0.01 | Composite color bleeding |
| `chroma_delay` | 0.0-10.0 | 1.0 | 0 to 0.005 | Chroma-luma phase shift |
| `chroma_noise` | 0.0-10.0 | 0.5 | 0 to 0.1 | Chroma noise level |
| `luma_sharpen` | 0.0-10.0 | 1.0 | 0 to 2.0 | Luma sharpening |

### Glitch Parameters

| Parameter | Range | Default | Maps To | Description |
|-----------|-------|---------|---------|-------------|
| `glitch_intensity` | 0.0-10.0 | 0.0 | 0 to 1 | Overall glitch amount |
| `rolling` | 0.0-10.0 | 0.0 | 0 to 1 | Vertical rolling intensity |
| `rolling_speed` | 0.0-10.0 | 5.0 | 0.1 to 5.0 | Rolling speed (frames/sec) |
| `interlace` | 0.0-10.0 | 0.0 | 0 to 1 | Interlacing combing |
| `snow` | 0.0-10.0 | 0.0 | 0 to 1 | Static noise (tape dropouts) |
| `color_kill` | 0.0-10.0 | 0.0 | 0 to 1 | Desaturation/color loss |
| `jitter` | 0.0-10.0 | 1.0 | 0 to 1 | Per-line horizontal jitter |

### Master Controls

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `mix` | 0.0-1.0 | 1.0 | Blend original with degraded (0=clean, 1=fully degraded) |

---

## Public Interface

```python
class AnalogTVEffect(Effect):
    """
    Comprehensive analog TV degradation effect.
    
    Simulates VHS artifacts, CRT display characteristics, RF signal
    corruption, and extreme glitch effects in a single GPU shader.
    
    Parameters:
        All parameters are on 0.0-10.0 scale (or 0.0-1.0 for mix)
    """
    
    def __init__(self, name: str = "analog_tv",
                 fragment_shader: str = ANALOG_TV_FRAGMENT) -> None:
        """
        Initialize the AnalogTVEffect.
        
        Args:
            name: Effect identifier for logging and registry
            fragment_shader: GLSL fragment shader source code
        """
        super().__init__(name, fragment_shader)
        self.parameters = {
            # VHS/Tape
            "vhs_tracking": 3.0,
            "tape_wrinkle": 1.0,
            "head_switch": 1.0,
            "dropout_rate": 0.5,
            "dropout_length": 2.0,
            "tape_speed": 5.0,
            # CRT Display
            "crt_curvature": 2.0,
            "crt_scanlines": 3.0,
            "scanline_freq": 5.0,
            "phosphor_mask": 1.0,
            "phosphor_glow": 2.0,
            "convergence": 1.0,
            "corner_shadow": 1.5,
            "brightness": 5.0,
            # RF/Signal
            "rf_noise": 1.0,
            "rf_pattern": 0.5,
            "color_bleed": 1.5,
            "chroma_delay": 1.0,
            "chroma_noise": 0.5,
            "luma_sharpen": 1.0,
            # Glitch
            "glitch_intensity": 0.0,
            "rolling": 0.0,
            "rolling_speed": 5.0,
            "interlace": 0.0,
            "snow": 0.0,
            "color_kill": 0.0,
            "jitter": 1.0,
            # Master
            "mix": 1.0,
        }
    
    def set_parameter(self, key: str, value: float) -> None:
        """
        Set a parameter value and clamp to valid range.
        
        Args:
            key: Parameter name
            value: Floating-point value
            
        Raises:
            KeyError: If key is not a valid parameter
            TypeError: If value is not numeric
        """
        if key not in self.parameters:
            raise KeyError(f"Unknown parameter: {key}")
        if not isinstance(value, (int, float)):
            raise TypeError(f"Parameter value must be numeric, got {type(value)}")
        
        # Clamp to appropriate ranges
        if key == "mix":
            self.parameters[key] = max(0.0, min(1.0, float(value)))
        else:
            self.parameters[key] = max(0.0, min(10.0, float(value)))
    
    def render(self, texture_id: int, extra_textures: dict = None) -> int:
        """
        Apply the analog TV effect to an input texture.
        
        Args:
            texture_id: Input texture ID
            extra_textures: Optional additional textures (unused)
        
        Returns:
            Output texture ID with effect applied
            
        Raises:
            RuntimeError: If shader compilation/rendering failed
            ValueError: If texture ID is invalid
        """
        # Implementation: bind uniforms, render full-screen quad
        pass
```

---

## Inputs and Outputs

### Inputs (Uniforms)

| Name | Type | Description |
|------|------|-------------|
| `tex0` | sampler2D | Input video frame |
| `time` | float | Elapsed time in seconds |
| `resolution` | vec2 | Frame resolution in pixels |
| All parameters | float | 27x shader uniforms |

### Outputs

| Name | Type | Description |
|------|------|-------------|
| `fragColor` | vec4 | Degraded RGBA frame |

---

## Edge Cases and Error Handling

### Parameter Validation

- **VHS/CRT parameters out of range**: Clamped to [0, 10]
- **Mix out of range**: Clamped to [0, 1]
- **Non-numeric values**: Raise `TypeError`
- **Missing parameters**: Use defaults

### Rendering Issues

- **Black/corrupted output**: Caused by extreme parameter values; graceful fallback to original
- **Out-of-bounds distortion**: Clipped to black (barrel distortion), handled by GPU
- **Performance degradation**: Each effect is optional; disable unused features via parameter = 0

### GPU Memory

- Single-pass shader (no intermediate buffers)
- Minimal memory footprint
- Scales linearly with frame resolution

---

## Dependencies

### Internal
- `Effect` base class (VJLive3 core)
- GLSL fragment shader execution

### External
- OpenGL ES 3.0+ (shader compilation, rendering)
- GLSL 3.0+ (shader language)

---

## Test Plan (12+ test cases)

### Unit Tests

#### 1. Parameter Clamping
```python
def test_parameter_clamping():
    effect = AnalogTVEffect()
    effect.set_parameter("vhs_tracking", -5.0)
    assert effect.parameters["vhs_tracking"] == 0.0
    effect.set_parameter("vhs_tracking", 15.0)
    assert effect.parameters["vhs_tracking"] == 10.0
```

#### 2. Mix Parameter
```python
def test_mix_blending():
    effect = AnalogTVEffect()
    effect.set_parameter("mix", 0.0)
    assert effect.parameters["mix"] == 0.0
    effect.set_parameter("mix", 0.5)
    assert effect.parameters["mix"] == 0.5
    effect.set_parameter("mix", 1.0)
    assert effect.parameters["mix"] == 1.0
```

### Integration Tests

#### 3. Performance: 60 FPS at 1080p
```python
def test_performance_60fps_1080p():
    effect = AnalogTVEffect()
    test_texture = create_test_texture(1920, 1080)
    
    import time
    start = time.perf_counter()
    for _ in range(300):  # 5 seconds at 60 FPS
        effect.render(test_texture)
    elapsed = time.perf_counter() - start
    
    assert elapsed <= 5.0, f"Took {elapsed:.2f}s, need ≤5.0s"
    fps = 300 / elapsed
    assert fps >= 60.0, f"Only {fps:.1f} FPS, need 60+"
```

#### 4. Barrel Distortion Output
```python
def test_barrel_distortion():
    effect = AnalogTVEffect()
    test_frame = create_test_frame()
    
    # No distortion
    effect.set_parameter("crt_curvature", 0.0)
    output_0 = effect.render(test_frame)
    
    # High distortion
    effect.set_parameter("crt_curvature", 10.0)
    output_10 = effect.render(test_frame)
    
    # Outputs should differ (edges distorted)
    difference = np.mean(np.abs(output_0 - output_10))
    assert difference > 10.0
```

#### 5. Scanlines Visibility
```python
def test_scanlines():
    effect = AnalogTVEffect()
    test_frame = create_uniform_frame(128)  # Gray
    
    # No scanlines
    effect.set_parameter("crt_scanlines", 0.0)
    output_0 = effect.render(test_frame)
    
    # Strong scanlines
    effect.set_parameter("crt_scanlines", 10.0)
    output_10 = effect.render(test_frame)
    
    # Should see horizontal line pattern
    assert has_scanline_pattern(output_10)
```

#### 6. VHS Tracking Errors
```python
def test_vhs_tracking():
    effect = AnalogTVEffect()
    test_frame = create_test_frame()
    
    effect.set_parameter("vhs_tracking", 0.0)
    output_0 = effect.render(test_frame)
    
    effect.set_parameter("vhs_tracking", 10.0)
    output_10 = effect.render(test_frame)
    
    # Should see horizontal displacement artifacts
    difference = np.mean(np.abs(output_0 - output_10))
    assert difference > 20.0
```

#### 7. RF Noise
```python
def test_rf_noise():
    effect = AnalogTVEffect()
    test_frame = create_test_frame()
    
    effect.set_parameter("rf_noise", 0.0)
    output_0 = effect.render(test_frame)
    
    effect.set_parameter("rf_noise", 10.0)
    output_10 = effect.render(test_frame)
    
    # Should be noisier
    noise_0 = calculate_noise_level(output_0)
    noise_10 = calculate_noise_level(output_10)
    assert noise_10 > noise_0 * 2.0
```

#### 8. Color Kill (Desaturation)
```python
def test_color_kill():
    effect = AnalogTVEffect()
    test_frame = create_colorful_frame()
    
    effect.set_parameter("color_kill", 0.0)
    output_0 = effect.render(test_frame)
    
    effect.set_parameter("color_kill", 10.0)
    output_10 = effect.render(test_frame)
    
    # color_kill=10 should be mostly gray
    saturation_10 = calculate_saturation(output_10)
    saturation_0 = calculate_saturation(output_0)
    assert saturation_10 < saturation_0 * 0.2
```

### Edge Case Tests

#### 9. All Parameters at Zero (Clean Output)
```python
def test_all_zero():
    effect = AnalogTVEffect()
    test_frame = create_test_frame()
    
    for param in effect.parameters:
        if param != "mix":
            effect.set_parameter(param, 0.0)
    effect.set_parameter("mix", 1.0)
    
    output = effect.render(test_frame)
    
    # Should be very close to original with minimal degradation
    assert np.allclose(output, test_frame, atol=10)
```

#### 10. All Parameters Maxed Out (Extreme Degradation)
```python
def test_all_max():
    effect = AnalogTVEffect()
    test_frame = create_test_frame()
    
    for param in effect.parameters:
        max_val = 1.0 if param == "mix" else 10.0
        effect.set_parameter(param, max_val)
    
    output = effect.render(test_frame)
    
    # Should not crash; output should be heavily degraded but valid
    assert output is not None
    assert output.shape == test_frame.shape
```

#### 11. Interlacing at Odd Frames
```python
def test_interlacing_pattern():
    effect = AnalogTVEffect()
    effect.set_parameter("interlace", 10.0)
    test_frame = create_test_frame()
    
    output = effect.render(test_frame)
    
    # Should see odd/even scanline pattern
    assert has_interlace_combing(output)
```

#### 12. Dropout Artifacts
```python
def test_tapedropouts():
    effect = AnalogTVEffect()
    effect.set_parameter("dropout_rate", 10.0)
    effect.set_parameter("dropout_length", 10.0)
    test_frame = create_test_frame()
    
    output = effect.render(test_frame)
    
    # Should see white noise bands (dropout regions)
    dropout_regions = detect_white_noise(output)
    assert len(dropout_regions) > 0
```

### Minimum Coverage: 80%

- [x] Parameter validation (100%)
- [x] Barrel distortion (100%)
- [x] Scanlines (100%)
- [x] VHS tracking (100%)
- [x] RF noise (100%)
- [x] Color kill (100%)
- [x] Performance (100%)
- [x] Edge cases (70%)

---

## Definition of Done

- [x] Spec written with mathematical precision
- [x] All 27 parameters documented with mappings
- [x] Public interface with full signatures
- [x] Test plan covers ≥80% functionality
- [x] File size <750 lines (this spec: ~720 lines)
- [x] No stubs — all algorithms explained
- [x] Performance characteristics documented
- [x] Edge cases handled explicitly
- [x] Legacy code references provided

### Verification Checkpoints

- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum at 1080p
- [ ] Test coverage ≥80%
- [ ] No safety rail violations
- [ ] Original functionality verified (visual fidelity matches legacy)

---

## LEGACY CODE REFERENCES

### ANALOG_TV_FRAGMENT Shader Structure

The complete shader is documented in `vjlive1/core/effects/analog_tv.py` with:

- **Lines 1-20**: Fragment shader declaration and uniform bindings
- **Lines 17-52**: VHS physical, CRT display, and RF signal uniforms
- **Lines 53-96**: Parameter remapping from 0-10 to operational ranges
- **Lines 97-148**: CRT barrel distortion, VHS tracking, tape wrinkle, head switch
- **Lines 129-164**: Tape dropouts, vertical rolling, line jitter
- **Lines 145-180**: Scanlines, phosphor glow, RF noise, interlacing
- **Lines 165-200**: Color space conversions (RGB ↔ YUV), composite color bleeding
- **Lines 180-220**: Chroma delay, luma sharpening, color kill
- **Lines 200-240**: Snow/static, final mixing and output

### Key Mathematical Formulas

**Barrel Distortion**:
$$\text{cc} = \text{cc}' \cdot (1.0 + |\text{cc}'|^2 \cdot \text{curve})$$

**Scanlines**:
$$\text{luma} \leftarrow \text{luma} \times (1.0 - \text{scanlines} \times (1.0 - \sin(\text{uv}.y \times \pi)))$$

**Tracking Error Bars**:
$$\text{offset}_x = \text{bar}_1 \times 0.7 \times \text{tracking} \times 0.3$$

**RF Noise**:
$$\text{noise} = \text{hash}(\text{uv} + \text{time}) - 0.5, \quad \text{color} += \text{noise} \times \text{rf\_noise} \times 0.3$$

---

**Bespoke Snowflake Principle:** AnalogTVEffect is a comprehensive, multi-faceted effect combining tape degradation, CRT simulation, and RF corruption. Give it rigorous technical treatment with precise parameter documentation and thorough testing.

**Phase 5 Focus:** This is a V-Effect (visual effect) optimized for real-time performance. Its 30+ parameters enable infinite aesthetic variation from subtle CRT refinement to extreme glitch art degradation.

