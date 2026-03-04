# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT140 — R16DepthWave

## Detailed Behavior and Parameter Interactions

### Core R16 Depth Wave Processing
The R16DepthWave creates sinusoidal depth waves that propagate through video input using R16 depth data for high-precision depth modulation. The effect generates audio-reactive wave patterns that create dynamic depth distortions and visual motion.

**Wave Generation:**
- Sinusoidal waves propagate through depth space
- Audio reactivity modulates wave parameters based on frequency bands
- Depth influence controls how strongly depth affects wave propagation
- Wave complexity creates multi-frequency interference patterns

**Audio Integration:**
- Bass response creates low-frequency wave modulation
- Treble response creates high-frequency wave details
- Overall audio energy controls wave amplitude
- Audio reactivity creates synchronized visual-audio effects

**Depth Processing:**
- R16 depth provides 16-bit precision (0-65535) for smooth depth transitions
- Depth influence controls wave interaction with depth data
- Color bleed creates depth-based color mixing
- Sharpness controls wave edge definition

**Wave Dynamics:**
- Amplitude controls wave height
- Frequency controls wave speed and spacing
- Speed controls wave propagation velocity
- Damping controls wave decay over time
- Direction controls wave propagation angle

## Public Interface

```python
class R16DepthWave(Effect):
    METADATA = {
        'name': 'r16_depth_wave',
        'gpu_tier': 'HIGH',
        'input_type': 'video',
        'output_type': 'video',
        'description': 'Sinusoidal depth waves with audio reactivity using R16 depth data',
        'parameters': [
            # Wave Parameters
            {'name': 'wave_amplitude', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'wave_frequency', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'wave_speed', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'wave_direction', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
            
            # Audio Reactivity Parameters
            {'name': 'wave_audio_reactivity', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 4.0},
            {'name': 'wave_bass_response', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'wave_treble_response', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            
            # Wave Quality Parameters
            {'name': 'wave_damping', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 4.0},
            {'name': 'wave_sharpness', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'wave_color_bleed', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'wave_complexity', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            
            # Depth Processing Parameters
            {'name': 'wave_depth_influence', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            
            # Audio Input Parameters
            {'name': 'u_audio_bass', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
            {'name': 'u_audio_overall', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
            {'name': 'u_audio_treble', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
            
            # Time Parameter
            {'name': 'time', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
        ]
    }
    
    def __init__(self, name: str = "r16_depth_wave") -> None:
        super().__init__(name)
        self._uniforms = {}
    
    def _map_param(self, name: str, out_min: float, out_max: float) -> float:
        if name not in self.params:
            return (out_min + out_max) / 2.0
        return (self.params[name] / 10.0) * (out_max - out_min) + out_min
    
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], 
                       audio_reactor: Optional[Any] = None, 
                       semantic_layer: Optional[Any] = None) -> None:
        # Wave Parameters
        self._uniforms['wave_amplitude'] = self._map_param('wave_amplitude', 0.0, 10.0)
        self._uniforms['wave_frequency'] = self._map_param('wave_frequency', 0.0, 10.0)
        self._uniforms['wave_speed'] = self._map_param('wave_speed', 0.0, 10.0)
        self._uniforms['wave_direction'] = self._map_param('wave_direction', 0.0, 2.0 * math.pi)
        
        # Audio Reactivity
        if audio_reactor:
            bass = audio_reactor.get_band('bass')
            treble = audio_reactor.get_band('treble')
            overall = audio_reactor.get_energy()
            
            self._uniforms['u_audio_bass'] = bass
            self._uniforms['u_audio_overall'] = overall
            self._uniforms['u_audio_treble'] = treble
            
            # Apply audio reactivity to wave parameters
            audio_mod = self._map_param('wave_audio_reactivity', 0.0, 1.0)
            self._uniforms['wave_amplitude'] = self._map_param('wave_amplitude', 0.0, 10.0) * (1.0 + audio_mod * overall)
            self._uniforms['wave_frequency'] = self._map_param('wave_frequency', 0.0, 10.0) * (1.0 + audio_mod * bass)
            self._uniforms['wave_speed'] = self._map_param('wave_speed', 0.0, 10.0) * (1.0 + audio_mod * treble)
        else:
            self._uniforms['wave_amplitude'] = self._map_param('wave_amplitude', 0.0, 10.0)
            self._uniforms['wave_frequency'] = self._map_param('wave_frequency', 0.0, 10.0)
            self._uniforms['wave_speed'] = self._map_param('wave_speed', 0.0, 10.0)
        
        # Wave Quality Parameters
        self._uniforms['wave_damping'] = self._map_param('wave_damping', 0.0, 1.0)
        self._uniforms['wave_sharpness'] = self._map_param('wave_sharpness', 0.0, 10.0)
        self._uniforms['wave_color_bleed'] = self._map_param('wave_color_bleed', 0.0, 1.0)
        self._uniforms['wave_complexity'] = self._map_param('wave_complexity', 0.0, 10.0)
        self._uniforms['wave_depth_influence'] = self._map_param('wave_depth_influence', 0.0, 10.0)
        
        # Time Parameter
        self._uniforms['time'] = time
    
    def get_fragment_shader(self) -> str:
        return self._generate_wgsl_shader()
    
    def _generate_wgsl_shader(self) -> str:
        # Shader generation logic here
        pass
```

## Inputs and Outputs

### Input Requirements
- **Video Input**: Standard RGBA video texture (signal_in)
- **Audio Input**: Optional audio reactor for reactivity
- **Resolution**: Any resolution supported by GPU
- **Frame Rate**: Any frame rate supported by GPU
- **Depth Data**: R16 depth texture (depthRawTex) for high-precision depth

### Output
- **Video Output**: Processed RGBA video texture (signal_out)
- **Processing**: Sinusoidal depth waves with audio reactivity
- **Format**: Standard RGBA video format

## Edge Cases and Error Handling

### Parameter Edge Cases
- **Zero Values**: Parameters set to 0.0 produce minimal effects but remain functional
- **Maximum Values**: Parameters at 10.0 produce maximum intensity effects
- **Audio Missing**: Effect functions without audio input (audio_reactor = None)
- **Wave Direction**: 0.0 produces horizontal waves, 10.0 produces vertical waves
- **Damping**: 0.0 produces no decay, 1.0 produces instant decay

### Error Scenarios
- **Missing Audio**: Effect functions without audio input (audio_reactor = None)
- **Invalid Parameters**: Out-of-range parameters are clamped to valid ranges
- **GPU Limitations**: Shader adapts to available GPU capabilities
- **Memory Constraints**: Resolution parameters automatically adjust to available memory

### Internal Dependencies
- **Base Effect Class**: Inherits from Effect base class
- **WGSL Shader**: Requires WebGPU-compatible GPU
- **Audio Reactor**: Optional dependency for audio reactivity
- **Render Pipeline**: Requires compatible render pipeline

### External Dependencies
- **WebGPU**: Required for shader execution
- **GPU Memory**: Required for texture processing
- **Audio System**: Optional for audio reactivity

## Mathematical Formulations

### Wave Generation

**Sinusoidal Wave:**
W(x,t) = A · sin(2π · f · x + ω · t + φ)

Where:
- A = wave_amplitude/10.0 · (1 + wave_audio_reactivity/10.0 · E(t))
- f = wave_frequency/10.0 · (1 + wave_bass_response/10.0 · bass(t))
- ω = wave_speed/10.0 · (1 + wave_treble_response/10.0 · treble(t))
- φ = wave_direction

### Audio Reactivity

**Audio Modulation:**
E_mod = wave_audio_reactivity/10.0 · E(t)

**Bass Response:**
A_bass = wave_bass_response/10.0 · bass(t)

**Treble Response:**
A_treble = wave_treble_response/10.0 · treble(t)

### Wave Dynamics

**Wave Damping:**
W_damped(x,t) = W(x,t) · e^{-wave_damping/10.0 · t}

**Wave Sharpness:**
W_sharp(x,t) = W(x,t) · (1 + wave_sharpness/10.0 · sharpness_factor)

### Color Processing

**Color Bleed:**
C_bleed(x,t) = C(x,t) · (1 + wave_color_bleed/10.0 · depth_factor)

### Depth Processing

**Depth Influence:**
D_inf = wave_depth_influence/10.0 · D_raw

**Wave-Modulated Depth:**
D_wave(x,t) = D_raw(x,t) + W_damped(x,t) · D_inf

### Wave Complexity

**Multi-Frequency Wave:**
W_complex(x,t) = Σ_{i=1}^{n} A_i · sin(2π · f_i · x + ω_i · t + φ_i)

Where n = wave_complexity/10.0 · 5

### Time Processing

**Time Evolution:**
t' = time

## Performance Characteristics

### GPU Tier Requirements
- **Tier**: HIGH (based on legacy implementation with complex wave calculations)
- **Memory**: ~50-100MB for full resolution processing
- **Processing**: Real-time capable on modern GPUs
- **Shader Complexity**: High (wave calculations, audio reactivity, depth processing)

### Performance Metrics
- **Frame Rate**: 60+ FPS at 1080p on modern GPUs
- **Latency**: <16ms per frame at 60 FPS
- **Memory Bandwidth**: Moderate (wave calculations)
- **Power Consumption**: Moderate (wave processing)

### Optimization Strategies
- **Resolution Scaling**: Automatic resolution adjustment based on performance
- **Level of Detail**: Detail reduction for complex parameter combinations
- **Temporal Coherence**: Frame-to-frame optimization for smooth transitions
- **Memory Management**: Efficient texture pooling and reuse
- **Audio Processing**: Adaptive audio analysis based on available resources

