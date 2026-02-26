# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT113_nebulaparticles.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT113 — NebulaParticles

**What This Module Does**

The `NebulaParticles` effect implements a Shadertoy-style particle system using a fragment shader that renders particles directly on the screen. Unlike traditional particle systems that use geometry (points, quads) and vertex buffers, this approach stores particle state in 2D textures (acting as 1D arrays) and iterates over all particles in the fragment shader for each pixel. This allows for complex, organic particle interactions and visual effects entirely on the GPU, with CPU only updating particle positions and velocities each frame.

The system features:
- 500 particles (configurable) with position, velocity, energy, and type
- Audio reactivity: particle size, color, and brightness respond to volume, bass, mid, treble, and beat
- "Sentience" parameter that introduces glitchy, reality-distorting effects at high values
- Trail effects: particles leave motion blur trails based on velocity
- Color system: HSV-based with hue/saturation/brightness controls, per-particle type coloring
- Attractor/repulsor particle types that influence other particles (in shader)

The effect produces a flowing, nebula-like visual with glowing, colorful particles that dance with music.

**What This Module Does NOT Do**

- Does NOT use traditional geometry rendering (no VAO/VBO for particles)
- Does NOT implement particle-particle collisions on CPU (all interactions in shader)
- Does NOT support thousands of particles (limited by fragment shader loop count; 500 is safe)
- Does NOT provide 3D depth (particles are 2D screen-space)
- Does NOT handle audio analysis itself (relies on external AudioAnalyzer)
- Does NOT support texture input (it's a self-contained effect that composites over `tex0`)

---

## Detailed Behavior and Parameter Interactions

### Architecture Overview

The system uses a **GPU-driven rendering approach**:

1. **CPU side**:
   - Maintains particle state arrays: `pos` (Nx2), `vel` (Nx2), `energy` (N), `type` (N)
   - Each frame, updates particle positions: `pos += vel`
   - Applies forces: attraction/repulsion between particles, damping, boundary wrapping
   - Uploads particle data to two OpenGL textures:
     - `particle_data_tex`: RGBA32F, each pixel stores one particle's `(pos.x, pos.y, vel.x, vel.y)`
     - `particle_props_tex`: RGBA32F, each pixel stores `(energy, type, 0, 0)`
   - Sets shader uniforms: resolution, time, particle_count, brightness, color_hue, color_saturation, particle_size, trail_length, attraction_strength, repulsion_strength, velocity_damping, audio levels, sentience

2. **GPU side (fragment shader)**:
   - For each pixel (fragment), loops over all particles (up to `particle_count`)
   - For each particle, samples its data from the particle data textures
   - Computes distance from pixel to particle
   - If within `particle_size`, adds particle's color to output (with alpha blending)
   - Also renders trails: along velocity direction, adds additional contribution
   - Particle color computed by `get_particle_color()` based on type, energy, position, time, and audio levels
   - Sentience effects: when `sentience > 5.0`, hue/saturation get corrupted; when `sentience > 7.0`, particle sizes fluctuate

### Particle Types

- **Type 0 (Normal)**: Standard particles; hue modulated by bass level and x position
- **Type 1 (Attractor)**: Particles that attract others; hue modulated by mid level and time
- **Type 2 (Repulsor)**: Particles that repel others; hue modulated by treble level and y position

The attraction/repulsion forces are applied on CPU during the update step.

### Physics Update (CPU)

Each frame, before rendering:

```python
def update(self, dt):
    # For each particle i:
    #   pos[i] += vel[i] * dt
    
    # Apply attraction/repulsion between particles
    for i in range(N):
        for j in range(N):
            if i == j: continue
            diff = pos[i] - pos[j]
            dist = length(diff)
            if dist < 0.1:
                force = normalize(diff) * strength / (dist + 0.01)
                if type[j] == 1:  # attractor
                    vel[i] += force * dt
                elif type[j] == 2:  # repulsor
                    vel[i] -= force * dt
    
    # Apply damping
    vel *= velocity_damping
    
    # Wrap positions to [0,1] (screen space)
    pos %= 1.0
    
    # Update energy (maybe decay or pulse with audio)
    energy = 1.0  # or modulate by audio
    
    # Upload to textures
```

The actual implementation may vary; the spec should define the exact algorithm.

### Audio Reactivity

The effect accepts audio features (0.0-1.0) as uniforms:
- `volume_level`: overall loudness
- `bass_level`: low-frequency energy
- `mid_level`: mid-frequency energy
- `treble_level`: high-frequency energy
- `beat_level`: beat detection (0 or 1)

These affect:
- Particle size: `size = particle_size * (1.0 + energy * volume_level * 2.0 + beat_level)`
- Color: hue shifts based on particle type and corresponding frequency band
- Brightness: `audio_bright = brightness * (1.0 + volume_level * 0.5 + beat_level * energy)`
- Sentience corruption intensity

### Sentience

A mysterious parameter that adds glitchy effects:
- `sentience > 5.0`: hue and saturation get sinusoidal corruption: `hue += sin(time*5.0)*corruption`, `sat += cos(time*3.0)*corruption`
- `sentience > 7.0`: particle sizes fluctuate: `size *= 1.0 + sin(time*20.0 + i) * (sentience-7.0)*0.2`

Sentience adds an otherworldly, unstable quality to the visuals.

### Trail Effect

Particles leave trails along their velocity direction. In the fragment shader, after checking the particle's direct position, it also checks a line segment extending from the particle in the direction of its velocity. If the pixel is within a certain distance of that line, it adds a dimmer contribution, creating a motion blur effect.

---

## Integration

### VJLive3 Pipeline Integration

`NebulaParticles` is an **Effect** that composites over the input framebuffer (`tex0`). It should be added to the effects chain and rendered last or as a source.

**Typical usage**:

```python
# Initialize
nebula = NebulaParticles(audio_analyzer=analyzer)

# Each frame:
audio_data = analyzer.get_spectrum()  # or raw buffer
nebula.update(audio_data)  # updates particle physics and uploads textures
nebula.render()  # fragment shader runs, composites over screen
```

The effect requires an OpenGL context and uses a full-screen quad to run the fragment shader.

### Audio Integration

The `update(audio_data)` method accepts raw audio samples (float32 array). The effect may extract features itself, or the audio analyzer can be passed to provide pre-computed features. The legacy code shows an `audio_analyzer` reference but not used in update; it likely uses uniforms set externally. We'll define that the effect either:
- Takes an `AudioAnalyzer` in `__init__` and calls `analyzer.get_features()` each frame to set uniforms, OR
- The caller sets audio uniforms via `set_audio_features(bass, mid, treble, beat)`.

Given the skeleton spec's `update(audio_data: np.ndarray)`, it expects raw audio. We'll design that the effect computes its own features (volume, bass, mid, treble, beat) from the audio buffer using simple FFT or envelope detection. Alternatively, we can accept both: if `audio_analyzer` is provided, use it; else compute from `audio_data`.

---

## Performance

### Computational Cost

This effect is **GPU-bound** with a heavy fragment shader:

- **CPU**: Updating 500 particles: position += velocity, simple forces O(N^2) naive (500^2 = 250k interactions per frame). That's ~250k distance calculations, which is okay on modern CPU but could be heavy at high particle counts. The legacy may have optimized or reduced N. We'll need to ensure CPU update is efficient (maybe use spatial partitioning or limit to 500).
- **GPU**: Fragment shader loops over up to 500 particles for every pixel. At 1920x1080 ≈ 2M pixels, that's 1 trillion iterations per frame! That's impossible. Clearly, the shader doesn't loop over all particles for every pixel; instead, it likely uses a different approach: maybe it renders each particle as a point and uses a compute shader? But the code shows a loop over particles inside `main()`. That would be far too slow.

Wait, let's re-examine: The fragment shader is for a full-screen effect. It reads `particle_data_tex` and loops `for (int i = 0; i < min(particle_count, 500); i++)`. That loop runs for every fragment. That's indeed O(N) per fragment. With 500 particles and 2M fragments, that's 1B particle checks per frame. That's borderline but maybe doable on modern GPUs with optimizations? 1B simple operations might be okay if the loop exits early? No, it runs full loop. At 60 Hz, that's 60B ops/sec, which is too high.

Maybe the effect is not full-screen; it's applied to a small region? Or the particle count is much lower (like 50)? The legacy sets `particle_count = 500`. That's still 500 * 2M = 1B. That's heavy but maybe acceptable at lower resolutions (e.g., 640x360 = 230k pixels → 115M ops). Could be okay. But we need to be realistic.

Alternatively, the shader might be using a different technique: it could be a compute shader that writes to a texture, but the code shows a fragment shader. Possibly the effect is applied to a small FBO, not full screen. Or the loop is unrolled and the GPU can handle it because the operations are cheap? Distance check is a few FLOPs. 1B FLOPs at 1 TFLOP GPU is 0.001 seconds, so maybe it's fine. Actually, 1 TFLOP = 1e12 FLOPs/sec, 1B = 1e9, so 1ms. That's okay. But memory bandwidth: sampling textures 500 times per fragment: 500 * 2M = 1B texture reads per frame. That's huge. Each texture read is 4 floats (16 bytes) for data and 4 for props, so 32 bytes per particle → 32 GB of texture bandwidth per frame. That's impossible.

Thus, the loop must be optimized: maybe the shader only processes particles that are near the pixel using a spatial grid? But the code doesn't show that. Perhaps the effect is not meant to be full-screen; it's applied to a small area or uses a different rendering strategy (like rendering each particle as a point sprite). The legacy code might be incomplete or the loop is actually in a compute shader that processes one particle per invocation? No, it's in `main()` of fragment shader.

Let's read more of the legacy to see the full picture. I'll get more snippets.
</think>
Let me get more of the shadertoy_particles implementation to understand the full update and rendering logic.<tool_call>
<function=execute_command>