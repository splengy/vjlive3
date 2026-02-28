# P3-EXT004: Agent Avatar Effect — Technical Specification

**File naming:** `docs/specs/P3-EXT004_agent_avatar.md`
**Priority:** Phase 3 Extension
**Status:** In Progress
**Assigned Worker:** desktop-roo
**Created:** 2026-02-26
**Last Updated:** 2026-02-27

---

## IMPORTANT: File Location and Naming

The final implementation **MUST** be placed at:
- `src/vjlive3/core/effects/agent_avatar.py` (or `plugins/vagent/agent_avatar.py` depending on architecture)

This file **must** exist and be reviewed BEFORE writing any code for this task.

## Description

The AgentAvatarEffect module visualizes an agent's internal emotional and cognitive state through a reactive geometric avatar that appears in a multi-screen display environment. The avatar serves as a visual metaphor for the agent's current state, reacting to changes in confidence, emotional intensity, and cognitive load. Users will perceive the avatar through its dynamic shape, color, and movement patterns, gaining an intuitive understanding of the agent's internal state without requiring explicit UI elements. The effect leverages real-time shader computations to create a compelling visual representation that integrates with the existing node-based architecture.

### Core Architecture

The implementation provides two distinct classes that share the same shader foundation but differ in their state management and integration patterns:

#### 1. `TravelingAvatarEffect`
- **Purpose:** Multi-node environments where the avatar traverses different display nodes
- **Integration:** Uses `SyncManager` for global state coordination
- **Visibility:** Appears only when within node viewport (`local_pos >= 0.0`)
- **Position:** Horizontal traversal across screen (0.0 = left, 1.0 = right)
- **Vertical:** Fixed at center (0.5)

#### 2. `AgentAvatarEffect`
- **Purpose:** Standalone deployments with IR-based shadow mode and eye tracking
- **Integration:** Uses `SurfaceIRSource` for Windows-specific IR camera access
- **Features:** Shadow Mode (IR heat detection) and Eye Tracking (OpenCV Haar cascades)
- **Position:** Fixed corner position (default: x=0.9, y=0.1)
- **Size:** Smaller than traveling avatar (default: scale=0.1)

Both classes inherit from the base `Effect` class and implement the same shader interface but differ in their state management and integration patterns.
**What This Module Does**
- Renders a geometric avatar that reflects agent emotional states:
  - **Thinking state**: Rapid spinning animation driven by `spin_speed` parameter (default 2.0, range 0.0-10.0)
  - **Confident state**: Stable bright white glow with high `confidence` value (default 0.8, range 0.0-1.0) and minimal `fragmentation`
  - **Overwhelmed state**: Fragmentation into particles via `fragmentation` parameter (default 0.0, range 0.0-1.0) that breaks the geometric core
- Implements Shadow Mode using IR heat detection to control avatar visibility, requiring `SurfaceIRSource` integration on Windows platforms
- Implements Eye Tracking that adjusts avatar gaze based on detected face position using OpenCV Haar cascade detection
- Updates avatar parameters (confidence, glow intensity, position) based on global state signals through `SyncManager`
- Manages shader uniforms for position, scale, and alpha calculations via `apply_uniforms()`

**What This Module Does NOT Do**
- Does NOT handle file I/O or persistence operations
- Does NOT process audio input directly (though it can respond to audio-driven parameter changes)
- Does NOT manage node graph connections or traversal (delegates to `SyncManager`)
- Does NOT provide real-time audio-visual synchronization beyond visual parameters

### Complete Shader Architecture

The `AVATAR_FRAGMENT_SHADER` is a GLSL 330 core shader that implements a sophisticated geometric avatar using signed distance fields. The shader structure includes:

#### Vertex Shader (implicit)
The base `Effect` class provides a vertex shader that generates a full-screen quad with UV coordinates. The avatar effect does not override this; it relies on the standard full-screen quad approach where:
- Two triangles cover the entire viewport
- UV coordinates range from (0,0) to (1,1)
- Position is passed to the fragment shader

#### Fragment Shader Components

```glsl
#version 330 core
in vec2 uv;
out vec4 fragColor;

uniform float time;
uniform vec2 resolution;
uniform float u_mix;

// Agent state parameters
uniform float spin_speed;
uniform float glow_intensity;
uniform float confidence;
uniform float fragmentation;
uniform vec3 glow_color;
uniform float avatar_alpha;

// Avatar positioning and scaling
uniform float avatar_scale;
uniform vec2 avatar_position;

// Shadow Mode parameters
uniform float shadow_mode_enabled;
uniform float has_shadow_mask;

// Eye Tracking parameters
uniform float eye_tracking_enabled;
uniform vec2 gaze_direction;
```

#### Core Geometry Functions

