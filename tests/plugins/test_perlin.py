"""
Tests for PerlinEffect (plugins/perlin.py) — P3-EXT125.

All GPU objects are mocked.  Tests verify the public API contract,
parameter clamping, uniform packing, and the draw() protocol.
"""

import struct
import sys
from typing import Any
from unittest.mock import MagicMock, call

import pytest

# PerlinEffect lazy-imports wgpu only inside _ensure_pipeline(), so this
# import is safe even without wgpu installed in the test environment.
from vjlive3.plugins.perlin import PerlinEffect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _inject_wgpu(monkeypatch):
    mock_wgpu = MagicMock(name="wgpu")
    mock_wgpu.TextureFormat.rgba8unorm = "rgba8unorm"
    mock_wgpu.PrimitiveTopology.triangle_strip = "triangle-strip"
    mock_wgpu.BufferUsage.UNIFORM = 0x40
    mock_wgpu.BufferUsage.COPY_DST = 0x08
    monkeypatch.setitem(sys.modules, "wgpu", mock_wgpu)
    return mock_wgpu


def _make_device():
    device = MagicMock(name="GPUDevice")
    pipeline = MagicMock(name="GPURenderPipeline")
    pipeline.get_bind_group_layout.return_value = MagicMock()
    device.create_shader_module.return_value = MagicMock()
    device.create_render_pipeline.return_value = pipeline
    device.create_buffer.return_value = MagicMock(name="UniformBuf")
    device.create_bind_group.return_value = MagicMock(name="BindGroup")
    return device, pipeline


# ---------------------------------------------------------------------------
# Parameter tests
# ---------------------------------------------------------------------------

def test_default_parameters():
    """PerlinEffect initialises with spec-mandated defaults."""
    from vjlive3.plugins.perlin import PerlinEffect
    fx = PerlinEffect()
    assert fx.params["speed"]       == pytest.approx(0.6)
    assert fx.params["scale"]       == pytest.approx(2.0)
    assert fx.params["octaves"]     == pytest.approx(5.0)
    assert fx.params["persistence"] == pytest.approx(0.5)
    assert fx.params["ridging"]     == pytest.approx(0.0)
    assert fx.params["turbulence"]  == pytest.approx(0.0)
    assert fx.params["color_hue"]   == pytest.approx(0.0)
    assert fx.params["u_mix"]       == pytest.approx(1.0)


def test_enabled_by_default():
    from vjlive3.plugins.perlin import PerlinEffect
    assert PerlinEffect().enabled is True


def test_name():
    from vjlive3.plugins.perlin import PerlinEffect
    assert PerlinEffect.name == "perlin"


def test_get_state_returns_params():
    from vjlive3.plugins.perlin import PerlinEffect
    fx = PerlinEffect()
    fx.params["speed"] = 3.0
    state = fx.get_state()
    assert state["speed"] == pytest.approx(3.0)
    assert state is not fx.params  # must be a copy


def test_metadata_spec():
    from vjlive3.plugins.perlin import PerlinEffect
    assert PerlinEffect.METADATA["spec"] == "P3-EXT125"
    assert PerlinEffect.METADATA["category"] == "generators"


# ---------------------------------------------------------------------------
# apply_uniforms tests
# ---------------------------------------------------------------------------

def test_apply_uniforms_stores_time():
    from vjlive3.plugins.perlin import PerlinEffect
    fx = PerlinEffect()
    fx.apply_uniforms(time=42.5, resolution=(1920, 1080))
    assert fx._time == pytest.approx(42.5)


def test_apply_uniforms_stores_resolution():
    from vjlive3.plugins.perlin import PerlinEffect
    fx = PerlinEffect()
    fx.apply_uniforms(time=0.0, resolution=(1280, 720))
    assert fx._resolution == (1280.0, 720.0)


def test_apply_uniforms_accepts_audio_reactor():
    """apply_uniforms must accept audio_reactor kwarg without raising."""
    from vjlive3.plugins.perlin import PerlinEffect
    fx = PerlinEffect()
    fx.apply_uniforms(time=1.0, resolution=(640, 480), audio_reactor=MagicMock())


# ---------------------------------------------------------------------------
# _pack_uniforms tests (no GPU required)
# ---------------------------------------------------------------------------

def test_pack_uniforms_byte_length():
    from vjlive3.plugins.perlin import PerlinEffect, _UNIFORM_SIZE
    fx = PerlinEffect()
    raw = fx._pack_uniforms()
    assert len(raw) == _UNIFORM_SIZE == 48


def test_pack_uniforms_time_at_offset_0():
    from vjlive3.plugins.perlin import PerlinEffect
    fx = PerlinEffect()
    fx._time = 7.5
    raw = fx._pack_uniforms()
    (t,) = struct.unpack_from("f", raw, 0)
    assert t == pytest.approx(7.5, rel=1e-5)


def test_pack_uniforms_clamps_octaves_low():
    from vjlive3.plugins.perlin import PerlinEffect
    fx = PerlinEffect()
    fx.params["octaves"] = 0.0   # below minimum — should clamp to 1.0
    raw = fx._pack_uniforms()
    # octaves is packed at index 3 in the struct (4th float)
    (oct_val,) = struct.unpack_from("f", raw, 3 * 4)
    assert oct_val == pytest.approx(1.0)


def test_pack_uniforms_clamps_persistence_high():
    from vjlive3.plugins.perlin import PerlinEffect
    fx = PerlinEffect()
    fx.params["persistence"] = 2.5   # above maximum — should clamp to 1.0
    raw = fx._pack_uniforms()
    (per_val,) = struct.unpack_from("f", raw, 4 * 4)
    assert per_val == pytest.approx(1.0)


def test_pack_uniforms_clamps_scale_low():
    from vjlive3.plugins.perlin import PerlinEffect
    fx = PerlinEffect()
    fx.params["scale"] = -10.0   # below minimum — should clamp to 0.1
    raw = fx._pack_uniforms()
    (scale_val,) = struct.unpack_from("f", raw, 2 * 4)
    assert scale_val == pytest.approx(0.1, abs=0.01)


# ---------------------------------------------------------------------------
# draw() protocol tests
# ---------------------------------------------------------------------------

def test_draw_builds_pipeline_lazily(monkeypatch):
    _inject_wgpu(monkeypatch)
    device, _ = _make_device()
    fx = PerlinEffect()
    assert fx._gpu_pipeline is None

    fx.draw(MagicMock(), MagicMock(), device)
    assert fx._gpu_pipeline is not None
    device.create_render_pipeline.assert_called_once()


def test_draw_lazy_build_only_once(monkeypatch):
    _inject_wgpu(monkeypatch)
    device, _ = _make_device()
    fx = PerlinEffect()

    fx.draw(MagicMock(), MagicMock(), device)
    fx.draw(MagicMock(), MagicMock(), device)

    device.create_render_pipeline.assert_called_once()


def test_draw_creates_uniform_buffer(monkeypatch):
    _inject_wgpu(monkeypatch)
    device, _ = _make_device()
    PerlinEffect().draw(MagicMock(), MagicMock(), device)
    device.create_buffer.assert_called_once()


def test_draw_calls_write_buffer(monkeypatch):
    _inject_wgpu(monkeypatch)
    device, _ = _make_device()
    PerlinEffect().draw(MagicMock(), MagicMock(), device)
    device.queue.write_buffer.assert_called()


def test_draw_sets_pipeline_on_render_pass(monkeypatch):
    _inject_wgpu(monkeypatch)
    device, pipeline = _make_device()
    render_pass = MagicMock(name="RenderPass")
    PerlinEffect().draw(render_pass, MagicMock(), device)
    render_pass.set_pipeline.assert_called_once_with(pipeline)


def test_draw_sets_bind_group_0(monkeypatch):
    _inject_wgpu(monkeypatch)
    device, _ = _make_device()
    bg = device.create_bind_group.return_value
    render_pass = MagicMock(name="RenderPass")
    PerlinEffect().draw(render_pass, MagicMock(), device)
    render_pass.set_bind_group.assert_called_once_with(0, bg)


# ---------------------------------------------------------------------------
# Shader content tests
# ---------------------------------------------------------------------------

def test_get_fragment_shader_returns_string():
    from vjlive3.plugins.perlin import PerlinEffect
    shader = PerlinEffect().get_fragment_shader()
    assert isinstance(shader, str)
    assert len(shader) > 100


def test_shader_contains_perlin_function():
    from vjlive3.plugins.perlin import PerlinEffect
    shader = PerlinEffect().get_fragment_shader()
    assert "fn perlin(" in shader


def test_shader_contains_fractal_noise():
    from vjlive3.plugins.perlin import PerlinEffect
    shader = PerlinEffect().get_fragment_shader()
    assert "fn fractal_noise(" in shader


def test_shader_contains_uniform_struct():
    from vjlive3.plugins.perlin import PerlinEffect
    shader = PerlinEffect().get_fragment_shader()
    assert "struct Uniforms" in shader
    assert "u_time" in shader
    assert "u_speed" in shader
    assert "u_octaves" in shader


def test_shader_no_glsl_contamination():
    """Shader must not use GLSL-only builtins."""
    from vjlive3.plugins.perlin import PerlinEffect
    shader = PerlinEffect().get_fragment_shader()
    assert "gl_FragColor" not in shader
    assert "gl_Position" not in shader
    assert "#version" not in shader
    assert "uniform " not in shader  # GLSL uniform keyword (WGSL uses var<uniform>)


# Lazy import guard — PerlinEffect must be importable without wgpu installed
def test_import_without_wgpu(monkeypatch):
    """PerlinEffect.__init__ must not import wgpu at module load time."""
    monkeypatch.setitem(sys.modules, "wgpu", None)  # simulate missing wgpu
    # Remove cached module to force re-import check
    sys.modules.pop("vjlive3.plugins.perlin", None)
    from vjlive3.plugins.perlin import PerlinEffect  # must not raise
    fx = PerlinEffect()
    assert fx.params["speed"] == pytest.approx(0.6)
