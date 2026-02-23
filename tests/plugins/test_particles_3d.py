"""Tests for P3-EXT003: Advanced Particle 3D System (AdvancedParticle3DPlugin)."""
import sys, pytest
from unittest.mock import MagicMock, patch, call
import numpy as np

# ── GL mock ───────────────────────────────────────────────────────────────────
_g = MagicMock()
_g.glGetShaderiv.return_value   = 1
_g.glGetProgramiv.return_value  = 1
_g.glCreateProgram.return_value = 99
_g.glGenVertexArrays.return_value = 44
_g.glGenBuffers.return_value    = 55
_g.glGenFramebuffers.return_value = 51
_g.glGenTextures.return_value   = 101
for attr in ("GL_VERTEX_SHADER","GL_FRAGMENT_SHADER","GL_COMPILE_STATUS","GL_LINK_STATUS",
             "GL_TEXTURE_2D","GL_RGBA","GL_UNSIGNED_BYTE","GL_LINEAR","GL_LINEAR_MIPMAP_LINEAR",
             "GL_CLAMP_TO_EDGE","GL_TEXTURE_MIN_FILTER","GL_TEXTURE_MAG_FILTER",
             "GL_TEXTURE_WRAP_S","GL_TEXTURE_WRAP_T","GL_FRAMEBUFFER","GL_COLOR_ATTACHMENT0",
             "GL_COLOR_BUFFER_BIT","GL_TRIANGLE_STRIP","GL_POINTS","GL_ARRAY_BUFFER",
             "GL_STREAM_DRAW","GL_FLOAT","GL_FALSE","GL_BLEND","GL_SRC_ALPHA","GL_ONE",
             "GL_PROGRAM_POINT_SIZE"):
    setattr(_g, attr, MagicMock())
_g.GL_FALSE = 0

sys.modules['OpenGL']    = MagicMock()
sys.modules['OpenGL.GL'] = _g

from vjlive3.plugins.particles_3d import (
    AdvancedParticle3DPlugin, METADATA, PRESETS,
    _perspective, _rotation_x, _rotation_y, _mat4_mul
)


@pytest.fixture(autouse=True)
def reset_gl():
    _g.reset_mock()
    _g.glGetShaderiv.return_value   = 1
    _g.glGetProgramiv.return_value  = 1
    _g.glCreateProgram.return_value = 99
    _g.glGenVertexArrays.return_value = 44
    _g.glGenBuffers.return_value    = 55
    _g.glGenFramebuffers.return_value = 51
    _g.glGenTextures.return_value   = 101


@pytest.fixture
def plugin(): return AdvancedParticle3DPlugin()


@pytest.fixture
def ctx():
    c = MagicMock()(MagicMock())
    c.width = 64; c.height = 48; c.time = 0.0
    c.inputs = {"video_in": 10}; c.outputs = {}
    return c


# ── Metadata ──────────────────────────────────────────────────────────────────

def test_metadata_name():       assert METADATA["name"] == "Advanced Particle 3D"
def test_metadata_22_params():  assert len(METADATA["parameters"]) == 22  # 21 system + mix
def test_metadata_min_max():
    for p in METADATA["parameters"]:
        assert p["min"] == 0.0 and p["max"] == 10.0
def test_presets_count():       assert len(PRESETS) == 5


# ── Math helpers ──────────────────────────────────────────────────────────────

def test_perspective_returns_16():  assert len(_perspective(60, 1.0, 0.1, 100.0)) == 16
def test_rotation_x_returns_16():   assert len(_rotation_x(0.0)) == 16
def test_rotation_y_returns_16():   assert len(_rotation_y(0.0)) == 16
def test_mat4_mul_identity():
    I = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
    result = _mat4_mul(I, I)
    assert abs(result[0] - 1.0) < 1e-6
    assert abs(result[5] - 1.0) < 1e-6


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@patch('vjlive3.plugins.particles_3d.gl', _g)
def test_initialize(plugin, ctx):
    assert plugin.initialize(ctx) is True
    assert plugin._initialized is True

@patch('vjlive3.plugins.particles_3d.gl', _g)
def test_zero_texture_returns_zero(plugin, ctx):
    plugin.initialize(ctx)
    assert plugin.process_frame(0, {}, ctx) == 0

@patch('vjlive3.plugins.particles_3d.gl', _g)
def test_process_frame_draws_points(plugin, ctx):
    plugin.initialize(ctx)
    plugin.process_frame(10, {}, ctx)
    _g.glDrawArrays.assert_called()

@patch('vjlive3.plugins.particles_3d.gl', _g)
def test_process_sets_video_out(plugin, ctx):
    plugin.initialize(ctx)
    plugin.process_frame(10, {}, ctx)
    assert 'video_out' in ctx.outputs

@patch('vjlive3.plugins.particles_3d.gl', _g)
def test_all_params(plugin, ctx):
    plugin.initialize(ctx)
    params = {p["name"]: p["default"] for p in METADATA["parameters"]}
    assert plugin.process_frame(10, params, ctx) is not None

@patch('vjlive3.plugins.particles_3d.gl', _g)
def test_compile_failure(plugin, ctx):
    _g.glGetShaderiv.return_value = 0
    _g.glGetShaderInfoLog.return_value = b"err"
    assert plugin.initialize(ctx) is False
    assert plugin._mock_mode is True

@patch('vjlive3.plugins.particles_3d.gl', _g)
def test_cleanup(plugin, ctx):
    plugin.initialize(ctx)
    plugin.prog_particle = 99; plugin.prog_composite = 100
    plugin.cleanup()
    _g.glDeleteProgram.assert_any_call(99)
    _g.glDeleteProgram.assert_any_call(100)

def test_mock_mode(plugin, ctx):
    plugin._mock_mode = True
    assert plugin.process_frame(10, {}, ctx) == 10
    assert ctx.outputs.get('video_out') == 10


# ── Physics ───────────────────────────────────────────────────────────────────

def test_physics_gravity_pulls_down():
    p = AdvancedParticle3DPlugin()
    p._alloc_particles(10)
    p._positions[:, :] = 0.0; p._velocities[:, :] = 0.0; p._lifetimes[:] = 1.0
    p._update_physics(10, {"gravity": 10.0, "emit_spread": 0.0, "lifetime": 5.0}, 0.1, 0.0)
    assert np.all(p._velocities[:, 1] < 0)  # Y should be decreasing (gravity pulls down)

def test_physics_respawn_dead():
    p = AdvancedParticle3DPlugin()
    p._alloc_particles(5)
    p._lifetimes[:] = 0.0   # All dead
    p._update_physics(5, {"gravity": 0.0, "emit_spread": 1.0, "lifetime": 5.0}, 0.016, 0.0)
    assert np.all(p._lifetimes[:5] > 0.9)   # All respawned (slightly < 1 due to age increment)

def test_alloc_particles():
    p = AdvancedParticle3DPlugin()
    p._alloc_particles(100)
    assert p._positions.shape  == (100, 3)
    assert p._velocities.shape == (100, 3)
    assert p._lifetimes.shape  == (100,)
    assert p._ages.shape       == (100,)
