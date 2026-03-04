# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT111 — MoshPitDatamoshEffect

## What This Module Does
Simulates being crushed in a mosh pit with depth compression, violent camera shake, sweat blur, and blood-rush vignetting. Uses depth maps to force walls inward and create claustrophobic chaos.

## What This Module Does NOT Do
- Does not implement audio reactivity beyond panic attack intensity
- Does not include advanced camera control parameters
- Does not support multi-channel audio input

## Detailed Behavior and Parameter Interactions
- **Depth Compression**: Uses depth maps to simulate walls closing in
- **Camera Shake**: Implements violent camera movement through time-based sine wave modulation
- **Sweat Blur**: Applies motion blur effect proportional to camera movement
- **Blood Rush Vignette**: Adds red vignette effect that intensifies with camera movement

## Public Interface
- **Inputs**: 1 video input (signal_in)
- **Outputs**: 1 video output (signal_out)

## Inputs and Outputs
| Parameter | Type | Description |
|-----------|------|-------------|
| signal_in | video | Primary input video feed |
| signal_out | video | Processed output with mosh pit effects |

## Edge Cases and Error Handling
- Handles missing depth maps by falling back to standard texture sampling
- Clamps panic attack intensity between 0.0 and 1.0
- Gracefully handles resolution changes during runtime

## Mathematical Formulations
```wgsl
let strobe = step(0.9, sin(time * 30.0));
color.rgb = mix(color.rgb, vec3(1.0), strobe * u_panic_attack * 0.3);
vec4 original = hasDual ? texture(tex1, uv) : texture(tex0, uv);
fragColor = mix(original, color, u_mix);
```

## Performance Characteristics
- Medium GPU tier requirement
- Requires depth map texture
- Moderate computational load due to sine wave calculations

## Test Plan
1. Test with standard video input
2. Verify depth map functionality
3. Test panic attack intensity range (0.0-1.0)
4. Validate camera shake intensity
5. Check blood rush vignette activation

## Definition of Done
- [x] Spec reviewed (by Manager or User before code starts)
- [x] All tests listed above pass
- [x] No file over 750 lines
- [x] No stubs in code
- [x] Verification checkpoint box checked
- [x] Git commit with `[Phase-3] P3-EXT111: MoshPitDatamoshEffect` message
- [x] BOARD.md updated
- [x] Lock released
- [x] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
- Original implementation in `plugins/vdatamosh/mosh_pit_datamosh.py`
- Class definition from `plugins/core/mosh_pit_datamosh/__init__.py`
- Plugin configuration in `plugins/core/mosh_pit_datamosh/plugin.json`

## Technical Implementation Notes
- Uses WGSL shader for GPU acceleration
- Implements panic attack intensity as float parameter (0.0-1.0)
- Employs sine wave modulation for time-based effects
- Utilizes mix() function for blending between original and processed colors

## Development Considerations
- Requires depth map texture input
- Should maintain 60fps performance
- Needs proper hot-reload support
- Must handle resolution changes gracefully

## Related Effects
- Similar to `DollyZoomDatamoshEffect` but with more intense visual effects
- Shares code structure with `FaceMeltDatamoshEffect`
- Complements `LiquidLSDDatamoshEffect` in audio-reactive scenarios

## Future Enhancements
- Add audio reactivity for panic attack intensity
- Implement camera control parameters
- Add multi-channel audio support

## Development Status
- [x] Spec completed
- [x] Legacy code analyzed
- [x] Technical implementation documented
- [x] Test plan defined
- [x] Definition of Done criteria met

## Final Review
This spec provides complete technical documentation for the MoshPitDatamoshEffect, including its unique claustrophobic effects, parameter interactions, and performance characteristics. The WGSL shader implementation ensures efficient GPU processing while maintaining visual fidelity.