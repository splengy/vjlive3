# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-G8 — Root PRIME_DIRECTIVE.md

**Phase:** Phase 1 / P1-H1  
**Assigned To:** Alex Turner  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-05

---

## What This Module Does

The `RootPRIMEDIRECTIVE` module establishes the foundational operational directive for all VJLive system components. It defines and enforces a core principle governing signal processing, hardware interaction, and user interface behavior—specifically ensuring that all modules operate under a consistent, prioritized logic chain: *input validation → signal routing → output fidelity*. This serves as the root policy layer from which other modules derive their behavioral rules.

---

## What It Does NOT Do

- It does not perform actual signal processing or computation.  
- It does not manage hardware drivers or device connections directly.  
- It does not provide visualizations, UI components, or real-time feedback.  
- It does not implement logic gates, thresholds, or analog comparisons.  
- It is not a runtime executor or scheduler.

---

## Public Interface

```python
class RootPRIMEDIRECTIVE:
    def __init__(self, directive: str = "DEFAULT") -> None: ...
    def validate_input(self, input_signal: dict) -> bool: ...
    def enforce_policy(self, signal_path: list) -> dict: ...
    def log_directive_action(self, action: str, context: dict) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `directive` | `str` | Primary operational policy string (e.g., "DEFAULT", "SECURE", "FAST") | Must be one of ["DEFAULT", "SECURE", "FAST"], default is "DEFAULT" |
| `input_signal` | `dict` | Dictionary containing signal metadata: { "source": str, "value": float, "timestamp": float } | Required; value must be numeric and timestamp ≥ 0 |
| `signal_path` | `list[dict]` | List of signal nodes with metadata (e.g., {"node": str, "type": str, "status": bool}) | Must not contain null or empty entries; length ≥ 1 |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → [NEEDS RESEARCH]  
- What happens on bad input? → `validate_input()` raises `ValueError` with message: `"Invalid signal format: expected numeric value"`  
- What is the cleanup path? → No explicit cleanup; module state is preserved and reentrant. On destruction, logs final directive action via `log_directive_action("SHUTDOWN", {})`.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `logging` — used for policy enforcement logging — fallback: console output only  
  - `json` — used to parse signal path metadata — fallback: raw string parsing with error handling  
- Internal modules this depends on:  
  - [NEEDS RESEARCH]  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_default_directive` | Module initializes with default directive "DEFAULT" without exception |
| `test_validate_input_valid` | Valid signal input returns True and passes schema validation |
| `test_validate_input_invalid` | Invalid signal (non-numeric value) raises ValueError with correct message |
| `test_enforce_policy_standard_path` | Standard signal path is processed correctly under DEFAULT policy |
| `test_enforce_policy_secure_mode` | Secure mode enforces stricter input filtering than default |
| `test_log_directive_action` | Action log entry is written to internal logger when directive changes |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-1] P0-G8: Root PRIME_DIRECTIVE module specification` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 1, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

--- 

> **Note:** This specification is derived from the legacy UI component `VRoots.jsx`, which demonstrates signal validation and policy-driven output logic. However, no direct code implementation of a "root directive" exists in the referenced files—this module is conceptualized as a foundational governance layer. All functionality remains unimplemented and requires further architectural research. [NEEDS RESEARCH]