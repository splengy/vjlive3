# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT144 — RGBShiftEffect

## Detailed Behavior and Parameter Interactions

### Core Chromatic Aberration
The RGBShiftEffect creates a chromatic aberration (RGB split) effect by offsetting the red and blue color channels in opposite directions while keeping the green channel centered. This simulates lens chromatic aberration or creates psychedelic color separation effects.

**Channel Separation:**
- Red channel: shifted in one direction based on angle and amount
- Green channel: remains at original position (no shift)
- Blue channel: shifted in opposite direction to red
- Alpha channel: remains at original position

**Shift Direction:**
- `angle`: Controls the direction of the shift (0-10 mapped to 0-360 degrees)
- `amount`: Controls the magnitude of the shift (0-10)
- Offset vector: `offset = (cos(angle), sin(angle)) * amount * scale_factor`
- Red samples at `uv + offset`, Blue samples at `uv - offset`

**Blend Control:**
- `u_mix`: Internal uniform controlling blend with original (0-1)
- Effect can be mixed with original video
- Full effect (u_mix=1) shows full RGB shift
- No effect (u_mix=0) shows original video

**Visual Characteristics:**
- Creates color fringing at edges
- Simulates optical lens aberration
- Can produce psychedelic/glitch effects with large amounts
- Works best with high-contrast edges

## Public Interface

```python
class RGBShiftEffect(Effect):
    METADATA = {
        'name': 'rgb_shift',
        'gpu_tier': 'LOW',
        'input_type': 'video',
        'output_type': 'video',
        'description': 'RGB Shift - Chromatic aberration effect with directional color channel separation',
        'parameters': [
            {'name': 'amount', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
            {'name': 'angle', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
        ]
    }
    
    def __init__(self, name: str = "rgb_shift") -> None:
        super().__init__(name)
        self._uniforms = {}
    
    def _map_param(self, name: str, out_min: float, out_max: float) -> float:
        if name not in self.params:
            return (out_min + out_max) / 2.0
        value = self.params[name]
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        return (value / 10.0) * (out_max - out_min) + out_min
    
    def apply_uniforms(self, time: float, resolution: Tuple[int, int],
                       audio_reactor: Optional[Any] = None,
                       semantic_layer: Optional[Any] = None) -> None:
        self._uniforms['amount'] = self._map_param('amount', 0.0, 10.0)
        self._uniforms['angle'] = self._map_param('angle', 0.0, 360.0)
        self._uniforms['u_mix'] = self._map_param('u_mix', 0.0, 1.0) if 'u_mix' in self.params else 1.0
        self._uniforms['time'] = time
        self._uniforms['resolution'] = resolution
    
    def get_fragment_shader(self) -> str:
        return self._generate_wgsl_shader()
    
    def _generate_wgsl_shader(self) -> str:
        shader = """
            struct Uniforms {
                amount: f32,
                angle: f32,
                u_mix: f32,
                time: f32,
                resolution: vec2<f32>,
            };
            
            @group(0) @binding(0) var tex0: texture_2d<f32>;
            @group(0) @binding(1) var s0: sampler;
            
            @fragment
            fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
                // Convert angle to radians
                let angle_rad = angle * 3.14159 / 180.0;
                
                // Calculate offset direction and magnitude
                // Scale factor: amount * 0.005 for usability (0-10 -> 0-0.05 max UV shift)
                let offset_magnitude = amount * 0.005;
                let offset = vec2<f32>(
                    cos(angle_rad) * offset_magnitude,
                    sin(angle_rad) * offset_magnitude
                );
                
                // Sample color channels with offsets
                let r = textureSample(tex0, s0, uv + offset).r;
                let g = textureSample(tex0, s0, uv).g;
                let b = textureSample(tex0, s0, uv - offset).b;
                let a = textureSample(tex0, s0, uv).a;
                
                // Reconstruct shifted color
                let shifted_color = vec4<f32>(r, g, b, a);
                let original_color = textureSample(tex0, s0, uv);
                
                // Blend with original based on u_mix
                let final_color = mix(original_color, shifted_color, u_mix);
                
                return final_color;
            }
        """
        return shader
```

## Inputs and Outputs

### Input Requirements
- **Video Input**: RGBA video texture (tex0)
- **Resolution**: Any resolution supported by GPU
- **Frame Rate**: Any frame rate supported by GPU

### Output
- **Video Output**: Processed RGBA video texture (signal_out)
- **Processing**: RGB channel-shifted video with chromatic aberration
- **Format**: Standard RGBA video format

## Edge Cases and Error Handling

### Parameter Edge Cases
- **amount = 0.0**: No shift, original video (regardless of angle)
- **angle = 0.0**: Shift along positive X axis (cos(0)=1, sin(0)=0)
- **angle = 90° (2.5 in 0-10 scale)**: Shift along positive Y axis
- **angle = 180° (5.0 in 0-10 scale)**: Shift along negative X axis
- **angle = 270° (7.5 in 0-10 scale)**: Shift along negative Y axis
- **amount > 10.0**: Clamped to 10.0 (max 0.05 UV shift)
- **u_mix = 0.0**: No effect, pure original
- **u_mix = 1.0**: Full effect

### Error Scenarios
- **Invalid Parameters**: Out-of-range parameters are clamped
- **GPU Limitations**: Shader adapts to available GPU capabilities
- **Memory Constraints**: Resolution parameters automatically adjust
- **Missing Texture**: If texture missing, output is black or undefined

### Internal Dependencies
- **Base Effect Class**: Inherits from Effect base class
- **WGSL Shader**: Requires WebGPU-compatible GPU
- **Sampler**: Requires texture sampler

### External Dependencies
- **WebGPU**: Required for shader execution
- **GPU Memory**: Required for texture processing

## Mathematical Formulations

### Offset Calculation

**Angle Conversion:**
θ = angle × (π / 180.0)  [convert degrees to radians]

**Offset Magnitude:**
M = amount × 0.005  [scale 0-10 to 0-0.05 UV units]

**Offset Vector:**
offset = (cos(θ) × M, sin(θ) × M)

**Channel Sampling:**
- R = texture(uv + offset).r
- G = texture(uv).g
- B = texture(uv - offset).b
- A = texture(uv).a

**Blending:**
C_out = (1 - u_mix) × C_original + u_mix × C_shifted

### Coordinate Wrapping

**Edge Behavior:**
- UV coordinates outside [0,1] typically wrap or clamp
- Common approaches: repeat (wrap), clamp to edge, or mirror

## Performance Characteristics

### GPU Tier Requirements
- **Tier**: LOW (simple texture sampling with offset)
- **Memory**: ~5-10MB for full resolution processing
- **Processing**: Very fast, suitable for real-time on any GPU
- **Shader Complexity**: Very low (3 texture samples, basic math)

### Performance Metrics
- **Frame Rate**: 60+ FPS at 4K resolution
- **Latency**: <1ms per frame
- **Memory Bandwidth**: Low (3 texture reads, 1 write)
- **Power Consumption**: Minimal

### Optimization Strategies
- **Resolution Scaling**: Not needed, performs well at any resolution
- **Level of Detail**: Not applicable (simple operation)
- **Temporal Coherence**: Not needed (stateless operation)
- **Memory Management**: Standard texture handling

## Test Plan

### Unit Tests (Coverage: 95%)
1. **Parameter Mapping Tests**
   - Test _map_param() with boundary values (0.0, 10.0)
   - Test angle mapping to radians
   - Test parameter clamping
   - Test default parameter handling

2. **Uniform Application Tests**
   - Test apply_uniforms() with various parameter combinations
   - Verify all uniforms are set correctly
   - Test u_mix parameter handling

3. **Shader Generation Tests**
   - Test _generate_wgsl_shader() output structure
   - Test uniform binding generation
   - Test shader compilation with test parameters
   - Verify WGSL syntax correctness

### Integration Tests (Coverage: 90%)
4. **Effect Pipeline Tests**
   - Test complete effect processing pipeline
   - Test video input/output handling
   - Test parameter interaction effects

