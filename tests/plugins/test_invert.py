"""
Tests for InvertEffect (plugins/invert.py).

No wgpu installation required — device, pipeline, and render_pass are all
mocked. Tests verify the draw() protocol contract and lazy-build behaviour.
"""

import sys
from unittest.mock import MagicMock, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_device():
    """Return a mock GPUDevice with realistic method returns."""
    device = MagicMock(name="GPUDevice")

    pipeline = MagicMock(name="GPURenderPipeline")
    bgl = MagicMock(name="BindGroupLayout")
    pipeline.get_bind_group_layout.return_value = bgl

    device.create_shader_module.return_value = MagicMock(name="ShaderModule")
    device.create_render_pipeline.return_value = pipeline
    device.create_sampler.return_value = MagicMock(name="Sampler")
    device.create_bind_group.return_value = MagicMock(name="BindGroup")

    return device, pipeline


def _inject_wgpu(monkeypatch):
    mock_wgpu = MagicMock(name="wgpu")
    mock_wgpu.TextureFormat.rgba8unorm = "rgba8unorm"
    mock_wgpu.PrimitiveTopology.triangle_strip = "triangle-strip"
    monkeypatch.setitem(sys.modules, "wgpu", mock_wgpu)
    return mock_wgpu


# ---------------------------------------------------------------------------
# InvertEffect tests
# ---------------------------------------------------------------------------

def test_invert_effect_enabled_by_default():
    """InvertEffect.enabled starts as True."""
    from vjlive3.plugins.invert import InvertEffect
    assert InvertEffect().enabled is True


def test_invert_effect_has_name():
    """InvertEffect.name is 'invert'."""
    from vjlive3.plugins.invert import InvertEffect
    assert InvertEffect.name == "invert"


def test_invert_effect_draw_builds_pipeline_lazily(monkeypatch):
    """
    _ensure_screen_blit_pipeline is called on first draw, result cached.
    Calling draw() twice only calls create_render_pipeline once.
    """
    _inject_wgpu(monkeypatch)
    from vjlive3.plugins.invert import InvertEffect

    device, pipeline = _make_device()
    render_pass = MagicMock(name="RenderPass")
    input_view = MagicMock(name="InputView")

    effect = InvertEffect()
    assert effect._gpu_pipeline is None  # not built yet

    effect.draw(render_pass, input_view, device)
    assert effect._gpu_pipeline is not None
    device.create_render_pipeline.assert_called_once()

    # second draw — pipeline already built, should not call create_render_pipeline again
    effect.draw(render_pass, input_view, device)
    device.create_render_pipeline.assert_called_once()  # still only once


def test_invert_effect_draw_sets_pipeline_on_render_pass(monkeypatch):
    """draw() calls render_pass.set_pipeline() with the compiled pipeline."""
    _inject_wgpu(monkeypatch)
    from vjlive3.plugins.invert import InvertEffect

    device, gpu_pipeline = _make_device()
    render_pass = MagicMock(name="RenderPass")

    effect = InvertEffect()
    effect.draw(render_pass, MagicMock(), device)

    render_pass.set_pipeline.assert_called_once_with(gpu_pipeline)


def test_invert_effect_draw_sets_bind_group_0(monkeypatch):
    """draw() calls render_pass.set_bind_group(0, bg) with the input texture."""
    _inject_wgpu(monkeypatch)
    from vjlive3.plugins.invert import InvertEffect

    device, _ = _make_device()
    bind_group = device.create_bind_group.return_value
    render_pass = MagicMock(name="RenderPass")

    effect = InvertEffect()
    effect.draw(render_pass, MagicMock(), device)

    render_pass.set_bind_group.assert_called_once_with(0, bind_group)


def test_invert_effect_draw_binds_input_view(monkeypatch):
    """draw() passes input_view as binding 0 in the bind group entries."""
    _inject_wgpu(monkeypatch)
    from vjlive3.plugins.invert import InvertEffect

    device, _ = _make_device()
    input_view = MagicMock(name="SpecificInputView")

    effect = InvertEffect()
    effect.draw(MagicMock(), input_view, device)

    # Inspect entries passed to create_bind_group
    _, kwargs = device.create_bind_group.call_args
    entries = kwargs.get("entries", device.create_bind_group.call_args[0][0] if device.create_bind_group.call_args[0] else [])
    # try keyword form first, fall back to checking call_args
    call_kwargs = device.create_bind_group.call_args.kwargs
    entries = call_kwargs.get("entries", [])
    binding0 = next((e for e in entries if e["binding"] == 0), None)
    assert binding0 is not None
    assert binding0["resource"] is input_view


def test_invert_effect_draw_creates_sampler(monkeypatch):
    """draw() creates a sampler during pipeline build."""
    _inject_wgpu(monkeypatch)
    from vjlive3.plugins.invert import InvertEffect

    device, _ = _make_device()
    effect = InvertEffect()
    effect.draw(MagicMock(), MagicMock(), device)

    device.create_sampler.assert_called_once()


def test_invert_effect_shader_compiles(monkeypatch):
    """create_shader_module is called with WGSL source during pipeline build."""
    _inject_wgpu(monkeypatch)
    from vjlive3.plugins.invert import InvertEffect, _INVERT_WGSL

    device, _ = _make_device()
    effect = InvertEffect()
    effect.draw(MagicMock(), MagicMock(), device)

    args, kwargs = device.create_shader_module.call_args
    code = kwargs.get("code", "")
    assert "@vertex" in code
    assert "@fragment" in code
    assert "1.0 - col" in code  # inversion formula present
