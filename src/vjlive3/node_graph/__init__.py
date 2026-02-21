"""
vjlive3.node_graph
==================
DAG-based effect chain (the UnifiedMatrix) for VJLive3.

Sub-modules (added as Phase 1 tasks complete):
    registry     — P1-N1: UnifiedMatrix + node registry (manifest-based)
    node_types   — P1-N2: Full node type collection from both codebases
    persistence  — P1-N3: Save/load state (orjson serialisation)
    ui           — P1-N4: Visual node graph UI (WebSocket-driven)

The node graph is represented as a networkx.DiGraph.
Node execution order is a topological sort of the DAG.
State serialisation uses orjson (10x faster than stdlib json) for
large session files with hundreds of nodes and parameter values.

Reference: VJlive-2/core/matrix/, graph/, graph_renderer.py, node_*.py
"""
