# Spec: P6-AG2 — Agent Physics (16D Manifold + Gravity Wells)

**File naming:** `docs/specs/phase6_agent/P6-AG2_Agent_Physics.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-AG2 — Agent Physics

**Phase:** Phase 6 / P6-AG2
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Agent Physics provides a 16-dimensional manifold simulation with gravity wells for agent movement and interaction. It models agent trajectories, forces, collisions, and emergent behaviors in a high-dimensional space, enabling complex autonomous agent choreography and spatial reasoning.

---

## What It Does NOT Do

- Does not handle agent decision-making (delegates to P6-AG1)
- Does not manage agent memory (delegates to P6-AG3)
- Does not provide agent UI (delegates to P6-AG4)
- Does not include collision response details (basic detection only)

---

## Public Interface

```python
class AgentPhysics:
    def __init__(self, manifold_dim: int = 16) -> None: ...
    
    def add_gravity_well(self, position: np.ndarray, strength: float, radius: float) -> str: ...
    def remove_gravity_well(self, well_id: str) -> bool: ...
    
    def set_agent_state(self, agent_id: str, position: np.ndarray, velocity: np.ndarray) -> None: ...
    def get_agent_state(self, agent_id: str) -> AgentPhysicsState: ...
    
    def apply_force(self, agent_id: str, force: np.ndarray) -> None: ...
    def update(self, dt: float) -> None: ...
    
    def check_collision(self, agent1: str, agent2: str) -> bool: ...
    def get_distance(self, agent1: str, agent2: str) -> float: ...
    
    def get_manifold_dimension(self) -> int: ...
    def get_gravity_wells(self) -> List[GravityWell]: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `manifold_dim` | `int` | Dimensions in manifold | 4-32 |
| `position` | `np.ndarray` | Position in manifold | shape=(manifold_dim,) |
| `velocity` | `np.ndarray` | Velocity in manifold | shape=(manifold_dim,) |
| `strength` | `float` | Gravity well strength | Can be negative (repel) |
| `radius` | `float` | Gravity well influence radius | > 0 |
| `force` | `np.ndarray` | Force vector | shape=(manifold_dim,) |
| `dt` | `float` | Time step in seconds | > 0 |

**Output:** `AgentPhysicsState`, `GravityWell`, `bool`, `float` — Various physics results

---

## Edge Cases and Error Handling

- What happens if manifold dimension mismatch? → Raise ValueError
- What happens if gravity well strength is extreme? → May cause instability
- What happens if agent state is invalid? → Reset to safe defaults
- What happens if dt is too large? → May cause numerical instability
- What happens on cleanup? → Clear all wells, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for vector operations — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_gravity_wells` | Gravity wells affect agent motion |
| `test_agent_state` | Agent state updates correctly |
| `test_force_application` | Forces affect velocity |
| `test_collision_detection` | Detects agent collisions |
| `test_manifold_dimension` | Manifold dimension works correctly |
| `test_edge_cases` | Handles extreme values gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-AG2: Agent Physics (16D manifold)` message
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

*Specification based on VJlive-2 Agent Physics module.*