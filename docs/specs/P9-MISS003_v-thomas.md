# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

## Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `/home/happy/Desktop/claude projects/VJlive-2/plugins/core/modulation_attractors/__init__.py`
- **Class Names**: `VThomasPlugin`
- **Key Algorithms (Methods)**: `__init__, to_dict, from_dict, process`
- **Parameter Mappings (__init__ args)**: `None found`
- **Edge Cases**: Needs review of implementation for tight coupling or hardware dependencies.

---

## Task: P9-MISS003 — V-Thomas (VThomasPlugin)

**Phase:** P9 / P9-MISS003
**Assigned To:** Antigravity
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-23

---

## What This Module Does

VThomasPlugin is a chaotic attractor module that generates continuously evolving X/Y/Z/T outputs using the Thomas differential equations. It produces grid-like chaotic structures using sine functions (dx=-b*x+sin(y), dy=-b*y+sin(z), dz=-b*z+sin(x)). The attractor creates intricate, lattice-like patterns with smooth transitions, offering a distinct visual signature compared to other chaotic attractors.

## What It Does NOT Do

- Does not generate visual output directly (uses dummy shader)
- Does not provide real-time parameter editing during playback
- Does not support multiple attractor types (only Thomas)
- Does not include audio reactivity
- Does not provide 3D visualization of the attractor itself

---

## Public Interface

```python
from typing import Dict, Any
from core.effects.shader_base import Effect

class VThomasPlugin(Effect):
    def __init__(self) -> None:
        """
        Initialize the Thomas attractor plugin with default parameters.
        
        Creates a ThomasAttractor instance and sets up default
        speed (5.0) and amplitude (5.0) parameters.
        """
        pass
    
    def process(self, dt: float = 0.016, **kwargs) -> Dict[str, Any]:
        """
        Process one frame of the attractor.
        
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
        Get current internal state of the attractor.
        
        Returns:
            Dictionary containing:
            - 'x': Current X position
            - 'y': Current Y position
            - 'z': Current Z position
            - 'speed': Current speed parameter (0.0-10.0)
            - 'amplitude': Current amplitude parameter (0.0-10.0)
            - 'b': Thomas parameter 'b' (0.188 default)
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize plugin state to dictionary for saving.
        
        Returns:
            Dictionary with all parameters needed to restore state:
            - 'speed': Speed parameter
            - 'amplitude': Amplitude parameter
            - 'b': Thomas parameter 'b'
        """
        pass
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'VThomasPlugin':
        """
        Create plugin instance from serialized dictionary.
        
        Args:
            d: Dictionary containing saved parameters
            
        Returns:
            New VThomasPlugin instance with restored state
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
| `x` | `float` | Normalized X coordinate from attractor | 0.0-1.0 |
| `y` | `float` | Normalized Y coordinate from attractor | 0.0-1.0 |
| `z` | `float` | Normalized Z coordinate from attractor | 0.0-1.0 |
| `t` | `float` | Time-based oscillation for additional variation | 0.0-1.0 |

---

## Edge Cases and Error Handling

- **Missing hardware**: No hardware dependencies - uses pure mathematical computation
- **Bad input (dt)**: If dt <= 0, raises ValueError with message "dt must be positive"
- **Parameter out of range**: Parameters are clamped to valid ranges (0.0-10.0 for speed/amplitude, 'b' parameter has reasonable range)
- **Numerical instability**: Attractor equations can produce extreme values; normalization prevents overflow
- **Resource cleanup**: No external resources to clean up - pure computation

---

## Dependencies

- **External libraries needed**:
  - `math` — used for mathematical functions (sin, etc.) — fallback: Python built-in
  - `typing` — used for type hints — fallback: None (type hints are optional)

- **Internal modules this depends on**:
  - `core.effects.shader_base.Effect` — base class for all effects
  - `core.modulation_attractors.ThomasAttractor` — core attractor engine

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module initializes without hardware dependencies |
| `test_basic_operation` | Process method returns valid output dictionary |
| `test_parameter_clamping` | Speed and amplitude parameters are clamped to 0.0-10.0 |
| `test_output_range` | All outputs (x, y, z, t) are within 0.0-1.0 range |
| `test_serialization` | to_dict and from_dict preserve all parameters including 'b' |
| `test_state_consistency` | get_state returns current internal values |
| `test_dt_validation` | Negative dt raises ValueError |
| `test_performance` | Process method completes within 1ms at 60 FPS |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-9] P9-MISS003: V-Thomas plugin implementation` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Implementation Notes

- The Thomas attractor uses the equations: dx=-b*x+sin(y), dy=-b*y+sin(z), dz=-b*z+sin(x)
- Default parameter: b=0.188 (classic Thomas grid chaos)
- Speed parameter controls evolution rate (0.01-5.0 range)
- Amplitude parameter scales output (0.0-10.0 range)
- Uses dummy shader since this is a modulation plugin, not a visual effect
- All outputs are normalized to 0.0-1.0 range for consistent use in visual systems