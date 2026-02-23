# P4-COR024_AgentInteractionMode.md

**Phase:** Phase 4 / P4-COR024  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR024 — AgentInteractionMode

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `vjlive/core/agent_bridge.py`  
**Legacy Class:** `AgentInteractionMode` (Enum)  

---

## What This Module Does

`AgentInteractionMode` is the foundational telemetry and state-machine primitive defining the balance of power between the human operator and the VJLive AI Agents. It defines a strict 5-tier hierarchy scaling from complete human control (Agent restricted to observation) to complete AI autonomy. This enumeration is consumed globally by the UI, the `AgentOrchestrator`, and every Effect Node to determine whether an AI parameter mutation should be permitted, queued for approval, or executed immediately.

---

## What It Does NOT Do

- Does NOT enforce the access control itself (it is purely a data structure; the `AgentBridge` consumes it to allow/deny actions).
- Does NOT contain complex methods or initialization logic.

---

## Public Interface

```python
from enum import Enum

class AgentInteractionMode(Enum):
    """
    Five-tier agent interaction model defining the boundary of autonomy.
    """
    
    METADATA = {
        "id": "AgentInteractionMode",
        "type": "enum",
        "version": "1.0.0",
        "legacy_ref": "agent_bridge (AgentInteractionMode)"
    }
    
    OBSERVE = "observe"
    ADVISE = "advise"
    COLLABORATE = "collaborate"
    PILOT = "pilot"
    AUTONOMOUS = "autonomous"
```

---

## Inputs and Outputs

N/A. As a strict Python Enum, this module defines static constants. 

### Constant Definitions

| State | Value String | Functional Definition (Enforced by Consumers) |
|-------|--------------|---------------------------------------------|
| `OBSERVE` | `"observe"` | Agent watches only, calculates metrics, sends suggestions to the UI overlay. Zero parameter influence allowed. |
| `ADVISE` | `"advise"` | Agent actively calculates parameter changes and queues them in an approval pipeline for the human to accept. |
| `COLLABORATE` | `"collaborate"` | Blended control. Both human and agent mutate parameters based on a weighted influence slider. |
| `PILOT` | `"pilot"` | Agent drives the majority of parameters by default, but human input immediately overrides and temporarily locks the parameter. |
| `AUTONOMOUS` | `"autonomous"` | Full agent control including structural Graph building (adding/removing nodes). Human input is ignored. |

---

## Edge Cases and Error Handling

### Invalid Parameters
- Legacy systems often attempt to coerce the old 4-tier `ControlMode` enum (`HUMAN`, `AGENT`, `DUEL`, `CROWD`) into this structure. While the coercion mapping happens outside this file (in `AgentBridge`), this Enum must strictly maintain the string values defined above to ensure legacy UI dropdowns pointing to `"observe"`, `"advise"`, etc., do not break.

---

## Dependencies

### External Libraries
- `enum` (standard library)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_enum_completeness` | Verifies all 5 states (`OBSERVE`, `ADVISE`, `COLLABORATE`, `PILOT`, `AUTONOMOUS`) exist. |
| `test_enum_string_values` | Verifies the string values exactly match their lowercase equivalents (e.g. `AgentInteractionMode.OBSERVE.value == "observe"`). |

**Minimum coverage:** 100% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 100 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR024: AgentInteractionMode` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- This should reside in its own explicit `agent_interaction_mode.py` file within `vjlive3/support/enums/` or the equivalent central structure directory, rather than being buried at the top of a massive `agent_bridge` god-file as it was in legacy. 

### Legacy References
- Sourced from `/home/happy/Desktop/claude projects/vjlive/core/agent_bridge.py` lines 15-21.
