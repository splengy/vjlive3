# P3-EXT224: ConsciousnessNet

## Description

Deep learning module `ConsciousnessNet` serving as the cognitive engine for the Neural and Quantum integration layers. It simulates spatial reality warping, multi-dimensional tensor matrix rotations, and quantum probability entanglement across a bespoke PyTorch topology.

## What This Module Does

This module implements the `ConsciousnessNet` inference core, ported from the legacy `VJlive-2/plugins/vdepth/tunnel_vision_3.py` codebase. It represents the pinnacle of visual synthesis technology, generating 8x8 quantum state matrices and pushing them through a deep forward-pass network to produce fluid probability distributions. It operates independently of standard image convolution, instead generating topological state data (e.g., `reality_matrix`, `singularity_field`) that downstream shaders use to warp spatial constraints dynamically.

## Public Interface

```python
class ConsciousnessNet(nn.Module):
    def __init__(self):
        # 4-Layer PyTorch topology initialized
        pass
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Processes quantum state probability distributions
        pass

class QuantumConsciousnessSystem:
    # Encapsulates the network + state matrices (entanglement/reality)
    def compute_consciousness_state(self, time_val: float) -> np.ndarray:
        pass
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
