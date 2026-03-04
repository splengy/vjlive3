# P3-EXT080_ForceType.md

# Spec Template — Focus on Technical Accuracy

## Task: P3-EXT080 — ForceType

### What This Module Does
Implements the ForceType system for 3D particle systems, defining standardized force categories and their mathematical behaviors. Enables consistent force application patterns across different particle effects.

### What This Module Does NOT Do
Does not handle particle rendering or system initialization. Focuses solely on force definition and application logic.

### Detailed Behavior and Parameter Interactions

#### ForceType Enum
```python
enum('ForceType'):
    ATTRACTION = 'attraction'  # Pulls particles toward a point
    REPULSION = 'repulsion'    # Pushes particles away from a point
    VORTEX = 'vortex'          # Spins particles around an axis
    TURBULENCE = 'turbulence'  # Random directional forces
    GRAVITY = 'gravity'        # Constant downward acceleration
    NOISE = 'noise'            # Perlin/noise-based random forces
```

#### Key Parameters
1. **strength** (float, 0.0-1.0): Force intensity
2. **radius** (float, 0.0-10.0): Influence radius
3. **frequency** (float, 0.0-10.0): Update frequency for dynamic forces
4. **direction** (np.ndarray): Custom force direction vector
5. **decay** (float, 0.0-1.0): Rate at which force diminishes over distance

#### Interaction with Particle System
- Applies forces to particles based on their position relative to force sources
- Supports multiple simultaneous forces
- Allows dynamic parameter changes during runtime
- Integrates with audio reactivity for parameter modulation

### Public Interface
```python
class Force:
    def __init__(self, force_type: ForceType, **kwargs):
        # Initialize with type and parameters

    def apply(self, particle_position: np.ndarray, particle_velocity: np.ndarray) -> np.ndarray:
        # Calculate and return force vector to apply to particle

    def update(self, dt: float):
        # Update dynamic parameters based on time delta

    def set_strength(self, strength: float):
        # Update force strength

    def set_radius(self, radius: float):
        # Update influence radius
```

### Inputs and Outputs
- **Inputs**: ForceType enum, parameter dictionary
- **Outputs**: Force vector to apply to particles

### Edge Cases and Error Handling
- Invalid ForceType values (fallback to NO_FORCE)
- Radius values outside valid range (clamped to 0.0-10.0)
- Strength values outside valid range (clamped to 0.0-1.0)
- Direction vector normalization errors (graceful degradation)

### Mathematical Formulations
- **Attraction**: `F = strength * (target_position - particle_position) / (distance + ε)`
- **Repulsion**: `F = strength * (particle_position - target_position) / (distance + ε)`
- **Vortex**: `F = strength * (direction × (particle_position - center)) / (distance² + ε)`
- **Turbulence**: `F = noise_function(particle_position, frequency) * strength`
- **Gravity**: `F = (0.0, -9.81, 0.0) * strength`

### Performance Characteristics
- O(1) per-force application cost
- O(n) total cost where n = number of active forces
- GPU-compatible when integrated with particle system
- Minimal memory overhead (stores only force parameters)

### Test Plan
1. Verify all ForceType variants produce expected force directions
2. Test parameter boundary conditions (strength, radius, frequency)
3. Validate mathematical formulations match expected behavior
4. Measure performance with 1000+ active forces
5. Test dynamic parameter updates during runtime
6. Validate audio reactivity integration

### Definition of Done
- [ ] Spec reviewed by Manager
- [ ] All test cases pass
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES
- particles_3d.py (AdvancedParticle3DSystem implementation)
- silver_visions.py (ForceType usage examples)
- core/effects/silver_visions.py (Particle system integration)
- core/generators/particles_3d.py (Force application logic)
