"""
Tests for P1-R2 — RenderTarget (framebuffer.py)
Spec: docs/specs/_02_fleshed_out/P1-R2_gpu_pipeline.md
"""

import sys
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------

def _inject_wgpu(monkeypatch):
    """Inject wgpu mock and return (mock_wgpu, mock_device)."""
    mock_wgpu = MagicMock(name="wgpu")
    mock_wgpu.TextureFormat.rgba8unorm = "rgba8unorm"
    mock_wgpu.TextureUsage.RENDER_ATTACHMENT = 0x10
    mock_wgpu.TextureUsage.TEXTURE_BINDING = 0x04
    mock_wgpu.TextureUsage.COPY_SRC = 0x01

    mock_device = MagicMock(name="GPUDevice")
    mock_tex = MagicMock(name="GPUTexture")
    mock_view = MagicMock(name="GPUTextureView")
    mock_tex.create_view.return_value = mock_view
    mock_device.create_texture.return_value = mock_tex

    monkeypatch.setitem(sys.modules, "wgpu", mock_wgpu)
    return mock_wgpu, mock_device, mock_tex, mock_view


@pytest.fixture(autouse=True)
def patch_device(monkeypatch, request):
    """Patch get_current_device for every test in this module."""
    _, device, *_ = _inject_wgpu(monkeypatch)
    monkeypatch.setattr(
        "vjlive3.render.render_context.get_current_device",
        lambda: device
    )
    request.node._mock_device = device
    return device


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_render_target_create():
    """RenderTarget(1920, 1080) constructs without error, calls create_texture."""
    from vjlive3.render.framebuffer import RenderTarget
    rt = RenderTarget(1920, 1080)
    assert rt.width == 1920
    assert rt.height == 1080
    assert rt.texture is not None
    rt.delete()


def test_render_target_bind_unbind():
    """bind() and unbind() can be called without raising."""
    from vjlive3.render.framebuffer import RenderTarget
    encoder = MagicMock(name="encoder")
    rt = RenderTarget(800, 600)
    rt.bind(encoder)
    rt.unbind(encoder)
    rt.delete()


def test_render_target_context_manager():
    """'with RenderTarget(...)' calls delete() on exit."""
    from vjlive3.render.framebuffer import RenderTarget
    with RenderTarget(640, 480) as rt:
        assert not rt._deleted
    assert rt._deleted


def test_render_target_double_delete():
    """Calling delete() twice is a silent no-op."""
    from vjlive3.render.framebuffer import RenderTarget
    rt = RenderTarget(256, 256)
    rt.delete()
    rt.delete()  # must not raise


def test_render_target_incomplete_raises():
    """Invalid dimensions (0 or negative) raise RuntimeError."""
    from vjlive3.render.framebuffer import RenderTarget
    with pytest.raises(RuntimeError, match="invalid dimensions"):
        RenderTarget(0, 1080)
    with pytest.raises(RuntimeError, match="invalid dimensions"):
        RenderTarget(1920, -1)
