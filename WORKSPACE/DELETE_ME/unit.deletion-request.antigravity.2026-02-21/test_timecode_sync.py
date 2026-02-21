"""Tests for P2-X2 Timecode Sync.

Covers:
- Timecode dataclass: total_frames, total_seconds, __str__, from_total_seconds
- InternalClock: start/stop, get_position advances, is_locked
- NTPClock: start/stop, get_position is non-negative, is_locked
- TimecodeEngine: start/stop, get_timecode, callback dispatch, fallback on lock loss,
  hot-swap source, is_locked
"""
import time
import threading
from unittest.mock import MagicMock, patch

import pytest

from vjlive3.sync.timecode import (
    Timecode,
    TimecodeSourceType,
    TimecodeSource,
    InternalClock,
    NTPClock,
    TimecodeEngine,
)


# ── Timecode dataclass ────────────────────────────────────────────────────────

class TestTimecode:

    def test_total_frames_simple(self):
        tc = Timecode(hours=0, minutes=0, seconds=1, frames=0, fps=30.0)
        assert tc.total_frames == 30

    def test_total_frames_complex(self):
        # 1h 2m 3s 4f @ 25fps
        tc = Timecode(hours=1, minutes=2, seconds=3, frames=4, fps=25.0)
        expected = ((3600 + 120 + 3) * 25) + 4
        assert tc.total_frames == expected

    def test_total_seconds(self):
        tc = Timecode(hours=0, minutes=0, seconds=2, frames=15, fps=30.0)
        assert tc.total_seconds == pytest.approx(2.5, abs=0.001)

    def test_str_format(self):
        tc = Timecode(hours=1, minutes=2, seconds=3, frames=4, fps=30.0)
        assert str(tc) == "01:02:03:04"

    def test_from_total_seconds_zero(self):
        tc = Timecode.from_total_seconds(0.0, fps=30.0)
        assert tc.hours == 0 and tc.minutes == 0 and tc.seconds == 0 and tc.frames == 0

    def test_from_total_seconds_round_trip(self):
        """from_total_seconds → total_seconds should be approx identity."""
        original = 3661.5   # 1h 1m 1s + half frame
        tc = Timecode.from_total_seconds(original, fps=30.0)
        assert abs(tc.total_seconds - int(original * 30) / 30) < 1.0 / 30

    def test_from_total_seconds_negative_clamped(self):
        tc = Timecode.from_total_seconds(-5.0, fps=30.0)
        assert tc.hours == 0

    def test_frozen(self):
        tc = Timecode(0, 0, 0, 0)
        with pytest.raises((AttributeError, TypeError)):
            tc.hours = 1  # type: ignore[misc]


# ── InternalClock ─────────────────────────────────────────────────────────────

class TestInternalClock:

    def test_not_locked_before_start(self):
        clk = InternalClock()
        assert not clk.is_locked

    def test_locked_after_start(self):
        clk = InternalClock()
        clk.start()
        assert clk.is_locked
        clk.stop()

    def test_get_position_none_before_start(self):
        clk = InternalClock()
        assert clk.get_position() is None

    def test_get_position_advances(self):
        clk = InternalClock()
        clk.start()
        t0 = clk.get_position()
        time.sleep(0.05)
        t1 = clk.get_position()
        clk.stop()
        assert t1 > t0

    def test_stop_resets_lock(self):
        clk = InternalClock()
        clk.start()
        clk.stop()
        assert not clk.is_locked
        assert clk.get_position() is None

    def test_start_offset(self):
        clk = InternalClock(start_offset=100.0)
        clk.start()
        pos = clk.get_position()
        clk.stop()
        assert pos >= 100.0


# ── NTPClock ──────────────────────────────────────────────────────────────────

class TestNTPClock:

    def test_start_returns_true(self):
        clk = NTPClock()
        assert clk.start() is True
        clk.stop()

    def test_position_non_negative(self):
        clk = NTPClock()
        clk.start()
        pos = clk.get_position()
        clk.stop()
        assert pos is not None and pos >= 0.0

    def test_position_advances(self):
        clk = NTPClock()
        clk.start()
        p0 = clk.get_position()
        time.sleep(0.05)
        p1 = clk.get_position()
        clk.stop()
        assert p1 > p0

    def test_locked_after_start(self):
        clk = NTPClock()
        clk.start()
        assert clk.is_locked
        clk.stop()

    def test_not_locked_after_stop(self):
        clk = NTPClock()
        clk.start()
        clk.stop()
        assert not clk.is_locked


# ── TimecodeEngine ─────────────────────────────────────────────────────────────

class TestTimecodeEngine:

    def test_start_stop(self):
        engine = TimecodeEngine(fps=30.0)
        engine.start()
        assert engine.fps == 30.0
        engine.stop()

    def test_stop_idempotent(self):
        engine = TimecodeEngine()
        engine.stop()   # before start — must not raise
        engine.start()
        engine.stop()
        engine.stop()   # second stop — must not raise

    def test_get_timecode_returns_timecode(self):
        engine = TimecodeEngine(fps=30.0)
        engine.start()
        tc = engine.get_timecode()
        engine.stop()
        assert isinstance(tc, Timecode)
        assert tc.fps == 30.0

    def test_position_advances(self):
        engine = TimecodeEngine(fps=30.0)
        engine.start()
        p0 = engine.get_position()
        time.sleep(0.1)
        p1 = engine.get_position()
        engine.stop()
        assert p1 > p0

    def test_callback_invoked(self):
        received = []
        engine = TimecodeEngine(fps=30.0)

        def cb(tc: Timecode) -> None:
            received.append(tc)

        engine.add_callback(cb)
        engine.start()
        time.sleep(0.1)   # allow at least one tick at 60fps
        engine.stop()
        assert len(received) > 0

    def test_callback_removed(self):
        received = []
        engine = TimecodeEngine(fps=30.0)

        def cb(tc: Timecode) -> None:
            received.append(tc)

        engine.add_callback(cb)
        engine.start()
        time.sleep(0.05)
        before = len(received)
        engine.remove_callback(cb)
        time.sleep(0.05)
        after = len(received)
        engine.stop()
        assert after == before  # no new callbacks after removal

    def test_hot_swap_source(self):
        engine = TimecodeEngine(fps=25.0)
        engine.start()
        new_source = InternalClock(fps=25.0)
        engine.set_source(new_source)
        tc = engine.get_timecode()
        engine.stop()
        assert isinstance(tc, Timecode)

    def test_fallback_on_lock_loss(self):
        """Engine switches to internal fallback when source loses lock."""
        mock_source = MagicMock(spec=TimecodeSource)
        mock_source.is_locked = False        # never locks
        mock_source.get_position.return_value = 5.0
        mock_source.source_type = TimecodeSourceType.LTC
        mock_source.start.return_value = True

        engine = TimecodeEngine(fps=30.0)
        engine.set_source(mock_source)
        engine.start()
        time.sleep(0.7)  # exceed _LOCK_CHECK_INTERVAL (0.5s)
        # Engine should be on fallback since mock never calls is_locked=True
        pos = engine.get_position()
        engine.stop()
        # Must return a valid position from internal fallback, not crash
        assert pos >= 0.0
        assert not engine.is_locked

    def test_is_locked_with_internal_clock(self):
        engine = TimecodeEngine()
        engine.start()
        time.sleep(0.05)
        locked = engine.is_locked
        engine.stop()
        assert locked is True
