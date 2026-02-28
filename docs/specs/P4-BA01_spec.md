# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA01 — BOneToEight Audio Switcher

**Phase:** Phase 2 / P2-H3  
**Assigned To:** Alex Turner  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-05

---

## What This Module Does

The BOneToEight module implements an audio routing switch that routes a single input signal to one of eight output channels based on clock, reset, and CV inputs. It supports step-based navigation (forward/backward) with configurable step count and selection via a control voltage (CV). The module maintains state across cycles using internal memory for reset and clock edge detection.

---

## What It Does NOT Do

- It does not perform audio filtering or processing.
- It does not support multi-channel input routing beyond one source.
- It does not generate new signals; it only routes existing inputs.
- It does not handle MIDI or external protocol communication.
- It does not provide real-time visualization or UI controls.

---

## Public Interface

```python
class BOneToEight(BogaudioNode):
    METADATA = {
        "id": "b1to8", 
        "name": "BOneToEight", 
        "category": "Switch",
        "inputs": ["input", "clock", "reset", "select_cv"],
        "outputs": [f"out{i+1}" for i in range(8)]
    }
    
    def __init__(self, name: str = "BOneToEight", parameters: Dict[str, float] = None) -> None:
        super().__init__(name, parameters)
        self._step = 0
        self._prev_clock = False
        self._prev_reset = False
        if not parameters:
            parameters = {'forward': 10.0, 'select': 0.0, 'steps': 7.3}
    
    def process_audio(self, dt: float, **kwargs) -> Dict[str, Any]:
        t = lambda p: self.parameters.get(p, 0.0) / 10.0
        forward = self.parameters.get('forward', 0.0) > 5.0
        select = min(7, int(t('select') * 8))
        steps = min(8, max(1, int(t('steps') * 9)))
        
        clock = (kwargs.get('clock', 0.0) or 0.0) > 0.5
        reset = (kwargs.get('reset', 0.0) or 0.0) > 0.5
        select_cv = kwargs.get('select_cv', 0.0) or 0.0
        inp = kwargs.get('input', 0.0) or 0.0
        
        if reset and not self._prev_reset:
            self._step = 0
        self._prev_reset = reset
        
        if clock and not self._prev_clock:
            if forward:
                self._step = (self._step + 1) % steps
            else:
                self._step = (self._step - 1) % steps
        self._prev_clock = clock
        
        cv_offset = int(select_cv / 1.25) if abs(select_cv) >= 1.25 else 0
        active = (self._step + select + cv_offset) % steps
        
        fn = lambda i: inp if i == active else 0.0
        return {f'out{i+1}': fn(i) for i in range(8)}
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `input` | float | Primary audio signal to route | Must be a valid numeric value (0.0–1.0 or any real number) |
| `clock` | float | Clock pulse input; triggers step change | Value > 0.5 indicates active clock edge |
| `reset` | float | Reset input; resets step counter on rising edge | Value > 0.5 indicates active reset |
| `select_cv` | float | Control voltage to override step selection | Must be within [-10, 10]; offset applied in steps of 1.25 |
| `output[i]` (i=1–8) | float | Output channels; one receives input, others zero | All outputs are scalar audio values |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Uses the NullDevice pattern via parent class BogaudioNode. No crash; returns empty output dict.
- What happens on bad input? → Invalid or non-numeric inputs are converted to 0.0 using `or 0.0` fallbacks. Parameters with invalid keys default to 0.0.
- What is the cleanup path? → No explicit cleanup required due to state being stored in instance variables (`_step`, `_prev_clock`, `_prev_reset`). On module destruction, no resources are released as it operates entirely in memory.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `typing` — used for type hints and metadata structure — fallback: built-in Python types
- Internal modules this depends on:
  - `vjlive2.plugins.core.vbogaudio_base.BogaudioNode` — base class providing initialization, input/output handling, and metadata system

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent (via NullDevice pattern) |
| `test_basic_operation` | Core function returns expected output when inputs are valid and clock is active |
| `test_error_handling` | Bad input values (e.g., None, string) raise no exception; default to 0.0 |
| `test_cleanup` | No memory leaks or resource issues on module destruction (no explicit close() needed) |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-2] P4-BA01: BOneToEight audio switcher` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

[NEEDS RESEARCH]: None found. All required functionality and edge cases are covered in legacy code references.