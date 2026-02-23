"""Tests for P3-EXT006: Analog TV Effect (AnalogTVPlugin)."""
import sys, pytest
from unittest.mock import MagicMock, patch

_g = MagicMock()
_g.glGetShaderiv.return_value   = 1
_g.glGetProgramiv.return_value  = 1
_g.glCreateProgram.return_value = 99
_g.glGenVertexArrays.return_value = 44
for attr in ("GL_VERTEX_SHADER","GL_FRAGMENT_SHADER","GL_COMPILE_STATUS","GL_LINK_STATUS",
             "GL_TEXTURE_2D","GL_TRIANGLE_STRIP","GL_TEXTURE0"):
    setattr(_g, attr, MagicMock())

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _g

from vjlive3.plugins.analog_tv import AnalogTVPlugin, METADATA, PRESETS, _remap, _RANGES


@pytest.fixture(autouse=True)
def reset_gl():
    _g.reset_mock()
    _g.glGetShaderiv.return_value   = 1
    _g.glGetProgramiv.return_value  = 1
    _g.glCreateProgram.return_value = 99
    _g.glGenVertexArrays.return_value = 44


@pytest.fixture
def plugin(): return AnalogTVPlugin()

@pytest.fixture
def ctx():
    c = MagicMock()(MagicMock())
    c.width = 64; c.height = 48; c.time = 0.0
    c.inputs = {"video_in": 10}; c.outputs = {}
    return c


# ── Metadata ──────────────────────────────────────────────────────────────────

def test_metadata_name():         assert METADATA["name"] == "Analog TV"
def test_metadata_29_params():    assert len(METADATA["parameters"]) == 29  # 28 analog + mix
def test_metadata_tags():
    for t in ("analog", "vhs", "crt", "glitch", "retro"):
        assert t in METADATA["tags"]
def test_metadata_all_ranges():
    for p in METADATA["parameters"]:
        assert p["min"] == 0.0 and p["max"] == 10.0
def test_presets_5():             assert len(PRESETS) == 5


# ── Parameter remap ───────────────────────────────────────────────────────────

def test_remap_vhs_tracking_0():  assert _remap("vhs_tracking", 0.0)  == 0.0
def test_remap_vhs_tracking_10(): assert _remap("vhs_tracking", 10.0) == 1.0
def test_remap_dropout_length_0():
    lo, hi = _RANGES["dropout_length"]
    assert abs(_remap("dropout_length", 0.0) - lo) < 1e-6
def test_remap_scanline_freq_10():
    lo, hi = _RANGES["scanline_freq"]
    assert abs(_remap("scanline_freq", 10.0) - hi) < 1e-6
def test_remap_out_of_range_clamped():
    assert _remap("vhs_tracking", -5.0) == 0.0
    assert _remap("vhs_tracking", 99.0) == 1.0

def test_all_29_params_have_range():
    from vjlive3.plugins.analog_tv import _PARAMS
    assert len(_PARAMS) == 28  # 28 explicit analog params (mix added separately in METADATA)
    for n, *_ in _PARAMS:
        assert n in _RANGES


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@patch('vjlive3.plugins.analog_tv.gl', _g)
def test_initialize(plugin, ctx): assert plugin.initialize(ctx) is True

@patch('vjlive3.plugins.analog_tv.gl', _g)
def test_zero_texture(plugin, ctx): assert plugin.process_frame(0, {}, ctx) == 0

@patch('vjlive3.plugins.analog_tv.gl', _g)
def test_process_calls_draw(plugin, ctx):
    plugin.initialize(ctx); plugin.process_frame(10, {}, ctx)
    _g.glDrawArrays.assert_called()

@patch('vjlive3.plugins.analog_tv.gl', _g)
def test_process_sets_many_uniforms(plugin, ctx):
    plugin.initialize(ctx); plugin.process_frame(10, {}, ctx)
    assert _g.glUniform1f.call_count >= 10  # At least one per param

@patch('vjlive3.plugins.analog_tv.gl', _g)
def test_all_params(plugin, ctx):
    plugin.initialize(ctx)
    params = {p["name"]: p["default"] for p in METADATA["parameters"]}
    assert plugin.process_frame(10, params, ctx) is not None

@patch('vjlive3.plugins.analog_tv.gl', _g)
def test_preset_clean_crt(plugin, ctx):
    plugin.initialize(ctx)
    assert plugin.process_frame(10, PRESETS["clean_crt"], ctx) is not None

@patch('vjlive3.plugins.analog_tv.gl', _g)
def test_preset_extreme_glitch(plugin, ctx):
    plugin.initialize(ctx)
    assert plugin.process_frame(10, PRESETS["extreme_glitch"], ctx) is not None

@patch('vjlive3.plugins.analog_tv.gl', _g)
def test_compile_failure(plugin, ctx):
    _g.glGetShaderiv.return_value = 0; _g.glGetShaderInfoLog.return_value = b"err"
    assert plugin.initialize(ctx) is False
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.analog_tv.gl', _g)
def test_cleanup(plugin, ctx):
    plugin.initialize(ctx); plugin.prog = 99; plugin.cleanup()
    _g.glDeleteProgram.assert_called_with(99)

def test_mock_mode(plugin, ctx):
    plugin._mock_mode = True
    assert plugin.process_frame(10, {}, ctx) == 10
    assert ctx.outputs.get('video_out') == 10
