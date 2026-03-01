# P3-VD32: Depth Distance Filter Effect

## What This Module Does

This module implements the `DepthDistanceFilterEffect`, ported from the legacy `VJlive-2/plugins/vdepth/depth_distance_filter.py` codebase. It is the core spatial depth-matte generator of the suite. It selectively isolates video pixels within a configurable near/far clipping window utilizing sub-pixel smoothstep falloffs. It operates as a virtual "depth green screen", capable of stripping backgrounds or foregrounds, substituting them with solid colors, procedural gaussian blur, or secondary `tex_b` video inputs.

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
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/depth_distance_filter.py`
- **Architectural Soul**: The legacy shader contains an advanced edge-refinement section that samples 4 cardinal GLSL neighbors to execute real-time morphological Erode (via `min()` intersections) and Dilate (via `max()` unions) of the depth map mask. Additionally, its procedural 81-tap gaussian blur fallback for the out-of-bounds `fill_mode` must be successfully ported.

### Key Algorithms
1. **Smoothstep Clipping Window**: `mask *= smoothstep(near) * (1.0 - smoothstep(far))` to establish soft mask boundaries.
2. **Morphological Edge Refine**: Expands or shrinks the clip mask smoothly to prevent aliased artifacting from jagged raw depth feeds.
3. **Multi-State Fill Extrapolator**: Replaces `mask == 0.0` pixels with four logic blocks: Alpha 0.0, Solid Color (via `fill_color`), Procedural Blur (`tex0` spatial sample), or Video B (`texture(tex_b)`).
4. **False-Color Visualization**: Contains a custom diagnostic color scale mapping the active depth topology using distinct RGB gradients.

### Optimization Constraints & Safety Rails
- **Optimization Constraint (Safety Rail #1):** The legacy implementation is burdened by the same `glTexImage2D` frame-loop VRAM memory reallocation anti-pattern as the other legacy VDepth plugins. This MUST be refactored to memory-safe `glTexSubImage2D` updates wrapped against a pre-allocated texture canvas in VJLive3.
- **Missing Resource Handling**: The shader queries `tex_b` directly. VJLive3 must route an empty fallback texture unit if no secondary input exists.
- **Cleanup Requirement (Safety Rail #8):** `self.depth_texture` memory leaks caused by relying upon Python `__del__` garbage collection. Porting requires an explicit `cleanup` cycle to manually call `glDeleteTextures`.

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