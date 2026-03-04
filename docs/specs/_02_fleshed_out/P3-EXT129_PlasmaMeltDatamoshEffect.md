# P3-EXT129: PlasmaMeltDatamoshEffect — Fleshed Specification

## Task: P3-EXT129 — PlasmaMeltDatamoshEffect

**Module Type:** Datamosh Effect (Dual-Video Thermodynamic Simulation)  
**Priority:** P0 (Core Datamosh)  
**Phase:** Pass 2 — Fleshed Specification  
**Agent:** desktop-roo  
**Date:** 2026-03-04  

---

## What This Module Does

The `PlasmaMeltDatamoshEffect` is a dual-source datamosh effect that simulates thermodynamic melting between two video inputs. It treats the boundary between Video A and Video B as a physical interface where kinetic energy from A generates heat, causing B's pixels to liquefy and flow like plasma.

**Core Concept:**
- Video A (source) provides motion energy that heats the system
- Video B (target) melts and distorts under thermal stress
- Depth information modulates viscosity: foreground objects drip more dramatically
- The result is a fluid, organic transition between the two video sources

**Key Characteristics:**
- Dual video input: `tex0` (Video A / motion source) and `tex1` (Video B / melt target)
- Depth-aware: optional depth buffer influences viscosity
- Thermodynamic simulation: heat propagation, cooling, and surface tension
- High GPU tier: requires compute-intensive fluid-like calculations
- Real-time performance: optimized for 60fps at 1080p on modern GPUs

---

## What This Module Does NOT Do

- **NOT** a simple crossfade: produces organic, non-linear melting behavior
- **NOT** a traditional fluid simulation: does not solve Navier-Stokes; uses approximate thermal model
- **NOT** depth reconstruction: requires external depth input; does not generate depth from color
- **NOT** a single-source effect: requires two distinct video inputs (though can operate with only `tex0` by using it as both A and B)
- **NOT** a temporal buffer effect: does not store previous frames (all simulation is per-frame or uses external feedback)
- **NOT** a 3D volumetric effect: operates in 2D screen space; depth is a scalar mask

---

## Detailed Behavior and Parameter Interactions

### Core Algorithm

The effect implements a **thermodynamic melting simulation** with the following stages:

1. **Heat Generation** (from Video A)
   - Compute motion magnitude from Video A (frame difference or optical flow)
   - Motion intensity `motion` ∈ [0,1] scales to heat: `heat = motion * u_temperature`
   - Heat accumulates over time (temporal integration)

2. **Viscosity and Flow**
   - Viscosity `viscosity` controls resistance to flow (lower = more fluid)
   - Depth-aware modulation: if depth buffer provided, foreground (low depth) has reduced viscosity
   - Flow direction `flow_direction` (vector) biases the melt direction
   - Turbulence `turbulence` adds Perlin-like noise to flow field

3. **Plasma Distortion**
   - Melted pixels are displaced along the flow field
   - Displacement magnitude inversely proportional to viscosity
   - `plasma_scale` controls the spatial scale of plasma cells
   - `melt_speed` controls how fast pixels flow (time integration factor)

4. **Surface Tension and Crystallization**
   - `surface_tension` pulls melted regions back toward original positions (elasticity)
   - `crystallize` parameter can freeze melted areas back into solid B pixels
   - Balance between melt and crystallize determines steady-state behavior

5. **Color Diffusion and Cross-Contamination**
   - `color_diffusion` controls how much melted colors blend with neighboring pixels
   - Cross-contamination: melted B pixels bleed into A, and vice versa
   - `entropy` parameter increases chaotic mixing

6. **Bubble Formation** (optional)
   - `bubble_rate` spawns circular "bubbles" of pure A or B that rise/fall
   - Bubbles add organic, cellular structure to the melt

7. **Final Composition**
   - Original Video A (if `hasDual` is false) or mixed result
   - `u_mix` controls overall effect strength (0 = original B, 1 = fully melted)

### Parameter Interactions

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `viscosity` | float | [0.01, 1.0] | 0.3 | Fluid resistance; lower = more liquid |
| `temperature` | float | [0.0, 2.0] | 1.0 | Heat generation multiplier from motion |
| `turbulence` | float | [0.0, 1.0] | 0.2 | Flow field noise amplitude |
| `plasma_scale` | float | [1.0, 64.0] | 8.0 | Spatial scale of plasma cells (in pixels) |
| `melt_speed` | float | [0.0, 1.0] | 0.5 | Rate of pixel displacement per second |
| `surface_tension` | float | [0.0, 1.0] | 0.4 | Elastic pull back to original positions |
| `color_diffusion` | float | [0.0, 1.0] | 0.3 | Color bleeding between adjacent pixels |
| `depth_viscosity` | float | [0.0, 2.0] | 1.0 | Multiplier for depth-based viscosity modulation |
| `bubble_rate` | float | [0.0, 1.0] | 0.1 | Frequency of bubble formation |
| `flow_direction` | vec2 | [-1,1] | (0,1) | Preferred flow direction (e.g., downward) |
| `crystallize` | float | [0.0, 1.0] | 0.2 | Tendency to freeze back to solid state |
| `entropy` | float | [0.0, 1.0] | 0.15 | Chaos factor for cross-contamination |

**Parameter Dependencies:**
- `viscosity` and `surface_tension` are opposing forces; high viscosity + high tension = stiff, slow melt
- `temperature` must be >0 to initiate melting; at 0, effect is static
- `melt_speed` should be ≤ 1.0 for stability; >1.0 can cause explosive divergence
- `depth_viscosity` only active if depth buffer is provided; otherwise ignored

### Dual Input Handling

- **`hasDual` flag:** Determines whether `tex1` is used
  - `hasDual = true`: Use both `tex0` (A) and `tex1` (B)
  - `hasDual = false`: Use `tex0` as both A and B (self-melting)
- The shader samples `tex0` for motion/heat and `tex1` for target colors (when `hasDual`)

---

## Public Interface

### Class Definition

```python
from vjlive3.render.effect import Effect
from vjlive3.render.program import RenderPipeline
import numpy as np

class PlasmaMeltDatamoshEffect(Effect):
    """
    Plasma Melt Datamosh — Liquefies boundaries between two video sources.
    
    DUAL VIDEO INPUT: Connect Video A to 'video_in' and Video B to 'video_in_b'.
    Motion from A generates heat that melts B's pixels into flowing plasma.
    
    Depth-aware: foreground objects have lower viscosity and drip more dramatically.
    
    Parameters:
        viscosity (float): Fluid resistance [0.01, 1.0]
        temperature (float): Heat generation multiplier [0.0, 2.0]
        turbulence (float): Flow field noise amplitude [0.0, 1.0]
        plasma_scale (float): Spatial scale of plasma cells [1.0, 64.0]
        melt_speed (float): Displacement rate per second [0.0, 1.0]
        surface_tension (float): Elastic pull to original positions [0.0, 1.0]
        color_diffusion (float): Color bleeding amount [0.0, 1.0]
        depth_viscosity (float): Depth-based viscosity multiplier [0.0, 2.0]
        bubble_rate (float): Bubble formation frequency [0.0, 1.0]
        flow_direction (tuple): Preferred flow direction (dx, dy) ∈ [-1,1]
        crystallize (float): Freezing tendency [0.0, 1.0]
        entropy (float): Chaos factor for mixing [0.0, 1.0]
    """
    
    METADATA = {
        "name": "PlasmaMeltDatamoshEffect",
        "spec": "P3-EXT129",
        "version": "1.0.0",
        "tier": "Pro-Tier Native",
        "category": "datamosh",
        "description": "Dual-source thermodynamic melting with depth-aware viscosity",
        "gpu_tier": "HIGH",
        "inputs": ["tex0", "tex1", "depth_tex (optional)"],
        "outputs": ["fragColor"]
    }
    
    def __init__(self, name: str = "plasma_melt_datamosh") -> None:
        """
        Initialize the PlasmaMeltDatamoshEffect.
        
        Args:
            name: Instance name for the effect (default: "plasma_melt_datamosh")
        """
        fragment_source = self._get_wgsl_shader()
        super().__init__(name, fragment_source)
        
        # Initialize default parameters
        self.parameters = {
            "viscosity": 0.3,
            "temperature": 1.0,
            "turbulence": 0.2,
            "plasma_scale": 8.0,
            "melt_speed": 0.5,
            "surface_tension": 0.4,
            "color_diffusion": 0.3,
            "depth_viscosity": 1.0,
            "bubble_rate": 0.1,
            "flow_direction_x": 0.0,
            "flow_direction_y": 1.0,
            "crystallize": 0.2,
            "entropy": 0.15,
        }
        
        # State for temporal integration (heat accumulation)
        self._heat_state = None
        self._flow_field = None
    
    def _get_wgsl_shader(self) -> str:
        """Return the WGSL shader source code."""
        return """
        @group(0) @binding(0) var tex0: texture_2d<f32>;  // Video A (motion source)
        @group(0) @binding(1) var tex1: texture_2d<f32>;  // Video B (melt target)
        @group(0) @binding(2) var s0: sampler;
        @group(0) @binding(3) var depth_tex: texture_2d<f32>;  // Optional depth
        @group(0) @binding(4) var depth_sampler: sampler;
        
        struct Uniforms {
            viscosity: f32,
            temperature: f32,
            turbulence: f32,
            plasma_scale: f32,
            melt_speed: f32,
            surface_tension: f32,
            color_diffusion: f32,
            depth_viscosity: f32,
            bubble_rate: f32,
            flow_dir_x: f32,
            flow_dir_y: f32,
            crystallize: f32,
            entropy: f32,
            mix: f32,
            enabled: f32,
            has_dual: f32,
            time: f32,
        };
        
        @binding(5) @group(0) var<uniform> uniforms: Uniforms;
        
        // Pseudo-random function for turbulence
        fn hash(p: vec2<f32>) -> f32 {
            var p2 = fract(p * vec2<f32>(123.45, 678.91));
            p2 += dot(p2, p2 + 45.67);
            return fract(p2.x * p2.y);
        }
        
        // Value noise for flow field
        fn noise(uv: vec2<f32>) -> f32 {
            let i = floor(uv);
            let f = fract(uv);
            let a = hash(i);
            let b = hash(i + vec2<f32>(1.0, 0.0));
            let c = hash(i + vec2<f32>(0.0, 1.0));
            let d = hash(i + vec2<f32>(1.0, 1.0));
            let u = f * f * (3.0 - 2.0 * f);
            return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
        }
        
        @fragment
        fn main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
            // Sample current colors
            let currA = textureSample(tex0, s0, uv);
            let currB = textureSample(tex1, s0, uv);
            
            // Compute motion from Video A (simple frame difference)
            // In practice, this would come from a separate motion buffer
            let motion = length(currA.rgb - currB.rgb);  // Simplified
            
            // Generate heat from motion
            var heat = motion * uniforms.temperature;
            
            // Temporal heat accumulation would be stored in a separate texture
            // For this shader, we use per-pixel approximation
            let noise_val = noise(uv * uniforms.plasma_scale + uniforms.time * 0.1);
            heat += noise_val * uniforms.turbulence;
            
            // Depth-aware viscosity
            var visc = uniforms.viscosity;
            if (uniforms.depth_viscosity > 0.0) {
                let depth = textureSample(depth_tex, depth_sampler, uv).r;
                // Foreground (low depth) = less viscous (more drip)
                visc = max(0.01, visc - depth * uniforms.depth_viscosity);
            }
            
            // Flow direction
            let flow = vec2<f32>(uniforms.flow_dir_x, uniforms.flow_dir_y);
            
            // Compute displacement based on heat and viscosity
            let displacement = (heat / visc) * uniforms.melt_speed * 0.01;
            let offset = flow * displacement;
            
            // Sample melted B with offset
            var melted = textureSample(tex1, s0, uv + offset);
            
            // Cross-contamination: A's colors bleed into melted B
            let contamination = heat * uniforms.entropy * 0.3;
            melted.rgb = mix(melted.rgb, currA.rgb, contamination * 0.2);
            
            // Surface tension: pull back toward original B
            melted.rgb = mix(melted.rgb, currB.rgb, uniforms.surface_tension);
            
            // Color diffusion (simple blur would be better but costly)
            // Here we approximate with a 3-tap kernel
            if (uniforms.color_diffusion > 0.0) {
                let du = vec2<f32>(1.0/1920.0, 0.0);  // Assume 1920px width
                let dv = vec2<f32>(0.0, 1.0/1080.0);
                let c0 = textureSample(tex1, s0, uv);
                let c1 = textureSample(tex1, s0, uv + du);
                let c2 = textureSample(tex1, s0, uv - du);
                let c3 = textureSample(tex1, s0, uv + dv);
                let c4 = textureSample(tex1, s0, uv - dv);
                let blurred = (c0 + c1 + c2 + c3 + c4) / 5.0;
                melted.rgb = mix(melted.rgb, blurred, uniforms.color_diffusion);
            }
            
            // Bubble formation (simple circular blobs)
            if (uniforms.bubble_rate > 0.0) {
                let bubble_noise = noise(uv * 20.0 + uniforms.time);
                if (bubble_noise < uniforms.bubble_rate * 0.1) {
                    // Bubble: sample from A with brightening
                    let bubble = textureSample(tex0, s0, uv);
                    melted.rgb = mix(melted.rgb, bubble.rgb * 1.2, 0.5);
                }
            }
            
            // Crystallization: freeze back to B
            let freeze = uniforms.crystallize * (1.0 - heat);
            let final = mix(melted, currB, freeze);
            
            // Final mix with original (if hasDual, use B as original; else use A)
            let original = uniforms.has_dual > 0.5 ? currB : currA;
            let output = mix(original, final, uniforms.mix);
            
            return output;
        }
        """
    
    def apply_uniforms(self, pipeline: RenderPipeline) -> None:
        """
        Upload current parameter values to the GPU pipeline.
        
        Args:
            pipeline: RenderPipeline instance to update
        """
        pipeline.set_uniform("viscosity", self.parameters["viscosity"])
        pipeline.set_uniform("temperature", self.parameters["temperature"])
        pipeline.set_uniform("turbulence", self.parameters["turbulence"])
        pipeline.set_uniform("plasma_scale", self.parameters["plasma_scale"])
        pipeline.set_uniform("melt_speed", self.parameters["melt_speed"])
        pipeline.set_uniform("surface_tension", self.parameters["surface_tension"])
        pipeline.set_uniform("color_diffusion", self.parameters["color_diffusion"])
        pipeline.set_uniform("depth_viscosity", self.parameters["depth_viscosity"])
        pipeline.set_uniform("bubble_rate", self.parameters["bubble_rate"])
        pipeline.set_uniform("flow_dir_x", self.parameters["flow_direction_x"])
        pipeline.set_uniform("flow_dir_y", self.parameters["flow_direction_y"])
        pipeline.set_uniform("crystallize", self.parameters["crystallize"])
        pipeline.set_uniform("entropy", self.parameters["entropy"])
        # mix, enabled, has_dual, time are managed by base class or external
    
    def set_dual_input(self, has_dual: bool) -> None:
        """
        Configure whether to use dual video inputs.
        
        Args:
            has_dual: True to use both tex0 and tex1; False to self-melt using tex0
        """
        # This would set a uniform; actual implementation depends on base class
        self.parameters["has_dual"] = 1.0 if has_dual else 0.0
```

### Integration with VJLive3

- Inherits from [`Effect`](src/vjlive3/render/effect.py) base class
- Uses [`RenderPipeline`](src/vjlive3/render/program.py) for WGSL compilation
- Requires **two video input bindings** (`tex0`, `tex1`) and optionally a depth texture
- Parameters are exposed via `self.parameters` dict for GUI binding
- `apply_uniforms()` uploads all 12+ parameters each frame
- Compatible with effect chaining via [`Chain`](src/vjlive3/render/chain.py)

### Texture Binding Layout

| Binding | Type | Purpose |
|---------|------|---------|
| 0 | `texture_2d<f32>` | Video A (motion source) |
| 1 | `texture_2d<f32>` | Video B (melt target) |
| 2 | `sampler` | Sampler for both textures (shared) |
| 3 | `texture_2d<f32>` | Optional depth buffer (if available) |
| 4 | `sampler` | Depth sampler |
| 5 | `uniform` | Uniforms buffer |

---

## Inputs and Outputs

### Inputs

| Stream | Type | Description |
|--------|------|-------------|
| `tex0` | `texture_2d<f32>` | Video A — provides motion energy for heat |
| `tex1` | `texture_2d<f32>` | Video B — target that melts |
| `depth_tex` (optional) | `texture_2d<f32>` | Depth buffer; modulates viscosity by depth |
| Uniforms | `Uniforms` struct | 16+ parameters (see table above) |

### Outputs

| Stream | Type | Description |
|--------|------|-------------|
| Fragment output | `vec4<f32>` | RGBA color with plasma melt applied |

### Data Flow

1. Both input textures bound to fragment shader
2. Motion computed from difference between `tex0` and `tex1` (or from external motion buffer)
3. Heat generated and combined with turbulence noise
4. Viscosity adjusted by depth if depth texture provided
5. Flow field computed from `flow_direction` and heat
6. Displacement applied to `tex1` samples
7. Cross-contamination blends in `tex0` colors
8. Surface tension and crystallization modify result
9. Final `mix` blends with original (B if dual, else A)
10. Output written to framebuffer

---

## Edge Cases and Error Handling

### Missing Dual Input

- **Scenario:** `hasDual = true` but `tex1` is not bound (null texture)
- **Behavior:** Shader should sample `tex0` as fallback; or engine should ensure valid texture bound
- **Mitigation:** Python-side validation in `apply_uniforms()` checks that required textures are present

### Depth Texture Absent

- **Scenario:** `depth_viscosity > 0` but no depth texture bound
- **Behavior:** Shader treats missing depth as 0 (no viscosity modulation) or 1 (full effect)? Should default to 0 (no modulation) to avoid unexpected behavior.
- **Mitigation:** Document that depth is optional; if `depth_viscosity` is nonzero, depth texture should be provided.

### Extreme Parameter Values

- **`viscosity` too low (<0.01):** Can cause explosive displacement (divergence). Clamp to 0.01 minimum.
- **`melt_speed` too high (>1.0):** Can cause pixel skipping and instability. Clamp to 1.0.
- **`temperature` = 0:** No heat generation; effect becomes static (only turbulence and bubbles move). Valid but may be confusing.
- **`entropy` = 1:** Maximum cross-contamination; output may become noisy and lose source identity.

### Temporal Consistency

- **Risk:** The shader as written uses per-pixel noise without state; heat does not persist across frames. This may cause flickering.
- **Mitigation:** In production, heat should be stored in a separate framebuffer (ping-pong) and accumulated over time. The spec should note this as a **future enhancement**.
- **Current behavior:** Approximate heat from current frame only; effect is mostly static per-frame with noise-driven variation.

### Flow Direction Normalization

- **Risk:** `flow_direction` could be (0,0) causing no displacement.
- **Mitigation:** Document that non-zero flow is recommended; could auto-normalize to unit vector if magnitude > 1.

### Bubble Artifacts

- **Risk:** `bubble_rate` too high creates excessive bright spots, resembling snow noise.
- **Mitigation:** Clamp `bubble_rate` to [0, 0.5] reasonable range; default 0.1 is safe.

---

## Mathematical Formulations

### Heat Generation

```
motion = length(tex0.rgb - tex1.rgb)  // L2 norm of color difference
heat = motion * temperature + turbulence * noise(uv * plasma_scale + time)
```

### Viscosity Modulation with Depth

```
if depth_tex provided:
    depth = depth_tex.r  // Assume linear depth [0,1] (0 = near, 1 = far)
    effective_viscosity = max(0.01, viscosity - depth * depth_viscosity)
else:
    effective_viscosity = viscosity
```

### Displacement

```
flow = normalize(flow_direction)  // unit vector
displacement_magnitude = (heat / effective_viscosity) * melt_speed * scale_factor
offset = flow * displacement_magnitude
```

Where `scale_factor` is a small constant (e.g., 0.01) to keep displacements in UV space.

### Cross-Contamination

```
contamination = heat * entropy * 0.3
melted.rgb = mix(melted.rgb, tex0.rgb, contamination * 0.2)
```

### Surface Tension

```
tension_factor = surface_tension
melted.rgb = mix(melted.rgb, tex1.rgb, tension_factor)
```

### Crystallization

```
freeze = crystallize * (1.0 - heat)
final = mix(melted, tex1.rgb, freeze)
```

### Color Diffusion (5-tap box blur approximation)

```
if color_diffusion > 0:
    blurred = (center + left + right + up + down) / 5.0
    melted.rgb = mix(melted.rgb, blurred, color_diffusion)
```

### Final Composition

```
original = has_dual ? tex1.rgb : tex0.rgb
output = mix(original, final, mix_factor)
```

---

## Performance Characteristics

### Computational Complexity

- **Per-fragment operations:**
  - 4 texture samples (tex0, tex1, depth optional, plus 5 for diffusion if enabled)
  - 2 `length()` calls (color difference, flow normalization)
  - 2 `noise()` calls (each ~20 ops)
  - Multiple `mix()` operations (6-8)
  - Arithmetic: ~50-100 FLOPs per fragment
- **Memory bandwidth:** 4-6 texture fetches per fragment (worst-case with diffusion and depth)
- **Uniforms:** 16 floats = 64 bytes per draw call

### GPU Utilization

- **Fragment-bound:** Heavy fragment shader; performance scales with resolution
- **Texture bandwidth:** High due to multiple samples; may be bottleneck on integrated GPUs
- **No vertex processing:** Standard full-screen quad
- **No compute shader:** Could be optimized with compute for larger kernels, but fragment is simpler

### Optimization Opportunities

- **Reduce texture samples:** Diffusion could be done with 3-tap separable blur (horizontal + vertical passes) but requires multi-pass
- **Pre-compute noise:** Use a 3D noise texture instead of procedural hash to reduce ALU
- **Lower resolution simulation:** Render heat/flow at half-resolution and upscale
- **Temporal reprojection:** Reuse previous frame's displacement to reduce per-frame computation

### Benchmarks (Estimated)

| Resolution | Texture Samples | Relative Cost | Target FPS (RTX 3060) |
|------------|----------------|---------------|----------------------|
| 1920×1080  | 4 (no diffusion) | 1.0× | 60+ fps |
| 1920×1080  | 6 (with diffusion) | 1.3× | 50-60 fps |
| 3840×2160  | 4 | 2.0× | 30-40 fps |
| 1920×1080  | 6 + depth | 1.5× | 45-55 fps |

These are rough estimates; actual performance depends on GPU and driver.

---

## Test Plan

### Unit Tests (Python)

1. **Parameter Validation**
   - Test all parameters clamp to valid ranges
   - Test default values are within spec
   - Test `set_dual_input()` sets `has_dual` correctly

2. **Shader Compilation**
   - Verify WGSL source compiles without errors
   - Test that all uniform locations are valid

3. **Uniform Upload**
   - Mock `RenderPipeline.set_uniform()` and verify all parameters uploaded
   - Test that `apply_uniforms()` handles all 12+ parameters

4. **Metadata**
   - Verify `METADATA` contains required keys and correct `spec` ID

### Integration Tests (Render)

1. **Dual Input Basic**
   - Create two test textures (A: moving gradient, B: static color)
   - Set `has_dual=True`, `temperature=1.0`, `viscosity=0.3`
   - Verify output shows B distorted by motion from A
   - Check that displacement direction matches `flow_direction`

2. **Self-Melting**
   - Set `has_dual=False` (use tex0 as both A and B)
   - Verify effect still produces melting (self-motion generates heat)

3. **Depth Modulation**
   - Provide a depth texture (gradient from 0 to 1)
   - Set `depth_viscosity=1.0`
   - Verify that foreground (low depth) melts more than background

4. **Parameter Sweeps**
   - Vary `viscosity` from 0.01 to 1.0: observe flow smoothness
   - Vary `temperature` from 0 to 2: observe heat intensity
   - Vary `turbulence`: observe noise in flow field
   - Vary `bubble_rate`: observe bubble density

5. **Edge Cases**
   - `temperature=0`: verify static behavior (only noise moves)
   - `viscosity=0.01`: verify extreme fluidity (may need clamp)
   - `has_dual=False` with identical A and B: should produce no motion (heat=0)

6. **Chain Integration**
   - Insert effect into a `Chain` with preceding and following effects
   - Verify correct texture binding and output

### Visual Regression

- Render a standard test sequence (e.g., moving color bars) with fixed parameters
- Compare against golden video sequence (per-frame SSIM > 0.95)
- Store reference in `tests/reference/P3-EXT129/`

### Performance Tests

- Measure frame time at 1920×1080 with all parameters at default
- Ensure sustained 60fps on target hardware (RTX 3060 or equivalent)
- Profile texture fetch count and shader occupancy

---

## Definition of Done

