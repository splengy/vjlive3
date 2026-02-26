# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT136_quantum_entanglement_point_cloud.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT136 — quantum_entanglement_point_cloud

## Description

The Quantum Entanglement Point Cloud module creates a sophisticated consciousness matrix visualization that transforms video input into living, breathing quantum point clouds with extensive parameter control. Based on the legacy implementation, this effect combines quantum physics simulation, consciousness modeling, hyperspace transformations, fractal generation, and reality distortion fields to produce complex, evolving visual patterns.

The effect operates through multiple interconnected systems: quantum wave functions that simulate superposition and entanglement, neural network patterns that model consciousness and thought processes, hyperspace transformations that manipulate dimensional properties, fractal algorithms that generate infinite complexity, and reality distortion fields that create spacetime effects. Each particle in the point cloud represents a quantum state that evolves through these multiple computational layers, creating emergent behaviors that appear conscious and responsive.

The module processes video frames through a sophisticated GLSL shader that applies 32+ parameters across six major categories: Quantum Physics, Consciousness, Hyperspace, Fractal Generation, Reality Distortion, and Audio Reactivity. The effect maintains visual correlation with the original video while transforming it into an abstract representation of quantum consciousness, with particles that exhibit behaviors like tunneling, entanglement, neural firing, and dimensional shifts. The result is a mesmerizing, ever-changing visualization that responds to both video content and extensive parameter controls, making it suitable for complex live performances and artistic installations.

## What This Module Does

- **Transforms 2D video into 3D point clouds** using depth extraction from video luminance and maps pixel brightness to particle density and distribution
- **Simulates quantum phenomena** including superposition, entanglement, decoherence, tunneling, quantum foam, and quantum interference through mathematical wave functions
- **Models consciousness and neural networks** simulating neural firing patterns, thought processes, memory formation, emotional states, and cognitive load
- **Applies hyperspace transformations** including dimensional shifts, wormhole effects, time dilation, and parallel universe influences
- **Generates fractal patterns** using Mandelbrot/Julia sets with configurable depth, zoom, rotation, symmetry, and distortion parameters
- **Creates reality distortion effects** including gravity wells, space warping, reality collapse, quantum foam, and event horizons
- **Processes audio reactivity** with separate controls for bass, treble, mid-range, overtones, rhythm sensitivity, harmony, and dissonance response
- **Supports 32+ elaborate parameters** across six major categories for maximum creative expression and fine-tuned control
- **Implements preset system** with five built-in configurations (Custom, Quantum Dream, Neural Network, Hyperspace, Reality Collapse)
- **Provides GPU-accelerated rendering** through sophisticated GLSL shaders with real-time uniform parameter updates
- **Outputs processed video frames** with quantum entanglement effects while maintaining temporal coherence

## What This Module Does NOT Do

- Implement actual quantum computing or quantum physics simulation (uses mathematical approximations and sine wave functions for visual effect)
- Process raw audio signals directly (audio data must be pre-analyzed and passed as parameters)
- Perform true 3D rendering with hardware-accelerated depth buffers or volumetric effects
- Handle networked quantum state synchronization between multiple instances
- Provide scientific accuracy for quantum mechanics research or education
- Support arbitrary 3D model import or custom particle geometries
- Implement machine learning-based quantum state prediction or adaptive algorithms
- Process video files longer than real-time performance constraints due to shader complexity
- Generate true fractals with infinite detail (uses iterative approximation with fixed depth limits)
- Create actual wormholes or dimensional rifts (uses mathematical transformations for visual effect)

## Detailed Behavior

### Parameter Mapping and Ranges

All parameters use a normalized 0.0-10.0 range that maps to specific technical values across six major categories:

**Quantum Physics Parameters:**
- `quantum_state` (0-10) → 0.0 to 1.0 baseline quantum superposition intensity
- `entanglement_strength` (0-10) → 0.0 to 1.0 correlation strength between entangled particles
- `decoherence_rate` (0-10) → 0.0 to 1.0 rate of quantum state decay per second
- `tunnel_probability` (0-10) → 0.0 to 1.0 probability of quantum tunneling per frame
- `superposition_level` (0-10) → 0.0 to 1.0 degree of quantum superposition
- `entanglement_range` (0-10) → 0.0 to 1.0 entanglement connection range
- `quantum_foam` (0-10) → 0.0 to 1.0 quantum foam intensity
- `quantum_interference` (0-10) → 0.0 to 1.0 quantum interference strength

**Consciousness Parameters:**
- `consciousness_level` (0-10) → 0.0 to 1.0 overall consciousness level
- `neural_activity` (0-10) → 0.0 to 1.0 neural firing activity
- `thought_intensity` (0-10) → 0.0 to 1.0 thought intensity
- `memory_decay` (0-10) → 0.0 to 1.0 memory decay rate
- `emotional_state` (0-10) → 0.0 to 1.0 emotional state
- `cognitive_load` (0-10) → 0.0 to 1.0 cognitive load
- `awareness_level` (0-10) → 0.0 to 1.0 awareness level
- `perception_intensity` (0-10) → 0.0 to 1.0 perception intensity

**Hyperspace Parameters:**
- `hyperspace_dimension` (0-10) → 3.0 to 11.0 hyperspace dimension (3D to 11D)
- `wormhole_strength` (0-10) → 0.0 to 1.0 wormhole connection strength
- `dimensional_shift` (0-10) → -1.0 to 1.0 dimensional shift
- `time_dilation` (0-10) → 0.1 to 10.0 time dilation factor
- `parallel_universes` (0-10) → 0.0 to 1.0 parallel universe influence
- `hyperspace_warp` (0-10) → 0.0 to 1.0 hyperspace warp intensity
- `quantum_tunnel` (0-10) → 0.0 to 1.0 quantum tunnel strength
- `dimensional_folding` (0-10) → 0.0 to 1.0 dimensional folding

**Fractal Parameters:**
- `fractal_type` (0-10) → 0.0 to 3.0 fractal type (0=Mandelbrot, 1=Julia, 2=Newton, 3=Custom)
- `fractal_depth` (0-10) → 1.0 to 100.0 fractal iteration depth
- `fractal_zoom` (0-10) → 0.1 to 100.0 fractal zoom level
- `fractal_rotation` (0-10) → -3.14 to 3.14 fractal rotation
- `fractal_offset` (0-10) → -1.0 to 1.0 fractal offset
- `fractal_symmetry` (0-10) → 0.0 to 1.0 fractal symmetry
- `fractal_noise` (0-10) → 0.0 to 1.0 fractal noise intensity
- `fractal_distortion` (0-10) → 0.0 to 1.0 fractal distortion

**Reality Distortion Parameters:**
- `gravity_well` (0-10) → -1.0 to 1.0 gravity well strength
- `space_warp` (0-10) → -1.0 to 1.0 space warp intensity
- `reality_collapse` (0-10) → 0.0 to 1.0 reality collapse
- `quantum_foam` (0-10) → 0.0 to 1.0 quantum foam
- `event_horizon` (0-10) → 0.0 to 1.0 event horizon
- `reality_shift` (0-10) → -1.0 to 1.0 reality shift
- `dimensional_rift` (0-10) → 0.0 to 1.0 dimensional rift
- `reality_fracture` (0-10) → 0.0 to 1.0 reality fracture

**Audio Reactivity Parameters:**
- `audio_influence` (0-10) → 0.0 to 1.0 audio influence
- `bass_response` (0-10) → 0.0 to 1.0 bass response
- `treble_response` (0-10) → 0.0 to 1.0 treble response
- `mid_response` (0-10) → 0.0 to 1.0 mid response
- `overtone_response` (0-10) → 0.0 to 1.0 overtone response
- `rhythm_sensitivity` (0-10) → 0.0 to 1.0 rhythm sensitivity
- `harmony_response` (0-10) → 0.0 to 1.0 harmony response
- `dissonance_response` (0-10) → 0.0 to 1.0 dissonance response

