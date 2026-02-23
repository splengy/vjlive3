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
mock_gl.glGenFramebuffers.return_value = 51
mock_gl.glGenTextures.return_value = 61
mock_gl.glGenVertexArrays.return_value = 44

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_holographic import DepthHolographicPlugin, METADATA

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.return_value = 99
    mock_gl.glGenFramebuffers.return_value = 51
    mock_gl.glGenTextures.return_value = 61
    return DepthHolographicPlugin()

@pytest.fixture
def context():
    ctx = MagicMock()(MagicMock())
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
    assert meta["name"] == "DepthHolographic"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    p_names = [p["name"] for p in meta["parameters"]]
    assert "iridescenceAmount" in p_names
    assert "filmThickness" in p_names
    assert len(p_names) == 15

@patch('vjlive3.plugins.depth_holographic.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.program == 99

@patch('vjlive3.plugins.depth_holographic.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.depth_holographic.gl', mock_gl)
@patch('vjlive3.plugins.depth_holographic.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateShader': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777

@patch('vjlive3.plugins.depth_holographic.gl', mock_gl)
def test_process_frame_standard_execution_matrix(plugin, context):
    plugin.initialize(context)
    
    params = {
        "filmThickness": 5.0,
        "filmDepthScale": 8.0,
        "interferenceOrder": 2.0,
        "fresnelPower": 5.0,  
        "fresnelBias": 2.0,
        "spectralSpread": 5.0, 
        "spectralShift": 4.0,
        "gratingDensity": 6.0,
        "gratingAngle": 7.0,
        "gratingOrder": 3.0,
        "iridescenceAmount": 9.0,
        "pearlescence": 8.0,
        "hologramNoise": 2.0,
        "colorMode": 5.0,
        "shimmerSpeed": 3.0
    }
    
    res = plugin.process_frame(777, params, context)
    
    # Validation against the Single-Pass state limits
    assert res == 61
    assert plugin.fbo == 51
    assert plugin.texture == 61
    
    # Validates input assignments 
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tex0"), 0)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "depth_tex"), 1)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "has_depth"), 1)
    
    # Validate Coefficient outputs map bounds correctly
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "film_thickness"), 0.5)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "film_depth_scale"), 0.8)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "interference_order"), 0.2)
    
    # 5.0 normalized 1.0->8.0 
    # ((5.0 / 10) * 7.0) + 1.0 = 4.5
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "fresnel_power"), 4.5)
    
    # 5.0 normalized 0.0->10.0
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "color_mode"), 5.0)

@patch('vjlive3.plugins.depth_holographic.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE

@patch('vjlive3.plugins.depth_holographic.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.fbo = 51
    plugin.texture = 61
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [51])
    mock_gl.glDeleteTextures.assert_any_call(1, [61])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [44])
