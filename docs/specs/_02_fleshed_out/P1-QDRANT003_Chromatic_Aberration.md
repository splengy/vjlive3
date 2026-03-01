# P1-QDRANT003 — Chromatic Aberration Effect

**What This Module Does**
The Chromatic Aberration effect simulates realistic lens distortion by separating color channels based on optical physics principles. It models the wavelength-dependent refraction of light through lens elements, creating authentic color fringing at high-contrast edges. The effect supports configurable aberration intensity, radial falloff, and wavelength-specific dispersion curves. It operates in real-time using GPU-accelerated shader computations, making it suitable for live VJ performance scenarios where optical realism enhances visual impact.

**What This Module Does NOT Do**
- Does not perform full ray-tracing or physical lens simulation
- Does not handle multi-pass optical effects like flare or ghosting
- Does not process HDR tone mapping or color grading
- Does not manage camera calibration or lens profiles
- Does not implement depth-of-field or bokeh effects
- Does not handle video capture or encoding

---

## Detailed Behavior

The Chromatic Aberration effect processes images through a multi-stage pipeline:

1. **Channel Separation**: Extract RGB channels into separate texture samples
2. **Radial Displacement**: Calculate displacement vectors based on distance from center
3. **Wavelength Dispersion**: Apply wavelength-specific refraction coefficients
4. **Edge Enhancement**: Amplify aberration at high-contrast edges using Sobel detection
5. **Channel Recombination**: Recombine displaced channels with configurable blending
6. **Artifact Suppression**: Apply optional de-fringing in low-contrast regions
7. **Temporal Smoothing**: Optional frame-to-frame coherence for stable output

Key behavioral characteristics:
- Uses single-pass fragment shader for optimal performance
- Displacement magnitude follows inverse-square law from center
- Chromatic dispersion uses Cauchy's equation for realistic wavelength separation
- Edge detection uses 3×3 Sobel kernel with configurable threshold
- All operations use 32-bit floating point for HDR compatibility

---

## Integration Notes

- **Input**: Accepts any OpenGL texture (2D, RGB/RGBA format)
- **Output**: Single texture with chromatic aberration applied
- **Parameter Control**: All parameters animatable via VJLive3 parameter system
- **Dependencies**: Requires OpenGL 3.3+ for shader support
- **Performance**: ~0.5ms per 1080p frame on modern GPU
- **Memory**: Uses 3× temporary channel buffers (can be optimized to 1× with careful design)

---

## Performance Characteristics

- **Computational Complexity**: O(width × height) per frame
- **Shader Instructions**: ~50-80 ALU operations per pixel
- **Memory Bandwidth**: 4× read (original + 3 channels) + 1× write
- **Target Frame Rates**: 60 FPS minimum at 1080p, 120 FPS at 720p
- **GPU Utilization**: ~15-20% on mid-range GPU (GTX 1060 equivalent)
- **Latency**: Single frame (no multi-pass buffering required)

---

## Public Interface

```python
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

class AberrationModel(Enum):
    """Optical models for chromatic aberration."""
    SIMPLE_RADIAL = "simple_radial"       # Basic radial displacement
    CAUCHY_DISPERSION = "cauchy_dispersion"  # Physics-based wavelength separation
    EMPIRICAL_LENS = "empirical_lens"     # Measured lens profile
    CUSTOM_CURVE = "custom_curve"         # User-defined dispersion function

@dataclass
class ChromaticConfig:
    """Configuration for chromatic aberration effect."""
    intensity: float = 0.5                # Overall aberration strength [0.0, 2.0]
    model: AberrationModel = AberrationModel.CAUCHY_DISPERSION
    radial_falloff: float = 1.0          # Power law for falloff [0.5, 3.0]
    edge_enhancement: float = 0.0        # Extra aberration at edges [0.0, 1.0]
    edge_threshold: float = 0.1          # Contrast threshold for edge detection [0.0, 1.0]
    wavelength_scale: float = 1.0        # Scale factor for wavelength separation [0.1, 3.0]
    de_fringe_strength: float = 0.0      # Anti-fringing in flat areas [0.0, 1.0]
    temporal_smoothing: float = 0.0      # Frame-to-frame coherence [0.0, 1.0]
    custom_curve: Optional[np.ndarray] = None  # Custom dispersion curve (256 values)

@dataclass
class WavelengthCoefficients:
    """Cauchy equation coefficients for wavelength dispersion."""
    red_coeff: float = 0.015             # Red channel displacement coefficient
    green_coeff: float = 0.010           # Green channel (reference)
    blue_coeff: float = 0.005            # Blue channel displacement coefficient
    cauchy_b: float = 1.5                # Cauchy's B constant
    cauchy_c: float = 0.004              # Cauchy's C constant (μm²)

class ChromaticAberration:
    def __init__(self, config: ChromaticConfig) -> None:
        """
        Initialize chromatic aberration effect.
        
        Args:
            config: Effect configuration parameters
            
        Raises:
            InvalidConfigError: If configuration parameters are invalid
            ShaderCompilationError: If shader fails to compile
        """
    
    def apply_aberration(
        self, 
        image: np.ndarray,
        intensity: Optional[float] = None
    ) -> np.ndarray:
        """
        Apply chromatic aberration to input image.
        
        Args:
            image: Input image as numpy array (HxWx3 or HxWx4, float32)
            intensity: Optional override for aberration intensity
            
        Returns:
            Aberrated image with same shape and dtype as input
            
        Raises:
            InvalidImageError: If image format is invalid
            ShaderExecutionError: If shader execution fails
            MemoryError: If insufficient GPU memory
        """
    
    def validate_intensity(self, intensity: float) -> bool:
        """
        Validate aberration intensity parameter.
        
        Args:
            intensity: Intensity value to validate
            
        Returns:
            True if intensity is within valid range [0.0, 2.0]
        """
    
    def generate_aberration_report(self, image_id: str) -> str:
        """
        Generate detailed aberration analysis report.
        
        Args:
            image_id: Identifier for the processed image
            
        Returns:
            Formatted report with statistics and metrics
            
        Raises:
            ReportGenerationError: If report generation fails
        """
    
    def calibrate_color_channels(
        self, 
        color_profile: str,
        target_aberration: float
    ) -> Dict[str, Any]:
        """
        Calibrate channel coefficients for specific color profile.
        
        Args:
            color_profile: Color profile name (e.g., "sRGB", "Rec709")
            target_aberration: Target aberration amount in pixels
            
        Returns:
            Dictionary with calibrated coefficients and validation metrics
            
        Raises:
            CalibrationError: If calibration fails
            UnsupportedProfileError: If color profile is unknown
        """
    
    def set_custom_dispersion_curve(
        self, 
        curve: np.ndarray,
        normalize: bool = True
    ) -> None:
        """
        Set custom wavelength dispersion curve.
        
        Args:
            curve: Array of 256 displacement values (0-255 wavelength index)
            normalize: Whether to normalize curve to [0.0, 1.0] range
            
        Raises:
            InvalidCurveError: If curve format is invalid
        """
    
    def compute_edge_mask(
        self, 
        image: np.ndarray,
        threshold: float = 0.1
    ) -> np.ndarray:
        """
        Compute edge mask for selective aberration application.
        
        Args:
            image: Input image
            threshold: Edge detection threshold [0.0, 1.0]
            
        Returns:
            Edge mask as float32 array (0.0-1.0)
        """
    
    def apply_temporal_smoothing(
        self, 
        current_frame: np.ndarray,
        previous_frame: Optional[np.ndarray],
        smoothing_factor: float
    ) -> np.ndarray:
        """
        Apply temporal smoothing between frames.
        
        Args:
            current_frame: Current aberrated frame
            previous_frame: Previous aberrated frame (or None)
            smoothing_factor: Smoothing amount [0.0, 1.0]
            
        Returns:
            Temporally smoothed frame
        """
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `image` | `np.ndarray` | Input image | Shape (H, W, 3) or (H, W, 4), dtype float32, values [0.0, 1.0] |
| `intensity` | `float` | Aberration strength | [0.0, 2.0], default 0.5 |
| `model` | `AberrationModel` | Optical model | Enum value |
| `radial_falloff` | `float` | Falloff power | [0.5, 3.0], default 1.0 |
| `edge_enhancement` | `float` | Edge amplification | [0.0, 1.0], default 0.0 |
| `edge_threshold` | `float` | Edge detection threshold | [0.0, 1.0], default 0.1 |
| `wavelength_scale` | `float` | Dispersion scale | [0.1, 3.0], default 1.0 |
| `de_fringe_strength` | `float` | Anti-fringing amount | [0.0, 1.0], default 0.0 |
| `temporal_smoothing` | `float` | Temporal coherence | [0.0, 1.0], default 0.0 |
| `custom_curve` | `np.ndarray` | Custom dispersion curve | Shape (256,), values [0.0, 1.0] |
| `red_coeff` | `float` | Red wavelength coefficient | [0.001, 0.1], default 0.015 |
| `green_coeff` | `float` | Green wavelength coefficient | [0.001, 0.1], default 0.010 |
| `blue_coeff` | `float` | Blue wavelength coefficient | [0.001, 0.1], default 0.005 |
| `cauchy_b` | `float` | Cauchy's B constant | [1.0, 3.0], default 1.5 |
| `cauchy_c` | `float` | Cauchy's C constant | [0.0, 0.01], default 0.004 |
| `image_id` | `str` | Image identifier | Non-empty string |

**Data Structures:**

```python
# Configuration structure
ChromaticConfig = {
    'intensity': float,                # [0.0, 2.0]
    'model': AberrationModel,          # Enum
    'radial_falloff': float,           # [0.5, 3.0]
    'edge_enhancement': float,         # [0.0, 1.0]
    'edge_threshold': float,           # [0.0, 1.0]
    'wavelength_scale': float,         # [0.1, 3.0]
    'de_fringe_strength': float,       # [0.0, 1.0]
    'temporal_smoothing': float,       # [0.0, 1.0]
    'custom_curve': Optional[np.ndarray]  # (256,) float32
}

# Wavelength coefficients (Cauchy model)
WavelengthCoefficients = {
    'red_coeff': float,    # [0.001, 0.1]
    'green_coeff': float,  # [0.001, 0.1]
    'blue_coeff': float,   # [0.001, 0.1]
    'cauchy_b': float,     # [1.0, 3.0]
    'cauchy_c': float      # [0.0, 0.01]
}
```

---

## Edge Cases and Error Handling

### Image Format Issues
- **Invalid Shape**: Raise `InvalidImageError` with details about expected shape
- **Wrong Dtype**: Convert float64 to float32 automatically, reject integer types
- **Channel Count**: Support both RGB (3) and RGBA (4), reject other channel counts
- **Value Range**: Clamp values to [0.0, 1.0] with warning if out of range
- **Empty Image**: Raise `InvalidImageError` for zero-sized images

### Parameter Validation
- **Intensity Out of Range**: Clamp to [0.0, 2.0] with warning
- **Invalid Model**: Fall back to CAUCHY_DISPERSION with warning
- **Radial Falloff Extreme**: Clamp to [0.5, 3.0], log warning if adjusted
- **Edge Threshold Invalid**: Clamp to [0.0, 1.0], warn if outside range
- **Custom Curve Wrong Size**: Raise `InvalidCurveError` if not 256 elements
- **Custom Curve NaN/Inf**: Replace with linear curve, log warning

### Shader and GPU Issues
- **Shader Compilation Failure**: Fall back to CPU implementation, log error
- **GPU Memory Exhaustion**: Reduce resolution by half, continue with warning
- **OpenGL Context Lost**: Attempt context recovery, fail gracefully if unavailable
- **Shader Execution Timeout**: Kill hanging shader, use CPU fallback
- **Texture Format Unsupported**: Convert to supported format (RGB8/RGBA8)

### Edge Detection and Artifacts
- **No Edges Detected**: Apply uniform aberration based on intensity
- **Excessive Edges**: Cap edge enhancement to prevent over-amplification
- **Color Bleeding**: Apply de-fringing when `de_fringe_strength > 0`
- **Temporal Inconsistency**: Increase temporal smoothing if frame-to-frame jitter > threshold
- **Aliasing at High Intensity**: Enable optional supersampling when intensity > 1.5

### Performance and Resource Management
- **Large Images**: Downscale images > 4K before processing, upscale after
- **Memory Pressure**: Release temporary buffers after each frame
- **CPU Fallback**: Use numpy-based CPU implementation if GPU unavailable
- **Concurrent Access**: Use per-instance shader programs, thread-safe parameter updates
- **Resource Leaks**: Ensure all OpenGL objects deleted on destruction

### Calibration and Customization
- **Unsupported Color Profile**: Use sRGB fallback coefficients, log warning
- **Calibration Failure**: Return default coefficients with error status
- **Custom Curve Monotonic**: Detect non-monotonic curves, warn and smooth
- **Coefficient Incompatibility**: Adjust coefficients to maintain physical plausibility

---

## Dependencies

- **External Libraries**:
  - `OpenGL` / `GLSL` — shader-based GPU acceleration (fallback: CPU numpy)
  - `numpy` — array operations and image processing (required)
  - `PIL.Image` — image loading and format conversion (optional)
  - `pyopengl` — OpenGL bindings (fallback: context manager)
  - `glsl` — shader compilation utilities (fallback: manual compilation)

- **Internal Dependencies**:
  - `vjlive3.renderer.shader_program` — shader management
  - `vjlive3.renderer.texture` — texture handling
  - `vjlive3.parameters` — parameter system for animation
  - `vjlive3.utils.image_utils` — image conversion utilities
  - `vjlive3.monitoring.telemetry` — performance metrics

- **Fallback Mechanisms**:
  - If OpenGL unavailable: Use CPU implementation (10× slower but functional)
  - If shader compilation fails: Use simplified shader or CPU path
  - If PIL unavailable: Accept numpy arrays only
  - If GPU memory exhausted: Process in tiles or reduce resolution

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_valid_config` | Effect initializes with valid configuration |
| `test_init_invalid_intensity` | Rejects intensity outside [0.0, 2.0] |
| `test_apply_aberration_rgb` | Correctly processes RGB images |
| `test_apply_aberration_rgba` | Correctly processes RGBA images (preserves alpha) |
| `test_apply_aberration_float64` | Auto-converts float64 to float32 |
| `test_apply_aberration_invalid_shape` | Raises error for invalid image shapes |
| `test_validate_intensity_valid` | Validates intensity within range |
| `test_validate_intensity_invalid` | Rejects intensity outside range |
| `test_simple_radial_model` | Simple radial displacement works correctly |
| `test_cauchy_dispersion_model` | Cauchy dispersion produces wavelength separation |
| `test_empirical_lens_model` | Empirical lens profile applies correctly |
| `test_custom_curve_application` | Custom dispersion curve applied accurately |
| `test_edge_detection_sobel` | Sobel edge detection identifies high-contrast regions |
| `test_edge_enhancement_amplification` | Edge enhancement amplifies aberration at edges |
| `test_de_fringe_suppression` | De-fringing reduces artifacts in flat regions |
| `test_temporal_smoothing_consistency` | Temporal smoothing reduces frame-to-frame jitter |
| `test_radial_falloff_power` | Falloff follows specified power law |
| `test_intensity_scaling` | Aberration scales linearly with intensity parameter |
| `test_calibration_srgb_profile` | sRGB profile calibrates correctly |
| `test_calibration_rec709_profile` | Rec.709 profile calibrates correctly |
| `test_calibration_unknown_profile` | Unknown profile falls back to sRGB |
| `test_custom_curve_256_elements` | Custom curve requires exactly 256 elements |
| `test_custom_curve_normalization` | Normalization scales curve to [0.0, 1.0] |
| `test_custom_curve_non_monotonic` | Non-monotonic curve triggers warning |
| `test_edge_mask_computation` | Edge mask correctly identifies edges |
| `test_performance_1080p_60fps` | Sustains 60 FPS at 1080p on target GPU |
| `test_performance_4k_30fps` | Sustains 30 FPS at 4K on target GPU |
| `test_memory_usage_1080p` | Peak memory < 100MB for 1080p processing |
| `test_gpu_fallback_cpu` | CPU fallback produces similar results (within tolerance) |
| `test_shader_compilation_success` | Shader compiles without errors |
| `test_shader_compilation_failure` | Handles shader compilation errors gracefully |
| `test_concurrent_processing_safety` | Thread-safe concurrent image processing |
| `test_report_generation_valid` | Report generation includes all metrics |
| `test_report_generation_empty_id` | Handles empty image_id gracefully |
| `test_parameter_animation` | Parameters can be animated over time without artifacts |
| `test_zero_intensity_no_change` | Intensity=0 produces identical output |
| `test_maximum_intensity_artifacts` | Intensity=2.0 produces strong but controlled artifacts |
| `test_alpha_channel_preservation` | RGBA alpha channel preserved unchanged |
| `test_color_space_accuracy` | Output color space matches input (no gamut shift) |
| `test_radial_symmetry_center` | Aberration centered on image center (width/2, height/2) |
| `test_different_aspect_ratios` | Works with 16:9, 4:3, 1:1, 21:9 aspect ratios |
| `test_very_small_images` | Handles images as small as 64×64 |
| `test_very_large_images` | Handles images up to 8K resolution (with downscaling if needed) |
| `test_nan_inf_handling` | Replaces NaN/Inf values with 0.0 before processing |
| `test_negative_values_clamping` | Clamps negative values to 0.0 with warning |
| `test_values_above_one_clamping` | Clamps values >1.0 to 1.0 with warning |

**Minimum coverage:** 90% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed and approved by architecture team
- [ ] All tests listed above pass with 90%+ coverage
- [ ] No file over 750 lines in the implementation
- [ ] No stubs or placeholder code in final implementation
- [ ] Comprehensive error handling implemented for all edge cases
- [ ] Shader code optimized for performance (target: <1ms per 1080p frame)
- [ ] CPU fallback path fully functional and validated
- [ ] Performance benchmarks meet requirements (60 FPS @ 1080p minimum)
- [ ] Documentation updated with usage examples and API reference
- [ ] Git commit with `[P1-QDRANT003] Chromatic Aberration: Complete implementation`
- [ ] BOARD.md updated with effect status
- [ ] Lock released and resources cleaned up
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## Technical Implementation Details

### Mathematical Formulation

**Radial Displacement**:
For a pixel at position `(x, y)` with center `(cx, cy)`:

```
r = sqrt((x - cx)² + (y - cy)²) / max_radius
displacement = intensity × r^radial_falloff × wavelength_coefficient
```

Where `max_radius = sqrt(cx² + cy²)` normalizes distance to [0.0, 1.0].

**Cauchy Dispersion Model**:
Wavelength-dependent refraction using Cauchy's equation:

```
n(λ) = A + B/λ² + C/λ⁴
displacement = k × (n(λ_red) - n(λ_green)) / (λ_red - λ_green)
```

With default coefficients:
- Red: λ = 0.650 μm → n ≈ 1.622
- Green: λ = 0.520 μm → n ≈ 1.522 (reference)
- Blue: λ = 0.450 μm → n ≈ 1.528

**Edge Enhancement**:
Using Sobel gradient magnitude:

```
Gx = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
Gy = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
gradient = sqrt(Gx² + Gy²)
edge_mask = smoothstep(edge_threshold, edge_threshold+0.1, gradient)
final_intensity = intensity × (1.0 + edge_enhancement × edge_mask)
```

**De-fringing**:
Suppress aberration in low-contrast regions:

```
local_variance = variance_in_5x5_window
de_fringe_factor = 1.0 - de_fringe_strength × (1.0 - local_variance)
aberration *= de_fringe_factor
```

**Temporal Smoothing**:
Exponential moving average:

```
smoothed_frame = (1 - smoothing_factor) × current_frame + smoothing_factor × previous_frame
```

### Shader Implementation (GLSL)

```glsl
#version 330 core

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform float u_intensity;
uniform int u_model;  // 0=simple, 1=cauchy, 2=empirical, 3=custom
uniform float u_radial_falloff;
uniform float u_edge_enhancement;
uniform float u_edge_threshold;
uniform float u_wavelength_scale;
uniform float u_de_fringe_strength;
uniform sampler1D u_custom_curve;  // 256-entry LUT
uniform vec3 u_channel_coeffs;  // (red, green, blue) displacement coefficients

in vec2 v_texcoord;
out vec4 frag_color;

// Sobel edge detection
float sobel_edge(vec2 uv, vec2 texel) {
    vec3 tl = texture(u_texture, uv + vec2(-texel.x, -texel.y)).rgb;
    vec3 tm = texture(u_texture, uv + vec2(0.0, -texel.y)).rgb;
    vec3 tr = texture(u_texture, uv + vec2(texel.x, -texel.y)).rgb;
    vec3 ml = texture(u_texture, uv + vec2(-texel.x, 0.0)).rgb;
    vec3 mr = texture(u_texture, uv + vec2(texel.x, 0.0)).rgb;
    vec3 bl = texture(u_texture, uv + vec2(-texel.x, texel.y)).rgb;
    vec3 bm = texture(u_texture, uv + vec2(0.0, texel.y)).rgb;
    vec3 br = texture(u_texture, uv + vec2(texel.x, texel.y)).rgb;
    
    vec3 gx = -tl - 2.0*ml - bl + tr + 2.0*mr + br;
    vec3 gy = -tl - 2.0*tm - tr + bl + 2.0*bm + br;
    
    float mag = length(vec2(length(gx), length(gy)));
    return mag / sqrt(2.0);  // Normalize to [0, 1]
}

// Cauchy dispersion calculation
float cauchy_dispersion(float wavelength, float B, float C) {
    return 1.0 + B / (wavelength * wavelength) + C / (wavelength * wavelength * wavelength * wavelength);
}

void main() {
    vec2 center = u_resolution * 0.5;
    vec2 pos = gl_FragCoord.xy - center;
    float r = length(pos) / length(center);  // Normalized radius [0, 1]
    
    // Compute base displacement
    float radial_factor = pow(r, u_radial_falloff);
    
    // Model-specific displacement coefficients
    vec3 coeffs = u_channel_coeffs;
    if (u_model == 0) {  // Simple radial
        coeffs = vec3(1.0, 0.0, -1.0);  // Red out, blue in
    } else if (u_model == 1) {  // Cauchy
        float n_red = cauchy_dispersion(0.650, 1.5, 0.004);
        float n_green = cauchy_dispersion(0.520, 1.5, 0.004);
        float n_blue = cauchy_dispersion(0.450, 1.5, 0.004);
        coeffs = vec3(
            n_red - n_green,
            0.0,
            n_blue - n_green
        );
    }
    
    // Edge enhancement
    float edge = sobel_edge(v_texcoord, 1.0/u_resolution);
    float edge_factor = 1.0 + u_edge_enhancement * smoothstep(u_edge_threshold, u_edge_threshold + 0.1, edge);
    
    // Final displacement per channel
    vec2 displacement = u_intensity * radial_factor * edge_factor * u_wavelength_scale * coeffs.xy;
    // Note: Z component used for blue channel offset in opposite direction
    
    // Sample channels with displacement
    vec2 red_uv = v_texcoord + displacement * vec2(1.0, 0.0);
    vec2 green_uv = v_texcoord;  // Green stays centered
    vec2 blue_uv = v_texcoord - displacement * vec2(1.0, 0.0);
    
    float red = texture(u_texture, red_uv).r;
    float green = texture(u_texture, green_uv).g;
    float blue = texture(u_texture, blue_uv).b;
    float alpha = texture(u_texture, v_texcoord).a;
    
    // De-fringing (simple luminance preservation)
    if (u_de_fringe_strength > 0.0) {
        vec3 original = texture(u_texture, v_texcoord).rgb;
        float original_lum = dot(original, vec3(0.299, 0.587, 0.114));
        vec3 aberrated = vec3(red, green, blue);
        float aberrated_lum = dot(aberrated, vec3(0.299, 0.587, 0.114));
        float lum_diff = abs(original_lum - aberrated_lum);
        float de_fringe = 1.0 - u_de_fringe_strength * smoothstep(0.0, 0.2, lum_diff);
        aberrated = mix(aberrated, original, de_fringe);
        red = aberrated.r;
        green = aberrated.g;
        blue = aberrated.b;
    }
    
    frag_color = vec4(red, green, blue, alpha);
}
```

### CPU Fallback Implementation

```python
def apply_aberration_cpu(
    image: np.ndarray,
    config: ChromaticConfig,
    coeffs: WavelengthCoefficients
) -> np.ndarray:
    """CPU implementation using numpy for fallback."""
    h, w = image.shape[:2]
    center = np.array([w / 2, h / 2])
    y, x = np.mgrid[0:h, 0:w]
    pos = np.stack([x, y], axis=-1) - center
    r = np.linalg.norm(pos, axis=-1) / np.linalg.norm(center)
    radial = r ** config.radial_falloff
    
    # Compute displacements
    red_disp = config.intensity * radial * coeffs.red_coeff * config.wavelength_scale
    green_disp = np.zeros_like(radial)
    blue_disp = -config.intensity * radial * coeffs.blue_coeff * config.wavelength_scale
    
    # Edge enhancement
    if config.edge_enhancement > 0:
        edge_mask = compute_sobel_edges_cpu(image, config.edge_threshold)
        red_disp *= (1.0 + config.edge_enhancement * edge_mask)
        blue_disp *= (1.0 + config.edge_enhancement * edge_mask)
    
    # Sample channels with subpixel interpolation
    result = np.zeros_like(image)
    for c, disp in enumerate([red_disp, green_disp, blue_disp]):
        map_x = (x + disp) / (w - 1)
        map_y = y / (h - 1)
        result[..., c] = map_coordinates(image[..., c], [map_y, map_x], order=1)
    
    if image.shape[-1] == 4:
        result[..., 3] = image[..., 3]  # Preserve alpha
    
    return result
```

