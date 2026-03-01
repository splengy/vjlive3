# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

## Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `/home/happy/Desktop/claude projects/VJlive-2/plugins/core/modulation_attractors/__init__.py`
- **Class Names**: `VLanguorPlugin`
- **Key Algorithms (Methods)**: `__init__, _remap_params, process, get_state, to_dict, from_dict`
- **Parameter Mappings (__init__ args)**: `None found`
- **Edge Cases**: Needs review of implementation for tight coupling or hardware dependencies.

---

## Task: P9-MISS005 — V-Languor (VLanguorPlugin)

**Phase:** P9 / P9-MISS005
**Assigned To:** Antigravity
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-23

---

## What This Module Does

VLanguorPlugin is a composite chaotic attractor module that combines all four individual attractors (Lorenz, Halvorsen, Thomas, Sakarya) into a single weighted blend. It generates continuously evolving X/Y/Z/T outputs by averaging the outputs of all four attractors, creating a rich, complex chaotic pattern that never repeats. This module provides a more diverse and nuanced chaotic behavior compared to individual attractors, making it ideal for applications requiring maximum variation and complexity.

## What It Does NOT Do

- Does not generate visual output directly (uses dummy shader)
- Does not provide real-time parameter editing during playback
- Does not support individual attractor parameter control
- Does not include audio reactivity
- Does not provide 3D visualization of the attractor itself
- Does not allow weighted blending ratios (uses equal weighting)

---

## Public Interface

```python
from typing import Dict, Any
from core.effects.shader_base import Effect

class VLanguorPlugin(Effect):
    def __init__(self) -> None:
        """
        Initialize the Languor composite attractor plugin with default parameters.
        
        Creates instances of all four attractors (Lorenz, Halvorsen, Thomas, Sakarya)
        and sets up default speed (5.0) and amplitude (5.0) parameters.
        """
        pass
    
    def process(self, dt: float = 0.016, **kwargs) -> Dict[str, Any]:
        """
        Process one frame of the composite attractor.
        
        Args:
            dt: Time delta in seconds (default 0.016 for 60 FPS)
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Dictionary with normalized X/Y/Z/T outputs:
            - 'x': Normalized X coordinate (0.0-1.0)
            - 'y': Normalized Y coordinate (0.0-1.0)
            - 'z': Normalized Z coordinate (0.0-1.0)
            - 't': Time-based oscillation (0.0-1.0)
        """
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current internal state of the composite attractor.
        
        Returns:
            Dictionary containing:
            - 'speed': Current speed parameter (0.0-10.0)
            - 'amplitude': Current amplitude parameter (0.0-10.0)
            - 'lorenz_state': Current Lorenz attractor state
            - 'halvorsen_state': Current Halvorsen attractor state
            - 'thomas_state': Current Thomas attractor state
            - 'sakarya_state': Current Sakarya attractor state
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize plugin state to dictionary for saving.
        
        Returns:
            Dictionary with all parameters needed to restore state:
            - 'speed': Speed parameter
            - 'amplitude': Amplitude parameter
        """
        pass
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'VLanguorPlugin':
        """
        Create plugin instance from serialized dictionary.
        
        Args:
            d: Dictionary containing saved parameters
            
        Returns:
            New VLanguorPlugin instance with restored state
        """
        pass
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `dt` | `float` | Time delta in seconds for frame processing | Default: 0.016 (60 FPS), Range: >0 |
| `**kwargs` | `dict` | Additional parameters (ignored) | None |

**Outputs:**

| Name | Type | Description | Range |
|------|------|-------------|-------|
| `x` | `float` | Normalized X coordinate from composite attractor | 0.0-1.0 |
| `y` | `float` | Normalized Y coordinate from composite attractor | 0.0-1.0 |
| `z` | `float` | Normalized Z coordinate from composite attractor | 0.0-1.0 |
| `t` | `float` | Time-based oscillation for additional variation | 0.0-1.0 |

---

## Edge Cases and Error Handling

- **Missing hardware**: No hardware dependencies - uses pure mathematical computation
- **Bad input (dt)**: If dt <= 0, raises ValueError with message "dt must be positive"
- **Parameter out of range**: Parameters are clamped to valid ranges (0.0-10.0 for speed/amplitude)
- **Numerical instability**: Composite attractor can produce extreme values; normalization prevents overflow
- **Resource cleanup**: No external resources to clean up - pure computation

---

## Dependencies

- **External libraries needed**:
  - `math` — used for mathematical functions (sin, etc.) — fallback: Python built-in
  - `typing` — used for type hints — fallback: None (type hints are optional)

- **Internal modules this depends on**:
  - `core.effects.shader_base.Effect` — base class for all effects
  - `core.modulation_attractors.LorenzAttractor` — Lorenz attractor engine
  - `core.modulation_attractors.HalvorsenAttractor` — Halvorsen attractor engine
  - `core.modulation_attractors.ThomasAttractor` — Thomas attractor engine
  - `core.modulation_attractors.SakaryaAttractor` — Sakarya attractor engine

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module initializes without hardware dependencies |
| `test_basic_operation` | Process method returns valid output dictionary |
| `test_parameter_clamping` | Speed and amplitude parameters are clamped to 0.0-10.0 |
| `test_output_range` | All outputs (x, y, z, t) are within 0.0-1.0 range |
| `test_serialization` | to_dict and from_dict preserve all parameters |
| `test_state_consistency` | get_state returns current internal values |
| `test_dt_validation` | Negative dt raises ValueError |
| `test_performance` | Process method completes within 1ms at 60 FPS |
| `test_composite_behavior` | All four attractors are processed and blended correctly |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-9] P9-MISS005: V-Languor plugin implementation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Implementation Notes

- The Languor plugin combines all four attractors using equal weighting (1/4 each)
- Each attractor is processed independently with the same speed parameter
- X/Y/Z outputs are averaged across all four attractors
- Time output 't' is a special blend of all attractor states for additional variation
- Uses dummy shader since this is a modulation plugin, not a visual effect
- All outputs are normalized to 0.0-1.0 range for consistent use in visual systems
- Provides maximum chaotic complexity through composite behavior