5. **RGB Shift Accuracy Tests**
   - Test offset calculation accuracy
   - Test channel separation (R shifted +, B shifted -, G centered)
   - Test angle direction correctness
   - Test amount magnitude scaling
   - Test u_mix blending

6. **Edge Case Tests**
   - Test with amount = 0 (no shift)
   - Test with angle = 0, 90, 180, 270 degrees
   - Test with u_mix = 0 and 1
   - Test with extreme values

### Performance Tests (Coverage: 85%)
7. **Benchmark Tests**
   - Test frame rate at various resolutions (1080p, 4K)
   - Test memory usage
   - Test GPU utilization

8. **Compatibility Tests**
   - Test across different GPU architectures
   - Test with various video formats
   - Test with different color spaces

### Visual Quality Tests (Coverage: 75%)
9. **Visual Consistency Tests**
   - Test smooth parameter transitions
   - Test for artifacts or color corruption
   - Test edge handling (wrapping/clamping)

10. **Comparison Tests**
    - Compare output with reference RGB shift implementation
    - Verify mathematical correctness
    - Test against known chromatic aberration patterns

## Definition of Done

### Technical Requirements
- [ ] Both parameters (amount, angle) implemented correctly
- [ ] WGSL shader generates without compilation errors
- [ ] Real-time performance maintained at 60+ FPS at any resolution
- [ ] RGB channel separation accurate
- [ ] Edge cases handled gracefully
- [ ] Memory usage minimal (<10MB)
- [ ] Cross-platform compatibility verified

### Quality Requirements
- [ ] 80%+ test coverage achieved
- [ ] Documentation complete and accurate
- [ ] Performance benchmarks established
- [ ] Error handling robust
- [ ] Visual quality meets specifications

### Integration Requirements
- [ ] Compatible with VJLive3 plugin system
- [ ] Proper uniform binding implementation
- [ ] Texture handling optimized
- [ ] Resource cleanup implemented
- [ ] Works in effect chain with other color effects

## Legacy References

### Original Implementation
- **Source**: core/effects/rgb_shift.py and plugins/core/rgb_shift/__init__.py
- **Parameters**: amount (0.0-10.0), angle (0.0-10.0)
- **GPU Tier**: LOW
- **Input**: tex0 (video)
- **Output**: RGB-shifted video

### Parameter Mapping from Legacy
| Legacy Parameter | VJLive3 Parameter | Range Mapping |
|------------------|-------------------|---------------|
| amount | amount | 0.0-10.0 (scaled by 0.005 for UV shift) |
| angle | angle | 0.0-10.0 → 0-360 degrees |

### Shader Reference (Legacy GLSL)
```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform float amount;
uniform float angle;
uniform float u_mix;

void main() {
    // Scale down amount for usability (0-10 -> 0-0.05 effective UV shift)
    vec2 offset = vec2(cos(angle), sin(angle)) * amount * 0.005;
    
    float r = texture(tex0, uv + offset).r;
    float g = texture(tex0, uv).g;
    float b = texture(tex0, uv - offset).b;
    float a = texture(0, uv).a;
    
    vec4 color = vec4(r, g, b, a);
    vec4 input_color = texture(tex0, uv);
    
    fragColor = mix(input_color, color, u_mix);
}
```

**Note**: The legacy shader uses `angle` directly as radians in the cos/sin functions. In VJLive3, we map the 0-10 parameter to 0-360 degrees and convert to radians for clarity.

### Performance Characteristics
- **Frame Rate**: 60+ FPS at any resolution
- **Memory**: ~5-10MB
- **GPU**: LOW tier
- **Audio**: Not applicable (static effect)

### Visual Effects
- Chromatic aberration (RGB split)
- Directional color fringing
- Lens simulation effect
- Psychedelic color separation
- Edge enhancement through color splitting
- Minimal performance impact

This spec provides a comprehensive blueprint for implementing the RGBShiftEffect in VJLive3, maintaining compatibility with the original legacy implementation while leveraging the modern VJLive3 architecture with WebGPU and WGSL shaders.