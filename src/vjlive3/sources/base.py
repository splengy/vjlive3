"""Abstract base class for video sources.

This module defines the Source interface that all video sources must implement.
"""

from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional
import numpy as np


class Source(ABC):
    """Abstract base class for all video sources.

    Sources provide frames to the pipeline via an iterator interface.

    Example:
        >>> class MySource(Source):
        ...     def stream(self) -> Iterator[np.ndarray]:
        ...         while True:
        ...             yield generate_frame()
    """

    @abstractmethod
    def stream(self) -> Iterator[np.ndarray]:
        """Generate an infinite stream of frames.

        Yields:
            Frames as HxWxC numpy arrays (RGB format)

        Note:
            The stream should be infinite or very long. The pipeline will
            consume frames as needed. If the source ends, the iterator
            should stop.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get source information.

        Returns:
            Dictionary with source metadata:
            - type: Source type name
            - width: Frame width (if known)
            - height: Frame height (if known)
            - fps: Frames per second (if known)
            - format: Pixel format (usually "RGB")
        """
        return {
            "type": self.__class__.__name__,
            "width": None,
            "height": None,
            "fps": None,
            "format": "RGB",
        }

    def close(self) -> None:
        """Close the source and release resources.

        Override if your source needs cleanup (e.g., closing files, cameras).
        Base implementation: transient sources need no explicit close action.
        """
        return  # Base: no resources to release in default implementation

    def __enter__(self) -> "Source":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __iter__(self) -> Iterator[np.ndarray]:
        """Iterate over frames."""
        return self.stream()

    def __repr__(self) -> str:
        """String representation."""
        info = self.get_info()
        return f"{self.__class__.__name__}({info})"