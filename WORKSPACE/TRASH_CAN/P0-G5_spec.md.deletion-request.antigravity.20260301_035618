# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-G5 — Workspace Communications Decisions

**Phase:** Phase 0 / P0  
**Assigned To:** Alex Chen  
**Spec Written By:** Jordan Lee  
**Date:** 2024-04-10

---

## What This Module Does

This module defines the communication protocols, decision rules, and governance structure for how agents and human users interact within the VJLive Reborn workspace. It establishes standards for message formatting, routing logic, and conflict resolution in real-time parameter and state sharing across devices, agents, and UIs. The module ensures consistency with the Signal Standard (0.0–10.0 float range) and supports multi-node synchronization via LAN-based frame-accurate sync.

---

## What It Does NOT Do

- It does not implement actual message routing or network transport — that is handled by `vjlive1/COMMS/TRANSPORT.py`.
- It does not manage UI rendering or visual feedback — this belongs to the frontend (`vjlive1/FRONTEND`).
- It does not define plugin behavior or effect logic — those are governed by the Plugin System in `vjlive1/PLUGINS`.
- It does not handle hardware input capture (e.g., camera, MIDI) — that is managed by the Input/Output module.

---

## Public Interface

```python
class WorkspaceCommunicationsDecisions:
    def __init__(self, node_id: str, cluster_mode: bool = False) -> None: ...
    def resolve_conflict(self, source_a: str, source_b: str, param_name: str, value_a: float, value_b: float) -> float: ...
    def broadcast_decision(self, decision: dict, target_nodes: list[str]) -> bool: ...
    def validate_message_format(self, message: dict) -> tuple[bool, str]: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `node_id` | `str` | Unique identifier for this node in the cluster | Must be 1–32 alphanumeric characters; must match pattern `[a-z0-9]+` |
| `cluster_mode` | `bool` | Whether this node is part of a multi-node cluster | Default: False. If True, requires frame-sync enabled via `SyncManager`. |
| `source_a`, `source_b` | `str` | IDs of conflicting input sources (e.g., agent or UI) | Must be valid source names registered in UnifiedMatrix |
| `param_name` | `str` | Name of the parameter being contested | Must match Parameter name schema: `[a-z_][a-z0-9_]*(?<!\s)` |
| `value_a`, `value_b` | `float` | Values from conflicting sources (in 0.0–10.0 range) | Must be within [0.0, 10.0]; otherwise rejected |
| `decision` | `dict` | Final decision payload to broadcast | Must include `"action"`, `"value"`, and `"source"` keys |
| `target_nodes` | `list[str]` | List of node IDs to send the decision to | May be empty; if non-empty, must contain valid node IDs |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → (NullDevice pattern / graceful fallback)  
  If a source node is unreachable or offline, the module returns a default value of `5.0` for contested parameters and logs a warning via `Logger.warn("source_unreachable")`.

- What happens on bad input? → (raise ValueError with message)  
  Invalid parameter names or values outside [0.0, 10.0] raise `ValueError("Invalid parameter format: {error}")`. Message includes the invalid field and value.

- What is the cleanup path? → (close(), __exit__, resource release)  
  On shutdown, the module emits a `node_shutdown` event to all connected agents via Socket.IO and releases any held references to active nodes. No memory leaks are permitted due to strict state propagation rules.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `socket.io-client` — used for bi-directional message routing — fallback: local file-based logging only  
  - `pydantic` — used for message schema validation — fallback: basic string checks with no schema enforcement  

- Internal modules this depends on:  
  - `vjlive1/ARCHITECTURE.md` — for signal standard and parameter contract definitions  
  - `vjlive1/SIGNAL_SYSTEM.py` — to validate parameter names and value ranges  
  - `vjlive1/MULTI_NODE_SYNC.py` — for cluster-level frame sync decisions  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_cluster_mode` | Module starts without crashing if cluster mode is disabled |
| `test_resolve_conflict_equal_values` | When both sources provide same value, returns that value unchanged |
| `test_resolve_conflict_different_values` | Returns weighted average (50/50) when values differ and no preference defined |
| `test_broadcast_to_empty_list` | Broadcast succeeds even with empty target list |
| `test_validate_message_format_valid` | Valid message passes validation without error |
| `test_validate_message_format_invalid_param_name` | Invalid parameter name raises correct ValueError |
| `test_resolve_conflict_out_of_range_value` | Values outside [0.0, 10.0] are rejected and logged |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-G5: Workspace Communications Decisions` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 0, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L1-20)  
```python
# VJLive Reborn — Architecture Reference

## Overview
VJLive Reborn is a professional-grade real-time Visual Jockey (VJ) application designed for high-performance video synthesis, effect processing, and projection mapping. It is built as a hybrid system with a high-performance Python/OpenGL backend and a modern React-based frontend, designed from the ground up for deep collaboration between human artists and AI agents.

## Core Principles
1.  **60 FPS is Sacred**: The rendering pipeline must never drop frames. All heavy compute is offloaded or time-sliced.
2.  **The One State**: The application state is unified and singular. Whether accessed via the Node Graph, the Matrix, the WebSocket API, or the Lumen scripting language, the state is identical.
3.  **Agent-Native**: First-class support for AI agents to observe, advise, and pilot the system. All parameters include semantic metadata for agents.
4.  **Signal Standard**: All modulated parameters at I/O boundaries use a normalized `0.0` to `10.0` float range.
```

### vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L17-36)  
```python
-   **Communication**: Socket.IO (Async) for bi-directional state sync
-   **Data Storage**: Vector DB (for agent memory/performance recordings)

### Frontend (The Shell)
-   **Framework**: React
-   **Styling**: Tailwind CSS
-   **Communication**: `socket.io-client`
-   **Visualization**: WebGL for GUI replications of the main output
```

### vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L33-52)  
```python
### 2. The Signal System (Matrix)
-   **UnifiedMatrix**: The central router for all parameter modulation.
-   **Sources**: LFOs, Audio Analysis, External MIDI/OSC, Agent Inputs.
-   **Destinations**: Effect Parameters.
-   **Standard**: 0.0 - 10.0 float.

### 3. The Plugin System
-   **Format**: Standalone `.vjfx` packages.
-   **Interface**: Strict contract for parameter discovery and rendering.
-   **Hot-Loading**: Plugins can be loaded/unloaded at runtime without restarting the engine.

### 4. Input/Output
-   **Video**: Camera inputs, Video files, NDI.
-   **Control**: MIDI, OSC, WebSocket, Lumen Script.
-   **Output**: HDMI (local), NDI (network), Web Stream (preview).
```

### vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L49-68)  
```python
### 5. Multi-Node Architecture
-   **Hardware**: optimized for ARM-based SBCs (Orange Pi 5/6).
-   **Cluster