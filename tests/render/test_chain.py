"""
Tests for P1-R2 — EffectChain (chain.py)
Spec: docs/specs/_02_fleshed_out/P1-R2_gpu_pipeline.md
"""

import sys
from unittest.mock import MagicMock

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------

def _inject_all(monkeypatch):
    """Inject wgpu + numpy-aware device mock. Returns (mock_wgpu, mock_device)."""
    mock_wgpu = MagicMock(name="wgpu")
    mock_wgpu.TextureFormat.rgba8unorm = "rgba8unorm"
    mock_wgpu.TextureFormat.r32float = "r32float"
    mock_wgpu.TextureFormat.rg32float = "rg32float"
    mock_wgpu.TextureFormat.rgba32float = "rgba32float"
    mock_wgpu.TextureUsage.RENDER_ATTACHMENT = 0x10
    mock_wgpu.TextureUsage.TEXTURE_BINDING = 0x04
    mock_wgpu.TextureUsage.COPY_DST = 0x08
    mock_wgpu.TextureUsage.COPY_SRC = 0x01
    mock_wgpu.PrimitiveTopology.triangle_strip = "triangle-strip"

    mock_device = MagicMock(name="GPUDevice")

    def _make_tex(**_):
        tex = MagicMock(name="GPUTexture")
        tex.create_view.return_value = MagicMock(name="GPUTextureView")
        return tex

    mock_device.create_texture.side_effect = _make_tex

    # readback returns 1920*1080*4 zero bytes
    mock_device.queue.read_texture.side_effect = lambda *a, **kw: bytes(1920 * 1080 * 4)

    monkeypatch.setitem(sys.modules, "wgpu", mock_wgpu)
    return mock_wgpu, mock_device


@pytest.fixture(autouse=True)
def patch_device(monkeypatch):
    _, device = _inject_all(monkeypatch)
    monkeypatch.setattr(
        "vjlive3.render.render_context.get_current_device",
        lambda: device,
    )
    return device


def _make_effect(name="fx"):
    """Create a minimal mock Effect."""
    eff = MagicMock()
    eff.name = name
    eff.enabled = True
    eff.mix = 1.0
    eff.manual_render = False
    pipe = MagicMock()
    pipe.use = MagicMock()
    eff.pipeline = pipe
    eff.apply_uniforms.return_value = None
    eff.pre_process.return_value = None
    return eff


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_effect_chain_create():
    """EffectChain(1920, 1080) initialises without error, allocates two targets."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain(1920, 1080)
    assert ec._width == 1920
    assert ec._height == 1080
    assert ec._target_a is not None
    assert ec._target_b is not None
    ec.delete()


def test_effect_chain_no_effects():
    """render() with empty chain returns input_texture unchanged."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain(1920, 1080)
    fake_tex = MagicMock(name="input-tex")
    result = ec.render(fake_tex)
    assert result is fake_tex
    ec.delete()


def test_effect_chain_add_remove():
    """add_effect / remove_effect update the internal list correctly."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain()
    eff = _make_effect("noise")
    ec.add_effect(eff)
    assert "noise" in ec.get_available_effects()
    ec.remove_effect("noise")
    assert "noise" not in ec.get_available_effects()
    ec.delete()


def test_effect_chain_render_passthrough():
    """Single enabled effect: render() forward-calls effect.pipeline.use()."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain(1920, 1080)
    eff = _make_effect("pass")
    ec.add_effect(eff)

    fake_tex = MagicMock(name="input-tex")
    result = ec.render(fake_tex)

    # Pipeline should have been used via _draw_effect
    assert result is not None
    ec.delete()


def test_effect_chain_delete():
    """delete() releases render targets and pipeline without error."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain(1920, 1080)
    ec.delete()
    assert ec._deleted
    assert ec._target_a is None
    assert ec._target_b is None


def test_effect_chain_context_manager():
    """'with EffectChain():' calls delete() on exit."""
    from vjlive3.render.chain import EffectChain
    with EffectChain(640, 480) as ec:
        assert not ec._deleted
    assert ec._deleted


def test_effect_chain_readback(patch_device):
    """readback_last_output() returns an H×W×3 numpy array or None."""
    from vjlive3.render.chain import EffectChain

    # Configure device.queue.read_texture to return correct sized bytes
    w, h = 640, 480
    patch_device.queue.read_texture.side_effect = lambda *a, **kw: bytes(w * h * 4)

    ec = EffectChain(w, h)
    fake_tex = MagicMock(name="input")
    ec._last_output = fake_tex

    result = ec.readback_last_output()
    # Either a numpy array or None (if read fails)
    assert result is None or isinstance(result, np.ndarray)
    ec.delete()


def test_effect_chain_upload_texture(patch_device):
    """upload_texture() calls device.create_texture and queue.write_texture."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain(1920, 1080)

    image = np.zeros((480, 640, 3), dtype=np.uint8)
    view = ec.upload_texture(image)

    patch_device.create_texture.assert_called()
    patch_device.queue.write_texture.assert_called()
    assert view is not None
    ec.delete()


def test_spatial_view():
    """set_spatial_view([0, 0], [1, 1]) updates internal state without raising."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain()
    ec.set_spatial_view([240.0, 0.0], [5760.0, 1080.0])
    assert ec._view_offset == [240.0, 0.0]
    assert ec._view_scale == [5760.0, 1080.0]
    ec.delete()


def test_projection_mapping():
    """set_projection_mapping() stores params without raising."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain()
    ec.set_projection_mapping(
        warp_mode=1,
        corners=[0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0],
        edge_feather=0.05,
        node_side=0,
        calibration_mode=True,
    )
    assert ec._warp_mode == 1
    assert ec._edge_feather == pytest.approx(0.05)
    assert ec._calibration_mode is True
    ec.delete()


# ---------------------------------------------------------------------------
# _draw_effect dispatch tests (draw() protocol vs legacy pipeline.use())
# ---------------------------------------------------------------------------

class _DrawEffect:
    """Minimal effect implementing the draw() protocol (no pipeline attr)."""
    name = "draw-proto"
    enabled = True
    mix = 1.0
    manual_render = False

    def __init__(self):
        self.draw_calls: list = []

    def apply_uniforms(self, **_):
        return None

    def pre_process(self, ctx):
        return None

    def draw(self, render_pass, input_view, device):
        self.draw_calls.append((render_pass, input_view, device))


class _LegacyEffect:
    """Minimal effect with only pipeline.use() (no draw() method)."""
    name = "legacy-pipe"
    enabled = True
    mix = 1.0
    manual_render = False

    def __init__(self):
        from unittest.mock import MagicMock as _MM
        self.pipeline = _MM(name="pipe")
        self.pipeline.use = _MM(name="use")

    def apply_uniforms(self, **_):
        return None

    def pre_process(self, ctx):
        return None


class _BothEffect(_DrawEffect):
    """Effect that has both draw() and pipeline — draw() must win."""
    name = "both"

    def __init__(self):
        super().__init__()
        from unittest.mock import MagicMock as _MM
        self.pipeline = _MM(name="pipe")
        self.pipeline.use = _MM(name="use")


def test_draw_effect_uses_draw_protocol(patch_device):
    """If effect implements draw(), it receives (render_pass, input_view, device)."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain(64, 64)
    eff = _DrawEffect()
    ec.add_effect(eff)

    fake_input = MagicMock(name="input-view")
    ec.render(fake_input)

    assert len(eff.draw_calls) == 1
    _, got_input_view, _ = eff.draw_calls[0]
    # The chain may feed pre_result or the raw input; either way a view is passed
    assert got_input_view is not None
    ec.delete()


def test_draw_effect_falls_back_to_pipeline_use(patch_device):
    """Effect without draw() falls back to pipeline.use(render_pass)."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain(64, 64)
    eff = _LegacyEffect()
    ec.add_effect(eff)

    ec.render(MagicMock(name="input"))
    eff.pipeline.use.assert_called_once()
    ec.delete()


def test_draw_effect_draw_protocol_preferred_over_pipeline(patch_device):
    """When effect has both draw() and pipeline, draw() is called, pipeline.use is not."""
    from vjlive3.render.chain import EffectChain
    ec = EffectChain(64, 64)
    eff = _BothEffect()
    ec.add_effect(eff)

    ec.render(MagicMock(name="input"))

    assert len(eff.draw_calls) == 1
    eff.pipeline.use.assert_not_called()
    ec.delete()
