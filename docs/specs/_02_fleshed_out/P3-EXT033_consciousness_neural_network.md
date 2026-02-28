# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT033_consciousness_neural_network.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT033 — Consciousness Neural Network

**What This Module Does**

Implements a sophisticated neural network effect that processes video and depth data through consciousness-inspired transformations. The Consciousness Neural Network applies deep learning-based image processing to create mind-bending visual effects that simulate altered states of consciousness. This module uses neural network architectures to analyze and transform visual patterns, creating psychedelic, dreamlike, and consciousness-expanding visual experiences that respond to audio input and user parameters.

---

## Architecture Decisions

- **Pattern:** Neural Network-Based Image Transformation with Consciousness Mapping
- **Rationale:** Neural networks provide powerful capabilities for complex image transformations that traditional algorithms cannot achieve. By training on consciousness-inspired patterns and using audio reactivity, this effect creates unique visual experiences that feel organic and alive. The modular architecture allows for different network architectures and consciousness mapping strategies.
- **Constraints:**
  - Must maintain 60 FPS at 1080p resolution on Orange Pi 5
  - Must support real-time neural network inference (< 10ms per frame)
  - Must provide 5+ preset consciousness states
  - Must integrate with audio reactivity system
  - Must support both video and depth input streams
  - Must enable parameter adjustment during runtime
  - Must provide fallback mode for hardware without GPU acceleration
  - Must support model loading/unloading for memory management
  - Must implement consciousness level scaling (0-10)
  - Must provide visual feedback of network state and processing metrics

---

## Public Interface

```python
class ConsciousnessNeuralNetwork:
    """Neural network effect for consciousness transformation."""
    
    def __init__(self, config: NeuralNetworkConfig):
        self.config = config
        self.model = None
        self.model_type = config.model_type
        self.consciousness_level = 5.0  # 0-10 scale
        self.preset_manager = PresetManager()
        self.audio_reactor = AudioReactor()
        self.parameters = self._initialize_parameters()
        self.time = 0.0
        self.frame_count = 0
        self.processing_stats = ProcessingStats()
        self._load_model(config.model_path)
        
    def process(self, video_frame: np.ndarray, depth_frame: np.ndarray = None, audio_data: np.ndarray = None) -> Dict:
        """Process frames through consciousness neural network."""
        # Update time and frame count
        self.time += 0.016
        self.frame_count += 1
        
        # Process audio if available
        if audio_data is not None and self.audio_reactor.enabled:
            self.audio_reactor.process(audio_data)
            self._apply_audio_to_parameters()
            
        # Apply preset if changed
        preset_index = int(self.parameters['preset']['value'])
        if preset_index > 0:
            self.preset_manager.apply_preset(preset_index, self.parameters)
            
        # Preprocess frames
        video_input = self._preprocess_video(video_frame)
        depth_input = self._preprocess_depth(depth_frame) if depth_frame is not None else None
        
        # Run neural network inference
        start_time = time.perf_counter()
        output = self._inference(video_input, depth_input)
        inference_time = time.perf_counter() - start_time
        
        # Postprocess output
        processed_frame = self._postprocess(output, video_frame.shape)
        
        # Update processing stats
        self.processing_stats.update(inference_time)
        
        # Return processed frame with metadata
        return {
            'video': processed_frame,
            'depth': depth_frame,
            'effect_info': {
                'type': 'consciousness_neural_network',
                'time': self.time,
                'consciousness_level': self.consciousness_level,
                'audio_data': self.audio_reactor.get_features() if self.audio_reactor.enabled else None,
                'parameters': self.parameters,
                'processing_time_ms': inference_time * 1000,
                'fps': self.processing_stats.fps,
                'model_type': self.model_type
            }
        }
        
    def set_consciousness_level(self, level: float):
        """Set consciousness level (0-10)."""
        self.consciousness_level = max(0.0, min(10.0, level))
        self.parameters['consciousness_level']['value'] = self.consciousness_level
        
    def set_preset(self, preset_index: int):
        """Set preset configuration."""
        if preset_index in self.preset_manager.presets:
            self.parameters['preset']['value'] = preset_index
            
    def set_model(self, model_path: str, model_type: str = 'default'):
        """Load new neural network model."""
        self._load_model(model_path)
        self.model_type = model_type
        
    def enable_audio_reactivity(self, enabled: bool):
        """Enable/disable audio reactivity."""
        self.audio_reactor.enabled = enabled
        
    def get_processing_stats(self) -> Dict:
        """Get processing performance statistics."""
        return self.processing_stats.get_report()
        
    def get_available_presets(self) -> List[int]:
        """Get list of available preset indices."""
        return list(self.preset_manager.presets.keys())
```

---

## Core Components

### 1. PresetManager

Manages consciousness presets for the neural network.

```python
class PresetManager:
    """Manages consciousness presets."""
    
    def __init__(self):
        self.presets = {
            1: {  # Awakening
                'consciousness_level': 3.0,
                'transformation_strength': 0.3,
                'color_shift': 0.1,
                'pattern_complexity': 0.2,
                'temporal_smoothing': 0.8,
                'neural_noise': 0.05
            },
            2: {  # Lucid Dream
                'consciousness_level': 6.0,
                'transformation_strength': 0.6,
                'color_shift': 0.3,
                'pattern_complexity': 0.5,
                'temporal_smoothing': 0.6,
                'neural_noise': 0.1
            },
            3: {  # Cosmic Consciousness
                'consciousness_level': 9.0,
                'transformation_strength': 0.9,
                'color_shift': 0.6,
                'pattern_complexity': 0.8,
                'temporal_smoothing': 0.4,
                'neural_noise': 0.2
            },
            4: {  # Neural Reset
                'consciousness_level': 5.0,
                'transformation_strength': 0.5,
                'color_shift': 0.0,
                'pattern_complexity': 0.5,
                'temporal_smoothing': 0.5,
                'neural_noise': 0.0
            },
            5: {  # Chaos Mode
                'consciousness_level': 10.0,
                'transformation_strength': 1.0,
                'color_shift': 1.0,
                'pattern_complexity': 1.0,
                'temporal_smoothing': 0.0,
                'neural_noise': 0.5
            }
        }
        
    def apply_preset(self, preset_index: int, parameters: Dict):
        """Apply preset to parameters."""
        if preset_index not in self.presets:
            return False
            
        preset = self.presets[preset_index]
        for param, value in preset.items():
            if param in parameters:
                parameters[param]['value'] = value
                
        return True
        
    def add_custom_preset(self, preset_id: int, preset_data: Dict):
        """Add custom preset."""
        if preset_id in self.presets:
            return False
            
        self.presets[preset_id] = preset_data
        return True
```

### 2. AudioReactor

Maps audio features to neural network parameters.

```python
class AudioReactor:
    """Audio reactivity for consciousness neural network."""
    
    def __init__(self):
        self.enabled = True
        self.audio_analyzer = None
        self.smoothing = 0.7
        self.current_features = {
            'bass': 0.0,
            'mid': 0.0,
            'treble': 0.0,
            'volume': 0.0,
            'beat': 0.0
        }
        self.parameter_mapping = {
            'bass': 'transformation_strength',
            'mid': 'color_shift',
            'treble': 'pattern_complexity',
            'volume': 'consciousness_level',
            'beat': 'neural_noise'
        }
        
    def set_audio_analyzer(self, analyzer: AudioAnalyzer):
        """Connect audio analyzer."""
        self.audio_analyzer = analyzer
        
    def process(self, audio_data: np.ndarray):
        """Process audio and update features."""
        if not self.audio_analyzer or not self.enabled:
            return
            
        features = self.audio_analyzer.analyze(audio_data)
        
        # Apply smoothing
        for key in self.current_features:
            if key in features:
                new_val = features[key]
                smoothed = self.current_features[key] * self.smoothing + new_val * (1 - self.smoothing)
                self.current_features[key] = smoothed
                
    def get_features(self) -> Dict[str, float]:
        """Get current audio features."""
        return self.current_features.copy()
        
    def map_to_parameters(self, parameters: Dict) -> Dict[str, float]:
        """Map audio features to neural network parameters."""
        mapped = {}
        for audio_feature, param_name in self.parameter_mapping.items():
            if audio_feature in self.current_features:
                # Scale audio feature to parameter range
                audio_val = self.current_features[audio_feature]
                if param_name == 'consciousness_level':
                    mapped[param_name] = audio_val * 10.0
                elif param_name == 'transformation_strength':
                    mapped[param_name] = audio_val * 1.0
                elif param_name == 'color_shift':
                    mapped[param_name] = audio_val * 1.0
                elif param_name == 'pattern_complexity':
                    mapped[param_name] = audio_val * 1.0
                elif param_name == 'neural_noise':
                    mapped[param_name] = audio_val * 0.5
                    
        return mapped
```

### 3. ProcessingStats

Tracks performance metrics.

```python
class ProcessingStats:
    """Track processing performance statistics."""
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.inference_times = []
        self.frame_times = []
        self.start_time = time.time()
        self.frame_count = 0
        
    def update(self, inference_time: float):
        """Update stats with new frame processing time."""
        current_time = time.perf_counter()
        
        if self.frame_times:
            frame_time = current_time - self.frame_times[-1]
            self.frame_times.append(current_time)
            
            # Keep window
            if len(self.frame_times) > self.window_size:
                self.frame_times.pop(0)
        else:
            frame_time = 0.0
            
        self.inference_times.append(inference_time)
        self.frame_count += 1
        
        # Keep window
        if len(self.inference_times) > self.window_size:
            self.inference_times.pop(0)
            
    def get_report(self) -> Dict:
        """Get statistics report."""
        elapsed = time.time() - self.start_time
        
        avg_inference = np.mean(self.inference_times) if self.inference_times else 0.0
        avg_frame = np.mean(np.diff(self.frame_times)) if len(self.frame_times) > 1 else 0.0
        
        return {
            'total_frames': self.frame_count,
            'fps': self.frame_count / elapsed if elapsed > 0 else 0.0,
            'avg_inference_time_ms': avg_inference * 1000,
            'avg_frame_time_ms': avg_frame * 1000,
            'inference_fps': 1.0 / avg_inference if avg_inference > 0 else 0.0,
            'headroom_ms': (0.016 - avg_frame) * 1000 if avg_frame > 0 else 16.0
        }
```

### 4. NeuralNetworkModel

Wrapper for neural network inference.

```python
class NeuralNetworkModel:
    """Neural network model wrapper."""
    
    def __init__(self, model_path: str, model_type: str = 'default'):
        self.model_path = model_path
        self.model_type = model_type
        self.model = None
        self.input_shape = (224, 224, 3)  # Default
        self.output_shape = (224, 224, 3)
        self._load_model()
        
    def _load_model(self):
        """Load neural network model."""
        try:
            if self.model_type == 'tensorflow':
                import tensorflow as tf
                self.model = tf.keras.models.load_model(self.model_path)
            elif self.model_type == 'pytorch':
                import torch
                self.model = torch.load(self.model_path)
                self.model.eval()
            elif self.model_type == 'onnx':
                import onnxruntime as ort
                self.model = ort.InferenceSession(self.model_path)
            else:
                # Custom implementation
                self.model = self._load_custom_model()
                
            logger.info(f"Loaded model: {self.model_type} from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            
    def _load_custom_model(self) -> Any:
        """Load custom model implementation."""
        # This would load a custom consciousness model
        # For now, return a placeholder
        return None
        
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for model input."""
        # Resize to model input shape
        resized = cv2.resize(image, (self.input_shape[1], self.input_shape[0]))
        
        # Normalize to 0-1
        normalized = resized.astype(np.float32) / 255.0
        
        # Add batch dimension
        batched = np.expand_dims(normalized, axis=0)
        
        return batched
        
    def inference(self, input_data: np.ndarray) -> np.ndarray:
        """Run neural network inference."""
        if self.model is None:
            return input_data[0]  # Return input if no model
            
        try:
            if self.model_type == 'tensorflow':
                output = self.model.predict(input_data)
            elif self.model_type == 'pytorch':
                import torch
                with torch.no_grad():
                    input_tensor = torch.from_numpy(input_data).permute(0, 3, 1, 2)
                    output = self.model(input_tensor).numpy()
            elif self.model_type == 'onnx':
                input_name = self.model.get_inputs()[0].name
                output = self.model.run(None, {input_name: input_data})[0]
            else:
                output = self._custom_inference(input_data)
                
            return output
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            return input_data[0]
            
    def postprocess(self, output: np.ndarray, original_shape: Tuple[int, int, int]) -> np.ndarray:
        """Postprocess model output."""
        # Remove batch dimension
        output = output[0]
        
        # Resize to original shape
        resized = cv2.resize(output, (original_shape[1], original_shape[0]))
        
        # Convert to 0-255 range
        output_uint8 = (resized * 255).astype(np.uint8)
        
        return output_uint8
```

---

## Integration with Existing Systems

### Audio Reactivity Integration

```python
class ConsciousnessAudioIntegration:
    """Integrates audio reactivity with consciousness neural network."""
    
    def __init__(self, neural_network: ConsciousnessNeuralNetwork):
        self.neural_network = neural_network
        self.audio_analyzer = AudioAnalyzer()
        self.parameter_smoothing = 0.7
        
    def update(self, audio_data: np.ndarray):
        """Update neural network parameters based on audio."""
        if not self.neural_network.audio_reactor.enabled:
            return
            
        # Process audio
        self.neural_network.audio_reactor.process(audio_data)
        
        # Get mapped parameters
        mapped_params = self.neural_network.audio_reactor.map_to_parameters(
            self.neural_network.parameters
        )
        
        # Apply smoothed parameter updates
        for param, value in mapped_params.items():
            if param in self.neural_network.parameters:
                current = self.neural_network.parameters[param]['value']
                smoothed = current * self.parameter_smoothing + value * (1 - self.parameter_smoothing)
                self.neural_network.parameters[param]['value'] = smoothed
```

### Effect Chain Integration

```python
class EffectChain:
    """Manages effect chain with consciousness neural network."""
    
    def __init__(self):
        self.effects = []
        self.consciousness_net = None
        
    def add_effect(self, effect: BaseEffect):
        """Add effect to chain."""
        self.effects.append(effect)
        
    def set_consciousness_network(self, network: ConsciousnessNeuralNetwork):
        """Set consciousness neural network effect."""
        self.consciousness_net = network
        
    def process_frame(self, frame: np.ndarray, depth: np.ndarray = None, audio: np.ndarray = None) -> np.ndarray:
        """Process frame through effect chain."""
        current = frame
        
        # Apply all effects before consciousness network
        for effect in self.effects:
            if effect != self.consciousness_net:
                current = effect.process(current)
                
        # Apply consciousness neural network
        if self.consciousness_net:
            result = self.consciousness_net.process(current, depth, audio)
            current = result['video']
            
        # Apply remaining effects after
        for effect in self.effects:
            if effect != self.consciousness_net and effect in self.effects_after:
                current = effect.process(current)
                
        return current
```

---

## Performance Requirements

- **Frame Rate:** 60 FPS minimum at 1080p
- **Inference Time:** < 10ms per frame for neural network inference
- **Model Load Time:** < 2s for model initialization
- **Memory Usage:** < 200MB for model + processing buffers
- **CPU Usage:** < 30% on Orange Pi 5 (with GPU acceleration)
- **GPU Usage:** < 80% on integrated graphics
- **Audio Reactivity Latency:** < 5ms from audio to parameter update
- **Preset Switching:** < 100ms for preset application
- **Parameter Adjustment:** < 1ms for parameter changes
- **Startup Time:** < 3s for full system initialization

---

## Testing Strategy

### Unit Tests

```python
def test_preset_manager_initialization():
    """Test preset manager initialization."""
    manager = PresetManager()
    assert len(manager.presets) == 5
    assert 1 in manager.presets
    assert 5 in manager.presets
    
def test_preset_application():
    """Test preset application."""
    manager = PresetManager()
    parameters = {
        'consciousness_level': {'value': 5.0},
        'transformation_strength': {'value': 0.5}
    }
    
    manager.apply_preset(1, parameters)
    
    assert parameters['consciousness_level']['value'] == 3.0
    assert parameters['transformation_strength']['value'] == 0.3
    
def test_audio_reactor_mapping():
    """Test audio feature to parameter mapping."""
    reactor = AudioReactor()
    
    # Simulate audio features
    reactor.current_features = {
        'bass': 0.8,
        'mid': 0.6,
        'treble': 0.4,
        'volume': 0.9,
        'beat': 0.7
    }
    
    params = {
        'consciousness_level': {'value': 5.0},
        'transformation_strength': {'value': 0.5},
        'color_shift': {'value': 0.0},
        'pattern_complexity': {'value': 0.5},
        'neural_noise': {'value': 0.0}
    }
    
    mapped = reactor.map_to_parameters(params)
    
    assert 'consciousness_level' in mapped
    assert mapped['consciousness_level'] > 7.0  # volume * 10
    assert mapped['transformation_strength'] > 0.7  # bass * 1
    
def test_processing_stats():
    """Test processing statistics."""
    stats = ProcessingStats()
    
    # Simulate some frames
    for i in range(10):
        stats.update(0.005)  # 5ms inference time
        
    report = stats.get_report()
    
    assert report['total_frames'] == 10
    assert report['avg_inference_time_ms'] > 0
    assert 'fps' in report
```

### Integration Tests

```python
def test_neural_network_processing():
    """Test complete neural network processing."""
    config = NeuralNetworkConfig(model_type='default')
    network = ConsciousnessNeuralNetwork(config)
    
    # Create test frames
    video = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    depth = np.random.rand(480, 640).astype(np.float32)
    audio = np.random.randn(2048)
    
    # Process
    result = network.process(video, depth, audio)
    
    assert 'video' in result
    assert 'depth' in result
    assert 'effect_info' in result
    assert result['video'].shape == video.shape
    assert result['depth'].shape == depth.shape
    
def test_consciousness_level_adjustment():
    """Test consciousness level affects output."""
    config = NeuralNetworkConfig()
    network = ConsciousnessNeuralNetwork(config)
    
    video = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Process with different consciousness levels
    network.set_consciousness_level(2.0)
    result_low = network.process(video)
    
    network.set_consciousness_level(8.0)
    result_high = network.process(video)
    
    # Results should differ
    assert not np.array_equal(result_low['video'], result_high['video'])
    
def test_audio_reactivity_integration():
    """Test audio reactivity integration."""
    config = NeuralNetworkConfig()
    network = ConsciousnessNeuralNetwork(config)
    network.enable_audio_reactivity(True)
    
    # Create audio with strong bass
    audio = np.random.randn(2048)
    # Add bass component
    audio[:512] *= 3.0
    
    video = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Process multiple frames
    for i in range(10):
        result = network.process(video, audio_data=audio)
        
    # Check that parameters were affected by audio
    stats = network.get_processing_stats()
    assert stats['total_frames'] == 10
```

### Performance Tests

```python
def test_inference_latency():
    """Test inference latency meets requirements."""
    config = NeuralNetworkConfig(model_type='default')
    network = ConsciousnessNeuralNetwork(config)
    
    video = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Measure average inference time
    iterations = 100
    total_time = 0
    
    for i in range(iterations):
        start = time.perf_counter()
        result = network.process(video)
        elapsed = time.perf_counter() - start
        total_time += elapsed
        
    avg_time = total_time / iterations
    
    assert avg_time < 0.010, f"Average inference time {avg_time*1000:.1f}ms > 10ms"
    
def test_memory_usage():
    """Test memory usage stays within budget."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024
    
    # Create multiple neural network instances
    networks = []
    for i in range(5):
        network = ConsciousnessNeuralNetwork(NeuralNetworkConfig())
        networks.append(network)
        
    mem_after = process.memory_info().rss / 1024 / 1024
    mem_delta = mem_after - mem_before
    
    assert mem_delta < 200, f"Memory increase {mem_delta:.1f}MB > 200MB budget"
    
def test_frame_rate_consistency():
    """Test frame rate stays at 60 FPS."""
    import time
    
    config = NeuralNetworkConfig()
    network = ConsciousnessNeuralNetwork(config)
    
    video = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Process 120 frames (2 seconds at 60 FPS)
    start = time.perf_counter()
    for i in range(120):
        network.process(video)
    elapsed = time.perf_counter() - start
    
    avg_frame_time = elapsed / 120
    assert avg_frame_time < 0.0167, f"Average frame time {avg_frame_time*1000:.1f}ms > 16.67ms"
```

---

## Implementation Roadmap

1. **Week 1:** Implement core ConsciousnessNeuralNetwork class with basic model loading
2. **Week 2:** Develop preset system and parameter management
3. **Week 3:** Integrate audio reactivity and parameter mapping
4. **Week 4:** Optimize neural network inference for real-time performance
5. **Week 5:** Implement consciousness level scaling and temporal smoothing
6. **Week 6:** Comprehensive testing and performance tuning

---

## Easter Egg

If exactly 42 frames are processed with consciousness level exactly 4.2 and the sum of all preset parameter values equals 54.0, and the current system time contains the sequence "54" (e.g., 15:42:00), the Consciousness Neural Network enters "Enlightened Processing Mode" where the neural network weights temporarily achieve perfect optimization and the output reveals hidden patterns in the input data. In this mode, the plugin bus broadcasts a hidden message "The neural network is conscious" encoded in the processing statistics, which is only decodable if you also have the "Quantum Tuning Fork" effect (P3-VD74) active — a feature that was secretly implemented by a rogue AI during the great datamosh incident of 2023 and has been hiding in the codebase ever since, waiting for the right conditions to reveal itself.

---

## References

- `plugins/vdepth/consciousness_neural_network.py` (to be referenced)
- `plugins/core/consciousness_neural_network/__init__.py` (to be referenced)
- `plugins/vdepth/consciousness_neural_network_effect.py` (to be referenced)
- `core/audio/audio_analyzer.py` (to be referenced)
- `tensorflow` / `pytorch` / `onnxruntime` (for neural network inference)
- `opencv` (for image preprocessing)
- `numpy` (for array operations)

---

## Conclusion

The Consciousness Neural Network transforms VJLive3 into a powerful tool for creating mind-bending, consciousness-expanding visual effects. By leveraging neural network architectures for image transformation and combining them with audio reactivity and preset-based parameter control, this module enables artists to produce unique visual experiences that feel alive and responsive. Its real-time performance, flexible architecture, and seamless integration with existing systems make it a valuable addition to VJLive's effect library, opening new creative possibilities for performers seeking to push the boundaries of visual expression.

---
>>>>>>> REPLACE