- [x] Spec document completed in `docs/specs/_02_fleshed_out/P3-EXT129_PlasmaMeltDatamoshEffect.md`
- [ ] WGSL shader implemented in `src/vjlive3/plugins/plasma_melt_datamosh.py`
- [ ] Python class `PlasmaMeltDatamoshEffect` with full parameter set
- [ ] Dual input handling (`tex0`, `tex1`) and optional depth support
- [ ] All unit tests passing (`tests/plugins/test_plasma_melt_datamosh.py`)
- [ ] All integration tests passing (render tests with dual inputs)
- [ ] Code coverage ≥ 80%
- [ ] No linter errors (`ruff`, `mypy`)
- [ ] Performance: 60fps at 1920×1080 on target GPU
- [ ] Spec reviewed and approved by Manager

---

## Legacy References

### VJlive (Original) — `plugins/vdatamosh/plasma_melt_datamosh.py`

```python
class PlasmaMeltDatamoshEffect(Effect):
    """
    Plasma Melt Datamosh — Liquefies boundaries between two video sources.
    
    DUAL VIDEO INPUT: Connect Video A to 'video_in' and Video B to 'video_in_b'.
    Motion from A generates heat that melts B's pixels into flowing plasma.
    
    Depth-aware: foreground objects have lower viscosity and drip more dramatically.
```

The legacy implementation included a WGSL/GLSL shader (snippet shown in lookup) with:
- Heat calculation from motion
- Cross-contamination between sources
- Final mix with `u_mix`

**Parameters from test file:**
```python
['viscosity', 'temperature', 'turbulence', 'plasma_scale',
 'melt_speed', 'surface_tension', 'color_diffusion', 'depth_viscosity',
 'bubble_rate', 'flow_direction', 'crystallize', 'entropy']
```

### VJlive-2 (Legacy) — `plugins/core/plasma_melt_datamosh/__init__.py`

Same class structure and shader as above. The plugin manifest (`plugin.json`) indicates:
- Category: Datamosh
- GPU tier: MEDIUM (VJLive3 spec upgrades to HIGH due to added features)
- Description: "Kinetic energy from Video A thermally melts Video B into a highly viscous, depth-aware plasma fluid simulation."

### Migration Notes

- **Shader language:** Legacy likely used GLSL; VJLive3 uses WGSL. The algorithm translates with minor syntax changes.
- **Temporal state:** Legacy may have used a feedback framebuffer for heat accumulation. The VJLive3 spec should eventually incorporate a ping-pong framebuffer for persistent heat. Current implementation uses per-frame approximation.
- **Depth handling:** Legacy mentions depth-aware viscosity; our spec includes `depth_tex` binding to support this.
- **Parameter mapping:** Direct 1:1 mapping; parameter names and ranges preserved from legacy tests.

---

## Technical Notes for Implementation

### Motion Estimation

The shader currently uses `length(currA - currB)` as a proxy for motion. This is simplistic and can be noisy. Better approaches:
- Use an external optical flow buffer (from `OpticalFlowEffect`) as input
- Use frame difference with thresholding
- Use luma-only motion: `abs(luma(A) - luma(B))`

### Temporal Heat Accumulation

For a more realistic simulation, heat should persist across frames:
- Allocate a `heat_tex` framebuffer (same size as output)
- Each frame: read previous heat, decay by `(1 - cooling_rate)`, add new heat from motion
- Write new heat back to `heat_tex` for next frame
- This requires multi-pass rendering or compute shader

### Diffusion Optimization

The 5-tap blur in the shader is a simple approximation. A separable blur (horizontal then vertical) would be cheaper:
- Pass 1: horizontal blur to intermediate texture
- Pass 2: vertical blur from intermediate to final
- But this adds render passes; the current single-pass approach is simpler.

### Depth Coordinate Space

Depth texture should match screen UVs. If depth comes from a camera with different resolution, it must be upsampled/downsampled to match screen size. The effect assumes depth is already in screen space.

---
-

## References

- [`Effect` base class](src/vjlive3/render/effect.py)
- [`RenderPipeline`](src/vjlive3/render/program.py)
- [`Chain`](src/vjlive3/render/chain.py)
- Legacy: `plugins/vdatamosh/plasma_melt_datamosh.py` (VJlive)
- Legacy: `plugins/core/plasma_melt_datamosh/__init__.py` (VJlive-2)
- Legacy test: `tests/test_datamosh_dual_input.py`
- BOARD.md task entry: P3-EXT129

---

**Specification Status:** ✅ Fleshed — Ready for Implementation (Pass 3)
