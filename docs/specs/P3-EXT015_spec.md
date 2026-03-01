# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P3-EXT015_bass_cannon_2.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT015 — bass_cannon_2 (BassCanon2)

**Phase:** Phase 3  
**Assigned To:** Alex Chen  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-05

---

## What This Module Does

The `bass_cannon_2` module implements a real-time bass cannon effect that generates low-frequency audio waves based on depth sensor input and visual feedback. It integrates with the audio reactor, depth cameras, and video source to produce synchronized neural-style bass loops with synesthetic color mapping. The module enables live performance environments where sound, motion, and visuals are dynamically linked through collective consciousness-inspired processing.

---

## What It Does NOT Do

- It does not generate high-frequency or melodic content.
- It does not process user input via MIDI or keyboard events.
- It does not support 3D spatial audio rendering beyond basic stereo output.
- It does not perform real-time video encoding or streaming to external platforms.
- It does not manage camera calibration, exposure, or focus settings.

---

## Public Interface

```python
class BassCanon2:
    def __init__(self, depth_sources: list[DepthCamera] = None, audio_reactor: AudioReactor = None) -> None:
        """
        Initialize the Bass Canon 2.0 effect.
        
        Args:
            depth_sources: List of DepthCamera instances to feed into the bass generation pipeline.
                           If None, defaults to simulated sources.
            audio_reactor: Optional AudioReactor instance for audio output routing.
                           If None, creates a default one internally.
        """
    
    def set_depth_sources(self, depth_sources: list[DepthCamera]) -> None:
        """
        Assign depth camera inputs to the bass cannon effect.
        
        Args:
            depth_sources: List of DepthCamera instances to use as input sources.
        """
    
    def configure_effect(self, mode: str = "underground_rave", intensity: float = 1.0) -> None:
        """
        Configure operational parameters for the bass cannon effect.
        
        Args:
            mode: Predefined mode (e.g., "underground_rave", "neural_flood", "synesthetic_pulse").
            intensity: Bass output intensity between 0.0 and 1.0.
        """
    
    def start(self) -> None:
        """
        Begin real-time processing of depth inputs and audio generation.
        Blocks until stop() is called or an error occurs.
        """
    
    def stop(self) -> None:
        """
        Gracefully terminate the effect, releasing resources and stopping audio loops.
        """
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `depth_sources` | `list[DepthCamera]` | List of depth camera devices providing input data for bass generation | Must be non-null; length ≥ 0. If empty, simulated sources are used. |
| `audio_reactor` | `AudioReactor` | Audio processing and routing system to send generated bass signals to speakers | Can be None — module creates a default instance internally. |
| `mode` | `str` | Operational mode defining behavior of the bass loop (e.g., "underground_rave", "neural_flood") | Must be one of: ["underground_rave", "neural_flood", "synesthetic_pulse"]. Default: "underground_rave". |
| `intensity` | `float` | Controls volume and resonance strength of the bass output | Range: [0.0, 1.0]. Values outside range are clamped. |
| `output_audio` | `np.ndarray` | Generated low-frequency audio waveform (in float32) | Output is generated at 48kHz sample rate; duration matches input frame time. |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Uses simulated depth sources via `DepthCamera.simulated()` pattern to maintain functionality without crashing.
- What happens on bad input? → Raises `ValueError` with descriptive message if:
  - `depth_sources` contains invalid or unconnected camera objects
  - `mode` is not in allowed list
  - `intensity` is outside [0.0, 1.0] range
- What is the cleanup path? → `stop()` method calls internal resource release (e.g., audio thread termination, buffer flush), and logs shutdown event.

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for waveform generation and array operations — fallback: built-in list operations with reduced precision
  - `cv2` — used for depth image processing — fallback: grayscale simulation using random noise
  - `pygame` — used for visual feedback display — fallback: silent mode (no UI, only audio)
- Internal modules this depends on:
  - `core.audio_reactor.AudioReactor`
  - `core.depth_camera.DepthCamera`
  - `core.video_source.VideoSource`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if depth sources are None or invalid |
| `test_basic_operation` | Core effect generates audio and updates visual feedback in real time when valid inputs are provided |
| `test_error_handling` | Invalid mode or intensity raises correct ValueError with clear message |
| `test_cleanup` | stop() method releases resources cleanly, stops audio thread, and logs shutdown event |
| `test_simulated_input` | Effect functions correctly using simulated depth sources when hardware is unavailable |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-3] P3-EXT015: bass_cannon_2 port from legacy` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 3, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### vjlive1/demo_bass_cannon_2.py (L17-36)
```python
import time
import numpy as np
import cv2
import pygame
import threading
from plugins.vdepth.bass_cannon_2 import create_bass_cannon_2
from core.audio_reactor import AudioReactor
from core.depth_camera import DepthCamera
from core.video_source import VideoSource
```

### vjlive1/demo_bass_cannon_2.py (L33-52)
```python
    def __init__(self):
        self.bass_cannon = None
        self.audio_reactor = None
        self.depth_cameras = []
        self.video_source = None
        self.running = False
        self.demo_mode = "underground_rave"
        self.show_debug = False
        self.bass_intensity = 1.0
        self.rave_time = 0.0
        self.rave_started = False
        
    def initialize_demo(self):
        """Initialize the demo environment."""
        logger.info("Initializing Bass Canon 2.0 demo...")
        
        # Create bass cannon effect
        self.bass_cannon = create_bass_cannon_2()
        logger.info("Bass Canon 2.0 effect created")
        
        # Create audio reactor
        self.audio_reactor = AudioReactor()
        logger.info("Audio reactor created")
        
        # Create depth cameras (simulated for demo)
        self.depth_cameras = [
            DepthCamera(device_id=0, name="Crowd Depth"),
            DepthCamera(device_id=1, name="Stage Depth")
        ]
        logger.info("Depth cameras created")
        
        # Create video source
        self.video_source = VideoSource()
        logger.info("Video source created")
```

### vjlive1/demo_bass_cannon_2.py (L65-84)
```python
    def configure_effect(self):
        """Configure the bass cannon effect for demo."""
        logger.info("Configuring Bass Canon 2.0 for demo...")
        
        # Set depth sources
        self.bass_cannon.set_depth_sources(self.depth_cameras)
        logger.info("Depth sources configured")
```

[NEEDS RESEARCH] — No explicit documentation of `create_bass_cannon_2()` function signature or internal behavior  
[NEEDS RESEARCH] — No known test suite for legacy module in vjlive1  
[NEEDS RESEARCH] — No specification on audio output format (sample rate, bit depth) beyond implied use of AudioReactor  
[NEEDS RESEARCH] — No details on how `set_depth_sources()` handles invalid camera objects or missing devices