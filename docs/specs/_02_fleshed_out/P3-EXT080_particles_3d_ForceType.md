# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT080 — particles_3d_ForceType

**Phase:** Phase 3 / P3-EXT
**Assigned To:** Desktop Roo Worker
**Spec Written By:** Desktop Roo Worker
**Date:** 2026-03-01

---

## What This Module Does

The `particles_3d_ForceType` module provides a comprehensive system for applying various force types to 3D particle systems. It enables real-time manipulation of particle behavior through configurable force fields including gravity, turbulence, vortex, attraction/repulsion, and custom mathematical functions. The module supports both CPU and GPU acceleration for optimal performance across different hardware configurations.

## What It Does NOT Do

- Handle particle rendering or visual effects
- Manage particle system lifecycle or memory allocation
- Provide physics simulation beyond force application
- Implement collision detection or spatial partitioning
- Support non-3D particle systems or 2D particle effects

## Public Interface
```python
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass

@dataclass
class ForceParameters:
    strength: float
    falloff: float
    noise_scale: float
    noise_amplitude: float
    frequency: float
    octaves: int
    persistence: float
    lacunarity: float

class ForceType:
    def __init__(self, force_type: str, parameters: ForceParameters) -> None:
        """
        Initialize a force type with specific parameters.
        
        Args:
            force_type: Type of force to apply (gravity, turbulence, vortex, etc.)
            parameters: Configuration parameters for the force
        """
        pass
    
    def apply_force(
        self, 
        particles: np.ndarray,  # (N, 3) particle positions
        velocities: np.ndarray, # (N, 3) particle velocities
        time: float
    ) -> np.ndarray:
        """
        Apply the force to particle velocities.
        
        Args:
            particles: Current particle positions (N x 3 array)
            velocities: Current particle velocities (N x 3 array)
            time: Current simulation time
            
        Returns:
            Updated velocities with force applied
        """
        pass

class ForceSystem:
    def __init__(self, max_particles: int = 100000) -> None:
        """
        Initialize the force system with particle capacity.
        
        Args:
            max_particles: Maximum number of particles to support
        """
        pass
    
    def add_force(self, force: ForceType) -> int:
        """
        Add a force to the system.
        
        Args:
            force: ForceType instance to add
            
        Returns:
            Index of the added force
        """
        pass
    
    def remove_force(self, force_id: int) -> bool:
        """
        Remove a force from the system.
        
        Args:
            force_id: Index of force to remove
            
        Returns:
            True if removed, False if not found
        """
        pass
    
    def update_forces(
        self, 
        particles: np.ndarray,  # (N, 3) particle positions
        velocities: np.ndarray, # (N, 3) particle velocities
        time: float
    ) -> np.ndarray:
        """
        Update all forces and apply to particle velocities.
        
        Args:
            particles: Current particle positions (N x 3 array)
            velocities: Current particle velocities (N x 3 array)
            time: Current simulation time
            
        Returns:
            Updated velocities with all forces applied
        """
        pass
    
    def set_force_parameters(
        self, 
        force_id: int, 
        parameters: ForceParameters
    ) -> bool:
        """
        Update parameters for a specific force.
        
        Args:
            force_id: Index of force to update
            parameters: New parameters to apply
            
        Returns:
            True if updated, False if force_id not found
        """
        pass
```

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `particles` | `np.ndarray` | Particle positions (N x 3) | N >= 0, float32 |
| `velocities` | `np.ndarray` | Particle velocities (N x 3) | N >= 0, float32 |
| `time` | `float` | Current simulation time | >= 0.0 |
| `force_type` | `str` | Type of force to apply | One of: gravity, turbulence, vortex, attraction, repulsion, custom |
| `parameters` | `ForceParameters` | Force configuration | See parameter constraints |

## Edge Cases and Error Handling

- **Empty particle system**: Return velocities unchanged when N = 0
- **Invalid force type**: Raise ValueError with descriptive message
- **Parameter out of range**: Clamp values to valid ranges or raise ValueError
- **Memory overflow**: Raise MemoryError if particle count exceeds system limits
- **NaN/Inf values**: Detect and handle invalid numerical inputs gracefully
- **Performance degradation**: Implement adaptive quality based on frame rate

## Mathematical Implementation Details

### Gravity Force
```python
# F = m * g
force = np.array([0.0, -9.81, 0.0]) * parameters.strength
```

### Turbulence Force (Perlin Noise)
```python
# Generate 3D Perlin noise for turbulence
noise = perlin_noise_3d(
    particles * parameters.noise_scale,
    time * parameters.frequency,
    octaves=parameters.octaves,
    persistence=parameters.persistence,
    lacunarity=parameters.lacunarity
)
force = noise * parameters.noise_amplitude
```

### Vortex Force
```python
# Create rotational force around axis
axis = np.array([0.0, 1.0, 0.0])  # Y-axis
radius = np.linalg.norm(particles, axis=1)
center = np.mean(particles, axis=0)

# Calculate tangential direction
tangent = np.cross(particles - center, axis)
tangent /= np.linalg.norm(tangent, axis=1, keepdims=True) + 1e-8

# Apply vortex force with falloff
force = tangent * parameters.strength * (1.0 / (radius + 1e-8))**parameters.falloff
```

### Attraction/Repulsion Force
```python
# Calculate distance vectors
center = np.mean(particles, axis=0)
distance = particles - center
magnitude = np.linalg.norm(distance, axis=1, keepdims=True)

# Normalize and apply force
normalized = distance / (magnitude + 1e-8)
force = normalized * parameters.strength * (1.0 / (magnitude + 1e-8))**parameters.falloff

# Invert for repulsion
if force_type == 'repulsion':
    force = -force
```

## Performance Characteristics

- **CPU Implementation**: O(N) per force type, where N is particle count
- **GPU Implementation**: O(N) with parallel processing, supports up to 1M particles
- **Memory Usage**: ~24 bytes per particle (position + velocity + temporary calculations)
- **Frame Rate**: Target 60fps at 1080p resolution with 100K particles
- **Batch Processing**: Process particles in chunks of 10K for memory efficiency

## Dependencies

```python
import numpy as np
from typing import Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
import math

# Optional GPU acceleration
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
```

## Test Plan

### Unit Tests
- Test force calculations with known inputs and expected outputs
- Verify parameter validation and error handling
- Test edge cases (empty arrays, extreme values, NaN inputs)
- Validate mathematical correctness of force implementations

### Integration Tests
- Test force system with multiple concurrent forces
- Verify performance with varying particle counts
- Test GPU vs CPU implementations for correctness
- Validate real-time performance targets

### Performance Tests
- Benchmark force application at different particle counts
- Measure memory usage and identify optimization opportunities
- Test frame rate stability under load
- Compare CPU vs GPU performance

### Stress Tests
- Test with maximum particle count
- Verify behavior with rapid parameter changes
- Test memory leak prevention
- Validate thread safety for concurrent access

## Definition of Done

- All force types implemented with correct mathematical behavior
- Error handling covers all edge cases
- Performance targets met for target hardware
- Documentation complete with usage examples
- Test coverage exceeds 95%
- GPU acceleration available when hardware permits

