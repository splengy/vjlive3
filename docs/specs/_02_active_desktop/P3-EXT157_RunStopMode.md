# P3-EXT157: RunStopMode Enumeration

## Specification Status
- **Phase**: Pass 1 (Skeleton)
- **Target Phase**: Pass 2 (Detailed Technical Spec)
- **Priority**: P0
- **Module**: `vtempi` plugin support system
- **Implementation Path**: `src/vjlive3/plugins/vtempi/run_stop_mode.py`

## Executive Summary

RunStopMode is an enumeration that defines the operational state control modes for temporal/rhythm-based VJLive3 plugins (specifically the vtempi module family). It manages how plugins respond to play/stop commands in live performance contexts, supporting both predictable synchronization and adaptive performance behavior.

## Problem Statement

Live VJ performances require flexible control over temporal plugin behavior:
- Some effects need to **freeze** on stop (e.g., scanning effects hold position)
- Some effects need to **continue** internally but stop output (e.g., generative processes)
- Some effects need **immediate reset** for clean transitions
- Some effects need **phase-locked synchronization** with external clock sources

Without a standardized mode enumeration, each plugin implements its own stop behavior, creating inconsistency and unpredictable performance in mixed effect chains.

## Solution Overview

RunStopMode provides a standard enum with 4-6 operational modes:

1. **RUN**: Active normal operation
2. **STOP**: Frozen state, no internal updates
3. **SYNC**: Continue internal state but synchronized to external clock
4. **RESET**: Initialize to default values, then stop
5. **PAUSE**: Continue internal state without output (optional)
6. **HOLD**: Freeze output but update internal state (generative only)

## Detailed Behavior

### State Transitions
```
STOP → RUN: Resume from frozen state
STOP → RESET: Clear state, remain stopped
STOP → SYNC: Lock to external clock, resume timing
RUN → STOP: Freeze current state
RUN → PAUSE: Continue state, suppress output
PAUSE → RUN: Resume output from paused state
```

### Mode Specifications

**STOP Mode** (Frozen)
- No internal state updates
- Output frozen at last valid value
- Memory of previous state preserved
- Can resume without artifacts

**RUN Mode** (Active)
- Full operation, all internal updates active
- Normal parameter responsiveness
- Standard output pipeline

**SYNC Mode** (Clock-Locked)
- Internal state updates locked to external tempo/BPM
- Phase alignment with global clock
- Useful for tempo-reactive effects

**RESET Mode** (Initialize)
- Clear all internal state to defaults
- Return to initial configuration
- Typically followed by STOP

**HOLD Mode** (Generative Pause)
- Continue internal random/generative processes
- Do not output to render pipeline
- Allows "prepare next frame" for smooth transitions

## Public Interface

```python
from enum import Enum

class RunStopMode(Enum):
    """Enum for run/stop state modes of temporal plugins."""
    
    RUN = "run"           # Active normal operation
    STOP = "stop"         # Frozen state
    SYNC = "sync"         # Synchronized to external clock
    RESET = "reset"       # Initialize to defaults
    PAUSE = "pause"       # Continue updating but hold output (optional)
    HOLD = "hold"         # Continue generation but don't output (optional)
    
    def __str__(self) -> str:
        """Return human-readable mode name."""
    
    def can_output(self) -> bool:
        """Check if mode allows output rendering."""
        # STOP, RESET, HOLD: no output
        # RUN, SYNC, PAUSE: allow output
    
    def updates_internal_state(self) -> bool:
        """Check if mode updates internal state."""
        # STOP, RESET: no continuous updates
        # RUN, SYNC, PAUSE, HOLD: update state
    
    @classmethod
    def from_string(cls, mode_str: str) -> 'RunStopMode':
        """Parse mode from string (case-insensitive)."""
    
    def to_dict(self) -> dict:
        """Serialize mode to JSON-compatible dict."""
```

## Mathematical Formulations

### Phase Synchronization (SYNC Mode)
For effects requiring tempo-lock:

$$\text{phase}(t) = (t \cdot \text{bpm} / 60) \mod 1$$

where $t$ is elapsed time in seconds and bpm is beats per minute.

### State Preservation (STOP Mode)
Frozen state $S_{\text{frozen}}$ preserved through transition:

$$S_{\text{stop}}(t) = S_{\text{last}} \quad \forall t > t_{\text{stop}}$$

## Performance Characteristics

- **Enum lookup**: O(1) constant time
- **State transition**: O(1) no recomputation needed
- **Memory overhead**: 1 byte per enumeration instance
- **Compatibility**: Works with all plugin types

## Test Plan

1. **Enumeration Integrity**
   - All enum values accessible
   - No duplicate values
   - String parsing works correctly
   
2. **State Transition Validation**
   - All valid transitions succeed
   - Invalid transitions rejected (if enforced)
   - No state leaks across transitions

3. **Mode Behavior Queries**
   - `can_output()` returns correct values per mode
   - `updates_internal_state()` returns correct values
   - `from_string()` handles all mode strings

4. **Serialization**
   - Modes serialize to/from dict
   - JSON compatibility verified
   - Round-trip serialization works

5. **Integration**
   - Works with vtempi base class
   - Compatible with parameter system
   - No conflicts with existing modes

6. **Edge Cases**
   - Case-insensitive string parsing
   - Invalid string input handling
   - Enum comparison operators work

## Definition of Done

- [ ] Enum defined with all 6 modes
- [ ] `__str__()` returns human-readable names
- [ ] `can_output()` logic matches spec
- [ ] `updates_internal_state()` logic correct
- [ ] `from_string()` parses all modes
- [ ] `to_dict()` serialization works
- [ ] All test cases pass (100% coverage)
- [ ] No type annotation issues
- [ ] Integration test with vtempi base class
- [ ] Documentation complete
- [ ] No stub code remaining
- [ ] Performance benchmarks <1ms
- [ ] Compatible with existing plugins
- [ ] State transition rules enforced or documented
- [ ] Error handling for invalid modes
- [ ] Serialization round-trip verified
- [ ] ≤900 lines including docstrings
- [ ] Complies with style guide

## Dependencies

- `enum.Enum` (standard library)
- vtempi base class (for integration)
- PerformanceMonitor (optional, for timing)

## Related Specs

- P3-VTEMPI-BASE: vtempi plugin base class
- P3-COR-PARAMS: Parameter system integration
- P0-PLUGIN-ARCH: Overall plugin architecture

---

**Notes for Pass 2 Implementation:**
- Determine if state transition validation is strict (reject invalid) or logged (warn invalid)
- Confirm which modes (PAUSE, HOLD) are truly needed vs luxury
- Document expected behavior for plugins not supporting all modes
- Add mode compatibility matrix documentation
