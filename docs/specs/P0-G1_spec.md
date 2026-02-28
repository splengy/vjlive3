# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-G1 — Prime Directive Module

**Phase:** Phase 0 / P0  
**Assigned To:** Alex Chen  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-03

---

## What This Module Does

The Prime Directive Module establishes the foundational behavioral and architectural principles that govern all components of VJLive Reborn. It enforces core system invariants—such as frame rate fidelity, unified state consistency, and signal standardization—across the entire application stack. By defining these non-negotiable rules at the system level, it ensures that every module, plugin, and agent operates within a predictable and interoperable framework.

---

## What It Does NOT Do

- It does not implement rendering or effect processing logic.
- It does not handle user input or UI state management.
- It does not manage hardware connections or network synchronization directly.
- It does not provide real-time parameter modulation or signal routing.
- It is not a plugin, driver, or service—it serves as a declarative policy layer.

---

## Public Interface

```python
class PrimeDirective:
    def __init__(self) -> None: ...
    def validate_state(self, state: dict) -> bool: ...
    def enforce_signal_standard(self, value: float) -> float: ...
    def is_framing_sacred(self) -> bool: ...
    def get_system_invariants(self) -> dict: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `state` | `dict[str, Any]` | System state to validate | Must contain all required keys; values must be numeric or boolean |
| `value` | `float` | Parameter value for standardization | Range: 0.0–10.0 inclusive |
| `system_invariants` | `dict[str, bool]` | List of enforced system rules | Output only; immutable after initialization |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → [NEEDS RESEARCH]  
- What happens on bad input? → Raises `InvalidStateError` with message "State violates core invariants" if `validate_state()` fails.  
- What is the cleanup path? → No explicit cleanup; module is stateless and initialized once at startup.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `socketio` — used for state propagation monitoring — fallback: disabled, no warnings  
  - `pydantic` — used to validate parameter types — fallback: basic type checks only  
- Internal modules this depends on:  
  - `vjlive1.engine.UnifiedMatrix` — for signal validation  
  - `vjlive1.signal.ParameterMetadata` — for metadata consistency checking  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_validate_state_with_valid_input` | Core state invariants are respected when input matches expected schema |
| `test_enforce_signal_standard_range` | Values outside 0.0–10.0 are clipped to bounds and logged |
| `test_is_framing_sacred_returns_true` | The "60 FPS is Sacred" principle is correctly enforced at runtime |
| `test_get_system_invariants_returns_expected_keys` | All defined invariants (e.g., frame rate, signal range) are returned as expected |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-G1: Prime Directive Module enforces system invariants` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

**Legacy Code References**

> *From vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L1-20):*  
> "VJLive Reborn is a professional-grade real-time Visual Jockey (VJ) application... Core Principles: 60 FPS is Sacred, The One State, Agent-Native, Signal Standard."

> *From vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L17-36):*  
> "Communication: Socket.IO (Async) for bi-directional state sync. Data Storage: Vector DB (for agent memory/performance recordings)."

> *From vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L33-52):*  
> "UnifiedMatrix: central router for all parameter modulation. Sources: LFOs, Audio Analysis, External MIDI/OSC, Agent Inputs. Destinations: Effect Parameters. Standard: 0.0 - 10.0 float."

> *From vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L49-68):*  
> "Multi-Node Architecture: optimized for ARM-based SBCs (Orange Pi 5/6). Cluster: multiple nodes link to form larger display surface or share compute. Sync: frame-accurate across LAN."

> *From vjlive1/WORKSPACE IGNORE OLD /ARCHITECTURE.md (L65-73):*  
> "The Parameter Contract: Every controllable property is a Parameter. Class Parameter: name, value (float 0.0–10.0), meta. State Propagation: Input → Network → Engine → UnifiedMatrix → Render → Broadcast."