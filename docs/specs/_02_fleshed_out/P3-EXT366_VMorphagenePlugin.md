# P3-EXT366: Make Noise Morphagene

## What This Module Does
This module provides a software emulation of the Make Noise Morphagene Eurorack synthesizer module. It translates physical CV (Control Voltage) and audio-rate behavior into VJLive3's virtual graph, maintaining strict adherence to the Make Noise philosophy of modular synthesis.

## What It Does NOT Do
- Handle file I/O or persistent storage operations
- Process audio streams or provide sound-reactive capabilities
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context

## Public Interface
```python
class VMorphagenePlugin(EffectNode):
    """Software virtualization of Make Noise Morphagene."""
    # Physical knob/jack parameters map 1:1 to Uniforms/Inputs
```

## Implementation Notes
### Legacy References
- **Source Codebase**: `VJlive-2` and `vjlive`
- **Software File Paths**: `plugins/core/vmake_noise/vmake_noise.py`
- **Hardware Documentation**:
  - **Manual PDF**: `vjlive/JUNK/manuals_make_noise/morphagene-manual.pdf`

### Architectural Soul
The module is expected to replicate the exact DSP logic (if audio-rate) or mathematical modulation curves (if control-rate) described in the `morphagene` documentation.

### Optimization Constraints & Safety Rails
- **GIL Locking limits:** If implementing DSP in pure Python, NumPy vectorization must be used to process audio buffers chunk-by-chunk to avoid blocking the main 60FPS render loop.

## Test Plan
| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware (GPU) is absent or unavailable |
| `test_basic_operation` | Core rendering function produces valid ASCII output when given a clean input frame |
| `test_parameter_range_validation` | All parameter inputs are clamped to 0.0-10.0 range and rejected outside bounds |
| `test_color_mode_switching` | Switching between color modes (e.g., mono_green → rainbow) changes output appearance correctly |
| `test_scroll_rain_effect` | Matrix rain animation moves at correct speed and density based on scroll_speed and rain_density |
| `test_crt_effects` | Scanlines, phosphor glow, and flicker are visible and proportional to input values |
| `test_edge_detection_and_detail_boost` | Edge detection and detail boost improve character clarity in low-contrast scenes |
| `test_parameter_set_get_cycle` | Dynamic parameter updates via set/get methods reflect real-time changes in output |
| `test_grayscale_input_handling` | Input in grayscale is correctly interpreted for luminance-based ASCII mapping |
| `test_invalid_frame_size` | Invalid frame sizes (e.g., <64x64) raise appropriate exceptions without crashing |
| `test_legacy_compatibility` | Output matches expected visual characteristics of legacy implementations |

## Deliverables
1. `src/vjlive3/plugins/make_noise/morphagene.py`
2. Integrated block in the `MakeNoiseRegistry`

## Minimum coverage: 80% before task is marked done.

## Definition of Done
- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT366: Make Noise Morphagene - software emulation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up