"""
Phase-Locked Loop (PLL) Synchroniser

Provides smooth, jitter-corrected frame interpolation used by
TimecodeSync to lock to an external timecode source.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Deque, Dict, Tuple

logger = logging.getLogger(__name__)

_HISTORY_SIZE = 32  # samples kept for drift analysis


class PLLSync:
    """Phase-locked loop for timecode frame interpolation.

    The PLL tracks an external master (e.g. LTC/MTC stream) and
    interpolates smooth frame positions between received sync pulses.

    METADATA constant — Prime Directive Rule 2.
    """

    METADATA = {
        "name": "PLLSync",
        "description": "Phase-locked loop for smooth frame interpolation",
        "version": "1.0",
    }

    def __init__(self, target_fps: float = 30.0) -> None:
        if target_fps <= 0:
            raise ValueError(f"PLLSync: target_fps must be > 0, got {target_fps!r}")

        self._target_fps = target_fps
        self._master_frame: float = 0.0
        self._last_sync_time: float = 0.0
        self._last_sync_frame: float = 0.0

        # PLL state
        self._sync_offset: float = 0.0
        self._drift_rate: float = 0.0          # frames-per-second correction
        self._sync_quality: float = 0.0        # 0–1

        # Running history for drift estimation
        self._history: Deque[Tuple[float, float]] = deque(maxlen=_HISTORY_SIZE)

        logger.debug("PLLSync: initialised at %.2f fps", target_fps)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def target_fps(self) -> float:
        return self._target_fps

    @property
    def sync_quality(self) -> float:
        """0.0 = no sync, 1.0 = perfect lock."""
        return self._sync_quality

    @property
    def drift_rate(self) -> float:
        """Estimated drift in frames-per-second between master and local."""
        return self._drift_rate

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sync_to_master(self, frame: float, timestamp: float | None = None) -> None:
        """Receive a master frame tick and update PLL state.

        Args:
            frame:     The master frame number received.
            timestamp: Wall-clock time of receipt (defaults to now).
        """
        now = timestamp if timestamp is not None else time.monotonic()

        if self._last_sync_time > 0:
            dt = now - self._last_sync_time
            expected_frames = dt * self._target_fps
            actual_advance = frame - self._last_sync_frame

            # Drift: difference between how many frames we expected vs received
            drift = actual_advance - expected_frames
            self._history.append((now, drift))
            self._update_drift()

        self._master_frame = float(frame)
        self._last_sync_time = now
        self._last_sync_frame = float(frame)

        logger.debug("PLLSync.sync_to_master: frame=%.1f drift=%.4f", frame, self._drift_rate)

    def get_interpolated_frame(self) -> float:
        """Predict the current frame using elapsed time + drift correction."""
        if self._last_sync_time == 0.0:
            return self._master_frame

        elapsed = time.monotonic() - self._last_sync_time
        predicted = self._master_frame + elapsed * (self._target_fps + self._drift_rate)
        return predicted + self._sync_offset

    def set_sync_offset(self, offset: float) -> None:
        """Apply a manual frame offset (e.g. for sub-frame alignment)."""
        self._sync_offset = offset

    def reset(self) -> None:
        """Reset all PLL state to zero."""
        self._master_frame = 0.0
        self._last_sync_time = 0.0
        self._last_sync_frame = 0.0
        self._drift_rate = 0.0
        self._sync_quality = 0.0
        self._sync_offset = 0.0
        self._history.clear()
        logger.debug("PLLSync: reset")

    def get_stats(self) -> Dict[str, float]:
        """Return a snapshot of current PLL statistics."""
        return {
            "target_fps": self._target_fps,
            "master_frame": self._master_frame,
            "interpolated_frame": self.get_interpolated_frame(),
            "drift_rate": self._drift_rate,
            "sync_quality": self._sync_quality,
            "sync_offset": self._sync_offset,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_drift(self) -> None:
        """Recalculate drift rate and quality from history."""
        if len(self._history) < 2:
            return

        # Rolling average of recent drift samples
        drifts = [d for _, d in self._history]
        avg_drift = sum(drifts) / len(drifts)

        # Drift rate = frames/second correction needed
        if len(self._history) >= 2:
            span = self._history[-1][0] - self._history[0][0]
            total_drift = sum(drifts)
            self._drift_rate = total_drift / span if span > 0 else 0.0
        else:
            self._drift_rate = avg_drift

        # Sync quality: how consistent are the drift samples?
        if len(drifts) > 1:
            variance = sum((d - avg_drift) ** 2 for d in drifts) / len(drifts)
            # Map variance to quality: 0 variance → quality 1.0
            self._sync_quality = max(0.0, min(1.0, 1.0 / (1.0 + variance)))
        else:
            self._sync_quality = 0.5
