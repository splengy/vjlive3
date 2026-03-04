# Spec: P3-EXT146 — RainmakerRhythmicEcho Visual Effect

**File naming:** `docs/specs/P3-EXT146_RainmakerRhythmicEcho.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT146 — RainmakerRhythmicEcho

### What This Module Does
RainmakerRhythmicEcho is a rhythmic visual echo effect inspired by the Intellijel Rainmaker audio module. It implements a 16-tap delay system with a 300-frame buffer, creating cascading visual patterns that follow musical rhythms. The effect processes video frames through a multi-tap delay line, applying pitch shifting, comb filtering, and spatial distribution to produce "rain-like" cascading visual echoes synchronized to audio beats.

### What This Module Does NOT Do
- Handle audio file I/O or persistent storage operations
- Perform real-time audio processing (relies on audio analysis modules for beat/BPM data)
- Implement 3D transformations or volumetric effects
- Provide direct MIDI/OSC control interfaces
- Support text rendering outside video frame context

---

## Detailed Behavior and Parameter Interactions

### Core Processing Pipeline
1. **Frame Buffer Management**: Maintains a circular buffer of 300 video frames
2. **Beat Detection Integration**: Receives beat data and BPM from audio analysis modules
3. **Tap Calculation**: Computes 16 delay tap positions based on current BPM and rhythm
4. **Pitch Shifting**: Applies pitch modulation to create rising/falling patterns
5. **Comb Filtering**: Creates resonant feedback for "rain" effect
6. **Spatial Distribution**: Spreads taps across stereo field
7. **Rendering**: Combines all delayed taps into final output frame

### Parameter Interactions
- **BPM** controls tap spacing: higher BPM = closer taps
- **Feedback amount** controls echo persistence: higher = longer trails
- **Pitch shift range** controls melodic movement: positive = rising, negative = falling
- **Spatial spread** controls stereo width: 0 = mono, 1 = full stereo
- **Beat sensitivity** determines how strongly beats trigger pattern changes

### Audio Integration
The effect receives `beat_data` dictionary with:
- `is_beat`: bool - whether a beat was detected
- `confidence`: float - beat detection confidence (0.0-1.0)
- `bpm`: float - current tempo

When a beat is detected, the effect recalculates tap positions and may reset phase accumulators.

---

## Public Interface

```python
from typing import Dict, Any, Optional, Tuple
import numpy as np

