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
mock_gl.GL_TEXTURE2 = 33986
mock_gl.GL_TEXTURE3 = 33987
mock_gl.GL_TEXTURE4 = 33988
mock_gl.GL_TEXTURE5 = 33989
mock_gl.GL_TEXTURE6 = 33990
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
mock_gl.glGenFramebuffers.side_effect = [55, 56]
mock_gl.glGenTextures.side_effect = [66, 67]
mock_gl.glGenVertexArrays.return_value = 44

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_feedback_matrix_datamosh import DepthFeedbackMatrixDatamoshPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.return_value = 99
    # Reset side effects
    mock_gl.glGenFramebuffers.side_effect = [55, 56]
    mock_gl.glGenTextures.side_effect = [66, 67]
    return DepthFeedbackMatrixDatamoshPlugin()

@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 1920
    ctx.height = 1080
    ctx.inputs = {
        "video_in": 777,
        "video_b_in": 888,
        "depth_in": 999
    }
    ctx.outputs = {}
    return ctx

def test_plugin_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "DepthFeedbackMatrixDatamosh"
    assert "depth" in meta["tags"]
    p_names = [p["name"] for p in meta["parameters"]]
    assert "tap1Delay" in p_names
    assert "tap4ToTap1" in p_names

@patch('vjlive3.plugins.depth_feedback_matrix_datamosh.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.program == 99

@patch('vjlive3.plugins.depth_feedback_matrix_datamosh.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.depth_feedback_matrix_datamosh.gl', mock_gl)
@patch('vjlive3.plugins.depth_feedback_matrix_datamosh.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateShader': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777

@patch('vjlive3.plugins.depth_feedback_matrix_datamosh.gl', mock_gl)
def test_process_frame_standard_execution_matrix(plugin, context):
    plugin.initialize(context)
    
    params = {
        "moshIntensity": 8.0,
        "blockSize": 6.0,
        "tap1Delay": 2.0,
        "tap1DepthMin": 1.0,
        "tap1DepthMax": 9.0,
        "tap1Feedback": 5.0,
        "tap1EnableLoop": 10.0,
        "tap1ToTap2": 4.0
    }
    
    # First frame (ping)
    res1 = plugin.process_frame(777, params, context)
    assert res1 == 66 # fbo tex1
    assert plugin.fbo1 == 55
    assert plugin.fbo2 == 56
    
    # Second frame (pong)
    res2 = plugin.process_frame(777, params, context)
    assert res2 == 67 # fbo tex2
    
    # Check texture uniform assignments
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tex0"), 0)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tex1"), 1)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "texPrev"), 2)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "depth_tex"), 3)
    
    # Check feedback loop internal remaps to tu=2 (`texPrev`)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tap1_return"), 2)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tap4_return"), 2)
    
    # Check Math Mapping tests (0-10 mapped to 0.0-1.0)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "tap1_delay"), 0.2)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "mosh_intensity"), 0.8)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tap1_enable_loop"), 1)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "has_depth"), 1)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "has_video_b"), 1)

@patch('vjlive3.plugins.depth_feedback_matrix_datamosh.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Mosh Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE

@patch('vjlive3.plugins.depth_feedback_matrix_datamosh.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.fbo1 = 55
    plugin.fbo2 = 56
    plugin.tex1 = 66
    plugin.tex2 = 67
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [55])
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [56])
    mock_gl.glDeleteTextures.assert_any_call(1, [66])
    mock_gl.glDeleteTextures.assert_any_call(1, [67])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [44])
