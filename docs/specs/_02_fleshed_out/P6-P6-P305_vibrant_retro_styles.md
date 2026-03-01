# P6-P305: vibrant_retro_styles

> **Task ID:** `P6-P305`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/vstyle/vibrant_retro_styles.py`)
> **Class:** `RadiantMeshEffect`
> **Phase:** Phase 6
> **Status:** ⚪ In Progress

## What This Module Does
The `vibrant_retro_styles` plugin implements a retro-style visual effect that creates vibrant, mesh-based patterns with dynamic color modulation. It generates visually complex effects by combining geometric mesh structures with procedural color generation, creating a distinctive retro aesthetic that responds to audio input and time-based animations.

The module produces:
- Real-time mesh-based retro visual patterns
- Dynamic color modulation based on audio input
- Integration with VJLive3's rendering pipeline
- Configurable retro-style effects (e.g., scanlines, color cycling)

## Public Interface
```python
class RadiantMeshEffect(Effect):
    def __init__(self, config: dict):
        # Initialize retro mesh effect with configuration
        super().__init__(config)

    def update(self, frame_data: dict) -> None:
        # Update mesh positions and colors based on audio input
        pass

    def render(self) -> None:
        # Render mesh effect using VJLive3's rendering system
        pass

    def set_parameter(self, name: str, value: any) -> None:
        # Update retro effect parameters dynamically
        pass
```

## Inputs and Outputs
| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | dict | Initial configuration (mesh density, color palette) | Must include `mesh_density`, `color_palette`, `retro_mode` |
| `frame_data` | dict | Input from VJLive3's frame pipeline | Must contain `audio_level`, `time_delta` |
| `mesh_data` | list[dict] | Output containing updated mesh states | Each entry has `position`, `color`, `intensity` |

## Edge Cases and Error Handling
- **Missing audio input**: Falls back to time-based animation if audio input is unavailable
- **Invalid config**: Raises `ValueError` if `mesh_density` < 1 or `color_palette` is empty
- **Resource exhaustion**: Implements mesh culling for particles beyond viewport
- **Color overflow**: Clamps color values to valid RGB range (0-255)

## Dependencies
- `src/vjlive3/plugins/` for base Effect class
- `src/vjlive3/render/` for rendering integration
- `numpy` for mesh geometry calculations
- `pyopencl` (optional) for GPU-accelerated mesh rendering

## Test Plan
| Test Name | What It Verifies |
|-----------|------------------|
| `test_basic_mesh_generation` | Mesh structures generate correctly with default parameters |
| `test_audio_reactivity` | Mesh colors respond to audio input levels |
| `test_retro_modes` | Different retro modes (scanlines, color cycling) work correctly |
| `test_parameter_updates` | Dynamic parameter changes affect mesh behavior |
| `test_performance` | Maintains 60 FPS at 1080p resolution |

**Minimum coverage:** 80% before task completion.

## Verification Checkpoints
- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum
- [ ] Test coverage ≥80%
- [ ] Original functionality verified (side-by-side comparison)
- [ ] No safety rail violations

## Definition of Done
- [ ] Spec reviewed by Manager/User
- [ ] All tests pass
- [ ] File size ≤750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-P305: vibrant_retro_styles - port from vjlive2/plugins/vstyle/vibrant_retro_styles.py`
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg**: Add a hidden parameter `debug_mode` that creates a rainbow mesh trail when enabled
