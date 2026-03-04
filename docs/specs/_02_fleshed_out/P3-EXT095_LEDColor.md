# P3-EXT095_LEDColor.md

## Task: P3-EXT095 — LEDColor

## Detailed Behavior and Parameter Interactions

### LEDColor Enum Definition
```python
class LEDColor(Enum):
    OFF = "off"
    BLUE = "blue"
    RED = "red"
    GREEN = "green"
    PURPLE = "purple"
    AMBER = "amber"
    PINK = "pink"
    WHITE = "white"
```

### BANK_COLORS Mapping
```python
# Bank index → LED color (per firmware v.31 / René-matched)
BANK_COLORS = {
    0: LEDColor.BLUE,
    1: LEDColor.AMBER,
    2: LEDColor.PINK,
    3: LEDColor.WHITE,
}
```

### TempiLEDState Class
```python
class TempiLEDState:
    """Virtual LED panel mirroring the hardware TEMPI's visual feedback."""
    
    def __init__(self):
        self.state_led: LEDColor = LEDColor.BLUE       # Bank color
        self.state_led_flash: bool = False              # Flash on state change
        self.tempo_led: LEDColor = LEDColor.BLUE        # Blue=free, Green=follow
        self.tempo_led_flash: bool = False
        self.channel_leds: List[LEDColor] = [LEDColor.BLUE] * 6
        self.pgm_a_led: LEDColor = LEDColor.OFF
        self.pgm_a_flash: bool = False
        self.pgm_b_led: LEDColor = LEDColor.OFF
        self.pgm_b_flash: bool = False
        self.mod_led: LEDColor = LEDColor.OFF
```

### LED Color Logic

#### Channel LED State Mapping
```python
def update_channel_leds(self, channels: List[TempiChannel]):
    """Update channel LEDs based on channel state."""
    for i, ch in enumerate(channels):
        if ch.muted:
            self.channel_leds[i] = LEDColor.RED
        elif ch.mod_enabled:
            self.channel_leds[i] = LEDColor.PURPLE
        elif ch.active and ch.clock_high:
            self.channel_leds[i] = LEDColor.BLUE
        else:
            self.channel_leds[i] = LEDColor.OFF
```

#### Bank LED State Mapping
```python
def set_bank(self, bank_index: int):
    self.state_led = BANK_COLORS.get(bank_index, LEDColor.BLUE)
```

#### Channel State Logic
```python
class TempiChannel:
    """Single clock channel with multiplier/divisor, phase, and output state."""
    
    id: int = 0
    # Timing
    multiplier: int = 1       # 1–32 coarse
    divisor: int = 1          # 1–32 coarse
    fine_offset: float = 0.0  # Fine increment/decrement accumulator
    # Phase
    phase_coarse: int = 0     # 0–3 (leading-tempo cycles offset)
    phase_fine: float = 0.0   # Fine phase accumulator
    # Output
    muted: bool = False
    active: bool = True       # Run/stop can disable
    mod_enabled: bool = False
    # Clock state
    duty_cycle: DutyCycleMode = DutyCycleMode.CLOCK_50
    tap_tempo_enabled: bool = False  # Only Ch1
    # Internal
    clock_high: bool = False  # Current output level
```

## Public Interface

### LEDColor Enum
- **OFF**: "off" - LED turned off
- **BLUE**: "blue" - Standard active state
- **RED**: "red" - Error/muted state
- **GREEN**: "green" - Follow mode indicator
- **PURPLE**: "purple" - Modulation enabled
- **AMBER**: "amber" - Bank 1 indicator
- **PINK**: "pink" - Bank 2 indicator
- **WHITE**: "white" - Bank 3 indicator

### TempiLEDState Methods
- **`update_channel_leds(channels: List[TempiChannel])`**: Updates all 6 channel LEDs based on channel states
- **`set_bank(bank_index: int)`**: Sets state LED based on bank index using BANK_COLORS mapping
- **`to_dict() -> dict`**: Serializes LED state for UI consumption

## Inputs and Outputs

### Input Sources
- **TempiChannel objects**: 6 channels with state properties (muted, mod_enabled, active, clock_high)
- **Bank index**: Integer 0-3 for bank selection
- **Internal state**: Flash flags for visual feedback

### Output Destinations
- **Virtual LED panel**: State, tempo, channel, program, and mod LEDs
- **UI serialization**: Dictionary format for frontend display
- **Hardware mirroring**: Virtual state mirrors physical TEMPI hardware

## Edge Cases and Error Handling

### Bank Index Handling
- **Valid range**: 0-3 (4 banks total)
- **Out of range**: Defaults to BLUE (bank 0) via `BANK_COLORS.get(bank_index, LEDColor.BLUE)`
- **Negative indices**: Treated as out of range, defaults to BLUE

### Channel State Precedence
1. **Muted**: Highest priority - RED
2. **Mod enabled**: Second priority - PURPLE
3. **Active + clock_high**: Third priority - BLUE
4. **Default**: OFF

### Flash State Management
- **Flash flags**: Separate boolean for each LED that can flash
- **State changes**: `state_led_flash` triggered on bank changes
- **Program LEDs**: `pgm_a_flash` and `pgm_b_flash` for program changes

## Mathematical Formulations

### LED State Priority Calculation
```
LED_state = 
    RED           if muted
    PURPLE        if mod_enabled and not muted
    BLUE          if active and clock_high and not muted and not mod_enabled
    OFF           otherwise
```

### Bank Color Mapping
```
state_led_color = BANK_COLORS[bank_index] if 0 <= bank_index <= 3 else BLUE
```

### Channel LED Array Initialization
```
channel_leds = [BLUE, BLUE, BLUE, BLUE, BLUE, BLUE]  # 6 channels initialized to BLUE
```

## Performance Characteristics

### Time Complexity
- **Channel LED update**: O(n) where n = 6 channels (constant time)
- **Bank LED update**: O(1) dictionary lookup
- **State serialization**: O(n) for channel LED array conversion

### Space Complexity
- **LED state storage**: 11 LEDColor objects + 11 flash booleans
- **Channel LED array**: Fixed size 6-element list
- **Memory footprint**: Minimal, suitable for real-time operation

### Real-time Suitability
- **Update frequency**: Can handle 1000+ updates per second
- **CPU overhead**: Negligible (< 0.1ms per update cycle)
- **Memory allocation**: No dynamic allocation during updates

## Test Plan

### Unit Tests (100% coverage target)
1. **LEDColor Enum Tests**
   - Test all 8 enum values and their string representations
   - Verify enum ordering and uniqueness

2. **BANK_COLORS Mapping Tests**
   - Test all 4 bank indices map to correct colors
   - Test out-of-range indices default to BLUE
   - Test negative indices default to BLUE

3. **TempiLEDState Tests**
   - Test initial state initialization
   - Test `update_channel_leds()` with various channel state combinations
   - Test `set_bank()` with valid and invalid indices
   - Test `to_dict()` serialization accuracy

4. **Channel State Priority Tests**
   - Test muted state overrides all other states (RED)
   - Test mod_enabled state overrides active state (PURPLE)
   - Test active + clock_high state (BLUE)
   - Test default OFF state

5. **Flash State Tests**
   - Test flash flags are independent of LED colors
   - Test flash state persistence across updates

### Integration Tests
1. **Full LED Panel Update**
   - Simulate complete TEMPI state with all channels
   - Verify all LEDs update correctly based on channel states
   - Test bank switching behavior

2. **Hardware Mirroring Tests**
   - Verify virtual state matches expected hardware behavior
   - Test edge cases and error conditions

### Visual Regression Tests
1. **LED Color Verification**
   - Capture UI state for various TEMPI configurations
   - Verify LED colors match expected values

2. **Flash Animation Tests**
   - Verify flash states create expected visual effects
   - Test flash timing and synchronization

## Definition of Done

### Technical Requirements
- [ ] All 8 LEDColor enum values implemented and documented
- [ ] BANK_COLORS mapping correctly handles all 4 banks
- [ ] TempiLEDState class fully implemented with all methods
- [ ] Channel state priority logic correctly implemented
- [ ] Flash state management working independently
- [ ] Serialization to dictionary format working correctly
- [ ] Edge cases (invalid bank indices) handled gracefully
- [ ] Performance characteristics meet real-time requirements
- [ ] 100% unit test coverage achieved
- [ ] Integration tests pass for full LED panel updates
- [ ] Visual regression tests pass

### Documentation Requirements
- [ ] Complete technical specification with all sections filled
- [ ] Mathematical formulations for LED state logic
- [ ] Performance analysis with complexity calculations
- [ ] Test plan with comprehensive coverage strategy
- [ ] Edge case documentation with error handling
- [ ] Public interface documentation

### Quality Requirements
- [ ] Code follows project style guidelines
- [ ] All tests pass and maintain 100% coverage
- [ ] No regressions in existing functionality
- [ ] Documentation is accurate and complete
- [ ] Performance meets real-time requirements

---

*Last Updated: 2026-03-03*  
*Spec Author: desktop-roo*  
*Task ID: P3-EXT095*