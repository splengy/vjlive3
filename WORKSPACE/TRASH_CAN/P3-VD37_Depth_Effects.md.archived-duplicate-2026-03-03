# P3-VD37: Depth Effects (DepthPointCloudEffect)

## What This Module Does

Implements `DepthPointCloudEffect` — a depth-based point cloud manipulation effect that creates 3D point cloud visualizations from depth data. This effect transforms depth buffers into point cloud representations with optional colorization, enabling sophisticated 3D visualizations that respond to depth information.

## Public Interface

```python
class DepthPointCloudEffect(Effect):
    METADATA = {
        "name": "Depth Point Cloud",
        "description": "Convert depth buffer to 3D point cloud visualizations",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "point_size",
                "type": "float",
                "min": 1.0,
                "max": 10.0,
                "default": 2.0,
                "description": "Size of rendered points in pixels"
            },
            {
                "name": "point_color",
                "type": "dict",
                "default": {
                    "r": 1.0,
                    "g": 1.0,
                    "b": 1.0,
                    "a": 1.0
                },
                "description": "Base color for all points"
            },
            {
                "name": "color_by_depth",
                "type": "bool",
                "default": true,
                "description": "Color points based on depth values"
            },
            {
                "name": "depth_palette",
                "type": "dict",
                "default": {
                    "min": [0.0, 0.0, 0.0],
                    "max": [1.0, 0.0, 0.0]
                },
                "description": "Color mapping from depth min to max"
            },
            {
                "name": "point_spread",
                "type": "float",
                "min": 0.0,
                "max": 5.0,
                "default": 0.5,
                "description": "Random spread applied to point positions"
            },
            {
                "name": "density_scale",
                "type": "float",
                "min": 0.1,
                "max": 5.0,
                "default": 1.0,
                "description": "Density multiplier for point generation"
            },
            {
                "name": "depth_sensitivity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.9,
                "description": "How strongly depth affects point cloud generation"
            },
            {
                "name": "audio_sync",
                "type": "bool",
                "default": true,
                "description": "Enable audio-reactive point cloud modulation"
            }
        ],
        "metadata": {
            "tags": ["point", "cloud", "depth", "3d", "visualization"],
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
- Modified frame with point cloud visualization applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT create true 3D geometry (projects 2D points to screen space)
- Does NOT include perspective-correct rendering (uses simple projection)
- Does NOT handle point occlusion (points always render on top)
- Does NOT include advanced shading (uses simple point sprites)
- Does NOT modify alpha channel (preserves transparency)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_point_generation.py`: Verify point cloud generation accuracy
- `test_color_mapping.py`: Test depth-based colorization
- `test_audio_sync.py`: Audio-reactive point size modulation
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and DepthSource
- `test_performance.py`: Benchmark processing time, ensure <15ms at 1080p

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges

## Implementation Notes

### Legacy References
- `vjlive/vdepth/depth_point_cloud.py` — Original implementation
- `VJlive-2/plugins/p3_vd37.py` — Existing port (if present)

### Key Algorithms
1. **Point Cloud Generation**: Convert depth values to 3D points with projection
2. **Color Mapping**: Apply depth-based color gradients
3. **Point Sprites**: Render points as textured quads with spread
4. **Audio Reactivity**: Modulate point size/density based on audio features

### Performance Targets
- 1080p @ 60fps: <15ms per frame
- Memory: <25 MB additional (point buffer storage)
- CPU: Optimized using NumPy vectorization and sparse processing

### Safety Rails
- **RAIL 1**: Must maintain 60fps target
- **RAIL 6**: Handle missing depth source gracefully (fallback to no points)
- **RAIL 8**: No GPU memory leaks in texture allocation

## Deliverables

1. `src/vjlive3/plugins/p3_vd37.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd37.py` — Comprehensive test suite
3. `docs/plugins/p3_vd37.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] Point cloud generation accurately reflects depth information
- [x] Color mapping works correctly (depth-based or uniform)
- [x] Audio reactivity works (beat triggers point size/density changes)
- [x] ≥80% test coverage across implementation
- [x] Performance: <15ms per 1080p frame (66+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns