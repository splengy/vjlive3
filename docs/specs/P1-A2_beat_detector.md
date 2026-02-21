# Spec: P1-A2 — Real-Time Beat Detection (RhythmEngine)

**Phase:** Phase 1 / P1-A2
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Source References:** `VJlive-2/core/audio/rhythm_engine.py`, `vjlive/core/audio_analyzer.py`
**Depends On:** P1-A1 (`AudioFrame` from audio analyzer)

---

## What This Module Does

Tracks musical beats in real time using a Phase-Locked Loop (PLL) algorithm driven by
spectral flux onset detection. Consumes `AudioFrame` objects from P1-A1 and produces beat
events, BPM estimates, beat phase (0–1), and confidence scores. The engine is
"generative" — the internal phase clock continues even during silence or complex syncopation,
so downstream effects never see discontinuities. Also detects snare hits (mid-band energy
transients) as a secondary feature.

---

## What It Does NOT Do

- Does NOT capture audio (that is P1-A1)
- Does NOT route beat events to effect parameters (that is P1-A3)
- Does NOT do tempo sync over network (that is P2-X2)
- Does NOT detect melody, chord, or pitch
- Does NOT provide waveform or spectrum data — consume from `AudioFrame` directly

---

## Public Interface

```python
# vjlive3/audio/beat_detector.py

from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass(frozen=True)
class BeatState:
    """Immutable snapshot of one beat-detection tick."""
    beat: bool          # True for one tick when a beat fires
    snare: bool         # True for one tick on snare detection
    bpm: float          # Current BPM estimate (60–200)
    phase: float        # Beat phase 0.0–1.0 (continuous, PLL-driven)
    confidence: float   # Lock confidence 0.0–1.0


class BeatDetector:
    """
    Phase-Locked Loop beat tracker.

    Call update() once per audio analysis tick (aligned with AudioFrame production).
    Call get_state() at any time from any thread to read the latest BeatState.

    Thread-safe for get_state(); update() must be called from one thread only
    (the audio analysis thread or a dedicated beat thread).
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 2048,
        bpm_min: float = 60.0,
        bpm_max: float = 200.0,
        initial_bpm: float = 120.0,
    ) -> None:
        """
        Args:
            sample_rate: Must match AudioAnalyzer sample rate.
            buffer_size: Must match AudioAnalyzer buffer size.
            bpm_min / bpm_max: Clamp for PLL BPM tracking.
            initial_bpm: Starting BPM before any audio input.
        """

    def update(self, frame: 'AudioFrame', dt: float) -> BeatState:
        """
        Process one AudioFrame and advance the PLL.

        Args:
            frame: Latest AudioFrame from P1-A1.
            dt:    Elapsed seconds since last update() call.

        Returns:
            Updated BeatState (also stored internally for get_state()).
        """

    def get_state(self) -> BeatState:
        """
        Return most recent BeatState. Thread-safe, never blocks.
        Returns zeroed state if update() has never been called.
        """

    def reset(self, bpm: float = 120.0) -> None:
        """Reset PLL to a known BPM, zeroing phase and confidence."""
```

---

## Inputs and Outputs

| Item | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `AudioFrame` | From P1-A1 | Must be current tick's frame |
| `dt` | `float` | Seconds since last update | > 0; capped internally at 1.0s max |
| **Output:** `BeatState.beat` | `bool` | Beat fired this tick | True for exactly one tick |
| **Output:** `BeatState.snare` | `bool` | Snare fired this tick | True for exactly one tick |
| **Output:** `BeatState.bpm` | `float` | Current BPM | 60–200 |
| **Output:** `BeatState.phase` | `float` | Beat progress | 0.0–1.0, continuous |
| **Output:** `BeatState.confidence` | `float` | PLL lock quality | 0.0–1.0 |

---

## Algorithm: PLL Beat Tracker

### Step 1 — Spectral Flux Onset Detection
Compute positive half-wave rectified flux from low-frequency bins 0–20 (approx 0–420 Hz
at 44100/2048):
```python
flux = np.sum(np.maximum(0, magnitudes[:20] - prev_spectrum[:20]))
```
Adaptive threshold = `mean(recent_flux_history) * 1.5` (deque of ~43 ticks ≈ 1s).
`is_onset = flux > threshold`.

### Step 2 — PLL Phase Advance
```python
period = 60.0 / bpm
phase += dt / period
if phase >= 1.0:
    phase -= 1.0
```

### Step 3 — PLL Error Correction (on onset)
```python
error = phase if phase < 0.5 else phase - 1.0
alpha = 0.1 + (1.0 - confidence) * 0.2   # more aggressive when low confidence
phase -= error * alpha

if abs(error) < 0.2:   # only adjust tempo on confident onsets
    new_period = period + error * 0.01
    bpm = clip(0.9 * bpm + 0.1 * (60.0 / new_period), bpm_min, bpm_max)
    confidence = min(1.0, confidence + 0.1)
else:
    confidence = max(0.0, confidence - 0.005)
```

### Step 4 — Beat Event
`beat = True` when phase transitions through 0 (phase < 0.1 after wrap).

### Step 5 — Snare Detection
```python
b, a = butter(5, [250/nyquist, 4000/nyquist], btype='band')
mid_signal = lfilter(b, a, audio_data)
snare = np.sum(mid_signal ** 2) > 0.25
```

---

## Edge Cases and Error Handling

- **`dt > 1.0`:** Cap dt to 1.0 to prevent runaway phase on long gaps.
- **`dt <= 0`:** Use `dt = 0.016` (assume 60fps) to avoid division by zero.
- **Silent input (all-zero frame):** Flux is 0, PLL coasts on momentum; confidence decays slowly.
- **Very fast transients (dt < 0.001):** Skip onset detection, only advance phase.
- **`bpm` out of range:** Always clamp to `[bpm_min, bpm_max]`.

---

## Dependencies

### External
- `numpy >= 1.24` — array maths
- `scipy >= 1.10` — `butter`, `lfilter` for snare bandpass filter

### Internal
- `vjlive3.audio.analyzer.AudioFrame` — input type (P1-A1)

---

## Test Plan

| Test ID | What It Verifies |
|---------|-----------------|
| `test_beat_state_is_frozen` | BeatState immutable |
| `test_initial_state_zeroed` | get_state() before update returns zeroed state |
| `test_silent_input_coast` | PLL phase advances without input (generative) |
| `test_bpm_clamp_min` | BPM never drops below bpm_min |
| `test_bpm_clamp_max` | BPM never exceeds bpm_max |
| `test_phase_wraps_0_1` | phase always in [0.0, 1.0) |
| `test_beat_fires_on_wrap` | beat=True exactly at phase wrap |
| `test_confidence_grows_with_onsets` | repeated regular onsets → confidence increases |
| `test_confidence_decays_in_silence` | silence → confidence decays |
| `test_reset_clears_state` | reset(120) sets bpm=120, phase=0, confidence=0 |
| `test_dt_cap_at_1s` | dt > 1.0 does not cause runaway phase |
| `test_snare_detection_mid_energy` | high mid-band energy → snare=True |
| `test_snare_false_for_bass_only` | bass-only energy → snare=False |
| `test_pll_locks_to_regular_beat` | synthetic 120bpm onsets → bpm estimate ≈ 120 ± 5 |
| `test_thread_safe_get_state` | 100 concurrent get_state() calls return valid BeatState |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] All 15 tests pass
- [ ] File < 750 lines
- [ ] No stubs
- [ ] Tested with `NullAudioAnalyzer` (no hardware)
- [ ] BOARD.md P1-A2 marked ✅
- [ ] Lock released in LOCKS.md
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Command

```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_beat_detector.py -v

# Smoke test with simulated 120bpm pulses
PYTHONPATH=src python3 -c "
from vjlive3.audio.beat_detector import BeatDetector
from vjlive3.audio.analyzer import AudioFrame
import time, numpy as np

det = BeatDetector(initial_bpm=120.0)
# Simulate 4 beats at 120bpm (0.5s interval)
for i in range(8):
    frame = AudioFrame(bass=0.8 if i % 2 == 0 else 0.0,
                       mid=0.0, high=0.0, rms=0.5, peak=0.5,
                       spectrum=[0.0]*128, waveform=[0.0]*512,
                       spectral_flux=0.8 if i % 2 == 0 else 0.0,
                       timestamp=time.monotonic())
    state = det.update(frame, dt=0.5)
    print(f'tick {i}: beat={state.beat} bpm={state.bpm:.1f} phase={state.phase:.2f} conf={state.confidence:.2f}')
"
```
