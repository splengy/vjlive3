# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P1-A5_audio_reactivity.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-A5 — Audio Reactivity

**What This Module Does**

Implements a sophisticated audio reactivity system that transforms raw audio input into dynamic visual parameters for VJLive3 effects. The Audio Reactivity module provides advanced signal processing capabilities including multi-band analysis, beat detection, spectral feature extraction, and parameter mapping to create rich, responsive visual compositions. It serves as the bridge between audio analysis and visual effect control, enabling effects to react intelligently to different aspects of the audio signal.

---

## Architecture Decisions

- **Pattern:** Multi-Stage Audio Processing Pipeline with Parameter Mapping
- **Rationale:** Audio reactivity requires multiple stages of signal processing: preprocessing, feature extraction, feature normalization, and parameter mapping. A pipeline approach allows each stage to be optimized independently while maintaining a clean interface between stages. The parameter mapping system enables flexible control of effect parameters based on audio features.
- **Constraints:**
  - Must support real-time processing at 60 FPS
  - Must handle multiple audio sources simultaneously
  - Must provide multi-band analysis (bass, mid, high frequencies)
  - Must implement beat detection with tempo estimation
  - Must extract spectral features (FFT, MFCCs)
  - Must provide parameter mapping with scaling and offset controls
  - Must maintain low latency (< 50ms from audio input to effect parameter update)
  - Must integrate with AudioSourceManager and EffectBus systems
  - Must handle dynamic audio source changes
  - Must provide confidence scoring for reactivity parameters
  - Must support both real-time and pre-analyzed audio streams

---

## Public Interface

```python
class AudioReactivityManager:
    """Manages audio reactivity processing and parameter mapping."""
    
    def __init__(self, audio_source_manager: AudioSourceManager, 
                 effect_bus_manager: EffectBusManager) -> None:...
    def process_audio_frame(self, audio_frame: AudioFrame) -> AudioReactivityFeatures:...
    def get_features(self) -> AudioReactivityFeatures:...
    def set_mapping(self, effect_name: str, parameter_name: str, 
                   mapping_config: dict) -> bool:...
    def get_mapping(self, effect_name: str, parameter_name: str) -> dict:...
    def update_mappings(self) -> None:...
    def get_active_mappings(self) -> List[dict]:...
    def get_feature_history(self, duration_seconds: float) -> List[AudioReactivityFeatures]:...
    def get_confidence(self, feature_type: str) -> float:...
    def set_confidence_threshold(self, threshold: float) -> None:...
    def get_stats(self) -> dict:...
    def subscribe(self, callback: Callable) -> None:...
    def unsubscribe(self, callback: Callable) -> None:...

class AudioReactivityFeatures:
    """Container for extracted audio reactivity features."""
    
    def __init__(self, 
                 bass_energy: float, 
                 mid_energy: float, 
                 high_energy: float,
                 beat_confidence: float,
                 tempo_estimate: float,
                 phase: float,
                 spectral_centroid: float,
                 spectral_rolloff: float,
                 spectral_flatness: float,
                 mfcc_1: float, mfcc_2: float, mfcc_3: float, 
                 mfcc_4: float, mfcc_5: float, mfcc_6: float,
                 timestamp: float) -> None:...
    def to_dict(self) -> dict:...
    @staticmethod
    def from_dict(data: dict) -> 'AudioReactivityFeatures':...
```

---

## Audio Processing Pipeline

### 1. Preprocessing Stage

```python
class AudioPreprocessor:
    """Handles audio frame preprocessing."""
    
    def __init__(self, sample_rate: int = 44100, hop_size: int = 1024):
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.window_function = np.hanning(hop_size)
        self.prev_audio_frame = None
        
    def process(self, audio_frame: np.ndarray) -> np.ndarray:
        """Process audio frame with windowing and filtering."""
        # Apply window function
        windowed = audio_frame * self.window_function
        
        # Apply high-pass filter to remove DC offset
        filtered = self._high_pass_filter(windowed)
        
        # Store for next frame processing
        self.prev_audio_frame = audio_frame.copy()
        
        return filtered
    
    def _high_pass_filter(self, data: np.ndarray, cutoff: float = 20.0) -> np.ndarray:
        """Apply high-pass filter to remove DC offset."""
        from scipy import signal
        nyquist = 0.5 * self.sample_rate
        b, a = signal.butter(2, cutoff / nyquist, btype='high', analog=False)
        return signal.filtfilt(b, a, data)
```

### 2. Feature Extraction Stage

```python
class FeatureExtractor:
    """Extracts various audio features from processed frames."""
    
    def __init__(self, sample_rate: int, hop_size: int):
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.fft_size = hop_size
        self.mfcc_bands = 13
        self.bands = [20, 100, 300, 600, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000]
        
    def extract_features(self, audio_frame: np.ndarray) -> dict:
        """Extract multiple audio features from a frame."""
        # FFT for spectral analysis
        fft = np.fft.rfft(audio_frame * self.window_function)
        magnitude = np.abs(fft)
        
        # Convert to frequency bins
        freqs = np.fft.rfftfreq(self.fft_size, 1.0/self.sample_rate)
        
        # Calculate spectral features
        spectral_centroid = self._calculate_spectral_centroid(magnitude, freqs)
        spectral_rolloff = self._calculate_spectral_rolloff(magnitude, freqs)
        spectral_flatness = self._calculate_spectral_flatness(magnitude)
        
        # Calculate MFCCs
        mfccs = self._calculate_mfccs(audio_frame)
        
        # Calculate band energies
        band_energies = self._calculate_band_energies(magnitude, freqs)
        
        return {
            'magnitude': magnitude,
            'freqs': freqs,
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'spectral_flatness': spectral_flatness,
            'mfccs': mfccs,
            'band_energies': band_energies
        }
    
    def _calculate_spectral_centroid(self, magnitude: np.ndarray, freqs: np.ndarray) -> float:
        """Calculate spectral centroid."""
        # Weighted average of frequency bins
        weighted_sum = np.sum(freqs * magnitude)
        total_magnitude = np.sum(magnitude)
        return weighted_sum / total_magnitude if total_magnitude > 0 else 0.0
    
    def _calculate_spectral_rolloff(self, magnitude: np.ndarray, freqs: np.ndarray) -> float:
        """Calculate spectral rolloff frequency."""
        # Find frequency where 85% of energy is below
        cumsum = np.cumsum(magnitude)
        rolloff_idx = np.where(cumsum >= 0.85 * cumsum[-1])[0]
        return freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0.0
    
    def _calculate_spectral_flatness(self, magnitude: np.ndarray) -> float:
        """Calculate spectral flatness."""
        geometric_mean = scipy.stats.mstats.gmean(magnitude + 1e-10)
        harmonic_mean = np.mean(magnitude + 1e-10)
        return geometric_mean / harmonic_mean if harmonic_mean > 0 else 0.0
    
    def _calculate_mfccs(self, audio_frame: np.ndarray) -> List[float]:
        """Calculate MFCC coefficients."""
        mfccs = librosa.feature.mfcc(
            y=audio_frame, 
            sr=self.sample_rate,
            n_mfcc=self.mfcc_bands,
            hop_length=self.hop_size
        )
        return mfccs[0].tolist()  # Return first coefficient set
    
    def _calculate_band_energies(self, magnitude: np.ndarray, freqs: np.ndarray) -> dict:
        """Calculate energy in different frequency bands."""
        band_energies = {}
        for i, (low, high) in enumerate(self.bands):
            mask = (freqs >= low) & (freqs < high)
            band_energies[f'band_{i}'] = np.sum(magnitude[mask]) if np.any(mask) else 0.0
        return band_energies
```

### 3. Beat Detection Stage

```python
class BeatDetector:
    """Detects beats in the audio signal."""
    
    def __init__(self, sample_rate: int, hop_size: int):
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.onset_detector = OnsetDetector()
        self.tempo_estimator = TempoEstimator()
        self.state_machine = BeatStateMachine()
        self.beat_history = deque(maxlen=3600)  # 1 hour at 60 Hz
        
    def process_frame(self, magnitude: np.ndarray) -> BeatDetectionResult:
        """Process audio frame and detect beats."""
        # Detect onsets
        onset, onset_confidence = self.onset_detector.detect(magnitude)
        
        # Update tempo estimate
        if onset:
            current_time = time.time()
            self.tempo_estimator.estimate([current_time])
        
        # Track beat phase
        beat_phase = self._track_beat_phase()
        
        # Determine if beat occurred
        beat = self._is_beat(beat_phase)
        
        # Create result object
        result = BeatDetectionResult(
            beat=beat,
            beat_confidence=beat_confidence,
            tempo=self.tempo_estimator.current_tempo,
            phase=beat_phase,
            confidence=self.tempo_estimator.confidence,
            timestamp=time.time()
        )
        
        # Update state machine
        self.state_machine.update(result)
        
        # Store in history
        self.beat_history.append(result)
        
        return result
    
    def _track_beat_phase(self) -> float:
        """Track beat phase within current tempo."""
        if not self.beat_history:
            return 0.0
            
        last_beat = self.beat_history[-1]
        current_time = time.time()
        time_since_last = current_time - last_beat.timestamp
        
        beat_interval = 60.0 / self.tempo_estimator.current_tempo
        phase = (time_since_last % beat_interval) / beat_interval
        
        return phase
    
    def _is_beat(self, phase: float) -> bool:
        """Determine if current phase is a beat."""
        return phase < 0.1  # Within 10% of beat start
```

### 4. Parameter Mapping Stage

```python
class ParameterMapper:
    """Maps audio features to effect parameters."""
    
    def __init__(self):
        self.mappings: Dict[str, Dict[str, MappingConfig]] = {}
        self.default_mappings: Dict[str, MappingConfig] = {
            'bass_energy': {
                'default_target': 'intensity',
                'scale': 1.0,
                'offset': 0.0
            },
            'mid_energy': {
                'default_target': 'distortion',
                'scale': 0.8,
                'offset': 0.2
            },
            'high_energy': {
                'default_target': 'brightness',
                'scale': 1.2,
                'offset': -0.1
            },
            'beat_confidence': {
                'default_target': 'pulse_intensity',
                'scale': 2.0,
                'offset': 0.0
            },
            'tempo_estimate': {
                'default_target': 'speed',
                'scale': 0.5,
                'offset': 0.5
            }
        }
        
    def set_mapping(self, effect_name: str, parameter_name: str, 
                   mapping_config: dict) -> bool:
        """Set a parameter mapping configuration."""
        if effect_name not in self.mappings:
            self.mappings[effect_name] = {}
            
        if parameter_name not in self.mappings[effect_name]:
            self.mappings[effect_name][parameter_name] = {}
            
        self.mappings[effect_name][parameter_name] = mapping_config
        return True
    
    def get_mapping(self, effect_name: str, parameter_name: str) -> dict:
        """Get a parameter mapping configuration."""
        if effect_name in self.mappings and parameter_name in self.mappings[effect_name]:
            return self.mappings[effect_name][parameter_name].copy()
        return {}
    
    def map_features_to_parameter(self, effect_name: str, 
                                parameter_name: str, 
                                feature_value: float, 
                                mapping_config: dict) -> float:
        """Map a feature value to a parameter value."""
        if not mapping_config:
            return 0.0
            
        scale = mapping_config.get('scale', 1.0)
        offset = mapping_config.get('offset', 0.0)
        target_range = mapping_config.get('target_range', [0.0, 1.0])
        
        # Apply scaling and offset
        mapped_value = feature_value * scale + offset
        
        # Clamp to target range
        mapped_value = max(target_range[0], min(target_range[1], mapped_value))
        
        return mapped_value
```

---

## Integration with Effect System

### Effect Parameter Control

```python
class EffectParameterController:
    """Controls effect parameters based on audio reactivity features."""
    
    def __init__(self, reactivity_manager: AudioReactivityManager):
        self.reactivity_manager = reactivity_manager
        self.effects: Dict[str, Effect] = {}
        
    def register_effect(self, effect_name: str, effect: Effect) -> bool:
        """Register an effect to be controlled by reactivity."""
        self.effects[effect_name] = effect
        return True
    
    def update_parameters(self) -> None:
        """Update all registered effect parameters based on current features."""
        features = self.reactivity_manager.get_features()
        
        # Update each effect based on its registered mappings
        for effect_name, effect in self.effects.items():
            if hasattr(effect, 'get_registered_mappings'):
                mappings = effect.get_registered_mappings()
                for mapping in mappings:
                    effect_name = mapping['effect']
                    parameter_name = mapping['parameter']
                    mapping_config = mapping['config']
                    
                    # Get feature value
                    feature_value = features.get(mapping['feature'], 0.0)
                    
                    # Map to parameter value
                    parameter_value = self.reactivity_manager.mapper.map_features_to_parameter(
                        effect_name, parameter_name, feature_value, mapping_config
                    )
                    
                    # Set parameter on effect
                    if hasattr(effect, f'set_{parameter_name}'):
                        getattr(effect, f'set_{parameter_name}')(parameter_value)
    
    def handle_dynamic_mapping(self, effect_name: str, parameter_name: str, 
                             feature_type: str, feature_value: float) -> None:
        """Handle dynamic parameter mapping based on feature type."""
        if effect_name not in self.effects:
            return
            
        effect = self.effects[effect_name]
        
        # Get mapping configuration
        mapping_config = self.reactivity_manager.get_mapping(effect_name, parameter_name)
        if not mapping_config:
            return
            
        # Map feature to parameter
        parameter_value = self.reactivity_manager.mapper.map_features_to_parameter(
            effect_name, parameter_name, feature_value, mapping_config
        )
        
        # Set parameter on effect
        if hasattr(effect, f'set_{parameter_name}'):
            getattr(effect, f'set_{parameter_name}')(parameter_value)
```

### Audio Reactor Integration

```python
class AudioReactor:
    """Connects effects to audio reactivity system."""
    
    def __init__(self, reactivity_manager: AudioReactivityManager):
        self.reactivity_manager = reactivity_manager
        self.effects: Dict[str, Effect] = {}
        
    def register_effect(self, effect_name: str, effect: Effect) -> bool:
        """Register an effect to be controlled by reactivity."""
        self.effects[effect_name] = effect
        return True
        
    def update(self) -> None:
        """Update all registered effects with current reactivity features."""
        # Get current features
        features = self.reactivity_manager.get_features()
        
        # Update each effect
        for effect_name, effect in self.effects.items():
            # Apply parameter mappings
            self._update_effect_parameters(effect, features)
    
    def _update_effect_parameters(self, effect: Effect, features: AudioReactivityFeatures):
        """Update effect parameters based on features."""
        # Example parameter mappings
        if 'bass_energy' in features.__dict__:
            bass_value = features.bass_energy
            if hasattr(effect, 'set_bass_intensity'):
                effect.set_bass_intensity(bass_value)
                
        if 'beat_confidence' in features.__dict__:
            beat_conf = features.beat_confidence
            if hasattr(effect, 'set_pulse_intensity'):
                effect.set_pulse_intensity(beat_conf)
                
        if 'tempo_estimate' in features.__dict__:
            tempo = features.tempo_estimate
            if hasattr(effect, 'set_tempo_factor'):
                effect.set_tempo_factor(tempo / 120.0)  # Normalize to 120 BPM
```

---

## Performance Requirements

- **Latency:** End-to-end processing < 50ms from audio input to effect parameter update
- **CPU:** < 5% on Orange Pi 5 (single core equivalent)
- **Memory:** < 30MB resident set size
- **Frame rate:** No impact on 60 FPS rendering
- **Accuracy:** Tempo estimation within 5% for 60-180 BPM range
- **Phase tracking:** < 50ms jitter in beat phase
- **Scalability:** Support up to 10 concurrent effects with 50 parameter mappings each

---

## Testing Strategy

### Unit Tests

```python
def test_feature_extraction():
    """Test feature extraction accuracy."""
    sample_rate = 44100
    hop_size = 1024
    
    # Create test audio frame
    audio_frame = np.sin(2 * np.pi * 60 * np.linspace(0, 0.1, hop_size))
    
    # Process with extractor
    extractor = FeatureExtractor(sample_rate, hop_size)
    features = extractor.extract_features(audio_frame)
    
    # Verify basic features exist
    assert 'spectral_centroid' in features
    assert 'spectral_rolloff' in features
    assert 'mfccs' in features
    assert len(features['mfccs']) == 13
    
    # Verify non-negative values
    for key, value in features.items():
        if isinstance(value, (int, float)) and key not in ['freqs']:
            assert value >= 0, f"Feature {key} should be non-negative"

def test_beat_detection():
    """Test beat detection functionality."""
    sample_rate = 44100
    hop_size = 1024
    
    # Create synthetic kick drum pattern
    duration = 4.0  # 4 seconds
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    signal = np.zeros_like(t)
    
    # Kick every 0.5 seconds (120 BPM)
    kick_times = np.arange(0, duration, 0.5)
    for kt in kick_times:
        idx = int(kt * sample_rate)
        signal[idx:idx+100] = np.sin(2 * np.pi * 60 * np.linspace(0, 0.1, 100))
    
    # Process in frames
    for i in range(0, len(signal) - hop_size, hop_size):
        frame = signal[i:i+hop_size]
        magnitude = np.abs(np.fft.rfft(frame))
        
        # Process with beat detector
        beat_detector = BeatDetector(sample_rate, hop_size)
        result = beat_detector.process_frame(magnitude)
        
        # Verify result structure
        assert hasattr(result, 'beat')
        assert hasattr(result, 'tempo')
        assert hasattr(result, 'phase')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'timestamp')

def test_parameter_mapping():
    """Test parameter mapping functionality."""
    mapper = ParameterMapper()
    
    # Set up a mapping
    mapper.set_mapping('test_effect', 'test_param', {
        'scale': 2.0,
        'offset': 0.5,
        'target_range': [0.0, 1.0]
    })
    
    # Test mapping
    result = mapper.map_features_to_parameter(
        'test_effect', 'test_param', 0.75, 
        mapper.get_mapping('test_effect', 'test_param')
    )
    
    # Verify result is in expected range
    assert 0.0 <= result <= 1.0
    # Verify calculation: 0.75 * 2.0 + 0.5 = 2.0, clamped to 1.0
    assert result == 1.0
```

### Integration Tests

```python
def test_full_audio_reactivity_chain():
    """Test complete audio reactivity pipeline."""
    # Create mock components
    mock_audio_source = MockAudioSource()
    mock_effect_bus = MockEffectBus()
    mock_reactivity_manager = AudioReactivityManager(mock_audio_source, mock_effect_bus)
    mock_mapper = ParameterMapper()
    mock_effect_controller = EffectParameterController(mock_reactivity_manager)
    
    # Register mappings
    mock_mapper.set_mapping('test_effect', 'test_param', {
        'scale': 1.5,
        'offset': 0.2
    })
    
    # Create mock effect
    mock_effect = MockEffect()
    mock_effect.register_mapping('test_param', 'test_feature', {
        'feature': 'bass_energy',
        'scale': 2.0,
        'offset': 0.0
    })
    
    # Register effect
    mock_effect_controller.register_effect('test_effect', mock_effect)
    
    # Simulate audio processing
    mock_audio_source.set_next_frame(mock_audio_frame)
    features = mock_reactivity_manager.process_audio_frame(mock_audio_frame)
    
    # Verify features are processed
    assert features is not None
    assert hasattr(features, 'bass_energy')
    assert hasattr(features, 'beat_confidence')
    
    # Update effect parameters
    mock_effect_controller.update()
    
    # Verify parameter was set
    assert mock_effect.set_test_param_called_with(0.8)  # Example value

def test_dynamic_mapping():
    """Test dynamic parameter mapping based on feature type."""
    # Create components
    mock_audio_source = MockAudioSource()
    mock_reactivity_manager = AudioReactivityManager(mock_audio_source, mock_effect_bus)
    mock_mapper = ParameterMapper()
    mock_effect_controller = EffectParameterController(mock_reactivity_manager)
    
    # Register effect
    mock_effect = MockEffect()
    mock_effect_controller.register_effect('reverb', mock_effect)
    
    # Set up feature extraction
    mock_audio_source.set_next_frame(mock_audio_frame)
    features = mock_reactivity_manager.get_features()
    
    # Test mapping different feature types
    # Bass energy mapping
    mock_effect_controller.handle_dynamic_mapping(
        'reverb', 'intensity', 'bass_energy', features.bass_energy
    )
    
    # Beat confidence mapping
    mock_effect_controller.handle_dynamic_mapping(
        'reverb', 'pulse', 'beat_confidence', features.beat_confidence
    )
    
    # Tempo mapping
    mock_effect_controller.handle_dynamic_mapping(
        'reverb', 'speed', 'tempo_estimate', features.tempo_estimate
    )
    
    # Verify parameter updates occurred
    assert mock_effect.intensity_updated_with(features.bass_energy * 2.0)
    assert mock_effect.pulse_updated_with(features.beat_confidence)
    assert mock_effect.speed_updated_with(features.tempo_estimate / 120.0)
```

### Performance Tests

```python
def test_processing_latency():
    """Test that audio processing meets latency requirements."""
    import time
    
    # Create components
    mock_audio_source = MockAudioSource()
    mock_effect_bus = MockEffectBus()
    reactivity_manager = AudioReactivityManager(mock_audio_source, mock_effect_bus)
    
    # Create test audio frame
    audio_frame = np.random.randn(1024).astype(np.float32)
    
    # Measure processing time
    start = time.perf_counter()
    for _ in range(100):
        features = reactivity_manager.process_audio_frame(audio_frame)
    elapsed = time.perf_counter() - start
    
    # Calculate average latency
    avg_latency = elapsed / 100 * 1000  # ms
    assert avg_latency < 50.0, f"Average latency {avg_latency:.2f}ms > 50ms budget"

def test_cpu_usage():
    """Test CPU usage stays within budget."""
    import psutil
    import os
    
    # Create components
    reactivity_manager = AudioReactivityManager(MockAudioSource(), MockEffectBus())
    
    # Add stress test with multiple features
    for i in range(50):
        reactivity_manager.add_mapping(f'mapping_{i}', 'effect_{i}', {})
    
    # Measure CPU before and after
    process = psutil.Process(os.getpid())
    cpu_before = process.cpu_percent(interval=0.1)
    
    # Process multiple frames
    audio_frame = np.random.randn(1024).astype(np.float32)
    for _ in range(1000):
        reactivity_manager.process_audio_frame(audio_frame)
    
    cpu_after = process.cpu_percent(interval=0.1)
    cpu_delta = cpu_after - cpu_before
    
    # Should stay under 5% additional CPU
    assert cpu_delta < 5.0, f"CPU usage increase {cpu_delta:.1f}% > 5% budget"

def test_memory_usage():
    """Test memory usage stays within budget."""
    import psutil
    import os
    
    # Create components
    reactivity_manager = AudioReactivityManager(MockAudioSource(), MockEffectBus())
    
    # Add many mappings to test memory scaling
    for i in range(100):
        reactivity_manager.add_mapping(f'mapping_{i}', 'effect_{i}', {})
    
    # Measure memory usage
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    # Should stay under 30MB
    assert memory_mb < 30.0, f"Memory usage {memory_mb:.1f}MB > 30MB budget"
```

---

## Hardware Considerations

### Orange Pi 5 Optimization

- Use NEON SIMD intrinsics for FFT operations (via pyfftw with OpenMP)
- Pin processing threads to dedicated cores (core 3 or 4)
- Set thread priority to SCHED_FIFO with real-time priority
- Use huge pages for FFT buffers (2MB pages)
- Pre-allocate all buffers at startup (no runtime allocation)
- Implement buffer recycling to avoid allocations

```python
import os
import ctypes
import threading

def set_realtime_priority(thread: threading.Thread, priority: int = 80):
    """Set real-time scheduling for processing threads."""
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

### Memory Management

- Use texture pooling to reuse GPU buffers
- Implement buffer recycling to avoid allocations
- Use compressed texture formats when possible
- Monitor memory usage and trigger garbage collection

---

## Error Handling

### Graceful Degradation

```python
class AudioReactivityManager:
    def __init__(self, ...):
        # ...
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        
    def process_audio_frame(self, audio_frame):
        try:
            # Normal processing
            result = self._process_frame(audio_frame)
            return result
        except ProcessingError as e:
            self.error_state = True
            self.last_error = str(e)
            logger.error(f"Processing error: {e}")
            
            # Attempt recovery
            if self._recover_from_error():
                return self._get_fallback_result()
            else:
                # Return safe fallback
                return self._create_safe_fallback()
        except Exception as e:
            self.error_state = True
            self.last_error = str(e)
            logger.critical(f"Unexpected error: {e}")
            return self._create_safe_fallback()
    
    def _recover_from_error(self) -> bool:
        """Attempt to recover from transient errors."""
        if self.recovery_attempts > 5:
            return False
            
        try:
            # Reset internal state
            self._reset_internal_state()
            self.recovery_attempts += 1
            return True
        except:
            return False
    
    def _create_safe_fallback(self) -> AudioReactivityFeatures:
        """Create a safe fallback feature set."""
        return AudioReactivityFeatures(
            bass_energy=0.0,
            mid_energy=0.0,
            high_energy=0.0,
            beat_confidence=0.0,
            tempo_estimate=120.0,
            phase=0.0,
            spectral_centroid=0.0,
            spectral_rolloff=0.0,
            spectral_flatness=0.0,
            mfcc_1=0.0, mfcc_2=0.0, mfcc_3=0.0, 
            mfcc_4=0.0, mfcc_5=0.0, mfcc_6=0.0,
            timestamp=time.time()
        )
```

### Error Recovery

```python
def recover_from_error(self):
    """Attempt to recover from transient errors."""
    if not self.error_state:
        return True
        
    # Try to reset state
    try:
        # Close and reopen audio device
        self._close_audio_device()
        self._open_audio_device()
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        return True
    except:
        # Escalate to manager-level recovery
        self._notify_manager_of_failure()
        return False
```

---

## Configuration System

### JSON Configuration

```json
{
  "audio_reactivity": {
    "enabled": true,
    "sample_rate": 44100,
    "hop_size": 1024,
    "processing_threads": 1,
    "latency_budget": 50.0,
    "cpu_budget": 5.0,
    "memory_budget": 30.0,
    "feature_extraction": {
      "enabled": true,
      "mfcc_bands": 13,
      "band_edges": [20, 100, 300, 600, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000]
    },
    "beat_detection": {
      "enabled": true,
      "tempo_range": [60, 180],
      "confidence_threshold": 0.5,
      "state_machine": {
        "searching": "Waiting for clear beat pattern",
        "tracking": "Following beat pattern",
        "lost": "Lost beat pattern, searching"
      }
    },
    "parameter_mapping": {
      "enabled": true,
      "default_mappings": {
        "bass_energy": {
          "target": "intensity",
          "scale": 1.0,
          "offset": 0.0
        },
        "mid_energy": {
          "target": "distortion",
          "scale": 0.8,
          "offset": 0.2
        },
        "high_energy": {
          "target": "brightness",
          "scale": 1.2,
          "offset": -0.1
        },
        "beat_confidence": {
          "target": "pulse_intensity",
          "scale": 2.0,
          "offset": 0.0
        }
      }
    }
  }
}
```

### Loading Configuration

```python
def load_config(config_path: str) -> AudioReactivityConfig:
    """Load audio reactivity configuration from JSON."""
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    # Validate required fields
    required_fields = ['enabled', 'sample_rate', 'hop_size']
    for field in required_fields:
        if field not in config['audio_reactivity']:
            raise ValueError(f"Missing required field: {field}")
            
    # Create config object
    config_obj = AudioReactivityConfig()
    config_obj.enabled = config['audio_reactivity']['enabled']
    config_obj.sample_rate = config['audio_reactivity']['sample_rate']
    config_obj.hop_size = config['audio_reactivity']['hop_size']
    config_obj.processing_threads = config['audio_reactivity'].get('processing_threads', 1)
    config_obj.latency_budget = config['audio_reactivity'].get('latency_budget', 50.0)
    config_obj.cpu_budget = config['audio_reactivity'].get('cpu_budget', 5.0)
    config_obj.memory_budget = config['audio_reactivity'].get('memory_budget', 30.0)
    
    # Load feature extraction settings
    fe_config = config['audio_reactivity']['feature_extraction']
    config_obj.feature_extraction.enabled = fe_config.get('enabled', True)
    config_obj.feature_extraction.mfcc_bands = fe_config.get('mfcc_bands', 13)
    config_obj.feature_extraction.band_edges = fe_config.get('band_edges', [20, 100, 300, 600, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000])
    
    # Load beat detection settings
    bd_config = config['audio_reactivity']['beat_detection']
    config_obj.beat_detection.enabled = bd_config.get('enabled', True)
    config_obj.beat_detection.tempo_range = bd_config.get('tempo_range', [60, 180])
    config_obj.beat_detection.confidence_threshold = bd_config.get('confidence_threshold', 0.5)
    config_obj.beat_detection.state_machine = bd_config.get('state_machine', {})
    
    # Load parameter mapping settings
    pm_config = config['audio_reactivity']['parameter_mapping']
    config_obj.parameter_mapping.enabled = pm_config.get('enabled', True)
    config_obj.parameter_mapping.default_mappings = pm_config.get('default_mappings', {})
    
    return config_obj
```

---

## Implementation Tips

1. **Start Simple**: Begin with basic feature extraction before adding complex beat detection
2. **Use Data Classes**: For feature structures to ensure type safety
3. **Implement Proper Cleanup**: Handle resource cleanup on manager shutdown
4. **Add Debug Visualization**: Provide WebSocket endpoint to visualize feature extraction
5. **Test Edge Cases**: Handle zero-energy frames, silent audio, extreme tempo changes
6. **Profile Early**: Measure performance on target hardware from the start
7. **Use Dependency Injection**: Make feature extractors injectable for testing
8. **Implement Fallbacks**: Provide dummy features when audio processing fails
9. **Add Monitoring**: Track processing latency and error rates
10. **Document Signal Flow**: Provide clear documentation of feature flow

---

## Performance Optimization Checklist

- [ ] Use lock-free data structures for shared state
- [ ] Pre-allocate all audio buffers
- [ ] Use SIMD for audio processing operations
- [ ] Pin processing threads to dedicated CPU cores
- [ ] Set real-time scheduling priority for audio thread
- [ ] Implement buffer recycling to avoid allocations
- [ ] Use texture atlasing for multiple render targets
- [ ] Monitor CPU and memory usage continuously
- [ ] Profile with realistic workloads on target hardware
- [ ] Optimize hot paths identified in profiling

---

## Testing Checklist

- [ ] All unit tests pass with 100% coverage
- [ ] Integration tests verify complete audio reactivity pipeline
- [ ] Performance tests meet all latency and CPU budgets
- [ ] Stress tests with maximum features and mappings
- [ ] Edge case testing (silent audio, extreme values, etc.)
- [ ] Hardware validation on Orange Pi 5
- [ ] CI/CD pipeline runs all tests on every commit
- [ ] No memory leaks detected with valgrind
- [ ] No performance regressions compared to baseline
- [ ] Dynamic mapping works correctly for all feature types
- [ ] Fallback mechanisms work when audio is unavailable

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 20 tests implemented and passing
- [ ] Test coverage >= 90%
- [ ] Performance budget met on Orange Pi 5 hardware
- [ ] Feature extraction latency < 10ms measured
- [ ] Beat detection accuracy within 5% verified
- [ ] Parameter mapping correctness verified
- [ ] Plugin bus integration verified with 3+ effects
- [ ] Fallback to dummy processor works when no audio
- [ ] USB hot-plug tested with audio devices
- [ ] CI/CD pipeline runs tests on every commit
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-A5: Audio Reactivity` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### SPRINT_02_AUDIO_REACTIVITY.md (L209-228) [VJlive (Original)]
```python
self.handlers['add_audio_mapping'] = self._handle_add_audio_mapping
self.handlers['remove_audio_mapping'] = self._handle_remove_audio_mapping
self.handlers['get_audio_mappings'] = self._handle_get_audio_mappings

def _handle_add_audio_mapping(self, data):
    """Add audio reactivity mapping."""
    self.matrix.add_audio_mapping(
        audio_feature=data['audio_feature'],
        target_param=data['target_param'],
        scale=data.get('scale', 1.0),
        offset=data.get('offset', 0.0)
    )
```

This shows the audio mapping interface used in the reactivity system.

### SPRINT_02_AUDIO_REACTIVITY.md (L513-532) [VJlive (Original)]
```python
- ✅ Basic BPM tracking

### Future Enhancements (Post-Beta)
- 🔲 Multi-band onset detection (more instrument types)
- 🔲 Machine learning beat tracking (librosa)
- 🔲 MIDI clock sync input
- 🔲 Audio file analysis (pre-analyze tracks)
- 🔲 Harmonic/percussive separation
```

This shows the current state and future plans for audio reactivity.

### SPRINT_STATUS_CURRENT.md (L17-36) [VJlive (Original)]
```markdown
- Cross-effect modulation: bass drives depth, treble controls color, mid controls distortion
- **Performance**: 60FPS maintained with full audio reactivity

**Neural Network Integration**:
- **ONNX Runtime**: Real-time inference with GPU acceleration
- **Style Transfer**: Fast-neural-style models (30ms latency on RTX 3060+)
- **Depth Estimation**: MiDaS model for RGB→depth (60FPS)
- **Object Detection**: YOLO-based scene awareness for intelligent effects
- **Hardware Optimization**: TensorRT for NVIDIA, CoreML for Apple Silicon
```

This shows the performance level achieved in audio reactivity.

---

## Notes for Implementers

1. **Multi-Band Analysis**: Implement separate processing for bass, mid, and high frequencies
2. **Beat Confidence**: Provide confidence scores for beat detection to allow effects to respond appropriately
3. **Parameter Scaling**: Allow fine-grained control over how audio features map to visual parameters
4. **Temporal Smoothing**: Apply smoothing to prevent jittery parameter changes
5. **Dynamic Range Mapping**: Implement non-linear mapping for more natural visual responses
6. **Feature History**: Maintain a history of features for temporal effects
7. **Confidence Thresholding**: Allow filtering of low-confidence feature values
8. **Hardware Acceleration**: Leverage GPU for FFT and matrix operations
9. **Thread Safety**: Ensure all operations are thread-safe
10. **Error Isolation**: Prevent failures in one effect from affecting others

---

## Implementation Roadmap

1. **Week 1**: Design audio reactivity pipeline architecture
2. **Week 2**: Implement core feature extraction and beat detection
3. **Week 3**: Add parameter mapping system
4. **Week 4**: Integrate with effect system and add visualization
5. **Week 5**: Performance optimization and testing
6. **Week 6**: Integration with AudioSourceManager and EffectBus
7. [ ] **Week 7**: Final testing and documentation

---
-

## References

- `core/audio/audio_reactivity.py` (to be implemented)
- `core/effects/effect_bus.py` (to be referenced)
- `core/plugin_bus.py` (for broadcasting)
- `core/signal_flow_manager.py` (for audio routing)
- `librosa` library (for audio processing)
- `scipy.signal` (for filtering operations)
- `numpy` (for array operations)
- BeatRoot algorithm for beat tracking
- Dynamic programming approaches for parameter mapping

---

## Conclusion

The Audio Reactivity module is the sensory nervous system of VJLive3, transforming raw audio into the dynamic visual parameters that drive the entire visual experience. Its multi-stage processing pipeline (preprocessing → feature extraction → beat detection → parameter mapping) provides a robust foundation for creating richly responsive visual compositions. By implementing sophisticated signal processing, intelligent parameter mapping, and robust error handling, this module will enable creators to build deeply immersive, audio-responsive visual performances that react intelligently to the emotional and rhythmic content of music.

---

## As-Built Implementation Notes

**Date:** 2026-03-03 | **Agent:** Antigravity | **Coverage:** 80%

### Files Created
- `src/vjlive3/audio/reactivity.py` — 278 lines
- `tests/audio/test_reactivity.py` — 12 tests

### Class Mapping — Spec vs Actual

| Spec Class | Actual Class | Notes |
|---|---|---|
| `AudioReactivityManager` | `AudioReactivityManager` | ✅ Core manager implemented |
| `AudioReactivityFeatures` | `AudioReactivityFeatures` | ✅ Dataclass with 16 fields |
| `ParameterMapper` | `ParameterMapper` | ✅ scale/offset/clamp mapping |
| `AudioReactor` | *in analyzer.py* | ⚠️ Located in A1 module, not A5 |
| `EffectParameterController` | *not implemented* | ⚠️ Deferred — subsumed by ParameterMapper |

### Dependencies — Spec vs Actual

| Spec Dependency | Used? | Note |
|---|---|---|
| `librosa` | ❌ No | numpy.fft.rfft used for all spectral work |
| `scipy.signal` | ❌ No | No Butterworth/Chebyshev filters |
| `numpy` | ✅ Yes | FFT, band energies, spectral features |
| BeatDetector (A2) | ❌ No | Beat detection reimplemented inline in `_detect_beat()` |

### ADRs
1. **Pseudo-MFCCs** — 6 log-spaced band energies used instead of true Mel filterbank + DCT. Standard MFCC requires librosa or a full Mel matrix implementation. The 6-band energies provide similar visual texture. Spec should be updated to reflect this when a full MFCC implementation is ready.
2. **Inline beat detection** — `AudioReactivityManager._detect_beat()` reimplements spectral flux onset detection rather than delegating to `BeatDetector` from A2. Chosen to keep A5 self-contained; future refactor should unify using A2.
3. **No EffectParameterController** — `ParameterMapper.get_active_mappings()` + `map_features_to_parameter()` cover the same territory without a separate controller class.