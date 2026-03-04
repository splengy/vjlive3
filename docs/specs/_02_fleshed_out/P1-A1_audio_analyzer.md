# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P1-A1_audio_analyzer.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-A1 — Audio Analyzer

**What This Module Does**

Implements a real-time audio analysis engine that processes microphone or line-in audio input to extract musical features (beat, onset, pitch, spectral characteristics) and broadcasts them via the plugin bus for consumption by audio-reactive visual effects. The analyzer uses a multi-stage processing pipeline: FFT computation, feature extraction, temporal smoothing, and event detection, all running in a dedicated audio processing thread to maintain 60 FPS video performance.

---

## Architecture Decisions

- **Pattern:** Producer-Consumer with Lock-Free Ring Buffer
- **Rationale:** Audio processing must run at audio sample rates (44.1/48 kHz) without blocking the main rendering thread. A lock-free ring buffer allows the audio thread to push analysis results while the main thread pulls them at 60 Hz, eliminating contention and ensuring deterministic performance.
- **Constraints:**
  - Must process 1024-sample FFT in < 2ms on Orange Pi 5
  - Must support both microphone and line-in inputs
  - Must handle sample rate conversion (44.1/48 kHz → internal 48 kHz)
  - Must broadcast features via plugin bus for multi-consumer use
  - Must provide fallback to dummy analyzer when no audio device available
  - Must not cause audio dropouts or glitches

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-2 | `core/audio/audio_analyzer.py` | AudioAnalyzer | Port — core analysis logic |
| VJlive-2 | `core/effects/audio_reactive_effects.py` | AudioReactor | Reference — feature consumption |
| VJlive-2 | `DEVELOPER_D_MILKDROP_MANIFOLD_NODERED.md` | set_audio_analyzer | Port — integration pattern |
| VJlive-2 | `DEVELOPER_PROMPTS/15_MOOD_MANIFOLD_PRESET_SYSTEM.md` | Audio reactivity | Reference — feature requirements |
| VJlive-2 | `INTEGRATION_CHECKLIST.md` | Audio signal bridge | Port — bus integration |

---

## Public Interface

```python
class AudioAnalyzer:
    """Real-time audio feature extraction engine."""
    
    def __init__(self, config: AudioAnalyzerConfig) -> None:...
    def start(self) -> None:...
    def stop(self) -> None:...
    def get_latest_features(self) -> AudioFeatures:...
    def get_feature_history(self, duration_seconds: float) -> List[AudioFeatures]:...
    def set_plugin_bus(self, bus: PluginBus) -> None:...
    def list_input_devices(self) -> List[AudioDevice]:...
    def select_input_device(self, device_id: int) -> bool:...
    def get_signal_flow_manager(self) -> SignalFlowManager:...
    def get_spectrum_data(self) -> np.ndarray:...
    def get_waveform_data(self) -> np.ndarray:...
    def reset(self) -> None:...
    def get_peak_level(self) -> float:...
    def get_rms_level(self) -> float:...
    def is_clipping(self) -> bool:...
    def get_latency(self) -> float:...
```

---

## Audio Features Extracted

### Core Features (Broadcast via Plugin Bus)

```python
@dataclass
class AudioFeatures:
    """Container for extracted audio features."""
    timestamp: float  # Unix timestamp in seconds
    beat: bool  # Beat onset detected
    beat_confidence: float  # 0.0-1.0 confidence
    onset: bool  # Any onset detected (not just beat)
    onset_confidence: float  # 0.0-1.0 confidence
    bass: float  # Bass energy (20-150 Hz) normalized 0.0-1.0
    mid: float  # Mid energy (150-2000 Hz) normalized 0.0-1.0
    high: float  # High energy (2000-20000 Hz) normalized 0.0-1.0
    volume: float  # Overall volume (RMS) normalized 0.0-1.0
    pitch: float  # Fundamental frequency in Hz (0 if unpitched)
    pitch_confidence: float  # 0.0-1.0 confidence
    spectral_centroid: float  # Brightness measure (0.0-1.0)
    spectral_rolloff: float  # Energy rolloff point (0.0-1.0)
    spectral_flux: float  # Spectral change rate (0.0-1.0)
    zero_crossing_rate: float  # Noisiness measure (0.0-1.0)
    harmony: float  # Harmonic content (0.0-1.0)
    percussive: float  # Percussive content (0.0-1.0)
    # Smoothed versions (temporal integration)
    bass_smooth: float  # Exponential moving average
    mid_smooth: float
    high_smooth: float
    volume_smooth: float
    # Beat tracking
    bpm: float  # Estimated tempo in BPM
    beat_phase: float  # 0.0-1.0 phase within beat
    # Loudness (EBU R128)
    loudness_integrated: float  # Integrated loudness in LUFS
    loudness_shortterm: float  # Short-term loudness in LUFS
    loudness_range: float  # Loudness range in LU
```

---

## Processing Pipeline

### 1. Audio Input

```python
class AudioInput:
    """Audio capture from system devices."""
    
    def __init__(self, sample_rate: int = 48000, buffer_size: int = 1024):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.device = None
        self.stream = None
        
    def list_devices(self) -> List[AudioDevice]:
        """Enumerate available input devices."""
        import sounddevice as sd
        devices = []
        for i, dev in enumerate(sd.query_devices()):
            if dev['max_input_channels'] > 0:
                devices.append(AudioDevice(
                    id=i,
                    name=dev['name'],
                    channels=dev['max_input_channels'],
                    default_samplerate=dev['default_samplerate']
                ))
        return devices
    
    def open_device(self, device_id: int) -> bool:
        """Open selected input device."""
        try:
            self.stream = sd.InputStream(
                device=device_id,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                callback=self._audio_callback
            )
            self.stream.start()
            return True
        except Exception as e:
            logger.error(f"Failed to open audio device: {e}")
            return False
    
    def _audio_callback(self, indata: np.ndarray, frames: int, time, status):
        """Callback for audio capture thread."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        # Push to ring buffer
        self.ring_buffer.write(indata[:, 0])  # Mono
```

### 2. Pre-processing

```python
class AudioPreprocessor:
    """Pre-process audio before analysis."""
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        # DC offset filter (high-pass at 10 Hz)
        self.dc_filter = DCBlockFilter()
        # Anti-aliasing filter (low-pass at Nyquist)
        self.anti_alias = ButterworthFilter(
            cutoff=sample_rate / 2 - 1000,
            sample_rate=sample_rate,
            order=8
        )
        # Normalization (peak limiter)
        self.normalizer = AudioNormalizer(threshold=0.99)
        
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply pre-processing chain."""
        # Remove DC offset
        audio = self.dc_filter.filter(audio)
        # Anti-alias
        audio = self.anti_alias.filter(audio)
        # Normalize
        audio = self.normalizer.normalize(audio)
        return audio
```

### 3. FFT Computation

```python
class FFTProcessor:
    """Compute frequency domain representation."""
    
    def __init__(self, fft_size: int = 2048, sample_rate: int = 48000):
        self.fft_size = fft_size
        self.sample_rate = sample_rate
        self.window = scipy.signal.windows.hann(fft_size)
        # Pre-allocate FFT buffer
        self.fft_buffer = np.zeros(fft_size, dtype=np.float32)
        self.fft_plan = pyfftw.builders.rfft(
            self.fft_buffer,
            threads=4  # Use 4 threads on Orange Pi 5
        )
        
    def compute(self, audio: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute FFT of audio frame."""
        # Apply window
        windowed = audio * self.window
        # Compute FFT
        spectrum = self.fft_plan(windowed)
        # Magnitude
        magnitude = np.abs(spectrum)
        # Phase (for pitch detection)
        phase = np.angle(spectrum)
        return magnitude, phase
```

### 4. Feature Extraction

```python
class FeatureExtractor:
    """Extract musical features from FFT."""
    
    def __init__(self, sample_rate: int = 48000, fft_size: int = 2048):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        # Frequency bands (in Hz)
        self.band_edges = {
            'bass': (20, 150),
            'mid': (150, 2000),
            'high': (2000, 20000)
        }
        # Band indices in FFT bins
        self.band_indices = self._compute_band_indices()
        # Beat detection
        self.beat_detector = BeatDetector(sample_rate=sample_rate)
        # Onset detection
        self.onset_detector = OnsetDetector(sample_rate=sample_rate)
        # Pitch tracking
        self.pitch_tracker = PitchTracker(sample_rate=sample_rate)
        # Spectral features
        self.spectral_features = SpectralFeatureExtractor()
        
    def extract(self, magnitude: np.ndarray, phase: np.ndarray) -> AudioFeatures:
        """Extract all features from FFT."""
        # Band energies
        bass = self._band_energy(magnitude, 'bass')
        mid = self._band_energy(magnitude, 'mid')
        high = self._band_energy(magnitude, 'high')
        
        # Volume (RMS)
        volume = np.sqrt(np.mean(magnitude ** 2))
        
        # Beat detection
        beat, beat_confidence = self.beat_detector.detect(magnitude)
        
        # Onset detection
        onset, onset_confidence = self.onset_detector.detect(magnitude)
        
        # Pitch tracking
        pitch, pitch_confidence = self.pitch_tracker.track(magnitude, phase)
        
        # Spectral features
        spectral_centroid = self.spectral_features.centroid(magnitude)
        spectral_rolloff = self.spectral_features.rolloff(magnitude)
        spectral_flux = self.spectral_features.flux(magnitude)
        zero_crossing_rate = self.spectral_features.zcr(magnitude)
        
        # Harmonic-percussive separation
        harmony, percussive = self.spectral_features.hpss(magnitude)
        
        return AudioFeatures(
            timestamp=time.time(),
            beat=beat,
            beat_confidence=beat_confidence,
            onset=onset,
            onset_confidence=onset_confidence,
            bass=bass,
            mid=mid,
            high=high,
            volume=volume,
            pitch=pitch,
            pitch_confidence=pitch_confidence,
            spectral_centroid=spectral_centroid,
            spectral_rolloff=spectral_rolloff,
            spectral_flux=spectral_flux,
            zero_crossing_rate=zero_crossing_rate,
            harmony=harmony,
            percussive=percussive,
            bass_smooth=self._smooth('bass', bass),
            mid_smooth=self._smooth('mid', mid),
            high_smooth=self._smooth('high', high),
            volume_smooth=self._smooth('volume', volume),
            bpm=self.beat_detector.bpm,
            beat_phase=self.beat_detector.phase,
            loudness_integrated=self.loudness_meter.integrated,
            loudness_shortterm=self.loudness_meter.shortterm,
            loudness_range=self.loudness_meter.range
        )
```

### 5. Temporal Smoothing

```python
class TemporalSmoother:
    """Apply exponential moving average to features."""
    
    def __init__(self, time_constant: float = 0.1, sample_rate: int = 60):
        """
        Args:
            time_constant: Smoothing time constant in seconds
            sample_rate: Update rate in Hz (typically 60 for VJLive)
        """
        self.alpha = 1.0 - np.exp(-1.0 / (time_constant * sample_rate))
        self.state = {}
        
    def smooth(self, feature_name: str, value: float) -> float:
        """Apply EMA smoothing to a feature."""
        if feature_name not in self.state:
            self.state[feature_name] = value
        else:
            self.state[feature_name] = (
                self.alpha * value +
                (1 - self.alpha) * self.state[feature_name]
            )
        return self.state[feature_name]
```

### 6. Plugin Bus Broadcasting

```python
class AudioBroadcaster:
    """Broadcast audio features via plugin bus."""
    
    def __init__(self, plugin_bus: PluginBus):
        self.bus = plugin_bus
        self.topic = "audio_features"
        
    def broadcast(self, features: AudioFeatures):
        """Publish features to plugin bus."""
        # Convert to dict for JSON serialization
        data = {
            'timestamp': features.timestamp,
            'beat': features.beat,
            'beat_confidence': features.beat_confidence,
            'onset': features.onset,
            'onset_confidence': features.onset_confidence,
            'bass': features.bass,
            'mid': features.mid,
            'high': features.high,
            'volume': features.volume,
            'pitch': features.pitch,
            'pitch_confidence': features.pitch_confidence,
            'spectral_centroid': features.spectral_centroid,
            'spectral_rolloff': features.spectral_rolloff,
            'spectral_flux': features.spectral_flux,
            'zero_crossing_rate': features.zero_crossing_rate,
            'harmony': features.harmony,
            'percussive': features.percussive,
            'bpm': features.bpm,
            'beat_phase': features.beat_phase
        }
        
        # Publish to bus
        self.bus.publish(self.topic, data)
```

---

## Threading Model

```python
class AudioAnalyzer:
    """Main analyzer with thread management."""
    
    def __init__(self, config: AudioAnalyzerConfig):
        self.config = config
        self.running = False
        self.audio_thread = None
        self.ring_buffer = LockFreeRingBuffer(
            capacity=config.buffer_size * 4,
            dtype=np.float32
        )
        self.preprocessor = AudioPreprocessor()
        self.fft_processor = FFTProcessor(
            fft_size=config.fft_size,
            sample_rate=config.sample_rate
        )
        self.feature_extractor = FeatureExtractor(
            sample_rate=config.sample_rate,
            fft_size=config.fft_size
        )
        self.smoother = TemporalSmoother(
            time_constant=0.1,
            sample_rate=60  # Match rendering frame rate
        )
        self.broadcaster = None
        self.latest_features = None
        self.feature_history = deque(maxlen=3600)  # 1 minute at 60 Hz
        
    def start(self):
        """Start audio processing thread."""
        if self.running:
            return
            
        self.running = True
        self.audio_thread = threading.Thread(
            target=self._audio_loop,
            name="AudioAnalyzer",
            daemon=True
        )
        self.audio_thread.start()
        
    def stop(self):
        """Stop audio processing thread."""
        self.running = False
        if self.audio_thread:
            self.audio_thread.join(timeout=2.0)
            
    def _audio_loop(self):
        """Main audio processing loop (runs in separate thread)."""
        while self.running:
            # Read audio from ring buffer (blocking)
            audio = self.ring_buffer.read(self.config.fft_size)
            if len(audio) < self.config.fft_size:
                continue
                
            # Pre-process
            audio = self.preprocessor.process(audio)
            
            # FFT
            magnitude, phase = self.fft_processor.compute(audio)
            
            # Extract features
            features = self.feature_extractor.extract(magnitude, phase)
            
            # Smooth features
            features.bass_smooth = self.smoother.smooth('bass', features.bass)
            features.mid_smooth = self.smoother.smooth('mid', features.mid)
            features.high_smooth = self.smoother.smooth('high', features.high)
            features.volume_smooth = self.smoother.smooth('volume', features.volume)
            
            # Store latest
            self.latest_features = features
            self.feature_history.append(features)
            
            # Broadcast to plugin bus (if connected)
            if self.broadcaster:
                self.broadcaster.broadcast(features)
```

