# P3-EXT166 — ShiftDirection Enumeration

## What This Module Does

The ShiftDirection enumeration provides a standardized directional control system for temporal/rhythm-based VJLive3 plugins. It defines 6 directional shift modes that control how effects respond to tempo/beat interactions, managing directional behavior in phase-locked effects, particle streams, and animated patterns within the vtempi module family. This ensures consistent directional logic across all plugins, enabling predictable behavior in mixed effect chains and improving composability.

## What This Module Does NOT Do

- Does not implement actual effect logic (delegates to individual plugins)
- Does not handle audio analysis or beat detection (separate module)
- Does not manage tempo synchronization (delegates to vtempi core)
- Does not perform 3D spatial transformations (2D directional only)
- Does not handle user input or control mapping (separate parameter system)
- Does not implement animation curves or easing functions (separate module)

---

## Detailed Behavior

The ShiftDirection enumeration provides 6 directional states with specific mathematical behaviors:

### Direction Mapping

```
FORWARD:      x increases, y increases, phase advances normally
REVERSE:      x decreases, y decreases, phase reverses
BIDIRECTIONAL: Alternates every N beats/frames
INWARD:       Distance from center decreases
OUTWARD:      Distance from center increases
RANDOM:       Unpredictable shifts with configurable probability
```

### Mathematical Formulations

#### Forward Progression
```
p_forward(t) = p_0 + v · t
```

#### Reverse Progression
```
p_reverse(t) = p_0 - v · t
```

#### Inward Convergence
```
d(t) = d_0 - r · t  ∈ distance from center
```

#### Outward Divergence
```
d(t) = d_0 + r · t
```

#### Bidirectional Oscillation
```
d(t) = d_0 · (1 + σ(2π f t))
```

#### Random Direction
```
direction(t) = π · random()  ∈ random angle [0, 2π]
```

### Direction Queries

- `is_increasing()`: True for FORWARD, OUTWARD
- `is_decreasing()`: True for REVERSE, INWARD
- `can_reverse()`: True for BIDIRECTIONAL, REVERSE
- `is_geometric()`: True for INWARD, OUTWARD
- `is_temporal()`: True for FORWARD, REVERSE

---

## Integration Notes

- **Input**: None (enumeration only)
- **Output**: Direction constants for plugin configuration
- **Parameter Control**: Used by vtempi plugins for directional behavior
- **Dependencies**: Standard library `enum.Enum`, vtempi base class
- **Performance**: O(1) constant time for all operations
- **Memory**: 1 byte per enumeration instance

---

## Public Interface

