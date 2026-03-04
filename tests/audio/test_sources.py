"""Tests for P1-A4 — AudioSource, AudioSourceManager (sources.py)"""
import pytest
from vjlive3.audio.sources import AudioSource, AudioSourceManager


# ---- AudioSource ---------------------------------------------------------

def test_source_creation():
    """AudioSource stores correct attributes after construction."""
    src = AudioSource("mic_01", "USB Microphone", sample_rate=44100, channels=1)
    assert src.source_id == "mic_01"
    assert src.device_name == "USB Microphone"
    assert src.sample_rate == 44100
    assert src.channels == 1
    assert src.get_status() == "connected"


def test_level_valid():
    """set_level accepts values in [0.0, 1.0]."""
    src = AudioSource("x", "Dev")
    assert src.set_level(0.0) is True
    assert src.get_level() == pytest.approx(0.0)
    assert src.set_level(0.75) is True
    assert src.get_level() == pytest.approx(0.75)
    assert src.set_level(1.0) is True


def test_level_invalid():
    """set_level rejects values outside [0.0, 1.0]."""
    src = AudioSource("x", "Dev")
    assert src.set_level(1.5) is False
    assert src.set_level(-0.1) is False


def test_connection_add_remove():
    """add_connection / remove_connection update the connection list."""
    src = AudioSource("x", "Dev")
    src.add_connection("reverb")
    src.add_connection("delay")
    assert "reverb" in src.get_connected_targets()
    src.remove_connection("reverb")
    assert "reverb" not in src.get_connected_targets()
    assert "delay" in src.get_connected_targets()


def test_source_error_recovery():
    """recover_from_error clears error_state."""
    src = AudioSource("x", "Dev")
    src.error_state = True
    src.last_error = "test error"
    assert src.recover_from_error() is True
    assert src.error_state is False
    assert src.last_error is None


# ---- AudioSourceManager --------------------------------------------------

def test_manager_add_source():
    """add_source creates a source and returns it."""
    mgr = AudioSourceManager()
    src = mgr.add_source("USB Mic")
    assert src.device_name == "USB Mic"
    assert len(mgr.get_active_sources()) == 1


def test_manager_remove_source():
    """remove_source deletes the source and returns True."""
    mgr = AudioSourceManager()
    src = mgr.add_source("USB Mic")
    result = mgr.remove_source(src.source_id)
    assert result is True
    assert len(mgr.get_active_sources()) == 0


def test_manager_connect_disconnect():
    """connect_source / disconnect_source update connection routing."""
    mgr = AudioSourceManager()
    src = mgr.add_source("Mic")
    sid = src.source_id
    assert mgr.connect_source(sid, "reverb") is True
    assert "reverb" in mgr.get_connected_targets(sid)
    assert mgr.disconnect_source(sid, "reverb") is True
    assert "reverb" not in mgr.get_connected_targets(sid)


def test_manager_set_get_level():
    """set_level / get_level work correctly through the manager."""
    mgr = AudioSourceManager()
    src = mgr.add_source("Mic")
    sid = src.source_id
    assert mgr.set_level(sid, 0.5) is True
    assert mgr.get_level(sid) == pytest.approx(0.5)


def test_manager_subscriber_notification():
    """Subscribers are notified when sources are added or removed."""
    mgr = AudioSourceManager()
    calls = []
    mgr.subscribe(lambda: calls.append(1))
    mgr.add_source("Mic")
    assert len(calls) >= 1
    count_before = len(calls)
    src = list(mgr._sources.values())[0]
    mgr.remove_source(src.source_id)
    assert len(calls) > count_before


def test_manager_stats():
    """get_stats returns a dict with expected keys."""
    mgr = AudioSourceManager()
    mgr.add_source("Mic")
    stats = mgr.get_stats()
    assert "source_count" in stats
    assert "error_state" in stats
    assert stats["source_count"] == 1
