# Spec: P6-GE09 — Voronoi Pattern Generator

**File naming:** `docs/specs/P6-P6-GE09_generators.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-GE09 — generators

**What This Module Does**  
The `VoronoiEffect` module generates tessellating cellular patterns using Voronoi diagram mathematics, creating organic-looking patchwork and seed-point-based visualizations. It produces dynamically-animated cell regions by computing nearest-neighbor distance fields to animated seed points, with support for multiple distance metrics, color per cell, and flowing boundary animations. The module transforms video input through Voronoi space partitioning, rendering each frame with mathematically precise cell boundaries, time-varying seed positions, and energy-based color mapping.

**What This Module Does NOT Do**  
- Handle file I/O or persistent storage operations  
- Process audio streams or provide direct sound input  
- Implement 3D geometry or volumetric effects  
- Provide direct MIDI or OSC control interfaces  
- Support arbitrary texture loading outside of procedural generation  

**Detailed Behavior**  
The module processes video frames through several mathematical stages:
1. **Seed Point Generation**: Initializes and animates seed points in [0,1]×[0,1] normalized space
2. **Distance Field Computation**: For each pixel, computes minimum distance to all active seed points using selected metric (Euclidean, Manhattan, Chebyshev)
3. **Voronoi Cell Assignment**: Determines which seed point "owns" each pixel based on nearest-neighbor relationship
4. **Boundary Detection**: Identifies edges between adjacent cells using gradient threshold
5. **Color Mapping**: Assigns colors per cell (hash-based, distance-gradient, or input-based)
6. **Output Compositing**: Blends Voronoi pattern with input frame using mix ratio

Key mathematical characteristics:
- Seed count maps 0-10 range to 4-64 seeds (n = ceil(4 + seeds/10 * 60))
- Seed position animation: `p_i(t) = p_i(0) + v_i * t * animation_speed / 10`
- Distance metric (Euclidean): `d_E(x,y) = sqrt((x-x_s)^2 + (y-y_s)^2)`
- Distance metric (Manhattan): `d_M(x,y) = |x-x_s| + |y-y_s|`
- Distance metric (Chebyshev): `d_C(x,y) = max(|x-x_s|, |y-y_s|)`
- Cell boundary width: `w_boundary = boundary_width / 10 * 0.05` (normalized frame units)
- Color assignment: `hue = (seed_index / seed_count) * 360°` or distance-based gradient
- Edge detection: `is_boundary = gradient_magnitude > threshold`
- Temporal modulation: `color_shift = color_animation * sin(time * animation_speed / 10 * π)`

**Integration Notes**  
The module integrates with the VJLive3 node graph through:
- Input: Video frames via standard VJLive3 frame ingestion pipeline
- Output: Processed frames with Voronoi tessellation maintaining original dimensions
- Parameter Control: All parameters dynamically updatable via set_parameter() method
- Dependency Relationships: Connects to shader_base for distance field and boundary detection

**Performance Characteristics**  
- Processing load scales O(n*m) where n=seed count, m=frame resolution (worst-case)
- GPU acceleration via distance field shader (computes all distances in parallel)
- CPU fallback using NumPy broadcasting for seed-to-pixel distance computation
- Real-time 60fps achievable with 16-32 seeds at 1080p on modern GPU
- Memory usage: O(seeds + frame_pixels), minimal buffering needed
- Latency kept under 16ms for 60fps target via single-pass computation

---

## Public Interface

```python
class VoronoiEffect:
    def __init__(self, frame_width: int, frame_height: int) -> None: ...
    def process_frame(self, input_frame: np.ndarray) -> np.ndarray: ...
    def set_parameter(self, param_name: str, value: float) -> None: ...
    def get_parameter(self, param_name: str) -> float: ...
    def reset(self) -> None: ...
    def stop(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame_width` | `int` | Input frame width in pixels | 64-4096 |
| `frame_height` | `int` | Input frame height in pixels | 64-4096 |
| `input_frame` | `np.ndarray` | RGB frame data (HxWx3) | uint8, 0-255 |
| `seed_count` | `float` | Number of Voronoi seed points | 0.0-10.0 (maps to 4-64) |
| `animation_speed` | `float` | Velocity of seed point motion | 0.0-10.0 |
| `distance_metric` | `float` | Distance function type | 0=Euclidean, 3.33=Manhattan, 6.67=Chebyshev, 10=Custom |
| `boundary_width` | `float` | Cell boundary line thickness | 0.0-10.0 |
| `color_mode` | `float` | Color assignment method | 0=per-cell hash, 5=distance gradient, 10=input sampled |
| `color_animation` | `float` | Temporal color modulation | 0.0-10.0 |
| `saturation` | `float` | Color saturation multiplier | 0.0-10.0 |
| `mix` | `float` | Output mix ratio (Voronoi vs input) | 0.0-1.0 |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → (CPU fallback using NumPy distance computation)
- What happens on bad input? → (raise ValueError with parameter name and valid range)
- What is the cleanup path? → (close() releases GPU resources, __exit__ cleanup)
- What if seed_count is 0? → (raise ValueError: "seed_count must be >= 0.4 (4 seeds minimum)")
- What if frame dimensions are invalid? → (raise ValueError with dimension constraints)

---

## Dependencies

- **External Libraries**: 
  - `numpy` for array operations and distance field computation
  - `scipy.spatial` for KDTree-based seed lookup (optional optimization)
  - `pyopencl` for GPU acceleration (optional)
- **Internal Dependencies**:
  - `vjlive3.core.effects.shader_base` for fundamental shader operations
  - `vjlive3.plugins.vcore.generators.py` for legacy implementation reference

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without GPU; uses CPU fallback |
| `test_basic_operation` | Core Voronoi generation produces valid output with clean input |
| `test_parameter_range_validation` | All parameters clamped to 0.0–10.0; out-of-range values raise ValueError |
| `test_seed_count_effect` | Increasing seed_count increases cell count appropriately |
| `test_animation_smoothness` | Seed positions move continuously without discontinuities |
| `test_distance_metric_euclidean` | Euclidean metric produces symmetric circular boundaries |
| `test_distance_metric_manhattan` | Manhattan metric produces diamond-shaped boundaries |
| `test_distance_metric_chebyshev` | Chebyshev metric produces square-shaped boundaries |
| `test_boundary_detection` | boundary_width parameter correctly thickens cell edges |
| `test_color_mode_per_cell` | Per-cell color mode assigns distinct color to each seed |
| `test_color_mode_distance_gradient` | Distance gradient mode produces smooth color ramps |
| `test_color_animation_temporal` | color_animation induces smooth temporal color shifts |
| `test_saturation_control` | saturation parameter correctly scales color intensity |
| `test_mix_ratio` | mix parameter correctly blends Voronoi pattern with input |
| `test_invalid_frame_size` | Invalid dimensions raise appropriate exceptions |
| `test_nearest_neighbor_correctness` | Each pixel correctly assigned to nearest seed |
| `test_boundary_continuity` | Cell boundaries form continuous edges without gaps |
| `test_legacy_compatibility` | Output matches expected visual characteristics |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-GE09: generators - port from vjlive/plugins/vcore/generators.py` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: Submit creative Easter Egg to `WORKSPACE/EASTEREGG_COUNCIL.md`

---

## LEGACY CODE REFERENCES  
Use these to fill in the spec. These are the REAL implementations:

### vjlive/plugins/vcore/generators.py (L1-20)  
```python
"""
Generator effects — create patterns from scratch.
Voronoi cell-based tessellation with animated seed points.

All parameters use 0.0-10.0 range from UI sliders.
Shaders remap internally to the values the math needs.
Supports Euclidean, Manhattan, Chebyshev distance metrics.
"""
```

### vjlive/plugins/vcore/generators.py (L200-240)  
```glsl
// Hash function for pseudo-random seed colors
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

// Calculate distance to a seed point using selected metric
float compute_distance(vec2 pixel_pos, vec2 seed_pos, int metric) {
    vec2 delta = pixel_pos - seed_pos;
    
    if (metric == 0) {
        // Euclidean distance
        return length(delta);
    } else if (metric == 1) {
        // Manhattan distance
        return abs(delta.x) + abs(delta.y);
    } else {
        // Chebyshev distance
        return max(abs(delta.x), abs(delta.y));
    }
}

// Find nearest seed point and compute Voronoi cell
vec3 eval_voronoi(vec2 uv, vec2 seed_positions[64], int seed_count, int distance_metric) {
    float min_dist = 999999.0;
    int closest_seed = 0;
    
    for (int i = 0; i < MAX_SEEDS; i++) {
        if (i >= seed_count) break;
        float d = compute_distance(uv, seed_positions[i], distance_metric);
        if (d < min_dist) {
            min_dist = d;
            closest_seed = i;
        }
    }
    
    // Return cell ID as color
    float hue = float(closest_seed) / float(seed_count);
    return hsv2rgb(vec3(hue, 1.0, 1.0));
}

// Detect cell boundaries via gradient magnitude
float detect_boundary(vec2 uv, sampler2D voronoi_field, float threshold) {
    vec2 dxdy = vec2(1.0 / resolution.x, 1.0 / resolution.y);
    
    vec3 center = texture(voronoi_field, uv).rgb;
    vec3 dx = texture(voronoi_field, uv + vec2(dxdy.x, 0.0)).rgb;
    vec3 dy = texture(voronoi_field, uv + vec2(0.0, dxdy.y)).rgb;
    
    float grad_x = distance(center, dx);
    float grad_y = distance(center, dy);
    float grad_mag = sqrt(grad_x*grad_x + grad_y*grad_y);
    
    return grad_mag > threshold ? 1.0 : 0.0;
}
```

### vjlive/plugins/vcore/generators.py (L241-280)  
```glsl
void main() {
    vec4 input_color = texture(tex0, uv);
    
    // Update seed positions based on time
    vec2 seed_positions[64];
    int num_seeds = int(ceil(seed_count / 10.0 * 60.0 + 4.0));
    float anim_speed = animation_speed / 10.0 * 5.0;
    
    for (int i = 0; i < MAX_SEEDS; i++) {
        if (i >= num_seeds) break;
        // Pseudo-random seed starting positions + animated offsets
        vec2 base_pos = fract(sin(vec2(i * 73.156, i * 32.891)) * 43758.5453);
        vec2 offset = vec2(cos(time * anim_speed + i * 6.28318 / num_seeds),
                          sin(time * anim_speed + i * 6.28318 / num_seeds)) * 0.3;
        seed_positions[i] = base_pos + offset;
    }
    
    // Map distance metric parameter
    int metric = int(distance_metric / 10.0 * 2.0); // 0, 1, or 2
    
    // Evaluate Voronoi diagram
    vec3 voronoi_color = eval_voronoi(uv, seed_positions, num_seeds, metric);
    
    // Apply boundary detection
    float boundary_thick = boundary_width / 10.0 * 0.05;
    float is_boundary = detect_boundary(uv, tex_voronoi, boundary_thick);
    voronoi_color = mix(voronoi_color, vec3(0.0), is_boundary * 0.8);
    
    // Temporal color animation
    float color_anim = color_animation / 10.0;
    float anim_factor = sin(time * anim_speed * color_anim) * 0.5 + 0.5;
    voronoi_color = mix(voronoi_color, voronoi_color * vec3(anim_factor), color_anim);
    
    // Saturation control
    vec3 hsv = rgb2hsv(voronoi_color);
    hsv.y *= saturation / 10.0 * 2.0;
    voronoi_color = hsv2rgb(hsv);
    
    // Final compositing
    fragColor = mix(input_color, vec4(voronoi_color, 1.0), u_mix);
}
```

### vjlive/plugins/vcore/generators.py (L280-310)  
```python
class VoronoiEffect(Effect):
    """Voronoi diagram generator — cellular tessellation with animated seeds."""

    def __init__(self):
        super().__init__("voronoi", VORONOI_FRAGMENT)
        self.parameters = {
            "seed_count": 5.0,
            "animation_speed": 3.0,
            "distance_metric": 0.0,  # 0=Euclidean
            "boundary_width": 2.0,
            "color_mode": 0.0,       # 0=per-cell
            "color_animation": 0.0,
            "saturation": 5.0,
        }
        self.seed_positions = []
        self.voronoi_field_texture = None
```

---

## Verification Checkpoints

- [ ] Plugin loads successfully via registry
- [ ] All parameters exposed and editable
- [ ] Renders at 60 FPS minimum
- [ ] Test coverage ≥80%
- [ ] No safety rail violations
- [ ] Original functionality verified (side-by-side comparison)
- [ ] Nearest-neighbor correctness mathematically verified
- [ ] Boundary detection produces clean edges

---

**Bespoke Snowflake Principle:** This plugin is unique. Do not batch-process. Give it individual attention and quality.

---

