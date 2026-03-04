# P3-EXT083_FrameHoldEffect.md

# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT083 — FrameHoldEffect

### What This Module Does
Implements a frame holding effect that randomly freezes video frames to simulate dropped I-frames or create rhythmic visual stutters. This effect can be used for creative purposes like simulating analog TV signal loss, creating rhythmic visual patterns, or adding intentional glitch artifacts to video output.

### What This Module Does NOT Do
Does not perform any video processing beyond frame selection. Does not handle audio synchronization directly (though it can be combined with audio-reactive effects). Does not modify pixel data - only selects between current and previous frames.

### Detailed Behavior and Parameter Interactions

#### Core Functionality
- **Frame Selection**: Chooses between current frame and previous frame based on probability
- **Random Frame Holding**: Uses a random chance mechanism to determine when to hold a frame
- **Feedback Control**: Allows adjustment of how long held frames persist
- **Temporal Stability**: Maintains frame consistency until a new frame is selected

#### Key Parameters
1. **holdChance** (float, 0.0-1.0): Probability of holding the previous frame instead of displaying the current frame
2. **feedback_amount** (float, 0.0-1.0): Controls how much of the previous frame persists in the mix
3. **delay** (float, 0.0-10.0): Optional frame delay in seconds before processing
4. **rand_seed** (int, 0-10000): Seed for random number generator to ensure reproducible sequences

#### Interaction with Video Pipeline
- Operates as a post-process effect that takes current and previous frames as input
- Outputs either the current frame or held previous frame based on holdChance
- Can be chained with other effects for complex glitch patterns
- Maintains temporal coherence when holding frames

### Public Interface
```python
class FrameHoldEffect(Effect):
    def __init__(self):
        # Initialize with default parameters
        # Set up shader program and frame buffers

    def update(self, dt: float):
        # Update frame timing and random number generator state

    def apply(self, current_frame: int, previous_frame: int, extra_textures: list = None) -> int:
        # Apply frame holding logic and return processed frame texture

    def set_parameter(self, name: str, value: float):
        # Update a specific parameter value

    def set_random_seed(self, seed: int):
        # Set random number generator seed for reproducible sequences
```

### Inputs and Outputs
- **Inputs**: 
  - Current video frame texture
  - Previous video frame texture  
  - Optional parameters and textures
- **Outputs**: 
  - Processed video texture (either current frame or held previous frame)

### Edge Cases and Error Handling
- Invalid parameter values (clamped to valid ranges)
- Missing previous frame buffer (graceful degradation to current frame only)
- Shader compilation failures (fallback to basic frame output)
- Texture sampling errors (handled with texture fallback mechanisms)

### Mathematical Formulations
- **Frame Selection**: `result = rand < holdChance ? previous : current`
- **Feedback Mix**: `final = mix(current, result, clamp(feedback_amount, 0.0, 1.0))`
- **Random Generation**: `rand = noise(time * 0.1 + rand_seed) * 2.0 - 1.0` (range -1 to 1)
- **Hold Duration**: Controlled by feedback_amount and holdChance combination

### Performance Characteristics
- **GPU-Bound**: Entirely shader-based with minimal computational overhead
- **Memory**: ~2 additional frame buffers (current and previous)
- **Resolution Dependent**: O(N) where N = pixel count
- **Typical Performance**: 100+ FPS at 1080p on mid-range GPU
- **Multi-pass**: Requires 1-2 render passes per frame

### Test Plan
1. Verify frame holding probability matches expected values
2. Test parameter clamping behavior for all parameters
3. Validate random sequence reproducibility with fixed seeds
4. Test chaining with other effects (datamosh, pixel_sort, etc.)
5. Measure performance at various resolutions (720p, 1080p, 4K)
6. Validate edge case handling (missing previous frame, shader errors)
7. Test feedback_amount modulation effects

### Definition of Done
- [ ] Spec reviewed by Manager
- [ ] All test cases pass
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
- core/effects/legacy_trash/datamosh.py (FrameHoldEffect implementation)
- test_results/coverage/z_536b96d659618960_node_vcore_py.html (Test coverage)
- verify_atomic_plugins.py (Plugin verification)
- core/effects/shader_base.py (Base Effect class)
- core/effects/legacy_trash/datamosh.py (Parameter definitions and export)
