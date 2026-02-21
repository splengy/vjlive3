"""Unit tests for sources module.

This module contains unit tests for video source implementations.
"""

import pytest
import numpy as np
from vjlive3.sources.generator import TestPatternGenerator


class TestTestPatternGenerator:
    """Test suite for TestPatternGenerator."""

    def test_init_with_valid_params(self) -> None:
        """Test initialization with valid parameters."""
        source = TestPatternGenerator(
            pattern="color_bars",
            width=1280,
            height=720,
            fps=30.0
        )
        assert source.pattern == "color_bars"
        assert source.width == 1280
        assert source.height == 720
        assert source.fps == 30.0

    def test_init_with_invalid_pattern_raises(self) -> None:
        """Test that invalid pattern raises ValueError."""
        with pytest.raises(ValueError, match="Pattern must be one of"):
            TestPatternGenerator(pattern="invalid")

    def test_init_with_invalid_dimensions_raises(self) -> None:
        """Test that invalid dimensions raise ValueError."""
        with pytest.raises(ValueError, match="Width and height must be positive"):
            TestPatternGenerator(width=-100, height=100)

        with pytest.raises(ValueError, match="Width and height must be positive"):
            TestPatternGenerator(width=100, height=0)

    def test_init_with_invalid_fps_raises(self) -> None:
        """Test that invalid FPS raises ValueError."""
        with pytest.raises(ValueError, match="FPS must be positive"):
            TestPatternGenerator(fps=0.0)

    def test_get_info(self) -> None:
        """Test get_info returns correct information."""
        source = TestPatternGenerator(
            pattern="gradient",
            width=1920,
            height=1080,
            fps=60.0
        )
        info = source.get_info()
        assert info["type"] == "TestPatternGenerator"
        assert info["pattern"] == "gradient"
        assert info["width"] == 1920
        assert info["height"] == 1080
        assert info["fps"] == 60.0
        assert info["format"] == "RGB"

    def test_get_parameters(self) -> None:
        """Test get_parameters returns correct values."""
        source = TestPatternGenerator(
            pattern="noise",
            width=640,
            height=480,
            fps=25.0,
            mean=100,
            std=50
        )
        params = source.get_parameters()
        assert params["pattern"] == "noise"
        assert params["width"] == 640
        assert params["height"] == 480
        assert params["fps"] == 25.0
        assert params["mean"] == 100
        assert params["std"] == 50

    def test_stream_yields_frames(self) -> None:
        """Test that stream yields frames."""
        source = TestPatternGenerator(
            pattern="solid",
            width=100,
            height=100,
            fps=30.0,
            color=(255, 0, 0)
        )

        frames = []
        stream = source.stream()

        # Get a few frames
        for _ in range(5):
            frame = next(stream)
            frames.append(frame)
            assert isinstance(frame, np.ndarray)
            assert frame.shape == (100, 100, 3)
            assert frame.dtype == np.uint8

        # All frames should be identical for solid pattern
        for frame in frames[1:]:
            assert np.array_equal(frame, frames[0])

    def test_stream_color_bars_pattern(self) -> None:
        """Test color bars pattern generation."""
        source = TestPatternGenerator(
            pattern="color_bars",
            width=800,
            height=600,
            fps=30.0
        )

        frame = next(source.stream())
        assert frame.shape == (600, 800, 3)

        # Check that we have different colors in different regions
        # The color bars pattern should have distinct colors
        unique_colors = np.unique(frame.reshape(-1, 3), axis=0)
        assert len(unique_colors) >= 5  # Should have at least 5 distinct colors

    def test_stream_gradient_pattern(self) -> None:
        """Test gradient pattern generation."""
        source = TestPatternGenerator(
            pattern="gradient",
            width=100,
            height=100,
            fps=30.0
        )

        frame = next(source.stream())
        assert frame.shape == (100, 100, 3)

        # Gradient should vary horizontally
        # Check that left and right edges have different values
        left_mean = frame[:, 0, :].mean()
        right_mean = frame[:, -1, :].mean()
        assert left_mean != right_mean

    def test_stream_noise_pattern(self) -> None:
        """Test noise pattern generation."""
        source = TestPatternGenerator(
            pattern="noise",
            width=100,
            height=100,
            fps=30.0,
            mean=128,
            std=50
        )

        # Get multiple frames - they should be different
        frame1 = next(source.stream())
        frame2 = next(source.stream())

        # Noise frames should be different (not identical)
        assert not np.array_equal(frame1, frame2)

        # Mean should be approximately 128
        assert 100 < frame1.mean() < 156  # Allow some variance

    def test_stream_checker_pattern(self) -> None:
        """Test checkerboard pattern generation."""
        source = TestPatternGenerator(
            pattern="checker",
            width=200,
            height=200,
            fps=30.0,
            square_size=20
        )

        frame = next(source.stream())
        assert frame.shape == (200, 200, 3)

        # Checkerboard should have alternating colors
        # Check that top-left and (0, 20) are different
        top_left = frame[0, 0]
        next_square = frame[0, 20]
        assert not np.array_equal(top_left, next_square)

    def test_context_manager(self) -> None:
        """Test that source can be used as context manager."""
        with TestPatternGenerator() as source:
            frame = next(source.stream())
            assert isinstance(frame, np.ndarray)

    def test_repr(self) -> None:
        """Test __repr__ output."""
        source = TestPatternGenerator(
            pattern="color_bars",
            width=1280,
            height=720,
            fps=30.0
        )
        repr_str = repr(source)
        assert "TestPatternGenerator" in repr_str
        assert "pattern='color_bars'" in repr_str
        assert "width=1280" in repr_str
        assert "height=720" in repr_str