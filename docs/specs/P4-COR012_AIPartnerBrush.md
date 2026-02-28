# P4-COR012: AIPartnerBrush (brush_engines)

## Description

`AIPartnerBrush` (originating from `vjlive/core/ai_creativity/brush_engines.py`) is an adaptive `GeneratorNode` subclass that acts as a collaborative rendering brush. Instead of retaining static parameters, it maintains a history of `observed_styles` from other agents (users or AIs) and merges their attributes (size, speed, color) into its own generative sequences.

## Public Interface Requirements

```python
from vjlive3.plugins.base import GeneratorNode
from typing import Dict

class AIPartnerBrush(GeneratorNode):
    """
    Adaptive brush generator that evolves its rendering traits by observing collaborators.
    """
    METADATA = {
        "id": "AIPartnerBrush",
        "type": "generator",
        "version": "1.0.0",
        "legacy_ref": "brush_engines (AIPartnerBrush)"
    }

    def __init__(self):
        super().__init__()
        self.observed_styles = []
        self.adaptation_threshold = 0.6
        
    def observe_style(self, agent_id: str, style_data: dict) -> None:
        """Records another agent's active parameters to influence future generation."""
        pass
```

## Implementation Notes

- **Generative Overhaul:** The legacy `render()` method outputted raw `AdaptiveBrushStroke` dictionaries. In VJLive3, this node is an engine `GeneratorNode` that outputs visual textures/data directly into the `FramebufferManager`. The mutation logic (e.g., swapping preferred color palettes) should happen during the generic `process()` tick instead.
- **Data Pruning:** The internal `observed_styles` array must be a fixed size `collections.deque(maxlen=10)` to prevent unbounded memory growth over an extended performance.

## Test Plan

- **Pytest:** Call `observe_style` with a `{ "color": [1.0, 0.0, 0.0, 1.0] }` payload. Assert that the internal brush output state drifts toward red over subsequent `process()` ticks.
- Coverage must exceed 80%.