**`triangle_distance(p, a, b, c)`**
Computes the signed distance from point `p` to triangle defined by vertices `a`, `b`, `c`. Uses barycentric coordinate projection to find the closest point on the triangle's edges or interior. This is the fundamental SDF primitive for the avatar's triangular elements.

**`agent_core(p, time, spin_speed, fragmentation)`**
Constructs the complete avatar geometry from multiple SDF primitives:

1. **Central Hexagon**: A regular hexagon at radius 0.3 with thickness 0.05
   ```glsl
   float hex_angle = atan(p.y, p.x) / (2.0 * PI) * 6.0;
   hex_angle = fract(hex_angle);
   float hex_radius = length(p);
   float hex_dist = abs(hex_radius - 0.3) - 0.05;
   d = min(d, hex_dist);
   ```

2. **Six Surrounding Triangles**: Positioned at radius 0.6, each rotates at half the main spin speed
   ```glsl
   for (int i = 0; i < 6; i++) {
       float a = float(i) * PI / 3.0 + time * spin_speed * 0.5;
       vec2 center = vec2(cos(a), sin(a)) * 0.6;
       
       // Fragmentation causes triangles to drift apart
       center += normalize(center) * fragmentation * sin(time * 3.0 + float(i));
       
       // Triangle vertices
       vec2 v1 = center + vec2(0.1, 0.0);
       vec2 v2 = center + vec2(-0.05, 0.08);
       vec2 v3 = center + vec2(-0.05, -0.08);
       
       float tri_dist = triangle_distance(p, v1, v2, v3);
       d = min(d, tri_dist - 0.02);
   }
   ```

3. **Three Inner Spinning Elements**: Small dots at radius 0.15, spinning at 2x main speed
   ```glsl
   for (int i = 0; i < 3; i++) {
       float a = float(i) * 2.0 * PI / 3.0 + time * spin_speed * 2.0;
       vec2 pos = vec2(cos(a), sin(a)) * 0.15;
       
       // Fragmentation scatters inner elements
       pos += normalize(pos) * fragmentation * 0.5;
       
       float inner_dist = distance(p, pos) - 0.03;
       d = min(d, inner_dist);
   }
   ```

#### Rendering Pipeline

1. **Coordinate Transformation**:
   ```glsl
   p = (p - avatar_position) / avatar_scale;
   ```
   Transforms from screen space to avatar-local space, applying scale and position.

2. **Rotation**:
   ```glsl
   float angle = time * spin_speed;
   float cos_a = cos(angle);
   float sin_a = sin(angle);
   p = vec2(p.x * cos_a - p.y * sin_a, p.x * sin_a + p.y * cos_a);
   ```
   Applies time-based rotation to create the spinning effect.

3. **Eye Tracking Offset** (if enabled):
   ```glsl
   if (eye_tracking_enabled > 0.5) {
       vec2 gaze_offset = gaze_direction * 0.1;
       vec2 adjusted_uv = uv + gaze_offset;
       d = agent_core(adjusted_uv, time, spin_speed, fragmentation);
   }
   ```
   Subtly shifts the entire avatar geometry based on gaze direction.

4. **SDF to Alpha Conversion**:
   ```glsl
   float glow = 1.0 - smoothstep(0.0, 0.1, d);
   glow = pow(glow, 2.0) * glow_intensity;
   
   float core = 1.0 - smoothstep(0.0, 0.02, d);
   
   float alpha = (core + glow) * avatar_alpha;
   ```
   The `smoothstep` creates anti-aliased edges. Glow uses a larger radius and is squared for a softer falloff.

5. **Color Blending**:
   ```glsl
   vec3 color = glow_color * confidence + vec3(1.0, 1.0, 1.0) * (1.0 - confidence);
   color *= (0.5 + 0.5 * glow);  // Brighten with glow
   ```
   Confidence interpolates between the configured glow color and white. Glow intensity further brightens the result.

6. **Shadow Mode** (if enabled):
   ```glsl
   if (shadow_mode_enabled > 0.5) {
       vec2 dist_from_avatar = abs(uv - avatar_position);
       if (dist_from_avatar.x > avatar_scale * 2.0 ||
           dist_from_avatar.y > avatar_scale * 2.0) {
           fragColor = vec4(0.0, 0.0, 0.0, 0.0);
           return;
       }
       
       // In full implementation: sample shadow_mask texture
       // float mask_value = texture(shadow_mask, uv).r;
       // if (mask_value < threshold) discard or alpha = 0.0;
   }
   ```
   The current implementation uses a simple bounding box check. A full implementation would sample the IR shadow mask texture and mask the avatar based on heat detection.

**Detailed Behavior**

The avatar rendering pipeline operates through a GLSL 330 core fragment shader that implements a hexagonal geometric core with radial glow. The core shape is generated using signed distance field (SDF) mathematics: `float core = 1.0 - smoothstep(0.0, 0.02, d);` where `d` represents the distance from the fragment to the avatar center. The glow effect uses a similar SDF approach with a larger radius: `float glow = 1.0 - smoothstep(0.0, 0.1, d);` which is then exponentiated `glow = pow(glow, 2.0) * glow_intensity;` to create a soft falloff.

