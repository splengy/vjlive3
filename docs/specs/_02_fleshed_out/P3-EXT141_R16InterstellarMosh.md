# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT141 — R16InterstellarMosh

## Detailed Behavior and Parameter Interactions

### Core Interstellar Moshing
The R16InterstellarMosh creates cosmic-scale visual distortions inspired by interstellar phenomena such as black holes, wormholes, gravitational lensing, and nebula formations. The effect uses R16 depth data to create 3D spatial warping and combines multiple video sources for complex interstellar compositions.

**Gravitational Effects:**
- Black hole singularity creates intense gravitational pull and event horizon effects
- Wormhole twisting creates spatial tunnels and dimensional portals
- Gravitational lensing bends light around massive objects
- Event horizon defines the point of no return for black hole effects

**Space Distortion:**
- Spatial warping creates non-Euclidean geometry
- Time dilation affects temporal evolution of effects
- Hyperdrive effects create speed lines and star streaks
- Nebula dispersion creates gaseous cloud formations

**Depth-Driven Cosmic Effects:**
- R16 depth provides high-precision depth for 3D spatial calculations
- Depth influence controls how strongly depth affects distortion
- Color depth provides visual depth representation
- Depth-based warping creates cosmic-scale spatial effects

**Multi-Source Composition:**
- Source A (tex0): Primary video input
- Source B (tex1): Secondary video for blending
- Previous Frame (texPrev): Temporal feedback for motion persistence
- Depth textures: Color depth and R16 raw depth

## Public Interface

```python
class R16InterstellarMosh(Effect):
    METADATA = {
        'name': 'r16_interstellar_mosh',
        'gpu_tier': 'HIGH',
        'input_type': 'video',
        'output_type': 'video',
        'description': 'Interstellar-scale visual distortions with black holes, wormholes, and gravitational effects',
        'parameters': [
            # Gravitational Effects
            {'name': 'singularity_pull', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'event_horizon', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'gravitational_lensing', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 4.0},
            {'name': 'wormhole_twist', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            
            # Space Distortion
            {'name': 'spatial_warp', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 4.0},
            {'name': 'time_dilation', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            {'name': 'hyperdrive_speed', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'star_stretch', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'nebula_dispersion', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            
            # Depth Processing
            {'name': 'depth_influence', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'depth_gain', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 3.0},
            {'name': 'color_bleed', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 2.0},
            
            # Moshing Parameters
            {'name': 'frame_decay', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'blend_mix', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'mix', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'dry_wet', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 7.0},
            
            # Master Controls
            {'name': 'master_fader', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 8.0},
            {'name': 'u_has_tex1', 'type': 'bool', 'min': 0, 'max': 1, 'default': 1},
            {'name': 'u_has_depth_raw', 'type': 'bool', 'min': 0, 'max': 1, 'default': 1},
        ]
    }
    
    def __init__(self, name: str = "r16_interstellar_mosh") -> None:
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
        # Gravitational Effects Uniforms
        self._uniforms['singularity_pull'] = self._map_param('singularity_pull', 0.0, 10.0)
        self._uniforms['event_horizon'] = self._map_param('event_horizon', 0.0, 10.0)
        self._uniforms['gravitational_lensing'] = self._map_param('gravitational_lensing', 0.0, 10.0)
        self._uniforms['wormhole_twist'] = self._map_param('wormhole_twist', 0.0, 10.0)
        
        # Space Distortion Uniforms
        self._uniforms['spatial_warp'] = self._map_param('spatial_warp', 0.0, 10.0)
        self._uniforms['time_dilation'] = self._map_param('time_dilation', 0.1, 10.0)
        self._uniforms['hyperdrive_speed'] = self._map_param('hyperdrive_speed', 0.0, 10.0)
        self._uniforms['star_stretch'] = self._map_param('star_stretch', 0.0, 10.0)
        self._uniforms['nebula_dispersion'] = self._map_param('nebula_dispersion', 0.0, 10.0)
        
        # Depth Processing Uniforms
        self._uniforms['depth_influence'] = self._map_param('depth_influence', 0.0, 10.0)
        self._uniforms['depth_gain'] = self._map_param('depth_gain', 0.0, 10.0)
        self._uniforms['color_bleed'] = self._map_param('color_bleed', 0.0, 1.0)
        
        # Moshing Uniforms
        self._uniforms['frame_decay'] = self._map_param('frame_decay', 0.0, 1.0)
        self._uniforms['blend_mix'] = self._map_param('blend_mix', 0.0, 1.0)
        self._uniforms['mix'] = self._map_param('mix', 0.0, 1.0)
        self._uniforms['dry_wet'] = self._map_param('dry_wet', 0.0, 1.0)
        
        # Master Controls
        self._uniforms['master_fader'] = self._map_param('master_fader', 0.0, 1.0)
        self._uniforms['u_has_tex1'] = self._map_param('u_has_tex1', 0.0, 1.0)
        self._uniforms['u_has_depth_raw'] = self._map_param('u_has_depth_raw', 0.0, 1.0)
        
        # Audio Reactivity (if available)
        if audio_reactor:
            energy = audio_reactor.get_energy()
            self._uniforms['audio_energy'] = energy
            self._uniforms['audio_modulation'] = energy * 0.5
    
    def get_fragment_shader(self) -> str:
        return self._generate_wgsl_shader()
    
    def _generate_wgsl_shader(self) -> str:
        # Shader generation logic here
        pass
```

