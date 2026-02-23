# P4-COR007_AICurator.md

**Phase:** Phase 4 / P4-COR007  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR007 — AICurator

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `vjlive/core/debug/co_creation_enhanced.py`  
**Legacy Class:** `AICurator`  

---

## What This Module Does

`AICurator` acts as a programmatic art critic for the Collaborative Canvas. Rather than modifying strokes or actively suggesting parameter changes mid-performance, the Curator is explicitly designed to evaluate static artwork snapshots. It calculates a heuristic `quality_score` based on compositional complexity (stroke count, layer count, distinct agents involved). Using these thresholds, it generates a human-readable critique rating (`excellent`, `good`, `fair`, `needs_work`), string feedback, and auto-generates stylized social media captions. In legacy, it also acted as the sorting mechanism for auto-curating the gallery.

---

## What It Does NOT Do

- Does NOT generate or draw visual elements on the canvas rendering loop.
- Does NOT perform actual deep-learning aesthetic scoring (it uses deterministic heuristics based strictly on stroke density and collaboration counts).
- Does NOT connect to external social media APIs (it just outputs formatted caption strings).

---

## Public Interface

```python
from typing import Dict, List, Any, Optional
from vjlive3.plugins.base import BasePlugin
import time

class AICurator(BasePlugin):
    """
    AI that analyzes collaborative artworks and provides aesthetic 
    feedback, scoring, and auto-generated captions based on composition metadata.
    """
    
    METADATA = {
        "id": "AICurator",
        "type": "ai_critic",
        "version": "1.0.0",
        "legacy_ref": "co_creation_enhanced (AICurator)"
    }
    
    def __init__(self) -> None:
        """Initializes aesthetic threshold mappings."""
        pass
        
    def critique_artwork(
        self, 
        canvas: Any, 
        artwork_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate the canvas against heuristic thresholds and return a structured critique.
        """
        pass
        
    def generate_caption(
        self, 
        canvas: Any, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Synthesize string hashtags and metadata variables into a social media post format.
        """
        pass
        
    def auto_curate_gallery(self, artworks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts a list of gallery artwork dictionaries by their internal creation dates.
        """
        pass
        
    def get_stats(self) -> Dict[str, Any]:
        """Returns session counts of generated critiques."""
        pass
```

---

## Inputs and Outputs

### Constants

Strict aesthetic heuristic mappings initialized in constructor:
- `excellent`: `>= 0.8` baseline score
- `good`: `>= 0.6` baseline score
- `fair`: `>= 0.4` baseline score
- `needs_work`: `< 0.4` baseline score

### Inputs

- **canvas**: External state object evaluated by calling `.get_stats()`. Expected to yield `total_strokes`, `unique_contributors`, and `total_layers` integer counts.

### Outputs

#### `critique_artwork()` Return Dictionary
| Key | Type | Description |
|-----|------|-------------|
| `quality_score` | `float` | Heuristic sum capped strictly at `1.0`. |
| `rating` | `str` | `"excellent" \| "good" \| "fair" \| "needs_work"` |
| `stroke_count` | `int` | Passthrough from canvas. |
| `contributor_count` | `int` | Passthrough from canvas. |
| `layer_count` | `int` | Passthrough from canvas. |
| `feedback` | `List[str]` | Human readable evaluations (e.g. "Solo creation. Invite others!") |
| `suggestions` | `List[Dict]` | Actionable prompts mapped to feedback strings. |
| `timestamp` | `float` | `time.time()` execution mark. |

---

## Edge Cases and Error Handling

### Missing Dependencies
- If `canvas.get_stats()` returns empty or `None` values for counts, fallback defaults must apply silently: `stroke_count=0`, `unique_contributors=1`, `layer_count=1`.

### Invalid Parameters
- `quality_score` additions mathematically risk exceeding `1.0` if a massive canvas with `>500 strokes` (`+0.6`), multiple layers (`+0.1`) and multiple contributors (`+0.2`) evaluates to `0.9`. The logic explicitly requires scaling and strictly clamping `min(1.0, quality_score)`.
- If `auto_curate_gallery` evaluates an artwork dict without a `'created'` Unix timestamp key, it must silently assume `0` as the fallback during reverse sorting so it doesn't crash the lambda function.

### Resource Limits
- Must operate rapidly on the Main Thread without async offloading as it relies strictly on cheap numeric dictionary access rather than pixel convolution.

---

## Dependencies

### External Libraries
- `time` (standard library) for critique timestamps and `random` (standard library) for caption template selection.

### Internal Modules
- Depends on `vjlive3.plugins.base.BasePlugin` core architecture. Note: It does NOT require `EffectNode` as it does not participate directly in the WebGL NodeGraph rendering path.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_critique_needs_work` | Canvas with `< 20` strokes and `1` layer yields `< 0.4` score and `needs_work` tier. |
| `test_critique_excellent_caps` | Canvas with `> 500 strokes`, `3` layers, `2` agents evaluates to exactly `1.0` (not `1.1`) and returns `excellent` rating. |
| `test_caption_template_binding` | Ensures injected format strings (`{agents}`, `{brush_count}`) populate correctly without triggering python `KeyError` matching errors. |
| `test_auto_curate_gallery_sort` | List of mock artwork dicts with scrambled `created` Unix timestamps are returned completely sorted from newest to oldest. |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code (no `pass` statements)
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR007: AICurator` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- Preserve the 4 distinct string templates exactly inside `generate_caption` as they establish the "canon" flavor text of the system.
- Ensure the extraction loop inside `generate_caption` properly de-duplicates agent names and brush types globally across the canvas iteration.

### Risks
- `generate_caption` assumes exact schema of `stroke.agent_id` and `stroke.brush_type`. Strong type duck-typing is required around the mock `CollaborativeCanvas` objects in unit tests to prevent CI failures.
