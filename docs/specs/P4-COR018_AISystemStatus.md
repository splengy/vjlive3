# P4-COR018: AISystemStatus (ai_integration)

## Description

The `AISystemStatus` (and its parent `AIIntegration` wrapper) in the legacy `VJlive-2/core/ai_integration.py` file functioned as the global health monitor and lifecycle supervisor for the 21 unique AI sub-modules. It reports on whether specific background systems (like the Predictor, Sandbox, or Narrator) are active, their current error rates, and CPU health.

## Public Interface Requirements

```python
from vjlive3.plugins.base import BaseNode
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class AISystemStatusPayload:
    """Read-only health metrics for a specific AI subsystem."""
    name: str
    available: bool
    initialized: bool
    health: float
    error_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

class AIIntegration(BaseNode):
    """
    Subsystem lifecycle manager and health aggregator.
    """
    METADATA = {
        "id": "AIIntegration_Manager",
        "type": "ai_registry",
        "version": "1.0.0",
        "legacy_ref": "ai_integration (AISystemStatus/AIIntegration)"
    }

    def __init__(self):
        super().__init__()
        self._status_registry: Dict[str, AISystemStatusPayload] = {}
        
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Returns an aggregated snapshot of all Agent thread healths."""
        pass
        
    def register_subsystem(self, name: str, available: bool = True) -> None:
        """Called by children (like AIBrain) during AgentManager initialization."""
        pass
```

## Implementation Notes

- **Collision with P4-COR009:** Note that the user's `BOARD.md` mapped `P4-COR009` to `AIIntegration` (referencing `collaboration_effects`), but `P4-COR018` is mapped to `ai_integration (AISystemStatus)`. To avoid naming collisions in the final Plugin registry, `P4-COR018` will expose its primary class as `AIIntegration_Manager` while mapping internally to the global health aggregator.
- **Async Polling:** The system status generation must not block. It should routinely output a dictionary to the `StateManager` (e.g., `state['ai.health']`) every 60 frames.

## Test Plan

- **Pytest:** Call `register_subsystem('AIScheduler', True)`. Assert that `get_comprehensive_status()` returns a payload containing `overall_health: 1.0` and the registered subsystem.
- Coverage must exceed 80%.
