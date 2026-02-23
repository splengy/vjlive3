# P3-VD33: Depth Dual Effect

## What This Module Does
Combines two different depth-based effects into a single composite effect. Allows blending between two distinct depth processing pipelines, creating complex visual effects that transition based on depth or other parameters. Useful for creating hybrid effects that combine different depth manipulation techniques.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthDual",
    "version": "3.0.0",
    "description": "Composite two depth effects with blending",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "composite",
    "tags": ["depth", "dual", "composite", "blend"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `effect_a_type: str` (default: "blur", options: ["blur", "color_grade", "distortion", "none"]) - First effect type
- `effect_b_type: str` (default: "color_grade", options: ["blur", "color_grade", "distortion", "none"]) - Second effect type
- `blend_mode: str` (default: "depth", options: ["depth", "uniform", "radial", "custom"]) - Blending control
- `blend_threshold: float` (default: 0.5, min: 0.0, max: 1.0) - Blend point for depth-based mixing
- `blend_transition: float` (default: 0.2, min: 0.0, max: 0.5) - Blend transition width
- `effect_a_params: dict` (default: {}) - Parameters for effect A
- `effect_b_params: dict` (default: {}) - Parameters for effect B
- `invert_blend: bool` (default: False) - Swap A/B based on depth

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)

### Outputs
- `video: Frame` (same format as input) - Composite video frame

## What It Does NOT Do
- Does NOT support arbitrary effect chaining (only two effects)
- Does NOT include all effect types (limited to blur/color_grade/distortion)
- Does NOT perform full effect isolation (effects may interact)
- Does NOT support temporal blending (per-frame only)
- Does NOT include HDR metadata preservation through effects
- Does NOT support custom shader effects beyond built-in types

## Test Plan
1. Unit tests for blend mask generation
2. Verify each effect type produces correct output
3. Test blend_mode variations
4. Performance: ≥ 60 FPS at 1080p with both effects active
5. Memory: < 150MB additional RAM (two effects)
6. Visual: verify smooth transitions between effects

## Implementation Notes
- Implement each effect type as separate processing path
- Compute blend weight based on blend_mode and depth
- For depth blend: weight = smoothstep(blend_threshold - transition, blend_threshold + transition, depth)
- Composite: output = lerp(effect_a_output, effect_b_output, weight)
- Pass effect_a_params/effect_b_params to respective effect implementations
- Optimize by sharing intermediate buffers when possible
- Follow SAFETY_RAILS: validate effect types, handle parameter errors

## Deliverables
- `src/vjlive3/effects/depth_dual.py`
- `tests/effects/test_depth_dual.py`
- `docs/plugins/depth_dual.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Both effects apply correctly
- [x] Blending works smoothly
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations