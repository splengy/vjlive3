# P3-EXT416: VTempi Engine (State, Channel, Multiplier Enums)

## Description

A faithful recreation of the Make Noise TEMPI logic—a 6-channel polyphonic hardware clocking module. This digital clone orchestrates complex video synchronization sequences based on prime multiples, Fibonacci divisions, and state-machine shifting.

## What This Module Does

This specification defines the foundational data types for the `VTempi` engine, ported from `VJlive-2/plugins/vtempi/vtempi.py`. It explicitly answers multiple P3-EXT references including `P3-EXT262` (DutyCycleMode), `P3-EXT274` (HumanResolution), `P3-EXT282` (LEDColor), and `P3-EXT298` (ModBehavior). Internally, VTempi mimics hardware by assigning multipliers/divisors to a leading tempo beat, triggering visual gates based on exact phase accumulation.

## Public Interface

```python
class ShiftDirection(Enum):
    CLOCKWISE = 'clockwise'
    COUNTERCLOCKWISE = 'counterclockwise'
    RANDOM = 'random'

class RunStopMode(Enum):
    RUN_STOP = "run_stop"           
    RUN_STOP_ALL = "run_stop_all"   
    ALT_RUN = "alt_run"             

class ModBehavior(Enum):
    TOGGLED = "toggled"
    MOMENTARY = "momentary"

class DutyCycleMode(Enum):
    CLOCK_50 = "clock_50"     
    TRIGGER_10MS = "trigger"  

class HumanResolution(Enum):
    RES_100 = 100    
    RES_50 = 50      
    RES_25 = 25      

class LEDColor(Enum):
    OFF = "off"
    # ... Red, Blue, Green, Purple, Pink, Amber, White
```

## Inputs and Outputs

*   **Inputs**: `Channel` Data structs holding multipliers/divisors, `HumanResolution` quantization limits mapping human keystrokes to tempos, Mod gate boolean flags.
*   **Outputs**: Phase-accurate visual pulse booleans applied synchronously to 6 parameter outputs, orchestrating complex polyrhythmic visual cuts.

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2` and `vjlive`
- **File Paths**: 
  - Source Code: `core/sequencers/tempi.py` / `plugins/vtempi/vtempi.py`
  - Hardware Manual: `vjlive/JUNK/manuals_make_noise/MNmanuals/tempi-manual.pdf`
  - Hardware Panel Photo: `vjlive/JUNK/manuals_make_noise/MNmanuals/tempi-website-feb29.jpg`
- **Architectural Soul**: A purely mathematical phase accumulator. By interpreting ratios (e.g., multiplier 3, divisor 2 = 1.5x speed) against a globally driven delta-time `dt`, it generates high-precision trigger states.

### Key Algorithms
1. **Phase Resolution Mathematics**: `HumanResolution.RES_100` forces rhythmic taps into pure whole integers. `RES_50` permits half-steps, calculating offsets internally via `half_step = round(ratio * 2) / 2.0`.
2. **Modulation System**: Using the physical hardware ruleset, enabling a `Mod Gate` combined with `ShiftDirection.CLOCKWISE` cascades the multiplier values of channel 1->2->3 instantly, creating chaotic evolving polyrhythms.
3. **State Factory**: Inherits 16 hardware-accurate preset states (Power of 2s, Primes, Odd, Fibonacci) identical to firmware v.31 mapping.

### Optimization Constraints & Safety Rails
- **State Serialization**: The `StateManager` writes states directly to JSON on disk. This MUST execute cleanly on a background thread preventing UI-lockout when modifying Bank structures.

## Test Plan

*   **Logic (Pytest)**: Heavily unit test `get_effective_ratio()` across prime/negative offsets. Ensure the `apply_shift()` command cascades values across `Channel` objects exactly per Make Noise documentation.
*   **Performance Constraints**: Phase checking runs every render tick across 6 multiplexed outputs; simple scalar arithmetic limits it safely below 1ms.

## Deliverables

1.  Implemented `types.py` for all VTempi enumerations.
2.  `Channel` and `State` classes holding structural multiplier data (`src/vjlive3/core/sequencer/vtempi_state.py`).
3.  Unit tests validating modulo shifting combinations.
