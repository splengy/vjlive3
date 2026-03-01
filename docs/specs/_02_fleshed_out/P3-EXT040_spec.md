# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P3-EXT040_depth_acid_fractal.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT040 — DepthAcidFractalPlugin

**Phase:** Phase 3 / P3
**Assigned To:** Alex Chen
**Spec Written By:** Jordan Lee
**Date:** 2025-04-05

---

## What This Module Does

The `DepthAcidFractalPlugin` applies a complex, depth-reactive visual effect to video frames by combining fractal mathematics with film-based color alchemy. It generates dynamic neon-style distortions based on depth data, using techniques such as Julia set rendering, prism splitting, solarization, cross-processing, and motion blur—all modulated by audio input and time. The output is a visually rich, immersive effect that transforms the scene into an alien, high-contrast neon environment with depth-aware edge enhancements.

---

## What It Does NOT Do

- It does not perform real-time object detection or segmentation.
- It does not generate new depth maps; it relies on existing depth texture input from the video pipeline.
- It does not support HDR tone mapping or dynamic range adjustments beyond the native 8-bit per channel limits of the shader.
- It does not process audio for pitch, tempo, or frequency analysis independently—only uses raw amplitude and bass features via `AudioReactor`.

---

## Public Interface

```python
class DepthAcidFractalPlugin(Effect):
    def __init__(self, depth_texture: str, resolution: tuple[int, int], time: float) -> None:
        super().__init__()
        self.depth_texture = depth_texture
        self.resolution = resolution
        self.time = time
    
    def process_frame(self, frame: np.ndarray, audio_features: AudioFeature) -> np.ndarray:
        """
        Applies the Depth Acid Fractal effect to a single video frame.
        
        Args:
            frame: Input RGB frame (H x W x 3), uint8 values in [0,255]
            audio_features: AudioFeature object with amplitude and bass components
            
        Returns:
            Processed frame as RGB numpy array
        """
        return processed_frame
    
    def set_parameter(self, name: str, value: float) -> None:
        """Set a parameter from the UI or config."""
        pass

    def get_parameter(self, name: str) -> float:
        """Retrieve current parameter value."""
        pass
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `depth_texture` | `str` | Path or identifier for depth texture input (e.g., "depth_map_0") | Must be valid texture name; must exist in frame pipeline |
| `resolution` | `tuple[int, int]` | Frame resolution (width, height) | Must match actual video dimensions; minimum 320x240 |
| `time` | `float` | Current playback time in seconds | Must be >= 0; updated per frame |
| `frame` | `np.ndarray` | Input RGB video frame (H x W x 3, uint8) | Values in [0,255]; must not be None |
| `audio_features` | `AudioFeature` | Audio amplitude and bass features from audio reactor | Must contain `amplitude`, `bass_throb` fields |
| `output_frame` | `np.ndarray` | Output processed frame (same shape as input) | Same dimensions; RGB, uint8 |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Use NullDevice pattern: return original frame with no effect if depth texture not available.
- What happens on bad input? → Raise `ValueError` with message "Invalid frame or audio features provided" if frame is None, invalid shape, or missing required audio fields.
- What is the cleanup path? → No external resources are held; all textures and buffers are managed via OpenGL context lifecycle. On shutdown, call `glDeleteTextures()` on any generated textures (if used), though this is currently not implemented in legacy code.

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — for array manipulation — fallback: use list comprehensions with performance warning
  - `OpenGL.GL` — for shader rendering — fallback: disable rendering, return original frame
- Internal modules this depends on:
  - `core.effects.shader_base.Effect`
  - `core.audio_reactor.AudioReactor`
  - `core.audio_analyzer.AudioFeature`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_depth_texture` | Module starts without crashing if depth texture is missing |
| `test_process_frame_valid_input` | Core effect applies correct fractal and film alchemy transformations |
| `test_process_frame_bad_input` | Bad frame or audio input raises appropriate ValueError |
| `test_parameter_set_get_cycle` | Parameters can be set and retrieved correctly over time |
| `test_edge_case_no_audio` | Effect runs gracefully when audio features are missing (default values used) |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT040: Port depth_acid_fractal to VJLive3` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### vjlive1/plugins/vdepth/depth_acid_fractal.py (L1-20)
```python
"""
Depth Acid Fractal Datamosh Effect
Neon fractal mayhem at 3AM. Bass in your chest. Pupils like saucers.

Combines techniques never used in the other effects:
- Julia set fractals with depth as the complex parameter (the scene
  BECOMES a fractal at depth boundaries)
- Prism splitting (like holding a crystal in front of the lens —
  multiple offset RGB copies with prismatic dispersion)
- Solarization / Sabattier effect (classic darkroom partial negative
  inversion — creates alien neon edge outlines)
- Cross-processing (wrong film chemistry — pushes colors into
  impossible neon combinations per depth band)
- Film burn / neon light leaks (depth-reactive overexposure hot spots
  that bleed neon along depth contours)
- Zoom blur (radial motion blur from center, depth-controlled —
  near objects sharp, far objects streak)
- Posterization per depth layer (reduced color bands, comic-book neon)
"""
```

### vjlive1/plugins/vdepth/depth_acid_fractal.py (L17-36)
```python
from core.effects.shader_base import Effect
from core.audio_reactor import AudioReactor
from core.audio_analyzer import AudioFeature
from OpenGL.GL import (glGenTextures, glBindTexture, glTexParameteri, glTexImage2D,
                     GL_TEXTURE_2D, GL_LINEAR, GL_CLAMP_TO_EDGE, GL_RED,
                     GL_UNSIGNED_BYTE, glActiveTexture, GL_TEXTURE0)
import numpy as np


DEPTH_ACID_FRACTAL_FRAGMENT = """
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
"""
```

### vjlive1/plugins/vdepth/depth_acid_fractal.py (L33-52)
```python
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Fractals
uniform float fractal_intensity;     // How much fractal replaces the image
uniform float fractal_zoom;          // Fractal zoom level
uniform float fractal_iterations;    // Iteration count (detail)
uniform float fractal_morph;         // Morphing Julia parameter over time

// Prism
uniform float prism_split;           // Prismatic RGB separation amount
uniform float prism_rotate;          // Prism rotation angle
uniform float prism_faces;           // Number of prism faces / copies
```

### vjlive1/plugins/vdepth/depth_acid_fractal.py (L49-68)
```python
uniform float prism_split;           // Prismatic RGB separation amount
uniform float prism_rotate;          // Prism rotation angle
uniform float prism_faces;           // Number of prism faces / copies

// Film Alchemy
uniform float solarize;              // Sabattier solarization intensity
uniform float cross_process;         // Cross-processing color shift
uniform float film_burn;             // Neon light leak / film burn
uniform float posterize;             // Posterization band count

// Motion
uniform float zoom_blur;             // Radial zoom blur (depth-controlled)
uniform float bass_throb;            // Bass-driven image pulse

// Intensity
uniform float neon_boost;            // Push everything to neon saturation
uniform float feedback;              //