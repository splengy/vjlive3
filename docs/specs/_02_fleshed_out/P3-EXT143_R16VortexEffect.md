# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT143 — R16VortexEffect

## Detailed Behavior and Parameter Interactions

### Core Vortex Distortion
The R16VortexEffect creates swirling vortex distortions in depth space, transforming the input video based on R16 depth values to produce a spiraling visual effect. The vortex pulls pixels toward a center point while rotating them around that center.

**Vortex Mechanics:**
- Central vortex point attracts pixels based on depth
- Rotation angle increases with proximity to center
- Depth values modulate the strength and character of the distortion
- Creates a swirling, funnel-like visual effect

**Depth-Driven Distortion:**
- Uses R16 depth texture to determine distortion intensity
- Closer depth values (lower numeric value) may create stronger vortex effects
- Depth influences both radial pull and rotational angle
- Creates 3D-like swirling through depth-aware warping

**Parameter Control:**
- `vortex_strength`: Controls overall intensity of the vortex effect
- `rotation_angle`: Base rotation angle around vortex center
- `depth_influence`: How strongly depth values affect the distortion
- `center_x`, `center_y`: Position of the vortex center (normalized 0-1)
- `falloff`: Controls how quickly effect diminishes from center

**Visual Characteristics:**
- Swirling, spiraling distortion pattern
- Depth-based modulation creates layered effect
- Can produce tunnel-like or drain-like visuals
- Works well with abstract video and generative content

## Public Interface

```python
class R16VortexEffect(Effect):
    METADATA = {
        'name': 'r16_vortex',
        'gpu_tier': 'MEDIUM',
        'input_type': 'video',
        'output_type': 'video',
        'description': 'R16 Vortex Effect - Creates swirling vortex distortions in depth data',
        'parameters': [
            {'name': 'vortex_strength', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'rotation_angle', 'type': 'float', 'min': 0.0, 'max': 360.0, 'default': 180.0},
            {'name': 'depth_influence', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'center_x', 'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.5},
            {'name': 'center_y', 'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.5},
            {'name': 'falloff', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
        ]
    }
    
    def __init__(self, name: str = "r16_vortex") -> None:
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
        self._uniforms['vortex_strength'] = self._map_param('vortex_strength', 0.0, 10.0)
        self._uniforms['rotation_angle'] = self._map_param('rotation_angle', 0.0, 360.0)
        self._uniforms['depth_influence'] = self._map_param('depth_influence', 0.0, 10.0)
        self._uniforms['center_x'] = self._map_param('center_x', 0.0, 1.0)
        self._uniforms['center_y'] = self._map_param('center_y', 0.0, 1.0)
        self._uniforms['falloff'] = self._map_param('falloff', 0.0, 10.0)
        self._uniforms['time'] = time
        self._uniforms['resolution'] = resolution
    
    def get_fragment_shader(self) -> str:
        return self._generate_wgsl_shader()
    
    def _generate_wgsl_shader(self) -> str:
        shader = """
            struct Uniforms {
                vortex_strength: f32,
                rotation_angle: f32,
                depth_influence: f32,
                center_x: f32,
                center_y: f32,
                falloff: f32,
                time: f32,
                resolution: vec2<f32>,
            };
            
            @group(0) @binding(0) var tex0: texture_2d<f32>;
            @group(0) @binding(1) var depth_tex: texture_2d<f32>;
            @group(0) @binding(2) var s0: sampler;
            
            @fragment
            fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
                let center = vec2<f32>(center_x, center_y);
                let delta = uv - center;
                let distance = length(delta);
                
                // Sample depth
                let depth_sample = textureSample(depth_tex, s0, uv);
                let depth = depth_sample.r * 65535.0;  // R16 depth value
                
                // Calculate vortex rotation based on distance and depth
                let angle_offset = rotation_angle * (3.14159 / 180.0);
                let falloff_factor = exp(-falloff * distance);
                let depth_factor = depth / 65535.0;
                
                // Combined rotation amount
                let rotation = angle_offset * falloff_factor * (1.0 + depth_factor * depth_influence);
                
                // Apply rotation
                let cos_r = cos(rotation);
                let sin_r = sin(rotation);
                let rotated_delta = vec2<f32>(
                    delta.x * cos_r - delta.y * sin_r,
                    delta.x * sin_r + delta.y * cos_r
                );
                
                // Apply vortex pull (toward center)
                let pull_strength = vortex_strength * falloff_factor * 0.1;
                let pulled_uv = center + rotated_delta * (1.0 - pull_strength);
                
                // Sample original texture at transformed coordinates
                let color = textureSample(tex0, s0, pulled_uv);
                
                // Apply depth-based transparency (optional)
                let depth_alpha = 1.0 - abs(depth_factor - 0.5) * 0.2;
                
                return vec4<f32>(color.rgb, color.a * depth_alpha);
            }
        """
        return shader
```

