"""
Tests for P1-R1 — RenderContext
Spec: docs/specs/_02_fleshed_out/P1-R1_opengl_context.md

wgpu and glfw are NOT installed in test environments. All GPU/window calls
are mocked via sys.modules injection before the module under test is imported.
"""

import importlib
import os
import sys
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Build reusable wgpu / glfw mock infrastructure
# ---------------------------------------------------------------------------

def _make_mock_device() -> MagicMock:
    dev = MagicMock(name="GPUDevice")
    return dev


def _make_mock_adapter(device: MagicMock) -> MagicMock:
    adapter = MagicMock(name="GPUAdapter")
    adapter.request_device_sync.return_value = device
    adapter.info = {"adapter_type": "MockGPU", "vendor": "TestVendor"}
    return adapter


def _make_mock_canvas() -> MagicMock:
    canvas = MagicMock(name="GlfwCanvas")
    canvas.get_closed.return_value = False
    canvas.is_closed.return_value = False
    canvas.force_draw = MagicMock(name="force_draw")
    canvas._maybe_close = MagicMock(name="_maybe_close")
    ctx = MagicMock(name="GPUCanvasContext")
    ctx.get_preferred_format.return_value = "rgba8unorm"
    canvas.get_context.return_value = ctx
    return canvas


def _inject_mocks(monkeypatch, *, glfw_init_ok: bool = True, adapter_ok: bool = True):
    """
    Inject mock wgpu and glfw into sys.modules so render_context.py lazy imports
    resolve to mocks. Returns (mock_wgpu, mock_glfw, mock_canvas, mock_adapter, mock_device).
    """
    device = _make_mock_device()
    adapter = _make_mock_adapter(device)
    canvas = _make_mock_canvas()

    mock_wgpu = MagicMock(name="wgpu")
    mock_wgpu.gpu.request_adapter_sync.return_value = adapter if adapter_ok else None

    mock_glfw = MagicMock(name="glfw")
    mock_glfw.init.return_value = glfw_init_ok

    mock_wgpu_gui_glfw = MagicMock(name="wgpu.gui.glfw")
    mock_wgpu_gui_glfw.WgpuCanvas.return_value = canvas

    monkeypatch.setitem(sys.modules, "wgpu", mock_wgpu)
    monkeypatch.setitem(sys.modules, "glfw", mock_glfw)

    # render_context._init_windowed imports from rendercanvas.glfw (not wgpu.gui.glfw)
    mock_rendercanvas = MagicMock(name="rendercanvas")
    mock_rendercanvas_glfw = MagicMock(name="rendercanvas.glfw")
    mock_rendercanvas_glfw.GlfwRenderCanvas.return_value = canvas
    monkeypatch.setitem(sys.modules, "rendercanvas", mock_rendercanvas)
    monkeypatch.setitem(sys.modules, "rendercanvas.glfw", mock_rendercanvas_glfw)

    # Keep legacy wgpu.gui.glfw mock so any stale imports don't crash.
    mock_wgpu_gui_glfw = MagicMock(name="wgpu.gui.glfw")
    monkeypatch.setitem(sys.modules, "wgpu.gui", MagicMock())
    monkeypatch.setitem(sys.modules, "wgpu.gui.glfw", mock_wgpu_gui_glfw)

    return mock_wgpu, mock_glfw, canvas, adapter, device


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the module-level singleton guard between tests."""
    import vjlive3.render.render_context as rcmod
    original = rcmod._active_instance
    rcmod._active_instance = None
    yield
    rcmod._active_instance = None


# ---------------------------------------------------------------------------
# Headless mode tests (no display required)
# ---------------------------------------------------------------------------

def test_context_headless_constructor(monkeypatch):
    """headless=True skips GLFW, creates wgpu device."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=True)

    assert ctx.headless is True
    assert ctx.device is device
    assert ctx.ctx is None          # No canvas context in headless
    mock_glfw.init.assert_not_called()
    ctx.terminate()


def test_context_env_headless(monkeypatch):
    """VJ_HEADLESS=true env var forces headless regardless of constructor arg."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)
    monkeypatch.setenv("VJ_HEADLESS", "true")

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=False)  # overridden by env var

    assert ctx.headless is True
    mock_glfw.init.assert_not_called()
    ctx.terminate()


def test_context_env_headless_case_insensitive(monkeypatch):
    """VJ_HEADLESS accepts True/TRUE/true."""
    _inject_mocks(monkeypatch)
    monkeypatch.setenv("VJ_HEADLESS", "TRUE")

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext()
    assert ctx.headless is True
    ctx.terminate()


def test_context_headless_adapter_unavailable_raises(monkeypatch):
    """RuntimeError raised if wgpu returns no adapter in headless mode."""
    _inject_mocks(monkeypatch, adapter_ok=False)
    monkeypatch.setenv("VJ_HEADLESS", "true")

    from vjlive3.render.render_context import RenderContext
    with pytest.raises(RuntimeError, match="adapter unavailable"):
        RenderContext()


def test_window_methods_noops_in_headless(monkeypatch):
    """poll_events, swap_buffers, make_current, should_close are no-ops in headless."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=True)

    ctx.make_current()    # must not raise
    ctx.poll_events()     # must not raise
    ctx.swap_buffers()    # must not raise
    assert ctx.should_close() is False

    mock_glfw.poll_events.assert_not_called()
    ctx.terminate()


def test_context_double_terminate(monkeypatch):
    """Calling terminate() twice must not raise (idempotent — ADR-019)."""
    _inject_mocks(monkeypatch)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=True)
    ctx.terminate()
    ctx.terminate()  # second call must be silent no-op


def test_context_manager_lifecycle(monkeypatch):
    """Using 'with RenderContext(...) as ctx:' calls terminate() on exit."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)

    from vjlive3.render.render_context import RenderContext
    with RenderContext(headless=True) as ctx:
        assert ctx.device is device
        assert not ctx._terminated

    assert ctx._terminated
    device.destroy.assert_called_once()


def test_context_properties(monkeypatch):
    """width, height, headless, adapter, device properties return correct values."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(width=1280, height=720, headless=True)

    assert ctx.width == 1280
    assert ctx.height == 720
    assert ctx.headless is True
    assert ctx.adapter is adapter
    assert ctx.device is device
    ctx.terminate()


def test_single_instance_guard(monkeypatch):
    """Creating a second RenderContext before terminating the first must raise."""
    _inject_mocks(monkeypatch)

    from vjlive3.render.render_context import RenderContext
    ctx1 = RenderContext(headless=True)

    with pytest.raises(RuntimeError, match="only one instance"):
        RenderContext(headless=True)

    ctx1.terminate()


def test_second_instance_allowed_after_terminate(monkeypatch):
    """After terminate(), a second RenderContext must succeed."""
    _inject_mocks(monkeypatch)

    from vjlive3.render.render_context import RenderContext
    ctx1 = RenderContext(headless=True)
    ctx1.terminate()

    ctx2 = RenderContext(headless=True)
    assert ctx2.device is not None
    ctx2.terminate()


# ---------------------------------------------------------------------------
# Windowed mode tests (mocked GLFW + wgpu)
# ---------------------------------------------------------------------------

def test_windowed_creates_glfwrendercanvas(monkeypatch):
    """Windowed mode constructs a GlfwRenderCanvas and obtains its wgpu context."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)
    monkeypatch.delenv("VJ_HEADLESS", raising=False)

    # GlfwRenderCanvas is imported from rendercanvas.glfw inside _init_windowed
    from rendercanvas.glfw import GlfwRenderCanvas  # this is now the mock
    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(width=800, height=600, headless=False)

    GlfwRenderCanvas.assert_called_once()
    assert ctx.headless is False
    assert ctx.ctx is canvas.get_context.return_value
    ctx.terminate()


def test_windowed_poll_events_calls_glfw(monkeypatch):
    """poll_events() in windowed mode calls glfw.poll_events()."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)
    monkeypatch.delenv("VJ_HEADLESS", raising=False)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=False)
    ctx.poll_events()

    mock_glfw.poll_events.assert_called_once()
    ctx.terminate()


def test_windowed_swap_buffers_calls_force_draw(monkeypatch):
    """swap_buffers() in windowed mode calls canvas.force_draw()."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)
    monkeypatch.delenv("VJ_HEADLESS", raising=False)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=False)
    ctx.swap_buffers()

    canvas.force_draw.assert_called_once()
    ctx.terminate()


def test_windowed_should_close_delegates_to_canvas(monkeypatch):
    """should_close() returns get_closed() result (rendercanvas 2.x API)."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)
    canvas.get_closed.return_value = True
    monkeypatch.delenv("VJ_HEADLESS", raising=False)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=False)
    assert ctx.should_close() is True
    ctx.terminate()


# ---------------------------------------------------------------------------
# blit_to_screen tests
# ---------------------------------------------------------------------------

def test_blit_to_screen_headless_noop(monkeypatch):
    """blit_to_screen() is a silent no-op in headless mode."""
    _inject_mocks(monkeypatch)
    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=True)
    ctx.blit_to_screen(src_view=MagicMock())  # must not raise
    ctx.terminate()


def _windowed_ctx_with_injected_gpu(monkeypatch):
    """
    Returns (ctx, mock_device, mock_canvas_ctx, mock_pipeline) for
    blit_to_screen tests, with _headless forced False and GPU objects injected.
    """
    _inject_mocks(monkeypatch)
    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=True)  # headless so no real window opens

    mock_device = MagicMock(name="MockDevice")
    pipeline = MagicMock(name="MockPipeline")
    pipeline.get_bind_group_layout.return_value = MagicMock()
    mock_device.create_shader_module.return_value = MagicMock()
    mock_device.create_render_pipeline.return_value = pipeline
    mock_device.create_sampler.return_value = MagicMock()
    mock_device.create_bind_group.return_value = MagicMock()

    encoder = MagicMock(name="Encoder")
    rp = MagicMock(name="RenderPass")
    encoder.begin_render_pass.return_value = rp
    mock_device.create_command_encoder.return_value = encoder

    mock_canvas_ctx = MagicMock(name="CanvasCtx")
    screen_tex = MagicMock()
    screen_tex.create_view.return_value = MagicMock()
    mock_canvas_ctx.get_current_texture.return_value = screen_tex

    # Inject windowed-mode state without opening a real window
    ctx._headless = False
    ctx._ctx = mock_canvas_ctx
    ctx._device = mock_device
    ctx._screen_format = "rgba8unorm"

    return ctx, mock_device, mock_canvas_ctx, pipeline


def test_blit_to_screen_with_src_view_sets_pipeline(monkeypatch):
    """blit_to_screen(src_view=...) builds SCREEN_BLIT pipeline and calls set_pipeline."""
    ctx, mock_device, _, pipeline = _windowed_ctx_with_injected_gpu(monkeypatch)
    src_view = MagicMock(name="SrcView")
    ctx.blit_to_screen(src_view=src_view)

    encoder = mock_device.create_command_encoder.return_value
    rp = encoder.begin_render_pass.return_value
    rp.set_pipeline.assert_called_once_with(pipeline)
    ctx._headless = True
    ctx.terminate()


def test_blit_to_screen_with_src_view_draws_quad(monkeypatch):
    """blit_to_screen(src_view=...) draws 4 vertices (fullscreen quad)."""
    ctx, mock_device, _, _ = _windowed_ctx_with_injected_gpu(monkeypatch)
    ctx.blit_to_screen(src_view=MagicMock())

    rp = mock_device.create_command_encoder.return_value.begin_render_pass.return_value
    rp.draw.assert_called_once_with(4)
    ctx._headless = True
    ctx.terminate()


def test_blit_to_screen_no_src_view_no_pipeline(monkeypatch):
    """blit_to_screen(src_view=None) uses colour-cycle path — no pipeline built."""
    ctx, mock_device, _, _ = _windowed_ctx_with_injected_gpu(monkeypatch)
    ctx.blit_to_screen(src_view=None, frame_time=0.0)

    mock_device.create_render_pipeline.assert_not_called()
    rp = mock_device.create_command_encoder.return_value.begin_render_pass.return_value
    rp.set_pipeline.assert_not_called()
    ctx._headless = True
    ctx.terminate()


def test_blit_to_screen_pipeline_built_only_once(monkeypatch):
    """Calling blit_to_screen twice with src_view only creates the pipeline once."""
    ctx, mock_device, _, _ = _windowed_ctx_with_injected_gpu(monkeypatch)
    ctx.blit_to_screen(src_view=MagicMock())
    ctx.blit_to_screen(src_view=MagicMock())

    mock_device.create_render_pipeline.assert_called_once()
    ctx._headless = True
    ctx.terminate()
