# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-W4 — Phase-Gate Check Workflow

**Phase:** Phase 0 / P0  
**Assigned To:** Agent-7  
**Spec Written By:** Agent-7  
**Date:** 2025-04-05

---

## What This Module Does

This module implements a phase-gate check workflow that validates whether a given task is eligible to proceed into the next development phase based on predefined criteria such as code quality, test coverage, and compliance with configuration policies. It evaluates incoming task metadata against gate rules defined in configuration files and returns a pass/fail decision along with diagnostic details.

---

## What It Does NOT Do

- It does not execute or modify actual code.
- It does not generate new tasks or trigger automated deployments.
- It does not perform real-time monitoring or logging of execution flow.
- It does not handle version control operations (e.g., commits, merges).
- It does not validate user identity or access rights.

---

## Public Interface

```python
class PhaseGateCheck:
    def __init__(self, config_path: str, gate_rules: dict) -> None: ...
    def check(self, task_metadata: dict) -> dict: ...
    def get_gate_status(self, task_id: str) -> str: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config_path` | `str` | Path to YAML configuration file containing gate rules | Must be absolute path; if missing, raises FileNotFoundError |
| `gate_rules` | `dict` | Dictionary of gate rule definitions (e.g., coverage_min: 80) | Keys must match known rule names; values must be numeric or boolean |
| `task_metadata` | `dict` | Metadata about the task including phase, test_coverage, code_size, etc. | Must contain required keys: 'phase', 'test_coverage', 'code_size' |
| `return_value` | `dict` | Contains gate decision and diagnostics | Must include 'passed': bool, 'reasons': list[str], 'warnings': list[str] |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → [NEEDS RESEARCH]  
  *(No hardware involved in this module; no device dependencies)*
- What happens on bad input? → Raises `ValueError` with message indicating missing or invalid key (e.g., "Missing required field: test_coverage")  
- What is the cleanup path? → No external resources are allocated. No cleanup needed.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `pyyaml` — used for parsing gate rules from YAML config — fallback: in-memory dict if file not found  
  - `python-dateutil` — used for date-based gate checks (e.g., deadline validation) — fallback: skip date checks, assume valid
- Internal modules this depends on:  
  - `vjlive3.config.loader.ConfigLoader` — to load gate rules from disk  
  - `vjlive3.validation.task_validator.TaskValidator` — to validate task metadata schema  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_with_valid_config` | Module initializes successfully with valid config and rule set |
| `test_check_passes_with_sufficient_coverage` | Task passes gate when test coverage meets or exceeds minimum threshold |
| `test_check_fails_on_insufficient_coverage` | Task fails when test coverage is below required level |
| `test_check_returns_detailed_reasons` | Output includes clear pass/fail reasons and warnings |
| `test_check_with_missing_metadata_field` | Raises ValueError with descriptive message for missing field |
| `test_get_gate_status_nonexistent_task` | Returns "unknown" status if task ID not found in history |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-W4: Implement phase-gate check workflow` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 0, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.  

> 🐛 Easter Egg Suggestion (for submission):  
> If the task metadata contains a field named `"debug_mode"` set to `true`, the gate check will return an extra field `"easter_egg": "Phase Gate is open — you've unlocked the Debug Portal!"` as a fun, non-functional hint. This is purely for developer morale and does not affect gate decisions.