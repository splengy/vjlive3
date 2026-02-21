"""Unit tests for VJLive3 core functionality.

This module contains unit tests for the core components of VJLive3,
including the video pipeline, effects, and sources.

Test structure:
- Test classes follow the pattern Test<ClassName>
- Test methods follow the pattern test_<behavior>
- Fixtures are used for common setup
- Parametrized tests for multiple scenarios
"""

import pytest
import numpy as np
from vjlive3.core.pipeline import VideoPipeline, PipelineConfig
from vjlive3.effects.blur import BlurEffect
from vjlive3.sources.generator import TestPatternGenerator


class TestVideoPipeline:
    """Test suite for VideoPipeline."""

    @pytest.fixture
    def sample_frame(self) -> np.ndarray:
        """Create a sample test frame."""
        return np.zeros((100, 100, 3), dtype=np.uint8)

    @pytest.fixture
    def blur_effect(self) -> BlurEffect:
        """Create a BlurEffect instance."""
        return BlurEffect(kernel_size=5)

    @pytest.fixture
    def test_source(self) -> TestPatternGenerator:
        """Create a TestPatternGenerator source."""
        return TestPatternGenerator(
            pattern="solid",
            width=100,
            height=100,
            fps=30.0
        )

    @pytest.fixture
    def pipeline_config(self, test_source: TestPatternGenerator) -> PipelineConfig:
        """Create a pipeline configuration."""
        return PipelineConfig(
            source=test_source,
            effects=[BlurEffect(kernel_size=3)]
        )

    @pytest.fixture
    def pipeline(self, pipeline_config: PipelineConfig) -> VideoPipeline:
        """Create a VideoPipeline instance."""
        return VideoPipeline(pipeline_config)

    def test_init_with_valid_config(self, pipeline_config: PipelineConfig) -> None:
        """Test pipeline initialization with valid config."""
        pipeline = VideoPipeline(pipeline_config)
        assert pipeline is not None
        assert pipeline.frame_count == 0

    def test_init_with_no_source_raises(self) -> None:
        """Test that pipeline initialization fails without source."""
        with pytest.raises(ValueError, match="Pipeline requires a source"):
            PipelineConfig(source=None, effects=[])

    def test_init_with_invalid_effects_raises(self) -> None:
        """Test that pipeline initialization fails with invalid effects."""
        with pytest.raises(ValueError, match="Effect at index"):
            PipelineConfig(
                source=TestPatternGenerator(),
                effects=["not an effect"]
            )

    def test_process_returns_same_shape(self, pipeline: VideoPipeline, sample_frame: np.ndarray) -> None:
        """Test that process returns frame with same shape."""
        result = pipeline.process(sample_frame)
        assert result.shape == sample_frame.shape

    def test_process_returns_rgb_frame(self, pipeline: VideoPipeline, sample_frame: np.ndarray) -> None:
        """Test that process returns RGB frame."""
        result = pipeline.process(sample_frame)
        assert result.shape[2] == 3

    def test_process_increases_frame_count(self, pipeline: VideoPipeline, sample_frame: np.ndarray) -> None:
        """Test that process increases frame count."""
        initial_count = pipeline.frame_count
        pipeline.process(sample_frame)
        assert pipeline.frame_count == initial_count + 1

    def test_process_with_invalid_frame_raises(self, pipeline: VideoPipeline) -> None:
        """Test that process raises on invalid frame."""
        with pytest.raises(ValueError, match="Frame cannot be None"):
            pipeline.process(None)

        with pytest.raises(ValueError, match="Frame must be HxWxC RGB array"):
            pipeline.process(np.zeros((100, 100)))  # 2D array

    def test_stream_yields_processed_frames(self, pipeline: VideoPipeline) -> None:
        """Test that stream yields processed frames."""
        frames = list(pipeline.stream())
        assert len(frames) > 0
        for frame in frames:
            assert frame.shape[2] == 3  # RGB

    def test_reset_clears_frame_count(self, pipeline: VideoPipeline, sample_frame: np.ndarray) -> None:
        """Test that reset clears frame count."""
        pipeline.process(sample_frame)
        assert pipeline.frame_count > 0

        pipeline.reset()
        assert pipeline.frame_count == 0

    def test_get_statistics_returns_dict(self, pipeline: VideoPipeline) -> None:
        """Test that get_statistics returns a dictionary."""
        stats = pipeline.get_statistics()
        assert isinstance(stats, dict)
        assert "frame_count" in stats
        assert "effects_count" in stats

    def test_get_statistics_includes_effect_stats(self, pipeline: VideoPipeline) -> None:
        """Test that get_statistics includes effect statistics."""
        stats = pipeline.get_statistics()
        if "effects" in stats:
            for effect_stats in stats["effects"]:
                assert "index" in effect_stats
                assert "type" in effect_stats
                assert "statistics" in effect_stats

    def test_multiple_effects_applied_in_sequence(self, pipeline: VideoPipeline, sample_frame: np.ndarray) -> None:
        """Test that multiple effects are applied in sequence."""
        # Create pipeline with multiple effects
        config = PipelineConfig(
            source=TestPatternGenerator(),
            effects=[
                BlurEffect(kernel_size=3),
                BlurEffect(kernel_size=5)
            ]
        )
        pipeline = VideoPipeline(config)

        result = pipeline.process(sample_frame)
        assert result.shape == sample_frame.shape

    def test_pipeline_with_no_effects(self, pipeline: VideoPipeline, sample_frame: np.ndarray) -> None:
        """Test pipeline with no effects (pass-through)."""
        config = PipelineConfig(
            source=TestPatternGenerator(),
            effects=[]
        )
        pipeline = VideoPipeline(config)

        result = pipeline.process(sample_frame)
        assert result.shape == sample_frame.shape

    def test_pipeline_with_different_frame_sizes(self, pipeline: VideoPipeline) -> None:
        """Test pipeline with different frame sizes."""
        small_frame = np.zeros((50, 50, 3), dtype=np.uint8)
        large_frame = np.zeros((200, 200, 3), dtype=np.uint8)

        result_small = pipeline.process(small_frame)
        result_large = pipeline.process(large_frame)

        assert result_small.shape == small_frame.shape
        assert result_large.shape == large_frame.shape

    def test_pipeline_statistics_after_processing(self, pipeline: VideoPipeline, sample_frame: np.ndarray) -> None:
        """Test that statistics are updated after processing."""
        initial_stats = pipeline.get_statistics()
        pipeline.process(sample_frame)
        final_stats = pipeline.get_statistics()

        assert final_stats["frame_count"] == initial_stats["frame_count"] + 1

    def test_pipeline_with_invalid_effect_type(self) -> None:
        """Test that pipeline raises on invalid effect type."""
        with pytest.raises(ValueError, match="Effect at index"):
            PipelineConfig(
                source=TestPatternGenerator(),
                effects=["not an effect"]
            )

    def test_pipeline_with_empty_effects_list(self) -> None:
        """Test pipeline with empty effects list."""
        config = PipelineConfig(
            source=TestPatternGenerator(),
            effects=[]
        )
        pipeline = VideoPipeline(config)

        sample_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = pipeline.process(sample_frame)
        assert np.array_equal(result, sample_frame)  # No effects, should be same

    def test_pipeline_frame_count_persistence(self, pipeline: VideoPipeline, sample_frame: np.ndarray) -> None:
        """Test that frame count persists across multiple process calls."""
        initial_count = pipeline.frame_count

        for _ in range(5):
            pipeline.process(sample_frame)

        assert pipeline.frame_count == initial_count + 5

    def test_pipeline_statistics_memory_usage(self, pipeline: VideoPipeline) -> None:
        """Test that statistics include memory usage if tracked."""
        stats = pipeline.get_statistics()
        if "memory_peak" in stats:
            assert stats["memory_peak"] >= 0
        if "memory_current" in stats:
            assert stats["memory_current"] >= 0