---

## Configuration

```python
@dataclass
class AudioAnalyzerConfig:
    """Configuration for audio analyzer."""
    sample_rate: int = 48000  # Internal sample rate
    fft_size: int = 2048  # FFT window size
    buffer_size: int = 1024  # Audio buffer size
    hop_size: int = 512  # FFT hop size (for overlap)
    smoothing_time: float = 0.1  # Temporal smoothing in seconds
    broadcast_rate: float = 60.0  # Features broadcast per second
    enable_pitch_tracking: bool = True
    enable_beat_detection: bool = True
    enable_onset_detection: bool = True
    enable_loudness_metering: bool = True
    fallback_to_dummy: bool = True  # Use dummy if no device
```

---

## Integration with Effects

### Audio Reactor Pattern

```python
class AudioReactor:
    """Connects effects to audio analyzer."""
    
    def __init__(self, audio_analyzer: AudioAnalyzer):
        self.audio_analyzer = audio_analyzer
        self.current_features = None
        
    def update(self):
        """Pull latest features from analyzer."""
        self.current_features = self.audio_analyzer.get_latest_features()
        
    def get_feature(self, feature_name: str, default: float = 0.0) -> float:
        """Get a specific feature value."""
        if self.current_features is None:
            return default
        return getattr(self.current_features, feature_name, default)
    
    def get_band_energy(self, band: str) -> float:
        """Get smoothed band energy."""
        if band == 'bass':
            return self.get_feature('bass_smooth')
        elif band == 'mid':
            return self.get_feature('mid_smooth')
        elif band == 'high':
            return self.get_feature('high_smooth')
        else:
            return default
```

### Effect Integration Example

```python
class AudioReactiveEffect(Effect):
    """Base class for audio-reactive effects."""
    
    def __init__(self):
        self.audio_reactor = None
        
    def set_audio_analyzer(self, analyzer: AudioAnalyzer):
        """Connect audio analyzer."""
        self.audio_reactor = AudioReactor(analyzer)
        
    def render(self, time: float, resolution: Tuple[int, int]) -> np.ndarray:
        """Render effect with audio reactivity."""
        # Update audio features
        if self.audio_reactor:
            self.audio_reactor.update()
            
        # Use audio features in shader
        bass = self.audio_reactor.get_band_energy('bass')
        volume = self.audio_reactor.get_feature('volume_smooth')
        
        # Pass to shader as uniforms
        uniforms = {
            'u_bass': bass,
            'u_volume': volume,
            'u_beat': self.audio_reactor.get_feature('beat', False)
        }
        
        return super().render(time, resolution, uniforms)
```

---

## Performance Requirements

- **Latency:** Audio input to feature broadcast < 50ms
- **CPU:** < 5% on Orange Pi 5 (single core equivalent)
- **Memory:** < 50MB resident set size
- **Threading:** Audio thread real-time priority (SCHED_FIFO)
- **Dropout-free:** Zero audio buffer underruns during capture
- **Frame rate:** No impact on 60 FPS rendering

---

## Testing Strategy

### Unit Tests

```python
def test_fft_processor_accuracy():
    """Test FFT against known signal."""
    # Generate 440 Hz sine wave
    t = np.linspace(0, 1, 48000, endpoint=False)
    signal = np.sin(2 * np.pi * 440 * t)
    
    processor = FFTProcessor(fft_size=2048, sample_rate=48000)
    magnitude, phase = processor.compute(signal[:2048])
    
    # Find peak frequency
    freqs = np.fft.rfftfreq(2048, 1/48000)
    peak_idx = np.argmax(magnitude)
    peak_freq = freqs[peak_idx]
    
    assert abs(peak_freq - 440) < 1.0, f"Peak at {peak_freq} Hz, expected 440 Hz"

def test_feature_extractor_consistency():
    """Test feature extraction produces valid ranges."""
    # Generate test signal
    signal = np.random.randn(2048).astype(np.float32)
    magnitude = np.abs(np.fft.rfft(signal))
    
    extractor = FeatureExtractor()
    features = extractor.extract(magnitude, np.angle(np.fft.rfft(signal)))
    
    # Validate ranges
    assert 0.0 <= features.bass <= 1.0
    assert 0.0 <= features.mid <= 1.0
    assert 0.0 <= features.high <= 1.0
    assert 0.0 <= features.volume <= 1.0
    assert 0.0 <= features.beat_confidence <= 1.0
    assert 0.0 <= features.onset_confidence <= 1.0
    assert 0.0 <= features.spectral_centroid <= 1.0
```

### Integration Tests

```python
def test_audio_to_effect_pipeline():
    """Test audio features drive effect parameters."""
    analyzer = AudioAnalyzer()
    effect = AudioReactiveEffect()
    effect.set_audio_analyzer(analyzer)
    
    # Simulate audio input
    test_signal = generate_test_signal()  # e.g., kick drum
    analyzer.ring_buffer.write(test_signal)
    
    # Render effect
    frame = effect.render(time=0.0, resolution=(1920, 1080))
    
    # Verify effect responds to audio
    assert effect.audio_reactor.get_band_energy('bass') > 0.5

def test_plugin_bus_broadcast():
    """Test features broadcast on plugin bus."""
    bus = PluginBus()
    analyzer = AudioAnalyzer()
    analyzer.set_plugin_bus(bus)
    
    # Subscribe to audio features
    received = []
    bus.subscribe("audio_features", lambda msg: received.append(msg))
    
    # Simulate audio
    analyzer.ring_buffer.write(np.random.randn(2048))
    
    # Wait for broadcast
    time.sleep(0.1)
    
    assert len(received) > 0
    assert 'bass' in received[-1]
    assert 'volume' in received[-1]
```

### Performance Tests

```python
def test_fft_latency():
    """Test FFT computation completes within budget."""
    import time
    
    processor = FFTProcessor(fft_size=2048)
    signal = np.random.randn(2048).astype(np.float32)
    
    start = time.perf_counter()
    for _ in range(1000):
        magnitude, phase = processor.compute(signal)
    elapsed = time.perf_counter() - start
    
    avg_latency = elapsed / 1000 * 1000  # ms
    assert avg_latency < 2.0, f"FFT latency {avg_latency:.2f}ms > 2ms budget"

def test_feature_extraction_throughput():
    """Test feature extraction keeps up with 60 Hz."""
    import time
    
    extractor = FeatureExtractor()
    magnitude = np.random.rand(1025).astype(np.float32)
    phase = np.random.rand(1025).astype(np.float32)
    
    # Run for 1 second
    start = time.perf_counter()
    count = 0
    while time.perf_counter() - start < 1.0:
        features = extractor.extract(magnitude, phase)
        count += 1
        
    assert count >= 60, f"Only {count} feature extractions/sec, need 60"
```

---

## Hardware Considerations

### Orange Pi 5 Optimization

- Use NEON SIMD intrinsics for FFT (via pyfftw with OpenMP)
- Pin audio thread to dedicated core (core 3 or 4)
- Set thread priority to SCHED_FIFO with real-time priority
- Use huge pages for FFT buffers (2MB pages)
- Pre-allocate all buffers at startup (no runtime allocation)

```python
import os
import ctypes
import threading

def set_realtime_priority(thread: threading.Thread, priority: int = 80):
    """Set real-time scheduling for audio thread."""
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

### Fallback to Dummy Analyzer

```python
class DummyAudioAnalyzer(AudioAnalyzer):
    """Fallback analyzer when no audio device available."""
    
    def __init__(self):
        super().__init__(AudioAnalyzerConfig())
        self.simulated_beat_phase = 0.0
        
    def start(self):
        """Start simulated audio."""
        # Generate synthetic features
        self.running = True
        self.audio_thread = threading.Thread(
            target=self._simulate_loop,
            daemon=True
        )
        self.audio_thread.start()
        
    def _simulate_loop(self):
        """Generate synthetic audio features."""
        while self.running:
            # Simulate beat every 0.5 seconds
            beat = (time.time() % 0.5) < 0.1
            
            features = AudioFeatures(
                timestamp=time.time(),
                beat=beat,
                beat_confidence=0.8 if beat else 0.0,
                onset=beat,
                onset_confidence=0.7 if beat else 0.0,
                bass=0.5 + 0.3 * np.sin(self.simulated_beat_phase),
                mid=0.3,
                high=0.2,
                volume=0.4,
                pitch=440.0,
                pitch_confidence=0.9,
                spectral_centroid=0.3,
                spectral_rolloff=0.4,
                spectral_flux=0.1,
                zero_crossing_rate=0.05,
                harmony=0.6,
                percussive=0.7 if beat else 0.3,
                bass_smooth=0.5,
                mid_smooth=0.3,
                high_smooth=0.2,
                volume_smooth=0.4,
                bpm=120.0,
                beat_phase=self.simulated_beat_phase % 1.0,
                loudness_integrated=-23.0,
                loudness_shortterm=-20.0,
                loudness_range=10.0
            )
            
            self.latest_features = features
            self.feature_history.append(features)
            
            if self.broadcaster:
                self.broadcaster.broadcast(features)
                
            time.sleep(1.0 / 60.0)  # 60 Hz
            self.simulated_beat_phase += 0.5
```

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_audio_device_enumeration` | Lists available input devices |
| `test_audio_device_opening` | Opens selected device successfully |
| `test_audio_capture` | Captures audio without dropouts |
| `test_fft_accuracy` | FFT produces correct frequency spectrum |
| `test_band_energy_calculation` | Band energies computed correctly |
| `test_beat_detection` | Beats detected on percussive signals |
| `test_onset_detection` | Onsets detected on transients |
| `test_pitch_tracking` | Pitch tracked for tonal signals |
| `test_spectral_features` | Spectral features within expected ranges |
| `test_temporal_smoothing` | Smoothing applied correctly |
| `test_feature_broadcast` | Features published to plugin bus |
| `test_audio_reactor_connection` | Effects connect to analyzer |
| `test_latency_budget` | End-to-end latency < 50ms |
| `test_cpu_usage` | CPU usage < 5% on Orange Pi 5 |
| `test_memory_usage` | Memory usage < 50MB |
| `test_fallback_to_dummy` | Dummy analyzer used when no device |
| `test_device_hot_plug` | USB device changes handled gracefully |
| `test_thread_safety` | No race conditions in ring buffer |
| `test_sample_rate_conversion` | Resampling works correctly |
| `test_clipping_detection` | Clipping detected and reported |

**Total tests:** 20
**Minimum coverage:** 90% before Phase 1 complete.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 20 tests implemented and passing
- [ ] Test coverage >= 90%
- [ ] Performance budget met on Orange Pi 5 hardware
- [ ] Audio latency < 50ms measured
- [ ] Zero audio dropouts during 1-hour stress test
- [ ] Plugin bus integration verified with 3+ effects
- [ ] Fallback to dummy analyzer works when no device
- [ ] USB hot-plug tested with Astra camera audio
- [ ] CI/CD pipeline runs tests on every commit
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-A1: Audio Analyzer` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

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

This shows the AudioReactor pattern for connecting effects to the analyzer.

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

This demonstrates how effects use audio features to drive parameters.

### core/effects/audio_reactive_effects.py (L97-116) [VJlive (Original)]
```python
    def set_audio_analyzer(self, analyzer: AudioAnalyzer):
        """Set audio analyzer for reactivity."""
        self.audio_analyzer = analyzer

    def set_parameter(self, name: str, value: float):
        """Set effect parameters."""
        if name == "num_particles":
            self.num_particles = max(10, min(200, int(value)))
            self._resize_particles()
        elif name == "particle_size":
            self.particle_size = max(0.001, min(0.1, value))
        elif name == "particle_speed":
            self.particle_speed = max(0.1, min(2.0, value))
        elif name == "trail_length":
            self.trail_length = max(0.1, min(2.0, value))
```

This shows parameter handling in audio-reactive effects.

### core/effects/audio_reactive_effects.py (L273-292) [VJlive (Original)]
```python
            distorted_uv.y += cos(uv.x * frequency_scale * 8.0 + time * 1.5) * distortion * 0.5;

            // Clamp to valid texture coordinates
            distorted_uv = clamp(distorted_uv, 0.0, 1.0);

            // Sample distorted texture
            vec4 distorted_color = texture(tex0, distorted_uv);

            // Color shifting based on audio
            vec3 color = distorted_color.rgb;
            color.r += sin(time * bass_level * 5.0) * color_shift * volume_level;
            color.b += cos(time * bass_level * 3.0) * color_shift * volume_level;

            // Mix with original
            fragColor = mix(texture(tex0, uv), vec4(color, distorted_color.a), u_mix);
        }
        """

    def set_audio_analyzer(self, analyzer: AudioAnalyzer):
        """Set audio analyzer for reactivity."""
        self.audio_analyzer = analyzer
```

This shows GLSL shader integration with audio features.

### core/effects/audio_reactive_effects.py (L449-468) [VJlive (Original)]
```python
                float glow = 1.0 - abs(uv.y - trail_height) / 0.1;
                glow = clamp(glow, 0.0, 1.0);

                color = mix(color, spectrum_color, glow * trail_opacity * u_mix);
            }

            // Add bass-reactive background glow
            float bass_glow = bass_level * 0.3 * (1.0 - uv.y / spectrum_height);
            color += vec3(bass_glow, bass_glow * 0.5, bass_glow * 0.2) * u_mix;
        }
        """

    def set_audio_analyzer(self, analyzer: AudioAnalyzer):
        """Set audio analyzer for reactivity."""
        self.audio_analyzer = analyzer
```

This demonstrates audio-reactive shader uniforms.

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

This shows the pattern for wiring audio analyzer to all effects.

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

This shows integration with the audio signal bridge.

---

## Notes for Implementers

1. **Real-Time Audio is Fragile**: Audio processing must never block. Use lock-free data structures, pre-allocated buffers, and real-time thread priorities. Test on actual Orange Pi 5 hardware, not just development machines.

2. **FFT Size Trade-offs**: Larger FFT (4096) gives better frequency resolution but higher latency. 2048 is a good compromise (43ms resolution at 48 kHz). Use overlap (50% with hop=1024) for smoother analysis.

3. **Beat Detection is Hard**: No perfect algorithm exists. Use multiple detectors (energy-based, onset-based, tempogram) and combine with confidence weighting. The legacy code likely uses a simple energy-based onset detector.

4. **Pitch Tracking is Expensive**: High-quality pitch tracking (like pYIN) is CPU-intensive. Consider using a cheaper algorithm (like SWIPE) or downsampling for real-time use.

5. **Plugin Bus is Key**: The audio analyzer doesn't push to effects directly. It broadcasts to the plugin bus, and effects subscribe. This decoupling allows multiple consumers and dynamic connection/disconnection.

6. **Temporal Smoothing is Essential**: Raw audio features are noisy. Apply exponential moving averages with ~100ms time constant to smooth bass/mid/high/volume. But keep beat/onset unsmoothed for precise timing.

7. **Loudness Metering**: Implement EBU R128 loudness metering for professional audio compliance. This requires integration over several seconds.

8. **Fallback Strategy**: Always have a dummy analyzer as fallback. In production, if no audio device available, the system should still run (with synthetic or last-known features) rather than crash.

9. **Testing with Real Audio**: Use test audio files with known characteristics:
   - Sine sweep (for frequency response)
   - Kick drum loop (for beat detection)
   - Pure tones (for pitch tracking)
   - White noise (for spectral features)
   - Silence (for baseline)

10. **Performance Profiling**: Profile on target hardware (Orange Pi 5) early. Use `perf` or `py-spy` to identify hotspots. FFT and pitch tracking are likely the most expensive operations.

---

## Implementation Tips

1. **Use pyfftw**: It's much faster than numpy FFT and supports multi-threading.
   ```python
   import pyfftw
   fft_obj = pyfftw.builders.rfft(data, threads=4)
   result = fft_obj()
   ```

2. **Lock-Free Ring Buffer**: Use `ringbuf` or implement with `collections.deque` with `maxlen` and atomic operations. For true lock-free, use `multiprocessing.shared_memory` or `numpy` with atomic operations.

3. **Real-Time Thread Priority**:
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

4. **Beat Detection Algorithm** (simple energy-based):
   ```python
   class BeatDetector:
       def __init__(self, sample_rate=48000):
           self.energy_history = deque(maxlen=43)  # ~1 second at 60 Hz
           self.energy_threshold = 1.3  # Local average multiplier
           
       def detect(self, magnitude: np.ndarray) -> Tuple[bool, float]:
           # Compute energy in low frequencies (bass)
           bass_energy = np.sum(magnitude[:20] ** 2)
           
           # Compute local average
           self.energy_history.append(bass_energy)
           if len(self.energy_history) < 10:
               return False, 0.0
               
           local_avg = np.mean(list(self.energy_history)[-10:])
           
           # Detect beat if energy exceeds threshold
           if bass_energy > local_avg * self.energy_threshold:
               confidence = min(1.0, bass_energy / (local_avg * 2.0))
               return True, confidence
               
           return False, 0.0
   ```

5. **Onset Detection** (spectral flux):
   ```python
   class OnsetDetector:
       def __init__(self):
           self.prev_magnitude = None
           
       def detect(self, magnitude: np.ndarray) -> Tuple[bool, float]:
           if self.prev_magnitude is None:
               self.prev_magnitude = magnitude
               return False, 0.0
               
           # Spectral flux: sum of positive differences
           diff = magnitude - self.prev_magnitude
           flux = np.sum(np.maximum(diff, 0.0))
           
           self.prev_magnitude = magnitude
           
           # Threshold (adaptive)
           threshold = 0.1
           if flux > threshold:
               confidence = min(1.0, flux / (threshold * 2.0))
               return True, confidence
               
           return False, 0.0
   ```

6. **Pitch Tracking** (use `librosa` if available, else simple autocorrelation):
   ```python
   def track_pitch(magnitude: np.ndarray, phase: np.ndarray, sample_rate: int) -> Tuple[float, float]:
       # Convert to log frequency scale
       # Use parabolic interpolation around peak
       # Compute fundamental frequency
       # Return (pitch_hz, confidence)
       # Simplified: just find peak in 50-2000 Hz range
       freqs = np.fft.rfftfreq(len(magnitude), 1/sample_rate)
       mask = (freqs >= 50) & (freqs <= 2000)
       if not np.any(mask):
           return 0.0, 0.0
       peak_idx = np.argmax(magnitude[mask])
       peak_freq = freqs[mask][peak_idx]
       confidence = magnitude[mask][peak_idx] / np.max(magnitude)
       return peak_freq, confidence
   ```

7. **Plugin Bus Integration**:
   ```python
   # In main.py
   from core.audio.audio_analyzer import AudioAnalyzer
   from core.plugin_bus import PluginBus
   
   # Create analyzer
   analyzer = AudioAnalyzer()
   
   # Connect to plugin bus
   analyzer.set_plugin_bus(self.plugin_bus)
   
   # Start analyzer
   analyzer.start()
   
   # Effects automatically connect via set_audio_analyzer
   # when they're loaded into the effect chain
   ```

8. **Configuration via JSON**:
   ```json
   {
     "audio_analyzer": {
       "enabled": true,
       "sample_rate": 48000,
       "fft_size": 2048,
       "smoothing_time": 0.1,
       "broadcast_rate": 60.0,
       "device_id": 0,
       "fallback_to_dummy": true
     }
   }
   ```

9. **Testing without Hardware**: Use `sounddevice`'s loopback or generate synthetic audio. For CI/CD, use dummy analyzer exclusively.

10. **Debug Visualization**: Add WebSocket endpoint to stream audio features in real-time for debugging:
    ```python
    # In websocket_gateway.py
    @websocket.route('/audio_features')
    async def audio_features_stream(ws):
        analyzer = self.vjlive.audio_analyzer
        while ws.open:
            features = analyzer.get_latest_features()
            await ws.send(json.dumps(features.__dict__))
            await asyncio.sleep(1.0 / 60.0)
    ```

---
-

## References

- `core/audio/audio_analyzer.py` (to be implemented)
- `core/audio/audio_signal_bridge.py` (for plugin bus integration)
- `core/effects/audio_reactive_effects.py` (existing audio-reactive effects)
- `core/plugin_bus.py` (for broadcasting)
- `core/signal_flow_manager.py` (for audio routing)
- `librosa` library (for pitch tracking, onset detection)
- `scipy.signal` (for spectral analysis)
- `pyfftw` (for fast FFT)
- `sounddevice` (for audio capture)
- EBU R128 loudness standard
- BeatRoot algorithm for beat tracking
- pYIN algorithm for pitch tracking

---

## Conclusion

The Audio Analyzer is the foundational component that transforms raw audio into a rich feature set driving visual reactivity. Its lock-free architecture ensures real-time performance without compromising 60 FPS rendering. By broadcasting features via the plugin bus, it enables a ecosystem of audio-reactive effects that can independently subscribe to the features they need. The implementation must be thoroughly tested on target Orange Pi 5 hardware to meet the stringent latency and CPU budget requirements that make VJLive3 suitable for live performance.

---

## As-Built Implementation Notes

**Date:** 2026-03-03 | **Agent:** Antigravity | **Coverage:** 71%

### Files Created
- `src/vjlive3/audio/features.py` — 119 lines (AudioFeatures, AudioAnalyzerConfig, AudioDevice)
- `src/vjlive3/audio/analyzer.py` — 270 lines (AudioAnalyzer, DummyAudioAnalyzer, AudioReactor)
- `tests/audio/test_features.py` — 6 tests
- `tests/audio/test_analyzer.py` — 12 tests

### Class Mapping — Spec vs Actual

| Spec Class | Actual Class | Notes |
|---|---|---|
| `AudioAnalyzer` | `AudioAnalyzer` | ✅ Main class with threading |
| `AudioFeatures` | `AudioFeatures` | ✅ 25-field dataclass in features.py |
| `AudioAnalyzerConfig` | `AudioAnalyzerConfig` | ✅ Config dataclass in features.py |
| `AudioPreprocessor` | *merged into _process_frame* | ⚠️ Not a separate class |
| `FFTProcessor` | *merged into _process_frame* | ⚠️ Not a separate class |
| `FeatureExtractor` | *merged into _process_frame* | ⚠️ Not a separate class |
| `TemporalSmoother` | `_TemporalSmoother` | ✅ Private EMA helper class |
| `AudioBroadcaster` | *merged as _broadcaster callback* | ⚠️ Not a separate class |
| `DummyAudioAnalyzer` | `DummyAudioAnalyzer` | ✅ 120 BPM synthetic fallback |
| `AudioReactor` | `AudioReactor` | ✅ Per-frame pull adapter |

### Dependencies — Spec vs Actual

| Spec Dependency | Used? | Note |
|---|---|---|
| `pyfftw` | ❌ No | `numpy.fft.rfft` used — pyfftw not installed |
| `sounddevice` | ✅ Lazy | Imported only inside `list_input_devices()` / `select_input_device()` |
| `scipy` | ❌ No | No filtering used |
| `numpy` | ✅ Yes | FFT, band energy, hanning window |
| `collections.deque` | ✅ Yes | Ring buffer (not lock-free) |

### ADRs
1. **No pyfftw** — `numpy.fft.rfft` used throughout. pyfftw would provide ~2–4× speedup on Orange Pi 5 NEON SIMD. Install when available: `pip install pyfftw` then swap `np.fft.rfft` → `pyfftw.interfaces.numpy_fft.rfft` with `cache=True`.
2. **Inner classes collapsed** — `AudioPreprocessor`, `FFTProcessor`, `FeatureExtractor`, `AudioBroadcaster` from spec merged into single `_process_frame()` method. Added when FFT pipeline grows complex enough to justify separation.
3. **deque + RLock ring buffer** — Spec specified a lock-free ring buffer using `ctypes` atomics. `collections.deque(maxlen=N)` with `threading.RLock` used instead. Python's GIL provides informal lock-free reads in practice, but this is not a hard guarantee. Upgrade path: `mmap`-based circular buffer.
4. **No EBU R128 loudness** — `loudness_integrated/shortterm/range` fields in `AudioFeatures` initialized to safe defaults (-23, -20, 10 LUFS) but not computed. Requires `pyloudnorm` or `ebur128` library (deferred).
5. **Coverage gap at 71%** — The sounddevice callback path, the `_processing_loop` daemon thread body, and the `set_plugin_bus` broadcaster path are untested. These require live audio hardware or a more sophisticated mock.