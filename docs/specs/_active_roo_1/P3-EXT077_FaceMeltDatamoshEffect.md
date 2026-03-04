# P3-EXT077_FaceMeltDatamoshEffect.md

# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT077 — FaceMeltDatamoshEffect

### What This Module Does
Implements the FaceMeltDatamoshEffect for 3D particle systems, creating a self-dissolution effect that isolates the subject using depth and melts them downwards while keeping the background stable. Simulates the sensation of a face sliding off.

### What This Module Does NOT Do
Does not handle particle physics calculations or rendering. Focuses solely on the datamosh effect implementation.

### Detailed Behavior and Parameter Interactions

#### Core Functionality
- **Depth Isolation**: Uses depth information to isolate the subject from the background
- **Melting Effect**: Simulates viscous melting with customizable speed and viscosity
- **Audio Reactivity**: Supports audio-driven melting intensity
- **Chaos Mode**: Randomizes particle vectors on audio highs

#### Key Parameters
1. **melt_speed** (float, 0.0-1.0): Controls the speed of the melting effect
2. **viscosity** (float, 0.0-1.0): Determines the thickness of the melting material
3. **face_isolation** (float, 0.0-1.0): Strength of subject isolation from background
4. **audio_lock** (float, 0.0-1.0): Freezes frame on audio beats
5. **chaos** (float, 0.0-1.0): Randomizes particle vectors on audio highs

#### Interaction with Particle System
- Initializes with depth-based subject isolation
- Applies melting effect using depth information
- Syncs melting intensity with audio beats
- Randomizes particle vectors during chaos mode

### Public Interface
```python
class FaceMeltDatamoshEffect(Effect):
    def __init__(self, **kwargs):
        # Initialize with parameters from kwargs

    def update(self, dt: float):
        # Update melting effect based on time delta

    def apply_audio_reactivity(self, audio_data):
        # Process audio data for reactivity

    def enable_chaos_mode(self, chaos_level: float):
        # Activate chaos mode with specified intensity
```

### Inputs and Outputs
- **Inputs**: Audio data, depth map, parameter values
- **Outputs**: Processed video with datamosh effect

### Edge Cases and Error Handling
- Invalid parameter ranges (e.g., negative values)
- Missing depth map input
- Audio data format mismatches

### Mathematical Formulations
- Melting intensity calculation: `intensity = melt_speed * (1 - viscosity)`
- Audio reactivity: `reactivity = audio_amplitude * chaos_level`
- Depth isolation: `isolation = face_isolation * (1 - depth_value)`

### Performance Characteristics
- O(1) initialization cost
- O(n) update cost per frame (n = active particles)
- GPU-accelerated when integrated with particle system

### Test Plan
1. Verify all parameters work within 0.0-1.0 range
2. Test audio reactivity with different music types
3. Validate chaos mode randomization
4. Measure performance with 1000+ active particles

### Definition of Done
- [ ] Spec reviewed by Manager
- [ ] All test cases pass
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
- face_melt_datamosh.py (Original implementation)
- plugin.json (Parameter definitions)
- node_datamosh.py (Effect registration)
