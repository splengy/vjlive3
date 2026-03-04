# P5-DM16: datamosh_3d
> **Task ID:** `P5-DM16`  
> **Priority:** P0 (Critical)  
> **Source:** VJlive-2 (`plugins/vdatamosh/datamosh_3d.py`)  
> **Class:** `Datamosh3DEffect`  
> **Phase:** Phase 5  
> **Status:** ⬜ Todo  

## Mission Context
Port the `Datamosh3DEffect` effect from `VJlive-2` codebase into VJLive3's clean architecture. This plugin is part of the Datamosh collection and is essential for complete feature parity.

## Technical Requirements
- Implement as a VJLive3 plugin following the manifest-based registry system
- Inherit from appropriate base class (`Effect` or specialized depth/audio base)
- Ensure 60 FPS performance (Safety Rail 1)
- Achieve ≥80% test coverage (Safety Rail 5)
- File size ≤750 lines (Safety Rail 4)
- No silent failures, proper error handling (Safety Rail 7)

## Implementation Notes
**Original Location:** `VJlive-2/plugins/vdatamosh/datamosh_3d.py`  
**Description:** Depth-driven pixel sorting and smearing effect using optical flow simulation based on depth gradients.

### Porting Strategy
1. Analyze the legacy implementation to extract mathematical parameters and logic
2. Map parameters to VJLive3's plugin architecture using `src/vjlive3/plugins/`
3. Create proper class inheritance from `Effect` base class
4. Implement parameter validation and error handling
5. Write comprehensive tests (≥80% coverage)
6. Verify against original behavior with test vectors
7. Document any deviations or improvements

