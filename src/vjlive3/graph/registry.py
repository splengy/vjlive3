"""Node registry for VJLive3 graph system.

Replaces the 400-line if/elif factory in VJlive-2's UnifiedMatrix with a
clean plugin registry. Nodes register themselves by type name; the graph
instantiates by type lookup.

Usage::

    # Registration (in each node module or a plugins/__init__.py)
    from vjlive3.graph.registry import global_registry

    @global_registry.register("GAIN")
    class GainNode(Node):
        ...

    # Instantiation
    node = global_registry.create("GAIN", node_id="n1", name="Master Gain")
"""
from __future__ import annotations

import importlib
from typing import Type

from vjlive3.graph.node import Node
from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)


class NodeRegistry:
    """Maps node type strings to Node subclasses.

    Example::

        registry = NodeRegistry()
        registry.register("BLUR", BlurNode)          # explicit
        # or via decorator:
        @registry.register("BLUR")
        class BlurNode(Node): ...

        node = registry.create("BLUR", node_id="b1", name="Blur")
        print(registry.list_types())   # ["BLUR"]
    """

    def __init__(self) -> None:
        self._registry: dict[str, Type[Node]] = {}

    # ------------------------------------------------------------------ #
    #  Registration                                                        #
    # ------------------------------------------------------------------ #

    def register(self, type_name: str, cls: Type[Node] | None = None):
        """Register a Node class under ``type_name``.

        Can be used as a plain call or as a class decorator::

            registry.register("FOO", FooNode)

            @registry.register("BAR")
            class BarNode(Node): ...
        """
        def _do_register(klass: Type[Node]) -> Type[Node]:
            if not issubclass(klass, Node):
                raise TypeError(f"{klass} is not a subclass of Node")
            self._registry[type_name] = klass
            logger.debug("Registered node type: %s → %s", type_name, klass.__name__)
            return klass

        if cls is not None:
            return _do_register(cls)

        # Called as decorator: @registry.register("TYPE")
        return _do_register

    # ------------------------------------------------------------------ #
    #  Instantiation                                                       #
    # ------------------------------------------------------------------ #

    def create(
        self,
        type_name: str,
        node_id: str | None = None,
        name:    str | None = None,
    ) -> Node:
        """Instantiate a node by type name.

        Args:
            type_name: Registered type identifier.
            node_id:   Optional explicit UUID (generated if None).
            name:      Display name (defaults to type_name).

        Raises:
            KeyError: If type_name is not registered.
        """
        cls = self._registry.get(type_name)
        if cls is None:
            raise KeyError(
                f"Unknown node type: '{type_name}'. "
                f"Available: {sorted(self._registry)}"
            )
        node = cls(node_id=node_id, name=name or type_name)
        logger.debug("Created node: %s id=%s", type_name, node.id[:8])
        return node

    # ------------------------------------------------------------------ #
    #  Inspection                                                          #
    # ------------------------------------------------------------------ #

    def list_types(self) -> list[str]:
        """Return all registered type names (sorted)."""
        return sorted(self._registry)

    def get_class(self, type_name: str) -> Type[Node] | None:
        """Return the Node class for type_name, or None if not registered."""
        return self._registry.get(type_name)

    def __contains__(self, type_name: str) -> bool:
        return type_name in self._registry

    def __len__(self) -> int:
        return len(self._registry)

    def __repr__(self) -> str:
        return f"<NodeRegistry types={sorted(self._registry)}>"


# ---------------------------------------------------------------------- #
#  Global singleton                                                        #
# ---------------------------------------------------------------------- #

global_registry: NodeRegistry = NodeRegistry()
"""Module-level singleton used by default in NodeGraph and plugins."""
