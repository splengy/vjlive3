# P3-EXT093_InfiniteFeedbackEffect.md
1--7 | # Spec Template — Focus on Technical Accuracy
8--15 | ## Task: P3-EXT093 — InfiniteFeedbackEffect
16--19 | ## Detailed Behavior and Parameter Interactions
20--23 | ## Public Interface
24--27 | ## Inputs and Outputs
28--31 | ## Edge Cases and Error Handling
32--35 | ## Mathematical Formulations
36--39 | ## Performance Characteristics
40--45 | ## Test Plan
46--59 | ## Definition of Done

# P3-EXT093_InfiniteFeedbackEffect.md

## Task: P3-EXT093 — InfiniteFeedbackEffect

### Executive Summary

The InfiniteFeedbackEffect is a BPM-synced feedback loop effect that creates infinite recursive visual patterns through rotation, zoom, and temporal delay accumulation. It samples from both the current frame and a previous frame buffer, applying synchronized transformations to create spiraling, zooming feedback patterns that evolve over time. The effect is particularly effective for creating psychedelic, kaleidoscopic visuals with rhythmic synchronization to audio BPM.

### Detailed Behavior and Parameter Interactions

#### Core Algorithm

The effect implements a dual-source feedback system:

1. **Current Frame Source**: Direct sampling from the current input texture (`tex0`)
2. **Accumulated Feedback Source**: Sampling from the previous frame buffer (`texPrev`) with transformations applied

**Transformation Pipeline:**
- **Rotation**: BPM-synced angular rotation around center point
- **Zoom**: Progressive zoom accumulation over time
- **Temporal Delay**: Simulated delay with sinusoidal offset
- **Decay**: Exponential decay of feedback intensity per frame

#### Parameter Mapping Table

| Parameter | UI Range (0-10) | Shader Range | Physical Meaning | Default |
|-----------|----------------|--------------|------------------|---------|
| amount | 0-10 | 0.0-1.0 | Feedback strength | 0.9 |
| decay | 0-10 | 0.0-0.1 | Per-frame decay rate | 0.05 |
| rotate_speed | 0-10 | 0.0-1.0 | Rotation speed (radians/sec) | 0.1 |
| zoom_speed | 0-10 | 0.0-0.1 | Zoom accumulation rate | 0.01 |
| delay | 0-10 | 0.0-2.0 | Temporal delay factor | 1.0 |
| bpm | 0-10 | 60.0-300.0 | Beats Per Minute | 120.0 |

**Remapping Formulas:**
- `amount = ui_amount * 0.1`
- `decay = ui_decay * 0.01`
- `rotate_speed = ui_rotate_speed * 0.1`
- `zoom_speed = ui_zoom_speed * 0.01`
- `delay = ui_delay * 0.2`
- `bpm = ui_bpm * 24.0 + 60.0`

#### Mathematical Formulations

**BPM-Synced Rotation:**
```glsl
float beat_time = time * (bpm / 60.0);
float angle = beat_time * rotate_speed;
```

**Zoom Accumulation:**
```glsl
float zoom = 1.0 + time * zoom_speed * 0.1;
```

**Temporal Delay Offset:**
```glsl
vec2 delay_offset = vec2(sin(time * delay), cos(time * delay)) * 0.02;
```

**Feedback Decay:**
```glsl
feedback.rgb *= (1.0 - decay);
```

**Final Mixing:**
```glsl
vec4 result = mix(current, feedback, amount);
fragColor = mix(current, result, mix * 0.8);
```

### Public Interface

#### Class Definition
```python
class InfiniteFeedbackEffect(Effect):
    def __init__(self):
        super().__init__("infinite_feedback", INFINITE_FEEDBACK_FRAGMENT)
        self.parameters = {
            "amount": 0.9,
            "decay": 0.05,
            "rotate_speed": 0.1,
            "zoom_speed": 0.01,
            "delay": 1.0,
            "bpm": 120.0,
        }
```

#### Parameter Access Methods
```python
def set_parameter(self, name: str, value: float):
    """Set parameter value with validation and remapping."""
    
    # Validate parameter name
    if name not in self.parameters:
        raise ValueError(f"Unknown parameter: {name}")
    
    # Remap UI value (0-10) to shader range
    if name == "amount":
        self.parameters[name] = value * 0.1
    elif name == "decay":
        self.parameters[name] = value * 0.01
    elif name == "rotate_speed":
        self.parameters[name] = value * 0.1
    elif name == "zoom_speed":
        self.parameters[name] = value * 0.01
    elif name == "delay":
        self.parameters[name] = value * 0.2
    elif name == "bpm":
        self.parameters[name] = value * 24.0 + 60.0
```

### Inputs and Outputs

