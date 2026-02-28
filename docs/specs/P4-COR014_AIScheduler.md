# P4-COR014: AIScheduler (brain)

## Description

`AIScheduler` (originating from `VJlive-2/core/ai/brain.py` as `the_brain`) is a singleton execution queue intended to route asynchronous AI tasks (like Voice Recognition intents from `VoiceBridge` or background generation requests to `CreativeHive`). 

## Public Interface Requirements

```python
from vjlive3.plugins.base import BaseNode
from typing import Dict, Any

class AIScheduler(BaseNode):
    """
    Singleton AI task routing and async execution manager.
    """
    METADATA = {
        "id": "AIScheduler",
        "type": "ai_core",
        "version": "1.0.0",
        "legacy_ref": "brain (AIScheduler)"
    }

    def __init__(self):
        super().__init__()
        self.is_running = False
        
    def start(self) -> None:
        """Initializes the background AI threadpool."""
        pass
        
    def process_request(self, request_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Routes a synchronous request to the appropriate AI subsystem."""
        pass
```

## Implementation Notes

- **Phase 1 Architecture Compliance:** VJLive3 strictly forbids monolithic singletons outside of the core `Engine`. The `AIScheduler` MUST be implemented as an isolated `Agent` running on the `AgentManager` threadpool loop. It cannot be instantiated via a global `the_brain = AIScheduler()` variable.
- **Message Passing:** Voice commands should be transmitted to the `Engine.state` dict, not hard-bound via callbacks.

## Test Plan

- **Pytest:** Instantiate an `AIScheduler` instance. Call `process_request('generate_suggestions', {})`. Assert it returns a dictionary payload conforming to the `{ "suggestions": [...] }` schema.
- Coverage must exceed 80%.
