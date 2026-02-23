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
mock_gl.glGenFramebuffers.side_effect = [51, 52]
mock_gl.glGenTextures.side_effect = [61, 62]
mock_gl.glGenVertexArrays.return_value = 44

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_groovy_datamosh import DepthGroovyDatamoshPlugin, METADATA

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.return_value = 99
    mock_gl.glGenFramebuffers.side_effect = [51, 52]
    mock_gl.glGenTextures.side_effect = [61, 62]
    return DepthGroovyDatamoshPlugin()

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
    assert meta["name"] == "DepthGroovyDatamosh"
    assert "video_in" in meta["inputs"]
    assert "depth_in" in meta["inputs"]
    assert "video_b_in" not in meta["inputs"] # Validating the dead-code cull
    p_names = [p["name"] for p in meta["parameters"]]
    assert "rainbowIntensity" in p_names
    assert "moshAmount" in p_names
    assert len(p_names) == 16

@patch('vjlive3.plugins.depth_groovy_datamosh.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.program == 99

@patch('vjlive3.plugins.depth_groovy_datamosh.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.depth_groovy_datamosh.gl', mock_gl)
@patch('vjlive3.plugins.depth_groovy_datamosh.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateShader': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777

@patch('vjlive3.plugins.depth_groovy_datamosh.gl', mock_gl)
def test_process_frame_standard_execution_matrix(plugin, context):
    plugin.initialize(context)
    
    # Passing 16 parametric bounds mappings tracking 0.0->10.0 generic translation limits
    params = {
        "rainbowIntensity": 8.0,
        "rainbowSpeed": 2.0,
        "kaleidoscope": 4.0,
        "spiralFeedback": 6.0,
        "spiralSpeed": 5.0,
        "breathing": 3.0,
        "breathingSpeed": 7.0,
        "depthZoom": 2.0,
        "pixelSort": 4.0,
        "melt": 1.0,
        "moshAmount": 9.0,
        "blockChaos": 8.0,
        "colorBleed": 5.0,
        "saturationBoost": 7.0,
        "glowTrails": 2.0,
        "strobeFlash": 6.0
    }
    
    # First frame (fbo2 writes, fbo1 reads)
    res = plugin.process_frame(777, params, context)
    
    # Validates memory logic state progression
    assert res == 62
    assert plugin.fbo1 == 51
    assert plugin.fbo2 == 52
    
    # Texture Sampler Index Allocations (Checking mapping without dead tex1 logic)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tex0"), 0)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "texPrev"), 1)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "depth_tex"), 2)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "has_depth"), 1)
    
    # Verify coefficient mappings scaled (val / 10.0)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "rainbow_intensity"), 0.8)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "spiral_feedback"), 0.6)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "mosh_amount"), 0.9)

    # Second frame swaps FBO writes simulating Ping-Pong temporal loops
    res2 = plugin.process_frame(777, params, context)
    assert res2 == 61

@patch('vjlive3.plugins.depth_groovy_datamosh.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Mosh Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE

@patch('vjlive3.plugins.depth_groovy_datamosh.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.fbo1 = 51
    plugin.tex1 = 61
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [51])
    mock_gl.glDeleteTextures.assert_any_call(1, [61])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [44])
