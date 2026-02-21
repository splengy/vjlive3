"""Color correction and grading effects.

This module provides effects for adjusting color properties:
- Brightness, contrast, saturation
- Color balance
- Levels and curves (future)
"""

from typing import Dict, Any, Optional
import numpy as np
from vjlive3.effects.base import Effect, ProcessingError


class ColorCorrectionEffect(Effect):
    """Basic color correction effect.

    Adjusts brightness, contrast, and saturation of the input frame.

    Example:
        >>> effect = ColorCorrectionEffect(brightness=1.2, contrast=1.1, saturation=0.9)
        >>> result = effect.apply(frame, timestamp=0.0)
    """

    def __init__(
        self,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
    ):
        """Initialize color correction effect.

        Args:
            brightness: Brightness multiplier (1.0 = no change)
            contrast: Contrast multiplier (1.0 = no change)
            saturation: Saturation multiplier (1.0 = no change)
        """
        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation
        self._total_processing_time = 0.0
        self._frame_count = 0

    def apply(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """Apply color correction to frame.

        Args:
            frame: Input frame (HxWxC, RGB)
            timestamp: Current time in seconds

        Returns:
            Color-corrected frame (same shape as input)
        """
        import time

        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ProcessingError("Frame must be HxWxC RGB array")

        start_time = time.perf_counter()

        try:
            # Convert to float32 for processing
            result = frame.astype(np.float32) / 255.0

            # Apply brightness
            result = result * self.brightness

            # Apply contrast
            if self.contrast != 1.0:
                result = (result - 0.5) * self.contrast + 0.5

            # Apply saturation
            if self.saturation != 1.0:
                # Convert to HSV for saturation adjustment
                hsv = cv2.cvtColor((result * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
                hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self.saturation, 0, 255)
                result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
                result = result.astype(np.float32) / 255.0

            # Clip and convert back to uint8
            result = np.clip(result * 255, 0, 255).astype(np.uint8)

            elapsed = time.perf_counter() - start_time
            self._total_processing_time += elapsed
            self._frame_count += 1

            return result

        except Exception as e:
            raise ProcessingError(f"Color correction failed: {e}") from e

    def get_parameters(self) -> Dict[str, Any]:
        """Get current effect parameters."""
        return {
            "brightness": self.brightness,
            "contrast": self.contrast,
            "saturation": self.saturation,
        }

    def set_parameter(self, name: str, value: Any) -> None:
        """Set effect parameter."""
        if name in ("brightness", "contrast", "saturation"):
            if not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a number")
            setattr(self, name, float(value))
        else:
            super().set_parameter(name, value)

    def reset(self) -> None:
        """Reset effect to defaults."""
        self.brightness = 1.0
        self.contrast = 1.0
        self.saturation = 1.0
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
        return f"ColorCorrectionEffect(**{params})"