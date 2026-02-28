# P4-COR005_AICreativePartner.md

**Phase:** Phase 4 / P4-COR005  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR005 — AICreativePartner

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `vjlive/core/ai_creativity/creative_partner.py`  
**Legacy Class:** `AICreativePartner`  

---

## What This Module Does

`AICreativePartner` is an autonomous, ambient background observer designed to simulate a "Fifth Collaborator" in the VJLive engine. It continuously processes incoming audio analytics and active canvas metadata (strokes, brushes, layers) to dynamically calculate its own `CreativeMood` (e.g., Excited, Serene, Rebellious). Based on this mood and historical collaboration patterns, it emits structural `CreativeSuggestion` objects to the UI or actively triggers transient "Magic Moment" particle/color-shift effects to surprise the human operators. 

---

## What It Does NOT Do

- Does NOT directly schedule UI prompts or chat popups; it simply yields `CreativeSuggestion` objects to be consumed by the frontend.
- Does NOT override the agent permissions system or force permanent destructive visual changes to the canvas layer stack.
- Does NOT use external network ML requests (it relies on fast internal math heuristics based on stroke/audio frequency).

---

## Public Interface

```python
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import time
from vjlive3.plugins.base import EffectNode

class CreativeMood(Enum):
    """AI partner's creative mood states."""
    CURIOUS = "curious"
    FOCUSED = "focused"
    EXCITED = "excited"
    SERENE = "serene"
    REBELLIOUS = "rebellious"
    SYMPHONIC = "symphonic"
    MYSTERIOUS = "mysterious"

@dataclass
class CreativeSuggestion:
    """An AI-generated creative suggestion."""
    type: str  # e.g., 'brush_change', 'color_palette'
    data: Dict[str, Any]
    confidence: float
    reasoning: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class CollaborationPattern:
    """Pattern observed in human-agent collaboration."""
    pattern_type: str
    agents_involved: List[str]
    frequency: float
    last_seen: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class AICreativePartner(EffectNode):
    """
    The AI Creative Partner that actively collaborates on the canvas.
    Observes the collaborative creation process and makes intelligent
    contributions based on simulated mood states and heuristics.
    """
    
    METADATA = {
        "id": "AICreativePartner",
        "type": "ai_partner",
        "version": "1.0.0",
        "legacy_ref": "creative_partner (AICreativePartner)"
    }
    
    def __init__(
        self, 
        audio_reactor: Optional[Any] = None,
        agent_bridge: Optional[Any] = None,
        canvas: Optional[Any] = None,
        enable_suggestions: bool = True,
        suggestion_frequency: float = 0.3
    ) -> None:
        pass
        
    def update(self, dt: float, audio_data: Optional[Dict[str, float]] = None) -> None:
        """Main tick function. Updates mood, observes, and triggers events."""
        pass
        
    def make_direct_contribution(
        self, 
        contribution_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """Applies a direct artistic contribution to the canvas."""
        pass
        
    def get_suggestions(self, limit: int = 5) -> List[CreativeSuggestion]:
        """Returns the queue of recently generated suggestions."""
        pass
        
    def get_stats(self) -> Dict[str, Any]:
        """Returns internal metrics on contributions and learned patterns."""
        pass
```

---

## Inputs and Outputs

### Parameters

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `enable_suggestions` | `bool` | Master toggle targeting ambient popup rules | Boolean |
| `suggestion_frequency` | `float` | Base probability scalar for suggestion emission per tick | 0.0 - 1.0 |
| `mood_transition_speed` | `float` | Velocity clamp for mood state shifts | 0.0 - 1.0 (defaults to 0.1) |
| `suggestion_cooldown` | `float` | Minimum seconds between new suggestions | Seconds > 0 (defaults to 5.0) |
| `surprise_probability`| `float` | Random chance per tick to fire a magic moment | 0.0 - 1.0 (defaults to 0.02) |

### Inputs

- **dt**: `float` representing delta time since last frame in the `update()` loop.
- **audio_data**: `Dict` containing normalized bands `{'bass': float, 'mids': float, 'highs': float}`.
- **canvas**: External reference state queried internally for `layers` and `strokes`.

### Outputs

- Returns internal memory objects (e.g., via `get_suggestions`). `update()` performs side-effects implicitly on injected `canvas` references or internal stats mappings.

---

## Edge Cases and Error Handling

### Missing Dependencies
- The `update` method must quietly fail and immediately return if `self.canvas` or `self.enabled` is `None`/`False`.
- If `audio_data` is `None` during `_update_mood`, it must fallback to a generic `energy = 0.5` calculation directly without raising `KeyError` exceptions.

### Invalid Parameters
- Out-of-bounds metrics observed on the canvas must be clamped internally when calculating `recent_count` divided by `20.0` to ensure `get_canvas_activity_level()` remains strictly `0.0 - 1.0`.

### Resource Limits
- `pattern_history` is explicitly capped at `maxlen=1000` via a `collections.deque` to prevent Out-Of-Memory (OOM) memory leaks as the timeline runs indefinitely.

---

## Dependencies

### Internal Modules
- `vjlive3.plugins.base.EffectNode` — base class.
- Threading (`threading.RLock()`) is explicitly required around all canvas observation logic (`self._observe_collaboration`) and mood modification routines.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_state` | Mood defaults to `CreativeMood.CURIOUS`, `stats['suggestions_made']` is `0`. |
| `test_audio_energy_excited` | Injecting `bass: 1.0, mids: 1.0, highs: 1.0` triggers `CreativeMood.EXCITED` transition. |
| `test_audio_energy_serene` | Injecting `bass: 0.1, mids: 0.1, highs: 0.1` triggers `CreativeMood.SERENE` transition. |
| `test_suggestion_cooldown` | Confirming `_consider_suggestion()` does not fire twice under `5.0` seconds. |
| `test_missing_audio_fallback` | Passing `None` to `audio_data` during update does not crash and defaults energy calculation. |

**Minimum coverage:** 85% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code (no `pass` statements for core logic blocks)
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR005: AICreativePartner` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- Preserve the *exact* list of string outputs generated by the surprise mechanics (e.g., logging "✨ AI created a sparkle burst!"). This is critical "Agent Art" personality mapped to the original file.
- Use explicit Type Hinting on all Enums and Dataclasses, ensuring robust typing for `CreativeMood` and `CreativeSuggestion`.

### Porting Strategy
1. Carry over the `CreativeMood`, `CreativeSuggestion`, and `CollaborationPattern` definitions exactly as written in the legacy file.
2. The legacy `_trigger_surprise` uses `random.choice(surprise_types)`. Maintain this random index mapping logic block for block to enforce the identical behavioral constraints.
3. Thread locks are non-negotiable around `self.canvas.lock` contexts inside `_observe_collaboration`.

### Risks
- Thread deadlocks if `self.lock` and `self.canvas.lock` calls accidentally interleave asynchronously. Strict ordering and immediate yield patterns must be observed.
