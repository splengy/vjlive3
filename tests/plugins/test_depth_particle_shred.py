"""
Tests for P3-VD61: Depth Particle Shred (GPGPU GL_POINTS implementation).
Mocks OpenGL before importing the plugin.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys

# ── GL mocks ──────────────────────────────────────────────────────
_mock_gl = MagicMock()
_mock_gl.GL_VERTEX_SHADER     = 35633
_mock_gl.GL_FRAGMENT_SHADER   = 35632
_mock_gl.GL_COMPILE_STATUS    = 35713
_mock_gl.GL_LINK_STATUS       = 35714
_mock_gl.GL_TEXTURE_2D        = 3553
_mock_gl.GL_RGBA              = 6408
_mock_gl.GL_UNSIGNED_BYTE     = 5121
_mock_gl.GL_LINEAR            = 9729
_mock_gl.GL_CLAMP_TO_EDGE     = 33071
_mock_gl.GL_TEXTURE_MIN_FILTER = 10241
_mock_gl.GL_TEXTURE_MAG_FILTER = 10240
_mock_gl.GL_TEXTURE_WRAP_S    = 10242
_mock_gl.GL_TEXTURE_WRAP_T    = 10243
_mock_gl.GL_FRAMEBUFFER       = 36160
_mock_gl.GL_COLOR_ATTACHMENT0 = 36064
_mock_gl.GL_COLOR_BUFFER_BIT  = 16384
_mock_gl.GL_TRIANGLE_STRIP    = 5
_mock_gl.GL_POINTS            = 0
_mock_gl.GL_ARRAY_BUFFER      = 34962
_mock_gl.GL_STATIC_DRAW       = 35044
_mock_gl.GL_FLOAT             = 5126
_mock_gl.GL_FALSE             = 0
_mock_gl.GL_TRUE              = 1
_mock_gl.GL_BLEND             = 3042
_mock_gl.GL_SRC_ALPHA         = 770
_mock_gl.GL_ONE               = 1
_mock_gl.GL_PROGRAM_POINT_SIZE = 34370
_mock_gl.glCheckFramebufferStatus.return_value = 36053

_mock_gl.glCreateShader.return_value      = 1
_mock_gl.glGetShaderiv.return_value       = 1
_mock_gl.glGetProgramiv.return_value      = 1
_mock_gl.glCreateProgram.return_value     = 99
_mock_gl.glGenVertexArrays.return_value   = 44
_mock_gl.glGenBuffers.return_value        = 33
_mock_gl.glGenFramebuffers.return_value   = 51
_mock_gl.glGenTextures.return_value       = 101

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _mock_gl

from vjlive3.plugins.depth_particle_shred import DepthParticleShredPlugin, METADATA


@pytest.fixture
def plugin():
    _mock_gl.reset_mock()
    _mock_gl.glGetShaderiv.return_value           = 1
    _mock_gl.glGetProgramiv.return_value          = 1
    _mock_gl.glCheckFramebufferStatus.return_value = 36053
    _mock_gl.glCreateProgram.return_value         = 99
    _mock_gl.glGenVertexArrays.return_value       = 44
    _mock_gl.glGenBuffers.return_value            = 33
    _mock_gl.glGenFramebuffers.return_value       = 51
    _mock_gl.glGenTextures.return_value           = 101
    return DepthParticleShredPlugin()


@pytest.fixture
def context():
    ctx = MagicMock()(MagicMock())
    ctx.width = 64
    ctx.height = 48
    ctx.inputs = {"video_in": 10, "depth_in": 20}
    ctx.time = 1.0
    ctx.outputs = {}
    return ctx


def test_metadata(plugin):
    m = plugin.get_metadata()
    assert m["name"] == "Depth Particle Shred"
    assert "video_in" in m["inputs"]
    assert "depth_in" in m["inputs"]
    assert "video_out" in m["outputs"]
    pnames = [p["name"] for p in m["parameters"]]
    assert "shred_amount" in pnames
    assert "particle_size" in pnames
    assert "trail_length" in pnames
    assert "gravity" in pnames
    assert len(pnames) == 7


@patch('vjlive3.plugins.depth_particle_shred.gl', _mock_gl)
def test_initialize(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True


@patch('vjlive3.plugins.depth_particle_shred.gl', _mock_gl)
def test_process_zero_input(plugin, context):
    plugin.initialize(context)
    assert plugin.process_frame(0, {}, context) == 0


@patch('vjlive3.plugins.depth_particle_shred.gl', _mock_gl)
@patch('vjlive3.plugins.depth_particle_shred.hasattr')
def test_mock_fallback(mock_hasattr, plugin, context):
    def chk(obj, attr): return False if attr == 'glCreateShader' else True
    mock_hasattr.side_effect = chk
    assert plugin.process_frame(10, {}, context) == 10


@patch('vjlive3.plugins.depth_particle_shred.gl', _mock_gl)
def test_process_renders_particles(plugin, context):
    plugin.initialize(context)
    params = {
        "shred_amount": 0.5, "particle_size": 4.0, "velocity_scale": 1.0,
        "turbulence": 0.3, "trail_length": 0.4, "color_shift": 0.2, "gravity": 0.1
    }
    res = plugin.process_frame(10, params, context)
    # Both GL passes should have been invoked
    _mock_gl.glDrawArrays.assert_called()
    _mock_gl.glBindFramebuffer.assert_called()


@patch('vjlive3.plugins.depth_particle_shred.gl', _mock_gl)
def test_process_depth_flag_no_depth(plugin, context):
    plugin.initialize(context)
    context.inputs = {"video_in": 10, "depth_in": 0}
    plugin.process_frame(10, {}, context)
    # has_depth should be set to 0
    _mock_gl.glUniform1i.assert_any_call(
        _mock_gl.glGetUniformLocation(99, "has_depth"), 0
    )


@patch('vjlive3.plugins.depth_particle_shred.gl', _mock_gl)
def test_compile_failure(plugin, context):
    _mock_gl.glGetShaderiv.return_value = 0
    _mock_gl.glGetShaderInfoLog.return_value = b"Error"
    assert plugin.initialize(context) is False
    assert plugin._mock_mode is True
    _mock_gl.glGetShaderiv.return_value = 1


@patch('vjlive3.plugins.depth_particle_shred.gl', _mock_gl)
def test_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.prog_particle  = 99
    plugin.prog_composite = 100
    plugin.cleanup()
    _mock_gl.glDeleteProgram.assert_any_call(99)
    _mock_gl.glDeleteProgram.assert_any_call(100)
