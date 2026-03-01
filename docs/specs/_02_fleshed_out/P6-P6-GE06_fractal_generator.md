# Fractal Generator Specification — P6-P6-GE06

**File naming:** `docs/specs/P6-P6-GE06_fractal_generator.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## What This Module Does

Generates mathematically precise fractal patterns using recursive iteration of complex functions. Supports multiple fractal types (Mandelbrot, Julia, Burning Ship, Nova), rendering modes (2D/3D), and produces output suitable for real-time visual applications. The generator implements exact mathematical formulas with specified parameter ranges and constraints.

---

## What It Does NOT Do

- Does not handle file I/O operations or persistent storage
- No audio processing or synchronization capabilities
- Does not implement physics-based simulations
- No direct user input handling

---

## Public Interface

```python
class FractalGenerator:
    def __init__(self, params: FractalParams) -> None: ...
    def generate(self, frame: int, resolution: Vec2) -> FractalOutput: ...
    def set_parameters(self, params: FractalParams) -> None: ...
    def get_parameters(self) -> FractalParams: ...
```

Where:
- `FractalParams` contains all configuration fields with strict type and range constraints
- `FractalOutput` includes the rendered frame data and metadata
- All methods enforce mathematical validity of inputs

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `params.fractal_type` | `str` | Fractal algorithm selector | Must be one of: `"mandelbrot"`, `"julia"`, `"burning_ship"`, `"nova"` |
| `params.c_iter` | `int` | Maximum iteration count | 1 ≤ `c_iter` ≤ 1000 |
| `params.bailout` | `float` | Escape radius threshold | 0.0 < `bailout` ≤ 100.0 |
| `params.offset_x` | `float` | Horizontal translation | -2.0 ≤ `offset_x` ≤ 2.0 |
| `params.offset_y` | `float` | Vertical translation | -2.0 ≤ `offset_y` ≤ 2.0 |
| `params.zoom` | `float` | Scale factor | 0.1 ≤ `zoom` ≤ 100.0 |
| `params.color_mode` | `str` | Color mapping strategy | Must be one of: `"hsv"`, `"rgb"`, `"grayscale"`, `"palette"` |
| `params.palette_id` | `int` | Color palette index | 0 ≤ `palette_id` ≤ 255 |
| `params.animation_offset` | `float` | Temporal offset for animation | 0.0 ≤ `animation_offset` ≤ 10.0 |
| `params.smooth_shading` | `bool` | Enables smooth iteration density | `True` or `False` |
| `params.particle_count` | `int` | Number of particles for particle-based variants | 1 ≤ `particle_count` ≤ 10000 |
| `params.particle_speed` | `float` | Movement speed for particle effects | 0.1 ≤ `particle_speed` ≤ 5.0 |
| `params.render_mode` | `str` | Output format | Must be one of: `"2d"`, `"3d"`, `"depth"`, `"normal"` |

**Output Structure:**
- `frame_data`: `np.ndarray` with shape matching `resolution`
- `metadata`: Dictionary containing generation statistics including:
  - `iteration_count`: `int` - actual iterations performed
  - `escape_radius`: `float` - final radius before escape
  - `convergence`: `float` - measure of convergence quality

---

## Key Features

- **Mathematical Precision**: Implements exact fractal formulas with double-precision floating point arithmetic
- **Recursive Optimization**: Uses iterative algorithms with early termination for performance
- **Multi-type Support**: Four distinct fractal algorithms with configurable parameters
- **Color Systems**: Four color mapping strategies with palette-based and HSV-based options
- **Animation Support**: Temporal parameters for smooth transitions between frames
- **3D Capabilities**: Depth-aware rendering with normal vector calculation
- **Particle Effects**: Optional particle system for enhanced visual complexity

---

## Edge Cases and Error Handling

- **Invalid fractal_type**: Raises `ValueError("Invalid fractal_type: {type}")` with specific message
- **Negative iteration count**: Clamps to minimum of 1, logs warning
- **Zero bailout radius**: Defaults to 2.0 with warning, prevents division by zero
- **Out-of-bounds parameters**: Automatically clamps to valid ranges with warning
- **Memory allocation failure**: Returns empty frame with error flag in metadata
- **Non-convergent sequences**: Marks as unconvergent in metadata without error
- **Invalid resolution**: Raises `ValueError("Resolution must be positive integers")`

---

## Dependencies

- **External Libraries**:
  - `numpy>=1.24.0` for array operations and mathematical functions
  - `scipy>=1.10.0` for advanced mathematical operations (optional for 3D modes)
- **Internal Modules**:
  - `vjlive3.core.math.fractals` - Core fractal calculation utilities
  - `vjlive3.core.math.complex` - Extended complex number operations
  - `vjlive3.core.render.base` - Base rendering functionality
  - `vjlive3.core.utils.validation` - Parameter validation helpers

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_mandelbrot_basic` | Correct pattern generation for standard Mandelbrot set with default parameters |
| `test_julia_set_animation` | Smooth animation between different complex constants for Julia sets |
| `test_burning_ship_3d` | Proper 3D depth calculation and normal vector generation |
| `test_nova_particle_effect` | Correct particle behavior with specified speed and count |
| `test_color_hsv_mapping` | Accurate HSV color space mapping across parameter ranges |
| `test_grayscale_conversion` | Proper luminance-to-grayscale conversion with smooth shading |
| `test_palette_indexing` | Correct palette lookup and application |
| `test_parameter_clamping` | Invalid parameters are clamped to valid ranges with warnings |
| `test_resolution_edge_cases` | Handles minimum (1x1) and maximum supported resolutions |
| `test_convergence_detection` | Correctly identifies convergent vs divergent sequences |
| `test_performance_60fps` | Maintains ≥60 FPS at 1280x720 resolution with default parameters |
| `test_test_coverage` | Achieves ≥80% test coverage as measured by coverage.py |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed and approved by Manager or User
- [ ] All tests pass with ≥80% coverage
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P6-P6-GE06: fractal_generator - complete spec` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: Invent a secret fractal pattern algorithm combining Mandelbrot set with cellular automata rules, and document it in `WORKSPACE/EASTEREGG_COUNCIL.md`

---

## Mathematical Foundations

The fractal generator implements the following core mathematical operations:

1. **Mandelbrot Set**: 
   - Iteration: `zₙ₊₁ = zₙ² + c` where `z₀ = 0` and `c = x + yi`
   - Escape condition: `|zₙ| > bailout`
   - Iteration count determines color mapping

2. **Julia Set**:
   - Fixed constant `c` with variable starting point `z₀`
   - Parameterized by `offset_x`, `offset_y`, and `zoom`

3. **Burning Ship**:
   - Modified iteration: `zₙ₊₁ = (|Re(zₙ)| + i|Im(zₙ)|)² + c`
   - Enhanced detail through absolute value operations

4. **Nova Set**:
   - Higher-order iteration: `zₙ₊₁ = (zₙ^4) + c`
   - More complex boundary behavior

All calculations use double-precision floating point arithmetic to maintain mathematical accuracy. The generator employs adaptive iteration termination to optimize performance while maintaining precision.

---

## Performance Characteristics

- **Time Complexity**: O(`c_iter` × `resolution.width` × `resolution.height`)
- **Space Complexity**: O(`resolution.width` × `resolution.height`) for frame storage
- **GPU Acceleration**: Optional OpenCL support for parallel computation
- **Memory Optimization**: Frame buffering and reuse for animation sequences
- **Scaling**: Linear performance degradation with increased `c_iter` and resolution

---

## Integration Points

- **Input**: Receives parameters from `EffectController` via `set_parameters()`
- **Processing**: Works with `RenderPipeline` for frame generation
- **Output**: Feeds into `Visualizer` for display and `EffectLogger` for metrics
- **Dependencies**: Requires `MathUtils` for complex number operations

---

## Limitations and Known Issues

- 3D rendering mode has higher memory consumption
- Particle effects may impact performance at maximum settings
- Some color palettes may not be perceptually uniform
- Very high zoom levels may introduce floating-point precision artifacts

These limitations are documented for user awareness and future improvement planning.
