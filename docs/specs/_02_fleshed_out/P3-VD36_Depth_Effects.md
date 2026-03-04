# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD36_Depth_Effects.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD36 — Depth Effects Module

## Description

The Depth Effects module is a comprehensive collection of GPU-accelerated visual effects that process depth camera data. It provides a unified framework for depth-based image manipulation, visualization, and glitch effects. The module includes a base class (`DepthEffect`) and numerous specialized effects that inherit from it, forming a cohesive ecosystem for depth-aware VJ performances.

This module is the primary interface for all depth-related visual processing in VJLive3, supporting effects ranging from basic depth visualization to advanced datamosh, color grading, and 3D reconstruction techniques.

## What This Module Does

- Provides the `DepthEffect` base class for all depth-aware effects
- Implements common depth source management and texture handling
- Exports a comprehensive set of depth effect classes:
  - **Visualization**: `DepthPointCloudEffect`, `DepthMeshEffect`, `DepthContourEffect`
  - **Color & Grading**: `DepthColorGradeEffect`, `DepthHolographicIridescenceEffect`
  - **Filtering & Blur**: `DepthBlurEffect`, `DepthFogEffect`, `DepthDistanceFilterEffect`
  - **Edge & Glow**: `DepthEdgeGlowEffect`
  - **Datamosh**: `DepthContourDatamoshEffect`, `DepthModulatedDatamoshEffect`, `DepthFractureDatamoshEffect`, `DepthTemporalStratEffect`, `DepthSlitScanDatamoshEffect`, `DepthGroovyDatamoshEffect`, `DepthRaverDatamoshEffect`, `DepthVoidDatamoshEffect`, `DepthAcidFractalDatamoshEffect`
  - **Dual-Camera**: `DepthDualEffect`, `DepthCameraSplitterEffect`
  - **Simulation**: `DepthSimulatorEffect`, `DepthReverbEffect`
  - **Utility**: `DepthDistanceFilterEffect`, `DepthCameraSplitterEffect`, `DepthDataMuxEffect`, `DepthFXLoopEffect`
- Manages depth texture lifecycle across all effects
- Provides standardized depth normalization and transformation utilities
- Integrates with the plugin system for dynamic loading

## What This Module Does NOT Do

- Does NOT implement depth camera drivers (relies on `AstraDepthSource` interface)
- Does NOT perform 3D reconstruction beyond point clouds and meshes
- Does NOT handle audio analysis (audio reactivity is added by individual effects)
- Does NOT manage node graph routing (that's the pipeline's job)
- Does NOT provide CPU fallbacks (all effects are GPU-accelerated)
- Does NOT store persistent state across sessions

---

## Module Structure

