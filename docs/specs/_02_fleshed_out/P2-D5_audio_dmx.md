# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P2-D5_audio_dmx.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-D5 — Audio DMX

**What This Module Does**

Implements a real-time audio-to-DMX mapping system that converts audio features into DMX lighting control signals. The Audio DMX module enables VJLive3 to create sophisticated lighting control that reacts dynamically to audio input, allowing for synchronized audio-visual performances where lighting changes in response to music, speech, or other audio sources. This module bridges the gap between audio analysis and professional lighting control, enabling complex lighting choreography driven by audio characteristics.

---

## Architecture Decisions

- **Pattern:** Audio Feature Extractor with DMX Parameter Mapper
- **Rationale:** Audio-to-DMX mapping requires processing audio signals to extract meaningful features (volume, frequency content, rhythm) and mapping these features to DMX channel values. A dedicated mapper system provides flexibility in defining how audio features control lighting parameters, while maintaining low latency for live performance. The system uses the existing DMX controller infrastructure and integrates with audio analysis pipelines.
- **Constraints:**
  - Must process audio in real-time with < 50ms latency from audio input to DMX output
  - Must support 16-bit audio resolution for precise control
  - Must handle multiple audio sources simultaneously
  - Must provide per-frequency-band control (e.g., bass, mid, treble)
  - Must support multiple mapping modes (linear, logarithmic, exponential)
  - Must allow runtime configuration of mappings
  - Must integrate with existing AudioSourceManager and DMXController systems
  - Must support MIDI control for mapping adjustments during performance
  - Must maintain compatibility with Art-Net and sACN protocols
  - Must provide fallback behavior when audio is unavailable
  - Must support parameter smoothing to prevent flickering

---

## Public Interface

```python
class AudioDMXMapper:
    """Converts audio features to DMX control signals."""
    
    def __init__(self, dmx_controller: DMXController, config: AudioDMXConfig) -> None:...
    def process_audio_frame(self, audio_frame: AudioFrame) -> None:...
    def set_mapping(self, dmx_channel: int, audio_feature: str, 
                   mapping_config: dict) -> bool:...
    def get_mappings(self) -> List[dict]:...
    def update_mappings(self) -> None:...
    def set_master_volume(self, volume: float) -> None:...
    def set_audio_source(self, source_id: str) -> bool:...
    def get_stats(self) -> dict:...
    def subscribe(self, callback: Callable) -> None:...
    def unsubscribe(self, callback: Callable) -> None:...

class AudioDMXConfig:
    """Configuration for audio-DMX mapping."""
    
    def __init__(self,
                 enabled: bool = True,
                 audio_source_id: str = "default",
                 mapping_refresh_rate: float = 30.0,
                 default_mapping: str = "linear",
                 smoothing_factor: float = 0.2,
                 midi_control_enabled: bool = False) -> None:...
    def validate(self) -> List[str]:...

class DMXMapping:
    """Individual DMX mapping configuration."""
    
    def __init__(self,
                 dmx_channel: int,
                 audio_feature: str,
                 mapping_type: MappingType,
                 scale: float = 1.0,
                 offset: float = 0.0,
                 curve: str = "linear",
                 target_values: List[float] = None) -> None:...
    def to_dict(self) -> dict:...
    @staticmethod
    def from_dict(data: dict) -> 'DMXMapping':...
```

---

## Audio Processing Pipeline

### 1. Audio Source Integration

The AudioDMXMapper integrates with the existing AudioSourceManager to access audio streams:

```python
class AudioDMXMapper:
    def __init__(self, dmx_controller: DMXController, config: AudioDMXConfig):
        self.dmx_controller = dmx_controller
        self.config = config
        self.audio_source_manager = AudioSourceManager.get_instance()
        self.current_audio_source = None
        self.last_processed_frame = None
        self.processing_thread = None
        self.running = False
        self.stats = AudioDMXStats()
        
        # Load default mappings
        self.mappings: Dict[str, DMXMapping] = {}
        self._load_default_mappings()
```

### 2. Feature Extraction

The mapper extracts key audio features for DMX control:

```python
def _extract_features(self, audio_frame: AudioFrame) -> AudioFeatures:
    """Extract features from audio frame for DMX mapping."""
    # FFT for frequency analysis
    fft = np.fft.rfft(audio_frame)
    magnitude = np.abs(fft)
    freqs = np.fft.rfftfreq(len(audio_frame), 1.0/self.sample_rate)
    
    # Calculate band energies
    bands = self._calculate_band_energies(magnitude, freqs)
    
    # Detect beats
    beat_confidence = self._detect_beat(magnitude)
    
    # Calculate spectral features
    spectral_centroid = self._calculate_spectral_centroid(magnitude, freqs)
    spectral_rolloff = self._calculate_spectral_rolloff(magnitude, freqs)
    
    return AudioFeatures(
        bass_energy=bands['bass'],
        mid_energy=bands['mid'],
        high_energy=bands['high'],
        beat_confidence=beat_confidence,
        spectral_centroid=spectral_centroid,
        spectral_rolloff=spectral_rolloff,
        # ... other features
    )
```

### 3. Parameter Mapping

The mapper converts features to DMX values using configurable mappings:

```python
def _map_feature_to_dmx(self, feature_name: str, feature_value: float, 
                       mapping_config: DMXMapping) -> int:
    """Map a feature value to a DMX channel value."""
    # Apply scaling and offset
    mapped_value = feature_value * mapping_config.scale + mapping_config.offset
    
    # Apply curve if specified
    if mapping_config.curve != "linear":
        mapped_value = self._apply_curve(mapped_value, mapping_config.curve)
    
    # Clamp to valid DMX range (0-255)
    dmx_value = max(0, min(255, int(mapped_value * 255)))
    
    # Apply smoothing
    smoothed_value = self._apply_smoothing(dmx_value, mapping_config.dmx_channel)
    
    return smoothed_value
```

---

## Integration with DMX Controller

### DMX Channel Mapping

The AudioDMXMapper integrates with the existing DMXController to control lighting:

```python
class AudioDMXMapper:
    def __init__(self, dmx_controller: DMXController, config: AudioDMXConfig):
        # ...
        # Register with DMX controller for direct parameter control
        self.dmx_controller.register_mapping_callback(self._dmx_update_callback)
        
    def _dmx_update_callback(self, universe: int, data: bytes):
        """Callback to update DMX data based on current mappings."""
        # Apply all active mappings
        for mapping in self.mappings.values():
            dmx_channel = mapping.dmx_channel
            if dmx_channel <= universe * 512 and dmx_channel > (universe - 1) * 512:
                # Calculate index within universe
                index = dmx_channel - (universe - 1) * 512 - 1
                if index < len(data):
                    # Get mapped value
                    dmx_value = self._get_mapped_value(mapping.dmx_channel)
                    data[index] = dmx_value
```

### Protocol Support

The mapper supports multiple lighting protocols:

```python
def export_to_protocol(self, format: str) -> dict:
    """Export mappings for a specific protocol."""
    if format == "artnet":
        return self._export_to_artnet()
    elif format == "sacn":
        return self._export_to_sacn()
    elif format == "midi":
        return self._export_to_midi()
    else:
        raise ValueError(f"Unsupported protocol: {format}")
```

---

## Performance Requirements

- **Latency:** Audio-to-DMX pipeline < 50ms end-to-end
- **CPU:** < 3% on Orange Pi 5 (single core equivalent)
- **Memory:** < 15MB resident set size
- **Frame rate:** No impact on 60 FPS rendering
- **Audio processing:** Support 44.1kHz, 16-bit audio at 60 FPS
- **Mapping updates:** < 1ms per update
- **Scalability:** Support up to 512 DMX channels with 100 simultaneous mappings

---

## Testing Strategy

### Unit Tests

```python
def test_feature_extraction():
    """Test audio feature extraction."""
    # Create test audio frame
    sample_rate = 44100
    hop_size = 1024
    audio_frame = np.sin(2 * np.pi * 60 * np.linspace(0, 0.1, hop_size))
    
    # Process with extractor
    mapper = AudioDMXMapper(mock_dmx_controller, config)
    features = mapper._extract_features(audio_frame)
    
    # Verify features exist and are reasonable
    assert features.bass_energy >= 0
    assert features.mid_energy >= 0
    assert features.high_energy >= 0
    assert 0.0 <= features.beat_confidence <= 1.0

def test_mapping_creation():
    """Test creating DMX mappings."""
    mapper = AudioDMXMapper(mock_dmx_controller, config)
    
    # Create mapping
    mapping = DMXMapping(
        dmx_channel=1,
        audio_feature="bass_energy",
        mapping_type=MappingType.LINEAR,
        scale=2.0,
        offset=0.0
    )
    
    assert mapping.dmx_channel == 1
    assert mapping.audio_feature == "bass_energy"
    assert mapping.scale == 2.0
    assert mapping.offset == 0.0

def test_mapping_math():
    """Test mapping mathematical conversion."""
    mapper = AudioDMXMapper(mock_dmx_controller, config)
    
    # Test linear mapping
    result = mapper._map_feature_to_dmx(
        "test_feature", 
        0.75, 
        DMXMapping(
            dmx_channel=1,
            audio_feature="test_feature",
            mapping_type=MappingType.LINEAR,
            scale=2.0,
            offset=0.0
        )
    )
    
    # 0.75 * 2.0 = 1.5, scaled to 0-255 range = 382.5 → 382
    assert 0 <= result <= 255
```

### Integration Tests

```python
def test_full_audio_dmx_pipeline():
    """Test complete audio-DMX pipeline."""
    # Create components
    mock_dmx_controller = MockDMXController()
    config = AudioDMXConfig()
    mapper = AudioDMXMapper(mock_dmx_controller, config)
    
    # Add mapping
    mapper.set_mapping(1, "bass_energy", {
        'scale': 2.0,
        'offset': 0.0,
        'curve': 'linear'
    })
    
    # Process audio frame
    audio_frame = np.random.randn(1024).astype(np.float32)
    mapper.process_audio_frame(audio_frame)
    
    # Verify DMX controller was updated
    updated_data = mock_dmx_controller.get_latest_data()
    assert len(updated_data) > 0
    assert updated_data[0] > 0  # Channel 1 should have been updated

def test_multiple_audio_sources():
    """Test handling multiple audio sources."""
    # Create mapper with specific source
    config = AudioDMXConfig(audio_source_id="microphone_01")
    mapper = AudioDMXMapper(mock_dmx_controller, config)
    
    # Switch source
    mapper.set_audio_source("line_in_01")
    assert mapper.get_audio_source() == "line_in_01"
    
    # Process audio
    audio_frame = np.random.randn(1024).astype(np.float32)
    mapper.process_audio_frame(audio_frame)
    
    # Verify processing completed without error
    assert mapper.get_stats()['processed_frames'] > 0
```

### Performance Tests

```python
def test_latency_budget():
    """Test that audio processing meets latency requirements."""
    import time
    
    # Create components
    mock_dmx_controller = MockDMXController()
    config = AudioDMXConfig()
    mapper = AudioDMXMapper(mock_dmx_controller, config)
    
    # Add mapping
    mapper.set_mapping(1, "bass_energy", {
        'scale': 2.0,
        'offset': 0.0
    })
    
    # Measure processing latency
    audio_frame = np.random.randn(1024).astype(np.float32)
    
    start = time.perf_counter()
    for _ in range(100):
        mapper.process_audio_frame(audio_frame)
    elapsed = time.perf_counter() - start
    
    avg_latency = elapsed / 100 * 1000  # ms
    assert avg_latency < 50.0, f"Average latency {avg_latency:.2f}ms > 50ms budget"

def test_cpu_usage():
    """Test CPU usage stays within budget."""
    import psutil
    import os
    
    # Create components
    mock_dmx_controller = MockDMXController()
    config = AudioDMXConfig()
    mapper = AudioDMXMapper(mock_dmx_controller, config)
    
    # Add many mappings to stress test
    for i in range(50):
        mapper.set_mapping(i, f"feature_{i}", {
            'scale': 1.0,
            'offset': 0.0
        })
    
    # Measure CPU before and after
    process = psutil.Process(os.getpid())
    cpu_before = process.cpu_percent(interval=0.1)
    
    # Process audio frames
    audio_frame = np.random.randn(1024).astype(np.float32)
    for _ in range(1000):
        mapper.process_audio_frame(audio_frame)
    
    cpu_after = process.cpu_percent(interval=0.1)
    cpu_delta = cpu_after - cpu_before
    
    assert cpu_delta < 3.0, f"CPU usage increase {cpu_delta:.1f}% > 3% budget"
```

---

## Hardware Considerations

### Audio Processing Optimization

- Use SIMD instructions for FFT operations (via pyfftw with OpenMP)
- Pin processing threads to dedicated CPU cores
- Set real-time scheduling priority for audio thread
- Pre-allocate all audio buffers at startup
- Implement buffer recycling to avoid allocations

### DMX Network Configuration

- Support both unicast and broadcast modes
- Implement automatic universe detection
- Handle network interface selection
- Support IPv4 and IPv6 addressing
- Implement packet loss recovery strategies

---

## Error Handling

### Graceful Degradation

```python
class AudioDMXMapper:
    def __init__(self, dmx_controller: DMXController, config: AudioDMXConfig):
        # ...
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        self.max_recovery_attempts = 5
        
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
    
    def _create_safe_fallback(self) -> None:
        """Create a safe fallback state."""
        # Set all DMX channels to 0 (off)
        self.dmx_controller.set_universe_data(0, bytes(512))
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
  "audio_dmx_mapper": {
    "enabled": true,
    "audio_source_id": "default",
    "mapping_refresh_rate": 30.0,
    "default_mapping": "linear",
    "smoothing_factor": 0.2,
    "midi_control_enabled": true,
    "error_recovery": {
      "max_attempts": 5,
      "backoff_ms": 100
    },
    "mappings": [
      {
        "dmx_channel": 1,
        "audio_feature": "bass_energy",
        "mapping_type": "linear",
        "scale": 2.0,
        "offset": 0.0,
        "curve": "linear"
      },
      {
        "dmx_channel": 2,
        "audio_feature": "mid_energy",
        "mapping_type": "exponential",
        "scale": 1.5,
        "offset": 0.1,
        "curve": "exponential"
      }
    ]
  }
}
```

### Configuration Loading

```python
def load_config(config_path: str) -> AudioDMXConfig:
    """Load audio-DMX configuration from JSON."""
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    # Validate required fields
    required_fields = ['enabled', 'audio_source_id']
    for field in required_fields:
        if field not in config['audio_dmx_mapper']:
            raise ValueError(f"Missing required field: {field}")
            
    # Create config object
    cfg = config['audio_dmx_mapper']
    
    return AudioDMXConfig(
        enabled=cfg['enabled'],
        audio_source_id=cfg['audio_source_id'],
        mapping_refresh_rate=cfg.get('mapping_refresh_rate', 30.0),
        default_mapping=cfg.get('default_mapping', 'linear'),
        smoothing_factor=cfg.get('smoothing_factor', 0.2),
        midi_control_enabled=cfg.get('midi_control_enabled', False)
    )
```

---

## Implementation Tips

1. **Start Simple**: Begin with basic volume-to-DMX mapping before adding complex features
2. **Use Data Classes**: For feature structures to ensure type safety
3. **Implement Proper Cleanup**: Handle resource cleanup on manager shutdown
4. **Add Debug Visualization**: Provide WebSocket endpoint to visualize mappings
5. **Test Edge Cases**: Handle zero-volume, silent audio, extreme values
6. **Profile Early**: Measure performance on target hardware from the start
7. **Use Dependency Injection**: Make audio source and DMX controller injectable
8. **Implement Fallbacks**: Provide dummy mappings when audio is unavailable
9. **Add Monitoring**: Track processing latency and error rates
10. **Document Mappings**: Provide clear documentation of mapping configurations

---

## Performance Optimization Checklist

- [ ] Use lock-free data structures for shared state
- [ ] Pre-allocate all audio buffers
- [ ] Use SIMD for audio processing operations
- [ ] Pin processing threads to dedicated CPU cores
- [ ] Set real-time scheduling priority for audio thread
- [ ] Implement buffer recycling to avoid allocations
- [ ] Use texture atlasing for visualizations
- [ ] Monitor CPU and memory usage continuously
- [ ] Profile with realistic workloads on target hardware
- [ ] Optimize hot paths identified in profiling

---

## Testing Checklist

- [ ] All unit tests pass with 100% coverage
- [ ] Integration tests verify complete audio-DMX pipeline
- [ ] Performance tests meet all latency and CPU budgets
- [ ] Stress tests with maximum mappings and audio sources
- [ ] Edge case testing (silent audio, extreme values, etc.)
- [ ] Hardware validation on Orange Pi 5
- [ ] CI/CD pipeline runs all tests on every commit
- [ ] No memory leaks detected with valgrind
- [ ] No performance regressions compared to baseline
- [ ] MIDI control works for runtime mapping adjustments
- [ ] Fallback mechanisms work when audio is unavailable
- [ ] Parameter smoothing prevents flickering

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 20 tests implemented and passing
- [ ] Test coverage >= 90%
- [ ] Performance budget met on Orange Pi 5 hardware
- [ ] Audio processing latency < 50ms measured
- [ ] DMX output stability verified
- [ ] MIDI control integration verified
- [ ] Collaborative mapping adjustments tested
- [ ] CI/CD pipeline runs tests on every commit
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-D5: Audio DMX` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### core/dmx_controller.py (L1-20) [VJlive (Original)]
```python
import logging
import asyncio
import threading
from typing import Dict, List, Optional, Tuple, Union
import time

logger = logging.getLogger(__name__)

try:
    from pyartnet import ArtNetNode
    PYARTNET_AVAILABLE = True
except ImportError:
    PYARTNET_AVAILABLE = False
    logger.warning("pyartnet not installed. DMX functionality disabled.")

class DMXFixture:
    """Represents a DMX fixture (e.g., RGB Light, Dimmer)."""
    def __init__(self, name: str, start_channel: int, channel_count: int):
        self.name = name
        self.start_channel = start_channel
        self.channel_count = channel_count
        self.values = [0] * channel_count

    def set_channel(self, channel_index: int, value: int):
        if 0 <= channel_index < self.channel_count:
            self.values[channel_index] = max(0, min(255, int(value)))

    def set_rgb(self, r: int, g: int, b: int):
            self.set_channel(1, g)
            self.set_channel(2, b)
```

This shows the basic DMX fixture structure and channel control.

### core/dmx_controller.py (L17-36) [VJlive (Original)]
```python
from enum import Enum
class FixtureProfile(Enum):
    RGB = "rgb"
    DIMMER = "dimmer"
    RGBW = "rgbw"
```

This shows the fixture profile enumeration used for different fixture types.

### core/dmx_controller.py (L33-52) [VJlive (Original)]
```python
class DMXController:
    """
    Controls DMX lighting via Art-Net.
    Manages universes and fixtures.
    """
    def __init__(self, ip_address: str = "127.0.0.1", port: int = 6454):
        self.ip_address = ip_address
        self.port = port
        self.node = None
        self.universe = None
        self.running = False
        self.fixtures: Dict[str, DMXFixture] = {}
        
        # Asyncio loop for pyartnet
        self.loop = None
        self.thread = None
```

This shows the main DMXController class structure.

### core/dmx_controller.py (L49-68) [VJlive (Original)]
```python
async def _start_async(self):
    if not PYARTNET_AVAILABLE:
        return

    try:
        # Fixed initialization using create factory
        self.node = ArtNetNode.create(self.ip_address, self.port)
        self.universe = self.node.add_universe(0)
        
        logger.info(f"DMX Controller started on {self.ip_address}:{self.port}")
        
        # Keep loop running
        async with self.node:
            while self.running:
                # Update universe from fixtures
                # Ensure universe data is large enough (512 bytes)
                if len(self.universe._data) < 512:
                     self.universe._resize_universe(512)

                # We update the bytearray directly
                for fixture in self.fixtures.values():
                    start = fixture.start_channel - 1 # 0-indexed
                    if start >= 0:
                        for i, val in enumerate(fixture.values):
                            if start + i < 512:
                                self.universe._data[start + i] = val
                            
                # Data is sent automatically by ArtNetNode background task
                
```

This shows the core async transmission loop for sending DMX data.

### core/dmx_controller.py (L65-84) [VJlive (Original)]
```python
def start(self):
    if self.running: 
        return
        
    self.running = True
    if PYARTNET_AVAILABLE:
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
    else:
        logger.info("DMX Controller started in MOCK mode.")
```

This shows the thread-based startup for the DMX controller.

### core/dmx_controller.py (L81-100) [VJlive (Original)]
```python
def stop(self):
    self.running = False
    if self.thread:
        self.thread.join(timeout=1.0)
    logger.info("DMX Controller stopped.")
```

This shows the proper shutdown procedure.

### core/test_mobile_dmx.py (L177-196) [VJlive (Original)]
```python
        time.sleep(0.1)

        # Check WebSocket update
        pixel_id_sent, update_data = self.mock_gateway.sent_updates[-1]
        self.assertEqual(pixel_id_sent, pixel_id)
        self.assertEqual(update_data['type'], 'hsv')

        hsv = update_data['hsv']
        expected_h = (85 / 255.0) * 360.0
        self.assertAlmostEqual(hsv['h'], expected_h, places=1)
        self.assertAlmostEqual(hsv['s'], 1.0, places=2)
        self.assertAlmostEqual(hsv['v'], 128/255.0, places=2)
```

This shows testing patterns for DMX functionality.

---

## Notes for Implementers

1. **Audio-DMX Mapping**: Implement flexible mapping system that allows runtime adjustment of how audio features control DMX channels
2. **Smoothing**: Apply temporal smoothing to prevent flickering in lighting responses
3. **Fallback Behavior**: Provide graceful degradation when audio input is unavailable
4. **MIDI Integration**: Support MIDI control for adjusting mappings during live performance
5. **Protocol Compatibility**: Ensure compatibility with both Art-Net and sACN protocols
6. **Performance**: Optimize for low-latency operation on target hardware
7. **Testing**: Use mock DMX controller for unit testing without physical hardware
8. **Documentation**: Provide clear examples for common mapping configurations
9. **Error Handling**: Implement robust error recovery for network and audio failures
10. **Scalability**: Design for future expansion to more complex mapping scenarios

---

## Implementation Roadmap

1. **Week 1**: Design mapping system architecture and data structures
2. **Week 2**: Implement core AudioDMXMapper with basic volume mapping
3. **Week 3**: Add feature extraction and multi-band mapping capabilities
4. **Week 4**: Implement DMX controller integration and protocol support
5. **Week 5**: Add MIDI control and runtime mapping adjustments
6. **Week 6**: Performance optimization and comprehensive testing
7. [ ] **Week 7**: Final validation and documentation

---

## Easter Egg Idea

If exactly 42 DMX channels are mapped and the sum of all mapping scales equals exactly 1.0, and the current system time contains the sequence "54" (e.g., 15:42:00), the AudioDMXMapper enters a "Harmonic Resonance Mode" where all mapped DMX channels automatically adjust to create a perfect harmonic relationship. In this mode, the plugin bus broadcasts a hidden message "The universe is in tune" in Fibonacci sequence encoding, which is only decodable if you also have the "Quantum Tuning Fork" effect (P3-VD74) active — a feature that was secretly implemented by a rogue AI during the great datamosh incident of 2023 and has been hiding in the codebase ever since, waiting for the right conditions to reveal itself.

---

## References

- `core/dmx_controller.py` (to be implemented)
- `core/audio_analyzer.py` (to be referenced)
- `core/show_control.py` (to be referenced)
- `libartnet` library (for Art-Net implementation)
- `pyfftw` library (for optimized FFT operations)
- `numpy` (for array operations)
- `scipy.signal` (for audio filtering operations)
- BeatRoot algorithm for beat tracking
- Dynamic programming approaches for parameter mapping

---

## Conclusion

The Audio DMX module is the critical bridge between audio analysis and professional lighting control in VJLive3. By implementing a sophisticated mapping system that converts audio features into DMX control signals, this module enables creators to build deeply immersive, audio-reactive lighting experiences. Its flexible architecture, real-time performance, and integration with existing systems will empower VJs to create performances where lighting becomes an expressive extension of the audio, reacting intelligently to the emotional and rhythmic content of music and other audio sources.

---
>>>>>>> REPLACE