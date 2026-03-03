"""
Tests for P1-R3 — WGSL ShaderCache and hot-reload
Spec: docs/specs/_01_skeletons/P1-R3_WGSL_hot_reload.md

All tests are CPU-only. No GPU context required.
File-watcher test uses a real temp file (pytest tmp_path).
"""

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from vjlive3.render.hot_reload import (
    ShaderCache,
    ShaderWatcher,
    reload_shader,
    watch_shader_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_compile_fn():
    """Returns a compile_fn that creates unique mock pipeline objects."""
    fn = MagicMock(side_effect=lambda src, name: MagicMock(name=f"pipeline:{name}"))
    return fn


def _mock_effect(pipeline=None, name="test-effect"):
    """Minimal duck-typed Effect with .cache, .pipeline, .name."""
    cache = ShaderCache(compile_fn=_mock_compile_fn())
    effect = MagicMock()
    effect.name = name
    effect.cache = cache
    effect.pipeline = pipeline
    return effect


# ---------------------------------------------------------------------------
# ShaderCache tests
# ---------------------------------------------------------------------------

def test_cache_compiles_once():
    """Same source string → compile_fn called once; same object returned."""
    fn = _mock_compile_fn()
    cache = ShaderCache(compile_fn=fn)

    src = "@vertex fn vs_main() -> @builtin(position) vec4<f32> { return vec4(0.0); }"
    p1 = cache.get_or_compile(src, name="test")
    p2 = cache.get_or_compile(src, name="test")

    assert p1 is p2
    fn.assert_called_once()


def test_cache_different_source():
    """Different source → compile_fn called twice; different objects."""
    fn = _mock_compile_fn()
    cache = ShaderCache(compile_fn=fn)

    p1 = cache.get_or_compile("@vertex fn vs_a() -> @builtin(position) vec4<f32> { return vec4(0.0); }")
    p2 = cache.get_or_compile("@vertex fn vs_b() -> @builtin(position) vec4<f32> { return vec4(1.0); }")

    assert p1 is not p2
    assert fn.call_count == 2


def test_cache_size():
    """size property reflects number of cached entries."""
    cache = ShaderCache(compile_fn=_mock_compile_fn())
    assert cache.size == 0

    cache.get_or_compile("@fragment fn fs_a() -> @location(0) vec4<f32> { return vec4(0.0); }")
    assert cache.size == 1

    cache.get_or_compile("@fragment fn fs_b() -> @location(0) vec4<f32> { return vec4(1.0); }")
    assert cache.size == 2


def test_cache_invalidate():
    """invalidate() removes entry; next call recompiles (compile_fn called twice)."""
    fn = _mock_compile_fn()
    cache = ShaderCache(compile_fn=fn)
    src = "@fragment fn fs() -> @location(0) vec4<f32> { return vec4(0.0); }"

    p1 = cache.get_or_compile(src)
    assert fn.call_count == 1

    cache.invalidate(src)
    assert cache.size == 0

    p2 = cache.get_or_compile(src)
    assert fn.call_count == 2
    # Both calls returned objects, but the compiled objects differ (new mock each time)
    assert p1 is not p2


def test_cache_invalidate_missing_noop():
    """invalidate() on a source not in cache is a silent no-op."""
    cache = ShaderCache(compile_fn=_mock_compile_fn())
    cache.invalidate("@fragment fn fs() -> @location(0) vec4<f32> { return vec4(0.0); }")  # must not raise
    assert cache.size == 0


def test_cache_clear():
    """clear() empties the cache; size returns 0."""
    cache = ShaderCache(compile_fn=_mock_compile_fn())
    cache.get_or_compile("@vertex fn vs() -> @builtin(position) vec4<f32> { return vec4(0.0); }")
    cache.get_or_compile("@fragment fn fs() -> @location(0) vec4<f32> { return vec4(0.0); }")
    assert cache.size == 2

    cache.clear()
    assert cache.size == 0


def test_cache_compile_failure_raises():
    """If compile_fn raises, get_or_compile raises RuntimeError."""
    def bad_compile(src, name):
        raise ValueError("bad WGSL syntax at line 3")

    cache = ShaderCache(compile_fn=bad_compile)
    with pytest.raises(RuntimeError, match="compilation failed"):
        cache.get_or_compile("this is not valid WGSL")


# ---------------------------------------------------------------------------
# reload_shader tests
# ---------------------------------------------------------------------------

def test_reload_success():
    """Valid WGSL swaps pipeline, returns True, old pipeline destroyed."""
    old_pipeline = MagicMock(name="old-pipeline")
    effect = _mock_effect(pipeline=old_pipeline)

    src = "@fragment fn fs() -> @location(0) vec4<f32> { return vec4(1.0); }"
    result = reload_shader(effect, src)

    assert result is True
    assert effect.pipeline is not old_pipeline
    old_pipeline.destroy.assert_called_once()


def test_reload_bad_wgsl_returns_false_and_keeps_old():
    """Compile failure → returns False, old pipeline remains unchanged."""
    def bad_compile(src, name):
        raise ValueError("parse error")

    old_pipeline = MagicMock(name="old")
    cache = ShaderCache(compile_fn=bad_compile)
    effect = MagicMock()
    effect.name = "bad-effect"
    effect.cache = cache
    effect.pipeline = old_pipeline

    result = reload_shader(effect, "not valid wgsl")

    assert result is False
    assert effect.pipeline is old_pipeline          # unchanged
    old_pipeline.destroy.assert_not_called()        # NOT destroyed


def test_reload_null_old_pipeline():
    """reload_shader with effect.pipeline = None must not crash."""
    effect = _mock_effect(pipeline=None)
    src = "@fragment fn fs() -> @location(0) vec4<f32> { return vec4(0.5); }"
    result = reload_shader(effect, src)
    assert result is True


def test_reload_always_recompiles():
    """reload_shader invalidates cache before compiling — always fresh compile."""
    fn = _mock_compile_fn()
    cache = ShaderCache(compile_fn=fn)
    effect = MagicMock()
    effect.name = "t"
    effect.cache = cache
    effect.pipeline = None

    src = "@fragment fn fs() -> @location(0) vec4<f32> { return vec4(0.0); }"
    reload_shader(effect, src)
    reload_shader(effect, src)

    # compile_fn called twice — cache invalidated before each reload
    assert fn.call_count == 2


# ---------------------------------------------------------------------------
# ShaderWatcher tests
# ---------------------------------------------------------------------------

def test_watch_detects_change(tmp_path):
    """File modification triggers reload_shader within 1 second."""
    wgsl_file: Path = tmp_path / "test.wgsl"
    initial_src = "@fragment fn fs() -> @location(0) vec4<f32> { return vec4(0.0); }"
    wgsl_file.write_text(initial_src, encoding="utf-8")

    effect = _mock_effect()
    reload_called = threading.Event()
    original_pipeline = effect.pipeline

    # Patch reload_shader to track calls
    import vjlive3.render.hot_reload as mod
    original_reload = mod.reload_shader

    def patched_reload(eff, src):
        result = original_reload(eff, src)
        reload_called.set()
        return result

    mod.reload_shader = patched_reload
    try:
        watcher = watch_shader_file(wgsl_file, effect, poll_interval=0.1)

        # Write new content to trigger change detection
        time.sleep(0.15)  # let watcher record initial mtime
        new_src = "@fragment fn fs() -> @location(0) vec4<f32> { return vec4(1.0); }"
        wgsl_file.write_text(new_src, encoding="utf-8")

        triggered = reload_called.wait(timeout=2.0)
        watcher.stop()

        assert triggered, "ShaderWatcher did not detect file change within 2 seconds"
    finally:
        mod.reload_shader = original_reload


def test_watcher_stop():
    """stop() terminates the background watcher thread."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".wgsl", delete=False) as f:
        f.write(b"@fragment fn fs() -> @location(0) vec4<f32> { return vec4(0.0); }")
        path = f.name

    try:
        effect = _mock_effect()
        watcher = watch_shader_file(path, effect, poll_interval=0.1)
        assert watcher.is_running()

        watcher.stop()
        assert not watcher.is_running()
    finally:
        os.unlink(path)


def test_watcher_is_running_false_before_start():
    """A ShaderWatcher that hasn't been started reports is_running=False."""
    watcher = ShaderWatcher(
        path=Path("/nonexistent/file.wgsl"),
        effect=_mock_effect(),
        poll_interval=0.5,
    )
    assert not watcher.is_running()
