# Spec: P4-BA02 — BLFO (Low Frequency Oscillator)

**File naming:** `docs/specs/phase4_audio/P4-BA02_BLFO.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA02 — BLFO

**Phase:** Phase 4 / P4-BA02
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BLFO is a low frequency oscillator plugin for VJLive3. It generates various waveform shapes (sine, triangle, square, sawtooth, noise) with frequency, amplitude, phase, and sync controls, providing modulation sources for audio and visual effects.

---

## What It Does NOT Do

- Does not process audio signals (modulation only)
- Does not include envelope generators (oscillator only)
- Does not provide audio-rate modulation (LFO only)
- Does not include MIDI control (manual parameters only)

---

## Public Interface

```python
class BLFOPlugin:
    def __init__(self, waveform: str = "sine") -> None: ...
    
    def set_frequency(self, frequency: float) -> None: ...
    def get_frequency(self) -> float: ...
    
    def set_amplitude(self, amplitude: float) -> None: ...
    def get_amplitude(self) -> float: ...
    
    def set_phase(self, phase: float) -> None: ...
    def get_phase(self) -> float: ...
    
    def set_waveform(self, waveform: str) -> None: ...
    def get_waveform(self) -> str: ...
    
    def set_sync(self, enabled: bool) -> None: ...
    def get_sync(self) -> bool: ...
    
    def generate(self, num_samples: int) -> np.ndarray: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `waveform` | `str` | Waveform shape | 'sine', 'triangle', 'square', 'sawtooth', 'noise' |
| `frequency` | `float` | Oscillation frequency | 0.01 to 20.0 Hz |
| `amplitude` | `float` | Output amplitude | 0.0 to 1.0 |
| `phase` | `float` | Phase offset | 0.0 to 1.0 |
| `enabled` | `bool` | Sync enable | True/False |
| `num_samples` | `int` | Number of samples to generate | > 0 |

**Output:** `np.ndarray` — Generated waveform samples

---

## Edge Cases and Error Handling

- What happens if frequency out of range? → Clamp to valid range
- What happens if amplitude negative? → Clamp to 0.0
- What happens if num_samples zero? → Return empty array
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
| `test_waveform_selection` | Selects waveform shapes |
| `test_sync_control` | Enables/disables sync |
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
- [ ] Git commit with `[Phase-4] P4-BA02: BLFO low frequency oscillator` message
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

*Specification based on Bogaudio BLFO module.*