"""Tests for P1-A3 — AudioReactiveEffect, AudioEffectBus (reactive_effect.py)"""
import time
import threading
import pytest
from vjlive3.audio.reactive_effect import AudioReactiveEffect, AudioEffectBus
from vjlive3.audio.features import AudioFeatures
from vjlive3.audio.analyzer import DummyAudioAnalyzer


# ---- AudioReactiveEffect mixin -------------------------------------------

class _TestEffect(AudioReactiveEffect):
    """Minimal concrete effect for testing."""

    def __init__(self):
        AudioReactiveEffect.__init__(self)
        self.received_count = 0
        self.last_features_received = None

    def on_audio_features(self, features: AudioFeatures) -> None:
        super().on_audio_features(features)
        self.received_count += 1
        self.last_features_received = features


def test_mixin_defaults():
    """AudioReactiveEffect initializes with sensitivity=1.0, no features."""
    e = _TestEffect()
    assert e.get_audio_sensitivity() == pytest.approx(1.0)
    assert e._last_features is None


def test_mixin_get_audio_params_no_data():
    """get_audio_params returns safe zero defaults before any features arrive."""
    e = _TestEffect()
    p = e.get_audio_params()
    assert p["bass"] == pytest.approx(0.0)
    assert p["bpm"] == pytest.approx(120.0)
    assert p["beat"] is False


def test_mixin_on_audio_features_stores_ref():
    """on_audio_features stores the features reference."""
    e = _TestEffect()
    f = AudioFeatures(bass_smooth=0.8, bpm=140.0, beat=True)
    e.on_audio_features(f)
    assert e._last_features is f
    assert e.received_count == 1


def test_mixin_sensitivity_scaling():
    """set_audio_sensitivity scales bass/mid/high in get_audio_params."""
    e = _TestEffect()
    f = AudioFeatures(bass_smooth=0.5, mid_smooth=0.3, high_smooth=0.2)
    e.on_audio_features(f)

    e.set_audio_sensitivity(2.0)
    p = e.get_audio_params()
    assert p["bass"] == pytest.approx(1.0)
    assert p["mid"] == pytest.approx(0.6)

    e.set_audio_sensitivity(0.0)
    p0 = e.get_audio_params()
    assert p0["bass"] == pytest.approx(0.0)


def test_mixin_sensitivity_clamps_negative():
    """Negative sensitivity is clamped to 0."""
    e = _TestEffect()
    e.set_audio_sensitivity(-1.0)
    assert e.get_audio_sensitivity() == pytest.approx(0.0)


# ---- AudioEffectBus ------------------------------------------------------

def test_bus_register_unregister():
    """Register and unregister updates effect_count."""
    bus = AudioEffectBus()
    e1, e2 = _TestEffect(), _TestEffect()
    bus.register(e1)
    bus.register(e2)
    assert bus.effect_count == 2
    bus.unregister(e1)
    assert bus.effect_count == 1
    bus.unregister(e2)
    assert bus.effect_count == 0


def test_bus_duplicate_register():
    """Registering the same effect twice only adds it once."""
    bus = AudioEffectBus()
    e = _TestEffect()
    bus.register(e)
    bus.register(e)
    assert bus.effect_count == 1


def test_bus_process_frame_invokes_on_audio_features():
    """process_frame() calls on_audio_features on each registered effect."""
    da = DummyAudioAnalyzer()
    bus = AudioEffectBus(analyzer=da)
    e = _TestEffect()
    bus.register(e)

    bus.process_frame()
    assert e.received_count == 1
    bus.process_frame()
    assert e.received_count == 2


def test_bus_fallback_to_dummy():
    """Bus initialized without an analyzer uses DummyAudioAnalyzer."""
    bus = AudioEffectBus()
    assert isinstance(bus._analyzer, DummyAudioAnalyzer)
    features = bus.process_frame()
    assert isinstance(features, AudioFeatures)


def test_bus_no_registered_effects():
    """process_frame with empty registry does not crash."""
    bus = AudioEffectBus()
    features = bus.process_frame()
    assert isinstance(features, AudioFeatures)
    assert bus.frame_count == 1


def test_bus_stress_many_effects():
    """10 effects all receive on_audio_features in a single frame."""
    bus = AudioEffectBus()
    effects = [_TestEffect() for _ in range(10)]
    for e in effects:
        bus.register(e)

    bus.process_frame()
    for e in effects:
        assert e.received_count == 1


def test_bus_frame_processing_time_lt_1ms():
    """100 frames with 10 effects must complete in <100ms total (<1ms/frame)."""
    bus = AudioEffectBus()
    for _ in range(10):
        bus.register(_TestEffect())

    start = time.perf_counter()
    for _ in range(100):
        bus.process_frame()
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    assert elapsed_ms < 100.0, f"100 frames took {elapsed_ms:.1f}ms > 100ms"


def test_bus_reactor_compatible_api():
    """get_energy, get_band, get_feature return floats without error."""
    bus = AudioEffectBus()
    bus.process_frame()  # initialise _last_features
    assert isinstance(bus.get_energy(), float)
    assert isinstance(bus.get_band("bass"), float)
    assert isinstance(bus.get_feature("volume_smooth"), float)


def test_bus_set_analyzer():
    """set_analyzer hot-swaps the audio source."""
    bus = AudioEffectBus()
    a2 = DummyAudioAnalyzer()
    bus.set_analyzer(a2)
    assert bus._analyzer is a2
