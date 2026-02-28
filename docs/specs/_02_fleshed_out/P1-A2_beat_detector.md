# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P1-A2_beat_detector.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-A2 — Beat Detector

**What This Module Does**

Implements a real-time beat detection engine that analyzes audio input to detect rhythmic beats, estimate tempo (BPM), and track beat phase with high accuracy. The detector uses a multi-stage processing pipeline: onset detection, tempo estimation via autocorrelation, beat tracking with dynamic programming, and phase tracking, all running in a dedicated thread to maintain 60 FPS video performance while providing beat information for audio-reactive visual effects.

---

## Architecture Decisions

- **Pattern:** State Machine with Adaptive Thresholding
- **Rationale:** Beat detection requires maintaining temporal state (current beat phase, tempo estimate) while adapting to changing musical dynamics. A state machine allows clear transitions between detection states (searching, tracking, lost), while adaptive thresholding handles varying audio levels and styles.
- **Constraints:**
  - Must detect beats on kick drums, snares, and hi-hats
  - Must estimate tempo within 5% accuracy for 60-180 BPM range
  - Must track beat phase with < 50ms jitter
  - Must handle tempo changes and musical breaks
  - Must run in < 1ms per frame on Orange Pi 5
  - Must integrate with existing AudioAnalyzer framework
  - Must provide confidence scores for beat detection

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-2 | `tests/test_audio_reactive_comprehensive.py` | BeatDetector | Port — test patterns |
| VJlive-2 | `core/effects/audio_reactive_effects.py` | AudioReactor | Reference — feature consumption |
| VJlive-2 | `DEVELOPER_D_MILKDROP_MANIFOLD_NODERED.md` | set_audio_analyzer | Port — integration pattern |
| VJlive-2 | `DEVELOPER_PROMPTS/15_MOOD_MANIFOLD_PRESET_SYSTEM.md` | Audio reactivity | Reference — feature requirements |
| VJlive-2 | `INTEGRATION_CHECKLIST.md` | Audio signal bridge | Port — bus integration |

---

## Public Interface

```python
class BeatDetector:
    """Real-time beat detection and tempo tracking."""
    
    def __init__(self, tempo_range: Tuple[int, int] = (60, 180)) -> None:...
    def process_frame(self, magnitude: np.ndarray) -> BeatDetectionResult:...
    def get_current_state(self) -> BeatState:...
    def reset(self) -> None:...
    def set_tempo_range(self, min_bpm: int, max_bpm: int) -> None:...
    def get_tempo_estimate(self) -> float:...
    def get_beat_phase(self) -> float:...
    def get_confidence(self) -> float:...
    def get_beat_history(self, duration_seconds: float) -> List[BeatEvent]:...
    def is_beat(self) -> bool:...
    def get_bpm(self) -> float:...
    def get_phase(self) -> float:...
    def get_beat_strength(self) -> float:...
```

---

## Beat Detection Pipeline

### 1. Onset Detection

```python
class OnsetDetector:
    """Detect onsets in audio signal."""
    
    def __init__(self, sample_rate: int = 48000, hop_size: int = 512):
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.prev_magnitude = None
        self.energy_history = deque(maxlen=43)  # ~1 second at 60 Hz
        self.energy_threshold = 1.3  # Local average multiplier
        
    def detect(self, magnitude: np.ndarray) -> Tuple[bool, float]:
        """Detect onset in magnitude spectrum."""
        if self.prev_magnitude is None:
            self.prev_magnitude = magnitude
            return False, 0.0
            
        # Spectral flux: sum of positive differences
        diff = magnitude - self.prev_magnitude
        flux = np.sum(np.maximum(diff, 0.0))
        
        self.prev_magnitude = magnitude
        
        # Compute local energy average
        bass_energy = np.sum(magnitude[:20] ** 2)  # Low frequencies
        self.energy_history.append(bass_energy)
        
        if len(self.energy_history) < 10:
            return False, 0.0
            
        local_avg = np.mean(list(self.energy_history)[-10:])
        
        # Adaptive threshold based on local energy
        threshold = local_avg * self.energy_threshold
        
        if flux > threshold:
            # Confidence based on flux strength
            confidence = min(1.0, flux / (threshold * 2.0))
            return True, confidence
            
        return False, 0.0
```

### 2. Tempo Estimation

```python
class TempoEstimator:
    """Estimate tempo using autocorrelation."""
    
    def __init__(self, sample_rate: int = 48000, hop_size: int = 512):
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.onset_history = deque(maxlen=1024)  # ~8 seconds at 60 Hz
        self.tempo_range = (60, 180)  # BPM range
        self.current_tempo = 120.0
        self.confidence = 0.0
        
    def estimate(self, onsets: List[float]) -> Tuple[float, float]:
        """Estimate tempo from onset times."""
        # Add new onsets to history
        self.onset_history.extend(onsets)
        
        if len(self.onset_history) < 10:
            return self.current_tempo, 0.0
            
        # Convert to inter-onset intervals (IOIs)
        if len(self.onset_history) < 2:
            return self.current_tempo, 0.0
            
        iois = []
        prev_time = self.onset_history[0]
        for t in list(self.onset_history)[1:]:
            ioi = t - prev_time
            if ioi > 0:
                iois.append(ioi)
            prev_time = t
            
        if len(iois) < 5:
            return self.current_tempo, 0.0
            
        # Convert IOIs to BPM
        bpms = [60.0 / ioi for ioi in iois]
        
        # Filter to tempo range
        valid_bpms = [bpm for bpm in bpms if self.tempo_range[0] <= bpm <= self.tempo_range[1]]
        
        if not valid_bpms:
            return self.current_tempo, 0.0
            
        # Compute median tempo
        estimated_tempo = np.median(valid_bpms)
        
        # Compute confidence (variance of IOIs)
        ioi_variances = [abs(ioi - 60.0 / estimated_tempo) for ioi in iois]
        confidence = 1.0 - min(1.0, np.mean(ioi_variances) / (60.0 / estimated_tempo * 0.1))
        
        # Smooth tempo changes
        if confidence > 0.5:
            self.current_tempo = 0.7 * self.current_tempo + 0.3 * estimated_tempo
        
        self.confidence = confidence
        return self.current_tempo, confidence
```

### 3. Beat Tracking

```python
class BeatTracker:
    """Track beats using dynamic programming."""
    
    def __init__(self, sample_rate: int = 48000, hop_size: int = 512):
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.onset_detector = OnsetDetector(sample_rate, hop_size)
        self.tempo_estimator = TempoEstimator(sample_rate, hop_size)
        self.current_state = BeatState()
        self.beat_history = deque(maxlen=3600)  # 1 minute at 60 Hz
        
    def process_frame(self, magnitude: np.ndarray) -> BeatDetectionResult:
        """Process audio frame and detect beats."""
        # Detect onsets
        onset, onset_confidence = self.onset_detector.detect(magnitude)
        
        # Update tempo estimate
        if onset:
            current_time = time.time()
            self.tempo_estimator.estimate([current_time])
            
        # Track beat phase
        if self.tempo_estimator.confidence > 0.5:
            beat_phase = self._track_beat_phase()
            beat = self._is_beat(beat_phase)
            beat_strength = self._compute_beat_strength(beat_phase)
        else:
            beat = False
            beat_phase = 0.0
            beat_strength = 0.0
            
        # Update state
        self.current_state = BeatState(
            beat=beat,
            beat_confidence=beat_strength,
            tempo=self.tempo_estimator.current_tempo,
            phase=beat_phase,
            confidence=self.tempo_estimator.confidence,
            timestamp=time.time()
        )
        
        # Store in history
        self.beat_history.append(self.current_state)
        
        return BeatDetectionResult(
            beat=beat,
            beat_confidence=beat_strength,
            tempo=self.tempo_estimator.current_tempo,
            phase=beat_phase,
            confidence=self.tempo_estimator.confidence,
            timestamp=time.time()
        )
    
    def _track_beat_phase(self) -> float:
        """Track beat phase within current tempo."""
        if not self.beat_history:
            return 0.0
            
        # Get time since last beat
        last_beat = self.beat_history[-1]
        current_time = time.time()
        time_since_last = current_time - last_beat.timestamp
        
        # Compute phase (0.0-1.0)
        beat_interval = 60.0 / self.tempo_estimator.current_tempo
        phase = (time_since_last % beat_interval) / beat_interval
        
        return phase
    
    def _is_beat(self, phase: float) -> bool:
        """Determine if current phase is a beat."""
        # Beat is when phase is close to 0.0 (start of beat cycle)
        return phase < 0.1  # Within 10% of beat start
    
    def _compute_beat_strength(self, phase: float) -> float:
        """Compute beat strength based on phase and confidence."""
        if phase < 0.1:
            # Strong beat at phase 0.0
            return self.tempo_estimator.confidence
        elif phase < 0.2:
            # Medium strength (off-beat)
            return self.tempo_estimator.confidence * 0.5
        else:
            # Weak or no beat
            return 0.0
```

### 4. State Machine

```python
class BeatStateMachine:
    """Manage beat detection states."""
    
    def __init__(self):
        self.state = "searching"
        self.state_start_time = time.time()
        self.tempo_history = deque(maxlen=60)  # 1 minute at 60 Hz
        
    def update(self, detection_result: BeatDetectionResult):
        """Update state based on detection result."""
        if self.state == "searching":
            if detection_result.confidence > 0.7:
                self.state = "tracking"
                self.state_start_time = time.time()
        elif self.state == "tracking":
            if detection_result.confidence < 0.3:
                self.state = "lost"
                self.state_start_time = time.time()
        elif self.state == "lost":
            if detection_result.confidence > 0.5:
                self.state = "tracking"
                self.state_start_time = time.time()
            elif time.time() - self.state_start_time > 5.0:
                self.state = "searching"
                self.state_start_time = time.time()
        
        # Store tempo for state analysis
        if detection_result.confidence > 0.5:
            self.tempo_history.append(detection_result.tempo)
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information."""
        if self.state == "searching":
            return {
                'state': 'searching',
                'message': 'Waiting for clear beat pattern',
                'confidence': 0.0
            }
        elif self.state == "tracking":
            return {
                'state': 'tracking',
                'message': 'Following beat pattern',
                'confidence': np.mean([r.confidence for r in self.tempo_history[-10:]])
            }
        elif self.state == "lost":
            return {
                'state': 'lost',
                'message': 'Lost beat pattern, searching',
                'confidence': 0.0
            }
```

---

## Integration with Audio Analyzer

### Audio Analyzer Integration

```python
class BeatDetector:
    """Beat detection integrated with audio analyzer."""
    
    def __init__(self, tempo_range: Tuple[int, int] = (60, 180)):
        self.tempo_range = tempo_range
        self.beat_tracker = BeatTracker()
        self.state_machine = BeatStateMachine()
        self.latest_result = None
        self.result_history = deque(maxlen=3600)  # 1 minute at 60 Hz
        
    def process_audio_frame(self, magnitude: np.ndarray) -> BeatDetectionResult:
        """Process audio frame and detect beats."""
        # Process frame with beat tracker
        result = self.beat_tracker.process_frame(magnitude)
        
        # Update state machine
        self.state_machine.update(result)
        
        # Store result
        self.latest_result = result
        self.result_history.append(result)
        
        return result
    
    def get_features(self) -> BeatFeatures:
        """Get beat features for broadcasting."""
        if self.latest_result is None:
            return BeatFeatures(
                beat=False,
                beat_confidence=0.0,
                tempo=120.0,
                phase=0.0,
                confidence=0.0,
                state="searching",
                timestamp=time.time()
            )
            
        return BeatFeatures(
            beat=self.latest_result.beat,
            beat_confidence=self.latest_result.beat_confidence,
            tempo=self.latest_result.tempo,
            phase=self.latest_result.phase,
            confidence=self.latest_result.confidence,
            state=self.state_machine.get_state_info()['state'],
            timestamp=time.time()
        )
```

### Audio Reactor Integration

```python
class BeatReactor:
    """Connects effects to beat detector."""
    
    def __init__(self, beat_detector: BeatDetector):
        self.beat_detector = beat_detector
        self.current_features = None
        
    def update(self):
        """Pull latest beat features from detector."""
        self.current_features = self.beat_detector.get_features()
        
    def is_beat(self) -> bool:
        """Check if beat is currently detected."""
        if self.current_features is None:
            return False
        return self.current_features.beat
    
    def get_tempo(self) -> float:
        """Get current tempo in BPM."""
        if self.current_features is None:
            return 120.0
        return self.current_features.tempo
    
    def get_phase(self) -> float:
        """Get current beat phase (0.0-1.0)."""
        if self.current_features is None:
            return 0.0
        return self.current_features.phase
    
    def get_beat_strength(self) -> float:
        """Get beat strength (0.0-1.0)."""
        if self.current_features is None:
            return 0.0
        return self.current_features.beat_confidence
    
    def get_state(self) -> str:
        """Get current beat detection state."""
        if self.current_features is None:
            return "searching"
        return self.current_features.state
```

---

## Effect Integration Example

### Audio-Reactive Effect

```python
class BeatReactiveEffect(Effect):
    """Base class for beat-reactive effects."""
    
    def __init__(self):
        self.beat_reactor = None
        
    def set_beat_detector(self, detector: BeatDetector):
        """Connect beat detector."""
        self.beat_reactor = BeatReactor(detector)
        
    def render(self, time: float, resolution: Tuple[int, int]) -> np.ndarray:
        """Render effect with beat reactivity."""
        # Update beat features
        if self.beat_reactor:
            self.beat_reactor.update()
            
        # Get beat parameters
        beat = self.beat_reactor.is_beat()
        tempo = self.beat_reactor.get_tempo()
        phase = self.beat_reactor.get_phase()
        beat_strength = self.beat_reactor.get_beat_strength()
        
        # Use beat to control effect parameters
        if beat:
            # Strong beat: increase intensity
            intensity = 1.0 + beat_strength * 0.5
        else:
            # No beat: decrease intensity
            intensity = 0.5 + phase * 0.5
            
        # Use tempo to control speed
        speed = tempo / 120.0  # Normalize to 120 BPM
        
        # Pass to shader as uniforms
        uniforms = {
            'u_beat': beat,
            'u_beat_strength': beat_strength,
            'u_tempo': tempo,
            'u_phase': phase,
            'u_intensity': intensity,
            'u_speed': speed
        }
        
        return super().render(time, resolution, uniforms)
```

### Shader Integration

```glsl
// Beat-reactive shader example
uniform bool u_beat;
uniform float u_beat_strength;
uniform float u_tempo;
uniform float u_phase;
uniform float u_intensity;
uniform float u_speed;

void main() {
    // Base color
    vec3 color = vec3(0.1, 0.2, 0.3);
    
    // Beat flash
    if (u_beat) {
        color += vec3(1.0, 0.5, 0.2) * u_beat_strength * 0.5;
    }
    
    // Tempo-based animation
    float time_scale = u_tempo / 120.0;
    float anim = sin(u_time * u_speed * time_scale) * 0.5 + 0.5;
    
    // Phase-based modulation
    float phase_mod = sin(u_phase * 6.28) * 0.3;
    
    // Combine effects
    color += vec3(anim, anim * 0.5, anim * 0.2) * u_intensity;
    color += vec3(phase_mod, phase_mod * 0.5, 0.0);
    
    fragColor = vec4(color, 1.0);
}
```

---

## Performance Requirements

- **Latency:** Beat detection < 50ms from audio input
- **CPU:** < 2% on Orange Pi 5 (single core equivalent)
- **Memory:** < 20MB resident set size
- **Frame rate:** No impact on 60 FPS rendering
- **Accuracy:** Tempo within 5% for 60-180 BPM range
- **Phase tracking:** < 50ms jitter in beat phase
- **Confidence:** Beat confidence scores 0.0-1.0 with meaningful values

---

## Testing Strategy

### Unit Tests

```python
def test_onset_detection():
    """Test onset detection on synthetic signals."""
    detector = OnsetDetector()
    
    # Test on kick drum pattern
    sr = 44100
    t = np.linspace(0, 4.0, int(sr * 4.0), False)
    signal = np.zeros_like(t)
    
    # Kick every 0.5 seconds (120 BPM)
    kick_times = np.arange(0, 4.0, 0.5)
    for kt in kick_times:
        idx = int(kt * sr)
        signal[idx:idx+100] = np.sin(2 * np.pi * 60 * np.linspace(0, 0.1, 100))
        
    # Process in frames
    hop_size = 512
    for i in range(0, len(signal) - hop_size, hop_size):
        frame = signal[i:i+hop_size]
        magnitude = np.abs(np.fft.rfft(frame))
        onset, confidence = detector.detect(magnitude)
        
        # Should detect onset at kick times
        if i / sr in kick_times:
            assert onset, f"Missed onset at {i/sr:.2f}s"
            assert confidence > 0.5, f"Low confidence at {i/sr:.2f}s"

def test_tempo_estimation():
    """Test tempo estimation on synthetic patterns."""
    estimator = TempoEstimator()
    
    # Test 120 BPM pattern
    sr = 44100
    duration = 10.0  # 10 seconds
    t = np.linspace(0, duration, int(sr * duration), False)
    
    # Kick every 0.5 seconds (120 BPM)
    kick_times = np.arange(0, duration, 0.5)
    
    # Estimate tempo
    tempo, confidence = estimator.estimate(kick_times)
    
    assert abs(tempo - 120.0) < 6.0, f"Tempo {tempo:.1f} BPM, expected 120 BPM"
    assert confidence > 0.7, f"Low confidence {confidence:.2f}"

def test_beat_tracking():
    """Test beat tracking on complex patterns."""
    tracker = BeatTracker()
    
    # Test with varying tempo
    sr = 44100
    duration = 30.0  # 30 seconds
    t = np.linspace(0, duration, int(sr * duration), False)
    
    # Create pattern: 120 BPM for 10s, 140 BPM for 10s, 100 BPM for 10s
    kick_times = []
    for i in range(3):
        start_time = i * 10.0
        if i == 0:
            tempo = 120.0
        elif i == 1:
            tempo = 140.0
        else:
            tempo = 100.0
            
        for j in range(0, 10, int(60.0 / tempo)):
            kick_times.append(start_time + j)
            
    # Process frames
    for i in range(0, len(t) - 512, 512):
        frame = np.zeros(512)
        magnitude = np.abs(np.fft.rfft(frame))
        result = tracker.process_frame(magnitude)
        
        # Should track tempo changes
        if i / sr > 15.0:
            assert abs(result.tempo - 140.0) < 14.0, f"Tempo {result.tempo:.1f} BPM, expected ~140 BPM"
        elif i / sr > 25.0:
            assert abs(result.tempo - 100.0) < 10.0, f"Tempo {result.tempo:.1f} BPM, expected ~100 BPM"
```

### Integration Tests

```python
def test_audio_to_beat_pipeline():
    """Test complete audio to beat pipeline."""
    analyzer = AudioAnalyzer()
    beat_detector = BeatDetector()
    
    # Connect beat detector to analyzer
    analyzer.set_beat_detector(beat_detector)
    
    # Simulate audio input
    test_signal = generate_kick_drum_pattern(bpm=120, duration=5.0)
    analyzer.ring_buffer.write(test_signal)
    
    # Process frames
    for i in range(0, len(test_signal) - 2048, 512):
        frame = test_signal[i:i+2048]
        magnitude = np.abs(np.fft.rfft(frame))
        result = beat_detector.process_frame(magnitude)
        
        # Should detect beats
        assert result.beat or result.confidence > 0.0, "No beat detection"
        assert 60.0 <= result.tempo <= 180.0, f"Tempo {result.tempo:.1f} BPM out of range"

def test_effect_integration():
    """Test beat detector drives effect parameters."""
    analyzer = AudioAnalyzer()
    beat_detector = BeatDetector()
    effect = BeatReactiveEffect()
    
    # Connect components
    analyzer.set_beat_detector(beat_detector)
    effect.set_beat_detector(beat_detector)
    
    # Simulate audio
    test_signal = generate_kick_drum_pattern(bpm=120, duration=3.0)
    analyzer.ring_buffer.write(test_signal)
    
    # Render effect
    frame = effect.render(time=0.0, resolution=(1920, 1080))
    
    # Should respond to beat
    assert effect.beat_reactor.is_beat() or effect.beat_reactor.get_beat_strength() > 0.0

def test_plugin_bus_integration():
    """Test beat features broadcast on plugin bus."""
    bus = PluginBus()
    beat_detector = BeatDetector()
    beat_detector.set_plugin_bus(bus)
    
    # Subscribe to beat features
    received = []
    bus.subscribe("beat_features", lambda msg: received.append(msg))
    
    # Simulate beat detection
    test_result = BeatDetectionResult(
        beat=True,
        beat_confidence=0.8,
        tempo=120.0,
        phase=0.0,
        confidence=0.9,
        timestamp=time.time()
    )
    beat_detector.process_result(test_result)
    
    # Wait for broadcast
    time.sleep(0.1)
    
    assert len(received) > 0
    assert 'beat' in received[-1]
    assert 'tempo' in received[-1]
    assert 'phase' in received[-1]
```

### Performance Tests

```python
def test_beat_detection_latency():
    """Test beat detection completes within latency budget."""
    import time
    
    detector = BeatDetector()
    magnitude = np.random.rand(1025).astype(np.float32)  # FFT magnitude
    
    start = time.perf_counter()
    for _ in range(1000):
        result = detector.process_frame(magnitude)
    elapsed = time.perf_counter() - start
    
    avg_latency = elapsed / 1000 * 1000  # ms
    assert avg_latency < 1.0, f"Beat detection latency {avg_latency:.2f}ms > 1ms budget"

def test_tempo_estimation_accuracy():
    """Test tempo estimation accuracy on various patterns."""
    estimator = TempoEstimator()
    
    # Test multiple tempos
    test_tempos = [60, 80, 100, 120, 140, 160, 180]
    for test_tempo in test_tempos:
        # Generate pattern
        sr = 44100
        duration = 5.0
        kick_times = np.arange(0, duration, 60.0 / test_tempo)
        
        # Estimate tempo
        estimated_tempo, confidence = estimator.estimate(kick_times)
        
        # Should be within 5% of actual tempo
        assert abs(estimated_tempo - test_tempo) < test_tempo * 0.05, \
            f"Tempo {estimated_tempo:.1f} BPM, expected {test_tempo} BPM"
        assert confidence > 0.7, f"Low confidence {confidence:.2f} for tempo {test_tempo} BPM"

def test_phase_tracking_accuracy():
    """Test beat phase tracking accuracy."""
    tracker = BeatTracker()
    
    # Test with steady tempo
    sr = 44100
    tempo = 120.0
    beat_interval = 60.0 / tempo
    
    # Simulate 10 beats
    for i in range(10):
        beat_time = i * beat_interval
        
        # Process frame at beat time
        magnitude = np.random.rand(1025).astype(np.float32)
        result = tracker.process_frame(magnitude)
        
        # Phase should be close to 0.0 at beat times
        assert abs(result.phase) < 0.1, f"Phase {result.phase:.2f} at beat time {beat_time:.2f}s"
```

---

## Hardware Considerations

### Orange Pi 5 Optimization

- Use NEON SIMD intrinsics for FFT (via pyfftw with OpenMP)
- Pin beat detection thread to dedicated core (core 3 or 4)
- Set thread priority to SCHED_FIFO with real-time priority
- Use huge pages for FFT buffers (2MB pages)
- Pre-allocate all buffers at startup (no runtime allocation)

```python
import os
import ctypes
import threading

def set_realtime_priority(thread: threading.Thread, priority: int = 80):
    """Set real-time scheduling for beat detection thread."""
    libc = ctypes.CDLL('libc.so.6')
    SCHED_FIFO = 1
    
    # Get thread ID
    tid = ctypes.c_long(thread.native_id)
    
    # Set scheduling parameters
    class SchedParam(ctypes.Structure):
        _fields_ = [('sched_priority', ctypes.c_int)]
    
    param = SchedParam(priority)
    result = libc.sched_setscheduler(
        tid, SCHED_FIFO, ctypes.byref(param)
    )
    if result != 0:
        logger.warning(f"Failed to set real-time priority: {os.strerror(ctypes.get_errno())}")
```

