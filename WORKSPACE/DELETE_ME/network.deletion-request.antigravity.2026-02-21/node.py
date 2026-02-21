"""P2-X1 — Network Node (peer descriptor for multi-node coordination).

A NetworkNode represents one VJLive3 instance on the network.
Nodes discover each other via the NodeCoordinator (coordinator.py) and
share state: role, capabilities, timecode position, and health.

This module is pure data/logic — no ZeroMQ imports here.
The coordinator imports and wraps these.

Dependencies: stdlib only.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── NodeRole ──────────────────────────────────────────────────────────────────

class NodeRole(str, Enum):
    """Role of a VJLive3 node in a multi-node setup."""
    LEADER   = "leader"     # Timecode master, scene controller
    FOLLOWER = "follower"   # Syncs to leader clock
    RELAY    = "relay"      # Repeates output downstream (display node)
    ISOLATED = "isolated"   # No active peers found


# ── NodeCapability ────────────────────────────────────────────────────────────

class NodeCapability(str, Enum):
    """Optional capabilities a node may advertise."""
    AUDIO    = "audio"       # Has audio input
    GPU      = "gpu"         # Has GPU output
    MIDI     = "midi"        # Has MIDI input
    DMX      = "dmx"         # Has DMX output
    OSC      = "osc"         # Accepts OSC control
    ASTRA    = "astra"       # Has depth camera


# ── NodeInfo ──────────────────────────────────────────────────────────────────

@dataclass
class NodeInfo:
    """Descriptor for a discovered peer node."""
    node_id:       str                          # Unique ID (UUID or hostname)
    host:          str                          # IP or hostname
    port:          int                          # Coordination port
    role:          NodeRole = NodeRole.FOLLOWER
    capabilities:  List[NodeCapability] = field(default_factory=list)
    last_seen:     float = field(default_factory=time.monotonic)
    timecode_pos:  float = 0.0                 # seconds
    metadata:      Dict[str, Any] = field(default_factory=dict)

    # ── Derived ───────────────────────────────────────────────────────────────

    @property
    def is_alive(self, timeout: float = 5.0) -> bool:
        """True if this node was seen within the last `timeout` seconds."""
        return (time.monotonic() - self.last_seen) < timeout

    def touch(self) -> None:
        """Update last_seen to now."""
        self.last_seen = time.monotonic()

    def has_capability(self, cap: NodeCapability) -> bool:
        return cap in self.capabilities

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id":      self.node_id,
            "host":         self.host,
            "port":         self.port,
            "role":         self.role.value,
            "capabilities": [c.value for c in self.capabilities],
            "last_seen":    self.last_seen,
            "timecode_pos": self.timecode_pos,
            "metadata":     self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NodeInfo":
        return cls(
            node_id=d["node_id"],
            host=d["host"],
            port=d["port"],
            role=NodeRole(d.get("role", "follower")),
            capabilities=[NodeCapability(c) for c in d.get("capabilities", [])],
            last_seen=d.get("last_seen", time.monotonic()),
            timecode_pos=float(d.get("timecode_pos", 0.0)),
            metadata=d.get("metadata", {}),
        )


# ── NodeRegistry ──────────────────────────────────────────────────────────────

class NodeRegistry:
    """
    In-memory registry of discovered network nodes.

    Thread-safe. Used by NodeCoordinator to track live peers.

    Usage::

        registry = NodeRegistry(self_id="my-node")
        registry.register(NodeInfo(...))
        peers = registry.list_live()
        registry.prune(timeout=5.0)
    """

    def __init__(self, self_id: str) -> None:
        import threading
        self._lock = threading.RLock()
        self._self_id = self_id
        self._nodes: Dict[str, NodeInfo] = {}

    def register(self, node: NodeInfo) -> None:
        """Add or update a node (by node_id)."""
        with self._lock:
            self._nodes[node.node_id] = node

    def get(self, node_id: str) -> Optional[NodeInfo]:
        with self._lock:
            return self._nodes.get(node_id)

    def remove(self, node_id: str) -> bool:
        with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]
                return True
            return False

    def list_all(self) -> List[NodeInfo]:
        """All known nodes (including stale)."""
        with self._lock:
            return list(self._nodes.values())

    def list_live(self, timeout: float = 5.0) -> List[NodeInfo]:
        """Nodes seen within the last `timeout` seconds, excluding self."""
        now = time.monotonic()
        with self._lock:
            return [
                n for n in self._nodes.values()
                if n.node_id != self._self_id
                and (now - n.last_seen) < timeout
            ]

    def list_by_role(self, role: NodeRole) -> List[NodeInfo]:
        with self._lock:
            return [n for n in self._nodes.values() if n.role == role]

    def prune(self, timeout: float = 10.0) -> int:
        """Remove nodes not seen for `timeout` seconds. Returns count removed."""
        now = time.monotonic()
        with self._lock:
            stale = [
                nid for nid, n in self._nodes.items()
                if (now - n.last_seen) >= timeout and nid != self._self_id
            ]
            for nid in stale:
                del self._nodes[nid]
        return len(stale)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._nodes)

    @property
    def self_id(self) -> str:
        return self._self_id


__all__ = [
    "NodeRole",
    "NodeCapability",
    "NodeInfo",
    "NodeRegistry",
]
