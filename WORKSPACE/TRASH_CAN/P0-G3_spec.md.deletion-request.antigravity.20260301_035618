# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-G3 — Agent Sync Module

**Phase:** Phase 0 / P0  
**Assigned To:** Alex Chen  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-05

---

## What This Module Does

The Agent Sync Module enables real-time, frame-accurate synchronization of AI agent states across multiple VJLive nodes in a cluster. It ensures that all agents observe and respond to the same system state—such as parameter values, effect chains, or input signals—using a unified signal propagation model derived from the UnifiedMatrix. This module establishes bidirectional communication via Socket.IO to maintain consistency between local and remote agent instances during collaborative performance.

---

## What It Does NOT Do

- It does not handle video rendering or playback.
- It does not manage plugin loading or effect execution.
- It does not process audio input/output.
- It does not provide user interface components (UI elements are handled by the frontend).
- It does not store agent memory or performance history—this is managed by the Vector DB.

---

## Public Interface

```python
class AgentSyncModule:
    def __init__(self, node_id: str, cluster_address: str, socket_io_client) -> None: ...
    def start_sync(self) -> None: ...
    def stop_sync(self) -> None: ...
    def broadcast_state_change(self, state: dict) -> None: ...
    def receive_param_update(self, param_name: str, value: float, source: str) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `node_id` | `str` | Unique identifier for this node in the cluster | Must be 1–32 characters; alphanumeric only |
| `cluster_address` | `str` | IP address or hostname of the cluster leader | Must be valid IPv4 or FQDN; reachable via UDP/TCP port 8080 |
| `socket_io_client` | `socketio.Client` | Socket.IO client instance for bi-directional communication | Required; must support event emission and listening |
| `state` | `dict` | Full system state to broadcast (includes parameter values) | Must conform to UnifiedMatrix schema with all values in 0.0–10.0 range |
| `param_name` | `str` | Name of the parameter being updated | Must match Parameter.name from UnifiedMatrix contract |
| `value` | `float` | New value for the parameter (0.0 to 10.0) | Must be within [0.0, 10.0]; otherwise rejected |
| `source` | `str` | Origin of the update (e.g., "agent-ai", "user-ui", "lfo") | Must be one of: ["agent-ai", "user-ui", "lfo", "osc"] |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Uses NullDevice pattern; sync remains active but no local state updates are applied.  
- What happens on bad input? → If `value` is outside [0.0, 10.0], raises `ValueError("Parameter value out of range")`. If `param_name` does not exist in UnifiedMatrix, logs warning and skips update.  
- What is the cleanup path? → `stop_sync()` closes the Socket.IO connection gracefully, unsubscribes from all events, and releases any allocated cluster references. On exit, emits a final `sync_shutdown` event to all connected agents.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `socketio` — used for real-time bi-directional communication — fallback: use polling with 100ms delay if Socket.IO fails  
  - `pydantic` — validates input state schema — fallback: disable strict validation, log warnings  
- Internal modules this depends on:  
  - `vjlive1.core.UnifiedMatrix` — for accessing parameter values and source metadata  
  - `vjlive1.signal.Parameter` — to validate incoming parameter types and ranges  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_with_valid_cluster_address` | Module initializes successfully with valid cluster address and node ID |
| `test_start_sync_emits_state_change_event` | After start_sync(), a state_change event is emitted to connected agents |
| `test_receive_param_update_valid_value` | A parameter update within [0.0, 10.0] is correctly received and logged |
| `test_receive_param_update_out_of_range` | An invalid value (e.g., 20.5) raises a ValueError with clear message |
| `test_stop_sync_closes_socket_io` | stop_sync() closes the socket connection without errors |
| `test_broadcast_state_change_with_full_schema` | Full system state is broadcast in correct format matching UnifiedMatrix schema |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-G3: Implement Agent Sync Module` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

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
```

### vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L49-68)
```python
### 5. Multi-Node Architecture
-   **Hardware**: optimized for ARM-based SBCs (Orange Pi 5/6).  
-   **Cluster**: Multiple nodes can link to form a larger display surface or share compute.  
-   **Sync**: Frame-accurate synchronization across the LAN.

## Data Model

### The Parameter Contract
Every controllable property is a **Parameter**.
```python
class Parameter:
    name: str
    value: float (0.0 - 10.0)
    meta: ParameterMetadata
```

### State Propagation
1.  **Input**: User slides a fader on Web UI.  
2.  **Network**: Socket.IO event `param_update` sent to Engine.  
3.  **Engine**: Updates `UnifiedMatrix`.  
```

### vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L65-73)
```python
### State Propagation
1.  **Input**: User slides a fader on Web UI.  
2.  **Network**: Socket.IO event `param_update` sent to Engine.  
3.  **Engine**: Updates `UnifiedMatrix`.  
4.  **Render**: Next frame uses new value.  
5.  **Broadcast**: Engine emits `state_change` to all other connected clients (Agents