#### Input Textures
- **`tex0`**: Current frame texture (sampler2D)
- **`texPrev`**: Previous frame buffer texture (sampler2D) - required for feedback loop

#### Output
- **`fragColor`**: Final composited color with feedback applied

#### Uniform Variables
- **`time`**: Current time in seconds (float)
- **`resolution`**: Viewport resolution (vec2)
- **`mix`**: Final mix factor (float, typically 0.5)

### Edge Cases and Error Handling

#### Missing Previous Frame Buffer
- **Issue**: `texPrev` may not be available on first frame
- **Solution**: Fallback to current frame only when `texPrev` is invalid
- **Implementation**: Check texture validity before sampling

#### BPM Synchronization Edge Cases
- **Zero BPM**: Division by zero in beat calculation
- **Negative BPM**: Invalid musical tempo
- **Solution**: Clamp BPM to valid range (60-300 BPM)

#### Parameter Boundary Conditions
- **Amount = 0**: No feedback, pure current frame
- **Amount = 1**: Full feedback, potential instability
- **Decay = 0**: No decay, infinite accumulation (may cause overflow)
- **Decay = 1**: Complete decay, no feedback persistence

#### Numerical Stability
- **Zoom Accumulation**: Can cause texture coordinate overflow
- **Rotation**: Large angles may cause precision issues
- **Solution**: Normalize texture coordinates and use modulo for angles

### Mathematical Formulations

#### Coordinate Transformation
```glsl
// Center coordinates around origin
vec2 centered = uv - 0.5;

// Apply rotation
float s = sin(angle);
float c = cos(angle);
vec2 rotated_uv = vec2(
    centered.x * c - centered.y * s,
    centered.x * s + centered.y * c
);

// Apply zoom
float zoom = 1.0 + time * zoom_speed * 0.1;
rotated_uv /= zoom;
rotated_uv += 0.5;  // Re-center
```

#### Feedback Mixing Algorithm
```glsl
// Sample current frame
vec4 current = texture(tex0, uv);

// Sample transformed feedback
vec4 feedback = texture(texPrev, rotated_uv);

// Apply temporal delay
vec2 delay_offset = vec2(sin(time * delay), cos(time * delay)) * 0.02;
vec4 delayed = texture(texPrev, uv + delay_offset);

// Combine feedback sources
feedback = mix(feedback, delayed, 0.3);

// Apply decay
feedback.rgb *= (1.0 - decay);

// Mix with current frame
vec4 result = mix(current, feedback, amount);

// Final output mixing
fragColor = mix(current, result, mix * 0.8);
```

### Performance Characteristics

#### Computational Complexity
- **Texture Samples**: 3-4 samples per pixel (current, feedback, delayed, final mix)
- **Trigonometric Functions**: 2 sin/cos calls per pixel (rotation, delay)
- **Arithmetic Operations**: ~20 FLOPs per pixel
- **Memory Bandwidth**: 3-4 texture fetches per pixel

#### Bottlenecks
1. **Trigonometric Functions**: sin/cos are expensive on mobile GPUs
2. **Texture Fetches**: Multiple dependent texture reads
3. **Feedback Loop**: Requires previous frame buffer, increasing memory usage

#### Optimization Opportunities
- **Pre-computed Rotation**: Cache rotation matrices for static BPM
- **Reduced Sampling**: Use lower resolution for feedback buffer
- **Temporal Reuse**: Reuse previous frame calculations

#### Memory Requirements
- **Current Frame**: Full resolution texture
- **Previous Frame**: Full resolution texture (feedback buffer)
- **Total**: 2x framebuffer memory

### Test Plan

#### Unit Tests (Python)
```python
def test_infinite_feedback_parameters():
    """Test parameter validation and remapping."""
    effect = InfiniteFeedbackEffect()
    
    # Test valid parameter ranges
    effect.set_parameter("amount", 5.0)  # Should map to 0.5
    assert effect.parameters["amount"] == 0.5
    
    effect.set_parameter("bpm", 10.0)  # Should map to 300.0
    assert effect.parameters["bpm"] == 300.0
    
    # Test invalid parameters
    with pytest.raises(ValueError):
        effect.set_parameter("invalid_param", 1.0)
```

#### Integration Tests (OpenGL)
```python
def test_infinite_feedback_rendering():
    """Test feedback effect rendering with mock textures."""
    effect = InfiniteFeedbackEffect()
    
    # Create mock textures
    current_texture = create_test_texture()
    previous_texture = create_test_texture()
    
    # Apply effect
    result = effect.apply_uniforms(
        time=1.0,
        resolution=(1920, 1080),
        tex0=current_texture,
        texPrev=previous_texture
    )
    
    # Verify output
    assert result.shape == current_texture.shape
    assert np.any(result != current_texture)  # Should be transformed
```

#### Visual Regression Tests
- **Static Pattern Test**: Apply to simple gradient, verify spiral pattern
- **BPM Sync Test**: Verify rotation speed matches BPM setting
- **Decay Test**: Verify feedback intensity decreases over time
- **Edge Case Test**: Test with extreme parameter values

#### Performance Tests
- **Frame Rate Test**: Measure FPS at different resolutions
- **Memory Usage Test**: Monitor GPU memory consumption
- **Bottleneck Analysis**: Profile trigonometric function usage

#### Coverage Targets
- **Python Code**: 85% line coverage
- **GLSL Shader**: 90% instruction coverage (via mock testing)
- **Integration**: 80% end-to-end coverage

### Definition of Done

#### Technical Requirements
- [ ] All parameters correctly remapped from 0-10 UI range to shader ranges
- [ ] BPM synchronization works correctly across valid tempo range
- [ ] Feedback loop maintains stability with decay parameter
- [ ] Edge cases handled gracefully (missing previous frame, extreme values)
- [ ] Performance meets real-time requirements (>30 FPS at 1080p)
- [ ] Memory usage stays within reasonable bounds (2x framebuffer)

#### Testing Requirements
- [ ] Unit tests cover all parameter validation and remapping
- [ ] Integration tests verify correct rendering with mock textures
- [ ] Visual regression tests pass for key parameter combinations
- [ ] Performance tests meet frame rate targets
- [ ] Edge case tests cover all documented failure modes

#### Documentation Requirements
- [ ] Complete parameter mapping table with formulas
- [ ] Mathematical formulations for all core algorithms
- [ ] Performance analysis with optimization suggestions
- [ ] Test plan with coverage targets and test cases
- [ ] WebGPU migration notes (bind group layouts, WGSL conversion)

#### Quality Requirements
- [ ] Code follows project style guidelines
- [ ] Comments explain complex mathematical operations
- [ ] Error messages are clear and actionable
- [ ] No memory leaks or resource management issues

## WebGPU Migration Notes

### Shader Conversion (GLSL 330 → WGSL)
```wgsl
// WGSL equivalent of INFINITE_FEEDBACK_FRAGMENT
@vertex
fn vs_main(input: VertexInput) -> VertexOutput {
    // Vertex shader implementation
}

@fragment
fn fs_main(input: FragmentInput) -> @location(0) vec4<f32> {
    // Fragment shader implementation
    
    // Texture sampling
    let current = textureSample(tex0, sampler, uv);
    let accumulated = textureSample(texPrev, sampler, uv);
    
    // Rotation and zoom transformations
    // ... (same mathematical operations)
    
    return fragColor;
}
```

### Uniform Buffer Layout
```rust
#[repr(C)]
#[derive(Debug, Copy, Clone)]
struct InfiniteFeedbackUniforms {
    time: f32,
    resolution: vec2,
    mix: f32,
    
    amount: f32,
    decay: f32,
    rotate_speed: f32,
    zoom_speed: f32,
    delay: f32,
    bpm: f32,
}
```

### Bind Group Layout
```rust
let bind_group_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
    entries: &[
        // Texture 0: Current frame
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
        // Texture 1: Previous frame (feedback buffer)
        wgpu::BindGroupLayoutEntry {
            binding: 1,
            visibility: wgpu::ShaderStages::FRAGMENT,
            ty: wgpu::BindingType::Texture {
                sample_type: wgpu::TextureSampleType::Float { filterable: true },
                view_dimension: wgpu::TextureViewDimension::D2,
                multisampled: false,
            },
            count: None,
        },
        // Uniform buffer
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
    label: Some("infinite_feedback_bind_group_layout"),
});
```

### Performance Considerations
- **Trigonometric Functions**: WGSL supports native sin/cos, but consider lookup tables for mobile
- **Texture Sampling**: WGSL texture sampling is similar to GLSL, but ensure proper filtering settings
- **Memory Layout**: Ensure uniform buffer alignment matches WGSL requirements

## Legacy Code Analysis

### Source Location
- **File**: `/home/happy/Desktop/claude projects/vjlive/core/effects/legacy_trash/blend.py`
- **Class**: `InfiniteFeedbackEffect`
- **Shader**: `INFINITE_FEEDBACK_FRAGMENT`

### Key Implementation Details
- **Base Class**: Inherits from `Effect` base class
- **Shader Registration**: Passes shader string to parent constructor
- **Parameter System**: Uses dictionary-based parameter storage with default values
- **Audio Reactivity**: No direct audio reactivity, but BPM parameter enables rhythmic synchronization

### Potential Issues
- **Memory Management**: No explicit cleanup of feedback buffer
- **Error Handling**: Limited validation of texture availability
- **Performance**: No optimization for mobile GPUs
