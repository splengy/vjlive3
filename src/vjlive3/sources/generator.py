"""Test pattern and procedural content generators.

This module provides various test pattern generators for development,
testing, and demo purposes.
"""

from typing import Dict, Any, Iterator
import numpy as np
from vjlive3.sources.base import Source


class TestPatternGenerator(Source):
    """Generates test patterns for development and testing.

    Supports various standard test patterns:
    - color_bars: SMPTE color bars
    - gradient: Horizontal gradient
    - noise: Random noise
    - solid: Solid color
    - checker: Checkerboard pattern

    Example:
        >>> source = TestPatternGenerator(
        ...     pattern="color_bars",
        ...     width=1280,
        ...     height=720,
        ...     fps=30.0
        ... )
        >>> for frame in source.stream():
        ...     process(frame)
    """

    PATTERNS = ["color_bars", "gradient", "noise", "solid", "checker"]

    def __init__(
        self,
        pattern: str = "color_bars",
        width: int = 1280,
        height: int = 720,
        fps: float = 30.0,
        **kwargs
    ):
        """Initialize test pattern generator.

        Args:
            pattern: Pattern name (see PATTERNS)
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Frame rate (for timing info)
            **kwargs: Pattern-specific parameters
                - For "solid": color (tuple of 3 ints)
                - For "noise": mean, std
                - For "checker": square_size
        """
        if pattern not in self.PATTERNS:
            raise ValueError(f"Pattern must be one of {self.PATTERNS}")

        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")

        if fps <= 0:
            raise ValueError("FPS must be positive")

        self.pattern = pattern
        self.width = width
        self.height = height
        self.fps = fps
        self.kwargs = kwargs
        self._frame_number = 0

    def stream(self) -> Iterator[np.ndarray]:
        """Generate infinite stream of test pattern frames."""
        import time

        frame_interval = 1.0 / self.fps
        last_frame_time = time.perf_counter()

        while True:
            # Generate frame based on pattern
            if self.pattern == "color_bars":
                frame = self._generate_color_bars()
            elif self.pattern == "gradient":
                frame = self._generate_gradient()
            elif self.pattern == "noise":
                frame = self._generate_noise()
            elif self.pattern == "solid":
                frame = self._generate_solid()
            elif self.pattern == "checker":
                frame = self._generate_checker()
            else:
                raise ValueError(f"Unknown pattern: {self.pattern}")

            self._frame_number += 1

            # Maintain frame rate
            current_time = time.perf_counter()
            elapsed = current_time - last_frame_time
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)
            last_frame_time = time.perf_counter()

            yield frame

    def _generate_color_bars(self) -> np.ndarray:
        """Generate SMPTE color bars pattern."""
        width, height = self.width, self.height
        bar_width = width // 8

        # SMPTE color bar colors (in RGB)
        colors = [
            (255, 255, 255),  # White
            (255, 255, 0),    # Yellow
            (0, 255, 255),    # Cyan
            (0, 255, 0),      # Green
            (255, 0, 255),    # Magenta
            (255, 0, 0),      # Red
            (0, 0, 255),      # Blue
            (0, 0, 0),        # Black
        ]

        frame = np.zeros((height, width, 3), dtype=np.uint8)

        for i, color in enumerate(colors):
            x_start = i * bar_width
            x_end = (i + 1) * bar_width
            frame[:, x_start:x_end] = color

        # Add bottom 10% with special pattern (simplified)
        border_height = int(height * 0.1)
        frame[-border_height:, :] = (128, 128, 128)

        return frame

    def _generate_gradient(self) -> np.ndarray:
        """Generate horizontal gradient."""
        gradient = np.linspace(0, 255, self.width, dtype=np.uint8)
        gradient = np.tile(gradient, (self.height, 1))
        frame = np.stack([gradient] * 3, axis=-1)
        return frame

    def _generate_noise(self) -> np.ndarray:
        """Generate random noise."""
        mean = self.kwargs.get("mean", 128)
        std = self.kwargs.get("std", 50)
        frame = np.random.normal(mean, std, (self.height, self.width, 3))
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        return frame

    def _generate_solid(self) -> np.ndarray:
        """Generate solid color."""
        color = self.kwargs.get("color", (128, 128, 128))
        frame = np.full((self.height, self.width, 3), color, dtype=np.uint8)
        return frame

    def _generate_checker(self) -> np.ndarray:
        """Generate checkerboard pattern."""
        square_size = self.kwargs.get("square_size", 50)
        color1 = self.kwargs.get("color1", (255, 255, 255))
        color2 = self.kwargs.get("color2", (0, 0, 0))

        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        for y in range(0, self.height, square_size):
            for x in range(0, self.width, square_size):
                color = color1 if ((x // square_size) + (y // square_size)) % 2 == 0 else color2
                y_end = min(y + square_size, self.height)
                x_end = min(x + square_size, self.width)
                frame[y:y_end, x:x_end] = color

        return frame

    def get_info(self) -> Dict[str, Any]:
        """Get source information."""
        return {
            "type": "TestPatternGenerator",
            "pattern": self.pattern,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "format": "RGB",
        }

    def get_parameters(self) -> Dict[str, Any]:
        """Get source parameters."""
        return {
            "pattern": self.pattern,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            **self.kwargs,
        }

    def __repr__(self) -> str:
        params = self.get_parameters()
        return f"TestPatternGenerator(**{params})"