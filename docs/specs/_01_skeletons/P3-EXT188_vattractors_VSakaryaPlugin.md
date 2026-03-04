# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT188 — VSakaryaPlugin

**Phase:** P3 / P3-EXT188
**Assigned To:** [Agent name]
**Spec Written By:** [Agent name]
**Date:** [YYYY-MM-DD]

---

## What This Module Does

VSakaryaPlugin is a chaotic attractor module that generates continuously evolving X/Y/Z/T outputs using the Sakarya differential equations. It produces 3D chaos with xy cross-coupling (dx=-x+y+y*z, dy=-x-y+a*x*z, dz=z-b*x*y). The attractor creates complex, intertwined trajectories with a distinctive character that combines elements of both spiral and grid-like chaos patterns.

---

## What It Does NOT Do

- Does not generate visual output directly (uses dummy shader)
- Does not provide real-time parameter editing during playback
- Does not support multiple attractor types (only Sakarya)
- Does not include audio reactivity
- Does not provide 3D visualization of the attractor itself

---

## Public Interface

```python
from typing import Dict, Any
from core.effects.shader_base import Effect

class VSakaryaPlugin(Effect):
    def __init__(self) -> None: ...
    def process(self, dt: float = 0.016, **kwargs) -> Dict[str, Any]: ...
    def get_state(self) -> Dict[str, Any]: ...
    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'VSakaryaPlugin': ...
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

- What happens if hardware is missing? → No hardware dependencies - uses pure mathematical computation
- What happens on bad input? → If dt <= 0, raises ValueError with message "dt must be positive"
- What is the cleanup path? → No external resources to clean up - pure computation

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `math` — used for mathematical functions (sin, etc.) — fallback: Python built-in
  - `typing` — used for type hints — fallback: None (type hints are optional)
- Internal modules this depends on:
  - `core.effects.shader_base.Effect` — base class for all effects
  - `core.modulation_attractors.SakaryaAttractor` — core attractor engine

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module initializes without hardware dependencies |
| `test_basic_operation` | Process method returns valid output dictionary |
| `test_parameter_clamping` | Speed and amplitude parameters are clamped to 0.0-10.0 |
| `test_output_range` | All outputs (x, y, z, t) are within 0.0-1.0 range |
| `test_serialization` | to_dict and from_dict preserve all parameters including 'a' and 'b' |
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
- [ ] Git commit with `[Phase-3] P3-EXT188: VSakaryaPlugin` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎀 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## Implementation Notes

- The Sakarya attractor uses the equations: dx=-x+y+y*z, dy=-x-y+a*x*z, dz=z-b*x*y
- Default parameters: a=0.398, b=0.3 (classic Sakarya chaos)
- Speed parameter controls evolution rate (0.01-5.0 range)
- Amplitude parameter scales output (0.0-10.0 range)
- Uses dummy shader since this is a modulation plugin, not a visual effect
- All outputs are normalized to 0.0-1.0 range for consistent use in visual systems