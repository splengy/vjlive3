# P4-COR017: AISuggestionEngine (ai_suggestion_engine)

## Description

The `AISuggestionEngine` is the active heuristic analysis class that scans the current layout of the active `QuantumTimeline`. It identifies gaps, calculates parameter correlations, and detects oscillation patterns to propose `AISuggestions` (e.g., "Add keyframe here to complete this LFO curve").

## Public Interface Requirements

```python
from vjlive3.plugins.base import BaseNode
from typing import List, Dict, Any

class AISuggestionEngine(BaseNode):
    """
    Analyzes historical timeline data to predict and suggest optimal parameter mutations.
    """
    METADATA = {
        "id": "AISuggestionEngine",
        "type": "ai_analytics",
        "version": "1.0.0",
        "legacy_ref": "ai_suggestion_engine (AISuggestionEngine)"
    }

    def __init__(self, bpm: float = 120.0):
        super().__init__()
        self.bpm = bpm
        self.suggestion_cooldown = 2.0
        
    def generate_suggestions(self, current_time: float, context: dict = None) -> List[Any]:
        """Scans the VJLive3 StateManager histories to output AISuggestion payloads."""
        pass
        
    def _analyze_timeline_state(self) -> Dict[str, Any]:
        """Internal heuristic evaluator looking for temporal gaps > 4 beats."""
        pass
```

## Implementation Notes

- **Decoupling from Legacy Timeline:** The legacy class hard-referenced `quantum_timeline.parameters`. In VJLive3, the engine must inject a reference to the active `StateManager` and poll its history buffers directly.
- **Performance:** This is an expensive loop (calculating cross-parameter correlations matrix-style). It must **never** run on the main OpenGL thread. It must be locked to the dedicated `AgentManager` async threadpool.

## Test Plan

- **Pytest:** Populate a mock StateManager with a parameter (e.g., `deck.a.mix`) that jumps from `0.0` at `t=0` to `1.0` at `t=2` with no keyframes in between. Call `generate_suggestions()`. Assert the engine returns an `AISuggestion` to fill the gap via linear interpolation at `t=1`.
- Coverage must exceed 80%.
