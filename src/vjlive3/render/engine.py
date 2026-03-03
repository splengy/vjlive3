"""
P1-R5 — 60 FPS Render Engine (Main Loop)
Spec: docs/specs/_01_skeletons/P1-R5_60fps loop.md
Tier: 🖥️ Pro-Tier Native — Python render loop + window driver.

Three classes in one file:
  1. FrameProfiler       — per-frame named-stage timing with context manager.
  2. FrameBudgetAllocator — adaptive skip/LOD controller for CPU-bound effects.
  3. RenderEngine        — main 60 FPS while-loop, threading-safe stop().

Derived from vjlive/core/app/app.py (run, render_frame, update_fps)
and vjlive/core/frame_budget.py — ported verbatim with OpenGL removed.
"""

import contextlib
import logging
import threading
import time
from collections import deque
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

_FPS_WARN_THRESHOLD = 30.0
_SUSTAINED_LOW_FPS_FRAMES = 10


# ---------------------------------------------------------------------------
# FrameProfiler
# ---------------------------------------------------------------------------

class FrameProfiler:
    """
    Lightweight per-frame stage timing.

    Usage:
        with profiler.time('effects'):
            ...
        metrics = profiler.get_metrics()  # {'effects': {'last_ms': 2.1, 'avg_ms': 2.3}}
    """

    def __init__(self) -> None:
        self._stages: Dict[str, deque] = {}
        self._frame_count: int = 0
        self._WINDOW = 60  # rolling avg over last 60 frames

    @contextlib.contextmanager
    def time(self, stage: str):
        """Context manager: times the block and records to stage."""
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.record(stage, (time.perf_counter() - t0) * 1000.0)

    def record(self, stage: str, duration_ms: float) -> None:
        """Manually record a duration for a named stage."""
        if stage not in self._stages:
            self._stages[stage] = deque(maxlen=self._WINDOW)
        self._stages[stage].append(duration_ms)
        if duration_ms > 5.0:
            logger.debug("FrameProfiler: stage '%s' took %.1f ms > 5 ms budget", stage, duration_ms)

    def tick(self) -> None:
        """Advance frame counter. Call once per frame after all stage records."""
        self._frame_count += 1

    def get_metrics(self) -> dict:
        """Return {stage: {'last_ms': float, 'avg_ms': float}} for all recorded stages."""
        result = {}
        for stage, samples in self._stages.items():
            if samples:
                result[stage] = {
                    "last_ms": samples[-1],
                    "avg_ms": sum(samples) / len(samples),
                }
        return result

    @property
    def frame_count(self) -> int:
        return self._frame_count


# ---------------------------------------------------------------------------
# FrameBudgetAllocator
# ---------------------------------------------------------------------------

class FrameBudgetAllocator:
    """
    Adaptive skip / LOD controller for CPU-bound effects.
    Ported from vjlive/core/frame_budget.py (lines 1-120).

    Per-effect rules:
      - If actual duration > budget_ms: set should_skip=True, reduce lod_scale.
      - Never skip more than 2 consecutive frames (enforced).
      - LOD scale: 1.0 → 0.5 → 0.25 on successive overruns; recovers on meeting budget.
    """

    _MAX_CONSECUTIVE_SKIPS = 2

    def __init__(self, target_fps: int = 60) -> None:
        self._target_fps = target_fps
        self._effects: Dict[str, dict] = {}  # name → {budget_ms, skip, consec, lod}

    def register(self, name: str, budget_ms: float = 4.0) -> None:
        """Register an effect with its per-frame time budget."""
        self._effects[name] = {
            "budget_ms": budget_ms,
            "should_skip": False,
            "consecutive_skips": 0,
            "lod_scale": 1.0,
        }

    def unregister(self, name: str) -> None:
        """Remove a registered effect. No-op if unknown."""
        self._effects.pop(name, None)

    def should_skip(self, name: str) -> bool:
        """True if the effect overran its budget last frame AND hasn't hit the 2-skip cap."""
        entry = self._effects.get(name)
        if entry is None:
            return False
        return bool(entry["should_skip"])

    def get_lod_scale(self, name: str) -> float:
        """Current LOD downscale factor (0.1–1.0). Reduced when effect overruns budget."""
        entry = self._effects.get(name)
        return entry["lod_scale"] if entry is not None else 1.0

    def record_duration(self, name: str, duration_ms: float) -> None:
        """
        Record actual compute time for an effect.
        Updates should_skip flag and lod_scale for the next frame.
        """
        entry = self._effects.get(name)
        if entry is None:
            return

        budget = entry["budget_ms"]
        if duration_ms > budget:
            # Overrun — schedule a skip next frame (unless at cap)
            consec = entry["consecutive_skips"]
            if consec < self._MAX_CONSECUTIVE_SKIPS:
                entry["should_skip"] = True
                entry["consecutive_skips"] = consec + 1
                # Reduce LOD scale progressively
                entry["lod_scale"] = max(0.1, entry["lod_scale"] * 0.5)
            else:
                # Consecutive skip cap reached — force compute next frame
                entry["should_skip"] = False
                entry["consecutive_skips"] = 0
        else:
            # Within budget — reset skip and gradually recover LOD
            entry["should_skip"] = False
            entry["consecutive_skips"] = 0
            entry["lod_scale"] = min(1.0, entry["lod_scale"] * 1.1)

    def get_status(self) -> dict:
        """Return full budget status for debug overlay."""
        return {
            name: {
                "budget_ms": e["budget_ms"],
                "should_skip": e["should_skip"],
                "consecutive_skips": e["consecutive_skips"],
                "lod_scale": round(e["lod_scale"], 3),
            }
            for name, e in self._effects.items()
        }


# ---------------------------------------------------------------------------
# RenderEngine
# ---------------------------------------------------------------------------

