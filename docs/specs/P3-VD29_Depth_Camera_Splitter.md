# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD29_Depth_Camera_Splitter.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD29 — DepthCameraSplitterEffect

## Description

The Depth Camera Splitter is a gateway node that demultiplexes a depth camera source into four independent output streams: color (RGB), depth (grayscale), infrared (IR), and colorized depth. This allows each stream to be processed independently through the node graph, enabling complex depth-based workflows where different depth representations are needed for different downstream effects. The effect acts as a hub for depth camera integration, providing standardized output formats that other depth-aware effects can consume.

The effect consumes a depth camera source (which may provide multiple channels) and produces four separate video outputs, each representing a different aspect of the depth data. This is particularly useful in setups where depth data needs to be visualized, analyzed, and processed in parallel, such as in depth-based compositing, 3D reconstruction, or mixed reality applications.

## What This Module Does

- Accepts a depth camera input that provides color, depth, and infrared channels
- Demultiplexes the input into four separate output streams:
  - **Color (RGB)**: Standard color video from the depth camera's RGB sensor
  - **Depth (grayscale)**: Single-channel depth map where brightness represents distance
  - **Infrared (IR)**: Infrared channel from the depth camera (if available)
  - **Colorized Depth**: Depth map with false-color applied for visualization
- Manages depth source lifecycle: connects to `AstraDepthSource` or compatible provider
- Updates depth texture each frame and ensures proper format conversion
- Provides multiple outputs that can be routed to different nodes in the graph simultaneously
- Handles resolution matching and format conversion between depth source and output streams
- Uses GPU shaders for efficient channel extraction and colorization
- Supports optional parameters for depth range normalization and colorization palette

## What This Module Does NOT Do

- Does NOT perform depth sensing or capture (relies on external depth camera driver)
- Does NOT generate infrared data if the source doesn't provide it (passes through or zeros)
- Does NOT apply depth processing (filtering, smoothing) — that's for downstream effects
- Does NOT manage node graph routing (caller must connect the four outputs to appropriate destinations)
- Does NOT compress or encode the streams (raw/uncompressed outputs only)
- Does NOT synchronize multiple depth cameras (single source only)
- Does NOT provide CPU fallback (requires GPU for texture operations)
- Does NOT store historical frames (purely stateless per-frame processing)

---

## Detailed Behavior

### Input Source

The effect expects a depth camera source that provides at least two channels: color (RGB) and depth. Some depth cameras (like Intel RealSense, Azure Kinect) also provide an infrared (IR) channel. The source should implement:

- `get_color_frame()` → returns RGB or RGBA image
- `get_depth_frame()` → returns single-channel depth map (normalized 0.0-1.0 or 16-bit)
- `get_ir_frame()` → returns IR image (optional, may return None)

The effect connects to this source via `set_depth_source()` and calls these methods each frame in `update_depth_data()`.

### Output Streams

The effect produces four distinct outputs, each as a separate framebuffer or texture that can be sampled by downstream nodes:

1. **Color Output (RGB)**:
   - Direct pass-through of the color frame from the depth source
   - Format: RGBA (with alpha=1.0) or RGB depending on source
   - Resolution: matches source color resolution
   - No processing applied

2. **Depth Output (Grayscale)**:
   - Extracted from the depth frame
   - Normalized to 0.0-1.0 range (if source provides 16-bit, scales accordingly)
   - Format: Single-channel (RED) or grayscale RGBA
   - May apply depth range clipping via `depth_min`/`depth_max` parameters
   - Output is linear; no gamma correction

3. **Infrared Output (IR)**:
   - Extracted from the IR frame if available
   - If IR not available, outputs black (all zeros) or passes through color as fallback
   - Format: Grayscale RGBA
   - May apply gain and offset via `ir_gain` and `ir_offset` parameters

4. **Colorized Depth Output**:
   - Depth map with false-color applied for visualization
   - Uses a color ramp (gradient) that maps depth values to colors
   - Default palette: near = warm colors (red/yellow), far = cool colors (blue/purple)
   - Configurable via `colorization_palette` parameter (preset names or custom LUT)
   - Format: RGBA

### Processing Pipeline

Each frame, the effect executes the following steps:

1. **Source Update**: Call `update_depth_data()` to fetch fresh frames from the depth source
2. **Texture Upload**: Upload each source frame (color, depth, IR) to GPU textures if changed
3. **Depth Normalization**: Convert depth to normalized [0,1] range, apply `depth_min`/`depth_max` clipping
4. **Colorization**: Generate colorized depth by sampling the depth texture through a 1D color LUT
5. **Output Generation**: Render each of the four outputs to separate framebuffers or a texture array
6. **Graph Dispatch**: Downstream nodes can sample any of the four outputs via texture units

The effect may use a single large framebuffer with multiple attachments (MRT) or four separate framebuffers. MRT is more efficient but requires OpenGL 3.0+.

