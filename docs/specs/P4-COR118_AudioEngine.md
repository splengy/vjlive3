# P4-COR118: AudioEngine — Core Audio Infrastructure

## Mission Context
The `AudioEngine` is the central orchestrator for all audio-related functionality in VJLive3. It manages multi-source audio input (microphones, line inputs, files, streams), coordinates audio analysis (FFT, beat detection, feature extraction), and provides audio reactivity data to the rest of the system. This is a core infrastructure component that must be robust, low-latency, and capable of handling multiple concurrent audio streams with sample-accurate synchronization.

## Technical Requirements

### Core Responsibilities
1. **Multi-Source Audio Management**
   - Support multiple audio source types: microphone, line-in, audio files, network streams
   - Each source has independent routing, volume, and processing controls
   - Thread-safe capture and playback with minimal latency
   - Automatic device enumeration and selection

2. **Audio Analysis Pipeline**
   - Real-time FFT (Fast Fourier Transform) with configurable resolution (e.g., 1024-8192 bins)
   - Beat/onset detection using spectral flux and energy-based algorithms
   - Feature extraction: RMS volume, spectral centroid, spectral rolloff, zero-crossing rate
   - Frequency band decomposition: bass (20-250 Hz), mid (250-4000 Hz), treble (4000+ Hz)

3. **Quantum-Enhanced Reactivity** (if applicable)
   - Integration with quantum audio analysis modules
   - Quantum-enhanced feature extraction for deeper musical insights
   - Predictive modulation based on quantum coherence

4. **AudioReactiveEngine Integration**
   - Provide processed audio features to `AudioReactiveEngine` for DMX output
   - Publish audio analysis data via event bus for plugin consumption
   - Support for audio-reactive effect parameters via `AudioReactorManager`

5. **Resource Management**
   - Efficient memory usage with buffer pooling
   - Graceful handling of audio device loss/reconnection
   - CPU/GPU load balancing for analysis tasks
   - Configurable quality/performance tradeoffs

6. **State Persistence**
   - Save/restore audio configuration (device selection, volumes, analysis settings)
   - Persist audio-reactive presets and mappings

### Architecture Constraints
- **Singleton Pattern**: One global `AudioEngine` instance coordinated via `AIIntegration` or standalone
- **Async Operations**: All audio capture and heavy analysis must be non-blocking
- **Thread Safety**: Lock-free or fine-grained locking for real-time performance
- **Error Resilience**: Audio device failures must not crash the system; fallback to dummy sources
- **Sample-Accurate Timing**: Use PTS (presentation timestamps) for synchronization with video

### Key Interfaces
```python
class AudioEngine:
    def __init__(self, config: AudioConfig, event_bus: Optional[EventBus] = None):
        """Initialize audio engine with configuration."""
        pass

    def initialize(self) -> None:
        """Enumerate devices, create default sources, start audio threads."""
        pass

    def start(self) -> None:
        """Begin audio capture/playback."""
        pass

    def stop(self) -> None:
        """Pause all audio activity."""
        pass

    def cleanup(self) -> None:
        """Release audio resources, close devices."""
        pass

    def add_source(self, source_type: AudioSourceType, device_id: str, **kwargs) -> AudioSource:
        """Create and register a new audio source."""
        pass

    def remove_source(self, source_id: str) -> None:
        """Unregister and destroy an audio source."""
        pass

    def get_source(self, source_id: str) -> Optional[AudioSource]:
        """Retrieve a registered audio source."""
        pass

    def get_features(self, source_id: str) -> AudioFeatures:
        """Get latest audio features (FFT, beat, bands) for a source."""
        pass

    def set_master_volume(self, volume: float) -> None:
        """Adjust master output volume (0.0-1.0)."""
        pass

    def get_spectrum(self, source_id: str) -> np.ndarray:
        """Return current FFT magnitude spectrum."""
        pass

    def get_waveform(self, source_id: str) -> np.ndarray:
        """Return current time-domain waveform."""
        pass

    def subscribe_to_beats(self, callback: Callable[[BeatEvent], None]) -> None:
        """Register for beat detection events."""
        pass

    def get_status(self) -> AudioEngineStatus:
        """Return health status and statistics."""
        pass
```

### Dependencies
- **ConfigManager**: Load `AudioConfig` (device preferences, analysis parameters)
- **EventBus**: Publish `AudioFeaturesUpdated`, `BeatDetected`, `SourceAdded/Removed` events
- **HealthMonitor**: Report audio engine health and device status
- **AudioFeatureExtractor**: Standalone feature extraction utility (may be inlined)
- **AudioAnalyzer**: Legacy compatibility adapter if needed
- **AudioReactiveEngine**: Consumer of audio features for DMX output
- **AudioReactorManager**: Manages parameter reactivity bindings
- **QuantumAudioAnalyzer** (optional): Quantum-enhanced analysis module

## Implementation Notes

### Audio Backend Selection
- Use **PyAudio** (PortAudio wrapper) for cross-platform audio I/O
- Alternative: **sounddevice** (more Pythonic, but less control)
- For advanced processing: **PySoundFile** (libsndfile) for file playback
- Consider **GStreamer** for network streams and complex pipelines

### FFT Implementation
- Use **NumPy FFT** (FFTW if available for speed)
- Window function: Hann or Hamming to reduce spectral leakage
- Overlap: 50% or 75% for smoother time resolution
- Real-time: Process in circular buffer to avoid allocation overhead

### Beat Detection Algorithm
- Combine energy-based onset detection with phase coherence
- Threshold: adaptive based on recent history (e.g., 1.3x median energy)
- Tempo estimation: autocorrelation of onset envelope for BPM tracking
- Output: `BeatEvent` with timestamp, confidence, and beat position

### Threading Model
- **Capture Thread**: Dedicated thread per audio source, lock-free ring buffers
- **Analysis Thread**: Single thread processes all sources sequentially to avoid lock contention
- **Main Thread**: Consumes audio features for rendering (called from render loop)
- Use `queue.Queue` or `collections.deque` with `maxlen` for circular buffers

### Error Handling
- **Device Unavailable**: Fall back to dummy source (silence or test tone)
- **Buffer Underrun**: Log warning, increase buffer size if persistent
- **Sample Rate Mismatch**: Resample to engine's internal rate (e.g., 48 kHz)
- **Exception in Callback**: Catch and log, do not propagate to main thread

## Verification Checkpoints

### 1. Unit Tests (≥80% coverage)
- [ ] `tests/audio/test_engine.py`: AudioEngine lifecycle (init, start, stop, cleanup)
- [ ] `tests/audio/test_sources.py`: AudioSource creation, routing, volume control
- [ ] `tests/audio/test_features.py`: Feature extraction accuracy (FFT, beat, bands)
- [ ] `tests/audio/test_threading.py`: Thread safety, lock-free operations
- [ ] `tests/audio/test_error_handling.py`: Device failure recovery, fallback behavior
- [ ] `tests/audio/test_performance.py`: Latency measurement (<10 ms capture-to-features)

### 2. Integration Tests
- [ ] AudioEngine + AudioReactiveEngine: Features correctly drive DMX output
- [ ] AudioEngine + RenderEngine: Audio-reactive effects respond in real-time
- [ ] Multi-source mixing: Multiple microphones + file playback mixed correctly
- [ ] Event bus: Beat events trigger visual effects with accurate timing

### 3. Manual QA
- [ ] Connect microphone, speak/clap: beat detection triggers on transients
- [ ] Play audio file: FFT spectrum shows correct frequency content
- [ ] Switch audio devices mid-performance: seamless transition without dropouts
- [ ] Simulate device unplug: engine continues with fallback, logs error
- [ ] Stress test: 8+ simultaneous audio sources, CPU usage <30% on target hardware

## Resources

### Legacy References
- `vjlive/audio/engine.py` — AudioEngine (legacy implementation)
- `vjlive/audio/analyzer.py` — AudioAnalyzer (FFT + beat detection)
- `vjlive/audio/source.py` — AudioSource base class
- `VJlive-2/src/audio/` — Existing audio analysis modules (if any)

### Existing VJLive3 Code
- `src/vjlive3/core/midi_controller.py` — Example of device management pattern
- `src/vjlive3/plugins/astra.py` — Threaded capture pattern (AstraDepthCamera)
- `src/vjlive3/render/engine.py` — Render loop integration example

### External Documentation
- PyAudio documentation: https://people.csail.mit.edu/hubert/pyaudio/
- FFT theory: https://en.wikipedia.org/wiki/Fast_Fourier_transform
- Beat detection: "A Streamlined Beat-Tracking System for Music" (Simon Dixon)

## Success Criteria

### Functional Completeness
- [ ] AudioEngine can enumerate and open at least 2 audio devices simultaneously
- [ ] FFT resolution ≥ 2048 bins, latency ≤ 20 ms from capture to features
- [ ] Beat detection accuracy ≥ 95% on test dataset (provided)
- [ ] All audio sources mixed correctly with independent volume control
- [ ] Event bus publishes at least 10 audio feature updates per second

### Performance
- [ ] CPU usage: <15% for 4 simultaneous sources at 48 kHz, 2048-bin FFT
- [ ] Memory: <50 MB for engine + 4 sources (excluding audio buffers)
- [ ] No audio dropouts or glitches during 1-hour stress test
- [ ] Latency from microphone input to feature availability: ≤ 30 ms

### Reliability
- [ ] System recovers gracefully from device unplug/replug
- [ ] No crashes during 24-hour continuous operation
- [ ] All exceptions logged with context, no silent failures
- [ ] Unit test coverage ≥ 80%

### Integration
- [ ] AudioEngine integrates with `AudioReactiveEngine` for DMX output
- [ ] Audio-reactive plugins can subscribe to audio features via event bus
- [ ] Configuration persists across application restarts
- [ ] Works in headless mode (no display) for server deployments

## Dependencies (Blocking)
- P1-A1: FFT + waveform analysis engine (provides low-level analysis primitives)
- P1-A3: Audio-reactive effect framework (defines event bus interfaces)
- ConfigManager: For loading `AudioConfig`
- EventBus: For publishing audio events

## Notes for Implementation Engineer (Alpha)

This is a **core infrastructure** component. It must be:
- **Robust**: Audio is real-time; no garbage collection pauses, no blocking I/O in main thread
- **Well-tested**: 80% coverage mandatory, include stress tests and failure simulations
- **Performant**: Profile with `cProfile` and `py-spy` to eliminate hotspots
- **Documented**: Every public method has docstring with parameter/return types

Start by:
1. Reading `vjlive/audio/engine.py` to understand legacy design
2. Defining `AudioConfig` Pydantic model (if not already defined)
3. Implementing `AudioSource` base class and concrete subclasses (MicrophoneSource, FileSource, etc.)
4. Building the FFT/beat detection pipeline using NumPy
5. Wiring up event bus and health monitoring
6. Writing tests alongside implementation (TDD style)

The spec is **auto-approved**. Proceed to implementation following the workflow: SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD.
