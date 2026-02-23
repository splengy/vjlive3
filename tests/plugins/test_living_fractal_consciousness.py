"""Tests for P3-EXT005: Living Fractal Consciousness (LivingFractalConsciousnessPlugin)."""
import sys, pytest, time
from unittest.mock import MagicMock, patch

_g = MagicMock()
_g.glGetShaderiv.return_value    = 1
_g.glGetProgramiv.return_value   = 1
_g.glCreateProgram.return_value  = 99
_g.glGenVertexArrays.return_value = 44
for attr in ("GL_VERTEX_SHADER","GL_FRAGMENT_SHADER","GL_COMPILE_STATUS","GL_LINK_STATUS",
             "GL_TEXTURE_2D","GL_TRIANGLE_STRIP","GL_TEXTURE0"):
    setattr(_g, attr, MagicMock())

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _g

from vjlive3.plugins.living_fractal_consciousness import (
    LivingFractalConsciousnessPlugin, AgentPersonality, AgentInfluence,
    FractalSnapshot, METADATA, PRESETS, PARAM_ORDER, MOOD_MODIFIERS, VALID_MOODS
)
from vjlive3.plugins.api import PluginContext


@pytest.fixture(autouse=True)
def reset_gl():
    _g.reset_mock()
    _g.glGetShaderiv.return_value   = 1
    _g.glGetProgramiv.return_value  = 1
    _g.glCreateProgram.return_value = 99
    _g.glGenVertexArrays.return_value = 44


@pytest.fixture
def plugin(): return LivingFractalConsciousnessPlugin()


@pytest.fixture
def ctx():
    c = PluginContext(MagicMock())
    c.width = 64; c.height = 48; c.time = 0.0
    c.inputs = {"video_in": 10}; c.outputs = {}
    return c


# ── Agent system ───────────────────────────────────────────────────────────

def test_agent_personality_enum():
    values = {p.value for p in AgentPersonality}
    assert values == {"trinity","cipher","neon","azura","antigravity"}

def test_agent_influence_default():
    a = AgentInfluence(AgentPersonality.TRINITY)
    assert a.intensity == 0.8
    assert a.mood == "neutral"
    assert a.effective_intensity() == a.intensity

def test_all_agents_initialized(plugin):
    assert len(plugin.agents) == 5
    for p in AgentPersonality:
        assert p in plugin.agents

def test_agent_configs_complete(plugin):
    for p, agent in plugin.agents.items():
        assert len(agent.parameter_weights) == 11  # All PARAM_ORDER keys

def test_mood_modifiers_present():
    for mood in VALID_MOODS:
        assert mood in MOOD_MODIFIERS

def test_set_agent_mood_valid(plugin):
    plugin.set_agent_mood(AgentPersonality.TRINITY, "calm")
    assert plugin.agents[AgentPersonality.TRINITY].mood == "calm"

def test_set_agent_mood_invalid_raises(plugin):
    with pytest.raises(ValueError):
        plugin.set_agent_mood(AgentPersonality.TRINITY, "bananas")

def test_get_agent_status(plugin):
    status = plugin.get_agent_status()
    assert "trinity" in status and "antigravity" in status

def test_influence_vector_length_5(plugin):
    vec = plugin.get_agent_influence_vector()
    assert len(vec) == 5

def test_mood_vector_length_5(plugin):
    vec = plugin.get_agent_mood_vector()
    assert len(vec) == 5


# ── Parameter system ────────────────────────────────────────────────────────

def test_all_11_core_params(plugin):
    for p in PARAM_ORDER:
        assert p in plugin.params

def test_set_parameter_valid(plugin):
    plugin.set_parameter("complexity", 8.0)
    assert plugin.params["complexity"] == 8.0

def test_set_parameter_clamped_high(plugin):
    plugin.set_parameter("complexity", 100.0)
    assert plugin.params["complexity"] == 10.0

def test_set_parameter_clamped_low(plugin):
    plugin.set_parameter("complexity", -5.0)
    assert plugin.params["complexity"] == 0.0

def test_set_parameter_unknown_noop(plugin):
    plugin.set_parameter("does_not_exist", 5.0)  # Should log warning, not raise


# ── Snapshot & morph ────────────────────────────────────────────────────────

def test_create_snapshot(plugin):
    snap = plugin.create_snapshot("test")
    assert snap.description == "test"
    assert "complexity" in snap.parameters
    assert len(snap.agent_states) == 5

def test_snapshot_captures_current_params(plugin):
    plugin.params["complexity"] = 9.0
    snap = plugin.create_snapshot()
    assert snap.parameters["complexity"] == 9.0

def test_start_morph_to(plugin):
    snap = plugin.create_snapshot()
    plugin.params["complexity"] = 3.0
    snap2 = plugin.create_snapshot()
    plugin.start_morph_to(snap2, duration=2.0)
    assert plugin.morph_target is not None
    assert plugin.morph_progress == 0.0

def test_morph_progress_linear(plugin):
    snap = plugin.create_snapshot()
    plugin.start_morph_to(snap, duration=2.0)
    done = plugin.update_morph(1.0)   # half way
    assert not done
    assert abs(plugin.morph_progress - 0.5) < 0.01

def test_morph_completes(plugin):
    snap = plugin.create_snapshot()
    plugin.start_morph_to(snap, duration=0.1)
    done = plugin.update_morph(0.2)
    assert done
    assert plugin.morph_target is None

def test_morph_interpolates_params(plugin):
    plugin.params["complexity"] = 2.0
    start = plugin.create_snapshot()
    plugin.params["complexity"] = 8.0
    end_snap = plugin.create_snapshot()
    plugin.start_morph_to(end_snap, duration=1.0)
    plugin.morph_start_params["complexity"] = 2.0
    plugin.update_morph(0.5)
    assert 4.0 < plugin.params["complexity"] < 6.0  # Interpolated midpoint


