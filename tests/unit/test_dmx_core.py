"""Tests for DMX core: universe, fixture, output, fx, engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from vjlive3.dmx.universe import DMXUniverse
from vjlive3.dmx.fixture import Fixture, FixtureProfile
from vjlive3.dmx.output import NullOutput, _build_artnet_packet
from vjlive3.dmx.fx import ChaseEffect, StrobeEffect, RainbowEffect, FadeEffect
from vjlive3.dmx.engine import DMXEngine


# ---- DMXUniverse --------------------------------------------------------

def test_universe_set_get():
    u = DMXUniverse(0)
    u.set(1, 200)
    assert u.get(1) == 200

def test_universe_clamps_max():
    u = DMXUniverse(0)
    u.set(1, 999)
    assert u.get(1) == 255

def test_universe_clamps_min():
    u = DMXUniverse(0)
    u.set(1, -50)
    assert u.get(1) == 0

def test_universe_channel_out_of_range():
    u = DMXUniverse(0)
    with pytest.raises(ValueError):
        u.set(0, 100)    # 0 is invalid (1-indexed)
    with pytest.raises(ValueError):
        u.set(513, 100)  # > 512

def test_universe_set_range():
    u = DMXUniverse(0)
    u.set_range(1, [255, 128, 64])
    assert u.get(1) == 255
    assert u.get(2) == 128
    assert u.get(3) == 64

def test_universe_set_range_overflow():
    u = DMXUniverse(0)
    with pytest.raises(ValueError):
        u.set_range(511, [100, 100, 100])  # would go 511-513

def test_universe_get_frame_is_bytes():
    u = DMXUniverse(0)
    u.set(10, 77)
    frame = u.get_frame()
    assert isinstance(frame, bytes)
    assert len(frame) == 512
    assert frame[9] == 77

def test_universe_get_frame_is_immutable():
    u = DMXUniverse(0)
    frame = u.get_frame()
    with pytest.raises((TypeError, AttributeError)):
        frame[0] = 99  # bytes are immutable

def test_universe_blackout():
    u = DMXUniverse(0)
    u.set(1, 255)
    u.blackout()
    assert u.get(1) == 0


# ---- Fixture ------------------------------------------------------------

def make_rgb_fixture(start=1):
    u = DMXUniverse(0)
    return Fixture("test", start, FixtureProfile.RGB, u), u

def test_fixture_set_rgb():
    fix, u = make_rgb_fixture()
    fix.set_rgb(100, 150, 200)
    assert u.get(1) == 100
    assert u.get(2) == 150
    assert u.get(3) == 200

def test_fixture_set_all():
    fix, u = make_rgb_fixture()
    fix.set_all(77)
    assert u.get(1) == 77
    assert u.get(3) == 77

def test_fixture_blackout():
    fix, u = make_rgb_fixture()
    fix.set_rgb(255, 255, 255)
    fix.blackout()
    assert u.get(1) == 0

def test_fixture_channel_out_of_range():
    fix, u = make_rgb_fixture()
    with pytest.raises(ValueError):
        fix.set_channel(3, 100)  # 0-indexed, 3 >= channel_count for RGB

def test_dimmer_fixture_set_dim():
    u = DMXUniverse(0)
    fix = Fixture("dim", 10, FixtureProfile.DIMMER, u)
    fix.set_dim(200)
    assert u.get(10) == 200

def test_fixture_hsv():
    fix, u = make_rgb_fixture()
    fix.set_rgb_from_hsv(0.0, 1.0, 1.0)  # red
    assert u.get(1) == 255
    assert u.get(2) == 0
    assert u.get(3) == 0

def test_fixture_get_values():
    fix, u = make_rgb_fixture()
    fix.set_rgb(10, 20, 30)
    assert fix.get_values() == [10, 20, 30]


# ---- Output -------------------------------------------------------------

def test_null_output_no_crash():
    out = NullOutput()
    out.send(0, bytes(512))
    out.close()

def test_artnet_packet_length():
    frame = bytes(512)
    pkt = _build_artnet_packet(0, frame)
    assert len(pkt) == 512 + 18  # 18-byte header

def test_artnet_packet_id():
    pkt = _build_artnet_packet(0, bytes(512))
    assert pkt[:7] == b"Art-Net"


# ---- FX effects ---------------------------------------------------------

def make_fixtures(n=3):
    u = DMXUniverse(0)
    return [Fixture(f"f{i}", i * 3 + 1, FixtureProfile.RGB, u) for i in range(n)], u

def test_chase_effect_lights_one_fixture():
    fixtures, u = make_fixtures(3)
    chase = ChaseEffect(fixtures, speed=10.0)  # fast so _t=0 → idx=0
    chase.tick(dt=0.0)
    # fixture 0 should be lit
    assert fixtures[0].get_values() == [255, 255, 255]
    # fixtures 1,2 should be black
    assert fixtures[1].get_values() == [0, 0, 0]

def test_strobe_effect_on_phase():
    fixtures, u = make_fixtures(2)
    strobe = StrobeEffect(fixtures, rate_hz=10.0)
    strobe.tick(dt=0.0)  # _t=0, in "on" half of period
    assert fixtures[0].get_values()[0] == 255

def test_rainbow_effect_varies_hue():
    fixtures, u = make_fixtures(3)
    rainbow = RainbowEffect(fixtures, speed=1.0)
    rainbow.tick(dt=0.25)
    vals0 = tuple(fixtures[0].get_values())
    vals1 = tuple(fixtures[1].get_values())
    # With 3 evenly-spaced hues the colours should differ
    assert vals0 != vals1

def test_fade_effect_completes():
    fixtures, u = make_fixtures(1)
    fade = FadeEffect(fixtures, target=200, duration=1.0, start=0)
    fade.tick(dt=0.5)
    assert fade.enabled is True
    fade.tick(dt=0.5)
    assert fade.enabled is False  # past duration

def test_disabled_effect_skipped():
    fixtures, u = make_fixtures(1)
    chase = ChaseEffect(fixtures, speed=1.0)
    chase.enabled = False
    chase.tick(dt=0.1)
    assert fixtures[0].get_values() == [0, 0, 0]  # untouched


# ---- DMXEngine ----------------------------------------------------------

def test_engine_add_universe_and_fixture():
    engine = DMXEngine(output=NullOutput())
    engine.add_universe(0)
    fix = engine.add_fixture("wash", 0, 1, FixtureProfile.RGB)
    assert fix is not None
    assert "wash" in engine.list_fixtures()

def test_engine_creates_universe_if_missing():
    engine = DMXEngine(output=NullOutput())
    engine.add_fixture("wash", universe_id=0, start_channel=1, profile=FixtureProfile.RGB)
    assert engine.get_universe(0) is not None

def test_engine_duplicate_fixture_raises():
    engine = DMXEngine(output=NullOutput())
    engine.add_fixture("wash", 0, 1, FixtureProfile.RGB)
    with pytest.raises(ValueError):
        engine.add_fixture("wash", 0, 4, FixtureProfile.RGB)

def test_engine_tick_no_crash():
    engine = DMXEngine(output=NullOutput())
    engine.add_fixture("spot", 0, 1, FixtureProfile.RGB)
    engine.tick(dt=0.016)  # must not raise

def test_engine_fx_applied():
    engine = DMXEngine(output=NullOutput())
    fix = engine.add_fixture("spot", 0, 1, FixtureProfile.RGB)
    from vjlive3.dmx.fx import StrobeEffect
    engine.add_effect(StrobeEffect([fix], rate_hz=1000.0))  # always on at dt=0
    engine.tick(dt=0.0)
    assert fix.get_values()[0] == 255

def test_engine_clear_effects():
    engine = DMXEngine(output=NullOutput())
    engine.add_effect(FadeEffect([], target=255, duration=1.0))
    engine.clear_effects()
    assert len(engine._effects) == 0

def test_engine_blackout_all():
    engine = DMXEngine(output=NullOutput())
    fix = engine.add_fixture("spot", 0, 1, FixtureProfile.RGB)
    fix.set_rgb(255, 255, 255)
    engine.blackout_all()
    assert fix.get_values() == [0, 0, 0]

def test_engine_fade_effect_culled_when_done():
    engine = DMXEngine(output=NullOutput())
    fix = engine.add_fixture("f", 0, 1, FixtureProfile.DIMMER)
    fade = FadeEffect([fix], target=255, duration=0.01, start=0)
    engine.add_effect(fade)
    engine.tick(dt=1.0)  # way past duration → fade done → culled
    assert len(engine._effects) == 0
