"""Video processing pipeline.

This module defines the VideoPipeline class, which orchestrates the flow of
video frames through a sequence of processing stages: source → effects → output.

The pipeline is designed to be:
- Modular: Each component is independent and replaceable
- Extensible: Easy to add new effects and sources
- Efficient: Minimal copying, optimized for real-time
- Testable: Clear interfaces and dependency injection
"""

from typing import List, Iterator, Optional, Any, Dict
from dataclasses import dataclass, field
import numpy as np

from vjlive3.effects.base import Effect
from vjlive3.sources.base import Source
from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for VideoPipeline.

    Attributes:
        source: Video source providing frames
        effects: List of effects to apply in sequence
        buffer_size: Number of frames to buffer (0 = no buffering)
        drop_frames: If True, drop frames when processing falls behind
        max_queue_size: Maximum number of frames in processing queue
    """

    source: Source
    effects: List[Effect] = field(default_factory=list)
    buffer_size: int = 0
    drop_frames: bool = True
    max_queue_size: int = 10


class VideoPipeline:
    """Main video processing pipeline orchestrator.

    The pipeline coordinates the flow of video frames from a source through
    a sequence of effects to produce the final output.

    Example:
        >>> source = TestPatternGenerator()
        >>> effects = [BlurEffect(kernel_size=5)]
        >>> pipeline = VideoPipeline(source=source, effects=effects)
        >>> for frame in source.stream():
        ...     processed = pipeline.process(frame)
        ...     # render or output processed frame
    """

    def __init__(self, config: PipelineConfig):
        """Initialize the video pipeline.

        Args:
            config: Pipeline configuration

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self._frame_count = 0
        self._start_time = None

        # Validate configuration
        self._validate_config()

        logger.info(
            f"VideoPipeline initialized with {len(config.effects)} effects"
        )

    def _validate_config(self) -> None:
        """Validate pipeline configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.config.source is None:
            raise ValueError("Pipeline requires a source")

        if not isinstance(self.config.effects, list):
            raise ValueError("Effects must be a list")

        for i, effect in enumerate(self.config.effects):
            if not isinstance(effect, Effect):
                raise ValueError(
                    f"Effect at index {i} is not an Effect instance: {type(effect)}"
                )

    def process(self, frame: np.ndarray, timestamp: Optional[float] = None) -> np.ndarray:
        """Process a single frame through the pipeline.

        Args:
            frame: Input frame as HxWxC numpy array (RGB)
            timestamp: Optional timestamp in seconds (uses current time if None)

        Returns:
            Processed frame as HxWxC numpy array (RGB)

        Raises:
            ProcessingError: If frame processing fails
            ValueError: If input frame is invalid
        """
        if frame is None:
            raise ValueError("Frame cannot be None")

        if len(frame.shape) != 3 or frame.shape[2] != 3:
            raise ValueError(
                f"Frame must be HxWxC RGB array, got shape {frame.shape}"
            )

        if timestamp is None:
            import time
            timestamp = time.perf_counter()

        # Apply each effect in sequence
        result = frame.copy()
        for effect in self.config.effects:
            try:
                result = effect.apply(result, timestamp)
            except Exception as e:
                logger.error(
                    f"Effect {effect.__class__.__name__} failed: {e}",
                    exc_info=True
                )
                raise ProcessingError(
                    f"Effect {effect.__class__.__name__} failed"
                ) from e

        self._frame_count += 1
        return result

    def stream(self) -> Iterator[np.ndarray]:
        """Stream processed frames from the source.

        Yields:
            Processed frames from the source through the pipeline

        Example:
            >>> for frame in pipeline.stream():
            ...     display(frame)
        """
        logger.info("Starting pipeline stream")

        try:
            for raw_frame in self.config.source.stream():
                processed = self.process(raw_frame)
                yield processed
        except Exception as e:
            logger.error(f"Pipeline stream error: {e}")
            raise
        finally:
            logger.info(
                f"Pipeline stream ended. Total frames: {self._frame_count}"
            )

    def reset(self) -> None:
        """Reset pipeline state.

        Clears frame count and resets all effects.
        """
        logger.info("Resetting pipeline")
        self._frame_count = 0

        for effect in self.config.effects:
            if hasattr(effect, "reset"):
                effect.reset()

    @property
    def frame_count(self) -> int:
        """Total number of frames processed."""
        return self._frame_count

    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics.

        Returns:
            Dictionary with statistics:
            - frame_count: Total frames processed
            - effects_count: Number of effects in pipeline
            - source_info: Information about the source
        """
        stats = {
            "frame_count": self._frame_count,
            "effects_count": len(self.config.effects),
            "source_info": self.config.source.get_info()
            if hasattr(self.config.source, "get_info")
            else None,
        }

        # Add effect-specific statistics
        effect_stats = []
        for i, effect in enumerate(self.config.effects):
            if hasattr(effect, "get_statistics"):
                effect_stats.append({
                    "index": i,
                    "type": effect.__class__.__name__,
                    "statistics": effect.get_statistics(),
                })

        if effect_stats:
            stats["effects"] = effect_stats

        return stats


class ProcessingError(Exception):
    """Exception raised when frame processing fails."""

    pass