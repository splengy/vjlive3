"""
Timecode Synchronisation Engine

Manages multiple timecode source modes (INTERNAL / LTC / MTC / NTP / OSC)
with phase-locked loop interpolation and graceful hardware-absent fallback.
"""

from __future__ import annotations

import logging
import ntpath
import queue
import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional

from vjlive3.sync.pll import PLLSync

logger = logging.getLogger(__name__)


class TimecodeSource(Enum):
    """Available timecode sync sources."""

    INTERNAL = "internal"   # Wall-clock driven, no external hardware
    LTC = "ltc"             # Linear Timecode (audio input) — requires sounddevice
    MTC = "mtc"             # MIDI Timecode — requires python-rtmidi
    OSC = "osc"             # OSC-driven master (another VJLive3 node)
    NTP = "ntp"             # Network Time Protocol — requires ntplib or WS fallback


class TimecodeSync:
    """Full timecode synchronisation manager with PLL smoothing.

    Supports five source modes. LTC and MTC require hardware; they
    fall back gracefully to INTERNAL if the device is absent.

    Usage::

        ts = TimecodeSync(source=TimecodeSource.INTERNAL, fps=30.0)
        ts.start()
        # every frame:
        ts.update(dt=1/60)
        print(ts.get_timecode_string())  # "00:00:01:12"
        ts.stop()

    METADATA constant — Prime Directive Rule 2.
    """

    METADATA = {
        "name": "TimecodeSync",
        "description": "Multi-source timecode sync with PLL interpolation",
        "version": "1.0",
    }

    def __init__(
        self,
        source: TimecodeSource = TimecodeSource.INTERNAL,
        fps: float = 30.0,
    ) -> None:
        if fps <= 0:
            raise ValueError(f"TimecodeSync: fps must be > 0, got {fps!r}")

        self.source = source
        self.fps = fps

        self._pll = PLLSync(target_fps=fps)

        # State
        self._running = False
        self._current_frame: int = 0
        self._current_timecode: str = "00:00:00:00"
        self._internal_start: float = 0.0
        self._smoothed_tc: Optional[str] = None

        # Threading
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._cmd_queue: queue.Queue[Dict[str, Any]] = queue.Queue()

        # Callbacks
        self._sync_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._error_callback: Optional[Callable[[str], None]] = None

        # Buffer (frame, tc-string) for smoothing
        self._tc_buffer: queue.Queue[tuple[int, str]] = queue.Queue(maxsize=16)

        # Hardware-specific handles (initialised on start)
        self._ltc_handle: Any = None
        self._mtc_handle: Any = None

        logger.info("TimecodeSync: %s @ %.2f fps", source.value, fps)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def smoothed_timecode(self) -> Optional[str]:
        return self._smoothed_tc

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Start the timecode engine.

        Returns True on success.  Hardware failures fall back to INTERNAL.
        """
        if self._running:
            logger.warning("TimecodeSync.start: already running")
            return True

        self._internal_start = time.monotonic()
        self._running = True
        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._sync_loop,
            daemon=True,
            name="TimecodeSync",
        )
        self._thread.start()

        if self.source == TimecodeSource.LTC:
            self._start_ltc()
        elif self.source == TimecodeSource.MTC:
            self._start_mtc()
        elif self.source == TimecodeSource.NTP:
            self._start_ntp()

        logger.info("TimecodeSync: started — source=%s", self.source.value)
        return True

    def stop(self) -> None:
        """Stop the engine cleanly."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._ltc_handle is not None:
            try:
                self._ltc_handle.stop()
            except Exception:  # noqa: BLE001
                pass
            self._ltc_handle = None

        if self._mtc_handle is not None:
            try:
                self._mtc_handle.close()
            except Exception:  # noqa: BLE001
                pass
            self._mtc_handle = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        logger.info("TimecodeSync: stopped")

    # ------------------------------------------------------------------
    # Per-frame update (call this every render frame)
    # ------------------------------------------------------------------

    def update(self, dt: float = 1.0 / 60.0) -> None:
        """Advance internal state by *dt* seconds (call once per frame)."""
        if not self._running:
            return

        if self.source == TimecodeSource.INTERNAL:
            elapsed = time.monotonic() - self._internal_start
            frame = int(elapsed * self.fps)
            self._current_frame = frame
            self._pll.sync_to_master(frame)
            self._push_to_buffer(frame, self.get_timecode_string())

        # Apply smoothing and quality check
        self._smooth_timecode()
        stats = self._pll.get_stats()

        if (
            stats["sync_quality"] > 0.8
            and self._sync_callback is not None
            and self._smoothed_tc is not None
        ):
            self._sync_callback(
                {
                    "frame": self._current_frame,
                    "timecode": self._smoothed_tc,
                    "quality": stats["sync_quality"],
                }
            )

    # ------------------------------------------------------------------
    # External frame injection (OSC / LTC / MTC callbacks land here)
    # ------------------------------------------------------------------

    def receive_frame(self, frame: int, tc_string: str = "") -> None:
        """Inject a timecode frame received from hardware or network."""
        self._current_frame = frame
        self._current_timecode = tc_string or self._frame_to_string(frame)
        self._pll.sync_to_master(float(frame))
        self._push_to_buffer(frame, self._current_timecode)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_frame_number(self) -> int:
        """Current frame counter (integer)."""
        return self._current_frame

    def get_timecode_string(self) -> str:
        """Current timecode in HH:MM:SS:FF format."""
        if self.source == TimecodeSource.INTERNAL:
            return self._frame_to_string(self._current_frame)
        return self._current_timecode

    def get_sync_quality(self) -> float:
        """PLL sync quality 0–1."""
        return self._pll.sync_quality

    def get_stats(self) -> Dict[str, Any]:
        """Full stats dict (source, fps, timecode, PLL metrics, …)."""
        pll_stats = self._pll.get_stats()
        return {
            "source": self.source.value,
            "fps": self.fps,
            "running": self._running,
            "frame": self._current_frame,
            "timecode": self.get_timecode_string(),
            "smoothed_timecode": self._smoothed_tc,
            **pll_stats,
        }

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------

    def set_sync_callback(self, fn: Callable[[Dict[str, Any]], None]) -> None:
        self._sync_callback = fn

    def set_error_callback(self, fn: Callable[[str], None]) -> None:
        self._error_callback = fn

    def set_sync_offset(self, offset: float) -> None:
        """Forward a manual frame offset to the PLL."""
        self._pll.set_sync_offset(offset)

    def reset(self) -> None:
        """Reset frame counters and PLL state to zero."""
        self._current_frame = 0
        self._current_timecode = "00:00:00:00"
        self._smoothed_tc = None
        self._internal_start = time.monotonic()
        self._pll.reset()
        # Drain buffer
        while not self._tc_buffer.empty():
            try:
                self._tc_buffer.get_nowait()
            except queue.Empty:
                break
        logger.info("TimecodeSync: reset")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _sync_loop(self) -> None:
        """Background 60 Hz coordination thread."""
        interval = 1.0 / 60.0
        while self._running and not self._stop_event.is_set():
            try:
                self._process_commands()
            except Exception as exc:  # noqa: BLE001
                logger.error("TimecodeSync._sync_loop: %s", exc)
            self._stop_event.wait(timeout=interval)

    def _process_commands(self) -> None:
        """Drain the command queue."""
        try:
            while True:
                cmd = self._cmd_queue.get_nowait()
                ctype = cmd.get("type")
                if ctype == "set_offset":
                    self._pll.set_sync_offset(cmd["offset"])
                elif ctype == "reset":
                    self.reset()
        except queue.Empty:
            pass

    def _push_to_buffer(self, frame: int, tc: str) -> None:
        """Add a (frame, tc) sample to the smoothing buffer."""
        if self._tc_buffer.full():
            try:
                self._tc_buffer.get_nowait()
            except queue.Empty:
                pass
        try:
            self._tc_buffer.put_nowait((frame, tc))
        except queue.Full:
            pass

    def _smooth_timecode(self) -> None:
        """Compute a smoothed timecode string from the buffer."""
        samples: list[tuple[int, str]] = []
        while not self._tc_buffer.empty():
            try:
                samples.append(self._tc_buffer.get_nowait())
            except queue.Empty:
                break

        if samples:
            avg_frame = int(sum(f for f, _ in samples) / len(samples))
            self._smoothed_tc = self._frame_to_string(avg_frame)

    def _frame_to_string(self, frame: int) -> str:
        """Convert a raw frame number → HH:MM:SS:FF."""
        fps = int(self.fps)
        ff = frame % fps
        total_seconds = frame // fps
        ss = total_seconds % 60
        mm = (total_seconds // 60) % 60
        hh = total_seconds // 3600
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

    # ------------------------------------------------------------------
    # Hardware source initialisers — graceful fallback on ImportError
    # ------------------------------------------------------------------

    def _start_ltc(self) -> None:
        """Attempt to init LTC audio input.  Falls back to INTERNAL on failure."""
        try:
            import sounddevice as sd  # noqa: F401 — availability check only

            # Real LTC requires a bitstream decoder (e.g. ltc-tools or custom).
            # We register a placeholder callback via sounddevice; future work
            # when hardware is present will wire the actual LTC decoder.
            logger.info(
                "TimecodeSync: LTC source requested — sounddevice available, "
                "hardware decoder not yet wired; falling back to INTERNAL"
            )
        except ImportError:
            logger.warning("TimecodeSync: sounddevice not available — LTC fallback to INTERNAL")

        # Fall back to wall-clock so the engine still runs
        self.source = TimecodeSource.INTERNAL
        self._internal_start = time.monotonic()

    def _start_mtc(self) -> None:
        """Attempt to open an MTC MIDI input.  Falls back to INTERNAL on failure."""
        try:
            import rtmidi  # type: ignore[import]

            midi_in = rtmidi.MidiIn()
            ports = midi_in.get_ports()
            if not ports:
                raise OSError("No MIDI ports found for MTC")

            def _on_midi(message: tuple[list[int], float], _: Any = None) -> None:
                data, _ = message  # type: ignore[misc]
                # MTC quarter-frame messages (0xF1)
                if data and data[0] == 0xF1:
                    # Accumulate quarter frames — simplified: inject every 8 msgs
                    pass  # Full MTC accumulator reserved for Phase 3 hardware work

            self._mtc_handle = midi_in
            midi_in.open_port(0)
            midi_in.set_callback(_on_midi)
            logger.info("TimecodeSync: MTC listening on port 0 (%s)", ports[0])
        except (ImportError, OSError) as exc:
            logger.warning("TimecodeSync: MTC unavailable (%s) — fallback to INTERNAL", exc)
            self.source = TimecodeSource.INTERNAL
            self._internal_start = time.monotonic()

    def _start_ntp(self) -> None:
        """Sync one-shot to NTP, then run INTERNAL from that base."""
        try:
            import ntplib  # type: ignore[import]

            client = ntplib.NTPClient()
            response = client.request("pool.ntp.org", version=3, timeout=2.0)
            offset = response.offset  # seconds difference from NTP
            self._internal_start = time.monotonic() - offset
            logger.info("TimecodeSync: NTP sync OK — offset %.4f s", offset)
        except Exception as exc:  # noqa: BLE001
            logger.warning("TimecodeSync: NTP sync failed (%s) — using local clock", exc)
            self._internal_start = time.monotonic()
