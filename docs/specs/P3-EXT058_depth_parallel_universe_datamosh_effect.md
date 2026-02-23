# P3-EXT058 Depth Parallel Universe Datamosh Effect

## What This Module Does

Depth Parallel Universe Datamosh Effect creates complex datamosh effects that simulate multiple parallel universes or dimensions overlapping and interfering with each other, with depth information controlling which universe dominates at different depths. This creates surreal, multi-layered visual effects where different depth planes show different "parallel" versions of the video, creating a sense of dimensional rift and reality fragmentation.

## Public Interface

```python
METADATA = {
    "name": "Depth Parallel Universe Datamosh Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Creates multi-dimensional datamosh effects with depth-based universe selection",
    "category": "Depth Effects",
    "tags": ["depth", "datamosh", "parallel", "universe", "multidimensional"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "universe_count": {
            "type": "integer",
            "min": 2,
            "max": 8,
            "default": 4,
            "description": "Number of parallel universes"
        },
        "universe_mode": {
            "type": "enum",
            "options": ["split", "blend", "interfere", "sequence", "random"],
            "default": "blend",
            "description": "How universes are combined"
        },
        "depth_mapping": {
            "type": "enum",
            "options": ["linear", "exponential", "logarithmic", "squared", "cubic", "random"],
            "default": "linear",
            "description": "How depth maps to universe selection"
        },
        "universe_intensities": {
            "type": "array",
            "items": {"type": "float", "min": 0.0, "max": 1.0},
            "default": [1.0, 0.8, 0.6, 0.4],
            "description": "Intensity for each universe"
        },
        "universe_datamosh": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "intensity": {"type": "float", "min": 0.0, "max": 1.0},
                    "speed": {"type": "float", "min": 0.0, "max": 10.0},
                    "color_shift": {"type": "float", "min": -180.0, "max": 180.0}
                }
            },
            "default": [
                {"type": "random", "intensity": 0.5, "speed": 1.0, "color_shift": 0.0},
                {"type": "scanline", "intensity": 0.4, "speed": 1.5, "color_shift": 30.0},
                {"type": "block", "intensity": 0.6, "speed": 0.8, "color_shift": 60.0},
                {"type": "pixel_sort", "intensity": 0.5, "speed": 2.0, "color_shift": 90.0}
            ],
            "description": "Datamosh configuration for each universe"
        },
        "interference_strength": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Strength of interference between universes"
        },
        "interference_pattern": {
            "type": "enum",
            "options": ["wave", "noise", "grid", "fractal", "random"],
            "default": "wave",
            "description": "Pattern of interference between universes"
        },
        "transition_smoothness": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.3,
            "description": "Smoothness of transitions between universes"
        },
        "global_intensity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.7,
            "description": "Overall intensity of parallel universe effect"
        },
        "depth_response": {
            "type": "enum",
            "options": ["linear", "exponential", "logarithmic", "squared", "cubic"],
            "default": "linear",
            "description": "How depth affects universe selection"
        },
        "depth_exponent": {
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "default": 1.0,
            "description": "Exponent for depth response curve"
        },
        "motion_sensitivity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Sensitivity to motion in universe switching"
        },
        "feedback_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Amount of feedback between universes"
        },
        "feedback_mode": {
            "type": "enum",
            "options": ["additive", "multiply", "screen", "difference", "xor"],
            "default": "additive",
            "description": "Blending mode for feedback"
        },
        "seed": {
            "type": "integer",
            "min": 0,
            "max": 1000000,
            "default": 42,
            "description": "Random seed for universe patterns"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform audio-reactive universe switching
- Does not support external universe sources
- Does not handle infinite recursion (limited by feedback)

## Test Plan

1. **Universe Count Tests:**
   - Test with minimum 2 universes
   - Test with maximum 8 universes
   - Test with different universe counts

2. **Universe Mode Tests:**
   - Test split mode (separate universes per depth)
   - Test blend mode (mixed universes)
   - Test interfere mode (universe interference)
   - Test sequence mode (temporal switching)
   - Test random mode (random selection)

3. **Depth Mapping Tests:**
   - Test linear depth mapping
   - Test exponential depth mapping
   - Test logarithmic depth mapping
   - Test different depth exponents

4. **Universe Configuration Tests:**
   - Test different universe intensities
   - Test different datamosh types per universe
   - Test different datamosh parameters per universe
   - Test with invalid configurations (fallback behavior)

5. **Interference Tests:**
   - Test with no interference
   - Test with different interference strengths
   - Test with different interference patterns

6. **Transition Tests:**
   - Test with sharp transitions (0.0)
   - Test with smooth transitions (1.0)
   - Test with different transition smoothness

7. **Feedback Tests:**
   - Test with no feedback
   - Test with different feedback amounts
   - Test with different feedback modes

8. **Performance Tests:**
   - Measure FPS with different universe counts
   - Test with various resolutions
   - Verify memory usage with multiple universes

9. **Quality Tests:**
   - Check for visual artifacts
   - Verify smooth universe transitions
   - Test with moving objects
   - Test with static scenes

## Implementation Notes

- Use modular architecture for universe management
- Implement efficient depth-based universe routing
- Support real-time parameter adjustment
- Provide universe preview mode
- Include depth visualization for debugging

## Deliverables

- `src/vjlive3/plugins/depth_parallel_universe_datamosh.py` - Main plugin implementation
- `tests/plugins/test_depth_parallel_universe_datamosh.py` - Comprehensive test suite
- `docs/plugins/depth_parallel_universe_datamosh.md` - User documentation
- `shaders/depth_parallel_universe_datamosh.glsl` - GPU shader for universe processing

## Success Criteria

- ✅ Multi-universe datamosh system with depth-based selection
- ✅ Multiple universe modes and interference patterns
- ✅ Real-time performance with minimal FPS impact
- ✅ Configurable universe parameters and transitions
- ✅ Various feedback and blending options
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails