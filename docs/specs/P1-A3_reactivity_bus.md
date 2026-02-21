# Spec: P1-A3 — Audio-Reactive Effect Framework (ReactivityBus)

**Phase:** Phase 1 / P1-A3
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Source References:** `vjlive/core/audio_reactor.py`, `VJlive-2/core/audio_reactor.py`
**Depends On:** P1-A1 (`AudioFrame`), P1-A2 (`BeatState`)

---

## What This Module Does

Acts as the reactive wiring layer between the audio analysis system and effect parameters.
Maintains a registry of "bindings" — mappings from an audio feature (bass, mid, high, rms,
beat_phase, etc.) to a specific effect parameter identified by a dot-path string (e.g.
`"effects.datamosh.intensity"`). On each frame tick, it reads the latest `AudioFrame` and
`BeatState`, applies per-binding smoothing (frame-rate-independent exponential lerp), maps
the 0–1 feature value to the parameter's [min, max] range, and returns the modulated value
when queried. Thread-safe for concurrent reads from the render thread.

---

## What It Does NOT Do

- Does NOT capture audio (P1-A1)
- Does NOT detect beats (P1-A2)
- Does NOT apply values to effect parameters directly — callers query the bus and apply
- Does NOT persist bindings to disk (that is P1-N3)
- Does NOT provide MIDI-to-parameter binding (that is P2-H1)
- Does NOT implement LFO or envelope-follower modulators

---

## Public Interface

```python
# vjlive3/audio/reactivity_bus.py

from enum import Enum, auto
from typing import Optional, Dict, List
from vjlive3.audio.analyzer import AudioFrame
from vjlive3.audio.beat_detector import BeatState


class AudioFeature(Enum):
    """Named audio features consumers can bind to."""
    BASS         = auto()   # frame.bass
    MID          = auto()   # frame.mid
    HIGH         = auto()   # frame.high
    RMS          = auto()   # frame.rms (volume)
    PEAK         = auto()   # frame.peak
    SPECTRAL_FLUX = auto()  # frame.spectral_flux
    BEAT         = auto()   # 1.0 on beat tick, else 0.0
    BEAT_PHASE   = auto()   # beat_state.phase  (0.0–1.0 continuous)
    BEAT_CONFIDENCE = auto() # beat_state.confidence
    SPECTRUM     = auto()   # energy in a user-defined Hz sub-band of frame.spectrum


class ReactivityBus:
    """
    Audio → Parameter binding bus with smoothing.

    Usage:
        bus = ReactivityBus(analyzer, beat_detector)
        bus.bind('effects.datamosh.intensity', AudioFeature.BASS, min_val=0.0, max_val=1.0)
        # Each render frame:
        bus.tick(dt)
        val = bus.get('effects.datamosh.intensity', base_value=0.5)
    """

    def __init__(
        self,
        analyzer: 'AudioAnalyzerBase',
        beat_detector: 'BeatDetector',
    ) -> None:
        """
        Args:
            analyzer:      Live AudioAnalyzerBase instance (P1-A1).
            beat_detector: Live BeatDetector instance (P1-A2).
        """

    # --- Binding management ---

    def bind(
        self,
        param_path: str,
        feature: AudioFeature,
        min_val: float = 0.0,
        max_val: float = 1.0,
        smoothing: float = 0.0,
        freq_min: float = 20.0,   # only used when feature == SPECTRUM
        freq_max: float = 20000.0,
    ) -> None:
        """
        Register a binding from an audio feature to a parameter path.

        Args:
            param_path: Dot-path identifier, e.g. 'effects.blur.amount'
            feature:    Which audio feature to track.
            min_val / max_val: Output range for the parameter.
            smoothing:  Exponential smoothing factor 0.0 (instant) – 0.99 (very slow).
            freq_min / freq_max: Hz range for SPECTRUM feature only.
        """

    def unbind(self, param_path: str) -> None:
        """Remove a binding. No-op if not bound."""

    def clear(self) -> None:
        """Remove all bindings."""

    def list_bindings(self) -> List[dict]:
        """
        Return list of active bindings for inspection / serialisation.

        Each entry: {param_path, feature, min_val, max_val, smoothing}
        """

    # --- Per-frame update ---

    def tick(self, dt: float) -> None:
        """
        Advance smoothing for all bindings.

        Call once per render frame BEFORE querying get().
        Thread-safe — uses RLock internally.

        Args:
            dt: Seconds since last tick. Used for frame-rate-independent smoothing.
        """

    # --- Value access ---

    def get(self, param_path: str, base_value: float = 0.0) -> float:
        """
        Return the audio-modulated value for a parameter.

        If no binding exists for param_path, returns base_value unchanged.
        Thread-safe.

        Returns value in [min_val, max_val] for the binding.
        """

    def get_feature(self, feature: AudioFeature) -> float:
        """
        Get current raw 0–1 value for a named feature directly.

        Useful for diagnostic/display code. Does NOT apply smoothing or range mapping.
        """

    # --- Convenience helpers (used by Agent and live-coding) ---

    def bass(self) -> float: ...       # get_feature(BASS)
    def mid(self) -> float: ...        # get_feature(MID)
    def high(self) -> float: ...       # get_feature(HIGH)
    def rms(self) -> float: ...        # get_feature(RMS)
    def beat(self) -> bool: ...        # beat_state.beat
    def beat_phase(self) -> float: ... # beat_state.phase
    def bpm(self) -> float: ...        # beat_state.bpm
    def confidence(self) -> float: ... # beat_state.confidence
```

