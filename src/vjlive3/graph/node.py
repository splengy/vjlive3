"""Base Node and Parameter for VJLive3 node graph.

Every processing unit in the graph inherits from Node.
Parameters use a typed dataclass instead of raw dicts.
"""
from __future__ import annotations

import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from vjlive3.graph.signal import Port, SignalType
from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Parameter:
    """A typed, range-clamped node parameter.

    All numeric parameters are stored in **native units** and converted to
    the canonical 0-10 signal range only when crossing node boundaries.

    Args:
        name:        Unique identifier within the node
        value:       Current value (native units)
        min_value:   Minimum allowed value
        max_value:   Maximum allowed value
        description: Human-readable description
        group:       UI grouping hint (e.g. "Colour", "Timing")

    Example::

        p = Parameter("brightness", 1.0, 0.0, 2.0, "Master brightness")
        p.set(1.5)
        print(p.to_signal())   # → 7.5  (in 0-10 range)
    """
    name:        str
    value:       float = 5.0
    min_value:   float = 0.0
    max_value:   float = 10.0
    description: str   = ""
    group:       str   = "General"

    def set(self, v: float) -> None:
        """Set value, clamping to [min_value, max_value]."""
        self.value = max(self.min_value, min(self.max_value, float(v)))

    def to_signal(self) -> float:
        """Convert native value to normalised 0-10 signal range."""
        span = self.max_value - self.min_value
        if span == 0:
            return 0.0
        return max(0.0, min(10.0, (self.value - self.min_value) / span * 10.0))

    def from_signal(self, signal: float) -> None:
        """Set value from a 0-10 signal value."""
        self.set(self.min_value + (signal / 10.0) * (self.max_value - self.min_value))

    def to_dict(self) -> dict[str, Any]:
        """Serialise for persistence."""
        return {
            "name": self.name,
            "value": self.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "description": self.description,
            "group": self.group,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Parameter":
        """Deserialise from persistence dict."""
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class Node(ABC):
    """Abstract base class for all graph nodes.

    Subclasses define their ports and parameters at class level via
    ``_input_ports``, ``_output_ports``, and ``_parameters``, then implement
    the ``process()`` method.

    .. note::
        Ports are **class-level** (shared structure); parameter **values** are
        instance-level clones so each node instance has independent state.

    Example::

        class GainNode(Node):
            node_type = "GAIN"
            _input_ports = [Port("input", SignalType.VIDEO)]
            _output_ports = [Port("output", SignalType.VIDEO)]
            _parameters = [Parameter("gain", 1.0, 0.0, 4.0, "Output gain")]

            def process(self, inputs, dt):
                frame = inputs.get("input")
                if frame is not None:
                    return {"output": frame * self.get_parameter("gain").value}
                return {}
    """

    node_type:     str = "BASE"
    _input_ports:  list[Port] = []
    _output_ports: list[Port] = []
    _parameters:   list[Parameter] = []

    def __init__(self, node_id: str | None = None, name: str = "") -> None:
        self.id: str   = node_id or str(uuid.uuid4())
        self.name: str = name or self.node_type
        self.enabled:  bool = True

        # Position in graph canvas (for UI)
        self.x: float = 0.0
        self.y: float = 0.0

        # Instance-level parameter copies (independent from class defs)
        self._params: dict[str, Parameter] = {
            p.name: Parameter(
                name=p.name, value=p.value,
                min_value=p.min_value, max_value=p.max_value,
                description=p.description, group=p.group,
            )
            for p in self.__class__._parameters
        }

        self._lock = threading.RLock()
        logger.debug("Node created: %s (%s) id=%s", self.name, self.node_type, self.id)

    # ------------------------------------------------------------------ #
    #  Ports                                                               #
    # ------------------------------------------------------------------ #

    @property
    def input_ports(self) -> list[Port]:
        return self.__class__._input_ports

    @property
    def output_ports(self) -> list[Port]:
        return self.__class__._output_ports

    def get_input_port(self, name: str) -> Port | None:
        return next((p for p in self.input_ports if p.name == name), None)

    def get_output_port(self, name: str) -> Port | None:
        return next((p for p in self.output_ports if p.name == name), None)

    # ------------------------------------------------------------------ #
    #  Parameters                                                          #
    # ------------------------------------------------------------------ #

    def get_parameter(self, name: str) -> Parameter | None:
        return self._params.get(name)

    def set_parameter(self, name: str, value: float) -> bool:
        """Set parameter value. Returns False if param doesn't exist."""
        with self._lock:
            p = self._params.get(name)
            if p is None:
                return False
            p.set(value)
            return True

    def parameters(self) -> dict[str, Parameter]:
        return dict(self._params)

    # ------------------------------------------------------------------ #
    #  Processing                                                          #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def process(self, inputs: dict[str, Any], dt: float) -> dict[str, Any]:
        """Process inputs and return outputs.

        Args:
            inputs: dict of port_name -> value from connected upstream nodes
            dt:     frame delta time in seconds

        Returns:
            dict of output_port_name -> value
        """

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    # ------------------------------------------------------------------ #
    #  Persistence                                                         #
    # ------------------------------------------------------------------ #

    def get_state(self) -> dict[str, Any]:
        """Serialise node state for save/load."""
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type,
            "enabled": self.enabled,
            "x": self.x,
            "y": self.y,
            "parameters": {n: p.to_dict() for n, p in self._params.items()},
        }

    def set_state(self, state: dict[str, Any]) -> None:
        """Restore node state from a saved dict."""
        self.name    = state.get("name", self.name)
        self.enabled = state.get("enabled", True)
        self.x       = state.get("x", 0.0)
        self.y       = state.get("y", 0.0)
        for pname, pdata in state.get("parameters", {}).items():
            if pname in self._params:
                self._params[pname].set(pdata.get("value", self._params[pname].value))

    def __repr__(self) -> str:
        return f"<Node {self.node_type}({self.id[:8]}) '{self.name}'>"
