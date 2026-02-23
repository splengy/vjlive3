"""Tests for P3-EXT004: Agent Avatar Effect (AgentAvatarPlugin)."""
import sys, pytest
from unittest.mock import MagicMock, patch

_g = MagicMock()
_g.glGetShaderiv.return_value   = 1
_g.glGetProgramiv.return_value  = 1
_g.glCreateProgram.return_value = 99
_g.glGenVertexArrays.return_value = 44
for attr in ("GL_VERTEX_SHADER","GL_FRAGMENT_SHADER","GL_COMPILE_STATUS","GL_LINK_STATUS",
             "GL_TEXTURE_2D","GL_TRIANGLE_STRIP"):
    setattr(_g, attr, MagicMock())

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _g

from vjlive3.plugins.agent_avatar import AgentAvatarPlugin, METADATA, PRESETS


@pytest.fixture(autouse=True)
def reset_gl():
    _g.reset_mock()
    _g.glGetShaderiv.return_value = 1
    _g.glGetProgramiv.return_value = 1
    _g.glCreateProgram.return_value = 99
    _g.glGenVertexArrays.return_value = 44


@pytest.fixture
def plugin(): return AgentAvatarPlugin()


@pytest.fixture
def ctx():
    c = MagicMock()(MagicMock())
    c.width = 64; c.height = 48; c.time = 1.0
    c.inputs = {"video_in": 10}; c.outputs = {}
    return c


def test_metadata_name():       assert METADATA["name"] == "Agent Avatar"
def test_metadata_20_params():  assert len(METADATA["parameters"]) == 20
def test_required_params():
    names = {p["name"] for p in METADATA["parameters"]}
    for n in ("spin_speed", "confidence", "fragmentation", "glow_intensity",
              "avatar_scale", "shadow_mode_enabled", "eye_tracking_enabled"):
        assert n in names
def test_presets_count():       assert len(PRESETS) == 6
def test_presets_content():
    assert "thinking_state" in PRESETS and "overwhelmed_state" in PRESETS


@patch('vjlive3.plugins.agent_avatar.gl', _g)
def test_initialize(plugin, ctx):   assert plugin.initialize(ctx) is True

@patch('vjlive3.plugins.agent_avatar.gl', _g)
def test_zero_texture(plugin, ctx): plugin.initialize(ctx); assert plugin.process_frame(0, {}, ctx) == 0

@patch('vjlive3.plugins.agent_avatar.gl', _g)
def test_process_calls_draw(plugin, ctx):
    plugin.initialize(ctx); plugin.process_frame(10, {}, ctx)
    _g.glDrawArrays.assert_called()

@patch('vjlive3.plugins.agent_avatar.gl', _g)
def test_video_out_set(plugin, ctx):
    plugin.initialize(ctx); plugin.process_frame(10, {}, ctx)
    assert 'video_out' in ctx.outputs

@patch('vjlive3.plugins.agent_avatar.gl', _g)
def test_all_params(plugin, ctx):
    plugin.initialize(ctx)
    params = {p["name"]: p["default"] for p in METADATA["parameters"]}
    assert plugin.process_frame(10, params, ctx) is not None

@patch('vjlive3.plugins.agent_avatar.gl', _g)
def test_thinking_preset(plugin, ctx):
    plugin.initialize(ctx)
    assert plugin.process_frame(10, PRESETS["thinking_state"], ctx) is not None

@patch('vjlive3.plugins.agent_avatar.gl', _g)
def test_overwhelmed_preset(plugin, ctx):
    plugin.initialize(ctx)
    assert plugin.process_frame(10, PRESETS["overwhelmed_state"], ctx) is not None

@patch('vjlive3.plugins.agent_avatar.gl', _g)
def test_eye_tracking_uniforms_set(plugin, ctx):
    plugin.initialize(ctx)
    plugin.process_frame(10, {"eye_tracking_enabled": 10.0, "gaze_x": 8.0, "gaze_y": 2.0}, ctx)
    _g.glUniform2f.assert_called()

@patch('vjlive3.plugins.agent_avatar.gl', _g)
def test_compile_failure(plugin, ctx):
    _g.glGetShaderiv.return_value = 0
    _g.glGetShaderInfoLog.return_value = b"err"
    assert plugin.initialize(ctx) is False
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.agent_avatar.gl', _g)
def test_cleanup(plugin, ctx):
    plugin.initialize(ctx); plugin.prog = 99; plugin.cleanup()
    _g.glDeleteProgram.assert_called_with(99)

def test_mock_mode(plugin, ctx):
    plugin._mock_mode = True
    assert plugin.process_frame(10, {}, ctx) == 10
    assert ctx.outputs.get('video_out') == 10
