# Spec: P1-A2 — Beat Detector

**File naming:** `docs/specs/P1-A2_beat_detector.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-A2 — Beat Detector

**Phase:** Phase 1 / P1-A2
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

The beat detector analyzes audio in real-time to detect rhythmic beats and tempo. It uses onset detection algorithms, energy analysis, and temporal smoothing to identify beat times and estimate BPM, providing the core timing signal for audio-reactive visual effects and synchronization.

---

## What It Does NOT Do

- Does not perform FFT analysis (delegates to P1-A1)
- Does not handle audio input from multiple sources (delegates to P1-A4)
- Does not emit events or drive effects (delegates to P1-A3)
- Does not include tempo prediction or adaptive learning (basic detection only)

---

## Public Interface

```python
class BeatDetector:
    def __init__(self, sample_rate: int = 44100, lookahead: int = 10) -> None: ...
    
    def process(self, audio_data: np.ndarray, features: AudioFeatures) -> Optional[BeatInfo]: ...
    
    def get_tempo(self) -> float: ...
    def get_beat_phase(self) -> float: ...
    def is_beat(self) -> bool: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `sample_rate` | `int` | Audio sample rate in Hz | 8000-192000 |
| `lookahead` | `int` | Beat detection lookahead frames | 1-100 |
| `audio_data` | `np.ndarray` | Raw audio samples | 1D float array |
| `features` | `AudioFeatures` | Pre-computed audio features | From P1-A1 |

**Output:** `BeatInfo` — Dataclass with beat time, tempo, confidence or None

---

## Edge Cases and Error Handling

- What happens if audio is silent? → No beat detected, return None
- What happens if tempo is unstable? → Smooth tempo estimates over time
- What happens if multiple beats detected close together? → Use onset strength to pick strongest
- What happens on initialization? → Start with default tempo 120 BPM
- What happens on cleanup? → Reset internal state

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — required for signal processing — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.audio.audio_analyzer` (P1-A1)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_beat_detection` | Detects beats on percussive audio |
| `test_tempo_estimation` | Estimates BPM correctly |
| `test_beat_phase` | Beat phase calculation works |
| `test_silence_handling` | No false beats on silence |
| `test_steady_tempo` | Consistent tempo on steady beats |
| `test_variable_tempo` | Adapts to tempo changes |
| `test_edge_cases` | Handles extreme audio levels |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-A2: Beat detector` message
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

*Specification based on VJlive-2 beat detection system.*