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
mock_gl.glCreateProgram.side_effect = [99, 100]
mock_gl.glGetProgramiv.return_value = mock_gl.GL_TRUE
mock_gl.glGenFramebuffers.side_effect = [55, 56, 57, 58, 59, 60]
mock_gl.glGenTextures.side_effect = [66, 67, 68, 69, 70, 71]
mock_gl.glGenVertexArrays.return_value = 44

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.background_subtraction import BackgroundSubtractionPlugin, METADATA

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.side_effect = [99, 100]
    # Reset side effects
    mock_gl.glGenFramebuffers.side_effect = [55, 56, 57, 58, 59, 60]
    mock_gl.glGenTextures.side_effect = [66, 67, 68, 69, 70, 71]
    return BackgroundSubtractionPlugin()

@pytest.fixture
def context():
    ctx = MagicMock()(MagicMock())
    ctx.width = 1920
    ctx.height = 1080
    ctx.inputs = {"video_in": 777}
    ctx.outputs = {}
    return ctx

def test_plugin_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "BackgroundSubtraction"
    assert meta["plugin_type"] == "depth_effect"
    assert "varThreshold" in [p["name"] for p in meta["parameters"]]

@patch('vjlive3.plugins.background_subtraction.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.update_program == 99
    assert plugin.render_program == 100

@patch('vjlive3.plugins.background_subtraction.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.background_subtraction.gl', mock_gl)
@patch('vjlive3.plugins.background_subtraction.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateProgram': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777

@patch('vjlive3.plugins.background_subtraction.gl', mock_gl)
def test_process_frame_standard_execution(plugin, context):
    plugin.initialize(context)
    
    params = {
        "history": 500,
        "varThreshold": 25.0,
        "detectShadows": 1.0,
        "silhouetteColor_0": 0.5,
        "silhouetteColor_1": 0.6,
        "silhouetteColor_2": 0.7,
        "silhouetteColor_3": 1.0,
        "backgroundColor_0": 0.1,
        "backgroundColor_1": 0.2,
        "backgroundColor_2": 0.3,
        "backgroundColor_3": 1.0
    }
    
    res = plugin.process_frame(777, params, context)
    
    # Target texture is output
    assert res == 66 
    
    # Check allocated ping pongs
    assert plugin.target_fbo == 55
    assert plugin.bg_fbos[0] == 56
    assert plugin.bg_fbos[1] == 57
    
    # Check current idx switched T+1
    assert plugin.current_bg_idx == 1
    
    # Assert Program usages
    mock_gl.glUseProgram.assert_any_call(99)
    mock_gl.glUseProgram.assert_any_call(100)
    
    # Eval constraints mappings
    lr = 1.0 / 500.0
    threshold = (25.0 / 100.0) * 0.5
    
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "learning_rate"), lr)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(100, "threshold"), threshold)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(100, "detect_shadows"), 1.0)
    mock_gl.glUniform4f.assert_any_call(mock_gl.glGetUniformLocation(100, "silhouette_color"), 0.5, 0.6, 0.7, 1.0)
    mock_gl.glUniform4f.assert_any_call(mock_gl.glGetUniformLocation(100, "background_color"), 0.1, 0.2, 0.3, 1.0)

@patch('vjlive3.plugins.background_subtraction.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE

@patch('vjlive3.plugins.background_subtraction.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.target_fbo = 55
    plugin.target_texture = 66
    plugin.bg_fbos = [56, 57]
    plugin.bg_textures = [67, 68]
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteProgram.assert_any_call(100)
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [55])
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [56])
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [57])
    mock_gl.glDeleteTextures.assert_any_call(1, [66])
    mock_gl.glDeleteTextures.assert_any_call(1, [67])
    mock_gl.glDeleteTextures.assert_any_call(1, [68])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [44])
