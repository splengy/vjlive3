"""
Tests for P4-AU02: Audio Particle System.
OpenGL mocked before import; no coverage hang.
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import sys

# ── GL mock ─────────────────────────────────────────────────────────
_mock_gl = MagicMock()
_mock_gl.GL_VERTEX_SHADER    = 35633
_mock_gl.GL_FRAGMENT_SHADER  = 35632
_mock_gl.GL_COMPILE_STATUS   = 35713
_mock_gl.GL_LINK_STATUS      = 35714
_mock_gl.GL_TEXTURE_2D       = 3553
_mock_gl.GL_TRIANGLE_STRIP   = 5
_mock_gl.GL_FALSE = 0
_mock_gl.GL_TRUE  = 1
_mock_gl.glGetShaderiv.return_value  = 1
_mock_gl.glGetProgramiv.return_value = 1
_mock_gl.glCreateProgram.return_value = 99
_mock_gl.glGenVertexArrays.return_value = 44

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _mock_gl

from vjlive3.plugins.audio_particle_system import AudioParticleSystemPlugin, METADATA, MAX_PARTICLES, _map
from vjlive3.plugins.api import PluginContext


@pytest.fixture
def plugin():
    _mock_gl.reset_mock()
    _mock_gl.glGetShaderiv.return_value  = 1
    _mock_gl.glGetProgramiv.return_value = 1
    _mock_gl.glCreateProgram.return_value = 99
    _mock_gl.glGenVertexArrays.return_value = 44
    return AudioParticleSystemPlugin()


@pytest.fixture
def context():
    ctx = PluginContext(MagicMock())
    ctx.width  = 64
    ctx.height = 48
    ctx.time   = 1.0
    ctx.inputs = {"video_in": 10}
    ctx.outputs = {}
    return ctx


# ── Metadata ─────────────────────────────────────────────────────────

def test_metadata(plugin):
    m = plugin.get_metadata()
    assert m["name"] == "Audio Particle System"
    assert "video_in" in m["inputs"]
    assert "video_out" in m["outputs"]
    pnames = [p["name"] for p in m["parameters"]]
    assert "num_particles"     in pnames
    assert "particle_size"     in pnames
    assert "particle_speed"    in pnames
    assert "trail_length"      in pnames
    assert "color_sensitivity" in pnames


# ── Pure-Python helpers ───────────────────────────────────────────────

def test_map_limits(plugin):
    assert _map(0.0,  0.0, 1.0) == pytest.approx(0.0)
    assert _map(10.0, 0.0, 1.0) == pytest.approx(1.0)
    assert _map(5.0,  0.0, 10.0) == pytest.approx(5.0)
    # out-of-range clamped
    assert _map(-5.0, 0.0, 1.0) == pytest.approx(0.0)
    assert _map(15.0, 0.0, 1.0) == pytest.approx(1.0)

def test_allocate_particles(plugin):
    plugin._allocate_particles(20)
    assert plugin._n == 20
    assert plugin._positions.shape  == (20, 2)
    assert plugin._velocities.shape == (20, 2)
    assert plugin._energies.shape   == (20,)

def test_allocate_particles_bounded(plugin):
    plugin._allocate_particles(500)           # request too many
    assert plugin._n == MAX_PARTICLES         # clamped to 100

def test_allocate_particles_minimum(plugin):
    plugin._allocate_particles(0)             # below minimum
    assert plugin._n == 10                    # min is 10

def test_simulate_moves_particles(plugin):
    plugin._allocate_particles(10)
    old_pos = plugin._positions.copy()
    audio = {"bass": 0.8, "mid": 0.5, "treble": 0.3, "volume": 1.0}
    plugin._simulate(audio, particle_speed=1.0, time=0.0)
    # at least some positions should have changed
    assert not np.allclose(plugin._positions, old_pos)

def test_simulate_wraps_positions(plugin):
    plugin._allocate_particles(10)
    plugin._positions[:] = 2.0   # out of [0,1]
    audio = {"bass": 0.0, "mid": 0.0, "treble": 0.0, "volume": 0.0}
    plugin._simulate(audio, particle_speed=0.0, time=0.0)
    assert np.all(plugin._positions >= 0.0)
    assert np.all(plugin._positions <= 1.0)

def test_simulate_with_spectrum(plugin):
    plugin._allocate_particles(10)
    audio = {
        "bass": 0.5, "mid": 0.5, "treble": 0.5, "volume": 0.5,
        "spectrum": np.linspace(0.1, 1.0, 128),
    }
    plugin._simulate(audio, particle_speed=1.0, time=0.5)
    # energies should reflect audio
    assert np.any(plugin._energies[:10] > 0.0)


# ── GL tests ────────────────────────────────────────────────────────

@patch('vjlive3.plugins.audio_particle_system.gl', _mock_gl)
def test_initialize(plugin, context):
    assert plugin.initialize(context) is True
    assert plugin._initialized is True
    assert plugin.prog == 99
    assert plugin.vao  == 44

@patch('vjlive3.plugins.audio_particle_system.gl', _mock_gl)
def test_process_zero_input(plugin, context):
    plugin.initialize(context)
    assert plugin.process_frame(0, {}, context) == 0

@patch('vjlive3.plugins.audio_particle_system.gl', _mock_gl)
@patch('vjlive3.plugins.audio_particle_system.hasattr')
def test_mock_fallback(mock_hasattr, plugin, context):
    def chk(obj, attr): return False if attr == 'glCreateShader' else True
    mock_hasattr.side_effect = chk
    assert plugin.process_frame(10, {}, context) == 10

@patch('vjlive3.plugins.audio_particle_system.gl', _mock_gl)
def test_process_with_audio(plugin, context):
    plugin.initialize(context)
    context.inputs["audio_data"] = {
        "bass": 0.8, "mid": 0.5, "treble": 0.3, "volume": 0.9,
        "spectrum": np.linspace(0.1, 1.0, 128),
    }
    params = {"num_particles": 3.0, "particle_size": 5.0, "particle_speed": 5.0,
              "trail_length": 8.0, "color_sensitivity": 5.0}
    res = plugin.process_frame(10, params, context)
    assert res == 10
    _mock_gl.glDrawArrays.assert_called_once()

@patch('vjlive3.plugins.audio_particle_system.gl', _mock_gl)
def test_compile_failure(plugin, context):
    _mock_gl.glGetShaderiv.return_value = 0
    _mock_gl.glGetShaderInfoLog.return_value = b"Error"
    assert plugin.initialize(context) is False
    assert plugin._mock_mode is True
    _mock_gl.glGetShaderiv.return_value = 1

@patch('vjlive3.plugins.audio_particle_system.gl', _mock_gl)
def test_cleanup(plugin, context):
    plugin.initialize(context)
    plugin.prog = 99
    plugin.vao  = 44
    plugin.cleanup()
    _mock_gl.glDeleteProgram.assert_called_once_with(99)
