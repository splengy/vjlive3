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
mock_gl.GL_RGBA32F = 34836
mock_gl.GL_FLOAT = 5126
mock_gl.GL_UNSIGNED_BYTE = 5121
mock_gl.GL_LINEAR = 9729
mock_gl.GL_NEAREST = 9728
mock_gl.GL_TEXTURE_MIN_FILTER = 10241
mock_gl.GL_TEXTURE_MAG_FILTER = 10240
mock_gl.GL_FRAMEBUFFER = 36160
mock_gl.GL_COLOR_ATTACHMENT0 = 36064
mock_gl.GL_COLOR_ATTACHMENT1 = 36065
mock_gl.GL_FRAMEBUFFER_COMPLETE = 36053
mock_gl.GL_FALSE = 0
mock_gl.GL_TRUE = 1
mock_gl.GL_NO_ERROR = 0
mock_gl.GL_TRIANGLES = 4
mock_gl.GL_TRIANGLE_STRIP = 5
mock_gl.GL_POINTS = 0
mock_gl.GL_COLOR_BUFFER_BIT = 16384
mock_gl.GL_DEPTH_BUFFER_BIT = 256
mock_gl.GL_DEPTH_TEST = 2929
mock_gl.GL_LESS = 513
mock_gl.GL_ARRAY_BUFFER = 34962
mock_gl.GL_ELEMENT_ARRAY_BUFFER = 34963
mock_gl.GL_UNSIGNED_INT = 5125
mock_gl.GL_STATIC_DRAW = 35044
mock_gl.GL_BLEND = 3042
mock_gl.GL_SRC_ALPHA = 770
mock_gl.GL_ONE = 1
mock_gl.GL_PROGRAM_POINT_SIZE = 34370

mock_gl.glCreateShader.return_value = 1
mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
mock_gl.glCreateProgram.side_effect = [98, 99] # Sim, Render
mock_gl.glGetProgramiv.return_value = mock_gl.GL_TRUE
mock_gl.glGenFramebuffers.side_effect = [[52, 53], 55] # internal FBOs, render FBO
mock_gl.glGenTextures.side_effect = [[62, 63], [64, 65], 66] # Pos, Vel, Render Tex
mock_gl.glGenVertexArrays.return_value = 44
mock_gl.glCheckFramebufferStatus.return_value = mock_gl.GL_FRAMEBUFFER_COMPLETE

sys.modules['OpenGL'] = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_particle_3d import DepthParticle3DPlugin, METADATA

@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.side_effect = [98, 99]
    mock_gl.glGenFramebuffers.side_effect = [[52, 53], 55] 
    mock_gl.glGenTextures.side_effect = [[62, 63], [64, 65], 66] 
    return DepthParticle3DPlugin()

@pytest.fixture
def context():
    ctx = MagicMock()(MagicMock())
    ctx.width = 1920
    ctx.height = 1080
    ctx.inputs = {"video_in": 777, "depth_in": 42}
    ctx.outputs = {}
    return ctx

def test_plugin_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "DepthParticle3D"
    assert meta["plugin_type"] == "depth_effect"
    assert "particleLifetime" in [p["name"] for p in meta["parameters"]]

@patch('vjlive3.plugins.depth_particle_3d.gl', mock_gl)
def test_plugin_initialization_mock_mode(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.sim_program == 98
    assert plugin.render_program == 99
    assert plugin.data_fbos == [52, 53]
    assert plugin.pos_textures == [62, 63]
    assert plugin.vel_textures == [64, 65]
    mock_gl.glDrawBuffers.assert_any_call(2, [mock_gl.GL_COLOR_ATTACHMENT0, mock_gl.GL_COLOR_ATTACHMENT1])

@patch('vjlive3.plugins.depth_particle_3d.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    res = plugin.process_frame(0, {}, context)
    assert res == 0

@patch('vjlive3.plugins.depth_particle_3d.gl', mock_gl)
@patch('vjlive3.plugins.depth_particle_3d.hasattr')
def test_process_frame_fallback_mock_mode(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateProgram': return False
        return True
    mock_hasattr.side_effect = attr_check
    
    res = plugin.process_frame(777, {}, context)
    assert res == 777

@patch('vjlive3.plugins.depth_particle_3d.gl', mock_gl)
def test_process_frame_standard_execution(plugin, context):
    plugin.initialize(context)
    
    params = {
        "particleSize": 0.5,
        "emissionRate": 0.7,
        "color_mode": "depth"
    }
    
    # Run Frame 1 (Write to 1, Read 0)
    res = plugin.process_frame(777, params, context)
    
    # Sim pass Program usage
    mock_gl.glUseProgram.assert_any_call(98)
    # Render pass Program usage
    mock_gl.glUseProgram.assert_any_call(99)
    
    # Assert Simulation Quad triggered
    mock_gl.glDrawArrays.assert_any_call(mock_gl.GL_TRIANGLE_STRIP, 0, 4)
    # Assert Particles rendered
    mock_gl.glDrawArrays.assert_any_call(mock_gl.GL_POINTS, 0, 10000)
    
    # Assert ping-pong state updated
    assert plugin.ping_idx == 1
    
    # Run Frame 2 (Write to 0, Read 1)
    plugin.process_frame(777, params, context)
    assert plugin.ping_idx == 0

@patch('vjlive3.plugins.depth_particle_3d.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Syntax Error"
    
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE
    
@patch('vjlive3.plugins.depth_particle_3d.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.render_fbo = 55
    plugin.render_texture = 66
    
    plugin.cleanup()
    
    mock_gl.glDeleteProgram.assert_any_call(98)
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteFramebuffers.assert_any_call(1, [55])
    mock_gl.glDeleteFramebuffers.assert_any_call(2, [52, 53])
    mock_gl.glDeleteTextures.assert_any_call(1, [66])
    mock_gl.glDeleteTextures.assert_any_call(2, [62, 63])
    mock_gl.glDeleteTextures.assert_any_call(2, [64, 65])
