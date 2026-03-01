# P3-EXT412: Particles3D Core (Emitter, Force, Render Modes)

## Task: P3-EXT412 — Particles3D Core

**Phase:** Phase 3 / P3-EXT412
**Assigned To:** Desktop Roo Worker
**Spec Written By:** Desktop Roo Worker
**Date:** 2026-03-01

---

## What This Module Does

The `AdvancedParticle3DSystem` core engine replicates TouchDesigner-level capabilities for massive, GPU-accelerated 3D audio-reactive particle swarms. It provides a complete particle simulation framework with up to 100,000 particles simultaneously, supporting multiple emitter types, force fields, and render modes. The system processes audio-frequency data in real-time to create dynamic, music-reactive visual effects with procedural noise field mathematics and OpenGL memory mapping for optimal performance.

## What It Does NOT Do

- Handle file I/O or persistent storage operations
- Process audio streams directly (relies on external AudioAnalyzer)
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary 3D model loading or mesh processing
- Handle network streaming or distributed particle systems

---

## Public Interface

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable
import numpy as np
from OpenGL.GL import *

class ParticleState(Enum):
    EMITTED = "emitted"      # Newly created particle
    ALIVE = "alive"          # Active particle in simulation
    DYING = "dying"          # Particle in fade-out phase
    DEAD = "dead"            # Inactive particle ready for reuse

class EmitterType(Enum):
    POINT = "point"          # Single point emission
    LINE = "line"            # Linear emission along axis
    CIRCLE = "circle"        # Circular planar emission
    SPHERE = "sphere"        # Spherical volumetric emission
    BOX = "box"              # Cuboid volumetric emission
    GRID = "grid"            # Structured grid emission

class ForceType(Enum):
    GRAVITY = "gravity"      # Constant downward acceleration
    WIND = "wind"            # Directional force field
    MAGNETIC = "magnetic"    # Cross-product curved trajectories
    NOISE = "noise"          # Perlin/simplex procedural noise
    ATTRACTOR = "attractor"  # Point-based attraction
    REPELLER = "repeller"    # Point-based repulsion
    VORTEX = "vortex"        # Rotational force field

class RenderMode(Enum):
    POINTS = "points"        # Individual point rendering
    BILLBOARDS = "billboards" # Camera-facing quads
    RIBBONS = "ribbons"      # Connected line segments
    TRAILS = "trails"        # Particle history visualization
    LINES = "lines"          # Line connections between particles

@dataclass
class Particle:
    position: np.ndarray      # 3D position vector (x, y, z)
    velocity: np.ndarray      # 3D velocity vector (vx, vy, vz)
    acceleration: np.ndarray  # 3D acceleration vector (ax, ay, az)
    color: np.ndarray         # RGBA color (r, g, b, a)
    size: float              # Particle size in world units
    lifetime: float          # Time since birth in seconds
    max_lifetime: float      # Maximum lifetime before death
    state: ParticleState     # Current particle state
    age: float              # Normalized age (0.0 to 1.0)

@dataclass
class Emitter:
    emitter_type: EmitterType
    position: np.ndarray
    direction: np.ndarray
    spread: float
    rate: float              # Particles per second
    burst_count: int
    burst_rate: float
    radius: float
    dimensions: Tuple[float, float, float]
    grid_size: Tuple[int, int, int]
    color: np.ndarray
    size_range: Tuple[float, float]
    lifetime_range: Tuple[float, float]
    velocity_range: Tuple[float, float, float]
    audio_reactive: bool
    frequency_band: int      # Audio frequency band index
    sensitivity: float

@dataclass
class Force:
    force_type: ForceType
    position: np.ndarray
    direction: np.ndarray
    strength: float
    falloff: float
    noise_scale: float
    noise_speed: float
    radius: float
    noise_offset: np.ndarray

class AdvancedParticle3DSystem:
    def __init__(
        self,
        max_particles: int = 100000,
        particle_size: float = 0.1,
        max_lifetime: float = 5.0,
        gravity: Tuple[float, float, float] = (0.0, -9.81, 0.0),
        wind: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        audio_analyzer: Optional[Callable] = None,
        use_gpu: bool = True
    ) -> None: ...
    
    def add_emitter(self, emitter: Emitter) -> int: ...
    def remove_emitter(self, emitter_id: int) -> bool: ...
    def add_force(self, force: Force) -> int: ...
    def remove_force(self, force_id: int) -> bool: ...
    
    def update(self, dt: float, audio_data: Optional[np.ndarray] = None) -> None: ...
    def render(self, camera_matrix: np.ndarray) -> None: ...
    
    def set_render_mode(self, mode: RenderMode) -> None: ...
    def set_particle_size(self, size: float) -> None: ...
    def set_max_particles(self, count: int) -> None: ...
    def clear(self) -> None: ...
    
    def get_particle_count(self) -> int: ...
    def get_alive_count(self) -> int: ...
    def get_performance_stats(self) -> dict: ...

