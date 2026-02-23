import pytest
from unittest.mock import MagicMock, patch
import sys

mock_gl = MagicMock()
mock_gl.GL_VERTEX_SHADER    = 35633
mock_gl.GL_FRAGMENT_SHADER  = 35632
mock_gl.GL_COMPILE_STATUS   = 35713
mock_gl.GL_LINK_STATUS      = 35714
mock_gl.GL_TEXTURE_2D       = 3553
mock_gl.GL_RGBA              = 6408
mock_gl.GL_UNSIGNED_BYTE    = 5121
mock_gl.GL_LINEAR            = 9729
mock_gl.GL_CLAMP_TO_EDGE    = 33071
mock_gl.GL_FRAMEBUFFER      = 36160
mock_gl.GL_COLOR_ATTACHMENT0 = 36064
mock_gl.GL_COLOR_BUFFER_BIT  = 16384
mock_gl.GL_POINTS            = 0
mock_gl.GL_TRIANGLE_STRIP    = 5
mock_gl.GL_BLEND             = 3042
mock_gl.GL_SRC_ALPHA         = 770
mock_gl.GL_ONE               = 1
mock_gl.GL_PROGRAM_POINT_SIZE = 34370
mock_gl.GL_ARRAY_BUFFER      = 34962
mock_gl.GL_STATIC_DRAW       = 35044
mock_gl.GL_FLOAT             = 5126
mock_gl.GL_FALSE             = 0
mock_gl.GL_TRUE              = 1

mock_gl.glCreateShader.return_value     = 1
mock_gl.glGetShaderiv.return_value      = mock_gl.GL_TRUE
mock_gl.glGetProgramiv.return_value     = mock_gl.GL_TRUE
mock_gl.glGenVertexArrays.return_value  = 44
mock_gl.glGenBuffers.return_value       = 33

_c = {"fbo": 50, "tex": 60, "prog": 98}
def _gp():     _c["prog"]+=1; return _c["prog"]
def _gfbo(n):  _c["fbo"] +=1; return _c["fbo"]
def _gtex(n):  _c["tex"] +=1; return _c["tex"]
mock_gl.glCreateProgram.side_effect   = _gp
mock_gl.glGenFramebuffers.side_effect = _gfbo
mock_gl.glGenTextures.side_effect     = _gtex

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_particle_shred import DepthParticleShredPlugin, METADATA
from vjlive3.plugins.api import PluginContext


@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glGetShaderiv.return_value  = mock_gl.GL_TRUE
    mock_gl.glGetProgramiv.return_value = mock_gl.GL_TRUE
    mock_gl.glGenVertexArrays.return_value = 44
    mock_gl.glGenBuffers.return_value     = 33
    _c.update({"fbo": 50, "tex": 60, "prog": 98})
    return DepthParticleShredPlugin()


@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 1920; ctx.height = 1080
    ctx.inputs = {"video_in": 777, "depth_in": 888}
    ctx.time = 1.0; ctx.outputs = {}
    return ctx


def test_metadata(plugin):
    m = plugin.get_metadata()
    assert m["name"] == "Depth Particle Shred"
    assert "depth_in" in m["inputs"]
    pnames = [p["name"] for p in m["parameters"]]
    assert "shred_amount"  in pnames
    assert "particle_size" in pnames
    assert len(pnames) == 7


@patch('vjlive3.plugins.depth_particle_shred.gl', mock_gl)
def test_initialize(plugin, context):
    assert plugin.initialize(context) is True
    assert plugin._initialized is True


@patch('vjlive3.plugins.depth_particle_shred.gl', mock_gl)
def test_empty_input(plugin, context):
    plugin.initialize(context)
    assert plugin.process_frame(0, {}, context) == 0


@patch('vjlive3.plugins.depth_particle_shred.gl', mock_gl)
@patch('vjlive3.plugins.depth_particle_shred.hasattr')
def test_mock_fallback(mock_hasattr, plugin, context):
    def chk(obj, attr): return False if attr == 'glCreateShader' else True
    mock_hasattr.side_effect = chk
    assert plugin.process_frame(777, {}, context) == 777


@patch('vjlive3.plugins.depth_particle_shred.gl', mock_gl)
def test_process_with_depth(plugin, context):
    plugin.initialize(context)
    params = {"shred_amount": 0.5, "particle_size": 4.0, "velocity_scale": 1.0,
              "turbulence": 0.3, "trail_length": 0.4, "color_shift": 0.2, "gravity": 0.1}
    plugin.process_frame(777, params, context)
    mock_gl.glDrawArrays.assert_called()
    mock_gl.glBindFramebuffer.assert_called()


@patch('vjlive3.plugins.depth_particle_shred.gl', mock_gl)
def test_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"err"
    assert plugin.initialize(context) is False
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE


@patch('vjlive3.plugins.depth_particle_shred.gl', mock_gl)
def test_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.prog_particle  = 99
    plugin.prog_composite = 100
    plugin.cleanup()
    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteProgram.assert_any_call(100)
