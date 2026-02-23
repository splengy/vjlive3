import pytest
from unittest.mock import MagicMock, patch
import numpy as np

import sys
mock_gl = MagicMock()
mock_gl.GL_VERTEX_SHADER = 35633
mock_gl.GL_GEOMETRY_SHADER = 36313
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
mock_gl.GL_FALSE = 0
mock_gl.GL_TRUE = 1
mock_gl.GL_NO_ERROR = 0
mock_gl.GL_TRIANGLES = 4
mock_gl.GL_COLOR_BUFFER_BIT = 16384
mock_gl.GL_DEPTH_BUFFER_BIT = 256
mock_gl.GL_DEPTH_TEST = 2929
mock_gl.GL_LESS = 513
mock_gl.GL_ARRAY_BUFFER = 34962
mock_gl.GL_ELEMENT_ARRAY_BUFFER = 34963
mock_gl.GL_FRONT_AND_BACK = 10328
mock_gl.GL_LINE = 6913
mock_gl.GL_FILL = 6914
mock_gl.GL_UNSIGNED_INT = 5125
mock_gl.GL_STATIC_DRAW = 35044

mock_gl.glCreateShader.return_value = 1
mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
mock_gl.glCreateProgram.return_value = 99
mock_gl.glGetProgramiv.return_value = mock_gl.GL_TRUE
mock_gl.glGenFramebuffers.return_value = 55
mock_gl.glGenTextures.return_value = 66
mock_gl.glGenVertexArrays.return_value = 44
mock_gl.glGenBuffers.return_value = 88
mock_gl.glCheckFramebufferStatus.return_value = mock_gl.GL_FRAMEBUFFER_COMPLETE

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_mesh import DepthMeshEffectPlugin, METADATA
from vjlive3.plugins.api import PluginContext

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    return DepthMeshEffectPlugin()

@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 1920
    ctx.height = 1080
    ctx.inputs = {"video_in": 777, "depth_in": 42}
    ctx.outputs = {}
    return ctx

def test_plugin_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "DepthMesh"
    assert meta["plugin_type"] == "depth_effect"
    assert "mesh_resolution" in [p["name"] for p in meta["parameters"]]

@patch('vjlive3.plugins.depth_mesh.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.program == 99
    assert plugin.vao == 44
    assert plugin.ebo == 88
    mock_gl.glCreateShader.assert_any_call(mock_gl.GL_VERTEX_SHADER)
    mock_gl.glCreateShader.assert_any_call(mock_gl.GL_GEOMETRY_SHADER)
    mock_gl.glCreateShader.assert_any_call(mock_gl.GL_FRAGMENT_SHADER)

@patch('vjlive3.plugins.depth_mesh.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.depth_mesh.gl', mock_gl)
@patch('vjlive3.plugins.depth_mesh.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateProgram': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777

@patch('vjlive3.plugins.depth_mesh.gl', mock_gl)
def test_process_frame_standard_execution(plugin, context):
    plugin.initialize(context)
    
    params = {
        "mesh_resolution": 0.05,
        "mesh_wireframe": False,
        "color_mode": "velocity"
    }
    
    res = plugin.process_frame(777, params, context)
    
    assert res == 66 
    assert plugin.target_texture == 66
    
    # Assert EBO Buffer mapping triggers dynamically
    mock_gl.glBindBuffer.assert_any_call(mock_gl.GL_ELEMENT_ARRAY_BUFFER, 88)
    assert mock_gl.glBufferData.called
    
    mock_gl.glBindFramebuffer.assert_any_call(mock_gl.GL_FRAMEBUFFER, 55)
    mock_gl.glUseProgram.assert_any_call(99)
    
    # Assert Draw Elements is triggered with length mapped
    mock_gl.glDrawElements.assert_any_call(mock_gl.GL_TRIANGLES, plugin.num_indices, mock_gl.GL_UNSIGNED_INT, None)
    
    # Test alternative branches (Wireframe)
    params["mesh_wireframe"] = True
    params["color_mode"] = "white"
    res = plugin.process_frame(777, params, context)
    mock_gl.glPolygonMode.assert_any_call(mock_gl.GL_FRONT_AND_BACK, mock_gl.GL_LINE)

@patch('vjlive3.plugins.depth_mesh.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
@patch('vjlive3.plugins.depth_mesh.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.fbo = 55
    plugin.target_texture = 66
    plugin.program = 99
    plugin.vao = 44
    plugin.ebo = 88
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_called_with(99)
    mock_gl.glDeleteFramebuffers.assert_called_with(1, [55])
    mock_gl.glDeleteTextures.assert_called_with(1, [66])
    mock_gl.glDeleteVertexArrays.assert_called_with(1, [44])
    mock_gl.glDeleteBuffers.assert_called_with(1, [88])
