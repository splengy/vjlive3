"""
Node dataclasses for ZeroMQ multi-node coordination.

Separating these from the coordinator keeps the coordinator under
the 750-line limit and makes each concept independently testable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class NodeType(Enum):
    """Role a VJLive3 node plays in a distributed installation."""

    MASTER = "master"
    VIDEO_WORKER = "video_worker"
    AUDIO_WORKER = "audio_worker"
    DISPLAY_WORKER = "display_worker"
    LLM_WORKER = "llm_worker"


class NodeStatus(Enum):
    """Lifecycle state of a network node."""

    OFFLINE = "offline"
    STARTING = "starting"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class NodeInfo:
    """Snapshot of a node's identity and health.

    METADATA constant — Prime Directive Rule 2.
    """

    METADATA: "dict[str, str]" = field(
        default_factory=lambda: {
            "name": "NodeInfo",
            "description": "Identity + health snapshot for one VJLive3 network node",
            "version": "1.0",
        },
        init=False,
        repr=False,
        compare=False,
    )

    node_id: str
    node_type: NodeType
    hostname: str
    ip_address: str
    status: NodeStatus = NodeStatus.OFFLINE
    capabilities: Dict[str, Any] = field(default_factory=dict)
    load: float = 0.0
    last_heartbeat: float = field(default_factory=time.monotonic)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def is_alive(self, timeout_seconds: float = 5.0) -> bool:
        """Return True if this node sent a heartbeat within *timeout_seconds*."""
        return (time.monotonic() - self.last_heartbeat) < timeout_seconds

    def beat(self) -> None:
        """Update the heartbeat timestamp to now."""
        self.last_heartbeat = time.monotonic()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a JSON-safe dict for wire format."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "load": self.load,
            "last_heartbeat": self.last_heartbeat,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeInfo":
        """Deserialise from wire dict."""
        return cls(
            node_id=data["node_id"],
            node_type=NodeType(data["node_type"]),
            hostname=data["hostname"],
            ip_address=data["ip_address"],
            status=NodeStatus(data.get("status", "offline")),
            capabilities=data.get("capabilities", {}),
            load=float(data.get("load", 0.0)),
            last_heartbeat=float(data.get("last_heartbeat", time.monotonic())),
        )
