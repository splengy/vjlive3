"""
Tests for P1-R4 — TexturePool + PooledTexture
Spec: docs/specs/P1-R4_pooled, leak-free_spec.md

All tests are CPU-only. wgpu is mocked via sys.modules injection.
"""

import sys
import threading
from unittest.mock import MagicMock, call

import pytest


# ---------------------------------------------------------------------------
# wgpu mock injection — must happen before any import of texture_pool
# ---------------------------------------------------------------------------

def _inject_wgpu(monkeypatch):
    """Inject a minimal wgpu mock and return (mock_wgpu, mock_device)."""
    mock_wgpu = MagicMock(name="wgpu")

    # TextureFormat and TextureUsage need to behave like enums / ints
    mock_wgpu.TextureFormat.rgba8unorm = "rgba8unorm"
    mock_wgpu.TextureUsage.RENDER_ATTACHMENT = 0x10
    mock_wgpu.TextureUsage.TEXTURE_BINDING = 0x04

    mock_device = MagicMock(name="GPUDevice")
    # Each call to create_texture returns a fresh unique mock
    mock_device.create_texture.side_effect = lambda **kw: MagicMock(name="GPUTexture")

    monkeypatch.setitem(sys.modules, "wgpu", mock_wgpu)
    return mock_wgpu, mock_device


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_pool_acquire_new(monkeypatch):
    """First acquire allocates a texture via device.create_texture()."""
    mock_wgpu, device = _inject_wgpu(monkeypatch)

    from vjlive3.render.texture_pool import TexturePool
    pool = TexturePool(device=device, max_per_bucket=4)

    pt = pool.acquire(1920, 1080)

    device.create_texture.assert_called_once()
    assert pt.width == 1920
    assert pt.height == 1080
    pt.release()


def test_pool_acquire_reuse(monkeypatch):
    """Acquire → release → acquire of same dims returns the SAME texture object."""
    mock_wgpu, device = _inject_wgpu(monkeypatch)

    from vjlive3.render.texture_pool import TexturePool
    pool = TexturePool(device=device, max_per_bucket=4)

    pt1 = pool.acquire(640, 480)
    raw_tex = pt1.texture
    pt1.release()

    pt2 = pool.acquire(640, 480)
    assert pt2.texture is raw_tex        # same GPU object reused
    assert device.create_texture.call_count == 1   # only ONE alloc
    pt2.release()


def test_pool_different_dims(monkeypatch):
    """Different (w, h) use different buckets → separate textures."""
    mock_wgpu, device = _inject_wgpu(monkeypatch)

    from vjlive3.render.texture_pool import TexturePool
    pool = TexturePool(device=device)

    pt_a = pool.acquire(1920, 1080)
    pt_b = pool.acquire(640, 480)

    assert pt_a.texture is not pt_b.texture
    assert device.create_texture.call_count == 2
    pt_a.release()
    pt_b.release()


def test_pool_bucket_overflow(monkeypatch):
    """Releasing more textures than max_per_bucket destroys the excess."""
    mock_wgpu, device = _inject_wgpu(monkeypatch)

    from vjlive3.render.texture_pool import TexturePool
    pool = TexturePool(device=device, max_per_bucket=1)

    pt1 = pool.acquire(256, 256)
    tex1 = pt1.texture
    pt2 = pool.acquire(256, 256)
    tex2 = pt2.texture

    # Release both — bucket max is 1, so one should be destroyed
    pt1.release()
    pt2.release()

    assert pool.stats["idle_total"] == 1
    # Exactly one of the textures should have had .destroy() called
    destroyed_count = sum([
        1 for t in [tex1, tex2] if t.destroy.called
    ])
    assert destroyed_count == 1


def test_pool_context_manager(monkeypatch):
    """'with pool.acquire(...)' auto-releases on block exit."""
    mock_wgpu, device = _inject_wgpu(monkeypatch)

    from vjlive3.render.texture_pool import TexturePool
    pool = TexturePool(device=device)

    with pool.acquire(800, 600) as pt:
        assert not pt._released

    assert pt._released
    assert pool.stats["idle_total"] == 1


def test_pool_double_release(monkeypatch):
    """Calling release() twice on a PooledTexture must not crash or double-return."""
    mock_wgpu, device = _inject_wgpu(monkeypatch)

    from vjlive3.render.texture_pool import TexturePool
    pool = TexturePool(device=device, max_per_bucket=4)

    pt = pool.acquire(512, 512)
    pt.release()
    pt.release()  # must be silent no-op

    assert pool.stats["idle_total"] == 1


def test_pool_clear(monkeypatch):
    """clear() destroys all idle textures and empties all buckets."""
    mock_wgpu, device = _inject_wgpu(monkeypatch)

    from vjlive3.render.texture_pool import TexturePool
    pool = TexturePool(device=device)

    pt1 = pool.acquire(128, 128)
    pt2 = pool.acquire(256, 256)
    pt1.release()
    pt2.release()

    assert pool.stats["idle_total"] == 2

    pool.clear()

    assert pool.stats["idle_total"] == 0
    assert pool.stats["buckets"] == 0


def test_pool_stats(monkeypatch):
    """stats dict reflects correct bucket count, idle count, and allocated count."""
    mock_wgpu, device = _inject_wgpu(monkeypatch)

    from vjlive3.render.texture_pool import TexturePool
    pool = TexturePool(device=device)

    assert pool.stats == {"buckets": 0, "idle_total": 0, "allocated_total": 0}

    pt1 = pool.acquire(64, 64)
    assert pool.stats["allocated_total"] == 1
    assert pool.stats["idle_total"] == 0

    pt1.release()
    assert pool.stats["idle_total"] == 1
    assert pool.stats["allocated_total"] == 1  # still allocated (just idle)


def test_pool_thread_safety(monkeypatch):
    """Concurrent acquire/release from 4 threads must not crash or corrupt state."""
    mock_wgpu, device = _inject_wgpu(monkeypatch)

    from vjlive3.render.texture_pool import TexturePool
    pool = TexturePool(device=device, max_per_bucket=2)

    errors = []

    def worker():
        try:
            for _ in range(20):
                pt = pool.acquire(128, 128)
                pt.release()
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive(), "Thread did not finish in time"

    assert not errors, f"Thread errors: {errors}"


def test_pool_zero_max_no_pool(monkeypatch):
    """max_per_bucket=0 means always destroy on release (no-pool mode)."""
    mock_wgpu, device = _inject_wgpu(monkeypatch)

    from vjlive3.render.texture_pool import TexturePool
    pool = TexturePool(device=device, max_per_bucket=0)

    pt = pool.acquire(64, 64)
    raw = pt.texture
    pt.release()

    assert pool.stats["idle_total"] == 0
    raw.destroy.assert_called_once()
