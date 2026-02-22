# Spec Template — P2-D5 Audio-reactive DMX

**File naming:** `docs/specs/P2-D5_audio_dmx.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-D5 — Audio-reactive DMX

**Phase:** Phase 2
**Assigned To:** Worker
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module bridges the Audio Engine (P1-A1, P1-A2, P1-A3) with the DMX FX Engine (P2-D3). It allows lighting fixtures to react dynamically to incoming audio, extracting frequency bands, envelope followers, and beat triggers to modulate specific DMX parameters (like dimmer, color intensity, or strobe rate).

---

## What It Does NOT Do

- It does not calculate the FFT or beat detection itself (the Audio Engine does this).
- It does not generate raw DMX packets (P2-D1 handles output).
- It does not generate video-based audio-reactive effects (this is strictly for DMX).

---

## Public Interface

```python
from typing import Callable, List, Dict
import numpy as np

class AudioDmxLink:
    def __init__(self) -> None: ...
    def map_frequency_band(self, low_hz: float, high_hz: float, target_fx_param: str) -> None: ...
    def map_beat(self, target_fx_action: Callable) -> None: ...
    def update(self, audio_data: dict, delta_time: float) -> None: ...
    def clear_mappings(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `audio_data` | `dict` | Audio state from P1 Audio bus | Contains `bands`, `is_beat`, `rms` |
| `target_fx_param` | `str` | Name of parameter to modulate | Must exist on target DmxEffect |

---

## Edge Cases and Error Handling

- What happens if the audio engine stops sending data? → The DMX values should gradually decay to zero or their default state to avoid freezing at full brightness.
- What happens if a mapped parameter does not exist? → The mapper logs a warning and ignores the mapping.

---

## Dependencies

- Internal: Audio Bus interface, DMX FX Engine (P2-D3)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_beat_trigger_mapping` | An audio beat flag triggers the mapped DMX effect action (e.g., strobe) |
| `test_frequency_band_mapping` | Amplitude in a specific freq band correctly updates the mapped DMX parameter |
| `test_audio_dropout_decay` | Missing audio updates cause mapped values to decay to 0 |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-D5: Audio-reactive DMX` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
