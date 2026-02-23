# P3-EXT056 Depth Modular Datamosh Effect

## What This Module Does

Depth Modular Datamosh Effect creates datamosh effects using a modular system where different datamosh modules can be combined and configured based on depth information. This creates complex, customizable datamosh effects where different depth regions can have different datamosh behaviors, allowing for sophisticated glitch art with depth-aware modular processing.

## Public Interface

```python
METADATA = {
    "name": "Depth Modular Datamosh Effect",
    "version": "1.0.0",
    "author": "VJLive3",
    "description": "Creates modular datamosh effects with depth-based configuration",
    "category": "Depth Effects",
    "tags": ["depth", "datamosh", "modular", "glitch", "configurable"],
    "inputs": ["video", "depth"],
    "outputs": ["video"],
    "parameters": {
        "module_count": {
            "type": "integer",
            "min": 1,
            "max": 8,
            "default": 3,
            "description": "Number of datamosh modules"
        },
        "depth_ranges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "min": {"type": "float", "min": 0.0, "max": 1.0},
                    "max": {"type": "float", "min": 0.0, "max": 1.0},
                    "module": {"type": "integer", "min": 0, "max": 7}
                }
            },
            "default": [
                {"min": 0.0, "max": 0.33, "module": 0},
                {"min": 0.33, "max": 0.66, "module": 1},
                {"min": 0.66, "max": 1.0, "module": 2}
            ],
            "description": "Depth ranges and assigned modules"
        },
        "modules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "enum",
                        "options": ["random", "scanline", "block", "pixel_sort", "compression", "feedback", "loop", "echo"],
                        "description": "Type of datamosh module"
                    },
                    "intensity": {"type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
                    "speed": {"type": "float", "min": 0.0, "max": 10.0, "default": 1.0},
                    "color_shift": {"type": "float", "min": -180.0, "max": 180.0, "default": 0.0},
                    "contrast_adjust": {"type": "float", "min": -1.0, "max": 1.0, "default": 0.0},
                    "brightness_adjust": {"type": "float", "min": -1.0, "max": 1.0, "default": 0.0}
                }
            },
            "default": [
                {"type": "random", "intensity": 0.5, "speed": 1.0},
                {"type": "scanline", "intensity": 0.4, "speed": 1.5},
                {"type": "block", "intensity": 0.6, "speed": 0.8}
            ],
            "description": "Configuration for each datamosh module"
        },
        "global_intensity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.7,
            "description": "Overall intensity of all modules"
        },
        "transition_speed": {
            "type": "float",
            "min": 0.0,
            "max": 10.0,
            "default": 1.0,
            "description": "Speed of transitions between modules"
        },
        "motion_sensitivity": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.5,
            "description": "Sensitivity to motion in datamosh"
        },
        "feedback_amount": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "default": 0.2,
            "description": "Amount of feedback in modular system"
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
            "description": "Random seed for module patterns"
        }
    }
}
```

## What It Does NOT Do

- Does not generate depth from 2D video (requires depth input)
- Does not perform audio-reactive modular timing
- Does not support external module sources
- Does not handle infinite recursion (limited by feedback)

## Test Plan

1. **Module Count Tests:**
   - Test with single module (simple datamosh)
   - Test with maximum 8 modules
   - Test with different module counts

2. **Depth Range Tests:**
   - Test with different depth range configurations
   - Test with overlapping depth ranges
   - Test with non-overlapping depth ranges
   - Test with edge depth ranges

3. **Module Configuration Tests:**
   - Test different module types
   - Test different module intensities
   - Test different module speeds
   - Test different module color shifts

4. **Global Intensity Tests:**
   - Test with zero global intensity (no effect)
   - Test with maximum global intensity (full effect)
   - Test with different global intensities

5. **Transition Tests:**
   - Test with slow transitions
   - Test with fast transitions
   - Test with maximum transition speed

6. **Feedback Tests:**
   - Test with no feedback
   - Test with different feedback amounts
   - Test with different feedback modes

7. **Performance Tests:**
   - Measure FPS with different module counts
   - Test with various resolutions
   - Verify memory usage with multiple modules

8. **Quality Tests:**
   - Check for visual artifacts
   - Verify smooth module transitions
   - Test with moving objects
   - Test with static scenes

## Implementation Notes

- Use modular architecture for datamosh processing
- Implement efficient depth-based module routing
- Support real-time parameter adjustment
- Provide module preview mode
- Include depth visualization for debugging

## Deliverables

- `src/vjlive3/plugins/depth_modular_datamosh.py` - Main plugin implementation
- `tests/plugins/test_depth_modular_datamosh.py` - Comprehensive test suite
- `docs/plugins/depth_modular_datamosh.md` - User documentation
- `shaders/depth_modular_datamosh.glsl` - GPU shader for modular processing

## Success Criteria

- ✅ Modular datamosh system with depth-based configuration
- ✅ Multiple datamosh modules with configurable parameters
- ✅ Real-time performance with minimal FPS impact
- ✅ Configurable depth ranges and module routing
- ✅ Various feedback and transition options
- ✅ No visual artifacts or glitches
- ✅ Comprehensive test coverage (≥80%)
- ✅ Complete documentation with examples
- ✅ Passes all safety rails