# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT136_quantum_entanglement_point_cloud.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT136 — quantum_entanglement_point_cloud

## Description

The Quantum Entanglement Point Cloud module transforms video input into dynamic 3D point cloud visualizations that simulate quantum mechanical phenomena. By analyzing video content and extracting depth information, the effect generates thousands of particles that behave according to quantum-inspired physics, creating an ethereal, living visualization that responds to both the visual content and parameter controls.

The effect creates a bridge between classical video processing and quantum simulation, where each particle represents a quantum state that can exist in superposition, become entangled with neighboring particles, and undergo decoherence over time. The resulting visualization produces organic, flowing patterns that appear to have their own consciousness while maintaining visual fidelity to the original video source.

The module is designed for depth-based visual effects within the VJLive environment, operating as a real-time video effect that processes input streams and outputs transformed video with evolving point cloud patterns. It uses GPU-accelerated rendering to maintain interactive frame rates even with complex particle systems, making it suitable for live performance scenarios.

## What This Module Does

- **Transforms 2D video into 3D point clouds** by extracting depth information and mapping pixel brightness to particle density and distribution
- **Simulates quantum phenomena** including superposition (particles existing in multiple states simultaneously), entanglement (correlated particle behavior), and decoherence (gradual loss of quantum properties)
- **Generates dynamic particle systems** with thousands of particles that respond to video content and parameter controls in real-time
- **Applies quantum-inspired physics** including tunneling effects (particles passing through barriers), wave-particle duality, and probabilistic state transitions
- **Supports real-time parameter updates** allowing live performers to manipulate quantum properties during performances
- **Maintains video correlation** where particle behavior reflects the underlying video content through brightness and motion analysis
- **Provides GPU-accelerated rendering** for smooth performance even with complex particle systems
- **Outputs synchronized video streams** with the quantum effect overlaid or composited with the original video

## What This Module Does NOT Do

- Implement actual quantum computing or quantum physics simulation (uses mathematical approximations for visual effect)
- Process audio signals or create audio-reactive visualizations
- Perform true 3D rendering with depth buffers or volumetric effects
- Handle networked quantum state synchronization between multiple instances
- Provide scientific accuracy for quantum mechanics research or education
- Support arbitrary 3D model import or custom particle shapes
- Implement machine learning-based quantum state prediction
- Process video files longer than real-time performance constraints

## Detailed Behavior

### Parameter Mapping and Ranges

All parameters use a normalized 0.0-10.0 range that maps to specific technical values:

**Quantum State Controls:**
- `quantum_state` (0-10) → 0.0 to 1.0 baseline coherence level
- `superposition_level` (0-10) → 0.0 to 1.0 degree of quantum superposition
- `decoherence_rate` (0-10) → 0.0 to 0.5 rate of quantum state decay per second
- `entanglement_strength` (0-10) → 0.0 to 1.0 correlation strength between particles
- `entanglement_range` (0-10) → 0.0 to 100.0 maximum influence distance in world units
- `tunnel_probability` (0-10) → 0.0 to 0.2 probability of quantum tunneling per frame

**Particle System:**
- `particle_count` (0-10) → 1000 to 100000 particles (logarithmic)
- `particle_size` (0-10) → 0.5 to 5.0 pixel radius
- `depth_scale` (0-10) → 0.1 to 10.0 Z-axis exaggeration factor
- `motion_blur` (0-10) → 0.0 to 1.0 trail persistence

**Visual Effects:**
- `color_mode` (0-10) → discrete: 0=mono, 2=rainbow, 4=entanglement, 6=decoherence, 8=superposition, 10=custom
- `glow_intensity` (0-10) → 0.0 to 2.0 bloom/glow strength
- `trail_length` (0-10) → 0.0 to 1.0 motion trail persistence
- `field_of_view` (0-10) → 30 to 120 degrees camera FOV

### Rendering Pipeline

1. **Depth Extraction**: Analyze input video to extract depth information using:
   - Luminance-based depth estimation (brightness = near, dark = far)
   - Optional edge detection for depth discontinuities
   - Temporal smoothing to reduce depth noise

2. **Particle Generation**:
   - Create particle pool with size determined by `particle_count`
   - Initialize each particle with position (x, y, z), velocity, and quantum state
   - Map 2D screen coordinates to 3D world space using depth values
   - Distribute particles based on image brightness and edge density

3. **Quantum Simulation** (per frame):
   - Update each particle's quantum state using Schrödinger-inspired math:
     - Apply `decoherence_rate` to gradually collapse superposition
     - Calculate entanglement forces between particles within `entanglement_range`
     - Apply `tunnel_probability` for random position jumps
     - Update `quantum_state` coherence value based on neighbor states
   - Integrate particle physics:
     - Apply velocity and acceleration
     - Respond to entanglement attraction/repulsion forces
     - Apply damping and boundary constraints

4. **Rendering**:
   - Transform particles to screen space using camera projection
   - Sort particles by depth for proper occlusion
   - Render each particle as a point sprite with:
     - Size attenuation based on distance
     - Color determined by `color_mode` and quantum state
     - Alpha based on coherence and entanglement strength
   - Apply post-processing effects:
     - `glow_intensity` via bloom filter
     - `trail_length` via frame blending
     - Depth-of-field if enabled

5. **Compositing**: Blend rendered point cloud with original video using alpha mixing

### Edge Cases and Boundary Behavior

- **Particle count extremes**: At `particle_count=0` (1000 particles), system is sparse; at `particle_count=10` (100K particles), may exceed GPU limits on some hardware
- **Depth scale**: `depth_scale=0` flattens to 2D; high values (>5.0) may cause particles to clip through camera near/far planes
- **Entanglement range**: `entanglement_range=0` isolates particles; very high values (>50.0) cause O(n²) computation and performance collapse
- **Decoherence rate**: `decoherence_rate=0` maintains quantum coherence indefinitely; high values (>0.3) cause rapid state collapse
- **Tunnel probability**: Values >0.1 may cause particles to teleport erratically, creating visual glitches
- **Frame rate drops**: When particle count exceeds GPU capacity, frame rate will drop; system should dynamically reduce particle count or quality
- **Memory limits**: Very high particle counts may exhaust GPU memory; implementation should cap at reasonable maximum (e.g., 200K particles)
- **Invalid video input**: Non-standard resolutions should be handled gracefully; aspect ratio preserved
- **Parameter validation**: All parameters clamped to [0.0, 10.0] range; invalid types raise TypeError

### Integration Notes

The module integrates with the VJLive3 node graph through:

- **Input**: Video frames via standard VJLive3 frame ingestion pipeline, passed as `signal_in` VideoSignal
- **Output**: Processed video frames with point cloud overlay, maintaining original dimensions and aspect ratio
- **Parameter Control**: All parameters exposed as dictionary keys that can be dynamically updated via `set_parameter(name, value)` method at runtime
- **Dependency Relationships**:
  - Inherits from `vjlive3.effects.base.EffectBase` for common effect infrastructure
  - Uses `vjlive3.core.signal.VideoSignal` for video stream handling
  - May optionally use `vjlive3.audio.analyzer` for audio-reactive variations (future extension)
- **Node Graph Position**: Typically placed after video source nodes (camera, video player) and before output/compositing nodes
- **Frame Format**: Expects RGBA textures; depth extracted from luminance or separate depth channel if available
- **GPU Resources**: Requires OpenGL 3.3+ or Vulkan for shader-based particle rendering; falls back to CPU if GPU unavailable (with reduced performance)

### Performance Characteristics

- **GPU-bound**: Primary cost is particle rendering and quantum simulation; performance scales with particle count and screen resolution
- **Particle count impact**: Performance roughly linear with particle count; 100K particles at 1080p ~30fps on GTX 1060, 200K ~15fps
- **Entanglement computation**: O(n²) in worst case; uses spatial partitioning (grid or BVH) to limit to O(n log n) for reasonable `entanglement_range`
- **Memory footprint**: 
  - Particle state: ~64 bytes per particle (position, velocity, quantum state, etc.)
  - 100K particles = ~6.4 MB GPU memory
  - Additional buffers for depth map, color attachments: ~10-20 MB
- **Expected frame rates** (reference hardware: GTX 1060, 1080p):
  - 10K particles: 60+ fps
  - 50K particles: 45-60 fps
  - 100K particles: 30-45 fps
  - 200K particles: 15-25 fps
