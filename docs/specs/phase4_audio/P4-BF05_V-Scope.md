# Spec: P4-BF05 — V-Scope

**File naming:** `docs/specs/phase4_audio/P4-BF05_V-Scope.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BF05 — V-Scope

**Phase:** Phase 4 / P4-BF05
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

V-Scope (Befaco Oscilloscope) is a visual signal monitor that displays the waveform of an audio signal in real-time. It provides timebase (horizontal scale), gain (vertical scale), and trigger controls for stable waveform visualization, making it essential for signal monitoring and debugging.

---

## What It Does NOT Do

- Does not perform audio analysis or feature extraction
- Does not provide spectrum analysis (only time-domain)
- Does not include built-in effects or processing
- Does not support multiple channels (mono only)
- Does not save waveform data or provide measurement tools

---

## Public Interface

```python
class VScope:
    def __init__(self) -> None: ...
    
    def set_time_div(self, time_div: float) -> None: ...
    def get_time_div(self) -> float: ...
    
    def set_gain(self, gain: float) -> None: ...
    def get_gain(self) -> float: ...
    
    def set_trigger_level(self, trigger_level: float) -> None: ...
    def get_trigger_level(self) -> float: ...
    
    def process(self, audio: float) -> None: ...
    def get_waveform_buffer(self) -> np.ndarray: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `time_div` | `float` | Timebase (seconds per division) | 0.001 to 1.0 |
| `gain` | `float` | Vertical gain | 0.1 to 10.0 |
| `trigger_level` | `float` | Trigger threshold | -1.0 to 1.0 |
| `audio` | `float` | Input audio signal | -1.0 to 1.0 |

**Output:** `np.ndarray` — Waveform buffer (circular buffer of recent samples)

---

## Edge Cases and Error Handling

- What happens if time_div is too small? → May show compressed waveform
- What happens if gain is extreme? → May cause clipping or too small signal
- What happens if trigger_level is out of range? → Clamp to [-1.0, 1.0]
- What happens if audio is silent? → May not trigger, show flat line
- What happens on cleanup? → Clear buffer, reset parameters

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for circular buffer — fallback: use list
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_buffer_fill` | Circular buffer fills correctly |
| `test_timebase_control` | Timebase affects buffer display |
| `test_gain_control` | Gain scales waveform vertically |
| `test_trigger` | Trigger stabilizes waveform |
| `test_sine_wave` | Displays sine wave correctly |
| `test_edge_cases` | Handles extreme parameters |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BF05: V-Scope oscilloscope` message
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

*Specification based on Befaco V-Scope module from legacy VJlive-2 codebase.*