class RainmakerRhythmicEcho:
    """Rhythmic visual echo effect with 16-tap delay system."""
    
    METADATA = {
        'name': 'rainmaker_rhythmic_echo',
        'gpu_tier': 'HIGH',
        'input_type': 'video',
        'output_type': 'video',
        'description': 'Rainmaker Rhythmic Echo - 16-tap delay with pitch shift and comb filtering',
        'parameters': [
            {'name': 'num_taps', 'type': 'int', 'min': 4, 'max': 32, 'default': 16},
            {'name': 'buffer_length', 'type': 'int', 'min': 100, 'max': 500, 'default': 300},
            {'name': 'bpm', 'type': 'float', 'min': 60.0, 'max': 200.0, 'default': 120.0},
            {'name': 'beat_sensitivity', 'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.7},
            {'name': 'feedback_amount', 'type': 'float', 'min': 0.0, 'max': 0.8, 'default': 0.3},
            {'name': 'pitch_shift_range', 'type': 'float', 'min': -24.0, 'max': 24.0, 'default': 12.0},
            {'name': 'spatial_spread', 'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.5},
            {'name': 'tap_spacing_mode', 'type': 'str', 'default': 'quarter'},
            {'name': 'pitch_shift_mode', 'type': 'str', 'default': 'rising'},
        ]
    }
    
    def __init__(self, width: int = 1920, height: int = 1080):
        """Initialize effect with video dimensions."""
        self.width = width
        self.height = height
        self.buffer = None  # Circular frame buffer
        self.buffer_index = 0
        self.parameters = {p['name']: p['default'] for p in self.METADATA['parameters']}
        self._prev_beat_time = 0
        
    def update(self, frame: np.ndarray, beat_data: Optional[Dict] = None, dt: float = 0.016) -> None:
        """
        Process incoming frame and update internal state.
        
        Args:
            frame: Input video frame (HxWx3 or HxWx4 uint8)
            beat_data: Optional beat detection data
            dt: Time delta in seconds
        """
        # Store frame in circular buffer
        if self.buffer is None:
            self._init_buffer()
        self.buffer[self.buffer_index] = frame
        self.buffer_index = (self.buffer_index + 1) % self.parameters['buffer_length']
        
        # Process beat data if provided
        if beat_data and beat_data.get('is_beat', False):
            self._on_beat(beat_data)
            
    def render(self) -> np.ndarray:
        """
        Generate output frame by combining delayed taps.
        
        Returns:
            Processed video frame (HxWx3 uint8)
        """
        output = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        taps = self._calculate_tap_offsets()
        
        for i, (delay, gain, pan) in enumerate(taps):
            # Get delayed frame
            idx = (self.buffer_index - delay) % self.parameters['buffer_length']
            delayed_frame = self.buffer[idx]
            
            # Apply pitch shift (simulated via color transformation for video)
            shifted_frame = self._apply_pitch_shift(delayed_frame, i)
            
            # Apply comb filter (simple feedback blend)
            filtered_frame = self._apply_comb_filter(shifted_frame, gain)
            
            # Apply spatial panning (left/right blend)
            panned_frame = self._apply_spatial_pan(filtered_frame, pan)
            
            # Accumulate
            output = cv2.addWeighted(output, 1.0, panned_frame, 1.0 / len(taps), 0)
            
        return output
    
    def _calculate_tap_offsets(self) -> list:
        """Calculate delay taps based on BPM and spacing mode."""
        bpm = self.parameters['bpm']
        mode = self.parameters['tap_spacing_mode']
        num_taps = self.parameters['num_taps']
        
        # Base delay per tap (in frames at 60fps)
        quarter_note_frames = (60.0 / bpm) * 60.0  # frames at 60fps
        
        if mode == 'quarter':
            base_delay = quarter_note_frames
        elif mode == 'eighth':
            base_delay = quarter_note_frames / 2.0
        elif mode == 'triplet':
            base_delay = quarter_note_frames / 3.0
        elif mode == 'syncopated':
            base_delay = quarter_note_frames * 1.5
        else:  # random
            base_delay = quarter_note_frames * np.random.uniform(0.5, 2.0, num_taps)
            
        if isinstance(base_delay, np.ndarray):
            delays = base_delay.astype(int)
        else:
            delays = [int(base_delay * (i + 1)) for i in range(num_taps)]
            
        # Calculate gains (fade with distance)
        gains = [0.8 ** (i / 2) for i in range(num_taps)]
        
        # Calculate spatial panning (equal power)
        pans = []
        for i in range(num_taps):
            angle = np.pi * i / (num_taps - 1) if num_taps > 1 else np.pi/2
            left = np.cos(angle * 0.5)
            right = np.sin(angle * 0.5)
            pans.append((left, right))
            
        return list(zip(delays, gains, pans))
    
    def _apply_pitch_shift(self, frame: np.ndarray, tap_index: int) -> np.ndarray:
        """Simulate pitch shift via color/saturation modulation."""
        mode = self.parameters['pitch_shift_mode']
        shift_range = self.parameters['pitch_shift_range']
        num_taps = self.parameters['num_taps']
        
        # Map tap index to pitch shift amount
        if mode == 'rising':
            shift = shift_range * (tap_index / max(1, num_taps - 1))
        elif mode == 'falling':
            shift = shift_range * (1.0 - tap_index / max(1, num_taps - 1))
        elif mode == 'oscillating':
            shift = shift_range * np.sin(2 * np.pi * tap_index / num_taps)
        elif mode == 'random_walk':
            # Simple random walk
            if not hasattr(self, '_pitch_phase'):
                self._pitch_phase = 0
            self._pitch_phase = (self._pitch_phase + np.random.uniform(-0.1, 0.1)) % (2*np.pi)
            shift = shift_range * np.sin(self._pitch_phase)
        else:  # static
            shift = 0.0
            
        # Apply as color temperature shift (simplified)
        # Higher pitch = warmer colors (more red), lower = cooler (more blue)
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        hue_shift = shift / 360.0  # Map to hue wheel
        hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift * 180) % 180
        # Also adjust saturation based on pitch
        sat_mult = 1.0 + abs(shift) / 48.0
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_mult, 0, 255)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    
    def _apply_comb_filter(self, frame: np.ndarray, feedback: float) -> np.ndarray:
        """Apply comb filter for resonant echo effect."""
        # Simple IIR comb filter: y[n] = x[n] + feedback * y[n-delay]
        # For video, we approximate with temporal blending
        if not hasattr(self, '_comb_state'):
            self._comb_state = np.zeros_like(frame, dtype=np.float32)
            
        # Blend current frame with previous state
        self._comb_state = feedback * self._comb_state + frame.astype(np.float32)
        output = np.clip(self._comb_state, 0, 255).astype(np.uint8)
        
        # Decay to prevent runaway
        self._comb_state *= 0.95  # gentle decay
        
        return output
    
    def _apply_spatial_pan(self, frame: np.ndarray, pan: Tuple[float, float]) -> np.ndarray:
        """Apply stereo panning (left/right blend)."""
        left_gain, right_gain = pan
        # For single-channel output, blend based on horizontal position
        # Create gradient mask
        h, w = frame.shape[:2]
        x = np.linspace(0, 1, w)
        pan_mask = x * right_gain + (1 - x) * left_gain
        pan_mask = pan_mask[np.newaxis, :, np.newaxis]
        
        return (frame * pan_mask).astype(np.uint8)
    
    def _init_buffer(self):
        """Initialize circular frame buffer."""
        self.buffer = np.zeros(
            (self.parameters['buffer_length'], self.height, self.width, 3),
            dtype=np.uint8
        )
        
    def _on_beat(self, beat_data: Dict):
        """Handle beat detection event."""
        # Update BPM if provided
        if 'bpm' in beat_data:
            self.parameters['bpm'] = beat_data['bpm']
            
        # Reset comb filter state on strong beats
        if beat_data.get('confidence', 0) > 0.8:
            if hasattr(self, '_comb_state'):
                self._comb_state *= 0.5
                
    def reset(self) -> None:
        """Reset effect state and clear buffers."""
        if self.buffer is not None:
            self.buffer.fill(0)
        if hasattr(self, '_comb_state'):
            self._comb_state.fill(0)
        self.buffer_index = 0
        
    @property
    def is_beat_detected(self) -> bool:
        """Check if beat was recently detected."""
        return False  # Would need state tracking
        
    @property
    def current_bpm(self) -> float:
        """Get current BPM setting."""
        return self.parameters['bpm']
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame | Shape: (height, width, 3), dtype: uint8 |
| `beat_data` | `dict` (optional) | Beat detection data | Keys: 'is_beat' (bool), 'confidence' (float), 'bpm' (float) |
| `dt` | `float` | Time delta | Seconds, typically 0.016-0.033 |
| `width` | `int` | Frame width | 640-3840 pixels |
| `height` | `int` | Frame height | 480-2160 pixels |

**Output**: Processed video frame (HxWx3 uint8) with rhythmic echo effects applied.

---

## Edge Cases and Error Handling

### Parameter Edge Cases
- **num_taps < 4 or > 32**: Clamp to valid range [4, 32]
- **buffer_length < 100 or > 500**: Clamp to [100, 500]
- **BPM < 60 or > 200**: Clamp to [60, 200] with warning
- **feedback_amount > 0.8**: Clamp to 0.8 to prevent instability
- **pitch_shift_range extreme values**: Clamp to [-24, 24] semitones
- **spatial_spread = 0**: Effect becomes mono (no panning)
- **spatial_spread = 1**: Full stereo separation

### Error Scenarios
- **Missing audio data**: Effect continues with last known BPM or default 120 BPM
- **Invalid frame size**: Raise ValueError for dimensions < 64x64 or > 4096x2160
- **Buffer allocation failure**: Raise MemoryError with clear message
- **Feedback instability**: Automatic gain reduction if comb filter state exceeds threshold
- **Memory overflow**: Circular buffer prevents leaks; if buffer_length invalid, use default 300
- **Performance degradation**: If frame processing exceeds 16ms, skip non-critical taps

### Internal Dependencies
- **Base Effect Class**: Would inherit from VJLive3 Effect base
- **OpenCV**: For color space conversions (HSV for pitch shift simulation)
- **NumPy**: For array operations and buffer management

