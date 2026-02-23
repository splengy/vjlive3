"""
Tests for P4-AU04: Audio Spectrum Trails.
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import sys

_mock_gl = MagicMock()
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
_mock_gl.GL_COLOR_BUFFER_BIT  = 16384
_mock_gl.GL_TRIANGLE_STRIP   = 5
_mock_gl.GL_R32F              = 33326
_mock_gl.GL_RED               = 6403
_mock_gl.GL_FLOAT             = 5126
_mock_gl.GL_FALSE = 0
_mock_gl.GL_TRUE  = 1

_mock_gl.glGetShaderiv.return_value  = 1
_mock_gl.glGetProgramiv.return_value = 1
_mock_gl.glCreateProgram.return_value = 99
_mock_gl.glGenVertexArrays.return_value = 44
_mock_gl.glGenTextures.return_value = 55
_mock_gl.glGenFramebuffers.return_value = 51
_mock_gl.glCheckFramebufferStatus.return_value = 36053

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _mock_gl

from vjlive3.plugins.audio_spectrum_trails import AudioSpectrumTrailsPlugin, METADATA, _map
from vjlive3.plugins.api import PluginContext


@pytest.fixture
def plugin():
    _mock_gl.reset_mock()
    _mock_gl.glGetShaderiv.return_value  = 1
    _mock_gl.glGetProgramiv.return_value = 1
    _mock_gl.glCreateProgram.return_value = 99
    _mock_gl.glGenVertexArrays.return_value = 44
    _mock_gl.glGenTextures.return_value = 55
    _mock_gl.glGenFramebuffers.return_value = 51
    _mock_gl.glCheckFramebufferStatus.return_value = 36053
    return AudioSpectrumTrailsPlugin()


@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width  = 64
    ctx.height = 48
    ctx.time   = 1.0
    ctx.inputs = {"video_in": 10}
    ctx.outputs = {}
    return ctx


def test_metadata(plugin):
    m = plugin.get_metadata()
    assert m["name"] == "Audio Spectrum Trails"
    assert "video_in" in m["inputs"]
    pnames = [p["name"] for p in m["parameters"]]
    assert "trail_decay"     in pnames
    assert "spectrum_height" in pnames
    assert "frequency_bands" in pnames
    assert "color_mode"      in pnames
    assert "trail_opacity"   in pnames
    assert len(pnames) == 5

def test_map_limits(plugin):
    assert _map(0.0,  0.0, 1.0) == pytest.approx(0.0)
    assert _map(10.0, 0.0, 1.0) == pytest.approx(1.0)

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _mock_gl)
def test_initialize(plugin, context):
    assert plugin.initialize(context) is True
    assert plugin._initialized is True

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _mock_gl)
def test_process_zero_input(plugin, context):
    plugin.initialize(context)
    assert plugin.process_frame(0, {}, context) == 0

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _mock_gl)
@patch('vjlive3.plugins.audio_spectrum_trails.hasattr')
def test_mock_fallback(mock_hasattr, plugin, context):
    def chk(obj, attr): return False if attr == 'glCreateShader' else True
    mock_hasattr.side_effect = chk
    assert plugin.process_frame(10, {}, context) == 10

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _mock_gl)
def test_process_with_spectrum(plugin, context):
    plugin.initialize(context)
    context.inputs["audio_data"] = {
        "bass": 0.7, "volume": 0.9,
        "spectrum": np.abs(np.fft.rfft(np.random.randn(512))).astype(np.float32),
    }
    params = {"trail_decay": 7.5, "spectrum_height": 5.0,
              "frequency_bands": 5.0, "color_mode": 0.0, "trail_opacity": 8.0}
    res = plugin.process_frame(10, params, context)
    # Returns trail_tex (55)
    assert res == 55
    _mock_gl.glDrawArrays.assert_called_once()
    _mock_gl.glTexImage2D.assert_called()

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _mock_gl)
def test_process_no_spectrum(plugin, context):
    plugin.initialize(context)
    context.inputs["audio_data"] = {"bass": 0.5, "volume": 0.8}
    res = plugin.process_frame(10, {}, context)
    assert res == 55

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _mock_gl)
def test_compile_failure(plugin, context):
    _mock_gl.glGetShaderiv.return_value = 0
    _mock_gl.glGetShaderInfoLog.return_value = b"Error"
    assert plugin.initialize(context) is False
    assert plugin._mock_mode is True
    _mock_gl.glGetShaderiv.return_value = 1

@patch('vjlive3.plugins.audio_spectrum_trails.gl', _mock_gl)
def test_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.prog      = 99
    plugin.vao       = 44
    plugin.spec_tex  = 55
    plugin.trail_tex = 66
    plugin.trail_fbo = 51
    plugin.cleanup()
    _mock_gl.glDeleteProgram.assert_called_once_with(99)
