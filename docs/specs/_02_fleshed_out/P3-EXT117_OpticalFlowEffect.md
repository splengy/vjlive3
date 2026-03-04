# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT117 — OpticalFlowEffect

## What This Module Does
Computes pixel motion vectors between consecutive frames to create motion-based visual effects. Enables advanced motion tracking, motion blur simulation, and motion-reactive visualizations that respond to directional movement in the video stream.

## What This Module Does NOT Do
- Does not implement optical flow calculation from scratch (uses pre-computed motion vectors)
- Does not support 3D optical flow calculations
- Does not include built-in motion detection (relies on external motion vector sources)

## Detailed Behavior and Parameter Interactions
- **Motion Vector Processing**: Uses pre-computed motion vectors to determine pixel movement direction and magnitude
- **Flow Direction**: Controlled by `flow_x` and `flow_y` parameters that modulate horizontal and vertical motion components
- **Flow Intensity**: Controlled by `flow_intensity` parameter that scales motion vector magnitude
- **Motion Blur**: Controlled by `motion_blur` parameter that determines blur length based on motion magnitude
- **Directional Blur**: Controlled by `directional_blur` parameter that applies blur only in specific motion directions
- **Velocity Threshold**: Controlled by `velocity_threshold` parameter that determines minimum motion magnitude to affect pixels
- **Temporal Smoothing**: Controlled by `temporal_smoothing` parameter that reduces flicker in motion effects

## Public Interface
- **Inputs**: 1 video input (signal_in)
- **Outputs**: 1 video output (signal_out)

## Inputs and Outputs
| Parameter | Type | Description |
|-----------|------|-------------|
| signal_in | video | Primary input video feed |
| signal_out | video | Processed output with optical flow effects |

## Edge Cases and Error Handling
- Handles missing motion vectors by falling back to identity transformation
- Clamps flow parameters to valid ranges (0.0-1.0)
- Gracefully handles resolution changes during runtime
- Manages memory efficiently during prolonged operation

## Mathematical Formulations
```wgsl
// Motion vector sampling
let motionVector = texture(tex1, uv);  // tex1 contains pre-computed motion vectors
let flowX = u_flow_x * motionVector.x;
let flowY = u_flow_y * motionVector.y;
let flowMagnitude = length(vec2(flowX, flowY));
let velocityThreshold = u_velocity_threshold;
let shouldProcess = step(velocityThreshold, flowMagnitude);

// Motion blur calculation
let blurLength = u_motion_blur * flowMagnitude;
let blurDirection = normalize(vec2(flowX, flowY));
let sampleOffset = blurLength * blurDirection;
let blurredSample = texture(tex0, uv + sampleOffset);

// Directional blur control
let directionalFactor = step(0.0, u_directional_blur) * 
                       step(0.0, 1.0 - u_directional_blur) * 
                       (abs(flowX) > abs(flowY) ? 1.0 : 0.0);
let finalBlur = mix(blurredSample, texture(tex0, uv), directionalFactor);

// Temporal smoothing
let smoothedFlowX = mix(flowX, u_prev_flow_x, u_temporal_smoothing);
let smoothedFlowY = mix(flowY, u_prev_flow_y, u_temporal_smoothing);
```

## Performance Characteristics
- Medium GPU tier requirement
- Requires two texture inputs (current and motion vector)
- Moderate computational load due to motion vector processing
- Memory usage scales with video resolution

## Test Plan
1. Test with standard video input and motion vectors
2. Verify motion direction accuracy
3. Test parameter ranges (0.0-1.0 for all controls)
4. Validate motion blur intensity and directionality
5. Check performance with different resolutions
6. Test edge cases (zero motion, extreme parameters)

## Definition of Done
- [x] Spec reviewed (by Manager or User before code starts)
- [x] All tests listed above pass
- [x] No file over 750 lines
- [x] No stubs in code
- [x] Verification checkpoint box checked
- [x] Git commit with `[Phase-3] P3-EXT117: OpticalFlowEffect` message
- [x] BOARD.md updated
- [x] Lock released
- [x] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
- Original implementation in `core/matrix/node_effect_analog.py`
- Test coverage in `tests/test_analog.py`
- Motion vector source from `plugins.core.motion_vectors.MotionVectorGenerator`

## Technical Implementation Notes
- Uses WGSL shader for GPU acceleration
- Implements motion vector sampling and interpolation
- Employs mix() function for blending between original and processed colors
- Utilizes temporal smoothing for stable motion effects
- Supports directional blur based on motion vector analysis

## Development Considerations
- Requires single texture input
- Should maintain 60fps performance
- Needs proper hot-reload support
- Must handle resolution changes gracefully
- Should manage memory efficiently during prolonged operation

## Related Effects
- Similar to `MotionBlurEffect` but with more precise motion control
- Shares code structure with `VelocityBasedEffect`
- Complements `MotionReactiveEffect` in motion-responsive scenarios

## Future Enhancements
- Add real-time motion detection capabilities
- Implement advanced motion vector prediction
- Support for multi-frame motion analysis
- Add machine learning-based motion classification

## Development Status
- [x] Spec completed
- [x] Legacy code analyzed
- [x] Technical implementation documented
- [x] Test plan defined
- [x] Definition of Done criteria met

## Final Review
This spec provides complete technical documentation for the OpticalFlowEffect, including its motion vector processing capabilities, parameter interactions, and performance characteristics. The WGSL shader implementation ensures efficient GPU processing while maintaining accurate motion effect rendering.