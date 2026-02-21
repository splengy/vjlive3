"""
Plugin Runtime Safety Wrapper for VJLive3 — P1-P5.

Per-frame plugin call wrapper with:
  - Error budget: auto-disables plugin after N consecutive failures
  - Frame budget warning: logs if plugin exceeds time limit
  - Lazy instance caching
  - Output shape validation (must match input frame)
  - Full per-plugin stats

This is NOT an import-time sandbox (see sandbox.py).
This runs EVERY FRAME and must be near-zero overhead on the happy path.

Source: Spec docs/specs/P1-P5_plugin_sandbox.md
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np

from vjlive3.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class SandboxResult:
    """
    Result of a safely-wrapped plugin call.

    Attributes:
        success:    True if plugin.process() completed without error.
        output:     Processed frame (same shape as input), or None on failure.
        error:      Error message on failure, None on success.
        elapsed_ms: Wall-clock time for the process() call in milliseconds.
    """
    success: bool
    output: Optional[np.ndarray]
    error: Optional[str]
    elapsed_ms: float


# ---------------------------------------------------------------------------
# Per-plugin stats
# ---------------------------------------------------------------------------

@dataclass
class PluginStats:
    error_count: int = 0
    disabled: bool = False
    total_calls: int = 0
    total_ms: float = 0.0
    last_error: Optional[str] = None
    instance: Any = field(default=None, repr=False)

    @property
    def avg_ms(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_ms / self.total_calls


# ---------------------------------------------------------------------------
# Runtime sandbox
# ---------------------------------------------------------------------------

class PluginRuntime:
    """
    Per-frame plugin call wrapper with error budget and auto-disable.

    Usage::

        runtime = PluginRuntime(registry, frame_budget_ms=14.0, max_errors=5)

        result = runtime.call("my_effect", frame, audio_data)
        if result.success:
            frame = result.output

    Source: docs/specs/P1-P5_plugin_sandbox.md
    """

    def __init__(
        self,
        registry: PluginRegistry,
        frame_budget_ms: float = 14.0,
        max_errors: int = 5,
    ) -> None:
        """
        Args:
            registry:        Source of plugin classes.
            frame_budget_ms: Warn if plugin process() takes longer than this.
                             At 60fps each frame is 16.67ms; 14ms leaves 2ms margin.
            max_errors:      Disable plugin after this many consecutive errors.
        """
        self._registry = registry
        self.frame_budget_ms = frame_budget_ms
        self.max_errors = max_errors
        self._stats: Dict[str, PluginStats] = {}

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _get_stats(self, plugin_name: str) -> PluginStats:
        if plugin_name not in self._stats:
            self._stats[plugin_name] = PluginStats()
        return self._stats[plugin_name]

    def _get_instance(self, plugin_name: str, stats: PluginStats) -> Optional[Any]:
        """Lazy-instantiate and cache plugin instance."""
        if stats.instance is not None:
            return stats.instance

        cls = self._registry.get(plugin_name)
        if cls is None:
            return None

        try:
            stats.instance = cls()
            return stats.instance
        except Exception as exc:
            logger.error("[runtime] Failed to instantiate %s: %s", plugin_name, exc)
            return None

    # ── Public API ────────────────────────────────────────────────────────────

    def call(
        self,
        plugin_name: str,
        frame: np.ndarray,
        audio_data: Any = None,
        **kwargs: Any,
    ) -> SandboxResult:
        """
        Call a plugin's process() safely. Never raises.

        Safety sequence:
          1. Disabled? → return failure immediately
          2. Not in registry? → return failure
          3. Lazy-init instance
          4. Time the process() call
          5. Exception? → increment error_count; auto-disable at max_errors
          6. Wrong output shape? → return input frame, log warning
          7. Exceeds frame_budget_ms? → log warning (not an error)

        Args:
            plugin_name: Registered plugin name.
            frame:       Input frame uint8 RGBA (H, W, 4) or float32.
            audio_data:  AudioSnapshot or None.
            **kwargs:    Forwarded to plugin.process().

        Returns:
            SandboxResult — always.
        """
        stats = self._get_stats(plugin_name)

        # 1 — Disabled check
        if stats.disabled:
            return SandboxResult(
                success=False,
                output=None,
                error="disabled",
                elapsed_ms=0.0,
            )

        # 2 — Registry check + lazy instantiation
        instance = self._get_instance(plugin_name, stats)
        if instance is None:
            return SandboxResult(
                success=False,
                output=None,
                error=f"Plugin '{plugin_name}' not found in registry",
                elapsed_ms=0.0,
            )

        # 3 — Timed call
        stats.total_calls += 1
        t0 = time.perf_counter()

        try:
            output = instance.process(frame, audio_data, **kwargs)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            stats.total_ms += elapsed_ms

            # 4 — Validate output shape
            if not isinstance(output, np.ndarray) or output.shape != frame.shape:
                logger.warning(
                    "[runtime] %s returned wrong shape %s (expected %s) — using input frame",
                    plugin_name,
                    getattr(output, "shape", type(output)),
                    frame.shape,
                )
                stats.error_count = 0  # shape mismatch isn't a crash
                if elapsed_ms > self.frame_budget_ms:
                    logger.warning(
                        "[runtime] %s exceeded budget: %.1f ms > %.1f ms",
                        plugin_name, elapsed_ms, self.frame_budget_ms,
                    )
                return SandboxResult(
                    success=False,
                    output=frame,
                    error="wrong output shape",
                    elapsed_ms=elapsed_ms,
                )

            # 5 — Budget warning
            if elapsed_ms > self.frame_budget_ms:
                logger.warning(
                    "[runtime] %s exceeded budget: %.1f ms > %.1f ms",
                    plugin_name, elapsed_ms, self.frame_budget_ms,
                )

            # 6 — Happy path
            stats.error_count = 0  # reset consecutive error counter on success
            return SandboxResult(
                success=True,
                output=output,
                error=None,
                elapsed_ms=elapsed_ms,
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            stats.total_ms += elapsed_ms
            stats.error_count += 1
            stats.last_error = str(exc)

            logger.error(
                "[runtime] %s raised (error %d/%d): %s",
                plugin_name, stats.error_count, self.max_errors, exc,
            )

            if stats.error_count >= self.max_errors:
                stats.disabled = True
                logger.error(
                    "[runtime] Plugin %s DISABLED after %d consecutive errors",
                    plugin_name, self.max_errors,
                )

            return SandboxResult(
                success=False,
                output=frame,   # return input frame unchanged
                error=str(exc),
                elapsed_ms=elapsed_ms,
            )

    def disable(self, plugin_name: str) -> None:
        """Manually disable a plugin. Immediate effect."""
        self._get_stats(plugin_name).disabled = True
        logger.info("[runtime] Plugin %s manually disabled", plugin_name)

    def enable(self, plugin_name: str) -> None:
        """Re-enable a previously disabled plugin. Also clears error count."""
        stats = self._get_stats(plugin_name)
        stats.disabled = False
        stats.error_count = 0
        logger.info("[runtime] Plugin %s re-enabled, error count cleared", plugin_name)

    def is_disabled(self, plugin_name: str) -> bool:
        """Return True if plugin is currently disabled."""
        return self._get_stats(plugin_name).disabled

    def error_count(self, plugin_name: str) -> int:
        """Return current consecutive error count for a plugin."""
        return self._get_stats(plugin_name).error_count

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Return per-plugin stats dict.

        Returns:
            {plugin_name: {"error_count": int, "avg_ms": float, "disabled": bool,
                           "total_calls": int, "last_error": str|None}}
        """
        return {
            name: {
                "error_count": s.error_count,
                "avg_ms": round(s.avg_ms, 3),
                "disabled": s.disabled,
                "total_calls": s.total_calls,
                "last_error": s.last_error,
            }
            for name, s in self._stats.items()
        }


__all__ = ["SandboxResult", "PluginRuntime"]
