# Spec: P6-AG1 — Agent Bridge

**File naming:** `docs/specs/phase6_agent/P6-AG1_Agent_Bridge.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-AG1 — Agent Bridge

**Phase:** Phase 6 / P6-AG1
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Agent Bridge provides the communication and coordination layer between multiple autonomous agents in the VJLive3 system. It handles message passing, state synchronization, and decision coordination, enabling agents to work together on complex visual tasks while maintaining individual autonomy.

---

## What It Does NOT Do

- Does not handle agent physics (delegates to P6-AG2)
- Does not manage agent memory (delegates to P6-AG3)
- Does not provide agent UI (delegates to P6-AG4)
- Does not include agent decision-making logic

---

## Public Interface

```python
class AgentBridge:
    def __init__(self, agent_count: int = 4) -> None: ...
    
    def register_agent(self, agent_id: str, agent: AgentBase) -> None: ...
    def unregister_agent(self, agent_id: str) -> None: ...
    
    def send_message(self, from_agent: str, to_agent: str, message: Any) -> bool: ...
    def broadcast_message(self, from_agent: str, message: Any) -> None: ...
    
    def get_agent_state(self, agent_id: str) -> AgentState: ...
    def get_all_states(self) -> Dict[str, AgentState]: ...
    
    def coordinate_task(self, task_id: str, agents: List[str], params: Dict) -> None: ...
    def get_task_status(self, task_id: str) -> TaskStatus: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `agent_count` | `int` | Number of agents to support | 1-16 |
| `agent_id` | `str` | Unique agent identifier | Non-empty |
| `agent` | `AgentBase` | Agent instance | Valid agent |
| `from_agent` | `str` | Sender agent ID | Valid agent |
| `to_agent` | `str` | Recipient agent ID | Valid agent |
| `message` | `Any` | Message content | Serializable |
| `task_id` | `str` | Task identifier | Non-empty |
| `agents` | `List[str]` | List of agent IDs | Valid agents |
| `params` | `Dict` | Task parameters | Valid dict |

**Output:** `bool`, `AgentState`, `Dict[str, AgentState]`, `TaskStatus` — Various coordination results

---

## Edge Cases and Error Handling

- What happens if agent not registered? → Return error, log warning
- What happens if message too large? → Truncate or reject, log warning
- What happens if task coordination fails? → Rollback, notify agents
- What happens on cleanup? → Disconnect all agents, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - None required for basic functionality
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase` (for AgentBase)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_agent_registration` | Registers and unregisters agents |
| `test_message_passing` | Sends messages between agents |
| `test_broadcast` | Broadcasts messages to all agents |
| `test_task_coordination` | Coordinates tasks across agents |
| `test_state_synchronization` | Keeps agent states synchronized |
| `test_error_handling` | Handles agent failures gracefully |
| `test_cleanup` | Releases resources on cleanup |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-AG1: Agent Bridge` message
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

*Specification based on VJlive-2 Agent Bridge module.*