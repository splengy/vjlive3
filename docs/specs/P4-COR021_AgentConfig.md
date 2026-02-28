# P4-COR021: AgentConfig (config_manager)

## Description

`AgentConfig` (from `VJlive-2/core/config_types.py`) is a dataclass representing the structural configuration variables for the active AI Agent, including its personality trait (Minimalist, Raver, Ghost), adrenaline thresholds, and self-healing sensitivity.

## Public Interface Requirements

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any

class Personality(Enum):
    MINIMALIST = "minimalist"
    RAVER = "raver"
    GHOST = "ghost"

@dataclass
class AgentConfig:
    """
    Configuration parameters defining agent behavior boundaries.
    """
    active_personality: Personality = Personality.RAVER
    adrenaline_threshold: float = 0.85
    self_healing: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "sensitivity": 0.05
    })
    
    # Optional Hardware integrations (defaults to False)
    shadow_mode_enabled: bool = False
    eye_tracking_enabled: bool = False
```

## Implementation Notes

- **Migration to OmegaConf:** VJLive3 heavily leverages `OmegaConf` for YAML parsing. The `AgentConfig` class should be fully compatible with `OmegaConf.structured(AgentConfig)`.
- **Hot-Reloading:** Ensure that changing the `active_personality` at runtime fires an event on the EventBus so the underlying `AgentManager` can reset its context window immediately.

## Test Plan

- **Pytest:** Instantiate `AgentConfig` natively. Assert `active_personality` defaults to `Personality.RAVER`.
- Coverage must exceed 80%.
