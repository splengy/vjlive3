"""P1-P5 — Plugin Sandbox

Wraps plugin process() calls in safety boundaries so misbehaving plugins
cannot crash the engine.  14ms frame budget, 5-error auto-disable.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from vjlive3.plugins.registry import PluginRegistry

_log = logging.getLogger(__name__)

_DEFAULT_BUDGET_MS = 14.0   # must finish in < 14ms for stable 60fps
_DEFAULT_MAX_ERRORS = 5


@dataclass
class SandboxResult:
    success:    bool
    output:     Optional[np.ndarray]   # None on failure
    error:      Optional[str]          # None on success
    elapsed_ms: float


@dataclass
class _PluginStats:
    error_count:  int = 0
    disabled:     bool = False
    total_calls:  int = 0
    total_ms:     float = 0.0
    instance:     Optional[Any] = None   # cached instance

    @property
    def avg_ms(self) -> float:
        return (self.total_ms / self.total_calls) if self.total_calls else 0.0


class PluginSandbox:
    """Safe call wrapper for plugin process() execution.

    >>> import numpy as np
    >>> reg = _make_registry()   # doctest: +SKIP
    """

    def __init__(
        self,
        registry: PluginRegistry,
        frame_budget_ms: float = _DEFAULT_BUDGET_MS,
        max_errors: int = _DEFAULT_MAX_ERRORS,
    ) -> None:
        self._registry = registry
        self._budget_ms = frame_budget_ms
        self._max_errors = max_errors
        self._stats: Dict[str, _PluginStats] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def call(
        self,
        plugin_name: str,
        frame: np.ndarray,
        audio_data: Any = None,
        **kwargs: Any,
    ) -> SandboxResult:
        """Call plugin safely.  Never raises."""
        stats = self._get_stats(plugin_name)

        if stats.disabled:
            return SandboxResult(
                success=False,
                output=None,
                error=f"Plugin '{plugin_name}' is disabled",
                elapsed_ms=0.0,
            )

        cls = self._registry.get(plugin_name)
        if cls is None:
            return SandboxResult(
                success=False,
                output=None,
                error=f"Plugin '{plugin_name}' not in registry",
                elapsed_ms=0.0,
            )

        # Lazy-instantiate
        if stats.instance is None:
            try:
                stats.instance = cls()
                self._registry.increment_instance_count(plugin_name)
            except Exception as exc:
                return self._record_error(plugin_name, stats, frame, str(exc))

        # Call process()
        t0 = time.perf_counter()
        try:
            output: np.ndarray = stats.instance.process(frame, audio_data, **kwargs)
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            stats.total_calls += 1
            return self._record_error(plugin_name, stats, frame, str(exc), elapsed)

        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Validate output shape
        if not isinstance(output, np.ndarray) or output.shape != frame.shape:
            _log.warning(
                "Plugin '%s' returned wrong shape %s (expected %s) — using input",
                plugin_name,
                getattr(output, "shape", type(output)),
                frame.shape,
            )
            output = frame

        stats.total_calls += 1
        stats.total_ms += elapsed_ms

        if elapsed_ms > self._budget_ms:
            _log.warning(
                "Plugin '%s' exceeded frame budget: %.1fms > %.1fms",
                plugin_name, elapsed_ms, self._budget_ms,
            )

        return SandboxResult(success=True, output=output, error=None, elapsed_ms=elapsed_ms)

    def disable(self, plugin_name: str) -> None:
        """Manually disable a plugin."""
        self._get_stats(plugin_name).disabled = True
        _log.info("Plugin '%s' manually disabled", plugin_name)

    def enable(self, plugin_name: str) -> None:
        """Re-enable a disabled plugin.  Clears error count."""
        stats = self._get_stats(plugin_name)
        stats.disabled = False
        stats.error_count = 0
        _log.info("Plugin '%s' re-enabled", plugin_name)

    def is_disabled(self, plugin_name: str) -> bool:
        return self._get_stats(plugin_name).disabled

    def error_count(self, plugin_name: str) -> int:
        return self._get_stats(plugin_name).error_count

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Return per-plugin stats dict."""
        return {
            name: {
                "error_count": s.error_count,
                "avg_ms":      round(s.avg_ms, 2),
                "total_calls": s.total_calls,
                "disabled":    s.disabled,
            }
            for name, s in self._stats.items()
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _get_stats(self, name: str) -> _PluginStats:
        if name not in self._stats:
            self._stats[name] = _PluginStats()
        return self._stats[name]

    def _record_error(
        self,
        name: str,
        stats: _PluginStats,
        frame: np.ndarray,
        error_msg: str,
        elapsed_ms: float = 0.0,
    ) -> SandboxResult:
        stats.error_count += 1
        _log.error("Plugin '%s' error (%d/%d): %s", name, stats.error_count, self._max_errors, error_msg)

        if stats.error_count >= self._max_errors:
            stats.disabled = True
            stats.instance = None  # release instance
            _log.warning(
                "Plugin '%s' disabled after %d consecutive errors",
                name, self._max_errors,
            )

        return SandboxResult(
            success=False,
            output=None,
            error=error_msg,
            elapsed_ms=elapsed_ms,
        )


__all__ = ["PluginSandbox", "SandboxResult"]
