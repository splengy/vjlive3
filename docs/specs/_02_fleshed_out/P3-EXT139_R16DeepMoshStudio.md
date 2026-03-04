# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT139 — R16DeepMoshStudio

## Detailed Behavior and Parameter Interactions

### Core R16 Deep Moshing
The R16DeepMoshStudio creates advanced datamosh effects using R16 depth data combined with multiple video sources. The effect processes up to 4 source videos (A, B, C, D) along with previous frame feedback and depth information to create complex, evolving visual distortions.

**Multi-Source Processing:**
- Source A (tex0): Primary video input
- Source B (tex1): Secondary video for blending
- Source C (tex2): Tertiary video for complex mixing
- Source D (tex3): Quaternary video for advanced compositions
- Previous Frame (texPrev): Temporal feedback for motion persistence
- Depth Data: Color depth (depth_tex) and R16 raw depth (depthRawTex)

**Depth-Driven Distortion:**
- R16 depth provides high-precision depth values (0-65535)
- Color depth provides visual depth representation
- Depth influence controls how strongly depth affects distortion
- Depth-based warping creates 3D-like spatial effects

**Datamosh Processing:**
- Frame decay controls how quickly previous frames fade
- Flow scale and speed control motion vector magnitude and velocity
- Blend mix determines source mixing ratios
- Moshing intensity controls glitch and corruption levels

**Temporal Processing:**
- Memory echo creates persistent visual trails
- Time dilation affects temporal evolution speed
- Frame-to-frame coherence maintains smooth transitions
- Feedback loops create recursive visual patterns

## Public Interface

```python
class R16DeepMoshStudio(Effect):
    METADATA = {
        'name': 'r16_deep_mosh_studio',
        'gpu_tier': 'HIGH',
        'input_type': 'video',
        'output_type': 'video',
        'description': 'Advanced datamosh using R16 depth and multiple video sources',
        'parameters': [
            # Depth Processing Parameters
            {'name': 'depth_influence', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'depth_gain', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            
            # Flow and Motion Parameters
            {'name': 'flow_scale', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'flow_speed', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 1.0},
            {'name': 'wave_direction', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
            
            # Moshing Parameters
            {'name': 'frame_decay', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'blend_mix', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'mix', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'dry_wet', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 7.0},
            
            # Temporal Parameters
            {'name': 'memory_echo', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'time_dilation', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 1.0},
            
            # Advanced Effects
            {'name': 'singularity_pull', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'wormhole_twist', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 1.0},
            {'name': 'star_stretch', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'event_horizon', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 1.0},
            {'name': 'hyperdrive_speed', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'horizon_bend', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 1.0},
            
            # Audio Reactivity
            {'name': 'wave_audio_reactivity', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'wave_bass_response', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'wave_treble_response', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'wave_amplitude', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'wave_frequency', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 1.0},
            {'name': 'wave_speed', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'wave_damping', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 1.0},
            {'name': 'wave_sharpness', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'wave_color_bleed', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 1.0},
            {'name': 'wave_complexity', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'wave_depth_influence', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            
            # Master Controls
            {'name': 'master_fader', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 8.0},
            {'name': 'has_depth_raw', 'type': 'bool', 'min': 0, 'max': 1, 'default': 1},
            {'name': 'has_depth_tex', 'type': 'bool', 'min': 0, 'max': 1, 'default': 1},
            {'name': 'has_tex1', 'type': 'bool', 'min': 0, 'max': 1, 'default': 1},
        ]
    }
    
    def __init__(self, name: str = "r16_deep_mosh_studio") -> None:
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
        # Depth Processing Uniforms
        self._uniforms['depth_influence'] = self._map_param('depth_influence', 0.0, 10.0)
        self._uniforms['depth_gain'] = self._map_param('depth_gain', 0.0, 10.0)
        
        # Flow and Motion Uniforms
        self._uniforms['flow_scale'] = self._map_param('flow_scale', 0.0, 10.0)
        self._uniforms['flow_speed'] = self._map_param('flow_speed', 0.0, 10.0)
        self._uniforms['wave_direction'] = self._map_param('wave_direction', 0.0, 2.0 * math.pi)
        
        # Moshing Uniforms
        self._uniforms['frame_decay'] = self._map_param('frame_decay', 0.0, 1.0)
        self._uniforms['blend_mix'] = self._map_param('blend_mix', 0.0, 1.0)
        self._uniforms['mix'] = self._map_param('mix', 0.0, 1.0)
        self._uniforms['dry_wet'] = self._map_param('dry_wet', 0.0, 1.0)
        
        # Temporal Uniforms
        self._uniforms['memory_echo'] = self._map_param('memory_echo', 0.0, 10.0)
        self._uniforms['time_dilation'] = self._map_param('time_dilation', 0.1, 10.0)
        
        # Advanced Effects Uniforms
        self._uniforms['singularity_pull'] = self._map_param('singularity_pull', 0.0, 10.0)
        self._uniforms['wormhole_twist'] = self._map_param('wormhole_twist', 0.0, 10.0)
        self._uniforms['star_stretch'] = self._map_param('star_stretch', 0.0, 10.0)
        self._uniforms['event_horizon'] = self._map_param('event_horizon', 0.0, 10.0)
        self._uniforms['hyperdrive_speed'] = self._map_param('hyperdrive_speed', 0.0, 10.0)
        self._uniforms['horizon_bend'] = self._map_param('horizon_bend', 0.0, 10.0)
        
        # Audio Reactivity Uniforms
        if audio_reactor:
            energy = audio_reactor.get_energy()
            bass = audio_reactor.get_band('bass')
            treble = audio_reactor.get_band('treble')
            
            self._uniforms['audio_energy'] = energy
            self._uniforms['audio_bass'] = bass
            self._uniforms['audio_treble'] = treble
            
            # Apply audio reactivity to wave parameters
            audio_mod = self._map_param('wave_audio_reactivity', 0.0, 1.0)
            self._uniforms['wave_amplitude'] = self._map_param('wave_amplitude', 0.0, 10.0) * (1.0 + audio_mod * energy)
            self._uniforms['wave_frequency'] = self._map_param('wave_frequency', 0.0, 10.0) * (1.0 + audio_mod * bass)
            self._uniforms['wave_speed'] = self._map_param('wave_speed', 0.0, 10.0) * (1.0 + audio_mod * treble)
        else:
            self._uniforms['wave_amplitude'] = self._map_param('wave_amplitude', 0.0, 10.0)
            self._uniforms['wave_frequency'] = self._map_param('wave_frequency', 0.0, 10.0)
            self._uniforms['wave_speed'] = self._map_param('wave_speed', 0.0, 10.0)
        
        self._uniforms['wave_damping'] = self._map_param('wave_damping', 0.0, 1.0)
        self._uniforms['wave_sharpness'] = self._map_param('wave_sharpness', 0.0, 10.0)
        self._uniforms['wave_color_bleed'] = self._map_param('wave_color_bleed', 0.0, 1.0)
        self._uniforms['wave_complexity'] = self._map_param('wave_complexity', 0.0, 10.0)
        self._uniforms['wave_depth_influence'] = self._map_param('wave_depth_influence', 0.0, 10.0)
        self._uniforms['wave_bass_response'] = self._map_param('wave_bass_response', 0.0, 10.0)
        self._uniforms['wave_treble_response'] = self._map_param('wave_treble_response', 0.0, 10.0)
        
        # Master Controls
        self._uniforms['master_fader'] = self._map_param('master_fader', 0.0, 1.0)
        self._uniforms['has_depth_raw'] = self._map_param('has_depth_raw', 0.0, 1.0)
        self._uniforms['has_depth_tex'] = self._map_param('has_depth_tex', 0.0, 1.0)
        self._uniforms['has_tex1'] = self._map_param('has_tex1', 0.0, 1.0)
    
    def get_fragment_shader(self) -> str:
        return self._generate_wgsl_shader()
    
    def _generate_wgsl_shader(self) -> str:
        # Shader generation logic here
        pass
```

## Inputs and Outputs

### Input Requirements
- **Video Inputs**: Up to 4 RGBA video textures (tex0, tex1, tex2, tex3)
- **Previous Frame**: RGBA texture for temporal feedback (texPrev)
- **Depth Inputs**: 
  - Color depth texture (depth_tex) - RGBA depth representation
  - R16 raw depth texture (depthRawTex) - 16-bit depth values
- **Audio Input**: Optional audio reactor for reactivity
- **Resolution**: Any resolution supported by GPU
- **Frame Rate**: Any frame rate supported by GPU

### Output
- **Video Output**: Processed RGBA video texture (signal_out)
- **Processing**: Advanced datamosh with depth-driven distortion
- **Format**: Standard RGBA video format

## Edge Cases and Error Handling

### Parameter Edge Cases
- **Zero Values**: Parameters set to 0.0 produce minimal effects but remain functional
- **Maximum Values**: Parameters at 10.0 produce maximum intensity effects
- **Depth Missing**: Effect handles missing depth inputs gracefully (has_depth_raw/has_depth_tex flags)
- **Source Missing**: Effect handles missing source textures (has_tex1 flag)
- **Frame Decay**: 0.0 produces no decay, 1.0 produces instant decay

### Error Scenarios
- **Missing Audio**: Effect functions without audio input (audio_reactor = None)
- **Invalid Parameters**: Out-of-range parameters are clamped to valid ranges
- **GPU Limitations**: Shader adapts to available GPU capabilities
- **Memory Constraints**: Resolution parameters automatically adjust to available memory
- **Texture Missing**: Missing textures default to black or previous frame

### Internal Dependencies
- **Base Effect Class**: Inherits from Effect base class
- **WGSL Shader**: Requires WebGPU-compatible GPU
- **Audio Reactor**: Optional dependency for audio reactivity
- **Render Pipeline**: Requires compatible render pipeline
- **Texture Management**: Requires texture pooling for multiple sources

### External Dependencies
- **WebGPU**: Required for shader execution
- **GPU Memory**: Required for multiple texture processing
- **Audio System**: Optional for audio reactivity
- **Depth Source**: Required for depth-driven effects

## Mathematical Formulations

### Depth Processing

**Depth Influence:**
D_inf = depth_influence/10.0 · D_raw

**Depth Gain:**
D_gained = D_inf · depth_gain/10.0

### Flow and Motion

**Flow Vector:**
F = flow_scale/10.0 · (cos(θ), sin(θ)) · flow_speed/10.0

Where θ = wave_direction

**Wave Motion:**
W(x,t) = wave_amplitude · sin(2π · wave_frequency · x + wave_speed · t) · e^{-wave_damping · t}

### Datamosh Processing

**Frame Decay:**
F_decayed(t) = frame_decay · F(t-1) + (1 - frame_decay) · F(t)

**Blend Mix:**
B = blend_mix/10.0 · S_A + (1 - blend_mix/10.0) · S_B

Where S_A, S_B are source textures

**Dry/Wet Mix:**
O = dry_wet/10.0 · I + (1 - dry_wet/10.0) · P

Where I is input, P is processed

### Temporal Processing

**Memory Echo:**
E(t) = memory_echo/10.0 · E(t-1) + (1 - memory_echo/10.0) · O(t)

**Time Dilation:**
t' = time_dilation/10.0 · t

### Advanced Effects

**Singularity Pull:**
S_pull = singularity_pull/10.0 · (1 - |x - x_center|/R)

**Wormhole Twist:**
θ_twist = wormhole_twist/10.0 · (1 - |x - x_center|/R) · t

**Star Stretch:**
S_stretch = star_stretch/10.0 · (1 + |x - x_center|/R)

**Event Horizon:**
H = event_horizon/10.0 · (1 - |x - x_center|/R)^2

**Hyperdrive Speed:**
V_hyper = hyperdrive_speed/10.0 · t

**Horizon Bend:**
B_horizon = horizon_bend/10.0 · (1 - |x - x_center|/R)^3

### Audio Reactivity

