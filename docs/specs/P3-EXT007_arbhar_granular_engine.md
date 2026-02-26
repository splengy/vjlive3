# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT007_arbhar_granular_engine.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT007 — arbhar_granular_engine (ArbharGranularEngine)

**What This Module Does**

The `ArbharGranularEngine` module implements an advanced granular synthesis system that generates audio-reactive visual effects using temporal grain manipulation. It manages a circular buffer of video frames, controls grain density and pitch via user-defined parameters, and supports multiple quality modes with dynamic parameter smoothing based on incoming audio signals. The module provides a foundation for real-time, responsive visual generation in VJLive3.

---

## Public Interface

```python
class ArbharGranularEngine:
    def __init__(self) -> None:
        """
        Initialize the granular synthesis engine.
        
        Sets up buffer configuration, grain management arrays, audio reactivity settings,
        and quality modes. Seeds random number generator for temporal randomization.
        """
    
    def load(self) -> bool:
        """
        Load the associated .frag shader file.
        
        Returns:
            bool: True if shader file exists and loads successfully, False otherwise
        """
    
    def update(self, signals: Dict[str, Any]) -> None:
        """
        Update effect parameters based on incoming signals.
        
        Args:
            signals (Dict[str, Any]): A dictionary of realtime signals 
                                 (e.g., 'bass', 'treble', 'bpm', 'midi_cc_1').
        """
    
    def get_parameters(self) -> Dict[str, float]:
        """
        Get current state of all effect parameters.
        
        Returns:
            Dict[str, float]: Dictionary of parameter names and their current values
        """
    
    def set_parameter(self, name: str, value: float) -> None:
        """
        Set a specific parameter value.
        
        Args:
            name (str): Parameter name to set (e.g. "intensity", "spray", "grain_pitch")
            value (float): Value to assign to parameter; range 0.0–10.0 for all parameters
        """
```

---

## Description

The ArbharGranularEngine is a sophisticated granular synthesis system that creates audio-reactive visual effects by manipulating video frames as "grains" of time. It maintains a circular buffer of recent frames (typically 8 seconds at 60fps), then spawns multiple grains that play back segments of these frames with variable pitch, size, and timing. The engine responds to audio input by modulating grain density, pitch, and temporal randomization, creating dynamic visual patterns that react to music or sound in real-time.

---

## What This Module Does

- Manages a circular buffer of video frames for temporal grain access
- Spawns multiple grains (typically 32) with individual pitch, size, and timing
- Applies audio-reactive parameter modulation with smoothing
- Supports multiple quality modes (lo-fi, standard, hi-fi) with different processing costs
- Performs pitch shifting and time stretching on individual grains
- Mixes granular output with original frame for balanced visual effect
- Provides real-time parameter control via unified parameter system

## What This Module Does NOT Do

- Handle color space conversions (assumes input is in display color space)
- Perform global image processing or filtering
- Manage memory allocation for large frame buffers (uses fixed-size circular buffer)
- Handle non-RGB color formats (e.g., YUV, CMYK)
- Perform any geometric transformations or warping beyond grain-level operations
- Manage audio input directly (relies on external audio analysis)

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `signals` | `Dict[str, Any]` | Dictionary of input signals including audio levels or control data (e.g., "audio_level", "frame_rate") | Must contain at least `"audio_level"` if audio reactivity is enabled; values must be numeric |
| `name` | `str` | Parameter name to set (e.g. "intensity", "spray", "grain_pitch") | Must be one of: "intensity", "spray", "grain_pitch", "audio_reactivity_intensity", "audio_reactivity_smoothing" |
| `value` | `float` | Value to assign to parameter; range 0.0–10.0 for all parameters | Values must be within [0.0, 10.0] inclusive |
| `return_value` (from `get_parameters`) | `Dict[str, float]` | Current state of all effect parameters | All values in range [0.0, 10.0]; quality mode is string |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for array operations on frame buffers and grain data — fallback: built-in lists with reduced performance
  - `os` — used to check shader file existence — fallback: silent failure, no error raised
  - `time` — used for seeding random number generator — fallback: uses system time if available; falls back to monotonic clock
  - `cv2` (OpenCV) — used for frame processing and weighted blending — fallback: custom blending implementation with reduced quality
- Internal modules this depends on:
  - `core.base_effect.BaseEffect` — base class for effect processing pipeline
  - `core.video_buffer_manager.get_buffer_manager`, `VideoBufferConfig` — for buffer management and configuration

---

## Legacy Context

The ArbharGranularEngine is based on the original VJlive implementation found in `effects/arbhar_granular_engine.py`. It was designed as an audio-reactive granular synthesis system that creates dynamic visual patterns by manipulating video frames as grains of time. The legacy implementation used a 8-second circular buffer at 60fps, managed 32 active grains with individual pitch and timing, and supported three quality modes with different processing costs.

---

## Integration

This effect integrates with the VJLive3 node graph as a standard video effect node. It connects to:
- Input: Video signal from previous node or source (stored in circular buffer)
- Output: Processed video signal to next node or display (granular synthesis output)
- Parameters: Exposed via the unified parameter system with real-time control
- Performance: Designed to run at 60fps with minimal latency, though CPU cost is high
- Audio: Receives audio signals via the `update()` method for reactive parameter modulation

---

## Performance

- **Frame Rate Impact**: High CPU cost due to grain processing, but designed to maintain 60fps on modern hardware
- **Memory Usage**: High memory usage for circular buffer (8 seconds × 60fps × frame size)
- **GPU vs CPU**: CPU-based implementation with optional shader support
- **Latency**: Single-pass processing with minimal latency, approximately 2-5ms per frame on typical hardware
- **Scalability**: Performance scales linearly with frame resolution and grain count

---

## Detailed Behavior

### Audio-Reactive Parameter Updates

The `update()` method processes incoming audio signals and maps them to effect parameters with smoothing:

```python
# Map audio signals to effect parameters with smoothing
if "treble" in signals:
    target_intensity = signals["treble"] * 10.0 * self.audio_reactivity["intensity"]
    self.intensity = (self.intensity * (1.0 - self.audio_reactivity["smoothing"]) + 
                     target_intensity * self.audio_reactivity["smoothing"])
```

This creates smooth transitions between parameter values based on audio input, preventing abrupt changes that would be visually jarring.

### Grain Management

The engine manages 32 active grains with individual properties:

- **Positions**: Stored in `grain_positions` array, determines which frame segment each grain plays
- **Sizes**: Stored in `grain_sizes` array, controls the duration of each grain
- **Pitches**: Stored in `grain_pitches` array, controls time stretching/compression
- **Alphas**: Stored in `grain_alphas` array, controls transparency/mixing strength
- **Quality**: Stored in `grain_quality` array, determines processing quality per grain

### Quality Modes

The engine supports three quality modes with different processing costs:

- **Lo-fi**: 0.0 - Minimal processing, lowest CPU cost
- **Standard**: 5.0 - Balanced quality and performance (default)
- **Hi-fi**: 10.0 - Maximum quality, highest CPU cost

Quality affects grain processing, blending, and overall visual fidelity.

### Frame Processing

The `draw()` method performs the actual granular synthesis:

1. Gets current frame from circular buffer
2. For each active grain:
   - Calculates grain position in buffer
   - Gets source frame for this grain
   - Applies pitch shifting (time stretching)
   - Applies quality-based processing
   - Mixes grain into output frame with quality-based blending
3. Mixes original frame with granular effect (40% original, 60% granular)
4. Returns final processed frame

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware or external resources are absent |
| `test_load_shader_success` | `load()` returns True when shader file exists at expected path |
| `test_load_shader_failure` | `load()` returns False when shader file is missing or inaccessible |
| `test_update_with_audio_signal` | `update()` adjusts grain intensity based on audio level input (e.g., 0.5 sensitivity) |
| `test_parameter_set_range_validation` | Setting parameters outside [0.0, 10.0] raises ValueError |
| `test_get_parameters_returns_correct_values` | `get_parameters()` returns current values matching internal state |
| `test_quality_mode_switching` | Switching between "lo-fi", "standard", and "hi-fi" modes changes grain quality settings correctly |
| `test_audio_reactivity_smoothing` | Parameter smoothing works correctly with different smoothing factors |
| `test_grain_management` | Grain arrays are properly initialized and managed |
| `test_circular_buffer` | Frame buffer correctly wraps around and maintains 8-second history |
| `test_cleanup_resources` | No memory leaks or open file handles after module shutdown |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-X] P3-EXT007: Port ArbharGranularEngine to VJLive3` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

## LEGACY CODE REFERENCES

### vjlive1/effects/arbhar_granular_engine.py (L1-20)
```python
import numpy as np
from typing import Dict, Any
import os
import time
import random
import cv2
from core.base_effect import BaseEffect
from core.video_buffer_manager import get_buffer_manager, VideoBufferConfig

class ArbharGranularEngine(BaseEffect):
    """
    Arbhar Granular Engine - Advanced Granular Synthesis System
    
    Implements a sophisticated granular synthesis engine with:
    - Variable grain density and temporal randomization
    - Pitch shifting and UV scaling
    - Circular buffer management
    - Audio-reactive parameter control
    - Multiple quality modes
    """
```

### vjlive1/effects/arbhar_granular_engine.py (L17-36)
```python
    - Circular buffer management
    - Audio-reactive parameter control
    - Multiple quality modes
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Arbhar Granular Engine"
        self.shader_path = "effects/shaders/shaders/arbhar_granular_engine.frag"
        self.is_loaded = False
        
        # Effect parameters (0.0-10.0 range)
        self.intensity = 0.0      # Controls grain spawn rate and density
        self.spray = 0.0         # Controls temporal randomization
        self.grain_pitch = 0.0    # Controls individual grain UV scaling
        self.is_loaded = False
        
        # Buffer configuration
        self.buffer_length = 8.0  # seconds
        self.fps = 60.0
```

### vjlive1/effects/arbhar_granular_engine.py (L33-52)
```python
        # Buffer configuration
        self.buffer_length = 8.0  # seconds
        self.fps = 60.0
        self.buffer_size = int(self.buffer_length * self.fps)
        
        # Circular buffer for frame storage
        self.ring_buffer = [None] * self.buffer_size
        self.buffer_write_index = 0
        self.frames_recorded = 0
        
        # Grain management
        self.max_grains = 32
        self.active_grains = 0
        self.grain_positions = [0.0] * self.max_grains
        self.grain_sizes = [0.0] * self.max_grains
        self.grain_pitches = [0.0] * self.max_grains
        self.grain_alphas = [0.0] * self.max_grains
        self.grain_quality = [0.0] * self.max_grains
```

### vjlive1/effects/arbhar_granular_engine.py (L49-68)
```python
        self.grain_pitches = [0.0] * self.max_grains
        self.grain_alphas = [0.0] * self.max_grains
        self.grain_quality = [0.0] * self.max_grains
        
        # Audio reactivity settings
        self.audio_reactivity = {
            "intensity": 0.5,  # Sensitivity to audio signals
            "smoothing": 0.1   # Smoothing factor for parameter changes
        }
        
        # Quality modes
        self.quality_modes = {
            "lo-fi": 0.0,
            "standard": 5.0,
            "hi-fi": 10.0
        }
        self.current_quality = "standard"
        
        # Internal state
        self.last_update_time = 0.0
```

### vjlive1/effects/arbhar_granular_engine.py (L65-84)
```python
        self.current_quality = "standard"
        
        # Internal state
        self.last_update_time = 0.0
        self.frame_count = 0
        self.seed = int(time.time())
        random.seed(self.seed)
        
    def load(self):
        """Load the associated .frag shader file."""
        print(f"Loading Arbhar Granular Engine shader from {self.shader_path}")
        if os.path.exists(self.shader_path):
            self.is_loaded = True
            print("Arbhar Granular Engine shader loaded successfully.")
        else:
            print("Warning: .frag file for Arbhar Granular Engine not found.")
            self.is_loaded = False
    
    def update(self, signals: Dict[str, Any]):
```

### vjlive1/effects/arbhar_granular_engine.py (L81-100)
```python
            self.is_loaded = False
    
    def update(self, signals: Dict[str, Any]):
        """
        Update effect parameters based on incoming signals.
        
        Args:
            signals (Dict[str, Any]): A dictionary of realtime signals 
                                 (e.g., 'bass', 'treble', 'bpm', 'midi_cc_1').
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Map audio signals to effect parameters with smoothing
        if "treble" in signals:
            target_intensity = signals["treble"] * 10.0 * self.audio_reactivity["intensity"]
            self.intensity = (self.intensity * (1.0 - self.audio_reactivity["smoothing"]) + 
                             target_intensity * self.audio_reactivity["smoothing"])
```

### vjlive1/effects/arbhar_granular_engine.py (L97-116)
```python
            target_intensity = signals["treble"] * 10.0 * self.audio_reactivity["intensity"]
            self.intensity = (self.intensity * (1.0 - self.audio_reactivity["smoothing"]) + 
                             target_intensity * self.audio_reactivity["smoothing"])
        
        # Update grain parameters based on audio signals
        if "bass" in signals:
            bass_level = signals["bass"]
            # Adjust grain density based on bass level
            self.active_grains = int(bass_level * self.max_grains * 0.5)
            self.active_grains = max(1, min(self.max_grains, self.active_grains))
        
        # Update grain positions and sizes
        for i in range(self.max_grains):
            # Temporal randomization based on spray parameter
            randomization = (random.random() - 0.5) * self.spray * 2.0
            self.grain_positions[i] = (self.grain_positions[i] + randomization) % self.frames_recorded
            
            # Pitch shifting based on grain_pitch parameter
            self.grain_pitches[i] = 1.0 + (self.grain_pitch - 5.0) * 0.1
            
            # Quality-based processing
            self.grain_quality[i] = self.quality_modes[self.current_quality]
```

### vjlive1/effects/arbhar_granular_engine.py (L193-212)
```python
            # Get grain position in buffer
            grain_pos = int(self.grain_positions[i])
            if grain_pos < 0 or grain_pos >= self.frames_recorded:
                continue
            
            # Get source frame for this grain
            source_frame = self.ring_buffer[grain_pos % self.buffer_size]
            if source_frame is None:
                continue
            
            # Apply pitch shifting (time stretching)
            pitch_factor = self.grain_pitches[i]
            grain_size = self.grain_sizes[i] * pitch_factor
            
            # Apply quality-based processing
            quality_factor = self.grain_quality[i]
            
            # Mix grain into output frame with quality-based blending
            mix_factor = self.grain_alphas[i] * 0.05 * quality_factor  # Scale alpha for mixing
            output_frame = cv2.addWeighted(output_frame, 1.0, source_frame, mix_factor, 0)
```

### vjlive1/effects/arbhar_granular_engine.py (L209-228)
```python
            quality_factor = self.grain_quality[i]
            
            # Mix grain into output frame with quality-based blending
            mix_factor = self.grain_alphas[i] * 0.05 * quality_factor  # Scale alpha for mixing
            output_frame = cv2.addWeighted(output_frame, 1.0, source_frame, mix_factor, 0)
        
        # Mix original frame with granular effect
        mix_factor = 0.4  # 40% original, 60% granular
        final_frame = cv2.addWeighted(current_frame, mix_factor, output_frame, 1.0 - mix_factor, 0)
        
        return final_frame
    
    def add_frame_to_buffer(self, frame: np.ndarray):
        """Add a frame to the circular buffer."""
        # Store frame in ring buffer
        self.ring_buffer[self.buffer_write_index] = frame.copy()
        
        # Update indices
        self.buffer_write_index = (self.buffer_write_index + 1) % self.buffer_size
        self.frames_recorded = min(self.frames_recorded + 1, self.buffer_size)
```

### vjlive1/effects/arbhar_granular_engine.py (L225-244)
```python
        # Update indices
        self.buffer_write_index = (self.buffer_write_index + 1) % self.buffer_size
        self.frames_recorded = min(self.frames_recorded + 1, self.buffer_size)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Metadata for the effect."""
        return {
            "name": "Arbhar Granular Engine",
            "description": "Advanced granular synthesis with variable density, pitch shifting, temporal randomization, and multiple quality modes",
            "tags": ["granular", "synthesis", "audio-reactive", "buffer", "pitch-shift", "quality-modes"],
            "parameters": {
                "intensity": "Controls grain spawn rate and density",
                "spray": "Controls temporal randomization of grain positions",
                "grain_pitch": "Controls individual grain UV scaling and pitch shifting",
                "quality": "Selects quality mode: lo-fi (0.0), standard (5.0), hi-fi (10.0)"
            },
            "performance": {
                "complexity": "High",
                "cpu_cost": "High",
                "gpu_cost": "Medium",
                "memory_usage": "High"
            }
        }
```

### vjlive1/effects/arbhar_granular_engine.py (L241-253)
```python
            },
            "performance": {
                "complexity": "High",
                "cpu_cost": "High",
                "gpu_cost": "Medium",
                "memory_usage": "High"
            }
        }

# Register the effect for the effect system
if __name__ == "__main__":
    # This allows the effect to be imported and used by the system
    pass