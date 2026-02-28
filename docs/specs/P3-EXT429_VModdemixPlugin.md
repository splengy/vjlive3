# P3-EXT429: Make Noise Moddemix

## Description

A direct software emulation of the hardware Make Noise Moddemix Eurorack synthesizer module. Dual-channel balanced modulator (Ring Modulator) and VCA.

## What This Module Does

This specification defines the VJLive3 port for the legacy `vmake_noise` ecosystem plugin: `VModdemixPlugin`. It behaves as a NodeGraph component handling input/output audio or modulation streams identically to its real-world counterpart.

## Public Interface

```python
class VModdemixPlugin(EffectNode):
    """Software virtualization of Make Noise Moddemix."""
    # Physical knob/jack parameters map 1:1 to Uniforms/Inputs
```

## Implementation Notes

### Legacy References
- **Source Codebase**: `vjlive`
- **Hardware Documentation:**
  - **Manual PDF**: `vjlive/JUNK/manuals_make_noise/MNmanuals/moddemix-manual.pdf`

### Architectural Soul
The module is expected to replicate the exact DSP logic (if audio-rate) or mathematical modulation curves (if control-rate) described in the `moddemix` documentation.

### Optimization Constraints & Safety Rails
- **GIL Locking limits:** If implementing DSP in pure Python, NumPy vectorization must be used to process audio buffers chunk-by-chunk to avoid blocking the main 60FPS render loop.

## Test Plan

*   **Logic (Pytest)**: Send zeroed CV signals and verify the internal physics match the resting state of the Moddemix hardware.

## Deliverables
1. `src/vjlive3/plugins/make_noise/moddemix.py`
2. Integrated block in the `MakeNoiseRegistry`
