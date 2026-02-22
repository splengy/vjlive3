# Spec: P4-BA05 — BSwitch (Audio Router/Selector)

**File naming:** `docs/specs/phase4_audio/P4-BA05_BSwitch.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA05 — BSwitch

**Phase:** Phase 4 / P4-BA05
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BSwitch is an audio router/selector plugin for VJLive3. It provides multiple input selection, crossfading between sources, and mute functions, enabling flexible audio source switching during live performances.

---

## What It Does NOT Do

- Does not provide effects processing (routing only)
- Does not handle recording (playback only)
- Does not include automation (manual control only)
- Does not manage hardware inputs (software routing only)

---

## Public Interface

```python
class BSwitchPlugin:
    def __init__(self, num_inputs: int = 4) -> None: ...
    
    def select_input(self, input_index: int) -> None: ...
    def get_selected_input(self) -> int: ...
    
    def set_crossfade(self, input_a: int, input_b: int, amount: float) -> None: ...
    def get_crossfade(self) -> Tuple[int, int, float]: ...
    
    def mute(self, enabled: bool) -> None: ...
    def is_muted(self) -> bool: ...
    
    def set_volume(self, volume: float) -> None: ...
    def get_volume(self) -> float: ...
    
    def process(self, audio: AudioBuffer) -> AudioBuffer: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `num_inputs` | `int` | Number of inputs | 2-16 |
| `input_index` | `int` | Input to select | 0 to num_inputs-1 |
| `input_a` | `int` | Crossfade input A | 0 to num_inputs-1 |
| `input_b` | `int` | Crossfade input B | 0 to num_inputs-1 |
| `amount` | `float` | Crossfade amount | 0.0 (A) to 1.0 (B) |
| `enabled` | `bool` | Mute state | True/False |
| `volume` | `float` | Output volume | 0.0 to 1.0 |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |

**Output:** `AudioBuffer` — Routed audio

---

## Edge Cases and Error Handling

- What happens if input index out of range? → Clamp or raise error
- What happens if crossfade inputs same? → Select single input
- What happens if crossfade amount invalid? → Clamp to 0.0-1.0
- What happens on cleanup? → Reset all parameters, release resources

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
| `test_input_selection` | Selects inputs correctly |
| `test_crossfade` | Crossfades between inputs |
| `test_mute_control` | Mute works correctly |
| `test_volume_control` | Volume control works |
| `test_routing` | Routes audio correctly |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA05: BSwitch audio router` message
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

*Specification based on Bogaudio BSwitch module.*