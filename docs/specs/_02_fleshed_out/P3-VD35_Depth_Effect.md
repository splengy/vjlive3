# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD35_Depth_Effect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD35 — DepthEffect (Base Class)

## Description

The `DepthEffect` base class provides a foundation for all depth-aware visual effects in VJLive3. It encapsulates common functionality for managing depth sources, handling depth texture lifecycle, and providing a standardized interface for depth-based processing. All depth effects (such as DepthColorGrade, DepthEdgeGlow, DepthDistanceFilter, etc.) inherit from this base class to ensure consistency and reduce code duplication.

The base class handles:
- Connection to an `AstraDepthSource` (or compatible depth provider)
- Depth frame retrieval and caching
- OpenGL texture management for depth data
- Automatic texture updates when depth source changes
- Common parameters like depth range (near/far clipping)
- Resource cleanup (texture deletion)

## What This Module Does

- Provides abstract base class for all depth-based effects
- Manages depth source lifecycle: set, update, disconnect
- Handles GPU texture creation and updates for depth maps
- Caches depth frames to avoid redundant texture uploads
- Defines common depth-related parameters (near_clip, far_clip, depth_scale)
- Implements resource cleanup (glDeleteTextures)
- Establishes naming conventions and interface contracts for derived classes

## What This Module Does NOT Do

- Does NOT implement any specific visual effect (that's for subclasses)
- Does NOT provide depth source implementations (only consumes them)
- Does NOT perform depth processing (filtering, smoothing, etc.)
- Does NOT manage node graph connections (base class only)
- Does NOT provide audio reactivity (subclasses add this)
- Does NOT handle multiple depth sources (single source only)
- Does NOT implement shader compilation (subclasses provide their own shaders)

---

## Detailed Behavior

### Depth Source Management

The `DepthEffect` base class maintains a reference to a depth source object that implements the `AstraDepthSource` interface:

```python
class AstraDepthSource(ABC):
    @abstractmethod
    def get_depth_frame(self) -> Optional[np.ndarray]:
        """Retrieve the latest depth map as a 2D array."""
        pass
    
    @abstractmethod
    def get_color_frame(self) -> Optional[np.ndarray]:
        """Retrieve the corresponding color frame (if available)."""
        pass
    
    @abstractmethod
    def get_intrinsics(self) -> Dict[str, float]:
        """Return camera intrinsics (fx, fy, cx, cy)."""
        pass
```

The effect connects to a source via `set_depth_source(source)` and calls `source.get_depth_frame()` each frame in `update_depth_data()`.

### Depth Texture Lifecycle

The base class manages an OpenGL texture (`_depth_texture`) that stores the depth map on the GPU:

1. **Creation**: On first `update_depth_data()` call, generate a texture with `glGenTextures(1)`
2. **Format**: Use `GL_R8` for 8-bit depth or `GL_R16` for 16-bit depth (auto-detect from frame dtype)
3. **Upload**: Each frame, if depth data changed, upload via `glTexSubImage2D` (or `glTexImage2D` on size change)
4. **Resize**: If depth frame dimensions change, reallocate texture with `glTexImage2D`
5. **Deletion**: In `cleanup()`, call `glDeleteTextures(1, [_depth_texture])` and set to 0

### Depth Normalization

Depth cameras may output various formats:
- 8-bit unsigned (0-255) → normalize to [0,1] by dividing by 255.0
- 16-bit unsigned (0-65535) → normalize to [0,1] by dividing by 65535.0
- Float32 (0.0-1.0 or arbitrary) → clamp to [0,1] or use `near_clip`/`far_clip`

The base class provides `normalize_depth(frame: np.ndarray) -> np.ndarray` that handles these conversions.

### Common Parameters

All depth effects should support these standard parameters (exposed via `get_parameters()` and `set_parameter()`):

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `near_clip` | float | 1.0 | 0.0 - 10.0 | Near clipping distance (0=camera face, 10=max depth range) |
| `far_clip` | float | 10.0 | 0.0 - 10.0 | Far clipping distance (0=camera face, 10=max depth range) |
| `depth_scale` | float | 1.0 | 0.1 - 10.0 | Multiplier applied to depth values |
| `invert_depth` | float | 0.0 | 0.0 - 10.0 | Invert depth (0.0=normal, >0.0=inverted; 1.0 = full inversion) |

These parameters are applied in `apply_depth_transform(depth: np.ndarray) -> np.ndarray`:

```python
def apply_depth_transform(self, depth: np.ndarray) -> np.ndarray:
    # Normalize to [0,1] if needed
    depth = self.normalize_depth(depth)
    
    # Apply scale
    depth = depth * self.depth_scale
    
    # Invert if requested (param > 0 = inverted)
    if self.invert_depth > 0.0:
        depth = 1.0 - depth
    
    # Map 0-10 VJ params down to [0,1] clip values
    near = self.near_clip / 10.0
    far  = self.far_clip  / 10.0
    
    # Clamp to near/far
    depth = np.clip(depth, near, far)
    
    # Re-normalize to [0,1] after clipping
    depth = (depth - near) / (far - near + 1e-6)
    
    return depth
```

### Interface Contract

Subclasses must implement:

- `__init__(self)`: Call `super().__init__("effect_name", shader_fragment)` and initialize `_depth_source`, `_depth_frame`, `_depth_texture`
- `update_depth_data(self) -> None`: Fetch fresh depth from source, update texture
- `process_frame(self, frame: np.ndarray) -> np.ndarray`: Apply effect (must call `update_depth_data()` first)
- `cleanup(self) -> None`: Release GPU resources (call `super().cleanup()`)

Optionally override:
- `set_depth_source(self, source)`: Add custom source handling
- `apply_depth_transform(self, depth)`: Custom depth normalization
- `on_resolution_change(self, width, height)`: Handle frame size changes

### Shader Uniforms

The base class provides these uniforms to all depth effect shaders:

| Uniform | Type | Description |
|---------|------|-------------|
| `u_depth_texture` | `sampler2D` | Depth map texture |
| `u_near_clip` | `float` | Near clipping plane (normalized 0-1, mapped from VJ 0-10 param) |
| `u_far_clip` | `float` | Far clipping plane (normalized 0-1, mapped from VJ 0-10 param) |
| `u_depth_scale` | `float` | Depth scale multiplier |
| `u_invert_depth` | `float` | Depth inversion (0.0=normal, >0.0=inverted) |
| `u_frame_width` | `int` | Frame width in pixels |
| `u_frame_height` | `int` | Frame height in pixels |

Subclasses add their own uniforms via `apply_uniforms()`.

---

## Public Interface

```python
class DepthEffect(Effect):
    def __init__(self, name: str, fragment_shader: str) -> None: ...
    def set_depth_source(self, source: AstraDepthSource) -> None: ...
    def get_depth_source(self) -> Optional[AstraDepthSource]: ...
    def update_depth_data(self) -> None: ...
    def get_depth_texture(self) -> int: ...
    def normalize_depth(self, depth: np.ndarray) -> np.ndarray: ...
    def apply_depth_transform(self, depth: np.ndarray) -> np.ndarray: ...
    def set_parameter(self, name: str, value: Any) -> None: ...
    def get_parameters(self) -> Dict[str, Any]: ...
    def cleanup(self) -> None: ...
    def on_resolution_change(self, width: int, height: int) -> None: ...
```

---

## Inputs and Outputs

The base class itself has no inputs/outputs. Subclasses define their own.

---

## Parameters (Base Class)

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `near_clip` | float | 1.0 | 0.0 - 10.0 | Near clipping distance (0=camera face, 10=max depth range) |
| `far_clip` | float | 10.0 | 0.0 - 10.0 | Far clipping distance (0=camera face, 10=max depth range) |
| `depth_scale` | float | 1.0 | 0.1 - 10.0 | Multiplier applied to raw depth values |
| `invert_depth` | float | 0.0 | 0.0 - 10.0 | Invert depth (0.0=normal, >0.0=inverted) |

---

## State Management

**Persistent State:**
- `_name: str` — Effect name
- `_depth_source: Optional[AstraDepthSource]` — Connected depth source
- `_depth_frame: Optional[np.ndarray]` — Last retrieved depth frame (H or HxW)
- `_depth_texture: int` — OpenGL texture ID (0 if not created)
- `_frame_width: int` — Current frame width
- `_frame_height: int` — Current frame height
- `_parameters: dict` — Current parameter values
- `_shader: ShaderProgram` — Compiled shader program

**Per-Frame State:**
- None (stateless between frames)

**Initialization:**
- Shader compiled in `__init__()`
- Texture created on first `update_depth_data()`
- Parameters initialized to defaults

**Cleanup:**
- Delete depth texture if `_depth_texture != 0`
- Delete shader program
- Clear `_depth_source` reference (do not delete source)

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Depth texture | GL_TEXTURE_2D | GL_R8 or GL_R16 | depth frame size | Created on first depth update, recreated if size changes |

**Memory Budget (1080p depth):**
- GL_R8: 1920 × 1080 × 1 byte = ~2.1 MB
- GL_R16: 1920 × 1080 × 2 bytes = ~4.2 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| Depth source not set | `RuntimeError("No depth source")` | Call `set_depth_source()` before `update_depth_data()` |
| Depth frame is None | Log warning, texture not updated | Continue with previous depth frame if available |
| Texture creation fails | `RuntimeError` (out of GPU memory) | Propagate to caller |
| Shader compilation fails | `ShaderCompilationError` | Log error, effect becomes no-op |
| Invalid parameter name | `KeyError` or `ValueError` | Validate parameter names in `set_parameter()` |
| Parameter value out of range | Clamp to valid range or raise `ValueError` | Document ranges; optionally clamp |
| Resolution mismatch | Depth texture size ≠ expected | Recreate texture with correct size |

---

## Thread Safety

The base class is **not thread-safe**. All GPU operations (texture creation, updates, deletion) must occur on the thread with the current OpenGL context. The `_depth_frame` cache is mutated in `update_depth_data()`, so concurrent calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Overhead (per frame):**
- Depth frame retrieval: ~0.1-0.5 ms (depends on source)
- Texture upload (1080p, GL_R8): ~0.5-1 ms (PCIe bandwidth)
- Total base class overhead: ~1-2 ms

Subclasses add their own processing time on top of this.

**Optimization Strategies:**
- Only update texture if depth frame changed (compare frame counters or hash)
- Use `glTexSubImage2D` instead of `glTexImage2D` when size unchanged
- Use `GL_R8` for 8-bit depth to reduce bandwidth by 2× vs RGBA
- Consider PBOs (Pixel Buffer Objects) for asynchronous texture uploads if source is CPU-side

---

## Integration Checklist

- [ ] Subclass calls `super().__init__(name, fragment_shader)` in its `__init__`
- [ ] Subclass implements `update_depth_data()` and calls `super().update_depth_data()` if needed
- [ ] Subclass implements `process_frame()` and calls `self.update_depth_data()` at the start
- [ ] Subclass implements `cleanup()` and calls `super().cleanup()` to release texture
- [ ] Depth source is set before first `process_frame()` call
- [ ] Shader includes `u_depth_texture`, `u_near_clip`, `u_far_clip`, etc.
- [ ] Parameters `near_clip`, `far_clip`, `depth_scale`, `invert_depth` are exposed via UI

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Base class initializes with name and shader |
| `test_set_depth_source` | Depth source is stored and can be retrieved |
| `test_update_depth_data_no_source` | Raises error if source not set |
| `test_update_depth_data_with_source` | Retrieves depth, creates/updates texture |
| `test_normalize_depth_8bit` | 8-bit depth (0-255) normalized to [0,1] |
| `test_normalize_depth_16bit` | 16-bit depth (0-65535) normalized to [0,1] |
| `test_normalize_depth_float` | Float32 depth handled correctly |
| `test_apply_depth_transform` | Scale, invert, near/far clipping applied |
| `test_get_depth_texture` | Returns valid texture ID after update |
| `test_parameter_set_get` | Parameters can be set and retrieved |
| `test_cleanup` | Texture deleted, ID set to 0, shader deleted |
| `test_resolution_change` | Texture recreated when frame size changes |
| `test_subclass_interface` | Subclass must implement abstract methods |

**Minimum coverage:** 95% (base class is critical)

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD35: depth_effect_base` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vdepth/depth_effects.py` — Contains `DepthEffect` and other depth effect classes (VJLive Original)
- `core/effects/depth_effects.py` — VJLive-2 version with `DepthEffect`, `DepthPointCloudEffect`, `DepthMeshEffect`
- `sdk/examples/pro_depth/effect.py` — Example `ProDepthEffect` implementation
- `core/shader_pipeline_verifier.py` — References `DepthEffect` uniforms: `min_depth`, `max_depth`, `projection_matrix`, `view_matrix`, `model_matrix`

Design decisions inherited:
- Base class name: `DepthEffect`
- Inherits from `Effect` (not standalone)
- Manages `_depth_source`, `_depth_frame`, `_depth_texture`
- Provides common uniforms: `u_depth_texture`, `u_near_clip`, `u_far_clip`
- Subclasses: `DepthPointCloudEffect`, `DepthMeshEffect`, `DepthContourEffect`, `DepthDistortionEffect`, `DepthFieldEffect`, etc.

---

## Notes for Implementers

1. **Depth Source Interface**: The `AstraDepthSource` interface is defined elsewhere (likely in `core/sources/depth_source.py`). Ensure your implementation matches that interface. The key method is `get_depth_frame()` which returns a 2D numpy array.

2. **Texture Format Selection**: Auto-detect the appropriate texture format based on the depth frame's dtype:
   - `np.uint8` → `GL_R8`
   - `np.uint16` → `GL_R16`
   - `np.float32` → `GL_R32F` (if supported) or `GL_RGBA32F` with depth in R channel
   Provide a helper method `_get_texture_format(dtype)`.

3. **Shader Uniforms**: The base class should set the common uniforms before calling the subclass's `apply_uniforms()`. In the `render()` or `process_frame()` method:
   ```python
   self.shader.set_uniform('u_depth_texture', self._depth_texture)
   self.shader.set_uniform('u_near_clip', self.near_clip)
   self.shader.set_uniform('u_far_clip', self.far_clip)
   self.shader.set_uniform('u_depth_scale', self.depth_scale)
   self.shader.set_uniform('u_invert_depth', self.invert_depth)
   self.apply_uniforms()  # Subclass adds its own
   ```

4. **Resource Management**: The base class `cleanup()` must be called by subclasses. Use a template method pattern:
   ```python
   class DepthEffect(Effect):
       def cleanup(self):
           if self._depth_texture != 0:
               glDeleteTextures(1, [self._depth_texture])
               self._depth_texture = 0
           # Subclasses should call super().cleanup() after their own cleanup
   ```

5. **Resolution Changes**: If the frame size changes (e.g., pipeline resolution switch), the base class should be notified via `on_resolution_change(width, height)`. Subclasses can override this to handle their own resources. The base class may need to recreate the depth texture if the depth source's resolution changes.

6. **Depth Frame Caching**: To avoid unnecessary texture uploads, store a frame counter or hash from the depth source. Only upload if `depth_frame` differs from last frame. Many depth sources provide a `frame_number` or `timestamp` that can be compared.

7. **Error Handling**: The base class should be robust. If `get_depth_frame()` returns None, log a warning but don't crash. The effect can either skip processing or use the previous frame.

8. **Performance**: The base class adds minimal overhead. The main cost is texture upload. Consider using Pixel Buffer Objects (PBOs) for asynchronous uploads if the depth source is CPU-side and causing stalls.

9. **Documentation**: Document the expected depth range and normalization behavior clearly. Depth cameras vary widely (some output in millimeters, some in meters, some arbitrary units). The `depth_scale` and `near_clip`/`far_clip` parameters allow adaptation.

10. **Testing**: The base class should have extensive tests because it's foundational. Test with various depth formats (8-bit, 16-bit, float), resolutions, and edge cases (None frames, source disconnection, etc.).

---
-

## References

- VJLive1 legacy: `vjlive1/plugins/depth_effects.py` (if exists)
- OpenGL texture management: https://learnopengl.com/Advanced-OpenGL/Texture-class
- Depth camera interfaces: Intel RealSense SDK, Azure Kinect SDK
- Abstract base classes: https://docs.python.org/3/library/abc.html

---

## Implementation Tips

1. **Class Structure**:
   ```python
   class DepthEffect(Effect):
       def __init__(self, name: str, fragment_shader: str):
           super().__init__(name, fragment_shader)
           self._depth_source = None
           self._depth_frame = None
           self._depth_texture = 0
           self._frame_width = 1920   # TODO: pull from config.render.width (P1-C4)
           self._frame_height = 1080  # TODO: pull from config.render.height (P1-C4)
           self._parameters = {
               'near_clip': 1.0,
               'far_clip': 10.0,
               'depth_scale': 1.0,
               'invert_depth': 0.0,
           }
       
       def set_depth_source(self, source):
           self._depth_source = source
       
       def update_depth_data(self):
           if self._depth_source is None:
               raise RuntimeError("No depth source set")
           
           depth = self._depth_source.get_depth_frame()
           if depth is None:
               logger.warning("Depth source returned None")
               return
           
           # Normalize and transform
           depth = self.apply_depth_transform(depth)
           
           # Update texture
           self._update_depth_texture(depth)
       
       def _update_depth_texture(self, depth: np.ndarray):
           if self._depth_texture == 0:
               glGenTextures(1, [self._depth_texture])
           
           glBindTexture(GL_TEXTURE_2D, self._depth_texture)
           # Set texture parameters (GL_CLAMP_TO_EDGE, GL_NEAREST for depth)
           # Upload with glTexImage2D or glTexSubImage2D
           # ...
       
       def cleanup(self):
           if self._depth_texture != 0:
               glDeleteTextures(1, [self._depth_texture])
               self._depth_texture = 0
   ```

2. **Shader Boilerplate**: Provide a common vertex shader that all depth effects can use (simple full-screen quad). Subclasses only need to provide fragment shaders.

3. **Parameter Validation**: In `set_parameter()`, validate:
   - `near_clip` and `far_clip`: 0.0 ≤ near < far ≤ 10.0 (mapped to [0,1] internally via ÷10)
   - `depth_scale`: > 0
   - `invert_depth`: float ≥ 0.0 (>0.0 = inverted; treat as boolean threshold)

4. **Frame Size Handling**: The base class should know the expected frame size (from the pipeline). Provide `set_frame_size(width, height)` to update `_frame_width` and `_frame_height`. This is useful for shader uniforms.

5. **Depth Source Abstraction**: The base class should not assume a specific depth source class. Use duck typing: any object with `get_depth_frame()` method works.

6. **Logging**: Use the project's logging facility. Log at appropriate levels: warning for missing frames, error for source not set, debug for texture updates.

7. **Testing with Mocks**: Create a mock `AstraDepthSource` that returns synthetic depth maps (gradients, steps, spheres) for testing.

8. **Documentation**: Document the expected depth format (normalized, linear) and the transformation pipeline clearly. This is a common source of confusion.

---
