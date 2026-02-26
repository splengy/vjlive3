# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT003_particles_3d.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT003 — particles_3d (AdvancedParticle3DSystem)

## Description

This module implements an advanced 3D particle system inspired by TouchDesigner, designed to generate and simulate thousands of particles in real-time with physics-based behavior. It supports GPU instancing for high-performance rendering, audio reactivity, force fields (attractors, vortexes), and dynamic visual properties such as color, size, and life span. The module produces a stream of 3D particle data that can be rendered via OpenGL shaders and is fully configurable through runtime parameters.

## What This Module Does

- Generates and simulates up to 10,000 particles in real-time using CPU-side physics
- Supports GPU instancing for efficient rendering of large particle counts
- Implements physics-based behavior including gravity, drag, and turbulence
- Provides audio reactivity that modulates particle properties based on audio features
- Supports multiple force fields (attractors, vortexes) for dynamic particle manipulation
- Handles particle lifecycle including birth, aging, and death with configurable lifespans
- Offers configurable visual properties including color gradients, size transitions, and blend modes
- Provides camera control for 3D viewing and perspective management
- Supports texture mapping for enhanced visual effects
- Implements multiple render modes (points, textured, lines, mesh)

## What This Module Does NOT Do

- Handle file I/O or persistence of particle configurations
- Manage scene graph or other 3D objects beyond particles
- Provide collision detection between particles or with other objects
- Implement physics beyond basic particle dynamics (no rigid body physics)
- Handle network synchronization of particle states
- Provide particle physics on GPU (currently CPU-side simulation)
- Manage audio input directly (relies on external audio analyzer)

## Integration

This module integrates with the VJLive3 node graph as a visual effect generator. It connects to:

- **Audio Analyzer**: Receives audio features (bass, mid, treble, beat) for reactivity
- **Shader Base**: Uses OpenGL shaders for rendering and visual effects
- **Node Graph**: Outputs particle data as a renderable effect that can be composited with other visual elements using standard blending operations
- **Camera System**: Integrates with 3D camera controls for perspective and view management
- **Texture System**: Can use external textures for particle appearance

The module expects to be called within the main render loop and provides its output as a standard effect that can be combined with other visual elements using standard blending operations.

## Performance

- **Particle Count**: Supports up to 10,000 particles (configurable, default 2,000)
- **CPU Usage**: Physics simulation runs on CPU, optimized with numpy arrays
- **GPU Usage**: Rendering uses VBOs and VAOs for efficient GPU instancing
- **Memory**: ~50-100MB for particle data arrays (depends on particle count)
- **Frame Rate**: Target 60fps with 2,000 particles on mid-range hardware
- **Audio Processing**: Minimal overhead, processes audio features once per frame
- **Scalability**: Performance scales linearly with particle count
- **Fallback**: Can operate in simulation-only mode without rendering if OpenGL unavailable

---

## Public Interface

```python
class AdvancedParticle3DSystem:
    def __init__(self) -> None: ...
    def update(self, dt: float) -> None: ...
    def set_emitter_position(self, x: float, y: float, z: float) -> None: ...
    def set_particle_life_range(self, min_life: float, max_life: float) -> None: ...
    def add_force_field_attractor(self, pos: Tuple[float, float, float], strength: float) -> None: ...
    def set_camera_position(self, x: float, y: float, z: float) -> None: ...
    def set_turbulence_params(self, strength: float, scale: float, speed: float) -> None: ...
    def enable_audio_reactivity(self, sensitivity: float, beat_multiplier: float, spectrum_influence: float) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `dt` | `float` | Time delta in seconds for physics update | Must be ≥ 0.0; typically 1/60 or 1/120 |
| `x`, `y`, `z` | `float` | Coordinates for emitter or camera position | Range: [-10.0, 10.0] (normalized screen space) |
| `min_life`, `max_life` | `float` | Minimum and maximum particle lifetime in seconds | Must be > 0; min ≤ max |
| `strength` | `float` | Strength of force field influence | Range: [0.0, 10.0] |
| `sensitivity`, `beat_multiplier`, `spectrum_influence` | `float` | Audio reactivity parameters | Sensitivity ∈ [0.0, 5.0]; beat_multiplier ∈ [1.0, 3.0]; spectrum_influence ∈ [0.0, 1.0] |
| `turbulence_strength`, `scale`, `speed` | `float` | Parameters for turbulence force field | All ≥ 0.0; scale ∈ [0.1, 5.0], speed ∈ [0.0, 2.0] |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for particle array operations — fallback: manual list-based arrays (slower)
  - `OpenGL.GL` — required for rendering and shader binding — fallback: no rendering (only simulation)
- Internal modules this depends on:
  - `vjlive3.core.effects.shader_base` — for shader loading and rendering setup
  - `vjlive3.core.audio_analyzer.AudioAnalyzer` — to extract audio features for reactivity
  - `vjlive3.core.audio_reactor.AudioReactor` — to apply audio-based force modulation

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing if hardware (e.g. GPU) is unavailable |
| `test_basic_operation` | Core update loop advances particles correctly with gravity and drag |
| `test_force_fields` | Attractor and vortex forces modify particle trajectories as expected |
| `test_audio_reactivity` | Audio input modulates particle emission rate and size based on spectrum and beat |
| `test_turbulence_params` | Turbulence strength, scale, and speed affect motion patterns realistically |
| `test_particle_lifecycle` | Particles are born with correct life span and die at end of life |
| `test_camera_updates` | Camera position changes correctly affect view and particle visibility |
| `test_output_bounds` | All particle positions remain within expected bounds (e.g., [-10, 10]) |
| `test_max_particles` | System handles maximum particle count without crashing |
| `test_audio_edge_cases` | Handles silent audio and extreme audio levels gracefully |
| `test_memory_management` | Proper cleanup of particle arrays and GPU resources |
| `test_shader_compilation` | Vertex and fragment shaders compile correctly |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-X] P3-EXT003: particles_3d module implementation` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

