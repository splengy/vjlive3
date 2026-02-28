# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-VD74_ML_Depth_Estimation_Effect.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD74 — MLDepthEstimationEffect

## Description

The MLDepthEstimationEffect performs monocular depth estimation using machine learning models to generate depth maps from single RGB images. It implements a three-tier fallback strategy for maximum reliability: MiDaS deep learning model (best quality), WebcamDepthEstimator CPU fallback (decent quality), and a GPU shader heuristic (fast, approximate). This effect is essential for converting standard video into depth maps that can drive other depth-based effects.

This effect is ideal for VJ performances that need real-time depth estimation without requiring a dedicated depth camera. It enables depth-based effects on any video source, making it a powerful tool for creating 3D-like visuals from 2D content.

## What This Module Does

- Estimates depth from single RGB image using ML models
- Supports three-tier fallback: MiDaS (GPU), WebcamDepthEstimator (CPU), shader heuristic (GPU)
- Provides temporal smoothing for stable depth maps
- Configurable depth scale and focus distance
- Outputs depth as grayscale or colored depth map
- Optional depth-of-field effect
- Asynchronous model loading for responsive startup

## What This Module Does NOT Do

- Does NOT provide real-time depth at 60+ fps on high resolution (ML is slow)
- Does NOT work without PyTorch for full ML functionality (fallback available)
- Does NOT produce accurate metric depth (relative depth only)
- Does NOT support multiple ML models simultaneously
- Does NOT include training capabilities (inference only)
- Does NOT store persistent state across sessions

---

## Detailed Behavior

### Depth Estimation Pipeline

1. **Input frame**: RGB image (HxWxC, 0-255)
2. **Model selection**: Choose MiDaS variant (small/large/hybrid) or fallback
3. **Preprocessing**: Resize and normalize for model input
4. **Inference**: Run ML model or fallback algorithm
5. **Post-processing**: Resize to output resolution, apply temporal smoothing
6. **Output**: Depth map (HxW, normalized 0-1) or colored depth

### Three-Tier Fallback Strategy

The effect prioritizes quality but ensures functionality even without ML dependencies:

**Tier 1: MiDaS Deep Learning Model (Best Quality)**
- Uses PyTorch and MiDaS model (DPT_Hybrid, DPT_Large, or MiDaS_small)
- Requires `torch` and `torchvision` packages
- Produces high-quality, accurate depth maps
- Slow on CPU, fast on GPU (CUDA)
- Model loaded asynchronously to avoid blocking

**Tier 2: WebcamDepthEstimator CPU Fallback (Decent Quality)**
- Pure Python/NumPy implementation
- Uses structure-from-motion, feature matching, and optical flow
- Works without PyTorch
- Moderate quality, slower than GPU but faster than full ML on CPU
- Good compromise when ML unavailable

**Tier 3: GPU Shader Heuristic (Fast, Approximate)**
- Simple GLSL shader using color-based heuristics
- Assumes warmer colors are closer, cooler colors are farther
- Uses luminance as additional depth cue
- Very fast (real-time), but low quality
- Always available as fallback

### Depth Estimation Algorithms

#### MiDaS (Mixed Depth and Attention for Stereo)

MiDaS is a state-of-the-art monocular depth estimation model. The effect supports three variants:

- **MiDaS_small**: Fast, lower quality, suitable for real-time
- **DPT_Large**: High quality, slower, best for offline
- **DPT_Hybrid**: Balanced quality and speed

The model takes a RGB image, processes it through a transformer-based network, and outputs a relative depth map. Depth values are normalized to 0-1.

#### WebcamDepthEstimator

This CPU fallback uses classical computer vision techniques:

1. **Feature detection**: ORB or SIFT features
2. **Feature matching**: Between consecutive frames
3. **Motion estimation**: From matched features
4. **Depth from motion**: Using camera motion assumptions
5. **Smoothing**: Temporal and spatial filtering

It assumes a moving camera or scene to estimate depth from parallax.

#### Shader Heuristic

The fallback shader uses simple color heuristics:

```glsl
float lum = dot(col.rgb, vec3(0.299, 0.587, 0.114));
float warmth = (col.r - col.b) * 0.5 + 0.5;
float depth = lum * 0.7 + warmth * 0.3;
depth = 1.0 - depth;  // Invert: brighter = closer
```

This assumes:
- Brighter areas are closer (luminance cue)
- Warmer colors (red/yellow) are closer, cooler colors (blue) are farther (color temperature cue)

### Temporal Smoothing

To reduce depth flickering, temporal smoothing is applied:

```python
if self._prev_depth is not None:
    smoothing = self.parameters['temporal_smoothing'] / 10.0
    depth = prev_depth * smoothing + depth * (1.0 - smoothing)
self._prev_depth = depth
```

Higher smoothing = more stable but slower to respond to real depth changes.

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `depth_scale` | float | 5.0 | 0.0-10.0 | Scale factor for depth values (0-10 → 0.0-5.0) |
| `focus_distance` | float | 5.0 | 0.0-10.0 | Focus distance for depth-of-field effect (0-10 → 0.0-1.0) |
| `temporal_smoothing` | float | 7.0 | 0.0-10.0 | Smoothing factor (0=no smoothing, 10=heavy) |
| `model_variant` | str | 'small' | 'small', 'large', 'hybrid' | MiDaS model variant (internal) |
| `output_mode` | str | 'grayscale' | 'grayscale', 'colored', 'depth_of_field' | Output format (internal) |

**Inherited from Effect**: `u_mix`

---

## Public Interface

```python
class MLDepthEstimationEffect(MLBaseAsyncEffect):
    def __init__(self) -> None: ...
    def set_model_variant(self, variant: str) -> None: ...
    def set_output_mode(self, mode: str) -> None: ...
    def set_parameter(self, name: str, value: float) -> None: ...
    def get_parameter(self, name: str) -> float: ...
    def apply_uniforms(self, time: float, resolution: Tuple[int, int], audio_reactor=None) -> None: ...
    def process_frame(self, frame: np.ndarray) -> np.ndarray: ...
    def cleanup(self) -> None: ...
    def is_model_loaded(self) -> bool: ...
    def load_model(self) -> None: ...  # Async
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `frame` | `np.ndarray` | Input RGB frame (HxWxC, 0-255) |
| **Output** | `np.ndarray` | Depth map (HxW, normalized 0-1) or colored depth (HxWxC) |

---

## State Management

**Persistent State:**
- `_midas_model: Optional[torch.nn.Module]` — Loaded MiDaS model
- `_midas_transform: Optional[torchvision.transforms]` — Preprocessing transform
- `_depth_estimator: Optional[WebcamDepthEstimator]` — CPU fallback estimator
- `_prev_depth: Optional[np.ndarray]` — Previous depth for temporal smoothing
- `_parameters: dict` — Effect parameters
- `_shader: ShaderProgram` — Fallback shader
- `_output_mode: str` — Output format
- `_model_variant: str` — Selected MiDaS variant
- `_model_loaded: bool` — Model loading status

**Per-Frame:**
- Check if ML model loaded; if not, use fallback
- Preprocess frame (resize, normalize)
- Run inference (ML or fallback)
- Post-process depth (resize, scale)
- Apply temporal smoothing
- Convert to output format (grayscale/colored/DoF)
- Return depth map

**Initialization:**
- Compile fallback shader
- Initialize parameters: `depth_scale=5.0`, `focus_distance=5.0`, `temporal_smoothing=7.0`
- Set `_model_loaded = False`
- Start async model loading (if torch available)
- Initialize `_prev_depth = None`

**Cleanup:**
- Delete shader
- Free ML model (if loaded)
- Call `super().cleanup()`

---

## GPU Resources

| Resource | Type | Format | Dimensions | Lifecycle |
|----------|------|--------|------------|-----------|
| Shader program | GLSL | vertex + fragment | N/A | Init once (fallback) |
| Output texture (optional) | GL_TEXTURE_2D | GL_RGBA8 | frame size | For colored output |

**Memory Budget (640×480):**
- Shader: ~30-40 KB
- Output texture: ~1.2 MB (if colored output)
- Total: ~1.3 MB (light)

**ML Model Memory:**
- MiDaS_small: ~50-100 MB (GPU RAM)
- MiDaS_large: ~200-300 MB (GPU RAM)
- MiDaS_hybrid: ~100-150 MB (GPU RAM)

---

## Error Cases

| Error Condition | Response | Recovery |
|-----------------|----------|----------|
| PyTorch not available | Use WebcamDepthEstimator fallback | Normal operation |
| MiDaS model load fails | Use WebcamDepthEstimator fallback | Log error, continue |
| WebcamDepthEstimator fails | Use shader fallback | Normal operation |
| Out of GPU memory | Use CPU inference or fallback | Reduce resolution |
| Invalid model variant | Clamp to valid variants | Use 'small' as default |
| Invalid output mode | Clamp to valid modes | Use 'grayscale' as default |
| Frame too large | Resize to model input size | Automatic resize |

---

## Thread Safety

The effect is **not thread-safe**. Model loading is asynchronous but inference must occur on the thread with the OpenGL context (for fallback shader). The effect updates state each frame (temporal smoothing); concurrent `process_frame()` calls will cause race conditions. Use one instance per thread or protect with a mutex.

---

## Performance

**Expected Frame Time (640×480):**
- MiDaS_small (GPU): ~50-100 ms (10-20 fps)
- MiDaS_small (CPU): ~500-1000 ms (1-2 fps)
- WebcamDepthEstimator (CPU): ~100-200 ms (5-10 fps)
- Shader fallback (GPU): ~2-5 ms (200+ fps)

**Optimization Strategies:**
- Use smaller model variant (small vs large)
- Reduce input resolution (model scales internally)
- Use shader fallback for real-time requirements
- Increase temporal smoothing to reduce inference frequency
- Use GPU for ML inference (CUDA)

---

## Integration Checklist

- [ ] PyTorch installed for ML functionality (optional)
- [ ] MiDaS model downloaded (auto-download on first use)
- [ ] Model variant selected
- [ ] Output mode configured
- [ ] Depth scale and focus distance set
- [ ] Temporal smoothing configured
- [ ] `process_frame()` called each frame
- [ ] `cleanup()` called on shutdown

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init` | Effect initializes with default parameters |
| `test_set_parameter` | All parameters can be set and clamped |
| `test_get_parameter` | All parameters can be retrieved |
| `test_model_loading` | MiDaS model loads asynchronously |
| `test_fallback_chain` | Falls back through tiers correctly |
| `test_shader_fallback` | Shader heuristic produces depth map |
| `test_depth_scale` | Depth scale affects output range |
| `test_temporal_smoothing` | Smoothing reduces flickering |
| `test_output_modes` | Grayscale, colored, DoF outputs work |
| `test_model_variant` | Different model variants load |
| `test_cleanup` | All resources released |
| `test_no_memory_leak` | Repeated init/cleanup cycles don't leak |

**Minimum coverage:** 85%

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint checked
- [ ] Git commit with `[Phase-3] P3-VD74: ml_depth_estimation_effect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Legacy Code Mapping

Key references:
- `plugins/vml/ml_gpu_effects.py` — VJLive Original implementation
- `plugins/core/ml_vision/ml_effects.py` — VJLive-2 implementation
- `core/effects/ml_effects.py` — Base class `MLBaseAsyncEffect`
- `plugins/vml/ml_gpu_effects.py` — Contains `DEPTH_ESTIMATION_FALLBACK` shader

Design decisions inherited:
- Effect name: `ml_depth_estimation`
- Inherits from `MLBaseAsyncEffect` (async model loading)
- Three-tier fallback: MiDaS → WebcamDepthEstimator → shader
- Parameters: `depth_scale`, `focus_distance`, `temporal_smoothing`
- Internal state: `_output_mode`, `_model_variant`, `_midas_model`, `_depth_estimator`, `_prev_depth`
- Method `_load_ml_plugin()` attempts to load ML dependencies
- Shader fallback uses luminance + color temperature heuristic
- Presets: "fast", "quality", "balanced", "colored", "dof"

---

## Notes for Implementers

1. **Core Concept**: This effect estimates depth from a single RGB image using machine learning. It's a critical component for enabling depth-based effects on any video source without requiring a depth camera.

2. **Fallback Strategy**: The effect must work in all environments:
   - **Best**: MiDaS model with PyTorch (GPU preferred)
   - **Good**: WebcamDepthEstimator (CPU, no PyTorch)
   - **Basic**: Shader heuristic (GPU, always works)

3. **Asynchronous Loading**: MiDaS model is large (~100+ MB) and takes time to load. The effect should start with fallback and switch to ML when ready. Use a background thread for loading.

4. **MiDaS Integration**:
   - Download model from torch.hub: `torch.hub.load("intel-isl/MiDaS", model_name)`
   - Use appropriate transform: `MiDaS_transform` for input preprocessing
   - Run inference: `model(input_tensor)`
   - Normalize output to 0-1

5. **WebcamDepthEstimator**:
   - Pure Python implementation using OpenCV/NumPy
   - Tracks features between frames
   - Estimates depth from motion parallax
   - Slower but works without ML dependencies

6. **Shader Fallback**:
   - Very fast, real-time
   - Low quality, but better than nothing
   - Uses color heuristics: luminance + warmth
   - Always available as last resort

7. **Temporal Smoothing**: Essential for stable depth maps. ML models can flicker; smoothing reduces this.

8. **Parameters**:
   - `depth_scale`: Multiplies depth values (useful for tuning effect strength)
   - `focus_distance`: For depth-of-field output mode (controls blur amount)
   - `temporal_smoothing`: 0-1 blend with previous depth

9. **Output Modes**:
   - `grayscale`: Single-channel depth map (0-1)
   - `colored`: False-color depth visualization (jet colormap)
   - `depth_of_field`: Blurred image based on depth (requires original frame)

10. **Shader Uniforms** (fallback):
    ```glsl
    uniform sampler2D tex0;       // Input frame
    uniform float u_depth_scale;  // Depth multiplier
    uniform float u_focus_distance; // DoF focus point
    ```

11. **PRESETS**:
    ```python
    PRESETS = {
        "fast": {
            "depth_scale": 3.0, "temporal_smoothing": 5.0, "model_variant": "small",
            "output_mode": "grayscale",
        },
        "quality": {
            "depth_scale": 5.0, "temporal_smoothing": 8.0, "model_variant": "large",
            "output_mode": "colored",
        },
        "balanced": {
            "depth_scale": 4.0, "temporal_smoothing": 7.0, "model_variant": "hybrid",
            "output_mode": "grayscale",
        },
        "colored": {
            "depth_scale": 5.0, "temporal_smoothing": 6.0, "model_variant": "small",
            "output_mode": "colored",
        },
        "dof": {
            "depth_scale": 5.0, "temporal_smoothing": 7.0, "model_variant": "hybrid",
            "output_mode": "depth_of_field", "focus_distance": 0.5,
        },
    }
    ```

12. **Testing Strategy**:
    - Test with known images (checkerboard, gradients)
    - Verify fallback chain works when ML unavailable
    - Test temporal smoothing: depth should be stable
    - Test output modes: grayscale, colored, DoF
    - Test model loading: async, errors handled
    - Test parameter changes: depth_scale, focus_distance, smoothing

13. **Performance**: ML inference is slow. Use small model for real-time, large for offline. Shader fallback is instant.

14. **Memory**: ML models are large (50-300 MB). Consider lazy loading.

15. **Debug Mode**: Visualize depth map, show model loading status, fallback indicator.

---

## Easter Egg Idea

When `depth_scale` is set exactly to 6.66, `temporal_smoothing` to exactly 6.66, `focus_distance` to exactly 0.666, and `model_variant` is set to "hybrid", the ML depth estimation enters a "sacred depth" state where the MiDaS model produces exactly 666 layers of depth segmentation, each layer separated by exactly 6.66 depth units, the temporal smoothing creates exactly 666 frames of persistence, the focus distance creates exactly 666 distinct bokeh circles, and the entire depth map encodes the number 666 in both spatial and temporal dimensions. The fallback shader, if activated, produces exactly 666 distinct color bands in the depth colormap, and the WebcamDepthEstimator finds exactly 666 feature points per frame. The effect becomes a "depth prayer" where every pixel's depth is exactly 666% more profound than normal.

---

## References

- MiDaS: https://github.com/isl-org/MiDaS
- Monocular depth estimation: https://en.wikipedia.org/wiki/Depth_perception#Monocular_cues
- Temporal smoothing: https://en.wikipedia.org/wiki/Temporal_filtering
- WebcamDepthEstimator: Classical structure-from-motion techniques
- VJLive legacy: `plugins/vml/ml_gpu_effects.py`

---

## Implementation Tips

1. **Full Shader (Fallback)**:
   ```glsl
   #version 330 core
   in vec2 uv;
   out vec4 fragColor;
   
   uniform sampler2D tex0;
   uniform float u_depth_scale;
   uniform float u_focus_distance;
   
   void main() {
       vec4 col = texture(tex0, uv);
       
       // Use luminance and color temperature as depth proxy
       float lum = dot(col.rgb, vec3(0.299, 0.587, 0.114));
       
       // Warmer colors tend to be closer, cooler colors farther
       float warmth = (col.r - col.b) * 0.5 + 0.5;
       
       // Combine cues (invert: brighter/warmer = closer)
       float depth = 1.0 - (lum * 0.7 + warmth * 0.3);
       
       // Apply depth scale
       depth = depth * u_depth_scale;
       depth = clamp(depth, 0.0, 1.0);
       
       // Output grayscale depth
       fragColor = vec4(depth, depth, depth, 1.0);
   }
   ```

2. **Python Implementation**:
   ```python
   class MLDepthEstimationEffect(MLBaseAsyncEffect):
       def __init__(self):
           super().__init__("ml_depth_estimation", DEPTH_ESTIMATION_FALLBACK)
           
           self.parameters = {
               'depth_scale': 5.0,
               'focus_distance': 5.0,
               'temporal_smoothing': 7.0,
           }
           
           self._output_mode = 'grayscale'
           self._model_variant = 'small'
           self._midas_model = None
           self._midas_transform = None
           self._depth_estimator = None
           self._prev_depth = None
           
           # Start async model loading
           self._model_loaded = False
           self._load_model_async()
       
       def _load_model_async(self):
           """Load MiDaS model in background thread."""
           def load():
               try:
                   import torch
                   import torch.hub
                   
                   model_type = self.MIDAS_MODELS[self._model_variant]
                   model = torch.hub.load("intel-isl/MiDaS", model_type)
                   transform = torch.hub.load("intel-isl/MiDaS", "transforms")
                   
                   self._midas_model = model
                   self._midas_transform = transform
                   self._model_loaded = True
               except ImportError:
                   # PyTorch not available, try CPU fallback
                   self._load_cpu_fallback()
               except Exception as e:
                   logger.error(f"MiDaS load failed: {e}")
                   self._load_cpu_fallback()
           
           thread = threading.Thread(target=load, daemon=True)
           thread.start()
       
       def _load_cpu_fallback(self):
           """Load WebcamDepthEstimator as fallback."""
           try:
               from some_module import WebcamDepthEstimator
               self._depth_estimator = WebcamDepthEstimator()
               self._model_loaded = True
           except ImportError:
               # No fallback available, will use shader
               pass
       
       def process_frame(self, frame):
           h, w = frame.shape[:2]
           
           if self._model_loaded and self._midas_model:
               # Use MiDaS
               depth = self._run_midas(frame)
           elif self._depth_estimator:
               # Use CPU fallback
               depth = self._run_cpu_fallback(frame)
           else:
               # Use shader fallback
               depth = self._run_shader_fallback(frame)
           
           # Temporal smoothing
           if self._prev_depth is not None:
               smoothing = self.parameters['temporal_smoothing'] / 10.0
               depth = self._prev_depth * smoothing + depth * (1.0 - smoothing)
           
           self._prev_depth = depth
           
           # Apply depth scale
           depth = depth * (self.parameters['depth_scale'] / 5.0)
           depth = np.clip(depth, 0.0, 1.0)
           
           # Convert to output mode
           if self._output_mode == 'grayscale':
               return (depth * 255).astype(np.uint8)
           elif self._output_mode == 'colored':
               return self._apply_colormap(depth)
           elif self._output_mode == 'depth_of_field':
               return self._apply_dof(frame, depth)
           
           return (depth * 255).astype(np.uint8)
       
       def _run_midas(self, frame):
           """Run MiDaS inference."""
           # Preprocess
           input_batch = self._midas_transform(frame).unsqueeze(0)
           
           # Inference
           with torch.no_grad():
               prediction = self._midas_model(input_batch)
               prediction = torch.nn.functional.interpolate(
                   prediction.unsqueeze(1),
                   size=frame.shape[:2],
                   mode="bicubic",
                   align_corners=False,
               ).squeeze()
           
           depth = prediction.cpu().numpy()
           depth = (depth - depth.min()) / (depth.max() - depth.min())
           return depth
       
       def _run_cpu_fallback(self, frame):
           """Run WebcamDepthEstimator."""
           return self._depth_estimator.estimate_depth(frame)
       
       def _run_shader_fallback(self, frame):
           """Run shader fallback."""
           # Upload frame, run shader, read back
           # ... (standard shader execution)
           pass
       
       def _apply_colormap(self, depth):
           """Apply false-color colormap to depth."""
           # Use matplotlib or custom colormap
           pass
       
       def _apply_dof(self, frame, depth):
           """Apply depth-of-field blur."""
           # Use depth as blur mask
           pass
   ```

3. **MiDaS Integration**: Use torch.hub to load model. Handle CUDA/CPU automatically. Normalize output to 0-1.

4. **WebcamDepthEstimator**: If available, use as good fallback. It's a classical CV algorithm that works without ML.

5. **Shader Fallback**: Always available. Fast but low quality. Use as last resort.

6. **Temporal Smoothing**: Critical for stable output. Use exponential smoothing: `new = old * alpha + current * (1-alpha)`.

7. **Performance**: ML is slow. Consider:
   - Running inference every N frames
   - Using smaller model
   - Lowering resolution
   - Using GPU (CUDA)

8. **Testing**: Test with various scenes: close/far objects, textures, lighting. Verify fallback chain.

9. **Future Extensions**:
   - Add more ML models (DPT, AdaBins, etc.)
   - Add confidence map output
   - Add metric depth scaling
   - Add multi-scale depth fusion

---

## Conclusion

The MLDepthEstimationEffect brings powerful monocular depth estimation to VJLive, enabling depth-based effects on any video source. With its three-tier fallback strategy (MiDaS ML, CPU fallback, shader heuristic), it ensures reliable operation across diverse environments while providing the best possible quality given available resources. Whether using state-of-the-art deep learning or fast GPU heuristics, this effect makes depth accessible to all VJ performances.

---
>>>>>>> REPLACE