**Point Cloud Parameters:**
- `point_size` (0-10) → 1.0 to 10.0 point size in pixels
- `point_density` (0-10) → 0.01 to 1.0 point density
- `glow_intensity` (0-10) → 0.0 to 1.0 glow intensity
- `motion_blur` (0-10) → 0.0 to 1.0 motion blur
- `depth_fog` (0-10) → 0.0 to 1.0 depth fog
- `adaptive_quality` (0-10) → 0.0 to 1.0 adaptive quality
- `mesh_generation` (0-10) → 0.0 to 1.0 real-time mesh generation
- `particle_lifetime` (0-10) → 1.0 to 10.0 particle lifetime in seconds

**Preset System:**
- `preset` (0-10) → 0 to 4 preset selection (0=Custom, 1=Quantum Dream, 2=Neural Network, 3=Hyperspace, 4=Reality Collapse)

### Rendering Pipeline

1. **GLSL Shader Processing**: The effect uses a sophisticated GLSL fragment shader (`QUANTUM_ENTANGLEMENT_FRAGMENT`) that processes video frames through multiple computational layers:

2. **Quantum Wave Function**: Applies quantum-inspired mathematics using sine wave functions to simulate:
   - Superposition: `sin(time * 0.1 + position.x * 0.5) * 0.5 + 0.5`
   - Entanglement: `sin(time * 0.2 + position.y * 0.3) * 0.5 + 0.5`
   - Tunneling: `sin(time * 0.3 + position.z * 0.2) * 0.5 + 0.5`
   - Quantum interference: `sin(time * 0.4 + position.x * 0.1 + position.y * 0.1) * 0.5 + 0.5`
   - Quantum foam: `sin(time * 0.5 + position.x * 0.05 + position.y * 0.05) * 0.5 + 0.5`

3. **Consciousness Neural Network**: Simulates neural activity through mathematical patterns:
   - Neural firing patterns based on position and time
   - Thought pattern generation
   - Memory formation with decay
   - Emotional state modeling
   - Cognitive load simulation

4. **Hyperspace Transformations**: Applies dimensional effects:
   - Dimensional shift calculations
   - Wormhole strength effects
   - Time dilation factors
   - Parallel universe influences

5. **Fractal Generation**: Implements iterative fractal algorithms:
   - Mandelbrot/Julia set calculations with configurable depth
   - Fractal rotation and zoom
   - Symmetry and noise application
   - Distortion effects

6. **Reality Distortion**: Creates spacetime effects:
   - Gravity well calculations
   - Space warp transformations
   - Reality collapse simulation
   - Event horizon effects

7. **Audio Reactivity**: Processes audio data through parameter mapping:
   - Bass, treble, and mid-range response
   - Overtone and rhythm sensitivity
   - Harmony and dissonance analysis

8. **Final Compositing**: Combines all effects into final output:
   - Color mixing based on multiple intensity factors
   - Glow intensity application
   - Depth fog calculations
   - Motion blur effects
   - Alpha blending with original video

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

- **Input**: Video frames and optional depth frames via standard VJLive3 frame ingestion pipeline, passed as `signal_in` VideoSignal and optional `depth_frame` for enhanced depth extraction
- **Output**: Processed video frames with quantum entanglement effects, maintaining original dimensions and aspect ratio
- **Audio Input**: Optional pre-analyzed audio data passed as dictionary with bass, treble, mid, overtone, rhythm, harmony, and dissonance values
- **Parameter Control**: All 32+ parameters exposed as dictionary keys that can be dynamically updated via `set_parameter(name, value)` method at runtime, with immediate effect on next frame
- **Preset System**: Built-in preset selection via `preset` parameter (0-4) with five comprehensive configurations
- **Dependency Relationships**:
  - Inherits from `vjlive3.effects.base.BaseNode` for common effect infrastructure
  - Uses `vjlive3.core.signal.VideoSignal` for video stream handling
  - Requires GLSL shader support through `vjlive3.effects.shader_base.Effect` wrapper
  - Optional audio integration through `vjlive3.audio.analyzer` for real-time audio analysis
