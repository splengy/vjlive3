# P3-VD28: Depth Blur Effect

## What This Module Does

Implements `DepthBlurEffect` — a depth-aware blur effect that applies variable blur intensity based on depth information. This effect creates realistic depth-of-field effects where foreground elements remain sharp while background elements become progressively more blurred, simulating camera focus and depth perception.

## Public Interface

```python
class DepthBlurEffect(Effect):
    METADATA = {
        "name": "Depth Blur",
        "description": "Depth-aware variable blur with focus simulation",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "focus_distance",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "Distance from camera where objects remain sharp"
            },
            {
                "name": "blur_radius",
                "type": "float",
                "min": 0.0,
                "max": 10.0,
                "default": 2.0,
                "description": "Maximum blur radius at farthest depth"
            },
            {
                "name": "focus_width",
                "type": "float",
                "min": 0.0,
                "max": 0.5,
                "default": 0.1,
                "description": "Width of focus transition zone"
            },
            {
                "name": "bokeh_strength",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.3,
                "description": "Intensity of bokeh highlights in out-of-focus areas"
            },
            {
                "name": "depth_sensitivity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.8,
                "description": "How strongly depth affects blur intensity"
            },
            {
                "name": "horizontal_blur",
                "type": "bool",
                "default": true,
                "description": "Enable horizontal blur component"
            },
            {
                "name": "vertical_blur",
                "type": "bool",
                "default": true,
                "description": "Enable vertical blur component"
            }
        ],
        "metadata": {
            "tags": ["blur", "depth", "bokeh", "focus", "optics"],
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
- Modified frame with depth-aware blur applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT perform full 3D camera simulation (simulates depth-based blur only)
- Does NOT handle motion blur (only static depth-based blur)
- Does NOT include lens flare or chromatic aberration effects
- Does NOT modify alpha channel (preserves transparency)
- Does NOT require depth data to be non-zero (handles missing depth gracefully)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_processing.py`: Frame processing with synthetic depth patterns
- `test_focus_simulation.py`: Verify focus distance correctly controls blur
- `test_audio_reactivity.py`: Audio-driven focus distance modulation
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and DepthSource
- `test_performance.py`: Benchmark processing time, ensure <12ms at 1080p

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges

## Implementation Notes

### Legacy References
- `vjlive/vdepth/depth_blur.py` — Original implementation
- `VJlive-2/plugins/p3_vd28.py` — Existing port (if present)

### Key Algorithms
1. **Depth-Based Blur Calculation**: Compute blur radius based on depth distance from focus point
2. **Gaussian Blur Application**: Apply separable Gaussian blur with variable radius
3. **Bokeh Simulation**: Add circular highlights in out-of-focus areas
4. **Depth Sensitivity Mapping**: Modulate blur intensity based on depth gradient

### Performance Targets
- 1080p @ 60fps: <12ms per frame
- Memory: <20 MB additional (blur kernel cache)
- CPU: Optimized using NumPy vectorization and separable filters

### Safety Rails
- **RAIL 1**: Must maintain 60fps target
- **RAIL 6**: Handle missing depth source gracefully (fallback to uniform blur)
- **RAIL 8**: No GPU memory leaks in texture allocation

## Deliverables

1. `src/vjlive3/plugins/p3_vd28.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd28.py` — Comprehensive test suite
3. `docs/plugins/p3_vd28.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] Focus distance correctly controls blur intensity
- [x] Audio reactivity works (beat triggers focus shifts)
- [x] ≥80% test coverage across implementation
- [x] Performance: <12ms per 1080p frame (83+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns