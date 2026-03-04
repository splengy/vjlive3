# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P3-EXT013_bad_trip_datamosh.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT013 — BadTripDatamoshEffect

**Phase:** Phase 3 / P3  
**Assigned To:** Alex R.  
**Spec Written By:** Sam K.  
**Date:** 2025-04-05

---

## What This Module Does

The `BadTripDatamoshEffect` simulates a psychologically disturbing visual experience by combining dual video inputs with dynamic distortions such as facial skeletalization, insect-like noise crawling across the frame, and screen tearing that reveals a second video stream. It leverages depth mapping to identify subjects and transform them into monstrous forms while introducing anxiety-inducing effects like strobing, color shifts, and void-based visual artifacts. This module produces a surreal, horror-themed output suitable for immersive or experimental performance environments.

---

## What It Does NOT Do

- It does not perform real-time audio processing or synchronization with sound.
- It does not support user-defined video input selection via UI; inputs are fixed at texture units 0 and 1.
- It does not provide a configuration interface (e.g., sliders in VJLive3 UI) — all parameters are passed via uniform values.
- It does not handle metadata tagging or mood classification beyond internal tags.
- It does not support hardware acceleration fallbacks outside of OpenGL shader execution.

---

## Public Interface

```python
class BadTripDatamoshEffect:
    def __init__(self, video_a: str, video_b: str, depth_map: str) -> None:
        """
        Initialize the effect with two video inputs and a depth map.
        
        Args:
            video_a: Path or identifier for first input video stream (tex0)
            video_b: Path or identifier for second input video stream (tex1)
            depth_map: Path or identifier for depth texture
        """
        pass

    def render(self, frame_time: float, resolution: tuple[int, int]) -> dict[str, Any]:
        """
        Render the effect using current frame data and return processed output.
        
        Args:
            frame_time: Current time in seconds (used for animation)
            resolution: Tuple of (width, height) of the current frame
            
        Returns:
            Dictionary containing fragment shader uniforms and metadata
        """
        pass

    def stop(self) -> None:
        """Release any held resources or cleanup internal state."""
        pass
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `video_a` | `str` | Identifier for first video input (used as tex0) | Required; must be valid path or stream ID |
| `video_b` | `str` | Identifier for second video input (used as tex1) | Required; must be valid path or stream ID |
| `depth_map` | `str` | Path to depth texture map used for facial distortion and artifacts | Required; must be valid path or stream ID |
| `frame_time` | `float` | Current time in seconds, used for animation and jitter effects | ≥ 0.0; precision: float32 |
| `resolution` | `tuple[int, int]` | Output resolution (width, height) of current frame | Width > 0, Height > 0; must be valid screen dimensions |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Uses the NullDevice pattern: if any input stream or depth map fails to load, it defaults to black with a warning log entry. The effect will still render but without visual distortion.
- What happens on bad input? → Raises `ValueError` with message indicating which parameter (e.g., "Invalid video_a path") is malformed or missing.
- What is the cleanup path? → `stop()` method releases GPU resources and logs a clean shutdown message. If called multiple times, it does nothing beyond first execution.

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `pyopengl` — used for shader rendering — fallback: software rasterization via legacy OpenGL context
  - `numpy` — for internal texture coordinate math — fallback: scalar operations only
- Internal modules this depends on:
  - `vjlive3.core.effects.shader_base` — base class for effect rendering
  - `vjlive3.utils.texture_loader` — for loading video and depth textures

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if any input (video_a, video_b, depth_map) is missing or invalid |
| `test_basic_operation` | Core rendering returns expected uniform values and correct texture references when valid inputs are provided |
| `test_error_handling` | Bad input paths raise a clear `ValueError` with descriptive message |
| `test_cleanup` | `stop()` method releases resources cleanly and logs shutdown event without errors |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-3] P3-EXT013: Port bad_trip_datamosh to VJLive3` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 3, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### vjlive1/plugins/vdatamosh/bad_trip_datamosh.py (L1-20)
```python
"""
Bad Trip Datamosh — The Nightmare Flip

DUAL VIDEO INPUT: tex0 = Video A, tex1 = Video B

"IT WON'T STOP."

This effect simulates a psychedelic crisis. The visuals are aggressive,
hostile, and unsettling. It uses depth to identify the subject and
turn them into a monster. The environment breathes with a sickly
pulse. Spiders crawl under the pixels.

Features:
- Demon Face: Distorts facial depth to look skeletal or demonic.
- Insect Crawl: High-frequency noise that moves like bugs.
- Paranoia Strobe: Random, anxiety-inducing flashes.
- Void Gaze: The center of the screen stares back at you.
- Reality Tear: Screen tearing that reveals the "other side" (Video B).

Metadata:
```

### vjlive1/plugins/vdatamosh/bad_trip_datamosh.py (L17-36)
```python
- Void Gaze: The center of the screen stares back at you.
- Reality Tear: Screen tearing that reveals the "other side" (Video B).

Metadata:
- Tags: horror, nightmare, bad-trip, paranoia, demons, glitch
- Mood: terrifying, anxious, sick, dark, overwhelming
- Visual Style: psychological-horror, deep-fried, cursed-image, void

Texture unit layout:
  Unit 0: tex0 (Video A)
  Unit 1: texPrev (previous frame)
  Unit 2: depth_tex (depth map)
  Unit 3: tex1 (Video B)
```

### vjlive1/plugins/vdatamosh/bad_trip_datamosh.py (L33-52)
```python
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

FRAGMENT = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D tex0;
uniform sampler2D texPrev;
uniform sampler2D depth_tex;
uniform sampler2D tex1;
uniform float time;
uniform vec2 resolution;

uniform float u_anxiety;           // Speed/Jitter intensity
uniform float u_demon_face;        // Facial distortion amount
uniform float u_insect_crawl;      // Bug-like noise
uniform float u_void_gaze;         // Dark vignette/hole
uniform float u_reality_tear;      // Glitch tearing
uniform float u_sickness;          // Green/Purple tinting
uniform float u_time_loop;         // Feedback delay echo
uniform float u_breathing_walls;   // UV warping
uniform float u_paranoia;          // Random strobe/cuts
uniform float u_shadow_people;     // Dark depth artifacts
uniform float u_psychosis;         // Color inversion/hue shift
uniform float u_doom;              // Contrast crush
uniform float u_mix;

float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
```

### vjlive1/plugins/vdatamosh/bad_trip_datamosh.py (L49-68)
```python
uniform float u_anxiety;           // Speed/Jitter intensity
uniform float u_demon_face;        // Facial distortion amount
uniform float u_insect_crawl;      // Bug-like noise
uniform float u_void