- **Node Graph Position**: Typically placed after video source nodes (camera, video player) and audio analysis nodes, before output/compositing nodes
- **Frame Format**: Expects RGBA textures; depth extracted from luminance using `depth = 0.299*R + 0.587*G + 0.114*B` formula
- **GPU Resources**: Requires OpenGL 3.3+ with GLSL 330 core support for sophisticated fragment shader processing
- **Shader Architecture**: Uses single comprehensive fragment shader with multiple uniform blocks for different effect categories
- **State Management**: Maintains internal state for time progression, audio data, and parameter values across frames

### Performance Characteristics

- **GPU-bound**: Primary cost is GLSL shader compilation and execution; performance scales with screen resolution and shader complexity
- **Shader complexity**: The single comprehensive fragment shader processes multiple mathematical functions per pixel, making it computationally intensive
- **Memory footprint**:
  - Shader uniforms: ~200+ float parameters (32+ categories × ~6-8 parameters each)
  - Frame buffers: Multiple render targets for depth, color, and intermediate effects
  - Texture memory: Input video texture, depth texture, potential glow textures
  - Total GPU memory: ~50-100 MB for full effect with high resolution
- **Expected frame rates** (reference hardware: GTX 1060, 1080p):
  - Low complexity (minimal parameters): 45-60 fps
  - Medium complexity (moderate parameters): 30-45 fps
  - High complexity (all parameters maxed): 15-25 fps
  - With fractal depth 100: 10-20 fps
- **CPU overhead**: Minimal CPU usage; most computation handled by GPU shader
- **Shader compilation time**: Initial shader compilation may take 100-500ms depending on GPU driver
- **Optimization opportunities**:
  - Reduce fractal iteration depth for better performance
  - Lower parameter counts to reduce uniform overhead
  - Use lower resolution for intermediate computations
  - Implement shader LOD based on performance targets
  - Cache compiled shaders to avoid recompilation

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

- **Shader base import failure**: If `shader_base` module unavailable, raise `ImportError` with fallback to basic processing without advanced effects
- **GPU shader compilation failure**: Raise `ShaderCompilationError` with detailed GLSL compilation log; check GLSL version support and uniform variable limits
- **Uniform parameter overflow**: If total uniforms exceed GPU limits (typically >256), raise `UniformLimitError` and suggest reducing parameter count
- **Invalid video dimensions**: If input video has zero or invalid dimensions, raise `ValueError` with specific dimension information
- **Audio data format mismatch**: If audio data dictionary is missing required keys (bass, treble, mid, etc.), raise `KeyError` with missing field list
- **Parameter type validation**: `TypeError` when non-numeric values passed to numeric parameters; `ValueError` for values outside [0.0, 10.0] range
- **Preset index out of bounds**: If `preset` parameter value outside 0-4 range, raise `ValueError` with valid range information
- **Memory allocation failure**: If GPU memory insufficient for frame buffers, raise `MemoryError` with available memory information
- **Shader uniform binding failure**: If uniform variable names don't match shader, raise `UniformBindingError` with mismatched list
- **Time progression overflow**: If internal time counter overflows after extended runtime, reset to zero and log warning
- **Fractal iteration limit**: If fractal calculations exceed iteration depth, clamp result and log performance warning

### Configuration Schema (Pydantic-style)