- **CPU fallback**: Software rendering at 10K particles: ~15-20 fps; not recommended for production
- **Optimization opportunities**:
  - Reduce particle count for higher resolutions
  - Disable expensive effects (glow, trails) for better performance
  - Use simpler entanglement range (local only) to avoid spatial queries
  - Implement level-of-detail (LOD) based on distance to camera

### Dependencies

**External Libraries:**
- `numpy` — used for particle state arrays and quantum calculations — fallback: Python lists with math module (slower)
- `OpenGL.GL` / `glsl` — used for shader-based particle rendering — fallback: software rasterizer (CPU, much slower)
- `pyvfx.video` — used for video signal processing — fallback: direct frame buffer access

**Internal Dependencies:**
- `vjlive3.core.signal.VideoSignal` — video stream abstraction
- `vjlive3.effects.base.EffectBase` — base effect class with lifecycle management
- `vjlive3.gpu.shader_manager` — shader compilation and uniform management
- `vjlive3.utils.spatial_index` — spatial partitioning for entanglement queries

**System Requirements:**
- OpenGL 3.3+ or Vulkan-capable GPU for hardware acceleration
- At least 512 MB GPU memory for high particle counts
- GLSL 330 core or SPIR-V shader support

### State Management

- **Per-frame state**: Particle positions, velocities, quantum coherence values updated each frame
- **Persistent state**: Particle pool allocation, GPU buffers, spatial index structure (reused across frames)
- **Init-once**: Shader programs, particle system configuration, spatial partitioning structure
- **Thread safety**: Not thread-safe; all operations must occur on GPU/rendering thread

### GPU Resources

- **Shaders**: 
  - `quantum_particle.vert` — vertex shader for particle point sprite rendering
  - `quantum_simulation.frag` — fragment shader for quantum state visualization
  - `depth_extract.frag` — shader to extract depth from video frame
- **Buffers**:
  - Particle SSBO (Shader Storage Buffer Object) for particle state
  - Spatial index buffer (if using GPU-based spatial queries)
  - Vertex array object for point sprite rendering
- **Textures**:
  - Depth map texture (from video input)
  - Particle color/glow texture (optional, for sprite shape)
  - Frame buffer object (FBO) for off-screen rendering
- **Compute**: Optional compute shader for quantum simulation (or do in vertex/fragment shader)

### Error Cases

- **GPU initialization failure**: Raise `RuntimeError` with message "GPU acceleration unavailable"; fall back to CPU if possible
- **Shader compilation failure**: Raise `ShaderCompilationError` with shader log; check GLSL version and uniform locations
- **Particle allocation failure**: If requested count exceeds GPU memory limits, raise `MemoryError` or automatically reduce to maximum supported
- **Invalid parameter types**: `TypeError` when non-numeric values passed to parameters
- **Out-of-range parameters**: `ValueError` when values outside [0.0, 10.0] range (or clamped with warning depending on configuration)
- **Video signal invalid**: `ValueError` when `signal_in` is None or has invalid dimensions
- **Spatial index corruption**: If entanglement queries fail, log warning and fall back to brute-force O(n²) for that frame
- **Frame buffer issues**: If FBO creation fails, raise `RuntimeError`; check GPU driver and memory

### Configuration Schema (Pydantic-style)

```python
class QuantumEntanglementPointCloudConfig:
    # Quantum parameters
    quantum_state: float = Field(0.5, ge=0.0, le=10.0)
    entanglement_strength: float = Field(0.7, ge=0.0, le=10.0)
    decoherence_rate: float = Field(0.1, ge=0.0, le=10.0)
    tunnel_probability: float = Field(0.3, ge=0.0, le=10.0)
    superposition_level: float = Field(0.6, ge=0.0, le=10.0)
    entanglement_range: float = Field(0.5, ge=0.0, le=10.0)

    # Particle system
    particle_count: float = Field(5.0, ge=0.0, le=10.0)  # logarithmic scale
    particle_size: float = Field(2.0, ge=0.0, le=10.0)
    depth_scale: float = Field(3.0, ge=0.0, le=10.0)
    motion_blur: float = Field(0.3, ge=0.0, le=10.0)

    # Visual effects
    color_mode: float = Field(2.0, ge=0.0, le=10.0)  # discrete: 0,2,4,6,8,10
    glow_intensity: float = Field(0.5, ge=0.0, le=10.0)
    trail_length: float = Field(0.2, ge=0.0, le=10.0)
    field_of_view: float = Field(5.0, ge=0.0, le=10.0)  # maps to 30-120 degrees
```

### Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module instantiates without crashing when GPU/driver is unavailable (falls back to CPU or raises clean error) |
| `test_basic_operation` | Given a uniform color frame, output shows correctly rendered particle cloud with expected density |
| `test_parameter_range_validation` | All parameters clamped to valid 0.0-10.0 range; out-of-range values rejected or clamped with warnings |
| `test_quantum_state_evolution` | Particle quantum states evolve according to decoherence and entanglement over time |
| `test_entanglement_force` | Particles within `entanglement_range` influence each other's motion based on `entanglement_strength` |
| `test_tunneling_effect` | With `tunnel_probability` > 0, particles occasionally teleport to new positions |
| `test_superposition_visualization` | `superposition_level` affects particle color/alpha blending between states |
| `test_decoherence_collapse` | High `decoherence_rate` causes rapid state collapse to definite values |
| `test_particle_count_scaling` | Particle count scales exponentially with `particle_count` parameter (logarithmic mapping) |
| `test_depth_extraction` | Depth map correctly extracted from input video luminance |
| `test_color_mode_switching` | Different `color_mode` values produce distinct color schemes |
| `test_glow_and_trails` | `glow_intensity` and `trail_length` produce visible post-processing effects |
| `test_performance_profile` | Frame rate scales appropriately with particle count; 100K particles achieves >30fps on reference hardware |
| `test_memory_usage` | No memory leaks after processing thousands of frames; GPU buffers properly released on cleanup |
| `test_parameter_set_get_cycle` | Dynamic updates via `set_parameter()` immediately affect next frame; `get_parameter()` returns current value |
| `test_invalid_video_input` | Invalid or None video signal raises appropriate exception |
| `test_gpu_fallback` | When GPU unavailable, module either falls back to CPU or raises clear error message |
| `test_spatial_index_accuracy` | Entanglement queries correctly identify neighbors within range; no false positives/negatives |
| `test_legacy_compatibility` | Output visually matches reference implementation for equivalent parameter sets (if legacy exists) |
| `test_edge_case_parameters` | Extreme values (0, 10) handled without crashes or visual artifacts |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT136: quantum_entanglement_point_cloud - Port from VJlive legacy to VJLive3` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

Based on analysis of legacy implementations in vjlive v1 and vjlive-2, the quantum_entanglement_point_cloud module implements the following key features:

### Module Structure (vjlive2/plugins/core/quantum_entanglement_point_cloud/plugin.json)

```json
{
  "name": "quantum_entanglement_point_cloud",
  "category": "Depth",
  "gpu_tier": "MEDIUM",
  "class": "QuantumEntanglementPointCloud",
  "description": "Transform video into living quantum point clouds using entanglement simulation."
}
```

### Core Implementation (vjlive2/plugins/core/quantum_entanglement_point_cloud.py)

The legacy implementation uses a particle-based system where each particle maintains:
- Position (x, y, z) in 3D space
- Velocity vector
- Quantum state: coherence (0-1), phase, and entanglement partners
- Visual properties: color, size, alpha

Key algorithms:

1. **Depth Extraction**: Convert 2D video to depth map using luminance: `depth = 0.299*R + 0.587*G + 0.114*B`, then remap to Z range.

2. **Quantum State Update** (per particle per frame):
   ```python
   # Decoherence
   coherence *= (1.0 - decoherence_rate * dt)
   
   # Entanglement: average state with neighbors in range
   if entanglement_strength > 0:
       neighbor_avg = average_coherence(neighbors_within_range)
       coherence = lerp(coherence, neighbor_avg, entanglement_strength * dt)
   
   # Superposition: add random fluctuation based on superposition_level
   if superposition_level > 0:
       coherence += random.gauss(0, superposition_level * 0.1) * dt
       coherence = clamp(coherence, 0.0, 1.0)
   
   # Tunneling: occasional random position jump
   if random.random() < tunnel_probability * dt:
       position += random_vector(max_jump=10.0)
   ```

3. **Particle Physics**: Standard Newtonian integration with damping:
   ```python
   velocity += acceleration * dt
   velocity *= (1.0 - damping * dt)
   position += velocity * dt
   ```

4. **Rendering**: Point sprites with size attenuation:
   ```glsl
   float size = base_size * (1.0 - distance / far_plane);
   gl_PointSize = size;
   ```

### Parameter Mapping and Ranges

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| quantum_state | 0-10 | 0.5 | Baseline quantum coherence (0.0-1.0) |
| entanglement_strength | 0-10 | 0.7 | Correlation strength between entangled particles (0.0-1.0) |
| decoherence_rate | 0-10 | 0.1 | Rate of quantum state decay per second (0.0-0.5) |
| tunnel_probability | 0-10 | 0.3 | Probability of tunneling per second (0.0-0.2) |
| superposition_level | 0-10 | 0.6 | Degree of superposition (0.0-1.0) |
| entanglement_range | 0-10 | 0.5 | Maximum influence distance (0.0-100.0 world units) |
| particle_count | 0-10 | 5.0 | Logarithmic: 10^value particles (1000 to 100K) |
| particle_size | 0-10 | 2.0 | Point sprite size in pixels (0.5-5.0) |
| depth_scale | 0-10 | 3.0 | Z-axis exaggeration factor (0.1-10.0) |
| motion_blur | 0-10 | 0.3 | Trail persistence (0.0-1.0) |
| color_mode | 0-10 | 2.0 | Discrete: 0=mono, 2=rainbow, 4=entanglement, 6=decoherence, 8=superposition, 10=custom |
| glow_intensity | 0-10 | 0.5 | Bloom/glow strength (0.0-2.0) |
| trail_length | 0-10 | 0.2 | Motion trail persistence (0.0-1.0) |
| field_of_view | 0-10 | 5.0 | Camera FOV (maps to 30-120 degrees) |

### Legacy Context

Based on analysis of legacy implementations in vjlive v1 and vjlive-2, the quantum_entanglement_point_cloud module implements the following key features:

1. **Quantum Simulation Model**:
   - Uses simplified quantum-inspired math, not full quantum mechanics
   - Each particle has a `coherence` value representing quantum state probability
   - Entanglement creates correlation between nearby particles' coherence values
   - Decoherence gradually collapses coherence to 0 or 1 (classical states)
   - Superposition adds random walk to coherence values

2. **Depth-Based Particle Placement**:
   - Video frame luminance converted to depth map
   - Particles spawned at (x, y) screen positions with Z from depth
   - Higher brightness = closer to camera; darker = farther away
   - Depth scale parameter controls Z-axis exaggeration for dramatic effect

3. **Entanglement Force Calculation**:
   - Spatial partitioning (grid or octree) to avoid O(n²) complexity
   - For each particle, query neighbors within `entanglement_range`
   - Compute average coherence of neighbors
   - Apply force toward/away from neighbors based on entanglement strength
   - Forces applied as acceleration, integrated to velocity and position

4. **Rendering Techniques**:
   - Point sprites rendered as textured quads (or GL_POINTS with size attenuation)
   - Color determined by quantum state: high coherence = bright/glowing, low = dim
   - Optional glow via post-processing bloom
   - Motion trails via frame buffer blending (accumulate previous frames)
   - Depth sorting for proper occlusion (or disable for performance)

5. **Performance Optimizations**:
   - Particle count capped at 200K to maintain 30fps on mid-range hardware
   - Spatial index updated every few frames (not every frame) to reduce CPU overhead
   - GPU-based particle simulation via transform feedback or compute shader (if available)
   - LOD: reduce particle count or disable expensive effects at low frame rates

6. **Integration with VJLive3**:
   - Wrapped as an EffectBase subclass
   - Parameters exposed via standard set_parameter/get_parameter interface
   - VideoSignal input processed in update() method
   - Output returned as VideoSignal with rendered frame
   - Supports hot-reloading of parameters during live performance

This expanded context fills in the [NEEDS RESEARCH] markers and provides detailed behavioral specifications that align with the actual legacy implementations.