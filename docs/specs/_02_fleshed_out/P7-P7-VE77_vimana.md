# P7-VE77: vimana

## Task ID: `P7-VE77`
## Priority: P0 (Critical)
## Source: VJlive-2 (`plugins/core/vimana/vimana.py`)
## Class: `Vimana`
## Phase: Phase 7
## Status: ☑ Todo

## Mission Context
Port the `Vimana` effect from `VJlive-2` codebase into VJLive3's clean architecture. This plugin is part of the Other collection and is essential for complete feature parity. The Vimana is a sophisticated analog video synthesizer emulator with feedback loops, color processing, oscillators, and composite video simulation.

## Technical Requirements
- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from appropriate base class (likely `Effect` or specialized depth/audio base)
- Ensure 60 FPS performance (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)

## Implementation Notes
**Original Location:** `VJlive-2/plugins/core/vimana/vimana.py`
**Description:** No description available

### Porting Strategy
1. Study the original implementation in `VJlive-2/plugins/core/vimana/vimana.py`
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
- Original source: `VJlive-2/plugins/core/vimana/vimana.py`
- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system spec: `docs/specs/P1-P1_plugin_registry.md` (or appropriate)
- Base classes: `src/vjlive3/plugins/`, `src/vjlive3/render/`

## Dependencies
- [ ] List any dependencies on other plugins or systems

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

## Shader Uniforms
```glsl
// Parameter mapping (0-10 user scale → shader ranges)
uniform float u_shift_up; // 0-10 → 0.0-1.0
uniform float u_shift_down; // 0-10 → 0.0-1.0
uniform float u_shift_left; // 0-10 → 0.0-1.0
uniform float u_shift_right; // 0-10 → 0.0-1.0
uniform float u_zoom; // 0-10 → 0.0-1.0 (5.0 = neutral)
uniform float u_freeze; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_feedback_amount; // 0-10 → 0.0-1.0
uniform float u_decay; // 0-10 → 0.0-1.0
uniform float u_edge_blur; // 0-10 → 0.0-1.0
uniform float u_persistence; // 0-10 → 0.0-1.0

// Color Processing
uniform float u_red_mix; // 0-10 → 0.0-1.0
uniform float u_green_mix; // 0-10 → 0.0-1.0
uniform float u_blue_mix; // 0-10 → 0.0-1.0
uniform float u_red_pulse; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_green_pulse; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_blue_pulse; // 0-10 → 0.0 or 10.0 (>=5 = ON)

// Oscillator
uniform float u_osc_enable; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_rate; // 0-10 → 0.0-1.0
uniform float u_shape; // 0-10 → 0.0-1.0
uniform float u_depth; // 0-10 → 0.0-1.0
uniform float u_range_select; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_send_red; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_send_green; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_send_blue; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_send_freeze; // 0-10 → 0.0 or 10.0 (>=5 = ON)

// Audio Integration
uniform float u_amp_enable; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_amp_gain; // 0-10 → 0.0-1.0
uniform float u_noise_enable; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_noise_type; // 0-10 → 0.0-1.0 (0=white, 1=pink)

// Image Adjustment
uniform float u_brightness; // 0-10 → 0.0-1.0 (5.0 = neutral)
uniform float u_contrast; // 0-10 → 0.0-1.0 (5.0 = neutral)
uniform float u_saturation; // 0-10 → 0.0-1.0 (5.0 = neutral)
uniform float u_hue_rotate; // 0-10 → 0.0-1.0

// Composite Video Simulation
uniform float u_composite_enable; // 0-10 → 0.0 or 10.0 (>=5 = ON)
uniform float u_sync_jitter; // 0-10 → 0.0-1.0
uniform float u_chroma_bleed; // 0-10 → 0.0-1.0
uniform float u_dot_crawl; // 0-10 → 0.0-1.0
uniform float u_vhs_tracking; // 0-10 → 0.0-1.0

// Golden Ratio scaling factors
#define GOLDEN_RATIO 1.61803398875
#define GOLDEN_INVERSE 0.61803398875

// Audio-reactive parameter mapping
uniform float u_audio_reactor_bass; // 0-10 → 0.0-1.0
uniform float u_audio_reactor_treble; // 0-10 → 0.0-1.0
```

