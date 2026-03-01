# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-G2 — Safety Rails Module

**Phase:** Phase 0 / P0  
**Assigned To:** Alex Chen  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-03

---

## What This Module Does

The Safety Rails module enforces runtime safety constraints on all parameter modifications within the VJLive Reborn system, ensuring that no operation violates predefined thresholds or behavioral rules. It acts as a middleware layer between user input and the UnifiedMatrix, validating every `param_update` event before propagation to prevent instability, hardware damage, or unintended visual artifacts. The module maintains a configurable set of safety policies—such as rate limits, value bounds, and temporal constraints—that are enforced in real time across all connected clients.

---

## What It Does NOT Do

- It does not perform rendering or effect processing.
- It does not manage plugin loading or unloading.
- It does not handle video input/output routing.
- It does not provide UI controls or visual feedback to users.
- It does not replace the UnifiedMatrix or Socket.IO communication layer.

---

## Public Interface

```python
class SafetyRails:
    def __init__(self, config: dict) -> None: ...
    def validate_param_update(self, param_name: str, value: float, source: str) -> bool: ...
    def apply_rate_limit(self, param_name: str, value: float, timestamp: float) -> float: ...
    def enforce_value_bounds(self, value: float, min_val: float, max_val: float) -> float: ...
    def log_event(self, event_type: str, details: dict) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `dict` | Configuration of safety policies (rate limits, bounds, thresholds) | Must contain keys: `value_bounds`, `rate_limits`, `thresholds`, `allowed_sources` |
| `param_name` | `str` | Name of the parameter being updated | Must match a registered parameter in UnifiedMatrix; case-sensitive |
| `value` | `float` | Proposed value for the parameter (0.0–10.0) | Must be within 0.0 to 10.0 range unless overridden by policy |
| `source` | `str` | Origin of the update (e.g., "MIDI", "Agent", "WebUI") | Must be in allowed_sources list; otherwise rejected |
| `timestamp` | `float` | Time of update in seconds since epoch | Must be valid float, not NaN or infinite |
| `return_value` | `float` | Final validated value after all checks | Always within 0.0–10.0 range unless policy allows override |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → (NullDevice pattern / graceful fallback)  
  The module does not depend on hardware state; it operates purely on parameter validation logic. If a source is invalid or unreachable, the update is rejected with a log entry and no action taken.

- What happens on bad input? → (raise ValueError with message)  
  Invalid `param_name`, out-of-range `value`, or malformed `config` will raise a `ValueError` with a descriptive message. For example: `"Invalid parameter name: 'invalid_param'"`.

- What is the cleanup path? → (close(), __exit__, resource release)  
  The module has no external resources to close. It does not maintain file handles, sockets, or timers. On shutdown, it only clears internal state and logs a final audit event.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `pydantic` — used for config validation — fallback: manual schema checks using basic type guards  
  - `logging` — used for event logging — fallback: silent mode with no output  

- Internal modules this depends on:  
  - `vjlive1.signal.UnifiedMatrix` — to validate parameter existence and retrieve metadata  
  - `vjlive1.core.EngineCore` — to access real-time state and detect source legitimacy  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_with_valid_config` | Module initializes without error using a valid config dictionary |
| `test_validate_param_update_invalid_name` | Rejects update with invalid parameter name; raises ValueError |
| `test_validate_param_update_out_of_range` | Rejects value outside 0.0–10.0 range when bounds are enforced |
| `test_apply_rate_limit_exceeds_threshold` | Applies rate limiting and returns clamped value if too frequent |
| `test_enforce_value_bounds_with_override` | Allows override only if explicitly permitted in policy |
| `test_log_event_success` | Logs an event with correct structure and timestamp |
| `test_validate_source_not_allowed` | Rejects update from source not in allowed_sources list |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-G2: Safety Rails module enforces parameter validation` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

[NEEDS RESEARCH]: Policy enforcement for agent-driven inputs (e.g., AI agents with unbounded behavior)  
[NEEDS RESEARCH]: Integration with real-time performance monitoring and feedback loops  
[NEEDS RESEARCH]: How to define "safe" thresholds dynamically based on system load or hardware state