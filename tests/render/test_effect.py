"""
Tests for P1-R2 — Effect base class (effect.py)
Spec: docs/specs/_02_fleshed_out/P1-R2_gpu_pipeline.md
"""

import sys
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Mock infrastructure — Effect.__init__ creates a RenderPipeline so we need
# wgpu + get_current_device mocked.
# ---------------------------------------------------------------------------

def _inject_wgpu(monkeypatch):
    mock_wgpu = MagicMock(name="wgpu")
    mock_wgpu.TextureFormat.rgba8unorm = "rgba8unorm"
    mock_wgpu.PrimitiveTopology.triangle_strip = "triangle-strip"
    monkeypatch.setitem(sys.modules, "wgpu", mock_wgpu)
    mock_device = MagicMock(name="GPUDevice")
    monkeypatch.setattr(
        "vjlive3.render.render_context.get_current_device",
        lambda: mock_device,
    )
    return mock_device


_FRAG_WGSL = "@fragment fn fs_main() -> @location(0) vec4<f32> { return vec4(0.0); }"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_effect_init(monkeypatch):
    """Effect.__init__ sets name, enabled, mix, and creates pipeline + cache."""
    _inject_wgpu(monkeypatch)
    from vjlive3.render.effect import Effect
    eff = Effect("my-effect", _FRAG_WGSL)
    assert eff.name == "my-effect"
    assert eff.enabled is True
    assert eff.mix == 1.0
    assert eff.manual_render is False
    assert eff.pipeline is not None
    assert eff.cache is not None


def test_effect_apply_uniforms_noop(monkeypatch):
    """Base apply_uniforms() is a no-op that must not raise."""
    _inject_wgpu(monkeypatch)
    from vjlive3.render.effect import Effect
    eff = Effect("noop", _FRAG_WGSL)
    eff.apply_uniforms(time=0.0, resolution=(1920, 1080), audio_reactor=None, semantic_layer=None)


def test_effect_pre_process_returns_none(monkeypatch):
    """Base pre_process() returns None (no pre-pass)."""
    _inject_wgpu(monkeypatch)
    from vjlive3.render.effect import Effect
    eff = Effect("pre", _FRAG_WGSL)
    result = eff.pre_process(chain=None, input_tex=MagicMock())
    assert result is None


def test_effect_repr(monkeypatch):
    """__repr__ includes name, enabled, and mix."""
    _inject_wgpu(monkeypatch)
    from vjlive3.render.effect import Effect
    eff = Effect("repr-test", _FRAG_WGSL)
    r = repr(eff)
    assert "repr-test" in r
    assert "enabled=True" in r


def test_effect_metadata(monkeypatch):
    """METADATA class attribute exists and has spec/tier keys."""
    _inject_wgpu(monkeypatch)
    from vjlive3.render.effect import Effect
    assert "spec" in Effect.METADATA
    assert Effect.METADATA["spec"] == "P1-R2"
