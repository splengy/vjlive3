# P3-EXT073_EmitterType.md

# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT073 — EmitterType

### What This Module Does
Implements the EmitterType system for 3D particle systems, defining standardized emitter configurations and behaviors. Enables consistent particle emission patterns across different effects.

### What This Module Does NOT Do
Does not handle particle physics calculations or rendering. Focuses solely on emitter configuration and initialization.

### Detailed Behavior and Parameter Interactions

#### EmitterType Enum
```python
enum('EmitterType'):
    SPHERE = 'sphere'  # Spherical emission pattern
    CIRCLE = 'circle'  # Circular emission in 2D plane
    LINE = 'line'      # Linear emission along a vector
    CUSTOM = 'custom'  # User-defined emission pattern
```

#### Key Parameters
1. **rate** (float): Particles emitted per second
2. **lifetime** (float): Particle lifespan in seconds
3. **position** (np.ndarray): 3D origin point
4. **color_range** (tuple): (start_color, end_color) for gradient
5. **emit_on_beat** (bool): Sync emission with audio beats

#### Interaction with Particle System
- Initializes emitters with specified parameters
- Maintains emitter state (active/inactive)
- Supports dynamic parameter changes during runtime

### Public Interface
```python
class Emitter:
    def __init__(self, emitter_type: EmitterType, **kwargs):
        # Initialize emitter with type and parameters

    def update(self, dt: float):
        # Update emitter state based on time delta

    def stop(self):
        # Stop emission

    def restart(self):
        # Restart emission with current parameters
```

### Inputs and Outputs
- **Inputs**: EmitterType enum, parameter dictionary
- **Outputs**: Active particle stream with defined characteristics

### Edge Cases and Error Handling
- Invalid parameter types (e.g., negative rate)
- Position outside valid space
- Color format mismatches

### Mathematical Formulations
- Particle velocity calculation: `v = (position - origin) * rate_factor`
- Lifetime decay: `remaining_life = max(0, initial_life - dt)`

### Performance Characteristics
- O(1) initialization cost
- O(n) update cost per frame (n = active emitters)
- GPU-accelerated when integrated with particle system

### Test Plan
1. Verify all EmitterType variants work as expected
2. Test parameter boundary conditions
3. Validate audio synchronization for emit_on_beat
4. Measure performance with 1000+ active emitters

### Definition of Done
- [ ] Spec reviewed by Manager
- [ ] All test cases pass
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
- silver_visions.py (Sphere emitter implementation)
- particles_3d.py (Basic emitter interface)
- silver_visions_node.py (Advanced emitter usage)
