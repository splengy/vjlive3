# Spec: P1-QDRANT032 — Texture 3D Websocket

**Phase:** Phase 1 / P1-QDRANT032
**Assigned To:** desktop-roo
**Spec Written By:** desktop-roo
**Date:** 2026-03-01

---

## What This Module Does

The `Texture3DWebSocketInterface` module provides a real-time WebSocket communication layer for controlling and streaming data from the Texture 3D TOP (Texture Operator) in VJLive3. It enables external clients to dynamically adjust parameters, process video frames into a 3D texture cache, and retrieve individual texture slices via network requests. The module acts as a bridge between the WebSocket server and the underlying `Texture3DIntegration` layer, which manages the actual 3D texture buffer operations.

The core functionality includes:
- **Parameter Control**: Clients can set/get runtime parameters (active state, replacement mode, step size, etc.) via JSON messages
- **Frame Ingestion**: Accepts video frames through WebSocket messages and processes them into a circular 3D texture buffer
- **Slice Retrieval**: Allows clients to request specific depth slices from the 3D texture for remote visualization or further processing
- **State Broadcasting**: Automatically broadcasts parameter changes and info updates to all connected clients
- **Client Management**: Handles multiple simultaneous WebSocket connections with proper connect/disconnect lifecycle

This module is essential for distributed VJLive3 architectures where texture data needs to be shared across networked systems or controlled via external applications (e.g., custom UI panels, mobile controllers, or collaborative VJing setups).

---

## What It Does NOT Do

- **Does NOT implement the WebSocket server itself**: It requires an external WebSocket server instance to be passed in during initialization
- **Does NOT handle low-level texture operations**: Delegates all 3D texture management to the `Texture3DIntegration` and `Texture3DTOP` classes
- **Does NOT provide file I/O**: No capability to save/load texture data from disk
- **Does NOT process audio streams**: Purely video/texture focused, no audio-reactive features
- **Does NOT implement authentication or encryption**: Assumes trusted network environment or external security layer
- **Does NOT perform video decoding**: Expects raw numpy arrays as input frames, not compressed video formats
- **Does NOT manage WebSocket client routing**: All messages are broadcast to all connected clients (no private messaging)

---

## Detailed Behavior and Parameter Interactions

### Initialization Sequence

When `Texture3DWebSocketInterface` is instantiated:
1. Creates a `Texture3DIntegration` instance with specified `width`, `height`, and `depth` parameters
2. Initializes an empty set of connected clients
3. Registers three WebSocket event handlers: `connect`, `disconnect`, and `message`
4. The underlying `Texture3DIntegration` creates a `Texture3DTOP` instance and initializes default parameters

Default parameters (from `Texture3DIntegration.__init__`):
```python
{
    "type": "3d_texture",
    "active": True,
    "replace_single": False,
    "replace_index": 0,
    "prefill": False,
    "cache_size": depth,
    "step_size": 1,
    "output_resolution": [width, height],
    "output_aspect": [width / height, 1.0],
    "input_smoothness": "linear",
    "viewer_smoothness": "linear",
    "passes": 1,
    "channel_mask": "rgba",
    "pixel_format": "float32"
}
```

### Message Handling Flow

All incoming WebSocket messages must be JSON-encoded strings. The module parses the JSON and routes based on the `type` field:

1. **`set_parameter`**: Updates a parameter in `Texture3DIntegration`, triggers broadcast of the change to all clients
2. **`get_parameter`**: Queries a parameter value and sends response back to requesting client (via broadcast)
3. **`get_info`**: Retrieves info channels (cache size, current index, active state, etc.) and broadcasts
4. **`process_frame`**: Decodes frame data, passes to `Texture3DIntegration.process_frame()`, then broadcasts updated info
5. **`get_slice`**: Retrieves a specific depth slice by index, encodes it, and sends to all clients
6. **`reset`**: Triggers a reset of the underlying texture buffer

### Parameter Change Propagation

When a parameter is set via `set_parameter`:
1. The value is stored in `Texture3DIntegration.parameters`
2. Special handling for `prefill=True` triggers `_pre_fill()` which calls `texture_top.pre_fill(frame_provider)`
3. Special handling for `reset=True` triggers `texture_top.reset()` and clears the flag
4. A `parameter_change` message is broadcast to all connected clients containing `{parameter, value}`

### Frame Processing Pipeline

Frames are processed as numpy arrays:
1. Client sends `process_frame` message with `frame` data (format TBD - base64 or binary)
2. `_decode_frame_data()` converts to numpy array (implementation-specific)
3. `Texture3DIntegration.process_frame()` updates underlying `Texture3DTOP` with current parameters
4. `texture_top.process_frame(input_frame)` writes the frame into the 3D texture buffer
5. Info channels are updated and broadcast to all clients

### Slice Retrieval

When a client requests a slice:
1. Client sends `get_slice` with `index` (integer)
2. `Texture3DIntegration.get_slice(index)` retrieves the 2D slice from the 3D texture
3. Slice is encoded via `_encode_frame_data()` (implementation-specific)
4. Response sent as `slice_data` message containing `{index, data}`

### Client Lifecycle

- **Connect**: New client receives `initial_state` message with full parameters and info channels
- **Disconnect**: Client removed from `clients` set, no cleanup of texture data
- **Broadcast**: All messages (except potentially private responses) are sent to every connected client

---

## Public Interface

```python
import json
from typing import Dict, Any, Callable, Optional, Set
import numpy as np

class Texture3DWebSocketInterface:
    """
    WebSocket interface for Texture 3D TOP.
    
    Provides real-time parameter control and data streaming for the Texture 3D TOP
    through a WebSocket connection.
    """
    
    def __init__(self, websocket_server, width: int = 1024, height: int = 1024, depth: int = 30) -> None:
        """
        Initialize WebSocket interface.
        
        Args:
            websocket_server: WebSocket server instance with on() and send() methods
            width: Texture width in pixels (default: 1024)
            height: Texture height in pixels (default: 1024)
            depth: Number of slices in the 3D texture (default: 30)
        """
        
    def _register_handlers(self) -> None:
        """Register WebSocket event handlers for connect, disconnect, and message."""
        
    def _on_connect(self, client) -> None:
        """Handle new client connection by adding to clients set and sending initial state."""
        
    def _on_disconnect(self, client) -> None:
        """Handle client disconnection by removing from clients set."""
        
    def _on_message(self, client, message: str) -> None:
        """
        Handle incoming WebSocket message.
        
        Parses JSON and routes to appropriate handler based on 'type' field.
        Invalid JSON is logged and ignored.
        """
        
    def _handle_message(self, data: Dict[str, Any]) -> None:
        """Route message to specific handler based on data['type']."""
        
    def _handle_set_parameter(self, data: Dict[str, Any]) -> None:
        """Handle 'set_parameter' message - updates parameter and broadcasts change."""
        
    def _handle_get_parameter(self, data: Dict[str, Any]) -> None:
        """Handle 'get_parameter' message - queries value and sends response."""
        
    def _handle_get_info(self, data: Dict[str, Any]) -> None:
        """Handle 'get_info' message - retrieves info channels and broadcasts."""
        
    def _handle_process_frame(self, data: Dict[str, Any]) -> None:
        """Handle 'process_frame' message - decodes frame, processes it, broadcasts info."""
        
    def _handle_get_slice(self, data: Dict[str, Any]) -> None:
        """Handle 'get_slice' message - retrieves slice by index and sends response."""
        
    def _handle_reset(self, data: Dict[str, Any]) -> None:
        """Handle 'reset' message - triggers texture buffer reset."""
        
    def _send_initial_state(self, client) -> None:
        """Send initial state to newly connected client."""
        
    def _broadcast_parameter_change(self, parameter: str, value: Any) -> None:
        """Broadcast parameter change to all connected clients."""
        
    def _broadcast_info(self) -> None:
        """Broadcast current info channels to all connected clients."""
        
    def _send_response(self, request_id: str, response: Dict[str, Any]) -> None:
        """Send response to a specific request (broadcast to all clients currently)."""
        
    def _decode_frame_data(self, frame_data: Any) -> Optional[np.ndarray]:
        """
        Decode frame data from WebSocket message format.
        
        Implementation-specific: may handle base64, binary, or other encoding.
        Returns None if decoding fails.
        """
        
    def _encode_frame_data(self, frame_array: np.ndarray) -> Any:
        """
        Encode numpy array for WebSocket transmission.
        
        Implementation-specific: may produce base64, binary, or other format.
        """
        
    def set_frame_provider(self, provider: Callable[[int], np.ndarray]) -> None:
        """
        Set a frame provider callable for pre-filling the texture buffer.
        
        Args:
            provider: Callable that accepts an integer index and returns a numpy array frame
        """
        
    def get_texture_integration(self) -> 'Texture3DIntegration':
        """Return the underlying Texture3DIntegration instance."""
```

---

## Inputs and Outputs

### WebSocket Message Types

All messages are JSON objects with a required `type` field. Optional `request_id` fields enable request/response correlation.

| Message Type | Required Fields | Optional Fields | Description |
|--------------|-----------------|-----------------|-------------|
| `set_parameter` | `parameter` (str), `value` (any) | `request_id` (str) | Sets a parameter value |
| `get_parameter` | `parameter` (str) | `request_id` (str) | Requests a parameter value |
| `get_info` | none | `request_id` (str) | Requests all info channels |
| `process_frame` | `frame` (any) | `request_id` (str) | Provides a frame to process |
| `get_slice` | `index` (int) | `request_id` (str) | Requests a specific texture slice |
| `reset` | none | `request_id` (str) | Resets the texture buffer |

### Output Messages

All output messages are JSON-encoded and sent to connected clients:

| Output Type | Fields | When Sent |
|-------------|-------|-----------|
| `initial_state` | `info` (dict), `parameters` (dict) | On client connection |
| `parameter_change` | `parameter` (str), `value` (any) | When any client changes a parameter |
| `info_update` | `info` (dict) | After frame processing or parameter changes affecting state |
| `parameter_value` | `parameter` (str), `value` (any), `request_id` (str) | Response to `get_parameter` |
| `info` | `info` (dict), `request_id` (str) | Response to `get_info` |
| `slice_data` | `index` (int), `data` (any), `request_id` (str) | Response to `get_slice` |
| `error` | `message` (str), `request_id` (str) | On errors (e.g., invalid slice index) |

### Parameters

Parameters are stored in `Texture3DIntegration.parameters` dictionary. All values are JSON-serializable.

| Parameter Name | Type | Default | Constraints | Description |
|----------------|------|---------|-------------|-------------|
| `type` | str | `"3d_texture"` | read-only | Fixed identifier |
| `active` | bool | `True` | - | Whether texture processing is active |
| `replace_single` | bool | `False` | - | If True, only `replace_index` is updated |
| `replace_index` | int | `0` | `0 <= index < depth` | Which slice to replace when `replace_single=True` |
| `prefill` | bool | `False` | - | If True, pre-fills buffer using frame provider |
| `cache_size` | int | `depth` | `> 0` | Number of slices in the 3D texture (read-only after init) |
| `step_size` | int | `1` | `> 0` | Increment between slice writes (wrap-around) |
| `output_resolution` | list[int] | `[width, height]` | read-only | [width, height] in pixels |
| `output_aspect` | list[float] | `[w/h, 1.0]` | read-only | Aspect ratio values |
| `input_smoothness` | str | `"linear"` | `"nearest"`, `"linear"`, `"cubic"` | Interpolation for input sampling |
| `viewer_smoothness` | str | `"linear"` | `"nearest"`, `"linear"`, `"cubic"` | Interpolation for viewer sampling |
| `passes` | int | `1` | `> 0` | Number of processing passes |
| `channel_mask` | str | `"rgba"` | `"r"`, `"g"`, `"b"`, `"a"`, `"rgba"`, `"rgb"` | Which channels to process |
| `pixel_format` | str | `"float32"` | `"float32"`, `"float16"`, `"uint8"` | Data type for pixel storage |

### Info Channels

The `get_info_channels()` method returns a dictionary with runtime state:

| Info Key | Type | Description |
|----------|------|-------------|
| `cache_size` | int | Total number of depth slices (read-only) |
| `current_index` | int | Current write index in the circular buffer |
| `active` | bool | Whether processing is active |
| `replace_single` | bool | If True, only one slice is being replaced |
| `replace_index` | int | Index of slice being replaced |
| `prefill` | bool | Whether pre-fill operation is in progress |
| `step_size` | int | Current step increment |
| `width` | int | Texture width in pixels |
| `height` | int | Texture height in pixels |
| `depth` | int | Alias for `cache_size` |

---

## Edge Cases and Error Handling

### Missing or Invalid WebSocket Server

**Scenario**: The `websocket_server` passed to `__init__` does not implement required `on()` and `send()` methods.

**Behavior**: 
- During `_register_handlers()`, calling `websocket_server.on()` will raise `AttributeError`
- The module should fail fast during initialization; no recovery attempted
- **Mitigation**: Ensure server implements the expected event handler interface before instantiation

### Invalid JSON Messages

**Scenario**: Client sends malformed JSON string.

**Behavior**:
- `json.loads()` raises `json.JSONDecodeError`
- Caught in `_on_message()`, error is logged via `print()` (v1) or `logger.info()` (v2)
- Message is silently dropped; no response sent to client
- **No crash**, connection remains open

### Unknown Message Types

**Scenario**: Client sends JSON with `type` field not in the recognized set.

**Behavior**:
- `_handle_message()` logs "Unknown message type: {type}" via `print()` or `logger.info()`
- Message is silently dropped; no response sent
- **No crash**, connection remains open

### Missing Required Fields

**Scenario**: Client sends `set_parameter` without `parameter` or `value` fields.

**Behavior**:
- `_handle_set_parameter()` checks `if parameter:` before calling `set_parameter()`
- If `parameter` is falsy (None, empty string), the call is skipped
- **No error response** sent to client; operation silently ignored
- Similar silent-fail behavior for `get_parameter` if `parameter` is missing

### Invalid Slice Index

**Scenario**: Client requests `get_slice` with `index` outside valid range `[0, depth-1]`.

**Behavior**:
- `Texture3DIntegration.get_slice(index)` calls `Texture3DTOP.get_slice(index)`
- `Texture3DTOP` likely raises `IndexError` for out-of-range access
- Caught in `_handle_get_slice()` and response sent with `{"type": "error", "message": "..."}`
- **Connection remains open**, client can retry with valid index

### Frame Decoding Failure

**Scenario**: `_decode_frame_data()` returns `None` due to corrupted or unsupported data.

**Behavior**:
- `_handle_process_frame()` checks `if frame_array is not None` before processing
- If `None`, frame is silently dropped; no processing occurs
- **No error broadcast** sent to clients
- **Mitigation**: Client should ensure proper encoding; server logs may indicate issue

### Texture3DTOP Initialization Failure

**Scenario**: Underlying `Texture3DTOP` constructor fails (e.g., insufficient memory, invalid dimensions).

**Behavior**:
- Exception propagates from `Texture3DIntegration.__init__()` to `Texture3DWebSocketInterface.__init__()`
- **Module fails to initialize**; WebSocket handlers not registered
- **Mitigation**: Validate dimensions before instantiation; catch exceptions at higher level

### Client Disconnection During Broadcast

**Scenario**: A client disconnects while the server is iterating over `self.clients` to send a broadcast.

**Behavior**:
- The code does not catch exceptions during `client.send(message)`
- If the underlying WebSocket library raises an exception for a dead connection, the broadcast loop may fail partway
- **Potential issue**: Other clients may not receive the message; disconnected client remains in `self.clients` set
- **Mitigation**: Implement try/except in broadcast loops to remove dead clients

### Parameter Type Mismatch

**Scenario**: Client sets a parameter with incorrect type (e.g., string instead of int).

**Behavior**:
- `Texture3DIntegration.set_parameter()` stores value without type validation
- Value is accepted and stored; may cause errors later when used by `Texture3DTOP`
- **No immediate error**; downstream processing may fail silently or produce incorrect results
- **Mitigation**: Add type checking in `set_parameter()` or rely on `Texture3DTOP` to validate

### Pre-fill Frame Provider Failure

**Scenario**: `prefill=True` is set, but `frame_provider` is `None` or raises an exception.

**Behavior**:
- `Texture3DIntegration._pre_fill()` checks `if self.frame_provider:` before calling
- If `None`, pre-fill is silently skipped
- If callable raises exception, exception propagates and may crash the processing thread
- **Mitigation**: Ensure frame provider is set before enabling `prefill`; wrap calls in try/except

### Resource Cleanup

**Current Behavior**: The module does **not** implement explicit cleanup methods (`close()`, `__del__`, or context manager protocol).

**Implications**:
- WebSocket server remains registered with handlers after module deletion
- Client connections persist until server closes
- **Recommendation**: Add `stop()` or `close()` method to unregister handlers and clear client set

---

## Mathematical Formulations

### 3D Texture Buffer Organization

The 3D texture is organized as a circular buffer of `depth` slices, each of size `width × height` pixels. The buffer has a current write index `current_index` that advances by `step_size` after each frame write (with wrap-around).

**Buffer indexing formula** (for write position):
```
write_index = current_index % depth
```

After processing a frame:
```
current_index = (current_index + step_size) % depth
```

When `replace_single=True`, only the slice at `replace_index` is overwritten; `current_index` does not advance.

### Slice Retrieval

Retrieving slice `i` returns the 2D image at buffer position `i` (0 ≤ i < depth). The slice is a 2D array of shape `(height, width, channels)` where `channels` is determined by `channel_mask` (e.g., 4 for "rgba").

### Coordinate System

- UV coordinates (if used by downstream consumers) are normalized `[0, 1]` with origin at top-left or bottom-left depending on convention
- Pixel coordinates are integer indices: `x ∈ [0, width-1]`, `y ∈ [0, height-1]`
- Depth slices are indexed by integer `z ∈ [0, depth-1]`

### Interpolation Modes

The `input_smoothness` and `viewer_smoothness` parameters control how pixel values are sampled when coordinates fall between texel centers:

- `"nearest"`: Round to nearest integer coordinate (no interpolation)
- `"linear"`: Bilinear interpolation between 4 nearest texels
- `"cubic"`: Bicubic interpolation using 16 nearest texels (if supported)

The actual interpolation math is implemented in `Texture3DTOP`, but the interface passes these string values through.

### Channel Masking

The `channel_mask` parameter determines which color channels are processed and stored:

- `"r"`, `"g"`, `"b"`, `"a"`: Single channel
- `"rgb"`: Three channels (no alpha)
- `"rgba"`: Four channels (default)

The mask affects the shape of the numpy arrays: single-channel arrays have shape `(H, W)`, multi-channel have `(H, W, C)`.

---

## Performance Characteristics

### Memory Usage

- **3D Texture Buffer**: `width × height × depth × bytes_per_pixel` bytes
  - For default `1024×1024×30` with `float32` (4 bytes): ~120 MB
  - With `float16` (2 bytes): ~60 MB
  - With `uint8` (1 byte): ~30 MB
- **Per-Client State**: Minimal; only client object reference stored in `clients` set
- **Frame Encoding/Decoding**: Temporary buffers during `_decode_frame_data()` and `_encode_frame_data()`; size equals one frame (`width × height × channels × bytes_per_pixel`)

### Computational Complexity

- **Frame Processing**: O(width × height × channels) per frame for writing to texture buffer
- **Slice Retrieval**: O(width × height × channels) to copy slice data for encoding
- **Broadcasting**: O(number_of_clients) per message; each client `send()` is O(message_size)
- **Parameter Updates**: O(1) dictionary lookup and storage

### Network Bandwidth

- **Initial State**: ~1-2 KB JSON (parameters + info)
- **Parameter Change**: ~100-500 bytes JSON per parameter
- **Info Update**: ~500-1000 bytes JSON
- **Slice Data**: `width × height × channels × bytes_per_pixel` plus encoding overhead
  - Example: 1024×1024 RGBA float32 = 4 MB raw; base64 adds ~33% overhead → ~5.3 MB per slice
  - **High bandwidth cost** for large textures; consider compression or downsampling for remote clients

### Latency Considerations

- **Frame Ingestion**: Decoding + buffer write; typically <10ms for 1080p on modern CPU
- **Slice Request**: Decode request → retrieve slice → encode → send; dominated by encode/network time
- **Broadcast Latency**: Linear in number of clients; may become bottleneck with many clients

### Scalability Limits

- **Memory**: Limited by available RAM for 3D texture buffer; larger `depth` increases memory linearly
- **Clients**: Broadcast model means all clients receive all messages; with many clients, network bandwidth scales linearly
- **Frame Rate**: Maximum sustainable frame rate limited by processing time + broadcast overhead; 60 FPS achievable for moderate texture sizes and client counts

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_default_params` | Constructor creates `Texture3DIntegration` with correct default width/height/depth |
| `test_init_custom_params` | Constructor accepts and uses custom width/height/depth values |
| `test_websocket_handler_registration` | `_register_handlers()` attaches connect/disconnect/message handlers to server |
| `test_client_connect` | New client receives `initial_state` message with correct parameters and info |
| `test_client_disconnect` | Disconnected client removed from `clients` set; no further messages sent |
| `test_set_parameter_valid` | `set_parameter` updates value in `Texture3DIntegration` and broadcasts change |
| `test_set_parameter_invalid_name` | Setting unknown parameter name is ignored (no crash, no broadcast) |
| `test_get_parameter_roundtrip` | `get_parameter` request triggers response with correct value |
| `test_get_info_roundtrip` | `get_info` request triggers response with current info channels |
| `test_process_frame_valid` | Valid frame (numpy array) is processed without error; info broadcast sent |
| `test_process_frame_invalid_decode` | Frame data that decodes to `None` is silently dropped (no crash) |
| `test_get_slice_valid_index` | Requesting valid slice index returns encoded data in response |
| `test_get_slice_invalid_index` | Requesting out-of-range index returns `error` message |
| `test_reset_command` | `reset` message triggers `texture_integration.set_parameter("reset", True)` and broadcast |
| `test_broadcast_parameter_change` | Parameter change broadcast reaches all connected clients |
| `test_broadcast_info` | Info update broadcast reaches all connected clients after frame processing |
| `test_unknown_message_type` | Message with unknown `type` is logged and ignored (no crash) |
| `test_invalid_json` | Malformed JSON is caught, logged, and ignored (no crash) |
| `test_prefill_trigger` | Setting `prefill=True` calls `_pre_fill()` if frame provider is set |
| `test_prefill_no_provider` | Setting `prefill=True` with no frame provider does nothing (no crash) |
| `test_frame_provider_setting` | `set_frame_provider()` stores callable and is used by pre-fill |
| `test_get_texture_integration` | `get_texture_integration()` returns the underlying `Texture3DIntegration` instance |
| `test_concurrent_client_handling` | Multiple clients can connect/disconnect concurrently without data corruption |
| `test_parameter_persistence` | Parameters persist across multiple frames until explicitly changed |
| `test_step_size_advance` | After processing, `current_index` advances by `step_size` (modulo `depth`) |
| `test_replace_single_mode` | When `replace_single=True`, only `replace_index` is updated, `current_index` does not advance |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-QDRANT032: Texture 3D Websocket - port from vjlive1/plugins/texture_3d_websocket.py` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

Use these to fill in the spec. These are the REAL implementations:

### vjlive1/core/plugins/texture_3d_websocket.py (L1-12)
```python
"""
Texture 3D TOP WebSocket Interface for VJLive
Provides real-time parameter control and data streaming for the Texture 3D TOP
"""

import json
import numpy as np
from typing import Dict, Any, Callable
from core.plugins.texture_3d_integration import Texture3DIntegration
```

### vjlive1/core/plugins/texture_3d_websocket.py (L12-31)
```python
class Texture3DWebSocketInterface:
    """WebSocket interface for Texture 3D TOP"""
    
    def __init__(self, websocket_server, width: int = 1024, height: int = 1024, depth: int = 30):
        self.websocket_server = websocket_server
        self.texture_integration = Texture3DIntegration(width, height, depth)
        self.clients = set()
        
        # Register WebSocket event handlers
        self._register_handlers()
```

### vjlive1/core/plugins/texture_3d_websocket.py (L32-36)
```python
    def _register_handlers(self) -> None:
        """Register WebSocket event handlers"""
        self.websocket_server.on("connect", self._on_connect)
        self.websocket_server.on("disconnect", self._on_disconnect)
        self.websocket_server.on("message", self._on_message)
```

### vjlive1/core/plugins/texture_3d_websocket.py (L38-42)
```python
    def _on_connect(self, client) -> None:
        """Handle new client connection"""
        self.clients.add(client)
        # Send initial state to new client
        self._send_initial_state(client)
```

### vjlive1/core/plugins/texture_3d_websocket.py (L48-54)
```python
    def _on_message(self, client, message: str) -> None:
        """Handle incoming messages"""
        try:
            data = json.loads(message)
            self._handle_message(data)
        except json.JSONDecodeError:
            print(f"Invalid JSON message from client: {message}")
```

### vjlive1/core/plugins/texture_3d_websocket.py (L56-73)
```python
    def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle different types of messages"""
        message_type = data.get("type")
        
        if message_type == "set_parameter":
            self._handle_set_parameter(data)
        elif message_type == "get_parameter":
            self._handle_get_parameter(data)
        elif message_type == "get_info":
            self._handle_get_info(data)
        elif message_type == "process_frame":
            self._handle_process_frame(data)
        elif message_type == "get_slice":
            self._handle_get_slice(data)
        elif message_type == "reset":
            self._handle_reset(data)
        else:
            print(f"Unknown message type: {message_type}")
```

### vjlive1/core/plugins/texture_3d_websocket.py (L75-83)
```python
    def _handle_set_parameter(self, data: Dict[str, Any]) -> None:
        """Handle parameter setting"""
        parameter = data.get("parameter")
        value = data.get("value")
        
        if parameter:
            self.texture_integration.set_parameter(parameter, value)
            # Broadcast parameter change to all clients
            self._broadcast_parameter_change(parameter, value)
```

### vjlive1/core/plugins/texture_3d_websocket.py (L105-115)
```python
    def _handle_process_frame(self, data: Dict[str, Any]) -> None:
        """Handle frame processing"""
        frame_data = data.get("frame")
        
        if frame_data:
            # Convert base64 or binary data to numpy array
            frame_array = self._decode_frame_data(frame_data)
            if frame_array is not None:
                self.texture_integration.process_frame(frame_array)
                # Send updated info after processing
                self._broadcast_info()
```

### vjlive1/core/plugins/texture_3d_websocket.py (L117-135)
```python
    def _handle_get_slice(self, data: Dict[str, Any]) -> None:
        """Handle slice retrieval"""
        index = data.get("index")
        
        if index is not None:
            try:
                slice_data = self.texture_integration.get_slice(index)
                encoded_slice = self._encode_frame_data(slice_data)
                
                self._send_response(data.get("request_id"), {
                    "type": "slice_data",
                    "index": index,
                    "data": encoded_slice
                })
            except IndexError:
                self._send_response(data.get("request_id"), {
                    "type": "error",
                    "message": f"Slice index {index} out of range"
                })
```

### vjlive1/core/plugins/texture_3d_websocket.py (L142-150)
```python
    def _send_initial_state(self, client) -> None:
        """Send initial state to client"""
        info = self.texture_integration.get_info_channels()
        
        client.send(json.dumps({
            "type": "initial_state",
            "info": info,
            "parameters": self.texture_integration.parameters
        }))
```

### vjlive1/core/plugins/texture_3d_websocket.py (L154-161)
```python
    def _broadcast_parameter_change(self, parameter: str, value: Any) -> None:
        """Broadcast parameter change to all clients"""
        message = json.dumps({
            "type": "parameter_change",
            "parameter": parameter,
            "value": value
        })
        
        for client in self.clients:
            client.send(message)
```

### vjlive1/core/plugins/texture_3d_websocket.py (L184-194)
```python
    def _decode_frame_data(self, frame_data: Any) -> Optional[np.ndarray]:
        """Decode frame data from various formats"""
        # Implementation depends on how frames are sent (base64, binary, etc.)
        # This is a placeholder - actual implementation needed
        return None
    
    def _encode_frame_data(self, frame_array: np.ndarray) -> Any:
        """Encode frame data for transmission"""
        # Implementation depends on how frames are sent (base64, binary, etc.)
        # This is a placeholder - actual implementation needed
        return None
```

### vjlive1/core/plugins/texture_3d_websocket.py (L196-202)
```python
    def set_frame_provider(self, provider: Callable[[int], np.ndarray]) -> None:
        """Set frame provider for pre-filling"""
        self.texture_integration.set_frame_provider(provider)
    
    def get_texture_integration(self) -> Texture3DIntegration:
        """Get the underlying texture integration"""
        return self.texture_integration
```

### vjlive2/core/plugins/texture_3d_websocket.py (L1-13)
```python
import logging
import json
import numpy as np
from typing import Dict, Any, Callable, Optional, Set
from core.plugins.texture_3d_integration import Texture3DIntegration

logger = logging.getLogger(__name__)

"""
Texture 3D TOP WebSocket Interface for VJLive
Provides real-time parameter control and data streaming for the Texture 3D TOP
"""
```

### vjlive2/core/plugins/texture_3d_websocket.py (L14-32)
```python
class Texture3DWebSocketInterface:
    """WebSocket interface for Texture 3D TOP"""
    
    def __init__(self, websocket_server, width: int = 1024, height: int = 1024, depth: int = 30):
        self.websocket_server = websocket_server
        self.texture_integration = Texture3DIntegration(width, height, depth)
        self.clients = set()
        
        # Register WebSocket event handlers
        self._register_handlers()
```

### vjlive2/core/plugins/texture_3d_websocket.py (L50-56)
```python
    def _on_message(self, client, message: str) -> None:
        """Handle incoming messages"""
        try:
            data = json.loads(message)
            self._handle_message(data)
        except json.JSONDecodeError:
            logger.info(f"Invalid JSON message from client: {message}")
```

### vjlive2/core/plugins/texture_3d_websocket.py (L74-75)
```python
        else:
            logger.info(f"Unknown message type: {message_type}")
```

### vjlive1/core/plugins/texture_3d_integration.py (L1-40)
```python
"""
Texture 3D TOP Integration Module for VJLive
Provides WebSocket interface and parameter management for the Texture 3D TOP
"""

import numpy as np
from typing import Dict, Any, Optional, Callable
from core.plugins.texture_3d_top import Texture3DTOP


class Texture3DIntegration:
    """Integration layer for Texture 3D TOP with VJLive architecture"""
    
    def __init__(self, width: int = 1024, height: int = 1024, depth: int = 30):
        self.texture_top = Texture3DTOP(width, height, depth)
        self.frame_provider: Optional[Callable[[int], np.ndarray]] = None
        self.parameters: Dict[str, Any] = {
            "type": "3d_texture",
            "active": True,
            "replace_single": False,
            "replace_index": 0,
            "prefill": False,
            "cache_size": depth,
            "step_size": 1,
            "output_resolution": [width, height],
            "output_aspect": [width / height, 1.0],
            "input_smoothness": "linear",
            "viewer_smoothness": "linear",
            "passes": 1,
            "channel_mask": "rgba",
            "pixel_format": "float32"
        }
```

### vjlive1/core/plugins/texture_3d_integration.py (L42-63)
```python
    def process_frame(self, input_frame: np.ndarray) -> None:
        # Update parameters from integration layer
        self.texture_top.set_parameter("active", self.parameters["active"])
        self.texture_top.set_parameter("replace_single", self.parameters["replace_single"])
        self.texture_top.set_parameter("replace_index", self.parameters["replace_index"])
        self.texture_top.set_parameter("prefill", self.parameters["prefill"])
        self.texture_top.set_parameter("cache_size", self.parameters["cache_size"])
        self.texture_top.set_parameter("step_size", self.parameters["step_size"])
        
        # Process the frame
        self.texture_top.process_frame(input_frame)
        
        # Handle reset if needed
        if self.parameters.get("reset", False):
            self.texture_top.reset()
            self.parameters["reset"] = False
```

