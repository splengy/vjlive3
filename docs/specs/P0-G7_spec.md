# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-G7 — Tool Tips Manager

**Phase:** Phase 0 / P0  
**Assigned To:** [Agent name]  
**Spec Written By:** [Agent name]  
**Date:** 2025-04-05

---

## What This Module Does

This module manages and renders contextual tool tips for users within the VJLive Reborn interface. It listens to user interactions (e.g., hovering over controls, selecting nodes) and dynamically displays descriptive, semantic tooltips using metadata from the UnifiedMatrix and Parameter contracts. Tooltips are rendered in real-time via the frontend's WebGL layer and synchronized across connected clients through Socket.IO.

---

## What It Does NOT Do

- It does not generate or modify effect parameters.
- It does not handle input parsing or signal routing.
- It does not manage hardware connections (e.g., camera, MIDI).
- It does not perform rendering of video content or effects.
- It does not store user preferences or history.

---

## Public Interface

```python
class ToolTipsManager:
    def __init__(self, matrix: UnifiedMatrix, socket_io: SocketIOClient) -> None: ...
    def on_hover(self, element_id: str, position: tuple[float, float]) -> None: ...
    def on_click(self, element_id: str) -> None: ...
    def update_tooltip(self, param_name: str, value: float, metadata: ParameterMetadata) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `matrix` | `UnifiedMatrix` | The central signal routing system for parameter access | Must be initialized with valid sources/destinations |
| `socket_io` | `SocketIOClient` | Client to broadcast tooltip events to other UIs and agents | Must support `tooltip_show`, `tooltip_hide` events |
| `element_id` | `str` | Unique identifier of UI element (e.g., "lfo-1", "effect-param-3") | Must match registered control in the UI tree |
| `position` | `tuple[float, float]` | Mouse position relative to screen (x, y) | Range: 0.0–100.0; must be valid for rendering |
| `param_name` | `str` | Name of parameter being viewed | Must exist in UnifiedMatrix or raise KeyError |
| `value` | `float` | Current value of the parameter (0.0 to 10.0) | Must be within [0.0, 10.0] range |
| `metadata` | `ParameterMetadata` | Semantic description and context for the parameter | Required; includes title, units, category |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → (NullDevice pattern / graceful fallback)  
  If a required source (e.g., audio input) is unavailable, the tooltip will display a generic "Unavailable" message using default metadata.

- What happens on bad input? → (raise ValueError with message)  
  - Invalid `element_id` → raise `ValueError("Unknown UI element")`  
  - Parameter not found in matrix → raise `KeyError(f"Parameter {param_name} not found")`  
  - Value outside [0.0, 10.0] → raise `ValueError("Parameter value out of range")`

- What is the cleanup path? → (close(), __exit__, resource release)  
  On shutdown or disconnect: emits `tooltip_hide` to all clients and clears internal tooltip cache.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `socket.io-client` — used for real-time UI sync — fallback: local-only rendering with no broadcast  
  - `pydantic` — used to validate metadata schema — fallback: use minimal default fields  

- Internal modules this depends on:  
  - `vjlive1.signal.UnifiedMatrix` — for accessing parameter metadata and current values  
  - `vjlive1.data.ParameterMetadata` — defines tooltip content structure  
  - `vjlive1.ui.ElementRegistry` — to validate element_id against known UI controls

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_with_valid_matrix` | Module initializes without error when given a valid UnifiedMatrix and socket client |
| `test_hover_no_tooltip` | No tooltip is shown if no matching parameter exists for the element_id |
| `test_hover_with_parameter` | Tooltip displays correct title, value, and units from metadata on hover |
| `test_click_triggers_update` | Clicking an element updates internal state and emits a valid `tooltip_show` event |
| `test_error_on_missing_param` | Raises KeyError when attempting to access a non-existent parameter |
| `test_value_range_validation` | Rejects values outside [0.0, 10.0] with ValueError |
| `test_cleanup_emits_hide_event` | On close(), emits `tooltip_hide` event to all connected clients |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-G7: Tool Tips Manager` message  
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
4.  **Render**: Next frame uses new value.  
5.  **Broadcast**: Engine emits `state_change` to all other