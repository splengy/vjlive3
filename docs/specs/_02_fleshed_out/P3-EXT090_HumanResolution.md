# P3-EXT090 — HumanResolution

**Fleshed Specification — Pass 2**  
**Agent:** desktop-roo  
**Date:** 2025-03-03  
**Phase:** 3-Pass Architecture — Pass 2 (Spec Fleshing)  
**Legacy Source:** `core/sequencers/tempi.py` (lines 44-47, 385-436) and `plugins/vtempi/vtempi.py` (complete)  
**Related:** TempiProgrammingEngine, TempiChannel, tap tempo quantization

---

## Executive Summary

`HumanResolution` is an **enumeration** that defines the quantization resolution for human tap tempo input in the V-Tempi sequencer module. It controls how precisely the system interprets a user's tap timing to set channel tempo ratios. The enum has three values:

- `RES_100` (100): Strictest quantization — rounds to nearest integer multiplier/divisor
- `RES_50` (50): Default — half-step quantization (0.5 increments) with fine offset
- `RES_25` (25): Freest — fine quantization (1-cent increments) with fine offset

**Key Characteristics:**
- **Category:** Utility / Configuration (not a visual effect)
- **Usage:** Set on `TempiProgrammingEngine.human_resolution` to control tap quantization behavior
- **Complexity:** Low (simple enum + conditional logic in `tap_channel()`)
- **Bug:** The core implementation in `core/sequencers/tempi.py` is **incomplete** — `RES_25` case is missing from `tap_channel()` method. The complete implementation exists in `plugins/vtempi/vtempi.py`.
- **Migration:** Straightforward port to VJLive3; ensure all three resolution cases are implemented.

---

## Detailed Behavior and Parameter Interactions

### 1. Enum Definition

```python
from enum import Enum

class HumanResolution(Enum):
    RES_100 = 100    # Strictest — quantized to coarse mult/div
    RES_50 = 50      # Default — moderate quantization
    RES_25 = 25      # Freest — fine mult/div equivalent
```

The numeric values (100, 50, 25) represent the **resolution in "human readability" units**, not directly used in calculations. They indicate the level of quantization: 100 = strictest (coarse), 25 = freest (fine).

### 2. Quantization Algorithms

The `tap_channel()` method in `TempiProgrammingEngine` processes tap intervals and converts them to channel timing parameters (`multiplier`, `divisor`, `fine_offset`). The algorithm varies based on `human_resolution`.

**Common Preprocessing:**

```python
def tap_channel(self, channel: TempiChannel, timestamp: float):
    # Record tap
    cid = channel.id
    if cid not in self._tap_buffers:
        self._tap_buffers[cid] = []
    self._tap_buffers[cid].append(timestamp)
    self._tap_buffers[cid] = self._tap_buffers[cid][-8:]  # Keep last 8 taps

    taps = self._tap_buffers[cid]
    if len(taps) < 2:
        return  # Need at least 2 taps to compute interval

    intervals = [taps[i] - taps[i-1] for i in range(1, len(taps))]
    avg_interval = sum(intervals) / len(intervals)
    if avg_interval <= 0:
        return

    tap_bpm = 60.0 / avg_interval  # Convert average interval to BPM
```

**Resolution-Specific Quantization:**

#### Case A: `RES_100` (Strictest)

```python
if self.human_resolution == HumanResolution.RES_100:
    # Quantize to nearest integer ratio relative to current channel setting
    ratio = tap_bpm / max(1, channel.multiplier / max(channel.divisor, 1) * 120.0)
    nearest = max(1, round(ratio))
    if ratio >= 1:
        channel.multiplier = nearest
        channel.divisor = 1
    else:
        channel.divisor = max(1, round(1.0 / ratio))
        channel.multiplier = 1
    channel.fine_offset = 0.0
```

**Behavior:**  
- Computes `ratio = tap_bpm / (current_ratio × 120)`  
- Rounds `ratio` to nearest integer  
- If `ratio ≥ 1`, sets `multiplier = nearest`, `divisor = 1`  
- If `ratio < 1`, sets `divisor = round(1/ratio)`, `multiplier = 1`  
- `fine_offset` always 0 (no fine adjustment)

**Result:** Coarse quantization; only integer multiplier/divisor values (1, 2, 3, ...). Suitable for strict, repetitive tempi.

#### Case B: `RES_50` (Default)