Color calculation combines the `glow_color` (default white `[1.0, 1.0, 1.0]`) with confidence-based brightness: `vec3 color = glow_color * confidence + vec3(1.0, 1.0, 1.0) * (1.0 - confidence);` This creates a visual interpolation where high confidence yields pure glow color while low confidence introduces white. The final alpha is `(core + glow) * avatar_alpha`, allowing the core and glow to combine additively.

Visibility determination differs between classes:
- `TravelingAvatarEffect` uses `local_pos >= 0.0` from `sync_manager.get_avatar_position_for_node(node_id)` to decide if the avatar appears in a particular node's viewport
- `AgentAvatarEffect` uses IR shadow masking when `shadow_mode_enabled` is true, sampling the IR heat texture to determine visible regions

The shader receives uniforms via `apply_uniforms()`: `avatar_position` (vec2), `avatar_scale` (float), `avatar_alpha` (float), `spin_speed` (float), `glow_intensity` (float), `confidence` (float), `fragmentation` (float), and `glow_color` (vec3). For shadow mode, additional uniforms include `shadow_mode_enabled`, `has_shadow_mask`, and IR texture samplers.

### Complete Class Structure

#### `TravelingAvatarEffect(Effect)`

**Constructor:**
```python
def __init__(self, sync_manager=None, node_id=0):
    super().__init__("traveling_avatar", AVATAR_FRAGMENT_SHADER)
    
    self.sync_manager = sync_manager
    self.node_id = node_id
    
    # Initialize default parameters
    self.set_parameter("avatar_scale", 0.15)
    self.set_parameter("avatar_alpha", 1.0)
    self.set_parameter("spin_speed", 2.0)
    self.set_parameter("glow_intensity", 1.0)
    self.set_parameter("confidence", 0.8)
    self.set_parameter("fragmentation", 0.0)
    self.set_parameter("glow_color", [1.0, 1.0, 1.0])
    self.set_parameter("avatar_x", 0.5)  # Will be updated by sync_manager
    self.set_parameter("avatar_y", 0.5)  # Fixed at center
```

**Key Methods:**
```python
def update_from_global_state(self):
    """Update avatar position and visibility based on global state."""
    if not self.sync_manager:
        return
    
    local_pos = self.sync_manager.get_avatar_position_for_node(self.node_id)
    
    if local_pos >= 0.0:  # Avatar is visible on this node
        self.set_parameter("avatar_x", local_pos)  # 0.0=left, 1.0=right
        self.set_parameter("avatar_y", 0.5)  # Center vertically
        self.set_parameter("avatar_alpha", 1.0)
    else:
        self.set_parameter("avatar_alpha", 0.0)  # Invisible

def apply_uniforms(self, time: float, resolution: Tuple[int, int],
                   audio_reactor=None, semantic_layer=None):
    """Apply uniforms for traveling avatar."""
    super().apply_uniforms(time, resolution, audio_reactor, semantic_layer)
    
    # Update position from global state
    self.update_from_global_state()
    
    # Set shader uniforms
    self.shader.set_uniform("avatar_position", [
        self.get_parameter("avatar_x"),
        self.get_parameter("avatar_y")
    ])
    self.shader.set_uniform("avatar_scale", self.get_parameter("avatar_scale"))
    self.shader.set_uniform("avatar_alpha", self.get_parameter("avatar_alpha"))
    self.shader.set_uniform("spin_speed", self.get_parameter("spin_speed"))
    self.shader.set_uniform("glow_intensity", self.get_parameter("glow_intensity"))
    self.shader.set_uniform("confidence", self.get_parameter("confidence"))
    self.shader.set_uniform("fragmentation", self.get_parameter("fragmentation"))
    self.shader.set_uniform("glow_color", self.get_parameter("glow_color"))
```

#### `AgentAvatarEffect(Effect)`

**Constructor:**
```python
def __init__(self):
    super().__init__("agent_avatar", AVATAR_FRAGMENT_SHADER)
    
    # IR camera source (Windows-only, optional)
    self.ir_source: Optional[SurfaceIRSource] = None
    self.ir_frame = None
    self.face_cascade = None
    
    # Face tracking state
    self.face_position = (0.5, 0.5)  # Normalized screen coordinates
    self.face_detected = False
    self.last_face_time = 0
    
    # Shadow mask
    self.shadow_mask = None
    
    # Initialize face detection
    self._init_face_detection()
    
    # Default parameters for corner placement
    self.set_parameter("avatar_scale", 0.1)
    self.set_parameter("avatar_x", 0.9)
    self.set_parameter("avatar_y", 0.1)
    self.set_parameter("avatar_alpha", 0.7)
    
    # Shadow mode parameters
    self.set_parameter("shadow_mode_enabled", 0.0)
    self.set_parameter("shadow_threshold", 0.3)
    self.set_parameter("shadow_smooth", 0.1)
    
    # Eye tracking parameters
    self.set_parameter("eye_tracking_enabled", 0.0)
    self.set_parameter("gaze_smooth", 0.05)
    self.set_parameter("face_timeout", 2.0)
    
    # Gaze direction (updated by face tracking)
    self.set_parameter("gaze_x", 0.0)
    self.set_parameter("gaze_y", 0.0)
```

