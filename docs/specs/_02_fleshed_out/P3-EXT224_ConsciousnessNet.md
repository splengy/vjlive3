# P3-EXT224: ConsciousnessNet

## Description

Deep learning module `ConsciousnessNet` serving as the cognitive engine for the Neural and Quantum integration layers. It simulates spatial reality warping, multi-dimensional tensor matrix rotations, and quantum probability entanglement across a bespoke PyTorch topology.

## What This Module Does

This module implements the `ConsciousnessNet` inference core, ported from the legacy `VJlive-2/plugins/vdepth/tunnel_vision_3.py` codebase. It represents the pinnacle of visual synthesis technology, generating 8x8 quantum state matrices and pushing them through a deep forward-pass network to produce fluid probability distributions. It operates independently of standard image convolution, instead generating topological state data (e.g., `reality_matrix`, `singularity_field`) that downstream shaders use to warp spatial constraints dynamically.

## Public Interface

```python
import torch
import torch.nn as nn
import numpy as np
from typing import Tuple, Optional

class ConsciousnessNet(nn.Module):
    """
    Deep learning module serving as the cognitive engine for Neural and Quantum integration layers.
    
    Implements a 4-layer PyTorch topology: Linear(8, 16) -> Linear(16, 32) -> Linear(32, 16) -> Linear(16, 8)
    using F.relu activations and final torch.sigmoid clamp. Processes quantum state probability distributions.
    """
    
    def __init__(self):
        """
        Initialize the 4-layer PyTorch topology with specific dimensions.
        
        Architecture: 8 -> 16 -> 32 -> 16 -> 8 neurons
        Activations: ReLU for hidden layers, Sigmoid for output
        """
        super().__init__()
        
        # Layer definitions with specific dimensions
        self.layer1 = nn.Linear(8, 16)
        self.layer2 = nn.Linear(16, 32)
        self.layer3 = nn.Linear(32, 16)
        self.layer4 = nn.Linear(16, 8)
        
        # Initialize weights using Kaiming uniform for ReLU layers
        nn.init.kaiming_uniform_(self.layer1.weight)
        nn.init.kaiming_uniform_(self.layer2.weight)
        nn.init.kaiming_uniform_(self.layer3.weight)
        
        # Initialize final layer with Xavier uniform
        nn.init.xavier_uniform_(self.layer4.weight)
        
        # Track whether model is in evaluation mode
        self._is_evaluated = False
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Process quantum state probability distributions through the network.
        
        Args:
            x: Input tensor of shape (batch_size, 8) representing quantum state
        
        Returns:
            torch.Tensor of shape (batch_size, 8) with normalized probability distributions
        
        Raises:
            ValueError: If input tensor has incorrect shape
        """
        if x.shape[1] != 8:
            raise ValueError(f"Input tensor must have 8 features, got {x.shape[1]}")
        
        # Forward pass through network
        x = torch.relu(self.layer1(x))
        x = torch.relu(self.layer2(x))
        x = torch.relu(self.layer3(x))
        x = torch.sigmoid(self.layer4(x))
        
        self._is_evaluated = True
        return x
    
    def is_evaluated(self) -> bool:
        """
        Check if the network has been evaluated at least once.
        
        Returns:
            bool: True if forward pass has been called, False otherwise
        """
        return self._is_evaluated

class QuantumConsciousnessSystem:
    """
    Encapsulates the ConsciousnessNet network + state matrices for entanglement/reality manipulation.
    
    Manages quantum state evolution, reality matrix generation, and neural singularity calculations.
    """
    
    def __init__(self, consciousness_net: Optional[ConsciousnessNet] = None):
        """
        Initialize the quantum consciousness system.
        
        Args:
            consciousness_net: Optional pre-trained ConsciousnessNet instance
        """
        # Initialize network (create if not provided)
        self.net = consciousness_net if consciousness_net else ConsciousnessNet()
        
        # Initialize state matrices
        self._quantum_state = torch.zeros(8)
        self._reality_matrix = np.eye(4)
        self._singularity_field = np.zeros((16, 16))
        self._phase = 0.0
        
        # Performance tracking
        self._evaluation_count = 0
        self._total_evaluation_time = 0.0
    
    def compute_consciousness_state(self, time_val: float) -> np.ndarray:
        """
        Compute consciousness state from quantum probability distributions.
        
        Args:
            time_val: Current time value for phase calculations
        
        Returns:
            np.ndarray: Normalized consciousness state vector (8 elements)
        
        Raises:
            RuntimeError: If PyTorch is unavailable or CUDA OOM occurs
        """
        try:
            # Generate quantum state noise seeds
            quantum_seeds = torch.randn(8)
            
            # Process through network
            with torch.no_grad():
                start_time = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                end_time = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                
                if start_time:
                    start_time.record()
                
                # Forward pass
                quantum_state = self.net(quantum_seeds.unsqueeze(0)).squeeze()
                
                if end_time:
                    end_time.record()
                    torch.cuda.synchronize()
                    elapsed = start_time.elapsed_time(end_time) / 1000.0  # Convert to seconds
                else:
                    elapsed = 0.0
                
                # Update performance tracking
                self._evaluation_count += 1
                self._total_evaluation_time += elapsed
            
            # Store quantum state
            self._quantum_state = quantum_state
            
            # Apply consciousness evolution
            consciousness_state = self._apply_consciousness_evolution(quantum_state, time_val)
            
            return consciousness_state.numpy()
            
        except (RuntimeError, ImportError) as e:
            # Fallback to identity matrix if PyTorch unavailable or CUDA OOM
            logger.warning(f"Quantum consciousness fallback: {str(e)}")
            return np.eye(4).flatten()
    
    def _apply_consciousness_evolution(self, quantum_state: torch.Tensor, time_val: float) -> torch.Tensor:
        """
        Apply phase matrix to evaluate quantum probability over time.
        
        Args:
            quantum_state: Input quantum state tensor
            time_val: Current time value for phase calculations
        
        Returns:
            torch.Tensor: Evolved consciousness state
        """
        phase = time_val % (2 * np.pi)
        
        # Create phase matrix: exp(1j * phase * (i + j))
        indices = torch.arange(8).float()
        phase_matrix = torch.exp(1j * phase * (indices.unsqueeze(1) + indices.unsqueeze(0)))
        
        # Apply phase transformation
        evolved_state = torch.matmul(phase_matrix, quantum_state.unsqueeze(1)).squeeze()
        
        # Normalize via absolute sum
        norm = torch.sum(torch.abs(evolved_state))
        if norm > 0:
            evolved_state = evolved_state / norm
        
        return evolved_state
    
    def generate_reality_matrix(self, time_val: float) -> np.ndarray:
        """
        Generate 4x4 spatial distortion matrix for reality manipulation.
        
        Args:
            time_val: Current time value for rotation calculations
        
        Returns:
            np.ndarray: 4x4 reality transformation matrix
        """
        phase = time_val % (2 * np.pi)
        
        # Create rotation matrices for 4D space
        rotation_1 = self._create_4d_rotation_matrix(phase, 0, 1)
        rotation_2 = self._create_4d_rotation_matrix(phase * 0.7, 2, 3)
        
        # Combine rotations
        reality_matrix = np.matmul(rotation_1, rotation_2)
        
        # Store for later use
        self._reality_matrix = reality_matrix
        return reality_matrix
    
    def _create_4d_rotation_matrix(self, angle: float, axis1: int, axis2: int) -> np.ndarray:
        """
        Create a 4D rotation matrix for specified axes.
        
        Args:
            angle: Rotation angle in radians
            axis1: First rotation axis (0-3)
            axis2: Second rotation axis (0-3)
        
        Returns:
            np.ndarray: 4x4 rotation matrix
        """
        matrix = np.eye(4)
        matrix[axis1, axis1] = np.cos(angle)
        matrix[axis1, axis2] = -np.sin(angle)
        matrix[axis2, axis1] = np.sin(angle)
        matrix[axis2, axis2] = np.cos(angle)
        return matrix
    
    def generate_neural_singularity(self, time_val: float, intensity: float = 1.0) -> np.ndarray:
        """
        Generate 16x16 gravity well for neural singularity calculations.
        
        Args:
            time_val: Current time value for phase calculations
            intensity: Gravity well intensity (0.0-1.0)
        
        Returns:
            np.ndarray: 16x16 singularity field
        """
        phase = time_val % (2 * np.pi)
        
        # Create coordinate grid
        x = np.linspace(-1, 1, 16)
        y = np.linspace(-1, 1, 16)
        xx, yy = np.meshgrid(x, y)
        
        # Calculate distance from center
        distance = np.sqrt(xx**2 + yy**2)
        
        # Apply singularity formula
        singularity = np.exp(-distance / (1 + intensity)) * np.sin(phase + distance * 0.1)
        
        # Store for later use
        self._singularity_field = singularity
        return singularity
    
    def get_performance_metrics(self) -> dict:
        """
        Get performance metrics for the consciousness system.
        
        Returns:
            dict: Performance metrics including evaluation count and average time
        """
        avg_time = (self._total_evaluation_time / self._evaluation_count
                   ) if self._evaluation_count > 0 else 0.0
        
        return {
            'evaluations': self._evaluation_count,
            'avg_time_ms': avg_time * 1000,
            'total_time_s': self._total_evaluation_time,
            'status': 'active' if self.net.is_evaluated() else 'inactive'
        }
    
    def reset(self) -> None:
        """
        Reset the consciousness system to initial state.
        """
        self._quantum_state = torch.zeros(8)
        self._reality_matrix = np.eye(4)
        self._singularity_field = np.zeros((16, 16))
        self._phase = 0.0
        self._evaluation_count = 0
        self._total_evaluation_time = 0.0
        self.net = ConsciousnessNet()  # Reinitialize network
```

