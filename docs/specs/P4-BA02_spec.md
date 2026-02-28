# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA02 — BLFO

**Phase:** Phase 4  
**Assigned To:** Alex Turner  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-03

---

## What This Module Does

The BLFO (Basic Low-Frequency Oscillator) module generates a stable, low-frequency sine wave signal for use in analog control systems and sensor calibration. It provides configurable frequency and amplitude outputs with real-time feedback via an internal state monitor. The module is designed to operate within narrow thermal and power constraints typical of embedded hardware environments.

---

## What It Does NOT Do

- It does not generate high-frequency or digital signals.  
- It does not perform audio output or communication over network interfaces.  
- It does not support external modulation or phase shifting beyond basic amplitude control.  
- It does not interface with higher-level control logic such as PID loops directly.

---

## Public Interface

```python
class BLFO:
    def __init__(self, frequency: float, amplitude: float, sample_rate: int) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def get_output(self) -> tuple[float, float]: ...
    def set_frequency(self, freq: float) -> None: ...
    def set_amplitude(self, amp: float) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frequency` | `float` | Desired output frequency in Hz | Must be ≥ 0.1 and ≤ 500.0 |
| `amplitude` | `float` | Output signal amplitude (normalized to [0,1]) | Must be ≥ 0.0 and ≤ 1.0 |
| `sample_rate` | `int` | Number of samples per second for output generation | Must be ≥ 100 and ≤ 20000 |
| `output` | `tuple[float, float]` | Returns (time_step, sine_wave_value) | Time step in seconds; value in [−1.0, +1.0] |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → (NullDevice pattern: returns zero output with warning log)  
- What happens on bad input? → (raise ValueError with message indicating invalid parameter range)  
- What is the cleanup path? → (stop() calls internal state reset; releases allocated buffers and interrupts)

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `numpy` — used for sine wave generation — fallback: pure Python math.sin()  
  - `pyaudio` — not required; used only in debug mode — fallback: no audio output  
- Internal modules this depends on:  
  - `vjlive3.hardware.analog_driver.AnalogOutputDevice` — for signal delivery  
  - `vjlive3.utils.time_utils.TimeManager` — for sample timing and synchronization  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing if analog hardware is absent (uses NullDevice) |
| `test_basic_operation` | Core function returns expected sine wave at correct frequency and amplitude |
| `test_error_handling` | Invalid frequency or amplitude raises ValueError with clear message |
| `test_cleanup` | stop() releases resources cleanly; no memory leaks observed in profiling |
| `test_edge_frequency_values` | Module handles edge cases (0.1 Hz, 500 Hz) without instability |
| `test_amplitude_clamping` | Output values are clamped to [−1.0, +1.0] regardless of input |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-4] P4-BA02: Implement BLFO module` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

[NEEDS RESEARCH]: Hardware abstraction layer version compatibility with `vjlive3.hardware.analog_driver.AnalogOutputDevice`  
[NEEDS RESEARCH]: Sample rate impact on power consumption and thermal behavior  
[NEEDS RESEARCH]: Real-time performance under concurrent signal generation tasks