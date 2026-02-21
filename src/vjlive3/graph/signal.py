"""Signal type definitions and port system for VJLive3 node graph.

Provides:
    SignalType — enum of compatible port types
    Port       — typed connection point on a node
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SignalType(str, Enum):
    """Port signal types.

    Compatibility rules:
    - Ports must have matching types, OR either end must be SignalType.ANY.
    - This allows generic routing nodes without explicit casting.
    """
    VIDEO      = "video"        # Frame data (np.ndarray H×W×C)
    AUDIO      = "audio"        # Audio samples / AudioSnapshot
    MODULATION = "modulation"   # Continuous float in 0-10 range
    TRIGGER    = "trigger"      # Momentary bool pulse
    ANY        = "any"          # Wildcard — matches all types

    def compatible_with(self, other: "SignalType") -> bool:
        """Return True if this port type can connect to ``other``."""
        return self is SignalType.ANY or other is SignalType.ANY or self is other


@dataclass(frozen=True)
class Port:
    """A typed connection point on a Node.

    Args:
        name:        Port identifier (unique within input or output set)
        signal_type: Type of data carried by this port
        description: Human-readable description

    Example::

        Port("frame_in", SignalType.VIDEO, "Incoming video frame")
    """
    name:        str
    signal_type: SignalType
    description: str = ""
