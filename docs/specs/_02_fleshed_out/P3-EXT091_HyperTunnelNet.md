# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT091 — NeuralQuantumHyperTunnel

**Phase:** Phase 3 / P3-EXT
**Assigned To:** Desktop Roo Worker
**Spec Written By:** Desktop Roo Worker
**Date:** 2026-03-01

---

## What This Module Does

The `NeuralQuantumHyperTunnel` module provides an advanced visual creation system that combines Tunnel Vision geometry, real-time Machine Learning Neural Inference, and Agent-based interaction to generate hyper-dimensional rave graphics. It bridges the gap between traditional shader-based effects and modern AI-driven content generation, creating dynamic, responsive visual experiences that evolve based on user interaction and audio input.

## What It Does NOT Do

- Handle basic 2D video effects or simple transformations
- Provide standalone audio processing or synthesis
- Implement traditional particle systems or physics simulations
- Support non-real-time rendering or offline processing
- Function as a general-purpose machine learning inference engine

## Public Interface
```python
from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
from torch import nn
from dataclasses import dataclass

@dataclass
class AudioSpectrum:
    bass_norm: float
    mid_norm: float
    treble_norm: float
    spectral_flux: float
    spectral_centroid: float

@dataclass
class AgentContext:
    user_preference: float
    session_length: float
    sync_state: str
    collective_consciousness: float
    agent_autonomy: float
    surprise_factor: float

class HyperTunnelNet(nn.Module):
    def __init__(
        self,
        input_channels: int = 3,
        hidden_dim: int = 128,
        num_heads: int = 8,
        num_layers: int = 4,
        dropout: float = 0.1
    ) -> None:
        """
        Initialize the HyperTunnelNet neural network.
        
        Args:
            input_channels: Number of input channels (3 for RGB)
            hidden_dim: Hidden dimension size for attention layers
            num_heads: Number of attention heads
            num_layers: Number of transformer layers
            dropout: Dropout probability
        """
        super().__init__()
        self.input_channels = input_channels
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        
        # CNN feature extractor
        self.conv_layers = nn.Sequential(
            nn.Conv2d(input_channels, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.ReLU()
        )
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output projection
        self.output_projection = nn.Linear(hidden_dim, 256)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the neural network.
        
        Args:
            x: Input tensor of shape (batch_size, channels, height, width)
            
        Returns:
            Output tensor of shape (batch_size, output_dim)
        """
        # Extract features
        features = self.conv_layers(x)
        batch_size, channels, height, width = features.shape
        features = features.view(batch_size, channels, -1).permute(2, 0, 1)  # (seq_len, batch, dim)
        
        # Apply transformer
        transformed = self.transformer(features)
        
        # Aggregate and project
        aggregated = transformed.mean(dim=0)  # (batch, dim)
        output = self.output_projection(aggregated)  # (batch, 256)
        
        return output

class NeuralQuantumHyperTunnel(BaseNode):
    def __init__(
        self,
        model_path: Optional[str] = None,
        max_particles: int = 100000,
        quantum_feedback: float = 0.5,
        synesthetic_mapping: bool = True,
        agent_autonomy: float = 0.7
    ) -> None:
        """
        Initialize the NeuralQuantumHyperTunnel node.
        
        Args:
            model_path: Path to pre-trained model weights (optional)
            max_particles: Maximum number of particles for tunnel effects
            quantum_feedback: Strength of quantum feedback effects
            synesthetic_mapping: Enable audio-reactive parameter mapping
            agent_autonomy: Degree of agent control over parameters
        """
        super().__init__()
        
        # Neural network
        self.neural_model = HyperTunnelNet()
        if model_path:
            self.load_model(model_path)
        
        # Quantum state matrices
        self.quantum_state = np.eye(4, dtype=np.float32)
        self.warp_matrix = np.eye(4, dtype=np.float32)
        
        # Parameters
        self.tunnel_speed = 1.0
        self.neural_intensity = 0.5
        self.synesthetic_mapping = synesthetic_mapping
        self.agent_autonomy = agent_autonomy
        self.surprise_factor = 0.1
        self.learning_rate = 0.01
        
        # Agent system
        self.agent_interaction_history = []
        self.user_preference_model = None
        self.collective_consciousness = 0.0
        
        # Audio processing
        self.audio_spectrum = AudioSpectrum(0.0, 0.0, 0.0, 0.0, 0.0)
        
        # Performance tracking
        self.frame_times = []
        self.inference_times = []
        
    def load_model(self, model_path: str) -> None:
        """
        Load pre-trained model weights.
        
        Args:
            model_path: Path to model weights file
        """
        try:
            checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
            self.neural_model.load_state_dict(checkpoint['model_state_dict'])
            self.neural_model.eval()
        except Exception as e:
            print(f"Warning: Could not load model: {e}")
    
    def get_agent_suggestions(self, current_context: AgentContext) -> Dict[str, float]:
        """
        Generate parameter suggestions based on agent context.
        
        Args:
            current_context: Current agent context including user preferences
            
        Returns:
            Dictionary of parameter suggestions
        """
        suggestions = {}
        
        # Base suggestions from context
        suggestions['tunnel_speed'] = current_context.user_preference * 2.0
        suggestions['neural_intensity'] = current_context.collective_consciousness * 0.8
        suggestions['quantum_feedback'] = current_context.surprise_factor * 1.5
        
        # Apply agent autonomy
        for param, value in suggestions.items():
            current_value = getattr(self, param, 0.5)
            suggestions[param] = current_value * (1.0 - self.agent_autonomy) + value * self.agent_autonomy
        
        return suggestions
    
    def apply_agent_learning(self, user_feedback: float) -> None:
        """
        Update agent model based on user feedback.
        
        Args:
            user_feedback: User satisfaction rating (0.0 to 1.0)
        """
        # Update user preference model
        if self.user_preference_model:
            self.user_preference_model.update(user_feedback)
        
        # Adjust learning rate based on feedback
        self.learning_rate = 0.01 + (1.0 - user_feedback) * 0.05
        
        # Update collective consciousness
        self.collective_consciousness = (
            self.collective_consciousness * 0.9 + user_feedback * 0.1
        )
    
    def apply_uniforms(
        self, 
        time_val: float,
        resolution: Tuple[int, int],
        audio_reactor: AudioSpectrum,
        frame_data: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """
        Generate OpenGL uniforms for rendering.
        
        Args:
            time_val: Current time in seconds
            resolution: Screen resolution (width, height)
            audio_reactor: Audio spectrum data
            frame_data: Current video frame
            
        Returns:
            Dictionary of uniform values for shader
        """
        uniforms = {}
        
        # Update audio spectrum
        self.audio_spectrum = audio_reactor
        
        # Synesthetic audio mapping
        if self.synesthetic_mapping:
            self.tunnel_speed = 1.0 + audio_reactor.bass_norm * 2.0
            self.neural_intensity = 0.3 + audio_reactor.mid_norm * 0.7
            
        # Neural inference (asynchronous)
        if hasattr(self, 'ml_inference_worker') and self.ml_inference_worker.is_ready():
            frame_tensor = torch.from_numpy(frame_data).permute(2, 0, 1).float() / 255.0
            frame_tensor = frame_tensor.unsqueeze(0)  # Add batch dimension
            
            with torch.no_grad():
                neural_output = self.neural_model(frame_tensor)
                self.neural_intensity = neural_output.mean().item() * 0.1
        
        # Quantum state updates
        angle = time_val * self.tunnel_speed * 0.1
        self.quantum_state = np.array([
            [np.cos(angle), -np.sin(angle), 0, 0],
            [np.sin(angle), np.cos(angle), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Warp matrix calculations
        self.warp_matrix = self.calculate_hyper_warp(time_val, resolution)
        
        # Collect uniforms
        uniforms['quantum_state'] = self.quantum_state
        uniforms['warp_matrix'] = self.warp_matrix
        uniforms['tunnel_speed'] = np.array([self.tunnel_speed], dtype=np.float32)
        uniforms['neural_intensity'] = np.array([self.neural_intensity], dtype=np.float32)
        uniforms['collective_consciousness'] = np.array([self.collective_consciousness], dtype=np.float32)
        uniforms['agent_autonomy'] = np.array([self.agent_autonomy], dtype=np.float32)
        uniforms['audio_bass'] = np.array([audio_reactor.bass_norm], dtype=np.float32)
        uniforms['audio_mid'] = np.array([audio_reactor.mid_norm], dtype=np.float32)
        uniforms['audio_treble'] = np.array([audio_reactor.treble_norm], dtype=np.float32)
        
        return uniforms
    
    def calculate_hyper_warp(
        self, 
        time_val: float, 
        resolution: Tuple[int, int]
    ) -> np.ndarray:
        """
        Calculate hyper-warp matrix for 4D transformations.
        
        Args:
            time_val: Current time in seconds
            resolution: Screen resolution (width, height)
            
        Returns:
            4x4 warp matrix
        """
        width, height = resolution
        aspect = width / height
        
        # Base rotation
        angle = time_val * self.tunnel_speed * 0.05
        
        # Additional quantum effects
        quantum_effect = np.sin(time_val * 2.0) * self.quantum_feedback * 0.5
        
        # Construct warp matrix
        warp = np.array([
            [np.cos(angle), -np.sin(angle), 0, quantum_effect * 0.1],
            [np.sin(angle), np.cos(angle), 0, -quantum_effect * 0.1],
            [0, 0, 1 + quantum_effect * 0.2, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        return warp
    
    def process_frame(
        self, 
        frame: np.ndarray,
        audio_data: np.ndarray
    ) -> np.ndarray:
        """
        Process a video frame with neural effects.
        
        Args:
            frame: Input video frame (H x W x 3)
            audio_data: Audio data for synesthetic effects
            
        Returns:
            Processed frame with effects applied
        """
        # Get audio spectrum
        audio_spectrum = self.analyze_audio(audio_data)
        
        # Generate uniforms
        uniforms = self.apply_uniforms(
            time_val=time.time(),
            resolution=frame.shape[:2][::-1],
            audio_reactor=audio_spectrum,
            frame_data=frame
        )
        
        # Apply effects (placeholder - actual implementation would use OpenGL)
        processed_frame = self.apply_shader_effects(frame, uniforms)
        
        return processed_frame
    
    def analyze_audio(self, audio_data: np.ndarray) -> AudioSpectrum:
        """
        Analyze audio data to extract spectrum information.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            AudioSpectrum object with normalized values
        """
        # Compute FFT
        fft = np.fft.rfft(audio_data)
        fft = np.abs(fft)
        
        # Split into bands
        bass = np.mean(fft[:10])
        mid = np.mean(fft[10:50])
        treble = np.mean(fft[50:])
        
        # Normalize
        total = bass + mid + treble + 1e-6
        return AudioSpectrum(
            bass_norm=bass / total,
            mid_norm=mid / total,
            treble_norm=treble / total,
            spectral_flux=np.std(fft),
            spectral_centroid=np.average(np.arange(len(fft)), weights=fft)
        )
    
    def apply_shader_effects(
        self, 
        frame: np.ndarray, 
        uniforms: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """
        Apply shader effects using uniforms.
        
        Args:
            frame: Input frame
            uniforms: Uniform values
            
        Returns:
            Frame with effects applied
        """
        # This would be implemented using OpenGL shaders in practice
        # For now, return the frame unchanged
        return frame.copy()
```

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame_data` | `np.ndarray` | Video frame (H x W x 3) | uint8, 0-255 |
| `audio_reactor` | `AudioSpectrum` | Audio spectrum data | Normalized 0.0-1.0 |
| `agent_context` | `AgentContext` | Agent parameters | See AgentContext constraints |
| `time_val` | `float` | Current time | >= 0.0 |
| `resolution` | `Tuple[int, int]` | Screen resolution | Positive integers |

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `uniforms` | `Dict[str, np.ndarray]` | OpenGL uniforms | 4x4 matrices, floats |
| `processed_frame` | `np.ndarray` | Output frame | uint8, 0-255 |
| `neural_output` | `torch.Tensor` | Neural network output | Float tensor |

## Edge Cases and Error Handling

- **Empty frame**: Return black frame when input is None or empty
- **Invalid audio data**: Handle zero-length audio arrays gracefully
- **Model loading failure**: Fall back to default parameters if model cannot be loaded
- **Performance degradation**: Implement adaptive quality based on frame rate
- **NaN/Inf values**: Detect and handle invalid numerical inputs in neural outputs
- **Memory overflow**: Raise MemoryError if particle count exceeds system limits
- **GPU unavailability**: Fall back to CPU implementation when CUDA not available

## Mathematical Implementation Details

### Neural Network Forward Pass
```python
# Feature extraction through CNN layers
features = conv_layers(input_tensor)  # (batch, 256, H', W')
features = features.view(batch_size, 256, -1).permute(2, 0, 1)  # (seq_len, batch, dim)

# Transformer attention mechanism
transformed = transformer(features)  # MultiheadAttention with 8 heads

# Aggregation and projection
aggregated = transformed.mean(dim=0)  # (batch, 256)
output = output_projection(aggregated)  # (batch, 256)
```

### Quantum State Matrix Calculation
```python
# Base rotation matrix
angle = time_val * tunnel_speed * 0.1
quantum_matrix = np.array([
    [np.cos(angle), -np.sin(angle), 0, 0],
    [np.sin(angle), np.cos(angle), 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1]
], dtype=np.float32)

# Add quantum feedback effects
quantum_effect = np.sin(time_val * 2.0) * quantum_feedback * 0.5
quantum_matrix[0, 3] = quantum_effect * 0.1
quantum_matrix[1, 3] = -quantum_effect * 0.1
quantum_matrix[2, 2] = 1 + quantum_effect * 0.2
```

### Synesthetic Audio Mapping
```python
# Audio spectrum to parameter mapping
mapped_speed = 1.0 + bass_norm * 2.0  # Bass affects tunnel speed
mapped_intensity = 0.3 + mid_norm * 0.7  # Mids affect neural intensity
mapped_aberration = treble_norm * 0.5  # Treble affects visual aberration
```

### Hyper-Warp Matrix Calculation
```python
# Calculate warp matrix with quantum effects
warp_matrix = np.array([
    [np.cos(angle), -np.sin(angle), 0, quantum_effect * 0.1],
    [np.sin(angle), np.cos(angle), 0, -quantum_effect * 0.1],
    [0, 0, 1 + quantum_effect * 0.2, 0],
    [0, 0, 0, 1]
], dtype=np.float32)
```

## Performance Characteristics

- **Neural Inference**: ~15-30ms per frame on modern GPU (depends on model size)
- **CPU Fallback**: ~200-500ms per frame (not suitable for real-time)
- **Memory Usage**: ~50MB for model + ~10MB for frame buffers
- **Frame Rate**: Target 60fps at 1080p with GPU acceleration
- **Batch Processing**: Process frames in batches of 4 for optimal GPU utilization
- **Audio Analysis**: ~1ms for FFT computation on 1024 samples

## Dependencies

```python
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Optional GPU acceleration
try:
    import torch.cuda
    GPU_AVAILABLE = torch.cuda.is_available()
except ImportError:
    GPU_AVAILABLE = False
```

## Test Plan

### Unit Tests
- Test neural network forward pass with known inputs and expected outputs
- Verify quantum matrix calculations for different time values
- Test audio spectrum analysis with synthetic audio data
- Validate parameter mapping from audio to visual effects
- Test agent suggestion generation with different contexts

### Integration Tests
- Test full pipeline with mock video and audio inputs
- Verify performance with varying frame rates and resolutions
- Test GPU vs CPU implementations for correctness
- Validate real-time performance targets
- Test agent learning with simulated user feedback

### Performance Tests
- Benchmark neural inference at different model sizes
- Measure memory usage and identify optimization opportunities
- Test frame rate stability under load
- Compare CPU vs GPU performance
- Profile audio analysis performance

### Stress Tests
- Test with maximum resolution and frame rate
- Verify behavior with rapid parameter changes
- Test memory leak prevention
- Validate thread safety for concurrent access
- Test model loading with corrupted files

## Definition of Done

- All neural network components implemented and tested
- Quantum state calculations produce correct matrices
- Audio-reactive parameter mapping works correctly
- Agent system generates reasonable suggestions
- Performance targets met for target hardware
- Error handling covers all edge cases
- Documentation complete with usage examples
- Test coverage exceeds 95%

