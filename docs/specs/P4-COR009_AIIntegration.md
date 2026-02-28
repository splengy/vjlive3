# P4-COR009: AIIntegration (collaboration_effects)

## Description

The `AIIntegration` module (formerly from `collaboration_effects.py` and `collaborative_canvas.py` in the `vjlive` codebase) serves as the centralized registry mapping specific generative AI brush algorithms (like `NebulaVortexBrush`) to collaborative networked inputs. 

## Public Interface Requirements

```python
from vjlive3.plugins.base import BaseNode
from typing import Dict, Any, Type

class AIIntegration(BaseNode):
    """
    Registry and factory for AI-driven collaborative brush rendering effects.
    """
    METADATA = {
        "id": "AIIntegration",
        "type": "ai_registry",
        "version": "1.0.0",
        "legacy_ref": "ai_integration (AIIntegration)"
    }

    def __init__(self):
        super().__init__()
        self.brush_models: Dict[str, Type] = {}
        
    def register_brush_model(self, name: str, model_class: Type) -> None:
        """Adds a new AI generative brush to the collaborative registry."""
        pass
        
    def spawn_brush(self, name: str, agent_id: str, **kwargs) -> Any:
        """Instantiates and returns an active AI brush."""
        pass
```

## Implementation Notes

- **Decoupling from Canvas:** The legacy version directly appended brushes to a `CollaborativeCreationSystem`. The VJLive3 port must return standard `RenderCommands` or instantiate `GeneratorNode` equivalents that the master node graph can consume.
- **Support for NebulaVortex:** It must port the specific `NebulaVortexBrush` parameters (rotation, intensity, color) as native uniforms.

## Test Plan

- **Pytest:** Register a dummy brush class. Call `spawn_brush('dummy', 'agent_alpha')`. Assert the returned instance exists and matches the registered type.
- Coverage must exceed 80%.
