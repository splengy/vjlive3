# Spec: P1-A3 — Reactivity Bus (Audio-Reactive Framework)

**File naming:** `docs/specs/P1-A3_reactivity_bus.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-A3 — Reactivity Bus

**Phase:** Phase 1 / P1-A3
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

The reactivity bus provides a publish-subscribe framework for audio-reactive effects. It distributes audio features and beat events to registered plugins, allowing them to react to audio input. The bus manages feature smoothing, parameter mapping, and ensures thread-safe communication between audio analysis and rendering systems.

---

## What It Does NOT Do

- Does not perform audio analysis (delegates to P1-A1)
- Does not detect beats (delegates to P1-A2)
- Does not handle audio input sources (delegates to P1-A4)
- Does not provide UI for mapping parameters (delegates to P1-N4)

---

## Public Interface

```python
class ReactivityBus:
    def __init__(self) -> None: ...
    
    def subscribe(self, plugin_id: str, callback: ReactivityCallback) -> None: ...
    def unsubscribe(self, plugin_id: str) -> None: ...
    
    def publish_features(self, features: AudioFeatures) -> None: ...
    def publish_beat(self, beat_info: BeatInfo) -> None: ...
    
    def map_parameter(self, plugin_id: str, param_name: str, source: str, curve: MappingCurve) -> None: ...
    def unmap_parameter(self, plugin_id: str, param_name: str) -> None: ...
    
    def get_mapped_value(self, plugin_id: str, param_name: str) -> float: ...
    
    def start_smoothing(self, plugin_id: str, param_name: str, smoothing_time: float) -> None: ...
    def stop_smoothing(self, plugin_id: str, param_name: str) -> None: ...
    
    def clear_mappings(self, plugin_id: str) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `plugin_id` | `str` | Unique plugin identifier | Non-empty |
| `callback` | `ReactivityCallback` | Function to call on update | Callable |
| `features` | `AudioFeatures` | Audio analysis results | From P1-A1 |
| `beat_info` | `BeatInfo` | Beat detection result | From P1-A2 |
| `param_name` | `str` | Plugin parameter name | Valid parameter |
| `source` | `str` | Audio feature source (e.g., 'bass', 'mid', 'treble') | Known feature |
| `curve` | `MappingCurve` | Response curve for mapping | Linear, exponential, etc. |
| `smoothing_time` | `float` | Smoothing time in seconds | > 0 |

**Output:** Publishes mapped parameter values to subscribed callbacks

---

## Edge Cases and Error Handling

- What happens if plugin subscribes twice? → Replace existing subscription
- What happens if plugin unsubscribes but not subscribed? → Ignore
- What happens if mapping source doesn't exist? → Use default value
- What happens if smoothing time is invalid? → Use default smoothing
- What happens on cleanup? → Clear all subscriptions and mappings

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - None required for basic functionality
- Internal modules this depends on:
  - `vjlive3.audio.audio_analyzer` (P1-A1)
  - `vjlive3.audio.beat_detector` (P1-A2)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_subscribe_unsubscribe` | Subscription management works |
| `test_publish_features` | Features published to callbacks |
| `test_publish_beat` | Beat events published to callbacks |
| `test_parameter_mapping` | Audio features mapped to parameters |
| `test_smoothing` | Parameter smoothing works correctly |
| `test_multiple_plugins` | Handles multiple subscribers |
| `test_edge_cases` | Handles invalid inputs gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-A3: Reactivity bus` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Checkpoint

- [ ] Spec reviewed and approved
- [ ] Implementation ready to begin
- [ ] All dependencies verified
- [ ] Test plan complete
- [ ] Definition of Done clear

---

*Specification based on VJlive-2 reactivity bus architecture.*