### Base Class Implementation
```python
import numpy as np
from OpenGL.GL import *
from core.effects.shader_base import Effect
from core.sources.depth_source import AstraDepthSource


class DepthEffect(Effect):
    """
    Base class for all depth-based effects.
    
    Provides common functionality for depth texture management,
    normalization, and transformation. All depth effects should
    inherit from this class.
    """
    
    # Default depth range (in meters) for normalization
    DEFAULT_NEAR = 0.1
    DEFAULT_FAR = 10.0
    
    def __init__(self, name: str, fragment_shader: str):
        """
        Initialize the depth effect.
        
        Args:
            name: Human-readable effect name
            fragment_shader: GLSL fragment shader source code
        """
        super().__init__(name, fragment_shader)
        
        # Depth source (set via set_depth_source)
        self._depth_source = None
        
        # Depth texture (managed by base class)
        self._depth_texture = None
        
        # Depth normalization parameters
        self._near_clip = self.DEFAULT_NEAR
        self._far_clip = self.DEFAULT_FAR
        self._depth_scale = 1.0
        self._invert_depth = False
        
        # Frame dimensions
        self._frame_width = 640
        self._frame_height = 480
        
        # Initialize parameters dict
        self.parameters = {
            'depth_strength': 1.0,
            'threshold': 0.0,
            'smoothing': 0.0,
            'edge_enhance': 0.0,
            'blend': 1.0,
            'feedback': 0.0
        }
    
    def set_depth_source(self, source: AstraDepthSource) -> None:
        """
        Set the depth source for this effect.
        
        Args:
            source: An object implementing the AstraDepthSource interface
        """
        self._depth_source = source
    
    def update_depth_data(self) -> bool:
        """
        Fetch fresh depth data from the source and update the depth texture.
        
        Returns:
            True if depth data was updated successfully, False otherwise
        """
        if not self._depth_source:
            raise RuntimeError("No depth source set")
        
        # Get depth frame from source
        depth_frame = self._depth_source.get_depth_frame()
        if depth_frame is None:
            return False
        
        # Normalize depth to [0, 1] range
        depth_normalized = self.normalize_depth(depth_frame)
        
        # Apply optional transformations
        depth_transformed = self.apply_depth_transform(depth_normalized)
        
        # Upload to GPU texture
        self._upload_depth_texture(depth_transformed)
        
        return True
    
    def normalize_depth(self, depth: np.ndarray) -> np.ndarray:
        """
        Convert raw depth values to normalized [0, 1] range.
        
        Args:
            depth: Raw depth array (in meters or arbitrary units)
            
        Returns:
            Normalized depth array in [0, 1]
        """
        # Clip to near/far planes
        depth_clipped = np.clip(depth, self._near_clip, self._far_clip)
        
        # Normalize to [0, 1]
        normalized = (depth_clipped - self._near_clip) / (self._far_clip - self._near_clip)
        
        # Invert if needed
        if self._invert_depth:
            normalized = 1.0 - normalized
        
        return normalized.astype(np.float32)
    
    def apply_depth_transform(self, depth: np.ndarray) -> np.ndarray:
        """
        Apply additional transformations to normalized depth.
        Override this in subclasses for custom processing.
        
        Args:
            depth: Normalized depth array [0, 1]
            
        Returns:
            Transformed depth array
        """
        return depth
    
    def get_depth_texture(self) -> int:
        """
        Get the OpenGL texture ID for the current depth data.
        
        Returns:
            OpenGL texture ID (uint)
        """
        return self._depth_texture
    
    def _upload_depth_texture(self, depth: np.ndarray):
        """Upload depth array to GPU texture."""
        if self._depth_texture is None:
            self._depth_texture = glGenTextures(1)
        
        glBindTexture(GL_TEXTURE_2D, self._depth_texture)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_R32F,
            depth.shape[1], depth.shape[0], 0,
            GL_RED, GL_FLOAT, depth
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    
    def apply_uniforms(self, time: float, resolution: tuple):
        """Upload all uniforms including depth-specific ones."""
        super().apply_uniforms(time, resolution)
        
        # Depth uniforms
        self.set_uniform('u_depth_texture', self._depth_texture)
        self.set_uniform('u_near_clip', self._near_clip)
        self.set_uniform('u_far_clip', self._far_clip)
        self.set_uniform('u_depth_scale', self._depth_scale)
        self.set_uniform('u_invert_depth', int(self._invert_depth))
        self.set_uniform('u_frame_width', self._frame_width)
        self.set_uniform('u_frame_height', self._frame_height)
        
        # Effect parameters
        for param in ['depth_strength', 'threshold', 'smoothing',
                     'edge_enhance', 'blend', 'feedback']:
            self.set_uniform(param, self.parameters[param])
    
    def set_parameter(self, name: str, value: Any) -> None:
        """Set parameter with validation."""
        # Validate numeric ranges
        if name in ['depth_strength', 'blend', 'feedback']:
            value = max(0.0, min(1.0, value))
        elif name in ['threshold', 'smoothing', 'edge_enhance']:
            value = max(0.0, min(1.0, value))
        
        self.parameters[name] = value
    
    def cleanup(self):
        """Release GPU resources."""
        if self._depth_texture:
            glDeleteTextures([self._depth_texture])
            self._depth_texture = None
        super().cleanup()
```

### Effect Categories

1. **Point Cloud & Mesh** (`DepthPointCloudEffect`, `DepthMeshEffect`)
   - 3D point cloud generation from depth maps
   - Mesh reconstruction and rendering
   - Requires projection/view/model matrices

2. **Contour & Edge** (`DepthContourEffect`, `DepthEdgeGlowEffect`)
   - Iso-depth contour line extraction
   - Edge detection with neon glow
   - Multi-scale Sobel operators

3. **Color Grading** (`DepthColorGradeEffect`, `DepthHolographicIridescenceEffect`)
   - 3-zone depth-based color correction
   - Holographic interference patterns
   - Per-zone hue, saturation, temperature, exposure

4. **Datamosh Family** (9+ effects)
   - Contour-based datamosh
   - Modulated datamosh
   - Fracture datamosh
   - Temporal stratification
   - Slit-scan datamosh
   - Groovy, Raver, Void, Acid Fractal variants

5. **Dual Camera** (`DepthDualEffect`, `DepthCameraSplitterEffect`)
   - Two-depth-source combination (6 modes)
   - Split depth camera into 4 streams (RGB, depth, IR, colorized)

6. **Atmospheric** (`DepthFogEffect`, `DepthBlurEffect`)
   - Depth-based fog simulation
   - Depth-of-field blur

7. **Filtering** (`DepthDistanceFilterEffect`)
   - Near/far clipping with soft edges
   - Multiple fill modes (transparent, color, blur, secondary)

8. **Simulation** (`DepthSimulatorEffect`, `DepthReverbEffect`)
   - Simulated depth from 2D video
   - Depth-based reverb/echo

9. **Utility** (`DepthDataMuxEffect`, `DepthFXLoopEffect`)
   - Data multiplexing
   - FX loop recording

---

## Public Interface (Module Level)

```python
# Import all depth effects
from plugins.vdepth import (
    DepthEffect,
    DepthPointCloudEffect,
    DepthPointCloud3DEffect,
    DepthMeshEffect,
    DepthContourEffect,
    DepthParticle3DEffect,
    DepthDistortionEffect,
    DepthFieldEffect,
    DepthParticleShredEffect,
    DepthTemporalEchoEffect,
    DepthMotionTransferEffect,
    DepthMosaicEffect,
    DepthLiquidRefractionEffect,
    DepthPortalCompositeEffect,
    DepthVideoProjectionEffect,
    DepthSliceEffect,
    DepthAwareCompressionEffect,
    DepthModulatedDatamoshEffect,
    DepthFractureDatamoshEffect,
    DepthTemporalStratEffect,
    DepthSlitScanDatamoshEffect,
    DepthGroovyDatamoshEffect,
    DepthRaverDatamoshEffect,
    DepthVoidDatamoshEffect,
    DepthAcidFractalDatamoshEffect,
    DepthHolographicIridescenceEffect,
    DepthReverbEffect,
    DepthDistanceFilterEffect,
    DepthFogEffect,
    DepthBlurEffect,
    DepthEdgeGlowEffect,
    DepthColorGradeEffect,
    DepthDualEffect,
    DepthSimulatorEffect,
    DepthCameraSplitterEffect,
    DepthFXLoopEffect,
    DepthModularDatamoshEffect,
    DepthDataMuxEffect,
)

# Plugin registration
def get_plugin_class() -> Type[Effect]:
    """Return the plugin class for dynamic loading."""
    return DepthEffect  # Actually returns a dict of all effects
```

---

## Dependencies

### External
- `numpy` — Array operations
- `OpenGL` — GPU rendering
- `PIL` (optional) — Image conversions

### Internal
- `core.effects.base.Effect` — Base effect class
- `core.sources.depth_source.AstraDepthSource` — Depth provider interface
- `core.shader_program.ShaderProgram` — Shader compilation
- `core.framebuffer.Framebuffer` — GPU framebuffer abstraction

---

## Common Patterns

### Depth Texture Management

All effects that use depth data follow this pattern:

1. Set depth source via `set_depth_source()`
2. Call `update_depth_data()` each frame to refresh depth texture
3. Access depth texture via `get_depth_texture()` in shader
4. Clean up texture in `cleanup()` (call `super().cleanup()`)

### Shader Uniforms

Base class provides:
- `u_depth_texture` (sampler2D)
- `u_near_clip`, `u_far_clip` (float)
- `u_depth_scale` (float)
- `u_invert_depth` (bool)
- `u_frame_width`, `u_frame_height` (int)

Subclasses add their own uniforms.

### Parameter Schema

Each effect defines a `parameters` dict with defaults. Parameters are exposed to UI via `get_parameters()` and `set_parameter()`.

---

## GPU Resource Management

Each effect manages its own GPU resources:
- Depth texture (from base class)
- Additional textures (FBOs, LUTs, etc.)
- Shader program
- Framebuffers (if needed)

All resources must be released in `cleanup()`.

---

## Error Handling

Common errors:
- `RuntimeError("No depth source")` — Source not set
- `RuntimeError("Depth data not available")` — Source returned None
- `ShaderCompilationError` — Shader failed to compile
- `RuntimeError("Out of GPU memory")` — Texture/FBO allocation failed

Effects should be robust: log warnings but continue if possible.

---

## Performance Expectations

