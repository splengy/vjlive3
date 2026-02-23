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
mock_gl.glCreateProgram.side_effect = [98, 99] # send_program, loop_program
mock_gl.glGetProgramiv.return_value = mock_gl.GL_TRUE
mock_gl.glGenFramebuffers.side_effect = [51, 52, 53] # fbo1, fbo2, send_fbo
mock_gl.glGenTextures.side_effect = [61, 62, 63]     # tex1, tex2, send_texture
mock_gl.glGenVertexArrays.return_value = 44

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_fx_loop import DepthFxLoopPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.side_effect = [98, 99]
    mock_gl.glGenFramebuffers.side_effect = [51, 52, 53]
    mock_gl.glGenTextures.side_effect = [61, 62, 63]
    return DepthFxLoopPlugin()

@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 1920
    ctx.height = 1080
    ctx.inputs = {
        "video_in": 777,
        "depth_in": 999,
        "video_b_in": 888  # FX Return
    }
    ctx.time = 42.0
    ctx.outputs = {}
    return ctx

def test_plugin_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "DepthFxLoop"
    assert "video_b_in" in meta["inputs"]
    assert "video_out_b" in meta["outputs"]
    assert "depth" in meta["tags"]
    p_names = [p["name"] for p in meta["parameters"]]
    assert "sendMode" in p_names
    assert "feedbackHueDrift" in p_names

@patch('vjlive3.plugins.depth_fx_loop.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.send_program == 98
    assert plugin.loop_program == 99

@patch('vjlive3.plugins.depth_fx_loop.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.depth_fx_loop.gl', mock_gl)
@patch('vjlive3.plugins.depth_fx_loop.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateShader': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777
    assert context.outputs["video_out_b"] == 777

@patch('vjlive3.plugins.depth_fx_loop.gl', mock_gl)
def test_process_frame_standard_execution_matrix(plugin, context):
    plugin.initialize(context)
    
    params = {
        "sendMode": 8.0,
        "wetDry": 2.0,
        "depthGateMin": 1.0,
        "depthGateMax": 9.0,
        "gateSoftness": 5.0,
        "feedbackAmount": 4.0,
        "feedbackDecay": 3.0,
        "feedbackHueDrift": 2.0,
        "sendBrightness": 7.0,
        "sendSaturation": 4.0,
        "returnBlendMode": 6.0,
        "returnOpacity": 8.0
    }
    
    # First frame (fbo2 writes, fbo1 reads)
    res = plugin.process_frame(777, params, context)
    
    # Outputs resolution
    assert res == 62 # tex2 returned on first frame
    assert plugin.fbo1 == 51
    assert plugin.send_fbo == 53
    assert context.outputs["video_out_b"] == 63 # send texture returned
    
    # Send Shader Program bindings
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(98, "tex0"), 0)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(98, "depth_tex"), 1)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(98, "send_brightness"), 0.7)
    
    # Loop Return Shader Program bindings
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "texPrev"), 2)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "fx_return_tex"), 3)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "feedback_amount"), 0.4)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "return_blend_mode"), 6.0)
    
    # Second frame swaps FBOS
    res2 = plugin.process_frame(777, params, context)
    assert res2 == 61

@patch('vjlive3.plugins.depth_fx_loop.gl', mock_gl)
def test_process_frame_no_return_fallback(plugin, context):
    # If no fx_return_tex is bound implicitly by inputs, standard loop folds onto input texture
    context.inputs.pop("video_b_in")
    plugin.initialize(context)
    
    res = plugin.process_frame(777, {}, context)
    
    # ensure fx_return_tex binds texture 777 fallback safely
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "fx_return_tex"), 3)
    # The active texture 3 must be bound to 777 internally
    mock_gl.glActiveTexture.assert_any_call(mock_gl.GL_TEXTURE3)
    mock_gl.glBindTexture.assert_any_call(mock_gl.GL_TEXTURE_2D, 777)

@patch('vjlive3.plugins.depth_fx_loop.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Mosh Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE

@patch('vjlive3.plugins.depth_fx_loop.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.fbo1 = 51
    plugin.tex1 = 61
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_any_call(98)
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [51])
    mock_gl.glDeleteTextures.assert_any_call(1, [61])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [44])
