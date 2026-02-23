"""
Tests for P3-EXT185-191: VAttractorsPlugin (Lorenz, Halvorsen, Thomas, Sakarya, Languor).
"""
import math
import sys
from unittest.mock import MagicMock, patch

import pytest

# ── GL stub ──────────────────────────────────────────────────────────────────
gl_stub = MagicMock()
gl_stub.glCreateShader.return_value = 1
gl_stub.glCreateProgram.return_value = 1
gl_stub.glGetShaderiv.return_value   = 1
gl_stub.glGetProgramiv.return_value  = 1
gl_stub.glGenVertexArrays.return_value = 1
gl_stub.glGenBuffers.return_value    = 1
gl_stub.GL_VERTEX_SHADER             = 0x8B31
gl_stub.GL_FRAGMENT_SHADER           = 0x8B30
gl_stub.GL_COMPILE_STATUS            = 0x8B81
gl_stub.GL_LINK_STATUS               = 0x8B82
gl_stub.GL_ARRAY_BUFFER              = 0x8892
gl_stub.GL_DYNAMIC_DRAW              = 0x88E8
gl_stub.GL_POINTS                    = 0x0000
gl_stub.GL_TRIANGLE_STRIP            = 0x0005
gl_stub.GL_FLOAT                     = 0x1406
gl_stub.GL_FALSE                     = 0
gl_stub.GL_BLEND                     = 0x0BE2
gl_stub.GL_SRC_ALPHA                 = 0x0302
gl_stub.GL_ONE                       = 1
gl_stub.GL_PROGRAM_POINT_SIZE        = 0x8642
gl_stub.GL_TEXTURE0                  = 0x84C0
gl_stub.GL_TEXTURE_2D                = 0x0DE1

sys.modules.setdefault('OpenGL', MagicMock())
sys.modules.setdefault('OpenGL.GL', gl_stub)

from vjlive3.plugins.vattractors import (  # noqa: E402
    VAttractorsPlugin, _Lorenz, _Halvorsen, _Thomas, _Sakarya,
    _normalize, VLorenzPlugin, VHalvorsenPlugin, VThomasPlugin, VSakaryaPlugin,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Attractor integrators (CPU)
# ─────────────────────────────────────────────────────────────────────────────

class TestAttractorModels:
    def test_lorenz_diverges(self):
        a = _Lorenz()
        x0, y0, z0 = a.x, a.y, a.z
        for _ in range(50): a.step(0.01)
        assert (a.x, a.y, a.z) != (x0, y0, z0)

    def test_halvorsen_evolves(self):
        a = _Halvorsen()
        x0 = a.x
        for _ in range(20): a.step(0.01)
        assert a.x != x0

    def test_thomas_periodic_chaos(self):
        a = _Thomas()
        for _ in range(100): a.step(0.01)
        # Thomas attractor stays bounded
        assert abs(a.x) < 100 and abs(a.y) < 100

    def test_sakarya_evolves(self):
        a = _Sakarya()
        x0 = a.x
        for _ in range(30): a.step(0.01)
        assert a.x != x0

    def test_normalize_clamped(self):
        assert _normalize(1000) == 1.0
        assert _normalize(-1000) == 0.0
        assert 0.0 <= _normalize(0.0) <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
#  Plugin lifecycle
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def plugin():
    p = VAttractorsPlugin()
    p._mock = True  # force headless
    return p

@pytest.fixture
def ctx():
    c = MagicMock()
    c.width = 1920; c.height = 1080
    c.outputs = {}
    return c


class TestVAttractorsPluginLifecycle:
    def test_metadata(self, plugin):
        m = plugin.get_metadata()
        assert m['name'] == 'V-Attractors'
        assert 'lorenz' in m['tags']

    def test_initialize_returns_true(self, plugin, ctx):
        assert plugin.initialize(ctx)

    def test_process_zero_texture(self, plugin, ctx):
        assert plugin.process_frame(0, {}, ctx) == 0

    def test_process_returns_texture(self, plugin, ctx):
        result = plugin.process_frame(42, {'mode': 0.0, 'speed': 5.0}, ctx)
        assert result == 42

    def test_trail_grows(self, plugin, ctx):
        plugin.initialize(ctx)
        for i in range(10):
            plugin.process_frame(1, {'trail': 10.0, 'mode': 0.0}, ctx)
        assert len(plugin._trail) <= 2048
        assert len(plugin._trail) >= 1

    def test_trail_bounded(self, plugin, ctx):
        plugin.initialize(ctx)
        for i in range(300):
            plugin.process_frame(1, {'trail': 1.0, 'mode': 0.0}, ctx)
        # trail_len with trail=1.0 → 1/10*2048 ≈ 204
        assert len(plugin._trail) <= 2048


# ─────────────────────────────────────────────────────────────────────────────
#  All 5 modes
# ─────────────────────────────────────────────────────────────────────────────

class TestAllModes:
    @pytest.mark.parametrize("mode", [0, 1, 2, 3, 4])
    def test_mode_runs(self, mode, ctx):
        p = VAttractorsPlugin(); p._mock = True; p.initialize(ctx)
        r = p.process_frame(7, {'mode': float(mode), 'speed': 5.0}, ctx)
        assert r == 7

    def test_mode_steps_different_attractor(self):
        """Lorenz and Thomas should produce different trajectories."""
        p1 = VAttractorsPlugin(); p1._mock = True
        p2 = VAttractorsPlugin(); p2._mock = True
        ctx = MagicMock(); ctx.width = 640; ctx.height = 480; ctx.outputs = {}
        p1.initialize(ctx); p2.initialize(ctx)
        for _ in range(20):
            p1.process_frame(1, {'mode': 0.0}, ctx)
            p2.process_frame(1, {'mode': 2.0}, ctx)
        # Trails differ
        assert p1._trail[-1] != p2._trail[-1]


# ─────────────────────────────────────────────────────────────────────────────
#  Compat aliases
# ─────────────────────────────────────────────────────────────────────────────

class TestCompatAliases:
    def test_lorenz_alias(self):
        assert VLorenzPlugin is VAttractorsPlugin

    def test_halvorsen_alias(self):
        assert VHalvorsenPlugin is VAttractorsPlugin

    def test_thomas_alias(self):
        assert VThomasPlugin is VAttractorsPlugin

    def test_sakarya_alias(self):
        assert VSakaryaPlugin is VAttractorsPlugin


# ─────────────────────────────────────────────────────────────────────────────
#  Cleanup
# ─────────────────────────────────────────────────────────────────────────────

class TestCleanup:
    def test_cleanup_after_init(self, plugin, ctx):
        plugin.initialize(ctx)
        plugin.cleanup()  # should not raise
        assert plugin._prog_pass == 0 and plugin._prog_pts == 0

    def test_cleanup_without_init(self):
        p = VAttractorsPlugin()
        p.cleanup()   # should not raise
