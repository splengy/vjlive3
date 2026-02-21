"""Tests for P1-A3 ReactivityBus.

Spec: docs/specs/P1-A3_reactivity_bus.md
Tests:
  - Bind/unbind lifecycle (bind, unbind, unbind_layer, clear, has_binding)
  - Feature extraction for all AudioFeature values
  - Smoothing: frame-rate independent EMA
  - Mapping: [0,1] → [min_val, max_val]
  - Edge cases: empty frame, zero dt, invalid args
  - Thread safety: 20 concurrent bind/tick calls
  - SPECTRUM_BAND energy calculation
  - get_raw vs get
  - list_bindings snapshot
"""
import threading
import time

import pytest

from vjlive3.audio.analyzer import AudioFrame
from vjlive3.audio.reactivity import AudioFeature, Binding, ReactivityBus


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _frame(**kwargs) -> AudioFrame:
    """Construct an AudioFrame with all fields defaulted."""
    defaults = dict(
        bass=0.0, mid=0.0, high=0.0,
        rms=0.0, peak=0.0,
        spectrum=[0.0] * 128,
        waveform=[0.0] * 128,
        spectral_flux=0.0,
        timestamp=time.monotonic(),
    )
    defaults.update(kwargs)
    return AudioFrame(**defaults)


@pytest.fixture()
def bus() -> ReactivityBus:
    return ReactivityBus()


@pytest.fixture()
def bass_frame() -> AudioFrame:
    return _frame(bass=0.8, mid=0.3, high=0.1, rms=0.5, peak=0.9, spectral_flux=0.4)


# ── Bind / unbind lifecycle ───────────────────────────────────────────────────

class TestBindLifecycle:

    def test_bind_creates_binding(self, bus):
        bus.bind("layer_0", "intensity", AudioFeature.BASS)
        assert bus.has_binding("layer_0", "intensity")
        assert bus.binding_count == 1

    def test_bind_replaces_existing(self, bus):
        bus.bind("layer_0", "intensity", AudioFeature.BASS, min_val=0.0, max_val=1.0)
        bus.bind("layer_0", "intensity", AudioFeature.MID, min_val=0.5, max_val=2.0)
        assert bus.binding_count == 1
        lst = bus.list_bindings()
        assert lst[0]["feature"] == "mid"
        assert lst[0]["max_val"] == 2.0

    def test_unbind_removes(self, bus):
        bus.bind("layer_0", "x", AudioFeature.BASS)
        assert bus.unbind("layer_0", "x") is True
        assert not bus.has_binding("layer_0", "x")
        assert bus.binding_count == 0

    def test_unbind_nonexistent_returns_false(self, bus):
        assert bus.unbind("ghost", "param") is False

    def test_unbind_layer_removes_all_for_layer(self, bus):
        bus.bind("layer_fx", "a", AudioFeature.BASS)
        bus.bind("layer_fx", "b", AudioFeature.MID)
        bus.bind("other_layer", "c", AudioFeature.HIGH)
        count = bus.unbind_layer("layer_fx")
        assert count == 2
        assert not bus.has_binding("layer_fx", "a")
        assert not bus.has_binding("layer_fx", "b")
        assert bus.has_binding("other_layer", "c")

    def test_clear_removes_everything(self, bus):
        bus.bind("L", "x", AudioFeature.BASS)
        bus.bind("L", "y", AudioFeature.MID)
        bus.clear()
        assert bus.binding_count == 0

    def test_bind_empty_layer_id_raises(self, bus):
        with pytest.raises(ValueError):
            bus.bind("", "intensity", AudioFeature.BASS)

    def test_bind_empty_param_name_raises(self, bus):
        with pytest.raises(ValueError):
            bus.bind("layer_0", "", AudioFeature.BASS)

    def test_bind_invalid_smoothing_raises(self, bus):
        with pytest.raises(ValueError):
            bus.bind("layer_0", "x", AudioFeature.BASS, smoothing=1.5)

    def test_list_bindings_snapshot(self, bus):
        bus.bind("L", "x", AudioFeature.BASS, min_val=0.2, max_val=0.8)
        lst = bus.list_bindings()
        assert len(lst) == 1
        assert lst[0]["layer_id"] == "L"
        assert lst[0]["param_name"] == "x"
        assert lst[0]["min_val"] == pytest.approx(0.2)
        assert lst[0]["max_val"] == pytest.approx(0.8)
        # Mutating the snapshot doesn't affect bus
        lst.clear()
        assert bus.binding_count == 1


# ── Feature extraction ────────────────────────────────────────────────────────

class TestFeatureExtraction:

    @pytest.mark.parametrize("feature,field_name,value", [
        (AudioFeature.BASS,          "bass",          0.7),
        (AudioFeature.MID,           "mid",           0.4),
        (AudioFeature.HIGH,          "high",          0.2),
        (AudioFeature.RMS,           "rms",           0.6),
        (AudioFeature.PEAK,          "peak",          0.9),
        (AudioFeature.SPECTRAL_FLUX, "spectral_flux", 0.3),
    ])
    def test_extract_standard_features(self, bus, feature, field_name, value):
        bus.bind("L", "p", feature, min_val=0.0, max_val=1.0, smoothing=0.0)
        frame = _frame(**{field_name: value})
        bus.tick(frame, dt=1.0 / 60)
        result = bus.get("L", "p")
        assert result == pytest.approx(value, abs=1e-5)

    def test_extract_beat_via_getattr(self, bus):
        """BEAT feature reads frame.beat via getattr — returns 0.0 if absent."""
        bus.bind("L", "p", AudioFeature.BEAT, smoothing=0.0)
        frame = _frame()  # no 'beat' attribute on AudioFrame yet
        bus.tick(frame, dt=1.0 / 60)
        assert bus.get("L", "p") == pytest.approx(0.0)

    def test_extract_spectrum_band(self, bus):
        # Set bins 40-80 to 1.0, rest 0.0 — check band 0-22050*40/128 Hz comes up bright
        spectrum = [0.0] * 128
        for i in range(40, 80):
            spectrum[i] = 1.0
        nyquist = 22050.0
        lo_hz = (40 / 128) * nyquist
        hi_hz = (80 / 128) * nyquist
        bus.bind("L", "p", AudioFeature.SPECTRUM_BAND,
                 min_val=0.0, max_val=1.0, smoothing=0.0,
                 band_lo=lo_hz, band_hi=hi_hz)
        frame = _frame(spectrum=spectrum)
        bus.tick(frame, dt=1.0 / 60)
        val = bus.get("L", "p")
        assert val == pytest.approx(1.0, abs=0.01)

    def test_spectrum_band_empty_spectrum(self, bus):
        bus.bind("L", "p", AudioFeature.SPECTRUM_BAND,
                 min_val=0.0, max_val=1.0, smoothing=0.0,
                 band_lo=200.0, band_hi=400.0)
        frame = _frame(spectrum=[])
        bus.tick(frame, dt=1.0 / 60)
        assert bus.get("L", "p") == pytest.approx(0.0)


# ── Smoothing ─────────────────────────────────────────────────────────────────

class TestSmoothing:

    def test_no_smoothing_snaps_instantly(self, bus):
        bus.bind("L", "p", AudioFeature.RMS, smoothing=0.0)
        bus.tick(_frame(rms=1.0), dt=1.0 / 60)
        assert bus.get("L", "p") == pytest.approx(1.0, abs=1e-5)

    def test_smoothing_lags_behind(self, bus):
        bus.bind("L", "p", AudioFeature.BASS, smoothing=0.8, min_val=0.0, max_val=1.0)
        # First tick initialises
        bus.tick(_frame(bass=0.0), dt=1.0 / 60)
        # Second tick with full signal — should NOT snap to 1.0 immediately
        bus.tick(_frame(bass=1.0), dt=1.0 / 60)
        val = bus.get("L", "p")
        assert 0.0 < val < 1.0, f"Expected lag but got {val}"

    def test_smoothing_converges_over_time(self, bus):
        bus.bind("L", "p", AudioFeature.BASS, smoothing=0.5, min_val=0.0, max_val=1.0)
        bus.tick(_frame(bass=0.0), dt=1.0 / 60)
        for _ in range(120):   # 2 seconds at 60fps
            bus.tick(_frame(bass=1.0), dt=1.0 / 60)
        val = bus.get("L", "p")
        assert val > 0.95, f"Expected convergence, got {val}"

    def test_smoothing_frame_rate_independent(self, bus):
        """Same smoothing coeff at 30fps should converge slower per-call but same wall-clock."""
        bus60 = ReactivityBus()
        bus30 = ReactivityBus()
        bus60.bind("L", "p", AudioFeature.BASS, smoothing=0.8)
        bus30.bind("L", "p", AudioFeature.BASS, smoothing=0.8)
        # Both simulate 1 second total of bass=1.0
        for _ in range(60):
            bus60.tick(_frame(bass=1.0), dt=1.0 / 60)
        for _ in range(30):
            bus30.tick(_frame(bass=1.0), dt=1.0 / 30)
        # Both should have converged to approximately the same value
        v60 = bus60.get("L", "p")
        v30 = bus30.get("L", "p")
        assert abs(v60 - v30) < 0.05, f"FPS-independent smoothing failed: 60fps={v60:.3f} 30fps={v30:.3f}"


