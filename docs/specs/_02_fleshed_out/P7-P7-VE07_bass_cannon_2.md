````markdown
# P7-VE07: Bass Cannon 2 (Audio-Reactive Projectile Effect)

> **Task ID:** `P7-VE07`
> **Priority:** P0 (Critical)
> **Source:** VJlive-2 (`plugins/vdepth/bass_cannon_2.py`)
> **Class:** `BassCanon2`
> **Phase:** Phase 7
> **Status:** ✅ Fleshed out

## Mission Context
Provide a complete, unambiguous Pass 2 specification for the `BassCanon2` effect—
an audio-reactive visual effect that launches geometric projectiles or "cannon fire"
synchronized to bass frequencies. The effect responds to audio energy by spawning,
scaling, and animating visual elements (lines, circles, shapes) that shoot outward
from a center point. The objective is to document exact audio-driven animation math,
parameter remaps, projectile trajectories, presets, CPU fallback, and comprehensive
tests for feature parity with VJLive-2.

## Technical Requirements
- Implement as a VJLive3 effect plugin (processes/generates video with audio input)
- Sustain 60 FPS with audio reactivity and geometric rendering (Safety Rail 1)
- Achieve ≥80% unit/test coverage (Safety Rail 5)
- Keep implementation <750 lines (Safety Rail 4)
- Graceful fallback without audio input (renders static pattern) (Safety Rail 7)
- No silent failures; handle missing audio gracefully

## Implementation Notes / Porting Strategy
1. Implement audio-reaction hooks (bass frequency detection via FFT or envelope).
2. Generate projectile geometry procedurally (lines, circles, polygons).
3. Animate projectile positions and scales based on time and envelopes.
4. Support multiple projectile modes (laser, smoke, kinetic, ethereal).
5. Provide deterministic NumPy-based CPU fallback (frame rasterization).
6. Cache audio analysis to prevent redundant FFT computation.

## Public Interface
```python
class BassCanon2(Effect):
    """
    Bass Cannon 2: Audio-reactive projectile cannon effect.
    
    Launches visual projectiles synchronized to bass frequencies, creating
    dynamic, rhythmic visual effects. Responds to audio input with geometric
    scaling and pulsing animations.
    """

    def __init__(self, width: int = 1920, height: int = 1080, 
                 use_gpu: bool = True):
        """
        Initialize the bass cannon 2 effect.
        
        Args:
            width: Output width (pixels).
            height: Output height (pixels).
            use_gpu: If True, use GPU rendering; else CPU rasterization.
        """
        super().__init__("Bass Cannon 2", CANNON_VERTEX_SHADER, 
                         CANNON_FRAGMENT_SHADER)
        
        # Agent Metadata
        self.effect_category = "audio_reactive"
        self.effect_tags = ["bass", "cannon", "audio", "kinetic"]
        self.features = ["AUDIO_REACTIVE", "PROJECTILE_ANIMATION"]
        self.usage_tags = ["AUDIO_DRIVEN", "GENERATIVE"]
        
        self.use_gpu = use_gpu
        self.projectile_buffer = None   # GPU buffer for projectile positions
        self.audio_history = None       # Rolling window of audio data
        self.last_bass_trigger = 0.0    # Timestamp of last bass spike

        # Parameter ranges (all UI sliders 0.0—10.0)
        self._parameter_ranges = {
            'cannon_intensity': (0.0, 10.0),   # projectile strength
            'fire_rate': (0.0, 10.0),          # projectile spawn frequency
            'projectile_scale': (0.0, 10.0),   # size of projectiles
            'projectile_speed': (0.0, 10.0),   # outward velocity
            'bass_sensitivity': (0.0, 10.0),   # audio reactivity amount
            'projectile_mode': (0.0, 10.0),    # style (laser, smoke, etc.)
            'rotation': (0.0, 10.0),           # cannon angle or rotation
            'opacity': (0.0, 10.0),            # projectile visibility
            'glow_intensity': (0.0, 10.0),     # bloom on projectiles
            'particle_count': (0.0, 10.0),     # projectiles per burst
        }

        # Default parameter values
        self.parameters = {
            'cannon_intensity': 6.0,
            'fire_rate': 5.0,
            'projectile_scale': 5.0,
            'projectile_speed': 6.0,
            'bass_sensitivity': 7.0,
            'projectile_mode': 3.0,            # balanced default
            'rotation': 5.0,
            'opacity': 8.0,
            'glow_intensity': 4.0,
            'particle_count': 4.0
        }

        # Parameter descriptions
        self._parameter_descriptions = {
            'cannon_intensity': "Overall cannon power (0=weak, 10=intense)",
            'fire_rate': "Projectile spawn frequency (0=rare, 10=continuous)",
            'projectile_scale': "Projectile size (0=tiny, 10=huge)",
            'projectile_speed': "Outward velocity (0=static, 10=fast)",
            'bass_sensitivity': "Audio responsiveness (0=none, 10=full)",
            'projectile_mode': "Style: 0=laser, 3=smoke, 6=kinetic, 10=ethereal",
            'rotation': "Cannon rotation/angle (0—360°)",
            'opacity': "Projectile visibility (0=invisible, 10=opaque)",
            'glow_intensity': "Bloom effect on projectiles (0=none, 10=intense)",
            'particle_count': "Projectiles per burst (1—32)",
        }

        # Sweet spots
        self._sweet_spots = {
            'cannon_intensity': [2.0, 5.0, 8.0],
            'fire_rate': [2.0, 5.0, 8.0],
            'bass_sensitivity': [5.0, 7.0, 10.0]
        }

    def render(self, tex_in: int = None, extra_textures: list = None, 
              chain = None) -> int:
        """
        Render animated projectiles with audio reactivity.
        
        Args:
            tex_in: Optional background texture (for compositing).
            extra_textures: Optional (audio texture or beat detector).
            chain: Rendering chain context.
            
        Returns:
            Output texture with projectiles rendered.
        """
        # Analyze audio input (bass extraction)
        # Update projectile positions and scales based on audio
        # Render projectiles to framebuffer
        # Apply glow and opacity
        # Return result
        pass

    def analyze_audio(self, audio_reactor):
        """
        Extract bass frequency energy from audio input.
        
        Args:
            audio_reactor: AudioReactor instance with FFT data.
            
        Returns:
            Tuple of (bass_energy, onset_detected).
        """
        # Low-pass filter audio spectrum (bass = 0—100 Hz range)
        # Compute RMS or peak value
        # Detect beat onsets via energy rise
        pass

    def apply_uniforms(self, time: float, resolution: tuple, 
                      audio_reactor = None, semantic_layer = None):
        """
        Apply shader uniforms and compute audio-driven parameters.
        
        Args:
            time: Current time (seconds).
            resolution: Tuple of (width, height).
            audio_reactor: Optional audio input.
            semantic_layer: Optional semantic input.
        """
        # Analyze audio if available
        # Compute projectile spawn and animation
        # Bind uniforms to GPU
        pass
```

### Exposed Parameters, types and remaps (UI slider 0—10)
- `cannon_intensity` (float, UI 0—10) → internal `I` = map_linear(x, 0,10, 0.0, 2.0)
  - Overall effect strength multiplier [0, 2]
- `fire_rate` (float, UI 0—10) → internal `R` = map_linear(x, 0,10, 0.0, 100.0)
  - Spawn rate in projectiles/second [0, 100]
- `projectile_scale` (float, UI 0—10) → internal `S` = map_linear(x, 0,10, 0.1, 2.0)
  - Size multiplier [0.1, 2.0]
- `projectile_speed` (float, UI 0—10) → internal `V` = map_linear(x, 0,10, 50.0, 800.0)
  - Pixels/second outward velocity [50, 800]
- `bass_sensitivity` (float, UI 0—10) → internal `A` = x / 10.0
  - Audio reactivity weight [0, 1]
- `projectile_mode` (int, UI 0—10) → internal mode:
  - 0–2: Laser (straight lines, sharp)
  - 3–5: Smoke (circles with decay)
  - 6–8: Kinetic (polygons, dynamic)
  - 9–10: Ethereal (soft particles, trails)
- `rotation` (float, UI 0—10) → internal `θ` = x * 36.0 % 360.0
  - Cannon direction in degrees [0, 360]
- `opacity` (float, UI 0—10) → internal `α` = map_linear(x, 0,10, 0.0, 1.0)
  - Projectile opacity [0, 1]
- `glow_intensity` (float, UI 0—10) → internal `G` = map_linear(x, 0,10, 0.0, 1.0)
  - Bloom strength [0, 1]
- `particle_count` (int, UI 0—10) → internal `N` = clamp(round(x * 3.2), 1, 32)
  - Projectiles per burst [1, 32]

Remap functions:
- `map_linear(v,a,b,c,d) = c + (d-c) * ((v-a)/(b-a))`

## Shader uniforms (authoritative names for GPU path)
- `uniform float cannon_intensity;`     // effect strength
- `uniform float fire_rate;`            // spawn frequency
- `uniform float projectile_scale;`     // size
- `uniform float projectile_speed;`     // velocity
- `uniform float bass_energy;`          // audio energy [0,1]
- `uniform int projectile_mode;`        // style selection
- `uniform float rotation;`             // cannon angle (radians)
- `uniform float opacity;`              // alpha
- `uniform float glow_intensity;`       // bloom
- `uniform int particle_count;`         // burst size
- `uniform float time;`                 // elapsed time
- `uniform sampler2D audio_texture;`    // optional FFT data

## Effect Math (concise, GPU/CPU-consistent)

### 1) Audio Analysis (Bass Extraction)

Extract bass frequency energy from audio spectrum:

```
// Assume audio_reactor provides FFT bins [0, 22050 Hz]
// Bass range: 0-200 Hz ~ bins [0, 4]

bass_start_bin = 0
bass_end_bin = 4

bass_energy = sum(fft[bass_start_bin : bass_end_bin]) / 4
bass_normalized = bass_energy / max_expected_energy  // in [0, 1]
```

Optional beat detection via onset energy:

```
bass_derivative = bass_energy - bass_energy_prev_frame
onset_detected = bass_derivative > threshold
```

### 2) Projectile Spawning (When Fire_Rate Triggers)

Each frame, compute how many projectiles to spawn:

```
spawn_accumulator += fire_rate * dt  // accumulate over time
num_spawn = floor(spawn_accumulator)
spawn_accumulator -= num_spawn

// Create num_spawn new projectiles
for i in range(num_spawn):
    angle = rotation / 180.0 * π + (i / particle_count) * 2π  // radial spread
    projectile.position = origin  // typically screen center
    projectile.velocity = (cos(angle), sin(angle)) * projectile_speed
    projectile.scale = projectile_scale * (1.0 + bass_energy * bass_sensitivity)
    projectile.birth_time = time
    projectile.lifetime = 2.0 + 0.5 * (1.0 - bass_energy)  // longer if quiet
```

### 3) Projectile Animation Over Time

For each projectile, compute position and opacity:

```
age = time - projectile.birth_time
progress = age / projectile.lifetime  // [0, 1]

// Position: linear outward motion
position = projectile.position + projectile.velocity * age

// Scale: optional pulsing with bass
scale_pulsed = projectile.scale * (1.0 + 0.2 * sin(frequency * time))

// Opacity: fade at end of lifetime
alpha = projectile.opacity * (1.0 - smoothstep(0.7, 1.0, progress))

// Remove projectile if progress >= 1.0
if progress >= 1.0:
    remove projectile
```

### 4) Projectile Rendering (Mode-Dependent)

a) **Laser mode**: Draw straight line from origin through position
```
line_start = origin + projectile.velocity * 10.0  // small offset
line_end = position
render_line(line_start, line_end, width=2, color=(1,1,1))
```

b) **Smoke mode**: Draw expanding circle
```
circle_radius = projectile.scale * (10 + 20 * progress)
render_circle(position, circle_radius, color=(0.5, 0.8, 1.0), alpha=alpha)
```

c) **Kinetic mode**: Draw rotating polygon
```
num_sides = 6
rotation_angle = time * 3.0
render_polygon(position, num_sides, radius=projectile.scale*10, 
               rotation=rotation_angle, color=(1, 0.5, 0))
```

d) **Ethereal mode**: Draw soft particle with trail
```
draw_particle(position, scale=projectile.scale*5, color=(1, 1, 0.8), blur=2)
// Also render faint trail from origin to position
```

### 5) Glow/Bloom (Post-Processing)

If glow_intensity > 0:

```
extract_bright = extract_luminance_above_threshold(frame, 0.5)
bright_blurred = gaussian_blur(extract_bright, sigma=4.0)
final_frame = frame + bright_blurred * glow_intensity
```

## CPU Fallback (NumPy sketch)

```python
def bass_cannon_cpu(frame, time, projectiles, cannon_intensity, 
                    fire_rate, projectile_speed, projectile_mode):
    """Render projectiles to frame on CPU."""
    
    h, w = frame.shape[:2]
    center = np.array([w/2, h/2])
    output = frame.copy().astype(np.float32)
    
    for proj in projectiles:
        age = time - proj['birth_time']
        if age < 0 or age > proj['lifetime']:
            continue
        
        progress = age / proj['lifetime']
        
        # Compute position
        pos = center + proj['velocity'] * age
        
        # Compute opacity
        alpha = proj['opacity'] * (1.0 - max(0, (progress - 0.7) / 0.3))
        
        # Render based on mode
        if projectile_mode == 0:  # laser
            # Draw line from origin to pos
            draw_line(output, center.astype(int), pos.astype(int), 
                     color=[255, 255, 255], thickness=2)
        elif projectile_mode == 3:  # smoke
            # Draw expanding circle
            radius = int(proj['scale'] * (10 + 20 * progress))
            cv2.circle(output, pos.astype(int), radius, 
                      (128, 204, 255), -1, cv2.LINE_AA)
        
        # Apply alpha
        output = output * (1 - alpha * 0.3) + frame * (alpha * 0.3)
    
    return output.astype(np.uint8)
```

## Presets (recommended)
- `Gentle Pulse`:
  - `cannon_intensity` 2.0, `fire_rate` 2.0, `projectile_scale` 3.0,
    `projectile_speed` 3.0, `bass_sensitivity` 5.0, `projectile_mode` 3.0 (smoke)
- `Laser Burst`:
  - `cannon_intensity` 7.0, `fire_rate` 6.0, `projectile_scale` 2.0,
    `projectile_speed` 8.0, `bass_sensitivity` 8.0, `projectile_mode` 0.0 (laser)
- `Kinetic Explosion`:
  - `cannon_intensity` 8.0, `fire_rate` 8.0, `projectile_scale` 5.0,
    `projectile_speed` 6.0, `bass_sensitivity` 9.0, `projectile_mode` 6.0 (kinetic),
    `glow_intensity` 6.0
- `Ethereal Cascade`:
  - `cannon_intensity` 3.0, `fire_rate` 4.0, `projectile_scale` 6.0,
    `projectile_speed` 2.0, `bass_sensitivity` 6.0, `projectile_mode` 10.0 (ethereal),
    `particle_count` 8.0

## Edge Cases and Error Handling
- **No audio input**: Render projectiles on timer (fallback: use system clock tempo).
- **Zero fire_rate**: No projectiles spawn (safe).
- **Off-screen projectiles**: Cull when position exceeds view bounds.
- **Missing audio texture**: Skip bass analysis, use fallback energy = sin(time).
- **Invalid projectile_mode**: Clamp to valid range [0, 10].
- **Projectile buffer overflow**: Cap total active projectiles (e.g., max 1000).

## Test Plan (minimum ≥80% coverage)
- `test_bass_energy_extraction` — verify bass frequencies summed correctly
- `test_projectile_spawn_rate` — projectiles spawn at correct frequency
- `test_projectile_position_linear` — position advances at correct velocity
- `test_projectile_lifetime_decay` — opacity decreases as lifetime expires
- `test_projectile_laser_mode` — laser renders straight lines
- `test_projectile_smoke_mode` — smoke renders expanding circles
- `test_projectile_kinetic_mode` — kinetic renders rotating polygons
- `test_projectile_ethereal_mode` — ethereal renders soft particles
- `test_bass_sensitivity_modulation` — bass_sensitivity scales projectile size
- `test_glow_bloom_effect` — glow_intensity brightens output
- `test_no_audio_fallback` — renders without crashing when audio unavailable
- `test_cpu_vs_gpu_parity` — CPU and GPU outputs match within tolerance
- `test_performance_60fps` — sustain ≥60 FPS at 1080p with 100+ projectiles

## Verification Checkpoints
- [ ] `BassCanon2` class registers with plugin registry
- [ ] All parameters (0—10 UI sliders) bind correctly to shader uniforms
- [ ] Audio analysis (bass extraction) produces valid energy [0,1]
- [ ] Projectiles spawn, animate, and fade correctly
- [ ] All 4 projectile modes render distinctly
- [ ] CPU fallback produces animated projectiles without crashing
- [ ] Presets render at intended visual styles
- [ ] Tests pass with ≥80% code coverage
- [ ] 60 FPS sustained at 1080p with typical cannon settings
- [ ] Graceful degradation when audio unavailable

## Implementation Handoff Notes
- Audio analysis optimization:
  - Cache FFT results; update only once per frame
  - Use rolling window (last 4 frames) for bass energy smoothing
  - Detect beat onsets via energy derivative thresholding
  
- Projectile buffers:
  - Use ring buffer for efficient spawn/cull cycles
  - Pre-allocate max capacity (e.g., 1000 projectiles)
  - Compact array each frame by removing expired projectiles
  
- Rotation parameter:
  - If cannon should rotate continuously, add `time * rotation_speed` term
  - Alternatively, treat rotation as fixed cannon angle

## Resources
- Reference (bass cannons): Resolume, TouchDesigner, vjlive legacy
- Audio: FFT libraries, beat detection via spectral flux
- Geometry: Line rendering, circle rasterization, polygon transforms

````
