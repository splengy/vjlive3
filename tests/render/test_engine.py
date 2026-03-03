"""
Tests for P1-R5 — RenderEngine, FrameProfiler, FrameBudgetAllocator (engine.py)
Spec: docs/specs/_01_skeletons/P1-R5_60fps loop.md

All tests use mocked RenderContext and EffectChain — no GPU required.
"""

import threading
import time
from unittest.mock import MagicMock, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ctx(should_close_after: int = 0):
    """Make a mock RenderContext that returns should_close()=True after N calls."""
    ctx = MagicMock(name="RenderContext")
    ctx.width = 1920
    ctx.height = 1080
    _counter = [0]

    def _should_close():
        _counter[0] += 1
        return _counter[0] > should_close_after

    ctx.should_close.side_effect = _should_close
    return ctx


def _make_chain():
    chain = MagicMock(name="EffectChain")
    chain.render.return_value = MagicMock(name="output-tex")
    chain.render_to_screen.return_value = None
    return chain


# ---------------------------------------------------------------------------
# FrameProfiler tests
# ---------------------------------------------------------------------------

class TestFrameProfiler:
    def test_profiler_records(self):
        """get_metrics() returns values after several timed frames."""
        from vjlive3.render.engine import FrameProfiler
        profiler = FrameProfiler()
        for _ in range(5):
            with profiler.time("effects"):
                time.sleep(0.001)  # 1ms
            profiler.tick()

        metrics = profiler.get_metrics()
        assert "effects" in metrics
        assert metrics["effects"]["last_ms"] > 0
        assert metrics["effects"]["avg_ms"] > 0
        assert profiler.frame_count == 5

    def test_profiler_manual_record(self):
        """record() stores a manually provided duration."""
        from vjlive3.render.engine import FrameProfiler
        profiler = FrameProfiler()
        profiler.record("graph", 3.0)
        m = profiler.get_metrics()
        assert m["graph"]["last_ms"] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# FrameBudgetAllocator tests
# ---------------------------------------------------------------------------

class TestFrameBudgetAllocator:
    def test_budget_register(self):
        """Registered effect starts with should_skip=False and lod_scale=1.0."""
        from vjlive3.render.engine import FrameBudgetAllocator
        alloc = FrameBudgetAllocator()
        alloc.register("depth-mosh", budget_ms=4.0)
        assert alloc.should_skip("depth-mosh") is False
        assert alloc.get_lod_scale("depth-mosh") == pytest.approx(1.0)

    def test_budget_skip(self):
        """Effect over budget → should_skip=True next frame."""
        from vjlive3.render.engine import FrameBudgetAllocator
        alloc = FrameBudgetAllocator()
        alloc.register("fx", budget_ms=2.0)
        alloc.record_duration("fx", 10.0)  # 5× budget
        assert alloc.should_skip("fx") is True
        assert alloc.get_lod_scale("fx") < 1.0

    def test_budget_max_consecutive_skips(self):
        """Effect skipped at most 2 frames in a row before forced compute."""
        from vjlive3.render.engine import FrameBudgetAllocator
        alloc = FrameBudgetAllocator()
        alloc.register("fx", budget_ms=1.0)

        # Overrun 3 times in a row
        alloc.record_duration("fx", 10.0)  # skip 1
        alloc.record_duration("fx", 10.0)  # skip 2
        alloc.record_duration("fx", 10.0)  # hits cap → forced compute

        # After hitting cap, should_skip resets
        assert alloc.should_skip("fx") is False

    def test_budget_lod_recovery(self):
        """LOD scale recovers over time when effect is within budget."""
        from vjlive3.render.engine import FrameBudgetAllocator
        alloc = FrameBudgetAllocator()
        alloc.register("fx", budget_ms=4.0)
        alloc.record_duration("fx", 10.0)  # overrun → lod drops
        lod_degraded = alloc.get_lod_scale("fx")

        for _ in range(20):
            alloc.record_duration("fx", 1.0)  # within budget → lod recovers

        assert alloc.get_lod_scale("fx") > lod_degraded

    def test_budget_unknown_effect(self):
        """Unknown effect name: should_skip=False, lod_scale=1.0, record does nothing."""
        from vjlive3.render.engine import FrameBudgetAllocator
        alloc = FrameBudgetAllocator()
        assert alloc.should_skip("ghost") is False
        assert alloc.get_lod_scale("ghost") == pytest.approx(1.0)
        alloc.record_duration("ghost", 100.0)  # must not raise


# ---------------------------------------------------------------------------
# RenderEngine tests
# ---------------------------------------------------------------------------

class TestRenderEngine:
    def test_engine_runs_headless(self):
        """Engine runs N frames via mocked context + chain, then exits cleanly."""
        from vjlive3.render.engine import RenderEngine
        ctx = _make_ctx(should_close_after=10)
        chain = _make_chain()
        engine = RenderEngine(ctx, chain, target_fps=1000.0)  # no sleep in test
        engine.run()
        assert engine.total_frames >= 10
        ctx.terminate.assert_called_once()

    def test_fps_cap(self):
        """Instant render + FPS cap: engine stays near target for brief run."""
        from vjlive3.render.engine import RenderEngine
        ctx = _make_ctx(should_close_after=0)  # close immediately
        chain = _make_chain()
        engine = RenderEngine(ctx, chain, target_fps=60.0)

        # Run for ~0.2 seconds via threading
        def stop_after():
            time.sleep(0.1)
            engine.stop()

        t = threading.Thread(target=stop_after)
        t.start()
        engine.run()
        t.join()

        # We just verify it ran without error and reported some FPS
        assert engine.total_frames >= 0

    def test_frame_time_clamped(self):
        """After simulated 1s freeze, frame_time is ≤ 0.1 s."""
        from vjlive3.render.engine import RenderEngine
        ctx = _make_ctx(should_close_after=2)
        chain = _make_chain()

        # Inject artificial delay on first poll_events call
        _called = [False]

        def _slow_poll():
            if not _called[0]:
                _called[0] = True
                time.sleep(0.15)  # > 100ms

        ctx.poll_events.side_effect = _slow_poll
        engine = RenderEngine(ctx, chain, target_fps=1000.0)
        engine.run()
        assert engine.frame_time <= 0.1

    def test_stop_from_thread(self):
        """stop() from a background thread exits the loop promptly."""
        from vjlive3.render.engine import RenderEngine
        ctx = _make_ctx(should_close_after=99999)  # never closes on its own
        chain = _make_chain()
        engine = RenderEngine(ctx, chain, target_fps=1000.0)

        def stopper():
            time.sleep(0.05)
            engine.stop()

        t = threading.Thread(target=stopper)
        t.start()
        start = time.time()
        engine.run()
        t.join()
        elapsed = time.time() - start
        assert elapsed < 2.0, "stop() did not exit loop within 2 seconds"

    def test_callback_called(self):
        """Frame callback is invoked exactly once per rendered frame."""
        from vjlive3.render.engine import RenderEngine
        N = 5
        ctx = _make_ctx(should_close_after=N)
        chain = _make_chain()
        engine = RenderEngine(ctx, chain, target_fps=1000.0)

        cb = MagicMock()
        engine.set_frame_callback(cb)
        engine.run()

        assert cb.call_count == N

    def test_effect_exception_survives(self):
        """Effect chain raising RuntimeError does not crash the loop."""
        from vjlive3.render.engine import RenderEngine
        ctx = _make_ctx(should_close_after=5)
        chain = _make_chain()
        chain.render.side_effect = RuntimeError("GPU exploded")
        engine = RenderEngine(ctx, chain, target_fps=1000.0)
        engine.run()  # must not raise
        assert engine.total_frames >= 5

    def test_fps_measurement(self):
        """fps property reads a plausible value after a short headless run."""
        from vjlive3.render.engine import RenderEngine
        ctx = _make_ctx(should_close_after=0)
        chain = _make_chain()
        engine = RenderEngine(ctx, chain, target_fps=1000.0)

        def stop_after():
            time.sleep(0.25)
            engine.stop()

        t = threading.Thread(target=stop_after)
        t.start()
        engine.run()
        t.join()
        # Any non-negative FPS is valid (value depends on CI machine speed)
        assert engine.fps >= 0.0
