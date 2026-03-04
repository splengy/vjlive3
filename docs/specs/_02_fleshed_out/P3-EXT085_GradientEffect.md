# Spec Template — Focus on Technical Accuracy
## Task: P3-EXT085 — GradientEffect

## Core Functionality
Generates dynamic gradient effects synchronized with audio input, featuring:
- Real-time color interpolation between multiple stops
- Audio-reactive speed modulation
- Shader-based GPU acceleration
- Framebuffer blending for smooth transitions

## Key Parameters
1. `gradient_type` (enum: LINEAR, RADIAL, CIRCULAR)
2. `color_stops` (array of {position: float, color: [r,g,b,a]})
3. `speed_multiplier` (float, 0.1-10.0)
4. `audio_lock` (bool, enables frequency analysis)
5. `chaos_factor` (float, 0-1, adds procedural variation)

## Interaction with Particle System
- Modulates particle color gradients based on audio spectrum
- Syncs gradient transitions with beat detection
- Applies chaos factor to particle spawn rates

## Public Interface
```python
def create_gradient_effect(audio_input, params):
    # Initialize shader program
    # Set up color stops buffer
    # Connect audio analysis callback
    # Start effect loop
```

## Inputs and Outputs
**Inputs**
- Audio input buffer (16-bit PCM)
- Parameter configuration JSON

**Outputs**
- RGBA gradient texture
- Audio analysis metadata

## Edge Cases and Error Handling
- Fallback to CPU processing if GPU shader fails
- Graceful degradation for missing audio input
- Clamping of out-of-range parameter values

## Mathematical Formulations
```glsl
// Linear gradient interpolation
vec4 linear_gradient(float t, vec4 c1, vec4 c2) {
    return mix(c1, c2, t);
}

// Radial gradient with audio modulation
vec4 radial_gradient(vec2 coord, float radius, vec4 c1, vec4 c2, float audio_amp) {
    float dist = length(coord - vec2(0.5));
    float t = smoothstep(0.0, radius, dist);
    t *= audio_amp; // Audio-reactive modulation
    return mix(c1, c2, t);
}

// Audio spectrum analysis
float audio_spectrum(float frequency, float* spectrum, int size) {
    int bin = int(frequency * size / 22050.0);
    return spectrum[min(bin, size-1)];
}
```

## Performance Characteristics
- GPU-accelerated: 60+ FPS at 1080p on mid-range GPU
- Memory usage: ~15MB for gradient textures
- CPU overhead: ~2ms per frame for audio analysis
- Shader compilation: ~50ms initial setup

## Test Plan
1. **Unit Tests**
   - Gradient interpolation accuracy
   - Audio spectrum analysis correctness
   - Parameter clamping behavior

2. **Integration Tests**
   - Real-time performance under load
   - Audio synchronization accuracy
   - Cross-platform compatibility

3. **Stress Tests**
   - High-frequency audio input
   - Extreme parameter values
   - Memory leak detection

## Definition of Done
- [ ] All mathematical formulations implemented
- [ ] Performance benchmarks meet targets
- [ ] Audio synchronization accurate within 10ms
- [ ] Cross-platform compatibility verified
- [ ] Memory usage under 20MB
- [ ] Shader compilation succeeds on target hardware

## LEGACY CODE REFERENCES
- `plugins/vcore/generators.py` - Gradient effect implementation
- `core/effects/legacy_trash/generators.py` - Original gradient generator
- `shaders/gradient.frag` - Fragment shader implementation
- `audio/analyzer.py` - Audio spectrum analysis module
- `effects/gradient.py` - Main gradient effect class

Legacy code shows gradient effects were originally implemented as simple linear interpolations but evolved to include audio-reactive features and multiple gradient types. The current implementation uses WebGL shaders for real-time performance with fallback to CPU processing for compatibility.
