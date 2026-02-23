# P4-COR023: AgentHydraExtension (unified_hydra_extensions)

## Description

The `AgentHydraExtension` (from `VJlive-2/core/unified_hydra_extensions.py`) serves as a bridge class connecting Python-side AI Agent context variables directly into the browser-based live-coding `Hydra` synthesizer. It provides dynamic GLSL uniforms (e.g., `agent_focus`, `agent_energy`) mimicking the agent's internal state.

## Public Interface Requirements

```python
from typing import Dict, Any

class AgentHydraExtension:
    """
    Bridge connecting Python Agent State to the JS/WebGL Hydra context pipeline.
    """
    METADATA = {
        "id": "AgentHydraExtension",
        "type": "hydra_bridge",
        "version": "1.0.0",
        "legacy_ref": "unified_hydra_extensions (AgentHydraExtension)"
    }

    def __init__(self, agent_manager=None):
        self.agent_manager = agent_manager
        
    def get_agent_uniforms(self) -> Dict[str, float]:
        """Serializes current agent metrics into a normalized float dictionary."""
        pass
```

## Implementation Notes

- **Modulation Interface:** The VJLive3 Engine supports dynamic parameter wrapping. Specifically, `get_agent_uniforms()` needs to map keys like `mood_confident` strictly to a normalized `[0.0, 1.0]` float space to avoid blowing out Hydra shader values.
- **Availability:** Ensure `is_available()` returns false if the underlying Agent lacks a loaded personality vector to prevent crashing the WebSocket broadcast.

## Test Plan

- **Pytest:** Mock an underlying Agent Manager returning an `energy` value of 0.8 and a `flow` value of 0.5. Calling `get_agent_uniforms()` must return `{"agent_energy": 0.8, "agent_intent_flow": 0.5}`.
- Coverage must exceed 80%.
