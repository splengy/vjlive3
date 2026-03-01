# P4-COR030_AgentPersona.md

**Phase:** Phase 4 / P4-COR030  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR030 — AgentPersona

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `VJlive-2/core/extensions/agents/agent_persona.py`  
**Legacy Class:** `AgentPersona`, `PersonalityCard`, `MemoryDB`, `LearningModule`, `VLMController`

---

## What This Module Does

`AgentPersona` is the topmost wrapper for an individual AI performer's identity and memory in VJLive3. It aggregates four major subsystems into a single cohesive agent:
1. **`PersonalityCard`**: A JSON-serializable dataclass holding the agent's core identity, aesthetic (`"Dark Goth"`, `"Fluffy Puppy"`, etc.), provider configurations (Ollama endpoints), and static directives.
2. **`MemoryDB`**: A SQLite-backed RAG wrapper that records `MemoryEntry` events—snapshots of the UI state, the agent's action, and the resulting human `sentiment_score` feedback. It supports context-similarity retrieval.
3. **`LearningModule`**: An exponential moving average (EMA) value-learning system that biases the agent towards actions that previously yielded high feedback scores.
4. **`VLMController`**: The interface that captures screenshots (`mss`), grounds UI elements into coordinate space, prompts the Vision-Language Model with the `PersonalityCard`, and parses the resulting string back into a structural GUI action.

This module guarantees that an agent can be "Hot Swapped" during a live performance, carrying over its aesthetic preferences while adopting a new system prompt.

---

## What It Does NOT Do

- Does NOT execute the actions. It returns a `Dict[str, Any]` describing the action (`"action_type": "slider", "target": "Feedback", "value": 7.5`). The `AgentOrchestrator` actually executes the action on the timeline.
- Does NOT train the VLM fine-tuning weights. The `LearningModule` applies a post-generation numerical bias to the VLM's output.

---

## Public Interface

```python
import sqlite3
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from vjlive3.plugins.base import BasePlugin

@dataclass
class PersonalityCard:
    agent_id: str
    name: str
    aesthetic: str
    engine_config: Dict[str, Any]
    directives: Dict[str, str]
    memory_path: str
    learning_rate: float
    exploration_factor: float
    aesthetic_preferences: Dict[str, Any]
    learned_preferences: Dict[str, Any]
    
    @classmethod
    def from_file(cls, filepath: str) -> 'PersonalityCard': pass
    def to_dict(self) -> Dict[str, Any]: pass

class MemoryDB:
    def __init__(self, db_path: str) -> None: pass
    def store_memory(self, entry: Any, agent_id: str) -> int: pass
    def retrieve_by_sentiment(self, min_sentiment: float = 0.8, limit: int = 10) -> List[Any]: pass
    def retrieve_by_context(self, context: Dict[str, Any], radius: float = 0.2) -> List[Any]: pass

class LearningModule:
    def __init__(self, learning_rate: float = 0.1) -> None: pass
    def update_from_feedback(self, action: Dict[str, Any], feedback_score: float, context: Dict[str, Any]) -> None: pass
    def get_action_value(self, action: Dict[str, Any], context: Dict[str, Any]) -> float: pass

class VLMController:
    def __init__(self, engine_config: Dict[str, Any]) -> None: pass
    def perceive_ui(self) -> List[Dict[str, Any]]: pass
    def generate_action(self, current_state: Dict[str, Any], intent: str, personality: PersonalityCard) -> Dict[str, Any]: pass

class AgentPersona(BasePlugin):
    """
    Hot-swappable agent personality with memory-database connections.
    """
    
    METADATA = {
        "id": "AgentPersona",
        "type": "agent",
        "version": "1.0.0",
        "legacy_ref": "agent_persona"
    }

    def __init__(self, personality_card_path: str) -> None:
        """Initializes the Card, MemoryDB, VLM, and Learning configurations."""
        pass
        
    def hot_swap_personality(self, new_card_path: str) -> None:
        """Loads a new PersonalityCard while merging the existing learned preferences."""
        pass
        
    def perceive_and_act(self, intent: str, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates aesthetic bias, invokes VLMController for a generated action,
        and applies the numerical bias shift based on the LearningModule.
        """
        pass
        
    def provide_feedback(self, action: Dict[str, Any], feedback_score: float, context: Dict[str, Any]) -> None:
        """Pushes feedback into the MemoryDB and LearningModule."""
        pass
        
    def recall_precedent(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Queries MemoryDB for the highest sentiment action in a similar context."""
        pass
```

---

## Inputs and Outputs

### Bias Application
When the VLM returns a bounded slider action (0.0 to 10.0), `perceive_and_act` alters it using the `aesthetic_bias` formula before returning it:
```python
if bias > 0.7:  # High bias = more extreme values
    biased['value'] = min(10.0, original * (1.0 + (bias - 0.5)))
elif bias < 0.3:  # Low bias = softer values
    biased['value'] = max(0.0, original * (0.5 + bias * 0.5))
```

### Context Hashing
Context similarity and learning lookups rely on deterministic MD5 hashing of the context dictionary:
```python
context_str = json.dumps(context, sort_keys=True)
hash_str = hashlib.md5(context_str.encode()).hexdigest()[:16]
```

---

## Edge Cases and Error Handling

### Missing Personality Keys
`PersonalityCard._validate_card()` will immediately throw a `ValueError` if the JSON is missing `agent_id`, `name`, `aesthetic`, `engine_config`, `directives`, or `memory_path`.

### VLM Parsing Failures
`VLMController._validate_action()` guarantees that the generated payload dict has an `action_type` string of exactly `"click"`, `"drag"`, `"slider"`, or `"keypress"`. It throws `ValueError` otherwise, interrupting the LangGraph loop before execution.

---

## Dependencies

### External Libraries
- `numpy` (Standard arrays, screenshot representation)
- `sqlite3` (Built-in standard library, critical for `MemoryDB`)
- `hashlib` (Standard library, context hashing)
- `mss` (For the `ScreenshotCapturer`. **NOTE: VJLive3 standardizes on Headless CI testing, so `mss.mss()` must be gracefully mocked out in CI pipelines**).

### Internal Modules
- Depends on `BasePlugin` to merge perfectly with the existing plugin registry architecture.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_vlm_action_validation` | Passing a malformed JSON payload (lacking `action_type` or invalid type) correctly raises `ValueError`. |
| `test_hot_swap_preserves_memory` | Instantiating a persona, pushing a learned preference to memory, and calling `hot_swap_personality` proves the new card inherits the old dictionary mapping. |
| `test_bias_calculation` | Ensures that sending an original slider action of `5.0` via a card with `0.9` bias returns exactly `7.0` (clamped). |

**Minimum coverage:** 85% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] Ensure SQLite database is created robustly (using `.parent.mkdir(parents=True, exist_ok=True)`) safely.
- [ ] `mss` usage must not hard-crash the test runner on environments without physical displays (e.g., GitHub Actions). Provide falling-back mocks inside `perceive_ui`.
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR030: AgentPersona` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- Ensure `sqlite3.connect` always runs wrapped cleanly in a `contextlib.closing()` context block so database file handles are never stuck locking up the disk on thread death, mirroring the legacy file structure exactly.
