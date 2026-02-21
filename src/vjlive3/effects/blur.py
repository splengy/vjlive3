"""Blur effects implementation.

This module provides various blur effects for video processing:
- Gaussian blur
- Box blur
- Median blur
"""

from typing import Dict, Any, Optional
import numpy as np
import cv2
from vjlive3.effects.base import Effect, ProcessingError


class BlurEffect(Effect):
    """Configurable blur effect.

    Supports multiple blur algorithms: gaussian, box, median.

    Example:
        >>> effect = BlurEffect(kernel_size=5, algorithm="gaussian")
        >>> result = effect.apply(frame, timestamp=0.0)
    """

    ALGORITHMS = ["gaussian", "box", "median"]

    def __init__(
        self,
        kernel_size: int = 5,
        algorithm: str = "gaussian",
    ):
        """Initialize blur effect.

        Args:
            kernel_size: Size of blur kernel (must be odd positive integer)
            algorithm: Blur algorithm ("gaussian", "box", "median")

        Raises:
            ValueError: If parameters are invalid
        """
        if kernel_size % 2 == 0 or kernel_size < 1:
            raise ValueError("kernel_size must be odd positive integer")

        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Algorithm must be one of {self.ALGORITHMS}")

        self.kernel_size = kernel_size
        self.algorithm = algorithm
        self._total_processing_time = 0.0
        self._frame_count = 0

    def apply(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """Apply blur to frame.

        Args:
            frame: Input frame (HxWxC, RGB)
            timestamp: Current time in seconds

        Returns:
            Blurred frame (same shape as input)
        """
        import time

        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ProcessingError("Frame must be HxWxC RGB array")

        # Convert to uint8 if needed
        if frame.dtype != np.uint8:
            frame_uint8 = (np.clip(frame, 0, 255)).astype(np.uint8)
        else:
            frame_uint8 = frame

        start_time = time.perf_counter()

        try:
            if self.algorithm == "gaussian":
                blurred = cv2.GaussianBlur(
                    frame_uint8,
                    (self.kernel_size, self.kernel_size),
                    0
                )
            elif self.algorithm == "box":
                blurred = cv2.blur(
                    frame_uint8,
                    (self.kernel_size, self.kernel_size)
                )
            elif self.algorithm == "median":
                blurred = cv2.medianBlur(
                    frame_uint8,
                    self.kernel_size
                )
            else:
                raise ProcessingError(f"Unknown algorithm: {self.algorithm}")

            # Convert back to original dtype if needed
            if frame.dtype != np.uint8:
                blurred = blurred.astype(frame.dtype)

            elapsed = time.perf_counter() - start_time
            self._total_processing_time += elapsed
            self._frame_count += 1

            return blurred

        except Exception as e:
            raise ProcessingError(f"Blur failed: {e}") from e

    def get_parameters(self) -> Dict[str, Any]:
        """Get current effect parameters."""
        return {
            "kernel_size": self.kernel_size,
            "algorithm": self.algorithm,
        }

    def set_parameter(self, name: str, value: Any) -> None:
        """Set effect parameter."""
        if name == "kernel_size":
            if value % 2 == 0 or value < 1:
                raise ValueError("kernel_size must be odd positive integer")
            self.kernel_size = value
        elif name == "algorithm":
            if value not in self.ALGORITHMS:
                raise ValueError(f"Algorithm must be one of {self.ALGORITHMS}")
            self.algorithm = value
        else:
            super().set_parameter(name, value)

    def reset(self) -> None:
        """Reset effect state."""
        self._total_processing_time = 0.0
        self._frame_count = 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get effect statistics."""
        if self._frame_count > 0:
            avg_time = self._total_processing_time / self._frame_count
        else:
            avg_time = 0.0

        return {
            "frame_count": self._frame_count,
            "total_processing_time": self._total_processing_time,
            "average_processing_time": avg_time,
        }

    def __repr__(self) -> str:
        params = self.get_parameters()
        stats = self.get_statistics()
        if stats["frame_count"] > 0:
            params_str = ", ".join(f"{k}={v}" for k, v in params.items())
            return f"BlurEffect({params_str}, avg_time={stats['average_processing_time']:.4f}s)"
        return super().__repr__()