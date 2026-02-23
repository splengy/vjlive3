# P3-VD31: Depth Contour Datamosh Effect

## What This Module Does

Implements `DepthContourDatamoshEffect` — a depth-aware datamosh effect that creates contour-based glitch patterns following depth edges and boundaries. This effect analyzes depth contours to generate targeted datamosh artifacts that trace object boundaries and depth transitions, creating organic, flowing glitch patterns that respond to the geometry of the scene.

## Public Interface

```python
class DepthContourDatamoshEffect(Effect):
    METADATA = {
        "name": "Depth Contour Datamosh",
        "description": "Contour-following datamosh with depth edge detection",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "contour_threshold",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "Edge detection sensitivity for contour identification"
            },
            {
                "name": "glitch_length",
                "type": "int",
                "min": 1,
                "max": 100,
                "default": 15,
                "description": "Maximum length of glitch displacement vectors"
            },
            {
                "name": "glitch_direction",
                "type": "enum",
                "options": ["normal", "tangent", "radial", "random"],
                "default": "tangent",
                "description": "Direction of glitch displacement relative to contour"
            },
            {
                "name": "color_swap_intensity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.3,
                "description": "Intensity of color channel swapping during datamosh"
            },
            {
                "name": "depth_sensitivity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.9,
                "description": "How strongly depth contours affect the effect"
            },
            {
                "name": "audio_sync",
                "type": "bool",
                "default": true,
                "description": "Enable audio-reactive parameter modulation"
            }
        ],
        "metadata": {
            "tags": ["datamosh", "contour", "depth", "edge", "organic"],
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
- Modified frame with contour-following datamosh applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT perform full edge detection (uses simplified depth-based approach)
- Does NOT include motion tracking (uses static depth frames)
- Does NOT handle 3D geometry transformations (pure 2D effect)
- Does NOT modify alpha channel (preserves transparency)
- Does NOT require exact contour detection (approximates contours from depth)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_contour_detection.py`: Verify depth contour extraction accuracy
- `test_glitch_generation.py`: Test displacement vector creation and application
- `test_audio_sync.py`: Audio-reactive parameter modulation
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and DepthSource
- `test_performance.py`: Benchmark processing time, ensure <18ms at 1080p

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges

## Implementation Notes

### Legacy References
- `vjlive/vdepth/depth_contour_datamosh.py` — Original implementation
- `VJlive-2/plugins/p3_vd31.py` — Existing port (if present)

### Key Algorithms
1. **Contour Extraction**: Use depth gradient magnitude to identify edges
2. **Displacement Vector Generation**: Create glitch patterns following contour directions
3. **Color Channel Swapping**: Apply selective color channel shifts during displacement
4. **Audio Reactivity**: Modulate glitch intensity and direction based on audio features

### Performance Targets
- 1080p @ 60fps: <18ms per frame
- Memory: <25 MB additional (contour buffer)
- CPU: Optimized using NumPy vectorization and sparse processing

### Safety Rails
- **RAIL 1**: Must maintain 60fps target
- **RAIL 6**: Handle missing depth source gracefully (fallback to uniform glitch)
- **RAIL 8**: No GPU memory leaks in texture allocation

## Deliverables

1. `src/vjlive3/plugins/p3_vd31.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd31.py` — Comprehensive test suite
3. `docs/plugins/p3_vd31.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] Depth contours correctly drive glitch patterns
- [x] Audio reactivity works (beat triggers glitch intensity)
- [x] ≥80% test coverage across implementation
- [x] Performance: <18ms per 1080p frame (55+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns