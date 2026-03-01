# P3-EXT210: AstraNode Class

## Specification Status
- **Phase**: Pass 1 (Skeleton)
- **Target Phase**: Pass 2 (Detailed Technical Spec)
- **Priority**: P0
- **Module**: `astra_node` depth camera interface
- **Implementation Path**: `src/vjlive3/depth_sources/astra_node.py`
- **Class Type**: Hardware Interface / Depth Sensor Driver

## Executive Summary

AstraNode is a wrapper class for Orbbec Astra depth cameras, providing unified depth frame acquisition and camera parameter control. It abstracts the low-level Astra SDK, handling frame buffering, resolution switching, and sensor calibration for use within VJLive3's depth processing pipeline.

## Problem Statement

Depth effects in VJLive3 require hardware depth input, but:
- Astra cameras require SDK-specific initialization
- Different Astra models have different APIs
- Frame timing is inconsistent (USB variability)
- Calibration data varies per device
- Multiple Astra units need coordination

Without a standardized wrapper, each effect reimplements Astra integration, leading to:
- Code duplication
- Inconsistent frame quality
- Difficult debugging
- Poor resource sharing

## Solution Overview

AstraNode provides:
1. **Camera enumeration**: Detect connected Astra units
2. **Device initialization**: Open camera, apply settings
3. **Frame acquisition**: Continuous depth frame delivery
4. **Parameter control**: Exposure, gain, IR strength
5. **Calibration access**: Intrinsics and distortion data
6. **Resolution switching**: Dynamic resolution adjustment
7. **Resource management**: Proper USB resource cleanup

## Detailed Behavior

### Phase 1: Device Detection
Enumerate connected Astra cameras via USB

### Phase 2: Initialization
Open selected camera and apply configuration

### Phase 3: Frame Acquisition
Continuous polling of depth frames from camera

### Phase 4: Buffer Management
Store frames in circular buffer for effect access

### Phase 5: Parameter Control
Apply adjustments (exposure, gain, IR) and verify

### Phase 6: Calibration Loading
Retrieve per-device calibration matrices

### Phase 7: Resource Cleanup
Proper USB connection shutdown on close

## Public Interface

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, List
import numpy as np

class AstraResolution(Enum):
    """Supported Astra depth resolutions."""
    QVGA = (320, 240)      # Low latency
    VGA = (640, 480)       # Balanced
    FULL = (1280, 960)     # High detail

@dataclass
class AstraCalibration:
    """Astra depth sensor calibration data."""
    fx: float               # Focal length X
    fy: float               # Focal length Y
    cx: float               # Principal point X
    cy: float               # Principal point Y
    k1: float               # Radial distortion K1
    k2: float               # Radial distortion K2
    baseline: float         # Stereo baseline (mm)
    z_offset: float         # Depth offset calibration

@dataclass
class DepthFrame:
    """Raw depth frame from camera."""
    data: np.ndarray        # 16-bit depth values (mm)
    timestamp_us: int       # Microsecond timestamp
    frame_number: int       # Frame sequence number
    resolution: AstraResolution

class AstraNode:
    """Orbbec Astra depth camera interface."""
    
    def __init__(self, device_id: Optional[str] = None):
        """
        Initialize Astra node.
        If device_id is None, uses first connected camera.
        """
    
    @staticmethod
    def enumerate_devices() -> List[Tuple[str, str]]:
        """
        List connected Astra cameras.
        Returns list of (device_id, model_name) tuples.
        """
    
    def open(self) -> bool:
        """Open camera connection. Returns True if successful."""
    
    def close(self) -> None:
        """Close camera connection and cleanup resources."""
    
    def is_open(self) -> bool:
        """Check if camera connection is active."""
    
    def get_frame(self, timeout_ms: int = 100) -> Optional[DepthFrame]:
        """
        Retrieve next available depth frame.
        Returns None if no frame within timeout.
        """
    
    def get_latest_frame(self) -> Optional[DepthFrame]:
        """Get most recent frame without blocking."""
    
    def list_resolutions(self) -> List[AstraResolution]:
        """List supported resolutions for this camera."""
    
    def set_resolution(self, resolution: AstraResolution) -> bool:
        """Change capture resolution. Returns True if successful."""
    
    def get_resolution(self) -> AstraResolution:
        """Get current capture resolution."""
    
    def set_exposure(self, exposure: int) -> bool:
        """Set camera exposure (1-255). Returns True if successful."""
    
    def get_exposure(self) -> int:
        """Get current exposure value."""
    
    def set_gain(self, gain: int) -> bool:
        """Set camera gain (1-200). Returns True if successful."""
    
    def get_gain(self) -> int:
        """Get current gain value."""
    
    def set_ir_power(self, power: float) -> bool:
        """Set IR LED power (0.0-1.0). Returns True if successful."""
    
    def get_ir_power(self) -> float:
        """Get IR power setting."""
    
    def get_calibration(self) -> AstraCalibration:
        """Retrieve depth sensor calibration data."""
    
    def get_device_info(self) -> dict:
        """Return dict with device name, serial, firmware version."""
    
    def get_frame_rate(self) -> float:
        """Get current frame rate (FPS)."""
    
    def reset_device(self) -> bool:
        """Perform hardware reset. Returns True if successful."""
    
    # Context manager support
    def __enter__(self):
        """Enter context manager (opens camera)."""
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager (closes camera)."""
```

## Mathematical Formulations

### Depth Unprojection (3D from Depth)
$$X = (u - c_x) \cdot Z / f_x$$
$$Y = (v - c_y) \cdot Z / f_y$$
where $(u, v)$ are pixel coordinates, $Z$ is depth, $(c_x, c_y)$ is principal point, $(f_x, f_y)$ is focal length.

### Lens Distortion Correction
$$r = \sqrt{x^2 + y^2}$$
$$x' = x(1 + k_1 r^2 + k_2 r^4)$$
$$y' = y(1 + k_1 r^2 + k_2 r^4)$$

### Confidence from Depth
$$\text{confidence} = 1 - |Z_{\text{temporal}} - Z_{\text{current}}| / Z_{\text{max}}$$

## Performance Characteristics

- **Frame rate**: 30 FPS @ VGA (640×480)
- **Latency**: 33-50ms per frame (USB variability)
- **Resolution**: 320×240 to 1280×960 (device-dependent)
- **Depth range**: 400mm to 8000mm (depends on mode)
- **USB bandwidth**: ~100 MB/s for VGA 30 FPS
- **Accuracy**: ±2-5% of distance at 1-2 meters

## Test Plan

1. **Device Detection**
   - Enumerate devices correctly
   - Identify camera model accurately
   - Handle no-device-connected case

2. **Camera Initialization**
   - Open/close cycle works
   - Multiple open attempts handled
   - Device state tracked correctly

3. **Frame Acquisition**
   - Frames acquired at expected rate
   - Timestamp monotonically increasing
   - Frame numbers sequential
   - No frame drops (or document expected loss)

4. **Resolution Switching**
   - Supports at least VGA and QVGA
   - Resolution change doesn't drop frames
   - Calibration updates with resolution

5. **Parameter Control**
   - Exposure range settable
   - Gain range settable
   - IR power adjustable 0-1.0
   - Values persist after get/set cycle

6. **Calibration Data**
   - Calibration retrieved successfully
   - Focal lengths reasonable (400-600 typically)
   - Principal point near image center
   - Distortion coefficients provided

7. **Resource Management**
   - Context manager works correctly
   - No resource leaks after close
   - Multiple open/close cycles safe

8. **Error Handling**
   - Timeout handled gracefully
   - Device disconnect detected
   - Parameter out-of-range rejected

## Definition of Done

- [ ] Astra SDK integrated and initialized
- [ ] Device enumeration working
- [ ] Camera open/close lifecycle correct
- [ ] Frame acquisition loop implemented
- [ ] Depth frame structure defined
- [ ] Resolution switching functional
- [ ] Exposure parameter controllable
- [ ] Gain parameter controllable
- [ ] IR power parameter controllable
- [ ] Calibration data accessible
- [ ] Device info retrieval working
- [ ] Frame rate reporting accurate
- [ ] Context manager implemented
- [ ] 15+ test cases passing
- [ ] Error handling comprehensive
- [ ] No resource leaks confirmed
- [ ] Complete docstrings
- [ ] ≤900 lines of code

## Dependencies

- Astra SDK (Orbbec) — via pip or system installation
- NumPy (frame storage and math)
- VJLive3 core utilities

## Related Specs

- P3-DEPTH-MUX: Depth data multiplexing (consumer)
- P3-DEPTH-VIZ: Depth visualization
- P3-SENSOR-CALIB: Calibration utilities
- P3-FRAME-BUFFER: Frame buffering infrastructure

---

**Notes for Pass 2 Implementation:**
- Confirm minimum Astra SDK version (recommend recent version with good Python bindings)
- Determine exact resolution enumeration (may be hardware-dependent)
- Define frame drop tolerance and recovery strategy
- Document expected latency variance at different resolutions
- Specify error codes for parameter out-of-range vs. hardware not ready