class RenderEngine:
    """
    Main 60 FPS render loop. Drives window, timing, and EffectChain.

    Loop structure (derived from vjlive/core/app/app.py lines 2799-2874):
        poll_events → frame_callbacks → input_texture → effect_chain.render
        → render_to_screen → swap_buffers → profiler.tick → fps_cap sleep
    """

    METADATA: dict = {
        "spec": "P1-R5",
        "tier": "Pro-Tier Native",
        "module": "vjlive3.render.engine",
    }

    def __init__(
        self,
        context: object,
        effect_chain: object,
        target_fps: float = 60.0,
        audio_reactor: Optional[object] = None,
    ) -> None:
        self._ctx = context
        self._chain = effect_chain
        self._target_fps = target_fps
        self._audio_reactor = audio_reactor

        self._running: bool = False
        self._lock = threading.Lock()

        self._frame_time: float = 0.0
        self._fps: float = 0.0
        self._total_frames: int = 0

        self._profiler = FrameProfiler()
        self._budget = FrameBudgetAllocator(target_fps=int(target_fps))

        self._frame_callbacks: list = []
        self._input_texture_callback: Optional[Callable] = None

        # FPS rolling measurement
        self._fps_timestamps: deque = deque(maxlen=120)
        self._low_fps_count: int = 0

    # ---- Configuration API -------------------------------------------------

    def set_frame_callback(self, cb: Callable[["RenderEngine"], None]) -> None:
        """Register a per-frame callback (MIDI sync, agent bridge, etc.)."""
        self._frame_callbacks.append(cb)

    def set_input_texture_callback(self, cb: Callable[[], Optional[object]]) -> None:
        """Register callback that returns current input texture view per frame."""
        self._input_texture_callback = cb

    # ---- Main Loop ---------------------------------------------------------

    def run(self) -> None:
        """Enter the main render loop. Blocks until window close or stop()."""
        target_frame_time = 1.0 / self._target_fps
        last_loop_time = time.time()
        self._running = True

        logger.info("RenderEngine: starting at %.0f FPS target", self._target_fps)

        while self._running and not self._ctx.should_close():
            frame_start = time.time()

            # 1. Delta time — clamped to 100 ms to prevent jumps after hangs
            self._frame_time = min(frame_start - last_loop_time, 0.1)
            last_loop_time = frame_start

            # 2. Window events
            self._ctx.poll_events()

            # 3. Per-frame callbacks
            for cb in self._frame_callbacks:
                try:
                    cb(self)
                except Exception as exc:
                    logger.error("RenderEngine: frame callback raised: %s", exc)

            # 4. Get input texture
            input_tex = None
            if self._input_texture_callback is not None:
                try:
                    input_tex = self._input_texture_callback()
                except Exception as exc:
                    logger.debug("RenderEngine: input_texture_callback raised: %s", exc)

            # 5. Render effect chain — exceptions must not crash the loop
            try:
                with self._profiler.time("effects"):
                    output_tex = self._chain.render(
                        input_tex, audio_reactor=self._audio_reactor
                    )
            except Exception as exc:
                logger.error("RenderEngine: effect chain raised: %s", exc)
                output_tex = input_tex

            # 6. Blit to screen
            w: int = getattr(self._ctx, "width", 1920)
            h: int = getattr(self._ctx, "height", 1080)
            try:
                with self._profiler.time("screen"):
                    self._chain.render_to_screen(output_tex, (0, 0, w, h))
                    self._ctx.swap_buffers()
            except Exception as exc:
                logger.error("RenderEngine: render_to_screen raised: %s", exc)

            # 7. Profiler + FPS
            self._profiler.tick()
            self._total_frames += 1
            self._update_fps(frame_start)

            # 8. FPS cap — sleep the remainder of the frame budget
            elapsed = time.time() - frame_start
            sleep_time = target_frame_time - elapsed
            if sleep_time > 0.0:
                time.sleep(sleep_time)
            else:
                total_ms = elapsed * 1000.0
                if total_ms > 16.67:
                    logger.debug("RenderEngine: frame %.1f ms > 16.67 ms budget", total_ms)

        self._ctx.terminate()
        logger.info(
            "RenderEngine: stopped — %d frames, FPS=%.1f",
            self._total_frames, self._fps,
        )

    def stop(self) -> None:
        """Request clean loop exit. Thread-safe."""
        self._running = False

    # ---- FPS Measurement ---------------------------------------------------

    def _update_fps(self, frame_start: float) -> None:
        now = time.time()
        self._fps_timestamps.append(now)
        # Count frames in the last 1 second
        cutoff = now - 1.0
        recent = sum(1 for t in self._fps_timestamps if t >= cutoff)
        self._fps = float(recent)

        if self._fps < _FPS_WARN_THRESHOLD:
            self._low_fps_count += 1
            if self._low_fps_count >= _SUSTAINED_LOW_FPS_FRAMES:
                logger.warning(
                    "RenderEngine: sustained FPS below %.0f (current %.1f)",
                    _FPS_WARN_THRESHOLD, self._fps,
                )
                self._low_fps_count = 0
        else:
            self._low_fps_count = 0

    # ---- Read-only properties ----------------------------------------------

    @property
    def frame_time(self) -> float:
        """Delta time of the previous frame in seconds. Clamped to 0.1s max."""
        return self._frame_time

    @property
    def fps(self) -> float:
        """Measured FPS averaged over the last 1 second."""
        return self._fps

    @property
    def total_frames(self) -> int:
        """Total frames rendered since run() was called."""
        return self._total_frames

    @property
    def profiler(self) -> FrameProfiler:
        return self._profiler

    @property
    def budget(self) -> FrameBudgetAllocator:
        return self._budget
