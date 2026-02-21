"""P2-H2 extension — OSC Address Space (namespace tree).

Maintains a tree of registered OSC addresses and their types/metadata,
supporting OSCQuery-style introspection without a running HTTP server.

Useful for:
- Advertising what addresses VJLive3 accepts (for OSCQuery discovery)
- Type-checking incoming values before dispatch
- Serialising the address tree to JSON for peer devices

No external dependencies required.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


# ── OscType enum-like constants ───────────────────────────────────────────────

class OscType:
    """OSC type tag constants (OSCQuery EXTENDED_TYPE)."""
    FLOAT  = "f"
    INT    = "i"
    STRING = "s"
    BOOL   = "T"   # True / "F" False represented as separate tags in OSC 1.0
    BLOB   = "b"
    DOUBLE = "d"
    VECTOR = "v"   # custom VJLive3 extension: list of floats


# ── AddressNode ───────────────────────────────────────────────────────────────

@dataclass
class AddressNode:
    """One node in the OSC address tree."""
    name:        str
    full_path:   str
    type_tag:    Optional[str] = None       # OscType constant or None for containers
    description: str = ""
    min_val:     Optional[float] = None
    max_val:     Optional[float] = None
    default_val: Optional[Any] = None
    read_only:   bool = False
    children:    Dict[str, "AddressNode"] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to OSCQuery-compatible dict for JSON export."""
        d: Dict[str, Any] = {
            "DESCRIPTION": self.description or self.name,
            "FULL_PATH": self.full_path,
        }
        if self.type_tag is not None:
            d["TYPE"] = self.type_tag
        if self.min_val is not None:
            d["RANGE"] = [{"MIN": self.min_val, "MAX": self.max_val}]
        if self.default_val is not None:
            d["VALUE"] = [self.default_val]
        if self.read_only:
            d["ACCESS"] = 1   # OSCQuery: 1=read-only, 3=read-write
        else:
            d["ACCESS"] = 3
        if self.children:
            d["CONTENTS"] = {k: v.to_dict() for k, v in self.children.items()}
        return d


# ── OscAddressSpace ───────────────────────────────────────────────────────────

class OscAddressSpace:
    """
    Thread-safe OSC address namespace tree.

    Supports registration of typed addresses and OSCQuery-style JSON export.

    Usage::

        space = OscAddressSpace()
        space.register("/vjlive/intensity", OscType.FLOAT,
                       description="Effect intensity", min_val=0.0, max_val=1.0)
        space.register("/vjlive/bpm", OscType.FLOAT, description="Current BPM")

        exists = space.has("/vjlive/intensity")   # True
        node = space.get("/vjlive/intensity")
        tree = space.to_dict()                    # OSCQuery JSON-ready dict
    """

    def __init__(self, host_name: str = "VJLive3", port: int = 7700) -> None:
        self._lock = threading.RLock()
        self._root = AddressNode(
            name="",
            full_path="/",
            description=f"{host_name} OSC namespace",
        )
        self._host_name = host_name
        self._port = port

    # ── Registration ──────────────────────────────────────────────────────────

    def register(
        self,
        address: str,
        type_tag: Optional[str] = None,
        *,
        description: str = "",
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        default_val: Optional[Any] = None,
        read_only: bool = False,
    ) -> AddressNode:
        """Register an OSC address in the namespace tree.

        Creates intermediate container nodes as needed.

        Args:
            address:     Full OSC address (must start with '/').
            type_tag:    OscType constant, or None for containers.
            description: Human-readable description.
            min_val:     Minimum value (for numeric types).
            max_val:     Maximum value (for numeric types).
            default_val: Default value.
            read_only:   If True, address is advertised as read-only.

        Returns:
            The created/updated AddressNode.

        Raises:
            ValueError: If address does not start with '/'.
        """
        if not address.startswith("/"):
            raise ValueError(f"OSC address must start with '/': {address!r}")

        parts = [p for p in address.split("/") if p]  # skip empty strings
        with self._lock:
            node = self._root
            built_path = ""
            for i, part in enumerate(parts):
                built_path += "/" + part
                if part not in node.children:
                    node.children[part] = AddressNode(
                        name=part,
                        full_path=built_path,
                    )
                node = node.children[part]

            # Update leaf with type info
            node.type_tag = type_tag
            node.description = description
            node.min_val = min_val
            node.max_val = max_val
            node.default_val = default_val
            node.read_only = read_only
            return node

    def unregister(self, address: str) -> bool:
        """Remove an address from the tree. Returns True if it existed."""
        if not address.startswith("/"):
            return False
        parts = [p for p in address.split("/") if p]
        with self._lock:
            return self._remove(self._root, parts)

    def _remove(self, node: AddressNode, parts: List[str]) -> bool:
        if not parts:
            return False
        key = parts[0]
        if key not in node.children:
            return False
        if len(parts) == 1:
            del node.children[key]
            return True
        return self._remove(node.children[key], parts[1:])

    # ── Lookup ────────────────────────────────────────────────────────────────

    def get(self, address: str) -> Optional[AddressNode]:
        """Return the AddressNode for an address, or None if not registered."""
        parts = [p for p in address.split("/") if p]
        with self._lock:
            node = self._root
            for part in parts:
                if part not in node.children:
                    return None
                node = node.children[part]
            return node

    def has(self, address: str) -> bool:
        """Return True if address is registered."""
        return self.get(address) is not None

    def list_addresses(self, prefix: str = "/") -> List[str]:
        """Return all registered leaf addresses under prefix (sorted)."""
        with self._lock:
            result: List[str] = []
            self._collect_leaves(self._root, result)
            return sorted(a for a in result if a.startswith(prefix))

    def _collect_leaves(self, node: AddressNode, result: List[str]) -> None:
        if node.type_tag is not None:
            result.append(node.full_path)
        for child in node.children.values():
            self._collect_leaves(child, result)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Return OSCQuery-compatible root dict (for JSON export)."""
        with self._lock:
            return {
                "DESCRIPTION":  f"{self._host_name} OSC namespace",
                "FULL_PATH":    "/",
                "HOST_INFO": {
                    "NAME":       self._host_name,
                    "OSC_PORT":   self._port,
                    "OSC_TRANSPORT": "UDP",
                },
                "CONTENTS": {
                    k: v.to_dict() for k, v in self._root.children.items()
                },
            }

    @property
    def address_count(self) -> int:
        """Total number of registered leaf addresses."""
        return len(self.list_addresses())


__all__ = ["OscType", "AddressNode", "OscAddressSpace"]
