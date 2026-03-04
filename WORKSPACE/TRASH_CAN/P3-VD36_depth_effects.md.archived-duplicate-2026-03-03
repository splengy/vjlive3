# P3-VD36: Depth Effects Plugin

## What This Module Does
Provides a collection of multiple depth-based effects that can be chained together in a single plugin. Allows users to combine different depth processing operations (blur, color grade, distortion, etc.) with configurable order and parameters. Useful for creating complex depth-based visual effects without managing multiple plugins.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthEffects",
    "version": "3.0.0",
    "description": "Chain multiple depth effects together",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "utility",
    "tags": ["depth", "effects", "chain", "pipeline"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `effect_chain: list[dict]` (default: []) - List of effects to apply in order
- `effect_order: list[str]` (default: []) - Names of effects in processing order
- `effect_params: dict` (default: {}) - Parameters for each effect
- `blend_mode: str` (default: "sequential", options: ["sequential", "parallel", "weighted"]) - How to combine effects
- `blend_weights: list[float]` (default: []) - Weights for parallel blending
- `enable_depth_normalization: bool` (default: True) - Normalize depth for all effects
- `preserve_original: bool` (default: False) - Keep original video for blending

### Effect Types Available
- "blur": Depth-based blur
- "color_grade": Depth-based color grading
- "distortion": Depth-based distortion
- "glow": Depth edge glow
- "fog": Depth-based fog
- "sharpen": Depth-based sharpening

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (normalized or raw)

### Outputs
- `video: Frame` (same format as input) - Processed video frame

## What It Does NOT Do
- Does NOT support custom effects beyond built-in types
- Does NOT include all possible effect combinations
- Does NOT perform real-time effect parameter optimization
- Does NOT handle HDR metadata preservation through effects
- Does NOT support effect-specific parameter validation
- Does NOT include effect-specific documentation

## Test Plan
1. Unit tests for effect chain execution
2. Verify each effect type produces correct output
3. Test blend_mode variations
4. Performance: ≥ 60 FPS at 1080p with 3 effects
5. Memory: < 200MB additional RAM (multiple effects)
6. Visual: verify effect combinations work as expected

## Implementation Notes
- Parse effect_chain to determine which effects to apply
- For sequential blend_mode: apply effects in order, each receives previous output
- For parallel blend_mode: apply all effects to original, then blend with weights
- For weighted blend_mode: apply effects with different strengths
- Use enable_depth_normalization for all effects if True
- If preserve_original: blend final result with original video
- Optimize by sharing depth buffer and intermediate buffers
- Follow SAFETY_RAILS: validate effect types, handle parameter errors

## Deliverables
- `src/vjlive3/effects/depth_effects.py`
- `tests/effects/test_depth_effects.py`
- `docs/plugins/depth_effects.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Effect chain executes correctly
- [x] All effect types functional
- [x] 60 FPS at 1080p with 3 effects
- [x] Test coverage ≥ 80%
- [x] No safety rail violations