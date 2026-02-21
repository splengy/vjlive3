"""Core NodeGraph — directed processing graph with topological execution.

Owns nodes and edges; responsible for:
- Connection management (with port-type validation)
- Topological sort execution each tick
- Dot-path parameter setting (node_id.param_name)
- Audio snapshot injection into the tick

Architecture note:
    This file stays < 500 lines. Registry lives in registry.py.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Iterator

from vjlive3.graph.node import Node
from vjlive3.graph.signal import SignalType
from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)


class GraphCycleError(Exception):
    """Raised when a cycle is detected in the graph."""


class PortTypeMismatchError(Exception):
    """Raised when connecting ports with incompatible signal types."""


@dataclass
class Edge:
    """A directed connection between two node ports.

    Args:
        id:          Unique edge identifier (auto-generated)
        src_node_id: Source node id
        src_port:    Source output port name
        dst_node_id: Destination node id
        dst_port:    Destination input port name
    """
    src_node_id: str
    src_port:    str
    dst_node_id: str
    dst_port:    str
    id:          str = field(default_factory=lambda: str(uuid.uuid4()))


class NodeGraph:
    """Directed processing graph.

    Nodes are added via ``add_node()``. Connections are made via
    ``connect()``, which validates port-type compatibility.
    ``tick()`` runs topological sort and calls each node's ``process()``
    in dependency order, passing outputs to downstream inputs.

    Example::

        graph = NodeGraph()
        src = SourceNode(node_id="src")
        fx  = BlurNode(node_id="fx")
        out = OutputNode(node_id="out")
        graph.add_node(src).add_node(fx).add_node(out)
        graph.connect("src", "frame", "fx", "frame_in")
        graph.connect("fx", "frame_out", "out", "frame_in")
        results = graph.tick(dt=0.016)
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}
        self._listeners: list = []

    # ------------------------------------------------------------------ #
    #  Node management                                                     #
    # ------------------------------------------------------------------ #

    def add_node(self, node: Node) -> "NodeGraph":
        """Add a node. Returns self for chaining."""
        if node.id in self._nodes:
            raise ValueError(f"Node id already exists: {node.id}")
        self._nodes[node.id] = node
        logger.debug("Graph: added node %s (%s)", node.id[:8], node.node_type)
        return self

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all edges connected to it."""
        if node_id not in self._nodes:
            return False
        # Remove incident edges
        to_remove = [
            eid for eid, e in self._edges.items()
            if e.src_node_id == node_id or e.dst_node_id == node_id
        ]
        for eid in to_remove:
            del self._edges[eid]
        del self._nodes[node_id]
        logger.debug("Graph: removed node %s", node_id[:8])
        return True

    def get_node(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def iter_nodes(self) -> Iterator[Node]:
        return iter(self._nodes.values())

    def node_count(self) -> int:
        return len(self._nodes)

    # ------------------------------------------------------------------ #
    #  Edge management                                                     #
    # ------------------------------------------------------------------ #

    def connect(
        self,
        src_node_id: str,
        src_port:    str,
        dst_node_id: str,
        dst_port:    str,
    ) -> str:
        """Connect an output port to an input port.

        Args:
            src_node_id: Source node id
            src_port:    Output port name on source node
            dst_node_id: Destination node id
            dst_port:    Input port name on destination node

        Returns:
            The edge id string.

        Raises:
            KeyError:              Node not found in graph
            AttributeError:        Port not found on node
            PortTypeMismatchError: Signal types incompatible
            GraphCycleError:       Connection would create a cycle
        """
        src = self._nodes.get(src_node_id)
        dst = self._nodes.get(dst_node_id)
        if src is None:
            raise KeyError(f"Source node not found: {src_node_id}")
        if dst is None:
            raise KeyError(f"Destination node not found: {dst_node_id}")

        out_port = src.get_output_port(src_port)
        in_port  = dst.get_input_port(dst_port)
        if out_port is None:
            raise AttributeError(f"Output port '{src_port}' not found on {src.node_type}")
        if in_port is None:
            raise AttributeError(f"Input port '{dst_port}' not found on {dst.node_type}")

        if not out_port.signal_type.compatible_with(in_port.signal_type):
            raise PortTypeMismatchError(
                f"Cannot connect {out_port.signal_type} → {in_port.signal_type}"
            )

        edge = Edge(
            src_node_id=src_node_id, src_port=src_port,
            dst_node_id=dst_node_id, dst_port=dst_port,
        )

        # Temporarily add edge to check for cycle
        self._edges[edge.id] = edge
        try:
            self._topo_sort()
        except GraphCycleError:
            del self._edges[edge.id]
            raise

        logger.debug(
            "Graph: connected %s.%s → %s.%s",
            src_node_id[:8], src_port, dst_node_id[:8], dst_port,
        )
        return edge.id

    def disconnect(self, edge_id: str) -> bool:
        """Remove an edge by id."""
        if edge_id not in self._edges:
            return False
        del self._edges[edge_id]
        return True

    def edge_count(self) -> int:
        return len(self._edges)

    # ------------------------------------------------------------------ #
    #  Parameter control                                                   #
    # ------------------------------------------------------------------ #

    def set_param(self, path: str, value: float) -> bool:
        """Set a node parameter using dot-path notation.

        Args:
            path:  "node_id.param_name"
            value: New value (clamped by parameter bounds)

        Returns:
            True if successfully set.
        """
        parts = path.split(".", 1)
        if len(parts) != 2:
            logger.warning("set_param: invalid path '%s'", path)
            return False
        node_id, param_name = parts
        node = self._nodes.get(node_id)
        if node is None:
            logger.warning("set_param: unknown node '%s'", node_id)
            return False
        ok = node.set_parameter(param_name, value)
        if ok:
            for cb in self._listeners:
                try:
                    cb(path, value)
                except Exception:
                    logger.exception("Graph listener raised")
        return ok

    def add_listener(self, callback) -> None:
        """Register a callback(path, value) fired on every set_param."""
        self._listeners.append(callback)

    # ------------------------------------------------------------------ #
    #  Execution                                                           #
    # ------------------------------------------------------------------ #

    def tick(
        self,
        dt: float = 0.016,
        audio_snapshot=None,
    ) -> dict[str, dict[str, Any]]:
        """Process all nodes in topological order.

        Args:
            dt:             Frame delta time in seconds.
            audio_snapshot: Optional AudioSnapshot from ReactivityBus.

        Returns:
            dict of node_id → {port_name: value} output maps.
        """
        order = self._topo_sort()
        # Accumulate outputs: src_node_id → {port → value}
        node_outputs: dict[str, dict[str, Any]] = {}

        for node_id in order:
            node = self._nodes[node_id]
            if not node.enabled:
                node_outputs[node_id] = {}
                continue

            # Gather inputs from upstream edges
            inputs: dict[str, Any] = {}
            if audio_snapshot is not None:
                inputs["__audio__"] = audio_snapshot

            for edge in self._edges.values():
                if edge.dst_node_id != node_id:
                    continue
                upstream = node_outputs.get(edge.src_node_id, {})
                value = upstream.get(edge.src_port)
                if value is not None:
                    inputs[edge.dst_port] = value

            try:
                outputs = node.process(inputs, dt)
                node_outputs[node_id] = outputs or {}
            except Exception:
                logger.exception("Node %s (%s) raised during process()", node_id[:8], node.node_type)
                node_outputs[node_id] = {}

        return node_outputs

    # ------------------------------------------------------------------ #
    #  Topological sort (Kahn's algorithm)                                 #
    # ------------------------------------------------------------------ #

    def _topo_sort(self) -> list[str]:
        """Return node ids in topological (dependency-first) order.

        Raises:
            GraphCycleError: If the graph contains a cycle.
        """
        # Build in-degree map and adjacency list
        in_degree: dict[str, int] = {nid: 0 for nid in self._nodes}
        adj: dict[str, list[str]] = {nid: [] for nid in self._nodes}

        for edge in self._edges.values():
            adj[edge.src_node_id].append(edge.dst_node_id)
            in_degree[edge.dst_node_id] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order: list[str] = []

        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for child in adj[nid]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if len(order) != len(self._nodes):
            raise GraphCycleError(
                "Graph contains a cycle — connection rejected"
            )
        return order

    # ------------------------------------------------------------------ #
    #  State                                                               #
    # ------------------------------------------------------------------ #

    def get_state(self) -> dict[str, Any]:
        """Serialise graph topology for persistence."""
        return {
            "nodes": [n.get_state() for n in self._nodes.values()],
            "edges": [
                {
                    "id": e.id,
                    "src_node_id": e.src_node_id,
                    "src_port": e.src_port,
                    "dst_node_id": e.dst_node_id,
                    "dst_port": e.dst_port,
                }
                for e in self._edges.values()
            ],
        }

    def __repr__(self) -> str:
        return (
            f"<NodeGraph nodes={len(self._nodes)} edges={len(self._edges)}>"
        )