## Inputs and Outputs

### Input Requirements
- **Video Inputs**: 
  - Source A (tex0): Primary video input
  - Source B (tex1): Secondary video for blending (optional)
  - Previous Frame (texPrev): Temporal feedback
- **Depth Inputs**: 
  - Color depth texture (depth_tex)
  - R16 raw depth texture (depthRawTex) - 16-bit depth values
- **Audio Input**: Optional audio reactor for reactivity
- **Resolution**: Any resolution supported by GPU
- **Frame Rate**: Any frame rate supported by GPU

### Output
- **Video Output**: Processed RGBA video texture (signal_out)
- **Processing**: Interstellar-scale visual distortions with gravitational effects
- **Format**: Standard RGBA video format

## Edge Cases and Error Handling

### Parameter Edge Cases
- **Zero Values**: Parameters set to 0.0 produce minimal effects but remain functional
- **Maximum Values**: Parameters at 10.0 produce maximum intensity effects
- **Missing Sources**: Effect handles missing source textures (u_has_tex1 flag)
- **Missing Depth**: Effect handles missing depth inputs (u_has_depth_raw flag)
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

### External Dependencies
- **WebGPU**: Required for shader execution
- **GPU Memory**: Required for texture processing
- **Audio System**: Optional for audio reactivity
- **Depth Source**: Required for depth-driven effects

## Mathematical Formulations

### Gravitational Effects

**Singularity Pull:**
P_singularity(x) = singularity_pull/10.0 · (1 - |x - x_center|/R)

Where R is the singularity radius.

**Event Horizon:**
H_event(x) = event_horizon/10.0 · (1 - |x - x_center|/R)^2

**Gravitational Lensing:**
L_grav(x) = gravitational_lensing/10.0 · M/|x - x_center|^2

Where M is the mass of the gravitational source.

**Wormhole Twist:**
θ_twist(x,t) = wormhole_twist/10.0 · (1 - |x - x_center|/R) · t

### Space Distortion

**Spatial Warp:**
W_spatial(x) = spatial_warp/10.0 · f_warp(x)

**Time Dilation:**
t' = time_dilation/10.0 · t

**Hyperdrive Speed:**
V_hyper(t) = hyperdrive_speed/10.0 · t

**Star Stretch:**
S_stretch(x) = star_stretch/10.0 · (1 + |x - x_center|/R)

**Nebula Dispersion:**
D_nebula(x,t) = nebula_dispersion/10.0 · f_noise(x,t)

### Depth Processing

**Depth Influence:**
D_inf = depth_influence/10.0 · D_raw

**Depth Gain:**
D_gained = D_inf · depth_gain/10.0

**Color Bleed:**
C_bleed(x,t) = C(x,t) · (1 + color_bleed/10.0 · D_gained)

### Moshing Processing

**Frame Decay:**
F_decayed(t) = frame_decay · F(t-1) + (1 - frame_decay) · F(t)

**Blend Mix:**
B = blend_mix/10.0 · S_A + (1 - blend_mix/10.0) · S_B

**Dry/Wet Mix:**
O = dry_wet/10.0 · I + (1 - dry_wet/10.0) · P

**Master Fader:**
O_final = master_fader/10.0 · O_processed

### Audio Reactivity

**Audio Modulation:**
A_mod = audio_energy · audio_modulation

**Audio-Driven Effects:**
E_audio(x,t) = E_base(x,t) · (1 + A_mod)

## Performance Characteristics

