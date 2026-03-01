# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-G4 — Lock Management System

**Phase:** Phase 0 / P0  
**Assigned To:** Alex Chen  
**Spec Written By:** Jordan Reed  
**Date:** 2025-04-03

---

## What This Module Does

The Lock Management System provides a centralized, thread-safe mechanism for managing access to shared resources across VJLive Reborn’s distributed architecture. It enables safe coordination between the frontend (React), backend (Python engine), and agent components when accessing critical system state or hardware interfaces. The module ensures that only one component can modify a resource at a time, preventing race conditions during high-frequency parameter updates or multi-node synchronization.

---

## What It Does NOT Do

- It does not implement authentication or authorization for access to locks.
- It does not manage user sessions or identity.
- It does not provide distributed consensus (e.g., Raft or Paxos).
- It does not handle network-level locking across firewalled domains.
- It is not responsible for hardware power management or device enumeration.

---

## Public Interface

```python
class LockManager:
    def __init__(self, lock_name: str) -> None: ...
    def acquire(self, timeout: float = 30.0) -> bool: ...
    def release(self) -> None: ...
    def is_locked(self) -> bool: ...
    def wait_for_release(self, timeout: float = 30.0) -> bool: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `lock_name` | `str` | Unique identifier for the lock (e.g., "unified_matrix", "camera_input") | Must be non-empty, max 64 chars. Must match a registered resource in the system. |
| `timeout` | `float` | Maximum time to wait for lock acquisition or release | Positive value; default is 30.0 seconds. Must not exceed 120.0 seconds. |
| `lock_name` (input) | `str` | Used as key to identify the resource being locked | Must be a valid identifier from the Parameter Contract or Hardware Registry |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Use NullDevice pattern: lock acquisition fails silently, but no crash. The system continues with fallback values via `UnifiedMatrix` defaults.
- What happens on bad input? → If `lock_name` is invalid or empty, raise `ValueError("Invalid lock name")`.
- What is the cleanup path? → On process exit, all locks are released automatically via `__del__()` and a background cleanup thread. If release fails due to timeout, log warning but do not block shutdown.

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `threading` — used for lock primitives — fallback: built-in Python threading
  - `time` — for timeouts and delays — fallback: standard library
- Internal modules this depends on:
  - `vjlive1.core.signal.UnifiedMatrix`
  - `vjlive1.hardware.registry.HardwareRegistry`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_acquire_release_basic` | Lock can be acquired and released without error in a single operation |
| `test_acquisition_timeout` | Timeout behavior correctly returns False when lock not available within limit |
| `test_concurrent_acquisition` | Two threads attempting to acquire same lock fail after first success |
| `test_lock_name_validation` | Invalid or empty lock names raise correct ValueError |
| `test_cleanup_on_exit` | Locks are released during process shutdown even if acquisition failed |
| `test_wait_for_release` | Wait function returns True only when lock is freed within timeout |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-G4: Lock Management System` message  
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
5.  **Broadcast**: Engine emits `state_change` to all other connected clients (Agents, other Web UIs).
```

### vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L73-end)
```python
## Directory Structure
(See `WORKSPACE/` for the authoritative file structure during rebuild)
```