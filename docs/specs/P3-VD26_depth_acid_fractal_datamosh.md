# P3-VD26: Depth Acid Fractal Datamosh Effect

## What This Module Does
Implements a datamosh effect that combines acid fractal patterns with depth buffer manipulation. The effect creates psychedelic, glitchy visuals by treating depth values as coordinates for fractal generation and then datamoshing the result with the original video stream.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthAcidFractalDatamoshEffect",
    "version": "3.0.0",
    "description": "Acid fractal datamosh effect with depth buffer integration",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "datamosh",
    "tags": ["depth", "datamosh", "fractal", "acid", "glitch"],
    "priority": 1,
    "dependencies": ["DepthBuffer", "FractalGenerator"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `fractal_scale: float` (default: 2.0, min: 0.1, max: 10.0) - Scale of fractal pattern
- `datamosh_intensity: float` (default: 0.5, min: 0.0, max: 1.0) - Strength of datamosh effect
- `depth_influence: float` (default: 0.7, min: 0.0, max: 1.0) - How much depth affects fractal
- `color_shift: float` (default: 0.3, min: 0.0, max: 1.0) - Color aberration amount
- `glitch_probability: float` (default: 0.1, min: 0.0, max: 1.0) - Chance of frame corruption
- `preserve_luminance: bool` (default: True) - Keep original brightness

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `beat_phase: float` (optional) - Current beat phase for sync (0.0-1.0)

### Outputs
- `video: Frame` (RGB or RGBA, same format as input) - Processed frame with acid fractal datamosh

## What It Does NOT Do
- Does NOT require external GPU compute (CPU-only implementation)
- Does NOT modify original depth buffer (operates on copy)
- Does NOT support 3D mesh extraction (2D depth mapping only)
- Does NOT include audio processing (audio-reactive optional via beat_phase)
- Does NOT handle HDR metadata (pass-through only)

## Test Plan
1. Unit tests for fractal generation with depth mapping
2. Verify datamosh algorithm produces expected corruption patterns
3. Test parameter boundaries (min/max values)
4. Performance test: ≥ 60 FPS at 1080p on reference hardware
5. Memory leak test: run 10,000 frames, monitor RAM usage
6. Visual regression: compare against golden outputs

## Implementation Notes
- Use iterative fractal function (Mandelbrot or Julia set)
- Map depth values to fractal coordinate space
- Apply datamosh by copying macroblocks from previous frames
- Use beat_phase to modulate parameters if provided
- Must maintain 60 FPS target; optimize with Numba/Cython if needed
- Follow SAFETY_RAILS.md: no silent failures, proper error handling

## Deliverables
- `src/vjlive3/effects/depth_acid_fractal_datamosh.py` (main plugin)
- `tests/effects/test_depth_acid_fractal_datamosh.py` (unit + integration)
- `docs/plugins/depth_acid_fractal_datamosh.md` (user documentation)
- `shaders/depth_acid_fractal.frag` (optional GLSL fallback)

## Success Criteria
- [x] Plugin loads via METADATA discovery system
- [x] Accepts video + depth inputs, produces output
- [x] All parameters functional and within safe ranges
- [x] 60 FPS at 1080p on reference hardware (i7-9700K, RTX 4070)
- [x] Zero memory leaks after 10k frame stress test
- [x] Test coverage ≥ 80%
- [x] No safety rail violations