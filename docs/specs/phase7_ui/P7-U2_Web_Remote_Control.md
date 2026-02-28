# Spec: P7-U2 — Web-Based Remote Control

**File naming:** `docs/specs/phase7_ui/P7-U2_Web_Remote_Control.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P7-U2 — Web Remote Control

**Phase:** Phase 7 / P7-U2
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Web Remote Control provides a browser-based interface for controlling VJLive3 from mobile devices, tablets, and computers. It exposes a WebSocket/HTTP API for real-time parameter control, plugin management, and performance monitoring, enabling remote control from anywhere on the network.

---

## What It Does NOT Do

- Does not replace the desktop GUI (complementary only)
- Does not handle authentication or user management (delegates to P7-B1)
- Does not provide collaborative features (delegates to P7-U3)
- Does not include advanced UI components (mobile-optimized only)

---

## Public Interface

```python
class WebRemoteControl:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None: ...
    
    def start_server(self) -> None: ...
    def stop_server(self) -> None: ...
    def is_running(self) -> bool: ...
    
    def register_plugin_controls(self, plugin_id: str, controls: List[ControlDef]) -> None: ...
    def unregister_plugin_controls(self, plugin_id: str) -> None: ...
    
    def set_parameter(self, plugin_id: str, param_name: str, value: Any) -> bool: ...
    def get_parameter(self, plugin_id: str, param_name: str) -> Any: ...
    
    def trigger_action(self, plugin_id: str, action: str, params: Dict) -> bool: ...
    
    def get_performance_stats(self) -> PerformanceStats: ...
    def get_plugin_list(self) -> List[str]: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `host` | `str` | Bind host address | Valid IP/hostname |
| `port` | `int` | Bind port | 1-65535 |
| `plugin_id` | `str` | Plugin identifier | Valid plugin |
| `controls` | `List[ControlDef]` | Control definitions | Valid controls |
| `param_name` | `str` | Parameter name | Valid parameter |
| `value` | `Any` | Parameter value | Valid for type |
| `action` | `str` | Action name | Valid action |
| `params` | `Dict` | Action parameters | Valid dict |

**Output:** `bool`, `Any`, `PerformanceStats`, `List[str]` — Various remote control results

---

## Edge Cases and Error Handling

- What happens if server fails to start? → Log error, retry with different port
- What happens if client disconnects? → Clean up session, log
- What happens if parameter invalid? → Return error to client
- What happens if rate limit exceeded? → Throttle or reject
- What happens on cleanup? → Stop server, close connections

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `websockets` — for WebSocket server — fallback: raise ImportError
  - `aiohttp` or `flask` — for HTTP server — fallback: raise ImportError
  - `json` — for message serialization — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.plugins.plugin_runtime`
  - `vjlive3.render.chain`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_server_start_stop` | Starts and stops server correctly |
| `test_plugin_registration` | Registers plugin controls |
| `test_parameter_set_get` | Sets and gets parameters remotely |
| `test_action_trigger` | Triggers actions remotely |
| `test_performance_stats` | Returns performance data |
| `test_client_connection` | Handles client connections |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-7] P7-U2: Web remote control` message
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

*Specification based on VJlive-2 web remote control module.*