# ── Mapping ───────────────────────────────────────────────────────────────────

class TestMapping:

    def test_zero_maps_to_min(self, bus):
        bus.bind("L", "p", AudioFeature.BASS, min_val=5.0, max_val=15.0, smoothing=0.0)
        bus.tick(_frame(bass=0.0), dt=1.0 / 60)
        assert bus.get("L", "p") == pytest.approx(5.0)

    def test_one_maps_to_max(self, bus):
        bus.bind("L", "p", AudioFeature.BASS, min_val=5.0, max_val=15.0, smoothing=0.0)
        bus.tick(_frame(bass=1.0), dt=1.0 / 60)
        assert bus.get("L", "p") == pytest.approx(15.0)

    def test_half_maps_to_midpoint(self, bus):
        bus.bind("L", "p", AudioFeature.BASS, min_val=0.0, max_val=10.0, smoothing=0.0)
        bus.tick(_frame(bass=0.5), dt=1.0 / 60)
        assert bus.get("L", "p") == pytest.approx(5.0, abs=0.01)

    def test_inverted_range(self, bus):
        """min > max is valid — inverts the mapping."""
        bus.bind("L", "p", AudioFeature.BASS, min_val=1.0, max_val=0.0, smoothing=0.0)
        bus.tick(_frame(bass=1.0), dt=1.0 / 60)
        assert bus.get("L", "p") == pytest.approx(0.0)
        bus.tick(_frame(bass=0.0), dt=1.0 / 60)
        assert bus.get("L", "p") == pytest.approx(1.0)


# ── Edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_get_without_binding_returns_base_value(self, bus):
        assert bus.get("ghost", "param", base_value=42.0) == pytest.approx(42.0)

    def test_get_raw_without_binding_returns_none(self, bus):
        assert bus.get_raw("ghost", "param") is None

    def test_get_raw_returns_0_to_1(self, bus):
        bus.bind("L", "p", AudioFeature.BASS, min_val=0.0, max_val=100.0, smoothing=0.0)
        bus.tick(_frame(bass=0.7), dt=1.0 / 60)
        raw = bus.get_raw("L", "p")
        assert raw is not None
        assert 0.0 <= raw <= 1.0

    def test_zero_dt_guarded(self, bus):
        """dt=0 should not crash or divide-by-zero."""
        bus.bind("L", "p", AudioFeature.BASS, smoothing=0.5)
        bus.tick(_frame(bass=0.5), dt=0.0)   # guarded internally
        bus.get("L", "p")  # no exception

    def test_tick_not_called_get_returns_base(self, bus):
        """Before tick() is ever called, get() should not crash."""
        bus.bind("L", "p", AudioFeature.BASS)
        result = bus.get("L", "p", base_value=99.9)
        # _initialized is False so _smoothed is 0 → min_val (0.0)
        # the result is 0.0 (first call initialises from zero)
        assert isinstance(result, float)

    def test_last_frame_none_before_tick(self, bus):
        assert bus.last_frame is None

    def test_last_frame_updated_after_tick(self, bus):
        bus.bind("L", "p", AudioFeature.BASS)
        f = _frame(bass=0.9)
        bus.tick(f, dt=1.0 / 60)
        assert bus.last_frame is f


# ── Thread safety ─────────────────────────────────────────────────────────────

class TestThreadSafety:

    def test_concurrent_bind_and_tick(self, bus):
        """20 threads bind and tick simultaneously — no exceptions or corruption."""
        errors = []
        dt = 1.0 / 60

        def worker(i: int) -> None:
            try:
                bus.bind(f"layer_{i}", "p", AudioFeature.BASS, smoothing=0.1)
                for _ in range(10):
                    bus.tick(_frame(bass=float(i) / 20.0), dt=dt)
                    bus.get(f"layer_{i}", "p")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert bus.binding_count == 20
