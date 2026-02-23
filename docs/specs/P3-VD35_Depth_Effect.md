# P3-VD35: Depth Effect Plugin

## What This Module Does

Implements `DepthEffectPlugin` — a versatile depth-based effect that provides foundational depth manipulation capabilities. This effect serves as a base for various depth processing operations, offering essential depth transformations and filtering that can be combined with other effects.

## Public Interface

```python
class DepthEffectPlugin(Effect):
    METADATA = {
        "name": "Depth Effect",
        "description": "Core depth manipulation and filtering foundation",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "depth_operation",
                "type": "enum",
                "options": ["invert", "scale", "offset", "clamp", "normalize", "smooth"],
                "default": "normalize",
                "description": "Primary depth transformation operation"
            },
            {
                "name": "operation_params",
                "type": "dict",
                "default": {
                    "scale": 1.0,
                    "offset": 0.0,
                    "clamp_min": 0.0,
                    "clamp_max": 1.0,
                    "smoothness": 0.5
                },
                "description": "Parameters for the selected depth operation"
            },
            {
                "name": "depth_multiplier",
                "type": "float",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
                "description": "Global multiplier applied to depth values"
            },
            {
                "name": "depth_offset",
                "type": "float",
                "min": -1.0,
                "max": 1.0,
                "default": 0.0,
                "description": "Global offset added to depth values"
            },
            {
                "name": "smoothing",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
                "description": "Depth smoothing filter strength"
            },
            {
                "name": "depth_sensitivity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 1.0,
                "description": "Overall depth influence on effect"
            },
            {
                "name": "audio_sync",
                "type": "bool",
                "default": true,
                "description": "Enable audio-reactive depth modulation"
            }
        ],
        "metadata": {
            "tags": ["depth", "manipulation", "filter", "foundation"],
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
- Modified frame with depth effect applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT create depth information (requires existing depth buffer)
- Does NOT perform 3D geometry transformations
- Does NOT modify alpha channel (preserves transparency)
- Does NOT require exact depth values (handles missing depth gracefully)
- Does NOT include advanced depth reconstruction (simple operations only)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_depth_operations.py`: Test all depth transformation operations
- `test_parameter_combinations.py`: Verify operation_params work correctly
- `test_audio_sync.py`: Audio-reactive depth modulation
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and DepthSource
- `test_performance.py`: Benchmark processing time, ensure <3ms at 1080p

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges

## Implementation Notes

### Legacy References
- `vjlive/vdepth/depth_effect.py` — Original implementation
- `VJlive-2/plugins/p3_vd35.py` — Existing port (if present)

### Key Algorithms
1. **Depth Operations**: Implement various depth transformations (invert, scale, offset, clamp, normalize, smooth)
2. **Audio Reactivity**: Modulate depth parameters based on audio features
3. **Smoothing Filter**: Apply Gaussian or bilateral filter to depth buffer
4. **Parameter Validation**: Ensure depth values stay within valid ranges

### Performance Targets
- 1080p @ 60fps: <3ms per frame
- Memory: <5 MB additional (depth buffer operations)
- CPU: Highly optimized using NumPy vectorization

### Safety Rails
- **RAIL 1**: Must maintain 60fps target
- **RAIL 6**: Handle missing depth source gracefully (fallback to no effect)
- **RAIL 8**: No GPU memory leaks in texture allocation

## Deliverables

1. `src/vjlive3/plugins/p3_vd35.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd35.py` — Comprehensive test suite
3. `docs/plugins/p3_vd35.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] All depth operations work correctly (invert, scale, offset, clamp, normalize, smooth)
- [x] Audio reactivity works (beat triggers depth modulation)
- [x] ≥80% test coverage across implementation
- [x] Performance: <3ms per 1080p frame (333+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns