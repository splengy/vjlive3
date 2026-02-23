# P4-COR029_AgentPerformanceBridge.md

**Phase:** Phase 4 / P4-COR029  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR029 — AgentPerformanceBridge

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `vjlive/core/agent_bridge.py`  
**Legacy Class:** `AgentPerformanceBridge`  

---

## What This Module Does

`AgentPerformanceBridge` is the monolithic control surface and physics engine connecting the autonomous agents to the VJLive performance API. It manages a 16-dimensional "Mood Manifold" (a structural physics simulation of the agent's emotional state) that drifts autonomously based on three factors: internal momentum, music telemetry (audio reactivity), and human "gravity wells" (UI overrides). It consumes the `AgentInteractionMode` enum to dictate exactly how strongly the AI's computed target coordinate interpolates against the human's manual inputs, executing blending mathematics for features like `PILOT`, `COLLABORATE`, and `AUTONOMOUS` modes.

---

## What It Does NOT Do

- Does NOT generate the actual VLM prompts or execute LangGraph loops (that is `AgentOrchestrator` / `PerformanceAgent`).
- Does NOT render video directly (it broadcasts state to WebSockets and pushes coordinates to `MoodManifold` nodes).

---

## Public Interface

```python
import numpy as np
from typing import Dict, List, Any, Optional, Union
from vjlive3.plugins.base import BasePlugin

class AgentPerformanceBridge(BasePlugin):
    """
    Core physics engine bridging the AI brain to the node graph.
    Simulates the 16D Agent Manifold and resolves human/AI control conflicts.
    """
    
    METADATA = {
        "id": "AgentPerformanceBridge",
        "type": "bridge",
        "version": "1.0.0",
        "legacy_ref": "agent_bridge (AgentPerformanceBridge)"
    }
    
    def __init__(self, dimensions: int = 16, websocket_gateway: Any = None, 
                 effect_chain: Any = None, audio_reactor: Any = None, 
                 mood_manifold: Any = None, fps_getter: Any = None) -> None:
        """Initializes the physical state vectors (velocity, coordinates) and mode defaults."""
        pass
        
    def set_control_mode(self, mode: Any) -> None:
        """Transitions the agent interaction mode."""
        pass

    def add_gravity_well(self, position: List[float], strength: float = 0.5, duration: float = 30.0) -> None:
        """Injects a human-override coordinate that physically pulls the agent's navigation."""
        pass

    def toggle_chaos_monkey(self, enabled: bool, duration: float = 60.0) -> None:
        """Activates erratic, instantaneous randomized manifold teleportation."""
        pass

    def on_frame(self, audio_state: Dict[str, Any], fps: float, crowd_energy: float = 0.0) -> None:
        """
        The central execution loop: 
        1) Updates Adrenaline
        2) Calculates internal/gravity momentum
        3) Resolves Human vs AI interpolation based on InteractionMode
        4) Mutates the external mood_manifold position
        5) Broadcasts state to WebSockets
        """
        pass

    def get_agent_state(self, agent_id: str = "agent") -> Dict[str, Any]:
        """Serializes internal physics and sentiment for the UI."""
        pass
        
    def update_visual_feedback(self, visual_data: Dict[str, Any]) -> None:
        """Modulates 'success_metric' based on screen motion and edge density."""
        pass
```

---

## Inputs and Outputs

### Physics Simulation (`on_frame`)
The fundamental calculation within `on_frame` generates the `combined_v` (velocity):
```python
v_internal = (mood_coordinate - previous_coordinate)
v_music = (target_from_audio - mood_coordinate)
v_gravity = sum((diff / dist) * strength / (dist + 0.1) for each gravity_well)

combined_v = (
    v_internal * 0.4 +
    v_music * 0.4 +
    v_gravity * 0.2
) + np.random.normal(0, exploration_noise)
```

### Interpolation Mathematics
Based on `AgentInteractionMode`, the bridge applies the `combined_v` target differently:
- `OBSERVE` / `ADVISE`: Target is ignored. `mood_coordinate` tracks human UI slider exactly.
- `COLLABORATE`: Uses lerp `0.1 + 0.2 * influence`.
- `PILOT`: Uses lerp `0.3`, dropping to `0.05` if a recent human override exists, simulating physical "resistance".
- `AUTONOMOUS`: Uses full `0.3` lerp, up to `0.8` if `chaos_mode` is active.

### Adrenaline & Chaos
- Adrenaline spikes based on `(spectral_flux + bass_energy) * 0.5` + beat detection.
- `adrenaline_decay` defaults to `0.95`.
- If `adrenaline > 0.98` for 30 consecutive seconds, `chaos_monkey` auto-triggers.

---

## Edge Cases and Error Handling

### Dimensional Drift
- If a `gravity_well` position array is passed with `< 16` dimensions, it must be padded with `0.5` (neutral). If `> 16`, it must be truncated abruptly. The math will throw `ValueError` during matrix addition otherwise.

### Zero Distance Div/0
- In the gravity well physics formula, `pull = (diff / dist) * well.strength * (1.0 / (dist + 0.1))`. The `dist + 0.1` denominator safely prevents `ZeroDivisionError` when the agent lands exactly on the human's override coordinate.

---

## Dependencies

### External Libraries
- `numpy` (Critical for vector math: `.copy()`, `np.linalg.norm()`, `np.random.normal()`)
- `time`

### Internal Modules
- `AgentInteractionMode`
- Expects duck-typed attributes: `websocket_gateway.broadcast()`, `mood_manifold.set_mood_vector()`.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_gravity_well_padding` | Passing a 3D well into a 16D bridge safely pads out to neutral `0.5` for dimensions 4-15 without crashing. |
| `test_adrenaline_decay` | Passing empty audio states over 10 consecutive `on_frame(dt=1/60)` calls correctly decays the `adrenaline` float down by factors of 0.95. |
| `test_interaction_mode_blending` | In `PILOT` mode with a recent human override, the lerp calculation mathematically drops from `0.3` back to `0.05`. |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 800 lines (The legacy file is 1000+ lines. Refactor extraneous sub-classes like `AgentSuggestion` into support types if needed).
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR029: AgentPerformanceBridge` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- The 16-D Manifold is a core defining aesthetic hook of VJLive. The `on_frame` integration math (`np.linalg.norm`) must be extremely tightly optimized as it executes every 16ms.

### Legacy Aliases
- Ensure `set_control_mode` correctly traps strings like `"pilot"`, the old enums `ControlMode.DUEL`, and the new enums `AgentInteractionMode.COLLABORATE` identically to the legacy adapter block. UI systems rely on these exact string bindings.
