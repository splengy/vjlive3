# P1-A1: FFT + Waveform Analysis Engine

## Overview
A high-performance audio analysis system that provides real-time FFT and waveform data for audio-reactive visual effects.

## Technical Requirements

### Core Functionality
- **FFT Analysis**: Real-time Fast Fourier Transform computation
- **Waveform Analysis**: Time-domain signal processing
- **Multi-channel Support**: Handle stereo and multi-channel audio
- **Low Latency**: Sub-10ms processing time
- **Thread Safety**: Safe concurrent access from multiple plugins

### Input/Output
- **Input**: Audio buffer (float32, 44.1kHz or 48kHz)
- **Output**: FFT spectrum (magnitude + phase), waveform data

### Parameters
- `fft_size`: FFT window size (128, 256, 512, 1024, 2048)
- `hop_size`: FFT hop size (50% overlap default)
- `window_type`: Hamming, Hann, Blackman, or rectangular
- `smoothing`: Spectral smoothing factor (0-1.0)
- `peak_decay`: Peak hold decay time (ms)
- `min_frequency`: Minimum frequency to analyze (20Hz)
- `max_frequency`: Maximum frequency to analyze (20kHz)

### Architecture
- **AudioBuffer**: Circular buffer for incoming audio
- **FFTProcessor**: Core FFT computation using NumPy/FFTW
- **WaveformProcessor**: Time-domain signal analysis
- **AnalyzerManager**: Thread-safe access control
- **DataCache**: Recent analysis results for smooth transitions

### Performance Considerations
- Use SIMD-optimized FFT libraries (FFTW, Intel MKL)
- Implement double buffering for thread safety
- Cache intermediate results for repeated queries
- Use GPU acceleration for large FFT sizes
- Implement adaptive quality based on system load

## Integration Points
- **Plugin System**: Register as AudioAnalyzer
- **Node Graph**: Add to audio analysis node collection
- **MIDI Mapping**: Map analysis parameters to MIDI
- **Audio Sources**: Connect to multiple audio input sources
- **Effect Framework**: Provide data to audio-reactive effects

## Testing Requirements
- **Unit Tests**: Verify FFT accuracy against reference implementations
- **Performance Tests**: Ensure sub-10ms latency
- **Stress Tests**: Handle high sample rates and multiple channels
- **Thread Safety Tests**: Concurrent access validation
- **Audio Quality Tests**: Verify no artifacts or distortion

## Safety Rails
- **Memory Limits**: Monitor buffer sizes and allocations
- **Performance Guardrails**: Fallback to lower quality if overloaded
- **Input Validation**: Validate audio format and sample rate
- **Error Handling**: Graceful degradation on audio source failure
- **Resource Cleanup**: Proper buffer deallocation

## Dependencies
- NumPy for numerical operations
- SciPy for FFT implementation
- PyAudio or PortAudio for audio input
- ModernGL for GPU acceleration (optional)
- Threading and synchronization primitives

## Implementation Notes
- Use overlap-add method for continuous FFT analysis
- Implement spectral whitening for better frequency resolution
- Add beat detection as a derived feature
- Provide both magnitude and phase information
- Support real-time parameter adjustment

## Verification Criteria
- [ ] FFT accuracy within 0.1% of reference implementation
- [ ] Waveform analysis shows correct amplitude and timing
- [ ] Latency stays below 10ms at 1024-point FFT
- [ ] Thread-safe access from multiple plugins
- [ ] Smooth parameter transitions without glitches
- [ ] Handles sample rate changes gracefully
- [ ] No memory leaks after extended operation

## Related Tasks
- P1-A2: Real-time beat detection
- P1-A3: Audio-reactive effect framework
- P1-A4: Multi-source audio input
- P1-R3: Shader compilation system (for visual effects)

## Performance Targets
- FFT Size 128: <1ms latency
- FFT Size 256: <2ms latency  
- FFT Size 512: <4ms latency
- FFT Size 1024: <8ms latency
- FFT Size 2048: <15ms latency
- Memory usage: <10MB per instance
- CPU usage: <5% on modern hardware