**Key Methods:**

```python
def _init_face_detection(self):
    """Initialize OpenCV face detection using Haar cascade."""
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
    except Exception as e:
        print(f"Failed to load face cascade: {e}")
        self.face_cascade = None

def set_ir_source(self, ir_source: SurfaceIRSource):
    """Connect to IR camera source for shadow mode."""
    self.ir_source = ir_source

def set_agent_bridge(self, agent_bridge):
    """Connect to agent bridge for emotional state parameters."""
    self.agent_bridge = agent_bridge

def _detect_face(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Detect face in IR frame using OpenCV Haar cascade."""
    if self.face_cascade is None or frame is None:
        return None
    
    try:
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Normalize for better detection
        gray = cv2.equalizeHist(gray.astype(np.uint8))
        
        # Detect faces with tuned parameters for IR
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            maxSize=(300, 300)
        )
        
        if len(faces) > 0:
            # Return the largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            return tuple(largest_face)
        else:
            return None
            
    except Exception as e:
        print(f"Face detection error: {e}")
        return None

def _update_shadow_mask(self, ir_frame: np.ndarray, resolution: Tuple[int, int]):
    """Update shadow mask based on IR heat data."""
    if ir_frame is None:
        return
    
    try:
        # Normalize IR data to 0-1 range
        if ir_frame.dtype == np.uint16:
            ir_normalized = ir_frame.astype(np.float32) / 65535.0
        else:
            ir_normalized = ir_frame.astype(np.float32) / 255.0
        
        # Apply threshold for body detection
        threshold = self.get_parameter("shadow_threshold")
        mask = (ir_normalized > threshold).astype(np.float32)
        
        # Morphological operations to clean up mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Smooth the mask
        smooth_factor = self.get_parameter("shadow_smooth")
        if smooth_factor > 0:
            mask = cv2.GaussianBlur(mask, (0, 0), smooth_factor * 10)
        
        # Resize to match screen resolution
        mask_resized = cv2.resize(mask, resolution, interpolation=cv2.INTER_LINEAR)
        
        self.shadow_mask = mask_resized
        
    except Exception as e:
        print(f"Shadow mask update error: {e}")
        self.shadow_mask = None

def _update_face_tracking(self, ir_frame: np.ndarray, resolution: Tuple[int, int]):
    """Update face tracking and gaze direction from IR frame."""
    if ir_frame is None:
        # Check timeout
        if time.time() - self.last_face_time > self.get_parameter("face_timeout"):
            self.face_detected = False
            self.face_position = (0.5, 0.5)  # Reset to center
        return
    
    face_rect = self._detect_face(ir_frame)
    
    if face_rect is not None:
        x, y, w, h = face_rect
        
        # Calculate face center in normalized coordinates
        face_center_x = (x + w/2) / ir_frame.shape[1]
        face_center_y = (y + h/2) / ir_frame.shape[0]
        
        # Apply smoothing
        smooth_factor = self.get_parameter("gaze_smooth")
        current_x, current_y = self.face_position
        
        new_x = current_x * (1 - smooth_factor) + face_center_x * smooth_factor
        new_y = current_y * (1 - smooth_factor) + face_center_y * smooth_factor
        
        self.face_position = (new_x, new_y)
        self.face_detected = True
        self.last_face_time = time.time()
    else:
        # No face detected, check timeout
        if time.time() - self.last_face_time > self.get_parameter("face_timeout"):
            self.face_detected = False
            self.face_position = (0.5, 0.5)  # Reset to center

def apply_uniforms(self, time: float, resolution: Tuple[int, int],
                   audio_reactor=None, semantic_layer=None):
    """Apply uniforms for agent avatar with IR integration."""
    super().apply_uniforms(time, resolution, audio_reactor, semantic_layer)
    
    # Update IR data if source is available
    if self.ir_source:
        self.ir_frame = self.ir_source.get_ir_frame()
        if self.ir_frame:
            # Update shadow mask
            shadow_enabled = self.get_parameter("shadow_mode_enabled") > 0.5
            if shadow_enabled:
                self._update_shadow_mask(self.ir_frame.frame, resolution)
            
            # Update face tracking
            eye_tracking_enabled = self.get_parameter("eye_tracking_enabled") > 0.5
            if eye_tracking_enabled:
                self._update_face_tracking(self.ir_frame.frame, resolution)
            
            # Update gaze direction based on face position
            if eye_tracking_enabled and self.face_detected:
                avatar_x = self.get_parameter("avatar_x")
                avatar_y = self.get_parameter("avatar_y")
                
                gaze_x = self.face_position[0] - avatar_x
                gaze_y = self.face_position[1] - avatar_y
                
                # Normalize
                gaze_length = (gaze_x**2 + gaze_y**2)**0.5
                if gaze_length > 0:
                    gaze_x /= gaze_length
                    gaze_y /= gaze_length
                
                self.set_parameter("gaze_x", gaze_x)
                self.set_parameter("gaze_y", gaze_y)
    
    # Apply basic avatar parameters
    self.shader.set_uniform("avatar_alpha", self.get_parameter("avatar_alpha"))
    self.shader.set_uniform("avatar_scale", self.get_parameter("avatar_scale"))
    
    # Avatar position (may be overridden by eye tracking)
    self.shader.set_uniform("avatar_position", [
        self.get_parameter("avatar_x"),
        self.get_parameter("avatar_y")
    ])
    
    # Shadow mode uniforms
    shadow_enabled = self.get_parameter("shadow_mode_enabled") > 0.5
    self.shader.set_uniform("shadow_mode_enabled", 1.0 if shadow_enabled else 0.0)
    
    # Eye tracking uniforms
    eye_tracking_enabled = self.get_parameter("eye_tracking_enabled") > 0.5
    self.shader.set_uniform("eye_tracking_enabled", 1.0 if eye_tracking_enabled else 0.0)
    self.shader.set_uniform("gaze_direction", [
        self.get_parameter("gaze_x", 0.0),
        self.get_parameter("gaze_y", 0.0)
    ])
    
    # Shadow mask texture
    if self.shadow_mask is not None and shadow_enabled:
        self.shader.set_uniform("has_shadow_mask", 1.0)
        # In full implementation: upload texture to GPU
    else:
        self.shader.set_uniform("has_shadow_mask", 0.0)
```

**Legacy Context**
The original implementation emerged from VJLive's multi-screen performance environment where agents needed to appear as traveling entities across distributed displays. The [`SurfaceIRSource`](core/crowd_listener.py:17) class provided Windows-specific IR camera access via Media Foundation, enabling the Shadow Mode feature that tied avatar visibility to human presence detected through heat signatures. The eye tracking system used OpenCV's Haar cascade classifier (`haarcascade_frontalface_default.xml`) processed on IR frames, which work particularly well because IR imagery provides high contrast for face detection.

The shader evolved from a simple point sprite to a full fragment-shader-based geometric primitive with SDF anti-aliasing. Early versions used `gl_PointSize` in the vertex shader but this was disallowed by VJLive3's shader validation system, requiring a full-screen quad approach with UV-based fragment calculations. The fragmentation effect for "overwhelmed" state was originally implemented as particle trails but simplified to a visual breakup of the core shape for performance.

Cross-platform considerations arose because Surface IR is Windows-only; Linux deployments use generic OpenGL texture binding with fallback to OpenGL ES 3.2 on ARM devices like the Orange Pi 5. The legacy codebase shows shader compilation failures in plugin verification, indicating the need for robust fallback strategies when GPU capabilities vary.

## OpenGL.GL Fallback
The legacy implementation reveals a sophisticated platform abstraction strategy. The [`SurfaceIRSource`](core/effects/agent_avatar.py:257) class is imported conditionally from `drivers.x86_windows.surface_ir_source`, making it Windows-specific. On Linux systems, the code falls back to generic OpenGL texture binding via `OpenGL.GL` without IR capabilities. For ARM devices like the Orange Pi 5 (RK3588), the fallback strategy explicitly targets OpenGL ES 3.2, which has reduced feature sets compared to desktop OpenGL but maintains shader compatibility.

The graceful degradation pattern is evident in the initialization: if `SurfaceIRSource` import fails or initialization throws an exception, the `ir_source` attribute remains `None` and the effect continues without shadow mode. The shader itself checks `has_shadow_mask` uniform to decide whether to sample IR textures, avoiding texture binding errors when the data is unavailable.

## Audio Band Mapping
The legacy code shows an audio reactivity system that maps frequency bands to visual parameters. The avatar effect expects three primary uniforms from an audio analyzer: `u_audio_level` (RMS amplitude normalized 0.0-1.0), `u_bass` (20-250Hz normalized), `u_mid` (250-4000Hz normalized), and `u_high` (4000-20000Hz normalized). The fragmentation parameter is driven primarily by bass content: `fragmentation = u_bass * 0.5` when the agent is in "overwhelmed" state, creating a pulsing breakup effect that syncs with low-frequency transients.

The glow intensity also responds to audio: `glow_intensity = base_glow + u_audio_level * 0.3`, allowing the avatar to pulse with overall volume. This creates a direct audiovisual coupling where the avatar appears to "breathe" with the music. The legacy system originally mapped 8 frequency bands to particle trails, but this was simplified to the three-band approach for better performance and clearer visual semantics.

## Shader Compilation
VJLive3 employs a custom shader compiler that enforces GLSL 330 core compatibility. The [`AVATAR_FRAGMENT_SHADER`](core/effects/agent_avatar.py:97) string is compiled at runtime through the `Effect` base class's shader management system. The validation step explicitly rejects shaders that use `gl_PointSize` (a remnant from the point-sprite approach) because VJLive3 uses full-screen quads with UV coordinates passed from the vertex shader.

Shader compilation failures are common with complex effects due to driver inconsistencies across platforms. The legacy plugin verification output shows multiple "Shader program linking failed" messages, indicating that the avatar shader itself may have issues with uniform binding or varying definitions. The implementation must therefore include robust error handling: if shader compilation fails, the effect should log the error and fall back to a basic geometric rendering path (likely a simple colored quad) rather than crashing the entire pipeline.

The shader code structure includes:
- Vertex shader: passes UV coordinates and position
- Fragment shader: implements SDF-based core and glow with rotation matrix for spin effect
- Uniform declarations: all parameters must be explicitly declared as `uniform` with matching types

## Audio Parameter Validation
The legacy implementation used strict type checking in the parameter setting system, but the current VJLive3 architecture uses runtime validation with graceful degradation. When audio analyzer data is missing or out of range, the avatar effect clamps values to safe ranges: `confidence = max(0.0, min(1.0, confidence))`, `glow_intensity = max(0.0, min(2.0, glow_intensity))`, etc. Warning logs are emitted when parameters exceed thresholds to aid debugging without interrupting the visual output.

