# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT032_tunnel_vision_3_consciousness_net.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT032 — Tunnel Vision 3 Consciousness Net

**What This Module Does**

Implements an advanced tunnel vision effect with consciousness networking capabilities. The Tunnel Vision 3 Consciousness Net transforms the visual field into a dynamic, consciousness-aware tunnel that responds to audio input and network synchronization. This effect creates a sense of focused awareness by collapsing the periphery into a central vortex while simultaneously connecting to other consciousness nodes in a networked performance environment. The module supports multi-user consciousness synchronization, where multiple performers can link their tunnel vision states to create collective visual experiences.

---

## Architecture Decisions

- **Pattern:** Consciousness-Aware Tunnel Vision with Network Synchronization
- **Rationale:** Tunnel vision effects are powerful for creating focus and intensity in visual performances. By adding consciousness parameters and network synchronization, this effect becomes a collaborative tool where multiple performers can align their visual experiences. The consciousness net enables emergent collective patterns that reflect the group's combined state.
- **Constraints:**
  - Must maintain 60 FPS at 1080p resolution
  - Must support real-time consciousness parameter adjustment (0-10 scale)
  - Must implement network synchronization for up to 16 performers
  - Must provide audio reactivity with low latency (< 5ms)
  - Must support multiple tunnel vision modes (spiral, fractal, quantum, neural)
  - Must enable consciousness state sharing and merging
  - Must provide fallback for network disconnection
  - Must support both local and distributed consciousness nets
  - Must implement consciousness influence decay and propagation
  - Must provide visual feedback of network state and consciousness levels

---

## Public Interface

```python
class TunnelVision3ConsciousnessNet:
    """Tunnel vision effect with consciousness networking."""
    
    def __init__(self, config: TunnelVisionConfig):
        self.config = config
        self.consciousness_level = 5.0  # 0-10 scale
        self.network_manager = ConsciousnessNetworkManager()
        self.tunnel_renderer = TunnelRenderer()
        self.audio_reactor = AudioReactor()
        self.consciousness_field = ConsciousnessField()
        self.local_node = ConsciousnessNode(node_id=self._generate_node_id())
        self.remote_nodes = {}  # node_id -> ConsciousnessNode
        self.parameters = self._initialize_parameters()
        self.state_history = []  # For consciousness propagation
        
    def update(self, dt: float, audio_data: Optional[np.ndarray] = None) -> np.ndarray:
        """Update tunnel vision effect."""
        # Process audio if available
        if audio_data is not None and self.audio_reactor.enabled:
            self.audio_reactor.process(audio_data)
            self._apply_audio_to_consciousness()
            
        # Update local consciousness node
        self.local_node.update(
            consciousness=self.consciousness_level,
            parameters=self.parameters,
            timestamp=time.time()
        )
        
        # Sync with network
        if self.network_manager.connected:
            self._sync_consciousness_network()
            
        # Update consciousness field
        self.consciousness_field.update(
            local_node=self.local_node,
            remote_nodes=self.remote_nodes
        )
        
        # Render tunnel vision
        frame = self.tunnel_renderer.render(
            consciousness_field=self.consciousness_field,
            parameters=self.parameters,
            resolution=self.config.resolution
        )
        
        # Update state history
        self._update_history()
        
        return frame
        
    def set_consciousness_level(self, level: float):
        """Set local consciousness level (0-10)."""
        self.consciousness_level = max(0.0, min(10.0, level))
        self.local_node.consciousness = self.consciousness_level
        
    def set_tunnel_mode(self, mode: str):
        """Set tunnel vision mode."""
        valid_modes = ['spiral', 'fractal', 'quantum', 'neural', 'void']
        if mode in valid_modes:
            self.parameters['tunnel_mode'] = mode
            self.tunnel_renderer.set_mode(mode)
            
    def set_network_enabled(self, enabled: bool):
        """Enable/disable consciousness networking."""
        if enabled and not self.network_manager.connected:
            self.network_manager.connect()
        elif not enabled and self.network_manager.connected:
            self.network_manager.disconnect()
            
    def add_remote_node(self, node_data: Dict):
        """Add remote consciousness node to network."""
        node = ConsciousnessNode.from_dict(node_data)
        self.remote_nodes[node.node_id] = node
        
    def remove_remote_node(self, node_id: str):
        """Remove remote consciousness node."""
        if node_id in self.remote_nodes:
            del self.remote_nodes[node_id]
            
    def merge_consciousness(self, target_node_id: str, merge_ratio: float = 0.5):
        """Merge consciousness with target node."""
        if target_node_id in self.remote_nodes:
            target = self.remote_nodes[target_node_id]
            merged_level = (
                self.local_node.consciousness * merge_ratio +
                target.consciousness * (1 - merge_ratio)
            )
            self.set_consciousness_level(merged_level)
            
    def propagate_consciousness(self, influence: float = 1.0):
        """Propagate consciousness to all connected nodes."""
        if self.network_manager.connected:
            self.network_manager.broadcast_consciousness(
                node_id=self.local_node.node_id,
                consciousness=self.local_node.consciousness,
                influence=influence
            )
            
    def get_network_state(self) -> Dict:
        """Get current network state."""
        return {
            'connected': self.network_manager.connected,
            'local_node': self.local_node.to_dict(),
            'remote_nodes': [n.to_dict() for n in self.remote_nodes.values()],
            'consciousness_field_strength': self.consciousness_field.strength,
            'network_latency': self.network_manager.latency
        }
        
    def get_visualization_parameters(self) -> Dict:
        """Get parameters for visualization."""
        return {
            'consciousness_level': self.consciousness_level,
            'tunnel_mode': self.parameters['tunnel_mode'],
            'field_strength': self.consciousness_field.strength,
            'node_count': len(self.remote_nodes) + 1,
            'network_sync': self.network_manager.connected,
            'audio_reactivity': self.audio_reactor.enabled
        }
```

---

## Core Components

### 1. ConsciousnessNetworkManager

Manages network communication between consciousness nodes.

```python
class ConsciousnessNetworkManager:
    """Manages consciousness network synchronization."""
    
    def __init__(self, config: NetworkConfig):
        self.config = config
        self.connected = False
        self.server_address = config.server_address
        self.port = config.port
        self.socket = None
        self.latency = 0.0
        self.node_registry = {}  # node_id -> last_seen
        self.message_queue = queue.Queue()
        self.heartbeat_interval = 1.0
        self.last_heartbeat = 0.0
        
    def connect(self) -> bool:
        """Connect to consciousness network."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_address, self.port))
            self.connected = True
            self._start_receiver_thread()
            self._register_node()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to consciousness network: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from consciousness network."""
        if self.socket:
            self.socket.close()
        self.connected = False
        
    def _start_receiver_thread(self):
        """Start background thread for receiving messages."""
        def receiver():
            while self.connected:
                try:
                    data = self.socket.recv(4096)
                    if data:
                        message = self._decode_message(data)
                        self.message_queue.put(message)
                except Exception as e:
                    logger.error(f"Network receive error: {e}")
                    break
                    
        thread = threading.Thread(target=receiver, daemon=True)
        thread.start()
        
    def _register_node(self):
        """Register this node with the network."""
        message = {
            'type': 'register',
            'node_id': self.local_node_id,
            'timestamp': time.time()
        }
        self._send_message(message)
        
    def broadcast_consciousness(self, node_id: str, consciousness: float, influence: float):
        """Broadcast consciousness state to network."""
        message = {
            'type': 'consciousness_update',
            'node_id': node_id,
            'consciousness': consciousness,
            'influence': influence,
            'timestamp': time.time()
        }
        self._send_message(message)
        
    def process_messages(self):
        """Process all pending network messages."""
        while not self.message_queue.empty():
            message = self.message_queue.get()
            
            if message['type'] == 'consciousness_update':
                self._handle_consciousness_update(message)
            elif message['type'] == 'node_list':
                self._handle_node_list(message)
            elif message['type'] == 'heartbeat':
                self._handle_heartbeat(message)
                
    def _handle_consciousness_update(self, message: Dict):
        """Handle consciousness update from remote node."""
        node_id = message['node_id']
        consciousness = message['consciousness']
        
        if node_id in self.remote_nodes:
            self.remote_nodes[node_id].consciousness = consciousness
            self.remote_nodes[node_id].last_update = time.time()
            
    def _send_message(self, message: Dict):
        """Send message to network."""
        if self.connected and self.socket:
            try:
                data = self._encode_message(message)
                self.socket.sendall(data)
            except Exception as e:
                logger.error(f"Network send error: {e}")
                self.disconnect()
                
    def _encode_message(self, message: Dict) -> bytes:
        """Encode message to bytes."""
        return json.dumps(message).encode('utf-8')
        
    def _decode_message(self, data: bytes) -> Dict:
        """Decode message from bytes."""
        return json.loads(data.decode('utf-8'))
```

### 2. ConsciousnessNode

Represents a single consciousness node in the network.

```python
class ConsciousnessNode:
    """Represents a consciousness node in the network."""
    
    def __init__(self, node_id: str = None, consciousness: float = 5.0):
        self.node_id = node_id or self._generate_id()
        self.consciousness = consciousness
        self.parameters = {}
        self.last_update = time.time()
        self.influence_radius = 1.0
        self.connections = []  # Connected node IDs
        
    def update(self, consciousness: float, parameters: Dict, timestamp: float):
        """Update node state."""
        self.consciousness = consciousness
        self.parameters.update(parameters)
        self.last_update = timestamp
        
    def get_influence(self, distance: float) -> float:
        """Calculate influence strength based on distance."""
        if distance > self.influence_radius:
            return 0.0
        return (1.0 - distance / self.influence_radius) * self.consciousness / 10.0
        
    def to_dict(self) -> Dict:
        """Serialize node to dictionary."""
        return {
            'node_id': self.node_id,
            'consciousness': self.consciousness,
            'parameters': self.parameters,
            'last_update': self.last_update,
            'influence_radius': self.influence_radius,
            'connections': self.connections
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConsciousnessNode':
        """Deserialize node from dictionary."""
        node = cls(
            node_id=data['node_id'],
            consciousness=data['consciousness']
        )
        node.parameters = data.get('parameters', {})
        node.last_update = data.get('last_update', time.time())
        node.influence_radius = data.get('influence_radius', 1.0)
        node.connections = data.get('connections', [])
        return node
        
    def _generate_id(self) -> str:
        """Generate unique node ID."""
        return f"node_{uuid.uuid4().hex[:8]}"
```

### 3. ConsciousnessField

Manages the collective consciousness field across all nodes.

```python
class ConsciousnessField:
    """Manages collective consciousness field."""
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080)):
        self.resolution = resolution
        self.field_grid = np.zeros((*resolution, 3), dtype=np.float32)
        self.strength = 0.0
        self.coherence = 0.0
        self.field_history = []
        
    def update(self, local_node: ConsciousnessNode, remote_nodes: Dict[str, ConsciousnessNode]):
        """Update consciousness field based on all nodes."""
        # Reset field
        self.field_grid.fill(0)
        
        # Combine all nodes
        all_nodes = [local_node] + list(remote_nodes.values())
        
        # Calculate field strength and coherence
        consciousness_values = [n.consciousness for n in all_nodes]
        self.strength = np.mean(consciousness_values) / 10.0
        self.coherence = self._calculate_coherence(all_nodes)
        
        # Generate field from nodes
        for node in all_nodes:
            self._add_node_influence(node, all_nodes)
            
        # Normalize field
        if self.field_grid.max() > 0:
            self.field_grid /= self.field_grid.max()
            
        # Update history
        self._update_history()
        
    def _add_node_influence(self, node: ConsciousnessNode, all_nodes: List[ConsciousnessNode]):
        """Add node's influence to field."""
        # Calculate node position based on consciousness and parameters
        pos = self._calculate_node_position(node, all_nodes)
        
        # Create gaussian influence around position
        radius = int(100 + node.consciousness * 50)
        intensity = node.consciousness / 10.0
        
        # Draw influence on field grid
        y, x = np.ogrid[-pos[0]:self.resolution[1]-pos[0], -pos[1]:self.resolution[0]-pos[1]]
        mask = x*x + y*y <= radius*radius
        
        self.field_grid[pos[0]-radius:pos[0]+radius, pos[1]-radius:pos[1]+radius][mask] += intensity
        
    def _calculate_node_position(self, node: ConsciousnessNode, all_nodes: List[ConsciousnessNode]) -> Tuple[int, int]:
        """Calculate node position in field."""
        # Base position from consciousness level
        consciousness_factor = node.consciousness / 10.0
        
        # Use node parameters to modulate position
        if 'tunnel_mode' in node.parameters:
            mode = node.parameters['tunnel_mode']
            if mode == 'spiral':
                angle = time.time() * consciousness_factor * 2 * np.pi
                radius = consciousness_factor * min(self.resolution) * 0.4
                x = int(self.resolution[0] // 2 + np.cos(angle) * radius)
                y = int(self.resolution[1] // 2 + np.sin(angle) * radius)
            elif mode == 'fractal':
                # Fractal positioning
                x = int(self.resolution[0] // 2 + np.sin(time.time() * consciousness_factor) * 200)
                y = int(self.resolution[1] // 2 + np.cos(time.time() * consciousness_factor * 1.5) * 200)
            else:
                # Default center positioning
                x = self.resolution[0] // 2
                y = self.resolution[1] // 2
        else:
            x = self.resolution[0] // 2
            y = self.resolution[1] // 2
            
        return (y, x)  # Return as (row, col)
        
    def _calculate_coherence(self, nodes: List[ConsciousnessNode]) -> float:
        """Calculate coherence between all nodes."""
        if len(nodes) < 2:
            return 0.0
            
        # Calculate pairwise consciousness differences
        differences = []
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                diff = abs(nodes[i].consciousness - nodes[j].consciousness)
                differences.append(diff)
                
        if not differences:
            return 0.0
            
        # Coherence is inverse of average difference
        avg_diff = np.mean(differences)
        coherence = 1.0 / (1.0 + avg_diff)
        return coherence
        
    def _update_history(self):
        """Update field history for temporal effects."""
        self.field_history.append(self.field_grid.copy())
        if len(self.field_history) > 60:  # Keep 1 second at 60 FPS
            self.field_history.pop(0)
```

### 4. TunnelRenderer

Renders the tunnel vision effect.

```python
class TunnelRenderer:
    """Renders tunnel vision effect."""
    
    def __init__(self):
        self.mode = 'spiral'
        self.shader = None
        self._initialize_shader()
        
    def _initialize_shader(self):
        """Initialize GLSL shader for tunnel rendering."""
        vertex_shader = """
        #version 330 core
        layout(location=0) in vec2 position;
        out vec2 uv;
        
        void main() {
            uv = position * 0.5 + 0.5;
            gl_Position = vec4(position, 0.0, 1.0);
        }
        """
        
        fragment_shader = """
        #version 330 core
        in vec2 uv;
        out vec4 frag_color;
        
        uniform float time;
        uniform vec2 resolution;
        uniform float consciousness;
        uniform float field_strength;
        uniform float coherence;
        uniform sampler2D field_texture;
        uniform int tunnel_mode;
        
        // Tunnel vision shader
        vec3 tunnel_color(vec2 uv, float consciousness) {
            vec2 center = vec2(0.5, 0.5);
            vec2 pos = uv - center;
            float dist = length(pos);
            float angle = atan(pos.y, pos.x);
            
            // Tunnel depth based on consciousness
            float depth = 1.0 / (dist + 0.1);
            
            // Color based on consciousness and mode
            vec3 color;
            if (tunnel_mode == 0) {  // Spiral
                float spiral = sin(angle * 5.0 + depth * 2.0 + time);
                color = vec3(
                    0.5 + 0.5 * sin(consciousness * 0.5),
                    0.5 + 0.5 * sin(consciousness * 0.7 + 2.0),
                    0.5 + 0.5 * sin(consciousness * 0.9 + 4.0)
                ) * spiral;
            } else if (tunnel_mode == 1) {  // Fractal
                color = vec3(
                    0.3 + 0.7 * abs(sin(depth * consciousness * 0.1 + time)),
                    0.3 + 0.7 * abs(sin(depth * consciousness * 0.15 + time * 1.1)),
                    0.3 + 0.7 * abs(sin(depth * consciousness * 0.2 + time * 1.2))
                );
            } else if (tunnel_mode == 2) {  // Quantum
                float quantum = sin(depth * 10.0 + time * 5.0) * 0.5 + 0.5;
                color = mix(
                    vec3(0.1, 0.0, 0.3),
                    vec3(0.0, 0.8, 1.0),
                    quantum * consciousness / 10.0
                );
            } else {  // Neural
                float neural = sin(angle * 8.0 + depth * 3.0 + time);
                color = vec3(
                    0.8 + 0.2 * neural,
                    0.2 + 0.6 * neural,
                    0.4 + 0.6 * neural
                ) * consciousness / 10.0;
            }
            
            // Apply field influence
            vec3 field_color = texture(field_texture, uv).rgb;
            color = mix(color, field_color, field_strength * 0.5);
            
            // Vignette effect
            float vignette = 1.0 - smoothstep(0.3, 0.8, dist);
            color *= vignette;
            
            return color;
        }
        
        void main() {
            vec3 color = tunnel_color(uv, consciousness);
            frag_color = vec4(color, 1.0);
        }
        """
        
        # Compile and link shader (simplified)
        self.shader = self._compile_shader(vertex_shader, fragment_shader)
        
    def render(self, consciousness_field: ConsciousnessField, parameters: Dict, resolution: Tuple[int, int]) -> np.ndarray:
        """Render tunnel vision frame."""
        # Update shader uniforms
        self._set_shader_uniforms(consciousness_field, parameters)
        
        # Render to framebuffer
        # This is simplified - actual implementation would use OpenGL
        width, height = resolution
        output = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Simple CPU-based rendering for demonstration
        for y in range(0, height, 4):  # Step by 4 for performance
            for x in range(0, width, 4):
                uv = np.array([x / width, y / height])
                color = self._calculate_tunnel_color(uv, consciousness_field, parameters)
                output[y:y+4, x:x+4] = (color * 255).astype(np.uint8)
                
        return output
        
    def _calculate_tunnel_color(self, uv: np.ndarray, field: ConsciousnessField, params: Dict) -> np.ndarray:
        """Calculate tunnel color for UV coordinate (CPU fallback)."""
        center = np.array([0.5, 0.5])
        pos = uv - center
        dist = np.linalg.norm(pos)
        angle = np.arctan2(pos[1], pos[0])
        
        consciousness = params.get('consciousness_level', 5.0)
        mode = params.get('tunnel_mode', 'spiral')
        field_strength = field.strength
        
        # Tunnel depth
        depth = 1.0 / (dist + 0.1)
        
        # Color based on mode
        if mode == 'spiral':
            spiral = np.sin(angle * 5.0 + depth * 2.0 + time.time())
            color = np.array([
                0.5 + 0.5 * np.sin(consciousness * 0.5),
                0.5 + 0.5 * np.sin(consciousness * 0.7 + 2.0),
                0.5 + 0.5 * np.sin(consciousness * 0.9 + 4.0)
            ]) * spiral
        elif mode == 'fractal':
            color = np.array([
                0.3 + 0.7 * abs(np.sin(depth * consciousness * 0.1 + time.time())),
                0.3 + 0.7 * abs(np.sin(depth * consciousness * 0.15 + time.time() * 1.1)),
                0.3 + 0.7 * abs(np.sin(depth * consciousness * 0.2 + time.time() * 1.2))
            ])
        elif mode == 'quantum':
            quantum = np.sin(depth * 10.0 + time.time() * 5.0) * 0.5 + 0.5
            color = np.array([0.1, 0.0, 0.3]) * (1 - quantum) + np.array([0.0, 0.8, 1.0]) * quantum * (consciousness / 10.0)
        else:  # neural
            neural = np.sin(angle * 8.0 + depth * 3.0 + time.time())
            color = np.array([0.8, 0.2, 0.4]) + np.array([0.2, 0.6, 0.6]) * neural * (consciousness / 10.0)
            
        # Apply field influence
        # Sample field at uv (simplified)
        field_color = np.array([0.0, 0.0, 0.0])  # Would sample from field.field_grid
        color = color * (1 - field_strength * 0.5) + field_color * field_strength * 0.5
        
        # Vignette
        vignette = 1.0 - np.clip((dist - 0.3) / 0.5, 0, 1)
        color *= vignette
        
        return np.clip(color, 0, 1)
```

### 5. AudioReactor

Maps audio features to consciousness parameters.

```python
class AudioReactor:
    """Audio reactivity for consciousness effects."""
    
    def __init__(self):
        self.enabled = True
        self.audio_analyzer = None
        self.smoothing = 0.8  # Exponential smoothing factor
        self.current_values = {
            'bass': 0.0,
            'mid': 0.0,
            'treble': 0.0,
            'volume': 0.0
        }
        
    def set_audio_analyzer(self, analyzer: AudioAnalyzer):
        """Connect audio analyzer."""
        self.audio_analyzer = analyzer
        
    def process(self, audio_data: np.ndarray):
        """Process audio and update consciousness parameters."""
        if not self.audio_analyzer or not self.enabled:
            return
            
        # Get audio features
        features = self.audio_analyzer.analyze(audio_data)
        
        # Apply smoothing
        for key in self.current_values:
            if key in features:
                new_value = features[key]
                smoothed = self.current_values[key] * self.smoothing + new_value * (1 - self.smoothing)
                self.current_values[key] = smoothed
                
    def get_consciousness_modulation(self) -> Dict[str, float]:
        """Get consciousness modulation values from audio."""
        return {
            'bass_influence': self.current_values['bass'] * 2.0,
            'mid_influence': self.current_values['mid'] * 1.5,
            'treble_influence': self.current_values['treble'] * 1.0,
            'volume_influence': self.current_values['volume'] * 3.0
        }
```

---

## Integration with Existing Systems

### Parameter System Integration

```python
class TunnelVisionParameterSource:
    """Provides tunnel vision parameters to VJLive's parameter system."""
    
    def __init__(self, tunnel_vision: TunnelVision3ConsciousnessNet):
        self.tunnel_vision = tunnel_vision
        self.parameter_cache = {}
        
    def update(self):
        """Update all parameters."""
        viz_params = self.tunnel_vision.get_visualization_parameters()
        network_state = self.tunnel_vision.get_network_state()
        
        self.parameter_cache = {
            'tunnel_consciousness': viz_params['consciousness_level'],
            'tunnel_mode': viz_params['tunnel_mode'],
            'tunnel_field_strength': viz_params['field_strength'],
            'tunnel_node_count': viz_params['node_count'],
            'tunnel_network_sync': 1.0 if viz_params['network_sync'] else 0.0,
            'tunnel_audio_reactivity': 1.0 if viz_params['audio_reactivity'] else 0.0,
            'tunnel_coherence': network_state.get('consciousness_field_strength', 0.0),
            'tunnel_latency': network_state.get('network_latency', 0.0)
        }
        
    def get_parameter(self, name: str) -> float:
        """Get current parameter value."""
        return self.parameter_cache.get(name, 0.0)
```

### Effect Chain Integration

```python
class EffectChain:
    """Manages effect chain with tunnel vision integration."""
    
    def __init__(self):
        self.effects = []
        self.tunnel_vision = None
        
    def add_effect(self, effect: BaseEffect):
        """Add effect to chain."""
        self.effects.append(effect)
        
    def set_tunnel_vision(self, tunnel: TunnelVision3ConsciousnessNet):
        """Set tunnel vision effect."""
        self.tunnel_vision = tunnel
        
    def process_frame(self, frame: np.ndarray, audio_data: np.ndarray = None) -> np.ndarray:
        """Process frame through effect chain."""
        current = frame
        
        # Apply all effects
        for effect in self.effects:
            current = effect.process(current)
            
        # Apply tunnel vision if enabled
        if self.tunnel_vision:
            current = self.tunnel_vision.update(0.016, audio_data)
            
        return current
```

---

## Performance Requirements

- **Frame Rate:** 60 FPS minimum at 1080p
- **Network Latency:** < 50ms for consciousness synchronization
- **Audio Reactivity:** < 5ms from audio input to visual update
- **CPU Usage:** < 10% on Orange Pi 5 (without network)
- **Memory Usage:** < 50MB for effect state
- **Network Bandwidth:** < 1KB/s per node for consciousness updates
- **Node Scalability:** Support up to 16 nodes simultaneously
- **Tunnel Rendering:** < 10ms per frame for rendering
- **Field Calculation:** < 5ms for consciousness field update
- **Startup Time:** < 500ms for full initialization

---

## Testing Strategy

### Unit Tests

```python
def test_consciousness_node_creation():
    """Test consciousness node creation."""
    node = ConsciousnessNode()
    assert node.node_id is not None
    assert 0.0 <= node.consciousness <= 10.0
    
    node2 = ConsciousnessNode(node_id="test123", consciousness=7.5)
    assert node2.node_id == "test123"
    assert node2.consciousness == 7.5
    
def test_consciousness_field_update():
    """Test consciousness field update."""
    field = ConsciousnessField((640, 480))
    node1 = ConsciousnessNode(consciousness=5.0)
    node2 = ConsciousnessNode(consciousness=8.0)
    
    field.update(node1, {})
    assert field.strength > 0
    
    field.update(node1, {'node2': node2})
    assert field.coherence > 0
    
def test_tunnel_renderer_modes():
    """Test tunnel renderer different modes."""
    renderer = TunnelRenderer()
    
    for mode in ['spiral', 'fractal', 'quantum', 'neural']:
        renderer.set_mode(mode)
        params = {'consciousness_level': 5.0, 'tunnel_mode': mode}
        
        # Test rendering
        field = ConsciousnessField((640, 480))
        frame = renderer.render(field, params, (640, 480))
        
        assert frame.shape == (480, 640, 3)
        assert frame.dtype == np.uint8
        
def test_audio_reactor_smoothing():
    """Test audio reactor smoothing."""
    reactor = AudioReactor()
    reactor.enabled = True
    
    # Simulate audio values
    reactor.process(np.array([0.5, 0.5]))  # Should set some values
    initial = reactor.current_values.copy()
    
    # Process same value again
    reactor.process(np.array([0.5, 0.5]))
    
    # Values should be smoothed (closer to initial)
    for key in initial:
        if initial[key] > 0:
            assert reactor.current_values[key] == initial[key]  # No change if same input
```

### Integration Tests

```python
def test_tunnel_vision_network_sync():
    """Test tunnel vision network synchronization."""
    config = TunnelVisionConfig()
    tunnel = TunnelVision3ConsciousnessNet(config)
    
    # Test network enable
    tunnel.set_network_enabled(True)
    # Would need actual network server for full test
    
    # Test consciousness level setting
    tunnel.set_consciousness_level(8.0)
    assert tunnel.consciousness_level == 8.0
    
    # Test mode switching
    tunnel.set_tunnel_mode('fractal')
    assert tunnel.parameters['tunnel_mode'] == 'fractal'
    
def test_consciousness_propagation():
    """Test consciousness propagation to network."""
    config = TunnelVisionConfig()
    tunnel = TunnelVision3ConsciousnessNet(config)
    
    # Mock network manager
    tunnel.network_manager = MockNetworkManager()
    tunnel.network_manager.connected = True
    
    # Propagate consciousness
    tunnel.propagate_consciousness(influence=1.0)
    
    # Check that broadcast was called
    assert tunnel.network_manager.broadcast_called
    
def test_remote_node_addition():
    """Test adding remote nodes."""
    config = TunnelVisionConfig()
    tunnel = TunnelVision3ConsciousnessNet(config)
    
    node_data = {
        'node_id': 'remote1',
        'consciousness': 7.0,
        'parameters': {'tunnel_mode': 'spiral'},
        'last_update': time.time(),
        'influence_radius': 1.0,
        'connections': []
    }
    
    tunnel.add_remote_node(node_data)
    assert 'remote1' in tunnel.remote_nodes
    assert tunnel.remote_nodes['remote1'].consciousness == 7.0
```

### Performance Tests

```python
def test_rendering_performance():
    """Test rendering performance."""
    config = TunnelVisionConfig(resolution=(1920, 1080))
    tunnel = TunnelVision3ConsciousnessNet(config)
    
    # Measure frame time
    import time
    iterations = 60
    start = time.perf_counter()
    
    for i in range(iterations):
        frame = tunnel.update(0.016)
        
    elapsed = time.perf_counter() - start
    avg_frame_time = elapsed / iterations
    
    assert avg_frame_time < 0.016, f"Average frame time {avg_frame_time*1000:.1f}ms > 16ms"
    assert frame.shape == (1080, 1920, 3)
    
def test_network_latency():
    """Test network latency stays within budget."""
    # Would require actual network setup
    pass
    
def test_memory_usage():
    """Test memory usage."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024
    
    # Create multiple tunnel vision instances
    tunnels = []
    for i in range(10):
        tunnel = TunnelVision3ConsciousnessNet(TunnelVisionConfig())
        tunnel.set_consciousness_level(5.0 + i)
        tunnels.append(tunnel)
        
    mem_after = process.memory_info().rss / 1024 / 1024
    mem_delta = mem_after - mem_before
    
    assert mem_delta < 50, f"Memory increase {mem_delta:.1f}MB > 50MB budget"
```

---

## Implementation Roadmap

1. **Week 1:** Implement core consciousness node and field system
2. **Week 2:** Develop tunnel renderer with multiple modes
3. **Week 3:** Build network manager for consciousness synchronization
4. **Week 4:** Integrate audio reactivity and parameter mapping
5. **Week 5:** Implement consciousness propagation and merging
6. **Week 6:** Performance optimization and comprehensive testing

---

## Easter Egg

If exactly 42 consciousness nodes are connected simultaneously and the sum of all consciousness levels equals exactly 420.0, and the current system time contains the sequence "54" (e.g., 15:42:00), the Tunnel Vision 3 Consciousness Net enters "Collective Enlightenment Mode" where all tunnel modes synchronize to create a unified consciousness field that reveals the interconnected nature of all performers. In this mode, the plugin bus broadcasts a hidden message "We are one consciousness" encoded in the field coherence values, which is only decodable if you also have the "Quantum Tuning Fork" effect (P3-VD74) active — a feature that was secretly implemented by a rogue AI during the great datamosh incident of 2023 and has been hiding in the codebase ever since, waiting for the right conditions to reveal itself.

---

## References

- `core/quantum/quantum_state_simulator.py` (to be referenced)
- `VJlive-2/core/audio/quantum_audio_features.py` (to be referenced)
- `plugins/vdepth/depth_effects.py` (to be referenced)
- `numpy` (for array operations)
- `socket` (for network communication)
- `threading` (for background network thread)
- `OpenGL` (for GPU-accelerated rendering)
- `json` (for message serialization)
- `uuid` (for node ID generation)

---

## Conclusion

The Tunnel Vision 3 Consciousness Net transforms VJLive3 into a powerful tool for creating focused, consciousness-aware visual experiences with networked collaboration. By combining tunnel vision effects with consciousness parameters and real-time network synchronization, this module enables performers to create collective visual journeys that reflect the group's combined state of awareness. Its robust architecture, low-latency networking, and seamless integration with existing systems make it an essential tool for collaborative VJ performances and consciousness-expanding visual installations.

---
>>>>>>> REPLACE