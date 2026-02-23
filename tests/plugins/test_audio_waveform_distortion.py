"""
Tests for P4-AU03: Audio Waveform Distortion.
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
_mock_gl.GL_LINEAR           = 9729
_mock_gl.GL_CLAMP_TO_EDGE    = 33071
_mock_gl.GL_TEXTURE_MIN_FILTER = 10241
_mock_gl.GL_TEXTURE_MAG_FILTER = 10240
_mock_gl.GL_TEXTURE_WRAP_S   = 10242
_mock_gl.GL_TEXTURE_WRAP_T   = 10243
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

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _mock_gl

from vjlive3.plugins.audio_waveform_distortion import AudioWaveformDistortionPlugin, METADATA, _map
from vjlive3.plugins.api import PluginContext


@pytest.fixture
def plugin():
    _mock_gl.reset_mock()
    _mock_gl.glGetShaderiv.return_value  = 1
    _mock_gl.glGetProgramiv.return_value = 1
    _mock_gl.glCreateProgram.return_value = 99
    _mock_gl.glGenVertexArrays.return_value = 44
    _mock_gl.glGenTextures.return_value = 55
    return AudioWaveformDistortionPlugin()


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
    assert m["name"] == "Audio Waveform Distortion"
    assert "video_in" in m["inputs"]
    pnames = [p["name"] for p in m["parameters"]]
    assert "distortion_strength" in pnames
    assert "frequency_scale"     in pnames
    assert "color_shift"         in pnames
    assert len(pnames) == 4

def test_map_limits(plugin):
    assert _map(0.0,  0.0, 1.0) == pytest.approx(0.0)
    assert _map(10.0, 0.0, 1.0) == pytest.approx(1.0)

@patch('vjlive3.plugins.audio_waveform_distortion.gl', _mock_gl)
def test_initialize(plugin, context):
    assert plugin.initialize(context) is True
    assert plugin._initialized is True

@patch('vjlive3.plugins.audio_waveform_distortion.gl', _mock_gl)
def test_process_zero_input(plugin, context):
    plugin.initialize(context)
    assert plugin.process_frame(0, {}, context) == 0

@patch('vjlive3.plugins.audio_waveform_distortion.gl', _mock_gl)
@patch('vjlive3.plugins.audio_waveform_distortion.hasattr')
def test_mock_fallback(mock_hasattr, plugin, context):
    def chk(obj, attr): return False if attr == 'glCreateShader' else True
    mock_hasattr.side_effect = chk
    assert plugin.process_frame(10, {}, context) == 10

@patch('vjlive3.plugins.audio_waveform_distortion.gl', _mock_gl)
def test_process_with_waveform(plugin, context):
    plugin.initialize(context)
    context.inputs["audio_data"] = {
        "bass": 0.7, "volume": 0.9,
        "waveform": np.sin(np.linspace(0, 2 * np.pi, 1024)).astype(np.float32),
    }
    params = {"distortion_strength": 3.0, "frequency_scale": 5.0,
              "smoothing": 8.0, "color_shift": 2.0}
    res = plugin.process_frame(10, params, context)
    assert res == 10
    # Waveform should have been uploaded
    _mock_gl.glTexImage2D.assert_called()
    _mock_gl.glDrawArrays.assert_called_once()

@patch('vjlive3.plugins.audio_waveform_distortion.gl', _mock_gl)
def test_process_no_waveform(plugin, context):
    plugin.initialize(context)
    context.inputs["audio_data"] = {"bass": 0.5, "volume": 0.8}
    res = plugin.process_frame(10, {}, context)
    assert res == 10
    # waveform_size should be 0
    _mock_gl.glUniform1i.assert_any_call(
        _mock_gl.glGetUniformLocation(99, "waveform_size"), 0
    )

@patch('vjlive3.plugins.audio_waveform_distortion.gl', _mock_gl)
def test_compile_failure(plugin, context):
    _mock_gl.glGetShaderiv.return_value = 0
    _mock_gl.glGetShaderInfoLog.return_value = b"Error"
    assert plugin.initialize(context) is False
    assert plugin._mock_mode is True
    _mock_gl.glGetShaderiv.return_value = 1

@patch('vjlive3.plugins.audio_waveform_distortion.gl', _mock_gl)
def test_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.prog     = 99
    plugin.vao      = 44
    plugin.wave_tex = 55
    plugin.cleanup()
    _mock_gl.glDeleteProgram.assert_called_once_with(99)
    _mock_gl.glDeleteTextures.assert_called_once_with(1, [55])
