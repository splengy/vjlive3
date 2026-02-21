"""Abstract base classes for effects.

This module defines the base classes and interfaces that all effects must
implement to be compatible with the VJLive3 pipeline.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import numpy as np


class Effect(ABC):
    """Abstract base class for all effects.

    All effects must inherit from this class and implement the required methods.

    Example:
        >>> class MyEffect(Effect):
        ...     def apply(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        ...         # Apply effect to frame
        ...         return processed_frame
        ...
        ...     def get_parameters(self) -> Dict[str, Any]:
        ...         return {"param1": self.param1}
        ...
        ...     def set_parameter(self, name: str, value: Any) -> None:
        ...         setattr(self, name, value)
    """

    @abstractmethod
    def apply(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """Apply the effect to a frame.

        Args:
            frame: Input frame as HxWxC numpy array (RGB)
            timestamp: Current time in seconds

        Returns:
            Processed frame as HxWxC numpy array (RGB)

        Raises:
            ProcessingError: If effect cannot be applied
        """
        # abstractmethod — must be implemented by subclass
        raise NotImplementedError  # noqa: this IS the abstract contract

    def get_parameters(self) -> Dict[str, Any]:
        """Get current effect parameters.

        Returns:
            Dictionary mapping parameter names to their current values
        """
        return {}

    def set_parameter(self, name: str, value: Any) -> None:
        """Set an effect parameter.

        Args:
            name: Parameter name
            value: Parameter value

        Raises:
            ValueError: If parameter name is invalid or value is inappropriate
        """
        raise ValueError(f"Parameter '{name}' is not settable for {self.__class__.__name__}")

    def reset(self) -> None:
        """Reset effect to initial state.

        This method is called when the pipeline is reset.
        Override if your effect maintains internal state.
        Base implementation: stateless effects need no reset action.
        """
        return  # Base: stateless — no action required

    def get_statistics(self) -> Dict[str, Any]:
        """Get effect-specific statistics.

        Returns:
            Dictionary with effect-specific metrics (e.g., processing time)
        """
        return {}

    def __repr__(self) -> str:
        """String representation of the effect."""
        params = ", ".join(f"{k}={v}" for k, v in self.get_parameters().items())
        return f"{self.__class__.__name__}({params})"


class ProcessingError(Exception):
    """Exception raised when an effect fails to process a frame."""