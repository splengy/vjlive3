import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import sys

mock_gl = MagicMock()
mock_gl.GL_VERTEX_SHADER = 35633
mock_gl.GL_FRAGMENT_SHADER = 35632
mock_gl.GL_COMPILE_STATUS = 35713
mock_gl.GL_LINK_STATUS = 35714
mock_gl.GL_TEXTURE_2D = 3553
mock_gl.GL_TEXTURE0 = 33984
mock_gl.GL_TEXTURE1 = 33985
mock_gl.GL_RGBA = 6408
mock_gl.GL_UNSIGNED_BYTE = 5121
mock_gl.GL_LINEAR = 9729
mock_gl.GL_TEXTURE_MIN_FILTER = 10241
mock_gl.GL_TEXTURE_MAG_FILTER = 10240
mock_gl.GL_FRAMEBUFFER = 36160
mock_gl.GL_COLOR_ATTACHMENT0 = 36064
mock_gl.GL_COLOR_BUFFER_BIT = 16384
mock_gl.GL_TRIANGLE_STRIP = 5
mock_gl.GL_FALSE = 0
mock_gl.GL_TRUE = 1

mock_gl.glCreateShader.return_value = 1
mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
mock_gl.glCreateProgram.return_value = 99
mock_gl.glGetProgramiv.return_value = mock_gl.GL_TRUE
mock_gl.glGenFramebuffers.return_value = 55
mock_gl.glGenTextures.return_value = 66
mock_gl.glGenVertexArrays.return_value = 44

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_fog import DepthFogPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.return_value = 99
    mock_gl.glGenFramebuffers.return_value = 55
    mock_gl.glGenTextures.return_value = 66
    return DepthFogPlugin()

@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 1920
    ctx.height = 1080
    ctx.inputs = {
        "video_in": 777,
        "depth_in": 999
    }
    ctx.time = 42.0
    ctx.outputs = {}
    return ctx

def test_plugin_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "DepthFog"
    assert "depth" in meta["tags"]
    p_names = [p["name"] for p in meta["parameters"]]
    assert "fogDensity" in p_names
    assert "fogMode" in p_names

@patch('vjlive3.plugins.depth_fog.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.program == 99

@patch('vjlive3.plugins.depth_fog.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.depth_fog.gl', mock_gl)
@patch('vjlive3.plugins.depth_fog.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateShader': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777

@patch('vjlive3.plugins.depth_fog.gl', mock_gl)
def test_process_frame_standard_execution_matrix(plugin, context):
    plugin.initialize(context)
    
    params = {
        "fogDensity": 8.0,
        "fogStart": 2.0,
        "fogEnd": 9.0,
        "fogMode": 5.0,
        "fogColorR": 10.0,
        "fogColorG": 0.0,
        "fogColorB": 5.0,
        "fogHeight": 3.0,
        "fogAnimate": 7.0,
        "fogScatter": 4.0,
        "fogOpacity": 8.0
    }
    
    res = plugin.process_frame(777, params, context)
    assert res == 66 
    assert plugin.fbo == 55
    
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tex0"), 0)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "depth_tex"), 1)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "has_depth"), 1)
    
    # Validation logic tests mapped
    # map_norm(fogDensity=8.0) -> 0.8
    # map_norm(fogMode=5.0, 10.0) -> 5.0  (multiples max_v instead of max 1.0)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "fog_density"), 0.8)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "fog_mode"), 5.0)
    mock_gl.glUniform3f.assert_any_call(mock_gl.glGetUniformLocation(99, "fog_color"), 1.0, 0.0, 0.5)

@patch('vjlive3.plugins.depth_fog.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Mosh Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE

@patch('vjlive3.plugins.depth_fog.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.fbo = 55
    plugin.target_texture = 66
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [55])
    mock_gl.glDeleteTextures.assert_any_call(1, [66])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [44])
