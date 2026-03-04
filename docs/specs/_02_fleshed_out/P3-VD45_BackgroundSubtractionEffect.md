# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD45_BackgroundSubtractionEffect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD45 — BackgroundSubtractionEffect

## Description

The BackgroundSubtractionEffect performs real-time background subtraction using OpenCV's MOG2 (Mixture of Gaussians) algorithm to isolate foreground elements from the background. It generates a probability mask indicating which pixels belong to the foreground, then uses this mask to apply various visual effects: silhouette replacement, ghosting, or foreground isolation.

This effect is ideal for creating silhouettes, removing backgrounds, or highlighting moving objects. It's commonly used in VJ performances to create dynamic masks, isolate performers, or generate ghostly after-images. The effect maintains a running background model that adapts to gradual lighting changes and can handle shadows.

## What This Module Does

- Performs background subtraction using OpenCV MOG2 algorithm
- Generates a foreground probability mask (0-1)
- Applies optional Gaussian blur to smooth the mask
- Supports three effect modes: silhouette, ghosting, foreground isolation
- Allows customization of silhouette color, opacity, and threshold
- Uploads mask as a texture for GPU processing
- Integrates with standard Effect base class

## What This Module Does NOT Do

- Does NOT perform depth-based background subtraction (RGB only)
- Does NOT provide CPU fallback (requires OpenCV)
- Does NOT implement advanced segmentation (ML-based)
- Does NOT store persistent state across sessions
- Does NOT handle camera motion compensation (static camera assumed)
- Does NOT provide real-time mask refinement (basic blur only)

---

## Detailed Behavior

### Background Subtraction Pipeline

1. **Update background model**: For each incoming frame, feed it to the MOG2 subtractor:
   ```python
   fg_mask = self.subtractor.apply(frame)
   ```
   The `fg_mask` is a single-channel image where:
   - 0 = background
   - 127 = shadow (if detected)
   - 255 = foreground

2. **Convert to probability**: Normalize mask to [0,1] range:
   ```python
   mask_float = fg_mask.astype(np.float32) / 255.0
   ```

3. **Apply blur**: If `blur` parameter > 0, apply Gaussian blur to smooth mask edges:
   ```python
   kernel_size = int(blur) * 2 + 1  # Ensure odd
   mask_float = cv2.GaussianBlur(mask_float, (kernel_size, kernel_size), 0)
   ```

4. **Upload mask texture**: Create/update a 2-channel float texture (R = mask, G = unused):
   ```python
   mask_rgb = np.zeros((h, w, 2), dtype=np.float32)
   mask_rgb[..., 0] = mask_float
   chain.update_float_texture(self.mask_texture, mask_rgb)
   ```

5. **Shader processing**: The fragment shader samples the mask and applies the selected effect mode.

### Effect Modes

**Mode 0: Silhouette**
- Replaces background with silhouette color, preserves foreground video
- `foreground = step(threshold, mask)`
- `color = silhouetteColor * foreground + video.rgb * (1 - foreground)`
- Creates a colored silhouette effect

**Mode 1: Ghosting**
- Fades entire video toward silhouette color based on foreground strength
- `alpha = foreground * opacity * u_mix`
- `color = mix(video.rgb, silhouetteColor, alpha)`
- Creates a ghostly overlay

**Mode 2: Foreground Isolation**
- Shows foreground normally, darkens background
- `color = mix(video.rgb, video.rgb * foreground, opacity * u_mix)`
- Isolates the foreground subject

### Parameters

All parameters use a 0-10 range from UI sliders (except `effectMode` which is derived):

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `threshold` | float | 5.0 | 0.0-10.0 | Foreground detection threshold (mapped to 0-1 in shader) |
| `blur` | float | 0.0 | 0.0-10.0 | Gaussian blur kernel size (0=no blur, 10→21×21 kernel) |
| `opacity` | float | 10.0 | 0.0-10.0 | Effect strength (mapped to 0-1) |
| `effectMode` | int | 0 | 0-2 | 0=silhouette, 1=ghosting, 2=foreground isolation |
| `silhouetteColorR`, `silhouetteColorG`, `silhouetteColorB` | float | 10.0, 10.0, 10.0 | 0.0-10.0 | Silhouette color (white) |

**Inherited from Effect**: `u_mix`, `resolution`

---

## Public Interface

```python
class BackgroundSubtractionEffect(Effect):
    def __init__(self) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None, semantic_layer=None) -> None: ...
    def delete(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input video frame (HxWxC, BGR or RGB) |
| **Output** | `np.ndarray` | Processed frame with background subtraction effect (HxWxC) |

---

## State Management

**Persistent State:**
- `_subtractor: cv2.BackgroundSubtractorMOG2` — OpenCV background subtractor
- `_mask_texture: int` — GL texture for mask (2-channel float)
- `_parameters: dict` — Effect parameters (threshold, blur, opacity, effectMode)
- `_silhouetteColor: Tuple[float, float, float]` — Silhouette color (0-10 range)
- `_shader: ShaderProgram` — Compiled shader
- `_pre_process_counter: int` — For periodic processing (if needed)

**Per-Frame:**
- Apply frame to MOG2 subtractor to get mask
- Convert mask to float and optionally blur
- Upload mask texture to GPU
- Render with shader applying effect mode

**Initialization:**
- Create MOG2 subtractor with `history=100`, `varThreshold=16`, `detectShadows=True`
- Create mask texture (lazy)
- Compile shader
- Default parameters: threshold=5.0, blur=0.0, opacity=10.0, effectMode=0, silhouetteColor=(10,10,10)

**Cleanup:**
- Delete mask texture (`glDeleteTextures`)
- Call `super().delete()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Mask texture | GL_TEXTURE_2D | GL_RG32F (2-channel float) | frame size | Updated each frame |
| Shader program | GLSL | vertex + fragment | N/A | Init once |

**Memory Budget (640×480):**
- Mask texture: 640×480×2×4 bytes = ~2.5 MB
- Shader: ~10-50 KB
- Total: ~2.5 MB

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| OpenCV not available | `ImportError` at init | Install opencv-python |
| Frame is None | Skip processing, return None or original | Normal operation |
| Mask texture upload fails | `RuntimeError("GPU error")` | Check GL errors |
| Shader compilation fails | `ShaderCompilationError` | Log and abort |
| Invalid parameter | Clamp to range | Document valid ranges |

---

## Thread Safety

The effect is **not thread-safe**. The MOG2 subtractor is not thread-safe, and the mask texture is updated each frame. All GPU operations must occur on the thread with the OpenGL context. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- MOG2 apply: ~2-5 ms (CPU)
- Gaussian blur (if enabled): ~1-3 ms (CPU)
- Texture upload: ~0.5-1 ms
- Shader render: ~0.5-1 ms
- Total: ~4-10 ms on CPU+GPU

**Optimization Strategies:**
- Reduce frame resolution before processing (downsample)
- Skip blur if not needed
- Use a smaller `history` parameter for MOG2 (faster but less stable)
- Cache mask texture if frame unchanged
- Process every Nth frame if real-time not critical

---

## Integration Checklist

- [ ] OpenCV installed (`pip install opencv-python`)
- [ ] Effect instantiated with shader
- [ ] `process_frame()` called each frame with BGR/RGB frame
- [ ] `apply_uniforms()` called before rendering
- [ ] Mask texture bound to texture unit 1
- [ ] `delete()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with MOG2 subtractor |
| `test_set_parameter` | Parameters can be set and clamped |
| `test_get_parameter` | Parameters can be retrieved |
| `test_process_frame_first` | First frame produces mask (all background initially) |
| `test_process_frame_motion` | Moving object creates foreground mask |
| `test_threshold` | Higher threshold reduces foreground |
| `test_blur` | Blur smooths mask edges |
| `test_silhouette_mode` | Silhouette color applied correctly |
| `test_ghosting_mode` | Ghosting effect blends toward silhouette color |
| `test_foreground_isolation_mode` | Background darkened, foreground preserved |
| `test_mask_texture_upload` | Mask texture created and updated |
| `test_apply_uniforms` | Uniforms set correctly (threshold, blur, opacity, color, mode) |
| `test_shader_compilation` | Shader compiles and links |
| `test_delete` | Resources cleaned up |
| `test_no_memory_leak` | Repeated init/delete cycles don't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD45: background_subtraction_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vcore/background_subtraction.py` — VJLive Original implementation
- `core/effects/__init__.py` — Registers effect in `BACKGROUND_SUBTRACTION` category
- `plugins/vcore/manifest.json` — Effect manifest entry

Design decisions inherited:
- Effect name: `background_subtraction`
- Inherits from `Effect` (not `DepthEffect`)
- Uses OpenCV MOG2 (`cv2.createBackgroundSubtractorMOG2`)
- Parameters in 0-10 range (UI slider mapping)
- Three effect modes: silhouette (0), ghosting (1), foreground isolation (2)
- Mask uploaded as 2-channel float texture (GL_RG32F)
- Shader uses `texMask` sampler2D, uniforms: threshold, blur, opacity, silhouetteColor, effectMode
- Allocates GL resources: mask texture

---

## Notes for Implementers

1. **OpenCV Dependency**: Ensure `opencv-python` is installed. The effect will fail to import if not available. Consider graceful degradation or clear error message.

2. **MOG2 Parameters**: The legacy uses:
   ```python
   cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=16, detectShadows=True)
   ```
   These can be made configurable if needed. `history` is number of frames to keep for background model. `varThreshold` affects sensitivity. `detectShadows` marks shadows as 127 in mask.

3. **Mask Conversion**: MOG2 returns mask with values {0, 127, 255}. Convert to float [0,1]:
   ```python
   mask_float = fg_mask.astype(np.float32) / 255.0
   ```
   Shadows become ~0.5. You may want to treat shadows as background by thresholding.

4. **Blur Kernel**: The `blur` parameter (0-10) is mapped to kernel size:
   ```python
   kernel_size = int(blur) * 2 + 1  # e.g., blur=5 → 11×11
   ```
   Ensure kernel size is odd and positive.

5. **Texture Format**: The legacy uses a 2-channel float texture (`GL_RG32F`). This is overkill; you could use single-channel (`GL_R32F`) or even normalized byte (`GL_R8`). However, using float gives precision for smooth blending.

6. **Shader Uniforms**: Must set:
   - `texMask` (int) — texture unit 1
   - `threshold` (float) — `threshold / 10.0`
   - `blur` (float) — passed directly (but blur already applied on CPU)
   - `opacity` (float) — `opacity / 10.0`
   - `silhouetteColor` (vec3) — `(r/10.0, g/10.0, b/10.0)`
   - `effectMode` (int) — 0, 1, or 2

7. **Performance**: MOG2 is CPU-bound. For high-resolution video, consider:
   - Downsampling before MOG2
   - Using a faster background subtractor (e.g., `cv2.createBackgroundSubtractorKNN` is slower)
   - Processing every other frame
   - Using a GPU-based background subtraction if available

8. **Shadow Handling**: MOG2 can detect shadows (value 127). The legacy code doesn't explicitly handle them; they become ~0.5 in float mask and are treated as partial foreground. You may want to threshold them out or treat as background.

9. **Initialization**: The first few frames (up to `history`) will have poor quality as the background model learns. Consider discarding initial frames or using a static background image if available.

10. **Testing**: Use a video with a static background and moving foreground (person, object). Verify mask correctly identifies moving regions. Test different thresholds and blur amounts.

11. **Future Extensions**:
    - Add learning rate control
    - Add shadow detection toggle
    - Add mask erosion/dilation
    - Add color-based foreground enhancement
    - Add depth integration (if depth available)

---
-

## References

- OpenCV MOG2: https://docs.opencv.org/master/d1/dc5/tutorial_background_subtraction.html
- Background subtraction: https://en.wikipedia.org/wiki/Background_subtraction
- Gaussian blur: https://docs.opencv.org/master/d4/d86/group__imgproc__filter.html#ga8c45db9afe636703801b0b2e440fce37
- VJLive legacy: `plugins/vcore/background_subtraction.py`

