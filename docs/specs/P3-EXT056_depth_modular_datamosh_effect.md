# P3-EXT056: Depth Modular Datamosh Effect

## What This Module Does
Provides a modular datamosh framework where different datamosh algorithms can be combined and configured. Uses depth information to control which modules are active and their parameters. Allows for customizable datamosh patterns by assembling different processing modules.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthModularDatamosh",
    "version": "3.0.0",
    "description": "Modular datamosh with depth-controlled modules",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "datamosh",
    "tags": ["depth", "datamosh", "modular", "configurable"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `active_modules: list[str]` (default: ["block_copy", "color_shift"]) - Which modules to enable
- `module_params: dict` (default: {}) - Parameters for each module
- `depth_thresholds: dict` (default: {}) - Depth thresholds for module activation
- `fallback_module: str` (default: "none") - Module to use when no thresholds met
- `processing_order: list[str]` (default: []) - Order to apply modules (defaults to active_modules)
- `enable_depth_gating: bool` (default: True) - Use depth to gate modules
- `global_intensity: float` (default: 1.0, min: 0.0, max: 2.0) - Overall effect strength

### Available Modules
- `block_copy`: Copy macroblocks from previous frames
- `color_shift`: Apply chromatic aberration
- `pixel_sort`: Sort pixels within blocks
- `edge_datamosh`: Datamosh only on depth edges
- `glitch_inject`: Add random glitches
- `temporal_blend`: Blend with previous frames

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)
- `previous_frames: list[Frame]` (optional) - Frame history for modules

### Outputs
- `video: Frame` (same format as input) - Modularly datamoshed video

## What It Does NOT Do
- Does NOT include all possible datamosh modules (limited to listed ones)
- Does NOT support custom module development at runtime
- Does NOT perform automatic module optimization
- Does NOT handle HDR metadata preservation
- Does NOT include module-specific parameter validation
- Does NOT support hot-swapping modules mid-stream

## Test Plan
1. Unit tests for module loading and initialization
2. Verify each module produces expected output
3. Test depth gating and threshold logic
4. Performance: ≥ 60 FPS at 1080p with 3 active modules
5. Memory: < 200MB additional RAM (module buffers)
6. Integration: verify module combinations work correctly

## Implementation Notes
- Define module interface: `process(frame, depth, params, context) -> frame`
- Load enabled modules from active_modules list
- For each module in processing_order (or active_modules if not specified):
  - Check if module should run based on depth_thresholds if enable_depth_gating
  - Call module's process function with frame, depth, module_params[module]
  - Update frame with module output
  - Update context (e.g., frame history) for next module
- If no module activates and fallback_module is set, apply fallback
- Apply global_intensity as final blend with original
- Provide sensible defaults for all module parameters
- Optimize by sharing buffers between modules
- Follow SAFETY_RAILS: validate module names, handle errors

## Deliverables
- `src/vjlive3/effects/depth_modular_datamosh.py`
- `tests/effects/test_depth_modular_datamosh.py`
- `docs/plugins/depth_modular_datamosh.md`
- Module implementations: `src/vjlive3/effects/modules/` (block_copy, color_shift, etc.)

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Modules load and execute in order
- [x] Depth gating works correctly
- [x] 60 FPS at 1080p with 3 modules
- [x] Test coverage ≥ 80%
- [x] No safety rail violations