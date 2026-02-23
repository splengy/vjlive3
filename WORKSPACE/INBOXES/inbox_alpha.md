# INBOX: Implementation Engineer Assignment

## Mission
Implement the core `AudioEngine` infrastructure for VJLive3. This is a foundational component that manages all audio input, analysis, and reactivity for the entire system. The AudioEngine must be robust, low-latency, and capable of handling multiple concurrent audio streams with sample-accurate synchronization.

## Specification
**Reference**: `docs/specs/P4-COR118_AudioEngine.md`

### Key Requirements
- **Multi-Source Audio Management**: Support microphone, line-in, audio files, and network streams
- **Real-time Analysis**: FFT (2048+ bins), beat detection, feature extraction (RMS, spectral centroid, bands)
- **Quantum Integration**: Optional quantum-enhanced analysis modules
- **Event Bus Integration**: Publish audio features and beat events for plugin consumption
- **Thread Safety**: Lock-free or fine-grained locking for real-time performance
- **Error Resilience**: Graceful handling of device failures with fallback sources
- **Performance**: <15% CPU for 4 sources, latency ≤ 30 ms from capture to features
- **Testing**: ≥80% code coverage with stress tests and failure simulations

### Code Files
```
src/vjlive3/audio/
├── __init__.py
├── engine.py              # AudioEngine class (main implementation)
├── source.py              # AudioSource base class and concrete implementations
├── analyzer.py            # AudioAnalyzer (FFT, beat detection, feature extraction)
├── config.py              # AudioConfig Pydantic model
├── reactive.py            # AudioReactiveEngine integration
├── quantum.py             # QuantumAudioAnalyzer (optional)
└── __init__.py

tests/audio/
├── __init__.py
├── test_engine.py         # AudioEngine lifecycle, threading, error handling
├── test_sources.py        # AudioSource creation, routing, volume control
├── test_features.py       # Feature extraction accuracy, beat detection
├── test_integration.py    # AudioEngine + AudioReactiveEngine integration
├── test_performance.py    # Latency, CPU usage, stress testing
└── test_error_handling.py # Device failure recovery, fallback behavior
```

### Documentation
- **README.md**: AudioEngine architecture, usage examples, API reference
- **API.md**: Detailed public interface documentation with type hints
- **PERFORMANCE.md**: Performance benchmarks, optimization notes, profiling results
- **TESTING.md**: Test strategy, coverage report, stress test procedures

### Verification
- [ ] Unit tests: ≥80% coverage across all modules
- [ ] Integration tests: AudioEngine + AudioReactiveEngine + RenderEngine
- [ ] Performance tests: Latency <30 ms, CPU <15% for 4 sources
- [ ] Stress tests: 8+ sources, 24-hour continuous operation
- [ ] Error handling: Device failure recovery, fallback sources
- [ ] Manual QA: Microphone input, file playback, device switching

## Workflow Protocol

### Phase 1: Foundation (Days 1-2)
1. **Setup**: Create project structure, add to `pyproject.toml`
2. **Configuration**: Define `AudioConfig` Pydantic model with device preferences
3. **Base Classes**: Implement `AudioSource` base class and concrete subclasses
4. **Testing Infrastructure**: Set up pytest, coverage, mock audio devices

### Phase 2: Core Engine (Days 3-5)
1. **AudioEngine Class**: Implement singleton pattern, lifecycle management
2. **Device Management**: Enumerate devices, handle hotplug, fallback sources
3. **Threading Model**: Capture threads, analysis thread, lock-free buffers
4. **Basic Analysis**: FFT using NumPy, simple RMS volume calculation

### Phase 3: Advanced Analysis (Days 6-8)
1. **Beat Detection**: Spectral flux algorithm, adaptive thresholding
2. **Feature Extraction**: Spectral centroid, rolloff, zero-crossing rate
3. **Frequency Bands**: Bass/mid/treble decomposition with configurable ranges
4. **Quantum Integration**: Optional quantum-enhanced analysis modules

### Phase 4: Integration & Polish (Days 9-10)
1. **Event Bus**: Publish `AudioFeaturesUpdated`, `BeatDetected` events
2. **AudioReactiveEngine**: Wire up audio features to DMX output
3. **Configuration Persistence**: Save/restore audio settings
4. **Performance Optimization**: Profile with `cProfile`, eliminate hotspots
5. **Documentation**: Complete API docs, usage examples, performance benchmarks

### Phase 5: Testing & Validation (Days 11-12)
1. **Unit Tests**: ≥80% coverage, include edge cases and error conditions
2. **Integration Tests**: End-to-end audio pipeline testing
3. **Performance Tests**: Latency measurement, CPU profiling, stress testing
4. **Manual QA**: Real hardware testing, device switching, failure scenarios

## Safety Rails Reminder

### RAIL 1: 60 FPS SACRED
- Audio analysis must not block the render loop
- Use dedicated threads for capture and analysis
- Profile to ensure <15% CPU usage for 4 sources

### RAIL 2: OFFLINE-FIRST ARCHITECTURE
- AudioEngine must work without network connectivity
- Network streams are optional features, not core dependencies

### RAIL 3: PLUGIN SYSTEM INTEGRITY
- AudioEngine must integrate cleanly with existing plugin system
- Use event bus for communication, not direct coupling

### RAIL 4: CODE SIZE DISCIPLINE
- Keep implementation under 750 lines per module
- Use composition over inheritance where appropriate

### RAIL 5: TEST COVERAGE GATE
- ≥80% code coverage mandatory
- Include stress tests and failure simulations

### RAIL 6: HARDWARE INTEGRATION SAFETY
- Graceful handling of device loss/reconnection
- Fallback to dummy sources on failure
- No crashes during hardware hotplug

### RAIL 7: NO SILENT FAILURES
- All exceptions logged with context
- Audio device failures reported via health monitor
- Fallback behavior clearly documented

### RAIL 8: RESOURCE LEAK PREVENTION
- Proper cleanup of audio devices and threads
- Use context managers for resource management
- Monitor memory usage during stress tests

## Resources

### Legacy References
- `vjlive/audio/engine.py` — AudioEngine (legacy implementation)
- `vjlive/audio/analyzer.py` — AudioAnalyzer (FFT + beat detection)
- `vjlive/audio/source.py` — AudioSource base class
- `VJlive-2/src/audio/` — Existing audio analysis modules (if any)

### Existing VJLive3 Code
- `src/vjlive3/core/midi_controller.py` — Device management pattern
- `src/vjlive3/plugins/astra.py` — Threaded capture pattern
- `src/vjlive3/render/engine.py` — Render loop integration example
- `src/vjlive3/core/event_bus.py` — Event bus for audio events

### External Documentation
- PyAudio documentation: https://people.csail.mit.edu/hubert/pyaudio/
- FFT theory: https://en.wikipedia.org/wiki/Fast_Fourier_transform
- Beat detection: "A Streamlined Beat-Tracking System for Music" (Simon Dixon)
- NumPy FFT: https://numpy.org/doc/stable/reference/routines.fft.html

### Tools
- **PyAudio**: Cross-platform audio I/O
- **NumPy**: FFT and numerical operations
- **pytest**: Unit testing framework
- **coverage.py**: Test coverage measurement
- **cProfile**: Performance profiling
- **py-spy**: CPU profiling

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

## Next Steps

1. **Read the specification**: `docs/specs/P4-COR118_AudioEngine.md`
2. **Set up development environment**: Create project structure, add dependencies
3. **Start with configuration**: Define `AudioConfig` Pydantic model
4. **Implement base classes**: `AudioSource` and concrete implementations
5. **Build core engine**: `AudioEngine` class with lifecycle management
6. **Add analysis pipeline**: FFT, beat detection, feature extraction
7. **Wire up integration**: Event bus, AudioReactiveEngine, health monitoring
8. **Write tests**: Unit tests alongside implementation (TDD style)
9. **Profile and optimize**: Ensure performance targets are met
10. **Document**: Complete API docs and usage examples

**Remember**: This is a **core infrastructure** component. It must be robust, well-tested, and performant. Follow the workflow: SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD.
