# P4-COR036_AgentRhythmProfile.md

**Phase:** Phase 4 / P4-COR036  
**Assigned To:** Implementation Engineer  
**Spec Written By:** Manager (Antigravity)  
**Date:** 2026-02-23  

---

## Task: P4-COR036 — AgentRhythmProfile

**Priority:** P0 (Critical)  
**Status:** ⬜ Todo  
**Source:** `VJlive-2/core/extensions/consciousness/rhythm_consciousness.py`  
**Legacy Class:** `AgentRhythmProfile`, `RhythmPersonality`, `BeatTimeline`, `RhythmConsciousness`

---

## What This Module Does

`AgentRhythmProfile` defines the musical identity and synchronous behavior for an AI agent. In combination with the `RhythmConsciousness` system, it transforms VJLive3 from a reactive system into a predictive, timeline-aware generative engine. 

The module defines a series of `RhythmPersonality` enums (`STEADY`, `SWING`, `POLYRHYTHMIC`, etc.), which dictate an agent's `accent_pattern`. The core `BeatTimeline` buffers incoming audio analysis frames, predicts upcoming beats up to 4.0 seconds into the future (using `np.mean` intervals and normal distribution noise), and handles agent-to-agent synchronization mapping (`call_and_response`, `sync`, `challenge`). 

The overarching `RhythmConsciousness` class serves as the manager, processing `AudioAnalyzer` events into `BeatEvent` structs, generating complementary MIDI-style beat arrays (`kick_pattern`, `hihat_pattern`), and bridging these synthetic events directly to the `AgentVisualizer` for particle bursts and ripples.

---

## What It Does NOT Do

- Does NOT do raw audio FFT processing (that is strictly `core.audio_analyzer`).
- Does NOT act as an OSC sequencer output. It strictly drives internal particle emitters and agent intents.

---

## Public Interface

```python
import threading
import numpy as np
import math
from typing import Dict, List, Optional, Tuple, Callable, Any
from collections import deque
from enum import Enum
from dataclasses import dataclass, field
from vjlive3.plugins.base import BasePlugin

class RhythmPersonality(Enum):
    STEADY = "steady"
    SWING = "swing"
    SYNCOPATED = "syncopated"
    POLYRHYTHMIC = "polyrhythmic"
    GROOVE = "groove"
    BREAKBEAT = "breakbeat"
    AMBIENT = "ambient"
    TECHNO = "techno"

@dataclass
class BeatEvent:
    beat_number: int
    timestamp: float
    confidence: float
    strength: float
    type: str  # 'kick', 'snare', 'hihat', 'predicted'
    agent_id: Optional[str] = None

@dataclass
class AgentRhythmProfile:
    """The static rhythm configuration for a single agent."""
    agent_id: str
    personality: RhythmPersonality = RhythmPersonality.STEADY
    base_bpm: float = 120.0
    groove_swing: float = 0.0
    syncopation_level: float = 0.0
    polyrhythm_layers: int = 1
    accent_pattern: List[float] = field(default_factory=list)

    def __post_init__(self) -> None: pass

class BeatTimeline:
    """Predictive engine forecasting the next 4 seconds of musical events."""
    def __init__(self, bpm: float = 120.0) -> None: pass
    def update_bpm(self, bpm: float, smooth: bool = True) -> None: pass
    def add_beat(self, beat_event: BeatEvent) -> None: pass
    def get_current_beat(self, current_time: Optional[float] = None) -> Tuple[int, float]: pass
    def get_predicted_beats(self, look_ahead: float = 2.0) -> List[BeatEvent]: pass
    def synchronize_agent(self, agent_id: str, target_bpm: Optional[float] = None) -> None: pass

class RhythmGenerator:
    """Procedurally generates 8-step velocity arrays tailored to agent personalities."""
    def generate_pattern(self, personality: RhythmPersonality, base_bpm: float = 120.0) -> Dict[str, Any]: pass
    def mutate_pattern(self, pattern: Dict[str, Any], mutation_rate: float = 0.1) -> Dict[str, Any]: pass

class RhythmConsciousness(BasePlugin):
    """
    Main threaded bridge. Analyzes live AudioAnalyzer inputs, maps them against
    AgentRhythmProfiles, and fires off visualizer triggers automatically.
    """
    METADATA = {
        "id": "RhythmConsciousness",
        "type": "consciousness_bridge",
        "version": "1.0.0",
        "legacy_ref": "rhythm_consciousness"
    }

    def __init__(self, audio_analyzer: Any, agent_visualizer: Any) -> None: pass
    def register_agent(self, agent_id: str, personality: RhythmPersonality = RhythmPersonality.STEADY) -> None: pass
    def unregister_agent(self, agent_id: str) -> None: pass
    def update(self, dt: float) -> None: pass
    
    # Internal beat routing logic
    def _detect_interaction(self, agent1: str, agent2: str, current_time: float) -> Optional[Any]: pass
    def create_beat_effect(self, effect_type: str, intensity: float = 1.0, **kwargs) -> str: pass
```

---

## Inputs and Outputs

### Beat Prediction Logic
`BeatTimeline` buffers events inside `beat_history (maxlen=64)`. When calculating predictions:
1. Slices the time deltas between the last 64 events.
2. Filters out anomalies (`0.2 < interval < 2.0`).
3. Takes `np.mean(intervals)` to find standard beat length.
4. Extrapolates forward `current_time + prediction_window` (4 seconds).
5. Adds micro-timing error via `np.random.normal(0, avg_interval * 0.02)` to make the prediction look biological instead of strictly quantized.

### Agent Interactions (`_detect_interaction`)
Compares two agents' synchronization phase (`beat_phase % 1.0`).
- If phase diff < 0.1: Returns a `sync` interaction.
- If phase diff is between 0.4 and 0.6: Returns a `call_and_response` interaction.

---

## Edge Cases and Error Handling

### Stale Timelines
If audio drops out for more than 4 seconds, the `BeatTimeline` will exhaust its predicted buffer. Code must degrade gracefully simply returning `0` values rather than throwing exceptions or continuing to extrapolate into infinity, which causes graphical stutters in visual emitters.

### Thread Safety Contention
Because `update()` is pulled from the main graphical loop but events can push from the OS Audio Callback thread, `self._lock = threading.RLock()` must wrap *all* insertions and predictions into the timeline `deque`.

---

## Dependencies

### External Libraries
- `numpy` (For fast `np.mean` and standard distribution curves).
- `math` (For standard `.sin()` pulsing formulas).

### Internal Modules
- Expected to receive injected references to `core.audio_analyzer.AudioAnalyzer` and `core.extensions.agents.agent_visualizer.AgentVisualizer`. Both are allowed to be duck-typed mocks during testing.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_rhythmpersonality_accents` | Initializing `AgentRhythmProfile` with `RhythmPersonality.SWING` correctly auto-populates `accent_pattern` with `[1.0, 0.3, 0.7, 0.3]`. |
| `test_timeline_prediction_extrapolation` | Adding 4 artificial 1-second interval `BeatEvent`s into the timeline accurately generates 4 seconds of future predictions at roughly 1.0x spacing in `get_predicted_beats()`. |
| `test_generative_pattern_mutation` | Passing `mutation_rate = 1.0` into `RhythmGenerator.mutate_pattern()` fundamentally alters the output arrays (does not return an identical referential clone). |

**Minimum coverage:** 85% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] Implement `threading.RLock()` safely across all state mutation methods
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-COR036: AgentRhythmProfile` message
- [ ] BOARD.md updated (Status → ✅ Done)
- [ ] Lock released