## Inputs and Outputs

### Input Requirements
- **Video Input**: RGBA video texture (tex0)
- **Depth Input**: R16 depth texture (depth_tex) - red channel contains 16-bit depth
- **Resolution**: Any resolution supported by GPU
- **Frame Rate**: Any frame rate supported by GPU

### Output
- **Video Output**: Processed RGBA video texture (signal_out)
- **Processing**: Vortex-distorted video based on depth
- **Format**: Standard RGBA video format with depth-modulated alpha

## Edge Cases and Error Handling

### Parameter Edge Cases
- **vortex_strength = 0.0**: No distortion, pass-through
- **rotation_angle = 0.0**: No rotation, only radial pull
- **depth_influence = 0.0**: Vortex independent of depth
- **falloff = 0.0**: Uniform effect across entire image
- **center at (0,0) or (1,1)**: Vortex at corner
- **center outside [0,1]**: Clamped or wrapped

### Error Scenarios
- **Missing Depth Texture**: Effect may use default depth or fail gracefully
- **Invalid Parameters**: Out-of-range parameters are clamped
- **GPU Limitations**: Shader adapts to available GPU capabilities
- **Memory Constraints**: Resolution parameters automatically adjust

### Internal Dependencies
- **Base Effect Class**: Inherits from Effect base class
- **WGSL Shader**: Requires WebGPU-compatible GPU
- **Depth Texture**: Requires R16 depth input

### External Dependencies
- **WebGPU**: Required for shader execution
- **GPU Memory**: Required for texture processing
- **Depth Source**: Required for depth-driven distortion

## Mathematical Formulations

### Vortex Transformation

**Coordinate System:**
Let uv = (x, y) be the texture coordinate
Let center = (cx, cy) be the vortex center
Let delta = uv - center

**Distance Calculation:**
d = |delta| = sqrt((x-cx)² + (y-cy)²)

**Falloff Factor:**
F_falloff = exp(-falloff × d)

**Depth Factor:**
D_factor = depth / 65535.0

**Rotation Calculation:**
θ = rotation_angle × (π/180) × F_falloff × (1 + depth_influence × D_factor)

**Rotation Matrix:**
R(θ) = [[cos(θ), -sin(θ)], [sin(θ), cos(θ)]]

**Rotated Delta:**
delta_rotated = R(θ) × delta

**Vortex Pull:**
P = vortex_strength × F_falloff × 0.1
uv_transformed = center + delta_rotated × (1 - P)

### Depth-Based Transparency

**Depth Alpha:**
α_depth = 1.0 - |D_factor - 0.5| × 0.2

**Final Alpha:**
α_final = α_original × α_depth

## Performance Characteristics

### GPU Tier Requirements
- **Tier**: MEDIUM (based on legacy implementation)
- **Memory**: ~30-60MB for full resolution processing
- **Processing**: Real-time capable on modern GPUs
- **Shader Complexity**: Medium (exponential, trigonometry, texture sampling)

### Performance Metrics
- **Frame Rate**: 30-60 FPS at 1080p, 30+ FPS at 4K
- **Latency**: <10ms per frame
- **Memory Bandwidth**: Medium (2 texture reads, complex math)
- **Power Consumption**: Medium

### Optimization Strategies
- **Resolution Scaling**: May need adjustment for 4K
- **Level of Detail**: Reduce trigonometric precision on lower tiers
- **Temporal Coherence**: Not applicable (stateless per frame)
- **Memory Management**: Efficient texture handling

## Test Plan

### Unit Tests (Coverage: 95%)
1. **Parameter Mapping Tests**
   - Test _map_param() with boundary values
   - Test parameter clamping
   - Test default parameter handling

2. **Uniform Application Tests**
   - Test apply_uniforms() with various parameter combinations
   - Verify all uniforms are set correctly

3. **Shader Generation Tests**
   - Test _generate_wgsl_shader() output structure
   - Test uniform binding generation
   - Test shader compilation

### Integration Tests (Coverage: 90%)
4. **Effect Pipeline Tests**
   - Test complete effect processing
   - Test video and depth input handling
   - Test output format correctness

5. **Vortex Transformation Tests**
   - Test rotation calculations
   - Test falloff behavior
   - Test depth influence on transformation
   - Test center point accuracy

6. **Edge Case Tests**
   - Test with zero strength
   - Test with extreme falloff values
   - Test with various depth inputs

### Performance Tests (Coverage: 85%)
7. **Benchmark Tests**
   - Test frame rate at various resolutions
   - Test memory usage
   - Test GPU utilization

8. **Compatibility Tests**
   - Test across different GPU architectures
   - Test with various video formats
   - Test with different depth ranges

### Visual Quality Tests (Coverage: 75%)
9. **Visual Consistency Tests**
   - Test smooth parameter transitions
   - Test for artifacts or distortions
   - Test depth-modulated alpha

10. **Accuracy Tests**
    - Compare with reference vortex implementation
    - Verify mathematical correctness
    - Test depth integration

## Definition of Done

### Technical Requirements
- [ ] All 6 parameters implemented correctly
- [ ] WGSL shader compiles without errors
- [ ] Real-time performance at 30+ FPS at 1080p
- [ ] Depth-driven distortion functional
- [ ] Edge cases handled gracefully
- [ ] Memory usage acceptable (<60MB)
- [ ] Cross-platform compatibility

### Quality Requirements
- [ ] 80%+ test coverage achieved
- [ ] Documentation complete and accurate
- [ ] Performance benchmarks established
- [ ] Error handling robust
- [ ] Visual quality meets specifications

### Integration Requirements
- [ ] Compatible with VJLive3 plugin system
- [ ] Proper uniform binding implementation
- [ ] Depth texture handling correct (R16 format)
- [ ] Resource cleanup implemented
- [ ] Works in effect chain with other R16 effects

## Legacy References

### Original Implementation
- **Source**: plugins/vdepth/r16_vortex.py and plugins/core/r16_vortex/__init__.py
- **Parameters**: vortex_strength, rotation_angle, depth_influence, center_x, center_y, falloff
- **GPU Tier**: MEDIUM
- **Input**: signal_in (video), depth_tex (R16 depth)
- **Output**: signal_out (distorted video)

### Parameter Mapping from Legacy
| Legacy Parameter | VJLive3 Parameter | Range Mapping |
|------------------|-------------------|---------------|
| vortex_strength | vortex_strength | 0.0-10.0 |
| rotation_angle | rotation_angle | 0.0-360.0 degrees |
| depth_influence | depth_influence | 0.0-10.0 |
| center_x | center_x | 0.0-1.0 (normalized) |
| center_y | center_y | 0.0-1.0 (normalized) |
| falloff | falloff | 0.0-10.0 |

### Shader Reference (Legacy GLSL)
```glsl
#version 330 core
in vec2 v_uv;
out vec4 fragColor;
uniform sampler2D tex0;
uniform usampler2D depth_tex;  // R16 depth
uniform float vortex_strength;
uniform float rotation_angle;
uniform float depth_influence;
uniform vec2 center;
uniform float falloff;

void main() {
    vec2 delta = v_uv - center;
    float distance = length(delta);
    
    // Get R16 depth (stored in red channel as normalized 0-1)
    float depth = texture(depth_tex, v_uv).r * 65535.0;
    float depth_factor = depth / 65535.0;
    
    float falloff_factor = exp(-falloff * distance);
    float angle_rad = rotation_angle * 3.14159 / 180.0;
    float rotation = angle_rad * falloff_factor * (1.0 + depth_factor * depth_influence);
    
    // Rotate
    float cos_r = cos(rotation);
    float sin_r = sin(rotation);
    vec2 rotated = vec2(
        delta.x * cos_r - delta.y * sin_r,
        delta.x * sin_r + delta.y * cos_r
    );
    
    // Pull toward center
    float pull = vortex_strength * falloff_factor * 0.1;
    vec2 new_uv = center + rotated * (1.0 - pull);
    
    vec4 color = texture(tex0, new_uv);
    
    // Depth-based transparency
    float depth_alpha = 1.0 - abs(depth_factor - 0.5) * 0.2;
    fragColor = vec4(color.rgb, color.a * depth_alpha);
}
```

### Performance Characteristics
- **Frame Rate**: 30-60 FPS at 1080p
- **Memory**: ~30-60MB
- **GPU**: MEDIUM tier
- **Audio**: Not applicable (depth distortion only)

### Visual Effects
- Swirling vortex distortion
- Depth-modulated rotation and pull
- Exponential falloff from center
- Depth-based transparency
- R16 depth integration
- Center-controlled vortex position

This spec provides a comprehensive blueprint for implementing the R16VortexEffect in VJLive3, maintaining compatibility with the original legacy implementation while leveraging the modern VJLive3 architecture with WebGPU and WGSL shaders.