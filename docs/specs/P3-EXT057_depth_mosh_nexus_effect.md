# P3-EXT057: Depth Mosh Nexus Effect

## What This Module Does
Creates a central "nexus" for depth-based mosh effects that combines multiple datamosh and distortion techniques into a unified, highly configurable effect. The nexus acts as a hub that routes depth information to various processing modules and combines their outputs in complex ways. Produces intense, chaotic visual effects suitable for high-energy performances.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthMoshNexus",
    "version": "3.0.0",
    "description": "Central hub for depth mosh effects",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "datamosh",
    "tags": ["depth", "mosh", "nexus", "chaos", "intense"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `active_effects: list[str]` (default: ["datamosh", "distortion", "color_shift"]) - Effects to include in nexus
- `effect_intensities: dict` (default: {}) - Individual effect strengths
- `depth_routing: str` (default: "parallel", options: ["parallel", "serial", "selective"]) - How effects process depth
- `routing_thresholds: dict` (default: {}) - Depth thresholds for selective routing
- `mix_mode: str` (default: "additive", options: ["additive", "multiply", "screen", "max"]) - Output mixing
- `chaos_factor: float` (default: 0.5, min: 0.0, max: 1.0) - Randomness and unpredictability
- `temporal_coherence: float` (default: 0.8, min: 0.0, max: 1.0) - Smoothness over time
- `output_clamp: bool` (default: True) - Clamp final output to valid range

### Available Effects
- `datamosh`: Block-based corruption
- `distortion`: Geometric warping
- `color_shift`: Chromatic aberration
- `edge_enhance`: Depth edge emphasis
- `feedback`: Temporal feedback loop
- `noise_inject`: Add depth-modulated noise

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `previous_frame: Frame` (optional) - Previous output for feedback effects
- `timestamp: float` (optional) - Current time for animation

### Outputs
- `video: Frame` (same format as input) - Intensely moshed video

## What It Does NOT Do
- Does NOT support infinite effect combinations (limited to available modules)
- Does NOT perform automatic effect optimization based on content
- Does NOT include preset management (all parameters manual)
- Does NOT handle HDR metadata preservation
- Does NOT support custom effect development at runtime
- Does NOT include safety limits beyond temporal_coherence

## Test Plan
1. Unit tests for each effect module
2. Verify depth routing logic works correctly
3. Test mix_mode variations
4. Performance: ≥ 60 FPS at 1080p with 4 active effects
5. Memory: < 300MB additional RAM (multiple effect buffers)
6. Visual: verify nexus produces intense, chaotic output

## Implementation Notes
- Implement each effect as a separate module with standardized interface
- For parallel routing: apply all active effects independently, then mix
- For serial routing: apply effects in order, each receives previous output
- For selective routing: use depth thresholds to determine which effects activate per-pixel
- Use effect_intensities to scale each effect's contribution
- Apply chaos_factor as random modulation of parameters or outputs
- Use temporal_coherence to smooth parameter changes over time
- Clamp output if output_clamp=True
- Optimize with shared buffers and minimal copying between effects
- Follow SAFETY_RAILS: validate effect names, handle parameter errors

## Deliverables
- `src/vjlive3/effects/depth_mosh_nexus.py`
- `tests/effects/test_depth_mosh_nexus.py`
- `docs/plugins/depth_mosh_nexus.md`
- Effect modules: `src/vjlive3/effects/nexus_modules/`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] All effects combine correctly
- [x] Depth routing functions as expected
- [x] 60 FPS at 1080p with 4 effects
- [x] Test coverage ≥ 80%
- [x] No safety rail violations