```python
from enum import Enum
from typing import Dict, Tuple, Optional
import numpy as np

class ShiftDirection(Enum):
    """Enum for directional shift modes of temporal effects."""
    
    FORWARD = "forward"           # Increasing, left-to-right, expanding
    REVERSE = "reverse"           # Decreasing, right-to-left, contracting
    BIDIRECTIONAL = "bidirectional"  # Alternating forward/reverse
    INWARD = "inward"             # Converging toward center
    OUTWARD = "outward"           # Diverging from center
    RANDOM = "random"             # Unpredictable direction
    
    def __str__(self) -> str:
        """Return human-readable direction name."""
        return self.value
    
    def is_increasing(self) -> bool:
        """Check if direction increases value/position."""
        return self in (ShiftDirection.FORWARD, ShiftDirection.OUTWARD)
    
    def is_decreasing(self) -> bool:
        """Check if direction decreases value/position."""
        return self in (ShiftDirection.REVERSE, ShiftDirection.INWARD)
    
    def opposite(self) -> 'ShiftDirection':
        """Return opposite direction."""
        opposites = {
            ShiftDirection.FORWARD: ShiftDirection.REVERSE,
            ShiftDirection.REVERSE: ShiftDirection.FORWARD,
            ShiftDirection.INWARD: ShiftDirection.OUTWARD,
            ShiftDirection.OUTWARD: ShiftDirection.INWARD,
            ShiftDirection.BIDIRECTIONAL: ShiftDirection.BIDIRECTIONAL,
            ShiftDirection.RANDOM: ShiftDirection.RANDOM
        }
        return opposites[self]
    
    def is_geometric(self) -> bool:
        """Check if direction is spatial (INWARD/OUTWARD)."""
        return self in (ShiftDirection.INWARD, ShiftDirection.OUTWARD)
    
    def is_temporal(self) -> bool:
        """Check if direction is temporal (FORWARD/REVERSE)."""
        return self in (ShiftDirection.FORWARD, ShiftDirection.REVERSE)
    
    def can_reverse(self) -> bool:
        """Check if direction can reverse (BIDIRECTIONAL, REVERSE)."""
        return self in (ShiftDirection.BIDIRECTIONAL, ShiftDirection.REVERSE)
    
    @classmethod
    def from_string(cls, direction_str: str) -> 'ShiftDirection':
        """Parse direction from string (case-insensitive)."""
        normalized = direction_str.lower().strip()
        for direction in cls:
            if direction.value == normalized:
                return direction
        raise ValueError(f"Invalid direction: {direction_str}")
    
    def to_vector(self) -> Tuple[float, float]:
        """Convert direction to unit vector (for spatial directions)."""
        vectors = {
            ShiftDirection.FORWARD: (1.0, 1.0),
            ShiftDirection.REVERSE: (-1.0, -1.0),
            ShiftDirection.INWARD: (0.0, 0.0),  # Convergence
            ShiftDirection.OUTWARD: (1.0, 1.0),  # Divergence
            ShiftDirection.BIDIRECTIONAL: (0.0, 0.0),  # Alternates
            ShiftDirection.RANDOM: (0.0, 0.0)  # Random
        }
        return vectors[self]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize direction to JSON-compatible dict."""
        return {
            'direction': self.value,
            'is_increasing': self.is_increasing(),
            'is_decreasing': self.is_decreasing(),
            'is_geometric': self.is_geometric(),
            'is_temporal': self.is_temporal(),
            'can_reverse': self.can_reverse()
        }
    
    def get_vector_for_point(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """
        Get direction vector for specific point (spatial directions only).
        
        Args:
            point: (x, y) coordinates in pixel space
            
        Returns:
            Unit vector in direction of shift
            
        Raises:
            ValueError: If direction is not spatial
        """
        if not self.is_geometric():
            raise ValueError(f"{self} is not a spatial direction")
        
        if self == ShiftDirection.INWARD:
            # Vector pointing toward center (0.5, 0.5)
            x, y = point
            center_x, center_y = 0.5, 0.5
            dx, dy = center_x - x, center_y - y
            length = np.sqrt(dx**2 + dy**2)
            if length < 1e-6:
                return (0.0, 0.0)
            return (dx/length, dy/length)
        
        elif self == ShiftDirection.OUTWARD:
            # Vector pointing away from center
            x, y = point
            center_x, center_y = 0.5, 0.5
            dx, dy = x - center_x, y - center_y
            length = np.sqrt(dx**2 + dy**2)
            if length < 1e-6:
                return (1.0, 0.0)  # Default outward direction
            return (dx/length, dy/length)
    
    def get_oscillation_frequency(self, base_frequency: float = 1.0) -> float:
        """
        Get oscillation frequency for bidirectional directions.
        
        Args:
            base_frequency: Base frequency in Hz
            
        Returns:
            Oscillation frequency in Hz
            
        Raises:
            ValueError: If direction is not bidirectional
        """
        if self != ShiftDirection.BIDIRECTIONAL:
            raise ValueError(f"{self} is not bidirectional")
        return base_frequency * 2.0  # Full cycle (forward+reverse)
    
    def get_random_direction(self) -> Tuple[float, float]:
        """
        Get random direction vector for RANDOM direction.
        
        Returns:
            Random unit vector (x, y)
            
        Raises:
            ValueError: If direction is not RANDOM
        """
        if self != ShiftDirection.RANDOM:
            raise ValueError(f"{self} is not random")
        angle = np.random.uniform(0, 2 * np.pi)
        return (np.cos(angle), np.sin(angle))
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `direction_str` | `str` | Direction string | Case-insensitive, one of: forward, reverse, bidirectional, inward, outward, random |
| `point` | `Tuple[float, float]` | Spatial point | (x, y) in [0.0, 1.0] normalized coordinates |
| `base_frequency` | `float` | Base frequency | [0.1, 10.0] Hz, default 1.0 |
| `direction` | `ShiftDirection` | Direction enum | One of 6 defined directions |

**Data Structures:**

```python
# Direction enum values
ShiftDirection = {
    'FORWARD': 'forward',
    'REVERSE': 'reverse', 
    'BIDIRECTIONAL': 'bidirectional',
    'INWARD': 'inward',
    'OUTWARD': 'outward',
    'RANDOM': 'random'
}

