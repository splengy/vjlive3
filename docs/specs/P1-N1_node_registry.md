# Spec: P1-N1 — UnifiedMatrix + Node Registry

**Phase:** Phase 1 / P1-N1
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Source References:** `VJlive-2/core/matrix/node.py`, `VJlive-2/core/matrix/registry.py`, `VJlive-2/core/matrix/unified_matrix.py`
**Depends On:** P1-P1 (PluginRegistry), P1-A3 (ReactivityBus)

---

## What This Module Does

Provides the foundation node graph layer for VJLive3. Defines the `NodeBase` abstract class
(METADATA-carrying, dirty-flag, quarantine system) and a `NodeRegistry` that maps node type IDs
to their classes. Also provides a `NodeGraph` that holds a live set of `NodeBase` instances
connected by edges, processes them in topological order each tick, and exposes serialisation/
deserialisation to JSON for project save/load. This replaces the `UnifiedMatrix` in VJlive-2
with a clean, SPEC FIRST ground-up implementation limited to the Phase 1 scope (no audio
nodes, no hardware nodes — those are Phase 2).

---

## What It Does NOT Do

- Does NOT implement any specific effect/generator/modulator nodes (that's P1-N2)
- Does NOT persist to disk (that's P1-N3)
- Does NOT render a visual node graph UI (that's P1-N4)
- Does NOT integrate with GPU rendering pipeline (that's P1-R5)
- Does NOT add audio-reactive or hardware nodes (Phase 2)

---

## Public Interface

### NodeBase

```python
# vjlive3/nodes/base.py

from typing import Any, Dict, List, Optional
import uuid


class NodeBase:
    """
    Abstract base for all VJLive3 graph nodes.

    Subclasses MUST define:
        METADATA: dict — with 'id', 'name', 'description', 'inputs', 'outputs', 'params'
    """

    METADATA: dict = {
        "id":          "",          # type identifier, e.g. "effect.blur"
        "name":        "Base Node",
        "description": "Abstract base class",
        "inputs":      [],          # [{name, type}]
        "outputs":     [],          # [{name, type}]
        "params":      [],          # [{id, name, type, min, max, default}]
    }

    def __init__(self, node_id: Optional[str] = None) -> None:
        self.id: str = node_id or str(uuid.uuid4())
        self.parameters: Dict[str, Any] = {}     # hydrated from METADATA["params"] defaults
        self.inputs: Dict[str, Optional[str]] = {}   # input_name → connected_node_id
        self.outputs: Dict[str, List[str]] = {}   # output_name → [connected_node_ids]
        self.active: bool = True
        self.x: float = 0.0   # UI position
        self.y: float = 0.0

        # Error / quarantine tracking
        self.error_state: Optional[str] = None
        self.error_count: int = 0
        self.quarantined: bool = False

    def set_parameter(self, param_id: str, value: Any) -> None:
        """Update a parameter. Raises KeyError if param unknown."""

    def get_parameter(self, param_id: str) -> Any:
        """Return parameter value."""

    def set_position(self, x: float, y: float) -> None:
        """Update canvas position for UI."""

    def set_active(self, active: bool) -> None:
        """Enable/disable. Re-enabling resets quarantine."""

    def set_error(self, message: str) -> None:
        """Record error. Quarantines node after 5 errors in 5 seconds."""

    def clear_error(self) -> None:
        """Clear error state."""

    def process(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute node logic for one frame.

        Args:
            inputs:  Dict of input-name → resolved value from upstream nodes
            context: Shared frame context (dt, frame_count, audio_frame, etc.)

        Returns:
            Dict of output-name → computed value
        """

    def serialize(self) -> Dict[str, Any]:
        """Return JSON-serialisable state snapshot."""

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'NodeBase':
        """Reconstruct node from serialized state."""
```

### NodeRegistry

```python
# vjlive3/nodes/registry.py

from typing import Optional, Type, List, Dict
from vjlive3.nodes.base import NodeBase


class NodeRegistry:
    """
    Thread-safe registry of node type classes.

    Each node type registers itself by calling NodeRegistry.register().
    """

    def register(self, cls: Type[NodeBase]) -> None:
        """
        Register a node type.

        cls.METADATA['id'] is used as the unique key.
        Raises ValueError if METADATA['id'] is empty.
        Raises ValueError if type_id already registered with a DIFFERENT class.
        Idempotent for the same class.
        """

    def get(self, type_id: str) -> Optional[Type[NodeBase]]:
        """Return node class for type_id, or None."""

    def all_types(self) -> List[str]:
        """Return sorted list of all registered type IDs."""

    def count(self) -> int:
        """Return number of registered node types."""
```

### NodeGraph

```python
# vjlive3/nodes/graph.py

from typing import Dict, Optional, List, Any, Tuple
from vjlive3.nodes.base import NodeBase
from vjlive3.nodes.registry import NodeRegistry


class NodeGraph:
    """
    Live node graph: instantiated nodes + edges, processed each frame.

    Processing order: topological sort of DAG edges.
    Cycles are detected at add_edge() time and rejected.
    """

    def __init__(self, registry: NodeRegistry) -> None:
        """
        Args:
            registry: Type registry for deserialising node types.
        """

    # -- Node management --

    def add_node(self, node: NodeBase) -> None:
        """Add a node to the graph. Raises ValueError if id already exists."""

    def remove_node(self, node_id: str) -> bool:
        """Remove node and all its edges. Returns True if existed."""

    def get_node(self, node_id: str) -> Optional[NodeBase]:
        """Return node by ID, or None."""

    def nodes(self) -> List[NodeBase]:
        """Return snapshot of all nodes."""

    # -- Edge management --

    def add_edge(
        self,
        from_node_id: str,
        output_name: str,
        to_node_id: str,
        input_name: str,
    ) -> None:
        """
        Connect an output to an input.

        Raises ValueError if:
            - Either node does not exist
            - Output/input name not in node's METADATA
            - Connection would create a cycle
        """

    def remove_edge(
        self,
        from_node_id: str,
        output_name: str,
        to_node_id: str,
        input_name: str,
    ) -> bool:
        """Remove edge. Returns True if existed."""

    # -- Frame processing --

    def tick(self, context: Dict[str, Any]) -> None:
        """
        Process all nodes for one frame.

        1. Topological sort of active nodes
        2. For each node: resolve inputs from upstream outputs, call process()
        3. Skip quarantined nodes
        4. Log errors per-node without crashing the graph
        """

    # -- Serialisation --

    def serialize(self) -> Dict[str, Any]:
        """Return JSON-serialisable full graph state."""

    def deserialize(self, data: Dict[str, Any]) -> None:
        """
        Reconstruct graph from serialized state.

        Clears current graph first.
        Uses registry to look up node types.
        Warns on unknown type IDs (does not crash).
        """
```

---

## Node Context Dict (passed to every `process()` call)

```python
context = {
    "dt":          float,     # seconds since last tick
    "frame_count": int,       # monotonically increasing
    "fps":         float,     # current measured FPS
    "audio_frame": AudioFrame | None,   # from P1-A1 (None if audio off)
    "beat_state":  BeatState | None,    # from P1-A2 (None if audio off)
}
```

---

## Edge Cases and Error Handling

- **Cycle detection:** `add_edge()` runs DFS to detect cycles before adding. Raises `ValueError`.
- **Node not found:** `add_edge()` with unknown node id raises `ValueError`.
- **Quarantined node:** skipped in `tick()`, outputs treated as empty.
- **process() exception:** caught per-node, logged, `set_error()` called (may trigger quarantine).
- **Deserialization with unknown type:** log WARNING, skip node, continue loading rest of graph.
- **Empty graph `tick()`:** no-op, no error.

---

## Dependencies

### External
- None beyond Python stdlib

### Internal
- `vjlive3.nodes.base.NodeBase`
- `vjlive3.audio.analyzer.AudioFrame` (P1-A1, optional)
- `vjlive3.audio.beat_detector.BeatState` (P1-A2, optional)

---

## Test Plan

| Test ID | What It Verifies |
|---------|-----------------|
| `test_nodebase_hydrates_defaults` | params initialised from METADATA defaults |
| `test_nodebase_set_parameter` | set_parameter updates value |
| `test_nodebase_unknown_param_raises` | KeyError on unknown param |
| `test_nodebase_quarantine_after_5_errors` | 5 errors in 5s → quarantined=True, active=False |
| `test_nodebase_clear_error` | clear_error resets error_state |
| `test_nodebase_deserialize_serialize_roundtrip` | serialize then deserialize preserves state |
| `test_registry_register_get` | register → get returns class |
| `test_registry_duplicate_same_class_ok` | same class registered twice → no error |
| `test_registry_duplicate_diff_class_raises` | different class at same id → ValueError |
| `test_graph_add_and_get` | add_node → get_node returns it |
| `test_graph_remove_node` | remove_node deletes node and edges |
| `test_graph_add_edge_valid` | add_edge between compatible nodes succeeds |
| `test_graph_add_edge_cycle_raises` | cyclic connection → ValueError |
| `test_graph_add_edge_unknown_node_raises` | missing node → ValueError |
| `test_graph_tick_calls_process` | tick invokes process() on each active node |
| `test_graph_tick_skips_quarantined` | quarantined node's process() not called |
| `test_graph_tick_error_no_crash` | node.process() raising doesn't halt graph |
| `test_graph_topological_order` | upstream node processed before downstream |
| `test_graph_serialize_deserialize` | full graph round-trips through JSON |
| `test_graph_deserialize_unknown_type_warning` | unknown type logs warning, skips node |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] All 20 tests pass
- [ ] No file > 750 lines (split `base.py`, `registry.py`, `graph.py` if needed)
- [ ] No stubs
- [ ] BOARD.md P1-N1 marked ✅
- [ ] Lock released in LOCKS.md
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Command

```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_node_graph.py -v

# Smoke test: build a tiny 2-node graph and tick it
PYTHONPATH=src python3 -c "
from vjlive3.nodes.base import NodeBase
from vjlive3.nodes.registry import NodeRegistry
from vjlive3.nodes.graph import NodeGraph

class SourceNode(NodeBase):
    METADATA = {'id': 'source', 'name': 'Source', 'description': 'Test source node',
                'inputs': [], 'outputs': [{'name': 'out', 'type': 'any'}], 'params': []}
    def process(self, inputs, context):
        return {'out': 42}

class SinkNode(NodeBase):
    METADATA = {'id': 'sink', 'name': 'Sink', 'description': 'Test sink node',
                'inputs': [{'name': 'in', 'type': 'any'}], 'outputs': [], 'params': []}
    last_val = None
    def process(self, inputs, context):
        SinkNode.last_val = inputs.get('in')
        return {}

registry = NodeRegistry()
registry.register(SourceNode)
registry.register(SinkNode)

graph = NodeGraph(registry)
src = SourceNode(); snk = SinkNode()
graph.add_node(src); graph.add_node(snk)
graph.add_edge(src.id, 'out', snk.id, 'in')
graph.tick({'dt': 0.016, 'frame_count': 1, 'fps': 60.0})
print('Sink received:', SinkNode.last_val)  # Expected: 42
"
```
