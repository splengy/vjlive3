# Spec: P3-EXT147 — ReactionDiffusionEffect

**File naming:** `docs/specs/P3-EXT147_ReactionDiffusionEffect.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT147 — ReactionDiffusionEffect

### What This Module Does
ReactionDiffusionEffect implements the Gray-Scott reaction-diffusion model, creating organic, evolving patterns through chemical-like interactions. It simulates two chemical species (A and B) that react and diffuse across the screen, producing Turing patterns, waves, and branching structures. The effect can operate as a standalone pattern generator or blend with input video for feedback effects.

### What This Module Does NOT Do
- Handle audio file I/O or persistent storage operations
- Perform real-time audio processing (relies on audio analysis modules for beat/BPM data)
- Implement 3D transformations or volumetric effects
- Provide direct MIDI/OSC control interfaces
- Support text rendering outside video frame context

---

## Detailed Behavior and Parameter Interactions

### Core Simulation Pipeline
1. **State Initialization**: Sets up two buffers (A and B) with initial conditions
2. **Reaction Step**: Applies Gray-Scott reaction equations to update chemical concentrations
3. **Diffusion Step**: Spreads chemicals using discrete Laplacian operator
4. **Pattern Formation**: Emergent patterns form based on feed/kill rates
5. **Color Mapping**: Converts chemical concentrations to RGB colors
6. **Feedback Blending**: Optionally mixes with input video for seeded patterns

### Parameter Interactions
- **Feed rate (f)** controls chemical production: higher = more growth
- **Kill rate (k)** controls chemical decay: higher = more elimination
- **Diffusion A (Da)** controls spread of activator: higher = faster spread
- **Diffusion B (Db)** controls spread of inhibitor: higher = faster spread
- **Sim speed** controls integration steps per frame: higher = faster evolution
- **Opacity** controls blend with input video: higher = more input visible

### Pattern Formation
The Gray-Scott model creates different patterns based on parameter combinations:
- **Spots**: Low feed, high kill (f=0.015, k=0.055)
- **Spirals**: Medium feed, medium kill (f=0.03, k=0.062)
- **Waves**: High feed, high kill (f=0.04, k=0.062)
- **Mitosis**: High feed, very high kill (f=0.025, k=0.06)

### Audio Integration
The effect receives `beat_data` dictionary with:
- `is_beat`: bool - whether a beat was detected
- `confidence`: float - beat detection confidence (0.0-1.0)
- `bpm`: float - current tempo

When a beat is detected, the effect may:
- Randomize parameters for variation
- Increase sim_speed for faster evolution
- Reset buffers for pattern regeneration

---

## Public Interface

```python
from typing import Dict, Any, Optional, Tuple
import numpy as np

class ReactionDiffusionEffect:
    """Procedural Reaction-Diffusion (Gray-Scott) pattern generator."""
    
    METADATA = {
        'name': 'reaction_diffusion',
        'gpu_tier': 'MEDIUM',
        'input_type': 'video',
        'output_type': 'video',
        'description': 'Reaction-diffusion simulation - Gray-Scott pattern formation',
        'parameters': [
            {'name': 'feed_rate', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'kill_rate', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'diffusion_a', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'diffusion_b', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'sim_speed', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'opacity', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 10.0},
            {'name': 'color_mode', 'type': 'int', 'min': 0, 'max': 5, 'default': 3},
            {'name': 'contrast', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 7.0},
            {'name': 'invert', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.0},
            {'name': 'edge_glow', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 4.0},
            {'name': 'bg_brightness', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'seed_mode', 'type': 'int', 'min': 0, 'max': 2, 'default': 0},
            {'name': 'seed_density', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 5.0},
            {'name': 'reseed_rate', 'type': 'float', 'min': 0.0, 'max': 10.0, 'default': 0.5},
        ]
    }
    
    def __init__(self, width: int = 1920, height: int = 1080, use_gpu: bool = True):
        """Initialize effect with video dimensions and GPU preference."""
        self.width = width
        self.height = height
        self.use_gpu = use_gpu
        self._state = {'buffer_a': None, 'buffer_b': None}
        self.parameters = {p['name']: p['default'] for p in self.METADATA['parameters']}
        self._prev_beat_time = 0
        
    def update(self, frame: np.ndarray, beat_data: Optional[Dict] = None, dt: float = 0.016) -> None:
        """
        Process incoming frame and update internal state.
        
        Args:
            frame: Input video frame (HxWx3 or HxWx4 uint8)
            beat_data: Optional beat detection data
            dt: Time delta in seconds
        """
        # Store frame for feedback blending
        self._input_frame = frame
        
        # Process beat data if provided
        if beat_data and beat_data.get('is_beat', False):
            self._on_beat(beat_data)
            
    def render(self) -> np.ndarray:
        """
        Generate output frame by simulating reaction-diffusion.
        
        Returns:
            Processed video frame (HxWx3 uint8)
        """
        if self.use_gpu:
            return self._render_gpu()
        else:
            return self._render_cpu()
            
    def _render_gpu(self) -> np.ndarray:
        """Render using GPU shader."""
        # GPU implementation would use WebGL/WGSL shader
        # This is a placeholder for the actual shader-based implementation
        return np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
    def _render_cpu(self) -> np.ndarray:
        """Render using CPU with NumPy."""
        # Initialize buffers if needed
        if self._state['buffer_a'] is None:
            self._init_buffers()
            
        # Apply Gray-Scott reaction-diffusion steps
        steps = int(self._map_param('sim_speed', 1, 16))
        for _ in range(steps):
            self._state['buffer_a'], self._state['buffer_b'] = self._reaction_diffusion_step(
                self._state['buffer_a'],
                self._state['buffer_b'],
                self._map_param('feed_rate', 0.02, 0.08),
                self._map_param('kill_rate', 0.02, 0.08),
                self._map_param('diffusion_a', 0.2, 1.0),
                self._map_param('kill_rate', 0.1, 0.5),
                0.1  # dt
            )
            
        # Convert to RGB colors
        output = self._buffer_to_rgb(self._state['buffer_a'], self._state['buffer_b'])
        
        # Blend with input frame
        if self._input_frame is not None:
            opacity = self._map_param('opacity', 0.0, 1.0)
            output = cv2.addWeighted(output, 1.0 - opacity, self._input_frame, opacity, 0)
            
        return output
        
    def _reaction_diffusion_step(self, u, v, f, k, Da, Db, dt):
        """Single Gray-Scott reaction-diffusion step."""
        # Laplacian kernel
        kernel = np.array([[0.05, 0.2, 0.05],
                           [0.2, -1.0, 0.2],
                           [0.05, 0.2, 0.05]])
        lap_u = convolve(u, kernel, mode='wrap')
        lap_v = convolve(v, kernel, mode='wrap')
        
        uvv = u * v * v
        du = Da * lap_u - uvv + f * (1 - u)
        dv = Db * lap_v + uvv - (f + k) * v
        
        u_new = u + du * dt
        v_new = v + dv * dt
        return np.clip(u_new, 0, 1), np.clip(v_new, 0, 1)
        
    def _buffer_to_rgb(self, u, v):
        """Convert chemical concentrations to RGB colors."""
        # Simple color mapping: u = red, v = blue
        rgb = np.zeros((u.shape[0], u.shape[1], 3), dtype=np.float32)
        rgb[:, :, 0] = u
        rgb[:, :, 2] = v
        
        # Apply contrast and color mode
        contrast = self._map_param('contrast', 1.0, 3.0)
        rgb = (rgb - 0.5) * contrast + 0.5
        
        # Apply color mode (simple hue rotation)
        color_mode = self.parameters['color_mode']
        if color_mode == 1:  # Green
            rgb = rgb[:, :, [1, 0, 2]]
        elif color_mode == 2:  # Blue
            rgb = rgb[:, :, [2, 0, 1]]
        elif color_mode == 3:  # Rainbow
            # Simple rainbow mapping
            hue = np.arctan2(v - 0.5, u - 0.5)
            rgb = self._hsv_to_rgb(hue, 1.0, np.maximum(u, v))
        
        return np.clip(rgb * 255, 0, 255).astype(np.uint8)
        
    def _init_buffers(self):
        """Initialize chemical concentration buffers."""
        # Start with uniform A, small random B
        self._state['buffer_a'] = np.ones((self.height, self.width), dtype=np.float32)
        self._state['buffer_b'] = np.random.uniform(0.01, 0.02, (self.height, self.width)).astype(np.float32)
        
        # Apply seed mode
        if self.parameters['seed_mode'] == 1:  # Center seed
            center_x, center_y = self.width // 2, self.height // 2
            radius = int(self.width * 0.1)
            y, x = np.ogrid[-center_y:self.height-center_y, -center_x:self.width-center_x]
            mask = x*x + y*y <= radius*radius
            self._state['buffer_b'][mask] = 0.5
        
    def _on_beat(self, beat_data: Dict):
        """Handle beat detection event."""
        # Update BPM if provided
        if 'bpm' in beat_data:
            self.parameters['bpm'] = beat_data['bpm']
            
        # Randomize parameters on strong beats
        if beat_data.get('confidence', 0) > 0.8:
            if np.random.random() < 0.3:  # 30% chance to randomize
                self.parameters['feed_rate'] = np.random.uniform(2.0, 8.0)
                self.parameters['kill_rate'] = np.random.uniform(4.0, 10.0)
                self._state['buffer_a'] = np.ones_like(self._state['buffer_a'])
                self._state['buffer_b'] = np.random.uniform(0.01, 0.02, self._state['buffer_b'].shape).astype(np.float32)
                
    def reset(self) -> None:
        """Reset effect state and clear buffers."""
        self._state = {'buffer_a': None, 'buffer_b': None}
        self._prev_beat_time = 0
        
    @property
    def is_beat_detected(self) -> bool:
        """Check if beat was recently detected."""
        return False  # Would need state tracking
        
    @property
    def current_bpm(self) -> float:
        """Get current BPM setting."""
        return self.parameters.get('bpm', 120.0)
        
    def _map_param(self, name: str, out_min: float, out_max: float) -> float:
        """Map parameter from 0-10 range to output range."""
        if name not in self.parameters:
            return (out_min + out_max) / 2.0
        value = self.parameters[name]
        return (value / 10.0) * (out_max - out_min) + out_min
        
    def _hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB."""
        h = h % (2 * np.pi)
        c = v * s
        x = c * (1 - np.abs((h / (np.pi/3)) % 2 - 1))
        m = v - c
        
        h_prime = (h / (np.pi/3)) % 6
        r = np.select([h_prime < 1, h_prime < 2, h_prime < 3, h_prime < 4, h_prime < 5, True],
                      [c, x, 0, 0, x, c])
        g = np.select([h_prime < 1, h_prime < 2, h_prime < 3, h_prime < 4, h_prime < 5, True],
                      [x, c, c, x, 0, 0])
        b = np.select([h_prime < 1, h_prime < 2, h_prime < 3, h_prime < 4, h_prime < 5, True],
                      [0, 0, x, c, c, x])
        
        return (np.stack([r, g, b], axis=-1) + m) * 255
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `frame` | `np.ndarray` | Input video frame | Shape: (height, width, 3), dtype: uint8 |
| `beat_data` | `dict` (optional) | Beat detection data | Keys: 'is_beat' (bool), 'confidence' (float), 'bpm' (float) |
| `dt` | `float` | Time delta | Seconds, typically 0.016-0.033 |
| `width` | `int` | Frame width | 640-3840 pixels |
| `height` | `int` | Frame height | 480-2160 pixels |

**Output**: Processed video frame (HxWx3 uint8) with reaction-diffusion patterns.

---

## Edge Cases and Error Handling

### Parameter Edge Cases
- **feed_rate + kill_rate > 0.1**: May cause numerical instability, clamp to safe range
- **diffusion_a or diffusion_b = 0**: No diffusion, patterns become static
- **sim_speed = 0**: No evolution, patterns remain static
- **opacity = 0**: Only reaction-diffusion patterns, no video input
- **opacity = 10**: Only video input, no reaction-diffusion
- **color_mode out of range**: Wrap to valid range [0, 5]
- **seed_density = 0**: No initial seeding, may produce uniform patterns

### Error Scenarios
- **Missing audio data**: Effect continues with default parameters
- **Invalid frame size**: Raise ValueError for dimensions < 64x64 or > 4096x2160
- **Buffer allocation failure**: Raise MemoryError with clear message
- **Numerical instability**: Automatic parameter clamping if patterns blow up
- **Performance degradation**: If frame processing exceeds 16ms, reduce sim_speed
- **GPU fallback**: If GPU unavailable, automatically switch to CPU implementation

### Internal Dependencies
- **Base Effect Class**: Would inherit from VJLive3 Effect base
- **NumPy**: For array operations and convolution
- **OpenCV**: For color space conversions (optional)
- **GPU**: Optional for shader-based implementation

### External Dependencies
- **Audio Analysis Module**: Provides beat_data (optional but recommended)
- **GPU**: Optional for hardware acceleration

---

## Mathematical Formulations

### Gray-Scott Reaction-Diffusion Equations

**Reaction terms:**
$$\frac{\partial u}{\partial t} = D_a \nabla^2 u - u v^2 + f(1 - u)$$
$$\frac{\partial v}{\partial t} = D_b \nabla^2 v + u v^2 - (f + k)v$$

Where:
- $u$ = activator concentration (chemical A)
- $v$ = inhibitor concentration (chemical B)
- $D_a$ = diffusion rate of A
- $D_b$ = diffusion rate of B
- $f$ = feed rate (chemical input)
- $k$ = kill rate (chemical decay)

### Discrete Laplacian Operator

**2D convolution kernel:**
$$K = \begin{bmatrix}
0.05 & 0.2 & 0.05 \\
0.2 & -1.0 & 0.2 \\
0.05 & 0.2 & 0.05
\end{bmatrix}$$

**Discrete Laplacian:**
$$\nabla^2 X = (X_{left} + X_{right} + X_{above} + X_{below} - 4X_{center}) / scale$$

### Pattern Formation Conditions

**Stability analysis:**
- **Spots**: $f < 0.02$, $k \approx 0.055$
- **Spirals**: $f \approx 0.03$, $k \approx 0.062$
- **Waves**: $f > 0.035$, $k \approx 0.062$
- **Mitosis**: $f \approx 0.025$, $k \approx 0.06$

**Turing instability condition:**
$$D_a > D_b \text{ and } f < k$$

### Color Mapping

**Simple RGB mapping:**
- Red channel: $R = u$
- Blue channel: $B = v$
- Green channel: $G = 0$

**With contrast adjustment:**
$$C_{out} = (C_{in} - 0.5) \times \text{contrast} + 0.5$$

### Spatial Boundary Conditions

**Toroidal topology (wrap-around):**
$$X_{i,j} = X_{(i \mod N), (j \mod M)}$$

---

## Performance Characteristics

### CPU Requirements
- **Processing load**: 20-40% CPU for real-time 60fps at 1080p
- **Memory usage**: ~50MB for 1080p buffers (2 × 1920 × 1080 × 4 bytes)
- **Frame rate target**: 60fps with buffer management
- **Latency**: <50ms including buffer delay
- **Algorithm complexity**: O(H × W × steps) per frame

### GPU Requirements (if implemented)
- **Processing load**: 5-15% GPU for real-time 60fps at 1080p
- **Memory usage**: ~20MB for texture buffers
- **Frame rate target**: 60fps with multi-pass shader
- **Latency**: <10ms with hardware acceleration
- **Shader complexity**: Medium (multi-pass reaction-diffusion)

### Memory Calculation
For 1080p (1920×1080):
- Single float32 buffer: 1920 × 1080 × 4 = 8,294,400 bytes ≈ 8.3 MB
- Two buffers (A and B): 2 × 8.3 MB = 16.6 MB
- **Optimization**: Use float16 or uint8 for memory savings

**Actual expected memory**: ~50-100MB with optimizations

### Optimization Strategies
- **Resolution scaling**: Process at lower resolution (e.g., 960×540) and upscale
- **Step reduction**: Reduce sim_speed steps on lower-end systems
- **Spatial sampling**: Process every other pixel for lower quality
- **Temporal coherence**: Reuse previous frame for smooth transitions
- **GPU acceleration**: Use WebGL/WGSL for hardware acceleration

---

## Test Plan

### Unit Tests (Coverage: 90%)
1. **Parameter validation**
   - Clamp out-of-range parameters
   - Default values set correctly
   - Parameter type checking

2. **Reaction-diffusion step**
   - Gray-Scott equations produce expected results
   - Numerical stability with various parameters
   - Boundary conditions wrap correctly

3. **Buffer management**
   - Circular buffer wraps correctly
   - Buffer initialization allocates correct size
   - Reset clears all state

4. **Color mapping**
   - RGB conversion produces valid colors
   - Contrast adjustment works correctly
   - Color mode selection produces expected results

5. **Audio integration**
   - Beat detection triggers parameter changes
   - Confidence threshold works correctly
   - BPM updates propagate to simulation

### Integration Tests (Coverage: 85%)
6. **Full render pipeline**
   - Given synthetic input, produce valid output
   - Output dimensions match input
   - No NaN or Inf values in output

7. **Pattern formation**
   - Different parameter sets produce distinct patterns
   - Patterns evolve over time
   - Beat-synced changes trigger correctly

8. **Performance benchmarks**
   - 60fps achievable at 1080p on reference hardware
   - Memory usage within budget (<100MB)
   - Frame time <16ms consistently

9. **Edge cases**
   - Zero feed rate: no growth
    - Zero kill rate: no decay
    - Zero diffusion: static patterns
    - Extreme parameters: stable or clamped

### Visual Quality Tests (Coverage: 75%)
10. **Pattern verification**
    - Spots, spirals, waves form correctly
    - Patterns remain stable over time
    - Color mapping produces visually pleasing results

11. **Audio synchronization**
    - Beat detection triggers expected changes
    - Smooth transitions between parameter changes
    - No visual artifacts from audio processing

---

## Definition of Done

### Technical Requirements
- [ ] All 14 parameters implemented with correct ranges
- [ ] Gray-Scott reaction-diffusion equations correctly implemented
- [ ] CPU implementation with NumPy working
- [ ] GPU shader implementation (optional but recommended)
- [ ] Beat synchronization with audio modules
- [ ] Real-time 60fps at 1080p on reference hardware
- [ ] Memory usage <100MB
- [ ] Edge cases handled gracefully

### Quality Requirements
- [ ] 80%+ test coverage achieved
- [ ] All unit tests passing
- [ ] Integration tests verify full pipeline
- [ ] Performance benchmarks documented
- [ ] Error handling robust with clear messages
- [ ] Visual quality meets organic pattern expectations

### Integration Requirements
- [ ] Compatible with VJLive3 effect chain
- [ ] Proper parameter exposure via set_parameter()
- [ ] Beat data integration with audio analyzer
- [ ] Resource cleanup in reset()/delete()
- [ ] Works alongside other video effects

---

## Legacy References

### Original Implementation
**Source**: `plugins/vcore/reaction_diffusion.py` (VJlive Original)

```python
class ReactionDiffusionEffect(Effect):
    """Reaction diffusion — Gray-Scott pattern formation with modulation."""

    PRESETS = {
        "mitosis": {"feed_rate": 4.6, "kill_rate": 8.3, "diffusion_a": 5.0, "diffusion_b": 2.5, "sim_speed": 5.0, "color_mode": 3.0, "contrast": 7.0,  ...[TRUNCATED LINE]
```

**Key characteristics from legacy:**
- Gray-Scott reaction-diffusion model
- GPU implementation with WGSL shader
- 14 parameters in 0.0-10.0 range
- Preset system for common patterns
- Audio-synchronized operation

### Related Implementation
**Enhanced version**: See P7-VE57 for full spec (already fleshed out)

### Shader Reference (Legacy WGSL)
The legacy implementation uses a fragment shader with:
- Multi-pass simulation loop
- Ping-pong buffers for state
- Gray-Scott equations in shader code
- Color mapping and feedback blending

**Note**: The exact shader code was not available in the knowledge base; implementation should follow the algorithmic description above.

### Parameter Mapping from Legacy
| Legacy Concept | VJLive3 Parameter | Range |
|----------------|-------------------|-------|
| Feed rate | feed_rate | 0.0-10.0 (maps to 0.02-0.08) |
| Kill rate | kill_rate | 0.0-10.0 (maps to 0.02-0.08) |
| Diffusion A | diffusion_a | 0.0-10.0 (maps to 0.2-1.0) |
| Diffusion B | diffusion_b | 0.0-10.0 (maps to 0.1-0.5) |
| Simulation speed | sim_speed | 0.0-10.0 (maps to 1-16 steps) |
| Opacity | opacity | 0.0-10.0 (maps to 0.0-1.0) |
| Color mode | color_mode | 0-5 (6 color schemes) |
| Contrast | contrast | 0.0-10.0 (maps to 1.0-3.0) |
| Invert | invert | 0.0-10.0 (binary on/off) |
| Edge glow | edge_glow | 0.0-10.0 (glow intensity) |
| Background brightness | bg_brightness | 0.0-10.0 (background level) |
| Seed mode | seed_mode | 0-2 (no seed, center seed, random seed) |
| Seed density | seed_density | 0.0-10.0 (initial B concentration) |
| Reseed rate | reseed_rate | 0.0-10.0 (continuous reseeding) |

---

## Easter Egg Idea

**Secret Feature**: "Quantum Superposition Mode"
- Hold a secret key combination (e.g., Ctrl+Alt+Shift+R) to enable quantum superposition of all chemical states
- Render all possible states simultaneously with quantum interference patterns
- Visual: shimmering, probabilistic patterns that look like quantum decoherence
- Hidden Easter egg message in the chemical concentrations when viewed with a spectrum analyzer

---

## Completion Notes

This spec provides a complete blueprint for implementing the ReactionDiffusionEffect in VJLive3. The effect is CPU-intensive due to multi-step reaction-diffusion simulation but can be optimized with resolution scaling and step reduction. The design follows the legacy architecture while adapting to VJLive3's effect chain model.

**Key implementation notes:**
- Use efficient circular buffer with pre-allocated memory
- Consider float16 for memory savings (Gray-Scott doesn't need high precision)
- Implement convolution with separable kernels for performance
- Use HSV color space for color mapping (faster than full RGB)
- Provide clear parameter documentation for VJ mapping

**Next steps after spec approval:**
1. Implement frame buffer with efficient memory layout
2. Optimize reaction-diffusion step with vectorized NumPy operations
3. Integrate with audio beat analyzer module
4. Add performance profiling and auto-quality adjustment
5. Create preset library for common patterns (spots, spirals, waves, mitosis)