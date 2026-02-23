"""Tests for P7-VE53: BenDayDotsPlugin."""
import pytest
from unittest.mock import MagicMock, patch
import sys
_gl=MagicMock(); _gl.GL_VERTEX_SHADER=35633; _gl.GL_FRAGMENT_SHADER=35632
_gl.GL_COMPILE_STATUS=35713; _gl.GL_LINK_STATUS=35714; _gl.GL_TEXTURE_2D=3553
_gl.GL_RGBA=6408; _gl.GL_UNSIGNED_BYTE=5121; _gl.GL_LINEAR=9729; _gl.GL_CLAMP_TO_EDGE=33071
_gl.GL_TEXTURE_MIN_FILTER=10241; _gl.GL_TEXTURE_MAG_FILTER=10240
_gl.GL_TEXTURE_WRAP_S=10242; _gl.GL_TEXTURE_WRAP_T=10243
_gl.GL_FRAMEBUFFER=36160; _gl.GL_COLOR_ATTACHMENT0=36064
_gl.GL_COLOR_BUFFER_BIT=16384; _gl.GL_TRIANGLE_STRIP=5; _gl.GL_FALSE=0; _gl.GL_TRUE=1
_gl.glGetShaderiv.return_value=1; _gl.glGetProgramiv.return_value=1
_gl.glCreateProgram.return_value=99; _gl.glGenVertexArrays.return_value=44
_gl.glGenTextures.return_value=55; _gl.glGenFramebuffers.return_value=51
sys.modules['OpenGL']=MagicMock(); sys.modules['OpenGL.GL']=_gl
from vjlive3.plugins.ben_day_dots import BenDayDotsPlugin, METADATA
@pytest.fixture
def plugin():
    _gl.reset_mock(); _gl.glGetShaderiv.return_value=1; _gl.glGetProgramiv.return_value=1
    _gl.glCreateProgram.return_value=99; _gl.glGenVertexArrays.return_value=44
    _gl.glGenTextures.return_value=55; _gl.glGenFramebuffers.return_value=51
    return BenDayDotsPlugin()
@pytest.fixture
def context():
    ctx=MagicMock()(MagicMock()); ctx.width=64; ctx.height=48; ctx.time=1.0
    ctx.inputs={"video_in":10}; ctx.outputs={}; return ctx
def test_metadata(plugin):
    m=plugin.get_metadata(); assert m["name"]=='Ben Day Dots'; assert len(m["parameters"])==6
@patch('vjlive3.plugins.ben_day_dots.gl', _gl)
def test_initialize(plugin, context): assert plugin.initialize(context) is True
@patch('vjlive3.plugins.ben_day_dots.gl', _gl)
def test_zero_input(plugin, context): plugin.initialize(context); assert plugin.process_frame(0,{},context)==0
@patch('vjlive3.plugins.ben_day_dots.gl', _gl)
@patch('vjlive3.plugins.ben_day_dots.hasattr')
def test_mock_fallback(mh, plugin, context):
    mh.side_effect=lambda o,a: False if a=='glCreateShader' else True
    assert plugin.process_frame(10,{},context)==10
@patch('vjlive3.plugins.ben_day_dots.gl', _gl)
def test_renders(plugin, context):
    plugin.initialize(context); assert plugin.process_frame(10,{},context)==55
    _gl.glDrawArrays.assert_called_once()
@patch('vjlive3.plugins.ben_day_dots.gl', _gl)
def test_compile_fail(plugin, context):
    _gl.glGetShaderiv.return_value=0; _gl.glGetShaderInfoLog.return_value=b"E"
    assert plugin.initialize(context) is False; _gl.glGetShaderiv.return_value=1
@patch('vjlive3.plugins.ben_day_dots.gl', _gl)
def test_cleanup(plugin, context):
    plugin.initialize(context); plugin.prog=99; plugin.cleanup()
    _gl.glDeleteProgram.assert_called_once_with(99)
