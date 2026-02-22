# Specification: P2-H3 Astra Depth Camera Integration

## 1. Overview
The Astra Depth Camera is a critical hardware input for volumetric and depth-based visual effects. Since OpenCV's `CAP_OPENNI2` backend is notoriously unstable across platforms, VJLive3 implements bespoke native drivers: a Linux implementation utilizing `PyUSB` and a Windows/Native implementation invoking the OpenNI2 C API via `ctypes`. This specification details the unification of these backends under a common `AstraSource` class, providing a stable, high-performance depth stream to the `vjlive3` plugin system.

## 2. Architecture

### 2.1 Backend Selection
The system automatically detects the OS and loads the appropriate backend:
- **Linux (`AstraLinuxSource`)**: Uses `pyusb` to talk directly to the Astra hardware (Vendor 0x2bc5, Product 0x0402), bypassing OpenNI2 entirely to avoid library conflicts and segfaults.
- **Windows (`AstraNativeSource`)**: Uses `ctypes` to load `OpenNI2.dll` and communicate via the C API (`oniInitialize`, `oniStreamReadFrame`, etc.).

### 2.2 Unified Interface (`AstraSource`)
Both backends must conform to a unified interface yielding asynchronous access to the depth stream. 
```python
class AstraSourceProtocol(Protocol):
    def start(self) -> bool: ...
    def stop(self) -> None: ...
    def read_depth(self) -> Tuple[bool, Optional[np.ndarray]]: ...
    def get_depth_info(self) -> dict: ...
```

### 2.3 Depth Processing Pipeline
Raw depth data (16-bit unsigned integers representing millimeters) must be conditioned before use by effects:
- **Temporal Smoothing**: A rolling average buffer (e.g., last 3 frames) to reduce temporal noise.
- **Thresholding**: Configurable near and far clipping planes (e.g., 0.5m to 4.0m) mapping valid depth to a normalized 0.0-1.0 float32 range.
- **Invalid Pixel Handling**: Zero-value pixels (no return) must be handled gracefully (e.g., mapped to 0.0 or ignored).

## 3. Implementation Details

### 3.1 Hardware Fail-Graceful (Safety Rail #6)
If the Astra camera is not physically connected or permissions are denied, the system **must not crash**.
- The `start()` method should gracefully return `False`.
- The node graph UI should display the source as "Offline" rather than throwing exceptions.
- The `read_depth` method should return `(False, None)`.

### 3.2 Linux PyUSB Backend (`src/vjlive3/hardware/astra_linux.py`)
- Identify USB `idVendor=0x2bc5` and `idProduct=0x0402`.
- Attempt to detach kernel drivers (`dev.detach_kernel_driver`) if bound.
- Read from the depth bulk IN endpoint asynchronously using a dedicated background thread.
- Extract $640 \times 480 \times 2$ bytes per frame, reshaping to a `(480, 640)` uint16 numpy array.
- Employ thread-safe locking (`threading.Lock()`) when copying the latest frame to the reader.

### 3.3 Windows Native Backend (`src/vjlive3/hardware/astra_native.py`)
- Find `OpenNI2.dll` (assume it will be placed in a known `bin/astra/` directory or loaded from system PATH).
- Handle missing DLL gracefully (fail-graceful).
- Initialize stream (`ONI_SENSOR_DEPTH`).
- Read frames in a background thread, using `ctypes` to map the `OniFrame` memory pointer to a numpy array without expensive looping.

### 3.4 Depth Source Manager (`src/vjlive3/hardware/astra.py`)
A factory or facade class that:
1. Detects the OS using `sys.platform`.
2. Instantiates the correct backend.
3. Provides higher-level processing (normalization, thresholding) if requested.

## 4. Node Graph Integration

A `DepthCameraNode` must be created in `src/vjlive3/plugins/core/astra_node.py` (or similar core node module):
- Exposes `near_clip` and `far_clip` parameters.
- Outputs a 2D float32 texture (via the texture manager) representing the normalized depth map.
- Generates a valid 1x1 black texture when the camera is offline to prevent shader pipeline errors.

## 5. Testing Requirements

- **Unit Tests**:
  - Mock the USB device/ctypes DLL to verify `start()`, `stop()`, and `read_depth()` logic without hardware.
  - Verify graceful failure when hardware is missing.
  - Test depth normalization math.
- **Integration Tests**:
  - `scripts/verify_astra_hardware.py` (manual execution) to test live hardware if present.

## 6. Constraints & Safety Rails
- **No Silent Failures**: Connection errors must be logged (`logger.error`), but the application must continue running (Hardware Fail-Graceful).
- **Resource Leak Prevention**: The background thread must shut down cleanly on `stop()`, and USB resources must be disposed of correctly.
- **Performance**: The background thread must use `time.sleep(0.001)` or blocking IO timeouts to avoid 100% CPU usage. Frame copies must use `numpy.copy()` within a tight lock to prevent tearing, but the lock must not be held during USB I/O.