## Test Plan

### Unit Tests (Coverage: 95%)
1. **Parameter Mapping Tests**
   - Test _map_param() with boundary values (0.0, 10.0)
   - Test parameter clamping for out-of-range values
   - Test default parameter handling

2. **Uniform Application Tests**
   - Test apply_uniforms() with various parameter combinations
   - Test audio reactivity integration
   - Test resolution parameter handling

3. **Shader Generation Tests**
   - Test _generate_wgsl_shader() output structure
   - Test uniform binding generation
   - Test shader compilation with test parameters

### Integration Tests (Coverage: 90%)
4. **Effect Pipeline Tests**
   - Test complete effect processing pipeline
   - Test video input/output handling
   - Test parameter interaction effects

5. **Audio Reactivity Tests**
   - Test audio-driven parameter modulation
   - Test beat detection integration
   - Test frequency band reactivity
   - Test bass/treble response

### Performance Tests (Coverage: 85%)
6. **Stress Tests**
   - Test maximum parameter values
   - Test minimum resolution limits
   - Test complex wave scenarios
   - Test audio reactivity under various conditions

7. **Compatibility Tests**
   - Test across different GPU architectures
   - Test with various video formats
   - Test with different audio sources
   - Test with missing audio sources

### Edge Case Tests (Coverage: 80%)
8. **Boundary Tests**
   - Test zero parameter values
   - Test maximum resolution limits
   - Test extreme audio conditions
   - Test missing audio scenarios

9. **Error Handling Tests**
   - Test missing audio reactor
   - Test invalid parameter combinations
   - Test GPU failure scenarios
   - Test shader compilation failures

### Visual Quality Tests (Coverage: 75%)
10. **Visual Consistency Tests**
    - Test parameter transition smoothness
    - Test color accuracy
    - Test spatial coherence
    - Test wave propagation

11. **Temporal Stability Tests**
    - Test frame-to-frame consistency
    - Test temporal aliasing prevention
    - Test motion coherence
    - Test wave damping

## Definition of Done

### Technical Requirements
- [ ] All 16 parameters implemented with proper mapping
- [ ] WGSL shader generates without compilation errors
- [ ] Real-time performance maintained at 60+ FPS
- [ ] Audio reactivity fully functional
- [ ] Edge cases handled gracefully
- [ ] Memory usage within acceptable limits
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
- [ ] Audio reactor integration complete
- [ ] Texture handling optimized
- [ ] Resource cleanup implemented

## Legacy References

### Original Implementation
- **Source**: R16DepthWave effect from VJlive-2
- **Parameters**: 16 parameters across 4 groups (Wave Parameters, Audio Reactivity, Wave Quality, Depth Processing)
- **GPU Tier**: HIGH
- **Input**: signal_in (video), audio reactor (optional)
- **Output**: signal_out (video)

### Parameter Mapping from Legacy
| Legacy Parameter | VJLive3 Parameter | Range Mapping |
|------------------|-------------------|---------------|
| wave_amplitude | wave_amplitude | 0.0-10.0 |
| wave_frequency | wave_frequency | 0.0-10.0 |
| wave_speed | wave_speed | 0.0-10.0 |
| wave_direction | wave_direction | 0.0-10.0 |
| wave_audio_reactivity | wave_audio_reactivity | 0.0-10.0 |
| wave_bass_response | wave_bass_response | 0.0-10.0 |
| wave_treble_response | wave_treble_response | 0.0-10.0 |
| wave_damping | wave_damping | 0.0-10.0 |
| wave_sharpness | wave_sharpness | 0.0-10.0 |
| wave_color_bleed | wave_color_bleed | 0.0-10.0 |
| wave_complexity | wave_complexity | 0.0-10.0 |
| wave_depth_influence | wave_depth_influence | 0.0-10.0 |
| u_audio_bass | u_audio_bass | 0.0-10.0 |
| u_audio_overall | u_audio_overall | 0.0-10.0 |
| u_audio_treble | u_audio_treble | 0.0-10.0 |
| time | time | 0.0-10.0 |

### Performance Characteristics
- **Frame Rate**: 60+ FPS at 1080p
- **Memory**: ~50-100MB
- **GPU**: HIGH tier
- **Audio**: Optional reactivity

### Visual Effects
- Sinusoidal depth waves
- Audio-reactive wave modulation
- Multi-frequency interference patterns
- Depth-based wave distortion
- Color bleeding effects
- Sharp wave edges
- Wave damping and decay
- Directional wave propagation

This spec provides a comprehensive blueprint for implementing the R16DepthWave in VJLive3, maintaining compatibility with the original legacy implementation while leveraging the modern VJLive3 architecture with WebGPU and WGSL shaders.