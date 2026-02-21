"""Distortion effects implementation.

This module provides various distortion and warping effects.
"""

from typing import Dict, Any
import numpy as np
import cv2
from vjlive3.effects.base import Effect, ProcessingError


class DistortEffect(Effect):
    """Simple distortion effect using sine wave displacement.

    Creates a wave-like distortion effect.

    Example:
        >>> effect = DistortEffect(amplitude=10.0, frequency=0.1, direction="horizontal")
        >>> result = effect.apply(frame, timestamp=0.0)
    """

    DIRECTIONS = ["horizontal", "vertical", "both"]

    def __init__(
        self,
        amplitude: float = 10.0,
        frequency: float = 0.1,
        direction: str = "horizontal",
    ):
        """Initialize distortion effect.

        Args:
            amplitude: Distortion amplitude in pixels
            frequency: Distortion frequency (waves per frame)
            direction: Distortion direction ("horizontal", "vertical", "both")
        """
        if amplitude < 0:
            raise ValueError("amplitude must be non-negative")
        if frequency <= 0:
            raise ValueError("frequency must be positive")
        if direction not in self.DIRECTIONS:
            raise ValueError(f"direction must be one of {self.DIRECTIONS}")

        self.amplitude = amplitude
        self.frequency = frequency
        self.direction = direction
        self._total_processing_time = 0.0
        self._frame_count = 0

    def apply(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """Apply distortion to frame.

        Args:
            frame: Input frame (HxWxC, RGB)
            timestamp: Current time in seconds

        Returns:
            Distorted frame (same shape as input)
        """
        import time

        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ProcessingError("Frame must be HxWxC RGB array")

        start_time = time.perf_counter()

        try:
            height, width = frame.shape[:2]
            result = frame.copy()

            # Create coordinate grids
            x = np.arange(width)
            y = np.arange(height)
            X, Y = np.meshgrid(x, y)

            # Calculate displacement based on direction
            if self.direction in ("horizontal", "both"):
                displacement_x = self.amplitude * np.sin(
                    2 * np.pi * self.frequency * Y + timestamp * 2 * np.pi
                )
                X = X + displacement_x

            if self.direction in ("vertical", "both"):
                displacement_y = self.amplitude * np.sin(
                    2 * np.pi * self.frequency * X + timestamp * 2 * np.pi
                )
                Y = Y + displacement_y

            # Remap image using displacement
            X = np.clip(X, 0, width - 1).astype(np.float32)
            Y = np.clip(Y, 0, height - 1).astype(np.float32)

            # Apply remap for each channel
            for c in range(3):
                result[:, :, c] = cv2.remap(
                    frame[:, :, c],
                    X,
                    Y,
                    interpolation=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT
                )

            elapsed = time.perf_counter() - start_time
            self._total_processing_time += elapsed
            self._frame_count += 1

            return result

        except Exception as e:
            raise ProcessingError(f"Distortion failed: {e}") from e

    def get_parameters(self) -> Dict[str, Any]:
        """Get current effect parameters."""
        return {
            "amplitude": self.amplitude,
            "frequency": self.frequency,
            "direction": self.direction,
        }

    def set_parameter(self, name: str, value: Any) -> None:
        """Set effect parameter."""
        if name == "amplitude":
            if value < 0:
                raise ValueError("amplitude must be non-negative")
            self.amplitude = float(value)
        elif name == "frequency":
            if value <= 0:
                raise ValueError("frequency must be positive")
            self.frequency = float(value)
        elif name == "direction":
            if value not in self.DIRECTIONS:
                raise ValueError(f"direction must be one of {self.DIRECTIONS}")
            self.direction = value
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
        return f"DistortEffect(**{params})"