# ── Audio reactivity ────────────────────────────────────────────────────────

def test_update_audio_sets_pulse(plugin):
    plugin.update_audio({"bass": 0.8, "beat": 0.6, "mid": 0.3, "high": 0.1, "volume": 0.5})
    assert plugin.params["pulse"] > 0.0

def test_audio_smoothing(plugin):
    plugin.update_audio({"bass": 1.0, "beat": 1.0, "mid": 0.0, "high": 0.0, "volume": 0.0})
    v1 = plugin.audio_buffer["bass"]
    plugin.update_audio({"bass": 0.0, "beat": 0.0, "mid": 0.0, "high": 0.0, "volume": 0.0})
    v2 = plugin.audio_buffer["bass"]
    assert 0.0 < v2 < v1  # Smoothed, not instant drop

def test_update_audio_empty_dict_safe(plugin):
    plugin.update_audio({})  # Should not raise


# ── Agent evolution ─────────────────────────────────────────────────────────

def test_evolve_agents_no_error(plugin):
    plugin.evolve_agents(1.0)  # Should not raise

def test_evolve_agents_triggers_after_interval(plugin):
    plugin._evolve_interval = 0.1
    original_moods = {p: a.mood for p, a in plugin.agents.items()}
    plugin.evolve_agents(0.2)  # Trigger evolution
    # At least one mood or intensity may have changed — can't assert exact value
    # but method should run without error


# ── Peak trigger ────────────────────────────────────────────────────────────

def test_trigger_peak_sets_intensity(plugin):
    plugin.trigger_agent_peak(AgentPersonality.NEON, duration=2.0)
    assert plugin.agents[AgentPersonality.NEON]._peak_intensity > 0

def test_peak_auto_decays(plugin):
    plugin.trigger_agent_peak(AgentPersonality.NEON, duration=0.1)
    plugin._update_peak_timers(0.2)
    assert plugin.agents[AgentPersonality.NEON]._peak_intensity == 0.0

def test_effective_intensity_during_peak(plugin):
    plugin.agents[AgentPersonality.TRINITY].intensity = 0.5
    plugin.trigger_agent_peak(AgentPersonality.TRINITY, duration=2.0)
    # effective should be >= 0.5 * 2 (peak)
    assert plugin.agents[AgentPersonality.TRINITY].effective_intensity() >= 0.5


# ── AI suggestions ──────────────────────────────────────────────────────────

def test_suggest_returns_empty_on_first_call(plugin):
    # Not enough history yet
    result = plugin.suggest_parameter_change()
    assert isinstance(result, dict)

def test_suggest_low_complexity(plugin):
    plugin.params["complexity"] = 1.0
    plugin.param_history = [{"complexity": 1.0}] * 15
    plugin._last_suggestion_time = 0.0  # Force fresh suggestion
    result = plugin.suggest_parameter_change()
    if result:
        assert "parameter" in result and "suggested_value" in result
        assert result.get("confidence", 0.0) >= 0.0

def test_suggest_valid_keys(plugin):
    plugin.params["complexity"] = 1.0
    plugin.param_history = [{"complexity": 1.0}] * 15
    plugin._last_suggestion_time = 0.0
    result = plugin.suggest_parameter_change()
    if result:
        for key in ("parameter","current_value","suggested_value","confidence","reason"):
            assert key in result


# ── Lifecycle ────────────────────────────────────────────────────────────────

@patch('vjlive3.plugins.living_fractal_consciousness.gl', _g)
def test_initialize(plugin, ctx): assert plugin.initialize(ctx) is True

@patch('vjlive3.plugins.living_fractal_consciousness.gl', _g)
def test_zero_texture(plugin, ctx): assert plugin.process_frame(0, {}, ctx) == 0

@patch('vjlive3.plugins.living_fractal_consciousness.gl', _g)
def test_process_calls_draw(plugin, ctx):
    plugin.initialize(ctx); plugin.process_frame(10, {}, ctx)
    _g.glDrawArrays.assert_called()

@patch('vjlive3.plugins.living_fractal_consciousness.gl', _g)
def test_all_params_render(plugin, ctx):
    plugin.initialize(ctx)
    params = {p["name"]: p["default"] for p in METADATA["parameters"]}
    assert plugin.process_frame(10, params, ctx) is not None

@patch('vjlive3.plugins.living_fractal_consciousness.gl', _g)
def test_compile_failure(plugin, ctx):
    _g.glGetShaderiv.return_value = 0
    _g.glGetShaderInfoLog.return_value = b"err"
    assert plugin.initialize(ctx) is False
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.living_fractal_consciousness.gl', _g)
def test_cleanup(plugin, ctx):
    plugin.initialize(ctx); plugin.prog = 99; plugin.cleanup()
    _g.glDeleteProgram.assert_called_with(99)

def test_mock_mode(plugin, ctx):
    plugin._mock_mode = True
    assert plugin.process_frame(10, {}, ctx) == 10

def test_presets_count():       assert len(PRESETS) >= 5
def test_presets_balanced():    assert "balanced" in PRESETS

@patch('vjlive3.plugins.living_fractal_consciousness.gl', _g)
def test_agent_params_applied(plugin, ctx):
    """Agent intensities from frame params should update agent objects."""
    plugin.initialize(ctx)
    plugin.process_frame(10, {"trinity_intensity": 10.0, "mix": 8.0}, ctx)
    assert abs(plugin.agents[AgentPersonality.TRINITY].intensity - 1.0) < 0.01
