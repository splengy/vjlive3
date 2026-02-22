---
description: Artisanal snowflake migration - how to port a single plugin or effect node from legacy to VJLive3
---

# Bespoke Plugin Migration Workflow

Each plugin/effect is handled as a unique work of art. No batch processing. No copy-paste.

## Prerequisites

- Read `WORKSPACE/PRIME_DIRECTIVE.md` Rule 4 (Bespoke Snowflakes)
- Pull the next assignment via the `request_work` MCP tool to confirm this spec is assigned to you.
- Query `vjlive-brain` MCP: `search_concepts(name="EffectName")` — is it already indexed?

## The Six-Step Migration Protocol

### Step 1: Extraction — Identify the Soul

Open the legacy file (v1 or v2). Read it in full. Ask:
- What does this effect actually do? (the visual output)
- What are its parameters and valid ranges?
- Does it have audio reactivity? How?
- Is there any [DREAMER_LOGIC] in here? (unusual, clever, or "impossible" code)
- What are its external dependencies? (OpenGL, numpy, custom modules)
- Are there known bugs? (scan commits, comments, and log files for clues)

Document your findings as inline notes — do NOT start coding yet.

### Step 2: Dreamer Review — Analyze Before Dismissing

If you found unusual code:
1. Log it in `WORKSPACE/KNOWLEDGE/DREAMER_LOG.md` with status `[DREAMER_LOGIC]`
2. Ask: is there a valid mathematical or computational basis for this?
3. If yes: tag `[DREAMER_GENIUS]` and plan to port the elegant version
4. If no: tag `[DREAMER_DEAD_END]` and document why
5. NEVER silently discard unusual code

### Step 3: Spec Writing — Document First

Create or update the spec doc at `docs/effects/<effect_name>.md`:
```markdown
# EffectName
**Source:** vjlive-v2:effects/effect_name/__init__.py
**Category:** generator | processor | transition | overlay
**Complexity:** low | medium | high

## Visual Description
What the viewer sees.

## Parameters
| Name | Type | Range | Default | Description |
...

## Audio Reactivity
How the effect responds to audio input (FFT, beat, amplitude).

## Known Legacy Bugs
Bugs identified in source — do NOT port.

## METADATA Constant
Full METADATA dict for the new class.
```

### Step 4: Artisanal Coding — Implement to Spec

1. Verify you exclusively own this task via your active switchboard task.
2. Create `src/vjlive3/effects/<category>/<effect_name>.py`
3. Implement the class with full `METADATA` constant (Rule 2)
4. Port the visual logic — validate against source, do NOT copy bugs
5. Use `Logger.termination()` for any known dead-end paths (Rule 6)
6. Keep file under 750 lines (Rule 5) — split if needed

**Effect class template:**
```python
"""<EffectName> — <One sentence description>."""
from __future__ import annotations
import logging
from vjlive3.core.base_effect import BaseEffect

class <EffectName>(BaseEffect):
    METADATA: dict = {
        "name": "<Creative Name>",
        "description": "<2-3 evocative sentences>",
        "version": "1.0.0",
        "api_version": "3.0",
        "origin": "vjlive-v2:effects/<path>",
        "dreamer_flag": False,
        "logic_purity": "clean",
        "role_assignment": "worker",
        "kitten_status": True,
        "parameters": { ... },
        "tags": [...],
        "category": "...",
        "performance_impact": "low|medium|high",
    }
    
    def __init__(self) -> None:
        super().__init__()
        self._log = logging.getLogger(f"vjlive3.effects.{self.__class__.__name__}")
    
    def process(self, frame: np.ndarray, audio_data: dict) -> np.ndarray:
        """Apply effect to frame."""
        ...
```

### Step 5: Validation — Test Before Moving On

```bash
# Run the effect's unit tests
pytest tests/effects/test_<effect_name>.py -v

# Check stub policy
python scripts/check_stubs.py src/vjlive3/effects/<category>/<effect_name>.py

# Check file size
python scripts/check_file_size.py src/vjlive3/effects/<category>/<effect_name>.py

# Full quality gate
make quality
```

All tests must pass. Coverage must be ≥80% for this file.

### Step 6: The Kitten Check — Visual Verification

Load the effect in the Phase 0 status window:
1. Does it render without errors?
2. Does it look like the legacy version?
3. Does FPS remain ≥58 with this effect active?
4. Does audio reactivity work?

If yes on all: check in the file, update BOARD.md, commit.

## Commit Message Format

```
[Plugin] feat: port <EffectName> from vjlive-v2
- Full METADATA constant
- Audio reactivity: <yes/no + method>
- Dreamer analysis: <none|genius|dead_end>
- Coverage: <X>%
```
