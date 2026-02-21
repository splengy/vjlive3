"""Tests for ReactivityBus and AudioSnapshot."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import threading
import numpy as np
import pytest
from vjlive3.audio.analyzer import AudioAnalyzer
from vjlive3.audio.beat_detector import BeatDetector
from vjlive3.audio.reactivity_bus import ReactivityBus, AudioSnapshot


def _push_silence(bus):
    a = AudioAnalyzer(fft_size=1024)
    d = BeatDetector()
    a.update(np.zeros(1024, dtype=np.float32))
    d.update(a)
    bus.push(a, d)
    return bus.snapshot()


def test_silence_snapshot_has_correct_fields():
    snap = AudioSnapshot.silence()
    assert snap.rms == 0.0
    assert snap.beat is False
    assert snap.bpm == 0.0
    assert snap.spectrum.shape == (1025,)


def test_push_updates_snapshot():
    bus = ReactivityBus()
    snap = _push_silence(bus)
    assert isinstance(snap, AudioSnapshot)
    assert snap.spectrum.shape[0] > 0


def test_snapshot_spectrum_is_copy():
    """Mutating the returned snapshot's spectrum shouldn't affect the bus."""
    bus = ReactivityBus()
    snap = _push_silence(bus)
    snap.spectrum[0] = 999.0
    snap2 = bus.snapshot()
    assert snap2.spectrum[0] != 999.0


def test_subscriber_called_on_push():
    received = []
    bus = ReactivityBus()
    bus.subscribe(received.append)
    _push_silence(bus)
    assert len(received) == 1
    assert isinstance(received[0], AudioSnapshot)


def test_unsubscribe():
    received = []
    bus = ReactivityBus()
    bus.subscribe(received.append)
    bus.unsubscribe(received.append)
    _push_silence(bus)
    assert len(received) == 0


def test_thread_safe_concurrent_reads():
    """Multiple threads reading snapshot simultaneously should not raise."""
    bus = ReactivityBus()
    _push_silence(bus)
    errors = []

    def reader():
        try:
            for _ in range(100):
                _ = bus.snapshot()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=reader) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, f"Thread errors: {errors}"
