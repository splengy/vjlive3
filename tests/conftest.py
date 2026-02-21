"""Pytest configuration and shared fixtures.

This module provides fixtures that can be used across all test modules.
"""

import pytest
import numpy as np
from vjlive3.core.pipeline import VideoPipeline, PipelineConfig
from vjlive3.effects.blur import BlurEffect
from vjlive3.effects.color import ColorCorrectionEffect
from vjlive3.sources.generator import TestPatternGenerator


@pytest.fixture
def sample_frame_720p() -> np.ndarray:
    """Create a 720p test frame."""
    return np.zeros((720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_1080p() -> np.ndarray:
    """Create a 1080p test frame."""
    return np.zeros((1080, 1920, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_random() -> np.ndarray:
    """Create a random test frame."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def blur_effect_small() -> BlurEffect:
    """Create a small blur effect."""
    return BlurEffect(kernel_size=3)


@pytest.fixture
def blur_effect_large() -> BlurEffect:
    """Create a large blur effect."""
    return BlurEffect(kernel_size=9)


@pytest.fixture
def color_correction_default() -> ColorCorrectionEffect:
    """Create a default color correction effect."""
    return ColorCorrectionEffect()


@pytest.fixture
def test_source_small() -> TestPatternGenerator:
    """Create a small test pattern source."""
    return TestPatternGenerator(
        pattern="color_bars",
        width=320,
        height=240,
        fps=30.0
    )


@pytest.fixture
def test_source_720p() -> TestPatternGenerator:
    """Create a 720p test pattern source."""
    return TestPatternGenerator(
        pattern="gradient",
        width=1280,
        height=720,
        fps=30.0
    )


@pytest.fixture
def simple_pipeline(test_source_small, blur_effect_small) -> VideoPipeline:
    """Create a simple pipeline with one effect."""
    config = PipelineConfig(
        source=test_source_small,
        effects=[blur_effect_small]
    )
    return VideoPipeline(config)


@pytest.fixture
def complex_pipeline(test_source_small) -> VideoPipeline:
    """Create a pipeline with multiple effects."""
    config = PipelineConfig(
        source=test_source_small,
        effects=[
            ColorCorrectionEffect(brightness=1.2, contrast=1.1),
            BlurEffect(kernel_size=3),
            ColorCorrectionEffect(saturation=0.9)
        ]
    )
    return VideoPipeline(config)


# Markers for custom test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_gpu: mark test as requiring GPU"
    )