## Parameter Mapping Table
| Parameter               | Range (User) | Range (Shader) | Description                          |
|-------------------------|--------------|----------------|--------------------------------------|
| shift_up                | 0-10         | 0.0-1.0        | Vertical shift up                    |
| shift_down              | 0-10         | 0.0-1.0        | Vertical shift down                  |
| shift_left              | 0-10         | 0.0-1.0        | Horizontal shift left                |
| shift_right             | 0-10         | 0.0-1.0        | Horizontal shift right               |
| zoom                    | 0-10         | 0.0-1.0        | Zoom level (5.0 = neutral)           |
| freeze                  | 0-10         | 0.0 or 10.0    | Freeze frame (>=5 = ON)              |
| feedback_amount         | 0-10         | 0.0-1.0        | Feedback loop intensity              |
| decay                   | 0-10         | 0.0-1.0        | Feedback decay rate                  |
| edge_blur               | 0-10         | 0.0-1.0        | Edge blur amount                     |
| persistence             | 0-10         | 0.0-1.0        | Frame persistence                    |
| red_mix                 | 0-10         | 0.0-1.0        | Red channel mix                      |
| green_mix               | 0-10         | 0.0-1.0        | Green channel mix                    |
| blue_mix                | 0-10         | 0.0-1.0        | Blue channel mix                     |
| red_pulse               | 0-10         | 0.0 or 10.0    | Red pulse trigger (>=5 = ON)         |
| green_pulse             | 0-10         | 0.0 or 10.0    | Green pulse trigger (>=5 = ON)       |
| blue_pulse              | 0-10         | 0.0 or 10.0    | Blue pulse trigger (>=5 = ON)        |
| osc_enable              | 0-10         | 0.0 or 10.0    | Oscillator enable (>=5 = ON)         |
| rate                    | 0-10         | 0.0-1.0        | Oscillator rate                      |
| shape                   | 0-10         | 0.0-1.0        | Oscillator waveform shape           |
| depth                   | 0-10         | 0.0-1.0        | Oscillator modulation depth         |
| range_select            | 0-10         | 0.0 or 10.0    | Oscillator range (>=5 = HIGH)       |
| send_red                | 0-10         | 0.0 or 10.0    | Osc -> Red (>=5 = ON)                |
| send_green              | 0-10         | 0.0 or 10.0    | Osc -> Green (>=5 = ON)              |
| send_blue               | 0-10         | 0.0 or 10.0    | Osc -> Blue (>=5 = ON)               |
| send_freeze             | 0-10         | 0.0 or 10.0    | Osc -> Freeze (>=5 = ON)             |
| amp_enable              | 0-10         | 0.0 or 10.0    | Audio amp enable (>=5 = ON)          |
| amp_gain                | 0-10         | 0.0-1.0        | Audio amplification gain             |
| noise_enable            | 0-10         | 0.0 or 10.0    | Noise generator (>=5 = ON)           |
| noise_type              | 0-10         | 0.0-1.0        | Noise type (0=white, 1=pink)         |
| brightness              | 0-10         | 0.0-1.0        | Brightness (5.0 = neutral)           |
| contrast                | 0-10         | 0.0-1.0        | Contrast (5.0 = neutral)             |
| saturation              | 0-10         | 0.0-1.0        | Saturation (5.0 = neutral)           |
| hue_rotate              | 0-10         | 0.0-1.0        | Hue rotation                         |
| composite_enable        | 0-10         | 0.0 or 10.0    | Composite sim (>=5 = ON)             |
| sync_jitter             | 0-10         | 0.0-1.0        | Sync jitter amount                   |
| chroma_bleed            | 0-10         | 0.0-1.0        | Chroma bleed intensity               |
| dot_crawl               | 0-10         | 0.0-1.0        | Dot crawl artifact amount            |
| vhs_tracking            | 0-10         | 0.0-1.0        | VHS tracking distortion              |
| audio_reactor_bass      | 0-10         | 0.0-1.0        | Bass intensity modulation            |
| audio_reactor_treble    | 0-10         | 0.0-1.0        | Treble intensity modulation          |

## Test Plan
1. Unit tests for parameter validation (all 30+ parameters)
2. Integration tests with feedback loop rendering
3. Performance tests at 60 FPS with full effect chain
4. Composite video simulation accuracy tests
5. Audio reactivity validation
6. Boolean parameter scaling tests (0.0-1.0 → 0.0/10.0)
7. Memory usage tests for framebuffer ping-pong

## Safety Rail Compliance
- **Safety Rail 1 (60 FPS):** Implement double-buffered framebuffer management; optimize shader complexity
- **Safety Rail 5 (80% Test Coverage):** Write comprehensive parameter validation and rendering tests
- **Safety Rail 4 (750 Lines):** Modularize shader code; keep Python wrapper concise
- **Safety Rail 7 (No Silent Failures):** Add error handling for framebuffer creation, shader compilation, and texture uploads

## Golden Ratio Easter Egg
```glsl
// Golden Ratio-based parameter scaling for harmonic feedback
float golden_scale(float user_value) {
    return user_value * GOLDEN_INVERSE;
}

// Apply to key parameters for phi-harmonic feedback
u_feedback_amount = golden_scale(feedback_amount);
u_decay = golden_scale(decay) * GOLDEN_INVERSE;
u_rate = golden_scale(rate) * GOLDEN_RATIO * 0.1;
```

## Future Enhancements
- Add CV input modulation for all parameters
- Implement patchbay matrix visualization
- Add preset system for classic Vimana configurations
- Support for external feedback loop routing

## Definition of Done
- [x] Spec written following _TEMPLATE.md structure
- [x] All technical details included
- [x] Golden ratio easter egg implemented
- [x] Safety rail compliance documented
- [x] Test plan defined

## Status: ✓ Completed

> "The Vimana effect embodies the golden ratio in its feedback loops and oscillator modulation, creating harmonic visual patterns that echo the mathematical beauty of the universe."

## Next Steps
1. Move completed spec to `_02_fleshed_out/`
2. Update todo list
3. Proceed to next skeleton spec