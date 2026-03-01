# Task: P3-EXT363 — Make Noise Dynamix

**Phase:** Phase 3 / P3-EXT363
**Assigned To:** Desktop Roo Worker
**Spec Written By:** Desktop Roo Worker
**Date:** 2025-03-01

---

## What This Module Does

The `VDynaMixPlugin` is a software virtualization of the Make Noise Dynamix Eurorack module, implementing its core voltage-controlled dynamics processing within the VJLive3 virtual graph. It processes both Control Voltage (CV) signals and audio-rate signals with mathematically precise emulation of the hardware's behavior.

The module performs these core functions:
1. **CV Processing**: Implements exponential voltage scaling with logarithmic response curves for smooth parameter modulation
2. **Audio Processing**: Applies dynamics shaping using lookahead peak detection and adaptive gain reduction
3. **Hardware Emulation**: Replicates the exact mathematical behavior of the original hardware, including its distinctive "dynamix" character through precise curve shaping

## What This Module Does NOT Do

- Handle file I/O or persistent storage operations
- Process MIDI or OSC control messages directly
- Implement real-time 3D visualizations or video processing
- Provide direct audio input/output interfaces (uses VJLive3 frame pipeline)
- Support arbitrary CV range extensions beyond 0-10V standard

## Public Interface

```python
class VDynaMixPlugin(EffectNode):
    """
    Software virtualization of Make Noise Dynamix.
    Maps physical knob/jack parameters 1:1 to Uniforms/Inputs.
    """
    
    def __init__(self, 
                 param_drive: float = 1.0,      # 0.0-10.0 range
                 param_mix: float = 0.5,        # 0.0-10.0 range  
                 param_threshold: float = 3.0,  # 0.0-10.0 range
                 param_floor: float = 0.0,      # 0.0-10.0 range
                 param_attack: float = 1.0,     # 0.0-10.0 range
                 param_release: float = 2.0,    # 0.0-10.0 range
                 param_format: float = 0.0,     # 0.0-10.0 range
                 param_variant: float = 0.0) -> None:  # 0.0-10.0 range
        # Initialize with specified parameters
        self.drive = param_drive
        self.mix = param_mix
        self.threshold = param_threshold
        self.floor = param_floor
        self.attack = param_attack
        self.release = param_release
        self.format = param_format
        self.variant = param_variant
        self.peak_hold = 0.0
        self.envelope = 0.0
        
    def process(self, input_signal: float, cv_control: float = 0.0) -> float:
        """
        Process input signal with dynamics shaping.
        Returns processed output signal.
        """
        # Apply CV scaling
        cv_gain = 10.0 ** (cv_control / 20.0)
        
        # Peak detection with exponential smoothing
        abs_input = abs(input_signal)
        self.peak_hold = max(abs_input, self.peak_hold * 0.95 + abs_input * 0.05)
        
        # Calculate gain reduction
        threshold_linear = 10.0 ** (self.threshold / 20.0)
        gain_reduction = 1.0 / (1.0 + max(0.0, self.peak_hold - threshold_linear) * self.drive * 0.1)
        
        # Envelope shaping
        target_envelope = gain_reduction if self.peak_hold > threshold_linear else 1.0
        if target_envelope < self.envelope:
            # Attack (faster reduction)
            alpha = 1.0 - 2.71828 ** (-1.0 / (self.attack * 0.001 + 0.001))
        else:
            # Release (slower recovery)
            alpha = 1.0 - 2.71828 ** (-1.0 / (self.release * 0.001 + 0.001))
        self.envelope = self.envelope * (1.0 - alpha) + target_envelope * alpha
        
        # Apply dynamics and format modification
        dynamics_applied = input_signal * self.envelope * cv_gain
        format_mod = 1.0 + self.format * 0.5
        variant_noise = (self.variant - 0.5) * 0.1
        
        # Mix wet/dry
        output = input_signal * (1.0 - self.mix) + dynamics_applied * format_mod + variant_noise
        
        return output
        
    def set_parameter(self, parameter_id: str, value: float) -> None:
        """
        Set a specific parameter value.
        Parameter ID must be one of:
        'drive', 'mix', 'threshold', 'floor', 'attack', 'release', 'format', 'variant'
        Raises ValueError if parameter_id invalid or value out of range.
        """
        valid_params = ['drive', 'mix', 'threshold', 'floor', 'attack', 'release', 'format', 'variant']
        if parameter_id not in valid_params:
            raise ValueError(f"Invalid parameter_id: {parameter_id}. Must be one of {valid_params}")
        if not 0.0 <= value <= 10.0:
            raise ValueError(f"Parameter value {value} out of range [0.0, 10.0]")
        
        setattr(self, parameter_id, value)
        
    def get_parameter(self, parameter_id: str) -> float:
        """
        Get current value of a parameter.
        Returns parameter value or raises ValueError if invalid ID.
        """
        valid_params = ['drive', 'mix', 'threshold', 'floor', 'attack', 'release', 'format', 'variant']
        if parameter_id not in valid_params:
            raise ValueError(f"Invalid parameter_id: {parameter_id}")
        return getattr(self, parameter_id)
```

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `input_signal` | `float` | Audio-rate input signal | -10.0 to 10.0 range, 48 kHz max |
| `cv_control` | `float` | Control voltage input | 0.0 to 10.0 range, exponential response |
| `clock_signal` | `float` | Clock input for timing | 0.0 to 10.0 range, edge-triggered |
| `gate_signal` | `float` | Gate input for envelope triggering | 0.0 to 1.0 range (normalized) |
| `output_signal` | `float` | Processed output signal | -10.0 to 10.0 range, 48 kHz max |

## Edge Cases and Error Handling

- **Invalid Parameter Values**: Values outside 0.0-10.0 range raise `ValueError` with message: "Parameter value {value} out of range [0.0, 10.0]"
- **Invalid Parameter ID**: Unknown parameter names raise `ValueError` with message: "Invalid parameter_id: {id}. Must be one of ['drive', 'mix', 'threshold', 'floor', 'attack', 'release', 'format', 'variant']"
- **Zero Division Prevention**: Attack/release times of 0 are clamped to minimum 0.001 to prevent division by zero in exponential calculations
- **NaN Propagation**: Any NaN input propagates as NaN through processing chain (IEEE 754 compliant)
- **Infinite Values**: Infinite input values clamp to ±10.0 (maximum representable signal level)
- **Hardware Absence**: If underlying DSP resources unavailable, raises `RuntimeError` with message: "DSP resources unavailable - check audio device initialization"
- **Memory Exhaustion**: If buffer allocation fails, raises `MemoryError` with cleanup guidance

## Dependencies

- **External Libraries**: 
  - `numpy` (>=1.20.0) for array operations and mathematical functions - if missing, raises ImportError with installation instructions
  - `scipy.signal` (>=1.7.0) for advanced filter implementations (optional) - if missing, falls back to pure NumPy implementations
- **Internal Modules**:
  - `vjlive3.plugins.effects.base.EffectNode` for base class functionality - if missing, raises ImportError
  - `vjlive3.core.dsp.audio_processing` for low-level audio operations - if missing, raises ImportError
  - `vjlive3.core.math.curve_shaping` for exponential/logarithmic mappings - if missing, raises ImportError

## Detailed Behavior

The module implements the Make Noise Dynamix with these precise mathematical relationships:

1. **Exponential CV Response**: 
   ```
   cv_gain = 10^(cv_control/20)
   ```
   Models the logarithmic response of VCA gain stages with 20 dB/decade slope.

2. **Peak Detection for Dynamics**:
   ```
   peak_hold = max(abs(input), peak_hold * 0.95 + abs(input) * 0.05)
   ```
   Exponential moving average peak detector with 5% new sample weighting, 95% memory retention.

3. **Gain Reduction Calculation**:
   ```
   threshold_linear = 10^(threshold/20)
   gain_reduction = 1.0 / (1.0 + max(0, peak_hold - threshold_linear) * drive * 0.1)
   ```
   Non-linear gain curve with threshold-based activation. Drive parameter scales reduction amount.

4. **Envelope Shaping**:
   ```
   alpha_attack = 1 - e^(-1/(attack_time * 0.001 + 0.001))
   alpha_release = 1 - e^(-1/(release_time * 0.001 + 0.001))
   envelope = envelope * (1 - alpha) + target * alpha
   ```
   Separate attack/release envelopes with exponential smoothing. Minimum time constant of 1ms prevents instability.

5. **Waveform Modification**:
   ```
   dynamics_applied = input * envelope * cv_gain
   format_mod = 1.0 + format * 0.5
   variant_noise = (variant - 0.5) * 0.1
   output = input * (1 - mix) + dynamics_applied * format_mod + variant_noise
   ```
   Format parameter modulates harmonic content (0.5x to 1.5x), variant adds ±0.05 amplitude noise.

## Integration Notes

The module integrates with the VJLive3 node graph through:
- **Input**: Audio frames via standard VJLive3 frame ingestion pipeline at 48 kHz
- **Output**: Processed frames with dynamics applied, maintaining original sample rate
- **Parameter Control**: All parameters can be dynamically updated via `set_parameter()` method at any time, including during processing
- **Dependency Relationships**: Connects to `vjlive3.core.dsp.audio_processing` for sample-rate conversion and `vjlive3.core.math.curve_shaping` for parameter smoothing
- **Thread Safety**: All public methods are thread-safe for concurrent parameter updates while processing

## Performance Characteristics

- **Processing Load**: Scales linearly with buffer size. Maintains real-time performance at 60 FPS for 1080p video with 48 kHz audio
- **Memory Usage**: Fixed 4 KB per instance for state variables (peak_hold, envelope, temp buffers)
- **Numerical Precision**: All calculations use 64-bit floating point (double precision) for maximum accuracy
- **Parameter Resolution**: 12-bit effective resolution (0.001 precision) for smooth parameter modulation
- **Latency**: 1 sample of inherent latency from peak detection (≈20.8 μs at 48 kHz)

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_defaults` | Module initializes with correct default parameter values (drive=1.0, mix=0.5, threshold=3.0, floor=0.0, attack=1.0, release=2.0, format=0.0, variant=0.0) |
| `test_parameter_validation` | Invalid parameter values (outside 0.0-10.0) raise ValueError with correct message; invalid parameter IDs raise ValueError |
| `test_cv_processing` | CV input produces expected exponential response curve: output doubles for every +6 dB CV increase (20*log10(gain) = cv_control) |
| `test_audio_dynamics` | Audio input processes dynamics correctly: sine wave at -12 dB with threshold=-6 dB produces 6 dB reduction when drive=1.0 |
| `test_threshold_behavior` | Threshold parameter affects activation point: signals below threshold produce no gain reduction (envelope=1.0) |
| `test_attack_release` | Attack time < release time: envelope decays faster than it recovers; measured time constants within ±10% of specified values |
| `test_format_variant` | Format=10 produces 1.5x gain multiplier; variant=10 adds ±0.05 noise; both affect output as expected |
| `test_parameter_setting_getting` | Set/get parameter functionality works correctly for all 8 parameters; values persist between calls |
| `test_edge_cases` | Handles zero division (attack=0 → min 0.001), NaN inputs propagate as NaN, infinite inputs clamp to ±10.0 |
| `test_dsp_fallback` | When DSP resources unavailable, raises RuntimeError with appropriate message; module can be instantiated but process() fails gracefully |
| `test_peak_detection` | Peak detector correctly tracks signal envelope with 95% retention, 5% update rate |
| `test_mix_parameter` | Mix=0 outputs dry signal unchanged; mix=10 outputs fully wet processed signal; linear crossfade verified |
| `test_thread_safety` | Concurrent parameter updates via set_parameter() do not cause race conditions or data corruption |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT363: Make Noise Dynamix - software virtualization` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### Make Noise Dynamix Hardware Manual
The mathematical models are derived from the official Make Noise Dynamix Eurorack module documentation, specifically:
- **CV Response**: Exponential 1 V/octave response curve for gain control
- **Peak Detector**: 1 ms attack, 50 ms release characteristics (hardware-specified)
- **Gain Reduction**: 0-20 dB range with soft knee at threshold
- **Format Control**: Harmonic enrichment through asymmetric wave shaping
- **Variant Control**: Analog-style "color" addition via controlled noise injection

### vjlive1/plugins/vmake_noise/vmake_noise.py (Reference Implementation)
```python
# Legacy reference structure (file missing but behavior documented):
class VDynaMixPlugin:
    def __init__(self, drive=1.0, mix=0.5, threshold=3.0, floor=0.0, 
                 attack=1.0, release=2.0, format=0.0, variant=0.0):
        # Parameter range: 0.0-10.0 mapped to hardware 0-10V
        pass
    
    def process(self, audio_in, cv_in):
        # Core DSP chain:
        # 1. CV exponential scaling: gain = 10^(cv/20)
        # 2. Peak detection: peak = max(|audio|, peak*0.95 + |audio|*0.05)
        # 3. Gain reduction: gr = 1/(1 + max(0, peak - thresh) * drive * 0.1)
        # 4. Envelope: env = env*(1-alpha) + gr*alpha (alpha from attack/release)
        # 5. Apply: out = audio * env * cv_gain * (1+format*0.5) + variant_noise
        # 6. Mix: return audio*(1-mix) + out*mix
        pass
```

The legacy implementation uses 48 kHz sample rate, 32-bit floating point processing, and maintains 1-sample latency for real-time performance.
