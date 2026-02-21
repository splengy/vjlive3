# Spec: P1-A1 — FFT + Waveform Analysis Engine

**Phase:** Phase 1 / P1-A1
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Source References:** `vjlive/core/audio_analyzer.py`, `VJlive-2/core/audio_analyzer.py`, `VJlive-2/core/audio/rhythm_engine.py`

---

## What This Module Does

Provides real-time audio analysis for VJLive3's VJ reactivity system. Captures audio from
a system input device via PyAudio, runs FFT analysis on each buffer, extracts frequency band
energies (bass/mid/high), amplitude envelope (RMS/peak), spectral flux, and waveform data.
Produces an `AudioFrame` dataclass on every analysis tick that all downstream systems consume.
Falls back to `NullAudioAnalyzer` (simulation mode) when no hardware is available.

---

## What It Does NOT Do

- Does NOT perform beat detection (that is P1-A2 / RhythmEngine)
- Does NOT route audio features to effect parameters (that is P1-A3)
- Does NOT manage multiple audio sources (that is P1-A4)
- Does NOT render waveform visualisations
- Does NOT write audio to disk or stream it over the network

---

## Public Interface

```python
# vjlive3/audio/analyzer.py

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np

@dataclass(frozen=True)
class AudioFrame:
    """Immutable snapshot of one analysis tick."""
    # Band energies (0.0–1.0, normalised)
    bass: float          # 20–250 Hz
    mid: float           # 250–4000 Hz
    high: float          # 4000–20000 Hz
    # Amplitude
    rms: float           # Root-mean-square amplitude (0.0–1.0)
    peak: float          # Peak absolute amplitude (0.0–1.0)
    # Spectral
    spectrum: List[float]    # 128 FFT magnitude bins (0.0–1.0, normalised)
    waveform: List[float]    # Downsampled time-domain buffer (every 4th sample)
    spectral_flux: float     # Positive spectral change rate (0.0–1.0)
    # Beat hints (raw; beat DECISIONS are made in P1-A2)
    timestamp: float         # time.monotonic() at capture


class AudioAnalyzerBase:
    """Abstract base — allows NullAudioAnalyzer and real implementation to be swapped."""

    def start(self) -> bool: ...
    def stop(self) -> None: ...
    def get_frame(self) -> AudioFrame: ...
    def set_simulation(self, frame: AudioFrame) -> None: ...
    @property
    def is_running(self) -> bool: ...
    @property
    def sample_rate(self) -> int: ...
    @property
    def buffer_size(self) -> int: ...


class AudioAnalyzer(AudioAnalyzerBase):
    """
    Real-time audio analysis engine.

    Thread-safe. Runs PyAudio callback on an internal thread; main thread
    reads `get_frame()` which returns the last completed analysis snapshot.

    NOT thread-safe for `start()`/`stop()` concurrent calls — callers must
    serialize lifecycle calls.
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 2048,
        device_index: Optional[int] = None,
    ) -> None:
        """
        Args:
            sample_rate: PCM sample rate. Default 44100 Hz.
            buffer_size: Frames per PyAudio buffer (power of 2). Default 2048.
            device_index: PyAudio device index, or None for system default.

        Raises:
            AudioInitError: If PyAudio cannot open a stream AND no simulation fallback
                            has been explicitly requested (rare; usually falls back silently).
        """

    def start(self) -> bool:
        """
        Open PyAudio stream and begin analysis.

        Returns True on success. Returns False (does NOT raise) if hardware
        is unavailable — automatically enters simulation mode with zeroed frames.
        """

    def stop(self) -> None:
        """Stop stream and release all audio resources. Idempotent."""

    def get_frame(self) -> AudioFrame:
        """
        Return the most recently computed AudioFrame.

        Thread-safe. Never blocks — returns last frame if analysis is mid-tick.
        Returns zeroed AudioFrame if not yet started.
        """

    def set_simulation(self, frame: AudioFrame) -> None:
        """
        Inject a synthetic AudioFrame (bypasses hardware).

        Used by tests and the Agent system to drive effects without real audio.
        While a simulation frame is set, get_frame() returns it instead of
        the hardware-derived frame.
        """

    def list_devices(self) -> List[dict]:
        """
        Return list of available audio input devices.

        Each entry: {index, name, max_input_channels, default_sample_rate}
        Returns empty list if PyAudio is unavailable.
        """


class NullAudioAnalyzer(AudioAnalyzerBase):
    """
    Hardware-free fallback. Always returns zeroed AudioFrame.
    Used in CI, headless servers, and hardware-absent deployments.
    """

    def start(self) -> bool: ...   # Always True
    def stop(self) -> None: ...    # No-op
    def get_frame(self) -> AudioFrame: ...  # Returns zeroed frame


# Factory function — primary entry point
def create_analyzer(
    sample_rate: int = 44100,
    buffer_size: int = 2048,
    device_index: Optional[int] = None,
    force_null: bool = False,
) -> AudioAnalyzerBase:
    """
    Return AudioAnalyzer if hardware available, else NullAudioAnalyzer.

    Args:
        force_null: If True, always return NullAudioAnalyzer (useful for CI).
    """
```

---

## Inputs and Outputs

| Item | Type | Description | Constraints |
|------|------|-------------|-------------|
| `sample_rate` | `int` | PCM sample rate | 22050 or 44100; default 44100 |
| `buffer_size` | `int` | Frames per buffer | Power of 2, 512–4096; default 2048 |
| `device_index` | `Optional[int]` | PyAudio device idx | None = system default |
| **Output:** `AudioFrame.bass` | `float` | 20–250 Hz energy | 0.0–1.0 |
| **Output:** `AudioFrame.mid` | `float` | 250–4000 Hz energy | 0.0–1.0 |
| **Output:** `AudioFrame.high` | `float` | 4–20 kHz energy | 0.0–1.0 |
| **Output:** `AudioFrame.rms` | `float` | Amplitude | 0.0–1.0 |
| **Output:** `AudioFrame.peak` | `float` | Peak amplitude | 0.0–1.0 |
| **Output:** `AudioFrame.spectrum` | `List[float]` | 128 FFT bins | Each 0.0–1.0 |
| **Output:** `AudioFrame.waveform` | `List[float]` | Downsampled PCM | Each -1.0–1.0 |
| **Output:** `AudioFrame.spectral_flux` | `float` | Positive flux | 0.0–1.0 |

---

## Edge Cases and Error Handling

- **PyAudio not installed:** `create_analyzer()` returns `NullAudioAnalyzer`; logs WARNING.
- **Hardware unavailable at start:** `start()` returns `False`, auto-enters simulation; does NOT raise.
- **Buffer overflow:** Log WARNING, skip frame analysis, return last good frame.
- **Analysis exception:** Log ERROR, return last good frame; attempt recovery up to 3 times.
- **Zero-length audio buffer:** Return last frame unchanged.
- **DC offset / silence:** All outputs stay 0.0; no division-by-zero (guard with `+ 1e-6`).

---

## Internal Design Notes

**FFT algorithm:** `scipy.fft.rfft` (real FFT, half the bins). Magnitudes = `np.abs(fft)`.
Normalise to 0–1 by dividing by `np.max(magnitudes) + 1e-6`.

**Band extraction:** Boolean masks on `rfftfreq` output:
```python
freqs = rfftfreq(buffer_size, 1 / sample_rate)
bass_mask = (freqs >= 20) & (freqs <= 250)
mid_mask  = (freqs >= 250) & (freqs <= 4000)
high_mask = (freqs >= 4000) & (freqs <= 20000)
```

**Thread model:** PyAudio callback runs on a dedicated audio thread. It writes to a
`threading.RLock`-protected `_current_frame` slot. `get_frame()` acquires the lock briefly
to copy the reference (immutable dataclass — copy is safe).

**Frame-skipping:** Analyze at most 60 times/second (`_analysis_interval = 1/60`). If callback
fires faster, skip the analysis and return the previous frame. This keeps CPU usage stable.

**Spectral flux:** Positive half-wave rectified difference between consecutive 128-bin spectra,
normalised relative to `max_magnitude`.

---

## Dependencies

### External (install via pyproject.toml)
- `pyaudio >= 0.2.13` — audio capture (optional; fallback to Null if missing)
- `scipy >= 1.10` — FFT (`scipy.fft.rfft`, `scipy.signal.butter`)
- `numpy >= 1.24` — array maths

### Internal Modules
- None at this layer (foundation module)

---

## Test Plan

| Test ID | What It Verifies |
|---------|-----------------|
| `test_null_analyzer_returns_frame` | NullAudioAnalyzer.get_frame() returns zeroed AudioFrame |
| `test_null_start_returns_true` | NullAudioAnalyzer.start() always returns True |
| `test_null_stop_noop` | NullAudioAnalyzer.stop() raises nothing |
| `test_create_analyzer_force_null` | create_analyzer(force_null=True) returns NullAudioAnalyzer |
| `test_audio_frame_is_frozen` | AudioFrame is immutable (should raise on setattr) |
| `test_audio_frame_band_range` | bass/mid/high are 0.0–1.0 after analysis |
| `test_spectrum_length` | frame.spectrum has exactly 128 elements |
| `test_waveform_values` | frame.waveform values are in -1.0..1.0 |
| `test_simulation_injection` | set_simulation() makes get_frame() return injected frame |
| `test_spectral_flux_silent` | spectral_flux == 0.0 for zeroed input |
| `test_list_devices_no_crash` | list_devices() returns list without crash (may be empty) |
| `test_analyze_sine_wave_bass` | 100 Hz sine → bass > 0, mid ≈ 0, high ≈ 0 |
| `test_analyze_sine_wave_high` | 8000 Hz sine → high > 0, bass ≈ 0 |
| `test_thread_safety` | 100 concurrent get_frame() calls from different threads return valid frames |
| `test_rms_silence` | Silent buffer → rms == 0.0 |
| `test_rms_full_scale` | Full-scale square wave → rms ≈ 1.0 |
| `test_start_stop_lifecycle` | start() → get_frame() → stop() in order, no crash |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] All 17 tests pass
- [ ] No file over 750 lines (split `_internals.py` if needed)
- [ ] No stubs (no `pass` or `raise NotImplementedError` in shipped code)
- [ ] `NullAudioAnalyzer` verified on headless CI (no PyAudio)
- [ ] VERIFICATION_CHECKPOINTS.md P2-MIDI row checked (after Manager reviews)
- [ ] BOARD.md P1-A1 marked ✅
- [ ] Lock released in LOCKS.md
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Command

```bash
# Unit tests (no hardware required — NullAnalyzer used)
PYTHONPATH=src python3 -m pytest tests/unit/test_audio_analyzer.py -v

# Integration smoke (with audio hardware)
PYTHONPATH=src python3 -c "
from vjlive3.audio.analyzer import create_analyzer
import time
a = create_analyzer()
a.start()
time.sleep(0.1)
f = a.get_frame()
print(f'bass={f.bass:.3f} mid={f.mid:.3f} high={f.high:.3f} rms={f.rms:.3f}')
print(f'spectrum bins={len(f.spectrum)} waveform samples={len(f.waveform)}')
a.stop()
"
```
