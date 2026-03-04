# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT142 — R16SimulatedDepth

## Detailed Behavior and Parameter Interactions

### Core Simulated Depth Generation
The R16SimulatedDepth effect generates R16 depth data from standard video input by analyzing luminance values. This creates a depth map where brighter areas are considered closer and darker areas are farther away, or vice versa based on the invert parameter.

**Depth from Luminance:**
- Converts RGB input to luminance (brightness) values
- Maps luminance to depth range (min_depth to max_depth)
- Outputs R16 format depth data (16-bit unsigned integer)
- Creates depth map suitable for R16 depth effects

**Depth Range Control:**
- `min_depth`: Depth value for black (0 luminance) in meters
- `max_depth`: Depth value for white (1 luminance) in meters
- Linear mapping between luminance and depth
- Depth values represent real-world distances

**Contrast Enhancement:**
- `contrast`: Adjusts the steepness of the luminance-to-depth mapping
- Values > 1.0 increase contrast (sharper depth transitions)
- Values < 1.0 decrease contrast (softer depth transitions)
- Applied as power function: depth = base_depth^contrast

**Inversion:**
- `invert`: 0 = Bright is Near (default), 1 = Dark is Near
- Reverses the luminance-to-depth mapping
- Useful for different scene compositions

**Temporal Smoothing:**
- `smoothing`: Controls temporal stability of depth map
- 0.0 = no smoothing (raw depth from each frame)
- 1.0 = maximum smoothing (very stable, slow to respond)
- Uses exponential moving average for smoothing

## Public Interface

```python
class R16SimulatedDepth(Effect):
    METADATA = {
        'name': 'r16_simulated_depth',
        'gpu_tier': 'MEDIUM',
        'input_type': 'video',
        'output_type': 'video',
        'description': 'Generates R16 depth data from video luminance',
        'parameters': [
            {'name': 'min_depth', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
            {'name': 'max_depth', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'invert', 'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.0},
            {'name': 'contrast', 'type': 'float', 'min': 0.1, 'max': 5.0, 'default': 1.0},
            {'name': 'smoothing', 'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.0},
        ]
    }
    
    def __init__(self, name: str = "r16_simulated_depth") -> None:
        super().__init__(name)
        self._uniforms = {}
        self._prev_depth = None  # For temporal smoothing
    
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
        self._uniforms['min_depth'] = self._map_param('min_depth', 0.0, 10.0)
        self._uniforms['max_depth'] = self._map_param('max_depth', 0.0, 10.0)
        self._uniforms['invert'] = self._map_param('invert', 0.0, 1.0)
        self._uniforms['contrast'] = self._map_param('contrast', 0.1, 5.0)
        self._uniforms['smoothing'] = self._map_param('smoothing', 0.0, 1.0)
        self._uniforms['time'] = time
    
    def get_fragment_shader(self) -> str:
        return self._generate_wgsl_shader()
    
    def _generate_wgsl_shader(self) -> str:
        # Generate WGSL shader for depth simulation
        shader = """
            struct Uniforms {
                min_depth: f32,
                max_depth: f32,
                invert: f32,
                contrast: f32,
                smoothing: f32,
                time: f32,
                resolution: vec2<f32>,
            };
            
            @group(0) @binding(0) var tex0: texture_2d<f32>;
            @group(0) @binding(1) var s0: sampler;
            
            @fragment
            fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
                let color = textureSample(tex0, s0, uv);
                
                // Convert to luminance (standard Rec. 709 weights)
                let luminance = dot(color.rgb, vec3<f32>(0.2126, 0.7152, 0.0722));
                
                // Apply contrast
                let adjusted_lum = pow(luminance, contrast);
                
                // Apply inversion
                let depth_factor = mix(adjusted_lum, 1.0 - adjusted_lum, invert);
                
                // Map to depth range
                let depth = mix(min_depth, max_depth, depth_factor);
                
                // Normalize to 0-1 range for R16 (0-65535)
                let normalized_depth = depth / 65535.0;
                
                // Output as R16 (stored in red channel, 16-bit precision)
                return vec4<f32>(normalized_depth, 0.0, 0.0, 1.0);
            }
        """
        return shader
```

## Inputs and Outputs

### Input Requirements
- **Video Input**: Standard RGBA video texture (signal_in)
- **Resolution**: Any resolution supported by GPU
- **Frame Rate**: Any frame rate supported by GPU

### Output
- **Video Output**: R16 depth texture (signal_out)
- **Format**: Single-channel depth in red channel, normalized to 0-1 range
- **Precision**: 16-bit depth values (0-65535) scaled to 0-1
- **Usage**: Suitable for R16 depth effects and processing

## Edge Cases and Error Handling

### Parameter Edge Cases
- **min_depth > max_depth**: Results in inverted depth range (still valid)
- **contrast = 0.1**: Very soft depth transitions
- **contrast = 5.0**: Very sharp depth transitions, may cause banding
- **smoothing = 0.0**: No temporal smoothing, may be noisy
- **smoothing = 1.0**: Very smooth, slow to respond to changes

### Error Scenarios
- **Invalid Parameters**: Out-of-range parameters are clamped to valid ranges
- **GPU Limitations**: Shader adapts to available GPU capabilities
- **Memory Constraints**: Resolution parameters automatically adjust to available memory
- **Missing Input**: If no video input, outputs black (depth = 0)

### Internal Dependencies
- **Base Effect Class**: Inherits from Effect base class
- **WGSL Shader**: Requires WebGPU-compatible GPU
- **Render Pipeline**: Requires compatible render pipeline

### External Dependencies
- **WebGPU**: Required for shader execution
- **GPU Memory**: Required for texture processing

## Mathematical Formulations

### Luminance Calculation

**Standard Rec. 709:**
L = 0.2126 × R + 0.7152 × G + 0.0722 × B

**Alternative (Rec. 601):**
L = 0.299 × R + 0.587 × G + 0.114 × B

### Contrast Adjustment

**Contrast Power:**
L_adj = L^contrast

Where contrast > 1 increases contrast, contrast < 1 decreases contrast.

### Depth Mapping

**Linear Mapping:**
D = min_depth + (max_depth - min_depth) × L_adj

**With Inversion:**
D = min_depth + (max_depth - min_depth) × (1 - L_adj)  [if invert = 1]

### R16 Normalization

**Normalized Depth:**
D_norm = D / 65535.0

**R16 Integer Value:**
D_r16 = round(D_norm × 65535)

### Temporal Smoothing

**Exponential Moving Average:**
D_smoothed(t) = smoothing × D_smoothed(t-1) + (1 - smoothing) × D(t)

Where D(t) is the current frame's depth value.

## Performance Characteristics

### GPU Tier Requirements
- **Tier**: MEDIUM (based on legacy implementation)
- **Memory**: ~20-50MB for full resolution processing
- **Processing**: Real-time capable on modern GPUs
- **Shader Complexity**: Low (simple luminance calculation and mapping)

### Performance Metrics
- **Frame Rate**: 60+ FPS at 4K resolution
- **Latency**: <5ms per frame
- **Memory Bandwidth**: Low (single texture read, single write)
- **Power Consumption**: Minimal

### Optimization Strategies
- **Resolution Scaling**: Not needed, performs well at any resolution
- **Level of Detail**: Not applicable (simple operation)
- **Temporal Coherence**: Smoothing parameter reduces temporal noise
- **Memory Management**: Standard texture handling

## Test Plan

### Unit Tests (Coverage: 95%)
1. **Parameter Mapping Tests**
   - Test _map_param() with boundary values
   - Test parameter clamping for out-of-range values
   - Test default parameter handling

