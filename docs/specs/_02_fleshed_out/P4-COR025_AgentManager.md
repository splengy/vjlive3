# P4-COR025_AgentManager.md

**Phase:** Phase 4 / P4-COR025  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR025 — AgentManager

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `VJlive-2/core/extensions/agents/agent_manager.py`  
**Legacy Class:** `AgentManager`  

---

## What This Module Does

`AgentManager` is the primary Dependency Injection (DI) hub and initialization orchestrator for the entire Agent Performance Subsystem. During application startup, it consumes a reference to the global `app_context` to instantiate, bind, and monkey-patch all high-level AI dependencies, including `AgentPerformanceBridge`, `PerformanceAgent`, `PerceptionBuffer`, `GravityWellAPI`, and the `LUMEN` Scripting engine. It also manages the automatic parsing and execution of the default `.lumen` show script on boot.

---

## What It Does NOT Do

- Does NOT contain active processing loops (it simply instantiates the worker objects and attaches them back to `self.app`).
- Does NOT own the instances long-term; it serves as a bootstrapping factory.
- Does NOT load visual UI components directly.

---

## Public Interface

```python
from typing import Any, Optional
from vjlive3.plugins.base import BasePlugin

class AgentManager(BasePlugin):
    """
    Manages the initialization and lifecycle of the Agent Performance System.
    Acts as a Dependency Injection hub binding AI components to the global application context.
    """
    
    METADATA = {
        "id": "AgentManager",
        "type": "manager",
        "version": "1.0.0",
        "legacy_ref": "agent_manager (AgentManager)"
    }
    
    def __init__(self, app_context: Any) -> None:
        """Stores the initial app context and nullifies system references."""
        pass
        
    def initialize(self) -> None:
        """
        Instantiates specific AI subsystems and attaches them back onto the
        app_context. Also handles initializing the LUMEN evaluator callbacks.
        """
        pass
        
    def load_default_lumen_script(self) -> None:
        """
        Attempts to read and execute the first `.lumen` script found in the
        standard `show_scripts` directory.
        """
        pass
```

---

## Inputs and Outputs

### Constructor Parameters

| Name | Type | Description |
|------|------|-------------|
| `app_context` | `Any` | Weakly-typed duck-typing interface. Expected to contain attributes: `mood_manifold`, `websocket_gateway`, `effect_chain`, `audio_reactor`, `audio_analyzer`, `config`, `fps`, `node_graph_bridge`. |

### `initialize()` State Mutations

This method fundamentally mutates the `app_context` object passed during initialization. It instantiates the following systems and dynamically attaches them using `setattr(self.app, name, instance)` logic:
1. `self.app.agent_bridge = AgentPerformanceBridge(...)`
2. `self.app.performance_agent = PerformanceAgent(...)`
3. `self.app.perception_buffer = PerceptionBuffer(...)`
4. `self.app.telemetry_streamer = TelemetryStreamer()`
5. `self.app.perception_stream_telemetry = PerceptionStreamTelemetry(...)`
6. `self.app.gravity_well_api = GravityWellAPI(...)`
7. `self.app.intent_vectorizer = IntentVectorizer(...)`
8. `self.app.script_executor = ScriptExecutor(...)`

_Note: It also conditionally connects `self.app.agent_avatar` and `self.app.text_overlay` to the `AgentBridge` if those attributes exist on the context._

---

## Edge Cases and Error Handling

### Missing Dependencies
- The `load_default_lumen_script` method relies on filesystem access to `./show_scripts`. If this directory does not exist, or contains no `.lumen` files, the method must log a debug message and exit safely without raising `FileNotFoundError` or crashing the startup sequence.
- During conditional hookups (avatar and overlay), it must use `hasattr(self.app, 'agent_avatar')` to prevent `AttributeError` crashes if the UI layers failed to load earlier in the boot sequence.

### Invalid Parameters
- `app_context.config.system.llm_provider/model` might be malformed. The `PerformanceAgent` initialization passes these blindly; it is the responsibility of `PerformanceAgent` to handle bad API keys, not the Manager.

---

## Dependencies

### External Libraries
- `os` (standard library) for path resolution of LUMEN scripts.

### Internal Modules
- Intimately coupled to the initialization signatures of:
    - `AgentPerformanceBridge`
    - `PerformanceAgent`
    - `PerceptionBuffer`
    - `GravityWellAPI`
    - `IntentVectorizer`, `LUMENScriptParser`, `ScriptExecutor`
    - `TelemetryStreamer`, `PerceptionStreamTelemetry`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_initialization_state_mutations` | Passes a Mock `app_context` into `initialize()` and asserts that `app.agent_bridge` and all other AI systems are successfully bound as attributes. |
| `test_conditional_ui_hookups` | If `app_context` has Mock `agent_avatar`, asserts `set_agent_bridge` is called on the avatar. |
| `test_missing_lumen_directory` | Temporarily patches `os.path.exists` to return `False`. Asserts `load_default_lumen_script` logs a debug string and exits without error. |
| `test_lumen_auto_load_success` | Patches filesystem and file reads to return a fake script, asserts `performance_agent.load_script()` and `start_execution()` are called. |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 300 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR025: AgentManager` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- Preserve the lazy binding format `fps_getter=lambda: self.app.fps`. Because `fps` fluctuates, passing it by value at startup would break metrics.
- Keep the `graph_callbacks` mapping dictionary in `ScriptExecutor` instantiation exactly matched to the legacy hook paths (`_on_graph_add_node`, etc.).

### Porting Strategy
This file is the literal architectural "glue" of the AI system. Because VJLive3 utilizes a new plugin loader architecture, the implementation engineer must ensure the `AgentManager` hooks into VJLive3's main initialization phase cleanly, likely after the `NodeGraph` is constructed but before the UI launches.