**Audio-Modulated Wave:**
W_audio(x,t) = W(x,t) · (1 + wave_audio_reactivity/10.0 · E(t))

**Bass Response:**
A_bass = wave_bass_response/10.0 · bass(t)

**Treble Response:**
A_treble = wave_treble_response/10.0 · treble(t)

### Master Controls

**Master Fader:**
O_final = master_fader/10.0 · O_processed

## Performance Characteristics

### GPU Tier Requirements
- **Tier**: HIGH (based on legacy implementation with multiple textures and complex shader)
- **Memory**: ~200-400MB for full resolution processing with multiple sources
- **Processing**: Real-time capable on high-end GPUs
- **Shader Complexity**: Very high (multiple texture sampling, depth processing, complex math)

### Performance Metrics
- **Frame Rate**: 30-60 FPS at 1080p on high-end GPUs
- **Latency**: <20ms per frame at 60 FPS
- **Memory Bandwidth**: Very high (7+ texture samplers)
- **Power Consumption**: High (extensive GPU computation)

### Optimization Strategies
- **Resolution Scaling**: Automatic resolution adjustment based on performance
- **Texture Optimization**: Use lower precision textures when possible
- **Level of Detail**: Disable advanced effects on lower-tier GPUs
- **Temporal Coherence**: Frame-to-frame optimization for smooth transitions
- **Memory Management**: Efficient texture pooling and reuse
- **Audio Processing**: Adaptive audio analysis based on available resources

## Test Plan

### Unit Tests (Coverage: 95%)
1. **Parameter Mapping Tests**
   - Test _map_param() with boundary values (0.0, 10.0)
   - Test parameter clamping for out-of-range values
   - Test default parameter handling
   - Test boolean parameter conversion

2. **Uniform Application Tests**
   - Test apply_uniforms() with various parameter combinations
   - Test audio reactivity integration
   - Test resolution parameter handling
   - Test depth flag handling

3. **Shader Generation Tests**
   - Test _generate_wgsl_shader() output structure
   - Test uniform binding generation
   - Test shader compilation with test parameters
   - Test texture sampler generation

### Integration Tests (Coverage: 90%)
4. **Effect Pipeline Tests**
   - Test complete effect processing pipeline
   - Test video input/output handling
   - Test parameter interaction effects
   - Test multiple source texture blending

5. **Depth Processing Tests**
   - Test depth influence on distortion
   - Test R16 depth parsing
   - Test color depth processing
   - Test depth-based warping

6. **Audio Reactivity Tests**
   - Test audio-driven parameter modulation
   - Test beat detection integration
   - Test frequency band reactivity
   - Test bass/treble response

### Performance Tests (Coverage: 85%)
7. **Stress Tests**
   - Test maximum parameter values
   - Test minimum resolution limits
   - Test complex multi-source scenarios
   - Test memory usage with all sources active

8. **Compatibility Tests**
   - Test across different GPU architectures
   - Test with various video formats
   - Test with different audio sources
   - Test with missing depth sources

### Edge Case Tests (Coverage: 80%)
9. **Boundary Tests**
   - Test zero parameter values
   - Test maximum resolution limits
   - Test extreme audio conditions
   - Test missing texture scenarios

10. **Error Handling Tests**
    - Test missing audio reactor
    - Test invalid parameter combinations
    - Test GPU failure scenarios
    - Test texture loading failures

### Visual Quality Tests (Coverage: 75%)
11. **Visual Consistency Tests**
    - Test parameter transition smoothness
    - Test color accuracy
    - Test spatial coherence
    - Test depth-based effects

12. **Temporal Stability Tests**
    - Test frame-to-frame consistency
    - Test temporal aliasing prevention
    - Test motion coherence
    - Test memory echo persistence

## Definition of Done

### Technical Requirements
- [ ] All 30 parameters implemented with proper mapping
- [ ] WGSL shader generates without compilation errors
- [ ] Real-time performance maintained at 30+ FPS at 1080p
- [ ] Audio reactivity fully functional
- [ ] Edge cases handled gracefully
- [ ] Memory usage within acceptable limits (<400MB)
- [ ] Cross-platform compatibility verified
- [ ] Multiple source texture support working
- [ ] Depth processing (R16 and color) functional

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
- [ ] Texture handling optimized for multiple sources
- [ ] Resource cleanup implemented
- [ ] Depth texture format conversion working

