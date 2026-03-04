# P3-EXT113: NebulaParticles

## Overview
NebulaParticles is a Shadertoy-based particle system that creates nebula/gas cloud effects. This plugin generates organic, flowing particle systems that simulate cosmic gas clouds with audio-reactive swirling and expansion behaviors.

## Public Interface

### Class: NebulaParticles
```python
class NebulaParticles(ShadertoyParticles):
    def __init__(self):
        super().__init__()
        self.particle_count = 300
        self.color_hue = 0.6  # Purple/blue
        self.color_saturation = 0.4
        self.particle_size = 0.01
        self.trail_length = 1.5
        self.velocity_damping = 0.999
    
    def _update_particles(self, time: float, volume: float, bass: float, mid: float, treble: float, beat: float):
        """Nebula-specific slow, flowing motion."""
        pass
```

## Inputs/Outputs

### Inputs
- **time**: float - Current time in seconds
- **volume**: float - Overall audio volume (0.0-1.0)
- **bass**: float - Bass frequency amplitude (0.0-1.0)
- **mid**: float - Mid frequency amplitude (0.0-1.0)
- **treble**: float - Treble frequency amplitude (0.0-1.0)
- **beat**: float - Beat detection signal (0.0-1.0)

### Outputs
- **particles_pos**: np.ndarray - Particle positions (N x 2)
- **particles_vel**: np.ndarray - Particle velocities (N x 2)
- **particles_energy**: np.ndarray - Particle energy levels (N)
- **color**: tuple - (hue, saturation, value) for rendering
- **size**: float - Particle size for rendering
- **trail_length**: float - Trail length for rendering

## Core Logic

### Particle System Architecture
- **Base Class**: Inherits from ShadertoyParticles
- **Particle Count**: 300 particles for optimal performance
- **Color Scheme**: Purple/blue hue (0.6) with moderate saturation (0.4)
- **Particle Size**: 0.01 units
- **Trail Length**: 1.5 seconds
- **Velocity Damping**: 0.999 for smooth motion

### Motion Algorithms

#### 1. Organic Flow Motion
```python
angle1 = time * 0.1 + i * 0.01
angle2 = time * 0.15 + i * 0.015

flow_force = np.array([
    np.sin(angle1) * 0.00001,
    np.cos(angle2) * 0.00001
])
```

#### 2. Audio-Reactive Swirling
```python
if mid > 0.1:
    swirl_center = np.array([0.5, 0.5])
    to_center = swirl_center - pos
    dist = np.linalg.norm(to_center)
    
    if dist > 0:
        tangent = np.array([-to_center[1], to_center[0]]) / dist
        swirl_force = tangent * mid * 0.00002
        flow_force += swirl_force
```

#### 3. Bass-Triggered Expansion
```python
if bass > 0.2:
    center = np.array([0.5, 0.5])
    away_from_center = pos - center
    dist = np.linalg.norm(away_from_center)
    if dist > 0:
        expansion = away_from_center / dist * bass * 0.00001
        flow_force += expansion
```

#### 4. Position Update
```python
vel += flow_force * dt
vel *= self.velocity_damping
pos += vel * dt
pos = np.mod(pos, 1.0)  # Wrap around
```

### Energy System
```python
target_energy = 0.3 + volume * 0.5 + np.sin(time * 0.5 + i * 0.1) * 0.2 + beat * 0.3
energy = energy * 0.995 + target_energy * 0.005
```

## Edge Cases

### Boundary Conditions
- **Position Wrapping**: Particles wrap around using modulo operation
- **Velocity Damping**: Prevents particles from accelerating indefinitely
- **Energy Decay**: Smooth energy transitions prevent sudden jumps

### Audio Input Handling
- **Thresholds**: Bass > 0.2, Mid > 0.1 for effect activation
- **Smooth Transitions**: Energy interpolation prevents audio artifacts
- **Zero Audio**: System maintains organic motion without audio input

### Performance Considerations
- **Particle Count**: 300 particles optimized for 60fps performance
- **Vector Operations**: NumPy operations for efficient computation
- **Memory Management**: Pre-allocated arrays for particle data

## Dependencies

### Core Dependencies
- **ShadertoyParticles**: Base class for particle systems
- **NumPy**: Vector operations and array management
- **ModernGL**: GPU rendering pipeline

### Audio System
- **AudioAnalyzer**: Provides volume, bass, mid, treble, beat data
- **BeatDetector**: Beat detection for rhythmic effects

