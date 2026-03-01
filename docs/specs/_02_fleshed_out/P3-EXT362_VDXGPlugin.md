# Spec: P3-EXT362 — Make Noise DXG

## Task: P3-EXT362 — Make Noise DXG

**Phase:** Phase 3 / P3-H2
**Assigned To:** Desktop Roo Worker
**Spec Written By:** Desktop Roo Worker
**Date:** 2026-03-01

---

## What This Module Does

The `VDXGPlugin` provides a software emulation of the Make Noise DXG Eurorack module, implementing dual-channel lowpass gate (LPG) functionality with vactrol-style dynamics. It processes audio and control voltage signals through two independent channels, each providing lowpass filtering and amplitude control based on envelope response to input signals.

## What It Does NOT Do

- Handle file I/O or persistent storage operations
- Process audio streams or provide sound-reactive capabilities
- Implement real-time 3D text extrusion or volumetric effects
- Provide direct MIDI or OSC control interfaces
- Support arbitrary text rendering outside of video frame context

## Detailed Behavior

The module processes signals through these stages:

1. **Envelope Detection**: Calculates envelope from input signal and strike/CV inputs
2. **Vactrol Response**: Applies exponential attack/release curves to simulate vactrol behavior
3. **Lowpass Filtering**: Filters input signal based on envelope-controlled cutoff frequency
4. **Signal Splitting**: Outputs both filtered (low) and unfiltered (high) components

Key behavioral characteristics:
- Vactrol response creates natural-sounding amplitude and frequency modulation
- Attack/release times controlled by response parameters (0.001-0.3 seconds range)
- Frequency cutoff scales with envelope level (0-5 kHz range)
- Each channel operates independently with separate parameters

## Public Interface

```python
class VDXGPlugin(EffectNode):
    """Make Noise DXG — dual crossover gate with vactrol dynamics."""
    
    def __init__(self) -> None:
        """Initialize DXG with default parameters."""
        self.ch1_freq: float = 0.5  # 0.0-1.0 (cutoff scaling)
        self.ch2_freq: float = 0.5
        self.ch1_response: float = 0.3  # 0.0-1.0 (vactrol speed)
        self.ch2_response: float = 0.3
        
        # Internal state
        self._ch1_env: float = 0.0
        self._ch2_env: float = 0.0
        self._lp_state: List[float] = [0.0, 0.0]
    
    def process(self, dt: float, **kwargs) -> Dict[str, Any]:
        """
        Process audio/control signals through DXG channels.
        
        Args:
            dt: Delta time in seconds since last process call
            kwargs: Input signals with keys:
                - ch1_input, ch2_input: Audio/control signals
                - ch1_strike, ch2_strike: Trigger inputs
                - ch1_cv, ch2_cv: Control voltage inputs
                
        Returns:
            Dictionary with outputs:
                - ch1_low, ch2_low: Filtered lowpass outputs
                - ch1_high, ch2_high: Unfiltered highpass outputs
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize current parameters for state saving."""
        pass
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'VDXGPlugin':
        """Deserialize parameters from saved state."""
        pass
```

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `ch1_input` | `float` | Channel 1 audio/control signal | -1.0 to 1.0 |
| `ch2_input` | `float` | Channel 2 audio/control signal | -1.0 to 1.0 |
| `ch1_strike` | `float` | Channel 1 trigger input | 0.0 to 1.0 |
| `ch2_strike` | `float` | Channel 2 trigger input | 0.0 to 1.0 |
| `ch1_cv` | `float` | Channel 1 control voltage | -1.0 to 1.0 |
| `ch2_cv` | `float` | Channel 2 control voltage | -1.0 to 1.0 |
| `ch1_low` | `float` | Channel 1 filtered output | -1.0 to 1.0 |
| `ch2_low` | `float` | Channel 2 filtered output | -1.0 to 1.0 |
| `ch1_high` | `float` | Channel 1 unfiltered output | -1.0 to 1.0 |
| `ch2_high` | `float` | Channel 2 unfiltered output | -1.0 to 1.0 |

## Edge Cases and Error Handling

- **Zero Input**: When all inputs are zero, outputs should be zero with minimal envelope activity
- **Extreme Values**: Inputs outside -1.0 to 1.0 range should be clamped to prevent distortion
- **Rapid Changes**: Envelope should handle rapid input changes without instability
- **Parameter Bounds**: All parameters should be clamped to valid ranges (0.0-1.0)
- **Division by Zero**: No division operations that could cause divide-by-zero errors

## Performance Characteristics

- **Processing Load**: O(1) per channel, minimal CPU overhead
- **Memory Usage**: Fixed small memory footprint (state variables only)
- **Real-time Performance**: Suitable for 60fps operation with minimal latency
- **Thread Safety**: No shared state between channels, safe for parallel processing

## Dependencies

- `EffectNode` base class from VJLive3 core
- Standard math library for exponential calculations
- No external dependencies required

## Test Plan

*   **Logic (Pytest)**: Send zeroed CV signals and verify the internal physics match the resting state of the DXG hardware.
*   **Parameter Validation**: Test parameter bounds and clamping behavior.
*   **Envelope Response**: Verify vactrol-style attack/release curves match expected behavior.
*   **Signal Processing**: Test audio signal processing with various input patterns.
*   **State Management**: Verify serialization/deserialization of parameters.

## Deliverables
1. `src/vjlive3/plugins/make_noise/dxg.py`
2. Integrated block in the `MakeNoiseRegistry`
3. Complete test suite with 100% code coverage
