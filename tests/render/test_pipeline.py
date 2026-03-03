"""
Tests for P1-R2 — RenderPipeline (program.py)
Spec: docs/specs/_02_fleshed_out/P1-R2_gpu_pipeline.md
"""

import sys
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------

def _inject_wgpu(monkeypatch):
    mock_wgpu = MagicMock(name="wgpu")
    mock_wgpu.TextureFormat.rgba8unorm = "rgba8unorm"
    mock_wgpu.PrimitiveTopology.triangle_strip = "triangle-strip"

    mock_device = MagicMock(name="GPUDevice")
    monkeypatch.setitem(sys.modules, "wgpu", mock_wgpu)
    return mock_wgpu, mock_device


@pytest.fixture(autouse=True)
def patch_device(monkeypatch):
    _, device = _inject_wgpu(monkeypatch)
    monkeypatch.setattr(
        "vjlive3.render.render_context.get_current_device",
        lambda: device,
    )
    return device


_GOOD_WGSL = """
@vertex
fn vs_main(@builtin(vertex_index) vid: u32) -> @builtin(position) vec4<f32> {
    return vec4<f32>(0.0, 0.0, 0.0, 1.0);
}

@fragment
fn fs_main() -> @location(0) vec4<f32> {
    return vec4<f32>(1.0, 0.0, 0.0, 1.0);
}
"""

_BAD_WGSL = "this is not valid WGSL at all"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_pipeline_compile_passthrough():
    """RenderPipeline(PASSTHROUGH_WGSL) succeeds with mocked device."""
    from vjlive3.render.program import RenderPipeline, BASE_VERTEX_SHADER, PASSTHROUGH_FRAGMENT
    src = BASE_VERTEX_SHADER + "\n" + PASSTHROUGH_FRAGMENT
    rp = RenderPipeline(src, name="passthrough")
    assert rp.name == "passthrough"
    rp.delete()


def test_pipeline_bad_shader_raises(patch_device):
    """compile failure (device.create_shader_module raises) → RuntimeError."""
    patch_device.create_shader_module.side_effect = Exception("WGSL parse error line 1")

    from vjlive3.render.program import RenderPipeline
    with pytest.raises(RuntimeError, match="compilation failed"):
        RenderPipeline(_BAD_WGSL, name="bad")


def test_pipeline_bad_fragment_raises(patch_device):
    """Pipeline creation failure → RuntimeError."""
    patch_device.create_render_pipeline.side_effect = Exception("fragment not found")

    from vjlive3.render.program import RenderPipeline
    with pytest.raises(RuntimeError, match="pipeline creation failed"):
        RenderPipeline(_GOOD_WGSL, name="bad-frag")


def test_pipeline_set_uniform_int():
    """set_uniform stores int value in uniforms dict without raising."""
    from vjlive3.render.program import RenderPipeline
    rp = RenderPipeline(_GOOD_WGSL, name="uni-test")
    rp.set_uniform("u_time_int", 42)
    assert rp.uniforms["u_time_int"] == 42
    rp.delete()


def test_pipeline_set_uniform_float():
    """set_uniform stores float value in uniforms dict."""
    from vjlive3.render.program import RenderPipeline
    rp = RenderPipeline(_GOOD_WGSL, name="uni-float")
    rp.set_uniform("u_time", 1.5)
    assert rp.uniforms["u_time"] == 1.5
    rp.delete()


def test_pipeline_set_unknown_uniform():
    """set_uniform with unknown name must not raise (silent cache)."""
    from vjlive3.render.program import RenderPipeline
    rp = RenderPipeline(_GOOD_WGSL, name="uni-unknown")
    rp.set_uniform("nonexistent_uniform_xyz", 99)  # must not raise
    rp.delete()
