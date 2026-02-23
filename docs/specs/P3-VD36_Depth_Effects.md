# P3-VD36: Depth Effects Plugin

## What This Module Does

Implements `DepthEffectPlugin` — a comprehensive depth effects processor that combines multiple depth manipulation techniques into a single versatile effect. This plugin provides a unified interface for applying various depth-based transformations, making it a workhorse for depth-based visual processing.

## Public Interface

```python
class DepthEffectPlugin(Effect):
    METADATA = {
        "name": "Depth Effects",
        "description": "Multi-function depth manipulation processor",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "effect_type",
                "type": "enum",
                "options": ["enhance", "suppress", "invert", "threshold", "smooth", "edge"],
                "default": "enhance",
                "description": "Primary depth effect to apply"
            },
            {
                "name": "strength",
                "type": "float",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
                "description": "Overall effect intensity"
            },
            {
                "name": "depth_range",
                "type": "dict",
                "default": {
                    "near": 0.0,
                    "far": 1.0
                },
                "description": "Depth range to which effect is applied"
            },
            {
                "name": "transition_smoothness",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "Smoothness of effect transition at range boundaries"
            },
            {
                "name": "contrast_boost",
                "type": "float",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
                "description": "Depth contrast enhancement"
            },
            {
                "name": "noise_reduction",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "Depth noise reduction strength"
            },
            {
                "name": "depth_sensitivity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 1.0,
                "description": "Overall depth influence"
            },
            {
                "name": "audio_sync",
                "type": "bool",
                "default": true,
                "description": "Enable audio-reactive depth modulation"
            }
        ],
        "metadata": {
            "tags": ["depth", "effects", "manipulation", "processor"],
            "category": "effect",
            "complexity": "medium",
            "performance_impact": "low"
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
- Modified frame with depth effects applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT create depth information (requires existing depth buffer)
- Does NOT perform 3D geometry transformations
- Does NOT modify alpha channel (preserves transparency)
- Does NOT require exact depth values (handles missing depth gracefully)
- Does NOT include advanced depth reconstruction (simple operations only)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_effect_types.py`: Test all effect_type options (enhance, suppress, invert, threshold, smooth, edge)
- `test_depth_range.py`: Verify depth range masking works correctly
- `test_parameter_combinations.py`: Test strength, contrast_boost, noise_reduction interactions
- `test_audio_sync.py`: Audio-reactive depth modulation
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and DepthSource
- `test_performance.py`: Benchmark processing time, ensure <8ms at 1080p

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges

## Implementation Notes

### Legacy References
- `vjlive/vdepth/depth_effects.py` — Original implementation
- `VJlive-2/plugins/p3_vd36.py` — Existing port (if present)

### Key Algorithms
1. **Depth Range Masking**: Apply effects only within specified depth range
2. **Effect Type Selection**: Implement multiple depth manipulation algorithms
3. **Contrast Enhancement**: Apply histogram equalization to depth buffer
4. **Noise Reduction**: Apply bilateral or median filter to reduce depth noise
5. **Audio Reactivity**: Modulate depth parameters based on audio features

### Performance Targets
- 1080p @ 60fps: <8ms per frame
- Memory: <10 MB additional (depth buffer operations)
- CPU: Optimized using NumPy vectorization

### Safety Rails
- **RAIL 1**: Must maintain 60fps target
- **RAIL 6**: Handle missing depth source gracefully (fallback to no effect)
- **RAIL 8**: No GPU memory leaks in texture allocation

## Deliverables

1. `src/vjlive3/plugins/p3_vd36.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd36.py` — Comprehensive test suite
3. `docs/plugins/p3_vd36.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] All effect types work correctly (enhance, suppress, invert, threshold, smooth, edge)
- [x] Depth range masking applies effects selectively
- [x] Audio reactivity works (beat triggers parameter changes)
- [x] ≥80% test coverage across implementation
- [x] Performance: <8ms per 1080p frame (125+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns