"""
Tests for P3-EXT040: DepthAcidFractalDatamoshPlugin.
"""
import sys
from unittest.mock import MagicMock

import pytest

# ── GL stub ──────────────────────────────────────────────────────────────────
gl_stub = MagicMock()
gl_stub.glCreateShader.return_value  = 1
gl_stub.glCreateProgram.return_value = 1
gl_stub.glGetShaderiv.return_value   = 1
gl_stub.glGetProgramiv.return_value  = 1
gl_stub.glGenVertexArrays.return_value = 1
gl_stub.glGenTextures.return_value   = 1
gl_stub.glGenFramebuffers.return_value = 1
gl_stub.GL_VERTEX_SHADER   = 0x8B31
gl_stub.GL_FRAGMENT_SHADER = 0x8B30
gl_stub.GL_COMPILE_STATUS  = 0x8B81
gl_stub.GL_LINK_STATUS     = 0x8B82
gl_stub.GL_RGBA8           = 0x8058
gl_stub.GL_RGBA            = 0x1908
gl_stub.GL_UNSIGNED_BYTE   = 0x1401
gl_stub.GL_TEXTURE_2D      = 0x0DE1
gl_stub.GL_TEXTURE_MIN_FILTER = 0x2801
gl_stub.GL_TEXTURE_MAG_FILTER = 0x2800
gl_stub.GL_LINEAR          = 0x2601
gl_stub.GL_FRAMEBUFFER     = 0x8D40
gl_stub.GL_COLOR_ATTACHMENT0 = 0x8CE0
gl_stub.GL_READ_FRAMEBUFFER  = 0x8CA8
gl_stub.GL_DRAW_FRAMEBUFFER  = 0x8CA9
gl_stub.GL_COLOR_BUFFER_BIT  = 0x4000
gl_stub.GL_NEAREST         = 0x2600
gl_stub.GL_TRIANGLE_STRIP  = 0x0005
gl_stub.GL_TEXTURE0        = 0x84C0
gl_stub.GL_TEXTURE1        = 0x84C1
gl_stub.GL_TEXTURE2        = 0x84C2

sys.modules.setdefault('OpenGL', MagicMock())
sys.modules.setdefault('OpenGL.GL', gl_stub)

from vjlive3.plugins.depth_acid_fractal_datamosh import (  # noqa: E402
    DepthAcidFractalDatamoshPlugin, DepthAcidFractalDatamoshEffect,
    METADATA, PRESETS,
)


@pytest.fixture
def plugin():
    p = DepthAcidFractalDatamoshPlugin()
    p._mock = True
    return p

@pytest.fixture
def ctx():
    c = MagicMock()
    c.width = 1920; c.height = 1080
    c.time = 0.0
    c.inputs = {}
    c.outputs = {}
    return c


class TestMetadata:
    def test_name(self, plugin):
        assert 'Acid Fractal' in plugin.get_metadata()['name']

    def test_has_presets(self):
        assert 'microdose' in PRESETS
        assert 'dimensional_rift' in PRESETS

    def test_preset_has_keys(self):
        for p in PRESETS.values():
            assert 'fractal_intensity' in p
            assert 'neon_boost' in p

    def test_metadata_tags(self):
        assert 'julia' in METADATA['tags']
        assert 'depth' in METADATA['tags']


class TestLifecycle:
    def test_initialize_mock(self, plugin, ctx):
        assert plugin.initialize(ctx)
        assert plugin._initialized

    def test_process_zero(self, plugin, ctx):
        plugin.initialize(ctx)
        assert plugin.process_frame(0, {}, ctx) == 0

    def test_process_passthrough_mock(self, plugin, ctx):
        plugin.initialize(ctx)
        assert plugin.process_frame(99, {}, ctx) == 99

    def test_output_set(self, plugin, ctx):
        plugin.initialize(ctx)
        plugin.process_frame(42, {}, ctx)
        assert ctx.outputs.get('video_out') == 42

    def test_cleanup_noop(self, plugin, ctx):
        plugin.initialize(ctx)
        plugin.cleanup()
        assert plugin._prog == 0


class TestParams:
    def test_default_params_passthrough(self, plugin, ctx):
        plugin.initialize(ctx)
        r = plugin.process_frame(1, {}, ctx)
        assert r == 1

    def test_all_presets_valid(self, ctx):
        for name, p in PRESETS.items():
            plugin = DepthAcidFractalDatamoshPlugin()
            plugin._mock = True
            plugin.initialize(ctx)
            r = plugin.process_frame(5, p, ctx)
            assert r == 5, f"Preset '{name}' failed"

    @pytest.mark.parametrize("key,val", [
        ('fractal_intensity', 10.0),
        ('prism_split', 10.0),
        ('solarize', 10.0),
        ('neon_boost', 10.0),
        ('feedback', 10.0),
    ])
    def test_extreme_params(self, plugin, ctx, key, val):
        plugin.initialize(ctx)
        r = plugin.process_frame(3, {key: val}, ctx)
        assert r == 3


class TestCompatAlias:
    def test_alias(self):
        assert DepthAcidFractalDatamoshEffect is DepthAcidFractalDatamoshPlugin


class TestMultipleFrames:
    def test_runs_100_frames(self, plugin, ctx):
        plugin.initialize(ctx)
        for i in range(100):
            ctx.time = float(i) * 0.016
            r = plugin.process_frame(1, {}, ctx)
            assert r == 1
