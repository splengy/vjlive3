"""Tests for P3-EXT008: Arbhar Granularizer (ArbharGranularizerPlugin)."""
import sys, pytest
from unittest.mock import MagicMock, patch

_g = MagicMock()
_g.glGetShaderiv.return_value   = 1
_g.glGetProgramiv.return_value  = 1
_g.glCreateProgram.return_value = 99
_g.glGenVertexArrays.return_value = 44
_g.glGenFramebuffers.return_value = 55
_g.glGenTextures.return_value   = 101
for attr in ("GL_VERTEX_SHADER","GL_FRAGMENT_SHADER","GL_COMPILE_STATUS","GL_LINK_STATUS",
             "GL_TEXTURE_2D","GL_TRIANGLE_STRIP","GL_TEXTURE0","GL_TEXTURE1",
             "GL_RGB","GL_UNSIGNED_BYTE","GL_LINEAR","GL_CLAMP_TO_EDGE",
             "GL_TEXTURE_MIN_FILTER","GL_TEXTURE_MAG_FILTER","GL_TEXTURE_WRAP_S","GL_TEXTURE_WRAP_T",
             "GL_FRAMEBUFFER","GL_COLOR_ATTACHMENT0"):
    setattr(_g, attr, MagicMock())

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _g

from vjlive3.plugins.arbhar_granularizer import (
    ArbharGranularizerPlugin, METADATA, PRESETS, MAX_GRAINS
)


@pytest.fixture(autouse=True)
def reset_gl():
    _g.reset_mock()
    _g.glGetShaderiv.return_value   = 1
    _g.glGetProgramiv.return_value  = 1
    _g.glCreateProgram.return_value = 99
    _g.glGenVertexArrays.return_value = 44
    _g.glGenFramebuffers.return_value = 55
    _g.glGenTextures.return_value   = 101


@pytest.fixture
def plugin(): return ArbharGranularizerPlugin()


@pytest.fixture
def ctx():
    c = MagicMock()(MagicMock())
    c.width = 64; c.height = 48; c.time = 0.0
    c.inputs = {"video_in": 10}; c.outputs = {}
    return c


def test_metadata_name():      assert METADATA["name"] == "Arbhar Granularizer"
def test_metadata_8_params():  assert len(METADATA["parameters"]) == 8
def test_presets_5():          assert len(PRESETS) == 5
def test_max_grains():         assert MAX_GRAINS == 256


# ── Grain management ──────────────────────────────────────────────────────────

def test_grain_spawn(plugin):
    plugin._update_grains(1.0, 10.0, 0.0)   # high density×intensity ensures spawn_count >= 1
    assert len(plugin._grains) > 0

def test_grain_max_limit(plugin):
    # Spawn massively
    for _ in range(20):
        plugin._update_grains(1.0, 1.0, 0.0)
    assert len(plugin._grains) <= MAX_GRAINS

def test_grain_ages(plugin):
    plugin._grains = [[0.5, 0.5, 0, 10]]   # 1 grain, lifetime=10
    plugin._update_grains(0., 0., 0.)
    if plugin._grains:
        assert plugin._grains[0][2] == 1   # age incremented

def test_grain_removed_when_old(plugin):
    plugin._grains = [[0.5, 0.5, 100, 5]]   # age > lifetime
    plugin._update_grains(0., 0., 0.)
    assert len(plugin._grains) == 0

def test_grain_spray_jitter(plugin):
    plugin._grains = [[0.5, 0.5, 0, 100]]
    plugin._update_grains(0., 0., 1.0)   # high spray
    if plugin._grains:
        # Position may have shifted
        assert 0.0 <= plugin._grains[0][0] <= 1.0


# ── Audio reactivity ──────────────────────────────────────────────────────────

def test_audio_update_no_crash(plugin):
    plugin.update_audio({"beat": 0.8, "energy": 0.6, "tempo": 0.5})

def test_audio_empty_dict(plugin):
    plugin.update_audio({})


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@patch('vjlive3.plugins.arbhar_granularizer.gl', _g)
def test_initialize(plugin, ctx): assert plugin.initialize(ctx) is True

@patch('vjlive3.plugins.arbhar_granularizer.gl', _g)
def test_zero_texture(plugin, ctx): assert plugin.process_frame(0, {}, ctx) == 0

@patch('vjlive3.plugins.arbhar_granularizer.gl', _g)
def test_draw_called(plugin, ctx):
    plugin.initialize(ctx); plugin.process_frame(10, {}, ctx)
    _g.glDrawArrays.assert_called()

@patch('vjlive3.plugins.arbhar_granularizer.gl', _g)
def test_all_params(plugin, ctx):
    plugin.initialize(ctx)
    params = {p["name"]: p["default"] for p in METADATA["parameters"]}
    assert plugin.process_frame(10, params, ctx) is not None

@patch('vjlive3.plugins.arbhar_granularizer.gl', _g)
def test_preset_feedback_heavy(plugin, ctx):
    plugin.initialize(ctx)
    assert plugin.process_frame(10, PRESETS["feedback_heavy"], ctx) is not None

@patch('vjlive3.plugins.arbhar_granularizer.gl', _g)
def test_compile_failure(plugin, ctx):
    _g.glGetShaderiv.return_value = 0; _g.glGetShaderInfoLog.return_value = b"err"
    assert plugin.initialize(ctx) is False

def test_mock_mode(plugin, ctx):
    plugin._mock_mode = True
    assert plugin.process_frame(10, {}, ctx) == 10
