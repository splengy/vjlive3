# Spec: P1-A1 — Audio Analyzer (FFT + Waveform)

**File naming:** `docs/specs/P1-A1_audio_analyzer.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-A1 — Audio Analyzer

**Phase:** Phase 1 / P1-A1
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

The audio analyzer provides real-time FFT (Fast Fourier Transform) and waveform analysis of audio input. It computes frequency spectrum, spectral features (centroid, rolloff, flux), and time-domain features (RMS, peak, zero-crossing rate) for use in audio-reactive visual effects and beat detection.

---

## What It Does NOT Do

- Does not perform beat detection (delegates to P1-A2)
- Does not handle audio input from multiple sources (delegates to P1-A4)
- Does not emit events or drive effects (delegates to P1-A3)
- Does not include audio playback or recording

---

## Public Interface

```python
class AudioAnalyzer:
    def __init__(self, sample_rate: int = 44100, fft_size: int = 2048) -> None: ...
    
    def process(self, audio_data: np.ndarray) -> AudioFeatures: ...
    
    def get_spectrum(self) -> np.ndarray: ...
    def get_waveform(self) -> np.ndarray: ...
    
    def get_spectral_centroid(self) -> float: ...
    def get_spectral_rolloff(self) -> float: ...
    def get_spectral_flux(self) -> float: ...
    
    def get_rms(self) -> float: ...
    def get_peak(self) -> float: ...
    def get_zero_crossing_rate(self) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `sample_rate` | `int` | Audio sample rate in Hz | 8000-192000 |
| `fft_size` | `int` | FFT window size (power of 2) | 256-8192 |
| `audio_data` | `np.ndarray` | Raw audio samples | 1D float array, length = fft_size |

**Output:** `AudioFeatures` — Dataclass containing all computed features

---

## Edge Cases and Error Handling

- What happens if audio_data length != fft_size? → Pad or truncate, log warning
- What happens if audio_data is all zeros? → Return zeroed features
- What happens if audio_data clips? → Clamp to [-1.0, 1.0] range
- What happens if FFT fails? → Return zeroed features, log error
- What happens on cleanup? → Release FFT plan and buffers

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — required for FFT and array operations — fallback: raise ImportError
  - `scipy` (optional) — for advanced window functions — fallback: use numpy windows
- Internal modules this depends on:
  - None (standalone analysis module)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_fft_spectrum` | FFT produces correct frequency bins |
| `test_waveform_buffer` | Waveform buffer updates correctly |
| `test_spectral_features` | Centroid, rolloff, flux computed correctly |
| `test_time_features` | RMS, peak, ZCR computed correctly |
| `test_silence_input` | Handles silent input gracefully |
| `test_clipping_input` | Handles clipped input correctly |
| `test_edge_cases` | Handles invalid parameters gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-A1: Audio analyzer (FFT + waveform)` message
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

*Specification based on VJlive-2 audio analysis system.*