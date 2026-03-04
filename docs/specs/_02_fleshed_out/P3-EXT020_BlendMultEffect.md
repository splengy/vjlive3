# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT020 — BlendMultEffect

## Detailed Behavior and Parameter Interactions

### Core Multiply Blending
The BlendMultEffect implements a multiply blend mode that combines two video sources by multiplying their color values. This creates a darkening effect where the result is always equal to or darker than the darkest input.

**Multiply Blend Mode:**
- Multiply blend mode: `C_out = C_A * C_B`
- Result is always darker than or equal to the darker input
- White (1.0) acts as a neutral element (no change)
- Black (0.0) produces black regardless of other input
- Creates shadowing and darkening effects

**Parameter Control:**
- `amount`: Controls the blend ratio between multiply and original
  - 0.0 = no effect (pass-through)
  - 1.0 = full multiply blend
  - Intermediate values create smooth transitions

**Color Channel Processing:**
- Each RGB channel is multiplied independently
- Alpha channel is typically preserved or multiplied based on implementation
- Color space: Linear RGB for correct multiplication
- HDR support: Multiplication works correctly with high dynamic range

**Use Cases:**
- Darkening images and video
- Creating shadow effects
- Texture blending and compositing
- Artistic color manipulation
- VJ performance transitions

## Public Interface

```python
class BlendMultEffect(Effect):
    METADATA = {
        'name': 'blend_mult',
        'gpu_tier': 'LOW',
        'input_type': 'video',
        'output_type': 'video',
        'description': 'Multiply blend mode for darkening and shadow effects',
        'parameters': [
            {'name': 'amount', 'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 1.0},
        ]
    }
    
    def __init__(self, name: str = "blend_mult") -> None:
        super().__init__(name)
        self._uniforms = {}
    
    def _map_param(self, name: str, out_min: float, out_max: float) -> float:
        if name not in self.params:
            return (out_min + out_max) / 2.0
        value = self.params[name]
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        return (value) * (out_max - out_min) + out_min
    
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], 
                       audio_reactor: Optional[Any] = None, 
                       semantic_layer: Optional[Any] = None) -> None:
        self._uniforms['amount'] = self._map_param('amount', 0.0, 1.0)
        
        # Audio reactivity (optional)
        if audio_reactor:
            energy = audio_reactor.get_energy()
            self._uniforms['audio_energy'] = energy
            # Modulate amount with audio energy if desired
            # self._uniforms['amount'] = min(1.0, self._uniforms['amount'] * (1.0 + energy * 0.5))
    
    def get_fragment_shader(self) -> str:
        return self._generate_wgsl_shader()
    
    def _generate_wgsl_shader(self) -> str:
        # Generate WGSL shader for multiply blend
        shader = """
            struct Uniforms {
                amount: f32,
                time: f32,
                resolution: vec2<f32>,
            }
            
            @group(0) @binding(0) var tex0: texture_2d<f32>;
            @group(0) @binding(1) var tex1: texture_2d<f32>;
            @group(0) @binding(2) var s0: sampler;
            
            @fragment
            fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
                let color_a = textureSample(tex0, s0, uv);
                let color_b = textureSample(tex1, s0, uv);
                
                // Multiply blend: C_out = C_A * C_B
                var multiplied = color_a * color_b;
                
                // Apply amount parameter for blending with original
                let original = color_a;  // or could be another source
                let final_color = mix(original, multiplied, amount);
                
                return final_color;
            }
        """
        return shader
```

## Inputs and Outputs

### Input Requirements
- **Video Input**: Two RGBA video textures (tex0, tex1)
- **Resolution**: Any resolution supported by GPU
- **Frame Rate**: Any frame rate supported by GPU
- **Audio Input**: Optional audio reactor for reactivity

### Output
- **Video Output**: Processed RGBA video texture (signal_out)
- **Processing**: Multiply blend of two input sources
- **Format**: Standard RGBA video format

## Edge Cases and Error Handling

### Parameter Edge Cases
- **amount = 0.0**: No effect, pass-through input unchanged
- **amount = 1.0**: Full multiply blend
- **amount > 1.0**: Clamped to 1.0 (or could be used for overdrive)
- **amount < 0.0**: Clamped to 0.0

### Error Scenarios
- **Missing Second Source**: If tex1 is not provided, effect may use black or fallback
- **Invalid Parameters**: Out-of-range parameters are clamped to valid ranges
- **GPU Limitations**: Shader adapts to available GPU capabilities
- **Memory Constraints**: Resolution parameters automatically adjust to available memory

### Internal Dependencies
- **Base Effect Class**: Inherits from Effect base class
- **WGSL Shader**: Requires WebGPU-compatible GPU
- **Render Pipeline**: Requires compatible render pipeline

### External Dependencies
- **WebGPU**: Required for shader execution
- **GPU Memory**: Required for texture processing

## Mathematical Formulations

### Multiply Blend Mode

**Basic Multiply:**
C_out = C_A × C_B

Where C_A and C_B are color vectors (RGB) from two sources.

**With Amount Control:**
C_final = (1 - amount) × C_A + amount × (C_A × C_B)