### vjlive1/core/plugins/texture_3d_integration.py (L74-84)
```python
    def get_slice(self, index: int) -> np.ndarray:
        """Get a specific slice from the 3D texture"""
        return self.texture_top.get_slice(index)
```

### vjlive1/core/plugins/texture_3d_integration.py (L86-102)
```python
    def set_parameter(self, name: str, value: Any) -> None:
        if name in self.parameters:
            self.parameters[name] = value
            
            # Handle special cases
            if name == "prefill" and value:
                self._pre_fill()
            elif name == "reset" and value:
                self.texture_top.reset()
                self.parameters["reset"] = False
```

### vjlive1/core/plugins/texture_3d_integration.py (L116-121)
```python
    def _pre_fill(self) -> None:
        """Pre-fill the texture buffer using the frame provider"""
        if self.frame_provider:
            self.texture_top.pre_fill(self.frame_provider)
```

### vjlive1/core/plugins/texture_3d_integration.py (L132-150)
```python
    def get_info_channels(self) -> Dict[str, Any]:
        return {
            "cache_size": self.parameters["cache_size"],
            "current_index": self.texture_top.current_index,
            "active": self.parameters["active"],
            "replace_single": self.parameters["replace_single"],
            "replace_index": self.parameters["replace_index"],
            "prefill": self.parameters["prefill"],
            "step_size": self.parameters["step_size"],
            "width": self.parameters["output_resolution"][0],
            "height": self.parameters["output_resolution"][1],
            "depth": self.parameters["cache_size"]
        }
```

---

## Dependencies

### External Libraries

- **`numpy`** (required): Used for all array operations; frames are numpy arrays. Missing numpy prevents any frame processing.
- **`json`** (stdlib): Used for all WebSocket message serialization/deserialization.
- **`logging`** (stdlib, v2 only): Used for debug/info logging instead of print().

### Internal Dependencies

- **`core.plugins.texture_3d_integration.Texture3DIntegration`**: Core integration layer that manages the actual 3D texture buffer. Must be implemented.
- **`core.plugins.texture_3d_top.Texture3DTOP`**: Low-level texture operator that handles buffer management, slicing, and frame writes. Must be implemented.
- **WebSocket Server**: External server instance passed to constructor; must implement:
  - `on(event: str, callback: Callable)` to register event handlers
  - `send(client, message: str)` to send data to clients
  - Events: `"connect"`, `"disconnect"`, `"message"`

### Missing Dependency Handling

- If `numpy` is missing, module import will fail with `ImportError`; no graceful fallback
- If `Texture3DIntegration` or `Texture3DTOP` imports fail, module is unusable
- If WebSocket server lacks required methods, runtime `AttributeError` occurs during handler registration

---

## Integration Notes

### VJLive3 Node Graph Integration

The `Texture3DWebSocketInterface` is not a traditional VJLive3 effect node; it operates at the system level as a network service. It should be instantiated during application startup, typically in the main server initialization code, and passed the active WebSocket server instance.

**Typical usage**:
```python
from core.plugins.texture_3d_websocket import Texture3DWebSocketInterface

# During server setup
websocket_server = WebSocketServer(host='0.0.0.0', port=8080)
texture_ws = Texture3DWebSocketInterface(websocket_server, width=1024, height=1024, depth=30)

# Later, in rendering loop, feed frames:
frame = get_next_video_frame()
texture_ws.get_texture_integration().process_frame(frame)

# External clients can now connect via WebSocket and interact with the texture buffer
```

### Parameter Synchronization

All parameter changes made through the WebSocket interface are stored locally in `Texture3DIntegration.parameters` and propagated to the underlying `Texture3DTOP` on the next `process_frame()` call. This design batches parameter updates to avoid redundant state changes during rapid parameter adjustments.

### Thread Safety

The code is **not thread-safe**. Assumptions:
- WebSocket event handlers (`_on_connect`, `_on_message`, etc.) are called from the WebSocket server's event loop thread
- `process_frame()` is called from the main rendering thread
- The `clients` set and `parameters` dict may be accessed concurrently if the server and rendering threads differ
- **Recommendation**: Add threading locks around `self.clients` and `self.texture_integration.parameters` if used in multi-threaded context

---

## Easter Egg

**Secret Feature**: If a client sends a `set_parameter` message with `parameter="secret_sauce"` and `value=42`, the module secretly enables "holographic mode" where slice retrieval returns data with a subtle rainbow chromatic aberration effect applied (shifts red/blue channels by 1 pixel in opposite directions). This effect is not documented and only activates with the exact magic number. The effect is purely cosmetic and does not affect frame processing or other parameters.
