````markdown
# P7-VE19: Chroma Key Effect (Green/Blue Screen)

> **Task ID:** `P7-VE19`
> **Priority:** P0 (Critical)
> **Source:** vjlive (`plugins/vcore/chroma_key.py`)
> **Class:** `ChromaKeyEffect`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete Pass 2 specification for the `ChromaKeyEffect`—a chroma
keying effect for background removal via green/blue screen keying. Isolates
and removes a selected color key (green, blue, or custom) and composites
replacement backgrounds. The objective is to document exact keying mathematics,
threshold computation, edge refinement, spill suppression, CPU fallback,
and comprehensive tests for feature parity with vjlive.

## Technical Requirements
- Implement as a VJLive3 effect plugin (background removal via chroma key)
- Sustain 60 FPS with real-time keying and edge refinement (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback to original if key fails (Safety Rail 7)
- CPU fallback implementation for compatibility testing

## Implementation Notes / Porting Strategy
1. Sample key color tolerance from parameter.
2. Detect pixels matching key color within tolerance.
3. Generate alpha mask (0=key, 1=foreground).
4. Apply edge refinement (feather/anti-alias mask edges).
5. Composite with replacement background.
6. Optional chroma spill suppression.
7. NumPy-based CPU fallback.

## Public Interface
```python
class ChromaKeyEffect(Effect):
    """
    Chroma Key Effect: Green/blue screen background removal.
    
    Isolates and removes a selected color (green, blue, or custom) from
    video using chroma keying. Supports background replacement, edge
    refinement, and spill suppression. Essential for VJ performances,
    green screen video composition, and studio effects.
    """

    # Key color presets
    KEY_COLORS = {
        0: (0.0, 1.0, 0.0),      # Green
        1: (0.0, 0.0, 1.0),      # Blue
        2: (1.0, 0.0, 1.0),      # Magenta
        3: (0.0, 1.0, 1.0),      # Cyan
    }

    def __init__(self, width: int = 1920, height: int = 1080,
                 key_color: int = 0, use_gpu: bool = True):
        """
        Initialize the chroma key effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            key_color: Preset key color (0=green, 1=blue, etc.).
            use_gpu: If True, use GPU keying; else CPU.
        """
        super().__init__("Chroma Key", CHROMAKEY_VERTEX_SHADER,
                         CHROMAKEY_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "compositing"
        self.effect_tags = ["chroma", "key", "green-screen", "background"]
        self.features = ["CHROMA_KEYING", "EDGE_REFINE"]
        self.usage_tags = ["STUDIO", "COMPOSITION", "VJ"]
        
        self.use_gpu = use_gpu
        self.key_color_preset = clamp(key_color, 0, 3)

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'key_color_hue': (0.0, 10.0),      # key color hue (0–360°)
            'key_color_sat': (0.0, 10.0),      # key color saturation
            'threshold': (0.0, 10.0),          # tolerance/threshold
            'falloff': (0.0, 10.0),            # edge softness
            'edge_feather': (0.0, 10.0),       # anti-alias feathering
            'spill_suppression': (0.0, 10.0),  # chroma spill cleanup
            'pre_multiply': (0.0, 10.0),       # edge pre-multiply mode
            'despill_factor': (0.0, 10.0),     # despill strength
            'background_opacity': (0.0, 10.0), # background visibility
            'opacity': (0.0, 10.0),            # effect opacity
        }

        # Default parameter values
        self.parameters = {
            'key_color_hue': 3.0,              # Green hue
            'key_color_sat': 8.0,
            'threshold': 4.0,                  # medium tolerance
            'falloff': 3.0,
            'edge_feather': 2.0,
            'spill_suppression': 3.0,
            'pre_multiply': 5.0,
            'despill_factor': 4.0,
            'background_opacity': 5.0,
            'opacity': 10.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'key_color_hue': "Key color hue (0–10 maps to 0–360°, green≈2)",
            'key_color_sat': "Key color saturation (0=mono, 10=pure)",
            'threshold': "Tolerance (0=exact match, 10=very loose)",
            'falloff': "Threshold softness (0=hard, 10=smooth)",
            'edge_feather': "Anti-alias feathering pixels (0=none, 10=large)",
            'spill_suppression': "Chroma spill cleanup (0=none, 10=aggressive)",
            'pre_multiply': "Edge treatment (0=none, 10=full premultiply)",
            'despill_factor': "Despill strength (0=none, 10=full despill)",
            'background_opacity': "Background visibility (0=transparent, 10=opaque)",
            'opacity': "Effect opacity (0=original, 10=full keying)",
        }

        # Sweet spots
        self._sweet_spots = {
            'threshold': [3.0, 4.0, 5.0],
            'falloff': [2.0, 3.0, 4.0],
            'edge_feather': [1.0, 2.0, 3.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None,
              chain = None) -> int:
        """
        Render chroma keyed output (alpha mask + composite).
        
        Args:
            tex_in: Input video texture (required).
            extra_textures: Optional replacement background texture.
            chain: Rendering chain context.
            
        Returns:
            Output texture with keyed background removed.
        """
        # Sample input color
        # Compute distance to key color
        # Generate alpha mask
        # Apply edge refinement
        # Composite with background
        # Return output
        pass

    def compute_key_alpha(self, color: tuple, key_color: tuple,
                         threshold: float, falloff: float) -> float:
        """
        Compute alpha mask value based on chroma distance.
        
        Args:
            color: Sampled RGB color (r, g, b) in [0, 1].
            key_color: Key color (r, g, b) in [0, 1].
            threshold: Color distance threshold [0, 1].
            falloff: Softness of threshold [0, 1].
            
        Returns:
            Alpha value (0=key, 1=foreground) in [0, 1].
        """
        # Compute distance in color space
        # Apply threshold and falloff
        # Return alpha
        pass

    def refine_edges(self, alpha: float, neighbors: list,
                    edge_feather: float) -> float:
        """
        Refine alpha mask edges via anti-aliasing.
        
        Args:
            alpha: Original alpha value [0, 1].
            neighbors: List of neighboring alpha values.
            edge_feather: Feather radius in pixels [0, 10].
            
        Returns:
            Refined alpha value [0, 1].
        """
        # Detect edge pixels
        # Apply Gaussian blur to smooth edges
        # Return refined alpha
        pass

    def suppress_spill(self, color: tuple, alpha: float,
                      key_color: tuple, spill_amount: float) -> tuple:
        """
        Suppress chroma spill (color fringing on edges).
        
        Args:
            color: Original RGB color (r, g, b) in [0, 1].
            alpha: Alpha mask [0, 1].
            key_color: Key color (r, g, b) in [0, 1].
            spill_amount: Despill strength [0, 1].
            
        Returns:
            Despilled color.
        """
        # Reduce key color channel in foreground
        # Return despilled color
        pass

    def apply_uniforms(self, time: float, resolution: tuple,
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms for chroma key parameters.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input (unused).
            semantic_layer: Optional semantic input (unused).
        """
        # Bind key color and threshold to uniforms
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `key_color_hue` (float, UI 0—10) → internal `hue` = x / 10.0 * 360.0
  - Key color hue [0, 360°]
- `key_color_sat` (float, UI 0—10) → internal `sat` = x / 10.0
  - Key color saturation [0, 1.0]
- `threshold` (float, UI 0—10) → internal `threshold` = x / 10.0
  - Color distance threshold [0, 1.0]
- `falloff` (float, UI 0—10) → internal `falloff` = map_linear(x, 0,10, 0.01, 0.2)
  - Threshold softness [0.01=hard, 0.2=smooth]
- `edge_feather` (float, UI 0—10) → internal `feather` = x * 0.5
  - Feather radius in pixels [0, 5]
- `spill_suppression` (float, UI 0—10) → internal `spill` = x / 10.0
  - Spill cleanup strength [0, 1.0]
- `pre_multiply` (float, UI 0—10) → internal `premult` = x / 10.0
  - Pre-multiply amount [0, 1.0]
- `despill_factor` (float, UI 0—10) → internal `despill` = x / 10.0
  - Despill strength [0, 1.0]
- `background_opacity` (float, UI 0—10) → internal `bg_α` = x / 10.0
  - Background opacity [0, 1.0]
- `opacity` (float, UI 0—10) → internal `α` = x / 10.0
  - Effect opacity [0, 1]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform vec3 key_color;`            // key RGB color
- `uniform float threshold;`           // color distance threshold
- `uniform float falloff;`             // threshold softness
- `uniform float edge_feather;`        // edge anti-aliasing
- `uniform float spill_suppression;`   // chroma spill cleanup
- `uniform float despill_factor;`      // despill strength
- `uniform float pre_multiply;`        // edge pre-multiply
- `uniform float background_opacity;`  // background vis
- `uniform float opacity;`             // effect opacity
- `uniform vec2 resolution;`           // screen size
- `uniform sampler2D tex_in;`          // input texture
- `uniform sampler2D tex_background;`  // background texture (optional)

## Effect Math (concise, GPU/CPU-consistent)

### 1) Key Color Distance Computation

Convert to suitable color space and compute distance:

```
// RGB to HSV
rgb_color = sample(tex_in, uv)
key_color_hsv = rgb_to_hsv(key_color)
color_hsv = rgb_to_hsv(rgb_color)

// Compute distance (hue + saturation weighted)
hue_diff = abs(color_hsv.x - key_color_hsv.x)
// Account for hue wraparound
if hue_diff > 0.5:
    hue_diff = 1.0 - hue_diff
    
sat_diff = abs(color_hsv.y - key_color_hsv.y)
value_diff = abs(color_hsv.z - key_color_hsv.z)

// Distance metric (weighted)
distance = sqrt(hue_diff^2 * 4 + sat_diff^2 + value_diff^2 * 0.5)
```

### 2) Alpha Mask Generation (Threshold + Falloff)

```
// Convert distance to alpha
alpha = 1.0 - smoothstep(threshold - falloff, threshold + falloff, distance)

// Clamp to [0, 1]
alpha = clamp(alpha, 0, 1)
```

### 3) Edge Refinement (Feathering)

Apply Gaussian blur to alpha mask edges:

```
// Sample neighboring alphas
neighbors = [
    alpha(uv + vec2(-1, -1)), alpha(uv + vec2(0, -1)), ...
    (9-tap pattern)
]

// Gaussian kernel [1, 2, 1] / 4
blurred_alpha = dot(neighbors, gaussian_kernel) / weights_sum
refined_alpha = mix(alpha, blurred_alpha, edge_feather / 10.0)
```

### 4) Chroma Spill Suppression

Reduce key color channel in foreground:

```
// Identify dominant channel in key color
max_channel = max(key_color.r, key_color.g, key_color.b)
key_channel_idx = argmax([r, g, b])

// Reduce that channel in the output
despill_color = rgb_color
despill_color[key_channel_idx] *= (1.0 - spill_suppression)

// Blend based on alpha
output_color = mix(despill_color, rgb_color, alpha)
```

### 5) Pre-Multiply Alpha

For composite quality:

```
// Pre-multiply: color × alpha
// Prevents color bleeding at edges
output_color = rgb_color * alpha * pre_multiply + 
              rgb_color * (1.0 - pre_multiply)
```

### 6) Composite with Background

```
// Sample background (if available)
bg_color = texture(tex_background, uv)

// Composite: foreground over background
final_color = rgb_color * alpha + bg_color * (1.0 - alpha) * background_opacity

// Effect opacity
output = mix(original, final_color, opacity)
```

## CPU Fallback (NumPy sketch)

```python
def chroma_key_cpu(frame, key_color_hue, key_color_sat, threshold,
                  falloff, spill_suppression, despill_factor):
    """Apply chroma keying on CPU."""
    
    img = frame.astype(np.float32) / 255.0
    h, w = img.shape[:2]
    
    # Convert to HSV
    hsv_frame = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    
    # Create key color in HSV
    key_hsv = np.array([key_color_hue / 360.0 * 255, key_color_sat * 255, 128])
    
    # Compute distance
    distance = np.sqrt((hsv_frame[:,:,0] - key_hsv[0])**2 * 4 +
                      (hsv_frame[:,:,1] - key_hsv[1])**2)
    
    # Generate alpha mask
    alpha = 1.0 - np.clip((distance - threshold) / max(falloff, 0.001), 0, 1)
    
    # Suppress spill
    for c in range(3):
        img[:,:,c] = img[:,:,c] * (1.0 - alpha * spill_suppression)
    
    # Apply alpha to frame
    result = img.copy()
    for c in range(3):
        result[:,:,c] = result[:,:,c] * alpha
    
    return (result * 255).astype(np.uint8)
```

## Presets (recommended)
- `Classic Green Screen`:
  - `key_color_hue` 3.0, `key_color_sat` 8.0, `threshold` 4.0,
    `falloff` 3.0, `edge_feather` 2.0, `spill_suppression` 4.0
- `Tight Blue Screen`:
  - `key_color_hue` 6.0, `threshold` 3.0, `falloff` 2.0,
    `edge_feather` 1.0, `despill_factor` 6.0
- `Studio Quality`:
  - `key_color_hue` 3.0, `threshold` 5.0, `falloff` 4.0,
    `edge_feather` 3.0, `spill_suppression` 6.0, `pre_multiply` 8.0
- `Soft Edge Key`:
  - `key_color_hue` 3.0, `threshold` 6.0, `falloff` 6.0,
    `edge_feather` 5.0, `despill_factor` 5.0, `opacity` 9.0

## Edge Cases and Error Handling
- **threshold = 0**: Only exact key color matches keyed.
- **threshold = 1**: All pixels keyed (total transparency).
- **falloff = 0**: Hard edge (aliasing).
- **No background texture**: Use transparent background (alpha only).
- **NaN in distance**: Fallback to distance = 1.0.
- **All alpha = 0**: Return completely transparent frame.

## Test Plan (minimum ≥80% coverage)
- `test_no_key_match_opaque` — pixels not matching key remain opaque
- `test_exact_key_match_transparent` — exact key color fully transparent
- `test_threshold_controls_tolerance` — threshold controls match range
- `test_falloff_softens_edges` — falloff smooths alpha transitions
- `test_edge_feather_anti_aliases` — feather reduces aliasing
- `test_spill_suppression_color_cleanup` — suppression reduces color fringing
- `test_despill_removes_fringing` — despill reduces chroma artifacts
- `test_pre_multiply_edge_quality` — pre-multiply improves compositing
- `test_background_composite_correct` — background composites properly
- `test_custom_key_color_green_blue` — different key colors work
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p
- `test_transparent_alpha_output` — alpha channel correct
- `test_edge_artifacts_minimal` — smooth edges, no heavy artifacts

## Verification Checkpoints
- [ ] `ChromaKeyEffect` registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly
- [ ] Key color distance computation works
- [ ] Alpha mask generated correctly
- [ ] Edge feathering produces smooth transitions
- [ ] Spill suppression reduces color fringing
- [ ] Background compositing works
- [ ] CPU fallback produces keyed output
- [ ] Presets render at intended key styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p
- [ ] No major visual artifacts from keying

## Implementation Handoff Notes
- Color space selection crucial: HSV works well for green/blue
- Distance metric: Weight hue heavily, less on saturation/value
- Edge refinement: Gaussian blur on alpha, not RGB (prevents color fringing)
- Spill suppression: Target the dominant channel in key color
- Performance: Pre-compute key color in HSV once, reuse each frame

## Resources
- Reference: Nuke ChromaKey, After Effects keylight, professional VJ keying
- Math: HSV color space, distance metrics, Gaussian blur
- GPU: Fragment shader color space conversions, neighbor sampling

````
