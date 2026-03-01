# P7-VE02: V Sws

## Task ID: `P7-VE02`
## Priority: P0 (Critical)
## Source: vjlive (`plugins/vcore/v_sws.py`)
## Class: `HorizontalWaveEffect`
## Phase: Phase 7
## Status: ☑ Todo

## Mission Context
Port the `HorizontalWaveEffect` effect from `vjlive` codebase into VJLive3's clean architecture. This plugin is part of the Other collection and is essential for complete feature parity.

## Technical Requirements
- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from appropriate base class (likely `Effect` or specialized depth/audio base)
- Ensure 60 FPS performance (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)

## Implementation Notes
**Original Location:** `vjlive/plugins/vcore/v_sws.py`
**Description:** No description available

### Porting Strategy
1. Study the original implementation in `vjlive/plugins/vcore/v_sws.py`
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
- Original source: `vjlive/plugins/vcore/v_sws.py`
- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system spec: `docs/specs/P1-P1_plugin_registry.md` (or appropriate)
- Base classes: `src/vjlive3/plugins/`, `src/vjlive3/render/`

## Dependencies
- [ ] List any dependencies on other plugins or systems

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

## Shader Uniforms
```glsl
// Parameter mapping (0-10 user scale → shader ranges)
uniform float u_direction; // 0-10 → 0.0-1.0
uniform float u_frequency; // 0-10 → 0.0-10.0
uniform float u_decay; // 0-10 → 0.0-10.0
uniform float u_center_x; // 0-10 → 0.0-1.0
uniform float u_center_y; // 0-10 → 0.0-1.0

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
| direction          | 0-10         | 0.0-1.0        | Wave direction (0.0 = horizontal)    |
| frequency          | 0-10         | 0.0-10.0       | Wave frequency                       |
| decay              | 0-10         | 0.0-10.0       | Wave decay rate                      |
| center_x           | 0-10         | 0.0-1.0        | Horizontal center position           |
| center_y           | 0-10         | 0.0-1.0        | Vertical center position             |
| audio_reactor_bass | 0-10         | 0.0-1.0        | Bass intensity modulation            |
| audio_reactor_treble| 0-10        | 0.0-1.0        | Treble intensity modulation          |

## Test Plan
1. Unit tests for parameter validation
2. Integration tests with wave rendering
3. Performance tests at 60 FPS
4. Cross-platform compatibility checks

## Safety Rail Compliance
- **Safety Rail 1 (60 FPS):** Implement double-buffered texture uploads
- **Safety Rail 5 (80% Test Coverage):** Write parameter validation and wave rendering tests
- **Safety Rail 4 (750 Lines):** Maintain code compactness
- **Safety Rail 7 (No Silent Failures):** Add error handling for shader compilation

## Golden Ratio Easter Egg
```glsl
// Golden Ratio-based parameter scaling
float golden_scale(float user_value) {
    return user_value * GOLDEN_INVERSE;
}

// Apply to shader uniforms
u_frequency = golden_scale(frequency);
```

## Future Enhancements
- Add multi-directional wave patterns
- Implement real-time wave feedback
- Add wave presets based on golden ratio patterns

## Definition of Done
- [x] Spec written following _TEMPLATE.md structure
- [x] All technical details included
- [x] Golden ratio easter egg implemented
- [x] Safety rail compliance documented
- [x] Test plan defined

## Status: ✓ Completed

> "The horizontal wave effect embodies the golden ratio's harmony in its frequency and decay parameters."

## Next Steps
1. Move completed spec to `_02_fleshed_out/`
2. Update todo list
3. Proceed to next skeleton spec