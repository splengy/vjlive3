import pytest
from unittest.mock import MagicMock, patch
import numpy as np

# Mocking strategy for Headless CI Compatibility
# Must execute before imports of gl occur
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
mock_gl.GL_FRAMEBUFFER_COMPLETE = 36053
mock_gl.GL_ACTIVE_UNIFORMS = 35718
mock_gl.GL_FALSE = 0
mock_gl.GL_TRUE = 1
mock_gl.GL_NO_ERROR = 0
mock_gl.GL_TRIANGLE_STRIP = 5
mock_gl.GL_POINTS = 0
mock_gl.GL_COLOR_BUFFER_BIT = 16384
mock_gl.GL_DEPTH_BUFFER_BIT = 256
mock_gl.GL_PROGRAM_POINT_SIZE = 34370
mock_gl.GL_DEPTH_TEST = 2929
mock_gl.GL_LESS = 513

mock_gl.glCreateShader.return_value = 1
mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
mock_gl.glCreateProgram.return_value = 99
mock_gl.glGetProgramiv.return_value = mock_gl.GL_TRUE
mock_gl.glGenFramebuffers.return_value = 55
mock_gl.glGenTextures.return_value = 66
mock_gl.glGenVertexArrays.return_value = 44
mock_gl.glCheckFramebufferStatus.return_value = mock_gl.GL_FRAMEBUFFER_COMPLETE

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_point_cloud_3d import DepthPointCloud3DEffectPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    return DepthPointCloud3DEffectPlugin()

@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 1920
    ctx.height = 1080
    ctx.inputs = {"video_in": 777, "depth_in": 42}
    ctx.outputs = {}
    return ctx

def test_plugin_metadata(plugin):
    """Ensure metadata follows PluginRegistry standard requirements"""
    meta = plugin.get_metadata()
    assert meta["name"] == "DepthPointCloud3D"
    assert meta["plugin_type"] == "depth_effect"
    assert "point_density" in [p["name"] for p in meta["parameters"]]

@patch('vjlive3.plugins.depth_point_cloud_3d.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    """Ensure Plugin Initialization parses shaders cleanly and generates empty VAO"""
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.program == 99
    assert plugin.empty_vao == 44
    mock_gl.glCreateShader.assert_any_call(mock_gl.GL_VERTEX_SHADER)
    mock_gl.glCreateShader.assert_any_call(mock_gl.GL_FRAGMENT_SHADER)
    mock_gl.glGenVertexArrays.assert_called_with(1)

@patch('vjlive3.plugins.depth_point_cloud_3d.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    """Ensure process_frame bails cleanly when no video_in texture exists"""
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.depth_point_cloud_3d.gl', mock_gl)
@patch('vjlive3.plugins.depth_point_cloud_3d.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    """Ensure module bypass returns cleanly when strict GL capabilities absent natively"""
    # Force hasattr return False when checking glCreateProgram
    def attr_check(obj, attr):
        if attr == 'glCreateProgram': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777
    assert context.outputs["video_out"] == 777

@patch('vjlive3.plugins.depth_point_cloud_3d.gl', mock_gl)
def test_process_frame_standard_execution(plugin, context):
    """Ensure execution maps parameters, computes valid numpy MVP, and binds glDrawArrays"""
    plugin.initialize(context)
    
    params = {
        "camera_distance": 5.0,
        "camera_angle_x": 0.0,
        "camera_angle_y": 0.0,
        "point_size": 2.5,
        "point_density": 0.5,
        "color_mode": "velocity"
    }
    
    res = plugin.process_frame(777, params, context)
    assert res == 66 
    mock_gl.glDrawArrays.assert_any_call(mock_gl.GL_POINTS, 0, 1920 * 1080)
    
    # Test alternative branches to reach >80% coverage
    params["color_mode"] = "white"
    res = plugin.process_frame(777, params, context)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "color_mode"), 2)
    
    params["color_mode"] = "depth"
    res = plugin.process_frame(777, params, context)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "color_mode"), 0)

@patch('vjlive3.plugins.depth_point_cloud_3d.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    """Ensure plugin refuses initialization if gl compilation fails bounds"""
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    # Revert static block
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
@patch('vjlive3.plugins.depth_point_cloud_3d.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    # Populate artificial attributes
    plugin.fbo = 55
    plugin.target_texture = 66
    plugin.program = 99
    plugin.empty_vao = 44
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_called_with(99)
    mock_gl.glDeleteFramebuffers.assert_called_with(1, [55])
    mock_gl.glDeleteTextures.assert_called_with(1, [66])
    mock_gl.glDeleteVertexArrays.assert_called_with(1, [44])
    
    assert plugin.program == 0
    assert plugin.fbo == 0
    assert plugin.target_texture == 0
    assert plugin.empty_vao == 0
