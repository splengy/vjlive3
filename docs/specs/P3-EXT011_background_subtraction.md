# P3-EXT011: BackgroundSubtractionEffect

**Priority:** P3-EXT (Missing Legacy Effects Parity)
**Status:** Spec Draft
**Assignee:** TBD
**Estimated Completion:** 2-3 days

---

## 📋 Task Overview

Port the legacy `BackgroundSubtractionEffect` from VJLive-2 to VJLive3. This is a CPU-based effect using OpenCV's MOG2 background subtractor to create silhouettes, ghosting, and foreground isolation effects. The effect computes a foreground mask on the CPU and uploads it as a texture for GPU blending.

---

## 🎯 Core Concept

BackgroundSubtractionEffect performs real-time background subtraction using OpenCV's MOG2 algorithm:

- **CPU Processing**: Uses `cv2.createBackgroundSubtractorMOG2()` to compute foreground mask
- **Adaptive Throttling**: Integrates with frame budget allocator to maintain 60 FPS
- **Adaptive LOD**: Downscales input frame for mask computation (configurable scale)
- **Mask Texture**: Uploads foreground probability mask as 2-channel float texture
- **GPU Blending**: Fragment shader applies threshold, blur, and blending modes
- **3 Effect Modes**: Silhouette, Ghosting, Foreground Isolation

The legacy implementation is ~204 lines with a 63-line fragment shader.

---

## 1. File Structure

```
src/vjlive3/plugins/background_subtraction.py
tests/plugins/test_background_subtraction.py
```

---

## 2. Class Hierarchy

```python
import cv2
import numpy as np
from typing import Tuple
from vjlive3.plugins.base import Effect
from OpenGL.GL import (glActiveTexture, glBindTexture, glDeleteTextures, GL_TEXTURE0, GL_TEXTURE_2D)

class BackgroundSubtractionEffect(Effect):
    """Background subtraction using OpenCV MOG2 for silhouette/ghosting effects."""

    def __init__(self):
        # Initialize OpenCV subtractor
        # Initialize parameters
        # Initialize mask texture
        pass

    def pre_process(self, chain, input_texture: int):
        """Compute background subtraction mask using OpenCV."""
        # Read back texture (downscaled)
        # Apply MOG2
        # Optional Gaussian blur
        # Upload mask texture
        # Report to budget allocator
        pass

    def apply_uniforms(self, time: float, resolution: Tuple[int, int],
                       audio_reactor=None, semantic_layer=None):
        """Bind mask texture and set uniforms."""
        pass

    def delete(self):
        """Clean up OpenGL texture and OpenCV resources."""
        pass
```

---

## 3. Parameters (0.0-10.0)

| Parameter Name | Type | Range | Default | Description |
|----------------|------|-------|---------|-------------|
| `threshold` | float | 0.0-10.0 | 5.0 | Foreground threshold (mapped to 0.0-1.0) |
| `blur` | float | 0.0-10.0 | 0.0 | Gaussian blur kernel size (0=no blur, value used directly as kernel scale) |
| `opacity` | float | 0.0-10.0 | 10.0 | Effect opacity (mapped to 0.0-1.0) |
| `effectMode` | float | 0.0-10.0 | 0.0 | Effect mode: 0=silhouette, 1=ghosting, 2=foreground isolation (derived from slider) |
| `silhouetteColor` | vec3 | (0.0-10.0, 0.0-10.0, 0.0-10.0) | (10.0, 10.0, 10.0) | Silhouette color (white) in 0-10 range |

**Note**: `effectMode` is derived from the slider value: `int(value / 10.0 * 2.0)` clamped to [0, 2].

---

## 4. GLSL Fragment Shader (63 lines)

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex0;        // Video input
uniform sampler2D texMask;     // Background subtraction mask (R = foreground prob)
uniform vec2 resolution;
uniform float u_mix;
uniform float threshold;       // 0-10 slider, remapped to 0-1
uniform float blur;            // 0-10 slider, used directly (kernel size calc in Python)
uniform vec3 silhouetteColor;  // 0-10 per channel, remapped to 0-1
uniform float opacity;         // 0-10 slider, remapped to 0-1
uniform int effectMode;        // 0=silhouette, 1=ghosting, 2=foreground isolation

void main() {
    vec4 video = texture(tex0, uv);
    float t = threshold / 10.0;     // 0-1
    float op = opacity / 10.0;      // 0-1
    vec3 sc = silhouetteColor / 10.0; // 0-1

    // Sample mask (red channel contains foreground probability)
    float mask = texture(texMask, uv).r;

    // Apply threshold
    float foreground = step(t, mask);

    vec3 color = video.rgb;

    if (effectMode == 0) {
        // Silhouette mode: replace background with silhouette color, keep foreground video
        vec3 silhouette = sc * foreground;
        vec3 background = video.rgb * (1.0 - foreground);
        color = mix(video.rgb, silhouette + background, op * u_mix);

    } else if (effectMode == 1) {
        // Ghosting mode: overlay silhouette color on top with alpha
        float alpha = foreground * op * u_mix;
        color = mix(video.rgb, sc, alpha);

    } else if (effectMode == 2) {
        // Foreground isolation: darken background, keep foreground bright
        color = mix(video.rgb, video.rgb * foreground, op * u_mix);
    }

    fragColor = vec4(color, video.a);
}
```

---

## 5. CPU Processing Pipeline

### OpenCV MOG2 Background Subtractor

```python
self.subtractor = cv2.createBackgroundSubtractorMOG2(
    history=100,        # Number of frames for background model
    varThreshold=16,    # Default threshold (we override with our own)
    detectShadows=True  # Detect shadows (mask value 127)
)
```

### pre_process() Workflow

1. **Frame Budget Check**:
   - Register with `chain.frame_budget` if available
   - Skip processing if budget exceeded and cached mask exists
   - Fallback to simple counter (every 3rd frame) if no budget

2. **Adaptive LOD Scaling**:
   - Get `lod_scale` from budget allocator (default 0.25)
   - Downscale input texture to reduce CPU processing load

3. **Texture Readback**:
   - `chain.readback_texture_downscaled(input_texture, scale=lod_scale)`
   - Returns NumPy array (H×W×3 or H×W) in BGR or grayscale

4. **MOG2 Apply**:
   - `fg_mask = self.subtractor.apply(current_frame)`
   - Returns 8-bit mask: 0=background, 255=foreground, 127=shadow

5. **Mask Conversion**:
   - Convert to float32: `fg_mask.astype(np.float32) / 255.0`
   - Result: 0.0-1.0 foreground probability

6. **Optional Blur**:
   - If `blur > 0`: `kernel_size = int(blur * 2) | 1` (ensure odd)
   - `cv2.GaussianBlur(mask_float, (kernel_size, kernel_size), 0)`

7. **Texture Upload**:
   - Create 2-channel float texture (H×W×2) if not exists
   - Upload with `chain.update_float_texture()` or `chain.upload_float_texture()`
   - Red channel = mask, Green channel unused

8. **Budget Reporting**:
   - Record processing duration to budget allocator
   - Helps adaptive throttling

---

## 6. Effect Modes

### Mode 0: Silhouette
- Replaces background with solid `silhouetteColor`
- Keeps foreground video pixels intact
- Creates cut-out silhouette effect

### Mode 1: Ghosting
- Overlays `silhouetteColor` on top of video with alpha
- Foreground areas tinted with silhouette color
- Creates ghost/phantom effect

### Mode 2: Foreground Isolation
- Multiplies video by foreground mask
- Background becomes black, foreground remains
- High-contrast isolation effect

---

## 7. Frame Budget Integration

The effect integrates with the **Frame Budget Allocator** to maintain 60 FPS:

```python
budget = getattr(chain, 'frame_budget', None)
if budget is not None:
    budget.register(self.name)
    if budget.should_skip(self.name) and self.mask_texture is not None:
        return None  # Skip processing, reuse last mask
```

- **Registration**: Effect registers itself with the budget system
- **Skip Decision**: Budget system decides if this frame should be processed based on time budget
- **Cached Mask**: If skipped, reuses previous mask texture (stale but better than dropping)
- **LOD Scaling**: Budget provides `get_lod_scale(self.name)` for adaptive resolution

**Fallback**: If no budget system, uses simple counter `% 3` to process every 3rd frame.

---

## 8. Texture Management

- **Mask Texture**: 2-channel float texture (GL_RG32F or similar)
- **Format**: H×W×2, Red channel = foreground probability, Green unused
- **Lifetime**: Created on first `pre_process`, reused with `glTexSubImage2D` updates
- **Cleanup**: Deleted in `delete()` method with `glDeleteTextures`

---

## 9. Presets (5 Minimum)

1. **`silhouette_default`**: threshold=5.0 (0.5), blur=0.0, opacity=10.0 (1.0), effectMode=0, silhouetteColor=(10,10,10) white
2. **`silhouette_soft`**: threshold=3.0 (0.3), blur=5.0 (kernel 10), opacity=8.0 (0.8), effectMode=0
3. **`ghost_subtle`**: threshold=6.0 (0.6), blur=0.0, opacity=3.0 (0.3), effectMode=1, silhouetteColor=(10,0,0) red
4. **`ghost_aggressive`**: threshold=4.0 (0.4), blur=0.0, opacity=10.0 (1.0), effectMode=1, silhouetteColor=(0,10,0) green
5. **`foreground_iso`**: threshold=5.0 (0.5), blur=2.0 (kernel 4), opacity=9.0 (0.9), effectMode=2

---

## 10. Unit Tests (≥ 80% coverage)

**Test File**: `tests/plugins/test_background_subtraction.py`

### Critical Tests:

1. **Parameter validation**:
   - All parameters accept valid 0.0-10.0 values
   - `effectMode` derived correctly: `int(value/10*2)` clamped to 0-2
   - `silhouetteColor` components clamped to 0-10

2. **OpenCV integration**:
   - MOG2 subtractor created successfully
   - `subtractor.apply(frame)` returns valid mask (0, 127, 255)
   - History and shadow detection configured

3. **Mask processing**:
   - Mask normalized to 0.0-1.0 correctly
   - Blur kernel size calculation: `int(blur*2)|1` yields odd number
   - Gaussian blur applied when blur > 0

4. **Texture management**:
   - Mask texture created with correct format (2-channel float)
   - Texture updates with `glTexSubImage2D`
   - Texture deleted in `delete()`

5. **Shader uniforms**:
   - All 8 uniforms set correctly (threshold, blur, opacity, silhouetteColor, effectMode, texMask)
   - `silhouetteColor` passed as 3-component vector
   - `texMask` bound to texture unit 1

6. **Effect mode rendering**:
   - Mode 0 (silhouette): background replaced with silhouetteColor, foreground preserved
   - Mode 1 (ghosting): silhouette color alpha-blended over video
   - Mode 2 (foreground): background darkened, foreground preserved

7. **Threshold application**:
   - `foreground = step(threshold/10.0, mask)` correct
   - Mask values below threshold become 0, above become 1

8. **Frame budget integration**:
   - Budget registration called when budget present
   - Skip logic respects cached mask
   - LOD scale retrieved from budget

9. **Edge cases**:
   - Zero threshold → all pixels foreground
   - Max threshold (10 → 1.0) → no pixels foreground
   - Zero opacity → no effect applied
   - Missing mask texture → no effect (safe)

---

## 11. Performance Tests

- **CPU Processing**: MOG2 on 320×240 (LOD 0.25) < 10ms on modern CPU
- **Texture Upload**: < 2ms for 1080p mask
- **Shader Compile**: < 15ms
- **FPS Impact**: < 10% with budget throttling (target 60 FPS)

---

## 12. Visual Regression Tests

Capture reference frames with:
- Static camera with person entering/exiting
- Moving camera with static background
- Low light conditions
- Rapid lighting changes
- All 3 effect modes
- Various threshold/blur settings

---

## 13. Implementation Phases

### Phase 1: Foundation (Day 1)
- Create plugin file with class skeleton
- Implement parameter definitions (5 parameters)
- Implement fragment shader (63 lines)
- Basic `apply_uniforms` and `delete` methods

### Phase 2: CPU Processing (Day 2)
- Initialize OpenCV MOG2 subtractor
- Implement `pre_process` with texture readback
- Implement mask conversion and blur
- Implement texture upload
- Integrate frame budget allocator

### Phase 3: Testing & Validation (Day 3)
- Write unit tests (target 85% coverage)
- Performance testing with various LOD scales
- Visual regression captures
- Safety rails verification

---

## 🔒 Safety Rails Compliance

| Rail | Compliance Strategy |
|------|---------------------|
| **60 FPS Sacred** | Frame budget allocator + adaptive LOD downscaling ensures CPU processing stays within budget |
| **Offline-First** | No network calls; OpenCV is local library |
| **Plugin Integrity** | `METADATA` constant with name, version, description, author, license |
| **750-Line Limit** | Expected ~250 lines total (well under limit) |
| **80% Test Coverage** | Unit tests targeting 85%+ (parameters, mask processing, texture management) |
| **No Silent Failures** | OpenCV errors raise exceptions; texture creation failures logged |
| **Resource Leak Prevention** | `delete()` method cleans up GL texture; MOG2 has no explicit cleanup |
| **Backward Compatibility** | New plugin, no compatibility concerns |
| **Security** | No user input in shader strings; all uniforms validated |

---

## 🎨 Legacy Reference Analysis

**Source File**: `/home/happy/Desktop/claude projects/VJlive-2/plugins/core/background_subtraction/__init__.py` (204 lines)

**Key Implementation Details**:
- Class: `BackgroundSubtractionEffect(Effect)`
- Parameters: `threshold` (0-10 → 0-1), `blur` (0-10 direct), `opacity` (0-10 → 0-1), `effectMode` (derived), `silhouetteColor` (0-10 per channel)
- Fragment shader: 63 lines (lines 17-64)
- OpenCV MOG2: `history=100`, `varThreshold=16`, `detectShadows=True`
- Frame budget: `chain.frame_budget` with `register()`, `should_skip()`, `get_lod_scale()`, `record_duration()`
- Texture readback: `chain.readback_texture_downscaled(input_texture, scale=lod_scale)`
- Mask texture: 2-channel float (RG), red channel = foreground probability
- Blur: `kernel_size = int(blur * 2) | 1` (odd kernel)
- Effect modes: 0=silhouette, 1=ghost, 2=foreground isolation

**Porting Notes**:
- Copy shader verbatim (simple blending logic)
- Preserve parameter mapping formulas exactly
- Frame budget integration is critical for 60 FPS; ensure chain has `frame_budget` attribute
- LOD scaling: default 0.25 (process at 1/4 resolution) when budget present
- Texture format: Use GL_RG32F for 2-channel float; shader samples only `.r`
- MOG2 returns 0/127/255; convert to 0.0-1.0 by dividing by 255.0 (shadows become ~0.5)
- The `blur` parameter is used directly as kernel scale; multiply by 2 and ensure odd
- `silhouetteColor` passed as 0-10 values, shader divides by 10.0

---

## ✅ Acceptance Criteria

1. **Functional**:
   - MOG2 background model learns background correctly
   - Foreground mask updates in real-time
   - All 3 effect modes produce expected visual results
   - Threshold controls sensitivity
   - Blur smooths mask edges
   - Opacity controls blend strength
   - Silhouette color applies correctly

2. **Performance**:
   - CPU processing < 10ms per frame at LOD 0.25 on modern CPU
   - Texture upload < 2ms
   - FPS maintained at 60+ with budget allocator
   - No frame drops when budget configured

3. **Quality**:
   - Clean silhouette edges (no jaggedness) with appropriate blur
   - No mask flickering or instability
   - Background model adapts to lighting changes over time

4. **Testing**:
   - Unit test coverage ≥ 80%
   - All tests pass
   - Visual regression baseline captured

5. **Safety**:
   - All safety rails satisfied
   - No memory leaks (textures deleted)
   - Proper error handling for OpenCV failures
   - Graceful degradation if budget system absent

---

## 🔗 Dependencies

- **Base Class**: `vjlive3.plugins.base.Effect`
- **OpenCV**: `cv2.createBackgroundSubtractorMOG2`, `cv2.GaussianBlur`
- **NumPy**: For mask array manipulation
- **OpenGL**: `glActiveTexture`, `glBindTexture`, `glDeleteTextures`
- **Chain Interface**: `chain.readback_texture_downscaled()`, `chain.upload_float_texture()`, `chain.update_float_texture()`, `chain.frame_budget` (optional)

---

## 📊 Success Metrics

- FPS: ≥ 60 with budget allocator
- Test Coverage: ≥ 80%
- Lines of Code: ≤ 250
- CPU Time: < 10ms (LOD 0.25)
- Memory: < 20 MB (texture + MOG2 model)

---

## 📝 Notes for Implementation Engineer

1. **Frame Budget**: The budget system is **critical** for performance. If `chain.frame_budget` is None, use fallback counter (every 3rd frame). But ideally the chain always provides a budget in production.
2. **LOD Scaling**: The default LOD scale is 0.25 (quarter resolution). This reduces CPU load by 4× with minimal quality loss after upscaling in shader (bilinear filtering).
3. **MOG2 Parameters**: `history=100` means background model retains 100 frames. `detectShadows=True` marks shadows as 127 (0.5). We treat all non-255 as background after thresholding.
4. **Mask Normalization**: Divide by 255.0 to get 0.0-1.0 range. Shadows become 0.5, which may be above or below threshold depending on `threshold` value.
5. **Blur**: Applied in Python on CPU before upload. Kernel size = `int(blur * 2) | 1`. If blur=0, skip blur.
6. **Texture Format**: Use `GL_RG32F` for 2-channel float. Upload with `glTexImage2D` or `glTexSubImage2D`. Shader samples red channel only.
7. **Silhouette Color**: Passed as 0-10 values, shader divides by 10.0 to get 0-1 range. Default white = (10,10,10) → (1,1,1).
8. **Effect Mode**: Derived from slider: `int(value / 10.0 * 2.0)`. Slider 0-10 maps to modes 0, 1, 2.
9. **Budget Reporting**: Call `budget.record_duration(self.name, duration_ms)` after processing to help future budget decisions.
10. **Testing**: Mock `chain` with methods `readback_texture_downscaled`, `upload_float_texture`, `update_float_texture`. Use synthetic video frames (solid colors, moving shapes) to test mask generation.

---

**Ready for Implementation after Approval**
