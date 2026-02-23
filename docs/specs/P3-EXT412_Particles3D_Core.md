# P3-EXT412: Particles3D Core (Emitter, Force, Render Modes)

## Description

The `AdvancedParticle3DSystem` core engine, replicating TouchDesigner-level capabilities for massive, GPU-accelerated 3D audio-reactive particle swarms.

## What This Module Does

This specification defines the foundational data types and physics loop for the `AdvancedParticle3DSystem` ported from `VJlive-2/core/effects/particles_3d.py`. It explicitly answers and defines several P3-EXT dependencies including `P3-EXT264` (EmitterType), `P3-EXT271` (ForceType), `RenderMode`, and `ParticleState`. The system handles up to 100k particles simultaneously via raw OpenGL memory mapping, audio-frequency reaction, and procedural noise field mathematics.

## Public Interface

```python
class ParticleState(Enum):
    EMITTED = "emitted"
    ALIVE = "alive"
    DYING = "dying"
    DEAD = "dead"

class EmitterType(Enum):
    POINT = "point"
    LINE = "line"
    CIRCLE = "circle"
    SPHERE = "sphere"
    BOX = "box"
    GRID = "grid"

class ForceType(Enum):
    GRAVITY = "gravity"
    WIND = "wind"
    MAGNETIC = "magnetic"
    NOISE = "noise"
    ATTRACTOR = "attractor"
    REPELLER = "repeller"
    VORTEX = "vortex"

class RenderMode(Enum):
    POINTS = "points"
    BILLBOARDS = "billboards"
    RIBBONS = "ribbons"
    TRAILS = "trails"
    LINES = "lines"
```

## Inputs and Outputs

*   **Inputs**: `dt` (Delta time), AudioAnalyzer frequencies, Camera projections.
*   **Outputs**: Fully transformed OpenGL Uniform/Buffer Objects pushing thousands of coordinates into the `v_velocity`, `v_size`, and `v_color` shader pathways.

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `core/effects/particles_3d.py`
- **Architectural Soul**: A master `_update_particles` physics loop iterating NumPy arrays: applying `ForceType` attributes (like `NOISE` math involving `pos[x] * scale + time * speed`), resolving boundary conditions, pruning `DEAD` `ParticleState` entities via alive-masking, and executing vertex buffering directly into PyOpenGL via `glBufferSubData`. 

### Key Algorithms
1. **Emitter Logic**: `EmitterType.SPHERE` calculates random spherical coordinate emission `radius * np.sin(phi) * np.cos(theta)`, utilizing `emit_burst` attributes or `audio_peak` energy detection to modify birth rates on-the-fly.
2. **Force Fields**: `ForceType.MAGNETIC` applies `np.cross(force_direction, to_force)` to curve particle pathways.
3. **Advanced Rendering**: `RenderMode.BILLBOARDS` calculates cross products inside the GLSL Vertex shader: `normalize(cross(camera_dir, vec3(0.0, 1.0, 0.0)))` to guarantee 2D texture quads infinitely face the viewport despite 3D traversal.

### Optimization Constraints & Safety Rails
- **Zero-Allocation Physics**: The legacy NumPy compactor correctly performs masked shifting (`self.positions[:alive_count] = self.positions[alive_mask]`) keeping memory strictly bounded to pre-allocated buffers. This paradigm MUST remain.
- **Node Wiring limitations**: Running 100k point iterations inside pure Python (even NumPy) introduces GIL constraints during the `_apply_forces` routine at dense resolutions.

## Test Plan

*   **Logic (Pytest)**: Validate that the Enum structures initialize properties inside the `ParticleEmitter` and `ParticleForce` dataclasses flawlessly.
*   **Performance Constraints**: Profile the Numpy alive compaction `alive_mask = self.lifetimes > 0`; loop times strictly cannot exceed 4ms for 50,000 points.

## Deliverables

1.  Implemented Enums mapped into `src/vjlive3/plugins/ml/particles/types.py`.
2.  Core Particle Engine implementation inside `src/vjlive3/plugins/advanced_particles_3d.py`.