**Channel-wise Operation:**
- R_out = R_A × R_B
- G_out = G_A × G_B
- B_out = B_A × B_B
- A_out = A_A × A_B (or preserve alpha)

**Linear vs sRGB:**
- For correct results, colors should be in linear space
- If inputs are sRGB, convert to linear before multiplication
- Convert result back to sRGB if needed

### Audio Reactivity (Optional)

**Audio-Modulated Amount:**
amount_audio = amount × (1 + audio_energy × reactivity_factor)

## Performance Characteristics

### GPU Tier Requirements
- **Tier**: LOW (simple multiplication operation)
- **Memory**: Minimal (~10-20MB)
- **Processing**: Very fast, suitable for real-time on any GPU
- **Shader Complexity**: Very low (single multiplication per pixel)

### Performance Metrics
- **Frame Rate**: 60+ FPS at 4K resolution easily
- **Latency**: <1ms per frame
- **Memory Bandwidth**: Low (2 texture reads, 1 write)
- **Power Consumption**: Minimal

### Optimization Strategies
- **Resolution Scaling**: Not needed, performs well at any resolution
- **Level of Detail**: Not applicable (simple operation)
- **Temporal Coherence**: Not needed (stateless operation)
- **Memory Management**: Standard texture handling

## Test Plan

### Unit Tests (Coverage: 95%)
1. **Parameter Mapping Tests**
   - Test _map_param() with boundary values (0.0, 1.0)
   - Test parameter clamping for out-of-range values
   - Test default parameter handling

2. **Uniform Application Tests**
   - Test apply_uniforms() with various parameter values
   - Test audio reactivity integration (if implemented)

3. **Shader Generation Tests**
   - Test _generate_wgsl_shader() output structure
   - Test uniform binding generation
   - Test shader compilation with test parameters

### Integration Tests (Coverage: 90%)
4. **Effect Pipeline Tests**
   - Test complete effect processing pipeline
   - Test video input/output handling
   - Test parameter interaction effects

5. **Blend Mode Tests**
   - Test multiply blend with known inputs/outputs
   - Test amount parameter interpolation
   - Test edge cases (black, white, primary colors)

6. **Color Accuracy Tests**
   - Test color space handling (linear vs sRGB)
   - Test alpha channel handling
   - Test HDR content support

### Performance Tests (Coverage: 85%)
7. **Benchmark Tests**
   - Test frame rate at various resolutions (1080p, 4K)
   - Test memory usage
   - Test GPU utilization

8. **Compatibility Tests**
   - Test across different GPU architectures
   - Test with various video formats
   - Test with different color spaces

### Edge Case Tests (Coverage: 80%)
9. **Boundary Tests**
   - Test amount = 0.0 (no effect)
   - Test amount = 1.0 (full multiply)
   - Test with black inputs
   - Test with white inputs
   - Test with extreme color values

10. **Error Handling Tests**
    - Test missing texture inputs
    - Test invalid parameter combinations
    - Test GPU failure scenarios

### Visual Quality Tests (Coverage: 75%)
11. **Visual Consistency Tests**
    - Test smooth parameter transitions
    - Test color accuracy
    - Test no artifacts or banding

12. **Comparison Tests**
    - Compare output with reference multiply blend implementation
    - Verify mathematical correctness
    - Test against known blend mode standards

## Definition of Done

### Technical Requirements
- [ ] Single parameter (amount) implemented correctly
- [ ] WGSL shader generates without compilation errors
- [ ] Real-time performance maintained at 60+ FPS at any resolution
- [ ] Multiply blend mathematically correct
- [ ] Edge cases handled gracefully
- [ ] Memory usage minimal (<20MB)
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
- [ ] Works with VJLive3 effect chain

## Legacy References

### Original Implementation
- **Source**: core/effects/legacy_trash/blend.py - BlendMultEffect class
- **Parameters**: 1 parameter (amount)
- **GPU Tier**: LOW
- **Input**: Two video sources (A and B)
- **Output**: Multiplied blend result

### Parameter Mapping from Legacy
| Legacy Parameter | VJLive3 Parameter | Range Mapping |
|------------------|-------------------|---------------|
| amount | amount | 0.0-1.0 |

### Shader Reference (Legacy GLSL)
```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D tex1;
uniform float amount;

void main() {
    vec4 a = texture(tex0, uv);
    vec4 b = texture(tex1, uv);
    vec4 blended = a * b;  // Multiply blend
    fragColor = mix(a, blended, amount);
}
```

### Performance Characteristics
- **Frame Rate**: 60+ FPS at any resolution
- **Memory**: ~10-20MB
- **GPU**: LOW tier (basic arithmetic)
- **Audio**: Optional reactivity

### Visual Effects
- Multiply blend darkens images
- Creates shadow and darkening effects
- Preserves highlights (white remains white)
- Black areas remain black
- Color channel independence
- Linear space multiplication for correct results

This spec provides a comprehensive blueprint for implementing the BlendMultEffect in VJLive3, maintaining compatibility with the original legacy implementation while leveraging the modern VJLive3 architecture with WebGPU and WGSL shaders.