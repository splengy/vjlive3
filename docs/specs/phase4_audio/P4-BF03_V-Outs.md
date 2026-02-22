# Spec: P4-BF03 — V-Outs

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

V-Outs (Befaco Output Module) provides a dedicated output stage for audio signals with level control and clipping protection. It serves as the final output stage before audio leaves the modular system, offering a master volume control and signal conditioning.

---

## What It Does NOT Do

- Does not provide stereo panning (mono only)
- Does not include built-in effects or processing
- Does not support multiple output channels
- Does not include metering or visual feedback

---

## Public Interface

```python
class VOuts:
    def __init__(self) -> None: ...
    
    def set_level(self, level: float) -> None: ...
    def get_level(self) -> float: ...
    
    def process(self, audio: float) -> float: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `level` | `float` | Output level | 0.0 to 1.0 |
| `audio` | `float` | Input audio signal | -1.0 to 1.0 |

**Output:** `float` — Output audio signal (clipped to -1.0 to 1.0)

---

## Edge Cases and Error Handling

- What happens if level is 0? → Output is silent
- What happens if level > 1? → Clamp to 1.0
- What happens if audio clips? → Hard clip to [-1.0, 1.0]
- What happens on cleanup? → Reset level to default (0.7)

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - None required for basic functionality
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_level_control` | Level parameter scales output |
| `test_clipping` | Clips output to valid range |
| `test_zero_level` | Level=0 produces silence |
| `test_edge_cases` | Handles extreme input values |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-4] P4-BF03: V-Outs output module` message
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

*Specification based on Befaco V-Outs module from legacy VJlive-2 codebase.*