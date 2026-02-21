"""Tests for sync/pll.py — Phase-Locked Loop

Covers: PLLState fields, pulse → frequency lock, phase advance, confidence
decay, reset, is_locked threshold, thread safety.
"""
import time
import threading
import pytest
from vjlive3.sync.pll import PLL, PLLState


class TestPLLState:
    def test_fields_exist(self):
        s = PLLState(phase=0.5, frequency=2.0, bpm=120.0, confidence=0.8, locked=True)
        assert s.phase == 0.5
        assert s.bpm == 120.0
        assert s.locked is True


class TestPLL:
    def test_initial_state(self):
        pll = PLL(nominal_freq=2.0)
        state = pll.update(dt=0.0)
        assert state.frequency == pytest.approx(2.0, abs=0.01)
        assert 0.0 <= state.phase <= 1.0
        assert state.confidence == pytest.approx(0.0)
        assert state.locked is False

    def test_phase_advances_with_dt(self):
        pll = PLL(nominal_freq=1.0)  # 1 Hz → phase 1.0 per second
        s0 = pll.update(dt=0.0)
        s1 = pll.update(dt=0.25)
        # Phase should advance by ~0.25
        assert s1.phase == pytest.approx(0.25, abs=0.02)

    def test_phase_wraps_at_one(self):
        pll = PLL(nominal_freq=1.0)
        for _ in range(10):
            pll.update(dt=0.15)
        state = pll.update(dt=0.0)
        assert 0.0 <= state.phase < 1.0

    def test_confidence_increases_on_pulse(self):
        pll = PLL(nominal_freq=2.0)
        pll.pulse()
        time.sleep(0.51)   # one period at 2Hz
        pll.pulse()
        state = pll.update(dt=0.0)
        assert state.confidence > 0.0

    def test_multiple_pulses_boost_confidence(self):
        """After many regular pulses, confidence should hit lock threshold."""
        pll = PLL(nominal_freq=2.0)
        pll.pulse()
        for _ in range(10):
            time.sleep(0.5)
            pll.pulse()
        state = pll.update(dt=0.0)
        assert state.confidence > 0.5

    def test_confidence_decays_over_time(self):
        pll = PLL(nominal_freq=2.0)
        pll.pulse()
        time.sleep(0.5)
        pll.pulse()
        # Now let it decay by advancing dt
        state = pll.update(dt=0.0)
        conf_before = state.confidence
        # Apply many frame advances to cause decay
        for _ in range(200):
            state = pll.update(dt=1.0 / 60)
        assert state.confidence < conf_before

    def test_reset_clears_confidence(self):
        pll = PLL(nominal_freq=2.0)
        pll.pulse()
        time.sleep(0.5)
        pll.pulse()
        pll.update(dt=0.0)
        pll.reset()
        assert pll.confidence == pytest.approx(0.0)
        assert pll.phase == pytest.approx(0.0)

    def test_reset_with_new_freq(self):
        pll = PLL(nominal_freq=2.0)
        pll.reset(nominal_freq=4.0)
        state = pll.update(dt=0.0)
        assert state.frequency == pytest.approx(4.0, abs=0.01)

    def test_frequency_clamped_by_limits(self):
        pll = PLL(nominal_freq=2.0, min_freq=0.5, max_freq=8.0)
        # Send very fast pulses (shouldn't exceed max_freq)
        t = 0.0
        pll.pulse(t=0.0)
        pll.pulse(t=0.01)   # 100 Hz interval — way above max
        state = pll.update(dt=0.0)
        assert state.frequency <= 8.0

    def test_is_locked_property(self):
        pll = PLL(nominal_freq=2.0)
        assert pll.is_locked is False

    def test_bpm_property(self):
        pll = PLL(nominal_freq=2.0)
        assert pll.bpm == pytest.approx(120.0, abs=0.1)

    def test_thread_safe_concurrent_pulses(self):
        errors = []
        pll = PLL(nominal_freq=2.0)

        def worker():
            try:
                for _ in range(10):
                    pll.pulse()
                    pll.update(dt=1.0 / 60)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
