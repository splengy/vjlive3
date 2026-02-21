"""Graph persistence — save and load NodeGraph to/from JSON.

Format::

    {
      "vjlive3_graph_version": 1,
      "nodes": [
        {"id": "...", "node_type": "GAIN", "name": "Master Gain",
         "enabled": true, "x": 0, "y": 0,
         "parameters": {"gain": {"value": 1.0, ...}}}
      ],
      "edges": [
        {"id": "...", "src_node_id": "...", "src_port": "output",
         "dst_node_id": "...", "dst_port": "input"}
      ]
    }
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vjlive3.graph.graph import NodeGraph, Edge
from vjlive3.graph.registry import NodeRegistry
from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)

_VERSION = 1


def save_graph(graph: NodeGraph, path: str | Path) -> None:
    """Serialise ``graph`` to a JSON file at ``path``.

    Args:
        graph: A NodeGraph instance.
        path:  Destination file path (created/overwritten).
    """
    path = Path(path)
    state = graph.get_state()
    state["vjlive3_graph_version"] = _VERSION
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    logger.info(
        "Graph saved: %s (%d nodes, %d edges)",
        path, len(state["nodes"]), len(state["edges"]),
    )


def load_graph(
    path: str | Path,
    registry: NodeRegistry,
) -> NodeGraph:
    """Deserialise a NodeGraph from a JSON file.

    Args:
        path:     Path to a JSON file previously saved by :func:`save_graph`.
        registry: NodeRegistry used to instantiate nodes by type name.

    Returns:
        A fully restored NodeGraph.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError:        If the file format is unrecognised.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Graph file not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))

    version = raw.get("vjlive3_graph_version", 0)
    if version != _VERSION:
        raise ValueError(f"Unsupported graph version: {version} (expected {_VERSION})")

    graph = NodeGraph()

    # Restore nodes
    for node_state in raw.get("nodes", []):
        node_type = node_state.get("node_type", "")
        node_id   = node_state.get("id")
        name      = node_state.get("name", node_type)
        try:
            node = registry.create(node_type, node_id=node_id, name=name)
            node.set_state(node_state)
            graph.add_node(node)
        except KeyError:
            logger.warning("Skipping unknown node type: '%s'", node_type)

    # Restore edges
    for edge_data in raw.get("edges", []):
        try:
            graph.connect(
                edge_data["src_node_id"], edge_data["src_port"],
                edge_data["dst_node_id"], edge_data["dst_port"],
            )
        except Exception as exc:
            logger.warning("Skipping invalid edge %s: %s", edge_data.get("id", "?"), exc)

    logger.info(
        "Graph loaded: %s (%d nodes, %d edges)",
        path, graph.node_count(), graph.edge_count(),
    )
    return graph
