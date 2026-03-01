# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P3-EXT066_depth_effects.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT066 — DepthEffectsPlugin

**Phase:** Phase 2 / P2-H3  
**Assigned To:** Alex Chen  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-05

---

## What This Module Does

The `DepthEffectsPlugin` module ports the legacy GPU-accelerated depth effects shader from VJlive1 to VJLive3, enabling real-time visualization and manipulation of depth data in video streams. It applies configurable transformations such as thresholding, smoothing, edge enhancement, color mapping, and blending to depth textures, producing visually rich output based on user-defined parameters.

---

## What It Does NOT Do

- It does not process raw pixel data or perform frame-by-frame image processing outside the GPU shader pipeline.
- It does not generate new depth maps; it only manipulates existing depth texture inputs.
- It does not support audio-based modulation of depth effects (e.g., dynamic thresholds).
- It does not provide depth estimation from video frames — this is out of scope for this module.

---

## Public Interface

```python
class DepthEffectsPlugin:
    def __init__(self, depth_texture: Texture, frame_width: float, frame_height: float) -> None:
        """
        Initialize the plugin with a depth texture and frame dimensions.
        
        Args:
            depth_texture: Input depth texture (sampler2D-like interface)
            frame_width: Width of input video frame
            frame_height: Height of input video frame
        """
    
    def apply_effect(self, time: float, params: Dict[str, float]) -> Texture:
        """
        Apply depth effects to the input depth texture using provided parameters.
        
        Args:
            time: Current playback time (for animation)
            params: Dictionary of effect controls
            
        Returns:
            Processed depth texture with visualized effects
        """
    
    def stop(self) -> None:
        """Release GPU resources and clean up internal state."""
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `depth_texture` | `Texture` | Input depth map from video stream | Must be valid 2D texture with float values in [0.0, 1.0] range |
| `frame_width` | `float` | Width of the input frame (in pixels) | Must be > 0; derived from video source |
| `frame_height` | `float` | Height of the input frame (in pixels) | Must be > 0; derived from video source |
| `time` | `float` | Current time in seconds for animation effects | ≥ 0.0, typically from playback timeline |
| `params` | `Dict[str, float]` | Effect control parameters: <br> - depth_strength (0.0–1.0) <br> - threshold (0.0–1.0) <br> - smoothing (0.0–1.0) <br> - edge_enhance (0.0–1.0) <br> - color_map (0.0–3.0) <br> - blend (0.0–1.0) <br> - feedback (0.0–1.0) | All values must be in valid ranges; invalid inputs raise ValueError |
| `output_texture` | `Texture` | Output depth texture with applied visual effects | Same resolution as input, float format [0.0, 1.0] |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Use the NullDevice pattern: return a dummy texture with zero values when GPU context fails to initialize.
- What happens on bad input? → Raise `ValueError` with descriptive message if any parameter falls outside valid range (e.g., negative smoothing).
- What is the cleanup path? → `stop()` method releases OpenGL/GPU resources and clears internal buffers. If called multiple times, no error should be raised.

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `pyopengl` — used for GPU context management — fallback: software-based texture processing via CPU
  - `glslang` — for shader compilation — fallback: use legacy GLSL interpreter with reduced performance
- Internal modules this depends on:
  - `vjlive3.core.texture.Texture`
  - `vjlive3.core.shader.ShaderManager`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing if GPU context is unavailable (NullDevice fallback) |
| `test_basic_operation` | Core effect applies correctly with default parameters and valid input texture |
| `test_error_handling` | Invalid parameter values (e.g., negative smoothing) raise ValueError with clear message |
| `test_cleanup` | stop() method releases resources cleanly; no memory leaks or open handles |
| `test_color_map_transitions` | Color mapping transitions between grayscale, heatmap, rainbow, and depth-based modes correctly |
| `test_smoothing_edge_cases` | Smoothing at 0.0 returns raw depth; smoothing near 1.0 applies full box blur with correct radius scaling |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-2] P3-EXT066: depth_effects plugin port` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### vjlive1/core/shaders/depth_effects.glsl (L1-20)
```glsl
#version 330 core
precision highp float;

uniform float time;
uniform float frame_width;
uniform float frame_height;
uniform float depth_strength;
uniform float threshold;
uniform float smoothing;
uniform float edge_enhance;
```

### vjlive1/core/shaders/depth_effects.glsl (L17-36)
```glsl
uniform float depth_strength; // 0.0-1.0
uniform float threshold;      // 0.0-1.0
uniform float smoothing;      // 0.0-1.0
uniform float edge_enhance;   // 0.0-1.0
uniform float color_map;      // Color mapping type
uniform float blend;          // 0.0-1.0
uniform float feedback;       // 0.0-1.0

uniform sampler2D video_texture;
uniform sampler2D depth_texture;

out vec4 frag_color;

float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}
```

### vjlive1/core/shaders/depth_effects.glsl (L33-52)
```glsl
float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

float map(float value, float in_min, float in_max, float out_min, float out_max) {
    return out_min + (out_max - out_min) * (value - in_min) / (in_max - in_min);
}

vec3 get_color_map(float depth) {
    if (color_map < 0.5) {
        // Grayscale
        return vec3(depth);
    } else if (color_map < 1.5) {
        // Heatmap
        vec3 color = vec3(0.0);
        color.r = smoothstep(0.0, 1.0, depth * 2.0);
        color.g = smoothstep(0.0, 1.0, (depth - 0.5) * 2.0);
        color.b = smoothstep(0.0, 1.0, (depth - 1.0) * 2.0);
        return color;
    } else if (color_map < 2.5) {
```

### vjlive1/core/shaders/depth_effects.glsl (L49-68)
```glsl
        color.g = smoothstep(0.0, 1.0, (depth - 0.5) * 2.0);
        color.b = smoothstep(0.0, 1.0, (depth - 1.0) * 2.0);
        return color;
    } else if (color_map < 2.5) {
        // Rainbow
        float r = sin(depth * 3.14159 * 2.0 + 0.0) * 0.