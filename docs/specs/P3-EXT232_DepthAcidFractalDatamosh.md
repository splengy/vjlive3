# P3-EXT232: Depth Acid Fractal Datamosh Effect

## Description

A chaotic, multi-dimensional psychedelic filter blending Julia Set fractals driven by depth map geometry, prismatic RGB chromatic aberration, Sabattier solarizations, and cross-processed chemical alchemy.

## What This Module Does

This module implements the `DepthAcidFractalDatamoshEffect`, ported from the legacy `VJlive-2/plugins/vdepth/depth_acid_fractal.py` codebase. It represents the height of visual intensity, pushing colors into "impossible neon combinations". The module executes 10 discrete transformation stages inside a monolithic shader perfectly synchronized to audio bands. It effectively replaces standard depth-culling with a mathematical Julia Set bounded by physical depth edges in the real world.

## Public Interface

```python
class DepthAcidFractalDatamoshEffect(EffectNode):
    def __init__(self):
        # 10 Stages initialized: BassThrob, PrismSplit, ZoomBlur, Fractal,
        # Solarize, CrossProcess, FilmBurn, Posterize, NeonBoost, Feedback
        pass
    def process(self, video_frame: np.ndarray, depth_frame: np.ndarray, audio_data: dict) -> np.ndarray:
        # Executes the 10-stage shader pipeline utilizing the frame's DepthMap
        pass
    def _map_param(self, name: str, out_min: float, out_max: float) -> float:
        # Translates internal 0-10 user slider ranges to precise shader constraints
        pass
```

## Inputs and Outputs

*   **Inputs**: RGB Texture (`tex0`), Previous frame texture for temporal mosh (`texPrev`), 32-bit Depth Texture (`depth_tex`), Audio frequency bands (Bass, Mid, Treble).
*   **Outputs**: Heavy datamoshed RGB frame.

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2`
- **File Paths**: `plugins/vdepth/depth_acid_fractal.py`
- **Architectural Soul**: The legacy Python binds explicit FFT bands to precise shader transformations (e.g., Bass->`bassThrob`/`filmBurn`/`prismSplit`, Mid->`fractalIntensity`/`solarize`, Treble->`neonBoost`). Its fragment shader combines film-chemistry manipulation techniques (e.g. converting RGB curves into E-6 in C-41 chemistry equivalent) against physical depth distance (`depth_edge`).

### Key Algorithms
1. **Depth-Bound Julia Set**: Drives the complex parameter `c` of the Julia Set dynamically based on the current physical depth distance, running 64 recursive iterations `z = z^2 + c`.
2. **Sabattier Solarization**: Uses the inverse absolute sine `abs(sin(v * 3.14159 * curves))` mapped specifically against intermediate depth bands to create glowing negative outlines.
3. **Cross-Processing Chemistry Math**: Simulates E-6 in C-41 (boosted greens, crushed blues) or C-41 in E-6 (heavy cyan, blown yellow shadows) completely procedurally depending on the fragment's distance from the camera `fract(depth * 3.0 + time * 0.1)`.
4. **VDepth Anti-Pattern Fix**: **WARNING:** The legacy code executes `glTexImage2D` allocating memory buffers inside the `apply_uniforms` draw loop for `self.depth_texture`.

### Optimization Constraints & Safety Rails
- **Optimization Constraint (Safety Rail #1):** Like all legacy VDepth plugins, the `depth_texture` memory leak in `DepthAcidFractal` MUST be patched. VJLive3 must utilize pre-dimensioned FBOs and strictly use `glTexSubImage2D` or zero-copy PBOs since this effect runs 10 heavy stages in parallel.
- **Explicit Cleanup (Safety Rail #8)**: Legacy uses dangerous Python `__del__` wrapping naked try/except `glDeleteTextures` blocks. VJLive3 requires deterministic `shutdown()` or `release()` methods called by the Graph Manager.
- **Shader Complexity**: Iterating a 64-step Julia set per pixel *on top* of 9 other operations is extremely GPU intensive. Implement an early exit bounds check `if (dot(z,z) > 4.0) break;`.

## Test Plan

*   **Logic (Pytest)**: Ensure the `_map_param` function successfully routes User Interface 0-10 sliders into their designated GL boundaries (e.g., `fractalZoom 0.5-4.0`).
*   **Visual Check**: Test that when `crossProcess` = 10, the near objects are color space 1 (E-6), mid objects are color space 2 (C-41), and far objects simulate IR. Test the Bass Throb reactivity to pulse the overall zoom mathematically.
*   **Performance Constraints**: Benchmark `glTexSubImage2D` integration over long multi-hour test runs to guarantee no VRAM exhaustion.

## Deliverables

1.  Implemented `DepthAcidFractalDatamoshEffect` node adhering to proper `glTexSubImage2D` buffer management inside `src/vjlive3/plugins/depth_acid_fractal.py`.
2.  Ported GLSL shader file (`assets/shaders/vdepth_acid_fractal.frag`).
3.  Unit tests evaluating the bounding mappings and cleanup logic (`tests/plugins/test_depth_acid_fractal.py`).
