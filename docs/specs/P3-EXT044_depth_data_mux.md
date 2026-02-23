# P3-EXT044: Depth Data Mux Effect

## What This Module Does
Implements a depth-based data multiplexer that can route, combine, or switch between multiple depth sources or processing paths. Allows for complex depth manipulation by selecting different depth processing strategies based on conditions or mixing multiple depth streams. Useful for creating hybrid depth effects or managing multiple depth inputs.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthDataMux",
    "version": "3.0.0",
    "description": "Multiplex and route depth data",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "utility",
    "tags": ["depth", "mux", "multiplexer", "routing"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `mux_mode: str` (default: "select", options: ["select", "blend", "switch", "conditional"]) - Multiplexing mode
- `depth_sources: list[str]` (default: []) - Source depth inputs (from other plugins or buffers)
- `active_source: int` (default: 0, min: 0, max: 3) - Which source to use when mode="select"
- `blend_weights: list[float]` (default: []) - Weights for blending sources (mode="blend")
- `switch_condition: str` (default: "depth_range", options: ["depth_range", "time", "beat", "custom"]) - When to switch
- `switch_threshold: float` (default: 0.5, min: 0.0, max: 1.0) - Threshold for switching
- `conditional_rules: dict` (default: {}) - Custom conditions for mode="conditional"
- `default_depth: float` (default: 0.5, min: 0.0, max: 1.0) - Fallback depth value

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Primary depth buffer
- `depth_secondary: Frame` (optional) - Secondary depth source for blending
- `depth_tertiary: Frame` (optional) - Tertiary depth source
- `depth_quaternary: Frame` (optional) - Quaternary depth source
- `timestamp: float` (optional) - Current time for time-based switching
- `beat_phase: float` (optional) - Beat phase for beat-based switching

### Outputs
- `video: Frame` (same format as input) - Processed video frame
- `depth_output: Frame` (optional) - Multiplexed depth buffer

## What It Does NOT Do
- Does NOT generate depth data (only routes/processes existing depth)
- Does NOT perform depth estimation or inference
- Does NOT support more than 4 depth sources (hard limit)
- Does NOT include depth enhancement or filtering (pure routing)
- Does NOT handle HDR metadata preservation
- Does NOT support dynamic source addition/removal at runtime

## Test Plan
1. Unit tests for each mux_mode
2. Verify depth source selection and blending
3. Test switch_condition logic
4. Performance: ≥ 60 FPS at 1080p
5. Memory: < 50MB additional RAM
6. Integration: verify depth_output matches expected routing

## Implementation Notes
- For mode="select": output = depth_sources[active_source]
- For mode="blend": output = weighted sum of depth_sources using blend_weights
- For mode="switch": monitor switch_condition and toggle between sources
- For mode="conditional": evaluate conditional_rules to select source
- Sources can be other plugin outputs or internal buffers
- If a source is None, use default_depth
- Optimize with minimal copying; use views where possible
- Follow SAFETY_RAILS: validate source indices, handle missing inputs

## Deliverables
- `src/vjlive3/effects/depth_data_mux.py`
- `tests/effects/test_depth_data_mux.py`
- `docs/plugins/depth_data_mux.md`

## Success Criteria
- [x] Plugin loads via METADATA
- [x] All mux modes work correctly
- [x] Depth routing functions as expected
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations