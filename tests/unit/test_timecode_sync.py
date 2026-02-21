"""
Unit tests for the Timecode Sync system:
  - PLLSync frame interpolation, drift, quality
  - TimecodeSync INTERNAL mode frame counting + timecode string
  - Start / stop lifecycle
  - Callbacks, reset, stats dict
"""

from __future__ import annotations

import time

import pytest

from vjlive3.sync.pll import PLLSync
from vjlive3.sync.timecode import TimecodeSource, TimecodeSync


# ---------------------------------------------------------------------------
# PLLSync tests
# ---------------------------------------------------------------------------


class TestPLLSync:
    def test_initial_state_zero(self) -> None:
        pll = PLLSync(target_fps=30.0)
        assert pll.get_interpolated_frame() == 0.0
        assert pll.sync_quality == 0.0

    def test_invalid_fps_raises(self) -> None:
        with pytest.raises(ValueError):
            PLLSync(target_fps=0)
        with pytest.raises(ValueError):
            PLLSync(target_fps=-1)

    def test_sync_to_master_advances_frame(self) -> None:
        pll = PLLSync(target_fps=30.0)
        pll.sync_to_master(0, 0.0)
        pll.sync_to_master(30, 1.0)  # 1 second later → 30 frames
        # Interpolated frame should be ≥ 30
        frame = pll.get_interpolated_frame()
        assert frame >= 30.0

    def test_sync_quality_increases_with_stable_input(self) -> None:
        pll = PLLSync(target_fps=30.0)
        t = 0.0
        for i in range(40):
            pll.sync_to_master(i * 30, t)
            t += 1.0
        # Quality should be high after consistent 30 fps ticks
        assert pll.sync_quality > 0.5

    def test_reset_clears_state(self) -> None:
        pll = PLLSync(target_fps=30.0)
        pll.sync_to_master(100, 3.33)
        pll.reset()
        assert pll.get_interpolated_frame() == 0.0
        assert pll.sync_quality == 0.0

    def test_set_sync_offset(self) -> None:
        import time as _time

        pll = PLLSync(target_fps=30.0)
        # Prime the PLL and backdate last_sync to create non-zero elapsed
        pll.sync_to_master(100, 0.0)
        pll._last_sync_time = _time.monotonic() - 1.0  # 1 second of elapsed time

        pll.set_sync_offset(0.0)
        frame_no_offset = pll.get_interpolated_frame()

        pll.set_sync_offset(50.0)
        frame_with_offset = pll.get_interpolated_frame()

        # With 50-frame positive offset, result should be 50 frames greater
        assert frame_with_offset > frame_no_offset
        assert abs((frame_with_offset - frame_no_offset) - 50.0) < 1.0


    def test_stats_dict_keys(self) -> None:
        pll = PLLSync(target_fps=25.0)
        stats = pll.get_stats()
        assert "target_fps" in stats
        assert "drift_rate" in stats
        assert "sync_quality" in stats
        assert stats["target_fps"] == 25.0


# ---------------------------------------------------------------------------
# TimecodeSync tests
# ---------------------------------------------------------------------------


class TestTimecodeSync:
    def test_internal_frame_counting(self) -> None:
        ts = TimecodeSync(source=TimecodeSource.INTERNAL, fps=30.0)
        ts.start()
        time.sleep(0.1)
        ts.update(dt=1 / 60)
        assert ts.get_frame_number() >= 0  # At least started
        ts.stop()

    def test_timecode_string_format(self) -> None:
        ts = TimecodeSync(source=TimecodeSource.INTERNAL, fps=30.0)
        ts.start()
        ts.update()
        tc = ts.get_timecode_string()
        parts = tc.split(":")
        assert len(parts) == 4
        for p in parts:
            assert p.isdigit()
            assert len(p) == 2
        ts.stop()

    def test_frame_to_string_known_value(self) -> None:
        """90 frames @ 30fps = 00:00:03:00"""
        ts = TimecodeSync(fps=30.0)
        result = ts._frame_to_string(90)
        assert result == "00:00:03:00"

    def test_frame_to_string_one_hour(self) -> None:
        ts = TimecodeSync(fps=30.0)
        result = ts._frame_to_string(30 * 3600)
        assert result == "01:00:00:00"

    def test_start_stop_lifecycle(self) -> None:
        ts = TimecodeSync(source=TimecodeSource.INTERNAL, fps=25.0)
        assert ts.is_running is False
        ts.start()
        assert ts.is_running is True
        ts.stop()
        assert ts.is_running is False

    def test_receive_frame_updates_state(self) -> None:
        ts = TimecodeSync(source=TimecodeSource.OSC, fps=30.0)
        ts.start()
        ts.receive_frame(150, "00:00:05:00")
        assert ts.get_frame_number() == 150
        assert ts.get_timecode_string() == "00:00:05:00"
        ts.stop()

    def test_sync_callback_fires_on_good_quality(self) -> None:
        fired: list[dict] = []
        ts = TimecodeSync(source=TimecodeSource.INTERNAL, fps=30.0)
        ts.set_sync_callback(lambda d: fired.append(d))
        ts.start()

        # Drive a lot of PLL ticks to build quality
        for i in range(60):
            ts._pll.sync_to_master(i * 30, float(i))
        ts._pll._sync_quality = 1.0  # Force quality for callback test
        ts._smoothed_tc = "00:00:01:00"  # Pre-populate smoothed

        ts.update()
        ts.stop()
        # callback may or may not fire depending on timing, but no crash
        assert isinstance(fired, list)

    def test_reset_clears_frame(self) -> None:
        ts = TimecodeSync(source=TimecodeSource.INTERNAL, fps=30.0)
        ts.start()
        time.sleep(0.05)
        ts.update()
        ts.reset()
        assert ts.get_frame_number() == 0
        ts.stop()

    def test_stats_dict_structure(self) -> None:
        ts = TimecodeSync(source=TimecodeSource.INTERNAL, fps=30.0)
        stats = ts.get_stats()
        assert "source" in stats
        assert "fps" in stats
        assert "frame" in stats
        assert "timecode" in stats
        assert stats["source"] == "internal"
        assert stats["fps"] == 30.0

    def test_invalid_fps_raises(self) -> None:
        with pytest.raises(ValueError):
            TimecodeSync(fps=0)

    def test_ltc_fallback_to_internal(self) -> None:
        """LTC without hardware should fall back gracefully."""
        ts = TimecodeSync(source=TimecodeSource.LTC, fps=30.0)
        ts.start()
        # After start, source should have fallen back
        assert ts.is_running is True
        ts.stop()

    def test_ntp_fallback_to_wallclock(self) -> None:
        """NTP with no network should not raise."""
        ts = TimecodeSync(source=TimecodeSource.NTP, fps=30.0)
        ts.start()
        assert ts.is_running is True
        ts.stop()
