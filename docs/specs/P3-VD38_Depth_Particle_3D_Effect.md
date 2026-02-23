# P3-VD38: Depth Particle 3D Effect

## What This Module Does

Implements `DepthParticle3DEffect` — a depth-based particle system that creates 3D particle simulations driven by depth information. This effect transforms depth buffers into dynamic particle systems where particles are positioned, sized, and colored based on depth data, enabling sophisticated 3D particle visualizations that respond to scene depth.

## Public Interface

```python
class DepthParticle3DEffect(Effect):
    METADATA = {
        "name": "Depth Particle 3D",
        "description": "Depth-driven 3D particle system visualization",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "particle_count",
                "type": "int",
                "min": 100,
                "max": 10000,
                "default": 5000,
                "description": "Number of particles to generate"
            },
            {
                "name": "particle_size",
                "type": "float",
                "min": 1.0,
                "max": 10.0,
                "default": 2.0,
                "description": "Base size of particles in pixels"
            },
            {
                "name": "size_curve",
                "type": "dict",
                "default": {
                    "near": 1.0,
                    "far": 0.2
                },
                "description": "Size scaling based on depth proximity"
            },
            {
                "name": "color_scheme",
                "type": "enum",
                "options": ["depth_gradient", "random", "uniform", "audio_sync"],
                "default": "depth_gradient",
                "description": "Color assignment strategy for particles"
            },
            {
                "name": "depth_color_palette",
                "type": "dict",
                "default": {
                    "min": [0.0, 0.0, 1.0],
                    "max": [1.0, 1.0, 0.0]
                },
                "description": "Color mapping from depth min to max"
            },
            {
                "name": "motion_type",
                "type": "enum",
                "options": ["static", "orbit", "pulse", "flow", "attract", "repel"],
                "default": "static",
                "description": "Particle motion pattern"
            },
            {
                "name": "motion_intensity",
                "type": "float",
                "min": 0.0,
                "max": 2.0,
                "default": 0.5,
                "description": "Intensity of particle motion"
            },
            {
                "name": "lifetime",
                "type": "float",
                "min": 0.1,
                "max": 5.0,
                "default": 2.0,
                "description": "Particle lifetime in seconds"
            },
            {
                "name": "depth_sensitivity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.9,
                "description": "How strongly depth affects particle behavior"
            },
            {
                "name": "audio_sync",
                "type": "bool",
                "default": true,
                "description": "Enable audio-reactive particle modulation"
            }
        ],
        "metadata": {
            "tags": ["particle", "3d", "depth", "visualization", "system"],
            "category": "effect",
            "complexity": "high",
            "performance_impact": "medium"
        }
    }

    def __init__(self, params: dict):
        """Initialize with parameter dictionary."""
        pass

    def process(self, frame: np.ndarray, depth: np.ndarray, audio_data: dict) -> np.ndarray:
        """Process frame with depth and audio data, return modified frame."""
        pass
```

## Inputs and Outputs

**Inputs:**
- `frame`: RGB/RGBA numpy array (HxWxC), dtype=uint8 or float32
- `depth`: Depth buffer numpy array (HxW), dtype=float32, normalized 0-1
- `audio_data`: Dictionary containing:
  - `fft`: FFT spectrum array (2048 bins)
  - `waveform`: Time-domain waveform array
  - `beat`: Boolean indicating beat detection
  - `bass`, `mid`, `treble`: Frequency band energies (0-1)

**Outputs:**
- Modified frame with particle system rendered, same shape and dtype as input

## What It Does NOT Do

- Does NOT create true 3D geometry (projects particles to 2D screen space)
- Does NOT include depth-based occlusion (particles always render on top)
- Does NOT handle perspective-correct rendering (uses simple projection)
- Does NOT include advanced particle physics (uses simplified dynamics)
- Does NOT modify alpha channel (preserves transparency)
- Does NOT require exact depth values (handles missing depth gracefully)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_particle_generation.py`: Verify particle count and positioning accuracy
- `test_color_assignment.py`: Test depth-based and audio-sync color schemes
- `test_motion_simulation.py`: Verify motion patterns work correctly
- `test_lifetime_management.py`: Test particle birth/death cycles
- `test_audio_sync.py`: Audio-reactive particle behavior
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and DepthSource
- `test_performance.py`: Benchmark processing time, ensure <20ms at 1080p

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges

## Implementation Notes

### Legacy References
- `vjlive/vdepth/depth_particle_3d.py` — Original implementation
- `VJlive-2/plugins/p3_vd38.py` — Existing port (if present)

### Key Algorithms
1. **Particle Generation**: Create particles based on depth values and count parameters
2. **Positioning**: Map depth values to 3D coordinates with projection
3. **Color Assignment**: Apply color schemes based on depth or audio features
4. **Motion Simulation**: Implement motion patterns (orbit, pulse, flow, attract, repel)
5. **Lifetime Management**: Handle particle birth and death cycles

### Performance Targets
- 1080p @ 60fps: <20ms per frame
- Memory: <30 MB additional (particle buffer storage)
- CPU: Optimized using NumPy vectorization and sparse processing

### Safety Rails
- **RAIL 1**: Must maintain 60fps target
- **RAIL 6**: Handle missing depth source gracefully (fallback to static particles)
- **RAIL 8**: No GPU memory leaks in texture allocation

## Deliverables

1. `src/vjlive3/plugins/p3_vd38.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd38.py` — Comprehensive test suite
3. `docs/plugins/p3_vd38.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] Particle generation accurately reflects depth information
- [x] Color schemes work correctly (depth_gradient, random, uniform, audio_sync)
- [x] Motion patterns function as expected (static, orbit, pulse, flow, attract, repel)
- [x] Audio reactivity works (beat triggers particle behavior changes)
- [x] ≥80% test coverage across implementation
- [x] Performance: <20ms per 1080p frame (50+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns