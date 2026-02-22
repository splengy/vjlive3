# Spec: P4-BF03 — V-Outs (Output Router)

**File naming:** `docs/specs/phase4_audio/P4-BF03_V-Outs.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BF03 — V-Outs

**Phase:** Phase 4 / P4-BF03
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

V-Outs is an output router plugin for VJLive3. It provides multiple output selection, independent volume control per output, and mute functions, enabling flexible audio routing to different outputs (main, aux, monitor, etc.).

---

## What It Does NOT Do

- Does not provide effects processing (routing only)
- Does not handle recording (playback only)
- Does not include automation (manual control only)
- Does not manage hardware outputs (software routing only)

---

## Public Interface

```python
class VOutsPlugin:
    def __init__(self, num_inputs: int = 1, num_outputs: int = 4) -> None: ...
    
    def route_input_to_output(self, input_idx: int, output_idx: int, enabled: bool) -> None: ...
    def get_routing(self, input_idx: int) -> List[bool]: ...
    
    def set_output_volume(self, output_idx: int, volume: float) -> None: ...
    def get_output_volume(self, output_idx: int) -> float: ...
    
    def mute_output(self, output_idx: int, enabled: bool) -> None: ...
    def is_output_muted(self, output_idx: int) -> bool: ...
    
    def process(self, audio: AudioBuffer) -> Dict[int, AudioBuffer]: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `num_inputs` | `int` | Number of inputs | 1-8 |
| `num_outputs` | `int` | Number of outputs | 1-8 |
| `input_idx` | `int` | Input index | 0 to num_inputs-1 |
| `output_idx` | `int` | Output index | 0 to num_outputs-1 |
| `enabled` | `bool` | Routing/mute state | True/False |
| `volume` | `float` | Output volume | 0.0 to 1.0 |
| `audio` | `AudioBuffer` | Input audio buffer | Valid buffer |

**Output:** `Dict[int, AudioBuffer]` — Routed audio per output

---

## Edge Cases and Error Handling

- What happens if input/output index out of range? → Clamp or raise error
- What happens if volume invalid? → Clamp to 0.0-1.0
- What happens if no routing configured? → Pass input to all outputs
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
| `test_routing_config` | Configures input-output routing |
| `test_output_volume` | Sets and gets output volume |
| `test_output_mute` | Mutes outputs correctly |
| `test_audio_routing` | Routes audio to correct outputs |
| `test_multiple_outputs` | Handles multiple outputs |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BF03: V-Outs output router` message
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

*Specification based on Befaco V-Outs module.*