# P3-EXT094_InvertEffect.md

## Task: P3-EXT094 — InvertEffect

### Executive Summary

The InvertEffect is a color manipulation filter that performs RGB channel inversion with sophisticated channel selection and brightness-based gating. It supports full negative, channel-specific inversion (red, green, or luma-only), and solarization effects through a luma gate parameter. The effect operates in linear color space and preserves alpha channels, making it suitable for both creative color effects and technical color correction workflows.

### Detailed Behavior and Parameter Interactions

#### Core Algorithm

The effect implements a flexible color inversion system with three independent controls:

1. **Amount**: Controls inversion strength (0 = no inversion, 1 = full inversion)
2. **Channel Mask**: Selects which color channels to invert (all, red only, green only, or luma-only)
3. **Luma Gate**: Brightness threshold that selectively inverts only bright or dark areas

**Processing Pipeline:**
```
Input Color → Luma Calculation → Luma Gate → Channel Selection → Inversion Mix → Output
```

#### Parameter Mapping Table

| Parameter | UI Range (0-10) | Shader Range | Physical Meaning | Default |
|-----------|----------------|--------------|------------------|---------|
| amount | 0-10 | 0.0-1.0 | Inversion strength | 10.0 |
| channel_mask | 0-10 | 0.0-3.0 | Channel selection mode | 0.0 |
| luma_gate | 0-10 | 0.0-1.0 | Brightness threshold | 0.0 |

**Remapping Formulas:**
- `a = amount / 10.0`
- `cm = channel_mask / 10.0 * 3.0` (maps to 0-3 range for mode selection)
- `lg = luma_gate / 10.0`

**Channel Mask Modes:**
- `0.0-0.5`: All channels (RGB)
- `1.5-2.5`: Red channel only
- `2.5-3.0`: Green channel only
- `> 3.0` (effectively): Luma-only (preserves color ratios)

#### Mathematical Formulations

**Luma Calculation:**
```glsl
float luma = dot(input_color.rgb, vec3(0.299, 0.587, 0.114));
```
Uses standard Rec. 709 luminance coefficients.

**Luma Gate:**
```glsl
float gate = smoothstep(lg * 0.5, lg * 0.5 + 0.1, luma);
float effective_a = a * gate;
```
- `lg = 0.0`: gate = 1.0 (invert all)
- `lg = 1.0`: gate ≈ 0.0 (invert none)
- Soft transition of width 0.1 between threshold and threshold+0.1

**Channel-Specific Inversion:**
```glsl
// All channels
inverted = mix(input_color.rgb, 1.0 - input_color.rgb, effective_a);

// Red only
inverted = input_color.rgb;
inverted.r = mix(inverted.r, 1.0 - inverted.r, effective_a);

// Green only
inverted = input_color.rgb;
inverted.g = mix(inverted.g, 1.0 - inverted.g, effective_a);

// Luma-only (preserves chroma)
float inv_luma = 1.0 - luma;
float ratio = inv_luma / max(luma, 0.001);
vec3 luma_inv = input_color.rgb * ratio;
inverted = mix(input_color.rgb, clamp(luma_inv, 0.0, 1.0), effective_a);
```

**Luma-Only Inversion Mathematics:**
The luma-only mode inverts brightness while preserving color hue/saturation:
```
I' = 1 - I
C' = C * (I' / I)  where I = luma, C = chroma
```
This maintains the chromaticity coordinates while flipping luminance.

### Public Interface

#### Class Definition
```python
class InvertEffect(Effect):
    """Color inversion with channel selection and luma gating."""

    PRESETS = {
        "full_negative": {"amount": 10.0, "channel_mask": 0.0, "luma_gate": 0.0},
        "solarize": {"amount": 10.0, "channel_mask": 0.0, "luma_gate": 5.0},
        "red_negative": {"amount": 10.0, "channel_mask": 3.0, "luma_gate": 0.0},
    }

    def __init__(self):
        super().__init__("invert", INVERT_FRAGMENT)
        self.parameters = {
            "amount": 10.0,
            "channel_mask": 0.0,
            "luma_gate": 0.0,
        }
        self.effect_tags = ["color", "invert", "negative", "solarize"]
        self.effect_category = "filter"
        self._parameter_groups = {"invert": ["amount", "channel_mask", "luma_gate"]}
        self._chaos_rating = {"amount": 0.3, "channel_mask": 0.5, "luma_gate": 0.4}
```

#### Parameter Access Methods
```python
def set_parameter(self, name: str, value: float):
    """Set parameter value with validation and remapping."""
    if name not in self.parameters:
        raise ValueError(f"Unknown parameter: {name}")
    
    # Clamp to valid UI range (0-10)
    value = max(0.0, min(10.0, value))
    self.parameters[name] = value
```

### Inputs and Outputs

#### Input Textures
- **`tex0`**: Source image texture (sampler2D)

#### Output
- **`fragColor`**: Inverted color with original alpha preserved

#### Uniform Variables
- **`time`**: Current time in seconds (float) - unused but required by base class
- **`resolution`**: Viewport resolution (vec2) - used for potential future effects
- **`u_mix`**: Final mix factor (float) - controls blend with original

### Edge Cases and Error Handling

#### Zero Luma Division
- **Issue**: Luma-only mode divides by luma: `ratio = inv_luma / max(luma, 0.001)`
- **Protection**: `max(luma, 0.001)` prevents division by zero
- **Behavior**: Near-black pixels (luma < 0.001) will have ratio clamped to 1.0, effectively no inversion

#### Channel Mask Boundary Conditions
- **Issue**: Floating-point comparisons near mode boundaries (0.5, 1.5, 2.5)
- **Protection**: Uses `<` comparisons with clear thresholds
- **Behavior**: Exact boundary values (e.g., 0.5) fall into the next higher mode

#### Luma Gate Extremes
- **`luma_gate = 0.0`**: `smoothstep(0, 0.1, luma)` → gate ≈ 1.0 for all luma > 0.1, partial for 0-0.1
- **`luma_gate = 10.0`**: `smoothstep(5.0, 5.1, luma)` → gate ≈ 0.0 for all luma < 5.1 (always 0 in 0-1 range)
- **Result**: Full inversion to no inversion range covered

#### Color Clamping
- **Issue**: Luma-only inversion can produce out-of-gamut colors
- **Protection**: `clamp(luma_inv, 0.0, 1.0)` ensures valid color range
- **Trade-off**: Clamping may slightly alter intended chroma preservation

#### Alpha Channel
- **Behavior**: Alpha is passed through unchanged: `fragColor = vec4(..., input_color.a)`
- **Rationale**: Inversion should not affect transparency

### Mathematical Formulations

#### Full Inversion
```glsl
vec3 result = mix(input_color.rgb, 1.0 - input_color.rgb, effective_a);
```

#### Channel-Selective Inversion
```glsl
// Single channel c (r, g, or b)
c = mix(c, 1.0 - c, effective_a);
```

#### Luma-Preserving Inversion
```glsl
float luma = dot(input_color.rgb, vec3(0.299, 0.587, 0.114));
float inv_luma = 1.0 - luma;
float ratio = inv_luma / max(luma, 0.001);
vec3 result = input_color.rgb * ratio;
result = mix(input_color.rgb, clamp(result, 0.0, 1.0), effective_a);
```

### Performance Characteristics

#### Computational Complexity
- **Texture Samples**: 1 per pixel
- **Arithmetic Operations**: ~15 FLOPs per pixel
- **Dot Product**: 3 multiplies + 2 adds
- **Trigonometric Functions**: None
- **Branches**: 1-2 conditional branches (channel selection)

#### Bottlenecks
- **Texture Bandwidth**: Single texture fetch, minimal impact
- **Branch Divergence**: Channel selection may cause GPU warp divergence
- **Smoothstep**: 2 multiplications + 1 smooth Hermite interpolation

#### Memory Requirements
- **Uniforms**: 3 floats (amount, channel_mask, luma_gate) + standard base uniforms
- **No Framebuffer**: Pure filter, no feedback buffers needed

#### Optimization Opportunities
- **Branchless Channel Selection**: Could use mix() with masks instead of if-else
- **Precomputed Luma**: If used in chain, could be passed from previous stage
- **Vectorization**: All operations are SIMD-friendly

### Test Plan

#### Unit Tests (Python)
```python
def test_invert_parameter_validation():
    """Test parameter clamping and validation."""
    effect = InvertEffect()
    
    # Test amount remapping
    effect.set_parameter("amount", 5.0)
    assert effect.parameters["amount"] == 5.0
    
    # Test clamping
    effect.set_parameter("amount", -1.0)
    assert effect.parameters["amount"] == 0.0
    effect.set_parameter("amount", 11.0)
    assert effect.parameters["amount"] == 10.0
    
    # Test invalid parameter
    with pytest.raises(ValueError):
        effect.set_parameter("invalid", 1.0)

def test_invert_presets():
    """Test preset configurations."""
    effect = InvertEffect()
    
    # Full negative
    effect.load_preset("full_negative")
    assert effect.parameters["amount"] == 10.0
    assert effect.parameters["channel_mask"] == 0.0
    assert effect.parameters["luma_gate"] == 0.0
    
    # Solarize
    effect.load_preset("solarize")
    assert effect.parameters["luma_gate"] == 5.0
```

#### Integration Tests (OpenGL)
```python
def test_invert_full_negative():
    """Test full color inversion."""
    effect = InvertEffect()
    effect.set_parameter("amount", 10.0)
    effect.set_parameter("channel_mask", 0.0)
    effect.set_parameter("luma_gate", 0.0)
    
    input_color = np.array([0.2, 0.4, 0.6, 1.0], dtype=np.float32)
    result = effect.apply_to_color(input_color)
    
    expected = np.array([0.8, 0.6, 0.4, 1.0], dtype=np.float32)
    assert np.allclose(result, expected, atol=0.01)

def test_invert_red_only():
    """Test red channel inversion only."""
    effect = InvertEffect()
    effect.set_parameter("amount", 10.0)
    effect.set_parameter("channel_mask", 3.0)  # Red mode
    effect.set_parameter("luma_gate", 0.0)
    
    input_color = np.array([0.2, 0.4, 0.6, 1.0], dtype=np.float32)
    result = effect.apply_to_color(input_color)
    
    expected = np.array([0.8, 0.4, 0.6, 1.0], dtype=np.float32)
    assert np.allclose(result, expected, atol=0.01)

def test_invert_luma_gate():
    """Test luma gating (solarization)."""
    effect = InvertEffect()
    effect.set_parameter("amount", 10.0)
    effect.set_parameter("channel_mask", 0.0)
    effect.set_parameter("luma_gate", 5.0)  # 50% threshold
    
    # Dark pixel (luma < 0.5) should not invert
    dark = np.array([0.1, 0.1, 0.1, 1.0], dtype=np.float32)
    result_dark = effect.apply_to_color(dark)
    assert np.allclose(result_dark, dark, atol=0.01)
    
    # Bright pixel (luma > 0.6) should invert
    bright = np.array([0.8, 0.8, 0.8, 1.0], dtype=np.float32)
    result_bright = effect.apply_to_color(bright)
    expected_bright = np.array([0.2, 0.2, 0.2, 1.0], dtype=np.float32)
    assert np.allclose(result_bright, expected_bright, atol=0.01)
```

#### Visual Regression Tests
- **Full Negative**: Verify complete RGB inversion
- **Red Negative**: Verify only red channel inverted
- **Solarize**: Verify threshold-based partial inversion
- **Luma-Only**: Verify color hue preserved while brightness inverted

#### Performance Tests
- **Frame Rate**: Measure FPS at 4K, 1080p, 720p
- **Memory Bandwidth**: Profile texture fetch impact
- **Branch Divergence**: Analyze shader occupancy with mixed channel modes

#### Coverage Targets
- **Python Code**: 90% line coverage (simple class)
- **GLSL Shader**: 100% instruction coverage via color test patterns
- **Integration**: 100% preset coverage

### Definition of Done

#### Technical Requirements
- [ ] All parameters correctly remapped from 0-10 UI range to shader ranges
- [ ] Channel mask mode selection works correctly with boundary conditions
- [ ] Luma gate provides smooth transition with no hard edges
- [ ] Luma-only mode preserves chroma while inverting brightness
- [ ] Division by zero prevented in luma-only mode
- [ ] Alpha channel preserved unchanged
- [ ] Performance meets real-time requirements (>60 FPS at 4K)

#### Testing Requirements
- [ ] Unit tests cover all parameter validation and remapping
- [ ] Integration tests verify each channel mode (RGB, R, G, luma-only)
- [ ] Luma gate threshold tested with dark/bright boundary cases
- [ ] Visual regression tests pass for all presets
- [ ] Performance tests meet frame rate targets

#### Documentation Requirements
- [ ] Complete parameter mapping table with formulas
- [ ] Mathematical formulations for luma calculation and luma-only inversion
- [ ] Channel mask mode decision tree documented
- [ ] Performance analysis with optimization suggestions
- [ ] WebGPU migration notes (uniform buffers, WGSL conversion)

#### Quality Requirements
- [ ] Code follows project style guidelines
- [ ] Comments explain complex luma-preserving algorithm
- [ ] Error handling documented for edge cases
- [ ] No memory leaks or resource management issues

## WebGPU Migration Notes

### Shader Conversion (GLSL 330 → WGSL)
```wgsl
@group(0) @binding(0) var tex0: texture_2d<f32>;
@group(0) @binding(1) var s0: sampler;

struct Uniforms {
    time: f32,
    resolution: vec2,
    u_mix: f32,
    amount: f32,
    channel_mask: f32,
    luma_gate: f32,
};

@group(0) @binding(2) var<uniform> uniforms: Uniforms;

@fragment
fn fs_main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
    let input_color = textureSample(tex0, s0, uv);
    
    let a = uniforms.amount / 10.0;
    let cm = uniforms.channel_mask / 10.0 * 3.0;
    let lg = uniforms.luma_gate / 10.0;
    
    let luma = dot(input_color.rgb, vec3<f32>(0.299, 0.587, 0.114));
    let gate = smoothstep(lg * 0.5, lg * 0.5 + 0.1, luma);
    let effective_a = a * gate;
    
    var inverted: vec3<f32>;
    if (cm < 0.5) {
        inverted = mix(input_color.rgb, vec3<f32>(1.0) - input_color.rgb, effective_a);
    } else if (cm < 1.5) {
        inverted = input_color.rgb;
        inverted.r = mix(inverted.r, 1.0 - inverted.r, effective_a);
    } else if (cm < 2.5) {
        inverted = input_color.rgb;
        inverted.g = mix(inverted.g, 1.0 - inverted.g, effective_a);
    } else {
        let inv_luma = 1.0 - luma;
        let ratio = inv_luma / max(luma, 0.001);
        let luma_inv = input_color.rgb * ratio;
        inverted = mix(input_color.rgb, clamp(luma_inv, vec3<f32>(0.0), vec3<f32>(1.0)), effective_a);
    }
    
    return vec4<f32>(clamp(inverted, vec3<f32>(0.0), vec3<f32>(1.0)), input_color.a);
}
```

### Uniform Buffer Layout
```rust
#[repr(C)]
#[derive(Debug, Copy, Clone)]
struct InvertUniforms {
    time: f32,
    resolution: vec2,
    u_mix: f32,
    amount: f32,
    channel_mask: f32,
    luma_gate: f32,
    _padding: f32,  // Align to 16-byte boundary
}
```

### Bind Group Layout
```rust
let bind_group_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
    entries: &[
        wgpu::BindGroupLayoutEntry {
            binding: 0,
            visibility: wgpu::ShaderStages::FRAGMENT,
            ty: wgpu::BindingType::Texture {
                sample_type: wgpu::TextureSampleType::Float { filterable: true },
                view_dimension: wgpu::TextureViewDimension::D2,
                multisampled: false,
            },
            count: None,
        },
        wgpu::BindGroupLayoutEntry {
            binding: 1,
            visibility: wgpu::ShaderStages::FRAGMENT,
            ty: wgpu::BindingType::Sampler {
                filtering: true,
                comparison: false,
            },
            count: None,
        },
        wgpu::BindGroupLayoutEntry {
            binding: 2,
            visibility: wgpu::ShaderStages::FRAGMENT,
            ty: wgpu::BindingType::Buffer {
                ty: wgpu::BufferBindingType::Uniform,
                has_dynamic_offset: false,
                min_binding_size: None,
            },
            count: None,
        },
    ],
    label: Some("invert_bind_group_layout"),
});
```

### Performance Considerations
- **WGSL smoothstep**: Same implementation as GLSL, no performance difference
- **Branching**: WGSL handles if-else similarly; consider branchless for optimal GPU utilization
- **Uniform Buffer**: Ensure proper alignment (16-byte) for WGSL compatibility

## Legacy Code Analysis

### Source Location
- **Primary**: `/home/happy/Desktop/claude projects/vjlive/core/effects/color.py` (lines 686-760)
- **Fallback**: `/home/happy/Desktop/claude projects/vjlive/core/effects/legacy_trash/color.py` (incomplete/corrupted)
- **Plugin**: `/home/happy/Desktop/claude projects/vjlive/plugins/vcore/color.py` (may contain wrapper)

### Key Implementation Details
- **Base Class**: Inherits from `Effect` base class
- **Shader Registration**: Passes `INVERT_FRAGMENT` string to parent constructor
- **Parameter System**: Dictionary-based with default values
- **Effect Metadata**: Tags, category, parameter groups, chaos rating
- **Presets**: Three built-in presets for common use cases

### Design Patterns
- **Parameter Groups**: Logical grouping for UI organization (`_parameter_groups`)
- **Chaos Rating**: Quantifies effect intensity for automated mixing (0.0-1.0 scale)
- **Effect Tags**: Used for filtering and categorization in UI

### Potential Issues
- **Branch Divergence**: If-else chain for channel selection may reduce GPU efficiency
- **Luma-Only Edge Case**: Division by near-zero can cause color artifacts on very dark pixels
- **Smoothstep Width**: Fixed 0.1 width may not be optimal for all luma ranges