| Effect Category | Expected Frame Time (1080p) |
|-----------------|----------------------------|
| Base class overhead | 1-2 ms |
| Simple filter (blur, fog) | 2-4 ms |
| Edge detection (Sobel) | 3-6 ms |
| Color grading (3-zone) | 2-3 ms |
| Datamosh (simple) | 3-5 ms |
| Datamosh (complex) | 5-10 ms |
| Point cloud (basic) | 4-8 ms |
| Point cloud (advanced) | 10-20 ms |

Total pipeline should maintain 60 FPS (16.7 ms/frame) with multiple effects.

---

## Testing Strategy

### Unit Tests (per effect)
- Initialization
- Parameter get/set
- Depth source connection
- Frame processing (with synthetic depth)
- Resource cleanup
- Error handling

### Integration Tests
- Multiple effects in pipeline
- Depth source switching
- Resolution changes
- Audio reactivity

### Performance Tests
- Frame time measurement
- Memory usage tracking
- GPU resource leaks

---

## Module Quality Standards

- **Test Coverage**: 85%+ for each effect class
- **Documentation**: Each effect has a spec file (P3-VD29 through P3-VD35+)
- **Naming**: Consistent `Depth*Effect` naming
- **Inheritance**: All depth effects inherit from `DepthEffect`
- **Resource Management**: No GPU leaks (all textures/FBOs deleted)
- **Thread Safety**: Documented (generally not thread-safe)

---

## Extension Points

To add a new depth effect:

1. Create class inheriting from `DepthEffect`
2. Implement `__init__` with shader fragment
3. Implement `process_frame()` (call `update_depth_data()` first)
4. Implement `cleanup()` (call `super().cleanup()`)
5. Add to `plugins/vdepth/__init__.py` `__all__` list
6. Create spec file (P3-VDXX)
7. Write tests
8. Update module manifest

---

## Known Issues (Legacy)

- **Texture leaks**: Many legacy effects don't call `glDeleteTextures` in `cleanup()`
- **No depth normalization**: Some effects assume depth is already normalized [0,1]
- **Hard-coded shader paths**: Shader loading not standardized
- **Missing error handling**: Many effects crash if depth source is None
- **Thread-unsafe**: All effects assume single-threaded OpenGL context

These must be fixed in VJLive3 implementation.

---

## Migration Guide (Legacy → VJLive3)

1. **Base Class**: Ensure all effects inherit from `DepthEffect`, not standalone `Effect`
2. **Texture Management**: Use `_depth_texture` from base class; don't manage your own depth texture
3. **Depth Normalization**: Call `apply_depth_transform()` to get normalized depth
4. **Shader Uniforms**: Use base class uniforms; add your own via `apply_uniforms()`
5. **Cleanup**: Always call `super().cleanup()` in your `cleanup()` method
6. **Parameters**: Define `self.parameters` dict with defaults; use `set_parameter()`/`get_parameter()`
7. **Error Handling**: Check for depth source before processing; handle None gracefully

---

## Test Plan (Module Level)

| Test | Description |
|------|-------------|
| `test_all_effects_import` | All effect classes can be imported without errors |
| `test_all_effects_instantiate` | Each effect can be instantiated with default parameters |
| `test_all_effects_cleanup` | Each effect's `cleanup()` can be called without errors |
| `test_depth_source_injection` | Depth source can be set and retrieved |
| `test_parameter_validation` | Invalid parameters raise appropriate errors |
| `test_no_memory_leaks` | Repeated create/destroy cycles don't increase GPU memory |
| `test_concurrent_effects` | Multiple effects can process frames simultaneously (if thread-safe) |
| `test_shader_compilation` | All shaders compile successfully on target GLSL version |

---

## Definition of Done (Module)

- [ ] All effect classes documented in individual spec files
- [ ] All effects inherit from `DepthEffect` base class
- [ ] All effects pass unit tests (85%+ coverage)
- [ ] No GPU memory leaks (verified with `gl_leaks.txt` audit)
- [ ] All shaders compile on target platforms (OpenGL 3.3+)
- [ ] Module exports complete `__all__` list
- [ ] Plugin registration works via `get_plugin_class()`
- [ ] Integration tests pass (multiple effects in pipeline)
- [ ] Performance benchmarks meet targets (<16ms/frame total for typical chain)
- [ ] Documentation includes migration guide from legacy code

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/__init__.py` — Original VJLive depth effects plugin module
- `plugins/vdepth/depth_effects.py` — Contains `DepthEffect` and basic effects
- `core/effects/depth_effects.py` — VJLive-2 version with more effects
- `core/shaders/depth_effects.glsl` — Shared shader code (some effects use this)
- `gl_leaks.txt` — Audit of texture allocation leaks across all effects

Design decisions inherited:
- Effect naming: `Depth<Something>Effect`
- Base class: `DepthEffect` (inherits from `Effect`)
- Depth source: `AstraDepthSource` interface
- Shader fragments defined as module-level constants (e.g., `DEPTH_COLOR_GRADE_FRAGMENT`)
- Plugin manifest: `plugin.json` with id, name, category, etc.

---

## Notes for Implementers

1. **Module Organization**: The `plugins/vdepth/` directory contains all depth effect implementations. Each effect should be in its own file (e.g., `depth_color_grade.py`, `depth_edge_glow.py`). The `__init__.py` imports all effects and populates `__all__`.

2. **Shader Management**: Consider centralizing shader compilation in the base class or a shader manager. Currently each effect compiles its own shader, which is fine but could be optimized.

3. **Depth Source Abstraction**: The `AstraDepthSource` interface is defined elsewhere. Ensure your implementation matches: `get_depth_frame()`, `get_color_frame()`, `get_intrinsics()`. Depth frame should be a 2D numpy array.

4. **Texture Formats**: The base class should auto-detect depth format (8-bit, 16-bit, float) and choose appropriate OpenGL internal format (`GL_R8`, `GL_R16`, `GL_R32F`). Document this clearly.

5. **Performance**: Depth effects are often chained. Be mindful of texture bandwidth. Use `GL_R8` for depth when possible. Consider using texture arrays or atlases if multiple depth effects are used together.

6. **Audio Reactivity**: Many effects support audio modulation. The base class could provide an optional `set_audio_analyzer()` method. Currently each effect implements its own. Consider standardizing.

7. **Testing**: Create synthetic depth maps for testing:
   - Gradient: `np.linspace(0, 1, H*W).reshape(H, W)`
   - Steps: `np.floor(depth * N) / N`
   - Circle: `np.sqrt((x-cx)**2 + (y-cy)**2) < radius`
   - Noise: `np.random.rand(H, W)`

8. **Debugging**: Provide a debug mode that outputs intermediate values (depth, mask, edges) as false-color for tuning parameters.

9. **Resource Tracking**: Consider implementing a resource tracker that logs all texture/FBO allocations and verifies cleanup. This helps catch leaks during development.

10. **Future Effects**: The module is designed to be extensible. New effects can be added by inheriting from `DepthEffect` and following the established patterns. See `DepthColorGradeEffect` or `DepthEdgeGlowEffect` as good examples.

---
-

## References

- VJLive1 legacy: `vjlive1/plugins/depth_effects.py`, `vjlive1/plugins/vdepth/`
- VJLive2 legacy: `core/effects/depth_effects.py`, `plugins/core/depth_*/`
- Hydra integration: `hydra/examples/depth_effects_integration.js`
- Shader reference: `core/shaders/depth_effects.glsl`
- MODULE_MANIFEST.md — Module inventory and quality standards

---

## Implementation Checklist

- [ ] Base class `DepthEffect` implemented with all required methods
- [ ] All 30+ depth effect classes implemented and tested
- [ ] Each effect has a spec file in `docs/specs/`
- [ ] `plugins/vdepth/__init__.py` exports all effects in `__all__`
- [ ] Plugin registration via `get_plugin_class()` works
- [ ] All shaders compile on OpenGL 3.3+ core profile
- [ ] No GPU memory leaks (verified with leak detector)
- [ ] Performance targets met for typical effect chains
- [ ] Documentation includes examples and migration guide
- [ ] Tests achieve 85%+ coverage across module

---

## Spec Files in This Series

- P3-VD29: Depth Camera Splitter
- P3-VD30: Depth Color Grade
- P3-VD31: Depth Contour Datamosh
- P3-VD32: Depth Distance Filter
- P3-VD33: Depth Dual
- P3-VD34: Depth Edge Glow
- P3-VD35: Depth Effect (Base Class)
- P3-VD36: **This document** (Depth Effects Module overview)

---

## Conclusion

The Depth Effects module is a cornerstone of VJLive3's depth-aware capabilities. It provides a comprehensive toolkit for real-time depth-based visual manipulation, from simple filtering to complex datamosh and 3D reconstruction. By following the established patterns and ensuring high quality (no leaks, good performance, comprehensive tests), this module will enable VJs to create stunning depth-reactive performances.

---
