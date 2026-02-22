# Spec: P4-BA03 — BMatrix81 (8x1 Mix Matrix)

**File naming:** `docs/specs/phase4_audio/P4-BA03_BMatrix81.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA03 — BMatrix81

**Phase:** Phase 4 / P4-BA03
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

BMatrix81 is an 8-input to 1-output mix matrix plugin for VJLive3. It provides individual channel volume controls, mute/solo functions, and flexible routing, allowing complex mixing configurations for live audio performance.

---

## What It Does NOT Do

- Does not provide multi-output routing (single output only)
- Does not include effects processing (mixing only)
- Does not handle recording (playback only)
- Does not include automation (manual control only)

---

## Public Interface

```python
class BMatrix81Plugin:
    def __init__(self, num_inputs: int = 8) -> None: ...
    
    def set_channel_volume(self, channel: int, volume: float) -> None: ...
    def get_channel_volume(self, channel: int) -> float: ...
    
    def mute(self, channel: int, enabled: bool) -> None: ...
    def solo(self, channel: int, enabled: bool) -> None: ...
    
    def set_output_volume(self, volume: float) -> None: ...
    def get_output_volume(self) -> float: ...
    
    def process(self, audio: AudioBuffer) -> AudioBuffer: ...
    
    def reset(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `num_inputs` | `int` | Number of input channels | 1-16 |
| `channel` | `int` | Channel index | 0 to num_inputs-1 |
| `volume` | `float` | Volume level | 0.0 to 1.0 |
| `enabled` | `bool` | Mute/solo state | True/False |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |

**Output:** `AudioBuffer` — Mixed output audio

---

## Edge Cases and Error Handling

- What happens if channel out of range? → Clamp or raise error
- What happens if volume invalid? → Clamp to 0.0-1.0
- What happens if all channels solo? → Mix all or mute based on policy
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
| `test_channel_volume` | Sets and gets channel volume |
| `test_mute_solo` | Mute and solo work correctly |
| `test_output_volume` | Sets and gets output volume |
| `test_mixing` | Mixes multiple channels correctly |
| `test_solo_priority` | Solo takes precedence over mute |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA03: BMatrix81 mix matrix` message
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

*Specification based on Bogaudio BMatrix81 module.*