---

## Inputs and Outputs

| Item | Type | Description |
|------|------|-------------|
| `param_path` | `str` | Dot-path binding key, e.g. `"effects.blur.amount"` |
| `feature` | `AudioFeature` | Which audio dimension to bind |
| `smoothing` | `float` | 0.0 = instant, 0.99 = very slow |
| `min_val / max_val` | `float` | Output range for the parameter |
| **Output** `get()` | `float` | Smoothed, range-mapped value |
| **Output** `get_feature()` | `float` | Raw 0–1 feature value |

---

## Smoothing Algorithm

Frame-rate-independent exponential lerp:

```python
alpha = (1.0 - smoothing) * (dt * 60.0)
alpha = max(0.0, min(1.0, alpha))
smoothed_value = smoothed_value + (target - smoothed_value) * alpha
```

At `smoothing=0.0` → `alpha = dt*60` (≈1.0 at 60fps = instant).
At `smoothing=0.9` → `alpha ≈ 0.1` per frame → slow glide.

---

## SPECTRUM Feature Sub-band Energy

When `feature == AudioFeature.SPECTRUM`:
```python
sample_rate = analyzer.sample_rate
buffer_size = analyzer.buffer_size
freq_resolution = sample_rate / buffer_size  # Hz per bin
bin_lo = int(freq_min / freq_resolution)
bin_hi = int(freq_max / freq_resolution)
energy = np.mean(frame.spectrum[bin_lo:bin_hi + 1])
```

---

## Edge Cases and Error Handling

- **Unbound `get()` call:** Returns `base_value` without error.
- **`smoothing` out of range:** Clamp to [0.0, 0.99].
- **`min_val == max_val`:** Always return `min_val`.
- **`dt <= 0`:** Use 0.016 to avoid divide-by-zero.
- **SPECTRUM with empty range:** Return 0.0, log WARNING.
- **Thread-safe writes to binding table:** All mutations inside `threading.RLock`.

---

## Dependencies

### External
- `numpy >= 1.24` — sub-band energy calculation

### Internal
- `vjlive3.audio.analyzer.AudioFrame` (P1-A1)
- `vjlive3.audio.analyzer.AudioAnalyzerBase` (P1-A1)
- `vjlive3.audio.beat_detector.BeatDetector` (P1-A2)
- `vjlive3.audio.beat_detector.BeatState` (P1-A2)

---

## Test Plan

| Test ID | What It Verifies |
|---------|-----------------|
| `test_unbound_returns_base` | get('x', 0.5) returns 0.5 when not bound |
| `test_bind_and_get_bass` | bind bass → tick → get returns scaled bass value |
| `test_range_mapping` | min_val=10, max_val=20, bass=0.5 → get() returns 15.0 |
| `test_smoothing_zero_instant` | smoothing=0.0 → get() returns exact target in one tick |
| `test_smoothing_high_slow` | smoothing=0.9 → value changes < 20% per tick |
| `test_unbind_reverts_to_base` | unbind() → get() returns base_value |
| `test_clear_removes_all` | clear() → all paths return base_value |
| `test_list_bindings_format` | list_bindings() returns list of dicts with expected keys |
| `test_beat_fires_on_beat_tick` | simulated beat=True → get(feat=BEAT) returns 1.0 |
| `test_beat_phase_passes_through` | phase=0.75 → get_feature(BEAT_PHASE) == 0.75 |
| `test_spectrum_sub_band` | bind SPECTRUM 80–160 Hz → tick → value reflects low bass bin energy |
| `test_thread_safety` | 50 concurrent get() + 10 concurrent bind() calls — no exception |
| `test_convenience_helpers` | bus.bass(), .mid(), .bpm() return matching frame values |
| `test_dt_zero_guard` | tick(dt=0) does not crash |
| `test_smoothing_clamp` | smoothing=2.0 → clamped to 0.99 |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] All 15 tests pass
- [ ] File < 750 lines
- [ ] No stubs
- [ ] Works with NullAudioAnalyzer (CI-safe)
- [ ] BOARD.md P1-A3 marked ✅
- [ ] Lock released in LOCKS.md
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Command

```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_reactivity_bus.py -v

# Integration smoke
PYTHONPATH=src python3 -c "
from vjlive3.audio.analyzer import create_analyzer, AudioFrame
from vjlive3.audio.beat_detector import BeatDetector
from vjlive3.audio.reactivity_bus import ReactivityBus, AudioFeature
import time

analyzer = create_analyzer(force_null=True)
detector = BeatDetector()
bus = ReactivityBus(analyzer, detector)

bus.bind('blur.amount', AudioFeature.BASS, min_val=0.0, max_val=10.0, smoothing=0.5)
analyzer.set_simulation(AudioFrame(bass=0.8, mid=0.2, high=0.1, rms=0.5, peak=0.6,
    spectrum=[0.0]*128, waveform=[0.0]*512, spectral_flux=0.0, timestamp=time.monotonic()))

bus.tick(dt=0.016)
print('blur.amount:', bus.get('blur.amount'))   # Expected: ~8.0 (smoothed towards 8.0)
"
```
