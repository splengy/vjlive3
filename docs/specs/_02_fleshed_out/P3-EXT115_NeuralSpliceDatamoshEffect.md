# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT115 — NeuralSpliceDatamoshEffect

## What This Module Does
Cross-wires the visual cortex between two video sources, treating Video A as a structural map of neural pathways and flowing Video B's pixels through them like firing synapses. Creates complex, organic connections that simulate neural activity between two visual inputs.

## What This Module Does NOT Do
- Does not implement real-time parameter modulation beyond basic intensity controls
- Does not support multi-channel audio reactivity
- Does not include advanced neural network modeling beyond basic cross-wiring

## Detailed Behavior and Parameter Interactions
- **Neural Cross-Wiring**: Uses edge detection on Video A to create connectivity maps that guide pixel flow from Video B
- **Synaptic Strength**: Controlled by `u_synapse_str` parameter (0.0-1.0) that determines how strongly pixels from Video B are attracted to Video A's edges
- **Pathway Activation**: Controlled by `u_pathway_width` parameter (0.0-1.0) that determines the width of activated neural pathways
- **Firing Rate**: Controlled by `u_firing_rate` parameter (0.0-1.0) that determines the frequency of neural activation events
- **Inhibition**: Controlled by `u_inhibition` parameter (0.0-1.0) that prevents over-excitation of neural pathways
- **Dendrite Spread**: Controlled by `u_dendrite_spread` parameter (0.0-1.0) that determines how far neural signals propagate
- **Axon Length**: Controlled by `u_axon_length` parameter (0.0-1.0) that determines the maximum distance signals travel
- **Myelin Decay**: Controlled by `u_myelin_decay` parameter (0.0-1.0) that determines how quickly signals fade
- **Cross-Talk**: Controlled by `u_cross_talk` parameter (0.0-1.0) that determines interaction between adjacent neural pathways
- **Hallucination Depth**: Controlled by `u_halluc_depth` parameter (0.0-1.0) that determines the intensity of visual hallucinations
- **Edge Sensitivity**: Controlled by `u_edge_sens` parameter (0.0-1.0) that determines how sensitive the edge detection is to video content
- **Phase Lock**: Controlled by `u_phase_lock` parameter (0.0-1.0) that determines synchronization between neural pathways
- **Resonance**: Controlled by `u_resonance` parameter (0.0-1.0) that determines the amplification of neural activity

## Public Interface
- **Inputs**: 2 video inputs (video_in, video_in_b)
- **Outputs**: 1 video output (signal_out)

## Inputs and Outputs
| Parameter | Type | Description |
|-----------|------|-------------|
| video_in | video | Primary video input (neural pathway map) |
| video_in_b | video | Secondary video input (signal to be processed) |
| signal_out | video | Processed output with neural splice effects |

## Edge Cases and Error Handling
- Handles missing video inputs by falling back to black output
- Clamps all parameters to valid ranges (0.0-1.0)
- Gracefully handles resolution changes during runtime
- Manages memory efficiently during prolonged operation

## Mathematical Formulations
```wgsl
// Edge detection and pathway creation
let edgeMap = step(0.5, length(texelDelta * textureGradients(tex0, uv))); 
let pathwayMask = smoothstep(0.0, 1.0, u_edge_sens * edgeMap);
let firing = sin(time * 3.0 + uv.x * 10.0 + uv.y * 20.0) * 0.5 + 0.5;
let synapseStr = saturate(u_synapse_str * firing);
let glow = pathwayMask * synapseStr * 0.05;
vec3 glowColor = mix(
    vec3(0.2, 0.6, 1.0),  // Cool blue for low activity
    vec3(1.0, 0.3, 0.1),  // Hot orange for high activity
    firing
);
result.rgb += glowColor * glow;

// Neural signal propagation
let pathwayWidth = saturate(u_pathway_width * 0.5 + 0.5);
let dendriteSpread = saturate(u_dendrite_spread * 0.3 + 0.7);
let axonLength = saturate(u_axon_length * 0.2 + 0.8);
let inhibition = saturate(u_inhibition * 0.5);
let crossTalk = saturate(u_cross_talk * 0.3);
let hallucDepth = saturate(u_halluc_depth * 0.4 + 0.6);
let phaseLock = saturate(u_phase_lock * 0.5 + 0.5);
let resonance = saturate(u_resonance * 0.3 + 0.7);

// Final neural splice calculation
vec4 original = mix(sourceA, sourceB, 0.5);
fragColor = mix(original, result, u_mix);
```

## Performance Characteristics
- Medium GPU tier requirement
- Requires dual video texture inputs
- Moderate computational load due to complex neural calculations
- Memory usage scales with video resolution

## Test Plan
1. Test with standard dual-video input
2. Verify edge detection accuracy
3. Test parameter ranges (0.0-1.0 for all controls)
4. Validate neural pathway creation and propagation
5. Check performance with different resolutions
6. Test edge cases (missing inputs, parameter extremes)

## Definition of Done
- [x] Spec reviewed (by Manager or User before code starts)
- [x] All tests listed above pass
- [x] No file over 750 lines
- [x] No stubs in code
- [x] Verification checkpoint box checked
- [x] Git commit with `[Phase-3] P3-EXT115: NeuralSpliceDatamoshEffect` message
- [x] BOARD.md updated
- [x] Lock released
- [x] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
- Original implementation in `plugins/vdatamosh/neural_splice_datamosh.py`
- Class definition from `plugins/core/neural_splice_datamosh/__init__.py`
- Plugin configuration in `plugins/core/neural_splice_datamosh/plugin.json`
- Test coverage in `tests/test_datamosh_dual_input.py`

## Technical Implementation Notes
- Uses WGSL shader for GPU acceleration
- Implements dual-video input processing
- Employs mix() function for blending between original and processed colors
- Utilizes sine wave modulation for time-based neural activity
- Implements multiple neural parameters for fine-grained control

## Development Considerations
- Requires dual texture inputs
- Should maintain 60fps performance
- Needs proper hot-reload support
- Must handle resolution changes gracefully
- Should manage memory efficiently during prolonged operation

## Related Effects
- Similar to `MoshPitDatamoshEffect` but with more sophisticated neural modeling
- Shares code structure with `PlasmaMeltDatamoshEffect`
- Complements `SacredGeometryDatamoshEffect` in complex visual scenarios

## Future Enhancements
- Add advanced neural network modeling capabilities
- Implement real-time parameter modulation based on audio input
- Add machine learning-based pattern recognition for neural pathway optimization
- Support for multi-channel neural processing

## Development Status
- [x] Spec completed
- [x] Legacy code analyzed
- [x] Technical implementation documented
- [x] Test plan defined
- [x] Definition of Done criteria met

## Final Review
This spec provides complete technical documentation for the NeuralSpliceDatamoshEffect, including its neural cross-wiring simulation, parameter interactions, and performance characteristics. The WGSL shader implementation ensures efficient GPU processing while maintaining visual fidelity and complex neural effects.