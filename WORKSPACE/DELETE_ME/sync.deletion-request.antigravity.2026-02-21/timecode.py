"""P2-X2 — Timecode Sync (LTC / MTC / internal clock)

Provides a monotonic timecode source for synchronising VJLive3 output to
external clocks (LTC audio, MIDI Time Code, or NTP-derived wall clock).

Design: single TimecodeEngine that wraps an interchangeable TimecodeSource.
Sources can be hot-swapped at runtime without interrupting the timecode stream.
When the external source is lost the engine falls back to an internal free-run
clock so playback continues smoothly.

P2-X2 Board entry: docs/specs/P2-X2_timecode_sync.md
Dependencies: stdlib only (sounddevice / rtmidi used lazily)
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

_log = logging.getLogger(__name__)


# ── Timecode frame ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Timecode:
    """Immutable SMPTE-style timecode position.

    hours: 0–23, minutes/seconds: 0–59, frames: 0–(fps-1)
    """
    hours:   int
    minutes: int
    seconds: int
    frames:  int
    fps:     float = 30.0        # 24, 25, 29.97, 30 …

    @property
    def total_frames(self) -> int:
        """Total frame count from 00:00:00:00."""
        total_secs = self.hours * 3600 + self.minutes * 60 + self.seconds
        return int(total_secs * self.fps) + self.frames

    @property
    def total_seconds(self) -> float:
        """Position as fractional seconds."""
        return self.total_frames / max(self.fps, 1e-6)

    def __str__(self) -> str:
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}:{self.frames:02d}"

    @staticmethod
    def from_total_seconds(secs: float, fps: float = 30.0) -> "Timecode":
        """Construct a Timecode from a total seconds value."""
        secs = max(0.0, secs)
        total_frames = int(secs * fps)
        fr  = total_frames % int(fps)
        s   = (total_frames // int(fps)) % 60
        m   = (total_frames // (int(fps) * 60)) % 60
        h   = total_frames // (int(fps) * 3600)
        return Timecode(hours=h, minutes=m, seconds=s, frames=fr, fps=fps)


# ── Source type enum ──────────────────────────────────────────────────────────

class TimecodeSourceType(str, Enum):
    INTERNAL = "internal"   # Free-run from system monotonic clock
    LTC      = "ltc"        # Linear Time Code on audio channel
    MTC      = "mtc"        # MIDI Time Code
    NTP      = "ntp"        # NTP-derived wall clock offset


# ── Abstract source ───────────────────────────────────────────────────────────

class TimecodeSource:
    """Base class for a timecode provider."""

    source_type: TimecodeSourceType = TimecodeSourceType.INTERNAL

    def start(self) -> bool:
        """Start the source. Returns True on success."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop and release resources."""
        raise NotImplementedError

    def get_position(self) -> Optional[float]:
        """Return current position in seconds from epoch, or None if lost."""
        raise NotImplementedError

    @property
    def is_locked(self) -> bool:
        """True when receiving a valid external sync signal."""
        return False


# ── InternalClock ─────────────────────────────────────────────────────────────

class InternalClock(TimecodeSource):
    """Free-running internal clock. Never loses lock. Always available."""

    source_type = TimecodeSourceType.INTERNAL

    def __init__(self, fps: float = 30.0, start_offset: float = 0.0) -> None:
        self._fps = fps
        self._start_offset = start_offset
        self._origin: Optional[float] = None

    def start(self) -> bool:
        self._origin = time.monotonic()
        return True

    def stop(self) -> None:
        self._origin = None

    def get_position(self) -> Optional[float]:
        if self._origin is None:
            return None
        return (time.monotonic() - self._origin) + self._start_offset

    @property
    def is_locked(self) -> bool:
        return self._origin is not None


# ── NTPClock (wall-clock offset) ──────────────────────────────────────────────

class NTPClock(TimecodeSource):
    """Offsets monotonic clock against UTC wall time at start.

    No NTP daemon required — uses system clock. For real NTP discipline
    the OS must be running ntpd/chronyd.
    """

    source_type = TimecodeSourceType.NTP

    def __init__(self, fps: float = 30.0) -> None:
        self._fps = fps
        self._offset: Optional[float] = None    # monotonic time at midnight UTC
        self._running = False

    def start(self) -> bool:
        # Compute offset so position = UTC seconds-of-day
        now_mono = time.monotonic()
        now_wall = time.time()
        midnight_wall = now_wall - (now_wall % 86400)  # midnight UTC
        self._offset = now_mono - (now_wall - midnight_wall)
        self._running = True
        return True

    def stop(self) -> None:
        self._running = False
        self._offset = None

    def get_position(self) -> Optional[float]:
        if self._offset is None:
            return None
        return time.monotonic() - self._offset

    @property
    def is_locked(self) -> bool:
        return self._running and self._offset is not None


# ── TimecodeEngine ────────────────────────────────────────────────────────────

