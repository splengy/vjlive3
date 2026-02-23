# P3-VD29: Depth Camera Splitter Effect

## What This Module Does

Implements `DepthCameraSplitterEffect` — a depth-aware camera splitter effect that divides the visual output into multiple segments based on depth information. This effect creates a multi-layered visual experience where different depth ranges are processed independently, allowing for creative depth-based compositing and spatial manipulation.

## Public Interface

```python
class DepthCameraSplitterEffect(Effect):
    METADATA = {
        "name": "Depth Camera Splitter",
        "description": "Split visual output by depth ranges for layered compositing",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "split_count",
                "type": "int",
                "min": 2,
                "max": 8,
                "default": 3,
                "description": "Number of depth-based segments to create"
            },
            {
                "name": "depth_ranges",
                "type": "list",
                "min_items": 2,
                "max_items": 8,
                "default": [0.0, 0.3, 0.7, 1.0],
                "description": "Depth range boundaries for segmentation"
            },
            {
                "name": "segment_processing",
                "type": "dict",
                "default": {
                    "0": {"effect": "identity", "params": {}},
                    "1": {"effect": "invert", "params": {}},
                    "2": {"effect": "color_shift", "params": {"shift_amount": 0.1}},
                    "3": {"effect": "glitch", "params": {"intensity": 0.3}}
                },
                "description": "Processing rules for each depth segment"
            },
            {
                "name": "transition_smoothness",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "Smoothness of transitions between depth segments"
            },
            {
                "name": "depth_offset",
                "type": "float",
                "min": -0.5,
                "max": 0.5,
                "default": 0.0,
                "description": "Offset applied to depth values for fine-tuning segmentation"
            },
            {
                "name": "output_mode",
                "type": "enum",
                "options": ["stack", "side_by_side", "picture_in_picture", "custom"],
                "default": "stack",
                "description": "How segments are composited together"
            }
        ],
        "metadata": {
            "tags": ["depth", "splitter", "compositing", "layering"],
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
- Modified frame with depth-based segmentation applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT modify the input frame in-place (creates copy)
- Does NOT require exact depth range boundaries (handles overlapping ranges gracefully)
- Does NOT process audio data directly (but can modulate parameters via audio_data)
- Does NOT handle 3D geometry transformations (pure 2D compositing)
- Does NOT include motion tracking (uses static depth frames)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_segmentation.py`: Verify depth ranges correctly partition the frame
- `test_processing_rules.py`: Validate segment processing logic
- `test_transition_smoothness.py`: Test smooth transitions between segments
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and DepthSource
- `test_compositing.py`: Verify output modes work correctly
- `test_performance.py`: Benchmark processing time, ensure <20ms at 1080p

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges

## Implementation Notes

### Legacy References
- `vjlive/vdepth/depth_camera_splitter.py` — Original implementation
- `VJlive-2/plugins/p3_vd29.py` — Existing port (if present)

### Key Algorithms
1. **Depth Range Partitioning**: Divide frame into segments based on depth boundaries
2. **Segment Processing**: Apply different effects to each depth segment
3. **Compositing**: Combine segments according to output mode
4. **Transition Smoothing**: Apply smooth interpolation between adjacent segments

### Performance Targets
- 1080p @ 60fps: <20ms per frame
- Memory: <30 MB additional (segment buffers)
- GPU: Optional compute shader acceleration

### Safety Rails
- **RAIL 1**: Must maintain 60fps target
- **RAIL 6**: Handle missing depth source gracefully (fallback to uniform processing)
- **RAIL 8**: No GPU memory leaks in texture allocation

## Deliverables

1. `src/vjlive3/plugins/p3_vd29.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd29.py` — Comprehensive test suite
3. `docs/plugins/p3_vd29.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] Depth ranges correctly partition the visual output
- [x] Segment processing rules work as expected
- [x] Output modes function correctly (stack, side_by_side, etc.)
- [x] ≥80% test coverage across implementation
- [x] Performance: <20ms per 1080p frame (50+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns