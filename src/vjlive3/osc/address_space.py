"""
OSCQuery Address Space

Maintains a typed tree of OSC address nodes that can be serialised to
JSON for the OSCQuery HTTP discovery protocol.

No external dependencies beyond stdlib.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


class OSCType(Enum):
    """Standard OSC type tags."""

    INT = "i"
    FLOAT = "f"
    STRING = "s"
    BOOL = "T"  # True / False — represented as T/F in OSC
    BLOB = "b"
    NONE = "N"  # impulse / no value


class OSCAccess(Enum):
    """OSCQuery access flags."""

    READ_ONLY = 1
    WRITE_ONLY = 2
    READ_WRITE = 3


@dataclass
class OSCNode:
    """A single node in the OSCQuery address space tree.

    METADATA constant required by Prime Directive Rule 2.
    """

    METADATA: "dict[str, str]" = field(
        default_factory=lambda: {
            "name": "OSCNode",
            "description": "One address-space node in the OSCQuery tree",
            "version": "1.0",
        },
        init=False,
        repr=False,
        compare=False,
    )

    path: str
    osc_type: OSCType = OSCType.NONE
    value: Any = None
    description: str = ""
    access: OSCAccess = OSCAccess.READ_WRITE
    children: Dict[str, "OSCNode"] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_child(self, node: "OSCNode") -> None:
        """Attach *node* as a child, keyed by its leaf name."""
        leaf = node.path.rstrip("/").rsplit("/", 1)[-1]
        self.children[leaf] = node
        logger.debug("OSCNode: added child %s under %s", leaf, self.path)

    def remove_child(self, leaf: str) -> bool:
        """Remove a child by its leaf name.  Returns True if removed."""
        if leaf in self.children:
            del self.children[leaf]
            logger.debug("OSCNode: removed child %s from %s", leaf, self.path)
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Return OSCQuery-compatible JSON representation of this node."""
        result: Dict[str, Any] = {
            "DESCRIPTION": self.description,
            "ACCESS": self.access.value,
        }

        if self.osc_type is not OSCType.NONE:
            result["TYPE"] = self.osc_type.value
            if self.value is not None:
                result["VALUE"] = [self.value]

        if self.children:
            contents: Dict[str, Any] = {}
            for leaf, child in self.children.items():
                contents[leaf] = child.to_dict()
            result["CONTENTS"] = contents

        return result


class OSCAddressSpace:
    """Root of the OSCQuery address tree.

    All VJLive3 controllable parameters and state endpoints are
    registered here so that OSCQuery clients (e.g. TouchOSC) can
    auto-discover the full API surface.
    """

    METADATA = {
        "name": "OSCAddressSpace",
        "description": "OSCQuery address tree — full parameter registry",
        "version": "1.0",
    }

    def __init__(self) -> None:
        self._root = OSCNode(path="/", description="VJLive3 OSCQuery Root")
        logger.info("OSCAddressSpace: initialised")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        path: str,
        osc_type: OSCType = OSCType.NONE,
        value: Any = None,
        description: str = "",
        access: OSCAccess = OSCAccess.READ_WRITE,
    ) -> OSCNode:
        """Create and register a node at *path*, creating intermediate nodes."""
        parts = [p for p in path.strip("/").split("/") if p]
        current = self._root

        # Walk / create the path
        accumulated = ""
        for i, part in enumerate(parts):
            accumulated += f"/{part}"
            if part not in current.children:
                node = OSCNode(path=accumulated, description=f"Container: {part}")
                current.add_child(node)
            current = current.children[part]

        # Configure the leaf
        current.osc_type = osc_type
        current.value = value
        current.description = description
        current.access = access
        logger.debug("OSCAddressSpace: registered %s (%s)", path, osc_type.name)
        return current

    def unregister(self, path: str) -> bool:
        """Remove a node by path.  Returns True on success."""
        parts = [p for p in path.strip("/").split("/") if p]
        if not parts:
            return False

        parent = self._get_node("/".join(parts[:-1]) or "/")
        if parent is None:
            return False

        return parent.remove_child(parts[-1])

    # ------------------------------------------------------------------
    # Lookup & value update
    # ------------------------------------------------------------------

    def get_node(self, path: str) -> Optional[OSCNode]:
        """Fetch a node by path; returns None if absent."""
        return self._get_node(path)

    def set_value(self, path: str, value: Any) -> bool:
        """Update the value of a registered node.  Returns True on success."""
        node = self._get_node(path)
        if node is None:
            logger.warning("OSCAddressSpace: set_value: unknown path %s", path)
            return False
        node.value = value
        return True

    def iter_nodes(self) -> Iterator[OSCNode]:
        """Depth-first iteration over every node in the tree."""
        yield from self._iter(self._root)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Full OSCQuery JSON dump — root object."""
        return {
            "DESCRIPTION": "VJLive3",
            "ACCESS": OSCAccess.READ_WRITE.value,
            "CONTENTS": {
                leaf: child.to_dict()
                for leaf, child in self._root.children.items()
            },
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_node(self, path: str) -> Optional[OSCNode]:
        if path in ("", "/"):
            return self._root

        parts = [p for p in path.strip("/").split("/") if p]
        current = self._root
        for part in parts:
            if part not in current.children:
                return None
            current = current.children[part]
        return current

    @staticmethod
    def _iter(node: OSCNode) -> Iterator[OSCNode]:
        yield node
        for child in node.children.values():
            yield from OSCAddressSpace._iter(child)
