# P3-VD32: Depth Distance Filter Effect

## What This Module Does

Implements `DepthDistanceFilterEffect` — a depth-aware filter that applies intensity-based processing based on distance from the camera. This effect creates realistic depth-based attenuation, perspective distortion, and spatial filtering that simulates optical effects like atmospheric perspective and depth-based focus falloff.

## Public Interface

```python
class DepthDistanceFilterEffect(Effect):
    METADATA = {
        "name": "Depth Distance Filter",
        "description": "Distance-based filtering with atmospheric perspective",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "near_clip",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.1,
                "description": "Near clipping plane distance (0-1 normalized)"
            },
            {
                "name": "far_clip",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 1.0,
                "description": "Far clipping plane distance (0-1 normalized)"
            },
            {
                "name": "attenuation_curve",
                "type": "enum",
                "options": ["linear", "exponential", "inverse", "logarithmic", "custom"],
                "default": "exponential",
                "description": "Depth-to-intensity mapping function"
            },
            {
                "name": "color_tint",
                "type": "dict",
                "default": {
                    "r": 0.0,
                    "g": 0.0,
                    "b": 0.0,
                    "a": 0.0
                },
                "description": "Color tint applied based on distance"
            },
            {
                "name": "focus_distance",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "Distance where objects are in sharpest focus"
            },
            {
                "name": "focus_transition",
                "type": "float",
                "min": 0.0,
                "max": 0.5,
                "default": 0.1,
                "description": "Transition width around focus distance"
            },
            {
                "name": "depth_sensitivity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.8,
                "description": "How strongly depth affects the filtering"
            },
            {
                "name": "audio_sync",
                "type": "bool",
                "default": true,
                "description": "Enable audio-reactive parameter modulation"
            }
        ],
        "metadata": {
            "tags": ["distance", "filter", "attenuation", "perspective"],
            "category": "effect",
            "complexity": "low",
            "performance_impact": "very_low"
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
- Modified frame with distance-based filtering applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT perform full camera projection (simulates depth effects only)
- Does NOT include motion blur or temporal effects
- Does NOT handle 3D geometry transformations
- Does NOT modify alpha channel (preserves transparency)
- Does NOT require exact depth values (handles missing depth gracefully)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_attenuation.py`: Verify distance-to-intensity mapping accuracy
- `test_color_tint.py`: Test distance-based color application
- `test_focus_simulation.py`: Verify focus distance controls sharpness
- `test_audio_sync.py`: Audio-reactive parameter modulation
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and DepthSource
- `test_performance.py`: Benchmark processing time, ensure <5ms at 1080p

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges

## Implementation Notes

### Legacy References
- `vjlive/vdepth/depth_distance_filter.py` — Original implementation
- `VJlive-2/plugins/p3_vd32.py` — Existing port (if present)

### Key Algorithms
1. **Distance Mapping**: Convert depth values to normalized distance (0-1)
2. **Attenuation Curve**: Apply mathematical function to determine intensity
3. **Color Tinting**: Apply distance-based color shifts
4. **Focus Simulation**: Create sharpness gradient around focus distance

### Performance Targets
- 1080p @ 60fps: <5ms per frame
- Memory: <5 MB additional (minimal processing)
- CPU: Highly optimized using NumPy vectorization

### Safety Rails
- **RAIL 1**: Must maintain 60fps target
- **RAIL 6**: Handle missing depth source gracefully (fallback to uniform processing)
- **RAIL 8**: No GPU memory leaks in texture allocation

## Deliverables

1. `src/vjlive3/plugins/p3_vd32.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd32.py` — Comprehensive test suite
3. `docs/plugins/p3_vd32.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] Distance mapping correctly controls filtering intensity
- [x] Focus simulation creates realistic sharpness gradient
- [x] Audio reactivity works (beat triggers attenuation changes)
- [x] ≥80% test coverage across implementation
- [x] Performance: <5ms per 1080p frame (200+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns