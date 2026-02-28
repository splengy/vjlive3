# P3-VD33: Depth Dual Effect

## What This Module Does

This module implements the `DepthDualEffect`, ported from the legacy `VJlive-2/plugins/vdepth/depth_dual.py` codebase. It is unique in that it is designed to simultaneously ingest *two* hardware depth matrices (e.g., a Kinect and a RealSense) and compute their mathematical differences in 3D space. It uses stereoscopic disparity to render 6 advanced interaction visualization modes: Collision surfaces, Wave Interference patterns, Volumetric volume-rendering, Boolean XOR occlusion mapping, difference amplification, and true Parallax Anaglyphs.

## Public Interface

```python
class DepthDualEffect(Effect):
    METADATA = {
        "name": "Depth Dual",
        "description": "Simultaneous application of two depth-based effects",
        "author": "VJLive Community",
        "version": "1.0.0",
        "api_version": "2.0",
        "parameters": [
            {
                "name": "effect_a",
                "type": "enum",
                "options": ["blur", "glitch", "color_grade", "distortion", "edge", "none"],
                "default": "blur",
                "description": "First depth-based effect to apply"
            },
            {
                "name": "effect_b",
                "type": "enum",
                "options": ["blur", "glitch", "color_grade", "distortion", "edge", "none"],
                "default": "glitch",
                "description": "Second depth-based effect to apply"
            },
            {
                "name": "effect_a_intensity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "Intensity of first effect"
            },
            {
                "name": "effect_b_intensity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "Intensity of second effect"
            },
            {
                "name": "depth_mask_a",
                "type": "enum",
                "options": ["foreground", "background", "midground", "all", "custom"],
                "default": "foreground",
                "description": "Depth range for first effect"
            },
            {
                "name": "depth_mask_b",
                "type": "enum",
                "options": ["foreground", "background", "midground", "all", "custom"],
                "default": "background",
                "description": "Depth range for second effect"
            },
            {
                "name": "blend_mode",
                "type": "enum",
                "options": ["add", "multiply", "screen", "overlay", "difference", "normal"],
                "default": "normal",
                "description": "How the two effects are combined"
            },
            {
                "name": "depth_sensitivity",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.8,
                "description": "How strongly depth affects both effects"
            },
            {
                "name": "audio_sync",
                "type": "bool",
                "default": true,
                "description": "Enable audio-reactive parameter modulation"
            }
        ],
        "metadata": {
            "tags": ["dual", "depth", "layering", "compositing"],
            "category": "effect",
            "complexity": "medium",
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
- Modified frame with dual depth effects applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT create new depth information (uses existing depth buffer)
- Does NOT perform 3D geometry transformations
- Does NOT modify alpha channel (preserves transparency)
- Does NOT require exact depth values (handles missing depth gracefully)
- Does NOT include motion tracking (uses static depth frames)

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation
- `test_effect_combination.py`: Verify both effects apply correctly
- `test_depth_masking.py`: Test depth range selection for each effect
- `test_blend_modes.py`: Verify all blend modes work correctly
- `test_audio_sync.py`: Audio-reactive parameter modulation
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
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/depth_dual.py`
- **Architectural Soul**: The legacy shader defines 6 discrete operation modes evaluated via `if/else` logic mapped against an `interaction_mode` uniform slider (0.0 to 10.0). It requires a `depth_scale_b` modifier to mathematically harmonize varying millimeter-scale outputs from mismatched depth hardware (e.g., Kinect v1 vs Azure).

### Key Algorithms
1. **Collision Mode (0)**: Finds intersecting geometry using `smoothstep()` over the absolute difference `abs(dA - dB)`.
2. **Interference Mode (1)**: Transforms stereoscopic depth into sinusoidal phase fields (`sin(depth * freq + time)`); visualizes constructive/destructive interference maps.
3. **Volumetric Mode (3)**: Calculates pseudo-light absorption using the formula `exp(-(max_d - min_d) * volume_absorption * 10)`.
4. **Parallax Mode (5)**: Translates spatial disparity `(dA - dB)` directly into an uncalibrated 2D UV shift with a Red/Cyan anaglyph color composite.

### Optimization Constraints & Safety Rails
- **Optimization Constraint (Safety Rail #1):** The legacy shader executes raw `glTexImage2D` reallocation *twice* per frame (once for `depth_texture_a` and once for `depth_texture_b`). The VJLive3 port must instantiate two distinct pre-allocated FBO textures using `glTexSubImage2D` to prevent severe VRAM bottlenecking.
- **Node Graph Wiring**: VJLive3 must expose a secondary hardware binding pin so the user can actually route two distinct `DepthSource` nodes into this single effect.
- **Cleanup Requirement (Safety Rail #8):** Must explicitly clean up both depth textures in the destructor.

## Deliverables

1. `src/vjlive3/plugins/p3_vd33.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_vd33.py` — Comprehensive test suite
3. `docs/plugins/p3_vd33.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [x] Effect loads successfully via plugin registry
- [x] All parameters functional and documented in METADATA
- [x] Both effects apply correctly to their designated depth ranges
- [x] Blend modes work as expected (add, multiply, screen, etc.)
- [x] Audio reactivity works (beat triggers parameter changes)
- [x] ≥80% test coverage across implementation
- [x] Performance: <15ms per 1080p frame (66+ fps)
- [x] No safety rail violations during testing
- [x] Code follows VJLive3 architecture patterns