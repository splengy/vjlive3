# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P1-LC1_Live Coding Environment.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-LC1 — Live Coding Environment

**Phase:** Phase 1 / P1-LC1
**Assigned To:** Desktop Roo Worker
**Spec Written By:** Desktop Roo Worker
**Date:** 2026-03-01

---

## What This Module Does

The Live Coding Environment provides real-time shader and effect modification capabilities during VJ performances without requiring restarts. It enables collaborative editing through WebSocket connections, allowing multiple users and AI agents to simultaneously modify shader code with immediate visual feedback. The system includes a visual node-based programming interface for creating shaders through node graphs, an AI creative assistant for code generation and suggestions, and robust error handling that displays syntax errors in the UI without crashing the performance. The core engine compiles GLSL shaders on-the-fly, manages collaborative editing sessions with conflict resolution, and provides hot-reload capabilities that swap shaders seamlessly into the rendering pipeline.

The module draws from legacy implementations in both vjlive v1 and vjlive-2, which provided file-watching-based hot reload, WebSocket collaboration, and visual node graph programming. The v1 version featured a hyper-enhanced live coding engine with comprehensive test suites, while v2 refined the architecture with modular session management and AI assistant integration.

**What This Module Does NOT Do**

- Handle persistent storage of shader files (relies on external file system)
- Provide a built-in code editor UI (integrates with Monaco/VSCode via external components)
- Perform audio analysis or provide audio-reactive uniforms directly (receives audio data from external systems)
- Manage project version control beyond session-based undo/redo
- Execute arbitrary Python code during live coding (restricted to GLSL shader compilation)
- Support 3D model loading or geometry manipulation beyond fragment shaders

---

## Detailed Behavior and Parameter Interactions

### Core Engine Operation

The `LiveCodingEngine` serves as the central coordinator, managing multiple collaborative sessions and handling shader compilation. It maintains:

- **Session Registry**: A dictionary mapping `session_id` → `CollaborativeSession` objects
- **Compilation Cache**: Stores recent compilation results `(success, error_message)` to avoid redundant compilation
- **WebSocket Connections**: Tracks active user connections `user_id → websocket_info`
- **Shader Templates**: Pre-defined shader code snippets for common use cases (basic, audio_reactive, sentience)

When a user applies an operation to a session document, the engine:
1. Delegates to `CollaborativeSession.apply_operation()` which validates the operation counter and resolves conflicts
2. If successful, triggers `_compile_shader()` with the updated document
3. Caches the compilation result and broadcasts the operation to other session participants

### Collaborative Session Management

Each `CollaborativeSession` implements a real-time collaborative editing system inspired by Operational Transformation (OT) principles:

- **Document State**: A single string containing the complete shader source code
- **Operation Log**: Chronological list of all applied operations `{type, position, text, counter, timestamp, user_id}`
- **User Counters**: Per-user integer counters ensuring operations are applied in order
- **Conflict Resolution**: Position-based conflict detection using `_operations_conflict()` examining the last 10 operations

The session enforces strict ordering: each user's operations must have sequentially incrementing counters. When a user attempts to apply operation with counter N+1, the system checks for position conflicts with recent operations from other users. If no conflict, the operation is applied; if conflict, it's rejected with an error.

**Parameter Mappings**:
- `cell_size` (0-10) → actual pixel size: `mix(4.0, 32.0, cell_size / 10.0)`
- `charset` (0-10) → charset ID: `int(charset / 10.0 * 4.0 + 0.5)` (0=classic, 1=blocks, 2=braille, 3=matrix, 4=binary)
- `color_mode` (0-10) → mode ID: `int(color_mode / 10.0 * 5.0 + 0.5)` (0=mono_green, 1=mono_amber, 2=original, 3=hue_shift, 4=rainbow, 5=thermal)

### Visual Node Graph Programming

The `VisualProgrammingInterface` allows users to construct shaders by connecting nodes:

- **Node Types**: Input, Output, Math, Time, UV, Color, Audio, Sentience
- **Connections**: Directed edges from output ports to input ports
- **Code Generation**: Traverses the node graph, generating GLSL code for each node and wiring variables

The code generation process:
1. Collects all uniform declarations (time, resolution, audio/sentience uniforms)
2. Generates variable declarations and computations for each non-output node
3. Generates the final `gl_FragColor` assignment in the output node
4. Wires variables by using `{node_id}.{output_port}` as variable names

**Math Node Operations**: add, subtract, multiply, divide, sin, cos
**Color Node Operations**: rgb_to_hsv, hsv_to_rgb, brightness, contrast

### AI Creative Assistant

The `AICreativeAssistant` provides style templates, pattern library, and code suggestions:

- **Style Templates**: glitch, retro, organic — each with code snippets and parameters
- **Pattern Library**: Stripes, Circles, Noise — parameterized procedural patterns
- **Suggestion Engine**: Analyzes current code for features (sin/cos usage, color operations, audio/sentience context) and returns relevant modifications
- **Error Detection**: Basic syntax checking for missing declarations, unmatched parentheses/braces
- **Improvement Suggestions**: Performance tips (sin/cos approximations, textureLod) and code organization advice

### WebSocket Server

`LiveCodingWebSocketServer` runs an asynchronous WebSocket server handling:

- **Message Types**: join_session, leave_session, operation, request_document, request_suggestions, compile_shader, get_templates, get_patterns, apply_style, detect_errors, suggest_improvements
- **Broadcasting**: Real-time operation propagation to all session participants except the originator
- **Connection Management**: Automatic cleanup of disconnected users from sessions

The server starts in a background thread (`start_server_sync()`) and runs an async event loop handling each connection independently.

---

## Public Interface

### CollaborativeSession

```python
class CollaborativeSession:
    def __init__(self, session_id: str, max_users: int = 10) -> None
    def add_user(self, user_id: str, user_info: Dict) -> bool
    def remove_user(self, user_id: str) -> None
    def update_cursor(self, user_id: str, position: int) -> None
    def apply_operation(self, user_id: str, operation: Dict) -> bool
    def get_document_info(self) -> Dict
    def get_user_list(self) -> List[Dict]
    def get_operation_log(self, since: Optional[float] = None) -> List[Dict]
    def is_active(self) -> bool

    # Internal methods (not part of public API)
    def _calculate_hash(self, content: str) -> str
    def _apply_operation_to_document(self, operation: Dict) -> bool
    def _resolve_conflict(self, user_id: str, operation: Dict) -> bool
    def _operations_conflict(self, op1: Dict, op2: Dict) -> bool
    def _generate_user_color(self) -> Tuple[float, float, float]
```

**Operation Dictionary Format**:
```python
{
    'type': 'insert' | 'delete',      # Operation type
    'position': int,                   # Character position in document
    'text': str,                       # Text to insert or delete
    'counter': int,                    # User's sequential operation counter
    # 'timestamp': float,              # Added automatically
    # 'user_id': str                   # Added automatically
}
```

### LiveCodingEngine

```python
class LiveCodingEngine:
    def __init__(self) -> None
    def create_session(self, user_id: str, user_info: Dict) -> str
    def join_session(self, user_id: str, user_info: Dict, session_id: str) -> bool
    def leave_session(self, user_id: str, session_id: str) -> None
    def apply_operation(self, user_id: str, session_id: str, operation: Dict) -> Tuple[bool, str]
    def get_session_info(self, session_id: str) -> Optional[Dict]
    def compile_shader(self, session_id: str) -> Tuple[bool, str]
    def get_active_sessions(self) -> List[str]
    def add_websocket_connection(self, user_id: str, websocket) -> None
    def remove_websocket_connection(self, user_id: str) -> None
    def broadcast_to_session(self, session_id: str, message: Dict) -> None

    # Internal methods
    def _compile_shader(self, shader_code: str) -> Tuple[bool, str]
    def _generate_session_id(self) -> str
```

**Shader Compilation Process**:
The `_compile_shader()` method wraps user code with:
- Uniform declarations: `time`, `resolution`, `volume`, `bass`, `mid`, `treble`, `sentience`
- A vertex shader that passes through positions and texture coordinates
- A fragment shader main that calls the user's `main()` function
- Backface culling fix: `if (!gl_FrontFacing) uv = vec2(1.0) - uv;`

### VisualProgrammingInterface

```python
class VisualNode:
    def __init__(self, node_id: str, node_type: str, position: Tuple[float, float],
                 name: str, description: str, inputs: List[str],
                 outputs: List[str], code: str, category: str) -> None
    # Attributes:
    #   node_id: str
    #   node_type: str
    #   position: Tuple[float, float]
    #   name: str
    #   description: str
    #   inputs: List[str]
    #   outputs: List[str]
    #   code: str
    #   category: str
    #   size: Tuple[int, int] = (200, 100)
    #   color: Tuple[float, float, float]

class Connection:
    def __init__(self, output_node_id: str, output_port: str,
                 input_node_id: str, input_port: str) -> None

class VisualProgrammingInterface:
    def __init__(self) -> None
    def create_node(self, node_type: str, node_id: str, position: Tuple[float, float]) -> VisualNode
    def connect_nodes(self, output_node_id: str, output_port: str,
                      input_node_id: str, input_port: str) -> bool
    def generate_shader_code(self) -> str
    def _get_node_types(self) -> Dict[str, Dict]
    def _generate_node_code(self, node: VisualNode) -> str
    def _generate_math_node_code(self, node: VisualNode, config: Dict) -> str
    def _generate_color_node_code(self, node: VisualNode, config: Dict) -> str
    def _generate_output_code(self, node: VisualNode) -> str
```

**Node Type Definitions** (from `_get_node_types()`):
- `input`: Uniform float `input_value`
- `output`: Sets `gl_FragColor = vec4(color, 1.0)`
- `math`: Operations: add, subtract, multiply, divide, sin, cos; inputs: `a`, `b`; output: `result`
- `time`: Injects `float time = $TIME;` (replaced during generation)
- `uv`: Injects `vec2 uv = gl_FragCoord.xy / resolution.xy;`
- `color`: Operations: rgb_to_hsv, hsv_to_rgb, brightness, contrast; input: `color`; output: `result`
- `audio`: Injects `volume`, `bass`, `mid`, `treble` uniforms
- `sentience`: Injects `sentience` uniform

### AICreativeAssistant

```python
class AICreativeAssistant:
    def __init__(self) -> None
    def suggest_modification(self, current_code: str, context: Dict) -> Dict
    def generate_pattern(self, pattern_name: str, parameters: Dict) -> str
    def apply_style(self, current_code: str, style_name: str) -> str
    def detect_errors(self, shader_code: str) -> List[str]
    def suggest_improvements(self, shader_code: str) -> List[str]

    # Internal methods
    def _load_style_templates(self) -> Dict[str, Dict]
    def _load_pattern_library(self) -> List[Dict]
```

**Style Template Structure**:
```python
{
    'description': str,
    'code': str,           # GLSL code to inject
    'parameters': Dict[str, Any]
}
```

**Pattern Library Entry**:
```python
{
    'name': str,
    'description': str,
    'code': str,
    'parameters': Dict[str, Any]
}
```

**Suggestion Return Format**:
```python
{
    'type': str,           # e.g., 'enhance_oscillation', 'audio_reactivity'
    'description': str,
    'suggestion': str,
    'code': str
}
```

### LiveCodingWebSocketServer

```python
class LiveCodingWebSocketServer:
    def __init__(self, host: str = 'localhost', port: int = 8765, start_immediately: bool = True) -> None
    def start_server_sync(self) -> None
    async def start_server(self) -> None
    async def handle_connection(self, websocket, path) -> None
    async def handle_join_session(self, websocket, data) -> None
    async def handle_leave_session(self, websocket, data) -> None
    async def handle_operation(self, websocket, data) -> None
    async def handle_document_request(self, websocket, data) -> None
    async def handle_suggestions_request(self, websocket, data) -> None
    async def handle_compile_request(self, websocket, data) -> None
    async def handle_templates_request(self, websocket, data) -> None
    async def handle_patterns_request(self, websocket, data) -> None
    async def handle_style_request(self, websocket, data) -> None
    async def handle_errors_request(self, websocket, data) -> None
    async def handle_improvements_request(self, websocket, data) -> None

    # Internal broadcasting
    def _broadcast_session_update(self, session_id: str, user_id: str, action: str) -> None
    def _broadcast_operation(self, session_id: str, user_id: str, operation: Dict) -> None
```

**WebSocket Message Protocol**:

Client → Server:
```json
{
  "type": "join_session" | "leave_session" | "operation" | "request_document" | 
         "request_suggestions" | "compile_shader" | "get_templates" | "get_patterns" |
         "apply_style" | "detect_errors" | "suggest_improvements",
  "session_id": str (optional, required for session operations),
  "user_id": str,
  "user_info": Dict (for join),
  "operation": Dict (for operation),
  "current_code": str (for suggestions),
  "shader_code": str (for error detection),
  "style_name": str (for apply_style),
  "pattern_name": str (for get_patterns),
  "parameters": Dict (for get_patterns),
  "audio": bool, "sentience": bool (for suggestions context)
}
```

Server → Client:
```json
{
  "type": "session_info" | "operation_response" | "document_info" | "suggestions" |
         "compilation_result" | "templates" | "pattern" | "style_application" |
         "errors" | "improvements" | "session_update",
  "session_id": str,
  "session_info": Dict (for session_info),
  "success": bool, "message": str (for operation_response, style_application),
  "suggestion": Dict (for suggestions),
  "error_message": str (for compilation_result),
  "templates": Dict (for templates),
  "pattern_name": str, "code": str (for pattern),
  "new_code": str (for style_application),
  "errors": List[str] (for errors),
  "suggestions": List[str] (for improvements),
  "action": str ("joined"|"left"), "users": List[Dict] (for session_update)
}
```

**Helper Function**:
```python
def start_live_coding_server(host: str = 'localhost', port: int = 8765) -> LiveCodingWebSocketServer:
    """Start the live coding WebSocket server in a background thread"""
```

---

## Inputs and Outputs

### CollaborativeSession

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `session_id` | `str` | Unique session identifier | UUID4 format |
| `max_users` | `int` | Maximum concurrent users | 1 ≤ max_users ≤ 100 |
| `user_id` | `str` | Unique user identifier | Non-empty string |
| `user_info` | `Dict` | User metadata (name, color, etc.) | At least `{'name': str}` |
| `operation` | `Dict` | Edit operation | Must have `type`, `position`, `text`, `counter` |
| `since` | `Optional[float]` | Timestamp filter for operation log | Unix timestamp or None |

**Outputs**:
- `add_user()` → `bool`: `True` if user added, `False` if session full
- `apply_operation()` → `bool`: `True` if operation applied, `False` if conflict/invalid
- `get_document_info()` → `Dict`: Contains `session_id`, `document`, `document_hash`, `creation_time`, `last_activity`, `user_count`, `users`
- `get_user_list()` → `List[Dict]`: Each entry has `user_id`, `info`, `joined_at`, `last_active`, `cursor_position`, `color`
- `get_operation_log()` → `List[Dict]`: Copy of operation log (filtered if `since` provided)
- `is_active()` → `bool`: `True` if users present and activity within 1 hour

### LiveCodingEngine

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `user_id` | `str` | Unique user identifier | Non-empty string |
| `session_id` | `str` | Session identifier | Must exist in `sessions` |
| `shader_code` | `str` | GLSL fragment shader code | Must contain `void main()` |
| `websocket` | `WebSocket` | Active WebSocket connection | Must be open |

**Outputs**:
- `create_session()` / `join_session()` → `str` / `bool`: Session ID or success flag
- `apply_operation()` → `Tuple[bool, str]`: Success flag and message
- `get_session_info()` → `Optional[Dict]`: Session info or `None` if not found
- `compile_shader()` → `Tuple[bool, str]`: Compilation success and error message (empty string if success)
- `get_active_sessions()` → `List[str]`: List of active session IDs

### VisualProgrammingInterface

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `node_type` | `str` | Type of node to create | Must be in `node_types` |
| `node_id` | `str` | Unique node identifier | Non-empty, unique within interface |
| `position` | `Tuple[float, float]` | X,Y position for node display | Coordinates in pixels |
| `output_node_id` | `str` | Source node ID | Must exist in `nodes` |
| `input_node_id` | `str` | Destination node ID | Must exist in `nodes` |
| `output_port` | `str` | Output port name on source node | Must be in `output_node.outputs` |
| `input_port` | `str` | Input port name on destination node | Must be in `input_node.inputs` |

**Outputs**:
- `create_node()` → `VisualNode`: Created node object
- `connect_nodes()` → `bool`: `True` if connection created, `False` if ports/nodes invalid
- `generate_shader_code()` → `str`: Complete GLSL shader source code

**Generated Code Structure**:
```glsl
uniform float time;
uniform vec2 resolution;
uniform float volume;
uniform float bass;
uniform float mid;
uniform float treble;
uniform float sentience;

// Node variable declarations (e.g., float math1 = ...)
// ...

void main() {
  vec2 uv = gl_FragCoord.xy / resolution.xy;
  if (!gl_FrontFacing) {
    uv = vec2(1.0) - uv;
  }
  main();  // User's main function from document
}
```

### AICreativeAssistant

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `current_code` | `str` | Current shader source code | Non-empty string |
| `context` | `Dict` | Context flags | Keys: `audio` (bool), `sentience` (bool) |
| `pattern_name` | `str` | Pattern to generate | Must match library entry |
| `parameters` | `Dict` | Pattern parameters | Keys depend on pattern |
| `style_name` | `str` | Style template to apply | Must be in style templates |
| `shader_code` | `str` | Shader to analyze | Non-empty string |

**Outputs**:
- `suggest_modification()` → `Dict`: Suggestion with `type`, `description`, `suggestion`, `code`
- `generate_pattern()` → `str`: Generated GLSL code snippet
- `apply_style()` → `str`: Modified shader code with style injected
- `detect_errors()` → `List[str]`: List of error messages (empty if no errors)
- `suggest_improvements()` → `List[str]`: List of improvement suggestions

---

## Edge Cases and Error Handling

### Session Management

**User Limit Exceeded**:
- `CollaborativeSession.add_user()` returns `False` when `len(users) >= max_users`
- Engine should propagate this to client with descriptive message

**Session Not Found**:
- All engine methods return appropriate error tuples or `None` when `session_id` not in `sessions`
- WebSocket handler sends error response with `"Session not found"` message

**WebSocket Disconnection**:
- Automatic cleanup: when a websocket closes, `leave_session()` and `remove_websocket_connection()` are called
- If session becomes empty, session is deleted from `engine.sessions` and removed from `active_sessions`

### Operation Conflicts

**Counter Mismatch**:
- If `operation['counter'] != user_counters[user_id] + 1`, conflict resolution is triggered
- `_resolve_conflict()` examines last 10 operations for position conflicts
- If conflict detected, operation is rejected; user must re-sync document

**Invalid Positions**:
- Insert: `position < 0` or `position > len(document)` → reject
- Delete: `position < 0` or `position + len(text) > len(document)` → reject

**Concurrent Edits**:
- Two inserts at overlapping positions within character length threshold → conflict
- Insert-delete overlap within max(text lengths) → conflict
- Delete-delete overlap within max(delete lengths) → conflict

### Shader Compilation

**Compilation Failures**:
- OpenGL compilation exceptions are caught and error messages parsed
- Line number extraction from `"ERROR: 0:{line}:{col}: {msg}"` format
- Error message is cached and returned to client
- No exception propagates to engine main loop

**Missing Uniforms**:
- User code may reference uniforms without declaring them; `detect_errors()` checks for this
- However, compilation will still succeed if uniforms are implicitly provided by the wrapper

**Syntax Errors**:
- `detect_errors()` performs basic checks: missing `void main()`, missing `out vec4` for `gl_FragColor`, unmatched parentheses/braces
- These are warnings, not blocking errors

### Node Graph

**Unknown Node Type**:
- `create_node()` raises `ValueError` if `node_type` not in `node_types`
- Client should validate node type before creation

**Invalid Connections**:
- `connect_nodes()` returns `False` if either node doesn't exist or specified ports don't exist
- No exception raised; client receives boolean

**Empty Graph**:
- `generate_shader_code()` returns `"// Empty shader graph"` if no nodes or connections
- Returns `"// No output node found"` if no node of type `'output'` exists

### AI Assistant

**Unknown Pattern**:
- `generate_pattern()` returns `"// Unknown pattern"` if pattern name doesn't match
- Client should validate pattern name against library

**Style Application to Empty Code**:
- `apply_style()` appends style code if no `void main()` found
- If `void main()` exists, style code is inserted before it

**Error Detection Robustness**:
- `detect_errors()` catches exceptions during line-by-line analysis and logs them, returning partial results
- Does not crash on malformed code

---

## Mathematical Formulations

### Parameter Remapping (from legacy v1 code)

All user-facing parameters use a normalized 0.0–10.0 range. The system remaps these to actual shader values using linear interpolation:

```python
def remap(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    return out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min)
```

**Specific Mappings**:

- `cell_size`: `4.0 + (cell_size / 10.0) * (32.0 - 4.0)` → `[4, 32]` pixels per character
- `aspect_correct`: `0.4 + (aspect_correct / 10.0) * (1.0 - 0.4)` → `[0.4, 1.0]` character aspect ratio
- `charset` → `int(charset / 10.0 * 4.0 + 0.5)` → `{0, 1, 2, 3, 4}` (5 charsets)
- `threshold_curve`: `0.3 + (threshold_curve / 10.0) * (3.0 - 0.3)` → `[0.3, 3.0]` luminance mapping gamma
- `edge_detect`: `edge_detect / 10.0` → `[0, 1]` mix factor
- `detail_boost`: `(detail_boost / 10.0) * 3.0` → `[0, 3]` contrast boost
- `color_mode` → `int(color_mode / 10.0 * 5.0 + 0.5)` → `{0,1,2,3,4,5}` (6 modes)
- `fg_brightness`: `0.3 + (fg_brightness / 10.0) * (3.0 - 0.3)` → `[0.3, 3.0]`
- `bg_brightness`: `(bg_brightness / 10.0) * 0.5` → `[0, 0.5]`
- `saturation`: `(saturation / 10.0) * 2.0` → `[0, 2.0]`
- `hue_offset`: `hue_offset / 10.0` → `[0, 1]` normalized hue shift
- `scanlines`: `scanlines / 10.0` → `[0, 1]` intensity
- `phosphor_glow`: `(phosphor_glow / 10.0) * 2.0` → `[0, 2]` radius
- `flicker`: `(flicker / 10.0) * 0.1` → `[0, 0.1]` brightness variation
- `scroll_speed`: `-5.0 + (scroll_speed / 10.0) * 10.0` → `[-5, 5]` units per second
- `rain_density`: `rain_density / 10.0` → `[0, 1]` probability
- `char_jitter`: `char_jitter / 10.0` → `[0, 1]` probability
- `wave_amount`: `(wave_amount / 10.0) * 0.5` → `[0, 0.5]` displacement
- `wave_freq`: `1.0 + (wave_freq / 10.0) * (20.0 - 1.0)` → `[1, 20]` Hz

### Conflict Resolution Algorithm

For two operations `op1` and `op2`:

```python
def operations_conflict(op1, op2):
    type1, type2 = op1['type'], op2['type']
    pos1, pos2 = op1['position'], op2['position']
    len1 = len(op1.get('text', ''))
    len2 = len(op2.get('text', ''))
    
    if type1 == 'insert' and type2 == 'insert':
        return abs(pos1 - pos2) < max(len1, len2)
    elif (type1 == 'insert' and type2 == 'delete') or (type1 == 'delete' and type2 == 'insert'):
        return abs(pos1 - pos2) < max(len1, len2)
    elif type1 == 'delete' and type2 == 'delete':
        return abs(pos1 - pos2) < max(len1, len2)
    return False
```

The conflict threshold is the maximum of the two operation's text lengths. If the absolute position difference is less than this threshold, the operations are considered conflicting because they affect overlapping regions of the document.

### Hash Calculation

Document integrity is verified using SHA-256:

```python
hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
```

This 64-character hex string is used to detect any document modifications.

### User Color Generation

Pseudo-random RGB color generation:

```python
seed = int(time.time() * 1000) % (2**32 - 1)
np.random.seed(seed)
color = tuple(np.random.rand(3))  # Each component in [0.0, 1.0]
```

Note: This is not cryptographically secure but sufficient for UI differentiation.

---

## Performance Characteristics

### Hot Reload Latency

Target: `<500ms` from file save to shader active on GPU

**Breakdown**:
- File system watcher detection: ~50-100ms (depends on OS)
- Syntax validation: ~5-10ms
- Shader compilation (1080p fragment shader): `<100ms` on modern GPU
- Program linking and uniform setup: ~10-20ms
- Texture/buffer re-binding: ~5ms

**Total**: ~70-135ms + watcher delay = well under 500ms target

### Compilation Performance

- **Vertex Shader**: Static, compiled once per session, negligible time
- **Fragment Shader**: Complexity-dependent; simple shaders `<50ms`, complex with multiple texture lookups `50-150ms`
- **Compute Shaders**: Not currently supported in this module

**Memory Usage**:
- Each compiled shader program: ~100-500KB GPU memory
- Compilation cache: Stores `(bool, str)` per session; negligible
- Session state: ~1-10KB per session (document text, operation log, user list)

### WebSocket Throughput

- **Operation Message Size**: ~100-500 bytes (JSON with small text snippets)
- **Broadcast Latency**: ~1-5ms on local network, ~10-50ms over internet
- **Concurrent Sessions**: Engine can handle 100+ sessions; each session limited to 20 users
- **Message Rate**: Each user typing at ~5 chars/sec → ~5 operations/sec → ~500 bytes/sec per user

### Node Graph Code Generation

- **Node Count**: 10-50 nodes typical; code generation time `<5ms`
- **Connection Count**: Linear with nodes; `O(nodes)` traversal
- **Shader Compilation**: Same as hot reload latency above

### AI Assistant Performance

- **Pattern Generation**: `<10ms` (string templating)
- **Style Application**: `<5ms` (string insertion)
- **Error Detection**: `<20ms` for 500-line shader (line-by-line scan)
- **Suggestion Generation**: `<50ms` (rule-based analysis, no LLM inference)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_session_creation` | `LiveCodingEngine.create_session()` returns valid UUID and session is stored |
| `test_session_join_existing` | `join_session()` adds user to existing session, returns `True` |
| `test_session_join_nonexistent` | `join_session()` returns `False` for invalid session ID |
| `test_session_leave` | `leave_session()` removes user; session deleted if empty |
| `test_operation_insert` | `apply_operation()` with `type='insert'` modifies document correctly |
| `test_operation_delete` | `apply_operation()` with `type='delete'` removes text correctly |
| `test_operation_invalid_position` | Insert/delete with out-of-bounds position returns `False` |
| `test_operation_counter_enforcement` | Operations must have sequential counters; gap causes conflict resolution |
| `test_conflict_detection_insert_insert` | Overlapping inserts from different users conflict |
| `test_conflict_detection_insert_delete` | Insert and delete on overlapping positions conflict |
| `test_conflict_resolution_non_overlapping` | Non-overlapping operations succeed even with counter gaps |
| `test_document_hash_updates` | `document_hash` updates after each successful operation |
| `test_user_color_generation` | `_generate_user_color()` returns 3-tuple of floats in [0,1] |
| `test_shader_compilation_success` | Valid shader code compiles without errors |
| `test_shader_compilation_syntax_error` | Missing `void main()` or invalid GLSL returns error with line number |
| `test_shader_compilation_missing_uniform` | Using undeclared uniform triggers error detection but may compile (wrapper provides) |
| `test_websocket_join_session` | Client joining via WebSocket creates/joins session and receives session info |
| `test_websocket_operation_broadcast` | Operation from one client broadcast to others (excluding sender) |
| `test_websocket_disconnect_cleanup` | Disconnected client removed from session automatically |
| `test_visual_node_creation` | `VisualProgrammingInterface.create_node()` creates node with correct attributes |
| `test_visual_node_connection` | `connect_nodes()` succeeds only with valid nodes and ports |
| `test_visual_code_generation_empty` | Empty graph returns `"// Empty shader graph"` |
| `test_visual_code_generation_no_output` | Graph without output node returns `"// No output node found"` |
| `test_visual_code_generation_simple` | Single input→math→output chain generates valid GLSL |
| `test_ai_suggestion_oscillation` | Code with `sin(` triggers `enhance_oscillation` suggestion |
| `test_ai_suggestion_color` | Code with `vec3` and `color` triggers `color_variation` suggestion |
| `test_ai_suggestion_audio` | With `audio=True` context, suggests audio reactivity |
| `test_ai_suggestion_sentience` | With `sentience=True` context, suggests sentience reactivity |
| `test_ai_pattern_generation` | `generate_pattern('Stripes', {'frequency': 20.0})` replaces default frequency |
| `test_ai_style_application` | `apply_style('glitch')` inserts glitch code before `void main()` |
| `test_ai_error_detection` | `detect_errors()` finds missing `void main()` and unmatched parentheses |
| `test_ai_improvement_suggestions` | Shader with multiple `sin/cos` and `texture` calls returns performance tips |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-LC1: Live Coding Environment` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive-v1/core/live_coding_engine.py (L1-200)
```python
"""
Hyper-Enhanced Live Coding Engine with Collaborative Features
Real-time shader modification, AI assistance, and visual programming
"""

import asyncio
import websockets
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Callable, Any
import threading
import re
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import websockets.exceptions


class CollaborativeSession:
    """
    Real-time collaborative coding session
    """

    def __init__(self, session_id: str, max_users: int = 10):
        self.session_id = session_id
        self.max_users = max_users
        self.users: Dict[str, Dict] = {}
        self.document: str = """# Welcome to VJLive Live Coding!
// This is a collaborative shader editor
// Changes appear instantly for all users

void main() {
 // Your shader code here
 gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); // Default: red
}"""
        self.document_hash: str = self._calculate_hash(self.document)
        self.operation_log: List[Dict] = []
        self.creation_time = time.time()
        self.last_activity = time.time()
        self.user_counters: Dict[str, int] = {}
```

### vjlive-v1/core/live_coding_engine.py (L217-435)
```python
class LiveCodingEngine:
    """
    Main live coding engine with real-time compilation and error handling
    """

    def __init__(self):
        self.sessions: Dict[str, CollaborativeSession] = {}
        self.active_sessions: List[str] = []
        self.compilation_cache: Dict[str, Tuple[bool, str]] = {}
        self.websocket_connections: Dict[str, Dict] = {}
        self.templates = {
            'basic': '''
// Basic shader template
void main() {
 vec2 uv = gl_FragCoord.xy / resolution.xy;
 vec3 color = vec3(uv.x, uv.y, 0.5);
 gl_FragColor = vec4(color, 1.0);
}''',
            'audio_reactive': '''
// Audio-reactive shader template
uniform float time;
uniform vec2 resolution;
uniform float volume;
uniform float bass;
uniform float mid;
uniform float treble;

void main() {
 vec2 uv = gl_FragCoord.xy / resolution.xy;
 float audio = volume + bass * 0.5 + mid * 0.3 + treble * 0.2;
 vec3 color = vec3(sin(time + uv.x * 10.0) * audio,
 cos(time + uv.y * 8.0) * audio,
 sin(time + (uv.x + uv.y) * 12.0) * audio);
 gl_FragColor = vec4(color, 1.0);
}''',
            'sentience': '''
// Sentience-reactive shader template
uniform float time;
uniform vec2 resolution;
uniform float sentience;

void main() {
 vec2 uv = gl_FragCoord.xy / resolution.xy;
 float consciousness = sentience * 0.5 + 0.5;
 vec3 color = vec3(sin(time * consciousness),
 cos(time * consciousness * 1.5),
 sin(time * consciousness * 2.0));
 gl_FragColor = vec4(color * consciousness, 1.0);
}'''
        }

    def create_session(self, user_id: str, user_info: Dict) -> str:
        session_id = self._generate_session_id()
        session = CollaborativeSession(session_id, max_users=20)
        session.add_user(user_id, user_info)
        self.sessions[session_id] = session
        self.active_sessions.append(session_id)
        return session_id

    def apply_operation(self, user_id: str, session_id: str, operation: Dict) -> Tuple[bool, str]:
        if session_id not in self.sessions:
            return False, "Session not found"
        session = self.sessions[session_id]
        success = session.apply_operation(user_id, operation)
        if success:
            compilation_success, error_message = self._compile_shader(session.document)
            self.compilation_cache[session_id] = (compilation_success, error_message)
            return True, "Operation applied successfully"
        else:
            return False, "Operation conflict or invalid"

    def _compile_shader(self, shader_code: str) -> Tuple[bool, str]:
        """Compile shader code"""
        try:
            complete_code = f"""
uniform float time;
uniform vec2 resolution;
uniform float volume;
uniform float bass;
uniform float mid;
uniform float treble;
uniform float sentience;

{shader_code}

void main() {{
 vec2 uv = gl_FragCoord.xy / resolution.xy;
 if (!gl_FrontFacing) {{
 uv = vec2(1.0) - uv;
 }}
 main(); // Call user's main function
}}
"""
            vertex_shader_source = """
#version 330 core
layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoords;
out vec2 TexCoords;
void main() {{
 gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0);
 TexCoords = aTexCoords;
}}
"""
            vertex_shader = compileShader(vertex_shader_source, GL_VERTEX_SHADER)
            fragment_shader = compileShader(complete_code, GL_FRAGMENT_SHADER)
            program = compileProgram(vertex_shader, fragment_shader)
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            return True, "Compilation successful"
        except Exception as e:
            error_message = str(e)
            if "ERROR: 0:" in error_message:
                line_info = error_message.split("ERROR: 0:")[1].split(':')[0]
                error_message = f"Line {line_info}: {str(e)}"
            return False, error_message
```

### vjlive-v1/core/live_coding_engine.py (L437-754)
```python
class VisualNode:
    """Visual node in the node-based programming interface"""
    def __init__(self, node_id: str, node_type: str, position: Tuple[float, float],
                 name: str, description: str, inputs: List[str],
                 outputs: List[str], code: str, category: str):
        self.node_id = node_id
        self.node_type = node_type
        self.position = position
        self.name = name
        self.description = description
        self.inputs = inputs
        self.outputs = outputs
        self.code = code
        self.category = category
        self.size = (200, 100)
        self.color = self._generate_node_color(category)

class Connection:
    """Connection between nodes"""
    def __init__(self, output_node_id: str, output_port: str,
                 input_node_id: str, input_port: str):
        self.output_node_id = output_node_id
        self.output_port = output_port
        self.input_node_id = input_node_id
        self.input_port = input_port

class VisualProgrammingInterface:
    """Visual node-based programming interface for shader creation"""
    def __init__(self):
        self.nodes: Dict[str, VisualNode] = {}
        self.connections: List[Connection] = []
        self.node_types = self._get_node_types()

    def _get_node_types(self) -> Dict[str, Dict]:
        return {
            'input': {'name': 'Input', 'description': 'Input parameters', 'inputs': [], 'outputs': ['value'], 'code': 'uniform float input_value;', 'category': 'Input'},
            'output': {'name': 'Output', 'description': 'Output color', 'inputs': ['color'], 'outputs': [], 'code': 'gl_FragColor = vec4(color, 1.0);', 'category': 'Output'},
            'math': {'name': 'Math', 'description': 'Mathematical operations', 'inputs': ['a', 'b'], 'outputs': ['result'], 'code': 'float result = a + b;', 'category': 'Math', 'operations': ['add', 'subtract', 'multiply', 'divide', 'sin', 'cos']},
            'time': {'name': 'Time', 'description': 'Time-based values', 'inputs': [], 'outputs': ['time'], 'code': 'float time = $TIME;', 'category': 'Input'},
            'uv': {'name': 'UV', 'description': 'Texture coordinates', 'inputs': [], 'outputs': ['uv'], 'code': 'vec2 uv = gl_FragCoord.xy / resolution.xy;', 'category': 'Input'},
            'color': {'name': 'Color', 'description': 'Color manipulation', 'inputs': ['color'], 'outputs': ['result'], 'code': 'vec3 result = color;', 'category': 'Color', 'operations': ['rgb_to_hsv', 'hsv_to_rgb', 'brightness', 'contrast']},
            'audio': {'name': 'Audio', 'description': 'Audio-reactive values', 'inputs': [], 'outputs': ['volume', 'bass', 'mid', 'treble'], 'code': 'float volume = $VOLUME; float bass = $BASS; float mid = $MID; float treble = $TREBLE;', 'category': 'Audio'},
            'sentience': {'name': 'Sentience', 'description': 'AI consciousness values', 'inputs': [], 'outputs': ['sentience'], 'code': 'float sentience = $SENTIENCE;', 'category': 'AI'}
        }

    def generate_shader_code(self) -> str:
        if not self.nodes or not self.connections:
            return "// Empty shader graph"
        output_node = None
        for node in self.nodes.values():
            if node.node_type == 'output':
                output_node = node
                break
        if not output_node:
            return "// No output node found"
        code_lines = []
        code_lines.append("uniform float time;")
        code_lines.append("uniform vec2 resolution;")
        code_lines.append("uniform float volume;")
        code_lines.append("uniform float bass;")
        code_lines.append("uniform float mid;")
        code_lines.append("uniform float treble;")
        code_lines.append("uniform float sentience;")
        for node in self.nodes.values():
            if node.node_type == 'output':
                continue
            node_code = self._generate_node_code(node)
            if node_code:
                code_lines.append(node_code)
        output_code = self._generate_output_code(output_node)
        if output_code:
            code_lines.append(output_code)
        return "\n".join(code_lines)

    def _generate_node_code(self, node: VisualNode) -> str:
        if node.node_type not in self.node_types:
            return ""
        config = self.node_types[node.node_type]
        if node.node_type == 'math':
            return self._generate_math_node_code(node, config)
        elif node.node_type == 'color':
            return self._generate_color_node_code(node, config)
        else:
            return config['code'].replace('$TIME', 'time').replace('$VOLUME', 'volume').replace('$BASS', 'bass').replace('$MID', 'mid').replace('$TREBLE', 'treble').replace('$SENTIENCE', 'sentience')

    def _generate_math_node_code(self, node: VisualNode, config: Dict) -> str:
        input_values = {}
        for conn in self.connections:
            if conn.input_node_id == node.node_id:
                output_node = self.nodes.get(conn.output_node_id)
                if output_node:
                    input_values[conn.input_port] = f"{output_node.node_id}.{output_node.outputs[0]}"
        operation = config.get('operations', ['add'])[0]
        a = input_values.get('a', '0.0')
        b = input_values.get('b', '0.0')
        if operation == 'add':
            return f"float {node.node_id} = {a} + {b};"
        elif operation == 'subtract':
            return f"float {node.node_id} = {a} - {b};"
        elif operation == 'multiply':
            return f"float {node.node_id} = {a} * {b};"
        elif operation == 'divide':
            return f"float {node.node_id} = {a} / {b};"
        elif operation == 'sin':
            return f"float {node.node_id} = sin({a});"
        elif operation == 'cos':
            return f"float {node.node_id} = cos({a});"
        return f"float {node.node_id} = 0.0;"

    def _generate_color_node_code(self, node: VisualNode, config: Dict) -> str:
        input_values = {}
        for conn in self.connections:
            if conn.input_node_id == node.node_id:
                output_node = self.nodes.get(conn.output_node_id)
                if output_node:
                    input_values[conn.input_port] = f"{output_node.node_id}.{output_node.outputs[0]}"
        operation = config.get('operations', ['rgb_to_hsv'])[0]
        color = input_values.get('color', 'vec3(1.0)')
        if operation == 'rgb_to_hsv':
            return f"vec3 {node.node_id} = rgb_to_hsv({color});"
        elif operation == 'hsv_to_rgb':
            return f"vec3 {node.node_id} = hsv_to_rgb({color});"
        elif operation == 'brightness':
            return f"vec3 {node.node_id} = {color} * 0.5;"
        elif operation == 'contrast':
            return f"vec3 {node.node_id} = ({color} - 0.5) * 2.0 + 0.5;"
        return f"vec3 {node.node_id} = vec3(1.0);"

    def _generate_output_code(self, node: VisualNode) -> str:
        input_values = {}
        for conn in self.connections:
            if conn.input_node_id == node.node_id:
                output_node = self.nodes.get(conn.output_node_id)
                if output_node:
                    input_values[conn.input_port] = f"{output_node.node_id}.{output_node.outputs[0]}"
        color = input_values.get('color', 'vec3(1.0)')
        return f"gl_FragColor = vec4({color}, 1.0);"
```

### vjlive-v1/core/live_coding_engine.py (L756-1022)
```python
class AICreativeAssistant:
    """AI assistant for creative suggestions and shader generation"""
    def __init__(self):
        self.style_templates = self._load_style_templates()
        self.pattern_library = self._load_pattern_library()

    def _load_style_templates(self) -> Dict[str, Dict]:
        return {
            'glitch': {
                'description': 'Digital glitch effects',
                'code': '''
// Add glitch effects
float glitch = sin(time * 100.0) * 0.1;
vec2 uv = gl_FragCoord.xy / resolution.xy + vec2(glitch, 0.0);
vec3 color = texture(screenTexture, uv).rgb;
''',
                'parameters': {'intensity': 0.5, 'frequency': 100.0, 'color_shift': True}
            },
            'retro': {
                'description': 'Retro/VHS effects',
                'code': '''
// Add VHS effects
vec2 uv = gl_FragCoord.xy / resolution.xy;
float scanline = sin(uv.y * 600.0 + time * 2.0) * 0.05;
vec3 color = texture(screenTexture, uv).rgb + vec3(scanline);
color += vec3(fract(sin(dot(uv, vec2(12.9898, 78.233)) * 43758.5453)) * 0.1);
''',
                'parameters': {'scanline_intensity': 0.5, 'noise_level': 0.1, 'vignette': True}
            },
            'organic': {
                'description': 'Organic/natural effects',
                'code': '''
// Add organic effects
vec2 uv = gl_FragCoord.xy / resolution.xy;
float noise = fract(sin(dot(uv * 10.0, vec2(12.9898, 78.233)) * 43758.5453));
vec3 color = texture(screenTexture, uv).rgb;
color += vec3(noise * 0.2);
color.r += sin(uv.x * 5.0 + time) * 0.1;
color.b += cos(uv.y * 3.0 + time) * 0.1;
''',
                'parameters': {'noise_intensity': 0.2, 'color_variation': 0.1, 'organic_movement': True}
            }
        }

    def _load_pattern_library(self) -> List[Dict]:
        return [
            {'name': 'Stripes', 'description': 'Vertical/horizontal stripes', 'code': '''
vec2 uv = gl_FragCoord.xy / resolution.xy;
float pattern = step(0.5, sin(uv.x * 10.0 + time));
vec3 color = vec3(pattern);
''', 'parameters': {'frequency': 10.0, 'direction': 'vertical', 'phase': 0.0}},
            {'name': 'Circles', 'description': 'Concentric circles', 'code': '''
vec2 uv = gl_FragCoord.xy / resolution.xy - 0.5;
float pattern = step(0.5, abs(sin(length(uv) * 10.0 - time)));
vec3 color = vec3(pattern);
''', 'parameters': {'frequency': 10.0, 'center': [0.5, 0.5], 'phase': 0.0}},
            {'name': 'Noise', 'description': 'Procedural noise', 'code': '''
vec2 uv = gl_FragCoord.xy / resolution.xy;
float noise = fract(sin(dot(uv * 15.0, vec2(12.9898, 78.233)) * 43758.5453));
vec3 color = vec3(noise);
''', 'parameters': {'scale': 15.0, 'intensity': 1.0, 'color': [1.0, 1.0, 1.0]}}
        ]

    def suggest_modification(self, current_code: str, context: Dict) -> Dict:
        suggestions = []
        if 'sin(' in current_code or 'cos(' in current_code:
            suggestions.append({'type': 'enhance_oscillation', 'description': 'Add more complex oscillations', 'suggestion': 'Try combining multiple sine waves with different frequencies', 'code': '// Add complex oscillation\nfloat complex_sin = sin(time) + 0.5 * sin(time * 2.3) + 0.25 * sin(time * 3.7);\n'})
        if 'vec3' in current_code and 'color' in current_code.lower():
            suggestions.append({'type': 'color_variation', 'description': 'Add color variation', 'suggestion': 'Try adding some color modulation', 'code': '// Add color variation\nvec3 color = vec3(sin(time), cos(time * 1.5), sin(time * 2.0));\n'})
        if 'audio' in context and context['audio']:
            suggestions.append({'type': 'audio_reactivity', 'description': 'Add audio reactivity', 'suggestion': 'Use audio features to modulate shader parameters', 'code': '// Add audio reactivity\nfloat audio = volume + bass * 0.5 + mid * 0.3 + treble * 0.2;\nvec3 color = vec3(sin(time + audio * 10.0));\n'})
        if 'sentience' in context and context['sentience']:
            suggestions.append({'type': 'sentience_reactivity', 'description': 'Add sentience reactivity', 'suggestion': 'Use AI consciousness to influence the shader', 'code': '// Add sentience reactivity\nfloat consciousness = sentience * 0.5 + 0.5;\nvec3 color = vec3(sin(time * consciousness));\n'})
        if suggestions:
            return suggestions[np.random.randint(0, len(suggestions))]
        return {'type': 'general', 'description': 'Try adding some basic effects', 'suggestion': 'Start with simple color modulation or patterns', 'code': '// Simple color modulation\nvec3 color = vec3(sin(time), cos(time), sin(time * 1.5));\n'}

    def generate_pattern(self, pattern_name: str, parameters: Dict) -> str:
        pattern_library = self._load_pattern_library()
        for pattern in pattern_library:
            if pattern['name'].lower() == pattern_name.lower():
                code = pattern['code']
                for param, value in parameters.items():
                    if param in pattern['parameters']:
                        if 'frequency' in param or 'scale' in param:
                            code = code.replace('10.0', str(value)) if 'frequency' in param else code.replace('15.0', str(value))
                        elif 'intensity' in param:
                            code = code.replace('1.0', str(value))
                        elif 'color' in param:
                            color_str = f'vec3({value[0]}, {value[1]}, {value[2]})'
                            code = code.replace('vec3(1.0)', color_str)
                return code
        return "// Unknown pattern"

    def apply_style(self, current_code: str, style_name: str) -> str:
        style_templates = self._load_style_templates()
        if style_name not in style_templates:
            return current_code
        style = style_templates[style_name]
        main_pos = current_code.find('void main()')
        if main_pos != -1:
            return current_code[:main_pos] + '\n' + style['code'] + '\n' + current_code[main_pos:]
        return current_code + '\n' + style['code']

    def detect_errors(self, shader_code: str) -> List[str]:
        errors = []
        if 'main()' in shader_code and 'void main()' not in shader_code:
            errors.append("Missing main function declaration")
        if 'gl_FragColor' in shader_code and 'out vec4' not in shader_code:
            errors.append("Missing output declaration")
        required_uniforms = ['time', 'resolution', 'volume', 'bass', 'mid', 'treble', 'sentience']
        for uniform in required_uniforms:
            if uniform in shader_code and f'uniform float {uniform}' not in shader_code:
                errors.append(f"Missing uniform declaration for {uniform}")
        try:
            lines = shader_code.split('\n')
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('//'):
                    if '(' in line and ')' not in line:
                        errors.append(f"Syntax error: missing closing parenthesis on line {i+1}")
                    if '{' in line and '}' not in line:
                        errors.append(f"Syntax error: missing closing brace on line {i+1}")
        except Exception as e:
            pass
        return errors

    def suggest_improvements(self, shader_code: str) -> List[str]:
        suggestions = []
        if 'sin(' in shader_code and 'cos(' in shader_code:
            suggestions.append("Consider using sin/cos approximations for better performance")
        if 'texture(' in shader_code:
            suggestions.append("Consider using textureLod for better mipmap filtering")
        if shader_code.count('vec3') > 5:
            suggestions.append("Consider creating helper functions for repeated vec3 operations")
        return suggestions
```

### vjlive-v1/core/live_coding_engine.py (L1025-1321)
```python
class LiveCodingWebSocketServer:
    """WebSocket server for real-time collaborative coding"""
    def __init__(self, host: str = 'localhost', port: int = 8765, start_immediately: bool = True):
        self.host = host
        self.port = port
        self.engine = LiveCodingEngine()
        self.ai_assistant = AICreativeAssistant()
        self.sessions: Dict[str, CollaborativeSession] = {}
        self.server = None
        self.server_task = None
        if start_immediately:
            self.start_server_sync()

    def start_server_sync(self):
        def run_server():
            asyncio.run(self.start_server())
        threading.Thread(target=run_server, daemon=True).start()

    async def start_server(self):
        async def handler(websocket, path):
            await self.handle_connection(websocket, path)
        self.server = await websockets.serve(handler, self.host, self.port)
        print(f"Live Coding WebSocket server started on ws://{self.host}:{self.port}")

    async def handle_connection(self, websocket, path):
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get('type') == 'join_session':
                    await self.handle_join_session(websocket, data)
                elif data.get('type') == 'leave_session':
                    await self.handle_leave_session(websocket, data)
                elif data.get('type') == 'operation':
                    await self.handle_operation(websocket, data)
                elif data.get('type') == 'request_document':
                    await self.handle_document_request(websocket, data)
                elif data.get('type') == 'request_suggestions':
                    await self.handle_suggestions_request(websocket, data)
                elif data.get('type') == 'compile_shader':
                    await self.handle_compile_request(websocket, data)
                elif data.get('type') == 'get_templates':
                    await self.handle_templates_request(websocket, data)
                elif data.get('type') == 'get_patterns':
                    await self.handle_patterns_request(websocket, data)
                elif data.get('type') == 'apply_style':
                    await self.handle_style_request(websocket, data)
                elif data.get('type') == 'detect_errors':
                    await self.handle_errors_request(websocket, data)
                elif data.get('type') == 'suggest_improvements':
                    await self.handle_improvements_request(websocket, data)
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")

    # Handler methods omitted for brevity - see full source for details

    def _broadcast_session_update(self, session_id: str, user_id: str, action: str):
        if session_id not in self.engine.sessions:
            return
        session = self.engine.sessions[session_id]
        message = {
            'type': 'session_update',
            'action': action,
            'user_id': user_id,
            'users': session.get_user_list()
        }
        for uid in session.users:
            if uid in self.engine.websocket_connections:
                websocket_info = self.engine.websocket_connections[uid]
                websocket = websocket_info['websocket']
                try:
                    asyncio.run_coroutine_threadsafe(
                        websocket.send(json.dumps(message)),
                        websocket.loop
                    )
                except websockets.exceptions.ConnectionClosed:
                    self.engine.leave_session(uid, session_id)
                    self.engine.remove_websocket_connection(uid)

    def _broadcast_operation(self, session_id: str, user_id: str, operation: Dict):
        if session_id not in self.engine.sessions:
            return
        session = self.engine.sessions[session_id]
        message = {
            'type': 'operation',
            'user_id': user_id,
            'operation': operation
        }
        for uid in session.users:
            if uid != user_id and uid in self.engine.websocket_connections:
                websocket_info = self.engine.websocket_connections[uid]
                websocket = websocket_info['websocket']
                try:
                    asyncio.run_coroutine_threadsafe(
                        websocket.send(json.dumps(message)),
                        websocket.loop
                    )
                except websockets.exceptions.ConnectionClosed:
                    self.engine.leave_session(uid, session_id)
                    self.engine.remove_websocket_connection(uid)

def start_live_coding_server(host: str = 'localhost', port: int = 8765):
    """Start the live coding WebSocket server"""
    server = LiveCodingWebSocketServer(host, port)
    return server
```

### vjlive-v1/docs/LIVE_CODING.md (L1-200)
```markdown
# Live Coding Engine

Enable VJs and AI agents to write and modify shaders/effects in real-time during performance without restarting.

## Features

### Hot Reload GLSL Shaders
- Compile on save, swap seamlessly
- No visual glitch, no restart required

### Python Effect Scripts
- Modify parameters and logic on-the-fly
- Real-time parameter updates

### Visual Feedback
- Syntax errors shown in UI, not crashes
- Line number highlighting
- Error recovery

### Version Control
- Undo/redo functionality
- Save snapshots
- Version history

### AI Code Generation
- LLM writes shaders from text prompts
- Semantic layer integration
- Collaborative coding

### Collaborative Editing
- Multiple users/agents edit simultaneously
- Real-time synchronization

## Architecture

### Live Coding Pipeline
[Code Editor (Monaco/VSCode)]
    |
    v
[File Watcher] detects changes
    |
    v
[Syntax Checker] validates code
    |
    v
[Shader Compiler] compiles GLSL
    |
    v
[Hot Reload Manager] swaps shader
    |
    v
[GPU] renders with new shader
    |
    v
[Visual Feedback] shows result
    |
    +--[Error?]---[Error Display] shows line number + message

## Quick Start

### 1. Install Dependencies
pip install watchdog pyopengl
npm install @monaco-editor/react

### 2. Start Hot Reload Watcher
from core.hot_reload_watcher import HotReloadWatcher
watcher = HotReloadWatcher()
watcher.start()

### 3. Use Web UI Editor
import ShaderEditor from './components/LiveCoding/ShaderEditor';
<ShaderEditor effectName="my_effect" initialCode={shaderCode} />

## API Reference

### LiveCodingEngine
engine = LiveCodingEngine(shader_dir="shaders", effect_dir="effects")
engine.load_shader("effect_name", "fragment.frag", "vertex.vert")
shader = engine.get_shader("effect_name")
engine.on_compile_error = lambda path, msg: print(f"Error: {msg}")
engine.on_compile_success = lambda effect: print(f"Loaded: {effect}")

### ShaderCompiler
compiler = ShaderCompiler()
program = compiler.compile(vertex_source, fragment_source, "effect_name")
program.use()
program.set_uniform("time", 1.0)

### AIShaderGenerator
ai_generator = AIShaderGenerator(llm_client)
generated_code = await ai_generator.generate_effect("add chromatic aberration")

## Performance Targets
| Metric | Target |
|--------|--------|
| Hot reload latency | <500ms |
| Compilation time (1080p shader) | <100ms |
| Editor responsiveness | <16ms (60fps) |
| AI code generation time | <3s |

## Testing
python -m unittest tests/test_live_coding.py
```

---

## Integration Notes

The Live Coding Environment integrates with the VJLive3 system through:

- **NodeGraph**: Effects can reference live-coded shaders as custom nodes
- **Shader Hot Reload Plugin**: Watches `shaders/live/` directory and hot-reloads into EffectChain
- **WebSocket Gateway**: Central WebSocket server multiplexes live coding messages alongside other VJLive protocols
- **AI Agent Bridge**: Agents can invoke `AICreativeAssistant` to generate or modify shaders during collaborative sessions
- **Performance Monitor**: Compilation times and operation latency tracked via `MetricCollector`

**Dependency Relationships**:
- `vjlive3.core.live_coding.LiveCodingEngine` ← depends on `OpenGL.GL.shaders` for compilation
- `vjlive3.core.live_coding.VisualProgrammingInterface` → generates GLSL for consumption by `LiveCodingEngine`
- `vjlive3.plugins.shader_hot_reload` → uses `LiveCodingEngine` to watch and reload shader files

---
