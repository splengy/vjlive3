"""Tests for AudioDMXBridge and audio-reactive DMX integration."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from vjlive3.dmx.universe import DMXUniverse
from vjlive3.dmx.fixture import Fixture, FixtureProfile
from vjlive3.dmx.audio_reactive import AudioDMXBridge
from vjlive3.dmx.engine import DMXEngine
from vjlive3.dmx.output import NullOutput


# ---- Fake AudioSnapshot -------------------------------------------------

class _Snap:
    """Minimal AudioSnapshot stub."""
    def __init__(self, rms=0.0, bass=0.0, mids=0.0, highs=0.0,
                 beat=False, bpm=0.0, onset_strength=0.0):
        self.rms            = rms
        self.bass           = bass
        self.mids           = mids
        self.highs          = highs
        self.beat           = beat
        self.bpm            = bpm
        self.onset_strength = onset_strength


def make_rgb_fixture(name="fx"):
    u = DMXUniverse(0)
    return Fixture(name, 1, FixtureProfile.RGB, u), u


# ---- AudioDMXBridge -----------------------------------------------------

def test_map_rms_to_dim():
    bridge = AudioDMXBridge()
    fix, u = make_rgb_fixture()
    bridge.map("rms", "fx", mode="dim", scale=255.0)
    snap = _Snap(rms=1.0)
    bridge.tick(snap, {"fx": fix})
    # set_dim on RGB scales all channels by 1.0 → 255
    assert u.get(1) == 255

def test_map_bass_to_red():
    bridge = AudioDMXBridge()
    fix, u = make_rgb_fixture()
    bridge.map("bass", "fx", mode="red", scale=200.0)
    snap = _Snap(bass=0.5)
    bridge.tick(snap, {"fx": fix})
    assert u.get(1) == 100  # 0.5*200 = 100

def test_map_beat_flash_on():
    bridge = AudioDMXBridge()
    u = DMXUniverse(0)
    fix = Fixture("fx", 1, FixtureProfile.DIMMER, u)
    bridge.map("beat", "fx", mode="flash")
    snap = _Snap(beat=True)
    bridge.tick(snap, {"fx": fix})
    assert u.get(1) == 255  # beat=True → full on

def test_map_beat_flash_off():
    bridge = AudioDMXBridge()
    u = DMXUniverse(0)
    fix = Fixture("fx", 1, FixtureProfile.DIMMER, u)
    bridge.map("beat", "fx", mode="flash")
    snap = _Snap(beat=False)
    bridge.tick(snap, {"fx": fix})
    assert u.get(1) == 0   # beat=False → off

def test_map_rgb_uniform():
    bridge = AudioDMXBridge()
    fix, u = make_rgb_fixture()
    bridge.map("mids", "fx", mode="rgb_uniform", scale=255.0)
    snap = _Snap(mids=0.5)
    bridge.tick(snap, {"fx": fix})
    assert u.get(1) == 127  # 0.5*255 = 127 (int floors)

def test_unmap_removes_mapping():
    bridge = AudioDMXBridge()
    fix, u = make_rgb_fixture()
    mid = bridge.map("rms", "fx", mode="dim", scale=255.0)
    bridge.unmap(mid)
    snap = _Snap(rms=1.0)
    bridge.tick(snap, {"fx": fix})
    # No mapping active — fixture stays at 0
    assert u.get(1) == 0

def test_unknown_feature_raises():
    bridge = AudioDMXBridge()
    with pytest.raises(ValueError, match="Unknown audio feature"):
        bridge.map("tempo", "fx", mode="dim")

def test_unknown_mode_raises():
    bridge = AudioDMXBridge()
    with pytest.raises(ValueError, match="Unknown mode"):
        bridge.map("rms", "fx", mode="wobble")

def test_missing_fixture_does_not_crash():
    bridge = AudioDMXBridge()
    bridge.map("rms", "nonexistent_fixture", mode="dim")
    snap = _Snap(rms=1.0)
    bridge.tick(snap, {})  # no fixture → silent skip

def test_list_mappings():
    bridge = AudioDMXBridge()
    bridge.map("rms", "fx1", mode="dim")
    bridge.map("bass", "fx2", mode="red")
    assert len(bridge.list_mappings()) == 2

def test_offset_applied():
    bridge = AudioDMXBridge()
    u = DMXUniverse(0)
    fix = Fixture("fx", 1, FixtureProfile.DIMMER, u)
    bridge.map("rms", "fx", mode="dim", scale=0.0, offset=100.0)
    snap = _Snap(rms=0.0)
    bridge.tick(snap, {"fx": fix})
    assert u.get(1) == 100


# ---- Engine integration -------------------------------------------------

def test_engine_audio_bridge_via_tick():
    engine = DMXEngine(output=NullOutput())
    fix = engine.add_fixture("spot", universe_id=0, start_channel=1,
                             profile=FixtureProfile.DIMMER)
    engine.audio_bridge.map("rms", "spot", mode="dim", scale=255.0)
    snap = _Snap(rms=0.8)
    engine.tick(dt=0.016, audio_snapshot=snap)
    # 0.8 * 255 = 204
    assert fix.get_values()[0] == 204

def test_engine_no_audio_snapshot_does_not_crash():
    engine = DMXEngine(output=NullOutput())
    engine.add_fixture("spot", 0, 1, FixtureProfile.RGB)
    engine.tick(dt=0.016, audio_snapshot=None)  # must not raise
