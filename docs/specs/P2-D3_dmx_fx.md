# Spec Template — P2-D3 DMX FX Engine

**File naming:** `docs/specs/P2-D3_dmx_fx.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-D3 — DMX FX Engine (Chases, Rainbow, Strobe)

**Phase:** Phase 2
**Assigned To:** Worker Beta
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

This module implements procedurally generated effects for DMX lighting fixtures. It sits above the core DMX engine (P2-D1) and feeds it channel values. It provides built-in patterns including Chases (sequential stepping), Rainbows (phase-shifted HSL to RGB conversion across fixtures), and Strobing (rapid on/off cycles). These effects can run independently or be driven by the audio reactivity bus (e.g., beat-synced strobes).

---

## What It Does NOT Do

- It does NOT communicate directly with ArtNet/sACN (that is P2-D2).
- It does NOT calculate audio beats itself (it receives beat triggers from the Audio Engine).
- It does NOT map universes (it applies effects to provided groups of `DMXFixture` instances).

---

## Public Interface

```python
from typing import List

class DmxEffect:
    def update(self, delta_time: float) -> None: ...
    def apply_to(self, fixtures: List['DMXFixture']) -> None: ...

class ChaseEffect(DmxEffect):
    def __init__(self, speed: float = 1.0, forward: bool = True) -> None: ...

class RainbowEffect(DmxEffect):
    def __init__(self, speed: float = 1.0, spread: float = 1.0) -> None: ...

class StrobeEffect(DmxEffect):
    def __init__(self, rate_hz: float = 10.0, duty_cycle: float = 0.5) -> None: ...
    def trigger(self) -> None: ... # For beat-sync

class DmxFxEngine:
    def __init__(self) -> None: ...
    def add_effect(self, group_name: str, effect: DmxEffect) -> None: ...
    def remove_effect(self, group_name: str) -> None: ...
    def update_all(self, delta_time: float, fixture_groups: dict) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `delta_time` | `float` | Time elapsed since last frame | > 0.0 |
| `fixtures` | `List[DMXFixture]`| Fixtures to apply effect to | P2-D1 valid fixtures |
| `speed` | `float` | Multiplier for effect speed | > 0.0 |
| `rate_hz` | `float` | Strobe flashes per second | 0.1 to 30.0 |

---

## Edge Cases and Error Handling

- What happens if an effect is applied to an empty fixture list? → It returns silently (no-op).
- What happens if `delta_time` is abnormally large (e.g., lag spike)? → Effects should clamp max progression to prevent skipping through multiple chase cycles instantly.
- What happens if a fixture lacks RGB capabilities but is given a Rainbow effect? → The effect safely falls back to modulating the DIMMER channel if available, or does nothing.

---

## Dependencies

- Internal modules:
  - `vjlive3.dmx.core.DMXFixture` (from P2-D1)
- Standard Library: `math`, `colorsys` (for HSL to RGB math)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_rainbow_color_spread` | Rainbow effect generates phase-shifted colors across fixtures |
| `test_chase_step_progression` | Chase effect moves exactly one fixture forward per interval |
| `test_strobe_duty_cycle` | Strobe effect correctly toggles between max and min values based on time |
| `test_fx_engine_update` | Engine correctly routes updates to assigned fixture groups |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-D3: DMX FX engine` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
