"""Tests for MIDIController — hardware-free using simulate_cc/note_on."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from vjlive3.midi.controller import MIDIController, MIDIMapping, MIDIMode


# ---- MIDIMapping validation --------------------------------------------- #

def test_mapping_valid():
    m = MIDIMapping(channel=0, control=7, target="blur.radius", min_val=0.0, max_val=20.0)
    assert m.target == "blur.radius"

def test_mapping_bad_channel():
    with pytest.raises(ValueError, match="channel"):
        MIDIMapping(channel=16, control=7, target="x.y")

def test_mapping_bad_control():
    with pytest.raises(ValueError, match="control"):
        MIDIMapping(channel=0, control=128, target="x.y")

def test_mapping_bad_range():
    with pytest.raises(ValueError, match="min_val"):
        MIDIMapping(channel=0, control=7, target="x.y", min_val=5.0, max_val=5.0)

def test_mapping_scale_midpoint():
    m = MIDIMapping(channel=0, control=7, target="x.y", min_val=0.0, max_val=10.0)
    scaled = m.scale(63)
    assert pytest.approx(scaled, abs=0.1) == 4.96  # 63/127 * 10


# ---- CC callbacks ------------------------------------------------------- #

def test_cc_callback_fires():
    received = []
    ctrl = MIDIController()
    ctrl.add_cc_callback(lambda ch, cc, val: received.append((ch, cc, val)))
    ctrl.simulate_cc(0, 7, 100)
    assert received == [(0, 7, 100)]

def test_multiple_cc_callbacks():
    a, b = [], []
    ctrl = MIDIController()
    ctrl.add_cc_callback(lambda ch, cc, val: a.append(val))
    ctrl.add_cc_callback(lambda ch, cc, val: b.append(val))
    ctrl.simulate_cc(1, 10, 64)
    assert a == [64] and b == [64]


# ---- Note callbacks ----------------------------------------------------- #

def test_note_on_callback():
    notes = []
    ctrl = MIDIController()
    ctrl.add_note_on_callback(lambda ch, n, v: notes.append((ch, n, v)))
    ctrl.simulate_note_on(0, 60, 100)
    assert notes == [(0, 60, 100)]


# ---- CC → parameter mapping --------------------------------------------- #

def test_cc_drives_mapping():
    ctrl = MIDIController()
    ctrl.add_mapping(MIDIMapping(channel=0, control=7, target="gain.val",
                                 min_val=0.0, max_val=10.0))
    ctrl.simulate_cc(0, 7, 127)
    assert ctrl.get_param_value("gain.val") == pytest.approx(10.0)

def test_cc_no_match_does_not_update():
    ctrl = MIDIController()
    ctrl.add_mapping(MIDIMapping(channel=0, control=7, target="x.y"))
    ctrl.simulate_cc(0, 8, 127)  # different CC
    assert ctrl.get_param_value("x.y") == 0.0

def test_mapping_replaces_same_cc():
    ctrl = MIDIController()
    ctrl.add_mapping(MIDIMapping(channel=0, control=7, target="a.b"))
    ctrl.add_mapping(MIDIMapping(channel=0, control=7, target="c.d"))  # replaces
    assert len(ctrl._mappings) == 1
    assert ctrl._mappings[0].target == "c.d"

def test_remove_mapping():
    ctrl = MIDIController()
    m = MIDIMapping(channel=0, control=7, target="x.y")
    ctrl.add_mapping(m)
    ok = ctrl.remove_mapping(m.id)
    assert ok is True
    assert len(ctrl._mappings) == 0


# ---- NodeGraph integration ---------------------------------------------- #

def test_bind_graph_set_param():
    calls = []
    ctrl = MIDIController()
    ctrl.bind_graph(lambda path, val: calls.append((path, val)) or True)
    ctrl.add_mapping(MIDIMapping(channel=0, control=1, target="node.param",
                                 min_val=0.0, max_val=1.0))
    ctrl.simulate_cc(0, 1, 64)
    assert len(calls) == 1
    assert calls[0][0] == "node.param"
    assert pytest.approx(calls[0][1], abs=0.01) == 0.504  # 64/127


# ---- MIDI Learn --------------------------------------------------------- #

def test_learn_mode_captures_cc():
    learned = []
    ctrl = MIDIController()
    ctrl.enable_learning("blur.radius", callback=lambda m: learned.append(m))
    assert ctrl.mode == MIDIMode.LEARNING
    ctrl.simulate_cc(0, 14, 80)  # this CC should be learned
    # After learning, mode should be NORMAL again
    assert ctrl.mode == MIDIMode.NORMAL
    assert len(learned) == 1
    assert learned[0].target == "blur.radius"
    assert learned[0].control == 14

def test_disable_learning():
    ctrl = MIDIController()
    ctrl.enable_learning("x.y")
    ctrl.disable_learning()
    assert ctrl.mode == MIDIMode.NORMAL


# ---- Status / NullMIDI -------------------------------------------------- #

def test_status_dict():
    ctrl = MIDIController()
    s = ctrl.get_status()
    assert "mode" in s and "connected" in s and "mappings" in s

def test_list_devices_no_crash():
    devs = MIDIController.list_devices()
    assert isinstance(devs, list)

def test_null_midi_start():
    """Without mido/hardware, start() should return True in NullMIDI mode."""
    from vjlive3.midi import controller as _ctrl_mod
    orig = _ctrl_mod._MIDO_AVAILABLE
    _ctrl_mod._MIDO_AVAILABLE = False
    try:
        ctrl = MIDIController()
        result = ctrl.start()
        assert result is True
        ctrl.stop()
    finally:
        _ctrl_mod._MIDO_AVAILABLE = orig
