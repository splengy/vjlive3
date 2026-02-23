# P3-EXT091: NeuralQuantumHyperTunnel (HyperTunnelNet)

## Description

An ultimate visual creation tool bridging the gap between Tunnel Vision geometry, real-time Machine Learning Neural Inference, and Agent-based interaction, generating hyper-dimensional rave graphics. 

## What This Module Does

This specification defines the `NeuralQuantumHyperTunnel` port derived from the VJlive-2 legacy stack. The module isn't just a shader; it integrates a full PyTorch `nn.Module` (HyperTunnelNet) featuring `MultiheadAttention` capable of accepting "creative context" triggers from the LLM-Agent system to organically alter parameters over time. It tracks "Collective Consciousness" variables based on user session length and sync states.

## Public Interface

```python
class NeuralQuantumHyperTunnel(BaseNode):
    # PyTorch Core
    neural_model: 'HyperTunnelNet'
    
    # Matrices
    quantum_state: np.ndarray # 4x4 matrix
    warp_matrix: np.ndarray # 4x4 matrix
    
    # Over 36 float parameters internally tracked spanning:
    # tunnel_speed, neural_intensity, quantum_feedback, synesthetic_mapping,
    # agent_autonomy, surprise_factor, learning_rate.
    
    def get_agent_suggestions(self, current_context: dict) -> dict: ...
    def apply_agent_learning(self, user_feedback: float) -> None: ...
    def apply_uniforms(self, time_val, resolution, audio_reactor, frame_data) -> dict: ...
```

## Inputs and Outputs

*   **Inputs**: Live video camera matrices (`frame_data`), real-time FFT slices (`audio_reactor`), and LLM-synthesized `agent_context` parameters.
*   **Outputs**: Generates a massive OpenGL Uniform Dictionary wrapping states across PyTorch inference coordinates, 4D hyperspace matrices, and collective energy floats.

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/neural_quantum_hyper_tunnel.py`
- **Architectural Soul**: The `HyperTunnelNet` PyTorch model takes a downsampled visual frame and runs it through CNNs followed by `MultiheadAttention(128)`. The outputs dynamically warp the image grid inside `_collective_consciousness` via matrix multiplication before pushing pixels into the final shader.

### Key Algorithms & Integration
1. **Synesthetic Audio Mapping**: Audio spectrum arrays are split into `bass_norm`, `mid_norm`, `treble_norm` mapping explicitly into `tunnel_speed`, `wall_warp`, `aberration`, and `grid_lines`.
2. **Agent Collaboration Loop**: Employs an RL-lite strategy where the `user_preference_model` detects user knob adjustments, appending them to an `agent_interaction_history`, generating parameter `suggestions` clamped by `agent_autonomy`.
3. **Hyper-Warp**: Calculates 4x4 homogeneous matrix rotation matrices driven by `time * hyper_warp_param` combining trigonometric shifts applied to UV map coordinate streams.

### Optimization Constraints & Safety Rails
- **Torch Overhead**: (Safety Rail #2) Inference via `self.neural_model(frame_tensor)` must not block the 60fps render thread. In VJLive3, the `HyperTunnelNet` inference MUST be decoupled into the asynchronous `MLInferenceWorker` queue.
- **NumPy Performance**: The legacy `np.mgrid` coordinate warping is incredibly CPU-expensive on 1080p frames. VJLive3 will deprecate the Python coordinate warp in favor of compiling the consciousness matrix directly into the PyOpenGL GLSL fragment shader input to maintain 60 FPS.

## Test Plan

*   **Logic (Pytest)**: Ensure the agent preference learning updates `autonomy` properly upon calling `apply_agent_learning`.
*   **Performance Tracking**: Ensure the module generates no blocking calls lasting over 16ms.

## Deliverables

1.  Implemented `NeuralQuantumHyperTunnel` inside `src/vjlive3/plugins/neural_quantum_hyper_tunnel.py` optimized via ML pipelines.
