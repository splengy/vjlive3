# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-G6 — Dreamer Log Module

**Phase:** Phase 0 / P0  
**Assigned To:** Alex Chen  
**Spec Written By:** Samira Patel  
**Date:** 2025-04-03

---

## What This Module Does

The Dreamer Log Module captures, stores, and retrieves agent-generated creative outputs—such as visual ideas, performance suggestions, or narrative fragments—during live VJ sessions. It acts as a persistent memory layer for AI agents, enabling them to reference past decisions and generate contextually relevant content in real time. The module logs all dream-like outputs using structured metadata tied to timestamps, session IDs, and parameter states from the UnifiedMatrix.

---

## What It Does NOT Do

- It does not perform real-time rendering or effect processing.
- It does not directly control hardware (e.g., video output, MIDI).
- It does not generate new visual content; it only stores and retrieves agent-generated ideas.
- It is not responsible for user interface display of logs—this is handled by the frontend via WebSocket events.

---

## Public Interface

```python
class DreamerLog:
    def __init__(self, session_id: str, storage_path: str) -> None: ...
    def record_dream(self, dream_content: dict, metadata: dict) -> bool: ...
    def retrieve_dreams(self, query: str = "", limit: int = 10) -> list[dict]: ...
    def delete_session(self, session_id: str) -> bool: ...
    def get_metadata_schema(self) -> dict: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `session_id` | `str` | Unique identifier for a live performance session | Must be 8–32 characters, alphanumeric only |
| `storage_path` | `str` | Directory where log files are stored | Must exist and be writable; defaults to `./logs/dreamer/` |
| `dream_content` | `dict` | Agent-generated creative output (e.g., "a swirling nebula with pulsing red veins") | Required field; must contain `"text"` key |
| `metadata` | `dict` | Contextual data tied to the dream entry | Must include `"timestamp"`, `"agent_id"`, and optional `"source_param"` |
| `query` | `str` | Search string for retrieving dreams (e.g., "nebula", "motion") | Case-insensitive; supports partial matches |
| `limit` | `int` | Maximum number of results to return | Range: 1–100; default = 10 |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → (NullDevice pattern / graceful fallback)  
  If the storage path is inaccessible or filesystem errors occur, the module logs a warning via `logger.warning()` and continues accepting new entries in memory until recovery.

- What happens on bad input? → (raise ValueError with message)  
  - Invalid session_id format: raises `ValueError("Invalid session ID format")`  
  - Missing required metadata fields (`timestamp`, `agent_id`): raises `ValueError("Missing required metadata field")`  
  - Query exceeds length limit (e.g., >256 chars): raises `ValueError("Query too long")`

- What is the cleanup path? → (close(), __exit__, resource release)  
  On shutdown, all in-memory entries are flushed to disk. The module calls `os.sync()` on the log directory and emits a `log_cleanup` event via Socket.IO for frontend awareness.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `pyyaml` — used for structured logging of dream content — fallback: JSON serialization with error logging  
  - `python-dotenv` — for loading environment variables (e.g., LOG_STORAGE_PATH) — fallback: default path in config  

- Internal modules this depends on:  
  - `vjlive1.architecture.UnifiedMatrix` — to retrieve parameter state context when storing dreams  
  - `vjlive1.communication.socket_io_client` — to broadcast log events to agents and UI clients  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_with_valid_session_id` | Module initializes without crashing with valid session ID and path |
| `test_record_dream_with_complete_metadata` | Dream is successfully recorded with full metadata and stored in file |
| `test_retrieve_dreams_by_query` | Query returns relevant dreams matching text content |
| `test_error_on_missing_timestamp` | Raises ValueError when required metadata field is missing |
| `test_cleanup_after_shutdown` | All pending entries are flushed to disk on close() call |
| `test_fallback_to_memory_on_disk_failure` | When storage fails, logs entry in memory and warns user |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-G6: Dreamer Log Module` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

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

### vjlive1/WORK