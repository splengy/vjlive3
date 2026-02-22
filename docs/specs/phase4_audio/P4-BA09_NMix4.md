# Spec: P4-BA09 — NMix4 (4-Channel Mixer with VU Meters)

**File naming:** `docs/specs/phase4_audio/P4-BA09_NMix4.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA09 — NMix4

**Phase:** Phase 4 / P4-BA09
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

NMix4 is a 4-channel audio mixer plugin for VJLive3 with built-in VU meters. It provides individual channel volume, pan, mute, solo, and output level metering, enabling precise audio mixing with visual feedback for live performances.

---

## What It Does NOT Do

- Does not provide audio effects (mixing only)
- Does not handle recording (playback only)
- Does not include automation (manual control only)
- Does not manage hardware outputs (software mixing only)

---

## Public Interface

```python
class NMix4Plugin:
    def __init__(self, num_channels: int = 4) -> None: ...
    
    def set_volume(self, channel: int, volume: float) -> None: ...
    def get_volume(self, channel: int) -> float: ...
    
    def set_pan(self, channel: int, pan: float) -> None: ...
    def get_pan(self, channel: int) -> float: ...
    
    def mute(self, channel: int, enabled: bool) -> None: ...
    def solo(self, channel: int, enabled: bool) -> None: ...
    
    def get_vu_meter(self, channel: int) -> float: ...
    def get_output_vu(self) -> float: ...
    
    def process(self, audio: AudioBuffer) -> AudioBuffer: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `num_channels` | `int` | Number of mixer channels | 1-8 |
| `channel` | `int` | Channel index | 0 to num_channels-1 |
| `volume` | `float` | Volume level | 0.0 to 1.0 |
| `pan` | `float` | Pan position | -1.0 (left) to 1.0 (right) |
| `enabled` | `bool` | Mute/solo state | True/False |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |

**Output:** `AudioBuffer` — Mixed output audio; `float` — VU meter level (0.0-1.0)

---

## Edge Cases and Error Handling

- What happens if channel out of range? → Clamp or raise error
- What happens if volume/pan invalid? → Clamp to valid range
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
| `test_channel_volume` | Sets and gets volume correctly |
| `test_channel_pan` | Sets and gets pan correctly |
| `test_mute_solo` | Mute and solo work correctly |
| `test_vu_meters` | VU meters update correctly |
| `test_audio_processing` | Processes audio through mixer |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BA09: NMix4 4-channel mixer with VU` message
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

*Specification based on Bogaudio NMix4 module.*