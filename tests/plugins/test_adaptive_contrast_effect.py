"""Tests for P3-EXT002: Adaptive Contrast Effect (AdaptiveContrastPlugin)."""
import sys, pytest
from unittest.mock import MagicMock, patch

_g = MagicMock()
_g.glGetShaderiv.return_value   = 1
_g.glGetProgramiv.return_value  = 1
_g.glCreateProgram.return_value = 99
_g.glGenVertexArrays.return_value = 44
_g.glGenFramebuffers.return_value = 51
_g.glGenTextures.return_value   = 101
for attr in ("GL_VERTEX_SHADER","GL_FRAGMENT_SHADER","GL_COMPILE_STATUS","GL_LINK_STATUS",
             "GL_TEXTURE_2D","GL_RGBA","GL_UNSIGNED_BYTE","GL_LINEAR","GL_CLAMP_TO_EDGE",
             "GL_TEXTURE_MIN_FILTER","GL_TEXTURE_MAG_FILTER","GL_TEXTURE_WRAP_S",
             "GL_TEXTURE_WRAP_T","GL_FRAMEBUFFER","GL_COLOR_ATTACHMENT0",
             "GL_COLOR_BUFFER_BIT","GL_TRIANGLE_STRIP"):
    setattr(_g, attr, MagicMock())

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _g

from vjlive3.plugins.adaptive_contrast import AdaptiveContrastPlugin, METADATA, PRESETS
from vjlive3.plugins.api import PluginContext


@pytest.fixture(autouse=True)
def reset_gl():
    _g.reset_mock()
    _g.glGetShaderiv.return_value   = 1
    _g.glGetProgramiv.return_value  = 1
    _g.glCreateProgram.return_value = 99
    _g.glGenVertexArrays.return_value = 44
    _g.glGenFramebuffers.return_value = 51
    _g.glGenTextures.return_value   = 101


@pytest.fixture
def plugin(): return AdaptiveContrastPlugin()


@pytest.fixture
def ctx():
    c = PluginContext(MagicMock())
    c.width = 64; c.height = 48; c.time = 0.0
    c.inputs = {"video_in": 10}; c.outputs = {}
    return c


def test_metadata_name():       assert METADATA["name"] == "Adaptive Contrast"
def test_metadata_7_params():   assert len(METADATA["parameters"]) == 7  # 6 core + mix
def test_required_tags():
    tags = METADATA["tags"]
    for t in ("contrast", "adaptive", "dynamics", "auto-level"):
        assert t in tags
def test_metadata_min_max_default():
    for p in METADATA["parameters"]:
        assert all(k in p for k in ("min", "max", "default"))
def test_presets_count():       assert len(PRESETS) == 5


@patch('vjlive3.plugins.adaptive_contrast.gl', _g)
def test_initialize(plugin, ctx):   assert plugin.initialize(ctx) is True

@patch('vjlive3.plugins.adaptive_contrast.gl', _g)
def test_zero_tex_returns_zero(plugin, ctx):
    plugin.initialize(ctx);  assert plugin.process_frame(0, {}, ctx) == 0

@patch('vjlive3.plugins.adaptive_contrast.gl', _g)
def test_process_calls_draw(plugin, ctx):
    plugin.initialize(ctx); plugin.process_frame(10, {}, ctx)
    _g.glDrawArrays.assert_called()

@patch('vjlive3.plugins.adaptive_contrast.gl', _g)
def test_video_out_set(plugin, ctx):
    plugin.initialize(ctx); plugin.process_frame(10, {}, ctx)
    assert 'video_out' in ctx.outputs

@patch('vjlive3.plugins.adaptive_contrast.gl', _g)
def test_all_params(plugin, ctx):
    plugin.initialize(ctx)
    params = {p["name"]: p["default"] for p in METADATA["parameters"]}
    assert plugin.process_frame(10, params, ctx) is not None

@patch('vjlive3.plugins.adaptive_contrast.gl', _g)
def test_compile_failure(plugin, ctx):
    _g.glGetShaderiv.return_value = 0
    _g.glGetShaderInfoLog.return_value = b"err"
    assert plugin.initialize(ctx) is False
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.adaptive_contrast.gl', _g)
def test_cleanup(plugin, ctx):
    plugin.initialize(ctx); plugin.prog = 99; plugin.cleanup()
    _g.glDeleteProgram.assert_called_with(99)

def test_mock_mode(plugin, ctx):
    plugin._mock_mode = True
    assert plugin.process_frame(10, {}, ctx) == 10
    assert ctx.outputs.get('video_out') == 10
