# Spec: P6-AG4 — Agent Control UI

**File naming:** `docs/specs/phase6_agent/P6-AG4_Agent_Control_UI.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-AG4 — Agent Control UI

**Phase:** Phase 6 / P6-AG4
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Agent Control UI provides a visual interface for monitoring and controlling autonomous agents. It displays agent states, physics visualization, memory snapshots, and coordination status, allowing users to observe agent behavior, intervene when needed, and understand the multi-agent system dynamics.

---

## What It Does NOT Do

- Does not handle agent decision-making (delegates to P6-AG1)
- Does not provide agent physics (delegates to P6-AG2)
- Does not manage agent memory (delegates to P6-AG3)
- Does not include advanced analytics or logging

---

## Public Interface

```python
class AgentControlUI:
    def __init__(self, agent_bridge: AgentBridge, physics: AgentPhysics) -> None: ...
    
    def set_agent_visibility(self, agent_id: str, visible: bool) -> None: ...
    def set_physics_visualization(self, enabled: bool) -> None: ...
    def set_memory_visualization(self, enabled: bool) -> None: ...
    
    def select_agent(self, agent_id: str) -> None: ...
    def get_selected_agent(self) -> Optional[str]: ...
    
    def render(self, ctx: moderngl.Context, width: int, height: int) -> None: ...
    def handle_event(self, event: UIEvent) -> None: ...
    
    def get_agent_list(self) -> List[str]: ...
    def get_agent_state_display(self, agent_id: str) -> AgentStateDisplay: ...
    
    def reset_view(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `agent_bridge` | `AgentBridge` | Agent coordination system | Must be initialized |
| `physics` | `AgentPhysics` | Physics simulation system | Must be initialized |
| `agent_id` | `str` | Agent identifier | Valid agent |
| `visible` | `bool` | Visibility flag | True/False |
| `enabled` | `bool` | Enable flag | True/False |
| `event` | `UIEvent` | User input event | Mouse, keyboard |
| `ctx` | `moderngl.Context` | OpenGL context | Valid |
| `width, height` | `int` | Canvas dimensions | > 0 |

**Output:** Renders UI to screen, manages agent selection and visualization

---

## Edge Cases and Error Handling

- What happens if agent not found? → Show error, deselect
- What happens if physics not initialized? → Disable physics viz
- What happens if UI event invalid? → Ignore
- What happens on resize? → Adjust layout accordingly
- What happens on cleanup? → Release UI resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `moderngl` — for rendering — fallback: raise ImportError
  - `imgui` or `pygame` — for UI framework — fallback: use basic pygame
- Internal modules this depends on:
  - `vjlive3.render.opengl_context`
  - `vjlive3.agent.agent_bridge` (P6-AG1)
  - `vjlive3.agent.agent_physics` (P6-AG2)
  - `vjlive3.agent.agent_memory` (P6-AG3)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_agent_list` | Lists all registered agents |
| `test_agent_selection` | Selects agents correctly |
| `test_physics_viz` | Physics visualization works |
| `test_memory_viz` | Memory visualization works |
| `test_event_handling` | Handles user input events |
| `test_render` | Renders UI without errors |
| `test_edge_cases` | Handles missing agents gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-AG4: Agent Control UI` message
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

*Specification based on VJlive-2 Agent Control UI module.*