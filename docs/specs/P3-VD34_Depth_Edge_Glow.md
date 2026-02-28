# P3-VD34: Depth Edge Glow Effect

## What This Module Does

This module implements the `DepthEdgeGlowEffect`, ported from the legacy `VJlive-2/plugins/vdepth/depth_edge_glow.py` codebase. It acts as a depth-contour scanner, wrapping objects in luminous neon boundaries by performing hardware-accelerated, multi-scale Sobel edge detection on the raw 32-bit depth matrix. It combines high-frequency topological discontinuities with procedurally generated sub-depth slicing intervals, feeding the result through an integrated multi-tap bloom operator for a heavy Outrun/Synthwave visual aesthetic.

## Public Interface

```python
class DepthEdgeGlowEffect(Effect):
    METADATA = {
        "name": "Depth Edge Glow",
        "description": "Depth-based edge detection with neon glow highlighting",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "edge_threshold",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "Sensitivity of depth edge detection"
            },
            {
                "name": "glow_intensity",
                "type": "float",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
                "description": "Brightness of the edge glow"
            },
            {
                "name": "glow_radius",
                "type": "int",
                "min": 1,
                "max": 20,
                "default": 3,
                "description": "Blur radius for glow effect"
            },
            {
                "name": "glow_color",
                "type": "dict",
                "default": {
                    "r": 0.0,
                    "g": 1.0,
                    "b": 1.0,
                    "a": 1.0
                },
                "description": "RGBA color of the edge glow"
            },
            {
                "name": "edge_thickness",
                "type": "int",
                "min": 1,
                "max": 10,
                "default": 2,
                "description": "Thickness of detected edges"
            },
            {
                "name": "depth_sensitivity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.9,
                "description": "How strongly depth affects edge detection"
            },
            {
                "name": "audio_sync",
                "type": "bool",
                "default": true,
                "description": "Enable audio-reactive glow pulsing"
            }
        ],
        "metadata": {
            "tags": ["edge", "glow", "depth", "neon", "highlight"],
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
- Modified frame with depth edge glow applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT perform full Canny edge detection (uses simplified depth gradient)
- Does NOT include motion tracking (uses static depth frames)
- Does NOT modify alpha channel (preserves transparency)
- Does NOT require exact depth values (handles missing depth gracefully)
- Does NOT include chromatic aberration (pure glow effect)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_edge_detection.py`: Verify depth gradient edge detection accuracy
- `test_glow_application.py`: Test glow blur and color application
- `test_audio_sync.py`: Audio-reactive glow intensity modulation
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and DepthSource
- `test_performance.py`: Benchmark processing time, ensure <10ms at 1080p

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/depth_edge_glow.py`
- **Architectural Soul**: The legacy shader utilizes a custom `depth_edge_multi` macro that executes spatial Sobel operators across multiple dynamic radii (controlled by `edge_thickness`). It relies on a heavy O(N^2) Gaussian-approximate convolution loop taking up to 49 spatial taps for its integrated `glow_radius` bloom pass.

### Key Algorithms
1. **Multi-Scale Sobel**: A loop aggregating depth gradients `max(edge, depth_edge_multi(uv, s))` across progressive `s` pixel scales to ensure thick, robust contours mapping complex geometry.
2. **Topographic Slicing**: Mixes physical object edges with procedural depth intervals generated via `fract(depth * intervals)`.
3. **Procedural Bloom Convolution**: Samples neighbor bounds via a double `for` loop, weighting luminosity exponentially by radial distance: `glow += e * exp(-dist * 0.5)`.
4. **Dynamic Hue Mapping**: Triple hue mode (Solid, Depth-mapped rainbow, Spatial-scrolling rainbow) manipulating HSV matrices.

### Optimization Constraints & Safety Rails
- **Shader Complexity**: The 49-tap dynamic bloom loop combined with the multi-scale Sobel convolution is extremely fragment-shader heavy. VJLive3 should ideally optimize this by splitting the bloom pass into a separable two-pass (horizontal/vertical) Gaussian blur FBO if performance suffers, though a direct port of the legacy single-pass loop is acceptable if FPS targets are maintained.
- **Optimization Constraint (Safety Rail #1):** Requires patching the universally faulty legacy VDepth `glTexImage2D` buffer reallocation in the draw loop; port entirely to `glTexSubImage2D`.
- **Cleanup Requirement (Safety Rail #8):** Requires explicit OpenGL texture deletion in the teardown.

## Deliverables

1. `src/vjlive3/plugins/p3_vd34.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd34.py` — Comprehensive test suite
3. `docs/plugins/p3_vd34.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] Depth edges correctly detected and highlighted
- [x] Glow color and intensity work as expected
- [x] Audio reactivity works (beat triggers glow pulses)
- [x] ≥80% test coverage across implementation
- [x] Performance: <10ms per 1080p frame (100+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns