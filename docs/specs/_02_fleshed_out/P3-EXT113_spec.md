# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT113_spec.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT113 — Audio Spectrum Trails

**What This Module Does**

Implements an audio-reactive visual effect that creates persistent spectrum trails with decay, frequency-based coloring, and energy thresholding. The Audio Spectrum Trails module transforms audio frequency data into flowing, trail-like visual patterns that persist and gradually fade over time. This effect combines real-time audio analysis with frame buffer persistence to create mesmerizing visual representations of sound that are perfect for live VJ performances and audio-visual installations.

---

## Architecture Decisions

- **Pattern:** Audio-Reactive Trail Effect with Frame Buffer Persistence
- **Rationale:** Spectrum trails provide a compelling visual representation of audio that is both immediately responsive and temporally rich. The trail effect creates a sense of history and motion, while frequency-based coloring maps different pitch ranges to distinct colors. This architecture enables real-time performance with low latency while maintaining visual complexity.
- **Constraints:**
  - Must maintain 60 FPS at 1080p resolution on Orange Pi 5
  - Must support real-time audio analysis with < 5ms latency
  - Must provide multiple color mapping modes (rainbow, heat, blue-red)
  - Must implement configurable trail decay and length parameters
  - Must support energy threshold to filter out quiet frequencies
  - Must integrate with existing audio analyzer module
  - Must provide GPU-accelerated rendering via OpenGL shaders
  - Must support both 1D spectrum texture and 2D trail buffer
  - Must enable parameter adjustment during runtime
  - Must provide fallback CPU rendering for systems without GPU

---

## Public Interface

```python
class AudioSpectrumTrails:
    """Audio-reactive spectrum trails effect."""
    
    def __init__(self, config: SpectrumTrailsConfig):
        self.config = config
        self.audio_analyzer = None
        self.shader = None
        self.spectrum_texture = None
        self.trail_buffer = None
        self.trail_framebuffer = None
        self.time = 0.0
        self.parameters = self._initialize_parameters()
        self._initialize_shader()
        self._initialize_buffers()
        
    def process(self, video_frame: np.ndarray, audio_data: np.ndarray = None) -> np.ndarray:
        """Process video frame with audio spectrum trails."""
        # Update time
        self.time += 0.016
        
        # Analyze audio if available
        spectrum_data = self._analyze_audio(audio_data)
        
        # Create spectrum texture
        spectrum_tex = self._create_spectrum_texture(spectrum_data)
        
        # Apply shader with trail effect
        output = self._apply_shader(video_frame, spectrum_tex, spectrum_data)
        
        # Update trail buffer (persistence)
        self._update_trail_buffer(output)
        
        # Cleanup
        glDeleteTextures(1, [spectrum_tex])
        
        return output
        
    def set_audio_analyzer(self, analyzer: AudioAnalyzer):
        """Set audio analyzer for spectrum extraction."""
        self.audio_analyzer = analyzer
        
    def set_parameter(self, param_name: str, value: float):
        """Set effect parameter."""
        if param_name in self.parameters:
            self.parameters[param_name]['value'] = value
            
    def get_parameter(self, param_name: str) -> float:
        """Get current parameter value."""
        return self.parameters.get(param_name, {}).get('value', 0.0)
        
    def set_color_mapping(self, mapping: int):
        """Set color mapping mode (0=rainbow, 1=heat, 2=blue-red)."""
        if mapping in [0, 1, 2]:
            self.parameters['color_mapping']['value'] = mapping
            
    def set_trail_decay(self, decay: float):
        """Set trail decay rate (0.8-0.999)."""
        self.parameters['trail_decay']['value'] = max(0.8, min(0.999, decay))
        
    def set_energy_threshold(self, threshold: float):
        """Set energy threshold (0.0-1.0)."""
        self.parameters['energy_threshold']['value'] = max(0.0, min(1.0, threshold))
```

---

## Core Components

### 1. SpectrumTrailsConfig

Configuration dataclass for spectrum trails parameters.

```python
@dataclass
class SpectrumTrailsConfig:
    """Configuration for audio spectrum trails."""
    trail_decay: float = 0.95
    color_mapping: int = 0  # 0=rainbow, 1=heat, 2=blue-red
    energy_threshold: float = 0.1
    trail_length: float = 0.8
    mix_amount: float = 1.0
    spectrum_size: int = 256
    enable_gpu: bool = True
```

