# P4-COR022: AgentGraphVisualizer (agent_graph_visualizer)

## Description

The `AgentGraphVisualizer` (from `VJlive-2/core/extensions/agents/agent_graph_visualizer.py`) is an interactive 3D visual effect that displays active remote agents (or internal AI subsystems) as nodes, bridging them with connection edges to represent collaborative data flow. It supports both clustered force-directed layouts and grid layouts.

## Public Interface Requirements

```python
from vjlive3.plugins.base import EffectNode
from typing import Dict, Any

class AgentGraphVisualizer(EffectNode):
    """
    3D force-directed layout rendering nodes representing the Agent mesh grid.
    """
    METADATA = {
        "id": "AgentGraphVisualizer",
        "type": "visualizer",
        "version": "1.0.0",
        "legacy_ref": "agent_graph_visualizer (AgentGraphVisualizer)"
    }

    def __init__(self):
        super().__init__()
        self.layout_type = 0  # 0: force-directed, 1: grid
        self._graph_data = {}
        
    def set_graph_data(self, graph_data: Dict[str, Any]) -> None:
        """Loads a dict of node_ids and connection weights to display."""
        pass
        
    def _force_directed_layout(self) -> None:
        """Calculates repulsive/attractive bounds for the internal points."""
        pass
```

## Implementation Notes

- **OpenGL Efficiency:** The legacy code iteratively executed CPU-based distance vector math over all nodes 60 times a second using nested loops. In VJLive3, the matrix calculation must be migrated entirely to a Compute Shader (or strictly mapped to a NumPy routine) to prevent an O(N^2) CPU bottleneck.
- **Node Size:** Node colors and visual sizes should pulse responsively by sampling the `AudioBus`.

## Test Plan

- **Pytest:** Call `set_graph_data` containing 3 densely connected nodes and 1 isolated node. Run `_force_directed_layout` for 10 ticks. Assert the distance between the 3 connected nodes is significantly smaller than their distance to the isolated node.
- Coverage must exceed 80%.
