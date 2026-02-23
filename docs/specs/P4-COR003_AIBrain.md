# P4-COR003_AIBrain.md

**Phase:** Phase 4 / P4-COR003  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR003 — AIBrain

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `VJlive-2/core/automation_timeline.py`  
**Legacy Class:** `AIBrain`  

---

## What This Module Does

`AIBrain` is the core observational and generative intelligence unit explicitly used by the `QuantumTimeline` automation system. Its primary role is to sample the current visual state of the VJLive engine and generate structurally coherent, AI-directed parameter variations ("creativity bursts") to automatically generate new animation keyframes. It acts as the intelligent scaffolding for automated show progression, mimicking human VJ parameter sweeping by introducing controlled chaos and smooth transitions into the parameter space.

---

## What It Does NOT Do

- Does NOT handle scheduling or task execution threading (that is the `AIScheduler`).
- Does NOT execute generic LLM queries or chat logic.
- Does NOT trigger clips, scenes, or overarching show logic (it only generates parameter variations for timeline tracks).
- Does NOT directly mutate the live render canvas; it strictly returns parameter dictionaries to the Timeline Engine for interpolation.

---

## Public Interface

```python
from typing import Dict, Any, Optional
from vjlive3.plugins.base import EffectNode

class AIBrain(EffectNode):
    """
    Intelligent parameter variation unit for the Timeline automation system.
    Samples state and hallucinates parameter variations for keyframe generation.
    """
    
    METADATA = {
        "id": "AIBrain",
        "type": "ai_core",
        "version": "1.0.0",
        "legacy_ref": "automation_timeline (AIBrain)"
    }
    
    def __init__(self) -> None:
        """Initialize the AIBrain parameter generation bounds and connections."""
        super().__init__()
        self.params: Dict[str, float] = {}
        
    def get_current_visual_state(self, state_manager: Any) -> Dict[str, Any]:
        """
        Samples the global StateManager to extract current active parameters
        for the currently focused layer or the global mix.
        """
        pass
        
    def generate_variations(
        self, 
        current_params: Dict[str, Any], 
        creativity: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculates new target parameters bounded by the creativity scalar.
        Higher creativity allows wider deviations from current_params.
        """
        pass
```

---

## Inputs and Outputs

### Parameters

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `base_creativity` | `float` | Base creativity scalar for generation | 0.0 - 1.0 |
| `chaos_ceiling` | `float` | Hard cap on absolute parameter drift | 0.0 - 1.0 |

### Inputs

- **current_params**: `Dict[str, Any]` representing floats, ints, or nested dicts of effect parameters actively running on the canvas.
- **creativity**: `float` modifier dictating the "distance" of the variation.
- **stateManager**: Pointer to the global state engine to sample active nodes.

### Outputs

- **varied_params**: `Dict[str, Any]` containing numerically jittered or intelligently smoothed variants of the input parameters, keeping structural symmetry.

---

## Edge Cases and Error Handling

### Missing Dependencies
- Return a deep copy of `current_params` with zero mutation if the internal variation math library fails. Do not crash the timeline generator.
- Handle empty `current_params` dictionaries gracefully by returning an empty dict.

### Invalid Parameters
- Clamp `creativity` bounds strictly to 0.0 - 1.0; log warnings for out-of-bounds variations.
- Discard/ignore string or boolean paths inside `current_params` to avoid MathExceptions during variation calculations.

### Resource Limits
- Must operate instantaneously (`<2ms` per tick) to ensure keyframe loops inside `automation_timeline` do not stall the main thread if invoked synchronously.

---

## Dependencies

### Internal Modules
- `vjlive3.plugins.base.EffectNode` — base class
- `vjlive3.core.state_manager` — required to satisfy references to the global state (mocked in tests).

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_defaults` | Module initializes without fault. |
| `test_generate_variations_bounds` | Calling `generate_variations` with a `creativity` of `0.0` returns the exact input dictionary untouched. |
| `test_generate_variations_high_creativity` | Calling `generate_variations` with `creativity` of `1.0` returns heavily skewed numerical values. |
| `test_invalid_types_ignored` | Passing a dictionary with strings and bools alongside floats only mutates the floats, returning strings/bools unchanged. |
| `test_performance_millisecond` | Ensure `generate_variations` executes 1,000 times in under 500ms. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code (no `pass` statements, no `TODO` comments)
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR003: AIBrain` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- Adhere strictly to the `EffectNode` subclass methodology despite this being an AI core, to ensure parameter binding works correctly with VJLive3's uniform system.
- Include thorough type hinting on nested dictionaries to appease `mypy`.

### Porting Strategy
1. The legacy file is a stub (`VJlive-2/core/automation_timeline.py` lines ~24-30). Write a robust, mathematical concrete version that applies `np.random.normal()` based drift scaling to numeric keys in deeply nested dictionaries.
2. Implement static bounds checking so floats don't drift outside 0.0 to 1.0 boundaries common to `EffectNodes`.
3. Exclude keys that shouldn't be drifted (e.g., `"mix_mode"`, `"enabled"`).

---

## References

- **Legacy Source**: `VJlive-2/core/automation_timeline.py`
- **Safety Rails**: `WORKSPACE/SAFETY_RAILS.md`
- **Prime Directive**: `WORKSPACE/PRIME_DIRECTIVE.md`
