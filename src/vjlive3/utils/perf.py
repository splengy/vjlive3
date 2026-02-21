"""Performance monitoring utilities.

This module provides tools for measuring and tracking performance metrics
such as execution time, memory usage, and frame rates.
"""

import time
import psutil
import tracemalloc
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class PerformanceMetrics:
    """Container for performance metrics.

    Attributes:
        elapsed_time: Total elapsed time in seconds
        iterations: Number of iterations
        avg_time: Average time per iteration
        min_time: Minimum iteration time
        max_time: Maximum iteration time
        memory_peak: Peak memory usage in bytes
        memory_current: Current memory usage in bytes
    """

    elapsed_time: float = 0.0
    iterations: int = 0
    avg_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    memory_peak: int = 0
    memory_current: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "elapsed_time": self.elapsed_time,
            "iterations": self.iterations,
            "avg_time": self.avg_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "memory_peak": self.memory_peak,
            "memory_current": self.memory_current,
        }


class Timer:
    """Simple timer for measuring execution time.

    Example:
        >>> timer = Timer()
        >>> with timer:
        ...     do_work()
        >>> print(f"Time: {timer.elapsed:.4f}s")
    """

    def __init__(self):
        """Initialize timer."""
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._elapsed: float = 0.0

    def start(self) -> None:
        """Start the timer."""
        self._start_time = time.perf_counter()
        self._end_time = None

    def stop(self) -> float:
        """Stop the timer and return elapsed time.

        Returns:
            Elapsed time in seconds
        """
        if self._start_time is None:
            raise RuntimeError("Timer not started")

        self._end_time = time.perf_counter()
        self._elapsed = self._end_time - self._start_time
        return self._elapsed

    def reset(self) -> None:
        """Reset timer to initial state."""
        self._start_time = None
        self._end_time = None
        self._elapsed = 0.0

    @property
    def elapsed(self) -> float:
        """Get elapsed time."""
        if self._start_time is not None and self._end_time is None:
            return time.perf_counter() - self._start_time
        return self._elapsed

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class PerformanceMonitor:
    """Monitor performance metrics over multiple iterations.

    Example:
        >>> monitor = PerformanceMonitor()
        >>> for i in range(100):
        ...     with monitor:
        ...         process_frame(frame)
        >>> stats = monitor.get_statistics()
        >>> print(f"Average: {stats['avg_time']:.4f}s")
    """

    def __init__(self, track_memory: bool = False):
        """Initialize performance monitor.

        Args:
            track_memory: If True, track memory usage (slower)
        """
        self.track_memory = track_memory
        self._times: List[float] = []
        self._start_time: Optional[float] = None
        self._tracemalloc_started = False

        if track_memory:
            tracemalloc.start()
            self._tracemalloc_started = True

    def __enter__(self):
        """Start timing."""
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record."""
        if self._start_time is None:
            return

        elapsed = time.perf_counter() - self._start_time
        self._times.append(elapsed)
        self._start_time = None

    def get_statistics(self) -> PerformanceMetrics:
        """Get performance statistics.

        Returns:
            PerformanceMetrics object with aggregated statistics
        """
        if not self._times:
            return PerformanceMetrics()

        metrics = PerformanceMetrics(
            elapsed_time=sum(self._times),
            iterations=len(self._times),
            avg_time=sum(self._times) / len(self._times),
            min_time=min(self._times),
            max_time=max(self._times),
        )

        if self.track_memory and self._tracemalloc_started:
            current, peak = tracemalloc.get_traced_memory()
            metrics.memory_current = current
            metrics.memory_peak = peak

        return metrics

    def reset(self) -> None:
        """Reset all collected statistics."""
        self._times.clear()
        self._start_time = None

        if self.track_memory and self._tracemalloc_started:
            tracemalloc.stop()
            tracemalloc.start()
            self._tracemalloc_started = True

    def __del__(self):
        """Cleanup on deletion."""
        if self._tracemalloc_started:
            tracemalloc.stop()


def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging.

    Returns:
        Dictionary with system info:
        - cpu_count: Number of CPU cores
        - cpu_freq: CPU frequency (if available)
        - memory_total: Total system memory in bytes
        - memory_available: Available memory in bytes
        - python_version: Python version
        - platform: Platform identifier
    """
    import platform
    import sys

    try:
        cpu_freq = psutil.cpu_freq()
        cpu_freq_str = f"{cpu_freq.current:.2f} MHz" if cpu_freq else "N/A"
    except Exception:
        cpu_freq_str = "N/A"

    memory = psutil.virtual_memory()

    return {
        "cpu_count": psutil.cpu_count(),
        "cpu_freq": cpu_freq_str,
        "memory_total": memory.total,
        "memory_available": memory.available,
        "memory_percent": memory.percent,
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
    }