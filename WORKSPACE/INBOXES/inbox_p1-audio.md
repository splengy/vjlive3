# P1-Audio: Core Audio Infrastructure

## Task Overview
Implement the core audio infrastructure for VJLive3, including FFT analysis, beat detection, audio-reactive framework, and multi-source audio input.

## Specifications

### P1-A1: FFT + Waveform Analysis Engine
**Spec:** `docs/specs/P1-A1_audio_analyzer.md`
- Real-time FFT computation with sub-10ms latency
- Waveform analysis for time-domain signal processing
- Multi-channel support (stereo and beyond)
- Thread-safe access for concurrent plugins
- Integration with audio-reactive effects

### P1-A2: Real-time Beat Detection
**Spec:** `docs/specs/P1-A2_beat_detector.md`
- Beat detection with >95% accuracy on reference tracks
- Tempo tracking with <2% error over 30-second periods
- Onset detection for note transients
- Rhythm pattern analysis
- Integration with timecode sync system

### P1-A3: Audio-Reactive Effect Framework
**Spec:** `docs/specs/P1-A3_reactivity_bus.md`
- Parameter mapping from audio features to visual parameters
- Smooth interpolation for parameter transitions
- Support for spectrum, beat, waveform, and pattern effects
- Real-time performance at 60 FPS
- Integration with all audio analysis systems

### P1-A4: Multi-Source Audio Input
**Spec:** `docs/specs/P1-A4_audio_sources.md`
- Support for microphone, line input, audio files, network streams
- Real-time source switching without glitches
- Audio mixing with individual level control
- Low-latency operation (<10ms for live sources)
- Format conversion and sample rate handling

## Implementation Requirements

### Core Architecture
- **Thread Safety**: All components must be thread-safe
- **Performance**: Maintain 60 FPS target with audio processing
- **Integration**: Seamless integration with existing plugin system
- **Testing**: Comprehensive test coverage (>80%)
- **Documentation**: Complete API documentation

### Dependencies
- NumPy for numerical operations
- SciPy for signal processing
- PyAudio/PortAudio for audio I/O
- ModernGL for GPU acceleration (optional)
- Threading and synchronization primitives

### Testing Strategy
- Unit tests for all core algorithms
- Performance benchmarks for latency targets
- Integration tests with complete audio pipeline
- Stress tests with multiple simultaneous sources
- Cross-platform compatibility testing

## Phase 1 Gate Requirements
- [ ] FFT analysis with <10ms latency at 1024-point FFT
- [ ] Beat detection accuracy >95% on standard tracks
- [ ] Audio-reactive framework updates at 60 FPS
- [ ] Multi-source audio input with <10ms latency
- [ ] All components integrate seamlessly with plugin system
- [ ] Comprehensive test coverage (>80%)
- [ ] Documentation complete for all APIs

## Safety Rails
- Memory usage <10MB per instance
- CPU usage <5% on modern hardware
- No audio artifacts or distortion
- Graceful degradation on device failure
- Proper resource cleanup on shutdown

## Related Tasks
- P1-R3: Shader compilation system (for visual effects)
- P2-X2: Timecode sync system (for beat synchronization)
- P3-VDxx: Depth plugins (will use audio analysis)
- P4-AUxx: Audio plugins (will use audio infrastructure)

## Implementation Notes
- Use double buffering for glitch-free operation
- Implement adaptive quality based on system load
- Cache intermediate results for repeated queries
- Provide both magnitude and phase information for FFT
- Support real-time parameter adjustment for all components

## Verification Criteria
- All components meet performance targets
- Seamless integration with existing systems
- Comprehensive test coverage achieved
- Documentation complete and accurate
- No safety rail violations during operation