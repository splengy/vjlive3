# Spec: P3-EXT089 — HorizontalWaveEffect

## Overview
The HorizontalWaveEffect is a wave distortion effect that creates horizontal wave patterns across video frames. It's a convenience wrapper around the VSwsEffect class that provides a simplified interface for horizontal wave distortion.

## Technical Details

### What This Module Does
The HorizontalWaveEffect applies a horizontal wave distortion to video frames using a sine wave pattern. The wave travels horizontally across the frame, with configurable parameters controlling wave properties.

### What This Module Does NOT Do
- Does not create vertical waves (use VerticalWaveEffect for that)
- Does not create spiral waves (use SpiralWaveEffect for that)
- Does not create ripple effects (use RippleEffect for that)
- Does not create spiral wave effects (use SpiralWaveEffect for that)

### Detailed Behavior and Parameter Interactions
The effect generates a horizontal wave distortion where:
- The wave direction is fixed to 0.0 (horizontal)
- Wave amplitude and frequency control the visual pattern
- Decay controls how quickly the wave dissipates
- Phase offset can be used to animate the wave over time

### Public Interface
```python
class HorizontalWaveEffect(VSwsEffect):
    """Convenience class for horizontal wave distortion."""
    
    def __init__(self, name: str = 'horizontal_wave'):
        super().__init__(name)
        self.parameters['direction'] = 0.0
```

### Inputs and Outputs
- **Input**: Video frame buffer with pixel data
- **Output**: Distorted video frame buffer with horizontal wave effect applied
- **Parameters**:
  - `direction`: Wave direction (0.0 = horizontal, fixed)
  - `frequency`: Wave frequency (default: 4.0)
  - `amplitude`: Wave amplitude (default: 1.0)
  - `decay`: Wave decay rate (default: 4.0)
  - `phase`: Phase offset for animation (default: 0.0)

### Edge Cases and Error Handling
- If `frequency` is 0, the effect becomes static (no movement)
- If `amplitude` is 0, the effect has no distortion
- If `decay` is 0, the effect is very short-lived
- Invalid parameter values are clamped to valid ranges

### Mathematical Formulation
The horizontal wave distortion is calculated using a sine wave function:
```
distortion_x = amplitude * sin(2 * π * frequency * x + phase) * exp(-decay * y)
```
Where:
- `x`, `y` are normalized coordinates (0-1)
- `amplitude` controls wave height
- `frequency` controls how many waves per unit distance
- `decay` controls exponential dissipation
- `phase` allows for animation

### Performance Characteristics
- Moderate computational cost
- Real-time performance achievable on modern hardware
- Memory usage proportional to video frame size
- Can be optimized using GPU shaders

### Test Plan
- Verify basic wave distortion works
- Test parameter boundaries (0 values, extreme values)
- Test animation with phase offset
- Verify no visual artifacts or glitches
- Test performance under load

### Performance Characteristics
- CPU-based implementation with moderate resource usage
- Can process 1080p video in real-time on modern CPUs
- GPU acceleration recommended for 4K and higher resolutions

### Edge Cases and Error Handling
- Handle zero division for frequency parameter
- Clamp amplitude and decay values to valid ranges
- Handle edge cases in wave calculation
- Graceful degradation if GPU is unavailable

### Mathematical Formulations
The core wave calculation:
```
wave_displacement = amplitude * sin(2 * π * frequency * x + phase) * exp(-decay * y)
```
Final pixel position:
```
final_x = clamp(x + wave_displacement, 0, 1)
final_y = y
```

### Test Plan
- Verify basic functionality with default parameters
- Test edge cases (zero frequency, zero amplitude)
- Test animation with phase changes
- Verify no visual artifacts or glitches
- Performance test on target hardware

### Definition of Done
- [ ] Spec reviewed and approved
- [ ] All tests pass (minimum 80% coverage)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT089: HorizontalWaveEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

## LEGACY CODE REFERENCES  
### Core Implementation References
1. **VSwsEffect Base Class** - Found in `core/effects/wave.py` and `plugins/vcore/v_sws.py`
2. **HorizontalWaveEffect Convenience Class** - Defined in both `core/effects/wave.py` and `plugins/vcore/v_sws.py`
3. **Parameter Structure** - Inherits `direction`, `frequency`, `amplitude`, `decay`, and `phase` parameters
4. **Wave Calculation Logic** - Uses sine wave with exponential decay for distortion

### Implementation Notes
- The effect inherits from VSwsEffect, so all VSwsEffect functionality applies
- Direction parameter is fixed to 0.0 for horizontal waves
- Additional parameters like amplitude and decay can be added to the parameter set
- Wave calculation uses normalized coordinates (0-1 range)
- The effect can be animated by changing phase parameter over time

## Implementation Roadmap
1. **Parameter Expansion**: Add amplitude, decay, and phase parameters to the effect
2. **Wave Calculation**: Implement sine wave with exponential decay distortion
3. **Animation Support**: Enable phase offset for animated waves
4. **Validation**: Add parameter validation and clamping
5. **Testing**: Implement comprehensive test suite
6. **Integration**: Integrate with existing effect framework

## Legacy Context Summary
The HorizontalWaveEffect is a convenience wrapper that simplifies the creation of horizontal wave distortions. It inherits from VSwsEffect and provides a simplified interface with fixed horizontal direction. The underlying wave calculation uses sine waves with configurable frequency, amplitude, and decay parameters to create visually appealing distortion effects.

## Mathematical Details
The wave distortion effect uses the following mathematical formulation:
- **Wave Function**: `sin(2 * π * frequency * x + phase)`
- **Exponential Decay**: `exp(-decay * y)` 
- **Amplitude Scaling**: `amplitude * wave_function * decay_factor`
- **Coordinate Transformation**: Distorted coordinates are calculated and clamped

## Performance Characteristics
- Real-time performance achievable on modern hardware
- Memory access patterns optimized for sequential processing
- Can be extended to GPU shaders for improved performance
- Effect complexity scales with frame resolution

## Test Plan
1. **Basic Functionality**: Verify wave distortion produces expected visual results
2. **Parameter Validation**: Test edge cases and boundary conditions
3. **Animation**: Verify phase offset creates smooth animation
4. **Performance**: Test under load with high-resolution video
5. **Regression**: Ensure no breaking changes to existing functionality

## Edge Cases
- Zero frequency results in static image
- Zero amplitude results in no distortion
- Negative values are clamped to positive ranges
- Very high decay values cause rapid effect dissipation

## Mathematical Formulation
The core distortion calculation:
```
distortion = amplitude * sin(2 * π * frequency * x + phase) * exp(-decay * y)
```
Where:
- `x`, `y` are normalized texture coordinates
- `amplitude` controls wave height
- `frequency` controls wave density
- `decay` controls exponential dissipation
- `phase` allows for temporal animation

## Performance Characteristics
- CPU-bound effect with moderate performance requirements
- Can process 1080p video in real-time on modern hardware
- GPU implementation recommended for 4K+ resolutions
- Memory usage proportional to frame buffer size

## Implementation Notes
- The effect should inherit all VSwsEffect properties and methods
- Parameter validation should clamp values to valid ranges
- Wave calculation should use efficient mathematical operations
- Animation should be supported through phase parameter updates
- The effect should integrate seamlessly with the existing effect pipeline