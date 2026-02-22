# Spec: P6-G4 — Spectraphon

**File naming:** `docs/specs/phase6_generators/P6-G4_Spectraphon.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-G4 — Spectraphon

**Phase:** Phase 6 / P6-G4
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Spectraphon is a spectral synthesis generator that creates audio and visual content from spectral data. It provides spectral analysis, resynthesis, and manipulation capabilities, allowing for unique sound and visual generation based on frequency domain transformations.

---

## What It Does NOT Do

- Does not perform real-time FFT on input audio (uses pre-computed or generated spectra)
- Does not include built-in effects (delegates to effect plugins)
- Does not handle audio file I/O (delegates to audio sources)
- Does not provide CV control of spectral parameters (manual control only)

---

## Public Interface

```python
class Spectraphon:
    def __init__(self) -> None: ...
    
    def set_spectrum(self, frequencies: np.ndarray, magnitudes: np.ndarray, phases: np.ndarray) -> None: ...
    def generate_spectrum(self, type: str, params: Dict[str, float]) -> None: ...
    
    def set_frequency_shift(self, shift: float) -> None: ...
    def set_magnitude_scale(self, scale: float) -> None: ...
    def set_phase_modulation(self, modulation: float) -> None: ...
    
    def synthesize(self, duration: float, sample_rate: int) -> np.ndarray: ...
    def get_spectral_data(self) -> SpectralData: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frequencies` | `np.ndarray` | Frequency bins in Hz | > 0, ascending |
| `magnitudes` | `np.ndarray` | Magnitude values | ≥ 0.0 |
| `phases` | `np.ndarray` | Phase values in radians | -π to π |
| `type` | `str` | Spectrum generation type | 'sine', 'noise', 'custom' |
| `params` | `Dict[str, float]` | Generation parameters | Valid param names |
| `shift` | `float` | Frequency shift in Hz | -1000 to 1000 |
| `scale` | `float` | Magnitude scale factor | 0.0 to 10.0 |
| `modulation` | `float` | Phase modulation amount | 0.0 to 1.0 |
| `duration` | `float` | Output duration in seconds | > 0 |
| `sample_rate` | `int` | Output sample rate | 8000-192000 |

**Output:** `np.ndarray` — Synthesized audio, `SpectralData` — Current spectral data

---

## Edge Cases and Error Handling

- What happens if spectrum arrays are mismatched? → Raise ValueError
- What happens if frequencies are not ascending? → Sort and warn
- What happens if magnitudes are negative? → Use absolute values
- What happens if duration is too short? → May not complete full cycle
- What happens on cleanup? → Clear spectral data, reset parameters

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for spectral operations — fallback: raise ImportError
  - `scipy` — for synthesis windows — fallback: use numpy
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_spectrum_setting` | Sets spectrum data correctly |
| `test_spectrum_generation` | Generates spectra by type |
| `test_frequency_shift` | Shifts frequencies correctly |
| `test_magnitude_scale` | Scales magnitudes correctly |
| `test_phase_modulation` | Modulates phases correctly |
| `test_synthesis` | Synthesizes audio from spectrum |
| `test_edge_cases` | Handles invalid data gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-G4: Spectraphon spectral generator` message
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

*Specification based on VJlive-2 Spectraphon module.*