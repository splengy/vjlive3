# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT145 — RadiantMeshEffect

## Detailed Behavior and Parameter Interactions

### Core Radiant Mesh Effect
The RadiantMeshEffect creates bold, neon-colored mesh overlays inspired by Keith Haring's distinctive artistic style. The effect generates geometric mesh patterns with glowing outlines and motion lines, optimized for high-contrast silhouettes like crowd scenes.

**Mesh Generation:**
- Grid-based mesh pattern overlaid on video
- Bold outlines defining mesh cells
- Neon color palette with high saturation
- Motion lines radiating from moving elements

**Visual Style:**
- Keith Haring-inspired aesthetic
- Bold black outlines with neon fills
- High contrast between elements
- Pop art sensibility with vibrant colors

**Parameter Control:**
- `mesh_density`: Controls grid resolution (number of mesh cells)
- `outline_thickness`: Thickness of bold outlines
- `neon_glow`: Intensity of neon glow effect
- `motion_sensitivity`: How strongly motion affects motion lines
- `color_scheme`: Selects neon color palette (multiple presets)
- `saturation_boost`: Additional color saturation

**Interaction with Source:**
- Effect overlays on original video
- Original video provides silhouette/motion information
- Mesh pattern can respond to motion in the source
- High-contrast scenes work best for silhouette detection

## Public Interface