class ParticleBuffer:
    def __init__(self, capacity: int) -> None: ...
    def update_particles(self, particles: List[Particle]) -> None: ...
    def bind(self) -> None: ...
    def unbind(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `dt` | `float` | Delta time in seconds since last update | Must be positive, typically 0.016 (60fps) |
| `audio_data` | `np.ndarray` | Audio frequency spectrum data | Shape: (bands, frames), values 0.0-1.0 |
| `camera_matrix` | `np.ndarray` | View-projection matrix for rendering | 4x4 transformation matrix |
| `max_particles` | `int` | Maximum particle capacity | 1 to 1,000,000, default 100,000 |
| `particle_size` | `float` | Base particle size in world units | 0.01 to 10.0, default 0.1 |
| `render_mode` | `RenderMode` | Current rendering mode | One of enum values |

---

## Edge Cases and Error Handling

- **Hardware missing**: If OpenGL context unavailable, system falls back to CPU-based rendering with reduced quality
- **Bad input**: Invalid parameters raise ValueError with descriptive messages
- **Memory limits**: If particle count exceeds GPU memory, system automatically reduces max_particles and logs warning
- **Audio data missing**: If audio_analyzer returns None, system continues with default particle behavior
- **Zero division**: All division operations include epsilon checks to prevent NaN propagation
- **Cleanup path**: System provides explicit cleanup() method that releases all GPU buffers and memory

---

## Dependencies

- **External Libraries**:
  - `numpy` — array operations and particle physics calculations — fallback: pure Python math
  - `PyOpenGL` — GPU buffer management and rendering — fallback: software rendering
  - `pyopencl` — optional GPU acceleration for force calculations — fallback: CPU
- **Internal Dependencies**:
  - `vjlive3.core.audio.AudioAnalyzer` — audio frequency data processing
  - `vjlive3.core.effects.shader_base` — fundamental shader operations
  - `vjlive3.plugins.vcore.particle_effect.py` — legacy implementation reference

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | System initializes without OpenGL context and falls back to CPU rendering |
| `test_basic_emission` | Emitter creates particles with correct initial properties |
| `test_force_application` | Force fields correctly modify particle trajectories |
| `test_audio_reactivity` | Audio data properly influences particle birth rates and properties |
| `test_particle_lifetime` | Particles transition through EMITTED→ALIVE→DYING→DEAD states correctly |
| `test_render_modes` | All RenderMode values produce valid OpenGL output |
| `test_performance_limits` | System maintains 60fps with 100k particles under load |
| `test_memory_management` | ParticleBuffer correctly manages GPU memory allocation |
| `test_boundary_conditions` | Particles properly handle world boundaries and collisions |
| `test_cleanup` | cleanup() method releases all resources without leaks |

**Minimum coverage:** 85% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed and approved by Manager
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Performance benchmarks meet 60fps target
- [ ] Memory usage stays under 512MB for 100k particles
- [ ] Git commit with `[Phase-3] P3-EXT412: Particles3D Core - complete particle system`
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 3, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## Mathematical Specifications

### Particle Physics
```python
# Position update using Euler integration
new_position = position + velocity * dt + 0.5 * acceleration * dt**2
new_velocity = velocity + acceleration * dt

# Force application (per particle)
acceleration = sum(forces) / mass

# Noise field using simplex noise
noise_value = simplex_noise(
    position * noise_scale + time * noise_speed + noise_offset
)
```

### Emitter Mathematics
```python
# Spherical emission coordinates
phi = np.random.uniform(0, np.pi)
theta = np.random.uniform(0, 2 * np.pi)
radius = np.random.uniform(0, emitter.radius)

x = radius * np.sin(phi) * np.cos(theta)
y = radius * np.sin(phi) * np.sin(theta)
z = radius * np.cos(phi)

# Grid emission
x = (i / grid_size[0] - 0.5) * dimensions[0]
y = (j / grid_size[1] - 0.5) * dimensions[1]
z = (k / grid_size[2] - 0.5) * dimensions[2]
```

### Force Field Calculations
```python
# Magnetic force using cross product
force = np.cross(force_direction, to_force_point) * strength

# Vortex force (rotational)
radius_vec = position - vortex_center
tangent = np.cross(up_vector, radius_vec)
force = tangent * strength / (np.linalg.norm(radius_vec) + 1e-6)

# Noise force with falloff
distance = np.linalg.norm(position - force.position)
falloff_factor = 1.0 / (1.0 + (distance / force.falloff)**2)
```

### Billboard Mathematics
```python
# Vertex shader for camera-facing quads
vec3 right = normalize(cross(camera_dir, vec3(0.0, 1.0, 0.0)))
vec3 up = cross(right, camera_dir)

vec3 vertex = position + right * (offset.x * size) + up * (offset.y * size)
```

---

## Performance Constraints

- **Update loop**: Must complete in ≤ 4ms for 100k particles (250Hz target)
- **Render loop**: Must complete in ≤ 6ms for 100k particles (166Hz target)
- **Memory usage**: ≤ 512MB total for particle data and buffers
- **GPU bandwidth**: ≤ 500MB/s for particle buffer updates
- **CPU usage**: ≤ 30% on quad-core system during full load

---

## Memory Layout

```python
# Particle buffer structure (GPU)
struct ParticleBuffer {
    vec3 position;      // 12 bytes
    vec3 velocity;      // 12 bytes
    vec3 acceleration;  // 12 bytes  
    vec4 color;         // 16 bytes
    float size;         // 4 bytes
    float lifetime;     // 4 bytes
    uint state;         // 4 bytes
    uint age;           // 4 bytes
    // Total: 80 bytes per particle
    // 100k particles = 8MB
};

# Index buffer for alive particles
struct AliveIndexBuffer {
    uint index;         // 4 bytes
    // 100k particles = 0.4MB
};
```

---

## Legacy Code References

### VJLive-2 Implementation Analysis

The legacy `VJlive-2/core/effects/particles_3d.py` uses a master `_update_particles` physics loop with the following characteristics:

1. **NumPy Array Processing**: All particle properties stored in parallel arrays for cache efficiency
2. **Zero-Allocation Physics**: Uses masked array operations to avoid memory allocation during updates
3. **Alive Masking**: `alive_mask = lifetimes > 0` creates boolean mask for active particles
4. **Compaction**: `positions[:alive_count] = positions[alive_mask]` maintains contiguous memory
5. **Direct OpenGL**: Uses `glBufferSubData` for immediate GPU buffer updates

### Key Algorithm Preservation

The new implementation must preserve:
- Masked array operations for alive particle filtering
- In-place array updates to avoid allocation
- Direct OpenGL buffer updates for performance
- Audio-reactive birth rate modulation using FFT frequency data

---

## Integration Notes

The `AdvancedParticle3DSystem` integrates with the VJLive3 node graph through:

- **Input Pipeline**: Receives `dt` from main render loop, audio data from AudioAnalyzer, and camera matrices from CameraManager
- **Output Pipeline**: Writes to OpenGL particle buffers, triggers render calls, and provides performance metrics
- **Parameter Control**: All parameters can be dynamically updated via setter methods
- **Dependency Relationships**: Connects to shader_base for fundamental rendering operations and audio_analyzer for music reactivity

---

## Safety Rails and Constraints

- **Maximum Particle Limit**: Hard cap at 1,000,000 particles to prevent memory exhaustion
- **Frame Rate Guarantee**: System monitors frame time and automatically reduces particle count if ≥ 16.7ms
- **Audio Data Validation**: All audio inputs validated to be within [0.0, 1.0] range
- **GPU Memory Check**: System queries available VRAM before allocating large buffers
- **Thread Safety**: All public methods are thread-safe for use in multi-threaded rendering pipelines

---

## Future Extensions

- **GPU Compute Shaders**: Optional OpenCL/CUDA acceleration for force calculations
- **Spatial Partitioning**: Octree or grid-based optimization for large particle counts
- **Particle Instancing**: Advanced rendering techniques for extreme particle counts
- **Network Distribution**: Multi-machine particle system for massive simulations
- **Physics Integration**: Rigid body dynamics and collision detection

---

## Implementation Priority

1. **Core Physics Engine** (P0): Basic particle simulation with Euler integration
2. **Emitter System** (P1): Multiple emitter types with audio reactivity
3. **Force Fields** (P2): Complete force system with noise and procedural effects
4. **Rendering Pipeline** (P3): OpenGL rendering with all RenderMode options
5. **Performance Optimization** (P4): GPU acceleration and memory management
6. **Advanced Features** (P5): Trail systems, ribbons, and complex interactions

---

## Verification Checklist

- [ ] All mathematical formulas verified against physical principles
- [ ] Performance targets validated through profiling
- [ ] Memory usage stays within specified limits
- [ ] Audio reactivity produces musically meaningful results
- [ ] All edge cases handled gracefully
- [ ] Integration with existing VJLive3 architecture confirmed
- [ ] Documentation complete and accurate
- [ ] Test coverage meets minimum requirements

---

## Notes for Implementation Team

- **Start Simple**: Begin with basic particle physics and add features incrementally
- **Profile Early**: Use profiling tools from the start to identify bottlenecks
- **Test on Target Hardware**: Validate performance on actual target systems
- **Document Assumptions**: Clearly document all assumptions about hardware capabilities
- **Maintain Compatibility**: Ensure backward compatibility with existing VJLive3 interfaces
- **Error Recovery**: Implement robust error handling and recovery mechanisms
- **Version Control**: Use feature branches and comprehensive commit messages

---

## Conclusion

The `AdvancedParticle3DSystem` provides a complete, high-performance particle simulation framework that meets the requirements of modern VJ applications. By combining efficient CPU-based physics with GPU-accelerated rendering, it achieves the performance targets necessary for real-time audio-reactive visual effects while maintaining the flexibility and control required by professional users.