# P3-EXT052: Depth Groovy Datamosh Effect

## What This Module Does
Creates a groovy, psychedelic datamosh effect that uses depth information to control the datamosh pattern and intensity. The effect produces colorful, flowing distortions that follow depth contours, creating a trippy, retro-futuristic visual style.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthGroovyDatamosh",
    "version": "3.0.0",
    "description": "Psychedelic datamosh with depth control",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "datamosh",
    "tags": ["depth", "datamosh", "groovy", "psychedelic", "colorful"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `datamosh_intensity: float` (default: 0.5, min: 0.0, max: 1.0) - Overall strength of datamosh
- `color_shift_amount: float` (default: 0.3, min: 0.0, max: 1.0) - Color aberration intensity
- `depth_contrast: float` (default: 1.0, min: 0.1, max: 3.0) - Contrast of depth-based modulation
- `flow_speed: float` (default: 1.0, min: 0.1, max: 5.0) - Speed of datamosh evolution
- `pattern_scale: int` (default: 8, min: 2, max: 32) - Size of datamosh blocks/macroblocks
- `preserve_luminance: bool` (default: True) - Keep original brightness levels
- `saturation_boost: float` (default: 0.2, min: 0.0, max: 1.0) - Increase color saturation
- `glow_intensity: float` (default: 0.1, min: 0.0, max: 0.5) - Additive glow effect

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `timestamp: float` (optional) - Current time for animation

### Outputs
- `video: Frame` (same format as input) - Groovy datamoshed video

## What It Does NOT Do
- Does NOT perform full frame interpolation (only macroblock copying)
- Does NOT support audio-reactive modulation (depth-only)
- Does NOT include 3D mesh extraction (2D depth mapping)
- Does NOT handle HDR metadata preservation
- Does NOT support custom color palettes (automatic color shifting)
- Does NOT include temporal smoothing (per-frame processing)

## Test Plan
1. Unit tests for depth-based datamosh pattern generation
2. Verify color shift produces psychedelic effects
3. Test all parameter combinations
4. Performance: ≥ 60 FPS at 1080p with datamosh_intensity=0.5
5. Memory: < 100MB additional RAM
6. Visual: verify groovy aesthetic matches expectations

## Implementation Notes
- Use depth to control which macroblocks get datamoshed and by how much
- Apply color_shift_amount to create chromatic aberration by offsetting RGB channels differently
- Use depth_contrast to enhance depth differences before applying datamosh
- Animate datamosh pattern using timestamp and flow_speed
- For each macroblock of size pattern_scale:
  - If depth value > threshold (modulated by depth_contrast), apply datamosh
  - Copy macroblock from previous frame or random location
  - Apply color shift based on depth
- If preserve_luminance: maintain original Y channel in YUV or use luminance-preserving blend
- Apply saturation_boost to enhance colors
- Add glow_intensity as additive brightening
- Optimize with block-based processing and SIMD
- Follow SAFETY_RAILS: handle edge cases, no silent failures

## Deliverables
- `src/vjlive3/effects/depth_groovy_datamosh.py`
- `tests/effects/test_depth_groovy_datamosh.py`
- `docs/plugins/depth_groovy_datamosh.md`
- Optional: `shaders/depth_groovy_datamosh.frag`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Groovy datamosh effect works with depth
- [x] Color shifting creates psychedelic look
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations