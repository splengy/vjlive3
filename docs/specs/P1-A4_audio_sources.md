# P1-A4: Multi-Source Audio Input

## Overview
A flexible audio input system that supports multiple audio sources with real-time switching and mixing capabilities.

## Technical Requirements

### Core Functionality
- **Multiple Sources**: Support for various audio input types
- **Real-time Switching**: Seamless source switching without glitches
- **Audio Mixing**: Mix multiple sources with individual levels
- **Latency Management**: Minimize input latency
- **Format Conversion**: Handle different audio formats and sample rates

### Input Sources
- **Microphone**: Built-in or external microphones
- **Line Input**: Line-level audio inputs
- **Audio File**: Playback of audio files (MP3, WAV, FLAC)
- **Network Stream**: Audio over network protocols
- **Virtual Cable**: Virtual audio cable inputs
- **MIDI Audio**: Audio generated from MIDI events

### Parameters
- `source_type`: Microphone, line input, file, network, virtual, MIDI
- `device_index`: Hardware device index
- `sample_rate`: Audio sample rate (44.1kHz, 48kHz, 96kHz)
- `buffer_size`: Audio buffer size (256, 512, 1024, 2048 samples)
- `latency`: Target latency in milliseconds
- `volume`: Input volume level (0-100%)
- `pan`: Stereo panning (-100% to 100%)
- `mute`: Mute state
- `solo`: Solo state (for mixing)
- `mix_mode`: Replace, mix, or crossfade between sources

### Architecture
- **AudioInputManager**: Central manager for all audio sources
- **SourceRegistry**: Registry of available audio sources
- **FormatConverter**: Handles sample rate and format conversion
- **BufferManager**: Manages audio buffers and latency
- **MixerEngine**: Mixes multiple audio sources
- **DeviceManager**: Manages hardware audio devices
- **StreamProcessor**: Processes audio streams in real-time

### Performance Considerations
- Use double buffering for glitch-free operation
- Implement efficient format conversion algorithms
- Cache device information for quick access
- Use SIMD-optimized audio processing
- Implement adaptive buffering based on system load

## Integration Points
- **Audio Analyzer**: Connect to FFT and waveform analysis
- **Beat Detector**: Connect to beat detection algorithms
- **Audio-Reactive Effects**: Provide audio data to effects
- **Plugin System**: Register as AudioInputSource
- **Node Graph**: Add to audio input node collection
- **MIDI Mapping**: Map input parameters to MIDI

## Testing Requirements
- **Unit Tests**: Verify audio format conversion accuracy
- **Performance Tests**: Ensure low latency operation
- **Device Tests**: Validate all supported audio devices
- **Stress Tests**: Handle multiple simultaneous sources
- **Integration Tests**: Test with complete audio pipeline

## Safety Rails
- **Memory Limits**: Monitor audio buffer sizes
- **Performance Guardrails**: Fallback to lower quality if overloaded
- **Input Validation**: Validate audio format and device availability
- **Error Handling**: Graceful degradation on device failure
- **Resource Cleanup**: Proper device deallocation

## Dependencies
- PyAudio or PortAudio for audio I/O
- NumPy for audio processing
- Threading and synchronization primitives
- AudioAnalyzer for analysis integration
- BeatDetector for beat detection integration

## Implementation Notes
- Use WASAPI/CoreAudio for low-latency operation on Windows
- Implement ASIO support for professional audio interfaces
- Add support for JACK on Linux systems
- Provide virtual audio cable support for routing
- Implement audio file playback with format support

## Verification Criteria
- [ ] All supported audio devices work correctly
- [ ] Format conversion maintains audio quality
- [ ] Latency stays below 10ms for live sources
- [ ] Seamless source switching without glitches
- [ ] Audio mixing works with multiple sources
- [ ] No audio artifacts or distortion
- [ ] Handles sample rate changes gracefully

## Related Tasks
- P1-A1: FFT + Waveform Analysis Engine
- P1-A2: Real-time beat detection
- P1-A3: Audio-reactive effect framework
- P1-R3: Shader compilation system (for visual effects)

## Performance Targets
- Latency: <10ms for live sources
- Format conversion: <1ms per buffer
- Mixing: <2ms for 4 sources
- Memory usage: <10MB per instance
- CPU usage: <5% on modern hardware
- Sample rate support: 44.1kHz, 48kHz, 96kHz
- Buffer sizes: 256, 512, 1024, 2048 samples

## Advanced Features
- **Automatic Device Detection**: Auto-detect available audio devices
- **Device Profiles**: Save and load device configurations
- **Audio Routing**: Route audio between different applications
- **Real-time Effects**: Apply effects to audio input
- **Audio Recording**: Record audio from any source
- **Network Audio**: Stream audio over network protocols
- **MIDI Integration**: Convert MIDI to audio for analysis
- **Audio Analysis**: Real-time audio feature extraction

## Source Types Details
- **Microphone**: Built-in, USB, XLR, wireless
- **Line Input**: Instrument, mixer, synthesizer
- **Audio File**: MP3, WAV, FLAC, OGG, M4A
- **Network Stream**: Icecast, SHOUTcast, custom protocols
- **Virtual Cable**: VB-Cable, Virtual Audio Cable
- **MIDI Audio**: Synthesizer, sampler, drum machine

## Format Support
- **Sample Rates**: 44.1kHz, 48kHz, 96kHz, 192kHz
- **Bit Depths**: 16-bit, 24-bit, 32-bit float
- **Channels**: Mono, stereo, surround (up to 8 channels)
- **Formats**: PCM, IEEE float, ALAW, MULAW
- **Container Formats**: WAV, AIFF, CAF, RAW