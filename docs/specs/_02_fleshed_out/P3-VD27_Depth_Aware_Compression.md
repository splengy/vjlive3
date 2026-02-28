# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD27_Depth_Aware_Compression.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD27 — DepthAwareCompressionEffect

## Description

The Depth Aware Compression effect applies video compression artifacts (such as blockiness, color quantization, and quality reduction) in a depth-modulated manner. By leveraging depth map information, the effect can apply different levels of compression to different depth layers, creating a volumetric degradation effect where foreground and background elements are compressed differently. This simulates scenarios like depth-of-field based encoding, where distant objects receive heavier compression, or foreground isolation where the subject remains crisp while the background exhibits streaming artifacts.

The effect integrates with the VJLive3 depth pipeline, consuming a depth map from an `AstraDepthSource` and applying shader-based compression algorithms that vary based on depth values. It supports multiple compression modes (block-based DCT-like artifacts, color quantization, motion block simulation) and provides presets that emulate real-world compression standards like JPEG 2000 and satellite video codecs.

## What This Module Does

- Consumes a depth map (single-channel texture) alongside the input video frame
- Applies compression artifacts that vary according to depth values using shader-based algorithms
- Supports multiple compression types: block-based artifacts (simulating macroblock compression), color quantization, and motion block simulation
- Provides preset configurations for common compression styles (streaming 720p, JPEG 2000, satellite feed)
- Integrates with the depth effect base class (`DepthEffect`) for consistent depth source management
- Uses GPU-accelerated fragment shaders for real-time performance at 60 FPS
- Allows audio reactivity to modulate compression parameters based on audio features
- Manages depth texture lifecycle: updates from depth source each frame, handles texture reallocation on resolution changes

## What This Module Does NOT Do

- Does NOT perform actual video encoding/compression (only simulates visual artifacts)
- Does NOT generate depth maps itself (requires external `AstraDepthSource` or compatible depth provider)
- Does NOT support multiple depth sources simultaneously (single depth source only)
- Does NOT implement full codec algorithms (artifacts are procedurally generated approximations)
- Does NOT handle audio analysis (relies on `AudioReactor` wrapper for feature extraction)
- Does NOT provide CPU fallback (requires GPU for shader-based artifact generation)
- Does NOT manage node graph connections (caller must route depth source to effect)
- Does NOT store persistent state across sessions (all parameters are in-memory)

---

## Detailed Behavior

### Compression Artifact Types

The effect implements several distinct compression artifact algorithms, each controlled by a parameter:

1. **Block-Based Artifacts** (`block_size`, `block_depth`):
   - Simulates macroblock-based compression (like JPEG, MPEG)
   - Divides the frame into square blocks of size `block_size` (in pixels)
   - Within each block, applies quantization and smoothing to create the "blockiness" effect
   - Depth modulates the intensity: deeper regions show more pronounced blocking
   - Implementation: In the fragment shader, compute block coordinates `block_x = floor(uv.x * width / block_size)`, then sample a uniform quantization value per block

2. **Color Quantization** (`color_quantize`):
   - Reduces the color palette to simulate low-bit-depth encoding
   - Depth influences which colors get quantized more aggressively
   - Algorithm: `quantized = floor(original_color * levels) / levels` where `levels = 2^color_quantize_bits`
   - Near objects may retain full color while distant objects use reduced palette

3. **Motion Block Simulation** (`motion_blocks`):
   - Simulates motion compensation artifacts seen in inter-frame codecs
   - Creates ghosting and block displacement effects
   - Depth determines which regions exhibit motion artifacts (typically mid-ground)
   - Implementation: Offset texture coordinates by a pseudo-random vector per block, creating misalignment

4. **Quality Layering** (`quality`, `depth_layers`):
   - Applies a global quality reduction that varies with depth
   - The image is divided into `depth_layers` discrete depth bands
   - Each band receives a different quality multiplier (0.0-1.0)
   - Closer layers may have quality=1.0 (no degradation), farthest layers quality=0.2 (severe degradation)

### Depth Integration

The effect expects a depth map texture with the following properties:
- Single-channel (RED format) or RGB with identical channels
- Normalized depth values: 0.0 = near, 1.0 = far (or vice versa depending on depth source convention)
- Resolution matches the input frame dimensions (or will be resized by the effect)
- Updated each frame via `set_depth_source()` and `update_depth_data()`

The depth value at each pixel determines the compression intensity:
```glsl
float depth = texture(depth_texture, uv).r;
float compression_factor = mix(u_quality_near, u_quality_far, depth);
```

### Audio Reactivity

When an `AudioReactor` is connected, certain parameters can be modulated by audio features:
- `intensity_curve` may respond to `BEAT_INTENSITY` (beats cause temporary quality drops)
- `motion_blocks` may respond to `ENERGY` (high energy increases motion artifact chaos)
- `color_quantize` may respond to `TEMPO` (faster tempo reduces color depth)

The exact mappings are configurable via `audio_reactor.assign_audio_feature()` calls during initialization.

### Presets

The effect includes three built-in presets that pre-configure parameters for common use cases:

- **`streaming_720p`**: Simulates low-bitrate streaming video with visible blocking and color banding, moderate depth modulation
- **`jpeg_2000`**: Simulates wavelet-based compression artifacts with smoother degradation and fewer blocking artifacts
- **`satellite_feed`**: Simulates noisy, low-resolution satellite transmission with heavy quantization and occasional frame corruption

Presets can be applied via `load_preset(preset_name)` which overwrites current parameter values.

---

## Public Interface

```python
class DepthAwareCompressionEffect:
    def __init__(self) -> None: ...
    def set_depth_source(self, source) -> None: ...
    def update_depth_data(self) -> None: ...
    def set_audio_analyzer(self, audio_analyzer) -> None: ...
    def load_preset(self, preset_name: str) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame (HWC, 3 or 4 channels) | dtype: uint8 or float32 |
| `depth_source` | `AstraDepthSource` | Depth map provider | Must implement `get_depth_frame()` |
| `audio_analyzer` | `AudioAnalyzer` | Optional audio feature source | Provides BEAT_INTENSITY, TEMPO, ENERGY |

**Output**: `np.ndarray` — Processed frame with compression artifacts applied, same shape/format as input

---

## Dependencies

### External Dependencies
- `numpy` — Array operations for frame data
- `OpenGL` (via `pyglet` or similar) — GPU rendering context
- `PIL` (optional) — Image format conversions

### Internal Dependencies
- `core.effects.depth_effect.DepthEffect` — Base class for depth-aware effects
- `core.audio.AudioReactor` — Audio feature wrapper
- `core.shader_program.ShaderProgram` — Shader compilation and uniform management
- `core.framebuffer.Framebuffer` — GPU framebuffer abstraction

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `depth_compression_ratio` | float | 0.5 | 0.0 - 1.0 | Overall influence of depth on compression strength |
| `block_size` | int | 8 | 4 - 32 | Size of compression blocks in pixels (power of 2 recommended) |
| `block_depth` | float | 4.0 | 0.0 - 10.0 | Intensity of block-based artifacts |
| `intensity_curve` | float | 3.0 | 0.0 - 10.0 | Exponent for depth-to-quality mapping (higher = more nonlinear) |
| `depth_layers` | int | 3 | 1 - 10 | Number of discrete depth bands for quality layering |
| `quality` | float | 6.0 | 0.0 - 10.0 | Base quality level (higher = less compression) |
| `motion_blocks` | float | 2.0 | 0.0 - 10.0 | Strength of motion block simulation artifacts |
| `color_quantize` | float | 6.0 | 0.0 - 8.0 | Color quantization levels (2^N where N=value) |
| `blend` | float | 0.8 | 0.0 - 1.0 | Blend factor between original and processed frame |

---

## State Management

**Persistent State:**
- `parameters: dict` — Current parameter values (see table above)
- `_depth_source: Optional[AstraDepthSource]` — Depth map provider
- `_depth_frame: Optional[np.ndarray]` — Cached depth map (updated each frame)
- `_depth_texture: int` — OpenGL texture ID for depth map
- `_shader: ShaderProgram` — Compiled fragment shader
- `_frame_width: int` — Current frame width (default 1920)
- `_frame_height: int` — Current frame height (default 1080)

**Per-Frame State:**
- Temporary shader uniform values
- Intermediate framebuffer bindings

**Initialization:**
- Depth texture created on first `update_depth_data()` or `process_frame()`
- Shader compiled in `__init__()`
- Framebuffer created in `set_frame_size()` if needed

**Cleanup:**
- Delete depth texture (`glDeleteTextures`)
- Delete shader program
- Delete any framebuffers

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_RED (or GL_R8) | frame size | Created on first depth update, recreated if resolution changes |
| Main shader | GLSL program | vertex + fragment | N/A | Init once |
| Work FBO (optional) | Framebuffer | RGBA8 | frame size | Init once if intermediate rendering needed |

**Memory Budget (1080p):**
- Depth texture: 1920 × 1080 × 1 byte = ~2.1 MB (GL_R8)
- Total VRAM: ~2.1 MB + shader overhead

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth source not set | `RuntimeError("No depth source")` | Call `set_depth_source()` before `process_frame()` |
| Depth frame missing | `RuntimeError("Depth data not available")` | Ensure depth source is providing frames |
| Shader compilation failure | `ShaderCompilationError` | Log error, effect becomes no-op |
| Depth texture creation fails | `RuntimeError` | Propagate to caller; may indicate out of GPU memory |
| Invalid parameter value | Shader undefined behavior | Document ranges; optionally clamp in `apply_uniforms()` |
| Resolution mismatch | Depth texture size ≠ frame size | Effect should resize depth texture automatically or raise error |

---

## Thread Safety

The effect is **not thread-safe**. All GPU operations must occur on the thread owning the OpenGL context. Multiple instances can run on different threads with separate contexts. The `_depth_frame` cache is per-instance and mutated each frame, so concurrent `process_frame()` calls on the same instance will cause race conditions.

---

## Performance

**Expected Frame Time (1080p):**
- Block-based artifacts: ~1-2 ms
- Color quantization: ~0.5 ms
- Motion blocks: ~1 ms
- Total with depth fetch: ~2-3 ms on discrete GPU

**Optimization Strategies:**
- Use `GL_R8` for depth texture to minimize memory bandwidth
- Precompute block coordinates in a vertex buffer if block_size is constant
- Early-out if `blend == 0` (return original frame)
- Cache depth texture between frames; only update if depth source provides new data

---

## Integration Checklist

- [ ] Depth source is connected via `set_depth_source()` before processing
- [ ] Depth map resolution matches frame resolution (or effect handles resizing)
- [ ] Shader compiles successfully on all target platforms
- [ ] Parameters are validated before being sent to shader
- [ ] `cleanup()` is called when effect is destroyed to release GPU resources
- [ ] Pipeline orchestrator calls `update_depth_data()` each frame to refresh depth texture

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect instantiates without errors |
| `test_set_depth_source` | Depth source is stored correctly |
| `test_update_depth_data` | Depth texture is created/updated with valid data |
| `test_process_frame_no_depth` | Raises error if depth source not set |
| `test_process_frame_with_depth` | Applies artifacts and returns frame of correct shape |
| `test_preset_loading` | Presets correctly set all related parameters |
| `test_parameter_ranges` | Extreme values don't crash shader |
| `test_cleanup` | All GPU resources released |
| `test_audio_reactivity` | Audio features modulate parameters if reactor connected |
| `test_blend_factor` | `blend=0` returns original, `blend=1` returns fully processed |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD27: depth_aware_compression` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references from legacy codebase:
- `plugins/vdepth/depth_aware_compression.py` — Original implementation
- `plugins/core/depth_aware_compression/__init__.py` — VJLive-2 version with presets
- `core/effects/depth_aware_compression.py` — Unified base class integration
- `tests/test_depth_restoration.py` — Test examples

Design decisions inherited:
- Depth texture stored as `GL_R8` for efficiency
- Block-based artifacts use integer division in shader for deterministic block boundaries
- Presets are hard-coded dictionaries mapping parameter names to values
- Audio reactivity assigned via `AudioReactor.assign_audio_feature()` pattern

---

## Notes for Implementers

1. **Depth Coordinate System**: Confirm whether depth value 0.0 means "near" or "far" from the depth source. The effect assumes 0.0=near, 1.0=far by default. If the source uses opposite convention, either invert in the effect or document the expectation.

2. **Block Size Alignment**: For best visual results, `block_size` should be a power of 2 (4, 8, 16, 32). The shader should use integer division and multiplication to ensure blocks align to a grid, not to pixel centers.

3. **Color Quantization**: The `color_quantize` parameter represents the exponent N in `2^N` levels per channel. For example, `color_quantize=6` yields 64 levels (2^6). The shader should compute: `quantized = floor(color * levels) / levels`.

4. **Performance**: The effect should be able to run at 60 FPS on a GTX 1060 or better at 1080p. If `block_size` is large (32), fewer blocks mean less shader workload. If `depth_layers` is high, the depth banding calculation may add overhead.

5. **Presets**: The three presets provided are starting points. Users may want to save custom presets; consider implementing preset serialization to JSON.

6. **Audio Smoothing**: Audio features can be noisy. Consider applying exponential smoothing to audio-driven parameter changes to avoid flickering artifacts.