### GPU Tier Requirements
- **Tier**: HIGH (based on legacy implementation with complex gravitational calculations)
- **Memory**: ~150-300MB for full resolution processing
- **Processing**: Real-time capable on high-end GPUs
- **Shader Complexity**: Very high (gravitational calculations, depth processing, multi-source blending)

### Performance Metrics
- **Frame Rate**: 30-60 FPS at 1080p on high-end GPUs
- **Latency**: <20ms per frame at 60 FPS
- **Memory Bandwidth**: High (multiple texture samplers, complex math)
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
   - Test depth flag handling (u_has_tex1, u_has_depth_raw)

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

5. **Gravitational Effect Tests**
   - Test singularity pull calculations
   - Test event horizon effects
   - Test gravitational lensing
   - Test wormhole twist propagation

6. **Depth Processing Tests**
   - Test depth influence on distortion
   - Test R16 depth parsing
   - Test color depth processing
   - Test depth-based spatial warping

### Performance Tests (Coverage: 85%)
7. **Stress Tests**
   - Test maximum parameter values
   - Test minimum resolution limits
   - Test complex interstellar scenarios
   - Test memory usage with all effects active

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
    - Test gravitational effect smoothness

12. **Temporal Stability Tests**
    - Test frame-to-frame consistency
    - Test temporal aliasing prevention
    - Test motion coherence
    - Test frame decay persistence

## Definition of Done

### Technical Requirements
- [ ] All 20 parameters implemented with proper mapping
- [ ] WGSL shader generates without compilation errors
- [ ] Real-time performance maintained at 30+ FPS at 1080p
- [ ] Audio reactivity fully functional
- [ ] Edge cases handled gracefully
- [ ] Memory usage within acceptable limits (<300MB)
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
- **Source**: plugins/vdepth/r16_interstellar_mosh.py and plugins/core/r16_interstellar_mosh/__init__.py
- **Parameters**: 20 parameters across 5 groups (Gravitational Effects, Space Distortion, Depth Processing, Moshing, Master Controls)
- **GPU Tier**: HIGH
- **Input**: 2 video sources (tex0, tex1), previous frame, depth textures (color and R16)
- **Output**: signal_out (video)

### Parameter Mapping from Legacy
| Legacy Parameter | VJLive3 Parameter | Range Mapping |
|------------------|-------------------|---------------|
| singularity_pull | singularity_pull | 0.0-10.0 |
| event_horizon | event_horizon | 0.0-10.0 |
| gravitational_lensing | gravitational_lensing | 0.0-10.0 |
| wormhole_twist | wormhole_twist | 0.0-10.0 |
| spatial_warp | spatial_warp | 0.0-10.0 |
| time_dilation | time_dilation | 0.0-10.0 |
| hyperdrive_speed | hyperdrive_speed | 0.0-10.0 |
| star_stretch | star_stretch | 0.0-10.0 |
| nebula_dispersion | nebula_dispersion | 0.0-10.0 |
| depth_influence | depth_influence | 0.0-10.0 |
| depth_gain | depth_gain | 0.0-10.0 |
| color_bleed | color_bleed | 0.0-10.0 |
| frame_decay | frame_decay | 0.0-10.0 |
| blend_mix | blend_mix | 0.0-10.0 |
| mix | mix | 0.0-10.0 |
| dry_wet | dry_wet | 0.0-10.0 |
| master_fader | master_fader | 0.0-10.0 |
| u_has_tex1 | u_has_tex1 | bool |
| u_has_depth_raw | u_has_depth_raw | bool |

### Texture Uniforms
- `tex0`: Source A (Unit 0)
- `texPrev`: Previous Frame (Unit 1)
- `depth_tex`: Color Depth (Unit 2)
- `tex1`: Source B (Unit 3)
- `depthRawTex`: R16 Depth (Unit 4)

### Performance Characteristics
- **Frame Rate**: 30-60 FPS at 1080p (high-end GPU)
- **Memory**: ~150-300MB
- **GPU**: HIGH tier
- **Audio**: Optional reactivity

### Visual Effects
- Black hole singularity pull
- Event horizon effects
- Gravitational lensing
- Wormhole spatial twisting
- Spatial warping
- Time dilation
- Hyperdrive speed lines
- Star stretching
- Nebula dispersion
- Depth-driven cosmic distortion
- Frame persistence and decay
- Multi-source blending

This spec provides a comprehensive blueprint for implementing the R16InterstellarMosh in VJLive3, maintaining compatibility with the original legacy implementation while leveraging the modern VJLive3 architecture with WebGPU and WGSL shaders.