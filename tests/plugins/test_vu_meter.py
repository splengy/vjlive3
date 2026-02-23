"""Tests for P7-VE82: VUMeterPlugin."""
import pytest
from unittest.mock import MagicMock, patch
import sys

_g = MagicMock()
_g.GL_VERTEX_SHADER=35633;_g.GL_FRAGMENT_SHADER=35632;_g.GL_COMPILE_STATUS=35713;_g.GL_LINK_STATUS=35714
_g.GL_TEXTURE_2D=3553;_g.GL_RGBA=6408;_g.GL_UNSIGNED_BYTE=5121;_g.GL_LINEAR=9729;_g.GL_CLAMP_TO_EDGE=33071
_g.GL_TEXTURE_MIN_FILTER=10241;_g.GL_TEXTURE_MAG_FILTER=10240;_g.GL_TEXTURE_WRAP_S=10242;_g.GL_TEXTURE_WRAP_T=10243
_g.GL_FRAMEBUFFER=36160;_g.GL_COLOR_ATTACHMENT0=36064;_g.GL_COLOR_BUFFER_BIT=16384;_g.GL_TRIANGLE_STRIP=5
_g.glGetShaderiv.return_value=1;_g.glGetProgramiv.return_value=1
_g.glCreateProgram.return_value=99;_g.glGenVertexArrays.return_value=44
_g.glGenTextures.return_value=55;_g.glGenFramebuffers.return_value=51
sys.modules['OpenGL']=MagicMock();sys.modules['OpenGL.GL']=_g

from vjlive3.plugins.vu_meter import VUMeterPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    _g.reset_mock();_g.glGetShaderiv.return_value=1;_g.glGetProgramiv.return_value=1
    _g.glCreateProgram.return_value=99;_g.glGenVertexArrays.return_value=44
    _g.glGenTextures.return_value=55;_g.glGenFramebuffers.return_value=51
    return VUMeterPlugin()

@pytest.fixture
def context():
    ctx=PluginContext(MagicMock());ctx.width=64;ctx.height=48;ctx.time=1.
    ctx.inputs={"video_in":10};ctx.outputs={};return ctx

def test_metadata(plugin): m=plugin.get_metadata();assert m["name"]=="Vu Meter";assert len(m["parameters"])==6
@patch('vjlive3.plugins.vu_meter.gl',_g)
def test_initialize(plugin,context): assert plugin.initialize(context) is True
@patch('vjlive3.plugins.vu_meter.gl',_g)
def test_zero(plugin,context): plugin.initialize(context);assert plugin.process_frame(0,{},context)==0
@patch('vjlive3.plugins.vu_meter.gl',_g)
@patch('vjlive3.plugins.vu_meter.hasattr')
def test_fallback(mh,plugin,context):
    mh.side_effect=lambda o,a:False if a=='glCreateShader' else True
    assert plugin.process_frame(10,{},context)==10
@patch('vjlive3.plugins.vu_meter.gl',_g)
def test_renders(plugin,context):
    plugin.initialize(context);assert plugin.process_frame(10,{},context)==55
    _g.glDrawArrays.assert_called_once()
@patch('vjlive3.plugins.vu_meter.gl',_g)
def test_compile_fail(plugin,context):
    _g.glGetShaderiv.return_value=0;_g.glGetShaderInfoLog.return_value=b"E"
    assert plugin.initialize(context) is False;_g.glGetShaderiv.return_value=1
@patch('vjlive3.plugins.vu_meter.gl',_g)
def test_cleanup(plugin,context):
    plugin.initialize(context);plugin.prog=99;plugin.cleanup()
    _g.glDeleteProgram.assert_called_once_with(99)
