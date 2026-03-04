# P3-EXT046: Depth Dual Effect

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

    def process(self, frame: np.ndarray, depth_a: np.ndarray, depth_b: np.ndarray, audio_data: dict) -> np.ndarray:
        """Process frame with two depth sources and audio data, return modified frame."""
        pass
```

## Inputs and Outputs

**Inputs:**
- `frame`: RGB/RGBA numpy array (HxWxC), dtype=uint8 or float32
- `depth_a`: First depth buffer numpy array (HxW), dtype=float32, normalized 0-1
- `depth_b`: Second depth buffer numpy array (HxW), dtype=float32, normalized 0-1
- `audio_data`: Dictionary containing:
  - `fft`: FFT spectrum array (2048 bins)
  - `waveform`: Time-domain waveform array
  - `beat`: Boolean indicating beat detection
  - `bass`, `mid`, `treble`: Frequency band energies (0-1)

**Outputs:**
- Modified frame with dual depth effects applied, same shape and dtype as input

## What It Does NOT Do

- Does NOT create new depth information (uses existing depth buffers)
- Does NOT perform 3D geometry transformations
- Does NOT modify alpha channel (preserves transparency)
- Does NOT require exact depth values (handles missing depth gracefully)
- Does NOT include motion tracking (uses static depth frames)
- Does NOT synchronize depth timestamps (assumes both depth sources are frame-aligned)

## Mathematical Formulations

### Core Algorithm

The effect processes two depth maps simultaneously, applying independent effects to each and blending the results. The core pipeline:

1. **Depth Mask Generation**: For each depth source, generate a mask based on `depth_mask_a`/`depth_mask_b`:
   - `foreground`: mask = smoothstep(0.0, 0.3, depth)
   - `background`: mask = 1.0 - smoothstep(0.7, 1.0, depth)
   - `midground`: mask = smoothstep(0.3, 0.7, depth)
   - `all`: mask = 1.0
   - `custom`: mask derived from user-provided depth range parameters

2. **Effect Application**: Apply selected effect to each depth-masked region:
   - `blur`: Gaussian blur weighted by depth value
   - `glitch`: Displacement based on depth gradient and noise
   - `color_grade`: Color correction based on depth (e.g., fog simulation)
   - `distortion`: UV displacement using depth as height map
   - `edge`: Sobel edge detection on depth, applied as outline
   - `none`: No effect (pass-through)

3. **Blending**: Combine the two effect outputs using `blend_mode`:
   - `normal`: `result = effect_a * (1 - effect_b_mask) + effect_b * effect_b_mask`
   - `add`: `result = effect_a + effect_b`
   - `multiply`: `result = effect_a * effect_b`
   - `screen`: `result = 1.0 - (1.0 - effect_a) * (1.0 - effect_b)`
   - `overlay`: `result = blend_overlay(effect_a, effect_b)`
   - `difference`: `result = abs(effect_a - effect_b)`

4. **Audio Reactivity**: When `audio_sync` is enabled, modulate `effect_a_intensity` and `effect_b_intensity` by audio energy:
   - `intensity_mod = 1.0 + bass * 0.5 * beat_trigger`
   - Applied as multiplicative factor on effect intensities

### Interaction Modes (Legacy Mapping)

The legacy shader used a continuous slider (0.0-10.0) to select 6 discrete modes. In the VJLive3 port, these are mapped to the `effect_a`/`effect_b` combination space:

| Legacy Mode | Index | Description | Modern Equivalent |
|-------------|-------|-------------|-------------------|
| Collision | 0 | Intersecting geometry via `smoothstep(abs(dA - dB))` | Use `effect_a="edge"`, `effect_b="edge"` with `blend_mode="difference"` |
| Interference | 1 | Sinusoidal phase fields from stereoscopic depth | Custom shader combining both depths as `sin(depthA * freq + time)` and `sin(depthB * freq + time)` |
| Volumetric | 3 | Pseudo-light absorption `exp(-(max_d - min_d) * volume_absorption * 10)` | Use `effect_a="color_grade"` with depth-based fog, `effect_b` disabled |
| Parallax | 5 | Spatial disparity → UV shift with Red/Cyan anaglyph | Use `effect_a="distortion"`, `effect_b="none"` with parallax offset from `(depthA - depthB)` |

### Depth Scale Harmonization

The legacy implementation required a `depth_scale_b` uniform to harmonize millimeter-scale outputs from mismatched hardware (Kinect v1 vs Azure). In VJLive3, this is abstracted into the `DepthSource` node calibration:

```python
# Pre-processing normalization
depth_a_normalized = (depth_a - depth_a_min) / (depth_a_max - depth_a_min)
depth_b_normalized = (depth_b - depth_b_min) / (depth_b_max - depth_b_min)
```

The `depth_sensitivity` parameter controls the strength of the cross-depth interactions:

```glsl
float cross_influence = abs(depth_a - depth_b) * depth_sensitivity;
```

## Performance Characteristics

**Memory Footprint:**
- Two depth textures resident in GPU memory: 2 × (width × height × 4 bytes) for float32
- Intermediate effect buffers: 2 × (width × height × 4 bytes) for RGBA float
- Total additional VRAM: ~12 MB per 1080p frame (1920×1080×4×6 bytes)

**Compute Cost:**
- Effect A: varies by type (blur = high, glitch = medium, edge = medium, others = low)
- Effect B: varies by type
- Blend: 1-2 texture samples per pixel
- **Worst-case** (both blur): ~200 texture fetches per pixel (Gaussian 9-tap × 2 + blend)
- **Best-case** (both none): ~3 texture fetches per pixel (depth read × 2 + frame)

**Optimization Constraints:**
1. **Safety Rail #1**: Must use pre-allocated FBO textures with `glTexSubImage2D`, not `glTexImage2D` reallocation
2. **Node Graph Wiring**: Expose secondary hardware binding pin for second `DepthSource`
3. **Cleanup Requirement**: Explicitly clean up both depth textures in destructor

**Benchmark Targets:**
- 1080p (1920×1080): <15ms per frame (66+ fps)
- 720p (1280×720): <8ms per frame (125+ fps)
- 4K (3840×2160): <35ms per frame (28+ fps)

## Edge Cases and Error Handling

**Missing Depth Data:**
- If `depth_a` is None or all zeros: fall back to `effect_b` only with warning log
- If `depth_b` is None or all zeros: fall back to `effect_a` only with warning log
- If both missing: no-op, return original frame unchanged

**Extreme Parameter Values:**
- `effect_a_intensity` or `effect_b_intensity` > 1.0: clamp to 1.0, log warning
- `depth_sensitivity` < 0.0 or > 1.0: clamp to valid range, log warning
- Invalid `blend_mode` enum: default to "normal", log error

**Depth Range Mismatch:**
- If depth values exceed [0, 1] range: auto-normalize using min/max per-frame
- If depth maps have different resolutions: upsample smaller to match larger using bilinear interpolation

**Audio Sync Failure:**
- If `audio_data` is None or missing keys: disable audio reactivity for that frame, continue processing
- If FFT array size mismatch: use first 2048 bins or pad with zeros

**Performance Safeguards:**
- If frame processing exceeds 50ms: auto-reduce `blur_samples` by half for next frame, log performance warning
- If VRAM usage > 80%: disable one effect temporarily, log resource warning

## Test Plan

**Unit Tests:**
- `test_initialization.py`: Verify METADATA completeness, parameter validation, default values
- `test_effect_combination.py`: Verify both effects apply correctly, intensity scaling
- `test_depth_masking.py`: Test depth range selection (foreground/background/midground/custom)
- `test_blend_modes.py`: Verify all 6 blend modes produce mathematically correct results
- `test_audio_sync.py`: Audio-reactive parameter modulation, beat trigger response
- `test_edge_cases.py`: Empty depth, extreme parameter values, null frames, mismatched resolutions

**Integration Tests:**
- `test_plugin_loading.py`: Effect loads via plugin system with correct manifest
- `test_render_pipeline.py`: Effect integrates with RenderEngine and dual DepthSource nodes
- `test_performance.py`: Benchmark processing time across resolutions, ensure <15ms at 1080p
- `test_fbo_management.py`: Verify two FBO textures allocated, updated via glTexSubImage2D, cleaned up

**Visual Regression Tests:**
- `test_output_consistency.py`: Compare against golden frames for known inputs (all 6 effect combinations)
- `test_parameter_sweep.py`: Generate sample outputs across parameter ranges (intensity 0→1, sensitivity 0→1)
- `test_stereoscopic_alignment.py`: Verify depth disparity correctly maps to parallax/anaglyph effects

**Coverage Target:** ≥85% across implementation and integration tests.

## Definition of Done

- [x] Spec document complete with all sections filled
- [x] Public interface clearly defined with METADATA
- [x] Mathematical formulations documented with GLSL snippets
- [x] Performance characteristics analyzed and benchmark targets established
- [x] Edge cases and error handling strategies enumerated
- [x] Test plan comprehensive with unit, integration, and visual regression tests
- [x] Legacy references cited (VJlive-2/plugins/vdepth/depth_dual.py)
- [x] Optimization constraints and safety rails documented
- [x] Easter egg idea generated and added to EASTEREGG_COUNCIL.md
- [x] Spec moved to `docs/specs/_02_fleshed_out/` directory
- [x] BOARD.md updated to mark task as "🟩 COMPLETING PASS 2"

## Legacy References

- **Source Codebase**: VJlive-2
- **File Paths**: `plugins/vdepth/depth_dual.py`
- **Architectural Soul**: The legacy shader defines 6 discrete operation modes evaluated via `if/else` logic mapped against an `interaction_mode` uniform slider (0.0 to 10.0). It requires a `depth_scale_b` modifier to mathematically harmonize varying millimeter-scale outputs from mismatched depth hardware (e.g., Kinect v1 vs Azure).

## Key Algorithms

1. **Collision Mode (0)**: Finds intersecting geometry using `smoothstep()` over the absolute difference `abs(dA - dB)`.
2. **Interference Mode (1)**: Transforms stereoscopic depth into sinusoidal phase fields (`sin(depth * freq + time)`); visualizes constructive/destructive interference maps.
3. **Volumetric Mode (3)**: Calculates pseudo-light absorption using the formula `exp(-(max_d - min_d) * volume_absorption * 10)`.
4. **Parallax Mode (5)**: Translates spatial disparity `(dA - dB)` directly into an uncalibrated 2D UV shift with a Red/Cyan anaglyph color composite.

## Optimization Constraints & Safety Rails

- **Optimization Constraint (Safety Rail #1):** The legacy shader executes raw `glTexImage2D` reallocation *twice* per frame (once for `depth_texture_a` and once for `depth_texture_b`). The VJLive3 port must instantiate two distinct pre-allocated FBO textures using `glTexSubImage2D` to prevent severe VRAM bottlenecking.
- **Node Graph Wiring**: VJLive3 must expose a secondary hardware binding pin so the user can actually route two distinct `DepthSource` nodes into this single effect.
- **Cleanup Requirement (Safety Rail #8):** Must explicitly clean up both depth textures in the destructor.

## Deliverables

1. `src/vjlive3/plugins/p3_ext046.py` — Effect implementation with METADATA
2. `tests/plugins/test_p3_ext046.py` — Comprehensive test suite
3. `docs/plugins/p3_ext046.md` — Usage documentation and parameter guide
4. Updated `BOARD.md` with completion status

## Success Criteria

- [ ] Effect loads successfully via plugin registry
- [ ] All parameters functional and documented in METADATA
- [ ] Both effects apply correctly to their designated depth ranges
- [ ] Blend modes work as expected (add, multiply, screen, etc.)
- [ ] Audio reactivity works (beat triggers parameter changes)
- [ ] ≥80% test coverage across implementation
- [ ] Performance: <15ms per 1080p frame (66+ fps)
- [ ] No safety rail violations during testing
- [ ] Code follows VJLive3 architecture patterns
`

## References

- Legacy implementation: `VJlive-2/plugins/vdepth/depth_dual.py`
- Related specs: P3-VD33_Depth_Dual.md (source of truth for this port)
- Depth effect patterns: P3-VD42_DepthDistortionEffect.md, P3-EXT043_DepthDisplacementEffect.md

## Implementation Tips

1. **Dual DepthSource Binding**: Use the NodeGraph's multi-input capability to bind two separate DepthSource nodes. The effect class should accept `depth_a` and `depth_b` as separate parameters in `process()`.

2. **FBO Management**: Create two FBOs at initialization with textures sized to match the frame resolution. Update textures each frame with `glTexSubImage2D` from the depth buffers. Clean up in `__del__` or `close()`.

3. **Effect Pipeline**: Consider implementing each effect type as a separate shader program or as a unified shader with `#define` switches. The unified approach reduces shader compilation overhead but increases code complexity.

4. **Audio Integration**: The `audio_sync` parameter should gate the audio reactivity. When enabled, use `audio_data['bass']` to scale `effect_a_intensity` and `audio_data['treble']` for `effect_b_intensity`. Beat detection (`audio_data['beat']`) can trigger momentary intensity spikes.

5. **Testing Strategy**: Generate synthetic depth maps with known disparities (e.g., gradient, checkerboard, sphere) to validate the stereoscopic effects. Use unit tests to verify each blend mode's mathematical correctness.

## Conclusion

The DepthDualEffect is a sophisticated stereoscopic depth processor that distinguishes VJLive3 from legacy VJ software. Its ability to fuse two independent depth streams enables truly three-dimensional visual manipulation, from collision detection to volumetric rendering. Careful attention to FBO management and performance optimization will ensure it meets real-time VJing requirements.
