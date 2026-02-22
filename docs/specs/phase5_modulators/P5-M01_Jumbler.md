# Spec: P5-M01 — Jumbler (Randomization Engine)

**File naming:** `docs/specs/phase5_modulators/P5-M01_Jumbler.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P5-M01 — Jumbler

**Phase:** Phase 5 / P5-M01
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Jumbler is a randomization engine that generates random values, sequences, and patterns for use in modular synthesis. It provides various randomization algorithms, probability controls, and pattern generation capabilities, making it ideal for creating evolving, unpredictable modulation sources.

---

## What It Does NOT Do

- Does not provide deterministic sequencing (use sequencer modules)
- Does not include built-in effects or processing
- Does not support CV control of randomization parameters
- Does not include pattern storage or recall

---

## Public Interface

```python
class Jumbler:
    def __init__(self) -> None: ...
    
    def set_mode(self, mode: str) -> None: ...
    def get_mode(self) -> str: ...
    
    def set_probability(self, probability: float) -> None: ...
    def get_probability(self) -> float: ...
    
    def set_range(self, min_val: float, max_val: float) -> None: ...
    def get_range(self) -> Tuple[float, float]: ...
    
    def set_steps(self, steps: int) -> None: ...
    def get_steps(self) -> int: ...
    
    def generate(self) -> float: ...
    def generate_sequence(self, length: int) -> List[float]: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `mode` | `str` | Randomization mode | 'uniform', 'gaussian', 'exponential', 'poisson' |
| `probability` | `float` | Probability of change | 0.0 to 1.0 |
| `min_val, max_val` | `float` | Output range | min_val < max_val |
| `steps` | `int` | Number of steps in sequence | > 0 |

**Output:** `float` — Random value or `List[float]` — Random sequence

---

## Edge Cases and Error Handling

- What happens if probability is 0? → Output is constant
- What happens if probability is 1? → Always changes
- What happens if range is invalid? → Raise ValueError
- What happens if steps is 0? → Return empty list
- What happens on cleanup? → Reset all parameters to defaults

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for random number generation — fallback: use random module
- Internal modules this depends on:
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_uniform_mode` | Generates uniform random values |
| `test_gaussian_mode` | Generates gaussian random values |
| `test_probability` | Probability affects output correctly |
| `test_range_control` | Output stays within specified range |
| `test_sequence_generation` | Generates correct length sequences |
| `test_edge_cases` | Handles extreme parameter values |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-5] P5-M01: Jumbler randomization engine` message
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

*Specification based on VJlive-2 Jumbler module.*