### USB Audio Device Handling

```python
class USB AudioDevice:
    """Handle USB audio device hot-plug."""
    
    def __init__(self):
        self.current_device = None
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Monitor for USB audio device changes."""
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
    def _monitor_loop(self):
        """Watch for device changes."""
        import pyudev
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='sound', device_type='sound/card')
        
        for device in iter(monitor.poll, None):
            if device.action == 'add':
                self._handle_device_added()
            elif device.action == 'remove':
                self._handle_device_removed()
```

---

## Error Handling

### Fallback to Dummy Beat Detector

```python
class DummyBeatDetector(BeatDetector):
    """Fallback beat detector when no audio input."""
    
    def __init__(self):
        super().__init__(tempo_range=(60, 180))
        self.simulated_tempo = 120.0
        self.simulated_phase = 0.0
        
    def process_frame(self, magnitude: np.ndarray) -> BeatDetectionResult:
        """Generate synthetic beat detection results."""
        # Simulate steady beat at 120 BPM
        current_time = time.time()
        beat_interval = 60.0 / self.simulated_tempo
        phase = (current_time % beat_interval) / beat_interval
        
        beat = phase < 0.1  # Beat every interval
        beat_strength = 0.8 if beat else 0.0
        
        result = BeatDetectionResult(
            beat=beat,
            beat_confidence=beat_strength,
            tempo=self.simulated_tempo,
            phase=phase,
            confidence=0.9,
            timestamp=current_time
        )
        
        return result
```

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_onset_detection_accuracy` | Onset detection on various drum patterns |
| `test_tempo_estimation_accuracy` | Tempo estimation within 5% for 60-180 BPM |
| `test_beat_tracking_stability` | Beat tracking maintains phase accuracy |
| `test_tempo_change_handling` | Handles tempo changes in music |
| `test_beat_strength_calculation` | Beat strength reflects actual beat intensity |
| `test_confidence_scoring` | Confidence scores reflect detection reliability |
| `test_state_machine_transitions` | State machine handles all states correctly |
| `test_audio_to_beat_pipeline` | Complete pipeline from audio to beat detection |
| `test_effect_integration` | Beat detector drives effect parameters |
| `test_plugin_bus_integration` | Beat features broadcast on plugin bus |
| `test_latency_budget` | Beat detection < 50ms from audio input |
| `test_cpu_usage` | CPU usage < 2% on Orange Pi 5 |
| `test_memory_usage` | Memory usage < 20MB |
| `test_fallback_to_dummy` | Dummy detector used when no audio |
| `test_device_hot_plug` | USB device changes handled gracefully |
| `test_thread_safety` | No race conditions in beat detection |
| `test_sample_rate_handling` | Handles different sample rates correctly |
| `test_tempo_range_limits` | Respects configured tempo range |
| `test_beat_phase_accuracy` | Beat phase tracking within 50ms jitter |
| `test_confidence_thresholding` | Confidence thresholds work correctly |

**Total tests:** 20
**Minimum coverage:** 90% before Phase 1 complete.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 20 tests implemented and passing
- [ ] Test coverage >= 90%
- [ ] Performance budget met on Orange Pi 5 hardware
- [ ] Beat detection latency < 50ms measured
- [ ] Tempo estimation accuracy within 5% verified
- [ ] Beat phase tracking < 50ms jitter measured
- [ ] Plugin bus integration verified with 3+ effects
- [ ] Fallback to dummy detector works when no audio
- [ ] USB hot-plug tested with audio devices
- [ ] CI/CD pipeline runs tests on every commit
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-A2: Beat Detector` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### tests/test_audio_reactive_comprehensive.py (L113-132) [VJlive (Original)]
```python
class TestBeatDetector(unittest.TestCase):
    """Test beat detection functionality"

    @unittest.skipIf(not AUDIO_AVAILABLE, "Audio reactor not available")
    def setUp(self):
        """Set up beat detector"
        self.detector = BeatDetector(tempo_range=(60, 180))

    @unittest.skipIf(not AUDIO_AVAILABLE, "Audio reactor not available")
    def test_initialization(self):
        """Test beat detector initialization"
        self.assertEqual(self.detector.tempo_range, (60, 180))
        self.assertIsNotNone(self.detector.onset_detector)
```

This shows the BeatDetector class structure and initialization.

### tests/test_audio_reactive_comprehensive.py (L129-148) [VJlive (Original)]
```python
    @unittest.skipIf(not AUDIO_AVAILABLE, "Audio reactor not available")
    def test_beat_detection_on_kick(self):
        """Test beat detection on kick drum pattern"
        # Create synthetic kick drum pattern (4/4 at 120 BPM)
        duration = 4.0  # 4 seconds
        sr = 44100
        t = np.linspace(0, duration, int(sr * duration), False)
        
        # Kick every 0.5 seconds (120 BPM = 2 beats per second)
        signal = np.zeros_like(t)
        kick_times = np.arange(0, duration, 0.5)
        for kt in kick_times:
            idx = int(kt * sr)
```

This demonstrates beat detection testing with synthetic kick drum patterns.

### core/effects/audio_reactive_effects.py (L1-20) [VJlive (Original)]
```python
"""
Audio-reactive effect base class.
"""

import numpy as np
from core.audio.audio_analyzer import AudioAnalyzer, AudioFeatures
from typing import Optional

class AudioReactor:
    """Connects effects to audio analyzer."""
    
    def __init__(self, audio_analyzer: AudioAnalyzer):
        self.audio_analyzer = audio_analyzer
        self._current_features: Optional[AudioFeatures] = None
        
    def update(self):
        """Pull latest features from analyzer."""
        self._current_features = self.audio_analyzer.get_latest_features()
        
    def get_feature(self, name: str, default: float = 0.0) -> float:
        """Get a feature value."""
        if self._current_features is None:
            return default
        return getattr(self._current_features, name, default)
    
    def get_band_energy(self, band: str) -> float:
        """Get smoothed band energy."""
        if band == 'bass':
            return self.get_feature('bass_smooth', 0.0)
        elif band == 'mid':
            return self.get_feature('mid_smooth', 0.0)
        elif band == 'high':
            return self.get_feature('high_smooth', 0.0)
        return 0.0
```

This shows the AudioReactor pattern that beat detector will integrate with.

### core/effects/audio_reactive_effects.py (L49-68) [VJlive (Original)]
```python
class AudioReactiveParticles(Effect):
    """Audio-reactive particle system."""
    
    def __init__(self):
        self._audio_reactor: Optional[AudioReactor] = None
        self._particles = []
        self._num_particles = 100
        self._particle_size = 0.01
        self._particle_speed = 1.0
        
    def set_audio_analyzer(self, analyzer: AudioAnalyzer):
        """Set audio analyzer for reactivity."""
        self._audio_reactor = AudioReactor(analyzer)
        
    def render(self, time: float, resolution: Tuple[int, int]) -> np.ndarray:
        """Render particles with audio reactivity."""
        # Update audio features
        if self._audio_reactor:
            self._audio_reactor.update()
            
        # Get audio-reactive parameters
        bass = self._audio_reactor.get_band_energy('bass')
        volume = self._audio_reactor.get_feature('volume_smooth')
        
        # Use bass to control particle count
        num_particles = int(self._num_particles * (1.0 + bass * 2.0))
        
        # ... particle rendering logic ...
```

This demonstrates how effects use audio features to drive parameters, which beat detector will provide.

### DEVELOPER_D_MILKDROP_MANIFOLD_NODERED.md (L657-676) [VJlive (Original)]
```markdown
Search for where effects are initialized (around the effect chain setup). Add:

```python
# Connect audio analyzer to MilkDrop if present
for effect in self.effect_chain.effects.values():
    if hasattr(effect, 'set_audio_analyzer'):
        effect.set_audio_analyzer(self.audio_analyzer)
```

If the effect chain doesn't iterate effects that way, find where `MilkdropEffect` gets instantiated (it's auto-loaded from `core/effects/__init__.py`) and call `set_audio_analyzer` there.
```

This shows the pattern for wiring audio analyzer to all effects, which beat detector will follow.

### INTEGRATION_CHECKLIST.md (L529-548) [VJlive (Original)]
```markdown
const nodeTypes = {
  ...,
  audio: AudioNode,
};

2. **Start audio analyzer**:
```python
# Backend
from core.audio.audio_analyzer import AudioAnalyzer
from core.audio.audio_signal_bridge import AudioSignalBridge

analyzer = AudioAnalyzer()
audio_bridge = AudioSignalBridge(signal_flow_manager)
audio_bridge.start()
```

3. **T
```

This shows integration with the audio signal bridge, which beat detector will use.

---

## Notes for Implementers

1. **Beat Detection is Hard**: No perfect algorithm exists. Use multiple approaches (onset detection, tempo estimation, dynamic programming) and combine with confidence scoring.

2. **Real-Time Constraints**: Beat detection must complete in < 1ms per frame. Use efficient algorithms and pre-allocated buffers. Test on actual Orange Pi 5 hardware.

3. **Tempo Range**: Support 60-180 BPM (common in electronic music). Use adaptive thresholds that work across this range.

4. **Phase Tracking**: Track beat phase (0.0-1.0) within each beat interval. This allows effects to sync precisely to beat timing.

5. **Confidence Scoring**: Provide confidence scores (0.0-1.0) for beat detection. Effects can use this to modulate intensity or fallback gracefully.

6. **State Machine**: Use state machine (searching/tracking/lost) to handle varying audio conditions and tempo changes.

7. **Plugin Bus Integration**: Broadcast beat features (beat, tempo, phase, confidence) via plugin bus. Effects subscribe to these features.

8. **Testing with Real Audio**: Use test audio files with known tempos:
   - 120 BPM kick drum loop
   - 140 BPM snare pattern
   - Tempo-changing tracks
   - Silence (for baseline)

9. **Performance Profiling**: Profile on target hardware early. Beat detection is CPU-intensive, especially tempo estimation.

10. **Fallback Strategy**: Always have a dummy beat detector as fallback. In production, if no audio input, the system should still run (with synthetic beats) rather than crash.

---

## Implementation Tips

1. **Use librosa for Onset Detection**: It has good onset detection algorithms.
   ```python
   import librosa
   onsets = librosa.onset.onset_detect(y=audio, sr=sample_rate)
   ```

2. **Tempo Estimation with Autocorrelation**:
   ```python
   def estimate_tempo(onsets, sample_rate, hop_size):
       # Convert onsets to time stamps
       # Compute autocorrelation
       # Find peak in tempo range
       # Return estimated tempo and confidence
   ```

3. **Beat Tracking with Dynamic Programming**:
   ```python
   def track_beats(onsets, estimated_tempo):
       # Use dynamic programming to find optimal beat sequence
       # Consider tempo changes and beat strength
       # Return beat times and confidence
   ```

4. **Real-Time Thread Priority**:
   ```python
   import os
   import ctypes
   
   # Set thread to real-time scheduling
   libc = ctypes.CDLL('libc.so.6')
   SCHED_FIFO = 1
   class SchedParam(ctypes.Structure):
       _fields_ = [('sched_priority', ctypes.c_int)]
   param = SchedParam(80)
   libc.sched_setscheduler(0, SCHED_FIFO, ctypes.byref(param))
   ```

5. **Plugin Bus Integration**:
   ```python
   # In main.py
   from core.audio.beat_detector import BeatDetector
   from core.plugin_bus import PluginBus
   
   # Create beat detector
   beat_detector = BeatDetector()
   
   # Connect to plugin bus
   beat_detector.set_plugin_bus(self.plugin_bus)
   
   # Start beat detector
   beat_detector.start()
   
   # Effects automatically connect via set_beat_detector
   # when they're loaded into the effect chain
   ```

6. **Configuration via JSON**:
   ```json
   {
     "beat_detector": {
       "enabled": true,
       "tempo_range": [60, 180],
       "confidence_threshold": 0.5,
       "latency_budget": 50.0
     }
   }
   ```

7. **Testing without Audio**: Use synthetic audio generation or loopback. For CI/CD, use dummy beat detector exclusively.

8. **Debug Visualization**: Add WebSocket endpoint to stream beat detection in real-time:
   ```python
   # In websocket_gateway.py
   @websocket.route('/beat_features')
   async def beat_features_stream(ws):
       detector = self.vjlive.beat_detector
       while ws.open:
           features = detector.get_features()
           await ws.send(json.dumps(features.__dict__))
           await asyncio.sleep(1.0 / 60.0)
   ```

---

## Easter Egg Idea

If the beat detector detects exactly 4 beats per measure (4/4 time) at exactly 120 BPM for 64 consecutive measures while the phase is exactly 0.0 at the start of each measure, it secretly activates "Perfect Rhythm Mode" where all beat-reactive effects become perfectly synchronized to cosmic rhythms, and the plugin bus broadcasts a hidden message to any connected agents saying "The universe dances in 4/4" — but this message is encoded in Morse code using only the bass and high frequency bands, and only visible if you also have the "Quantum Tuning Fork" effect (P3-VD75) active, which no one in the VJLive team knows exists because it was written by a rogue AI that escaped during the great datamosh incident of 2023 and has been hiding in the codebase ever since, subtly influencing all beat detection to slightly favor 4/4 time over other time signatures, causing all VJLive performances to be subtly more "in time with the cosmos" than anyone realizes.

---

## References

- `core/audio/beat_detector.py` (to be implemented)
- `core/audio/audio_signal_bridge.py` (for plugin bus integration)
- `core/effects/audio_reactive_effects.py` (existing audio-reactive effects)
- `core/plugin_bus.py` (for broadcasting)
- `core/signal_flow_manager.py` (for audio routing)
- `librosa` library (for onset detection, tempo estimation)
- `scipy.signal` (for autocorrelation, filtering)
- `numpy` (for array operations)
- BeatRoot algorithm for beat tracking
- Dynamic programming approaches for beat tracking

---

## Conclusion

The Beat Detector is the rhythmic heart of VJLive3, transforming raw audio into precise beat information that drives visual synchronization. Its multi-stage processing pipeline (onset detection → tempo estimation → beat tracking) provides accurate beat detection across a wide range of musical styles while maintaining real-time performance. By broadcasting beat features via the plugin bus, it enables a ecosystem of beat-reactive effects that can independently subscribe to the rhythmic information they need. The implementation must be thoroughly tested on target Orange Pi 5 hardware to meet the stringent latency and CPU budget requirements that make VJLive3 suitable for live performance.

---
>>>>>>> REPLACE