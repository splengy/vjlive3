# Spec: P6-AG3 — Agent Memory (50-Snapshot System)

**File naming:** `docs/specs/phase6_agent/P6-AG3_Agent_Memory.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-AG3 — Agent Memory

**Phase:** Phase 6 / P6-AG3
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Agent Memory provides a sophisticated memory system for autonomous agents, implementing a 50-snapshot circular buffer with associative recall, importance weighting, and temporal indexing. It allows agents to remember past states, experiences, and decisions, enabling learning and adaptation over time.

---

## What It Does NOT Do

- Does not handle agent decision-making (delegates to P6-AG1)
- Does not provide agent physics (delegates to P6-AG2)
- Does not include agent UI (delegates to P6-AG4)
- Does not support long-term storage (episodic memory only)

---

## Public Interface

```python
class AgentMemory:
    def __init__(self, capacity: int = 50) -> None: ...
    
    def record_snapshot(self, agent_id: str, state: AgentState, importance: float = 1.0) -> None: ...
    def recall_recent(self, agent_id: str, count: int = 10) -> List[AgentSnapshot]: ...
    def recall_by_similarity(self, agent_id: str, query_state: AgentState, top_k: int = 5) -> List[AgentSnapshot]: ...
    
    def get_snapshot(self, agent_id: str, index: int) -> Optional[AgentSnapshot]: ...
    def get_latest(self, agent_id: str) -> Optional[AgentSnapshot]: ...
    
    def forget_oldest(self, agent_id: str) -> None: ...
    def clear_memory(self, agent_id: str) -> None: ...
    
    def get_memory_stats(self, agent_id: str) -> MemoryStats: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `capacity` | `int` | Number of snapshots to retain | 10-200 |
| `agent_id` | `str` | Agent identifier | Valid agent |
| `state` | `AgentState` | Agent state to record | Valid state |
| `importance` | `float` | Importance weight | 0.0 to 1.0 |
| `count` | `int` | Number of snapshots to recall | > 0 |
| `query_state` | `AgentState` | State for similarity search | Valid state |
| `top_k` | `int` | Top matches to return | > 0 |
| `index` | `int` | Snapshot index | 0 ≤ index < capacity |

**Output:** `List[AgentSnapshot]`, `Optional[AgentSnapshot]`, `MemoryStats` — Various memory query results

---

## Edge Cases and Error Handling

- What happens if capacity exceeded? → Drop oldest snapshot
- What happens if importance is 0? → Record but may be forgotten first
- What happens if no snapshots exist? → Return empty list or None
- What happens if similarity query fails? → Return empty list
- What happens on cleanup? → Clear all memory buffers

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for state similarity calculations — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase` (for AgentState type)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_snapshot_capacity` | Respects capacity limit |
| `test_record_recall` | Records and recalls snapshots correctly |
| `test_importance_weighting` | Importance affects retention |
| `test_similarity_search` | Finds similar states correctly |
| `test_forgetting_oldest` | Forgets oldest when full |
| `test_clear_memory` | Clears all snapshots |
| `test_edge_cases` | Handles edge cases gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-AG3: Agent Memory (50-snapshot)` message
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

*Specification based on VJlive-2 Agent Memory module.*