### 2. Shader Implementation

GLSL shader for spectrum trail rendering.

```glsl
#version 330 core

uniform vec2 resolution;
uniform float time;
uniform float mix_amount;
uniform sampler2D tex0;

// Audio parameters
uniform sampler2D spectrum_tex;
uniform int spectrum_size;
uniform float trail_decay;
uniform int color_mapping; // 0=rainbow, 1=heat, 2=blue-red
uniform float energy_threshold;
uniform float trail_length;

// Previous frame for trails
uniform sampler2D texPrev;

out vec4 fragColor;

vec3 get_color(float freq_ratio, int mapping) {
    if (mapping == 0) { // Rainbow
        return vec3(
            0.5 + 0.5 * sin(freq_ratio * 6.28 + 0.0),
            0.5 + 0.5 * sin(freq_ratio * 6.28 + 2.1),
            0.5 + 0.5 * sin(freq_ratio * 6.28 + 4.2)
        );
    } else if (mapping == 1) { // Heat
        float t = freq_ratio;
        return vec3(
            t < 0.5 ? t * 2.0 : 1.0,
            t < 0.5 ? 0.0 : (t - 0.5) * 2.0,
            t > 0.5 ? (t - 0.5) * 2.0 : 0.0
        );
    } else { // Blue-red
        return mix(vec3(0.0, 0.0, 1.0), vec3(1.0, 0.0, 0.0), freq_ratio);
    }
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;

    // Get current spectrum value at this Y position
    float spectrum_value = 0.0;
    if (spectrum_size > 0) {
        // Map UV.x to spectrum index
        float spec_index = uv.x * float(spectrum_size - 1);
        int texel_x = int(floor(spec_index));
        if (texel_x >= 0 && texel_x < spectrum_size) {
            // Sample 1D spectrum texture
            spectrum_value = texture(spectrum_tex, vec2((float(texel_x) + 0.5) / float(spectrum_size), 0.5)).r;
        }
    }

    // Apply energy threshold
    if (spectrum_value < energy_threshold) {
        spectrum_value = 0.0;
    }

    // Get color based on frequency and spectrum value
    vec3 spectrum_color = get_color(uv.x, color_mapping) * spectrum_value;

    // Get previous frame for trails
    vec3 prev_color = texture(texPrev, uv).rgb;

    // Apply trail decay
    vec3 trail_color = prev_color * trail_decay;

    // Mix new spectrum with trail
    vec3 final_color = mix(trail_color, spectrum_color, mix_amount);

    // Apply trail length modulation
    float trail_mod = 1.0 - trail_length * 0.5;
    final_color *= trail_mod;

    fragColor = vec4(final_color, 1.0);
}
```

### 3. AudioAnalyzer Integration

```python
class AudioAnalyzer:
    """Audio analysis for spectrum trails."""
    
    def __init__(self, sample_rate: int = 44100, fft_size: int = 2048):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.window = np.hanning(fft_size)
        
    def analyze(self, audio_data: np.ndarray) -> np.ndarray:
        """Analyze audio and return spectrum data."""
        # Apply window
        windowed = audio_data * self.window
        
        # Compute FFT
        fft_result = np.fft.rfft(windowed)
        fft_magnitude = np.abs(fft_result)
        
        # Normalize
        fft_magnitude = fft_magnitude / (self.fft_size / 2.0)
        
        # Apply logarithmic scaling
        spectrum = 20 * np.log10(fft_magnitude + 1e-10)
        spectrum = np.clip(spectrum, -60, 0)  # dB range
        spectrum = (spectrum + 60) / 60.0  # Normalize to 0-1
        
        return spectrum
```

### 4. Buffer Management

```python
class BufferManager:
    """Manages framebuffer and texture buffers for trail effect."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.trail_fbo = None
        self.trail_texture = None
        self._create_framebuffer()
        
    def _create_framebuffer(self):
        """Create framebuffer for trail persistence."""
        # Create texture for trail buffer
        self.trail_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.trail_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.width, self.height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        
        # Create framebuffer
        self.trail_fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.trail_fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.trail_texture, 0)
        
        # Check framebuffer status
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Framebuffer creation failed")
            
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
    def bind_trail_buffer(self):
        """Bind trail framebuffer for writing."""
        glBindFramebuffer(GL_FRAMEBUFFER, self.trail_fbo)
        glViewport(0, 0, self.width, self.height)
        
    def unbind_trail_buffer(self):
        """Unbind trail framebuffer."""
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
    def get_trail_texture(self) -> int:
        """Get trail texture ID for shader."""
        return self.trail_texture
        
    def clear(self):
        """Clear trail buffer."""
        glBindFramebuffer(GL_FRAMEBUFFER, self.trail_fbo)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
```

---

## Integration with Existing Systems

### Effect Chain Integration

```python
class EffectChain:
    """Manages effect chain with spectrum trails."""
    
    def __init__(self):
        self.effects = []
        self.spectrum_trails = None
        
    def add_effect(self, effect: BaseEffect):
        """Add effect to chain."""
        self.effects.append(effect)
        
    def set_spectrum_trails(self, trails: AudioSpectrumTrails):
        """Set spectrum trails effect."""
        self.spectrum_trails = trails
        
    def process_frame(self, frame: np.ndarray, audio_data: np.ndarray = None) -> np.ndarray:
        """Process frame through effect chain."""
        current = frame
        
        # Apply all effects before spectrum trails
        for effect in self.effects:
            if effect != self.spectrum_trails:
                current = effect.process(current)
                
        # Apply spectrum trails
        if self.spectrum_trails:
            current = self.spectrum_trails.process(current, audio_data)
            
        return current
```

### Audio Source Integration

```python
class AudioSource:
    """Audio source for spectrum trails."""
    
    def __init__(self, audio_analyzer: AudioAnalyzer):
        self.audio_analyzer = audio_analyzer
        self.buffer_size = 2048
        self.audio_buffer = np.zeros(self.buffer_size)
        self.sample_rate = 44100
        
    def update_audio(self, audio_chunk: np.ndarray):
        """Update audio buffer with new chunk."""
        # Shift buffer and add new data
        self.audio_buffer = np.roll(self.audio_buffer, -len(audio_chunk))
        self.audio_buffer[-len(audio_chunk):] = audio_chunk
        
    def get_spectrum(self) -> np.ndarray:
        """Get current frequency spectrum."""
        if self.audio_analyzer:
            return self.audio_analyzer.analyze(self.audio_buffer)
        return np.zeros(256)
```

---

## Performance Requirements

- **Frame Rate:** 60 FPS minimum at 1080p
- **Audio Latency:** < 5ms from audio input to visual update
- **GPU Memory:** < 50MB for textures and framebuffers
- **CPU Usage:** < 10% on Orange Pi 5 (with GPU)
- **Shader Compilation:** < 100ms on first run
- **Parameter Updates:** < 1ms for parameter changes
- **Spectrum Analysis:** < 2ms for FFT computation
- **Texture Upload:** < 1ms for spectrum texture creation
- **Framebuffer Operations:** < 2ms for trail buffer updates
- **Startup Time:** < 500ms for full initialization

---

## Testing Strategy

### Unit Tests

```python
def test_spectrum_analysis():
    """Test audio spectrum analysis."""
    analyzer = AudioAnalyzer()
    
    # Create test audio (sine wave at 440Hz)
    t = np.linspace(0, 1, 2048)
    audio = np.sin(2 * np.pi * 440 * t)
    
    spectrum = analyzer.analyze(audio)
    
    assert len(spectrum) == 1025  # rfft size
    assert np.all(spectrum >= 0) and np.all(spectrum <= 1)
    
def test_color_mapping():
    """Test color mapping functions."""
    # Test rainbow mapping
    color_rainbow = get_color(0.5, 0)
    assert len(color_rainbow) == 3
    assert np.all(color_rainbow >= 0) and np.all(color_rainbow <= 1)
    
    # Test heat mapping
    color_heat = get_color(0.25, 1)
    assert color_heat[0] > 0  # Red component
    assert color_heat[1] == 0  # No green
    assert color_heat[2] == 0  # No blue
    
    # Test blue-red mapping
    color_bwr = get_color(0.75, 2)
    assert color_bwr[2] > color_bwr[0]  # More blue than red
    
def test_buffer_creation():
    """Test framebuffer buffer creation."""
    buffer_mgr = BufferManager(1920, 1080)
    
    assert buffer_mgr.trail_fbo is not None
    assert buffer_mgr.trail_texture is not None
    
    # Test clear
    buffer_mgr.clear()
    
    # Test bind/unbind
    buffer_mgr.bind_trail_buffer()
    buffer_mgr.unbind_trail_buffer()
```

### Integration Tests

```python
def test_spectrum_trails_processing():
    """Test complete spectrum trails processing."""
    config = SpectrumTrailsConfig()
    trails = AudioSpectrumTrails(config)
    
    # Create test frames
    video = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    audio = np.random.randn(2048)
    
    # Process
    result = trails.process(video, audio)
    
    assert result.shape == video.shape
    assert result.dtype == np.uint8
    
def test_parameter_adjustment():
    """Test parameter changes affect output."""
    config = SpectrumTrailsConfig()
    trails = AudioSpectrumTrails(config)
    
    video = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    audio = np.random.randn(2048)
    
    # Process with default parameters
    result1 = trails.process(video, audio)
    
    # Change decay
    trails.set_trail_decay(0.99)
    result2 = trails.process(video, audio)
    
    # Results should differ
    assert not np.array_equal(result1, result2)
    
def test_color_mapping_modes():
    """Test different color mapping modes."""
    config = SpectrumTrailsConfig()
    trails = AudioSpectrumTrails(config)
    
    video = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    audio = np.random.randn(2048)
    
    # Test each color mode
    for mode in [0, 1, 2]:
        trails.set_color_mapping(mode)
        result = trails.process(video, audio)
        assert result.shape == video.shape
```

### Performance Tests

```python
def test_rendering_performance():
    """Test rendering performance meets requirements."""
    config = SpectrumTrailsConfig()
    trails = AudioSpectrumTrails(config)
    
    video = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    audio = np.random.randn(2048)
    
    # Measure average frame time
    import time
    iterations = 120
    start = time.perf_counter()
    
    for i in range(iterations):
        result = trails.process(video, audio)
        
    elapsed = time.perf_counter() - start
    avg_frame_time = elapsed / iterations
    
    assert avg_frame_time < 0.016, f"Average frame time {avg_frame_time*1000:.1f}ms > 16ms"
    
def test_memory_usage():
    """Test memory usage stays within budget."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # Create multiple spectrum trails instances
    trails_list = []
    for i in range(5):
        trails = AudioSpectrumTrails(SpectrumTrailsConfig())
        trails_list.append(trails)
        
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    mem_delta = mem_after - mem_before
    
    assert mem_delta < 50, f"Memory increase {mem_delta:.1f}MB > 50MB budget"
```

---

## Implementation Roadmap

1. **Week 1:** Implement core AudioSpectrumTrails class with basic shader
2. **Week 2:** Develop audio analyzer integration and spectrum extraction
3. **Week 3:** Create buffer management system for trail persistence
4. **Week 4:** Implement color mapping modes and parameter controls
5. **Week 5:** Optimize GPU performance and add CPU fallback
6. **Week 6:** Comprehensive testing and performance tuning

---
## References

- `core/core_plugins/audio_spectrum_trails.json` (to be referenced)
- `core/core_plugins/audio_spectrum_trails.py` (to be referenced)
- `core/audio/audio_analyzer.py` (to be referenced)
- `OpenGL` (for GPU-accelerated rendering)
- `numpy` (for audio processing)
- `scipy` (for FFT operations)

---

## Conclusion

The Audio Spectrum Trails module transforms VJLive3 into a powerful tool for creating stunning audio-reactive visual effects with temporal persistence. By combining real-time frequency analysis with GPU-accelerated trail rendering, this effect enables performers to create mesmerizing visual representations of sound that evolve over time. Its flexible parameter system, multiple color mapping modes, and seamless integration with existing audio infrastructure make it an essential addition to any VJ's toolkit, providing both immediate visual impact and deep creative control.

---
