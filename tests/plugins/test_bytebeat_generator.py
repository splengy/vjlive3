"""Tests for P4-AU08: ByteBeat Generator."""
import pytest
from unittest.mock import MagicMock, patch
import sys

_mock_gl = MagicMock()
_mock_gl.GL_VERTEX_SHADER = 35633; _mock_gl.GL_FRAGMENT_SHADER = 35632
_mock_gl.GL_COMPILE_STATUS = 35713; _mock_gl.GL_LINK_STATUS = 35714
_mock_gl.GL_TEXTURE_2D = 3553; _mock_gl.GL_TRIANGLE_STRIP = 5
_mock_gl.GL_FALSE = 0; _mock_gl.GL_TRUE = 1
_mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
_mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44

sys.modules['OpenGL'] = MagicMock(); sys.modules['OpenGL.GL'] = _mock_gl

# from vjlive3.plugins.bytebeat_generator import ByteBeatGeneratorPlugin, METADATA, _map


@pytest.fixture
def plugin():
    _mock_gl.reset_mock()
    _mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
    _mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44
#     return ByteBeatGeneratorPlugin()


@pytest.fixture
def context():
    ctx = MagicMock()(MagicMock())
    ctx.width = 64; ctx.height = 48; ctx.time = 1.0
    ctx.inputs = {"video_in": 10}; ctx.outputs = {}
    return ctx


def test_metadata(plugin):
    m = plugin.get_metadata()
    assert m["name"] == "ByteBeat Generator"
    pnames = [p["name"] for p in m["parameters"]]
    assert "formula" in pnames; assert "speed" in pnames; assert "color_palette" in pnames
    assert len(pnames) == 4

def test_map_limits(plugin):
    assert _map(0.0, 0.0, 1.0) == pytest.approx(0.0); assert _map(10.0, 0.0, 1.0) == pytest.approx(1.0)

@patch('vjlive3.plugins.bytebeat_generator.gl', _mock_gl)
def test_initialize(plugin, context):
    assert plugin.initialize(context) is True

@patch('vjlive3.plugins.bytebeat_generator.gl', _mock_gl)
def test_process_zero_input(plugin, context):
    plugin.initialize(context); assert plugin.process_frame(0, {}, context) == 0

@patch('vjlive3.plugins.bytebeat_generator.gl', _mock_gl)
@patch('vjlive3.plugins.bytebeat_generator.hasattr')
def test_mock_fallback(mock_hasattr, plugin, context):
    mock_hasattr.side_effect = lambda o, a: False if a == 'glCreateShader' else True
    assert plugin.process_frame(10, {}, context) == 10

@patch('vjlive3.plugins.bytebeat_generator.gl', _mock_gl)
def test_process_all_formulas(plugin, context):
    plugin.initialize(context)
    context.inputs["audio_data"] = {"bass": 0.8, "treble": 0.5}
    for f in [0.0, 3.0, 6.0, 10.0]:
        _mock_gl.reset_mock()
        _mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
        _mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44
        assert plugin.process_frame(10, {"formula": f}, context) == 10

@patch('vjlive3.plugins.bytebeat_generator.gl', _mock_gl)
def test_compile_failure(plugin, context):
    _mock_gl.glGetShaderiv.return_value = 0; _mock_gl.glGetShaderInfoLog.return_value = b"Error"
    assert plugin.initialize(context) is False; assert plugin._mock_mode is True
    _mock_gl.glGetShaderiv.return_value = 1

@patch('vjlive3.plugins.bytebeat_generator.gl', _mock_gl)
def test_cleanup(plugin, context):
    plugin.initialize(context); plugin.prog = 99; plugin.cleanup()
    _mock_gl.glDeleteProgram.assert_called_once_with(99)
