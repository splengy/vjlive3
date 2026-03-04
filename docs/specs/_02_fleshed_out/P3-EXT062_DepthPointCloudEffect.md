# P3-EXT062: DepthPointCloudEffect — Fleshed Specification

## 1. Executive Summary

**DepthPointCloudEffect** is a 2D depth visualization effect that renders depth data as a point cloud overlay on the original video stream. Unlike its 3D counterpart [`DepthPointCloud3DEffect`](P3-EXT063_DepthPointCloud3DEffect.md), this effect operates entirely in 2D screen space, sampling depth values and rendering colored point sprites directly onto the video frame without perspective projection.

The effect creates a sci-fi "depth scan" visualization where points are colored based on depth (blue for near, red for far) with optional noise interference. It is designed for real-time performance and integrates with the depth data bus for automatic depth source discovery.

**Key Characteristics:**
- 2D screen-space point rendering (no 3D camera)
- 4 user-facing parameters on 0-10 rail
- Automatic depth texture management with GL texture uploads each frame
- Depth normalization using legacy assumption: meters → 0-255 uint8
- Proximity-based audio reactivity framework (stub implementation)
- Memory leak: depth texture allocated via `glGenTextures` but never freed

---

## 2. Detailed Behavior and Parameter Interactions

### 2.1 Architecture Overview

The effect follows the standard VJLive plugin architecture:

```
Effect Base Class
    ↓
DepthPointCloudEffect (2D composite)
    ├─ Depth source: AstraDepthSource or DepthDataBus
    ├─ Depth texture: GL_TEXTURE_2D (unit 1)
    ├─ Fragment shader: samples depth_tex, renders point sprites
    └─ Composite: mixes point cloud over video via u_mix
```

**Data Flow:**
1. `update_depth_data()` fetches depth frame and object list from depth source
2. `apply_uniforms()` normalizes depth to 0-255 uint8, uploads to GL texture
3. Fragment shader samples depth texture, colors pixels based on depth threshold
4. Effect composites colored points over original video using `u_mix`

### 2.2 Parameter System

All parameters operate on a **0-10 normalized rail** that maps to physical ranges via `_map_param()`:

| Parameter | Default | Rail → Physical Range | Description |
|-----------|---------|----------------------|-------------|
| `pointSize` | 2.0 | 0.1 – 20.0 pixels | Point sprite size (ignored in current 2D shader) |
| `pointDensity` | 1.0 | 0.01 – 1.0 | Sampling density: 1/density = step size in pixels |
| `minDepth` | 1.0 | 0.0 – 5.0 meters | Minimum depth to visualize |
| `maxDepth` | 8.0 | 0.0 – 10.0 meters | Maximum depth to visualize |

**Parameter Mapping Formula:**
```python
def _map_param(self, name: str, out_min: float, out_max: float) -> float:
    val = self.parameters.get(name, 5.0)
    return out_min + (val / 10.0) * (out_max - out_min)
```

**Note:** The shader does **not** use `pointSize`; it is a legacy parameter from the 3D point cloud variant. The 2D shader renders per-pixel effects, not actual point sprites.

### 2.3 Depth Normalization and Texture Upload

The effect assumes depth is in **meters** with a typical range of 0.3–4.0m. It normalizes to an 8-bit texture for GPU efficiency:

```python
# From apply_uniforms() line 115-116
depth_normalized = ((self.depth_frame - self.min_depth) /
                   (self.max_depth - self.min_depth) * 255).astype(np.uint8)
```

**Critical Behavior:**
- No clipping: values outside `[min_depth, max_depth]` wrap or clamp unpredictably during normalization
- Division by zero: if `min_depth == max_depth`, normalization crashes (see Edge Cases)
- Texture format: `GL_RED` with `GL_UNSIGNED_BYTE`, single-channel depth

### 2.4 Shader Logic

**Fragment Shader Uniforms:**
- `tex0`: original video (unit 0)
- `depth_tex`: depth texture (unit 1)
- `u_mix`: effect blend amount (0-1)
- `point_size`: unused
- `min_depth`, `max_depth`: depth range in meters
- `has_depth`: 1.0 if depth available, 0.0 otherwise
- `resolution`: viewport size

**Shader Execution:**
```glsl
void main() {
    vec4 original = texture(tex0, uv);
    if (has_depth > 0.0) {
        float depth = texture(depth_tex, uv).r * (max_depth - min_depth) + min_depth;
        if (depth > min_depth && depth < max_depth) {
            vec3 depth_color = depth_to_color(depth);  // Blue→Red gradient
            float noise = sin(uv.x * 100.0 + depth * 10.0) * 0.1;
            fragColor = vec4(mix(original.rgb, depth_color + noise, u_mix * 0.5), original.a);
        } else {
            fragColor = original;
        }
    } else {
        fragColor = original;
    }
}
```

**Color Mapping:**
```glsl
vec3 depth_to_color(float depth) {
    float t = clamp((depth - min_depth) / (max_depth - min_depth), 0.0, 1.0);
    return mix(vec3(0.0, 0.0, 1.0), vec3(1.0, 0.0, 0.0), t);
}
```

### 2.5 Depth Source Integration

The effect supports two depth source modes:

1. **Explicit source** via `set_depth_source(source)`:
   - Source must implement `get_filtered_depth_frame()` and `get_detected_objects()`
   - Typical source: `AstraDepthSource` from `core.video_sources`

2. **DepthDataBus fallback** (default if no source set):
   - Imports `get_depth_data_bus()` on each `update_depth_data()` call
   - Retrieves depth via `bus.get_depth()` and objects via `bus.get_objects()`
   - Silent failure if bus unavailable (logs debug, continues)

**Auto-wiring:** Any depth effect automatically receives data when an Astra camera publishes to the bus, without explicit connection.

### 2.6 Proximity and Audio Reactivity

The class includes extensive proximity tracking infrastructure but it is **non-functional**:

- `self.distances`: populated by `depth_source.get_inter_object_distances()` but never used in 2D shader
- `update_proximity_effects()`: checks object pairs against `min_proximity_distance`/`max_proximity_distance`
- `_trigger_proximity_effect()`: stores proximity events in `self.proximity_effects` list (max 10 entries)
- `get_audio_reactivity_from_depth()`: computes reactivity values (`object_count`, `avg_velocity`, `proximity_modulation`, `avg_depth`)
- `apply_audio_reactivity()`: **empty stub** — does not modulate any parameters

**Audio Reactivity Parameters:**
- `proximity_audio_enabled`: boolean (default `True`)
- `distance_audio_scale`: float (default `1.0`)
- `velocity_audio_scale`: float (default `1.0`)
- `min_proximity_distance`: float (default `0.2` meters)
- `max_proximity_distance`: float (default `2.0` meters)

---

## 3. Public Interface

### 3.1 Constructor

```python
def __init__(self) -> None:
```

**Behavior:**
- Creates fragment shader via `_get_fragment_shader()`
- Initializes base `Effect` with shader
- Sets up parameters: `pointSize`, `pointDensity`, `minDepth`, `maxDepth`
- Initializes depth data structures: `depth_source`, `depth_frame`, `objects`, `distances`, `depth_texture`
- Sets rendering state: `depth_vbo=0`, `depth_vao=0`, `num_depth_points=0`
- Configures visualization: `visualization_mode=DepthVisualizationMode.POINT_CLOUD`, `color_mode="depth"`
- Configures audio reactivity defaults

**Side Effects:** None (GL resources not allocated until first render)

### 3.2 Depth Source Management

```python
def set_depth_source(self, source: Any) -> None:
```

**Purpose:** Connect an explicit depth data source.

**Parameters:**
- `source`: Object implementing `get_filtered_depth_frame()` and `get_detected_objects()`

**Behavior:**
- Logs connection info at INFO level
- Stores `self.depth_source = source`
- If source provided, logs `source.get_info()`

**Error Handling:** No validation; `None` allowed to enable bus fallback.

---

```python
def update_depth_data(self) -> None:
```

**Purpose:** Fetch latest depth frame and object data.

**Behavior:**
1. If `self.depth_source` set:
   - Calls `self.depth_source.get_filtered_depth_frame()` → `self.depth_frame`
   - Calls `self.depth_source.get_detected_objects()` → `self.objects`
   - Logs timing and object tracking details at DEBUG level
   - On exception: logs ERROR with traceback, leaves previous data intact