## Legacy References

### Original Implementation
- **Source**: plugins/vdepth/r16_deep_mosh_studio.py and plugins/core/r16_deep_mosh_studio/__init__.py
- **Parameters**: 30 parameters across 6 groups (Depth Processing, Flow & Motion, Moshing, Temporal, Advanced Effects, Audio Reactivity)
- **GPU Tier**: HIGH
- **Input**: 4 video sources (tex0-tex3), previous frame, depth textures (color and R16)
- **Output**: signal_out (video)

### Parameter Mapping from Legacy
| Legacy Parameter | VJLive3 Parameter | Range Mapping |
|------------------|-------------------|---------------|
| depth_influence | depth_influence | 0.0-10.0 |
| depth_gain | depth_gain | 0.0-10.0 |
| flow_scale | flow_scale | 0.0-10.0 |
| flow_speed | flow_speed | 0.0-10.0 |
| wave_direction | wave_direction | 0.0-10.0 |
| frame_decay | frame_decay | 0.0-10.0 |
| blend_mix | blend_mix | 0.0-10.0 |
| mix | mix | 0.0-10.0 |
| dry_wet | dry_wet | 0.0-10.0 |
| memory_echo | memory_echo | 0.0-10.0 |
| time_dilation | time_dilation | 0.0-10.0 |
| singularity_pull | singularity_pull | 0.0-10.0 |
| wormhole_twist | wormhole_twist | 0.0-10.0 |
| star_stretch | star_stretch | 0.0-10.0 |
| event_horizon | event_horizon | 0.0-10.0 |
| hyperdrive_speed | hyperdrive_speed | 0.0-10.0 |
| horizon_bend | horizon_bend | 0.0-10.0 |
| wave_audio_reactivity | wave_audio_reactivity | 0.0-10.0 |
| wave_bass_response | wave_bass_response | 0.0-10.0 |
| wave_treble_response | wave_treble_response | 0.0-10.0 |
| wave_amplitude | wave_amplitude | 0.0-10.0 |
| wave_frequency | wave_frequency | 0.0-10.0 |
| wave_speed | wave_speed | 0.0-10.0 |
| wave_damping | wave_damping | 0.0-10.0 |
| wave_sharpness | wave_sharpness | 0.0-10.0 |
| wave_color_bleed | wave_color_bleed | 0.0-10.0 |
| wave_complexity | wave_complexity | 0.0-10.0 |
| wave_depth_influence | wave_depth_influence | 0.0-10.0 |
| master_fader | master_fader | 0.0-10.0 |
| has_depth_raw | has_depth_raw | bool |
| has_depth_tex | has_depth_tex | bool |
| has_tex1 | has_tex1 | bool |

### Texture Uniforms
- `tex0`: Source A (Unit 0)
- `texPrev`: Previous Frame (Unit 1)
- `depth_tex`: Color Depth (Unit 2)
- `tex1`: Source B (Unit 3)
- `depthRawTex`: R16 Depth (Unit 4)
- `tex2`: Source C (Unit 5)
- `tex3`: Source D (Unit 6)

### Performance Characteristics
- **Frame Rate**: 30-60 FPS at 1080p (high-end GPU)
- **Memory**: ~200-400MB
- **GPU**: HIGH tier
- **Audio**: Optional reactivity

### Visual Effects
- Depth-driven spatial warping
- Multi-source video blending
- Frame persistence and decay
- Wave-based distortion
- Singularity and wormhole effects
- Star stretching and horizon bending
- Hyperdrive speed effects
- Audio-reactive wave modulation

This spec provides a comprehensive blueprint for implementing the R16DeepMoshStudio in VJLive3, maintaining compatibility with the original legacy implementation while leveraging the modern VJLive3 architecture with WebGPU and WGSL shaders.