## Inputs and Outputs

*   **Inputs:** `time_val` (float), 8x8 `quantum_consciousness` noise seeds.
*   **Outputs:** Normalised `torch.Tensor` probability distributions controlling downstream visual phase states, `reality_matrix` 4x4 spatial distortions, and `singularity_field` focal coordinates.

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/tunnel_vision_3.py`
- **Architectural Soul**: The legacy implementation uses a highly specific 4-layer PyTorch topography: `Linear(8, 16) -> Linear(16, 32) -> Linear(32, 16) -> Linear(16, 8)` utilizing `F.relu` and a final `torch.sigmoid` activation clamp.

### Key Algorithms
1. **Consciousness Evolution**: Applies a phase matrix `np.exp(1j * phase * (i + j))` to evaluate quantum probability over time and normalize via absolute sum.
2. **Reality Manipulation**: Iterates through 4 spatial dimensions, generating a rotating transformation matrix applied to UV domains to simulate 4D rotation collapsing into 2D screens.
3. **Neural Singularity**: Generates a 16x16 gravity well mathematically calculating distance via `np.exp(-distance / (1 + intensity)) * np.sin(phase + distance * 0.1)`.
4. **Synesthetic Audio Map**: A 3x3 diagonal trace mapping Bass/Mid/Treble directly into the probability matrix framework.

### Optimization Constraints & Safety Rails
- **Memory Footprint**: Do NOT re-allocate the `torch.Tensor` every frame. Maintain state tensors locally to avoid continuous GC strain in the render loop.
- **Node Wiring (Safety Rail #6)**: Must fail gracefully if Torch is unavailable or CUDA OOMs occur, bypassing reality matrices to identity `np.eye(4)`.

## Test Plan

*   **Logic (Pytest)**: Ensure the 4-layer `ConsciousnessNet` dimensions strictly map (8 -> 16 -> 32 -> 16 -> 8) and that output distributions are correctly normalized between 0-1 via sigmoid.
*   **Visual Check**: Verifying that the generated `reality_matrix` correctly scales/rotates downstream UVs without artifact tearing or NaN explosion.
*   **Performance Constraints**: The pure-math iteration for `_quantum_consciousness` and `_neural_singularity` loops must execute within < 2ms to prevent render stalls.

## Deliverables

1.  Implemented `ConsciousnessNet` module inside `src/vjlive3/ml/consciousness_net.py`.
2.  Unit tests covering tensor transformations and neural phase boundaries (`tests/ml/test_consciousness_net.py`).
3.  Integration hooks for the `TunnelVision3` shader architecture.
