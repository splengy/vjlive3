# P4-COR027_AgentOrchestrator.md

**Phase:** Phase 4 / P4-COR027  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR027 — AgentOrchestrator

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `VJlive-2/core/agent_orchestrator.py`  
**Legacy Class:** `AgentOrchestrator`  

---

## What This Module Does

`AgentOrchestrator` is the core execution loop and state machine engine for autonomous VJLive performance agents. Utilizing `LangGraph`, it constructs a directed cyclic graph representing the sentient loop: **Perceive** (visual UI mapping) → **Recall** (RAG via MemoryDB) → **Plan** (VLM prompt generation) → **Execute** (translating planned actions into GUI driver limits) → **Verify** (post-execution visual differential scoring). It supports physical "Time Travel" by rewinding agent states via LangGraph's `MemorySaver` checkpointer.

---

## What It Does NOT Do

- Does NOT directly execute the ML models. It delegates perception to `self.agent.vlm_controller.screenshot_capturer` and retrieval to `self.agent.memory_db`.
- Does NOT act globally across multiple agents. Each `AgentOrchestrator` instance is strictly bound 1:1 to a specific `agent_persona` object injected during initialization.

---

## Public Interface

```python
from typing import Dict, List, Any, Optional, TypedDict
from vjlive3.plugins.base import BasePlugin
import numpy as np
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

class AgentState(TypedDict):
    """The state of the agent at any point in the cycle"""
    agent_id: str
    intent: str
    context: Dict[str, Any]
    screenshot: Optional[np.ndarray]
    ui_elements: List[Dict[str, Any]]
    precedents: List[Dict[str, Any]]
    planned_action: Optional[Dict[str, Any]]
    execution_result: Optional[Dict[str, Any]]
    feedback: Optional[float]
    history: List[Dict[str, Any]]

class AgentOrchestrator(BasePlugin):
    """
    Manages the LangGraph orchestration for a VJLive Agent.
    """
    
    METADATA = {
        "id": "AgentOrchestrator",
        "type": "orchestrator",
        "version": "1.0.0",
        "legacy_ref": "agent_orchestrator (AgentOrchestrator)"
    }
    
    def __init__(self, agent_persona: Any) -> None:
        """Initializes the checkpointer and compiles the LangGraph."""
        pass
        
    def _build_graph(self) -> Any:
        """Constructs and returns the compiled LangGraph workflow."""
        pass

    async def node_perceive(self, state: AgentState) -> Dict[str, Any]:
        """Captures hardware screenshots and perceive UI elements."""
        pass

    async def node_recall(self, state: AgentState) -> Dict[str, Any]:
        """Retrieves precedents from the agent's memory database."""
        pass

    async def node_plan(self, state: AgentState) -> Dict[str, Any]:
        """Queries the VLM controller to generate the next action."""
        pass

    async def node_execute(self, state: AgentState) -> Dict[str, Any]:
        """Translates the planned dictionary action into driver/plugin hardware limits."""
        pass

    async def node_verify(self, state: AgentState) -> Dict[str, Any]:
        """Computes a pixel-diff threshold to calculate execution success."""
        pass

    async def run_cycle(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Triggers the async stream across the built graph."""
        pass

    def rewind(self, steps: int = 1) -> Optional[Dict[str, Any]]:
        """Restores the agent's state back via the LangGraph checkpointer history."""
        pass
```

---

## Inputs and Outputs

### Node Mutators

LangGraph relies on node functions returning dictionaries that merge into the `AgentState`.
- `node_perceive`: Yields `{'screenshot': ... , 'ui_elements': ...}`
- `node_recall`: Yields `{'precedents': ...}`
- `node_plan`: Yields `{'planned_action': ...}`
- `node_execute`: Yields `{'execution_result': {'status': str, 'action': dict, 'error'?: str}}`
- `node_verify`: Yields `{'feedback': float}`

### Action Dictionary Execution (mapped in `node_execute`)

The executor requires deterministic mappings for specific string action types:
1. `set_parameter`: Invokes `vlm_controller.set_parameter(target, value)`
2. `click`: Invokes `vlm_controller.click(x, y)` from `coordinates`
3. `scroll`: Invokes `vlm_controller.scroll(direction, amount)`
4. `key_press`: Invokes `vlm_controller.key_press(key)`
5. `drag`: Invokes `vlm_controller.drag(start, end)`

### Visual Feedback Loop (mapped in `node_verify`)

If the action was `set_parameter`, `click`, or `drag`, `node_verify` compares the `pre_screenshot` to the post-action screenshot using `np.abs()`.
- If the mutation ratio `change_ratio > 0.01`: `feedback_score = min(1.0, 0.5 + change_ratio * 5)`
- Else: `feedback_score = 0.3`
If `>= 0.5`, the state is permanently saved into `memory_db.store_experience`.

---

## Edge Cases and Error Handling

### Missing Dependencies
- The `rewind()` method must handle an empty state history gracefully without throwing `IndexError`. If history is missing, return `None`.
- `node_verify` might fail to capture the post-screenshot (e.g., UI crashed). It must catch the exception, fallback to `feedback_score = 0.8` if execution status was `"success"`, else `0.3`, rather than halting the graph.

### Invalid Parameters
- Within `node_execute`, if `action_type` does not match the 5 known schemas, it attempts to duck-type `hasattr(vlm_controller, 'execute_action')`. If this fails, it must explicitly set `status` to `"unsupported"` and NOT throw an exception.
- If `planned_action` is `None` traversing into `node_execute`, immediately return `{"status": "skipped"}`.

### Resource Limits
- Thread configuration limits `config = {"configurable": {"thread_id": self.agent.card.agent_id}}`. As the DB checkpointer grows, `rewind()` must restrict index seeks mapping exactly to `min(steps, len(state_history) - 1)` to prevent history overflow bounds errors.

---

## Dependencies

### External Libraries
- `langgraph` (Requires explicit `StateGraph`, `END`, and `MemorySaver`).
- `numpy` for pixel differential calculations (`np.abs`, `np.mean`).

### Internal Modules
- Intimately coupled to the duck-typed submodules inside `self.agent`: `vlm_controller`, `memory_db`, `card`.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_graph_compilation` | Instantiating the class correctly builds a graph with 5 nodes matching the cyclic workflow path `perceive -> recall -> plan -> execute -> verify`. |
| `test_node_execute_unsupported` | Passing an action `{'type': 'teleport'}` yields `{'execution_result': {'status': 'unsupported'}}` if no custom fallback is present. |
| `test_node_verify_pixel_diff` | Passing a mock pre/post screenshot with `change_ratio=0.05` mathematically yields a `feedback` float of `0.75` for a click action. |
| `test_rewind_clamping` | Calling `rewind(steps=100)` when state history is only length `5` safely clamps to index `4`. |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR027: AgentOrchestrator` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- Preserve the precise mathematics inside the pixel-diff penalty checks in `node_verify` `(0.5 + change_ratio * 5)` and the fallback default constants (`0.7` for scroll, `0.3` for no change, `0.0` for error).
- Ensure explicit `async def` typing is retained for all 5 LangGraph node methods, as the `compile()` function evaluates async boundaries identically to legacy.

### Future Architecture Adjustments
- If `LlamaIndex` replaces `LangGraph` for VJLive3 core ML architecture, the entire `.graph` execution pipeline logic stringing the `_build_graph` dependencies must be refactored natively. Until that transition is explicitly greenlit by the user, emulate `LangGraph` precisely.
