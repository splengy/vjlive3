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
    canvas = MagicMock(name="WgpuCanvas")
    canvas.is_closed.return_value = False
    ctx = MagicMock(name="GPUCanvasContext")
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

def test_windowed_init_calls_glfw_init(monkeypatch):
    """Windowed mode must call glfw.init()."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)
    monkeypatch.delenv("VJ_HEADLESS", raising=False)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(width=800, height=600, headless=False)

    mock_glfw.init.assert_called_once()
    assert ctx.headless is False
    assert ctx.ctx is canvas.get_context.return_value
    ctx.terminate()


def test_windowed_glfw_init_fail_raises(monkeypatch):
    """RuntimeError raised if glfw.init() returns False."""
    _inject_mocks(monkeypatch, glfw_init_ok=False)
    monkeypatch.delenv("VJ_HEADLESS", raising=False)

    from vjlive3.render.render_context import RenderContext
    with pytest.raises(RuntimeError, match="glfw.init"):
        RenderContext(headless=False)


def test_windowed_poll_events_calls_glfw(monkeypatch):
    """poll_events() in windowed mode calls glfw.poll_events()."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)
    monkeypatch.delenv("VJ_HEADLESS", raising=False)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=False)
    ctx.poll_events()

    mock_glfw.poll_events.assert_called_once()
    ctx.terminate()


def test_windowed_swap_buffers_calls_present(monkeypatch):
    """swap_buffers() in windowed mode calls canvas.present()."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)
    monkeypatch.delenv("VJ_HEADLESS", raising=False)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=False)
    ctx.swap_buffers()

    canvas.present.assert_called_once()
    ctx.terminate()


def test_windowed_should_close_delegates_to_canvas(monkeypatch):
    """should_close() returns canvas.is_closed() result."""
    mock_wgpu, mock_glfw, canvas, adapter, device = _inject_mocks(monkeypatch)
    canvas.is_closed.return_value = True
    monkeypatch.delenv("VJ_HEADLESS", raising=False)

    from vjlive3.render.render_context import RenderContext
    ctx = RenderContext(headless=False)
    assert ctx.should_close() is True
    ctx.terminate()
