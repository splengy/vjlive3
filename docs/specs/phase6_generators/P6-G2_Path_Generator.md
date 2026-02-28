# Spec: P6-G2 — Path Generator (Procedural)

**File naming:** `docs/specs/phase6_generators/P6-G2_Path_Generator.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-G2 — Path Generator

**Phase:** Phase 6 / P6-G2
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Path Generator creates procedural paths and trajectories for visual elements and agents. It provides various path types (linear, circular, spline, noise), parameterized control, and real-time evolution, enabling complex automated motion and animation without manual keyframing.

---

## What It Does NOT Do

- Does not handle agent physics (delegates to P6-AG2)
- Does not provide path editing UI (delegates to P7-U1)
- Does not include collision detection (basic path following only)
- Does not support external path import (procedural generation only)

---

## Public Interface

```python
class PathGenerator:
    def __init__(self) -> None: ...
    
    def set_path_type(self, path_type: str) -> None: ...
    def get_path_type(self) -> str: ...
    
    def set_parameters(self, params: Dict[str, float]) -> None: ...
    def get_parameters(self) -> Dict[str, float]: ...
    
    def set_speed(self, speed: float) -> None: ...
    def get_speed(self) -> float: ...
    
    def get_position(self, t: float) -> np.ndarray: ...
    def get_velocity(self, t: float) -> np.ndarray: ...
    def get_rotation(self, t: float) -> np.ndarray: ...
    
    def generate_path(self, duration: float, sample_rate: float) -> PathData: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `path_type` | `str` | Type of path | 'linear', 'circle', 'spline', 'noise', 'lissajous' |
| `params` | `Dict[str, float]` | Path-specific parameters | Valid param names |
| `speed` | `float` | Path traversal speed | 0.0 to 10.0 |
| `t` | `float` | Time parameter | ≥ 0.0 |
| `duration` | `float` | Path duration in seconds | > 0 |
| `sample_rate` | `float` | Samples per second | > 0 |

**Output:** `np.ndarray` — Position/velocity/rotation, `PathData` — Complete path data

---

## Edge Cases and Error Handling

- What happens if path type is invalid? → Use default 'linear'
- What happens if parameters are missing? → Use defaults
- What happens if speed is 0? → Static path
- What happens if t exceeds duration? → Clamp or loop based on mode
- What happens on cleanup? → Clear cached path data

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for path calculations — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_path_types` | All path types generate correctly |
| `test_parameter_control` | Parameters affect path shape |
| `test_speed_control` | Speed affects traversal rate |
| `test_position_query` | Returns correct positions at time t |
| `test_velocity_rotation` | Derivatives are correct |
| `test_path_generation` | Generates complete path data |
| `test_edge_cases` | Handles invalid parameters gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-G2: Path generator` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Checkpoint

- [ ] Spec reviewed and approved
- [ ] Implementation ready to begin
- [ ] All dependencies verified
- [ ] Test plan complete
- [ ] Definition of Done clear

---

*Specification based on VJlive-2 Path Generator module.*