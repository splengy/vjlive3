# Task: P3-EXT364 — Make Noise Echophon

**Phase:** Phase 3 / P3-EXT364
**Assigned To:** Desktop Roo Worker
**Spec Written By:** Desktop Roo Worker
**Date:** 2026-03-01

---

## What This Module Does

The `VEchophonPlugin` provides a software emulation of the Make Noise Echophon Eurorack module, implementing pitch-shifting echo with dual feedback loops and freeze capabilities. It processes video frames as signal data, applying temporal effects through delay lines with pitch-bending capabilities, creating evolving echo trails that can be frozen in time.

The module performs these core functions:
1. **Pitch-Shifting Delay**: Applies frequency-domain pitch shifting to delayed signals using phase vocoder techniques
2. **Dual Feedback Loops**: Independent feedback paths for left/right channels with cross-feedback capability
3. **Freeze Function**: Captures and holds current delay buffer state indefinitely
4. **Temporal Manipulation**: Real-time pitch and delay time modulation via CV inputs

## What This Module Does NOT Do

- Handle file I/O or persistent storage operations
- Process audio streams directly (operates on video frame data as carrier)
- Implement real-time 3D visualizations or video effects beyond temporal manipulation
- Provide direct MIDI or OSC control interfaces
- Support external hardware CV inputs without VJLive3 node graph integration

## Public Interface

```python
class VEchophonPlugin(EffectNode):
    """
    Software virtualization of Make Noise Echophon.
    Maps physical knob/jack parameters 1:1 to Uniforms/Inputs.
    """
    
    def __init__(self,
                 param_echo_time: float = 2.0,      # 0.0-10.0 range (0-2000ms)
                 param_feedback: float = 0.5,       # 0.0-10.0 range (0-100%)
                 param_mix: float = 0.5,            # 0.0-10.0 range (0-100%)
                 param_pitch: float = 1.0,          # 0.0-10.0 range (0.5x-2.0x)
                 param_freeze: float = 0.0,         # 0.0-10.0 range (0=off, 10=on)
                 param_scan: float = 0.0,           # 0.0-10.0 range (delay modulation)
                 param_xfade: float = 0.0,          # 0.0-10.0 range (crossfade)
                 param_chaos: float = 0.0) -> None: # 0.0-10.0 range (randomization)
        # Initialize parameters
        self.echo_time = param_echo_time
        self.feedback = param_feedback
        self.mix = param_mix
        self.pitch = param_pitch
        self.freeze = param_freeze
        self.scan = param_scan
        self.xfade = param_xfade
        self.chaos = param_chaos
        
        # Internal state
        self._delay_buffer_ch1: List[np.ndarray] = []
        self._delay_buffer_ch2: List[np.ndarray] = []
        self._buffer_write_pos: int = 0
        self._freeze_active: bool = False
        self._pitch_shift_state: Dict[str, Any] = {}
        
    def process(self, 
                frame: np.ndarray,
                cv_echo_time: float = 0.0,
                cv_feedback: float = 0.0,
                cv_pitch: float = 0.0,
                dt: float = 0.016) -> np.ndarray:
        """
        Process video frame through Echophon effect.
        
        Args:
            frame: Input video frame as HxWxC numpy array (uint8 or float32)
            cv_echo_time: Control voltage for echo time modulation (0.0-10.0)
            cv_feedback: Control voltage for feedback modulation (0.0-10.0)
            cv_pitch: Control voltage for pitch shifting (0.0-10.0)
            dt: Delta time in seconds (default 16.67ms for 60fps)
            
        Returns:
            Processed frame with echo effect applied
        """
        pass
    
    def set_parameter(self, parameter_id: str, value: float) -> None:
        """
        Set a specific parameter value.
        Parameter ID must be one of:
        'echo_time', 'feedback', 'mix', 'pitch', 'freeze', 'scan', 'xfade', 'chaos'
        Raises ValueError if parameter_id invalid or value out of range.
        """
        valid_params = ['echo_time', 'feedback', 'mix', 'pitch', 
                       'freeze', 'scan', 'xfade', 'chaos']
        if parameter_id not in valid_params:
            raise ValueError(f"Invalid parameter_id: {parameter_id}")
        if not 0.0 <= value <= 10.0:
            raise ValueError(f"Parameter value {value} out of range [0.0, 10.0]")
        
        setattr(self, parameter_id, value)
        
        # Handle freeze state transition
        if parameter_id == 'freeze':
            self._freeze_active = (value >= 9.0)  # Threshold at 9.0 for activation
    
    def get_parameter(self, parameter_id: str) -> float:
        """
        Get current value of a parameter.
        Returns parameter value or raises ValueError if invalid ID.
        """
        valid_params = ['echo_time', 'feedback', 'mix', 'pitch', 
                       'freeze', 'scan', 'xfade', 'chaos']
        if parameter_id not in valid_params:
            raise ValueError(f"Invalid parameter_id: {parameter_id}")
        return getattr(self, parameter_id)
    
    def clear_buffers(self) -> None:
        """Clear all delay buffers and reset internal state."""
        self._delay_buffer_ch1.clear()
        self._delay_buffer_ch2.clear()
        self._buffer_write_pos = 0
        self._freeze_active = False
        self._pitch_shift_state.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize current parameters and state for state saving."""
        return {
            'parameters': {
                'echo_time': self.echo_time,
                'feedback': self.feedback,
                'mix': self.mix,
                'pitch': self.pitch,
                'freeze': self.freeze,
                'scan': self.scan,
                'xfade': self.xfade,
                'chaos': self.chaos
            },
            'state': {
                'buffer_write_pos': self._buffer_write_pos,
                'freeze_active': self._freeze_active,
                'pitch_shift_state': self._pitch_shift_state
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VEchophonPlugin':
        """Deserialize parameters from saved state."""
        instance = cls()
        params = data.get('parameters', {})
        for key, value in params.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        state = data.get('state', {})
        instance._buffer_write_pos = state.get('buffer_write_pos', 0)
        instance._freeze_active = state.get('freeze_active', False)
        instance._pitch_shift_state = state.get('pitch_shift_state', {})
        return instance
```

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC) | Height/Width ≥ 64, C=3 or 4, dtype=uint8 or float32 |
| `cv_echo_time` | `float` | Echo time CV modulation | 0.0 to 10.0 range, additive to base parameter |
| `cv_feedback` | `float` | Feedback CV modulation | 0.0 to 10.0 range, additive to base parameter |
| `cv_pitch` | `float` | Pitch shift CV modulation | 0.0 to 10.0 range, additive to base parameter |
| `dt` | `float` | Time delta since last frame | 0.001 to 1.0 seconds (1ms to 1000ms) |
| `output_frame` | `np.ndarray` | Processed output frame | Same shape/dtype as input, values clamped to valid range |

## Edge Cases and Error Handling

- **Invalid Frame Dimensions**: Frames with height/width < 64 pixels raise `ValueError` with message: "Frame dimensions must be at least 64x64, got {H}x{W}"
- **Invalid Channel Count**: Frames with channel count not in {3, 4} raise `ValueError`: "Expected 3 (RGB) or 4 (RGBA) channels, got {C}"
- **Invalid Data Type**: Frames with dtype not in {uint8, float32} raise `TypeError`: "Unsupported frame dtype {dtype}, must be uint8 or float32"
- **Zero Delta Time**: dt < 0.001 seconds clamped to 0.001 to prevent division by zero in time calculations
- **Excessive Delta Time**: dt > 1.0 seconds clamped to 1.0 to prevent buffer overflow
- **Parameter Bounds**: All parameters strictly clamped to [0.0, 10.0] range; out-of-range values raise `ValueError`
- **Freeze State Transition**: Freeze parameter ≥ 9.0 activates freeze; < 9.0 deactivates. Transition is immediate.
- **Buffer Overflow**: Maximum delay buffer size limited to 10 seconds at 60fps (600 frames). Exceeding this reduces echo time proportionally.
- **Memory Exhaustion**: If buffer allocation fails, raises `MemoryError` with suggestion to reduce resolution or echo time
- **NaN Propagation**: NaN values in input frame propagate to output (IEEE 754 compliant) but do not corrupt buffer state
- **Hardware Absence**: No external hardware dependencies; operates purely in software

## Detailed Behavior

The module implements the Make Noise Echophon with these precise mathematical relationships:

### 1. Echo Time Calculation

```
# Base echo time from parameter (0.0-10.0 → 0-2000ms)
base_time_ms = echo_time * 200.0

# CV modulation adds/subtracts (0.0-10.0 → ±1000ms)
cv_offset_ms = (cv_echo_time - 5.0) * 200.0

# Total echo time with clamping
total_time_ms = max(10.0, base_time_ms + cv_offset_ms)
total_time_ms = min(2000.0, total_time_ms)

# Convert to frame count at current dt
frame_delay = total_time_ms / (dt * 1000.0)
buffer_size_frames = ceil(frame_delay * 1.1)  # 10% safety margin
```

Echo time ranges from 10ms to 2000ms, with CV providing ±1000ms modulation. The delay buffer size scales with frame rate to maintain consistent temporal behavior.

### 2. Pitch Shifting Implementation

```
# Pitch ratio from parameter (0.0-10.0 → 0.5x-2.0x)
base_pitch_ratio = 0.5 + (pitch / 10.0) * 1.5

# CV modulation (±50% around base)
cv_pitch_factor = 1.0 + (cv_pitch - 5.0) * 0.1
pitch_ratio = base_pitch_ratio * cv_pitch_factor

# Clamp to valid range
pitch_ratio = max(0.25, min(4.0, pitch_ratio))

# Time-stretch factor for delay buffer read
read_interval = 1.0 / pitch_ratio
```

Pitch shifting uses a phase vocoder approach with overlap-add processing. The pitch ratio determines the time-stretch factor applied to delayed frames before recombination.

### 3. Feedback Loop Calculation

```
# Feedback amount from parameter (0.0-10.0 → 0-100%)
feedback_gain = feedback / 10.0

# CV modulation (±50% around base)
cv_feedback_factor = 1.0 + (cv_feedback - 5.0) * 0.2
effective_feedback = feedback_gain * cv_feedback_factor
effective_feedback = max(0.0, min(0.99, effective_feedback))

# Dual feedback with crossfade
ch1_feedback = effective_feedback * (1.0 - xfade / 10.0)
ch2_feedback = effective_feedback * (xfade / 10.0)
```

Feedback creates the echo tail. Crossfade parameter controls left/right feedback balance. Values near 0.99 can cause infinite reverb; values > 0.99 are clamped.

### 4. Freeze Function

When `freeze ≥ 9.0`:
- Current delay buffer state is locked
- New frames are not written to buffer
- Read pointer continues cycling through frozen buffer
- Feedback is effectively disabled (output = buffer read only)
- Pitch shifting remains active on frozen material

Implementation:
```python
if self._freeze_active:
    # Don't update buffer with new input
    output = self._read_delayed(frame.shape, pitch_ratio, dt)
else:
    # Normal operation: write then read
    self._write_to_buffer(frame)
    output = self._read_delayed(frame.shape, pitch_ratio, dt)
```

### 5. Scan Modulation

```
# Scan parameter adds periodic modulation to echo time
scan_depth = scan / 10.0  # 0.0 to 1.0
scan_rate = 0.5  # Hz (fixed hardware value)

# LFO for scan
scan_phase = (time * scan_rate) % 1.0
scan_modulation = sin(2π * scan_phase) * scan_depth

# Applied to echo time
modulated_echo_time = total_time_ms * (1.0 + scan_modulation * 0.5)
```

Scan creates a slow sinusoidal modulation of delay time, producing Doppler-like pitch shifts.

### 6. Chaos Parameter

```
# Chaos adds random variation to feedback and pitch
chaos_level = chaos / 10.0  # 0.0 to 1.0

# Per-frame random walk
chaos_feedback = effective_feedback + (random() - 0.5) * chaos_level * 0.1
chaos_pitch = pitch_ratio + (random() - 0.5) * chaos_level * 0.05

# Clamp to valid ranges
chaos_feedback = max(0.0, min(0.99, chaos_feedback))
chaos_pitch = max(0.25, min(4.0, chaos_pitch))
```

