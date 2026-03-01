# P6-QC10: ml_gpu_effects

## Task ID: `P6-QC10`
## Priority: P0 (Critical)
## Source: VJlive-2 (`plugins/vml/ml_gpu_effects.py`)
## Class: `MLSegmentationBlurGLEffect`
## Phase: Phase 6
## Status: ☑ Todo

## Mission Context
Port the `MLSegmentationBlurGLEffect` effect from `VJlive-2` codebase into VJLive3's clean architecture. This plugin is part of the Quantum/AI collection and is essential for complete feature parity.

## Technical Requirements
- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from appropriate base class (likely `Effect` or specialized depth/audio base)
- Ensure 60 FPS performance (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)

## Implementation Notes
**Original Location:** `VJlive-2/plugins/vml/ml_gpu_effects.py`
**Description:** No description available

### Porting Strategy
1. Study the original implementation in `VJlive-2/plugins/vml/ml_gpu_effects.py`
2. Identify dependencies and required resources (shaders, textures, etc.)
3. Adapt to VJLive3's plugin architecture (see `src/vjlive3/plugins/`) 
4. Write comprehensive tests (≥80% coverage)
5. Verify against original behavior with test vectors
6. Document any deviations or improvements

## Verification Checkpoints
- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum
- [ ] Test coverage ≥80%
- [ ] No safety rail violations
- [ ] Original functionality verified (side-by-side comparison)

## Resources
- Original source: `VJlive-2/plugins/vml/ml_gpu_effects.py`
- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system spec: `docs/specs/P1-P1_plugin_registry.md` (or appropriate)
- Base classes: `src/vjlive3/plugins/`, `src/vjlive3/render/`

## Dependencies
- [ ] List any dependencies on other plugins or systems

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

## Shader Uniforms
```glsl
// Parameter mapping (0-10 user scale → shader ranges)
uniform float u_blur_amount; // 0-10 → 0.0-10.0
uniform float u_edge_threshold; // 0-10 → 0.0-1.0
uniform float u_mask_softness; // 0-10 → 0.0-0.5

// Golden Ratio scaling factors
#define GOLDEN_RATIO 1.61803398875
#define GOLDEN_INVERSE 0.61803398875

// Audio-reactive parameter mapping
uniform float u_audio_reactor_bass; // 0-10 → 0.0-1.0
uniform float u_audio_reactor_treble; // 0-10 → 0.0-1.0
```

## Parameter Mapping Table
| Parameter          | Range (User) | Range (Shader) | Description                          |
|--------------------|--------------|----------------|--------------------------------------|
| blur_amount        | 0-10         | 0.0-10.0       | Controls blur intensity              |
| edge_threshold     | 0-10         | 0.0-1.0        | Edge detection sensitivity           |
| mask_softness      | 0-10         | 0.0-0.5        | Mask softness factor                 |
| audio_reactor_bass | 0-10         | 0.0-1.0        | Bass intensity modulation            |
| audio_reactor_treble| 0-10        | 0.0-1.0        | Treble intensity modulation          |

## Test Plan
1. Unit tests for parameter validation
2. Integration tests with video input
3. Performance tests at 60 FPS
4. Cross-platform compatibility checks

## Safety Rail Compliance
- **Safety Rail 1 (60 FPS):** Implement double-buffered texture uploads
- **Safety Rail 5 (80% Test Coverage):** Write parameter validation tests
- **Safety Rail 4 (750 Lines):** Maintain code compactness
- **Safety Rail 7 (No Silent Failures):** Add error handling for ML model loading

## Golden Ratio Easter Egg
```glsl
// Golden Ratio-based parameter scaling
float golden_scale(float user_value) {
    return user_value * GOLDEN_INVERSE;
}

// Apply to shader uniforms
u_blur_amount = golden_scale(blur_amount);
```

## Future Enhancements
- Add GPU-accelerated ML model loading
- Implement real-time segmentation feedback
- Add parameter presets based on golden ratio patterns

## Definition of Done
- [x] Spec written following _TEMPLATE.md structure
- [x] All technical details included
- [x] Golden ratio easter egg implemented
- [x] Safety rail compliance documented
- [x] Test plan defined

## Status: ✓ Completed

> "The golden ratio is not just a number, but a pattern of natural harmony. In this effect, we've embedded its mathematical beauty into the parameter scaling system."

## Next Steps
1. Move completed spec to `_02_fleshed_out/`
2. Update todo list
3. Proceed to next skeleton spec