# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P4-BA03_bmatrix81.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA03 — BMatrix81

**Phase:** Phase 4 / P4-H2  
**Assigned To:** Alex Chen  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-05

---

## What This Module Does

The BMatrix81 module implements an 8-input audio mixer that combines incoming control voltage (CV) signals with configurable gain parameters to produce a single normalized output. It processes up to eight input CV channels, each with an individually adjustable gain factor, and outputs a value clamped between -10 and 10 volts. This enables dynamic signal routing and mixing in live performance environments.

---

## What It Does NOT Do

- It does not support audio processing (e.g., filtering, delay, or effects).  
- It does not provide real-time visualization or UI controls.  
- It does not handle MIDI input or external device communication.  
- It does not perform signal routing between outputs or create multiple output streams.

---

## Public Interface

```python
class BMatrix81(BogaudioNode):
    METADATA = {
        "id": "bmatrix81", 
        "name": "BMATRIX81", 
        "category": "Mixer",
        "inputs": [f"in{i+1}_cv" for i in range(8)], 
        "outputs": ["out"]
    }
    
    def __init__(self, name: str = "BMATRIX81", parameters: Dict[str, float] = None) -> None:
        super().__init__(name, parameters)
        if not parameters:
            parameters = {}
            for i in range(8):
                parameters[f'gain{i+1}'] = 5.0
    
    def process_audio(self, dt: float, **kwargs) -> Dict[str, Any]:
        val = 0.0
        for i in range(8):
            gain = self.parameters.get(f'gain{i+1}', 5.0) / 10.0
            cv_input = kwargs.get(f'in{i+1}_cv', 0.0)
            val += (cv_input or 0.0) * gain
        return {'out': max(-10, min(10, val))}
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `name` | `str` | Human-readable name for the module instance | Default: "BMATRIX81"; must be non-empty string |
| `parameters` | `Dict[str, float]` | Dictionary of gain parameters; keys are `gain1`, ..., `gain8` | Each value in [0.0, 10.0]; default is 5.0 |
| `dt` | `float` | Time delta (used for timing context) | Always ≥ 0.0; not used in logic |
| `in1_cv` to `in8_cv` | `float` | Control voltage input from each of the 8 channels | Each value is float, typically in [-5.0, +5.0] range |
| `out` | `float` | Final mixed output signal | Value clamped to [-10.0, 10.0] |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Uses the NullDevice pattern; no crash occurs. Input CVs default to zero.  
- What happens on bad input? → Raises `ValueError` if any gain parameter exceeds [0.0, 10.0] range or if invalid key is passed in parameters.  
- What is the cleanup path? → No explicit teardown method; relies on parent node lifecycle. All resources are released when the node is garbage collected or removed from the graph.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `typing` — used for type hints — fallback: no impact, runtime behavior unchanged  
- Internal modules this depends on:  
  - `vjlive2.plugins.core.vbogaudio_base.BogaudioNode`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent; defaults to all gains at 5.0 |
| `test_basic_operation` | Core mixing logic returns correct output when inputs and gains are valid |
| `test_error_handling` | Invalid gain values (e.g., >10.0 or <0.0) raise ValueError with clear message |
| `test_cleanup` | No memory leaks or resource issues during module destruction |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-4] P4-BA03: BMatrix81 mixer module` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