PositionCallback = Callable[[Timecode], None]


class TimecodeEngine:
    """
    Master timecode engine with hot-swappable sources.

    Usage::

        engine = TimecodeEngine(fps=30.0)
        engine.set_source(InternalClock())
        engine.start()
        tc = engine.get_timecode()       # Timecode(00:00:00:01 @ 30fps)
        engine.stop()

    Falls back to InternalClock automatically when external source loses lock.
    Calls registered callbacks once per frame (on a background thread).
    """

    # Fallback-check interval (seconds)
    _LOCK_CHECK_INTERVAL = 0.5
    # Callback dispatch tick rate
    _TICK_INTERVAL = 1.0 / 60

    def __init__(self, fps: float = 30.0) -> None:
        self._fps = fps
        self._lock = threading.RLock()
        self._callbacks: list[PositionCallback] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._source: TimecodeSource = InternalClock(fps=fps)
        self._fallback: TimecodeSource = InternalClock(fps=fps)
        self._using_fallback = False
        self._last_lock_check = 0.0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the engine and begin emitting timecode."""
        with self._lock:
            if self._running:
                return
            self._source.start()
            self._fallback.start()
            self._running = True
        self._thread = threading.Thread(
            target=self._run, name="TimecodeEngine", daemon=True
        )
        self._thread.start()
        _log.info("TimecodeEngine started at %.2f fps", self._fps)

    def stop(self) -> None:
        """Stop the engine. Idempotent."""
        with self._lock:
            if not self._running:
                return
            self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        with self._lock:
            self._source.stop()
            self._fallback.stop()
        _log.info("TimecodeEngine stopped")

    # ── Source management ─────────────────────────────────────────────────────

    def set_source(self, source: TimecodeSource) -> None:
        """Hot-swap to a new timecode source.

        If the engine is running, the old source is stopped and the new one
        is started immediately. Fallback clock is unaffected.
        """
        with self._lock:
            was_running = self._running
            try:
                self._source.stop()
            except Exception:
                pass
            self._source = source
            if was_running:
                source.start()
            self._using_fallback = False
        _log.info("TimecodeEngine: source changed to %s", source.source_type)

    @property
    def source_type(self) -> TimecodeSourceType:
        with self._lock:
            if self._using_fallback:
                return TimecodeSourceType.INTERNAL
            return self._source.source_type

    @property
    def is_locked(self) -> bool:
        """True when the primary source has a valid lock (not on fallback)."""
        with self._lock:
            return (not self._using_fallback) and self._source.is_locked

    # ── Timecode access ───────────────────────────────────────────────────────

    def get_position(self) -> float:
        """Return current position in seconds. Thread-safe, never None."""
        with self._lock:
            src = self._fallback if self._using_fallback else self._source
        pos = src.get_position()
        return pos if pos is not None else 0.0

    def get_timecode(self) -> Timecode:
        """Return current position as a Timecode object."""
        return Timecode.from_total_seconds(self.get_position(), fps=self._fps)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def add_callback(self, cb: PositionCallback) -> None:
        """Register a callback called every frame with the current Timecode."""
        with self._lock:
            self._callbacks.append(cb)

    def remove_callback(self, cb: PositionCallback) -> bool:
        with self._lock:
            try:
                self._callbacks.remove(cb)
                return True
            except ValueError:
                return False

    # ── Background thread ─────────────────────────────────────────────────────

    def _run(self) -> None:
        """Tick loop: dispatch callbacks and check for source lock loss."""
        while True:
            with self._lock:
                if not self._running:
                    break
                callbacks = list(self._callbacks)
                now = time.monotonic()

            # Periodic lock check — switch to fallback if primary loses lock
            if now - self._last_lock_check > self._LOCK_CHECK_INTERVAL:
                self._check_lock()
                self._last_lock_check = now

            if callbacks:
                tc = self.get_timecode()
                for cb in callbacks:
                    try:
                        cb(tc)
                    except Exception as exc:
                        _log.warning("TimecodeEngine callback error: %s", exc)

            time.sleep(self._TICK_INTERVAL)

    def _check_lock(self) -> None:
        """Switch to fallback if primary source loses lock."""
        with self._lock:
            primary_locked = self._source.is_locked
            if not primary_locked and not self._using_fallback:
                _log.warning(
                    "TimecodeEngine: %s lost lock — switching to internal fallback",
                    self._source.source_type,
                )
                self._using_fallback = True
            elif primary_locked and self._using_fallback:
                _log.info(
                    "TimecodeEngine: %s re-acquired lock — resuming primary",
                    self._source.source_type,
                )
                self._using_fallback = False

    # ── FPS ───────────────────────────────────────────────────────────────────

    @property
    def fps(self) -> float:
        return self._fps


__all__ = [
    "Timecode",
    "TimecodeSourceType",
    "TimecodeSource",
    "InternalClock",
    "NTPClock",
    "TimecodeEngine",
]