---

## Implementation Tips

1. **Shader Code**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;
   uniform sampler2D texMask;
   uniform vec2 resolution;
   uniform float u_mix;
   uniform float threshold;       // 0-10
   uniform float blur;            // 0-10 (unused if blur done on CPU)
   uniform vec3 silhouetteColor;  // 0-10 per channel
   uniform float opacity;         // 0-10
   uniform int effectMode;        // 0,1,2
   
   void main() {
       vec4 video = texture(tex0, uv);
       float t = threshold / 10.0;     // Convert to 0-1
       float op = opacity / 10.0;      // Convert to 0-1
       vec3 sc = silhouetteColor / 10.0; // Convert to 0-1
       
       float mask = texture(texMask, uv).r;  // Foreground probability [0,1]
       
       // Apply threshold
       float foreground = step(t, mask);
       
       vec3 color = video.rgb;
       
       if (effectMode == 0) {
           // Silhouette mode
           vec3 silhouette = sc * foreground;
           vec3 background = video.rgb * (1.0 - foreground);
           color = mix(video.rgb, silhouette + background, op * u_mix);
       } else if (effectMode == 1) {
           // Ghosting mode
           float alpha = foreground * op * u_mix;
           color = mix(video.rgb, sc, alpha);
       } else if (effectMode == 2) {
           // Foreground isolation
           color = mix(video.rgb, video.rgb * foreground, op * u_mix);
       }
       
       fragColor = vec4(color, video.a);
   }
   ```

2. **Python Processing**:
   ```python
   def process_frame(self, frame):
       # frame: HxWxC (BGR or RGB, uint8)
       
       # Apply to MOG2
       fg_mask = self.subtractor.apply(frame)
       
       # Convert to float [0,1]
       mask_float = fg_mask.astype(np.float32) / 255.0
       
       # Apply blur if requested
       if self.parameters["blur"] > 0:
           kernel = int(self.parameters["blur"]) * 2 + 1
           mask_float = cv2.GaussianBlur(mask_float, (kernel, kernel), 0)
       
       # Upload as 2-channel float texture
       h, w = mask_float.shape
       mask_rg = np.zeros((h, w, 2), dtype=np.float32)
       mask_rg[..., 0] = mask_float
       
       if self.mask_texture is None:
           self.mask_texture = glGenTextures(1)
           glBindTexture(GL_TEXTURE_2D, self.mask_texture)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
           glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
       
       glBindTexture(GL_TEXTURE_2D, self.mask_texture)
       glTexImage2D(GL_TEXTURE_2D, 0, GL_RG32F, w, h, 0, GL_RG, GL_FLOAT, mask_rg)
       
       # Continue to render with shader
       return super().process_frame(frame)
   ```

3. **Parameter Mapping**: The UI uses 0-10 range. Map to actual values in shader:
   - `threshold` → `threshold/10.0` (0-1)
   - `opacity` → `opacity/10.0` (0-1)
   - `silhouetteColor` → each component `/10.0`
   - `effectMode` derived from `effectMode` param (0-2)

4. **Texture Management**: The mask texture should be updated each frame. Use `glTexImage2D` to replace data. If resolution changes, recreate texture.

5. **OpenCV MOG2**: The subtractor maintains internal state. It should persist across frames. Do not recreate each frame.

6. **Frame Format**: OpenCV expects BGR, but the effect should work with RGB too. Document expected format.

7. **Performance**: If processing is too slow, consider:
   - Processing at lower resolution (e.g., 320×240) and upscaling mask
   - Using `history=50` for faster adaptation
   - Skipping blur or using a faster blur implementation

---

## Conclusion

The BackgroundSubtractionEffect provides real-time foreground/background separation using OpenCV's MOG2 algorithm. It enables a variety of creative effects from silhouettes to ghosting to foreground isolation, making it a versatile tool for VJ performances. The effect combines CPU-based background modeling with GPU-based rendering for optimal performance and flexibility.

---
