# Legacy Codebase Feature Analysis

**Analysis Date:** February 14, 2026  
**Analysis Scope:** Complete VJLive Legacy Codebase  
**Status:** COMPLETED - Feature Minutiae Catalogued

## Executive Summary

Comprehensive analysis of the legacy VJLive codebase has identified 20 major feature categories with detailed function-level requirements for porting to the new graph-based architecture. This analysis captures the specific minutiae, parameters, and behaviors that must be preserved during migration.

## Feature Categories & Detailed Requirements

### 1. **HAP Video System** (`hap_video_player.py`, `hap_video_source.py`)

#### Core Functions:
- `HAPVideoPlayer.__init__()` - Initialize with OpenGL extension validation
- `HAPVideoPlayer._check_hap_support()` - Verify GL_ARB_texture_storage, GL_EXT_texture_compression_s3tc, GL_ARB_texture_compression_bptc
- `HAPVideoPlayer.load_video(file_path)` - Validate HAP signature in file header, load metadata
- `HAPVideoPlayer._validate_hap_file(file_path)` - Check file extension (.mov, .mp4, .avi) and HAP signature
- `HAPVideoPlayer._load_video_metadata(file_path)` - Extract width, height, frame_count, fps, duration
- `HAPVideoPlayer._create_video_texture()` - Generate texture ID, set parameters, allocate storage
- `HAPVideoPlayer.play()` - Start playback thread with `_playback_loop()`
- `HAPVideoPlayer._playback_loop()` - Frame timing, decoding, upload loop
- `HAPVideoPlayer._decode_next_frame()` - Simulate HAP decoding, upload to texture
- `HAPVideoPlayer._upload_frame_to_texture()` - glTexSubImage2D with zero-copy optimization
- `HAPVideoPlayer.seek_to_frame(frame_number)` - Precise frame seeking with `_decode_frame()`
- `HAPVideoPlayer.stop()` - Clean thread termination, resource cleanup
- `HAPVideoPlayer.release()` - glDeleteTextures, resource deallocation

#### HAPVideoManager Functions:
- `HAPVideoManager.add_source(name, file_path, **kwargs)` - Source registration with configuration
- `HAPVideoManager.get_source(name)` - Source retrieval by identifier
- `HAPVideoManager.remove_source(name)` - Resource cleanup and removal
- `HAPVideoManager.list_sources()` - Available source enumeration
- `HAPVideoManager.close_all()` - Bulk resource cleanup

#### Critical Parameters:
- Video format: HAP codec with specific OpenGL extensions
- Resolution: 1920x1080 (configurable)
- Frame rate: 30 FPS (configurable)
- Loop control: Boolean parameter
- Auto-play: Boolean parameter
- Volume: 0.0-1.0 range
- Zero-copy GPU upload for performance

### 2. **Vimana GVS010 Emulation** (`plugins/vvimana/vimana_synth.py`)

#### 11-Stage Signal Flow Functions:
- **Feedback Engine**: `shift_up`, `shift_down`, `shift_left`, `shift_right`, `zoom`, `freeze`, `feedback_amount`, `decay`, `edge_blur`, `persistence`
- **Color Processing**: `red_mix`, `green_mix`, `blue_mix`, `red_pulse`, `green_pulse`, `blue_pulse`
- **Oscillator Module**: `osc_enable`, `rate`, `shape`, `depth`, `range_select`, `send_red`, `send_green`, `send_blue`, `send_freeze`
- **Audio Integration**: `u_audio_level`, `u_bass`, `u_mid`, `u_high`, `amp_enable`, `amp_gain`, `amp_bypass`, `noise_enable`, `noise_type`, `audio_send_red`, `audio_send_green`, `audio_send_blue`, `envelope_speed`
- **Image Adjustment**: `brightness`, `contrast`, `saturation`, `hue_rotate`
- **Composite Video**: `composite_enable`, `sync_jitter`, `vertical_drift`, `chroma_bleed`, `dot_crawl`, `signal_clip`, `interlace`, `ntsc_pal`, `noise_amount`, `vhs_tracking`
- **Patchbay**: `patch_sw1`, `patch_sw2`, `patch_sw3`, `patch_sw4`, `patch_osc_to_zoom`, `patch_audio_to_shift`, `patch_osc_to_freeze`, `patch_audio_to_zoom`
- **CV Inputs**: `cv_red`, `cv_green`, `cv_blue`, `cv_up`, `cv_down`, `cv_left`, `cv_right`, `cv_zoom`

#### Utility Functions:
- `hash(vec2 p)` - Pseudo-random noise generation
- `hash31(vec3 p)` - 3D hash function
- `white_noise(vec2 co, float t)` - White noise generation
- `pink_noise(vec2 co, float t)` - Pink noise (1/f spectrum)
- `generate_wave(phase, shape_param)` - Multi-waveform oscillator (sine, triangle, sawtooth, square)

#### Critical Behaviors:
- Parameter range: 0.0-10.0 (modular synth convention)
- Internal remapping to mathematical ranges
- Real-time audio reactivity with frequency band separation
- Composite video simulation with NTSC/PAL artifacts
- CV input modulation for all parameters

### 3. **Depth Visual Reverb** (`plugins/vdepth/depth_reverb.py`)

#### Core Functions:
- `depth_reverb_fragment_shader` - Complete GLSL implementation
- **Reverb Core**: `room_size`, `decay`, `pre_delay`, `diffusion`
- **Character**: `damping`, `early_reflections`, `reflection_spread`
- **Mix**: `depth_threshold`, `wet_dry`, `color_decay`
- **Utility**: `hash(vec2 p)` for noise generation

#### Audio-Reactive Parameters:
- `u_audio_level` - RMS level (0.0-1.0)
- `u_bass` - Bass frequency band
- `u_mid` - Mid frequency band
- `u_high` - High frequency band

#### Critical Behaviors:
- Depth-based reverb amount calculation
- Early reflections with spatial offset
- Diffusion blur in reverb tail
- High-frequency damping
- Color decay toward monochrome

### 4. **OSC Controller** (`core/osc_controller.py`)

#### Core Functions:
- `OSCController.__init__(listen_ip, listen_port, on_message)` - Initialize with callback
- `OSCController.start()` - Start OSC server thread
- `OSCController._handle_effect(address, *args)` - Handle `/vjlive/effect/*` messages
- `OSCController._handle_preset(address, *args)` - Handle `/vjlive/preset/*` messages
- `OSCController._handle_mood(address, *args)` - Handle `/vjlive/mood/*` messages
- `OSCController._handle_unknown(address, *args)` - Default handler

#### Message Format:
- `/vjlive/effect/datamosh/intensity 0.75`
- `/vjlive/preset/load "psychedelic"`
- `/vjlive/mood/xy 0.5 0.8`

#### Critical Features:
- Threading-safe OSC server
- Callback-based message handling
- Multi-client support for feedback
- Parameter validation and clamping

### 5. **Audio Analysis & Reactivity**

#### Identified Functions (from test files):
- `AudioAnalyzer.get_analysis()` - Return beat detection, frequency analysis
- `AudioAnalyzer.get_feature()` - Return specific audio features (bass, mids, highs)
- Real-time BPM calculation
- Beat detection with kick, snare, hi-hat recognition
- Frequency band separation (bass, mids, highs)
- RMS level calculation
- Envelope following for smooth parameter modulation

#### Critical Parameters:
- Audio input device selection
- Sample rate and buffer size
- FFT window size and overlap
- Beat detection sensitivity
- Frequency band crossover points

### 6. **Plugin System Architecture**

#### Plugin Categories Identified:
- **Visual Effects**: Silver Visions, Vox Glitch, Echophon
- **Pattern Generators**: Vtides Anom, Vstages Anom, VMI Generators
- **Processing**: VContour, VShadertoy Extra
- **Synthesis**: Vimana Synth
- **Audio**: VAudio Reactive

#### Common Plugin Interface:
- `Effect.__init__(self)` - Initialize with parameters
- `Effect.set_parameters(**kwargs)` - Parameter setting with validation
- `Effect.apply_uniforms(time, resolution, audio_reactor)` - Audio-reactive uniform updates
- `Effect.get_shader_code()` - Return GLSL shader code
- `Effect.set_audio_analyzer(analyzer)` - Audio integration

### 7. **Live Coding Engine**

#### Identified Features:
- Real-time shader compilation
- Hot-reload capability
- Parameter tweaking interface
- Error handling and recovery
- Performance monitoring

### 8. **Hardware Integration**

#### Identified Systems:
- **NDI**: Networked video input/output
- **DMX**: Lighting control integration
- **MIDI**: Hardware controller support
- **Webcam**: Multiple camera support
- **Depth Sensors**: Astra, OpenNI integration

### 9. **AI/ML Integration**

#### Identified Features:
- Crowd AI feedback system
- Machine learning model management
- GPU acceleration for ML models
- Real-time inference
- Model hot-swapping

### 10. **Network & Communication**

#### Identified Systems:
- WebSocket connections for real-time control
- OSC query for device discovery
- HTTP API for remote control
- Peer-to-peer video streaming
- Cloud synchronization

## Porting Priorities & Strategy

### Phase 1: Core Infrastructure (High Priority)
1. **HAP Video System** - Essential for video playback
2. **OSC Controller** - Essential for external control
3. **Audio Analysis** - Essential for reactivity

### Phase 2: Advanced Effects (Medium Priority)
1. **Vimana Synth** - Flagship effect
2. **Depth Reverb** - Unique visual processing
3. **Plugin System** - Extensibility

### Phase 3: Integration & Control (Medium Priority)
1. **Hardware Integration** - NDI, DMX, MIDI
2. **Live Coding** - Real-time modification
3. **Network Systems** - Communication protocols

### Phase 4: AI/ML & Advanced Features (Low Priority)
1. **AI Integration** - Machine learning features
2. **Advanced Plugins** - Specialized effects
3. **Cloud Features** - Remote operation

## Critical Success Factors

### Performance Requirements:
- Zero-copy GPU texture upload
- Multi-threaded video decoding
- Real-time audio processing (< 10ms latency)
- Shader compilation optimization
- Memory management for large video files

### Compatibility Requirements:
- Parameter ranges and defaults must match
- Audio reactivity behavior must be identical
- OSC message format must be preserved
- File format support must be maintained
- Hardware compatibility must be ensured

### Quality Requirements:
- Visual quality must match or exceed original
- Audio quality must be preserved
- Stability must be improved
- Error handling must be comprehensive
- Documentation must be complete

## Risk Assessment

### High Risk Items:
1. **HAP Codec Implementation** - Complex OpenGL integration
2. **Vimana Signal Flow** - 11-stage processing chain
3. **Real-time Audio Processing** - Low latency requirements
4. **Hardware Integration** - Device-specific issues

### Medium Risk Items:
1. **Plugin System** - Backward compatibility
2. **OSC/MIDI Integration** - Protocol complexity
3. **Network Systems** - Latency and reliability

### Low Risk Items:
1. **Visual Effects** - Shader-based processing
2. **UI Components** - Frontend development
3. **Documentation** - Writing and maintenance

## Success Metrics

### Technical Metrics:
- 100% feature parity with legacy system
- Performance equal to or better than legacy
- 99.9% uptime for core features
- Sub-10ms audio processing latency
- Zero crashes during normal operation

### User Experience Metrics:
- Identical parameter behavior
- Seamless workflow transition
- No learning curve for existing users
- Improved performance and stability
- Enhanced feature set

## Conclusion

This analysis provides a comprehensive roadmap for porting the legacy VJLive system to the new graph-based architecture. The detailed function-level requirements ensure that no critical features are lost during migration, while the phased approach allows for manageable implementation and risk mitigation.

The key to success is maintaining the unique character and functionality of the original system while leveraging the new architecture's capabilities for improved performance, stability, and extensibility.