# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT004_agent_avatar.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task. 

## Description
The AgentAvatarEffect module visualizes an agent's internal emotional and cognitive state through a reactive geometric avatar that appears in a multi-screen display environment. The avatar serves as a visual metaphor for the agent's current state, reacting to changes in confidence, emotional intensity, and cognitive load. Users will perceive the avatar through its dynamic shape, color, and movement patterns, gaining an intuitive understanding of the agent's internal state without requiring explicit UI elements. The effect leverages real-time shader computations to create a compelling visual representation that integrates with the existing node-based architecture.

**What This Module Does**
- Renders a geometric avatar that reflects agent emotional states:
  - Thinking state: Rapid spinning animation
  - Confident state: Stable bright white glow
  - Overwhelmed state: Fragmentation into particles
- Implements Shadow Mode using IR heat detection to control avatar visibility
- Implements Eye Tracking that adjusts avatar gaze based on detected face position
- Updates avatar parameters (confidence, glow intensity, position) based on global state signals
- Manages shader uniforms for position, scale, and alpha calculations

**What This Module Does NOT Do**
- Does NOT handle file I/O or persistence operations
- Does NOT process audio input directly
- Does NOT manage node graph connections or traversal
- Does NOT provide real-time audio-visual synchronization beyond visual parameters

**Detailed Behavior**
- Accepts parameters: confidence (0.0-1.0), glow intensity (0.0-0.5), and position coordinates
- Color calculation combines glow color with confidence-based brightness adjustments
- Visibility is determined by node viewport position (local_pos >= 0.0)
- Uses AVATAR_FRAGMENT_SHADER with position, scale, and alpha parameters
- Integrates with SyncManager for global state access
- Applies shadow masking based on IR data when shadow mode is enabled
- Implements gaze tracking that smoothly follows detected facial positions

**Legacy Context**
- Original implementation used Surface IR data for shadow mode and eye tracking
- Shader code contained fragment calculations for core shape and glow effects
- Parameters were mapped from global state through sync_manager
- Cross-platform considerations: Windows IR support vs Linux OpenGL/Vulkan alternatives

**[NEEDS RESEARCH] OpenGL.GL fallback**
## OpenGL.GL Fallback
- Original implementation used SurfaceIRSource for Windows IR data
- Current implementation uses OpenGL.GL for texture binding
- Fallback strategy: Use OpenGL ES 3.2 on ARM devices

**[NEEDS RESEARCH] Audio band mapping**
## Audio Band Mapping
- Legacy code mapped 8 frequency bands to particle trails
- Current implementation uses dynamic band count (typically 3-8 bands)
- Audio analyzer integration: expects `u_audio_level` (RMS 0.0-1.0), `u_bass`, `u_mid`, `u_high` uniforms
- Band ranges: bass (20-250Hz), mid (250-4000Hz), high (4000-20000Hz)
- Validation: ensure audio analyzer provides normalized values in [0.0, 1.0] range

**[NEEDS RESEARCH] Shader compilation**
## Shader Compilation
- VJLive3 uses custom shader compiler with GLSL 330 core compatibility
- Uniform binding: expects `uniform` declarations for all parameters
- GPU acceleration: required for real-time performance, fallback to CPU rendering not supported
- Shader validation: checks for disallowed variables (e.g., `gl_PointSize`)
- Compilation errors: shader program linking failures are common with complex effects

**[NEEDS RESEARCH] Audio parameter validation**
## Audio Parameter Validation
- Legacy code used strict type checking for audio parameters
- Current implementation uses runtime validation with graceful degradation
- Audio parameter ranges: RMS level [0.0, 1.0], frequency bands [0.0, 1.0]
- Default color schemes: Neon (#00FFFF) for Confident state, Cipher (#FF00FF) for Overwhelmed state
- Validation: ensure audio analyzer provides normalized values, handle missing bands gracefully

**[NEEDS RESEARCH] Video processing**
## Video Processing
- Legacy system used point cloud rendering for avatar visualization
- Current implementation uses GPU-accelerated shaders with continuous math model
- Rendering pipeline: vertex shader → fragment shader → alpha blending
- Frame processing: real-time at 60fps target, supports variable frame rates
- Quantum state transitions: smooth interpolation between emotional states using continuous math
- Performance optimization: level-of-detail rendering based on avatar scale and distance

**Integration Notes**
## Integration
- Requires connection to SyncManager for global state access
- Node_id determines local position calculation within the node graph
- Shader uniforms must be updated in apply_uniforms() method
- Compatible with both TravelingAvatarEffect and legacy AgentAvatarEffect implementations
- Should integrate with existing effect chain for seamless visual transitions

**Performance Notes**
- GPU-intensive due to real-time position calculations and shader execution
- Memory usage scales with number of active nodes and avatar instances
- Shader complexity impacts frame rate performance, requiring optimization for target platforms
- Cross-platform performance profile: OpenGL baseline, OpenGL ES 3.2 for ARM, Vulkan for enhanced performance, CUDA/TensorRT for NVIDIA GPUs
- Memory optimization strategies: shared shader programs, texture reuse, level-of-detail techniques

**Test Plan**
| Test Name | What It Verifies |
|-----------|------------------|
| test_init_no_sync_manager | Module initializes correctly when sync_manager is None or missing |
| test_update_from_global_state | Avatar parameters update properly based on global state and position |
| test_apply_uniforms | Shader uniforms are set with correct avatar values |
| test_visibility_on_node | Avatar appears only when within node viewport (local_pos >= 0.0) |
| test_visibility_off_node | Avatar is invisible when outside node viewport |
| test_shadow_mode | Avatar appears only where IR heat is detected |
| test_eye_tracking | Avatar gaze follows detected face position |
| test_emotional_states | Avatar reacts to different emotional states |
| test_edge_cases | Handles boundary conditions like zero confidence, maximum glow intensity, and edge case position values |

**Edge Case Considerations**
- Zero confidence values should maintain avatar visibility but with minimal glow
- Maximum glow intensity should not cause visual artifacts
- Position values at exact boundary (local_pos = 0.0) should be handled consistently
- IR data absence should gracefully degrade shadow mode functionality
- Face detection loss should trigger appropriate fallback behavior

**Minimum coverage:** 80% before task is marked done.

**Definition of Done**
- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT004: agent_avatar` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written