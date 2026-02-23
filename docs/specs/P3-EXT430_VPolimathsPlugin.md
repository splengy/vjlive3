# P3-EXT430: Make Noise Polimaths

## Description

A direct software emulation of the hardware Make Noise Polimaths Eurorack synthesizer module. Polyphonic evolution of the legendary MATHS universal control voltage generator.

## What This Module Does

This specification defines the VJLive3 port for the legacy `vmake_noise` ecosystem plugin: `VPolimathsPlugin`. It behaves as a NodeGraph component handling input/output audio or modulation streams identically to its real-world counterpart.

## Public Interface

```python
class VPolimathsPlugin(EffectNode):
    """Software virtualization of Make Noise Polimaths."""
    # Physical knob/jack parameters map 1:1 to Uniforms/Inputs
```

## Implementation Notes

### Legacy References
- **Source Codebase**: `vjlive`
- **Hardware Documentation:**
  - **Manual PDF**: `vjlive/JUNK/manuals_make_noise/MNmanuals/polimaths-manual.pdf`

### Architectural Soul
The module is expected to replicate the exact DSP logic (if audio-rate) or mathematical modulation curves (if control-rate) described in the `polimaths` documentation.

### Optimization Constraints & Safety Rails
- **GIL Locking limits:** If implementing DSP in pure Python, NumPy vectorization must be used to process audio buffers chunk-by-chunk to avoid blocking the main 60FPS render loop.

## Test Plan

*   **Logic (Pytest)**: Send zeroed CV signals and verify the internal physics match the resting state of the Polimaths hardware.

## Deliverables
1. `src/vjlive3/plugins/make_noise/polimaths.py`
2. Integrated block in the `MakeNoiseRegistry`
