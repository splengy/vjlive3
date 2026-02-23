import pytest
from unittest.mock import MagicMock, patch
import sys

mock_gl = MagicMock()
mock_gl.GL_VERTEX_SHADER   = 35633
mock_gl.GL_FRAGMENT_SHADER = 35632
mock_gl.GL_COMPILE_STATUS  = 35713
mock_gl.GL_LINK_STATUS     = 35714
mock_gl.GL_TEXTURE_2D      = 3553
mock_gl.GL_TEXTURE0        = 33984
mock_gl.GL_RGBA            = 6408
mock_gl.GL_UNSIGNED_BYTE   = 5121
mock_gl.GL_LINEAR          = 9729
mock_gl.GL_TEXTURE_MIN_FILTER = 10241
mock_gl.GL_TEXTURE_MAG_FILTER = 10240
mock_gl.GL_FRAMEBUFFER     = 36160
mock_gl.GL_COLOR_ATTACHMENT0 = 36064
mock_gl.GL_COLOR_BUFFER_BIT  = 16384
mock_gl.GL_TRIANGLE_STRIP  = 5
mock_gl.GL_CLAMP_TO_EDGE = 33071
mock_gl.GL_FALSE = 0
mock_gl.GL_TRUE  = 1
mock_gl.glCheckFramebufferStatus.return_value = 36053  # GL_FRAMEBUFFER_COMPLETE

mock_gl.glCreateShader.return_value   = 1
mock_gl.glGetShaderiv.return_value    = mock_gl.GL_TRUE
mock_gl.glCreateProgram.return_value  = 99
mock_gl.glGetProgramiv.return_value   = mock_gl.GL_TRUE
mock_gl.glGenVertexArrays.return_value = 44

_fbo_c = 50
_tex_c = 60

def _gen_fbo(n):
    global _fbo_c
    _fbo_c += 1
    return _fbo_c

def _gen_tex(n):
    global _tex_c
    _tex_c += 1
    return _tex_c

mock_gl.glGenFramebuffers.side_effect = _gen_fbo
mock_gl.glGenTextures.side_effect     = _gen_tex

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = mock_gl

from vjlive3.plugins.depth_mosh_nexus import DepthMoshNexusPlugin, METADATA
from vjlive3.plugins.api import PluginContext


@pytest.fixture
def plugin():
    mock_gl.reset_mock()
    mock_gl.glCreateProgram.return_value = 99
    global _fbo_c, _tex_c
    _fbo_c = 50
    _tex_c = 60
    return DepthMoshNexusPlugin()


@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width   = 1920
    ctx.height  = 1080
    ctx.inputs  = {"video_in": 777, "depth_in": 888, "depth_in_b": 999}
    ctx.time    = 10.0
    ctx.outputs = {}
    return ctx


def test_plugin_metadata(plugin):
    meta = plugin.get_metadata()
    assert meta["name"] == "Depth Mosh Nexus"
    assert "video_in"   in meta["inputs"]
    assert "depth_in"   in meta["inputs"]
    assert "depth_in_b" in meta["inputs"]
    assert "video_out"  in meta["outputs"]
    p_names = [p["name"] for p in meta["parameters"]]
    assert "master_intensity"      in p_names
    assert "displacement_strength" in p_names
    assert "loop_in"               in p_names
    assert "loop_out"              in p_names
    assert len(p_names) == 10


@patch('vjlive3.plugins.depth_mosh_nexus.gl', mock_gl)
def test_plugin_initialization(plugin, context):
    res = plugin.initialize(context)
    assert res is True
    assert plugin._initialized is True
    assert plugin.prog == 99


@patch('vjlive3.plugins.depth_mosh_nexus.gl', mock_gl)
def test_process_frame_empty_input(plugin, context):
    plugin.initialize(context)
    assert plugin.process_frame(0, {}, context) == 0


@patch('vjlive3.plugins.depth_mosh_nexus.gl', mock_gl)
@patch('vjlive3.plugins.depth_mosh_nexus.hasattr')
def test_process_frame_mock_fallback(mock_hasattr, plugin, context):
    def attr_check(obj, attr):
        if attr == 'glCreateShader': return False
        return True
    mock_hasattr.side_effect = attr_check
    assert plugin.process_frame(777, {}, context) == 777


@patch('vjlive3.plugins.depth_mosh_nexus.gl', mock_gl)
def test_process_frame_standard_execution(plugin, context):
    plugin.initialize(context)
    params = {
        "master_intensity":      0.9,
        "displacement_strength": 0.8,
        "mosh_chaos":            0.6,
        "loop_in":               0.0,
        "loop_out":              1.0,
        "depth_blend":           0.7,
        "bass_pulse":            0.8,
        "treble_glow":           0.5,
        "mosh_speed":            1.5,
        "feedback_amount":       0.4,
    }
    res = plugin.process_frame(777, params, context)

    # Textures bound to expected units
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "tex0"),      0)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "texPrev"),   1)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "depth_tex0"), 2)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "depth_tex1"), 3)

    # Depth guards set correctly (both depth inputs present)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "has_depth0"), 1)
    mock_gl.glUniform1i.assert_any_call(mock_gl.glGetUniformLocation(99, "has_depth1"), 1)

    # Key parameter passthrough
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "master_intensity"),      0.9)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "loop_out"),              1.0)
    mock_gl.glUniform1f.assert_any_call(mock_gl.glGetUniformLocation(99, "mosh_speed"),            1.5)


@patch('vjlive3.plugins.depth_mosh_nexus.gl', mock_gl)
def test_gl_compile_failure(plugin, context):
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_FALSE
    mock_gl.glGetShaderInfoLog.return_value = b"Error"
    res = plugin.initialize(context)
    assert res is False
    assert plugin._initialized is False
    mock_gl.glGetShaderiv.return_value = mock_gl.GL_TRUE


@patch('vjlive3.plugins.depth_mosh_nexus.gl', mock_gl)
def test_plugin_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.fbo_a = 51
    plugin.tex_a = 61
    plugin.fbo_b = 52
    plugin.tex_b = 62
    plugin.prog  = 99

    plugin.cleanup()

    mock_gl.glDeleteProgram.assert_any_call(99)
    mock_gl.glDeleteFramebuffers.assert_any_call(2, [51, 52])
    mock_gl.glDeleteTextures.assert_any_call(2, [61, 62])
    mock_gl.glDeleteVertexArrays.assert_any_call(1, [44])