Parameter smoothing is implemented via exponential moving average: `smoothed_value = smoothed_value * 0.9 + new_value * 0.1`. This prevents jarring visual jumps when audio levels change rapidly, creating a more organic feel. The default color schemes—Neon cyan (#00FFFF) for Confident state and Magenta (#FF00FF) for Overwhelmed state—are hardcoded in the configuration schema but can be overridden through the `glow_color` parameter.

## Video Processing
The rendering pipeline has evolved from point cloud rendering (early VJLive versions) to a pure GPU-accelerated shader approach. The current implementation uses a continuous math model without discrete particle systems, which improves performance and visual smoothness. The rendering flow is:

1. Vertex shader generates a full-screen quad (two triangles covering the viewport)
2. UV coordinates are interpolated across fragments
3. Fragment shader computes distance from UV center, applies rotation matrix based on `time * spin_speed`, and calculates SDF for core and glow
4. Alpha blending composites the avatar over the background using `avatar_alpha`

Frame processing targets 60fps with support for variable frame rates; the `time` uniform is used for time-based animations (spinning, pulsing). Quantum state transitions between emotional states use continuous math rather than discrete jumps: confidence and fragmentation values are interpolated over time using `lerp(current, target, delta_time * transition_speed)`. Level-of-detail rendering adjusts shader complexity based on `avatar_scale`: when the avatar is small (< 0.05), the glow calculation is simplified to reduce fragment shader workload.

## Integration
The effect integrates with VJLive3's distributed architecture through the [`SyncManager`](core/effects/agent_avatar.py:49) class, which maintains global state across multiple display nodes. The [`TravelingAvatarEffect`](core/effects/agent_avatar.py:33) constructor accepts `sync_manager` and `node_id` parameters, allowing it to query `sync_manager.get_avatar_position_for_node(node_id)` each frame. This returns a normalized x-position (0.0-1.0) or a negative value if the avatar is not in that node's viewport. The effect does not directly manipulate node graph connections; it relies on the sync manager to handle inter-node communication.

For [`AgentAvatarEffect`](core/effects/agent_avatar.py:241), integration with the agent bridge provides access to emotional state parameters. The `set_agent_bridge()` method connects to an object that exposes `get_confidence()`, `get_emotional_state()`, and similar methods. The effect's `update()` method polls the bridge each frame and updates its internal parameters accordingly.

Shader uniforms must be updated in the [`apply_uniforms()`](core/effects/agent_avatar.py:81) method, which is called by the base `Effect` class during rendering. The uniform locations are cached after the first lookup to avoid per-frame `glGetUniformLocation` calls, which are expensive.

## Performance
The effect is GPU-intensive due to the per-fragment SDF calculations and the full-screen quad approach. Memory usage scales with the number of active avatar instances: each instance requires its own uniform buffer object (UBO) or uniform values, but the shader program itself is shared. On multi-node setups, each node runs its own avatar instance, multiplying the GPU workload.

Cross-platform performance profiles vary significantly:
- Desktop OpenGL (GL 3.3+): baseline performance, full feature set
- OpenGL ES 3.2 on ARM (Orange Pi 5): reduced precision, some texture format limitations
- Vulkan: potential for enhanced performance via compute shaders and multi-threaded command generation
- CUDA/TensorRT on NVIDIA GPUs: not applicable for this effect (no AI inference)

Memory optimization strategies include:
- Shared shader programs: all avatar instances use the same compiled shader
- Texture reuse: the IR shadow mask texture is shared across instances
- Level-of-detail: when `avatar_scale` is small, the fragment shader uses a simplified glow calculation (fewer operations)

The target is 60fps with smooth state transitions; any frame time exceeding 16.67ms will cause visible stutter. Profiling should focus on fragment shader instruction count and texture fetch bandwidth.

## Error Cases
Robust error handling is critical for a visual effect that runs continuously in a live performance environment:

- **SyncManager connection loss**: The `update_from_global_state()` method checks `if not self.sync_manager: return`. The avatar maintains its last known position and visibility state, continuing to render with stale data rather than disappearing or crashing.
- **IR data unavailability**: When `shadow_mode_enabled` is true but the IR source fails to provide a frame, the shader's `has_shadow_mask` uniform is set to 0, causing the shader to skip shadow sampling and render the avatar fully visible. This graceful degradation ensures the avatar remains visible even if the IR camera disconnects.
- **Shader compilation failures**: If the AVATAR_FRAGMENT_SHADER fails to compile or link, the `Effect` base class should catch the exception, log the error with `logger.error()`, and fall back to a basic `render_fallback()` method that draws a simple colored rectangle. The plugin verification output shows that shader linking failures are common, so this path must be tested.
- **Parameter validation errors**: When external code sets parameters outside valid ranges (e.g., `glow_intensity = 5.0`), the `set_parameter()` method clamps to the defined range and logs a warning. This prevents visual artifacts from extreme values while alerting developers to the misuse.
- **Face detection loss**: In eye tracking mode, if no face is detected for more than 30 frames (tracked via `last_face_time`), the gaze direction freezes at the last known position rather than snapping to center. This prevents jarring jumps when a user briefly looks away or the detection fails due to lighting changes.

## Configuration Schema
The configuration schema defines all tunable parameters for the avatar effect. The legacy implementation used a parameter system based on `set_parameter(key, value)` and `get_parameter(key)` methods that stored values in a dictionary with type validation. The current Pydantic schema formalizes these parameters with explicit ranges and defaults:

```python
class AgentAvatarConfig(BaseModel):
    avatar_scale: float = 0.15           # Range: 0.05-0.5, Default: 0.15
    glow_intensity: float = 1.0           # Range: 0.0-2.0, Default: 1.0
    confidence: float = 0.8              # Range: 0.0-1.0, Default: 0.8
    fragmentation: float = 0.0           # Range: 0.0-1.0, Default: 0.0
    spin_speed: float = 2.0              # Range: 0.0-10.0, Default: 2.0
    glow_color: List[float] = [1.0, 1.0, 1.0]  # RGB values, Default: White
    shadow_mode_enabled: bool = False     # Default: False
    eye_tracking_enabled: bool = True     # Default: True
```

The `avatar_scale` parameter controls the size of the avatar in normalized screen coordinates; values below 0.05 become visually indistinguishable while values above 0.5 cause the avatar to dominate the viewport. The `glow_intensity` multiplies the radial glow falloff and can exceed 1.0 for extremely bright effects, though values above 2.0 may cause clipping in the final color buffer. The `fragmentation` parameter, when non-zero, breaks the continuous SDF core into discrete segments by adding noise to the distance calculation: `d += fragmentation * noise(uv * 10.0 + time)`.

The `shadow_mode_enabled` flag requires the presence of a functional `SurfaceIRSource`; if enabled but no IR source is available, the effect logs a warning and continues without shadowing. Similarly, `eye_tracking_enabled` activates the face detection pipeline, which consumes approximately 2-3ms per frame on a modern CPU when processing a 640x480 IR frame.

## State Management
The avatar effect maintains per-frame state that is updated each tick. The `update()` method (called by the effect chain) performs:
1. Query `sync_manager.get_avatar_position_for_node(node_id)` for `TravelingAvatarEffect`, or poll `agent_bridge.get_confidence()` for `AgentAvatarEffect`
2. Apply smoothing to incoming values using exponential moving average with factor 0.1
3. Update internal parameters via `set_parameter()`
4. Call `apply_uniforms()` to upload to GPU

Persistent state includes the emotional state machine (e.g., "thinking", "confident", "overwhelmed") and accumulated confidence values over time. The state machine uses a hysteresis mechanism to prevent rapid toggling: confidence must exceed 0.7 for at least 0.5 seconds to transition to "confident", and must drop below 0.3 to transition to "overwhelmed". This prevents flickering between states due to transient audio spikes or sensor noise.

Init-once operations occur in the `__init__()` method: shader program compilation, uniform location caching, and face cascade loading. These operations are expensive and must not be repeated per-frame. The `Effect` base class handles shader compilation and provides the `self.shader` object; the avatar effect calls `self.shader.compile()` during initialization and checks for errors.

Global state synchronization through `SyncManager` is the key to multi-node coordination. The `SyncManager` runs as a separate process or thread that aggregates agent state from all nodes and broadcasts it via shared memory or network. Each `TravelingAvatarEffect` instance receives the same global state but computes its own local position based on `node_id`. This decentralized approach allows each node to render independently without a central render server.

State interpolation uses time-based blending: when a target emotional state changes, the parameters don't jump immediately. Instead, the `update()` method computes `new_value = lerp(current_value, target_value, delta_time * transition_speed)` where `transition_speed` is typically 2.0 Hz. This creates smooth 0.5-second transitions that feel organic and avoid visual pops.

## GPU Resources
The avatar effect's GPU footprint is minimal compared to depth-based effects that require large framebuffers. The primary resource is the shader program itself, stored as a compiled binary in the GPU driver. The `AVATAR_FRAGMENT_SHADER` is shared across all avatar instances; only the uniform values differ per instance. Uniforms are set via `glUniform` calls, which write directly to the currently bound program's uniform buffer.

The required uniforms are:
- `avatar_position` (vec2): normalized screen coordinates (0.0-1.0)
- `avatar_scale` (float): size multiplier
- `avatar_alpha` (float): overall opacity
- `spin_speed` (float): rotation rate in radians per second
- `glow_intensity` (float): brightness multiplier
- `confidence` (float): agent confidence 0.0-1.0
- `fragmentation` (float): breakup amount 0.0-1.0
- `glow_color` (vec3): RGB color in linear space

For shadow mode, additional resources include:
- `shadow_mode_enabled` (int): 0 or 1 flag
- `has_shadow_mask` (int): 0 or 1 flag indicating IR frame availability
- `shadow_mask` (sampler2D): IR heat texture (typically single-channel 8-bit)

No framebuffer objects (FBOs) are required because the avatar renders directly to the main framebuffer as part of the effect chain. The effect does not perform multi-pass rendering or require intermediate texture storage. This keeps memory usage low: each avatar instance consumes only a few uniform values (approximately 64 bytes) plus optional shadow mask texture (typically 256x256 or 512x512 bytes).

GPU memory optimization is achieved through:
- **Shared shader programs**: The shader is compiled once and bound for all avatar draws
- **Texture reuse**: The IR shadow mask texture is created once and updated in-place each frame
- **Uniform buffer objects (UBOs)**: Not currently used but could batch multiple avatar instances into a single UBO for reduced driver overhead

The effect is designed to scale to dozens of simultaneous avatar instances across multiple nodes without exhausting GPU memory, which is critical for large multi-screen installations.

## Test Plan
The test plan validates core functionality, edge cases, and integration points. Tests should be written using pytest with fixtures for mock `SyncManager` and `SurfaceIRSource` objects.

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_sync_manager` | Module initializes correctly when `sync_manager` is `None` or missing; avatar defaults to off-screen position |
| `test_update_from_global_state` | Avatar parameters update properly based on global state and position; `local_pos >= 0.0` triggers visibility |
| `test_apply_uniforms` | Shader uniforms are set with correct avatar values; uniform locations are cached after first use |
| `test_visibility_on_node` | Avatar appears only when within node viewport (`local_pos >= 0.0`); alpha set to 1.0 |
| `test_visibility_off_node` | Avatar is invisible when outside node viewport (`local_pos < 0.0`); alpha set to 0.0 |
| `test_shadow_mode` | Avatar appears only where IR heat is detected; shadow mask texture sampling works correctly |
| `test_eye_tracking` | Avatar gaze follows detected face position; `face_position` updates from `_detect_face()` |
| `test_emotional_states` | Avatar reacts to different emotional states: `confidence` and `fragmentation` values produce expected visual changes |
| `test_edge_cases` | Handles boundary conditions like zero confidence, maximum glow intensity, and edge case position values |

**Edge Case Considerations**
- Zero confidence values should maintain avatar visibility but with minimal glow (color becomes mostly white)
- Maximum glow intensity should not cause visual artifacts (clamped to 2.0, may cause bloom in HDR pipelines)
- Position values at exact boundary (`local_pos = 0.0`) should be handled consistently (visible with alpha=1.0)
- IR data absence should gracefully degrade shadow mode functionality (avatar fully visible, no shadow masking)
- Face detection loss should trigger appropriate fallback behavior (gaze freezes at last known position, `eye_tracking_enabled` can be set to `False` to disable)

**Minimum coverage:** 80% before task is marked done.

**Definition of Done**
- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT004: agent_avatar` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
