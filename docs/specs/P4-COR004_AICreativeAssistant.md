# P4-COR004_AICreativeAssistant.md

**Phase:** Phase 4 / P4-COR004  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR004 — AICreativeAssistant

**Priority:** P1 (High)  
**Status:** ⬜ Todo  
**Source:** `vjlive/core/debug/co_creation_enhanced.py`  
**Legacy Class:** `AICreativeAssistant`  

---

## What This Module Does

`AICreativeAssistant` is a multi-modal suggestion and generation engine for the Collaborative Canvas and Live Coding environment. It acts as an ambient intelligent observer that analyzes canvas composition, calculates stylistic gaps, and generates actionable creative recommendations (such as color palettes, structural simplification suggestions, and geometry patterns). It also houses the logic for emulating specific persona art styles (e.g., Trinity's ethereal particles, Cipher's glitch) by augmenting incoming brush strokes before they commit to the canvas.

---

## What It Does NOT Do

- Does NOT directly render pixels to the screen (it depends on the canvas or agents to consume its output).
- Does NOT connect to a real remote LLM/ML API (currently uses heuristic fallbacks and preset maps).
- Does NOT override agent autonomy, it only provides `suggestions` or modifies `target_strokes` actively passed to it.

---

## Public Interface

```python
from typing import Dict, Any, List, Tuple, Optional
from vjlive3.plugins.base import BasePlugin
# Note: Canvas and BrushStroke types are defined in the Co-Creation module

class AICreativeAssistant(BasePlugin):
    """
    AI-powered creative assistant that provides generative enhancements,
    style emulation, and compositional analysis.
    """
    
    METADATA = {
        "id": "AICreativeAssistant",
        "type": "ai_assistant",
        "version": "1.0.0",
        "legacy_ref": "co_creation_enhanced (AICreativeAssistant)"
    }
    
    def __init__(self, enabled: bool = True) -> None:
        """Initialize the assistant's style presets and heuristics."""
        pass
        
    def _load_model(self) -> None:
        """Mock method simulating the asynchronous loading of ML weights/heuristics."""
        pass
        
    def analyze_composition(self, canvas: Any) -> Dict[str, Any]:
        """Calculates complexity scores and returns optimization suggestions."""
        pass
        
    def suggest_color_palette(
        self, 
        canvas: Any, 
        reference_style: Optional[str] = None
    ) -> List[Tuple[float, float, float]]:
        """Extracts dominant colors from the canvas or returns a preset palette."""
        pass
        
    def apply_style_transfer(self, canvas: Any, style_name: str) -> bool:
        """Mutates existing strokes on the canvas to adopt a named style."""
        pass
        
    def generate_beat_synchronized_pattern(
        self, 
        audio_levels: Dict[str, float],
        agent_id: str
    ) -> List[Dict[str, float]]:
        """Procedurally shapes geometry coordinates linked to audio transients."""
        pass
        
    def emulate_agent_style(
        self, 
        agent_id: str, 
        canvas: Any,
        target_strokes: List[Any]
    ) -> List[Any]:
        """Reconstructs raw points into a specific agent's signature visual style."""
        pass
        
    def get_creative_suggestions(
        self, 
        canvas: Any,
        audio_levels: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """Aggregates composition analysis, audio state, and stroke depth into human-readable hints."""
        pass
        
    def enable(self) -> None:
        """Toggles the assistant active and attempts a model load."""
        pass
```

---

## Inputs and Outputs

### Constants

The following static styles must be preserved exactingly:
- `trinity_ethereal`: particle brush, cyan palette `[(0.0, 0.8, 1.0), (0.5, 0.9, 1.0), (1.0, 1.0, 1.0)]`
- `cipher_glitch`: glow brush, amber palette `[(0.8, 0.4, 0.0), (1.0, 0.6, 0.0), (0.5, 0.2, 0.0)]`
- `antigravity_precise`: vortex brush, green palette `[(0.2, 1.0, 0.2), (0.0, 0.8, 0.0), (1.0, 1.0, 1.0)]`
- `human_organic`: line brush, red palette `[(1.0, 0.2, 0.2), (0.8, 0.0, 0.0), (1.0, 0.5, 0.5)]`

### Parameters

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `analyze_composition` | `canvas` | `Dict[str, Any]` | Dictionary containing boolean `enabled`, float `complexity_score`, float `color_diversity`, and a list of `suggestions`. |
| `suggest_color_palette` | `canvas`, `reference_style` (str) | `List[Tuple[float, float, float]]` | Returns 3-5 RGB tuples scaled 0.0 to 1.0. |
| `generate_beat_synchronized_pattern` | `audio_levels` (Dict), `agent_id` (str) | `List[Dict]` | Returns lists of `{x, y}` point dictionaries tracing radial geometry based on bass/mid/treble. |

---

## Edge Cases and Error Handling

### Missing Dependencies
- The ML model is mocked. `_load_model` sets `model_loaded = True` but must catch simulated exceptions and gracefully set `self.enabled = False` without crashing the main thread.
- If `style_name` passed to `apply_style_transfer` doesn't exist, it should return `False` and do nothing.

### Invalid Parameters
- If `audio_levels` is completely absent or empty during pattern generation, assume `0.0` for bass/mid/treble to prevent math errors. Do NOT raise an exception.
- If the canvas is empty, `suggest_color_palette` must gracefully return a default fallback palette as defined in the legacy logic.

### State Corruption
- `emulate_agent_style` modifies the properties of `target_strokes`. It must copy or construct new `BrushStroke` objects to avoid mutation side-effects breaking the undostack of the Collaborative Canvas.

---

## Dependencies

### External Libraries
- `math` (standard library) for sine/degree calculations in pattern generation.
- `time` (standard library) for mocked model load delays.

### Internal Modules
- Depends on typing definitions for `CollaborativeCanvas`, `BrushStroke`, and `BrushType` from the co-creation system. (Use `Any` for typing bounds in the interface if circular imports become an issue, but strictly duck-type the required properties like `canvas.get_stats()`).

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_initialization_state` | Verifies `model_loaded` begins false and `enabled` defaults to True. |
| `test_analyze_empty_composition` | Analyzing a mock canvas with 0 strokes returns an "add detail" suggestion. |
| `test_analyze_complex_composition` | Analyzing a mock canvas with 2,000 strokes returns a "simplify" suggestion. |
| `test_suggest_color_palette_fallback` | Passing an empty canvas returns the 4-color default fallback palette. |
| `test_suggest_color_palette_preset` | Passing `reference_style="cipher_glitch"` strictly returns the amber palette tuples exactly. |
| `test_beat_pattern_generation` | Passing high bass float returns a larger number of radial geometry points than low bass float. |
| `test_agent_style_emulation` | Emulating "trinity" directly modifies the `metadata['style_emulated']` and brush properties of the returned stroke copies. |

**Minimum coverage:** 85% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code (no `pass` statements)
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR004: AICreativeAssistant` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released

---

## Implementation Notes

### Quality Standards
- The original code included `.lower()` checks for `agent_id` matching in style emulation. Ensure this case-insensitivity persists.
- The `generate_beat_synchronized_pattern` function directly uses hardcoded trigonometric radius formulas linked to audio bands. Transcribe these exactly as they are the mathematical "flavor" of the agent drawing styles.

### Legacy References
- Original path: `/home/happy/Desktop/claude projects/vjlive/core/debug/co_creation_enhanced.py` lines 547-850.

### Risks
- `apply_style_transfer` touches deeply nested canvas structure limits (`canvas.layers -> layer.strokes`). Ensure the port matches the `CollaborativeCanvas` API exposed in VJLive3 once that dependency is built.
