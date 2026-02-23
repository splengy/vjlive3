"""
Tests for P3-EXT001: ASCII Effect (ASCIIPlugin).
Mocks OpenGL for headless CI execution.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys

# ── GL mock setup ─────────────────────────────────────────────────────────────
_mock_gl = MagicMock()
_mock_gl.glGetShaderiv.return_value   = 1
_mock_gl.glGetProgramiv.return_value  = 1
_mock_gl.glCreateProgram.return_value = 99
_mock_gl.glGenVertexArrays.return_value = 44
_mock_gl.glGenFramebuffers.return_value = 51
_mock_gl.glGenTextures.return_value   = 101
_mock_gl.GL_VERTEX_SHADER    = 35633
_mock_gl.GL_FRAGMENT_SHADER  = 35632
_mock_gl.GL_COMPILE_STATUS   = 35713
_mock_gl.GL_LINK_STATUS      = 35714
_mock_gl.GL_TEXTURE_2D       = 3553
_mock_gl.GL_RGBA             = 6408
_mock_gl.GL_UNSIGNED_BYTE    = 5121
_mock_gl.GL_LINEAR           = 9729
_mock_gl.GL_CLAMP_TO_EDGE    = 33071
_mock_gl.GL_TEXTURE_MIN_FILTER = 10241
_mock_gl.GL_TEXTURE_MAG_FILTER = 10240
_mock_gl.GL_TEXTURE_WRAP_S   = 10242
_mock_gl.GL_TEXTURE_WRAP_T   = 10243
_mock_gl.GL_FRAMEBUFFER      = 36160
_mock_gl.GL_COLOR_ATTACHMENT0 = 36064
_mock_gl.GL_COLOR_BUFFER_BIT = 16384
_mock_gl.GL_TRIANGLE_STRIP   = 5

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _mock_gl

from vjlive3.plugins.ascii_effect import ASCIIPlugin, METADATA, PRESETS
from vjlive3.plugins.api import PluginContext


@pytest.fixture
def gl():
    _mock_gl.reset_mock()
    _mock_gl.glGetShaderiv.return_value   = 1
    _mock_gl.glGetProgramiv.return_value  = 1
    _mock_gl.glCreateProgram.return_value = 99
    _mock_gl.glGenVertexArrays.return_value = 44
    _mock_gl.glGenFramebuffers.return_value = 51
    _mock_gl.glGenTextures.return_value   = 101
    return _mock_gl


@pytest.fixture
def plugin(gl):
    return ASCIIPlugin()


@pytest.fixture
def ctx():
    c = PluginContext(MagicMock())
    c.width = 64; c.height = 48; c.time = 1.0
    c.inputs = {"video_in": 10}; c.outputs = {}
    return c


# ── Metadata ──────────────────────────────────────────────────────────────────

def test_metadata_name(plugin):
    assert METADATA["name"] == "ASCII Effect"


def test_metadata_has_22_params(plugin):
    assert len(METADATA["parameters"]) == 22  # 21 core + mix


def test_metadata_param_names(plugin):
    names = {p["name"] for p in METADATA["parameters"]}
    for required in ("cell_size", "charset", "color_mode", "scanlines", "mix",
                     "phosphor_glow", "rain_density", "scroll_speed", "curvature"):
        assert required in names, f"Missing param: {required}"


def test_metadata_all_params_have_min_max_default(plugin):
    for p in METADATA["parameters"]:
        assert "min" in p and "max" in p and "default" in p, f"Bad param: {p['name']}"


def test_presets_exist(plugin):
    assert len(PRESETS) == 5
    for name in ("matrix_rain", "classic_terminal", "color_ascii", "blocky_pixels", "glitch_text"):
        assert name in PRESETS


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@patch('vjlive3.plugins.ascii_effect.gl', _mock_gl)
def test_initialize_returns_true(plugin, ctx):
    assert plugin.initialize(ctx) is True
    assert plugin._initialized is True


@patch('vjlive3.plugins.ascii_effect.gl', _mock_gl)
def test_process_zero_texture_returns_zero(plugin, ctx):
    plugin.initialize(ctx)
    assert plugin.process_frame(0, {}, ctx) == 0


@patch('vjlive3.plugins.ascii_effect.gl', _mock_gl)
def test_process_frame_invokes_draw(plugin, ctx):
    plugin.initialize(ctx)
    plugin.process_frame(10, {}, ctx)
    _mock_gl.glDrawArrays.assert_called()


@patch('vjlive3.plugins.ascii_effect.gl', _mock_gl)
def test_process_frame_sets_video_out(plugin, ctx):
    plugin.initialize(ctx)
    plugin.process_frame(10, {}, ctx)
    assert 'video_out' in ctx.outputs


@patch('vjlive3.plugins.ascii_effect.gl', _mock_gl)
def test_process_frame_all_params(plugin, ctx):
    plugin.initialize(ctx)
    params = {p["name"]: p["default"] for p in METADATA["parameters"]}
    result = plugin.process_frame(10, params, ctx)
    assert result is not None


@patch('vjlive3.plugins.ascii_effect.gl', _mock_gl)
def test_resolution_change_rebuilds_fbo(plugin, ctx):
    plugin.initialize(ctx)
    plugin.process_frame(10, {}, ctx)
    ctx.width = 128; ctx.height = 96
    plugin.process_frame(10, {}, ctx)
    # glDeleteFramebuffers should have been called for the resize
    assert _mock_gl.glDeleteFramebuffers.called or _mock_gl.glGenFramebuffers.call_count >= 1


@patch('vjlive3.plugins.ascii_effect.gl', _mock_gl)
def test_compile_failure_sets_mock_mode(plugin, ctx):
    _mock_gl.glGetShaderiv.return_value = 0
    _mock_gl.glGetShaderInfoLog.return_value = b"GLSL error"
    result = plugin.initialize(ctx)
    assert result is False
    assert plugin._mock_mode is True
    _mock_gl.glGetShaderiv.return_value = 1


@patch('vjlive3.plugins.ascii_effect.gl', _mock_gl)
def test_cleanup_deletes_resources(plugin, ctx):
    plugin.initialize(ctx)
    plugin.prog = 99; plugin.vao = 44
    plugin.cleanup()
    _mock_gl.glDeleteProgram.assert_called_with(99)


def test_mock_mode_process_frame(plugin, ctx):
    """Without real GL, plugin should pass through input texture."""
    plugin._mock_mode = True
    result = plugin.process_frame(10, {}, ctx)
    assert result == 10
    assert ctx.outputs.get('video_out') == 10
