"""Logging utilities for VJLive3.

Uses loguru if installed (production), falls back to stdlib logging
for headless/test/CI environments where loguru is not available.

All modules should use get_logger() — it works regardless of whether
loguru is installed.
"""
from __future__ import annotations

import logging as _stdlib_logging
import sys
from pathlib import Path
from typing import Optional, Union

# Try loguru — if not installed, use stdlib shim
try:
    from loguru import logger as _loguru_logger
    _LOGURU_AVAILABLE = True
except ImportError:
    _loguru_logger = None
    _LOGURU_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
#  Stdlib shim — identical interface to loguru for our usage
# ─────────────────────────────────────────────────────────────

class _StdlibLogger:
    """Minimal loguru-compatible logger backed by stdlib."""

    def __init__(self, name: str = "vjlive3") -> None:
        self._log = _stdlib_logging.getLogger(name)

    def bind(self, **kwargs: object) -> "_StdlibLogger":
        name = kwargs.get("name", self._log.name)
        return _StdlibLogger(str(name))

    def debug(self, msg: str, *args: object, **kwargs: object) -> None:
        self._log.debug(msg, *args)

    def info(self, msg: str, *args: object, **kwargs: object) -> None:
        self._log.info(msg, *args)

    def warning(self, msg: str, *args: object, **kwargs: object) -> None:
        self._log.warning(msg, *args)

    def error(self, msg: str, *args: object, **kwargs: object) -> None:
        self._log.error(msg, *args)

    def critical(self, msg: str, *args: object, **kwargs: object) -> None:
        self._log.critical(msg, *args)

    def exception(self, msg: str, *args: object, **kwargs: object) -> None:
        self._log.exception(msg, *args)

    # loguru compatibility stubs
    def remove(self, *args: object) -> None:  # noqa: D401
        return None  # stdlib has no global remove — no-op

    def add(self, *args: object, **kwargs: object) -> None:
        return None  # loguru-style sink adding — no-op in stdlib mode


# Active logger backend
_logger: Union["_StdlibLogger", object] = (
    _loguru_logger if _LOGURU_AVAILABLE else _StdlibLogger("vjlive3")
)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
) -> None:
    """Configure logging for the application.

    Works with both loguru (production) and stdlib (headless/CI).

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        rotation: Log rotation size/time (loguru only)
        retention: Log retention period (loguru only)
    """
    if _LOGURU_AVAILABLE:
        _loguru_logger.remove()
        _loguru_logger.add(
            sys.stderr,
            level=level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            colorize=True,
        )
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            _loguru_logger.add(
                str(log_file),
                level=level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                       "{name}:{function}:{line} - {message}",
                rotation=rotation,
                retention=retention,
                compression="zip",
            )
    else:
        # Stdlib fallback — basic config
        _stdlib_logging.basicConfig(
            level=getattr(_stdlib_logging, level, _stdlib_logging.INFO),
            format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
            stream=sys.stderr,
        )
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = _stdlib_logging.FileHandler(str(log_file))
            fh.setLevel(level)
            _stdlib_logging.getLogger().addHandler(fh)

    get_logger(__name__).info(
        "Logging configured at level %s (backend: %s)",
        level, "loguru" if _LOGURU_AVAILABLE else "stdlib",
    )


def get_logger(name: str) -> "_StdlibLogger":
    """Get a logger instance for the given module name.

    Works identically whether loguru is installed or not.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger with .debug/.info/.warning/.error/.exception methods
    """
    if _LOGURU_AVAILABLE:
        return _loguru_logger.bind(name=name)
    return _StdlibLogger(name)