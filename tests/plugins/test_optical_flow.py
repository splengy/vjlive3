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
mock_gl.GL_READ_FRAMEBUFFER = 36008
mock_gl.GL_DRAW_FRAMEBUFFER = 36009
mock_gl.GL_COLOR_ATTACHMENT0 = 36064
mock_gl.GL_COLOR_BUFFER_BIT = 16384
mock_gl.GL_NEAREST = 9728
mock_gl.GL_TRIANGLE_STRIP = 5
mock_gl.GL_FALSE = 0
mock_gl.GL_TRUE = 1

mock_gl.glCreateShader.return_value = 1
mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
mock_gl.glCreateProgram.return_value = 99
mock_gl.glGetProgramiv.return_value = mock_gl.GL_TRUE
mock_gl.glGenFramebuffers.side_effect = [55, 56, 57, 58, 59, 60]
mock_gl.glGenTextures.side_effect = [66, 67, 68, 69, 70, 71]
mock_gl.glGenVertexArrays.return_value = 44

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.optical_flow import OpticalFlowPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.return_value = 99
    # Reset side effects for predictable FBO IDs per test
    mock_gl.glGenFramebuffers.side_effect = [55, 56, 57, 58, 59, 60]
    mock_gl.glGenTextures.side_effect = [66, 67, 68, 69, 70, 71]
    return OpticalFlowPlugin()

@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 1920
    ctx.height = 1080
    ctx.inputs = {"video_in": 777}
    ctx.outputs = {}
    return ctx

def test_plugin_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "OpticalFlow"
    assert meta["plugin_type"] == "depth_effect"
    assert "flowScale" in [p["name"] for p in meta["parameters"]]

@patch('vjlive3.plugins.optical_flow.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.program == 99

@patch('vjlive3.plugins.optical_flow.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.optical_flow.gl', mock_gl)
@patch('vjlive3.plugins.optical_flow.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateProgram': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777

@patch('vjlive3.plugins.optical_flow.gl', mock_gl)
def test_process_frame_standard_execution(plugin, context):
    plugin.initialize(context)
    
    params = {
        "flowScale": 2.5,
        "flowThreshold": 0.2,
        "flowOpacity": 0.5,
        "flowColorMode": 1
    }
    
    res = plugin.process_frame(777, params, context)
    # Output texture is target_texture (the first generated is 66)
    assert res == 66 
    
    # Assert fbos were generated (target=55, prev=56, tmp_fbo mapping should be 57)
    assert plugin.target_fbo == 55
    assert plugin.prev_fbo == 56
    
    # Assert Program usage
    mock_gl.glUseProgram.assert_any_call(99)
    # Assert FBO is bound
    mock_gl.glBindFramebuffer.assert_any_call(mock_gl.GL_FRAMEBUFFER, 55)
    
    # Assert Uniforms are passed
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "flow_scale"), 2.5)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "flow_threshold"), 0.2)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "flow_opacity"), 0.5)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "flow_color_mode"), 1)
    mock_gl.glUniform2f.assert_any_call(mock_gl.glGetUniformLocation(99, "resolution"), 1920.0, 1080.0)
    
    # Assert GLBlit Framebuffer transfer
    mock_gl.glBlitFramebuffer.assert_any_call(0, 0, 1920, 1080, 0, 0, 1920, 1080, mock_gl.GL_COLOR_BUFFER_BIT, mock_gl.GL_NEAREST)

@patch('vjlive3.plugins.optical_flow.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE

@patch('vjlive3.plugins.optical_flow.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.target_fbo = 55
    plugin.target_texture = 66
    plugin.prev_fbo = 56
    plugin.prev_texture = 67
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [55])
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [56])
    mock_gl.glDeleteTextures.assert_any_call(1, [66])
    mock_gl.glDeleteTextures.assert_any_call(1, [67])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [44])
