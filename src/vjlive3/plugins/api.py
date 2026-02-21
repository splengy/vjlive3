"""
Plugin API for VJLive3.

Ported directly from VJlive-2/core/plugin_api.py.
Defines the base classes and context that plugins interact with.
"""
# Source: VJlive-2/core/plugin_api.py (lines 1-196)

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class PluginContext:
    """
    Context provided to plugins.

    Allows plugins to:
    - Access specific parts of the render engine (safely)
    - Load shaders
    - Set parameters
    - Subscribe to events

    Source: VJlive-2/core/plugin_api.py:PluginContext
    """

    def __init__(self, engine, shader_loader=None):
        self._engine = engine
        self._shader_loader = shader_loader
        self.delta_time: float = 0.016  # Updated each frame by the render loop

    def load_shader(self, shader_name: str) -> Optional[Any]:
        """Load shader from plugin directory or system resources."""
        if self._shader_loader:
            return self._shader_loader.load(shader_name)
        return None

    def set_parameter(self, param_path: str, value: Any) -> None:
        """Set parameter in the engine."""
        try:
            if hasattr(self._engine, 'set_parameter'):
                self._engine.set_parameter(param_path, value)
        except Exception as exc:
            logger.warning("Failed to set parameter %s: %s", param_path, exc)

    def get_parameter(self, param_path: str) -> Any:
        """Get parameter from the engine."""
        try:
            if hasattr(self._engine, 'get_parameter'):
                return self._engine.get_parameter(param_path)
        except Exception as exc:
            logger.warning("Failed to get parameter %s: %s", param_path, exc)
        return None

    def emit_event(self, event_name: str, data: Any) -> None:
        """Emit custom event to the system."""
        try:
            if hasattr(self._engine, 'emit_event'):
                self._engine.emit_event(event_name, data)
            elif hasattr(self._engine, 'broadcast_event'):
                self._engine.broadcast_event(event_name, data)
        except Exception as exc:
            logger.warning("Failed to emit event %s: %s", event_name, exc)

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """Subscribe to system event."""
        try:
            if hasattr(self._engine, 'subscribe'):
                self._engine.subscribe(event_name, callback)
        except Exception as exc:
            logger.warning("Failed to subscribe to %s: %s", event_name, exc)

    def schedule(self, delay_seconds: float, callback: Callable) -> None:
        """Schedule callback after delay."""
        try:
            if hasattr(self._engine, 'schedule'):
                self._engine.schedule(delay_seconds, callback)
        except Exception as exc:
            logger.warning("Failed to schedule for %.2fs: %s", delay_seconds, exc)


class PluginBase(ABC):
    """
    Base class for all VJLive3 plugins.

    Source: VJlive-2/core/plugin_api.py:PluginBase
    """

    name: str = "Unknown Plugin"
    version: str = "0.0.0"
    author: str = "Unknown"
    description: str = ""

    # Populated by loader
    manifest_path: str = ""

    def __init__(self) -> None:
        self.parameters: Dict[str, Dict] = {}
        self.context: Optional[PluginContext] = None
        self.enabled: bool = True

    def initialize(self, context: PluginContext) -> None:
        """Called when plugin is loaded. Override to set up resources."""
        self.context = context

    def cleanup(self) -> None:
        """Called when plugin is unloaded. Override to free resources."""


class EffectPlugin(PluginBase):
    """
    Base class for video effect plugins.

    Source: VJlive-2/core/plugin_api.py:EffectPlugin
    """

    @abstractmethod
    def process_frame(
        self,
        input_texture: int,
        params: Dict[str, Any],
        context: PluginContext,
    ) -> int:
        """
        Process one video frame.

        Args:
            input_texture: OpenGL texture ID of the input frame.
            params: Current parameter values keyed by parameter name.
            context: Plugin context for accessing engine resources.

        Returns:
            Output texture ID (may be same as input for in-place effects).
        """


class ModifierPlugin(PluginBase):
    """
    Base class for control-signal modifier plugins.

    Source: VJlive-2/core/plugin_api.py:ModifierPlugin
    """

    @abstractmethod
    def process_signal(
        self,
        input_value: float,
        params: Dict[str, Any],
        context: PluginContext,
    ) -> float:
        """
        Process a control signal.

        Args:
            input_value: Input signal (0–10 range, matching parameter convention).
            params: Current parameter values.
            context: Plugin context.

        Returns:
            Transformed output signal value.
        """


class AgentPlugin(PluginBase):
    """
    Base class for AI agent plugins.

    Source: VJlive-2/core/plugin_api.py:AgentPlugin
    """

    def on_frame(self, context: PluginContext) -> None:
        """Called every render frame."""

    def on_beat(self, beat_info: Dict, context: PluginContext) -> None:
        """Called when a beat is detected."""

    def on_event(self, event_name: str, data: Any, context: PluginContext) -> None:
        """Called when a custom event is emitted."""


class UIPlugin(PluginBase):
    """
    Base class for UI module plugins (backend-side placeholder).

    Source: VJlive-2/core/plugin_api.py:UIPlugin
    """


__all__ = [
    "PluginContext",
    "PluginBase",
    "EffectPlugin",
    "ModifierPlugin",
    "AgentPlugin",
    "UIPlugin",
]