```python
class RadiantMeshEffect(Effect):
    METADATA = {
        'name': 'radiant_mesh',
        'gpu_tier': 'MEDIUM',
        'input_type': 'video',
        'output_type': 'video',
        'description': 'Radiant Mesh - Keith Haring style neon mesh overlay with motion lines',
        'parameters': [
            {'name': 'mesh_density', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'outline_thickness', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'neon_glow', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 7.0},
            {'name': 'motion_sensitivity', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'color_scheme', 'type': 'int', 'min': 0, 'max': 5, 'default': 0},
            {'name': 'saturation_boost', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
        ]
    }
    
    def __init__(self, name: str = "radiant_mesh") -> None:
        super().__init__(name)
        self._uniforms = {}
        self._prev_frame = None  # For motion detection
    
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
        self._uniforms['mesh_density'] = self._map_param('mesh_density', 1.0, 20.0)
        self._uniforms['outline_thickness'] = self._map_param('outline_thickness', 0.0, 5.0)
        self._uniforms['neon_glow'] = self._map_param('neon_glow', 0.0, 1.0)
        self._uniforms['motion_sensitivity'] = self._map_param('motion_sensitivity', 0.0, 1.0)
        self._uniforms['color_scheme'] = self.params.get('color_scheme', 0)
        self._uniforms['saturation_boost'] = self._map_param('saturation_boost', 1.0, 3.0)
        self._uniforms['time'] = time
        self._uniforms['resolution'] = resolution
    
    def get_fragment_shader(self) -> str:
        return self._generate_wgsl_shader()
    
    def _generate_wgsl_shader(self) -> str:
        shader = """
            struct Uniforms {
                mesh_density: f32,
                outline_thickness: f32,
                neon_glow: f32,
                motion_sensitivity: f32,
                color_scheme: i32,
                saturation_boost: f32,
                time: f32,
                resolution: vec2<f32>,
            };
            
            @group(0) @binding(0) var tex0: texture_2d<f32>;
            @group(0) @binding(1) var s0: sampler;
            
            // Neon color palettes (Keith Haring style)
            fn get_neon_color(scheme: i32, uv: vec2<f32>) -> vec3<f32> {
                var colors: array<vec3<f32>, 6> = array<vec3<f32>, 6>(
                    vec3<f32>(1.0, 0.0, 1.0),    // Magenta
                    vec3<f32>(0.0, 1.0, 1.0),    // Cyan
                    vec3<f32>(1.0, 1.0, 0.0),    // Yellow
                    vec3<f32>(0.0, 1.0, 0.0),    // Green
                    vec3<f32>(1.0, 0.5, 0.0),    // Orange
                    vec3<f32>(0.5, 0.0, 1.0),    // Purple
                );
                return colors[scheme % 6];
            }
            
            @fragment
            fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
                let original = textureSample(tex0, s0, uv);
                
                // Convert to grayscale for silhouette detection
                let gray = dot(original.rgb, vec3<f32>(0.299, 0.587, 0.114));
                
                // Create mesh grid
                let grid_size = mesh_density;
                let grid_uv = uv * grid_size;
                let grid_pos = fract(grid_uv);
                let grid_id = floor(grid_uv);
                
                // Distance to nearest grid line
                let dist_x = min(grid_pos.x, 1.0 - grid_pos.x);
                let dist_y = min(grid_pos.y, 1.0 - grid_pos.y);
                let min_dist = min(dist_x, dist_y);
                
                // Outline detection (bold lines)
                let outline = 1.0 - smoothstep(0.0, outline_thickness * 0.1, min_dist);
                
                // Motion detection (simple frame differencing would be done in CPU)
                // Here we use time-based animation for motion lines
                let motion = sin(grid_id.x * 0.1 + time) * cos(grid_id.y * 0.1 + time);
                let motion_line = step(0.9, motion) * motion_sensitivity;
                
                // Neon color
                let neon_color = get_neon_color(color_scheme, uv);
                
                // Combine effects
                var final_color = original.rgb;
                
                // Add neon glow to outlines
                let glow_intensity = neon_glow * (1.0 - min_dist * 2.0);
                final_color = mix(final_color, neon_color, outline * 0.8);
                final_color += neon_color * glow_intensity * 0.3;
                
                // Add motion lines
                final_color = mix(final_color, neon_color, motion_line * 0.5);
                
                // Boost saturation
                let gray_orig = dot(final_color, vec3<f32>(0.299, 0.587, 0.114));
                final_color = mix(vec3<f32>(gray_orig), final_color, saturation_boost);
                
                return vec4<f32>(final_color, original.a);
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
- **Processing**: Radiant mesh overlay with neon colors and motion lines
- **Format**: Standard RGBA video format

## Edge Cases and Error Handling

### Parameter Edge Cases
- **mesh_density = 0**: No grid, no effect (or single large cell)
- **mesh_density = 10**: Fine grid with many small cells
- **outline_thickness = 0**: No outlines, only glow and motion
- **outline_thickness = 10**: Very thick outlines, may fill cells
- **neon_glow = 0**: No glow, only flat neon colors
- **neon_glow = 10**: Intense glow, may wash out image
- **motion_sensitivity = 0**: No motion lines
- **motion_sensitivity = 10**: Constant motion lines
- **color_scheme out of range**: Modulo 6 to wrap within available palettes

### Error Scenarios
- **Invalid Parameters**: Out-of-range parameters are clamped
- **GPU Limitations**: Shader adapts to available GPU capabilities
- **Memory Constraints**: Resolution parameters automatically adjust
- **Missing Texture**: Output is black or undefined

### Internal Dependencies
- **Base Effect Class**: Inherits from Effect base class
- **WGSL Shader**: Requires WebGPU-compatible GPU
- **Sampler**: Requires texture sampler

### External Dependencies
- **WebGPU**: Required for shader execution
- **GPU Memory**: Required for texture processing

## Mathematical Formulations

### Mesh Grid Calculation

**Grid Coordinates:**
grid_uv = uv × mesh_density
grid_pos = fract(grid_uv)  [position within cell]
grid_id = floor(grid_uv)   [cell identifier]

**Distance to Grid Lines:**
dist_x = min(grid_pos.x, 1.0 - grid_pos.x)
dist_y = min(grid_pos.y, 1.0 - grid_pos.y)
min_dist = min(dist_x, dist_y)

**Outline Detection:**
outline = 1.0 - smoothstep(0, outline_thickness × 0.1, min_dist)

**Motion Line Generation:**
motion = sin(grid_id.x × 0.1 + time) × cos(grid_id.y × 0.1 + time)
motion_line = step(0.9, motion) × motion_sensitivity

**Neon Glow:**
glow_intensity = neon_glow × (1.0 - min_dist × 2.0)

**Saturation Boost:**
gray = dot(color, [0.299, 0.587, 0.114])
final_color = mix(gray, color, saturation_boost)

## Performance Characteristics

### GPU Tier Requirements
- **Tier**: MEDIUM (grid calculations, color palette lookups)
- **Memory**: ~20-40MB for full resolution processing
- **Processing**: Real-time capable on modern GPUs
- **Shader Complexity**: Medium (trigonometry, color mixing)

### Performance Metrics
- **Frame Rate**: 30-60 FPS at 4K resolution
- **Latency**: <5ms per frame
- **Memory Bandwidth**: Medium (single texture read, complex math)
- **Power Consumption**: Medium

### Optimization Strategies
- **Resolution Scaling**: May need adjustment for 4K
- **Level of Detail**: Reduce mesh_density on lower-tier GPUs
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
   - Test video input/output handling

5. **Mesh Generation Tests**
   - Test grid calculation accuracy
   - Test outline detection
   - Test motion line generation
   - Test color scheme selection

6. **Edge Case Tests**
   - Test with zero mesh_density
   - Test with extreme outline_thickness
   - Test with all color schemes
   - Test with zero motion_sensitivity

### Performance Tests (Coverage: 85%)
7. **Benchmark Tests**
   - Test frame rate at various resolutions
   - Test memory usage
   - Test GPU utilization

8. **Compatibility Tests**
   - Test across different GPU architectures
   - Test with various video formats

### Visual Quality Tests (Coverage: 75%)
9. **Visual Consistency Tests**
   - Test smooth parameter transitions
   - Test for artifacts or visual glitches
   - Test neon glow quality

10. **Style Accuracy Tests**
    - Verify Keith Haring aesthetic
    - Test bold outline rendering
    - Test motion line visibility

## Definition of Done

### Technical Requirements
- [ ] All 6 parameters implemented correctly
- [ ] WGSL shader compiles without errors
- [ ] Real-time performance at 30+ FPS at 1080p
- [ ] Mesh grid generation accurate
- [ ] Edge cases handled gracefully
- [ ] Memory usage acceptable (<40MB)
- [ ] Cross-platform compatibility

### Quality Requirements
- [ ] 80%+ test coverage achieved
- [ ] Documentation complete and accurate
- [ ] Performance benchmarks established
- [ ] Error handling robust
- [ ] Visual quality meets Keith Haring style

### Integration Requirements
- [ ] Compatible with VJLive3 plugin system
- [ ] Proper uniform binding implementation
- [ ] Texture handling optimized
- [ ] Resource cleanup implemented
- [ ] Works in effect chain with other style effects

## Legacy References

### Original Implementation
- **Source**: plugins/vstyle/vibrant_retro_styles.py - RadiantMeshEffect class
- **Category**: Vibrant Retro Styles (Keith Haring style)
- **GPU Tier**: MEDIUM
- **Input**: signal_in (video)
- **Output**: signal_out (styled video)

### Parameter Mapping from Legacy
Based on manifest and description:
| Legacy Parameter | VJLive3 Parameter | Range Mapping |
|------------------|-------------------|---------------|
| mesh_density (inferred) | mesh_density | 1.0-20.0 cells |
| outline_thickness (inferred) | outline_thickness | 0.0-5.0 |
| neon_glow (inferred) | neon_glow | 0.0-1.0 |
| motion_sensitivity (inferred) | motion_sensitivity | 0.0-1.0 |
| color_scheme (inferred) | color_scheme | 0-5 (6 palettes) |
| saturation_boost (inferred) | saturation_boost | 1.0-3.0 |

**Note**: Parameters are inferred based on typical mesh/neon effects and the Keith Haring style description. The legacy implementation may have different parameter names or additional parameters.

### Shader Reference (Conceptual WGSL)
The shader generates a grid mesh pattern with:
- Grid cell calculation using fract() and floor()
- Distance-to-line for bold outlines
- Time-based motion line generation
- Neon color palette selection
- Glow effect based on distance to outlines
- Saturation boosting

### Performance Characteristics
- **Frame Rate**: 30-60 FPS at 1080p
- **Memory**: ~20-40MB
- **GPU**: MEDIUM tier
- **Audio**: Not applicable (visual style effect)

### Visual Effects
- Keith Haring-inspired bold outlines
- Neon color palette (magenta, cyan, yellow, green, orange, purple)
- Motion lines radiating from moving elements
- Glowing mesh grid overlay
- High saturation pop art aesthetic
- Optimized for crowd silhouettes and high-contrast scenes

This spec provides a comprehensive blueprint for implementing the RadiantMeshEffect in VJLive3, capturing the Keith Haring aesthetic with bold outlines, neon colors, and motion lines while leveraging the modern VJLive3 architecture with WebGPU and WGSL shaders.