Chaos introduces controlled randomness, creating unstable, evolving echo textures.

### 7. Mix/Wet-Dry Blending

```
wet_gain = mix / 10.0
dry_gain = 1.0 - wet_gain

output = dry_gain * input_frame + wet_gain * processed_echo
```

Mix controls the balance between original (dry) and effected (wet) signals.

### 8. Frame Processing Pipeline

1. **Pre-processing**: Convert frame to float32 if needed, normalize to [0, 1] or [-1, 1] depending on mode
2. **Delay Buffer Write**: Store current frame at write position (if not frozen)
3. **Pitch-Shifted Read**: Read from buffer with interpolated positions based on pitch ratio
4. **Feedback Application**: Mix read output back into buffer at write position
5. **Post-processing**: Apply xfade, chaos modulation, and final mixing
6. **Output**: Convert back to original dtype and clamp to valid range

### 9. Buffer Management

The delay buffer is implemented as a circular buffer of frames:
```python
buffer_capacity = ceil(max_delay_frames)
buffer = [None] * buffer_capacity
write_pos = 0

def write(frame):
    buffer[write_pos] = frame.copy()
    write_pos = (write_pos + 1) % buffer_capacity

def read(pitch_ratio, current_frame_index):
    # Calculate read position with fractional index for pitch shifting
    read_offset = frame_delay / pitch_ratio
    read_index = (write_pos - read_offset) % buffer_capacity
    # Interpolate between nearest frames for smooth pitch shifting
    idx_floor = floor(read_index)
    idx_ceil = (idx_floor + 1) % buffer_capacity
    alpha = read_index - idx_floor
    frame_low = buffer[idx_floor]
    frame_high = buffer[idx_ceil]
    return frame_low * (1-alpha) + frame_high * alpha
```

## Integration Notes

The module integrates with the VJLive3 node graph through:
- **Input**: Video frames via standard VJLive3 frame ingestion pipeline at project frame rate (typically 60fps)
- **Output**: Processed frames with echo effect applied, maintaining original resolution and color space
- **Parameter Control**: All parameters can be dynamically updated via `set_parameter()` method at any time, including during processing. Changes take effect on the next frame.
- **CV Inputs**: Control voltage inputs allow real-time modulation from other nodes (LFOs, envelopes, sequencers)
- **Dependency Relationships**: 
  - Connects to `vjlive3.core.dsp.frame_processing` for frame format conversions
  - Uses `vjlive3.core.math.interpolation` for pitch-shift interpolation
  - Requires `numpy` for array operations
- **Thread Safety**: All public methods except `process()` are thread-safe for concurrent parameter updates. `process()` is not thread-safe and should be called from a single thread per instance.

## Performance Characteristics

- **Processing Load**: O(H×W×C) per frame with additional overhead for pitch-shifting interpolation (2-4× base cost). Maintains real-time performance at 60 FPS for 1080p (1920×1080×3) frames on modern CPUs.
- **Memory Usage**: Approximately `buffer_capacity × frame_size × 3` bytes. For 1080p at 60fps with 2-second maximum delay: ~2GB. Memory scales linearly with resolution and maximum delay time.
- **Latency**: One frame of inherent latency from circular buffer write-before-read. Additional latency from pitch-shifting interpolation is sub-frame (< 1ms at 60fps).
- **Numerical Precision**: Internal processing uses float32 for performance; final output converted to original dtype with proper clamping.
- **GIL Considerations**: NumPy operations release GIL; multi-threaded processing of multiple Echophon instances is feasible.

## Dependencies

- **External Libraries**:
  - `numpy` (>=1.20.0) for array operations and mathematical functions - if missing, raises `ImportError` with message: "numpy is required for VEchophonPlugin"
  - `scipy` (>=1.7.0) for advanced interpolation (optional) - if missing, falls back to linear interpolation using pure NumPy
- **Internal Modules**:
  - `vjlive3.plugins.effects.base.EffectNode` for base class functionality - if missing, raises `ImportError`
  - `vjlive3.core.dsp.frame_processing` for frame format conversions - if missing, raises `ImportError`
  - `vjlive3.core.math.interpolation` for pitch-shift interpolation - if missing, falls back to built-in linear interpolation

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_defaults` | Module initializes with correct default parameter values (echo_time=2.0, feedback=0.5, mix=0.5, pitch=1.0, freeze=0.0, scan=0.0, xfade=0.0, chaos=0.0) |
| `test_parameter_validation` | Invalid parameter values (outside 0.0-10.0) raise ValueError with correct message; invalid parameter IDs raise ValueError |
| `test_echo_time_range` | Echo time parameter correctly maps to 10-2000ms delay; CV modulation adds ±1000ms; values clamped to valid range |
| `test_feedback_gain` | Feedback parameter creates appropriate decay envelope; 0.0 = no feedback, 0.5 = moderate decay, 0.99 = long reverb-like tail |
| `test_pitch_shifting` | Pitch parameter changes playback speed without altering buffer timing; 0.5 = octave down, 2.0 = octave up; CV modulation works correctly |
| `test_freeze_activation` | Freeze parameter ≥ 9.0 locks buffer state; new frames stop writing; read continues; deactivation resumes normal operation |
| `test_scan_modulation` | Scan parameter creates sinusoidal echo time modulation at 0.5Hz; depth proportional to scan value |
| `test_chaos_behavior` | Chaos parameter adds random variation to feedback and pitch; higher values create more unstable output |
| `test_xfade_crossfeedback` | Xfade parameter smoothly transitions feedback from ch1-only (0.0) to ch2-only (10.0) with cross-mixing |
| `test_mix_parameter` | Mix=0 outputs dry signal unchanged; mix=10 outputs fully wet processed signal; linear crossfade verified |
| `test_buffer_management` | Circular buffer correctly handles wrap-around; buffer size matches calculated capacity; no data corruption at boundaries |
| `test_pitch_shift_interpolation` | Pitch-shifted read produces smooth results without artifacts; fractional indices interpolate correctly between frames |
| `test_frame_format_conversion` | Input frames with uint8 dtype properly normalized and converted; output converted back with correct clamping |
| `test_invalid_frame_size` | Frames with dimensions < 64×64 raise ValueError; frames with invalid channel count raise ValueError |
| `test_dt_clamping` | dt values < 0.001 clamped to 0.001; dt values > 1.0 clamped to 1.0; warning logged |
| `test_state_serialization` | to_dict() and from_dict() correctly preserve all parameters and internal state; freeze state preserved |
| `test_clear_buffers` | clear_buffers() resets all internal state and empties delay buffers |
| `test_nan_propagation` | NaN values in input propagate to output without crashing; buffer state remains valid |
| `test_thread_safety_params` | Concurrent set_parameter() calls do not cause race conditions or data corruption |
| `test_edge_case_zero_input` | Zero-input frames produce zero output with proper mixing; no buffer corruption |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT364: Make Noise Echophon - software virtualization` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### Make Noise Echophon Hardware Manual
The mathematical models are derived from the official Make Noise Echophon Eurorack module documentation, specifically:
- **Echo Time**: 10ms to 2000ms range with continuous control
- **Pitch Shifting**: 0.5x to 2.0x playback speed with formant preservation
- **Feedback**: 0% to 100% with independent left/right controls
- **Freeze**: Captures delay buffer state and holds indefinitely
- **Scan**: Low-frequency oscillator (0.5Hz) modulating delay time for chorusing effects
- **Chaos**: Introduces random variation in feedback and pitch for evolving textures

### vjlive1/plugins/vechophon/vechophon.py (Reference Implementation)
```python
# Legacy reference structure from VJlive-2:
class EchophonEffect:
    """
    Make Noise Echophon — Pitch Shifting Echo.
    Video frames as signal, temporal effects as pitch/delay.
    """
    
    def __init__(self):
        # Parameters in 0.0-10.0 range
        self.echo_time = 2.0      # 0-2000ms
        self.feedback = 0.5       # 0-100%
        self.mix = 0.5            # 0-100%
        self.pitch = 1.0          # 0.5x-2.0x
        self.freeze = 0.0         # 0=off, 10=on
        self.scan = 0.0           # delay modulation depth
        self.xfade = 0.0          # crossfade between channels
        self.chaos = 0.0          # randomization amount
        
        # State
        self.buffer = []
        self.write_pos = 0
        self.freeze_active = False
        
    def process_frame(self, frame, dt):
        # 1. Calculate effective parameters with CV modulation
        echo_ms = self.echo_time * 200.0  # 0-2000ms
        pitch_ratio = 0.5 + (self.pitch / 10.0) * 1.5
        fb_gain = self.feedback / 10.0
        
        # 2. Handle freeze state
        if self.freeze >= 9.0:
            # Don't write new frames, only read
            output = self._read_buffer(frame.shape, pitch_ratio)
            return output * self.mix + frame * (1.0 - self.mix)
            
        # 3. Write current frame to buffer
        self._write_buffer(frame)
        
        # 4. Read with pitch-shifting interpolation
        delayed = self._read_buffer(frame.shape, pitch_ratio)
        
        # 5. Apply feedback (mix delayed signal back into buffer)
        if fb_gain > 0:
            self._mix_into_buffer(delayed * fb_gain)
            
        # 6. Mix wet/dry and return
        output = delayed * self.mix + frame * (1.0 - self.mix)
        return output
    
    def _read_buffer(self, shape, pitch_ratio):
        # Calculate read position with pitch-shift offset
        frame_delay = self.echo_time * 200.0 / (dt * 1000.0)
        read_offset = frame_delay / pitch_ratio
        read_pos = (self.write_pos - read_offset) % len(self.buffer)
        
        # Linear interpolation between frames
        idx0 = int(floor(read_pos))
        idx1 = (idx0 + 1) % len(self.buffer)
        alpha = read_pos - idx0
        
        frame0 = self.buffer[idx0]
        frame1 = self.buffer[idx1]
        
        if frame0 is None or frame1 is None:
            return zeros(shape, dtype=frame0.dtype if frame0 is not None else frame1.dtype)
            
        return frame0 * (1-alpha) + frame1 * alpha
```

### vjlive1/core/matrix/node_effect_echophon.py (Node Implementation)
```python
# Node wrapper for VJLive-2 node graph:
class EchophonNode:
    """
    Echophon Video Delay Node.
    Pitch shifting echo with dual feedback loops and freeze.
    """
    
    def __init__(self):
        self.effect = EchophonEffect()
        self.inputs = {
            'video': None,
            'cv_echo': 0.0,
            'cv_feedback': 0.0,
            'cv_pitch': 0.0
        }
        self.outputs = {
            'video': None
        }
        
    def process(self):
        frame = self.inputs['video']
        if frame is None:
            return
            
        # Apply CV modulation
        cv_echo = self.inputs['cv_echo']
        cv_fb = self.inputs['cv_feedback']
        cv_pitch = self.inputs['cv_pitch']
        
        # Save original params
        orig_echo = self.effect.echo_time
        orig_fb = self.effect.feedback
        orig_pitch = self.effect.pitch
        
        # Apply CV offsets (CV 0-10V maps to ± parameter range)
        self.effect.echo_time = max(0.0, min(10.0, orig_echo + (cv_echo - 5.0)))
        self.effect.feedback = max(0.0, min(10.0, orig_fb + (cv_fb - 5.0)))
        self.effect.pitch = max(0.0, min(10.0, orig_pitch + (cv_pitch - 5.0)))
        
        # Process frame
        output = self.effect.process_frame(frame, self.dt)
        
        # Restore original params (CV is temporary modulation)
        self.effect.echo_time = orig_echo
        self.effect.feedback = orig_fb
        self.effect.pitch = orig_pitch
        
        self.outputs['video'] = output
```

The legacy implementation uses 60fps reference timing, float32 frame processing, and maintains circular buffers with 10% overallocation for safety. Pitch-shifting uses linear interpolation between adjacent frames for real-time performance.
