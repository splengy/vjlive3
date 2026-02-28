# P3-VD30: Depth Color Grade Effect

## What This Module Does

This module implements the `DepthColorGradeEffect`, ported from the legacy `VJlive-2/plugins/vdepth/depth_color_grade.py` codebase. Rather than a basic atmospheric haze, it is a professional cinematic 3-zone (Near, Mid, Far) color engine. It independently manipulates Hue, Saturation, Temperature (Orange/Blue push), and Exposure per depth band, blending them smoothly via physical distance markers. Furthermore, it explicitly calculates HSV matrix conversions directly on the GPU and caps the final output with an overarching Film Emulation curve (Linear, S-Curve, or Logarithmic).

## Public Interface

```python
class DepthColorGradeEffect(Effect):
    METADATA = {
        "name": "Depth Color Grade",
        "description": "Depth-based color grading with atmospheric effects",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "depth_curve",
                "type": "list",
                "min_items": 2,
                "max_items": 10,
                "default": [0.0, 0.3, 0.7, 1.0],
                "description": "Depth-to-color mapping curve points"
            },
            {
                "name": "foreground_palette",
                "type": "dict",
                "default": {
                    "hue": 0.0,
                    "saturation": 1.0,
                    "brightness": 0.0,
                    "contrast": 1.0
                },
                "description": "Color parameters for foreground elements"
            },
            {
                "name": "background_palette",
                "type": "dict",
                "default": {
                    "hue": 0.6,
                    "saturation": 0.7,
                    "brightness": -0.2,
                    "contrast": 0.8
                },
                "description": "Color parameters for background elements"
            },
            {
                "name": "atmospheric_haze",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.2,
                "description": "Intensity of atmospheric haze effect"
            },
            {
                "name": "depth_sensitivity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.9,
                "description": "How strongly depth affects color grading"
            },
            {
                "name": "color_transition",
                "type": "enum",
                "options": ["linear", "logarithmic", "exponential", "custom"],
                "default": "linear",
                "description": "Depth-to-color transition function"
            }
        ],
        "metadata": {
            "tags": ["color", "depth", "grade", "cinematic", "atmosphere"],
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
- Modified frame with depth-based color grading applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT perform full color space conversions (uses RGB space for simplicity)
- Does NOT include advanced film emulation (no film grain or halation)
- Does NOT handle HDR color grading (expects SDR input)
- Does NOT modify alpha channel (preserves transparency)
- Does NOT require depth data to be non-zero (handles missing depth gracefully)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_color_grading.py`: Verify color parameters correctly apply to depth ranges
- `test_curve_mapping.py`: Test depth_curve mapping accuracy
- `test_audio_reactivity.py`: Audio-driven color parameter modulation
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and DepthSource
- `test_compositing.py`: Verify color grading integrates properly with other effects
- `test_performance.py`: Benchmark processing time, ensure <10ms at 1080p

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/depth_color_grade.py`
- **Architectural Soul**: The legacy GLSL shader calculates complex temperature shifting by manually driving `color.r += t` and `color.b -= t` before executing an `rgb2hsv` conversion to lock saturation ratios. The 3-zone smoothstep blending algorithm (near_mask/mid_mask/far_mask) and the specific log emulation (`log(1.0 + color * 9.0) / log(10.0)`) MUST be preserved exactly to match the visual parity of the legacy effect.

### Key Algorithms
1. **Geometric Soft Masking**: Calculates `near_mask`, `mid_mask`, and `far_mask` per pixel using `smoothstep` blending ratios.
2. **GPU HSV Conversion**: Translates RGB space into HSV for mathematically perfect hue rotation and saturation scalar manipulation before reconstructing RGB.
3. **Film Emulation**: Overarching non-linear contrast mapping for `S-Curve` and `Log` cinematic finish.

### Optimization Constraints & Safety Rails
- **Optimization Constraint (Safety Rail #1):** Like its sister plugin `DepthBlur`, the legacy `DepthColorGrade` invokes `glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, dn.shape[1], dn.shape[0], ...)` in every single active frame loop. This is strictly prohibited in VJLive3. The 8-bit depth array must exclusively be updated via `glTexSubImage2D` into a statically sized bounding box allocated during `__init__`.
- **Handling Missing Audio Analytics:** If `audio_reactor=None`, the `near_temperature`, `near_saturation`, and `far_hue` uniforms gracefully fall back to parsing solely their unmodulated slider constants.
- **Cleanup Requirement (Safety Rail #8):** `self.depth_texture` memory leak via Python `__del__` is inadequate. This effect requires an explicit OpenGL resource `.cleanup()` method.

## Deliverables

1. `src/vjlive3/plugins/p3_vd30.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd30.py` — Comprehensive test suite
3. `docs/plugins/p3_vd30.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] Depth curve correctly maps to color parameters
- [x] Foreground/background separation works as expected
- [x] Atmospheric haze produces realistic depth effects
- [x] Audio reactivity works (beat triggers color shifts)
- [x] ≥80% test coverage across implementation
- [x] Performance: <10ms per 1080p frame (100+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns