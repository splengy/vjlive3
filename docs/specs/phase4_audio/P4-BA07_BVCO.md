# Spec: P4-BA07 — BVCO (Voltage-Controlled Oscillator)

**File naming:** `docs/specs/phase4_audio/P4-BA07_BVCO.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA07 — BVCO

**Phase:** Phase 4 / P4-BA07
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BVCO is a voltage-controlled oscillator plugin for VJLive3. It generates audio waveforms (sine, triangle, square, sawtooth) with frequency, amplitude, phase, and pulse width controls, providing audio-rate modulation sources and sound generation.

---

## What It Does NOT Do

- Does not provide LFO modulation (audio-rate only)
- Does not include effects processing (oscillator only)
- Does not handle recording (generation only)
- Does not include wavetable synthesis (basic waveforms only)

---

## Public Interface

```python
class BVCOPlugin:
    def __init__(self, waveform: str = "sine") -> None: ...
    
    def set_frequency(self, frequency: float) -> None: ...
    def get_frequency(self) -> float: ...
    
    def set_amplitude(self, amplitude: float) -> None: ...
    def get_amplitude(self) -> float: ...
    
    def set_phase(self, phase: float) -> None: ...
    def get_phase(self) -> float: ...
    
    def set_pulse_width(self, pw: float) -> None: ...
    def get_pulse_width(self) -> float: ...
    
    def generate(self, num_samples: int) -> np.ndarray: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `waveform` | `str` | Waveform shape | 'sine', 'triangle', 'square', 'sawtooth' |
| `frequency` | `float` | Oscillation frequency in Hz | 20.0 to 20000.0 |
| `amplitude` | `float` | Output amplitude | 0.0 to 1.0 |
| `phase` | `float` | Phase offset | 0.0 to 1.0 |
| `pw` | `float` | Pulse width (for square) | 0.01 to 0.99 |
| `num_samples` | `int` | Number of samples to generate | > 0 |

**Output:** `np.ndarray` — Generated audio samples

---

## Edge Cases and Error Handling

- What happens if frequency out of range? → Clamp to 20-20k Hz
- What happens if amplitude negative? → Clamp to 0.0
- What happens if pulse width invalid? → Clamp to 0.01-0.99
- What happens on cleanup? → Reset all parameters, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for waveform generation — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.plugins.api` (for PluginBase)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_frequency_setting` | Sets and gets frequency correctly |
| `test_amplitude_setting` | Sets and gets amplitude correctly |
| `test_phase_setting` | Sets and gets phase correctly |
| `test_pulse_width` | Sets and gets pulse width |
| `test_waveform_generation` | Generates correct waveforms |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA07: BVCO voltage-controlled oscillator` message
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

*Specification based on Bogaudio BVCO module.*