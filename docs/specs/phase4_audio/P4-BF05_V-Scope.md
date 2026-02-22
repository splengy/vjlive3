# Spec: P4-BF05 — V-Scope (Oscilloscope)

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

V-Scope is an oscilloscope plugin for VJLive3. It provides real-time waveform visualization of audio signals with adjustable timebase, vertical scale, trigger level, and display modes, enabling detailed audio signal analysis and debugging.

---

## What It Does NOT Do

- Does not process audio signals (visualization only)
- Does not include spectrum analysis (waveform only)
- Does not handle recording (real-time only)
- Does not provide measurement tools (basic display only)

---

## Public Interface

```python
class VScopePlugin:
    def __init__(self) -> None: ...
    
    def set_timebase(self, timebase: float) -> None: ...
    def get_timebase(self) -> float: ...
    
    def set_vertical_scale(self, scale: float) -> None: ...
    def get_vertical_scale(self) -> float: ...
    
    def set_trigger_level(self, level: float) -> None: ...
    def get_trigger_level(self) -> float: ...
    
    def set_display_mode(self, mode: str) -> None: ...
    def get_display_mode(self) -> str: ...
    
    def process(self, audio: AudioBuffer) -> None: ...
    def get_waveform_data(self) -> np.ndarray: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `timebase` | `float` | Time per division in seconds | 0.0001 to 1.0 |
| `scale` | `float` | Vertical scale (volts/div) | 0.01 to 10.0 |
| `level` | `float` | Trigger level | -1.0 to 1.0 |
| `mode` | `str` | Display mode | 'dots', 'lines', 'both' |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |

**Output:** `np.ndarray` — Waveform data for visualization

---

## Edge Cases and Error Handling

- What happens if timebase/scale out of range? → Clamp to valid range
- What happens if trigger level invalid? → Clamp to -1.0-1.0
- What happens if display mode invalid? → Use default (lines)
- What happens on cleanup? → Clear display buffers, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for audio processing — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.audio.audio_buffer` (for AudioBuffer type)
  - `vjlive3.plugins.api` (for PluginBase)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_timebase_setting` | Sets and gets timebase |
| `test_vertical_scale` | Sets and gets vertical scale |
| `test_trigger_level` | Sets and gets trigger level |
| `test_display_mode` | Changes display modes |
| `test_waveform_capture` | Captures waveform correctly |
| `test_edge_cases` | Handles errors gracefully |

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

*Specification based on Befaco V-Scope module.*