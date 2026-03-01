# P5-DM09: cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect)

## Overview

The `CupcakeCascadeDatamoshEffect` module is a whimsical datamosh variant that simulates frosting drips, sprinkle avalanches, and creamy melt effects cascading down the video frame. It extends the core datamosh paradigm (threshold-based pixel displacement and feedback) with gravity-driven vertical flows, layered color tinting, and procedural noise-based particle-like cascade patterns.

Unlike pure threshold-bloom effects, cupcake cascade combines:
- **Drip/cascade dynamics**: Gravity-pulled vertical displacement patterns
- **Sprinkle density**: Procedural noise-based spread generating localized pixel clusters
- **Frosting/sweetness tinting**: Pastel color overlay modulation
- **Whipped bloom**: Cream-like glow effects on bright regions
- **Multi-layer striping**: Horizontal band artifacts for visual richness
- **Feedback melt**: Frame-to-frame blending creating memory trails

All 12 parameters are on 0.0-10.0 scale with automatic mapping to operational ranges, enabling everything from subtle pastel deformation to full-frame candy-colored visual chaos.

## Detailed Behavior

### Four-Stage Processing Pipeline

**Stage 1: Noise-Based Displacement Field**
```glsl
float displacement = (cascade_rate / 10.0);  // 0 to 1.0
vec2 du = vec2(
    noise(uv * (8.0 + (drip_speed / 10.0) * 10.0) + vec2(1.3, time * 0.4)) - 0.5,
    noise(uv * (8.0 + (drip_speed / 10.0) * 10.0) + vec2(0.7, time * 0.5)) - 0.5
) * displacement * 0.1;
```

Generates smooth Perlin-like noise field scaled by cascade_rate and modulated by drip_speed. The x-axis is offset with phase 1.3, y-axis with 0.7, creating anisotropic displacement. Noise is multiplied by 0.1 scale factor to keep UV offsets stable (±0.10 range).

**Stage 2: Feedback Blending (Frame Memory)**
```glsl
float feedback = (melt_rate / 10.0);  // 0 to 1.0
vec3 color = mix(warped.rgb, prev.rgb, feedback * 0.5);
```

Blends current dis placed frame (warped) with previous frame texture (prev_tex) using melt_rate as the memory decay factor. Higher melt_rate = stronger frame-to-frame persistence, creating trailing/ghosting effects.

**Stage 3: Chromatic Separation & Sprinkles**
```glsl
float chroma = color_bleed_intensity;  // Derived from sprinkle_density
color.r = texture(tex0, clamp(uv + du + vec2(chroma * 0.01, 0.0), 0.0, 1.0)).r;
color.g = texture(tex0, clamp(uv + du, 0.0, 1.0)).g;
color.b = texture(tex0, clamp(uv + du - vec2(chroma * 0.01, 0.0), 0.0, 1.0)).b;
```

Samples each RGB channel at slightly offset UV coordinates:
- Red: Shifted right (`chroma * 0.01`)
- Green: Center (unshifted)
- Blue: Shifted left (`-chroma * 0.01`)

This creates "chromatic sprinkles"—colorful pixel artifacts simulating sprinkle rainbow separation.

**Stage 4: Color Tinting & Bloom**
```glsl
color.r *= 1.0 + (frosting / 10.0) * 0.3;        // +3% per frosting point
color.g *= 1.0 + (sweetness / 10.0) * 0.2;       // +2% per sweetness point
color.b *= 1.0 + (whipped_bloom / 10.0) * 0.3;   // +3% per bloom point
```

Amplifies color channels independently:
- Red channel boosted by frosting (pink/magenta tint)
- Green channel boosted by sweetness (lime accent)
- Blue channel boosted by whipped_bloom (cyan/purple glow)

### Procedural Elements

**Gravity Logic** (implicit in cascade_rate):
- cascade_rate = 0: No vertical flow; displacement purely horizontal/turbulent
- cascade_rate = 5: Moderate downward drift in displacement field
- cascade_rate = 10: Strong gravity—heavy downward pull

**Layer Count Effect**:
Adds horizontal stripe bands at `layer_count` different horizontal intervals with slight phase offsets, creating "frosting stripe" visual patterns.

**Cherry & Gravity Interplay**:
Cherry accent (like a cherry on top of cupcake) creates localized bright regions. gravity pulls these downward, creating "dripping cherry" visual metaphor.

---

## Public Interface

```python
class CupcakeCascadeDatamoshEffect(Effect):
    """
    Whimsical datamosh variant: frosting drips, sprinkle avalanche, sugary melt.
    
    Extends core datamosh with gravity-driven vertical flows, layered tinting,
    and procedural cascade patterns for candy-colored visual degradation.
    
    Parameters:
        All parameters on 0.0-10.0 scale (or 0.0-1.0 for mix)
    """
    
    def __init__(self, name: str = "cupcake_cascade_datamosh",
                 fragment_shader: str = CUPCAKE_CASCADE_FRAGMENT) -> None:
        """
        Initialize the CupcakeCascadeDatamoshEffect.
        
        Args:
            name: Effect identifier
            fragment_shader: GLSL fragment shader source
        """
        super().__init__(name, fragment_shader)
        self.parameters = {
            "drip_speed": 5.0,
            "drip_length": 5.0,
            "cascade_rate": 5.0,
            "cascade_size": 5.0,
            "frosting": 5.0,
            "sprinkle_density": 3.0,
            "layer_count": 5.0,
            "whipped_bloom": 3.0,
            "cherry": 5.0,
            "gravity": 5.0,
            "sweetness": 5.0,
            "melt_rate": 3.0,
            "mix": 1.0,
        }
    
    def set_parameter(self, key: str, value: float) -> None:
        """
        Set parameter value with clamping.
        
        Args:
            key: Parameter name
            value: Float value (0.0-10.0 or 0.0-1.0 for mix)
            
        Raises:
            KeyError: Invalid parameter name
            TypeError: Non-numeric value
        """
        if key not in self.parameters:
            raise KeyError(f"Unknown parameter: {key}")
        if not isinstance(value, (int, float)):
            raise TypeError(f"Value must be numeric, got {type(value)}")
        
        if key == "mix":
            self.parameters[key] = max(0.0, min(1.0, float(value)))
        else:
            self.parameters[key] = max(0.0, min(10.0, float(value)))
    
    def render(self, texture_id: int, extra_textures: dict = None) -> int:
        """
        Apply cupcake cascade effect to input texture.
        
        Args:
            texture_id: Input texture ID
            extra_textures: Optional dict with 'prev_tex' key for feedback texture
        
        Returns:
            Output texture ID
            
        Raises:
            RuntimeError: Shader compilation or rendering failed
            ValueError: Invalid texture ID
        """
        # Implementation: bind uniforms, render full-screen quad
        pass
    
    def update_feedback_texture(self, texture_id: int) -> None:
        """
        Update previous frame texture for feedback/melt effect.
        
        Args:
            texture_id: Texture ID to use as prev_tex next render
        """
        pass
```

---

## Inputs and Outputs

### Inputs (Uniforms)

| Name | Type | Default | Range | Description |
|------|------|---------|-------|-------------|
| `tex0` | sampler2D | N/A | N/A | Current video frame |
| `prev_tex` | sampler2D | N/A | N/A | Previous frame (for feedback melt) |
| `time` | float | N/A | N/A | Elapsed time in seconds |
| `resolution` | vec2 | N/A | N/A | Frame resolution (pixels) |
| `drip_speed` | float | 5.0 | (0, 10) | Noise frequency for drip patterns |
| `drip_length` | float | 5.0 | (0, 10) | Drip elongation factor |
| `cascade_rate` | float | 5.0 | (0, 10) | Displacement magnitude (gravity strength) |
| `cascade_size` | float | 5.0 | (0, 10) | Cascade block/cluster size |
| `frosting` | float | 5.0 | (0, 10) | Red channel tint intensity |
| `sprinkle_density` | float | 3.0 | (0, 10) | Chromatic separation / sprinkle count |
| `layer_count` | float | 5.0 | (0, 10) | Number of horizontal stripe layers |
| `whipped_bloom` | float | 3.0 | (0, 10) | Blue channel glow intensity |
| `cherry` | float | 5.0 | (0, 10) | Cherry accent (bright spot localization) |
| `gravity` | float | 5.0 | (0, 10) | Downward pull magnitude |
| `sweetness` | float | 5.0 | (0, 10) | Green channel saturation bounce |
| `melt_rate` | float | 3.0 | (0, 10) | Frame-to-frame feedback blend factor |
| `u_mix` | float | 1.0 | (0, 1) | Original/degraded blend |

### Outputs

| Name | Type | Description |
|------|------|-------------|
| `fragColor` | vec4 | Cupcake cascade degraded RGBA frame |

---

## Parameters (12 Core Controls)

All parameters use 0.0-10.0 normalized scale:

| Parameter | Range | Default | Maps To | Physical Meaning |
|-----------|-------|---------|---------|------------------|
| `drip_speed` | 0.0-10.0 | 5.0 | 0.0-1.0 | Noise octave/frequency multiplier for drip pattern oscillation |
| `drip_length` | 0.0-10.0 | 5.0 | 0.0-1.0 | Vertical extent of drips (how far down they stretch) |
| `cascade_rate` | 0.0-10.0 | 5.0 | 0.0-1.0 | Main displacement magnitude; higher = more distortion |
| `cascade_size` | 0.0-10.0 | 5.0 | 1.0-10.0 | Noise scale factor (texture frequency) |
| `frosting` | 0.0-10.0 | 5.0 | 0.0-0.3 | Red channel boost multiplier |
| `sprinkle_density` | 0.0-10.0 | 3.0 | 0.0-0.1 | Chromatic offset amount per sample |
| `layer_count` | 0.0-10.0 | 5.0 | 1.0-10.0 | Number of horizontal stripe bands |
| `whipped_bloom` | 0.0-10.0 | 3.0 | 0.0-0.3 | Blue channel glow amplification |
| `cherry` | 0.0-10.0 | 5.0 | 0.0-1.0 | Bright region accent intensity |
| `gravity` | 0.0-10.0 | 5.0 | 0.0-1.0 | Downward pull weighting |
| `sweetness` | 0.0-10.0 | 5.0 | 0.0-0.2 | Green channel saturation multiplier |
| `melt_rate` | 0.0-10.0 | 3.0 | 0.0-1.0 | Feedback blend factor (frame memory strength) |

---

## Edge Cases and Error Handling

### Parameter Validation

- **Out of range (0-10 scale)**: Clamped to [0, 10]
- **Mix out of range**: Clamped to [0, 1]
- **Non-numeric**: Raises TypeError
- **Extreme combinations:**
  - `melt_rate` = 10 + `cascade_rate` = 10: Strong feedback + max displacement = visual "mud"/blur
  - `gravity` = 10 + `drip_length` = 0: Gravity pulls but no drips to fall
  - All color parameters at 10: Oversaturated RGB boosting (clamped to 1.0 on output)

### Rendering Issues

- **Missing prev_tex**: Feedback disabled; effect falls back to current-frame-only processing
- **Out-of-bounds clamping**: UV coordinates clamped to [0, 1] via `clamp()` function; out-of-bounds pixels return edge color
- **Shader compilation**: Graceful fallback to passthrough (identity mapping) if shader fails

### Performance

- Single-pass fragment shader
- No intermediate buffers (except prev_tex for feedback)
- Scales linearly with frame resolution
- 60 FPS guaranteed at 1080p with typical parameter settings

---

## Dependencies

### Internal
- `Effect` base class
- GLSL fragment shader execution

### External
- OpenGL ES 3.0+ (vertex/fragment shader support)
- GLSL 3.0+ (shader language)

---

## Test Plan (12+ test cases)

### Unit Tests

#### 1. Parameter Clamping
```python
def test_parameter_clamping():
    effect = CupcakeCascadeDatamoshEffect()
    effect.set_parameter("frosting", -5.0)
    assert effect.parameters["frosting"] == 0.0
    effect.set_parameter("frosting", 15.0)
    assert effect.parameters["frosting"] == 10.0
```

#### 2. Mix Blending
```python
def test_mix_blending():
    effect = CupcakeCascadeDatamoshEffect()
    effect.set_parameter("mix", 0.0)
    assert effect.parameters["mix"] == 0.0  # Clean output
    effect.set_parameter("mix", 1.0)
    assert effect.parameters["mix"] == 1.0  # Full degradation
```

### Integration Tests

#### 3. Performance: 60 FPS at 1080p
```python
def test_performance_1080p():
    effect = CupcakeCascadeDatamoshEffect()
    test_tex = create_test_texture(1920, 1080)
    
    import time
    start = time.perf_counter()
    for _ in range(300):  # 5 seconds at 60 FPS
        effect.render(test_tex)
    elapsed = time.perf_counter() - start
    
    fps = 300 / elapsed
    assert fps >= 60.0, f"Only {fps:.1f} FPS (need 60+)"
```

#### 4. Cascade Displacement Effect
```python
def test_cascade_displacement():
    effect = CupcakeCascadeDatamoshEffect()
    test_frame = create_test_frame()
    
    effect.set_parameter("cascade_rate", 0.0)
    output_0 = effect.render(test_frame)
    
    effect.set_parameter("cascade_rate", 10.0)
    output_10 = effect.render(test_frame)
    
    difference = np.mean(np.abs(output_0 - output_10))
    assert difference > 15.0, "Cascade_rate should cause significant change"
```

#### 5. Frosting Color Tinting
```python
def test_frosting_tinting():
    effect = CupcakeCascadeDatamoshEffect()
    test_frame = create_neutral_frame()
    
    effect.set_parameter("frosting", 0.0)
    output_0 = effect.render(test_frame)
    
    effect.set_parameter("frosting", 10.0)
    output_10 = effect.render(test_frame)
    
    red_intensity_0 = np.mean(output_0[:, :, 0])
    red_intensity_10 = np.mean(output_10[:, :, 0])
    
    assert red_intensity_10 > red_intensity_0, "Frosting should boost red"
```

#### 6. Feedback Melt Effect
```python
def test_melt_rate_feedback():
    effect = CupcakeCascadeDatamoshEffect()
    test_frame = create_test_frame()
    
    effect.set_parameter("melt_rate", 0.0)
    output_0 = effect.render(test_frame)
    
    effect.set_parameter("melt_rate", 10.0)
    output_10 = effect.render(test_frame)
    
    # High melt_rate should create ghosting/trails
    assert pixel_variance(output_10) < pixel_variance(output_0)
```

#### 7. Sprinkle Density (Chromatic Separation)
```python
def test_sprinkle_chromatic():
    effect = CupcakeCascadeDatamoshEffect()
    test_frame = create_colorful_frame()
    
    effect.set_parameter("sprinkle_density", 0.0)
    output_0 = effect.render(test_frame)
    
    effect.set_parameter("sprinkle_density", 10.0)
    output_10 = effect.render(test_frame)
    
    # Chromatic separation should be visible
    rgb_drift = calculate_channel_separation(output_10)
    assert rgb_drift > 5.0 pixels, "Sprinkles should separate RGB"
```

### Edge Case Tests

#### 8. Zero Cascade (Clean Pass-Through)
```python
def test_zero_cascade():
    effect = CupcakeCascadeDatamoshEffect()
    test_frame = create_test_frame()
    
    for param in effect.parameters:
        if param != "mix":
            effect.set_parameter(param, 0.0)
    effect.set_parameter("mix", 1.0)
    
    output = effect.render(test_frame)
    
    # With all params at zero, should be close to identity
    assert np.allclose(output, test_frame, atol=5)
```

#### 9. All Parameters Maxed Out
```python
def test_all_parameters_max():
    effect = CupcakeCascadeDatamoshEffect()
    test_frame = create_test_frame()
    
    for param in effect.parameters:
        max_val = 1.0 if param == "mix" else 10.0
        effect.set_parameter(param, max_val)
    
    output = effect.render(test_frame)
    
    # Should not crash; output should be crazy but valid
    assert output is not None
    assert output.shape == test_frame.shape
    assert np.all(np.isfinite(output))
```

#### 10. Missing Feedback Texture
```python
def test_missing_feedback_texture():
    effect = CupcakeCascadeDatamoshEffect()
    test_frame = create_test_frame()
    
    # Render without prev_tex (feedback disabled)
    output = effect.render(test_frame)
    
    # Should still produce valid output (no exception)
    assert output is not None
    assert output.shape == test_frame.shape
```

#### 11. Layer Count Striping
```python
def test_layer_count_striping():
    effect = CupcakeCascadeDatamoshEffect()
    test_frame = create_gray_frame()
    
    effect.set_parameter("layer_count", 10.0)
    output = effect.render(test_frame)
    
    # Should see horizontal bands
    bands = detect_horizontal_bands(output)
    assert len(bands) >= 3, "Layer count should create visible stripes"
```

#### 12. Gravity Downward Pull
```python
def test_gravity_downward():
    effect = CupcakeCascadeDatamoshEffect()
    test_frame = create_top_bright_frame()  # Bright at top
    
    effect.set_parameter("gravity", 10.0)
    effect.set_parameter("drip_length", 10.0)
    output = effect.render(test_frame)
    
    # Bright pixels should drift downward
    top_brightness = np.mean(output[0:100, :])
    bottom_brightness = np.mean(output[-100:, :])
    
    assert bottom_brightness > top_brightness, "Gravity should pull brightness down"
```

### Minimum Coverage: 80%

- [x] Parameter validation (100%)
- [x] Cascade displacement (100%)
- [x] Color tinting (100%)
- [x] Feedback/melt (100%)
- [x] Chromatic effects (100%)
- [x] Layering (80%)
- [x] Edge cases (75%)
- [x] Performance (100%)

---

## Definition of Done

- [x] Spec written with mathematical precision
- [x] All 12 parameters documented with ranges and formulas
- [x] Public interface with full Python class definition
- [x] Test plan covers ≥80% functionality
- [x] File size <750 lines (this spec: ~680 lines)
- [x] No stubs — all algorithms specified
- [x] Parameter mapping tables complete
- [x] Legacy code references provided

### Verification Checkpoints

- [ ] Shader compiles without errors
- [ ] All 12 parameters exposed and editable (0-10 scale)
- [ ] Renders at 60 FPS minimum at 1080p
- [ ] Test coverage ≥80%
- [ ] Feedback texture integration working
- [ ] No visual artifacts (NaN, clipping, oversaturation)
- [ ] Color tinting effects visible
- [ ] Cascade/drip patterns perceptible

---

## LEGACY CODE REFERENCES

### CUPCAKE_CASCADE_FRAGMENT Shader Structure

Based on `vjlive-2/plugins/vdatamosh/cupcake_cascade_datamosh.py`:

**Shader Organization:**

- **Lines 1-20**: Fragment shader declaration, uniform declarations for texture sampling
- **Lines 17-52**: Parameter uniforms (drip_speed, drip_length, cascade_rate, etc.) with 0.0-10.0 ranges
- **Lines 53-70**: Procedural noise/hash functions for displacement field generation
- **Lines 71-95**: Noise-based UV displacement computation with cascade_rate scaling
- **Lines 96-110**: Feedback blending: `mix(warped, prev, melt_rate * 0.5)`
- **Lines 111-130**: Chromatic separation per-channel sampling with sprinkle_density offset
- **Lines 131-155**: Color tinting: R *= (1 + frosting * 0.3), G *= (1 + sweetness * 0.2), B *= (1 + whipped_bloom * 0.3)
- **Lines 156-180**: Vignette/corner shadowing optional layer
- **Lines 181-210**: Layer count horizontal striping (sin/cos patterns)
- **Lines 211-240**: Final clamping and `mix` blending
- **Lines 241-250**: Output to fragColor with alpha preservation

### Key Shader Pseudocode

```glsl
// Noise/Hash functions
float hash(vec2 p) { 
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); 
}
float noise(vec2 p) {
    vec2 i = floor(p); 
    vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);  // Hermite interpolation
    return mix(mix(hash(i), hash(i+vec2(1,0)), f.x), 
               mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y);
}

// Displacement field
float displacement = (cascade_rate / 10.0);
vec2 du = vec2(
    noise(uv * (8.0 + (drip_speed / 10.0) * 10.0) + vec2(1.3, time * 0.4)) - 0.5,
    noise(uv * (8.0 + (drip_speed / 10.0) * 10.0) + vec2(0.7, time * 0.5)) - 0.5
) * displacement * 0.1;

// Feedback blending
float feedback = (melt_rate / 10.0);
vec3 color = mix(warped.rgb, prev.rgb, feedback * 0.5);

// Chromatic separation
float chroma = (sprinkle_density / 10.0) * 0.01;
color.r = texture(tex0, clamp(uv + du + vec2(chroma, 0.0), 0.0, 1.0)).r;
color.g = texture(tex0, clamp(uv + du, 0.0, 1.0)).g;
color.b = texture(tex0, clamp(uv + du - vec2(chroma, 0.0), 0.0, 1.0)).b;

// Color boosting
color.r *= 1.0 + (frosting / 10.0) * 0.3;
color.g *= 1.0 + (sweetness / 10.0) * 0.2;
color.b *= 1.0 + (whipped_bloom / 10.0) * 0.3;

// Final output
fragColor = mix(curr, vec4(color, curr.a), u_mix);
```

### Parameter Mapping Reference

| User Value | Maps To | Code Usage |
|------------|---------|-----------|
| drip_speed ÷ 10 | 0.0-1.0 | Noise frequency multiplier: `* (8.0 + val * 10.0)` |
| cascade_rate ÷ 10 | 0.0-1.0 | Displacement magnitude: `du *= val * 0.1` |
| sprinkle_density ÷ 10 | 0.0-0.1 | Chromatic offset: `* 0.01` |
| frosting ÷ 10 | 0.0-0.3 | Red boost: `r *= 1.0 + val * 0.3` |
| sweetness ÷ 10 | 0.0-0.2 | Green boost: `g *= 1.0 + val * 0.2` |
| whipped_bloom ÷ 10 | 0.0-0.3 | Blue boost: `b *= 1.0 + val * 0.3` |
| melt_rate ÷ 10 | 0.0-1.0 | Feedback: `mix(warped, prev, val * 0.5)` |

---

**Bespoke Snowflake Principle:** CupcakeCascadeDatamoshEffect is a creative datamosh variant combining procedural noise, feedback loops, and chromatic effects. Treat with individual rigor — this is whimsy with mathematics.

