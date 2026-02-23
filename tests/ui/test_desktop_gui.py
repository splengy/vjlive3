"""Tests for vjlive3.ui.desktop_gui — GUI app, SentienceOverlay, CollaborativeStudio, QuantumCollaborativeStudio."""
import pytest
from vjlive3.ui.desktop_gui import (
    VJLiveGUIApp, UIBackend, SentienceOverlay, SENTIENCE_MESSAGES,
    SENTIENCE_TRIGGER, CollaborativeStudio, QuantumCollaborativeStudio
)


# ── SentienceOverlay ──────────────────────────────────────────────────────────

def test_sentience_not_active_by_default():
    s = SentienceOverlay()
    assert not s.is_active


def test_sentience_activates_on_trigger():
    s = SentienceOverlay()
    activated = False
    for ch in SENTIENCE_TRIGGER:
        if s.on_keypress(ch):
            activated = True
    assert activated
    assert s.is_active


def test_sentience_advance_cycles_messages():
    s = SentienceOverlay()
    for ch in SENTIENCE_TRIGGER:
        s.on_keypress(ch)
    msgs = [s.advance() for _ in range(len(SENTIENCE_MESSAGES) + 2)]
    assert all(m in SENTIENCE_MESSAGES for m in msgs if m)


def test_sentience_advance_inactive_returns_empty():
    s = SentienceOverlay()
    assert s.advance() == ""


def test_sentience_deactivate():
    s = SentienceOverlay()
    for ch in SENTIENCE_TRIGGER:
        s.on_keypress(ch)
    s.deactivate()
    assert not s.is_active


def test_sentience_message_count():
    s = SentienceOverlay()
    assert s.message_count == len(SENTIENCE_MESSAGES)


# ── VJLiveGUIApp ──────────────────────────────────────────────────────────────

def test_gui_starts_in_headless_mode():
    app = VJLiveGUIApp(UIBackend.HEADLESS)
    app.start()
    assert app.is_running


def test_gui_stop():
    app = VJLiveGUIApp()
    app.start()
    app.stop()
    assert not app.is_running


def test_gui_register_plugin():
    app = VJLiveGUIApp()
    app.register_plugin("bloom", [{"name": "intensity", "default": 5.0, "min": 0.0, "max": 10.0}])
    assert "bloom" in app.registered_plugins


def test_gui_set_get_param():
    app = VJLiveGUIApp()
    app.register_plugin("bloom", [{"name": "intensity", "default": 5.0}])
    app.set_param("bloom", "intensity", 7.0)
    assert app.get_param("bloom", "intensity") == pytest.approx(7.0)


def test_gui_on_change_callback():
    app = VJLiveGUIApp()
    app.register_plugin("bloom", [{"name": "intensity", "default": 5.0}])
    calls = []
    app.on_change(lambda p, par, v: calls.append((p, par, v)))
    app.set_param("bloom", "intensity", 9.0)
    assert calls == [("bloom", "intensity", 9.0)]


def test_gui_get_param_unregistered_returns_none():
    app = VJLiveGUIApp()
    assert app.get_param("nonexistent", "p") is None


def test_gui_backend_not_headless_raises():
    app = VJLiveGUIApp(UIBackend.PYQT6)
    with pytest.raises(NotImplementedError):
        app.start()


# ── CollaborativeStudio ───────────────────────────────────────────────────────

def test_collab_join_and_count():
    cs = CollaborativeStudio()
    assert cs.join("user1", "dj")
    assert cs.session_count == 1


def test_collab_invalid_role():
    cs = CollaborativeStudio()
    assert not cs.join("user1", "superhero")


def test_collab_leave():
    cs = CollaborativeStudio()
    cs.join("user1", "dj")
    cs.leave("user1")
    assert cs.session_count == 0


def test_collab_viewer_cannot_set_param():
    cs = CollaborativeStudio()
    cs.join("viewer1", "viewer")
    assert not cs.set_param("viewer1", "bloom", "intensity", 7.0)


def test_collab_dj_can_set_param():
    cs = CollaborativeStudio()
    cs.join("dj1", "dj")
    assert cs.set_param("dj1", "bloom", "intensity", 7.0)
    params = cs.get_shared_params()
    assert params["bloom"]["intensity"] == pytest.approx(7.0)


def test_collab_session_ids():
    cs = CollaborativeStudio()
    cs.join("a", "dj"); cs.join("b", "operator")
    assert set(cs.session_ids) == {"a", "b"}


# ── QuantumCollaborativeStudio ────────────────────────────────────────────────

def test_quantum_superposition_and_collapse_blend():
    qc = QuantumCollaborativeStudio()
    qc.join("q1", "dj")
    qc.put_superposition("q1", "bloom", "intensity", [(3.0, 1.0), (7.0, 1.0)])
    val = qc.collapse("bloom", "intensity", blend=True)
    assert val == pytest.approx(5.0, abs=0.1)


def test_quantum_collapse_max_amplitude():
    qc = QuantumCollaborativeStudio()
    qc.join("q1", "dj")
    qc.put_superposition("q1", "bloom", "intensity", [(3.0, 0.1), (9.0, 0.9)])
    val = qc.collapse("bloom", "intensity", blend=False)
    assert val == pytest.approx(9.0)


def test_quantum_collapse_no_superposition_falls_back():
    qc = QuantumCollaborativeStudio()
    qc.join("q1", "dj")
    qc.set_param("q1", "bloom", "intensity", 5.5)
    val = qc.collapse("bloom", "intensity")
    assert val == pytest.approx(5.5)


def test_quantum_collapse_all():
    qc = QuantumCollaborativeStudio()
    qc.join("q1", "dj")
    qc.put_superposition("q1", "bloom", "intensity", [(4.0, 0.5), (8.0, 0.5)])
    result = qc.collapse_all()
    assert "bloom" in result
    assert "intensity" in result["bloom"]


def test_quantum_clear_superpositions():
    qc = QuantumCollaborativeStudio()
    qc.join("q1", "dj")
    qc.put_superposition("q1", "bloom", "intensity", [(5.0, 1.0)])
    qc.clear_superpositions()
    assert qc.collapse_all() == {}


def test_quantum_superposition_unknown_session():
    qc = QuantumCollaborativeStudio()
    result = qc.put_superposition("ghost", "bloom", "intensity", [(5.0, 1.0)])
    assert not result
