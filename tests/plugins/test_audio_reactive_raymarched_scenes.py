"""Tests for P4-AU07: Audio Reactive Raymarched Scenes."""
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

from vjlive3.plugins.audio_reactive_raymarched_scenes import (
    AudioReactiveRaymarchedScenesPlugin, METADATA, _map
)
from vjlive3.plugins.api import PluginContext


@pytest.fixture
def plugin():
    _mock_gl.reset_mock()
    _mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
    _mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44
    return AudioReactiveRaymarchedScenesPlugin()


@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width = 64; ctx.height = 48; ctx.time = 1.0
    ctx.inputs = {"video_in": 10}; ctx.outputs = {}
    return ctx


def test_metadata(plugin):
    m = plugin.get_metadata()
    assert m["name"] == "Audio Reactive Raymarched Scenes"
    pnames = [p["name"] for p in m["parameters"]]
    assert "scene_type" in pnames; assert "base_radius" in pnames; assert len(pnames) == 5

def test_map_limits(plugin):
    assert _map(0.0, 0.0, 1.0) == pytest.approx(0.0); assert _map(10.0, 0.0, 1.0) == pytest.approx(1.0)

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _mock_gl)
def test_initialize(plugin, context):
    assert plugin.initialize(context) is True

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _mock_gl)
def test_process_zero_input(plugin, context):
    plugin.initialize(context); assert plugin.process_frame(0, {}, context) == 0

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _mock_gl)
@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.hasattr')
def test_mock_fallback(mock_hasattr, plugin, context):
    mock_hasattr.side_effect = lambda o, a: False if a == 'glCreateShader' else True
    assert plugin.process_frame(10, {}, context) == 10

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _mock_gl)
def test_process_scene_types(plugin, context):
    plugin.initialize(context)
    context.inputs["audio_data"] = {"bass": 0.7, "mid": 0.5, "treble": 0.3,
                                     "volume": 0.9, "beat_confidence": 0.8}
    for scene_val in [0.0, 5.0, 10.0]:
        _mock_gl.reset_mock()
        _mock_gl.glGetShaderiv.return_value = 1; _mock_gl.glGetProgramiv.return_value = 1
        _mock_gl.glCreateProgram.return_value = 99; _mock_gl.glGenVertexArrays.return_value = 44
        params = {"scene_type": scene_val, "base_radius": 5.0, "audio_sensitivity": 5.0}
        assert plugin.process_frame(10, params, context) == 10

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _mock_gl)
def test_compile_failure(plugin, context):
    _mock_gl.glGetShaderiv.return_value = 0; _mock_gl.glGetShaderInfoLog.return_value = b"Error"
    assert plugin.initialize(context) is False; assert plugin._mock_mode is True
    _mock_gl.glGetShaderiv.return_value = 1

@patch('vjlive3.plugins.audio_reactive_raymarched_scenes.gl', _mock_gl)
def test_cleanup(plugin, context):
    plugin.initialize(context); plugin.prog = 99; plugin.cleanup()
    _mock_gl.glDeleteProgram.assert_called_once_with(99)
