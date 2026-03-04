# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT099_LumaChromaMaskEffect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT099 — LumaChromaMaskEffect

**What This Module Does**

LumaChromaMaskEffect is the scalpel of video synthesis — a precision masking tool that routes effects to specific brightness or color regions of video. Instead of applying effects uniformly, it generates a mask texture based on luminance or chrominance thresholds, with smooth feathering, inversion, and multiple combination modes. The mask output can be used to composite, blend, or control other parameters.

**What This Module Does NOT Do**

- Generate new visual content from scratch
- Apply effects without masking (use other effects for that)
- Perform 3D transformations or spatial warping
- Handle audio reactivity (though it can be modulated by audio)
- Work with depth data (use depth-based effects for that)

---

## Detailed Behavior and Parameter Interactions

### Core Masking Architecture

The effect operates in two main phases:

1. **Mask Generation**: Creates a grayscale mask (0.0-1.0) based on selected source mode
2. **Mask Application**: Applies the mask to the source image using the selected output mode

### Mask Source Modes (6 options)

| Mode | Parameter | Description | Range Mapping |
|------|-----------|-------------|---------------|
| Luminance (0) | `mask_mode=0` | Brightness-based masking using dot product with luminance weights | 0-10 → 0=luma |
| Chroma Saturation (1) | `mask_mode=1` | Saturation-based masking from HSV color space | 0-10 → 1=chroma_sat |
| Chroma Hue Keying (2) | `mask_mode=2` | Hue-based keying with tolerance and saturation gate | 0-10 → 2=chroma_hue |
| Red Channel (3) | `mask_mode=3` | Isolates red channel for color-based masking | 0-10 → 3=red |
| Color Distance (4) | `mask_mode=4` | Distance from target color in RGB space | 0-10 → 4=custom |
| Motion Detection (5) | `mask_mode=5` | Pseudo-motion via frame differencing | 0-10 → 5=motion |

### Threshold System

- **Threshold Low** (`threshold_low`): 0-10 → 0.0-1.0 (below this = masked)
- **Threshold High** (`threshold_high`): 0-10 → 0.0-1.0 (above this = unmasked)
- **Feather** (`feather`): 0-10 → 0.0-0.5 (soft edge width)

The mask is calculated as: `mask = smoothstep(low-feather, low+feather, value) * (1.0 - smoothstep(high-feather, high+feather, value))`

### Mask Refinement Operations

**Morphological Operations** (applied after threshold):
- **Erode** (`erode`): 0-10 → 0-5px (shrinks mask by taking minimum in neighborhood)
- **Dilate** (`dilate`): 0-10 → 0-5px (expands mask by taking maximum in neighborhood)

**Spatial Operations**:
- **Blur** (`blur_amount`): 0-10 → 0-10px (Gaussian blur on mask)
- **Contrast** (`contrast`): 0-10 → 0.5-5.0 (contrast adjustment on mask)
- **Gamma** (`gamma`): 0-10 → 0.2-5.0 (gamma correction on mask)

### Combination Modes (5 options)

| Mode | Parameter | Description | Range Mapping |
|------|-----------|-------------|---------------|
| Replace Alpha (0) | `combine_mode=0` | Mask replaces alpha channel | 0-10 → 0=replace_alpha |
| Multiply RGB (1) | `combine_mode=1` | Mask multiplies RGB channels | 0-10 → 1=multiply_rgb |
| Screen (2) | `combine_mode=2` | Screen blend mode with mask | 0-10 → 2=screen |
| Isolate (3) | `combine_mode=3` | Mask isolates specific regions | 0-10 → 3=isolate |
| Animated Wipe (4) | `combine_mode=4` | Spatial wipe with animation | 0-10 → 4=wipe |

### Output Visualization Modes (5 options)

| Mode | Parameter | Description | Range Mapping |
|------|-----------|-------------|---------------|
| Masked Image (0) | `output_mode=0` | Original image with mask applied as alpha multiply | 0-10 → 0=masked_image |
| Mask Only (1) | `output_mode=1` | Grayscale mask visualization | 0-10 → 1=mask_only |
| Mask Colored (2) | `output_mode=2` | Mask colored with hue cycling | 0-10 → 2=mask_colored |
| Split View (3) | `output_mode=3` | Left=original, right=masked | 0-10 → 3=split_view |
| Overlay (4) | `output_mode=4` | Colored mask overlaid on image | 0-10 → 4=overlay |

### Hue Keying Specific Parameters

When `mask_mode=2` (chroma_hue):
- **Target Hue** (`target_hue`): 0-10 → 0.0-1.0 (target hue in HSV space)
- **Hue Width** (`hue_width`): 0-10 → 0.01-0.5 (tolerance around target hue)
- **Sat Min** (`sat_min`): 0-10 → 0.0-1.0 (minimum saturation to include)

### Animation and Effects

- **Animate Threshold** (`animate_threshold`): 0-10 → 0.0-1.0 (oscillates thresholds over time)
- **Wipe Angle** (`wipe_angle`): 0-10 → 0.0-6.28 (direction for animated wipe)
- **Wipe Softness** (`wipe_softness`): 0-10 → 0.0-0.5 (edge softness for wipe)
- **Mask Color Hue** (`mask_color_hue`): 0-10 → 0.0-1.0 (hue for colored mask visualization)
- **Mask Opacity** (`mask_opacity`): 0-10 → 0.0-1.0 (opacity for overlay mode)

---

## Public Interface

### Constructor
```python
LumaChromaMaskEffect(name: str = "luma_chroma_mask")
```

### Parameters (22 total)

#### Mask Source Parameters
- `mask_mode`: float (0.0-10.0) - Source mode selection
- `threshold_low`: float (0.0-10.0) - Lower threshold
- `threshold_high`: float (0.0-10.0) - Upper threshold
- `feather`: float (0.0-10.0) - Soft edge width
- `invert_mask`: float (0.0-10.0) - Invert mask (0.0=normal, 10.0=inverted)

#### Hue Keying Parameters (only active when mask_mode=2)
- `target_hue`: float (0.0-10.0) - Target hue for keying
- `hue_width`: float (0.0-10.0) - Hue tolerance width
- `sat_min`: float (0.0-10.0) - Minimum saturation gate

#### Mask Refinement Parameters
- `erode`: float (0.0-10.0) - Morphological erode
- `dilate`: float (0.0-10.0) - Morphological dilate
- `blur_amount`: float (0.0-10.0) - Gaussian blur
- `contrast`: float (0.0-10.0) - Contrast adjustment
- `gamma`: float (0.0-10.0) - Gamma correction

#### Combination Parameters
- `combine_mode`: float (0.0-10.0) - Blend mode selection
- `wipe_angle`: float (0.0-10.0) - Wipe direction angle
- `wipe_softness`: float (0.0-10.0) - Wipe edge softness

#### Visualization Parameters
- `output_mode`: float (0.0-10.0) - Output visualization mode
- `mask_color_hue`: float (0.0-10.0) - Color hue for visualization
- `mask_opacity`: float (0.0-10.0) - Overlay opacity
- `animate_threshold`: float (0.0-10.0) - Threshold animation amount

### Methods

#### apply_uniforms(time, resolution, audio_reactor=None, semantic_layer=None)
Applies all parameters to the shader uniforms. Handles:
- Parameter remapping from 0-10 UI range to shader-specific ranges
- Threshold animation when `animate_threshold > 0`
- Dynamic mask calculation based on current mode
- Morphological operations when erode/dilate > 0
- Blur when blur_amount > 0
- Contrast/gamma adjustments
- Wipe overlay when combine_mode=4

#### set_parameter(name, value)
Sets individual parameters by name.

#### get_parameter(name)
Gets individual parameter values by name.

---

## Inputs and Outputs

### Input Textures
- **tex0**: Primary input texture (sampler2D)
- **time**: Current time (float)
- **resolution**: Viewport resolution (vec2)
- **u_mix**: Mix factor between original and processed (float)

### Output
- **fragColor**: Final processed color (vec4)

### Texture Units
- **tex0**: Unit 0 (primary input)

---

## Edge Cases and Error Handling

### Parameter Edge Cases

1. **Threshold Inversion**: When `threshold_low > threshold_high`, the mask becomes inverted
2. **Feather Overflow**: When `feather` is large relative to threshold range, mask may become fully opaque/transparent
3. **Morphological Overflow**: Large `erode` or `dilate` values can cause mask to disappear or fill entire image
4. **Blur Performance**: High `blur_amount` values significantly increase computational cost

### Shader Edge Cases

1. **Division by Zero**: Protected in gamma calculation with `clamp(mask, 0.0, 1.0)`
2. **Texture Sampling**: All texture samples are clamped to valid UV coordinates
3. **NaN Prevention**: All calculations use safe operations with fallback values

### Runtime Edge Cases

1. **Zero Resolution**: Shader handles zero resolution gracefully (no division by zero)
2. **Invalid Parameters**: All parameters are clamped to valid ranges before use
3. **Memory Usage**: No dynamic memory allocation in shader

---

## Mathematical Formulations

### Parameter Remapping Functions

```glsl
// Mask source mode remapping
int mmode = int(mask_mode / 10.0 * 5.0 + 0.5);

// Threshold remapping
float t_low = threshold_low / 10.0;
float t_high = threshold_high / 10.0;
float feath = feather / 10.0 * 0.5;

// Morphological remapping
float ero = erode / 10.0 * 5.0;
float dil = dilate / 10.0 * 5.0;
float blur = blur_amount / 10.0 * 10.0;

// Color remapping
float m_hue = mask_color_hue / 10.0;
float m_opacity = mask_opacity / 10.0;

// Animation remapping
float anim = animate_threshold / 10.0;
```

### Core Mask Calculation

```glsl
// Luminance calculation
float luma = dot(src.rgb, vec3(0.299, 0.587, 0.114));

// HSV conversion
vec3 hsv = rgb2hsv(src.rgb);

// Hue distance (circular)
float hue_distance(float h1, float h2) {
    float d = abs(h1 - h2);
    return min(d, 1.0 - d);
}

// Threshold with feathering
float mask = smoothstep(t_low - feath, t_low + feath, mask_val) *
            (1.0 - smoothstep(t_high - feath, t_high + feath, mask_val));

// Invert
mask = mix(mask, 1.0 - mask, inv);
```

### Morphological Operations

```glsl
// Erode (minimum in neighborhood)
if (ero > 0.0) morph_val = min(morph_val, n_mask);

// Dilate (maximum in neighborhood)
if (dil > 0.0) morph_val = max(morph_val, n_mask);
```

### Blur Implementation

```glsl
// Gaussian blur with dynamic radius
float blurred = 0.0;
float weight_sum = 0.0;
for (float dx = -4.0; dx <= 4.0; dx += 1.0) {
    for (float dy = -4.0; dy <= 4.0; dy += 1.0) {
        float w = exp(-(dx*dx + dy*dy) / (blur * 0.5));
        // ... weighted sum calculation
    }
}
```

### Contrast and Gamma

```glsl
// Contrast adjustment
mask = (mask - 0.5) * cont + 0.5;

// Gamma correction
mask = pow(mask, 1.0 / gam);
```

### Animated Wipe

```glsl
// Spatial wipe with time-based animation
vec2 wipe_dir = vec2(cos(w_angle), sin(w_angle));
float wipe_pos = dot(uv - 0.5, wipe_dir) + 0.5;
float wipe_mask = smoothstep(0.5 - w_soft, 0.5 + w_soft, wipe_pos + sin(time * 0.5) * 0.3);
```

---

## Performance Characteristics

### Computational Complexity

| Operation | Cost | Notes |
|-----------|------|-------|
| Basic mask calc | O(1) | Single texture sample |
| Morphological ops | O(n²) | n=3-6 pixel radius |
| Blur | O(n²) | n=4-8 pixel radius |
| HSV conversion | O(1) | Branchless implementation |

### Texture Fetch Analysis

- **Base case**: 1 texture fetch
- **With blur**: ~64-100 texture fetches (8x8 kernel)
- **With morphology**: ~36-100 texture fetches (6x6 kernel)
- **Total worst case**: ~200 texture fetches

### Performance Optimizations

1. **Early Exit**: If all refinement parameters are zero, skip expensive operations
2. **Branch Optimization**: GLSL compiler optimizes mode-specific branches
3. **Constant Folding**: Parameter remapping happens at compile time when possible
4. **SIMD Utilization**: All operations are vectorizable

### Memory Usage

- **Registers**: ~32-64 vec4 registers
- **Shared Memory**: None (stateless shader)
- **Texture Cache**: Critical for performance with blur/morphology

### Bottlenecks

1. **Blur Operation**: Most expensive when blur_amount > 5
2. **Morphological Ops**: Expensive when erode/dilate > 3
3. **HSV Conversion**: Moderate cost but unavoidable for chroma modes

---

## Test Plan

### Unit Tests (Python)

1. **Parameter Remapping Tests**
   - Test all 0-10 to shader-specific range conversions
   - Verify edge cases (0, 5, 10)
   - Test invalid parameter handling

2. **Mask Calculation Tests**
   - Test each mask mode independently
   - Verify threshold behavior with various feather values
   - Test invert functionality

3. **Morphological Operation Tests**
   - Test erode/dilate with various radii
   - Verify correct min/max behavior
   - Test edge cases (zero radius, large radius)

4. **Blur Tests**
   - Test blur with various amounts
   - Verify Gaussian distribution
   - Test performance with high blur values

### Integration Tests (GLSL)

1. **Shader Compilation Tests**
   - Test all parameter combinations
   - Verify no compilation errors
   - Test with different OpenGL versions

2. **Visual Regression Tests**
   - Test each mask mode with known inputs
   - Verify output matches expected patterns
   - Test animation over time

3. **Performance Tests**
   - Benchmark with different parameter combinations
   - Test frame rate with high-cost operations
   - Verify memory usage stays within limits

### Edge Case Tests

1. **Zero Resolution**
   - Test with 0x0 resolution
   - Test with very small resolutions

2. **Invalid Parameters**
   - Test with NaN values
   - Test with infinite values
   - Test with out-of-range values

3. **Texture Edge Cases**
   - Test with transparent textures
   - Test with solid color textures
   - Test with gradient textures

### Coverage Target: 85% minimum

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT099: LumaChromaMaskEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

**Implementation Location**: `/home/happy/Desktop/claude projects/vjlive/plugins/vcore/luma_chroma_mask.py`

**Key Features from Legacy Code**:
- 22 parameters with 0-10 UI range
- 6 mask source modes (luma, saturation, hue key, red channel, color distance, motion)
- 5 combination modes including animated wipe
- 5 visualization modes
- HSV color space conversion functions
- Morphological erode/dilate operations
- Gaussian blur on mask
- Contrast and gamma correction
- Threshold animation capability
- Split view and overlay visualization modes

**Shader Complexity**: ~240 lines of GLSL 330 core code with comprehensive parameter handling and multiple optimization paths.