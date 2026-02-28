# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA05 — BSwitch Audio Switch Module

**Phase:** Phase 4 / P4-H2  
**Assigned To:** Alex Chen  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-05

---

## What This Module Does

The BSwitch module implements a dynamic audio switch that routes between two input signals (`a` and `b`) based on a gate signal, with optional latch behavior. It evaluates the gate against a configurable threshold to determine when to switch, and supports latching logic where the state persists until explicitly changed by a new gate pulse. The output is either `a` or `b`, depending on the current state.

---

## What It Does NOT Do

- It does not perform audio filtering, equalization, or gain adjustment.
- It does not support multi-channel routing beyond stereo (left/right).
- It does not provide real-time visual feedback or UI controls.
- It does not handle clock synchronization or timing jitter correction.
- It does not implement dynamic parameter updates during runtime without reinitialization.

---

## Public Interface

```python
class BSwitch:
    def __init__(self, name: str = "BSWITCH", parameters: Dict[str, float] = None) -> None:
        """
        Initialize the BSwitch module.
        
        Args:
            name: Human-readable name for the node (default: "BSWITCH")
            parameters: Dictionary of parameter values. Keys: 'latch', 'threshold'
                        Defaults to {'latch': 0.0, 'threshold': 10.0}
        """
    
    def process_audio(self, dt: float, a: float = 0.0, b: float = 0.0, gate: float = 0.0) -> Dict[str, float]:
        """
        Process audio inputs and return the selected output.
        
        Args:
            dt: Time delta (used for internal state updates)
            a: Input signal A
            b: Input signal B  
            gate: Gate control signal (0.0 to 1.0 or amplitude)

        Returns:
            Dictionary with key 'output' containing the selected audio value
        """
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `name` | `str` | Human-readable name for the node | Must be non-empty string, max 32 characters |
| `parameters` | `Dict[str, float]` | Module-specific parameters: <br> - 'latch': enables latching behavior (value > 5.0 triggers latch) <br> - 'threshold': gate threshold in dB (default: 10.0), scaled from -60 to 0 dB | All values must be ≥ 0.0, ≤ 100.0; defaults apply if missing |
| `dt` | `float` | Time delta between frames (in seconds) | Must be ≥ 0.0 |
| `a` | `float` | First input audio signal | Range: [-1.0, 1.0] or any valid amplitude |
| `b` | `float` | Second input audio signal | Range: [-1.0, 1.0] or any valid amplitude |
| `gate` | `float` | Gate control signal (amplitude) | Range: [0.0, ∞); treated as boolean via threshold comparison |
| `output` | `float` | Selected output from either 'a' or 'b' | Range: [-1.0, 1.0] |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Uses NullDevice pattern; returns default values without crashing  
- What happens on bad input? → Raises `ValueError` with message "Invalid parameter value" for out-of-range inputs (e.g., threshold > 100.0)  
- What is the cleanup path? → No explicit close() method required; state is preserved during shutdown, but all references are cleaned up via garbage collection and module unload hooks  

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `typing` — used for type hints — fallback: standard library included by default  
  - `math` — used in threshold scaling — fallback: no impact; defaults to linear behavior  
- Internal modules this depends on:  
  - `vjlive2.plugins.core.vbogaudio_base.BogaudioNode` — base class for audio nodes  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent (null device fallback) |
| `test_basic_operation` | Core switching logic returns correct output when gate crosses threshold |
| `test_latch_behavior` | Latching mode correctly toggles state on gate pulse when latch > 5.0 |
| `test_threshold_scaling` | Threshold is properly scaled from -60 dB to 0 dB using parameter value (e.g., 10 → -40 dB) |
| `test_error_handling` | Bad input values (e.g., threshold = 200.0) raise ValueError with clear message |
| `test_cleanup` | No memory leaks or resource leaks during module destruction |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-4] P4-BA05: BSwitch audio switch module` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

**Legacy Code References:**  
See `vjlive2/plugins/core/vbogaudio_bswitch/__init__.py` for implementation details.  
Core logic includes:  
- Threshold calculation: `thresh = -60.0 + t('threshold') * 60.0` where `t(p) = param / 10.0`  
- Latch condition: `latch = parameters.get('latch', 0.0) > 5.0`  
- State update: if latch, toggle state on gate pulse; else set to gate value  
- Output routing: return `b` if `_state`, otherwise `a`  

[NEEDS RESEARCH]: Behavior when multiple gate pulses occur in rapid succession (e.g., jitter or noise)  
[NEEDS RESEARCH]: Impact of floating-point precision on threshold comparison over long durations  
[NEEDS RESEARCH]: Support for non-constant gate signals with dynamic amplitude changes