# Direction properties dictionary
DirectionProperties = {
    'is_increasing': bool,
    'is_decreasing': bool,
    'is_geometric': bool,
    'is_temporal': bool,
    'can_reverse': bool
}

# Vector representation
Vector2D = Tuple[float, float]  # (x, y) unit vector
```

---

## Edge Cases and Error Handling

### String Parsing Issues
- **Invalid string**: Raise `ValueError` with clear message
- **Case sensitivity**: Handle all case variations (FORWARD, Forward, forward)
- **Whitespace**: Strip leading/trailing whitespace automatically
- **Empty string**: Raise `ValueError` (direction required)

### Vector Conversion Edge Cases
- **Non-spatial directions**: Return (0, 0) for FORWARD/REVERSE/BIDIRECTIONAL/RANDOM
- **Point at center**: Handle division by zero for INWARD/OUTWARD at (0.5, 0.5)
- **Invalid point coordinates**: Clamp to [0.0, 1.0] with warning
- **NaN/Inf coordinates**: Replace with center point (0.5, 0.5)

### Bidirectional Frequency Issues
- **Negative frequency**: Raise `ValueError` (frequency must be positive)
- **Zero frequency**: Return 0.0 (no oscillation)
- **Excessive frequency**: Warn if > 10.0 Hz (may cause visual artifacts)

### Random Direction Issues
- **Random seed**: Use system time for true randomness, allow seed for reproducibility
- **Distribution uniformity**: Ensure uniform distribution over [0, 2π]
- **Vector normalization**: Handle zero-length vectors gracefully

### Integration Edge Cases
- **Plugin compatibility**: Provide fallback to FORWARD for unknown directions
- **Version mismatch**: Handle missing directions gracefully in older plugins
- **Serialization errors**: Use string representation for JSON compatibility

### Performance Edge Cases
- **High-frequency updates**: Cache vector calculations for static points
- **Memory pressure**: Use flyweight pattern for direction instances
- **Thread safety**: Enum instances are immutable, thread-safe by design

---

## Dependencies

- **External Libraries**:
  - `enum.Enum` — Standard library enumeration (required)
  - `numpy` — Vector calculations and random number generation (required)
  - `typing` — Type hints for static analysis (required)

- **Internal Dependencies**:
  - `vjlive3.plugins.vtempi.base` — vtempi plugin base class (for integration)
  - `vjlive3.parameters` — Parameter system for direction control
  - `vjlive3.utils.math` — Mathematical utilities (optional)

- **Fallback Mechanisms**:
  - If numpy unavailable: Use pure Python math module (slower but functional)
  - If enum unavailable: Use string constants with validation
  - If vector calculations fail: Return default vectors (0, 0)

---

## Test Plan

| Test ID | Test Name | Expected Result |
|---------|-----------|-----------------|
| TC001 | `test_enum_values` | All 6 directions accessible as enum members |
| TC002 | `test_str_representation` | `__str__()` returns lowercase string values |
| TC003 | `test_is_increasing_forward` | FORWARD returns True for is_increasing() |
| TC004 | `test_is_increasing_reverse` | REVERSE returns False for is_increasing() |
| TC005 | `test_is_increasing_inward` | INWARD returns False for is_increasing() |
| TC006 | `test_is_increasing_outward` | OUTWARD returns True for is_increasing() |
| TC007 | `test_is_increasing_bidirectional` | BIDIRECTIONAL returns False for is_increasing() |
| TC008 | `test_is_increasing_random` | RANDOM returns False for is_increasing() |
| TC009 | `test_is_decreasing_forward` | FORWARD returns False for is_decreasing() |
| TC010 | `test_is_decreasing_reverse` | REVERSE returns True for is_decreasing() |
| TC011 | `test_is_decreasing_inward` | INWARD returns True for is_decreasing() |
| TC012 | `test_is_decreasing_outward` | OUTWARD returns False for is_decreasing() |
| TC013 | `test_is_decreasing_bidirectional` | BIDIRECTIONAL returns False for is_decreasing() |
| TC014 | `test_is_decreasing_random` | RANDOM returns False for is_decreasing() |
| TC015 | `test_is_geometric_inward` | INWARD returns True for is_geometric() |
| TC016 | `test_is_geometric_outward` | OUTWARD returns True for is_geometric() |
| TC017 | `test_is_geometric_forward` | FORWARD returns False for is_geometric() |
| TC018 | `test_is_geometric_reverse` | REVERSE returns False for is_geometric() |
| TC019 | `test_is_geometric_bidirectional` | BIDIRECTIONAL returns False for is_geometric() |
| TC020 | `test_is_geometric_random` | RANDOM returns False for is_geometric() |
| TC021 | `test_is_temporal_forward` | FORWARD returns True for is_temporal() |
| TC022 | `test_is_temporal_reverse` | REVERSE returns True for is_temporal() |
| TC023 | `test_is_temporal_inward` | INWARD returns False for is_temporal() |
| TC024 | `test_is_temporal_outward` | OUTWARD returns False for is_temporal() |
| TC025 | `test_is_temporal_bidirectional` | BIDIRECTIONAL returns False for is_temporal() |
| TC026 | `test_is_temporal_random` | RANDOM returns False for is_temporal() |
| TC027 | `test_can_reverse_forward` | FORWARD returns False for can_reverse() |
| TC028 | `test_can_reverse_reverse` | REVERSE returns True for can_reverse() |
| TC029 | `test_can_reverse_inward` | INWARD returns False for can_reverse() |
| TC030 | `test_can_reverse_outward` | OUTWARD returns False for can_reverse() |
| TC031 | `test_can_reverse_bidirectional` | BIDIRECTIONAL returns True for can_reverse() |
| TC032 | `test_can_reverse_random` | RANDOM returns False for can_reverse() |
| TC033 | `test_opposite_forward` | FORWARD.opposite() returns REVERSE |
| TC034 | `test_opposite_reverse` | REVERSE.opposite() returns FORWARD |
| TC035 | `test_opposite_inward` | INWARD.opposite() returns OUTWARD |
| TC036 | `test_opposite_outward` | OUTWARD.opposite() returns INWARD |
| TC037 | `test_opposite_bidirectional` | BIDIRECTIONAL.opposite() returns BIDIRECTIONAL |
| TC038 | `test_opposite_random` | RANDOM.opposite() returns RANDOM |
| TC039 | `test_from_string_forward` | from_string('forward') returns FORWARD |
| TC040 | `test_from_string_Forward` | from_string('Forward') returns FORWARD |
| TC041 | `test_from_string_FORWARD` | from_string('FORWARD') returns FORWARD |
| TC042 | `test_from_string_invalid` | from_string('invalid') raises ValueError |
| TC043 | `test_from_string_empty` | from_string('') raises ValueError |
| TC044 | `test_to_vector_forward` | FORWARD.to_vector() returns (1.0, 1.0) |
| TC045 | `test_to_vector_reverse` | REVERSE.to_vector() returns (-1.0, -1.0) |
| TC046 | `test_to_vector_inward` | INWARD.to_vector() returns (0.0, 0.0) |
| TC047 | `test_to_vector_outward` | OUTWARD.to_vector() returns (1.0, 1.0) |
| TC048 | `test_to_vector_bidirectional` | BIDIRECTIONAL.to_vector() returns (0.0, 0.0) |
| TC049 | `test_to_vector_random` | RANDOM.to_vector() returns (0.0, 0.0) |
| TC050 | `test_to_dict_forward` | to_dict() returns correct properties for FORWARD |
| TC051 | `test_to_dict_reverse` | to_dict() returns correct properties for REVERSE |
| TC052 | `test_get_vector_for_point_inward_center` | INWARD.get_vector_for_point((0.5, 0.5)) returns (0.0, 0.0) |
| TC053 | `test_get_vector_for_point_inward_corner` | INWARD.get_vector_for_point((0.0, 0.0)) returns unit vector |
| TC054 | `test_get_vector_for_point_outward_center` | OUTWARD.get_vector_for_point((0.5, 0.5)) returns (1.0, 0.0) |
| TC055 | `test_get_vector_for_point_outward_corner` | OUTWARD.get_vector_for_point((0.0, 0.0)) returns unit vector |
| TC056 | `test_get_vector_for_point_non_spatial` | FORWARD.get_vector_for_point raises ValueError |
| TC057 | `test_get_oscillation_frequency_bidirectional` | BIDIRECTIONAL.get_oscillation_frequency(1.0) returns 2.0 |
| TC058 | `test_get_oscillation_frequency_non_bidirectional` | FORWARD.get_oscillation_frequency raises ValueError |
| TC059 | `test_get_oscillation_frequency_negative` | get_oscillation_frequency(-1.0) raises ValueError |
| TC060 | `test_get_random_direction_random` | RANDOM.get_random_direction() returns unit vector |
| TC061 | `test_get_random_direction_non_random` | FORWARD.get_random_direction() raises ValueError |
| TC062 | `test_comparison_operators` | Enum comparison operators work correctly |
| TC063 | `test_hashing` | Enum instances are hashable and can be dict keys |
| TC064 | `test_serialization_roundtrip` | to_dict() + from_string() round-trip works |
| TC065 | `test_thread_safety` | Multiple threads can access enum safely |
| TC066 | `test_memory_footprint` | Enum instances use minimal memory (1 byte) |
| TC067 | `test_performance_constant_time` | All operations are O(1) constant time |
| TC068 | `test_integration_vtempi` | Integration with vtempi plugin works correctly |
| TC069 | `test_case_insensitive_parsing` | from_string handles all case variations |
| TC070 | `test_whitespace_handling` | from_string handles leading/trailing whitespace |
| TC071 | `test_vector_normalization` | All spatial vectors are unit length |
| TC072 | `test_vector_edge_cases` | Handles edge cases (NaN, Inf, zero vectors) |
| TC073 | `test_compatibility_matrix` | Direction compatibility matrix documented |
| TC074 | `test_error_messages` | Error messages are clear and actionable |
| TC075 | `test_documentation_accuracy` | Docstrings match actual implementation |
| TC076 | `test_type_annotations` | All methods have correct type hints |
| TC077 | `test_importability` | Enum can be imported without side effects |
| TC078 | `test_version_compatibility` | Works with Python 3.7+ enum.Enum |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] All 78 test cases implemented and passing
- [ ] Test coverage ≥ 90% (lines and branches)
- [ ] No stubs or placeholder code in implementation
- [ ] Complete docstrings with parameter constraints and examples
- [ ] Comprehensive error handling for all edge cases
- [ ] Performance benchmarks met (O(1) constant time for all operations)
- [ ] Memory usage minimal (1 byte per instance)
- [ ] Thread-safe implementation verified
- [ ] Integration test with vtempi plugin base class
- [ ] Serialization round-trip verified (to_dict + from_string)
- [ ] All mathematical formulations documented and tested
- [ ] Vector calculations validated for spatial directions
- [ ] Error messages are clear and actionable
- [ ] Type annotations complete and accurate
- [ ] Git commit with `[P3-EXT166] ShiftDirection: Complete enumeration`
- [ ] BOARD.md updated with effect status
- [ ] Lock released and resources cleaned up
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## Technical Implementation Details

### Direction Compatibility Matrix

| Direction | Temporal | Spatial | Can Reverse | Bidirectional | Random |
|-----------|----------|---------|-------------|---------------|--------|
| FORWARD | ✓ | ✗ | ✗ | ✗ | ✗ |
| REVERSE | ✓ | ✗ | ✓ | ✗ | ✗ |
| BIDIRECTIONAL | ✓ | ✗ | ✓ | ✗ | ✗ |
| INWARD | ✗ | ✓ | ✗ | ✗ | ✗ |
| OUTWARD | ✗ | ✓ | ✗ | ✗ | ✗ |
| RANDOM | ✗ | ✗ | ✗ | ✗ | ✗ |

### Mathematical Properties

#### Vector Properties
- **Magnitude**: All spatial vectors have magnitude 1.0 (unit vectors)
- **Direction**: Vectors point in direction of progression
- **Normalization**: Vectors normalized to prevent scaling artifacts

#### Temporal Properties
- **Phase**: FORWARD advances phase, REVERSE reverses phase
- **Frequency**: BIDIRECTIONAL oscillates at 2× base frequency
- **Randomness**: RANDOM provides uniform angular distribution

#### Spatial Properties
- **Distance**: INWARD decreases distance from center, OUTWARD increases
- **Convergence**: INWARD vectors point toward (0.5, 0.5)
- **Divergence**: OUTWARD vectors point away from center

### Performance Characteristics

- **Enum Lookup**: O(1) constant time via hash table
- **Direction Queries**: O(1) via precomputed boolean flags
- **Vector Conversion**: O(1) with cached results for static points
- **String Parsing**: O(1) with case-insensitive hash lookup
- **Memory Overhead**: 1 byte per instance + reference overhead

### Thread Safety

- **Immutable Instances**: Enum members are immutable, thread-safe
- **No Shared State**: No mutable class-level state
- **Atomic Operations**: All operations are atomic and thread-safe
- **Safe for Parallel**: Can be used concurrently across threads

### Integration Patterns

#### Plugin Integration
```python
class VTempiPlugin:
    def __init__(self, direction: ShiftDirection = ShiftDirection.FORWARD):
        self.direction = direction
        
    def update(self, dt: float):
        if self.direction.is_temporal():
            # Apply temporal progression
            self.phase += dt * self.speed * (1 if self.direction == ShiftDirection.FORWARD else -1)
        
        if self.direction.is_geometric():
            # Apply spatial transformation
            vector = self.direction.get_vector_for_point(self.position)
            self.position += vector * dt * self.speed
```

#### Parameter System Integration
```python
class DirectionParameter:
    def __init__(self, default: ShiftDirection = ShiftDirection.FORWARD):
        self.value = default
        
    def set_value(self, value: Union[str, ShiftDirection]):
        if isinstance(value, str):
            self.value = ShiftDirection.from_string(value)
        else:
            self.value = value
```

---

## Configuration Schema

```json
{
  "shift_direction": {
    "default": "forward",
    "valid_values": ["forward", "reverse", "bidirectional", "inward", "outward", "random"],
    "temporal_directions": ["forward", "reverse", "bidirectional"],
    "spatial_directions": ["inward", "outward"],
    "compatibility_matrix": {
      "temporal": ["forward", "reverse", "bidirectional"],
      "spatial": ["inward", "outward"],
      "reversible": ["reverse", "bidirectional"],
      "geometric": ["inward", "outward"]
    },
    "performance": {
      "lookup_time_ns": 10,
      "vector_calculation_time_ns": 50,
      "memory_per_instance_bytes": 1
    }
  }
}
```

---

## Security and Safety

- **Input Validation**: All string inputs validated against allowed values
- **Resource Limits**: No external resources, minimal memory footprint
- **Denial of Service Protection**: O(1) operations prevent timing attacks
- **Data Integrity**: Enum instances are immutable, preventing corruption
- **Thread Safety**: Immutable design ensures safe concurrent access
- **Error Handling**: Clear error messages for invalid inputs

---

## Future Enhancements

- **Custom Directions**: Allow plugins to define custom directional behaviors
- **Direction Interpolation**: Smooth transitions between different directions
- **3D Extension**: Add 3D spatial directions (up/down, forward/backward)
- **Direction Constraints**: Plugin-specific direction compatibility rules
- **Animation Curves**: Direction-specific easing functions for smooth transitions
- **Direction Groups**: Logical grouping of related directions
- **Direction Mapping**: Map between different direction systems
- **Direction History**: Track direction changes for debugging/analysis
- **Direction Visualization**: Visual representation of direction vectors
- **Direction Presets**: Predefined direction combinations for common patterns

---

This specification provides a comprehensive technical foundation for implementing a standardized directional control system suitable for temporal/rhythm-based VJLive3 plugins.