# P3-EXT001: ASCIIEffect

## Description

A dynamic shader converting the active visual stream or rendering output into a retro, pixelated ASCII-art representation utilizing texture-mapped character gradients.

## What This Module Does

This specification defines the VJLive3 port for the legacy `ascii_effect` component. It operates as an `EffectNode` manipulating the final FragColor output by quantizing resolution and mapping luminance to an ordered ASCII string gradient.

## Public Interface

```python
class ASCIIEffect(EffectNode):
    \"\"\"Transforms video blocks into character maps.\"\"\"
    
    # Core Controls
    character_ramp: str  # e.g., " .:-=+*#%@"
    grid_size: int       # Resolution quantizer (block size)
    color_mode: int      # 0: Monochromatic, 1: Original Color
```

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/core/ascii_effect.py`

### Architectural Soul
Rather than looping over CPU pixels (too slow), the effect leverages a GLSL fragment shader that performs a spatial block-average of the source texture to calculate local luminance, and then `texture2D` samples a pre-compiled monospace font atlas mapping the luminance to the X-coordinate of the atlas.

### Optimization Constraints & Safety Rails
- **Atlas Management:** The character atlas MUST be generated once at initialization utilizing `ImageDraw` and uploaded into a managed PyOpenGL texture ID to avoid frame-by-frame reallocation.

## Test Plan

*   **Logic (Pytest)**: Feed a pure white `[1.0, 1.0, 1.0]` frame and verify it returns the densest character (e.g., `@`). Follow up with pure black yielding the sparsest character (space).

## Deliverables
1. `src/vjlive3/plugins/ascii_effect.py` implemented via `UnifiedShaderManager`.
