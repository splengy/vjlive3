# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT121_Particle3DSystem.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT121 — Particle3DSystem

**What This Module Does**
- Renders thousands of 3D particles in real-time with GPU acceleration
- Supports particle physics including gravity, wind, and collision detection
- Provides audio-reactive particle behavior through AudioReactor integration
- Enables complex particle systems with emitters, attractors, and forces
- Generates volumetric particle effects for immersive visual experiences

**What This Module Does NOT Do**
- Does not handle 2D particle systems (use separate 2D particle effect)
- Does not perform video decoding or encoding
- Does not manage audio processing (delegates to AudioReactor)
- Does not provide advanced fluid dynamics (basic physics only)

---

## Detailed Behavior and Parameter Interactions

Particle3DSystem creates and manages a large number of 3D particles that can be influenced by various forces and audio reactivity. The system operates in three main phases:

1. **Particle Emission**: Spawns particles from emitter points with initial velocity, color, and lifetime
2. **Physics Simulation**: Updates particle positions, velocities, and attributes each frame
3. **Rendering**: Draws particles using GPU-accelerated point sprites or mesh instancing

**Parameter Interactions**:
- `particle_count` (0.0-10.0) controls the number of active particles (scaled to 1000-100000)
- `emission_rate` (0.0-10.0) determines how quickly new particles spawn
- `lifetime` (0.0-10.0) sets particle lifespan in seconds
- `gravity` (0.0-10.0) applies downward acceleration
- `wind_strength` (0.0-10.0) applies horizontal force
- `audio_reactivity` (0.0-10.0) scales audio-driven parameter modulation
- `size` (0.0-10.0) controls particle sprite size
- `color_shift` (0.0-10.0) modifies particle color based on audio or time

---

## Public Interface

```python
class Particle3DSystem(Effect):
    def __init__(self):
        super().__init__()
        
        # Core particle parameters
        self.particle_count = Parameter("Particle Count", 0.0, 10.0, default=5.0)
        self.emission_rate = Parameter("Emission Rate", 0.0, 10.0, default=3.0)
        self.lifetime = Parameter("Lifetime", 0.0, 10.0, default=5.0)
        
        # Physics parameters
        self.gravity = Parameter("Gravity", 0.0, 10.0, default=2.0)
        self.wind_strength = Parameter("Wind Strength", 0.0, 10.0, default=0.0)
        self.wind_direction = Parameter("Wind Direction", 0.0, 10.0, default=0.0)
        self.drag = Parameter("Drag", 0.0, 10.0, default=1.0)
        
        # Visual parameters
        self.size = Parameter("Size", 0.0, 10.0, default=3.0)
        self.size_variation = Parameter("Size Variation", 0.0, 10.0, default=2.0)
        self.color_hue = Parameter("Color Hue", 0.0, 10.0, default=0.0)
        self.color_saturation = Parameter("Color Saturation", 0.0, 10.0, default=5.0)
        self.color_brightness = Parameter("Color Brightness", 0.0, 10.0, default=7.0)
        
        # Audio reactivity
        self.audio_reactivity = Parameter("Audio Reactivity", 0.0, 10.0, default=0.0)
        self.audio_low_react = Parameter("Audio Low React", 0.0, 10.0, default=0.0)
        self.audio_mid_react = Parameter("Audio Mid React", 0.0, 10.0, default=0.0)
        self.audio_high_react = Parameter("Audio High React", 0.0, 10.0, default=0.0)
        
        # Emitter settings
        self.emitter_shape = Parameter("Emitter Shape", 0.0, 10.0, default=0.0)
        self.emitter_radius = Parameter("Emitter Radius", 0.0, 10.0, default=1.0)
        self.emitter_spread = Parameter("Emitter Spread", 0.0, 10.0, default=3.0)
        
        # Advanced
        self.collision_enable = Parameter("Collision Enable", 0.0, 10.0, default=0.0)
        self.trail_length = Parameter("Trail Length", 0.0, 10.0, default=0.0)
```

---

## Inputs and Outputs

**Inputs:**
- `video_in` (optional): Background video frame to composite particles onto
- `audio_in` (optional): Audio analysis data from AudioReactor for reactivity

**Outputs:**
- `video_out` (required): Rendered frame with particles
- `particle_buffer` (optional): Debug output showing particle positions/velocities

---

## Edge Cases and Error Handling

**Edge Cases:**
- **Zero particle count**: No particles rendered, passes through video input
- **Extreme particle counts (>100000)**: Clamps to safe maximum based on GPU capability
- **Negative lifetime**: Particles die immediately
- **High gravity**: Particles may fall off screen quickly
- **Audio data missing**: Falls back to default parameter values
- **Low memory**: Reduces particle count automatically

**Error Handling:**
- Graceful degradation when GPU resources limited
- Particle pool management to prevent memory leaks
- Parameter validation with clamping
- Performance monitoring with automatic quality reduction

---

## Mathematical Formulations

**Particle Physics:**

```python
# Position update with velocity integration
def update_particle(particle, dt, gravity, wind, drag):
    # Apply forces
    particle.velocity.y -= gravity * dt
    particle.velocity += wind * dt
    particle.velocity *= (1.0 - drag * dt)
    
    # Update position
    particle.position += particle.velocity * dt
    
    # Update age
    particle.age += dt
```

**Particle Spawning:**

```python
def spawn_particle(emitter, count):
    for i in range(count):
        particle = Particle()
        
        # Position based on emitter shape
        if emitter.shape == 0:  # Point
            particle.position = emitter.position
        elif emitter.shape == 1:  # Sphere
            particle.position = random_point_in_sphere(emitter.radius)
        elif emitter.shape == 2:  # Box
            particle.position = random_point_in_box(emitter.radius)
        
        # Velocity with spread
        particle.velocity = emitter.base_velocity + random_vector() * emitter.spread
        
        # Randomize attributes
        particle.size = emitter.size * (1.0 + random_variation(emitter.size_variation))
        particle.color = emitter.base_color + random_color_variation()
        particle.lifetime = emitter.lifetime * (1.0 + random_variation(0.2))
        
        return particle
```

**Audio Reactivity:**

```glsl
// Audio-reactive particle modulation
vec3 audioReactColor(float low, float mid, float high, float reactivity) {
    vec3 base_color = vec3(1.0, 1.0, 1.0);
    vec3 low_color = vec3(1.0, 0.0, 0.0);
    vec3 mid_color = vec3(0.0, 1.0, 0.0);
    vec3 high_color = vec3(0.0, 0.0, 1.0);
    
    float audio_level = low * 0.3 + mid * 0.5 + high * 0.2;
    vec3 reactive_color = mix(base_color, 
                              low_color * low + mid_color * mid + high_color * high, 
                              audio_level * reactivity);
    return reactive_color;
}

// Audio-reactive size modulation
float audioReactSize(float base_size, float audio_level, float reactivity) {
    return base_size * (1.0 + audio_level * reactivity);
}
```

**Rendering (GPU Shader):**

```glsl
// Vertex shader for point sprite particles
#version 330 core
layout(location = 0) in vec3 inPosition;
layout(location = 1) in float inSize;
layout(location = 2) in vec3 inColor;
layout(location = 3) in float inAlpha;

uniform mat4 viewProjectionMatrix;
uniform float pointScale;

out vec3 fragColor;
out float fragAlpha;

void main() {
    gl_Position = viewProjectionMatrix * vec4(inPosition, 1.0);
    gl_PointSize = inSize * pointScale;
    fragColor = inColor;
    fragAlpha = inAlpha;
}
```

---

## Performance Characteristics

**Target Performance:**
- **60 FPS** with 10000 particles at 1080p on mid-range GPUs
- **30 FPS** with 50000 particles at 1080p on high-end GPUs
- **Frame time**: <16.67ms for 60 FPS target

**Optimization Strategies:**
- **GPU instancing**: Uses OpenGL geometry shaders or point sprites
- **Particle culling**: Frustum and distance-based culling
- **Level-of-detail**: Reduces particle count at lower resolutions
- **Compute shaders**: Optional compute-based simulation for large counts
- **Batch rendering**: Single draw call for all particles

**Memory Usage:**
- **Particle buffers**: ~1.5MB for 10000 particles (position, velocity, color, lifetime)
- **Shader programs**: ~100KB for particle rendering
- **Frame buffers**: Standard video frame size

**Scalability:**
- **Particle count**: Linear scaling with GPU capability
- **Physics complexity**: Constant per-particle overhead
- **Rendering**: Efficient with instancing, scales well to high counts

---

## Test Plan

**Unit Tests:**
- [ ] Particle spawning creates particles with valid attributes
- [ ] Physics simulation updates positions correctly
- [ ] Particle lifetime management (spawn, age, death)
- [ ] Audio reactivity modulates parameters correctly
- [ ] Parameter clamping prevents invalid values
- [ ] Memory pool management (no leaks)

**Integration Tests:**
- [ ] Effect renders particles at target frame rates
- [ ] Audio reactivity responds to real audio input
- [ ] Parameter changes update effect in real-time
- [ ] Effect integrates with AudioReactor correctly
- [ ] Memory usage stable over extended operation

**Performance Tests:**
- [ ] 60 FPS with 10000 particles on target hardware
- [ ] Frame time variance <2ms under load
- [ ] Memory usage <100MB for typical operation
- [ ] GPU utilization <90% to allow other effects

**Visual Tests:**
- [ ] Particle appearance meets visual standards
- [ ] Physics behavior looks natural
- [ ] Audio reactivity creates musically responsive visuals
- [ ] Edge cases produce acceptable fallback behavior

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT121: Particle3DSystem` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Based on analysis of VJLive legacy codebases, this effect draws from:
- `core/effects/particles_3d.py` for AdvancedParticle3DSystem implementation patterns
- `core/effects/shader_base.py` for GPU-accelerated rendering techniques
- `core/effects/visualizer.py` for audio-reactive parameter modulation
- `core/effects/legacy_trash/` for experimental particle physics implementations

The implementation follows VJLive's established patterns for real-time visual effects with audio reactivity and parameter-based control, leveraging GPU instancing for high particle counts.