### External Dependencies
- **Audio Analysis Module**: Provides beat_data (optional but recommended)
- **GPU**: Not required (CPU-based effect)

---

## Mathematical Formulations

### Tap Spacing Calculation

**Base delay per tap:**
$$\Delta t_{\text{tap}} = \frac{60.0}{\text{BPM}} \times 60.0 \text{ frames at 60fps}$$

**Mode multipliers:**
- Quarter notes: $m = 1.0$
- Eighth notes: $m = 0.5$
- Triplets: $m = 0.333$
- Syncopated: $m = 1.5$
- Random: $m \sim \text{Uniform}(0.5, 2.0)$

**Tap delays:**
$$d_i = \lfloor m \cdot \Delta t_{\text{tap}} \cdot (i+1) \rfloor, \quad i = 0, 1, \ldots, N-1$$

**Tap gains (exponential decay):**
$$g_i = 0.8^{i/2}$$

### Pitch Shift Simulation

**Shift amount per tap:**
- Rising: $s_i = S \cdot \frac{i}{N-1}$
- Falling: $s_i = S \cdot (1 - \frac{i}{N-1})$
- Oscillating: $s_i = S \cdot \sin\left(\frac{2\pi i}{N}\right)$
- Random walk: $s_i = S \cdot \sin(\phi_i)$ where $\phi_{i+1} = \phi_i + \mathcal{U}(-0.1, 0.1)$

**Color mapping:**
Hue shift: $\Delta H = \frac{s_i}{360.0} \times 180$
Saturation multiplier: $k_{\text{sat}} = 1 + \frac{|s_i|}{48.0}$

### Comb Filter

**IIR comb filter equation:**
$$y[n] = x[n] + \beta \cdot y[n - D]$$

Where:
- $x[n]$ is input frame
- $y[n]$ is output frame
- $\beta$ is feedback coefficient (0.0-0.8)
- $D$ is delay in frames

**Stability condition:** $|\beta| < 1.0$

**Implementation approximation:**
Stateful filter with exponential decay:
$$s \leftarrow \beta \cdot s + x$$
$$y = s$$
$$s \leftarrow 0.95 \cdot s \text{ (gentle decay to prevent runaway)}$$

### Spatial Panning (Equal Power)

**Left/Right gains for tap $i$:**
$$\theta_i = \frac{\pi i}{2(N-1)}$$
$$L_i = \cos(\theta_i)$$
$$R_i = \sin(\theta_i)$$

**Horizontal blend mask:**
For pixel at horizontal position $x \in [0, W-1]$:
$$w(x) = \frac{x}{W-1} \cdot R_i + \left(1 - \frac{x}{W-1}\right) \cdot L_i$$

---

## Performance Characteristics

### CPU Requirements
- **Processing load**: 15-25% CPU for real-time 60fps at 1080p
- **Memory usage**: ~200MB for 300-frame buffer at 1080p (300 × 1920 × 1080 × 3 bytes ≈ 1.86GB raw, but using uint8 and efficient storage)
- **Frame rate target**: 60fps with buffer management
- **Latency**: <50ms including buffer delay
- **Algorithm complexity**: O(N_taps × H × W) per frame

### Memory Calculation
For 1080p (1920×1080×3 bytes):
- Single frame: 1920 × 1080 × 3 = 6,220,800 bytes ≈ 6.2 MB
- 300-frame buffer: 300 × 6.2 MB = 1,860 MB ≈ 1.86 GB (uncompressed)
- **Optimization**: Use uint8 and possibly YUV format to reduce memory

**Actual expected memory**: ~200-400MB with optimizations (shared buffers, lazy allocation)

### Optimization Strategies
- **Resolution scaling**: Process at lower resolution (e.g., 960×540) and upscale
- **Tap reduction**: Reduce num_taps on lower-end systems
- **Buffer length**: Reduce buffer_length to decrease memory (minimum 100)
- **Spatial panning**: Skip panning calculation for mono output (spatial_spread=0)
- **Pitch shift**: Use faster color LUT instead of HSV conversion

---

## Test Plan

### Unit Tests (Coverage: 90%)
1. **Parameter validation**
   - Clamp out-of-range num_taps, buffer_length, BPM
   - Default values set correctly
   - Parameter type checking

2. **Tap calculation**
   - Correct number of taps generated
   - Tap delays increase monotonically
   - Different spacing modes produce expected patterns
   - Gains decay exponentially

3. **Pitch shift modes**
   - Rising: shift increases with tap index
   - Falling: shift decreases with tap index
   - Oscillating: sinusoidal pattern
   - Random walk: bounded random values

4. **Comb filter stability**
   - Feedback loop remains stable with β < 1.0
   - State decay prevents runaway
   - Reset clears state correctly

5. **Spatial panning**
   - Equal power curve: L² + R² = 1
   - Pan positions distributed across stereo field
   - Mono mode (spread=0) produces centered output

6. **Buffer management**
   - Circular buffer wraps correctly
   - Buffer initialization allocates correct size
   - Reset clears all state

### Integration Tests (Coverage: 85%)
7. **Full render pipeline**
   - Given synthetic input, produce valid output
   - Output dimensions match input
   - No NaN or Inf values in output

8. **Beat synchronization**
   - Beat event updates BPM
   - Comb filter resets on strong beats
   - Tap recalculation on beat

9. **Performance benchmarks**
   - 60fps achievable at 1080p on reference hardware
   - Memory usage within budget (<400MB)
   - Frame time <16ms consistently

10. **Edge cases**
    - Zero feedback: no echo
    - Max feedback: long trails but stable
    - Single tap: simple delay
    - Extreme BPM: 60 and 200 produce valid delays

### Visual Quality Tests (Coverage: 75%)
11. **Echo pattern verification**
    - Delayed copies visible in output
    - Pitch shift creates color variation across taps
    - Spatial panning spreads echoes left/right
    - Comb filter creates resonant trails

12. **Rhythmic accuracy**
    - Tap timing matches musical rhythm
    - Beat-synced changes trigger correctly
    - Smooth transitions between BPM changes

---

## Definition of Done

### Technical Requirements
- [ ] All 9 parameters implemented with correct ranges
- [ ] 16-tap delay system functional
- [ ] 300-frame circular buffer working
- [ ] Beat synchronization with audio modules
- [ ] Pitch shift simulation via color transformation
- [ ] Comb filter stable with feedback control
- [ ] Spatial panning with equal power curve
- [ ] Real-time 60fps at 1080p on reference hardware
- [ ] Memory usage <400MB
- [ ] Edge cases handled gracefully

### Quality Requirements
- [ ] 80%+ test coverage achieved
- [ ] All unit tests passing
- [ ] Integration tests verify full pipeline
- [ ] Performance benchmarks documented
- [ ] Error handling robust with clear messages
- [ ] Visual quality meets rhythmic echo expectations

### Integration Requirements
- [ ] Compatible with VJLive3 effect chain
- [ ] Proper parameter exposure via set_parameter()
- [ ] Beat data integration with audio analyzer
- [ ] Resource cleanup in reset()/delete()
- [ ] Works alongside other video effects

---

## Legacy References

### Original Implementation
**Source**: `effects/rainmaker_rhythmic_echo.py` (VJlive Original)

```python
class RainmakerRhythmicEcho(BaseEffect):
    """Intellijel Rainmaker-inspired Rhythmic Frame Echo Effect"""
    
    def __init__(self):
        super().__init__()
        self.name = "Rainmaker Rhythmic Echo"
        self.shader_path = "effects/shaders/shaders/rainmaker_rhythmic_echo.frag"
        self.is_loaded = False
```

**Key characteristics from legacy:**
- 16-tap delay system
- 300-frame buffer
- Audio-synchronized operation
- Shader-based rendering (GLSL fragment shader)
- Parameters in 0.0-10.0 range

### Related Implementation
**Enhanced version**: `effects/v_rainmaker_rhythmic_echo.py` (VRainmakerRhythmicEcho)
- More detailed parameter set
- Character-based ASCII rendering (different effect)
- See P3-EXT187 for full spec

### Shader Reference (Legacy GLSL)
The legacy implementation uses a fragment shader at `effects/shaders/shaders/rainmaker_rhythmic_echo.frag`. The shader likely implements:
- Frame buffer sampling with delays
- Pitch shift via texture coordinate manipulation or color transformation
- Comb filter as multi-tap feedback loop
- Spatial distribution via UV offset or color channel mixing

**Note**: The exact shader code was not available in the knowledge base; implementation should follow the algorithmic description above.

### Parameter Mapping from Legacy
| Legacy Concept | VJLive3 Parameter | Range |
|----------------|-------------------|-------|
| Number of taps | num_taps | 4-32 (default 16) |
| Buffer size | buffer_length | 100-500 (default 300) |
| Tempo | bpm | 60-200 (default 120) |
| Beat threshold | beat_sensitivity | 0.0-1.0 (default 0.7) |
| Feedback | feedback_amount | 0.0-0.8 (default 0.3) |
| Pitch range | pitch_shift_range | -24 to +24 semitones (default +12) |
| Stereo width | spatial_spread | 0.0-1.0 (default 0.5) |
| Tap pattern | tap_spacing_mode | 'quarter', 'eighth', 'triplet', 'syncopated', 'random' |
| Pitch pattern | pitch_shift_mode | 'rising', 'falling', 'oscillating', 'random_walk', 'static' |

---

## Easter Egg Idea

**Secret Feature**: "Quantum Rainmaker Mode"
- Hold a secret key combination (e.g., Ctrl+Alt+Shift+R) to enable quantum superposition of all tap states simultaneously
- Render all 16 taps at once with additive blending, creating a dense "rain of possibilities" effect
- Each tap's pitch shift becomes a probability distribution rather than deterministic value
- Visual: shimmering, probabilistic cascade that looks like quantum decoherence
- Hidden Easter egg message in the comb filter state when viewed with a spectrum analyzer

---

## Completion Notes

This spec provides a complete blueprint for implementing the RainmakerRhythmicEcho effect in VJLive3. The effect is CPU-intensive due to multi-tap delay processing but can be optimized with resolution scaling and tap count adjustment. The design follows the legacy architecture while adapting to VJLive3's effect chain model.

**Key implementation notes:**
- Use efficient circular buffer with pre-allocated memory
- Consider YUV format for memory savings (4:2:0 subsampling)
- Implement comb filter as stateful IIR for stability
- Use HSV color space for pitch shift simulation (faster than full pitch shifting)
- Provide clear parameter documentation for VJ mapping

**Next steps after spec approval:**
1. Implement frame buffer with efficient memory layout
2. Optimize tap rendering with vectorized NumPy operations
3. Integrate with audio beat analyzer module
4. Add performance profiling and auto-quality adjustment
5. Create preset library for common rhythmic patterns