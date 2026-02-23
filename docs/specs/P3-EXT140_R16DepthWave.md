# P3-EXT140: R16DepthWave

## Description

A 16-bit high-precision depth routing algorithm designed to generate fluid waves utilizing the raw R16 format from Astra/Kinect.

## What This Module Does

This specification defines the VJLive3 port for the legacy component: `R16DepthWave`. It operates as a deeply integrated module within the spatial computing and quantum visualization engine.

## Public Interface

```python
class R16DepthWave(EffectNode):
    """Legacy virtualization of R16DepthWave."""
    # Standard inputs encompassing time, resolution, and depth fields.
```

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/r16_depth_wave.py`

### Architectural Soul
The engine tracks hyper-dimensional data utilizing spatial coherence buffers.

### Optimization Constraints & Safety Rails
- **Memory Allocation Limits:** To remain zero-allocation, coordinate framebuffers must be initialized once during instantiation and mutated via `glTexSubImage2D` per the VJLive3 spec (Safety Rail #1).

## Test Plan

*   **Logic (Pytest)**: Supply 16-bit depth gradient wedges to ensure spatial translation accuracy across frames.

## Deliverables
1. `src/vjlive3/plugins/vdepth/r16_depth_wave.py` implementation.