2. **Uniform Application Tests**
   - Test apply_uniforms() with various parameter combinations
   - Test all parameters are correctly set

3. **Shader Generation Tests**
   - Test _generate_wgsl_shader() output structure
   - Test uniform binding generation
   - Test shader compilation with test parameters

### Integration Tests (Coverage: 90%)
4. **Effect Pipeline Tests**
   - Test complete effect processing pipeline
   - Test video input/output handling
   - Test parameter interaction effects

5. **Depth Generation Tests**
   - Test luminance to depth conversion accuracy
   - Test min_depth and max_depth mapping
   - Test contrast adjustment
   - Test inversion functionality
   - Test temporal smoothing

6. **Color Space Tests**
   - Test with various input color spaces
   - Test luminance calculation accuracy
   - Test gamma correction handling

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
   - Test with black input (all zeros)
   - Test with white input (all ones)
   - Test with primary colors
   - Test with extreme contrast values
   - Test with min_depth = max_depth

10. **Error Handling Tests**
    - Test missing texture input
    - Test invalid parameter combinations
    - Test GPU failure scenarios

### Visual Quality Tests (Coverage: 75%)
11. **Visual Consistency Tests**
    - Test smooth parameter transitions
    - Test no artifacts or banding
    - Test depth map quality

12. **Accuracy Tests**
    - Compare output with reference depth generation
    - Verify R16 format correctness
    - Test depth range accuracy

## Definition of Done

### Technical Requirements
- [ ] All 5 parameters implemented with proper mapping
- [ ] WGSL shader generates without compilation errors
- [ ] Real-time performance maintained at 60+ FPS at any resolution
- [ ] R16 depth output format correct (16-bit precision)
- [ ] Edge cases handled gracefully
- [ ] Memory usage minimal (<50MB)
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
- [ ] Works as depth source for R16 effects

## Legacy References

### Original Implementation
- **Source**: plugins/vdepth/r16_simulated_depth.py and plugins/core/r16_simulated_depth/__init__.py
- **Parameters**: 5 parameters (min_depth, max_depth, invert, contrast, smoothing)
- **GPU Tier**: MEDIUM
- **Input**: signal_in (video)
- **Output**: signal_out (R16 depth video)

### Parameter Mapping from Legacy
| Legacy Parameter | VJLive3 Parameter | Range Mapping |
|------------------|-------------------|---------------|
| min_depth | min_depth | 0.0-10.0 meters |
| max_depth | max_depth | 0.0-10.0 meters |
| invert | invert | 0.0-1.0 (bool) |
| contrast | contrast | 0.1-5.0 |
| smoothing | smoothing | 0.0-1.0 |

### Shader Reference (Legacy GLSL)
```glsl
#version 330 core
in vec2 v_uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform float min_depth;
uniform float max_depth;
uniform float invert;
uniform float contrast;
uniform float smoothing;

void main() {
    vec4 color = texture(tex0, v_uv);
    float luminance = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
    float adjusted = pow(luminance, contrast);
    float depth_factor = mix(adjusted, 1.0 - adjusted, invert);
    float depth = mix(min_depth, max_depth, depth_factor);
    float normalized = depth / 65535.0;
    fragColor = vec4(normalized, 0.0, 0.0, 1.0);
}
```

### Performance Characteristics
- **Frame Rate**: 60+ FPS at any resolution
- **Memory**: ~20-50MB
- **GPU**: MEDIUM tier
- **Audio**: Not applicable (depth generation only)

### Visual Effects
- Depth map generation from luminance
- Configurable depth range (min_depth to max_depth)
- Contrast enhancement for depth separation
- Inversion for different scene compositions
- Temporal smoothing for stable depth
- R16 16-bit depth output format

This spec provides a comprehensive blueprint for implementing the R16SimulatedDepth in VJLive3, maintaining compatibility with the original legacy implementation while leveraging the modern VJLive3 architecture with WebGPU and WGSL shaders.