"""Tests for P5-DM24: MoshPitDatamoshPlugin."""
import pytest
from unittest.mock import MagicMock, patch
import sys

_mock_gl = MagicMock()
_mock_gl.GL_VERTEX_SHADER = 35633; _mock_gl.GL_FRAGMENT_SHADER = 35632
_mock_gl.GL_COMPILE_STATUS = 35713; _mock_gl.GL_LINK_STATUS = 35714
_mock_gl.GL_TEXTURE_2D = 3553; _mock_gl.GL_RGBA = 6408; _mock_gl.GL_UNSIGNED_BYTE = 5121
_mock_gl.GL_LINEAR = 9729; _mock_gl.GL_CLAMP_TO_EDGE = 33071
_mock_gl.GL_TEXTURE_MIN_FILTER = 10241; _mock_gl.GL_TEXTURE_MAG_FILTER = 10240
_mock_gl.GL_TEXTURE_WRAP_S = 10242; _mock_gl.GL_TEXTURE_WRAP_T = 10243
_mock_gl.GL_FRAMEBUFFER = 36160; _mock_gl.GL_COLOR_ATTACHMENT0 = 36064
_mock_gl.GL_COLOR_BUFFER_BIT = 16384; _mock_gl.GL_TRIANGLE_STRIP = 5
_mock_gl.GL_FALSE = 0; _mock_gl.GL_TRUE = 1
_mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
_mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44
_mock_gl.glGenTextures.return_value = 55; _mock_gl.glGenFramebuffers.return_value = 51

sys.modules['OpenGL'] = MagicMock(); sys.modules['OpenGL.GL'] = _mock_gl

from vjlive3.plugins.mosh_pit_datamosh import MoshPitDatamoshPlugin, METADATA


@pytest.fixture
def plugin():
    _mock_gl.reset_mock()
    _mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
    _mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44
    _mock_gl.glGenTextures.return_value = 55; _mock_gl.glGenFramebuffers.return_value = 51
    return MoshPitDatamoshPlugin()


@pytest.fixture
def context():
    ctx = MagicMock()(MagicMock())
    ctx.width = 64; ctx.height = 48; ctx.time = 1.0
    ctx.inputs = {"video_in": 10}; ctx.outputs = {}
    return ctx


def test_metadata(plugin):
    m = plugin.get_metadata()
    assert m["name"] == 'Mosh Pit Datamosh'
    assert "video_in" in m["inputs"]
    assert len(m["parameters"]) == 12

@patch('vjlive3.plugins.mosh_pit_datamosh.gl', _mock_gl)
def test_initialize(plugin, context):
    assert plugin.initialize(context) is True

@patch('vjlive3.plugins.mosh_pit_datamosh.gl', _mock_gl)
def test_process_zero_input(plugin, context):
    plugin.initialize(context); assert plugin.process_frame(0, {}, context) == 0

@patch('vjlive3.plugins.mosh_pit_datamosh.gl', _mock_gl)
@patch('vjlive3.plugins.mosh_pit_datamosh.hasattr')
def test_mock_fallback(mock_hasattr, plugin, context):
    mock_hasattr.side_effect = lambda o, a: False if a == 'glCreateShader' else True
    assert plugin.process_frame(10, {}, context) == 10

@patch('vjlive3.plugins.mosh_pit_datamosh.gl', _mock_gl)
def test_process_renders(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(10, {}, context)
    assert res == 55
    _mock_gl.glDrawArrays.assert_called_once()

@patch('vjlive3.plugins.mosh_pit_datamosh.gl', _mock_gl)
def test_compile_failure(plugin, context):
    _mock_gl.glGetShaderiv.return_value = 0; _mock_gl.glGetShaderInfoLog.return_value = b"Error"
    assert plugin.initialize(context) is False; assert plugin._mock_mode is True
    _mock_gl.glGetShaderiv.return_value = 1

@patch('vjlive3.plugins.mosh_pit_datamosh.gl', _mock_gl)
def test_cleanup(plugin, context):
    plugin.initialize(context); plugin.prog = 99; plugin.cleanup()
    _mock_gl.glDeleteProgram.assert_called_once_with(99)
