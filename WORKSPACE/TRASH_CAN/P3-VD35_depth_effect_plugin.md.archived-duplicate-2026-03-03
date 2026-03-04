# P3-VD35: Depth Effect Plugin

## What This Module Does
Provides a generic depth effect plugin framework that can be extended with custom shaders and processing pipelines. Acts as a base class or template for creating new depth-based effects with minimal boilerplate. Includes common depth handling utilities and parameter management.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthEffectPlugin",
    "version": "3.0.0",
    "description": "Base plugin for custom depth effects",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "utility",
    "tags": ["depth", "plugin", "framework", "template"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `custom_shader_path: str` (default: "") - Path to custom GLSL shader file
- `shader_uniforms: dict` (default: {}) - Uniform values to pass to shader
- `preprocess_steps: list[str]` (default: []) - Pre-processing operations
- `postprocess_steps: list[str]` (default: []) - Post-processing operations
- `depth_scale: float` (default: 1.0, min: 0.1, max: 10.0) - Depth value scaling
- `depth_offset: float` (default: 0.0, min: -1.0, max: 1.0) - Depth value offset
- `enable_depth_normalization: bool` (default: True) - Normalize depth to 0-1 range

### Inputs
- `video: Frame` (RGB or RGBA, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (normalized or raw)

### Outputs
- `video: Frame` (same format as input) - Processed video frame

## What It Does NOT Do
- Does NOT include any built-in visual effect (requires custom shader)
- Does NOT provide shader development environment (only runtime)
- Does NOT perform shader compilation or error recovery
- Does NOT support compute shaders (only fragment shaders)
- Does NOT include shader debugging tools
- Does NOT handle HDR metadata in custom shaders

## Test Plan
1. Unit tests for depth normalization and scaling
2. Verify custom shader loads and executes
3. Test shader uniform passing
4. Performance: ≥ 60 FPS at 1080p with simple shader
5. Memory: < 50MB additional RAM
6. Integration: verify pre/postprocess steps execute

## Implementation Notes
- Load and compile GLSL fragment shader from custom_shader_path
- Pass depth and video as textures to shader
- Set uniforms from shader_uniforms dict
- Apply preprocess_steps before shader (e.g., depth filtering)
- Apply postprocess_steps after shader (e.g., color correction)
- Use depth_scale and depth_offset to transform depth values
- If enable_depth_normalization, normalize depth to 0-1 before passing to shader
- Provide default vertex shader for full-screen quad
- Follow SAFETY_RAILS: validate shader paths, handle compilation errors

## Deliverables
- `src/vjlive3/effects/depth_effect_plugin.py`
- `tests/effects/test_depth_effect_plugin.py`
- `docs/plugins/depth_effect_plugin.md`
- `shaders/depth_effect_default.vert` (default vertex shader)

## Success Criteria
- [x] Plugin loads via METADATA
- [x] Custom shader executes correctly
- [x] Uniforms and depth processing work
- [x] 60 FPS at 1080p
- [x] Test coverage ≥ 80%
- [x] No safety rail violations