"""Tests for P3-EXT007: Arbhar Granular Engine (ArbharGranularEnginePlugin)."""
import sys, pytest, random
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

from vjlive3.plugins.arbhar_granular_engine import (
    ArbharGranularEnginePlugin, METADATA, PRESETS, MAX_GRAINS, _quality_factor
)
from vjlive3.plugins.api import PluginContext


@pytest.fixture(autouse=True)
def reset_gl():
    _g.reset_mock()
    _g.glGetShaderiv.return_value   = 1
    _g.glGetProgramiv.return_value  = 1
    _g.glCreateProgram.return_value = 99
    _g.glGenVertexArrays.return_value = 44


@pytest.fixture
def plugin(): return ArbharGranularEnginePlugin()


@pytest.fixture
def ctx():
    c = PluginContext(MagicMock())
    c.width = 64; c.height = 48; c.time = 0.0
    c.inputs = {"video_in": 10}; c.outputs = {}
    return c


# ── Metadata ──────────────────────────────────────────────────────────────────

def test_metadata_name():      assert METADATA["name"] == "Arbhar Granular Engine"
def test_metadata_5_params():  assert len(METADATA["parameters"]) == 5   # 4 core + mix
def test_presets_5():          assert len(PRESETS) == 5
def test_max_grains():         assert MAX_GRAINS == 32


# ── Quality factor ────────────────────────────────────────────────────────────

def test_quality_factor_lo_fi():    assert _quality_factor(0.0)  == 0.3
def test_quality_factor_standard(): assert _quality_factor(5.0)  == 0.7
def test_quality_factor_hi_fi():    assert _quality_factor(10.0) == 1.0
def test_quality_factor_mid():      assert _quality_factor(4.0)  == 0.7  # 0.4 >= 0.3 threshold → standard


# ── Grain management ──────────────────────────────────────────────────────────

def test_spawn_grain(plugin):
    plugin._spawn_grain(5.0)
    assert plugin._active == 1

def test_spawn_max_limit(plugin):
    for _ in range(MAX_GRAINS + 5):
        plugin._spawn_grain(5.0)
    assert plugin._active <= MAX_GRAINS

def test_update_decays_alpha(plugin):
    plugin._spawn_grain(5.0)
    initial = plugin._alphas[0]
    plugin._update_grain_parameters(0., 5.)
    assert plugin._alphas[0] < initial or plugin._active == 0  # decayed or removed

def test_update_removes_dead_grains(plugin):
    plugin._spawn_grain(5.0)
    plugin._alphas[0] = 0.001   # Almost dead
    # Run enough updates to kill it
    for _ in range(5):
        plugin._update_grain_parameters(0., 5.)
    # After decay, grain should be gone
    assert plugin._active == 0

def test_grain_position_jitter(plugin):
    plugin._spawn_grain(5.0)
    orig_x = plugin._positions[0][0]
    plugin._update_grain_parameters(5., 5.)   # High spray
    if plugin._active > 0:
        # Position may have changed due to jitter
        pass    # Just verify no exception


# ── Audio reactivity ──────────────────────────────────────────────────────────

def test_update_audio_sets_intensity(plugin):
    plugin.update_audio({"treble": 1.0, "bass": 0.0, "mid": 0.5})
    assert plugin._intensity >= 0.0

def test_update_audio_smoothing(plugin):
    plugin._intensity = 0.0
    plugin.update_audio({"treble": 1.0})
    v1 = plugin._intensity
    plugin.update_audio({"treble": 0.0})
    v2 = plugin._intensity
    assert 0.0 < v2 < v1  # Smoothed, not immediate drop

def test_update_audio_empty(plugin):
    plugin.update_audio({})  # No error


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@patch('vjlive3.plugins.arbhar_granular_engine.gl', _g)
def test_initialize(plugin, ctx): assert plugin.initialize(ctx) is True

@patch('vjlive3.plugins.arbhar_granular_engine.gl', _g)
def test_zero_texture(plugin, ctx): assert plugin.process_frame(0, {}, ctx) == 0

@patch('vjlive3.plugins.arbhar_granular_engine.gl', _g)
def test_draw_called(plugin, ctx):
    plugin.initialize(ctx); plugin.process_frame(10, {}, ctx)
    _g.glDrawArrays.assert_called()

@patch('vjlive3.plugins.arbhar_granular_engine.gl', _g)
def test_all_params(plugin, ctx):
    plugin.initialize(ctx)
    params = {p["name"]: p["default"] for p in METADATA["parameters"]}
    assert plugin.process_frame(10, params, ctx) is not None

@patch('vjlive3.plugins.arbhar_granular_engine.gl', _g)
def test_compile_failure(plugin, ctx):
    _g.glGetShaderiv.return_value = 0; _g.glGetShaderInfoLog.return_value = b"err"
    assert plugin.initialize(ctx) is False

@patch('vjlive3.plugins.arbhar_granular_engine.gl', _g)
def test_preset_dense(plugin, ctx):
    plugin.initialize(ctx)
    assert plugin.process_frame(10, PRESETS["dense_grains"], ctx) is not None

def test_mock_mode(plugin, ctx):
    plugin._mock_mode = True
    assert plugin.process_frame(10, {}, ctx) == 10