### Rendering Pipeline
- **Framebuffer**: Off-screen rendering for particle effects
- **ShaderCompiler**: GLSL shader compilation
- **TextureManager**: GPU texture management

## Test Plan

### Unit Tests
1. **Initialization Tests**
   - Verify particle count = 300
   - Check default color values
   - Validate particle size and trail length

2. **Motion Tests**
   - Test organic flow motion without audio
   - Verify swirling effect with mid-range audio
   - Test expansion with bass frequencies
   - Validate position wrapping behavior

3. **Energy System Tests**
   - Test energy response to volume changes
   - Verify beat-triggered energy spikes
   - Check energy decay rates

4. **Audio Integration Tests**
   - Test with zero audio input
   - Verify response to different frequency ranges
   - Test beat detection integration

### Integration Tests
1. **Rendering Pipeline Integration**
   - Test with ModernGL context
   - Verify shader compilation
   - Check texture management

2. **Audio System Integration**
   - Test with real-time audio input
   - Verify beat detection synchronization
   - Check audio-reactive parameters

3. **Performance Tests**
   - Verify 60fps performance with 300 particles
   - Test memory usage stability
   - Check GPU resource management

### Edge Case Tests
1. **Boundary Conditions**
   - Test particle wrapping at edges
   - Verify velocity damping limits
   - Check energy bounds

2. **Audio Edge Cases**
   - Test with extreme audio levels
   - Verify behavior with no audio input
   - Check response to rapid audio changes

3. **System Stress Tests**
   - Test with maximum particle count
   - Verify performance under load
   - Check memory leak prevention

## Performance Requirements

### Target Specifications
- **Frame Rate**: 60fps minimum
- **Particle Count**: 300 particles
- **Memory Usage**: < 50MB for particle data
- **GPU Usage**: Optimized shader operations

### Optimization Strategies
- **Vectorization**: NumPy operations for bulk calculations
- **Pre-allocation**: Memory pools for particle data
- **GPU Offload**: Shader-based rendering where possible
- **Efficient Algorithms**: Optimized motion calculations

## Safety Considerations

### Resource Management
- **Memory Leaks**: Prevent particle data accumulation
- **GPU Resources**: Proper cleanup of textures and buffers
- **Audio Input**: Handle audio stream interruptions gracefully

### Error Handling
- **Invalid Audio Data**: Graceful degradation with default motion
- **GPU Failures**: Fallback to CPU rendering if needed
- **Memory Issues**: Automatic cleanup and recovery

## Implementation Notes

### Shader Integration
- **GLSL Shaders**: Custom shaders for nebula rendering
- **Particle Effects**: GPU-accelerated particle rendering
- **Color Grading**: Real-time color adjustments

### Audio Synchronization
- **Low Latency**: Real-time audio processing
- **Beat Alignment**: Precise beat detection integration
- **Frequency Response**: Accurate frequency band separation

### Visual Quality
- **Smooth Motion**: Sub-pixel particle movement
- **Organic Behavior**: Natural-looking particle interactions
- **Color Dynamics**: Rich, evolving color schemes

## References

### Legacy Implementation
- **File**: `/home/happy/Desktop/claude projects/vjlive/core/effects/shadertoy_particles.py`
- **Class**: `NebulaParticles` (lines 513-576)
- **Key Methods**: `_update_particles()` implementation

### Related Plugins
- **FireParticles**: Similar particle system with different motion
- **ShadertoyParticles**: Base class for all Shadertoy effects
- **DepthAcidFractal**: Depth-reactive particle system

## Success Criteria

### Functional Requirements
- [ ] 300 particles with smooth organic motion
- [ ] Audio-reactive swirling and expansion effects
- [ ] Real-time performance at 60fps
- [ ] Proper integration with audio analysis system
- [ ] Seamless rendering with ModernGL pipeline

### Quality Requirements
- [ ] No memory leaks or resource issues
- [ ] Stable performance under various conditions
- [ ] High visual quality with smooth transitions
- [ ] Robust error handling and recovery
- [ ] Comprehensive test coverage

### Integration Requirements
- [ ] Compatible with existing Shadertoy framework
- [ ] Proper audio system integration
- [ ] Seamless node graph integration
- [ ] Configurable through standard interfaces

---

*Specification approved for implementation. Ready for assignment to Implementation Engineer.*