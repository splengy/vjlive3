# Spec: P7-U3 — Collaborative Studio UI

**File naming:** `docs/specs/phase7_ui/P7-U3_Collaborative_Studio_UI.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P7-U3 — Collaborative Studio UI

**Phase:** Phase 7 / P7-U3
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Collaborative Studio UI enables multiple users to work together on the same VJLive3 project in real-time. It provides shared node graphs, synchronized parameter control, chat, presence indicators, and conflict resolution, allowing distributed VJ teams to collaborate on live performances and productions.

---

## What It Does NOT Do

- Does not handle user authentication (delegates to P7-B1)
- Does not provide version control (basic sync only)
- Does not include video conferencing (chat only)
- Does not manage licensing (delegates to P7-B2)

---

## Public Interface

```python
class CollaborativeStudioUI:
    def __init__(self, server_url: str, user_id: str) -> None: ...
    
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...
    
    def share_node_graph(self, graph: GraphDefinition) -> None: ...
    def sync_parameter(self, plugin_id: str, param_name: str, value: Any) -> None: ...
    
    def send_chat_message(self, message: str, recipient: Optional[str] = None) -> None: ...
    def get_chat_history(self) -> List[ChatMessage]: ...
    
    def get_participants(self) -> List[ParticipantInfo]: ...
    def get_user_cursor(self, user_id: str) -> Optional[Tuple[float, float]]: ...
    
    def lock_node(self, node_id: str) -> bool: ...
    def unlock_node(self, node_id: str) -> bool: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `server_url` | `str` | Collaboration server URL | Valid URL |
| `user_id` | `str` | Unique user identifier | Non-empty |
| `graph` | `GraphDefinition` | Node graph definition | Valid graph |
| `plugin_id` | `str` | Plugin identifier | Valid plugin |
| `param_name` | `str` | Parameter name | Valid parameter |
| `value` | `Any` | Parameter value | Valid for type |
| `message` | `str` | Chat message | Non-empty |
| `recipient` | `str` | Recipient user ID | Valid user |
| `node_id` | `str` | Node identifier | Valid node |

**Output:** `bool`, `List[ChatMessage]`, `List[ParticipantInfo]`, `Optional[Tuple[float, float]]` — Various collaboration results

---

## Edge Cases and Error Handling

- What happens if server unreachable? → Show offline mode, retry
- What happens if network latency high? → Show lag indicator
- What happens if two users edit same node? → Conflict resolution via locking
- What happens if chat message fails? → Queue for retry
- What happens on cleanup? → Disconnect, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `websockets` — for real-time communication — fallback: raise ImportError
  - `aiohttp` — for HTTP API — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.plugins.plugin_runtime`
  - `vjlive3.node_graph.node_graph_ui` (P1-N4)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_connection` | Connects to collaboration server |
| `test_node_graph_sync` | Syncs node graph changes |
| `test_parameter_sync` | Syncs parameter changes |
| `test_chat` | Sends and receives chat messages |
| `test_participants` | Shows participant list |
| `test_node_locking` | Locks and unlocks nodes |
| `test_edge_cases` | Handles disconnections gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-7] P7-U3: Collaborative Studio UI` message
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

*Specification based on VJlive-2 collaborative studio UI module.*