### Parameters

- `depth_min`: float, default 0.0 — Minimum depth value to consider (clips lower values)
- `depth_max`: float, default 1.0 — Maximum depth value to consider (clips higher values)
- `ir_gain`: float, default 1.0 — Gain applied to IR channel before output
- `ir_offset`: float, default 0.0 — Offset added to IR channel
- `colorization_palette`: string, default "thermal" — Color palette for depth visualization ("thermal", "depth", "rainbow", "mono")
- `invert_depth`: bool, default false — If true, inverts depth mapping (near=1.0, far=0.0)

---

## Public Interface

```python
class DepthCameraSplitterEffect:
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def get_output_texture(self, stream_name: str) -> int: ...
    def get_output_framebuffer(self, stream_name: str) -> Framebuffer: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

### Inputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `depth_source` | `AstraDepthSource` | Depth camera provider | Must implement `get_color_frame()`, `get_depth_frame()`, `get_ir_frame()` |

### Outputs

The effect provides four named output streams that can be accessed via `get_output_texture()` or `get_output_framebuffer()`:

| Stream Name | Type | Description | Format |
|-------------|------|-------------|--------|
| `"color"` | texture/FBO | RGB color video | RGBA8 |
| `"depth"` | texture/FBO | Grayscale depth map | R8 or RGBA8 |
| `"ir"` | texture/FBO | Infrared channel | R8 or RGBA8 |
| `"colorized_depth"` | texture/FBO | False-color depth visualization | RGBA8 |

---

## Dependencies

### External Dependencies
- `numpy` — Array operations for frame data
- `OpenGL` — GPU texture and framebuffer operations
- `PIL` (optional) — Image format conversions

### Internal Dependencies
- `core.depth_source.AstraDepthSource` — Depth camera interface
- `core.framebuffer.Framebuffer` — GPU framebuffer abstraction
- `core.shader_program.ShaderProgram` — Shader compilation

---

## State Management

**Persistent State:**
- `_depth_source: Optional[AstraDepthSource]` — Connected depth camera source
- `_color_frame: Optional[np.ndarray]` — Last color frame (HWC)
- `_depth_frame: Optional[np.ndarray]` — Last depth frame (H or HWC)
- `_ir_frame: Optional[np.ndarray]` — Last IR frame (H or HWC)
- `_color_texture: int` — OpenGL texture ID for color stream
- `_depth_texture: int` — OpenGL texture ID for depth stream
- `_ir_texture: int` — OpenGL texture ID for IR stream
- `_colorized_texture: int` — OpenGL texture ID for colorized depth
- `_outputs: dict[str, Framebuffer]` — Framebuffers for each stream
- `_frame_width: int` — Current width
- `_frame_height: int` — Current height

**Per-Frame State:**
- Temporary texture bindings
- Shader uniform values

**Initialization:**
- Textures created on first `update_depth_data()` call
- Framebuffers created on first `get_output_framebuffer()` call or in `set_frame_size()`

**Cleanup:**
- Delete all 4 textures (`glDeleteTextures`)
- Delete all 4 framebuffers
- Clear references

---

## GPU Resources

| Resource | Type | Format | Dimensions | Count |
|----------|------|--------|------------|-------|
| Color texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | 1 |
| Depth texture | GL_TEXTURE_2D | GL_R8 or GL_RGBA8 | frame size | 1 |
| IR texture | GL_TEXTURE_2D | GL_R8 or GL_RGBA8 | frame size | 1 |
| Colorized texture | GL_TEXTURE_2D | GL_RGBA8 | frame size | 1 |
| Output FBOs (optional) | Framebuffer | RGBA8 | frame size | 4 (or use texture array) |

**Memory Budget (1080p):**
- 4 × RGBA8 textures: 4 × 8.3 MB = ~33.2 MB
- If using R8 for depth/IR: 2 × 2.1 MB + 2 × 8.3 MB = ~20.8 MB
- Total: ~21-33 MB depending on format choices

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth source not set | `RuntimeError("No depth source")` | Call `set_depth_source()` before processing |
| Color frame missing | Log warning, output black texture | Continue with other streams if available |
| Depth frame missing | Log warning, depth output = black | Continue with color/IR if available |
| Texture creation fails | `RuntimeError` (out of GPU memory) | Propagate to caller; may need to reduce resolution |
| Invalid stream name in `get_output_texture()` | `KeyError` | Document valid names: "color", "depth", "ir", "colorized_depth" |
| Resolution change without update | Textures become size-mismatched | Call `set_frame_size()` or recreate textures automatically |
| IR not available | IR output = black (0) | This is expected behavior; not an error |

---

## Thread Safety

This effect is **not thread-safe**. All GPU operations must occur on the thread with the current OpenGL context. The `_color_frame`, `_depth_frame`, `_ir_frame` caches are mutated each frame, so concurrent `update_depth_data()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (1080p):**
- Texture uploads (4 channels): ~1-2 ms (PCIe bandwidth dependent)
- Colorization shader: ~0.5 ms
- Total: ~2-3 ms on discrete GPU, ~5-8 ms on integrated GPU

**Optimization Strategies:**
- Only update textures when source frames change (compare frame counters or hash)
- Use `GL_R8` for depth and IR textures to reduce memory bandwidth by 4×
- Use texture arrays instead of separate textures if OpenGL 3.0+ available
- Implement lazy framebuffer creation: only create outputs that are actually used
- Consider using PBOs (Pixel Buffer Objects) for asynchronous texture uploads if source is CPU-side

---

## Integration Checklist

- [ ] Depth source is connected via `set_depth_source()` before first frame
- [ ] Depth source provides at least color and depth frames; IR is optional
- [ ] All four output streams are routed to downstream nodes as needed
- [ ] Texture formats match expectations (RGBA8 for color/colorized, R8 for depth/IR)
- [ ] `update_depth_data()` is called each frame before downstream nodes sample outputs
- [ ] `cleanup()` is called when the effect is destroyed to avoid GPU memory leaks
- [ ] Resolution changes trigger texture/FBO reallocation (either via `set_frame_size()` or automatic detection)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect instantiates without errors |
| `test_set_depth_source` | Source is stored and can be retrieved |
| `test_update_depth_data_no_source` | Raises error if source not set |
| `test_update_depth_data_missing_ir` | Handles IR=None gracefully (IR output = black) |
| `test_get_output_texture` | Returns valid texture IDs for all four streams |
| `test_get_output_framebuffer` | Creates and returns framebuffers on demand |
| `test_texture_upload` | Color and depth textures are updated with correct data |
| `test_colorization` | Colorized depth output shows gradient based on depth values |
| `test_parameter_application` | `depth_min`/`depth_max` clip depth values correctly |
| `test_cleanup` | All textures and framebuffers are deleted, IDs zeroed |
| `test_resolution_change` | Textures/FBOs are recreated when resolution changes |
| `test_invert_depth` | When enabled, depth values are inverted before colorization |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD29: depth_camera_splitter` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_camera_splitter.py` — Original VJLive implementation
- `plugins/core/depth_camera_splitter/__init__.py` — VJLive-2 version
- `plugins/vdepth/__init__.py` — Registration in depth plugin module
- `gl_leaks.txt` — Notes on texture allocation (missing `glDeleteTextures`)

Design decisions inherited:
- Effect name: `"depth_camera_splitter"`
- Four output streams: color, depth, IR, colorized_depth
- Uses `DEPTH_SPLITTER_FRAGMENT` shader (likely does channel extraction and colorization in one pass)
- Texture resource management: allocates with `glGenTextures`, must free with `glDeleteTextures` (noted as missing in legacy)
- Inherits from base `Effect` class (not `DepthEffect` specifically, though it uses depth source)

---

## Notes for Implementers

1. **Output Multi-Threading**: Since this effect produces multiple outputs that may be consumed by different downstream nodes, consider using a single shader with Multiple Render Targets (MRT) to render all four outputs in one pass. This is more efficient than four separate passes.

2. **Depth Normalization**: Depth cameras often output 16-bit depth (0-65535) or floating-point depth in arbitrary units. The effect should normalize to [0,1] using `depth_min` and `depth_max` parameters. Provide sensible defaults based on the depth source's native range.

3. **IR Fallback**: Not all depth cameras provide IR. The effect should handle `None` from `get_ir_frame()` gracefully, outputting black. Document this behavior clearly.

4. **Colorization Palettes**: Implement at least three palettes:
   - `"thermal"`: Black → red → yellow → white (like heat vision)
   - `"rainbow"`: Full hue spectrum from blue (near) to red (far)
   - `"mono"`: Simple grayscale (depth as brightness)
   Allow custom palettes via a 1D texture LUT.

5. **Resource Management**: The legacy code notes missing `glDeleteTextures` calls. Ensure your implementation properly deletes all 4 textures and any FBOs in `cleanup()`.

6. **Performance**: If the depth source is CPU-side (e.g., from OpenCV), texture uploads can be a bottleneck. Consider using Pixel Buffer Objects (PBOs) for asynchronous uploads to hide PCIe latency.

7. **Resolution Handling**: The depth source may provide color and depth at different resolutions. The effect should either:
   - Resize depth to match color resolution, OR
   - Output each stream at its native resolution and let downstream nodes handle resampling
   Choose one approach and document it.

8. **Node Graph Integration**: In VJLive3's node graph, this effect will have 1 input (the depth camera source) and 4 outputs. The graph system must support multi-output nodes. Document how to connect each output to downstream effects.