### Performance Optimization Strategies

1. **Shader Caching**: Compile shader once per configuration, reuse across frames
2. **Texture Format**: Use GL_RGBA16F for HDR processing, GL_RGBA8 for SDR
3. **Framebuffer Reuse**: Reuse FBO and renderbuffers across frames
4. **Batch Processing**: Process multiple images in single draw call when possible
5. **LOD Selection**: Downscale large images, process at lower resolution
6. **Region of Interest**: Only process changed regions if image has static areas
7. **SIMD Optimization**: Use vectorized numpy operations for CPU fallback
8. **Memory Pooling**: Pre-allocate temporary buffers to avoid per-frame allocation
9. **Early Exit**: Skip processing if intensity ≈ 0 or no edges detected
10. **Multi-threading**: Use thread pool for CPU fallback on multi-core systems

---

## Configuration Schema

```json
{
  "chromatic_aberration": {
    "default_intensity": 0.5,
    "default_model": "cauchy_dispersion",
    "default_radial_falloff": 1.0,
    "default_edge_enhancement": 0.0,
    "default_edge_threshold": 0.1,
    "default_wavelength_scale": 1.0,
    "default_de_fringe_strength": 0.0,
    "default_temporal_smoothing": 0.0,
    "performance": {
      "target_fps_1080p": 60,
      "target_fps_4k": 30,
      "max_memory_mb": 100,
      "gpu_fallback_timeout_ms": 10
    },
    "calibration": {
      "srgb_red_coeff": 0.015,
      "srgb_green_coeff": 0.010,
      "srgb_blue_coeff": 0.005,
      "rec709_red_coeff": 0.012,
      "rec709_green_coeff": 0.010,
      "rec709_blue_coeff": 0.008
    },
    "cauchy_constants": {
      "B": 1.5,
      "C": 0.004
    }
  }
}
```

---

## Security and Safety

- **Input Validation**: All images validated for format, dtype, and value range
- **Resource Limits**: Hard limits on image size (max 8K), memory usage (max 1GB)
- **Shader Safety**: Shader code reviewed for infinite loops and buffer overruns
- **Denial of Service Protection**: Timeouts on all GPU operations (default 10ms)
- **Data Integrity**: Output validated to ensure no NaN/Inf values
- **Memory Safety**: All OpenGL objects properly deleted on destruction
- **Thread Safety**: Parameter updates use atomic operations or locks
- **Fallback Safety**: CPU fallback produces equivalent results within tolerance

---

## Future Enhancements

- **Multi-pass Effects**: Combine with lens flare, ghosting, and bokeh
- **Anamorphic Simulation**: Model anamorphic lens squeeze/stretch
- **Depth-Aware Aberration**: Vary intensity based on depth map
- **Machine Learning Calibration**: Learn aberration from lens photographs
- **HDR Tone Mapping Integration**: Preserve HDR highlights during aberration
- **Vignette Coupling**: Combine aberration with vignette effects
- **Chromatic Temporal Effects**: Time-varying aberration for psychedelic effects
- **Subpixel Accuracy**: Use dithering for smoother displacement at low resolutions
- **Compute Shader**: Use Vulkan/DirectX compute for even better performance
- **Real Lens Profiles**: Import lens profiles from camera manufacturers

---

This specification provides a comprehensive technical foundation for implementing a high-performance, physically-plausible chromatic aberration effect suitable for live VJ performance and post-production applications.