## Public Interface
```python
class Datamosh3DEffect(Effect):
    """
    Datamosh 3D: Depth-driven pixel sorting and smearing.
    Uses depth map gradients to drive optical flow simulation.
    """
    
    def __init__(self, width: int = 1920, height: int = 1080):
        """
        Initialize the Datamosh3DEffect.
        
        Args:
            width: Output width in pixels (default: 1920)
            height: Output height in pixels (default: 1080)
        """
        super().__init__("Datamosh 3D", DATAMOSH_3D_FRAGMENT, BASE_VERTEX_SHADER)
        
        # Agent Metadata
        self.effect_category = "glitch"
        self.effect_tags = ["depth", "datamosh", "distortion", "feedback"]
        self.features = ["DEPTH_AWARE", "FEEDBACK_LOOP"]
        self.usage_tags = ["REQUIRES_DEPTH"]

        # Parameter ranges (0.0-10.0)
        self._parameter_ranges = {
            'flow_strength': (0.0, 10.0),
            'depth_threshold': (0.0, 10.0),
            'decay': (0.0, 10.0),
            'noise_amount': (0.0, 10.0),
            'u_mix': (0.0, 10.0)
        }
        
        # Default parameter values
        self.parameters = {
            'flow_strength': 5.0,
            'depth_threshold': 2.0,
            'decay': 9.0,
            'noise_amount': 1.0,
            'u_mix': 10.0
        }
        
        # Parameter descriptions
        self._parameter_descriptions = {
            'flow_strength': "Intensity of depth-driven displacement",
            'depth_threshold': "Sensitivity to depth edges for pixel refresh",
            'decay': "Feedback persistence (0=instant fade, 10=infinite)",
            'noise_amount': "Random chaotic displacement",
            'u_mix': "Mix factor for blending operations"
        }
        
        # Sweet spot values for optimal visual effects
        self._sweet_spots = {
            'flow_strength': [2.0, 5.0, 8.0],
            'decay': [9.0, 9.8],
            'depth_threshold': [1.5]
        }

    def render(self, tex_in: int, extra_textures: list = None, chain=None) -> int:
        """
        Custom render to handle texDepth binding and optical flow calculation.
        
        Args:
            tex_in: Input texture (current video frame) handle
            extra_textures: Additional textures including depth map (texDepth)
            chain: Rendering chain context
            
        Returns:
            Processed texture handle
        """
        # Implementation details follow

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor=None, semantic_layer=None):
        """
        Apply shader uniforms with proper parameter validation.
        
        Args:
            time: Current time in seconds
            resolution: Tuple of (width, height)
            audio_reactor: Optional audio input for parameter modulation
            semantic_layer: Optional semantic layer input
        """
        # Implementation details follow

## Inputs and Outputs
| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `tex_in` | `int` (texture handle) | Current video frame texture | Must be valid OpenGL texture |
| `extra_textures` | `list` of `int` | Additional textures including depth map | Must contain at least one depth texture |
| `chain` | `object` | Rendering chain context | May be None |
| `flow_strength` | `float` (0.0-10.0) | Intensity of depth-driven displacement | Range: 0.0-10.0 |
| `depth_threshold` | `float` (0.0-10.0) | Sensitivity to depth edges | Range: 0.0-10.0 |
| `decay` | `float` (0.0-10.0) | Feedback persistence | Range: 0.0-10.0 |
| `noise_amount` | `float` (0.0-10.0) | Random chaotic displacement | Range: 0.0-10.0 |
| `u_mix` | `float` (0.0-10.0) | Mix factor for blending operations | Range: 0.0-10.0 |

## Edge Cases and Error Handling
- **Hardware Absence**: If depth texture unavailable, fallback to color-based flow with graceful degradation
- **Invalid Parameters**: Validate all parameters against `_parameter_ranges`; clamp invalid values
- **Division by Zero**: Protect against depth gradient calculations with zero denominators
- **Memory Limits**: Monitor texture memory usage; implement streaming for large resolutions
- **Silent Failures**: All error conditions must raise explicit exceptions or return error codes

## Dependencies
- **External Libraries**: 
  - `numpy` for array operations and pixel processing
  - `PyOpenGL` for OpenGL shader operations
- **Internal Modules**:
  - `src/vjlive3/plugins/Effect.py` (base Effect class)
  - `src/vjlive3/render/ShaderBase.py` (shader compilation utilities)
  - `src/vjlive3/plugins/` (plugin registry system)

## Test Plan
| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware (GPU) is absent or unavailable |
| `test_basic_operation` | Core rendering function produces valid output when given clean input frame |
| `test_parameter_range_validation` | All parameter inputs are clamped to 0.0–10.0 range and rejected outside bounds |
| `test_color_mode_switching` | Switching between color modes changes output appearance correctly |
| `test_scroll_rain_effect` | Matrix rain animation moves at correct speed and density based on scroll_speed and rain_density |
| `test_crt_effects` | Scanlines, flicker, and phosphor glow are visible and proportional to input values |
| `test_edge_detection_and_detail_boost` | Edge detection and detail boost improve character clarity in low-contrast scenes |
| `test_parameter_set_get_cycle` | Dynamic parameter updates via set/get methods reflect real-time changes in output |
| `test_grayscale_input_handling` | Input in grayscale is correctly interpreted for luminance-based ASCII mapping |
| `test_invalid_frame_size` | Invalid frame sizes (e.g., <64x64) raise appropriate exceptions without crashing |
| `test_legacy_compatibility` | Output matches expected visual characteristics of legacy implementations |
| `test_performance_60fps` | Maintains ≥60 FPS at 1080p resolution under typical load |
| `test_coverage_80` | Achieves ≥80% test coverage as measured by coverage.py |

**Minimum coverage:** 80% before task is marked done.

## Verification Checkpoints
- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum
- [ ] Test coverage ≥80%
- [ ] No safety rail violations
- [ ] Original functionality verified (side-by-side comparison)

## Resources
- Original source: `VJlive-2/plugins/vdatamosh/datamosh_3d.py`
- Audit report: `docs/audit_report_comprehensive.json`
- Plugin system spec: `docs/specs/P1-P1_plugin_registry.md` (or appropriate)
- Base classes: `src/vjlive3/plugins/`, `src/vjlive3/render/`

## Dependencies
- [x] List any dependencies on other plugins or systems
  - Depends on `Effect` base class from `src/vjlive3/plugins/`
  - Requires depth texture input via `extra_textures` parameter
  - Uses `ShaderBase` for shader compilation
