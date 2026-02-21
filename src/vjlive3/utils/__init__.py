"""Utility modules for VJLive3.

Submodules:
- logging: Logging utilities (always available — stdlib fallback)
- image: Image processing utilities (requires opencv/numpy)
- perf: Performance monitoring (requires psutil)
- security: Security utilities (stdlib only)

Note: All submodules except logging are lazily imported to avoid
loading opencv/psutil at package import time in headless environments.
"""
from __future__ import annotations

# Logging is always safe — it has a stdlib fallback
from vjlive3.utils.logging import setup_logging, get_logger

__all__ = [
    "setup_logging",
    "get_logger",
    "resize_frame",
    "convert_color",
    "validate_frame",
    "Timer",
    "PerformanceMonitor",
    "sanitize_filename",
    "validate_path",
]


def __getattr__(name: str) -> object:
    """Lazy import for hardware-dependent utilities."""
    if name in ("resize_frame", "convert_color", "validate_frame"):
        from vjlive3.utils.image import resize_frame, convert_color, validate_frame
        return locals()[name]
    if name in ("Timer", "PerformanceMonitor"):
        from vjlive3.utils.perf import Timer, PerformanceMonitor
        return locals()[name]
    if name in ("sanitize_filename", "validate_path"):
        from vjlive3.utils.security import sanitize_filename, validate_path
        return locals()[name]
    raise AttributeError(f"module 'vjlive3.utils' has no attribute {name!r}")