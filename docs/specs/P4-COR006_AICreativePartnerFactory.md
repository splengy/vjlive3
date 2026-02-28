# P4-COR006_AICreativePartnerFactory.md

**Phase:** Phase 4 / P4-COR006  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR006 — AICreativePartnerFactory

**Priority:** P1 (High)  
**Status:** ⬜ Todo  
**Source:** `vjlive/core/ai_creativity/creative_partner.py`  
**Legacy Class:** `AICreativePartnerFactory`  

---

## What This Module Does

`AICreativePartnerFactory` is a lightweight instantiator pattern used to spawn instances of `AICreativePartner` with hardcoded, persona-driven heuristic overrides. By encapsulating these initialization presets ("Curious", "Focused", "Excited", "Mysterious"), the factory allows the live-coding environment or global state manager to quickly summon an AI collaborator whose base mood, suggestion frequency, and surprise probability are tailored to a specific artistic intention without requiring manual parameter tuning.

---

## What It Does NOT Do

- Does NOT maintain global state or act as a singleton manager itself (though the legacy file contains a separate `get_ai_creative_partner()` wrapper, the Factory strictly constructs fresh instances).
- Does NOT execute the actual ambient observation or generation logic (that remains the sole purview of `AICreativePartner`).
- Does NOT take ownership or memory-manage the returned `AICreativePartner` instances.

---

## Public Interface

```python
from typing import Any
from vjlive3.plugins.base import EffectNode

class AICreativePartnerFactory(EffectNode):
    """
    Factory class for instantiating AICreativePartner objects with
    pre-configured personality heuristics and baseline moods.
    """
    
    METADATA = {
        "id": "AICreativePartnerFactory",
        "type": "ai_factory",
        "version": "1.0.0",
        "legacy_ref": "creative_partner (AICreativePartnerFactory)"
    }
    
    @staticmethod
    def create_curious_partner(**kwargs: Any) -> Any:
        """Instantiates a partner with CURIOUS mood and high suggestion frequency (0.4)."""
        pass
        
    @staticmethod
    def create_focused_partner(**kwargs: Any) -> Any:
        """Instantiates a partner with FOCUSED mood and low suggestion frequency (0.2)."""
        pass
        
    @staticmethod
    def create_excited_partner(**kwargs: Any) -> Any:
        """Instantiates a partner with EXCITED mood and high surprise probability (0.05)."""
        pass
        
    @staticmethod
    def create_mysterious_partner(**kwargs: Any) -> Any:
        """
        Instantiates a partner with MYSTERIOUS mood, very low suggestion frequency (0.1),
        and moderate surprise probability (0.03).
        """
        pass
```

---

## Inputs and Outputs

### Parameters

No direct runtime parameters are maintained within the Factory itself. However, the static methods inject the following deterministic property mutations into the generated `AICreativePartner`:

| Method | `current_mood` Override | `suggestion_frequency` Override | `surprise_probability` Override |
|--------|-------------------------|--------------------------------|---------------------------------|
| `create_curious_partner` | `CreativeMood.CURIOUS` | `0.4` | *(Default 0.02)* |
| `create_focused_partner` | `CreativeMood.FOCUSED` | `0.2` | *(Default 0.02)* |
| `create_excited_partner` | `CreativeMood.EXCITED` | *(Default 0.3)* | `0.05` |
| `create_mysterious_partner` | `CreativeMood.MYSTERIOUS` | `0.1` | `0.03` |

### Inputs

- **kwargs**: `Dict[str, Any]` representing generic initialization bounds passed freely through the factory down into the `AICreativePartner` constructor (e.g., `audio_reactor`, `agent_bridge`, `canvas`).

### Outputs

- **AICreativePartner**: Returns a fully constructed, valid, memory-independent instance of the AI partner with properties mutated per the table above.

---

## Edge Cases and Error Handling

### Missing Dependencies
- The `**kwargs` propagation must explicitly pass through any missing or `None` values to the internal `AICreativePartner` constructor without raising `KeyError` or unpacking faults inside the Factory.

### Invalid Parameters
- N/A. Handled by the internal partner scope.

### State Corruption
- As a static toolkit, the `AICreativePartnerFactory` carries zero internal state. It is structurally immune to instance state corruption.

---

## Dependencies

### Internal Modules
- Intimately coupled to `vjlive3.core.ai_creativity.creative_partner.AICreativePartner` and `CreativeMood`.
- `vjlive3.plugins.base.EffectNode` — base class.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_create_curious_partner_mutations` | Verifies the returned instance has `current_mood == CURIOUS` and `suggestion_frequency == 0.4`. |
| `test_create_focused_partner_mutations` | Verifies the returned instance has `current_mood == FOCUSED` and `suggestion_frequency == 0.2`. |
| `test_create_excited_partner_mutations` | Verifies the returned instance has `current_mood == EXCITED` and `surprise_probability == 0.05`. |
| `test_create_mysterious_partner_mutations` | Verifies the returned instance has `current_mood == MYSTERIOUS`, `suggestion_frequency == 0.1`, `surprise_prob == 0.03`. |
| `test_kwargs_propagation_integrity` | Passing `canvas="MOCK_CANVAS"` accurately sets `instance.canvas == "MOCK_CANVAS"` during instantiation. |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code (no `pass` statements)
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR006: AICreativePartnerFactory` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- Strict usage of `@staticmethod` decorators is required to prevent accidental state accumulation.
- Ensure type hints are accurate, specifically unpacking `**kwargs` as `Any`.

### Porting Strategy
1. The logic is a direct 1:1 translation. Simply implement the 4 static constructors and exactly copy the heuristic overrides specified in the `Inputs and Outputs` matrix.
2. If `AICreativePartner` moves to a different directory standard in VJLive3, ensure the import path is fully updated.

### Risks
- Circular imports. If the Partner and Factory are split into separate files in the future, `Factory` requires `Partner`, but if `Partner` refers back to `Factory` for internal resets, the python interpreter will fault. In VJlive-2 they shared the same file; mirror this layout unless architecture explicitly dictates otherwise.