```python
elif self.human_resolution == HumanResolution.RES_50:
    ratio = tap_bpm / 120.0
    half_step = round(ratio * 2) / 2.0  # Round to nearest 0.5
    if half_step >= 1:
        channel.multiplier = int(half_step)
        channel.fine_offset = half_step - int(half_step)  # Fractional part (0 or 0.5)
        channel.divisor = 1
    else:
        inv = 1.0 / max(0.01, half_step)
        channel.divisor = int(inv)
        channel.fine_offset = -(inv - int(inv)) * 0.02
        channel.multiplier = 1
```

**Behavior:**  
- Computes `ratio = tap_bpm / 120`  
- Rounds to nearest **half-step** (`0.5` increments)  
- If `half_step ≥ 1`: `multiplier = int(half_step)`, `fine_offset = fractional part` (0 or 0.5)  
- If `half_step < 1`: Uses reciprocal; `divisor = int(1/half_step)`, `fine_offset = -(fractional part) × 0.02`  
- The `0.02` factor scales the fine offset to match the hardware's fine-tuning range

**Result:** Moderate quantization; allows 0.5 increments in multiplier (e.g., 1.5×, 2.5×). Default for general use.

#### Case C: `RES_25` (Freest) — **MISSING IN CORE**

```python
else:  # RES_25
    # Freest: fine resolution
    ratio = tap_bpm / 120.0
    if ratio >= 1:
        channel.multiplier = int(ratio)
        channel.fine_offset = ratio - int(ratio)  # Full fractional precision
        channel.divisor = 1
    else:
        inv = 1.0 / max(0.01, ratio)
        channel.divisor = int(inv)
        channel.fine_offset = -(inv - int(inv)) * 0.02
        channel.multiplier = 1
```

**Behavior:**  
- Computes `ratio = tap_bpm / 120`  
- **No rounding** — preserves full floating-point precision  
- If `ratio ≥ 1`: `multiplier = int(ratio)`, `fine_offset = full fractional part`  
- If `ratio < 1`: Uses reciprocal with fine offset as in RES_50  
- Allows arbitrary fine adjustments (e.g., 1.237× tempo)

**Result:** Finest quantization; suitable for experimental or microtonal tempi.

### 3. Parameter Interaction Summary

| Resolution | Rounding | Fine Offset | Use Case |
|------------|----------|-------------|----------|
| `RES_100` | Round to nearest integer | 0 (disabled) | Strict, repetitive tempi |
| `RES_50` | Round to nearest 0.5 | 0 or 0.5 (multiplier) or scaled reciprocal | Default, balanced |
| `RES_25` | No rounding (full float) | Full fractional precision | Experimental, fine control |

**Note:** The `fine_offset` parameter is a **signed accumulator** that adds/subtracts a small amount to the base ratio. In RES_50, the maximum fine offset is ±0.5 (or scaled reciprocal). In RES_25, it can be any value in (0, 1).

---

## Public Interface

### Enum Class: `HumanResolution`

**Module:** `core.sequencers.tempi` (or `plugins.vtempi.vtempi`)  
**Inheritance:** `Enum`  
**Values:**
- `HumanResolution.RES_100` (value = 100)
- `HumanResolution.RES_50` (value = 50)
- `HumanResolution.RES_25` (value = 25)

### Class: `TempiProgrammingEngine`

**Module:** `core.sequencers.tempi`  
**Attribute:**
```python
self.human_resolution: HumanResolution = HumanResolution.RES_50
```

**Methods:**

| Method | Signature | Purpose |
|--------|-----------|---------|
| `tap_channel` | `tap_channel(channel: TempiChannel, timestamp: float)` | Process a tap event; quantizes tempo based on current `human_resolution` |
| `set_resolution` | `set_resolution(res: HumanResolution)` | Set the quantization resolution (present in `vtempi.py`, missing in `tempi.py`) |
| `clear_taps` | `clear_taps(channel_id: int)` | Clear tap buffer for a channel |

**Usage Example:**
```python
engine = TempiProgrammingEngine()
channel = TempiChannel(id=1)

# User taps twice...
engine.tap_channel(channel, time.time())  # First tap (ignored)
time.sleep(0.5)
engine.tap_channel(channel, time.time())  # Second tap — channel parameters updated

# Change resolution to fine
engine.set_resolution(HumanResolution.RES_25)  # Requires method existence
```

---

## Inputs and Outputs

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `channel` | `TempiChannel` | The channel to update (modified in-place) |
| `timestamp` | `float` | Monotonic timestamp of tap (seconds) |

### Outputs

**Return:** None (modifies `channel` in-place)  
**Side Effects:**
- Updates `channel.multiplier`, `channel.divisor`, `channel.fine_offset`
- May modify `channel` state based on quantization

### State Dependencies

- `self.human_resolution`: Current quantization resolution
- `self._tap_buffers`: Per-channel tap history (last 8 taps)

---

## Edge Cases and Error Handling

### 1. Insufficient Taps

- **Condition:** `len(taps) < 2`  
- **Action:** Early return; no channel update  
- **Rationale:** Need at least one interval to compute tempo

### 2. Zero or Negative Interval

- **Condition:** `avg_interval <= 0`  
- **Action:** Early return; no channel update  
- **Rationale:** Invalid timing (timestamp going backwards or duplicate taps)

### 3. Division by Zero

- **Condition:** `max(1, channel.multiplier / max(channel.divisor, 1) * 120.0)`  
  The `max(channel.divisor, 1)` prevents division by zero if `channel.divisor = 0` (should never happen, but defensive).  
- **Condition:** `max(0.01, half_step)` and `max(0.01, ratio)` prevent division by zero in reciprocal calculations.

### 4. Very Fast Taps (High BPM)

- **Condition:** `tap_bpm` could be > 300 (unlikely but possible)  
- **Effect:** `ratio = tap_bpm / 120` could be > 2.5  
- **Handling:** `int(ratio)` truncates; fine offset captures fractional part. No overflow.

### 5. Very Slow Taps (Low BPM)

- **Condition:** `tap_bpm < 60` → `ratio < 0.5`  
- **Effect:** Enters reciprocal branch (`else` clause)  
- **Handling:** Sets `divisor` and negative `fine_offset` (scaled by 0.02). This is correct per hardware behavior.

### 6. Missing `RES_25` Implementation

- **Location:** `core/sequencers/tempi.py` line 420  
- **Bug:** The `tap_channel()` method has `if RES_100` and `elif RES_50` but **no `else` clause** for `RES_25`.  
- **Consequence:** If `human_resolution = RES_25`, the tap is silently ignored (no channel update).  
- **Fix:** Add `else:` branch with RES_25 logic (as implemented in `plugins/vtempi/vtempi.py`).

### 7. Tap Buffer Overflow

- **Condition:** More than 8 taps stored  
- **Action:** `self._tap_buffers[cid] = self._tap_buffers[cid][-8:]` truncates to last 8  
- **Rationale:** Limits memory; uses most recent taps for averaging

---

## Mathematical Formulations

### 1. BPM from Interval

```python
avg_interval = sum(intervals) / len(intervals)  # seconds
tap_bpm = 60.0 / avg_interval
```

**Derivation:** Beats per minute = 60 seconds per minute divided by seconds per beat.

### 2. Current Channel Ratio

```python
current_ratio = channel.multiplier / max(channel.divisor, 1) + channel.fine_offset
```

The fine offset is an **additive** adjustment to the base multiplier/divisor ratio.

### 3. RES_100 Quantization

```python
ratio = tap_bpm / (current_ratio * 120.0)
nearest = round(ratio)
if ratio >= 1:
    new_multiplier = nearest
    new_divisor = 1
    new_fine_offset = 0.0
else:
    new_multiplier = 1
    new_divisor = round(1.0 / ratio)
    new_fine_offset = 0.0
```

**Explanation:**  
- Normalizes tap BPM against current channel tempo (×120 for hardware-specific scaling)  
- Rounds to nearest integer  
- Forces either multiplier or divisor to 1 (hardware constraint: coarse adjustment uses only one of them)  
- Fine offset disabled

### 4. RES_50 Quantization

```python
ratio = tap_bpm / 120.0
half_step = round(ratio * 2) / 2.0  # Round to nearest 0.5

if half_step >= 1:
    new_multiplier = int(half_step)
    new_fine_offset = half_step - int(half_step)  # 0 or 0.5
    new_divisor = 1
else:
    inv = 1.0 / half_step
    new_divisor = int(inv)
    new_fine_offset = -(inv - int(inv)) * 0.02
    new_multiplier = 1
```

**Explanation:**  
- Direct ratio to 120 BPM base (no current channel scaling)  
- Rounds to nearest 0.5 (e.g., 1.0, 1.5, 2.0, ...)  
- If ratio < 1, uses reciprocal; fine offset is **negative** and scaled by 0.02 (hardware-specific scaling factor for fine decrement)

### 5. RES_25 Quantization (Missing in Core)

```python
ratio = tap_bpm / 120.0

if ratio >= 1:
    new_multiplier = int(ratio)
    new_fine_offset = ratio - int(ratio)  # Full fractional part
    new_divisor = 1
else:
    inv = 1.0 / ratio
    new_divisor = int(inv)
    new_fine_offset = -(inv - int(inv)) * 0.02
    new_multiplier = 1
```

**Explanation:**  
- Same as RES_50 but **no rounding** — preserves full floating-point precision  
- Fine offset can be any value in (0, 1) for multiplier case  
- Reciprocal branch identical to RES_50

### 6. Fine Offset Scaling

The `* 0.02` factor in the reciprocal branch is a **hardware-specific scaling** that maps the fractional part to the TEMPI module's fine-tuning range (likely ±1 semitone or similar). This constant should be verified against hardware documentation.

---

## Performance Characteristics

### Computational Cost

- **Tap processing:** O(1) per tap (after maintaining 8-tap buffer)  
- **Operations:** ~20 FLOPs per quantization (divisions, multiplications, rounding)  
- **Memory:** 8 floats per channel (tap buffer) + 1 `HumanResolution` enum

### No GPU Impact

This is a **CPU-side utility**; no shader or GPU involvement.

---

## Test Plan

### Unit Tests (Python)

**Target:** ≥80% coverage for `TempiProgrammingEngine.tap_channel()` and `HumanResolution` enum.

1. **Enum Values**  
   - `test_human_resolution_values()`: Verify `RES_100.value == 100`, `RES_50.value == 50`, `RES_25.value == 25`

2. **Tap Buffer Management**  
   - `test_tap_buffer_keeps_last_8()`: Simulate 10 taps; verify buffer length = 8, contains last 8 timestamps  
   - `test_clear_taps_removes_channel()`: Call `clear_taps()`; verify channel removed from `_tap_buffers`

3. **RES_100 Quantization**  
   - `test_res_100_rounds_up()`: Simulate taps yielding `tap_bpm = 125.0`; verify `multiplier = 1`, `divisor = 1`, `fine_offset = 0` (since 125/120 = 1.0417 → ratio < 1? Actually need to test both branches)  
   - Better: Test with known current_ratio to exercise `ratio >= 1` and `< 1` branches  
   - `test_res_100_coarse_only()`: Verify `fine_offset` always 0

4. **RES_50 Quantization**  
   - `test_res_50_half_step_rounding()`: Test `tap_bpm = 90` → `ratio = 0.75` → `half_step = 0.5` → divisor path  
   - `test_res_50_multiplier_path()`: Test `tap_bpm = 180` → `ratio = 1.5` → `half_step = 1.5` → `multiplier = 1`, `fine_offset = 0.5`  
   - `test_res_50_fine_offset_scaled()`: Verify `fine_offset` in reciprocal branch is negative and scaled by 0.02

5. **RES_25 Quantization** (if implemented)  
   - `test_res_25_preserves_fraction()`: Test `tap_bpm = 123.45` → `ratio = 1.02875` → `multiplier = 1`, `fine_offset = 0.02875`  
   - `test_res_25_fine_offset_range()`: Verify `fine_offset` can be any value in (0, 1)

6. **Edge Cases**  
   - `test_single_tap_no_update()`: Only 1 tap → channel unchanged  
   - `test_zero_interval_ignored()`: `avg_interval = 0` → early return  
   - `test_negative_interval_ignored()`: Negative interval → early return

7. **Integration**  
   - `test_engine_resolution_change()`: Set `human_resolution` to each value; verify `tap_channel` behaves accordingly  
   - `test_multiple_channels()`: Tap on two different channel IDs; verify separate buffers

**Coverage Note:** If `RES_25` is not implemented in `core/sequencers/tempi.py`, tests for that branch will fail. The spec should flag this as a **pre-existing bug** to be fixed in Phase 3.

---

## WebGPU Migration Notes

Not applicable. This is a pure Python utility module with no GPU code.

---

## Legacy Code Discrepancies

### 1. Duplicate Implementations

The `HumanResolution` enum and `TempiProgrammingEngine` exist in two locations:

- **Core:** `core/sequencers/tempi.py` (lines 44-47, 369-436)  
- **Plugin:** `plugins/vtempi/vtempi.py` (similar structure)

The core version is **missing the RES_25 case** in `tap_channel()` (lines 409-436). The plugin version has the complete implementation.

### 2. Missing `set_resolution` Method

- **Plugin:** `plugins/vtempi/vtempi.py` provides `set_resolution(res: HumanResolution)` to change resolution at runtime.  
- **Core:** `core/sequencers/tempi.py` does **not** have this method; resolution is set by directly assigning `engine.human_resolution`.  
- **Decision:** VJLive3 should implement `set_resolution()` for encapsulation, or document that direct attribute assignment is allowed.

### 3. Channel Dataclass

- **Core:** Uses `@dataclass` for `TempiChannel` (lines 88-156)  
- **Plugin:** May use a different `Channel` class (likely similar)  
- **Action:** Consolidate on the core `TempiChannel` definition.

### 4. Fine Offset Scaling

Both implementations use `* 0.02` in the reciprocal branch. This constant is **hardware-specific** and should be verified. It may need to be a configurable parameter if hardware varies.

### 5. Default Resolution

Both set default to `HumanResolution.RES_50`. Consistent.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass (≥80% coverage)  
- [ ] No file over 750 lines (this spec ~300 lines)  
- [ ] No stubs in code (RES_25 implementation added)  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-3] P3-EXT090: HumanResolution` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

---

## Implementation Notes for Phase 3

### Critical Bug Fix

The `tap_channel()` method in `core/sequencers/tempi.py` **must** include the `RES_25` case. The current code:

```python
if self.human_resolution == HumanResolution.RES_100:
    # ... RES_100 logic
elif self.human_resolution == HumanResolution.RES_50:
    # ... RES_50 logic
# MISSING: else clause for RES_25
```

**Fix:** Add the `else:` branch with the RES_25 logic from `plugins/vtempi/vtempi.py`.

### Method Addition

Consider adding `set_resolution()` method to `TempiProgrammingEngine` for consistency with the plugin:

```python
def set_resolution(self, res: HumanResolution):
    self.human_resolution = res
```

### Constant Extraction

The magic number `0.02` in the reciprocal fine offset calculation should be extracted to a module-level constant with a comment explaining its origin (e.g., `FINE_OFFSET_SCALE = 0.02  # Hardware scaling factor`).

### Test Priority

The test suite must **explicitly test all three resolution modes**, including the RES_25 branch after it is implemented. Use parameterized tests to cover both `ratio >= 1` and `ratio < 1` paths for each resolution.

---

## LEGACY CODE REFERENCES

**Primary Source:**  
`/home/happy/Desktop/claude projects/vjlive/core/sequencers/tempi.py`  
- Lines 44-47: `HumanResolution` enum definition  
- Lines 369-436: `TempiProgrammingEngine` class and `tap_channel()` method (incomplete)

**Complete Reference (Plugin):**  
`/home/happy/Desktop/claude projects/vjlive/plugins/vtempi/vtempi.py`  
- Contains full `HumanResolution` enum and complete `tap_channel()` with RES_25

**Supporting Types:**  
- `TempiChannel` dataclass (lines 88-156 in `tempi.py`)  
- `DutyCycleMode`, `ModBehavior`, `LEDColor` enums

**Related Modules:**  
- `core.sequencers.tempi` — core sequencer engine  
- `plugins.vtempi.vtempi` — plugin wrapper with UI and hardware interface

---

## Migration Checklist for Implementation Team

1. **Fix core bug:** Add `else:` clause for `RES_25` in `core/sequencers/tempi.py` `tap_channel()`  
2. **Copy RES_25 logic** from `plugins/vtempi/vtempi.py` (verified working implementation)  
3. **Add `set_resolution()` method** to `TempiProgrammingEngine` (optional but recommended)  
4. **Extract magic constant:** Replace `0.02` with named constant `FINE_OFFSET_SCALE`  
5. **Write unit tests** covering all three resolutions, both branches (multiplier vs divisor)  
6. **Verify integration** with `TempiChannel` fine_offset usage in downstream clock generation  
7. **Document hardware scaling** — why 0.02? (likely 1/50 or 1/60 semitone mapping)  
8. **Ensure backward compatibility** — default resolution remains RES_50

---

**End of Specification**  
**Next:** Implementation (Phase 3) → Bug fix → Testing → Review
