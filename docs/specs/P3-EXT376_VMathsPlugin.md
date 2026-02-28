# P3-EXT376: Make Noise Maths

## Description

A direct software emulation of the hardware Make Noise Maths Eurorack synthesizer module. It translates physical CV (Control Voltage) and audio-rate behavior into the VJLive3 virtual graph, maintaining strict adherence to the Make Noise philosophy.

## What This Module Does

This specification defines the VJLive3 port for the legacy `vmake_noise` ecosystem plugin: `VMathsPlugin`. It behaves as a NodeGraph component handling input/output audio or modulation streams identically to its real-world counterpart.

## Public Interface

```python
class VMathsPlugin(EffectNode):
    """Software virtualization of Make Noise Maths."""
    # Physical knob/jack parameters map 1:1 to Uniforms/Inputs
```

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2` and `vjlive`
- **Software File Paths**: `plugins/core/vmake_noise/vmake_noise.py`
- **Hardware Documentation:**
  - **Manual PDF**: `vjlive/JUNK/manuals_make_noise/maths-manual.pdf`

### Architectural Soul
The module is expected to replicate the exact DSP logic (if audio-rate) or mathematical modulation curves (if control-rate) described in the `maths` documentation.

### Optimization Constraints & Safety Rails
- **GIL Locking limits:** If implementing DSP in pure Python, NumPy vectorization must be used to process audio buffers chunk-by-chunk to avoid blocking the main 60FPS render loop.

## Test Plan

*   **Logic (Pytest)**: Send zeroed CV signals and verify the internal physics match the resting state of the Maths hardware.

## Deliverables
1. `src/vjlive3/plugins/make_noise/maths.py`
2. Integrated block in the `MakeNoiseRegistry`