## LEGACY CODE REFERENCES

See vjlive1/core/generators/particles_3d.py for full reference:

- **L17–36**: Class definition and core attributes including `max_particles`, `num_particles`, `enabled`, `initialized`
- **L33–52**: Physics parameters (`gravity`, `drag`, `turbulence_strength/scale/speed`), emitter settings (`emit_rate`, `emit_position`, `emit_radius`, `emit_velocity`, `emit_spread`)
- **L49–68**: Visual properties (`color_start/end`, `blend_mode`, `point_size`) and audio reactivity parameters (`audio_sensitivity`, `beat_multiplier`, `spectrum_influence`)
- **L65–84**: Force fields (`attractor_pos/strength`, `vortex_strength/axis`), camera setup (`camera_position`, `target`, `up`, `fov`), and particle data arrays (`pos`, `vel`, `life`, `props`) with structured layout

### Audio Reactivity Integration

Audio reactivity is integrated into the physics loop through the following mechanism:

1. Audio features (bass, mid, treble, beat) are extracted once per frame by the AudioAnalyzer
2. These features are passed to the particle system via uniform variables in the vertex shader
3. Audio displacement is applied to particle positions: `pos.y += audio_bass * 0.1 * sin(pos.x * 5.0 + time)`
4. Particle size is modulated by audio features: `size = props.y * (1.0 + audio_mid * 0.5)`
5. Audio beat influences emission rate and particle birth timing

### GPU Instancing and VBO Updates

The current implementation uses CPU-side arrays for physics simulation but leverages GPU instancing for rendering:

- Particle positions, velocities, and properties are stored in numpy arrays on CPU
- VBOs (Vertex Buffer Objects) are used to transfer data to GPU efficiently
- VAOs (Vertex Array Objects) manage the vertex attribute layout
- The system uses `gl_PointSize` for perspective scaling and particle sizing
- Texture mapping is supported through optional texture binding

### Camera Frustum Culling

Camera frustum culling is not explicitly implemented in the legacy code. The system relies on:

- Standard OpenGL perspective projection
- Particle visibility based on camera position and field of view
- No explicit culling of particles outside the view frustum
- Particles are rendered based on their 3D positions relative to the camera

### Particle Death and Rebirth

Particle lifecycle management includes:

- Particles are born with random life spans between `particle_life_min` and `particle_life_max`
- Each frame, particle life is decremented by `dt`
- When life ≤ 0, particles are marked for rebirth
- New particles are emitted at the emitter position with random spread
- Audio triggers can influence emission rate and particle properties

### Force Field Interactions

Force fields interact dynamically during runtime using additive force application:

- Attractors apply force: `F = strength * (attractor_pos - particle_pos) / distance`
- Vortexes apply rotational force around the vortex axis
- Forces are accumulated per-particle and applied to velocity
- Turbulence is applied as a global velocity perturbation
- All forces are combined additively before velocity integration

### Turbulence Application

Turbulence is applied per-particle using procedural noise:

- Turbulence strength, scale, and speed parameters control the effect
- Perlin or simplex noise is used for natural-looking motion
- Turbulence is applied as a velocity offset each frame
- The effect creates organic, fluid-like particle motion

### Memory Management

Memory management for large particle arrays includes:

- Pre-allocated numpy arrays for positions, velocities, and properties
- Efficient memory usage through typed arrays (float32)
- VBO management for GPU-side data
- Proper cleanup in destructor or release methods
- Fallback to CPU-only operation if GPU memory is constrained

### Shader Structure

The shader input/output structure maps to the `props` array as follows:

- `props.x`: life (normalized 0-1 for shader calculations)
- `props.y`: size (base particle size)
- `props.z`: rotation (particle rotation angle)
- `props.w`: unused (reserved for future use)

Vertex shader inputs:
- `position`: particle 3D position
- `color`: particle RGBA color
- `props`: particle properties array

Uniform variables:
- `mvp_matrix`: Model-View-Projection matrix for camera transformation
- `time`: Current time for animation and audio synchronization
- `audio_*`: Audio feature uniforms for reactivity
- `use_texture`: Flag for texture mapping
- `render_mode`: Render mode selection

Fragment shader outputs:
- `fragColor`: Final particle color with alpha blending

### Audio Feature Mapping

Audio features are extracted and mapped to particle properties:

- **Bass**: Influences vertical displacement and particle birth rate
- **Mid**: Modulates particle size and color intensity
- **Treble**: Affects particle velocity and rotation speed
- **Beat**: Triggers particle bursts and modulates emission rate
- Features are normalized to [0, 1] range for consistent behavior
- Audio sensitivity parameters allow user control over reactivity strength
