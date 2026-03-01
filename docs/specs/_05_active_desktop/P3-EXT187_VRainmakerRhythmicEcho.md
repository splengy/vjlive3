# P3-EXT187: VRainmakerRhythmicEcho Effect

## Specification Status
- **Phase**: Pass 1 (Skeleton)
- **Target Phase**: Pass 2 (Detailed Technical Spec)
- **Priority**: P0
- **Module**: `v_rainmaker_rhythmic_echo` plugin
- **Implementation Path**: `src/vjlive3/plugins/v_rainmaker_rhythmic_echo.py`
- **Effect Type**: Audio-Reactive/Delay/Echo

## Executive Summary

VRainmakerRhythmicEcho is an audio-reactive delay/echo effect that creates rhythmic cascading patterns synchronized to the beat. It combines audio-triggered impulses with rhythmic timing to produce stuttering, reverb-like effects that respond to percussion and bass frequencies in real-time.

## Problem Statement

Live VJ performances need dynamic echo/delay effects that:
- Sync to musical beat (not independent delay time)
- React to drums/percussion (triggered echo bursts)
- Create "rainmaker" cascading patterns (multiple delayed copies)
- Maintain synchronization without manual BPM entry
- Sound musical, not arbitrary

Existing delay effects either ignore timing or require explicit BPM configuration, making them unreliable in live settings where tempo may be unknown or changing.

## Solution Overview

VRainmakerRhythmicEcho provides:
1. **Audio analysis**: Detect beat/percussion peaks
2. **Rhythm tracking**: Extract BPM from audio content
3. **Echo triggering**: Generate echoes on beat detection
4. **Cascade pattern**: Create 3-5 staggered copies (the "rain")
5. **Spatial distribution**: Spread echoes across stereo field
6. **Feedback loop**: Optional regenerative echoes for "tails"

## Detailed Behavior

### Phase 1: Audio Analysis
Analyze incoming audio for percussion content and beat peaks

### Phase 2: BPM Detection
Extract tempo from rhythm content or use external BPM

### Phase 3: Echo Triggering
Generate echo impulses on detected beats with configurable sensitivity

### Phase 4: Cascade Generation
Create 3-5 delayed copies with exponential amplitude decay

### Phase 5: Spatial Mapping
Distribute echoes across stereo field (left, center, right)

### Phase 6: Feedback Application
Optional regenerative tail for smooth transition between beats

### Phase 7: Output
Render echoed/delayed audio frame

## Public Interface

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

class EchoCascadeMode(Enum):
    """Echo cascade pattern mode."""
    LINEAR = "linear"           # Evenly spaced echoes
    EXPONENTIAL = "exponential" # Exponentially decaying
    FIBONACCI = "fibonacci"     # Fibonacci-spaced delays
    CHAOTIC = "chaotic"         # Pseudo-random spacing

@dataclass
class EchoParameters:
    """Echo effect parameters."""
    feedback_amount: float      # Regenerative feedback [0, 0.8]
    decay_factor: float         # Amplitude decay per echo [0.3, 0.9]
    num_echoes: int             # Number of cascade echoes [1, 5]
    timing_offset_ms: float     # Time offset from beat [-50, 50]

class VRainmakerRhythmicEchoEffect:
    """Audio-reactive rhythmic echo effect."""
    
    def __init__(self, sample_rate: int = 44100, channels: int = 2):
        """Initialize effect with audio parameters."""
    
    def update(self, audio_frame: np.ndarray, dt: float) -> None:
        """Process audio frame and update internal state."""
        # Analyze percussion content
        # Detect beat peaks
        # Update rhythm tracking
    
    def render(self) -> np.ndarray:
        """Generate echoed audio output."""
        # Trigger echoes on beat
        # Apply cascade pattern
        # Mix with feedback
        # Return processed audio
    
    def analyze_beat(self, audio_frame: np.ndarray) -> Tuple[bool, float]:
        """Detect beat and return (is_beat, confidence)."""
    
    def get_current_bpm(self) -> float:
        """Get detected or configured BPM."""
    
    # Parameters
    @property
    def bpm(self) -> float:
        """Get/set beats per minute."""
    
    @bpm.setter
    def bpm(self, value: float) -> None:
        """Set BPM (60-200)."""
    
    @property
    def cascade_mode(self) -> EchoCascadeMode:
        """Get/set echo cascade pattern."""
    
    @cascade_mode.setter
    def cascade_mode(self, mode: EchoCascadeMode) -> None:
        """Change echo spacing pattern."""
    
    @property
    def echo_params(self) -> EchoParameters:
        """Get current echo parameters."""
    
    @echo_params.setter
    def echo_params(self, params: EchoParameters) -> None:
        """Update all echo parameters."""
    
    @property
    def beat_sensitivity(self) -> float:
        """Threshold for beat detection [0-1]."""
    
    @beat_sensitivity.setter
    def beat_sensitivity(self, value: float) -> None:
        """Set beat detection threshold."""
    
    @property
    def wet_dry_mix(self) -> float:
        """Wet/dry blend [0=dry, 1=wet]."""
    
    @property
    def stereo_spread(self) -> float:
        """Spatial distribution of echoes [0-1]."""
```

## Mathematical Formulations

### Beat Onset Detection
$$\text{energy}(n) = \sum_{k} |X[n, k]|^2 \quad \text{(spectral energy)}$$
$$\text{novelty}(n) = \max(0, \Delta\text{energy}(n))$$

### BPM Extraction (Autocorrelation)
$$R(lag) = \sum_{n} \text{energy}(n) \cdot \text{energy}(n + lag)$$

### Echo Delay (Linear Cascade)
$$\tau_i = i \cdot \frac{60000}{\text{BPM}} \quad \text{where } i = 1, 2, ..., N$$

### Echo Amplitude (Exponential Decay)
$$A_i = A_0 \cdot \alpha^i \quad \text{where } \alpha \in [0.3, 0.9]$$

### Feedback Regeneration
$$y(n) = x(n) + \beta \cdot y(n - \tau_{\text{feedback}})$$

### Stereo Panning (Linear)
$$L_i = A_i \cdot \max(0, 1 - i/N) \quad R_i = A_i \cdot \min(1, i/N)$$

## Performance Characteristics

- **Frame rate**: 44.1 kHz or higher
- **CPU usage**: 5-15% for real-time processing
- **Memory**: ~200MB for delay buffers (1-2 second history)
- **Latency**: <50ms for beat detection + echo trigger
- **Filter order**: 4th-order IIR (smooth envelope)

## Test Plan

1. **Beat Detection**
   - Detects onsets in sparse audio
   - Accurate in presence of noise
   - Sensitivity parameter changes threshold
   - No double-triggers within beat period

2. **BPM Extraction**
   - Correctly identifies tempo (±5% accuracy)
   - Tracks tempo changes smoothly
   - Works with diverse genres

3. **Echo Cascade**
   - Linear spacing correct
   - Exponential decay applied properly
   - Amplitude decay realistically models reverb
   - Multiple echoes render correctly

4. **Spatial Distribution**
   - Echoes spread across stereo field
   - Panning smooth and correlated
   - Mono compatibility verified

5. **Feedback**
   - Regenerative echoes stable
   - No runaway amplification
   - Decay prevents infinite loops

6. **Synchronization**
   - Echo timing aligns with beat
   - Offset parameter shifts timing
   - Syncs to external BPM source

7. **Performance**
   - Target latency met
   - Memory bounded
   - CPU utilization acceptable

## Definition of Done

- [ ] Beat detection algorithm implemented
- [ ] BPM extraction working
- [ ] Echo cascade generation correct
- [ ] Amplitude decay formula applied
- [ ] Spatial panning implemented
- [ ] Feedback loop stable
- [ ] All parameters exposed and settable
- [ ] 15+ test cases passing
- [ ] Latency <50ms verified
- [ ] Memory usage bounded (<250MB)
- [ ] No stubs or TODOs
- [ ] Complete docstrings
- [ ] Parameter validation
- [ ] Beat sensitivity parameter working
- [ ] Wet/dry mix blending correct
- [ ] External BPM sync option available
- [ ] ≤900 lines of code

## Dependencies

- NumPy (FFT, autocorrelation)
- SciPy (spectral analysis, filters)
- VJLive3 Audio effect base class
- PerformanceMonitor (latency tracking)

## Related Specs

- P3-AUDIO-ANALYZER: Beat and BPM detection
- P3-DELAY-BUFFER: Circular delay buffers
- P3-AUDIO-EFFECT-BASE: Audio effect base class
- P3-STEREO-PROCESSOR: Stereo panning utilities

---

**Notes for Pass 2 Implementation:**
- Decide exact beat detection algorithm (onset-based vs energy-based)
- Confirm BPM range (60-200 BPM standard)
- Define exact cascade modes and their spacing formulas
- Specify feedback stability criterion (gain < 1)
- Document panning law (constant power vs linear)
