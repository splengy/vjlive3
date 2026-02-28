# P3-EXT225: ConsciousnessNeuralNetwork

## Description

The `ConsciousnessNeuralNetwork` is a massive "Quantum Mind Matrix" effect mapping 28 granular psychological and neural state parameters into a unified shader. It renders dense, audio-reactive node networks based on cognitive loading and quantum phase states.

## What This Module Does

This module implements the `ConsciousnessNeuralNetwork` effect, ported from the legacy `VJlive-2/plugins/vdepth/consciousness_neural_network.py` codebase. Rather than using actual deep-learning (which `ConsciousnessNet` handles), this module is purely a high-end visualization engine designed to *look* like abstract cognitive processing. It calculates pseudo-3D neural topologies strictly on the GPU fragment shader by modulating depth matrices with sinusoidal interference, mimicking synapses firing across neural pathways under heavy cognitive or quantum load.

## Public Interface

```python
class ConsciousnessNeuralNetwork(EffectNode):
    def __init__(self):
        # Initializes 28 parameters split across 4 macro categories
        pass
    def process(self, video_frame: np.ndarray, depth_frame: np.ndarray, audio_data: dict) -> dict:
        # Pushes neural/consciousness state structs to the GPU
        pass
    def update_preset(self, preset_index: int) -> bool:
        # Cross-loads legacy Neural/Quantum/Consciousness macro states
        pass
```

## Inputs and Outputs

*   **Inputs**: RGB matrix (`tex0`), integer Depth Matrix (`depthRawTex`), time, Audio dictionary (Bass, Treble, Mid, Overtone).
*   **Outputs**: Abstract organic neural geometries rendered as a composite over the video feed.

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/consciousness_neural_network.py`
- **Architectural Soul**: Features an immense fragment shader comprising multiple discrete sub-systems: `neural_network_generation`, `consciousness_patterns`, `quantum_consciousness`, and `audio_reactivity`. 

### Key Algorithms
1. **Topological Synapse Generation**: Computes a spatial `neural_factor` inside the GLSL by multiplying density, fire rate, growth, plasticity, and reorganization frequency scales against UV and world positions.
2. **Cognitive Load Modulation**: Multiplies "thought intensity", "memory access", and "emotional state" sine wave intersections, drastically altering point generation structures based on the `u_consciousness_level` uniform.
3. **Quantum Mechanics Visualized**: Maps `u_quantum_entanglement` and `u_quantum_foam` into the topological math, shifting color gradients directly into the "Quantum Orange" (RGB `0.8, 0.4, 0.2`) spectrum.
4. **4-Tier Preset Engine**: Houses macro-snapshots configured from the legacy codebase: "Neural Network", "Quantum Mind", and "Consciousness Flow", fundamentally shifting all 28 slider states instantly.

### Optimization Constraints & Safety Rails
- **Uniform Overhead (Safety Rail #2)**: Uploading 28 individual float uniforms per frame is expensive natively on PyOpenGL. VJLive3 must either pack these into a UBO (Uniform Buffer Object) struct or vector arrays via `glUniform1fv` rather than calling `glUniform1f` 28 times per frame.
- **Shader Instruction Limit**: The fragment shader math is immensely intensive (dozens of cascaded trig functions per pixel). Requires validation that 1080p rendering sustains 60FPS on target hardware.

## Test Plan

*   **Logic (Pytest)**: Ensure the `update_preset` method accurately overwrites all 28 parameters without raising key errors.
*   **Visual Check**: Verifying that the "Consciousness Purple" (0.4, 0.2, 0.8) and "Neural Green" (0.2, 0.8, 0.4) gradients mix correctly via the `mix()` function based on audio intensity and cognitive load.
*   **Performance Constraints**: Must test the shader load at 4K resolution; if dropping frames, implement a parameter reducing the trig calculations or falling back to a lower-resolution render buffer (FBO) and upscaling.

## Deliverables

1.  Implemented `ConsciousnessNeuralNetwork` Node inside `src/vjlive3/plugins/consciousness_neural_network.py`.
2.  Ported and UBO-optimized GLSL fragment shader (`assets/shaders/consciousness_net.frag`).
3.  Unit tests validating parameter state transitions (`tests/plugins/test_consciousness_neural_network.py`).
