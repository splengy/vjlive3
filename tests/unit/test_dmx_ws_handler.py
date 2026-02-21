"""Tests for DMX WebSocket handler."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from vjlive3.dmx.engine import DMXEngine
from vjlive3.dmx.fixture import FixtureProfile
from vjlive3.dmx.output import NullOutput
from vjlive3.dmx.ws_handler import DMXWebSocketHandler


def make_engine():
    engine = DMXEngine(output=NullOutput())
    engine.add_fixture("wash",  universe_id=0, start_channel=1,  profile=FixtureProfile.RGB)
    engine.add_fixture("spot",  universe_id=0, start_channel=4,  profile=FixtureProfile.DIMMER)
    engine.add_fixture("strobe",universe_id=0, start_channel=5,  profile=FixtureProfile.RGB)
    return engine


# ---- Unknown command ---------------------------------------------------- #

def test_unknown_cmd_returns_error():
    h = DMXWebSocketHandler(make_engine())
    r = h.handle({"cmd": "explode_everything"})
    assert r["ok"] is False
    assert "Unknown command" in r["error"]


# ---- set_channel -------------------------------------------------------- #

def test_set_channel():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "set_channel", "universe": 0, "channel": 1, "value": 200})
    assert r["ok"] is True
    assert engine.get_universe(0).get(1) == 200

def test_set_channel_creates_universe():
    engine = DMXEngine(output=NullOutput())
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "set_channel", "universe": 3, "channel": 1, "value": 100})
    assert r["ok"] is True


# ---- set_range ---------------------------------------------------------- #

def test_set_range():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "set_range", "universe": 0,
                  "start_channel": 1, "values": [255, 128, 64]})
    assert r["ok"] is True
    assert engine.get_universe(0).get(2) == 128


# ---- set_rgb / set_dim -------------------------------------------------- #

def test_set_rgb():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "set_rgb", "fixture": "wash", "r": 100, "g": 150, "b": 200})
    assert r["ok"] is True
    assert engine.get_fixture("wash").get_values() == [100, 150, 200]

def test_set_rgb_unknown_fixture():
    h = DMXWebSocketHandler(make_engine())
    r = h.handle({"cmd": "set_rgb", "fixture": "no_such", "r": 0, "g": 0, "b": 0})
    assert r["ok"] is False

def test_set_dim():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "set_dim", "fixture": "spot", "value": 180})
    assert r["ok"] is True
    assert engine.get_fixture("spot").get_values()[0] == 180


# ---- blackout ----------------------------------------------------------- #

def test_blackout():
    engine = make_engine()
    engine.get_fixture("wash").set_rgb(255, 255, 255)
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "blackout"})
    assert r["ok"] is True
    assert engine.get_fixture("wash").get_values() == [0, 0, 0]


# ---- list_fixtures ------------------------------------------------------ #

def test_list_fixtures():
    h = DMXWebSocketHandler(make_engine())
    r = h.handle({"cmd": "list_fixtures"})
    assert r["ok"] is True
    names = [f["name"] for f in r["fixtures"]]
    assert "wash" in names and "spot" in names


# ---- add_fixture -------------------------------------------------------- #

def test_add_fixture():
    engine = DMXEngine(output=NullOutput())
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "add_fixture", "name": "new_wash",
                  "start_channel": 1, "profile": "rgb", "universe": 0})
    assert r["ok"] is True
    assert engine.get_fixture("new_wash") is not None

def test_add_fixture_bad_profile():
    h = DMXWebSocketHandler(make_engine())
    r = h.handle({"cmd": "add_fixture", "name": "x",
                  "start_channel": 10, "profile": "laser_cannon"})
    assert r["ok"] is False


# ---- FX commands -------------------------------------------------------- #

def test_fx_chase():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "fx_chase", "fixtures": ["wash", "spot"], "speed": 3.0})
    assert r["ok"] is True
    assert len(engine._effects) == 1

def test_fx_strobe():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "fx_strobe", "fixtures": ["wash"], "rate_hz": 20.0})
    assert r["ok"] is True

def test_fx_rainbow():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "fx_rainbow", "fixtures": ["wash", "strobe"], "speed": 0.5})
    assert r["ok"] is True

def test_fx_fade():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "fx_fade", "fixtures": ["spot"],
                  "target": 200, "duration": 2.0, "start": 0})
    assert r["ok"] is True

def test_fx_clear():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    h.handle({"cmd": "fx_chase", "fixtures": ["wash"], "speed": 1.0})
    r = h.handle({"cmd": "fx_clear"})
    assert r["ok"] is True
    assert len(engine._effects) == 0


# ---- audio_map ---------------------------------------------------------- #

def test_audio_map():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    r = h.handle({"cmd": "audio_map", "feature": "rms",
                  "fixture": "wash", "mode": "dim", "scale": 255.0})
    assert r["ok"] is True
    assert "mapping_id" in r
    assert isinstance(r["mapping_id"], int)

def test_audio_unmap():
    engine = make_engine()
    h = DMXWebSocketHandler(engine)
    r1 = h.handle({"cmd": "audio_map", "feature": "bass", "fixture": "wash", "mode": "red"})
    mid = r1["mapping_id"]
    r2 = h.handle({"cmd": "audio_unmap", "mapping_id": mid})
    assert r2["ok"] is True


# ---- status ------------------------------------------------------------- #

def test_status():
    h = DMXWebSocketHandler(make_engine())
    r = h.handle({"cmd": "status"})
    assert r["ok"] is True
    assert "fixtures" in r
    assert r["fixtures"] == 3