2. If no `depth_source`:
   - Attempts `DepthDataBus` fallback:
     ```python
     from ..depth_data_bus import get_depth_data_bus
     bus = get_depth_data_bus()
     depth = bus.get_depth()
     if depth: self.depth_frame = depth
     objects = bus.get_objects()
     if objects: self.objects = objects
     ```
   - If bus unavailable: logs debug message, no data update

**Idempotency:** Safe to call every frame; overwrites previous depth data.

---

### 3.3 Uniform Application

```python
def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None:
```

**Purpose:** Upload effect parameters and depth texture to GPU.

**Call Sequence:**
1. Calls `super().apply_uniforms(time, resolution, audio_reactor)` to set base uniforms
2. Sets `self.shader.set_uniform("depth_effect_mix", 1.0)` (DepthEffect composite uniform)
3. If `self.depth_frame` valid and non-empty:
   - Validates: checks for NaN/Inf → logs warning, sets `self.depth_frame = None` if invalid
   - Creates depth texture if `self.depth_texture == 0`:
     ```python
     self.depth_texture = glGenTextures(1)
     glBindTexture(GL_TEXTURE_2D, self.depth_texture)
     glTexParameteri(...)  # MIN/MAG_FILTER=LINEAR, WRAP=CLAMP_TO_EDGE
     ```
   - Uploads normalized depth to texture:
     ```python
     glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, width, height, 0, GL_RED, GL_UNSIGNED_BYTE, depth_normalized)
     ```
   - Sets shader uniforms:
     ```python
     self.shader.set_uniform("depth_tex", 1)  # Texture unit 1
     self.shader.set_uniform("has_depth", 1.0)
     self.shader.set_uniform("point_size", self.point_size)
     self.shader.set_uniform("min_depth", self.min_depth)
     self.shader.set_uniform("max_depth", self.max_depth)
     ```

**Error Handling:**
- Texture creation failure: logs error, sets `self.depth_texture = 0`, returns early
- Texture upload failure: logs error, returns early
- Uniform setting failure: logs error (but continues)

**Performance:** Uploads full depth texture every frame if depth changes; no dirty tracking.

---

### 3.4 Parameter Access

```python
def set_parameter(self, name: str, value: float) -> None:
def get_parameter(self, name: str) -> float:
```

**Behavior:**
- `set_parameter`: clamps value to `[0.0, 10.0]`, updates `self.parameters[name]` if valid, calls `super().set_parameter()`, logs DEBUG
- `get_parameter`: returns from `self.parameters` if present, else calls `super().get_parameter()`

**Supported Parameters:** `pointSize`, `pointDensity`, `minDepth`, `maxDepth`, plus inherited base parameters.

---

### 3.5 Proximity and Audio Reactivity (Stub)

```python
def update_proximity_effects(self) -> None:
def _trigger_proximity_effect(self, obj1: DetectedObject, obj2: DetectedObject, distance: float) -> None:
def get_audio_reactivity_from_depth(self) -> Dict[str, float]:
def apply_audio_reactivity(self, audio_reactor, time: float) -> None:
```

**Status:** Infrastructure present but **non-functional**:
- `update_proximity_effects()`: logic to detect proximity events, but `self.distances` never populated by `update_depth_data()` (missing `self.depth_source.get_inter_object_distances()` call)
- `apply_audio_reactivity()`: empty stub — iterates `reactivity` dict but does nothing

**Intended Design:** Proximity events would trigger visual/audio effects; audio reactivity would modulate effect parameters based on depth-derived metrics.

---

## 4. Inputs and Outputs

### 4.1 Inputs

| Input | Type | Source | Description |
|-------|------|--------|-------------|
| `tex0` | `sampler2D` | Pipeline | Original video frame (RGB/RGBA) |
| `depth_tex` | `sampler2D` | GL texture | Normalized depth map (GL_RED, uint8) |
| `time` | `float` | Pipeline | Global time in seconds |
| `resolution` | `vec2` | Pipeline | Viewport size in pixels |
| `u_mix` | `float` | Pipeline | Effect blend amount (0-1) |
| Depth source | `AstraDepthSource` or bus | `set_depth_source()` or auto-wiring | Live depth frames and object tracking |

