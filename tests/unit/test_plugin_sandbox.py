"""Tests for P1-P5 PluginSandbox"""
import numpy as np
import pytest
from vjlive3.plugins.registry import PluginRegistry
from vjlive3.plugins.sandbox import PluginSandbox, SandboxResult

_FRAME = np.zeros((4, 4, 4), dtype=np.uint8)


class _GoodPlugin:
    METADATA = {"name": "Good", "description": "g" * 50}
    def process(self, frame, audio, **kw):
        return frame.copy()


class _BoomPlugin:
    METADATA = {"name": "Boom", "description": "b" * 50}
    def process(self, frame, audio, **kw):
        raise RuntimeError("kaboom")


class _WrongShapePlugin:
    METADATA = {"name": "WrongShape", "description": "w" * 50}
    def process(self, frame, audio, **kw):
        return np.zeros((1, 1, 4), dtype=np.uint8)  # wrong shape


_M = lambda name: {
    "id": f"com.test.{name.lower()}", "name": name, "version": "1.0.0",
    "description": "x" * 50, "author": "T", "category": "effect", "tags": []
}


@pytest.fixture
def reg():
    r = PluginRegistry()
    r.register("good", _GoodPlugin, _M("good"))
    r.register("boom", _BoomPlugin, _M("boom"))
    r.register("wrongshape", _WrongShapePlugin, _M("wrongshape"))
    return r


@pytest.fixture
def box(reg):
    return PluginSandbox(reg, frame_budget_ms=14.0, max_errors=3)


def test_call_happy_path(box):
    result = box.call("good", _FRAME)
    assert result.success is True
    assert result.output is not None
    assert result.output.shape == _FRAME.shape


def test_call_unknown_plugin(box):
    result = box.call("ghost", _FRAME)
    assert result.success is False
    assert result.output is None


def test_call_plugin_raises(box):
    result = box.call("boom", _FRAME)
    assert result.success is False
    assert box.error_count("boom") == 1


def test_auto_disable(box):
    # max_errors = 3 in fixture
    for _ in range(3):
        box.call("boom", _FRAME)
    assert box.is_disabled("boom") is True
    # Another call returns disabled result immediately
    r = box.call("boom", _FRAME)
    assert "disabled" in (r.error or "").lower()


def test_manual_disable_enable(box):
    box.disable("good")
    assert box.is_disabled("good") is True
    box.enable("good")
    assert box.is_disabled("good") is False


def test_wrong_output_shape(box, caplog):
    import logging
    with caplog.at_level(logging.WARNING):
        result = box.call("wrongshape", _FRAME)
    assert result.success is True
    assert result.output.shape == _FRAME.shape  # falls back to input
    assert "wrong shape" in caplog.text.lower()


def test_stats(box):
    box.call("good", _FRAME)
    stats = box.get_stats()
    assert "good" in stats
    assert stats["good"]["total_calls"] == 1


def test_frame_budget_warning(reg, caplog):
    import logging, time

    class SlowPlugin:
        METADATA = {"name": "Slow", "description": "s" * 50}
        def process(self, frame, audio, **kw):
            time.sleep(0.05)  # 50ms >> budget
            return frame

    reg.register("slow", SlowPlugin, _M("slow"))
    box = PluginSandbox(reg, frame_budget_ms=1.0)
    with caplog.at_level(logging.WARNING):
        box.call("slow", _FRAME)
    assert "budget" in caplog.text.lower() or "exceeded" in caplog.text.lower()


def test_re_enable_clears_error_count(box):
    box.call("boom", _FRAME)
    assert box.error_count("boom") == 1
    box.enable("boom")
    assert box.error_count("boom") == 0
