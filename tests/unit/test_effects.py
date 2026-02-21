"""Unit tests for effects module.

This module contains unit tests for all effect implementations.
"""

import pytest
import numpy as np
from vjlive3.effects.blur import BlurEffect
from vjlive3.effects.color import ColorCorrectionEffect
from vjlive3.effects.distort import DistortEffect


class TestBlurEffect:
    """Test suite for BlurEffect."""

    def test_init_with_valid_kernel(self) -> None:
        """Test initialization with valid kernel size."""
        effect = BlurEffect(kernel_size=5)
        assert effect.kernel_size == 5
        assert effect.algorithm == "gaussian"

    def test_init_with_invalid_kernel_even_raises(self) -> None:
        """Test that even kernel size raises ValueError."""
        with pytest.raises(ValueError, match="kernel_size must be odd"):
            BlurEffect(kernel_size=4)

    def test_init_with_invalid_kernel_negative_raises(self) -> None:
        """Test that negative kernel size raises ValueError."""
        with pytest.raises(ValueError, match="kernel_size must be odd"):
            BlurEffect(kernel_size=-1)

    def test_init_with_invalid_algorithm_raises(self) -> None:
        """Test that invalid algorithm raises ValueError."""
        with pytest.raises(ValueError, match="Algorithm must be one of"):
            BlurEffect(kernel_size=5, algorithm="invalid")

    @pytest.mark.parametrize("algorithm", ["gaussian", "box", "median"])
    def test_different_algorithms(self, algorithm: str) -> None:
        """Test all blur algorithms."""
        effect = BlurEffect(kernel_size=5, algorithm=algorithm)
        assert effect.algorithm == algorithm

    def test_apply_returns_same_shape(self) -> None:
        """Test that apply returns frame with same shape."""
        effect = BlurEffect(kernel_size=5)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        assert result.shape == frame.shape

    def test_apply_preserves_dtype(self) -> None:
        """Test that apply preserves data type."""
        effect = BlurEffect(kernel_size=5)
        frame = np.zeros((50, 50, 3), dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        assert result.dtype == frame.dtype

    def test_apply_with_float_frame(self) -> None:
        """Test that apply works with float frames."""
        effect = BlurEffect(kernel_size=5)
        frame = np.zeros((50, 50, 3), dtype=np.float32)
        result = effect.apply(frame, timestamp=0.0)
        assert result.shape == frame.shape

    def test_apply_with_invalid_frame_raises(self) -> None:
        """Test that invalid frame raises ProcessingError."""
        effect = BlurEffect(kernel_size=5)
        with pytest.raises(ProcessingError, match="Frame must be HxWxC"):
            effect.apply(np.zeros((100, 100)), timestamp=0.0)  # 2D

    def test_get_parameters(self) -> None:
        """Test get_parameters returns correct values."""
        effect = BlurEffect(kernel_size=7, algorithm="box")
        params = effect.get_parameters()
        assert params["kernel_size"] == 7
        assert params["algorithm"] == "box"

    def test_set_parameter_kernel_size(self) -> None:
        """Test setting kernel_size parameter."""
        effect = BlurEffect(kernel_size=5)
        effect.set_parameter("kernel_size", 9)
        assert effect.kernel_size == 9

    def test_set_parameter_kernel_size_invalid_raises(self) -> None:
        """Test that setting invalid kernel_size raises."""
        effect = BlurEffect(kernel_size=5)
        with pytest.raises(ValueError, match="kernel_size must be odd"):
            effect.set_parameter("kernel_size", 6)

    def test_set_parameter_algorithm(self) -> None:
        """Test setting algorithm parameter."""
        effect = BlurEffect(kernel_size=5)
        effect.set_parameter("algorithm", "median")
        assert effect.algorithm == "median"

    def test_set_parameter_algorithm_invalid_raises(self) -> None:
        """Test that setting invalid algorithm raises."""
        effect = BlurEffect(kernel_size=5)
        with pytest.raises(ValueError, match="Algorithm must be one of"):
            effect.set_parameter("algorithm", "invalid")

    def test_reset_clears_statistics(self) -> None:
        """Test that reset clears statistics."""
        effect = BlurEffect(kernel_size=5)
        # Process some frames to accumulate stats
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        for _ in range(5):
            effect.apply(frame, timestamp=0.0)

        stats_before = effect.get_statistics()
        assert stats_before["frame_count"] > 0

        effect.reset()
        stats_after = effect.get_statistics()
        assert stats_after["frame_count"] == 0
        assert stats_after["total_processing_time"] == 0.0

    def test_get_statistics_after_processing(self) -> None:
        """Test that get_statistics returns correct values after processing."""
        effect = BlurEffect(kernel_size=5)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        effect.apply(frame, timestamp=0.0)
        stats = effect.get_statistics()

        assert stats["frame_count"] == 1
        assert stats["total_processing_time"] > 0
        assert stats["average_processing_time"] > 0

    def test_repr_includes_parameters(self) -> None:
        """Test that __repr__ includes parameters."""
        effect = BlurEffect(kernel_size=5, algorithm="gaussian")
        repr_str = repr(effect)
        assert "BlurEffect" in repr_str
        assert "kernel_size=5" in repr_str
        assert "algorithm='gaussian'" in repr_str


class TestColorCorrectionEffect:
    """Test suite for ColorCorrectionEffect."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default parameters."""
        effect = ColorCorrectionEffect()
        assert effect.brightness == 1.0
        assert effect.contrast == 1.0
        assert effect.saturation == 1.0

    def test_init_with_custom_values(self) -> None:
        """Test initialization with custom parameters."""
        effect = ColorCorrectionEffect(brightness=1.2, contrast=0.9, saturation=1.5)
        assert effect.brightness == 1.2
        assert effect.contrast == 0.9
        assert effect.saturation == 1.5

    def test_apply_returns_same_shape(self) -> None:
        """Test that apply returns frame with same shape."""
        effect = ColorCorrectionEffect()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        assert result.shape == frame.shape

    def test_apply_brightness(self) -> None:
        """Test brightness adjustment."""
        effect = ColorCorrectionEffect(brightness=2.0)
        frame = np.full((100, 100, 3), 100, dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        # Brightness should increase pixel values
        assert result.mean() > frame.mean()

    def test_apply_contrast(self) -> None:
        """Test contrast adjustment."""
        effect = ColorCorrectionEffect(contrast=2.0)
        frame = np.full((100, 100, 3), 128, dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        # Contrast should spread values
        assert result.std() > frame.std()

    def test_apply_saturation(self) -> None:
        """Test saturation adjustment."""
        effect = ColorCorrectionEffect(saturation=0.0)  # Grayscale
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        # Saturation 0 should produce grayscale (R=G=B for each pixel)
        # Check that all channels are equal (within small tolerance)
        diff_rg = np.abs(result[:, :, 0] - result[:, :, 1])
        diff_gb = np.abs(result[:, :, 1] - result[:, :, 2])
        assert np.mean(diff_rg) < 5  # Allow small differences due to rounding
        assert np.mean(diff_gb) < 5

    def test_get_parameters(self) -> None:
        """Test get_parameters returns correct values."""
        effect = ColorCorrectionEffect(brightness=1.5, contrast=0.8, saturation=1.2)
        params = effect.get_parameters()
        assert params["brightness"] == 1.5
        assert params["contrast"] == 0.8
        assert params["saturation"] == 1.2

    def test_set_parameter(self) -> None:
        """Test setting parameters."""
        effect = ColorCorrectionEffect()
        effect.set_parameter("brightness", 1.5)
        assert effect.brightness == 1.5
        effect.set_parameter("contrast", 0.9)
        assert effect.contrast == 0.9
        effect.set_parameter("saturation", 1.3)
        assert effect.saturation == 1.3

    def test_set_parameter_invalid_raises(self) -> None:
        """Test that setting invalid parameter raises."""
        effect = ColorCorrectionEffect()
        with pytest.raises(ValueError):
            effect.set_parameter("brightness", "not a number")

    def test_reset_to_defaults(self) -> None:
        """Test that reset restores default values."""
        effect = ColorCorrectionEffect(brightness=2.0, contrast=0.5, saturation=1.5)
        effect.reset()
        assert effect.brightness == 1.0
        assert effect.contrast == 1.0
        assert effect.saturation == 1.0

    def test_repr(self) -> None:
        """Test __repr__ output."""
        effect = ColorCorrectionEffect(brightness=1.2, contrast=1.1)
        repr_str = repr(effect)
        assert "ColorCorrectionEffect" in repr_str
        assert "brightness=1.2" in repr_str
        assert "contrast=1.1" in repr_str


class TestDistortEffect:
    """Test suite for DistortEffect."""

    def test_init_with_valid_params(self) -> None:
        """Test initialization with valid parameters."""
        effect = DistortEffect(amplitude=10.0, frequency=0.1, direction="horizontal")
        assert effect.amplitude == 10.0
        assert effect.frequency == 0.1
        assert effect.direction == "horizontal"

    def test_init_with_negative_amplitude_raises(self) -> None:
        """Test that negative amplitude raises ValueError."""
        with pytest.raises(ValueError, match="amplitude must be non-negative"):
            DistortEffect(amplitude=-1.0)

    def test_init_with_zero_frequency_raises(self) -> None:
        """Test that zero frequency raises ValueError."""
        with pytest.raises(ValueError, match="frequency must be positive"):
            DistortEffect(frequency=0.0)

    def test_init_with_invalid_direction_raises(self) -> None:
        """Test that invalid direction raises ValueError."""
        with pytest.raises(ValueError, match="direction must be one of"):
            DistortEffect(direction="invalid")

    @pytest.mark.parametrize("direction", ["horizontal", "vertical", "both"])
    def test_different_directions(self, direction: str) -> None:
        """Test all direction options."""
        effect = DistortEffect(direction=direction)
        assert effect.direction == direction

    def test_apply_returns_same_shape(self) -> None:
        """Test that apply returns frame with same shape."""
        effect = DistortEffect()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        assert result.shape == frame.shape

    def test_apply_with_zero_amplitude(self) -> None:
        """Test that zero amplitude produces no distortion."""
        effect = DistortEffect(amplitude=0.0)
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        # Should be identical (or very close) to original
        assert np.allclose(result, frame, atol=1)

    def test_apply_with_different_frame_sizes(self) -> None:
        """Test distortion with different frame sizes."""
        effect = DistortEffect(amplitude=5.0)
        small = np.zeros((50, 50, 3), dtype=np.uint8)
        large = np.zeros((200, 200, 3), dtype=np.uint8)

        result_small = effect.apply(small, timestamp=0.0)
        result_large = effect.apply(large, timestamp=0.0)

        assert result_small.shape == small.shape
        assert result_large.shape == large.shape

    def test_get_parameters(self) -> None:
        """Test get_parameters returns correct values."""
        effect = DistortEffect(amplitude=15.0, frequency=0.2, direction="vertical")
        params = effect.get_parameters()
        assert params["amplitude"] == 15.0
        assert params["frequency"] == 0.2
        assert params["direction"] == "vertical"

    def test_set_parameter_amplitude(self) -> None:
        """Test setting amplitude parameter."""
        effect = DistortEffect()
        effect.set_parameter("amplitude", 20.0)
        assert effect.amplitude == 20.0

    def test_set_parameter_amplitude_negative_raises(self) -> None:
        """Test that setting negative amplitude raises."""
        effect = DistortEffect()
        with pytest.raises(ValueError, match="amplitude must be non-negative"):
            effect.set_parameter("amplitude", -5.0)

    def test_set_parameter_frequency(self) -> None:
        """Test setting frequency parameter."""
        effect = DistortEffect()
        effect.set_parameter("frequency", 0.5)
        assert effect.frequency == 0.5

    def test_set_parameter_frequency_invalid_raises(self) -> None:
        """Test that setting invalid frequency raises."""
        effect = DistortEffect()
        with pytest.raises(ValueError, match="frequency must be positive"):
            effect.set_parameter("frequency", 0.0)

    def test_set_parameter_direction(self) -> None:
        """Test setting direction parameter."""
        effect = DistortEffect()
        effect.set_parameter("direction", "both")
        assert effect.direction == "both"

    def test_set_parameter_direction_invalid_raises(self) -> None:
        """Test that setting invalid direction raises."""
        effect = DistortEffect()
        with pytest.raises(ValueError, match="direction must be one of"):
            effect.set_parameter("direction", "invalid")

    def test_reset_clears_statistics(self) -> None:
        """Test that reset clears statistics."""
        effect = DistortEffect()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        for _ in range(3):
            effect.apply(frame, timestamp=0.0)

        stats_before = effect.get_statistics()
        assert stats_before["frame_count"] > 0

        effect.reset()
        stats_after = effect.get_statistics()
        assert stats_after["frame_count"] == 0

    def test_repr(self) -> None:
        """Test __repr__ output."""
        effect = DistortEffect(amplitude=10.0, frequency=0.1, direction="horizontal")
        repr_str = repr(effect)
        assert "DistortEffect" in repr_str
        assert "amplitude=10.0" in repr_str
        assert "frequency=0.1" in repr_str