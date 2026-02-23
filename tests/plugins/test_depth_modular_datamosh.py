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
mock_gl.glCreateProgram.return_value = 99
mock_gl.glGetProgramiv.return_value = mock_gl.GL_TRUE

_fbo_counter = 50
_tex_counter = 60

def _mock_gen_fbo(n):
    global _fbo_counter
    _fbo_counter += 1
    return _fbo_counter

def _mock_gen_tex(n):
    global _tex_counter
    _tex_counter += 1
    return _tex_counter

mock_gl.glGenFramebuffers.side_effect = _mock_gen_fbo
mock_gl.glGenTextures.side_effect = _mock_gen_tex
mock_gl.glGenVertexArrays.return_value = 44

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_modular_datamosh import DepthModularDatamoshPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.return_value = 99
    global _fbo_counter, _tex_counter
    _fbo_counter = 50
    _tex_counter = 60
    return DepthModularDatamoshPlugin()

@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 1920
    ctx.height = 1080
    ctx.inputs = {
        "video_in": 777,
        "depth_in": 999,
        "video_b_in": 888  # External Return channel injection
    }
    ctx.time = 42.0
    ctx.outputs = {}
    return ctx

def test_plugin_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "DepthModularDatamosh"
    assert "video_in" in meta["inputs"]
    assert "video_b_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    assert "video_out_b" in meta["outputs"]
    
    p_names = [p["name"] for p in meta["parameters"]]
    assert "mvIntensity" in p_names
    assert "depthComposite" in p_names
    assert len(p_names) == 14

@patch('vjlive3.plugins.depth_modular_datamosh.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.prog_stage1 == 99
    assert plugin.prog_stage2 == 99

@patch('vjlive3.plugins.depth_modular_datamosh.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.depth_modular_datamosh.gl', mock_gl)
@patch('vjlive3.plugins.depth_modular_datamosh.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateShader': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777

@patch('vjlive3.plugins.depth_modular_datamosh.gl', mock_gl)
def test_process_frame_standard_execution_matrix(plugin, context):
    plugin.initialize(context)
    
    params = {
        "mvIntensity": 4.0, "blockSize": 5.0, "depthEdgeThresh": 5.0,
        "chromaSplit": 2.0, "preWarp": 1.0, "preGlitch": 1.0,
        "corruption": 3.0, "feedback": 3.0, "feedbackDecay": 2.0,
        "colorCorrupt": 1.0, "quantize": 1.0, "scanCorrupt": 1.0,
        "loopWetDry": 5.0, "depthComposite": 4.0,
    }
    
    res = plugin.process_frame(777, params, context)
    
    # Validates input assignments 
    # Stage 1 limits (Send)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tex0"), 0)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "depth_tex"), 1)
    
    # Stage 2 limits (Return/Main)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "texPrev"), 1)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "loop_return"), 3)
    
    # 1.0 normalized over 10 bounds
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "pre_glitch"), 0.1)
    
    # 5.0 normalized over 10 bounds
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "loop_wetdry"), 0.5)

@patch('vjlive3.plugins.depth_modular_datamosh.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE

@patch('vjlive3.plugins.depth_modular_datamosh.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.fbo_send = 51
    plugin.tex_send = 61
    plugin.fbo_return = 52
    plugin.tex_return = 62
    plugin.fbo_prev = 53
    plugin.tex_prev = 63
    
    plugin.prog_stage1 = 99
    plugin.prog_stage2 = 98
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteProgram.assert_any_call(98)
    mock_gl.glDeleteFramebuffers.assert_any_call(3, [51, 52, 53])
    mock_gl.glDeleteTextures.assert_any_call(3, [61, 62, 63])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [44])
