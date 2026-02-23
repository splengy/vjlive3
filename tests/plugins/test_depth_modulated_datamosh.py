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

from vjlive3.plugins.depth_modulated_datamosh import DepthModulatedDatamoshPlugin, METADATA

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.return_value = 99
    global _fbo_counter, _tex_counter
    _fbo_counter = 50
    _tex_counter = 60
    return DepthModulatedDatamoshPlugin()

@pytest.fixture
def context():
    ctx = MagicMock()(MagicMock())
    ctx.width = 1920
    ctx.height = 1080
    ctx.inputs = {
        "video_in": 777,
        "depth_in": 999,
        "video_b_in": 888 
    }
    ctx.time = 42.0
    ctx.outputs = {}
    return ctx

def test_plugin_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "DepthModulatedDatamosh"
    assert "video_in" in meta["inputs"]
    assert "video_b_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_out" in meta["outputs"]
    
    p_names = [p["name"] for p in meta["parameters"]]
    assert "depthCurve" in p_names
    assert "modStrength" in p_names
    assert len(p_names) == 11

@patch('vjlive3.plugins.depth_modulated_datamosh.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.prog == 99

@patch('vjlive3.plugins.depth_modulated_datamosh.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.depth_modulated_datamosh.gl', mock_gl)
@patch('vjlive3.plugins.depth_modulated_datamosh.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateShader': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777

@patch('vjlive3.plugins.depth_modulated_datamosh.gl', mock_gl)
def test_process_frame_standard_execution_matrix(plugin, context):
    plugin.initialize(context)
    
    params = {
        "depthCurve": 5.0,
        "modStrength": 5.0, 
        "minMosh": 0.0,
        "maxMosh": 10.0,
        "invertDepth": 0.0,
        "intensity": 5.0,
        "threshold": 1.0, 
        "blend": 8.0,
        "blockSize": 5.0,
        "speed": 5.0,
        "feedback": 0.0,
    }
    
    res = plugin.process_frame(777, params, context)
    
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tex0"), 0)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tex1"), 1)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "texPrev"), 2)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "depth_tex"), 3)
    
    # Validation against correctly scaled math offsets based on config specs:
    # 5.0 / 10 * 2.0 = 1.0 (modStrength)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "modulation_strength"), 1.0)
    
    # 1.0 / 10 * 0.5 = 0.05 (threshold)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "threshold"), 0.05)
    
    # 5.0 / 10 * 30.0 + 2.0 = 17.0 (blockSize)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "blockSize"), 17.0)

@patch('vjlive3.plugins.depth_modulated_datamosh.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE

@patch('vjlive3.plugins.depth_modulated_datamosh.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.fbo_return = 51
    plugin.tex_return = 61
    plugin.fbo_prev = 52
    plugin.tex_prev = 62
    
    plugin.prog = 99
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteFramebuffers.assert_any_call(2, [51, 52])
    mock_gl.glDeleteTextures.assert_any_call(2, [61, 62])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [44])