```python
class QuantumEntanglementPointCloudConfig:
    # Quantum Physics parameters
    quantum_state: float = Field(0.5, ge=0.0, le=10.0, description="Baseline quantum superposition intensity")
    entanglement_strength: float = Field(0.7, ge=0.0, le=10.0, description="Correlation strength between entangled particles")
    decoherence_rate: float = Field(0.1, ge=0.0, le=10.0, description="Rate of quantum state decay per second")
    tunnel_probability: float = Field(0.3, ge=0.0, le=10.0, description="Probability of quantum tunneling per frame")
    superposition_level: float = Field(0.6, ge=0.0, le=10.0, description="Degree of quantum superposition")
    entanglement_range: float = Field(0.5, ge=0.0, le=10.0, description="Entanglement connection range")
    quantum_foam: float = Field(0.2, ge=0.0, le=10.0, description="Quantum foam intensity")
    quantum_interference: float = Field(0.4, ge=0.0, le=10.0, description="Quantum interference strength")

    # Consciousness parameters
    consciousness_level: float = Field(0.5, ge=0.0, le=10.0, description="Overall consciousness level")
    neural_activity: float = Field(0.7, ge=0.0, le=10.0, description="Neural firing activity")
    thought_intensity: float = Field(0.3, ge=0.0, le=10.0, description="Thought intensity")
    memory_decay: float = Field(0.1, ge=0.0, le=10.0, description="Memory decay rate")
    emotional_state: float = Field(0.4, ge=0.0, le=10.0, description="Emotional state")
    cognitive_load: float = Field(0.5, ge=0.0, le=10.0, description="Cognitive load")
    awareness_level: float = Field(0.6, ge=0.0, le=10.0, description="Awareness level")
    perception_intensity: float = Field(0.3, ge=0.0, le=10.0, description="Perception intensity")

    # Hyperspace parameters
    hyperspace_dimension: float = Field(5.0, ge=3.0, le=11.0, description="Hyperspace dimension (3D to 11D)")
    wormhole_strength: float = Field(0.2, ge=0.0, le=10.0, description="Wormhole connection strength")
    dimensional_shift: float = Field(0.3, ge=-1.0, le=1.0, description="Dimensional shift")
    time_dilation: float = Field(2.0, ge=0.1, le=10.0, description="Time dilation factor")
    parallel_universes: float = Field(0.1, ge=0.0, le=10.0, description="Parallel universe influence")
    hyperspace_warp: float = Field(0.4, ge=0.0, le=10.0, description="Hyperspace warp intensity")
    quantum_tunnel: float = Field(0.2, ge=0.0, le=10.0, description="Quantum tunnel strength")
    dimensional_folding: float = Field(0.3, ge=0.0, le=10.0, description="Dimensional folding")

    # Fractal parameters
    fractal_type: float = Field(1.0, ge=0.0, le=3.0, description="Fractal type (0=Mandelbrot, 1=Julia, 2=Newton, 3=Custom)")
    fractal_depth: float = Field(50.0, ge=1.0, le=100.0, description="Fractal iteration depth")
    fractal_zoom: float = Field(2.0, ge=0.1, le=100.0, description="Fractal zoom level")
    fractal_rotation: float = Field(0.0, ge=-3.14, le=3.14, description="Fractal rotation")
    fractal_offset: float = Field(0.0, ge=-1.0, le=1.0, description="Fractal offset")
    fractal_symmetry: float = Field(0.5, ge=0.0, le=10.0, description="Fractal symmetry")
    fractal_noise: float = Field(0.3, ge=0.0, le=10.0, description="Fractal noise intensity")
    fractal_distortion: float = Field(0.2, ge=0.0, le=10.0, description="Fractal distortion")

    # Reality distortion parameters
    gravity_well: float = Field(0.0, ge=-1.0, le=1.0, description="Gravity well strength")
    space_warp: float = Field(0.0, ge=-1.0, le=1.0, description="Space warp intensity")
    reality_collapse: float = Field(0.0, ge=0.0, le=10.0, description="Reality collapse")
    quantum_foam_rd: float = Field(0.0, ge=0.0, le=10.0, description="Quantum foam (reality distortion)")
    event_horizon: float = Field(0.0, ge=0.0, le=10.0, description="Event horizon")
    reality_shift: float = Field(0.0, ge=-1.0, le=1.0, description="Reality shift")
    dimensional_rift: float = Field(0.0, ge=0.0, le=10.0, description="Dimensional rift")
    reality_fracture: float = Field(0.0, ge=0.0, le=10.0, description="Reality fracture")

    # Audio reactivity parameters
    audio_influence: float = Field(0.5, ge=0.0, le=10.0, description="Audio influence")
    bass_response: float = Field(0.7, ge=0.0, le=10.0, description="Bass response")
    treble_response: float = Field(0.3, ge=0.0, le=10.0, description="Treble response")
    mid_response: float = Field(0.4, ge=0.0, le=10.0, description="Mid response")
    overtone_response: float = Field(0.2, ge=0.0, le=10.0, description="Overtone response")
    rhythm_sensitivity: float = Field(0.6, ge=0.0, le=10.0, description="Rhythm sensitivity")
    harmony_response: float = Field(0.3, ge=0.0, le=10.0, description="Harmony response")
    dissonance_response: float = Field(0.1, ge=0.0, le=10.0, description="Dissonance response")

    # Point cloud parameters
    point_size: float = Field(2.0, ge=1.0, le=10.0, description="Point size in pixels")
    point_density: float = Field(0.1, ge=0.01, le=1.0, description="Point density")
    glow_intensity: float = Field(0.3, ge=0.0, le=10.0, description="Glow intensity")
    motion_blur: float = Field(0.1, ge=0.0, le=10.0, description="Motion blur")
    depth_fog: float = Field(0.2, ge=0.0, le=10.0, description="Depth fog")
    adaptive_quality: float = Field(1.0, ge=0.0, le=10.0, description="Adaptive quality")
    mesh_generation: float = Field(0.0, ge=0.0, le=10.0, description="Real-time mesh generation")
    particle_lifetime: float = Field(5.0, ge=1.0, le=10.0, description="Particle lifetime in seconds")

    # Preset system
    preset: int = Field(0, ge=0, le=4, description="Preset selection (0=Custom, 1=Quantum Dream, 2=Neural Network, 3=Hyperspace, 4=Reality Collapse)")
```

### Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_shader_base_import` | Module handles missing `shader_base` gracefully with fallback processing |
| `test_basic_operation` | Given uniform color frame, output shows correctly rendered quantum effects with expected density |
| `test_parameter_validation` | All 32+ parameters validated for type and range; invalid inputs raise appropriate exceptions |
| `test_quantum_wave_functions` | Sine-based quantum calculations produce expected superposition, entanglement, tunneling effects |
| `test_consciousness_simulation` | Neural network patterns generate expected thought, memory, emotional, and cognitive effects |
| `test_hyperspace_transformations` | Dimensional shifts, wormholes, time dilation, and parallel universe effects work correctly |
| `test_fractal_generation` | Mandelbrot/Julia sets with configurable depth, zoom, rotation, symmetry, and distortion |
| `test_reality_distortion` | Gravity wells, space warping, reality collapse, and event horizon effects function properly |
| `test_audio_reactivity` | Bass, treble, mid, overtone, rhythm, harmony, and dissonance responses affect visual output |
| `test_preset_system` | Five built-in presets (Custom, Quantum Dream, Neural Network, Hyperspace, Reality Collapse) apply correctly |
| `test_shader_compilation` | GLSL fragment shader compiles successfully with all uniform variables properly bound |
| `test_uniform_limit_handling` | System gracefully handles uniform variable limits without crashing |
| `test_memory_allocation` | GPU memory allocated correctly for frame buffers and textures; proper cleanup on shutdown |
| `test_time_progression` | Internal time counter advances correctly and handles overflow gracefully |
| `test_depth_extraction` | Luminance-based depth extraction using `0.299*R + 0.587*G + 0.114*B` formula |
| `test_parameter_immediate_effect` | Dynamic parameter updates via `set_parameter()` affect next frame immediately |
| `test_audio_data_format` | Optional audio data dictionary with required keys (bass, treble, mid, etc.) processed correctly |
| `test_error_recovery` | Various error conditions handled gracefully with appropriate exceptions and fallbacks |
| `test_performance_scaling` | Frame rate scales appropriately with shader complexity and resolution |
| `test_edge_case_parameters` | Extreme values (0, 10) and boundary conditions handled without crashes or artifacts |
| `test_legacy_compatibility` | Output matches reference legacy implementation for equivalent parameter configurations |
| `test_fractal_iteration_limits` | Fractal calculations respect iteration depth limits and performance constraints |

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