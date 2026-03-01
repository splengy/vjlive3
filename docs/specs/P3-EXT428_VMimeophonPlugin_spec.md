# P3-EXT428: Make Noise Mimeophon

## Description

A direct software emulation of the hardware Make Noise Mimeophon Eurorack synthesizer module. Stereo multi-zone color audio repeater bridging delay, chorus, and flange.

## What This Module Does

This specification defines the VJLive3 port for the legacy `vmake_noise` ecosystem plugin: `VMimeophonPlugin`. It behaves as a NodeGraph component handling input/output audio or modulation streams identically to its real-world counterpart.

## Public Interface

```python
class VMimeophonPlugin(EffectNode):
    """Software virtualization of Make Noise Mimeophon."""
    # Physical knob/jack parameters map 1:1 to Uniforms/Inputs
```

## Implementation Notes

### Legacy References
- **Source Codebase**: `vjlive`
- **Hardware Documentation:**
  - **Manual PDF**: `vjlive/JUNK/manuals_make_noise/MNmanuals/mimeophon-manual.pdf`

### Architectural Soul
The module is expected to replicate the exact DSP logic (if audio-rate) or mathematical modulation curves (if control-rate) described in the `mimeophon` documentation.

### Optimization Constraints & Safety Rails
- **GIL Locking limits:** If implementing DSP in pure Python, NumPy vectorization must be used to process audio buffers chunk-by-chunk to avoid blocking the main 60FPS render loop.

## Test Plan

*   **Logic (Pytest)**: Send zeroed CV signals and verify the internal physics match the resting state of the Mimeophon hardware.

## Deliverables
1. `src/vjlive3/plugins/make_noise/mimeophon.py`
2. Integrated block in the `MakeNoiseRegistry`