**Audio Reactor (unused):** `audio_reactor` parameter passed to `apply_uniforms()` but not used.

### 4.2 Outputs

| Output | Type | Destination | Description |
|--------|------|-------------|-------------|
| `fragColor` | `vec4` | Framebuffer | Composited output: video + depth point overlay |
| `depth_texture` | `GLuint` | GL state | Allocated texture ID (never freed) |

**Side Channel Outputs:**
- `self.proximity_effects`: list of proximity event dicts (for external consumption)
- `self.objects`: updated depth source object list (read-only)

---

## 5. Edge Cases and Error Handling

### 5.1 Depth Data Issues

| Edge Case | Current Behavior | Risk | Recommended Fix |
|-----------|------------------|------|-----------------|
| `depth_frame` is `None` | Shader receives `has_depth=0.0`, passes through original video | None (graceful) | Already handled |
| `depth_frame` contains NaN/Inf | Logs warning, sets `self.depth_frame = None` → passthrough | Data loss | Pre-filter depth source or replace invalid values |
| `depth_frame` empty (`size==0`) | Skips texture upload, `has_depth` may be 1.0 but texture empty → undefined shader behavior | Visual artifacts | Check `size > 0` before setting `has_depth=1.0` |
| Depth outside `[min_depth, max_depth]` | Normalization wraps/clamps; shader discards out-of-range pixels | Expected behavior | Document as feature |
| `min_depth == max_depth` | Division by zero in normalization → `NaN` in texture → shader undefined | Crash/artifacts | Clamp `max_depth` to `min_depth + epsilon` in `_map_param` or validation |

### 5.2 Texture Management

| Edge Case | Current Behavior | Risk | Recommended Fix |
|-----------|------------------|------|-----------------|
| `glGenTextures` fails (returns 0) | Logs error, `self.depth_texture=0`, returns early → no depth this frame | Temporary failure | Retry allocation or fallback to CPU rendering |
| `glTexImage2D` fails (invalid params) | Logs error, returns early → stale texture may remain | Visual artifacts | Validate depth dimensions, format |
| Texture never deleted | Memory leak: each effect instance leaks 1 texture ID on destruction | GPU memory exhaustion | Implement `__del__` or explicit cleanup: `glDeleteTextures([self.depth_texture])` |

### 5.3 Depth Source Failures

| Edge Case | Current Behavior | Risk | Recommended Fix |
|-----------|------------------|------|-----------------|
| `depth_source.get_filtered_depth_frame()` raises exception | Logs ERROR with traceback, `self.depth_frame` unchanged (may be stale) | Stale data displayed | Clear `self.depth_frame = None` on error |
| `DepthDataBus` import fails (relative import) | Silent debug log, no data update | No depth until explicit source | Use absolute import or lazy import with fallback |
| `DepthDataBus.get_depth()` returns `None` | No update, logs debug | No depth until data arrives | Already handled |

### 5.4 Shader and Uniform Issues

| Edge Case | Current Behavior | Risk | Recommended Fix |
|-----------|------------------|------|-----------------|
| Shader compilation fails (parent `Effect` class) | Effect likely fails to initialize | Startup failure | Already handled in base class |
| Uniform `depth_tex` not set to unit 1 | Texture bound to wrong unit → shader samples wrong data | Visual artifacts | Ensure `glActiveTexture(GL_TEXTURE1)` before binding (parent class may handle) |
| `point_size` uniform unused | No visual effect | None | Remove from shader or use in 3D variant |

### 5.5 Proximity and Audio Reactivity

| Edge Case | Current Behavior | Risk | Recommended Fix |
|-----------|------------------|------|-----------------|
| `self.distances` empty (never populated) | `update_proximity_effects()` returns immediately | Proximity features disabled | Call `self.depth_source.get_inter_object_distances()` in `update_depth_data()` |
| `apply_audio_reactivity()` called | Empty stub → no audio modulation | Expected (stub) | Implement parameter modulation or remove method |
| `proximity_audio_enabled=False` | Early return in `apply_audio_reactivity()` | Expected | Already handled |

---

## 6. Mathematical Formulations

### 6.1 Depth Normalization

**Purpose:** Convert floating-point depth (meters) to 8-bit texture for efficient GPU upload.

**Formula:**
```
depth_normalized = ((depth_frame - min_depth) / (max_depth - min_depth)) * 255
```

**Implementation:**
```python
depth_normalized = ((self.depth_frame - self.min_depth) /
                   (self.max_depth - self.min_depth) * 255).astype(np.uint8)
```

**Range:** Output in `[0, 255]` (clamped by `astype(np.uint8)`).

**Assumptions:**
- `depth_frame` in meters
- `min_depth`, `max_depth` in same units
- `max_depth > min_depth` (no division-by-zero protection)

**Inverse (Shader Side):**
```glsl
float depth = texture(depth_tex, uv).r * (max_depth - min_depth) + min_depth;
```

**Note:** This linear reconstruction assumes the normalized value is in `[0,1]` after division by 255, but the multiplication by `(max_depth - min_depth)` and addition of `min_depth` correctly inverts the normalization if the texture value is in `[0,255]`. However, the shader samples `depth_tex` as a normalized float (GL_RED → `[0,1]`), so the texture value is implicitly divided by 255 by OpenGL. The formula is correct.

### 6.2 Point Density Sampling

**Purpose:** Control number of points rendered by skipping pixels.

**Formula:**
```python
step = max(1, int(1.0 / self.point_density))
```

**Example:**
- `pointDensity = 1.0` → `step = 1` (every pixel)
- `pointDensity = 0.5` → `step = 2` (every other pixel)
- `pointDensity = 0.01` → `step = 100` (1% of pixels)

**Note:** This parameter is **not used** in the 2D shader version; it is only relevant for the 3D point cloud variant that generates vertex buffers. The 2D shader operates per-pixel and ignores `pointDensity`.

### 6.3 Depth-Based Color Mapping

**Shader Function:**
```glsl
vec3 depth_to_color(float depth) {
    float t = clamp((depth - min_depth) / (max_depth - min_depth), 0.0, 1.0);
    return mix(vec3(0.0, 0.0, 1.0), vec3(1.0, 0.0, 0.0), t);
}
```

**Interpretation:**
- `t = 0` (near `min_depth`) → blue `(0,0,1)`
- `t = 1` (near `max_depth`) → red `(1,0,0)`
- Linear interpolation between blue and red

**Noise Interference:**
```glsl
float noise = sin(uv.x * 100.0 + depth * 10.0) * 0.1;
depth_color += vec3(noise);
```

- Spatial frequency: 100 cycles across screen width
- Depth modulation: 10 rad/meter phase shift
- Amplitude: ±0.1 in RGB channels (low-contrast interference)

### 6.4 Composite Blending

**Final Output:**
```glsl
fragColor = vec4(mix(original.rgb, depth_color, u_mix * 0.5), original.a);
```

- Blend factor: `u_mix * 0.5` scales user blend to half intensity
- `u_mix = 0` → pure video
- `u_mix = 1` → 50% depth overlay
- Alpha preserved from original video

---

## 7. Performance Characteristics

### 7.1 Computational Complexity

| Stage | Operation | Cost |
|-------|-----------|------|
| `update_depth_data()` | Depth source fetch + object tracking | O(1) source-dependent |
| `apply_uniforms()` | Texture upload (full frame) | O(width × height) memory copy |
| Fragment shader | 1 depth texture fetch + 1 video fetch + arithmetic | O(width × height) fragment ops |

**Texture Upload Bandwidth:**
- At 1920×1080 @ 30 FPS: 1920×1080 × 1 byte = ~2 MB/frame × 30 = 60 MB/s
- Not negligible; consider dirty region or lower resolution depth

### 7.2 Memory Usage

| Resource | Size | Count | Total |
|----------|------|-------|-------|
| Depth texture (GL) | `width × height × 1` bytes | 1 | ~2 MB at 1080p |
| Depth frame (CPU) | `width × height × 4` bytes (float32) | 1 | ~8 MB at 1080p |
| VBO/VAO (unused in 2D) | — | — | 0 |
| Proximity effects list | ~200 bytes/entry × 10 | 1 | ~2 KB |

**Total:** ~10 MB per instance (mostly CPU depth buffer)

### 7.3 Bottlenecks

1. **Texture upload every frame:** No dirty tracking; even static depth causes full upload
2. **Depth source polling:** Called once per frame; depends on external source latency
3. **Fragment shader:** Light (2 texture reads, simple math); not the bottleneck

### 7.4 Optimization Opportunities

- **Dirty texture upload:** Only upload if `depth_frame` changed (compare hash or frame counter)
- **Lower resolution depth:** Upload at ½ or ¼ resolution, let GPU linear interpolate
- **Asynchronous PBO:** Use Pixel Buffer Objects for async texture upload
- **Remove unused parameters:** `pointSize`, `pointDensity` not used in 2D shader; could be repurposed for point density control via step uniform

---

## 8. Test Plan

### 8.1 Unit Tests

**Target:** ≥80% line coverage (current implementation ~200 lines)

| Test ID | Test Case | Expected Outcome |
|---------|-----------|------------------|
| `TEST_DEPTH_POINT_CLOUD_001` | `DepthPointCloudEffect()` construction | Parameters initialized to defaults; `depth_texture=0` |
| `TEST_DEPTH_POINT_CLOUD_002` | `set_parameter('pointSize', 7.5)` | `parameters['pointSize'] == 7.5` (clamped to [0,10]) |
| `TEST_DEPTH_POINT_CLOUD_003` | `set_parameter('invalid', 5.0)` | No change to parameters; base class handles |
| `TEST_DEPTH_POINT_CLOUD_004` | `_map_param('pointDensity', 0.01, 1.0)` with `pointDensity=5.0` | Returns `0.01 + (5/10)*(1-0.01) = 0.505` |
| `TEST_DEPTH_POINT_CLOUD_005` | `update_depth_data()` with mock source | `depth_frame` and `objects` updated from source |
| `TEST_DEPTH_POINT_CLOUD_006` | `update_depth_data()` with no source, bus unavailable | No exception; `depth_frame` unchanged |
| `TEST_DEPTH_POINT_CLOUD_007` | `apply_uniforms()` with valid depth | Creates texture, uploads data, sets uniforms |
| `TEST_DEPTH_POINT_CLOUD_008` | `apply_uniforms()` with `depth_frame=None` | `has_depth=0.0` (or texture not updated) |
| `TEST_DEPTH_POINT_CLOUD_009` | `apply_uniforms()` with NaN depth | Logs warning, `depth_frame` cleared, passthrough |
| `TEST_DEPTH_POINT_CLOUD_010` | `apply_uniforms()` with `min_depth == max_depth` | Division by zero → `depth_normalized` all NaN → undefined (document as bug) |
| `TEST_DEPTH_POINT_CLOUD_011` | `get_audio_reactivity_from_depth()` with 3 objects at depths [1.0, 2.0, 3.0] | Returns `{'object_count': 0.3, 'avg_depth': normalized_avg, ...}` |
| `TEST_DEPTH_POINT_CLOUD_012` | `apply_audio_reactivity()` with reactor | No error; stub does nothing |

### 8.2 Integration Tests

| Test ID | Test Case | Expected Outcome |
|---------|-----------|------------------|
| `TEST_DEPTH_POINT_CLOUD_I001` | Full render loop: `update_depth_data()` → `apply_uniforms()` → draw | Valid GL texture bound to unit 1; shader renders depth overlay |
| `TEST_DEPTH_POINT_CLOUD_I002` | Depth source disconnects mid-stream | `update_depth_data()` falls back to bus or passthrough |
| `TEST_DEPTH_POINT_CLOUD_I003` | Rapid parameter changes (10 Hz) | No GL errors; texture updates correctly |
| `TEST_DEPTH_POINT_CLOUD_I004` | Depth frame size changes (e.g., 640×480 → 1280×720) | Texture reallocated on next `apply_uniforms()` |
| `TEST_DEPTH_POINT_CLOUD_I005` | Multiple instances with different sources | Each maintains independent depth texture and state |

### 8.3 Visual Regression Tests

Capture reference frames with controlled depth patterns:

| Test ID | Depth Pattern | Parameter Settings | Expected Visual |
|---------|---------------|-------------------|-----------------|
| `TEST_DEPTH_POINT_CLOUD_V001` | Linear gradient 0.5–4.0m | `minDepth=0.5`, `maxDepth=4.0`, `u_mix=1.0` | Smooth blue→red gradient across depth |
| `TEST_DEPTH_POINT_CLOUD_V002` | Step depth: near=1.0m, far=5.0m | `minDepth=1.0`, `maxDepth=5.0` | Sharp color boundary at step |
| `TEST_DEPTH_POINT_CLOUD_V003` | Depth with NaN hole | Invalid pixel in center | Hole shows original video (no overlay) |
| `TEST_DEPTH_POINT_CLOUD_V004` | `u_mix=0.0` | Any depth | Pure video, no overlay |
| `TEST_DEPTH_POINT_CLOUD_V005` | `u_mix=1.0` | Any depth | Full overlay (50% blend) |

---

## 9. Migration Considerations (WebGPU / VJLive3)

### 9.1 OpenGL to WebGPU Porting Notes

**Key Changes Required:**

1. **Texture Management:**
   - Replace `glGenTextures`/`glTexImage2D` with `device.createTexture()` and `queue.writeTexture()`
   - Use `GPUTextureFormat.R8Unorm` for depth (matches GL_RED/GL_UNSIGNED_BYTE)
   - Create texture bind group with `sampler` and `texture` entries

2. **Uniform Buffers:**
   - Current: individual `set_uniform` calls
   - WebGPU: pack all uniforms into a single `GPUBuffer` with `uniform` binding
   - Uniform struct layout:
     ```wgsl
     struct Uniforms {
         u_mix: f32,
         point_size: f32,
         min_depth: f32,
         max_depth: f32,
         has_depth: f32,
         resolution: vec2<f32>,
         // padding to 16-byte alignment
     }
     ```

3. **Shader Conversion (GLSL → WGSL):**
   ```wgsl
   // Inputs
   @group(0) @binding(0) var tex0: texture_2d<f32>;
   @group(0) @binding(1) var depth_tex: texture_2d<f32>;
   @group(0) @binding(2) var s0: sampler;
   
   // Uniforms from buffer
   struct Params { ... };
   @group(0) @binding(3) var<uniform> params: Params;
   
   @fragment
   fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
       let original = textureSample(tex0, s0, uv);
       let depth_raw = textureSample(depth_tex, s0, uv).r;
       let depth = depth_raw * (params.max_depth - params.min_depth) + params.min_depth;
       // ... rest of logic
   }
   ```

4. **Depth Texture Upload:**
   - Create `depth_texture` as `GPUTexture` with `usage: TEXTURE_BINDING | COPY_DST`
   - Each frame: `queue.writeTexture({ texture: depth_texture, ... }, depth_normalized_data)`
   - No need to recreate texture if dimensions constant; just write new data

5. **Memory Leak Fix:**
   - Store `depth_texture` as `GPUTexture` object
   - On effect destruction or resize: `depth_texture.destroy()` (or let GC handle if no explicit destroy in WebGPU)

6. **Proximity/Audio Reactivity:**
   - Keep same Python-side logic; pass audio reactivity as additional uniforms or storage buffer
   - Consider moving proximity effect calculations to compute shader for performance

### 9.2 Bind Group Layout

**Bindings:**
- `0`: `texture_2d<f32>` — `tex0` (video)
- `1`: `texture_2d<f32>` — `depth_tex`
- `2`: `sampler` — linear sampler for both textures
- `3`: `uniform` buffer — all scalar parameters

**No storage buffers or external textures needed.**

### 9.3 Porting Effort Estimate

- **Low complexity:** Shader is simple (no loops, no complex math)
- **Medium effort:** Texture upload pipeline rewrite (GL → WebGPU API)
- **Low risk:** No feedback loops, no multiple render targets
- **Testing:** Visual regression tests sufficient; no algorithmic changes

---

## 10. Legacy Code References and Discrepancies

### 10.1 Source File

**Legacy Implementation:** `/home/happy/Desktop/claude projects/vjlive/plugins/vdepth/depth_effects.py`

- `DepthPointCloudEffect` class: lines 317–592
- `DepthEffect` base class: lines 49–316 (provides infrastructure)
- `DepthPointCloud3DEffect` class: lines 595–807 (separate 3D variant)

### 10.2 Known Discrepancies and Bugs

| Issue | Location | Impact | Fix Status |
|-------|----------|--------|------------|
| **Unused parameters** | `pointSize`, `pointDensity` not used in 2D shader | Confusing API; users expect point density control | In WebGPU: either use them (render actual point sprites) or remove from 2D variant |
| **Proximity audio stub** | `apply_audio_reactivity()` empty | Audio reactivity advertised but non-functional | Implement or remove method |
| **`self.distances` never populated** | `update_depth_data()` missing `get_inter_object_distances()` call | Proximity effects never trigger | Add `self.distances = self.depth_source.get_inter_object_distances()` |
| **Memory leak** | `self.depth_texture = glGenTextures(1)` never freed | GPU memory leak per instance | Add `__del__` method: `if self.depth_texture: glDeleteTextures([self.depth_texture])` |
| **Division by zero** | Normalization: `(self.max_depth - self.min_depth)` | Crash if equal | Clamp: `denom = max(1e-6, self.max_depth - self.min_depth)` |
| **No depth texture dirty tracking** | Upload every frame | Unnecessary bandwidth | Track `self.last_depth_hash` or frame counter |
| **Shader noise hard-coded** | `sin(uv.x * 100.0 + depth * 10.0)` | Not parameterized | Expose `noise_frequency`, `noise_depth_scale` as parameters |
| **`has_depth` uniform inconsistency** | Set in `apply_uniforms` but shader also checks `depth_frame` existence | Redundant | Keep or remove; current logic OK |

### 10.3 Related Classes

- **`DepthEffect`** (base): Provides 3D rendering infrastructure (`render_3d_depth_scene`, `_render_point_cloud`, `_setup_camera_matrices`). Not used by `DepthPointCloudEffect` (which inherits directly from `Effect`).
- **`DepthPointCloud3DEffect`**: True 3D variant with camera controls (`cameraDistance`, `cameraAngleX`, `cameraAngleY`). Separate class, not a mode of `DepthPointCloudEffect`.

---

## 11. Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (≥80% coverage)
- [ ] No file over 750 lines (current spec: ~300 lines)
- [ ] No stubs in code (legacy has stubs; Phase 3 implementation must fill)
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT062: DepthPointCloudEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

**Phase 2 Deliverable:** This fleshed specification.

---

## 12. Open Questions and Research Needs

1. **Should `DepthPointCloudEffect` support actual point sprites?** The 2D shader currently renders per-pixel color, not points. The `pointSize` and `pointDensity` parameters suggest an earlier design. Clarify intended visual: point cloud overlay vs. depth-colored video.
2. **Proximity audio reactivity:** Is this feature required for Phase 3, or can it be deferred? The infrastructure exists but is non-functional.
3. **Depth source contract:** Must `set_depth_source()` accept any object with methods, or should it type-check against `AstraDepthSource`?
4. **Texture upload optimization:** Is dirty tracking necessary for real-time performance? Benchmark with typical depth sources.
5. **WebGPU bind group layout:** Should `depth_tex` and `tex0` share a sampler? Current design uses same sampler; acceptable.

---
-

## 14. Migration Notes for Phase 3 Implementation

**Priority Order:**
1. Fix memory leak: ensure `depth_texture` is destroyed on effect teardown
2. Add division-by-zero protection in normalization
3. Decide on point sprite vs. per-pixel rendering and adjust parameters accordingly
4. Implement or remove proximity audio reactivity
5. Add dirty tracking for texture uploads
6. Port to WebGPU with bind group layout as described

**WebGPU Porting Checklist:**
- [ ] Create `GPUTexture` for depth (R8Unorm)
- [ ] Implement uniform buffer with std140 layout
- [ ] Convert GLSL shader to WGSL (straightforward)
- [ ] Bind group: tex0 (0), depth_tex (1), sampler (2), uniforms (3)
- [ ] Texture upload: `queue.writeTexture()` each frame
- [ ] Test with synthetic depth gradients
- [ ] Verify memory usage (no leaks)
- [ ] Performance: target <1 ms per frame for 1080p

**Testing Strategy:**
- Unit tests for parameter mapping and depth normalization
- Integration test with mock depth source (checkerboard pattern)
- Visual regression: compare screenshots against OpenGL reference (allow 1% color drift)

---

**End of Specification**
