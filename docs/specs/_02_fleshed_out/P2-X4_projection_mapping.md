# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P2-X4_projection_mapping.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-X4 — Projection Mapping

**What This Module Does**

Implements an automated surface detection and calibration system that enables VJLive3 to project content onto arbitrary 3D surfaces with pixel-perfect accuracy. The Projection Mapping module combines structured light scanning, mesh-based warping, and real-time calibration to transform VJLive's output into precisely aligned projections on complex physical environments. This module eliminates manual alignment workflows and enables dynamic, real-time adaptation to moving surfaces, enabling immersive installations, architectural projection, and interactive performance art.

---

## Architecture Decisions

- **Pattern:** Structured Light Scanning with Mesh-Based Warping and Real-Time Calibration
- **Rationale:** Projection mapping requires precise geometric alignment between the virtual scene and physical surface. A structured light approach provides dense 3D point clouds that can be converted to mesh geometry, while mesh-based warping allows for precise pixel manipulation. Real-time calibration ensures robustness against surface movement and environmental changes. This architecture provides sub-millimeter accuracy while maintaining real-time performance.
- **Constraints:**
  - Must support surfaces up to 10m x 10m with 0.1mm precision
  - Must operate at 60 FPS for live performance applications
  - Must handle dynamic surfaces with movement tracking
  - Must support multiple simultaneous projectors
  - Must provide visual feedback of mapping accuracy
  - Must integrate with existing effect chain system
  - Must support automated calibration workflows
  - Must maintain compatibility with existing rendering pipeline
  - Must provide fallback modes for low-feature surfaces
  - Must support manual override for fine-tuning
  - Must log calibration data for reproducibility
  - Must support network discovery of projectors
  - Must handle coordinate system transformations between camera and projector spaces

---

## Public Interface

```python
class ProjectionMappingManager:
    """Manages the complete projection mapping workflow."""
    
    def __init__(self, config: ProjectionMappingConfig) -> None:...
    def start_calibration(self) -> bool:...
    def stop_calibration(self) -> None:...
    def update_calibration(self) -> bool:...
    def apply_warp(self, texture: Texture) -> Texture:...
    def get_calibration_data(self) -> dict:...
    def save_calibration(self, filepath: str) -> bool:...
    def load_calibration(self, filepath: str) -> bool:...
    def calibrate_surface(self, surface_id: str) -> bool:...
    def track_surface_motion(self, surface_id: str) -> bool:...
    def get_surface_status(self, surface_id: str) -> dict:...
    def subscribe(self, event: str, callback: Callable) -> None:...
    def unsubscribe(self, event: str, callback: Callable) -> None:...
    def get_stats(self) -> dict:...

class ProjectionMappingConfig:
    """Configuration for projection mapping system."""
    
    def __init__(self,
                 enabled: bool = True,
                 camera_id: int = 0,
                 projector_count: int = 1,
                 calibration_algorithm: str = "auto",
                 point_cloud_density: int = 5000,
                 mesh_simplification: float = 0.1,
                 max_iterations: int = 10,
                 tolerance: float = 0.001,
                 network_discovery: bool = True,
                 auto_calibrate: bool = True) -> None:...
    def validate(self) -> List[str]:...

class MeshWarper:
    """Handles mesh-based warping operations."""
    
    def __init__(self, mesh: Mesh, warping_algorithm: str = "perspective"):
        # ...
    def warp(self, source: np.ndarray, target: np.ndarray) -> np.ndarray:...
    def optimize_warp(self, correspondences: List[Tuple[np.ndarray, np.ndarray]]) -> np.ndarray:...
    def get_warp_matrix(self) -> np.ndarray:...
    def apply_to_texture(self, texture: Texture, warp_matrix: np.ndarray) -> Texture:...

class StructuredLightScanner:
    """Handles structured light scanning operations."""
    
    def __init__(self, pattern_generator: PatternGenerator):
        # ...
    def capture_point_cloud(self) -> PointCloud:...
    def generate_calibration_pattern(self, pattern_type: str) -> np.ndarray:...
    def decode_point_cloud(self, image: np.ndarray) -> PointCloud:...
    def filter_noise(self, point_cloud: PointCloud) -> PointCloud:...
    def simplify_mesh(self, point_cloud: PointCloud, target_density: int) -> Mesh:...
```

---

## Core Components

### 1. ProjectionMappingManager

The central orchestrator that manages the complete projection mapping workflow from initialization to final warped output.

```python
class ProjectionMappingManager:
    """Manages the complete projection mapping workflow."""
    
    def __init__(self, config: ProjectionMappingConfig):
        self.config = config
        self.camera = None
        self.projectors: Dict[int, Projector] = {}
        self.active_surfaces: Dict[str, Surface] = {}
        self.mesh_warper = MeshWarper()
        self.scanner = StructuredLightScanner()
        self.calibration_data: Dict[str, Any] = {}
        self.stats = ProjectionMappingStats()
        self.subscribers: Dict[str, List[Callable]] = {
            'calibration_start': [],
            'calibration_end': [],
            'surface_added': [],
            'surface_removed': [],
            'warp_updated': []
        }
        
        # Initialize components
        self._initialize_hardware()
        self._load_default_settings()
        
    def start_calibration(self) -> bool:
        """Begin the calibration process for active surfaces."""
        if not self.camera.is_open():
            self._open_camera()
            
        # Generate calibration pattern
        pattern = self.scanner.generate_calibration_pattern("grid_10x10")
        self.camera.capture(pattern)
        
        # Process point cloud
        point_cloud = self.scanner.capture_point_cloud()
        filtered_cloud = self.scanner.filter_noise(point_cloud)
        
        # Create mesh
        mesh = self.scanner.simplify_mesh(filtered_cloud, self.config.point_cloud_density)
        
        # Initialize surface
        surface = Surface(mesh, self.config)
        self.active_surfaces["surface_0"] = surface
        
        # Apply initial warp
        self._apply_warp_to_surface(surface)
        
        self.stats.calibration_frames += 1
        self._notify_subscribers('calibration_end', {'status': 'success'})
        return True
        
    def _apply_warp_to_surface(self, surface: Surface) -> None:
        """Apply warping to a surface based on current calibration."""
        # Get camera and projector transforms
        camera_matrix = self.camera.get_extrinsic_matrix()
        projector_matrix = self.projectors[self.active_surfaces[surface.id]].get_extrinsic_matrix()
        
        # Compute warp matrix
        warp_matrix = self._compute_warp_matrix(camera_matrix, projector_matrix)
        
        # Apply to surface
        surface.warp_matrix = warp_matrix
        self.mesh_warper.warp_matrix = warp_matrix
        
        # Update texture warping
        for texture in surface.textures:
            texture.warp_matrix = warp_matrix
            
        self.stats.warp_updates += 1
        
    def _compute_warp_matrix(self, camera_extrinsic: np.ndarray, 
                            projector_extrinsic: np.ndarray) -> np.ndarray:
        """Compute the warp matrix from camera to projector space."""
        # Implement full calibration pipeline:
        # 1. Extract 3D points from point cloud
        # 2. Transform to projector coordinates
        # 3. Compute planar homography
        # 4. Optimize with RANSAC
        # 5. Return final warp matrix
        pass
```

### 2. StructuredLightScanner

Handles structured light pattern generation and point cloud acquisition.

```python
class StructuredLightScanner:
    """Handles structured light scanning operations."""
    
    def __init__(self, pattern_generator: PatternGenerator):
        self.pattern_generator = pattern_generator
        self.projector = None
        self.camera = None
        self.width = 0
        self.height = 0
        
    def initialize(self, width: int, height: int) -> bool:
        """Initialize scanner with specified resolution."""
        self.width = width
        self.height = height
        # Initialize projector and camera
        return True
        
    def capture_point_cloud(self) -> PointCloud:
        """Capture a structured light point cloud."""
        # Project pattern and capture image
        pattern_image = self.pattern_generator.generate_pattern("grid")
        self.projector.project(pattern_image)
        
        # Capture with camera
        capture_image = self.camera.capture()
        
        # Decode point cloud
        point_cloud = self._decode_point_cloud(capture_image)
        
        return point_cloud
        
    def _decode_point_cloud(self, image: np.ndarray) -> PointCloud:
        """Decode point cloud from captured pattern."""
        # Implement pattern decoding logic
        # This would involve:
        # 1. Pattern recognition
        # 2. Pixel coordinate extraction
        # 3. Depth calculation via triangulation
        # 4. Point cloud generation
        pass
        
    def filter_noise(self, point_cloud: PointCloud) -> PointCloud:
        """Apply statistical filtering to point cloud."""
        # Implement noise filtering
        pass
        
    def simplify_mesh(self, point_cloud: PointCloud, target_density: int) -> Mesh:
        """Simplify point cloud to target mesh density."""
        # Implement mesh simplification
        pass
```

### 3. MeshWarper

Handles mesh-based warping operations for precise projection alignment.

```python
class MeshWarper:
    """Handles mesh-based warping operations."""
    
    VERTEX_SHADER = """
    #version 330
    in vec2 in_position;    // Mesh vertex position
    in vec2 in_texcoord;    // Source texture coordinate
    out vec2 uv;
    uniform mat4 u_warp_matrix;
    void main() {
        gl_Position = u_warp_matrix * vec4(in_position, 0.0, 1.0);
        uv = in_texcoord;
    }
    """
    
    def __init__(self, mesh: Mesh, warping_algorithm: str = "perspective"):
        self.mesh = mesh
        self.warping_algorithm = warping_algorithm
        self.warp_matrix = np.eye(3)
        # Compile shader program
        self.shader_program = self._create_shader_program()
        
    def warp(self, source: np.ndarray, target: np.ndarray) -> np.ndarray:
        """Compute warp transformation between source and target point sets."""
        # Find point correspondences
        correspondences = self._find_correspondences(source, target)
        
        # Optimize transformation
        optimized_matrix = self._optimize_warp(correspondences)
        
        return optimized_matrix
        
    def _optimize_warp(self, correspondences: List[Tuple[np.ndarray, np.ndarray]]) -> np.ndarray:
        """Optimize warp matrix using RANSAC and least squares."""
        # Implement robust optimization
        # 1. Random sample minimal set
        # 2. Compute initial transform
        # 3. Validate with inlier count
        # 4. Refine with all inliers
        # 5. Return final transformation matrix
        pass
        
    def apply_to_texture(self, texture: Texture, warp_matrix: np.ndarray) -> Texture:
        """Apply warping to a texture using the computed matrix."""
        # Upload matrix to shader
        # Sample texture with warped coordinates
        # Return warped texture
        pass
```

---

## Integration with Effect Chain

The projection mapping system integrates seamlessly with VJLive3's existing effect chain architecture, allowing warped content to be processed by any downstream effects.

```python
class EffectChain:
    """Manages the sequence of visual effects."""
    
    def __init__(self):
        self.effects: List[Effect] = []
        self.input_textures: List[Texture] = []
        self.output_textures: List[Texture] = []
        
    def add_effect(self, effect: Effect) -> None:
        """Add an effect to the chain."""
        self.effects.append(effect)
        
    def process_frame(self, frame: Texture) -> Texture:
        """Process a frame through the entire effect chain."""
        current_texture = frame
        for effect in self.effects:
            current_texture = effect.process(current_texture)
        return current_texture
        
    def insert_warped_texture(self, texture: Texture, position: int) -> None:
        """Insert a warped texture at specified position in chain."""
        # Handle texture insertion
        # This allows warped content to be processed by subsequent effects
        pass
```

---

## Performance Requirements

- **Latency:** End-to-end pipeline < 33ms (30 FPS) for 1080p resolution
- **CPU:** < 8% on Orange Pi 5 (single core equivalent)
- **GPU:** < 12% GPU utilization on integrated graphics
- **Memory:** < 80MB resident set size for typical 1080p setup
- **Scalability:** Support up to 4 simultaneous projectors with 1080p each
- **Accuracy:** Sub-millimeter precision at 2m distance
- **Frame Rate:** Maintain 60 FPS even with complex mesh operations
- **Point Cloud Density:** Support 10,000+ points per frame
- **Mesh Operations:** Warp mesh with 500+ vertices in < 5ms
- **Optimization:** Use spatial indexing for correspondence finding
- **Threading:** Separate processing thread for calibration operations

---

## Testing Strategy

### Unit Tests

```python
def test_mesh_warper_basic():
    """Test basic mesh warping functionality."""
    # Create test mesh
    mesh = Mesh(vertices=[[0,0], [1,0], [0,1]], uvs=[[0,0], [1,0], [0,1]])
    
    # Create warper
    warper = MeshWarper(mesh)
    
    # Test identity warp
    source = np.array([[0,0], [1,0], [0,1]])
    target = np.array([[0,0], [1,0], [0,1]])
    warp_matrix = warper.warp(source, target)
    
    # Should be close to identity matrix
    assert np.linalg.norm(warp_matrix - np.eye(3)) < 0.001

def test_structured_light_scanner():
    """Test point cloud generation."""
    # Mock pattern generator
    pattern_gen = MockPatternGenerator()
    scanner = StructuredLightScanner(pattern_gen)
    
    # Initialize
    success = scanner.initialize(640, 480)
    assert success
    
    # Capture point cloud
    point_cloud = scanner.capture_point_cloud()
    assert len(point_cloud.points) > 0
    assert point_cloud.width == 640
    assert point_cloud.height == 480

def test_calibration_pipeline():
    """Test complete calibration pipeline."""
    # Create mock components
    mock_camera = MockCamera()
    mock_projector = MockProjector()
    config = ProjectionMappingConfig()
    
    # Create manager
    manager = ProjectionMappingManager(config)
    manager.camera = mock_camera
    manager.projectors[0] = mock_projector
    
    # Test start calibration
    result = manager.start_calibration()
    assert result is True
    
    # Test save/load
    test_file = "test_calib.json"
    manager.save_calibration(test_file)
    manager.load_calibration(test_file)
```

### Integration Tests

```python
def test_full_projection_mapping_pipeline():
    """Test complete projection mapping workflow."""
    # Create components
    mock_camera = MockCamera()
    mock_projector = MockProjector()
    config = ProjectionMappingConfig()
    
    # Create manager
    manager = ProjectionMappingManager(config)
    manager.camera = mock_camera
    manager.projectors[0] = mock_projector
    
    # Test surface creation
    manager.start_calibration()
    
    # Test warp application
    mock_texture = MockTexture()
    warped = manager.apply_warp(mock_texture)
    
    # Verify output
    assert warped is not None
    assert warped.width == mock_texture.width
    assert warped.height == mock_texture.height

def test_dynamic_surface_tracking():
    """Test surface motion tracking."""
    # Create manager
    manager = ProjectionMappingManager(config)
    manager.start_calibration()
    
    # Simulate surface movement
    for frame in range(100):
        # Update surface position
        manager.track_surface_motion("surface_0")
        
        # Verify tracking success
        status = manager.get_surface_status("surface_0")
        assert status['tracking'] is True
        
        # Verify warp update
        warp_updated = manager.update_calibration()
        assert warp_updated is True
```

### Performance Tests

```python
def test_latency_budget():
    """Test that end-to-end latency meets requirements."""
    import time
    
    # Create components
    mock_camera = MockCamera()
    mock_projector = MockProjector()
    config = ProjectionMappingConfig()
    
    # Create manager
    manager = ProjectionMappingManager(config)
    manager.camera = mock_camera
    manager.projectors[0] = mock_projector
    
    # Warm up
    for _ in range(10):
        manager.start_calibration()
        manager.update_calibration()
        
    # Measure latency
    test_texture = MockTexture()
    iterations = 100
    
    start = time.perf_counter()
    for _ in range(iterations):
        warped = manager.apply_warp(test_texture)
    elapsed = time.perf_counter() - start
    
    avg_latency = (elapsed / iterations) * 1000  # Convert to ms
    assert avg_latency < 33.0, f"Average latency {avg_latency:.1f}ms > 33ms budget"

def test_cpu_usage():
    """Test CPU usage stays within budget."""
    import psutil
    import os
    
    # Create manager with multiple projectors
    config = ProjectionMappingConfig(projector_count=2)
    manager = ProjectionMappingManager(config)
    
    # Measure CPU before and after processing
    process = psutil.Process(os.getpid())
    cpu_before = process.cpu_percent(interval=0.1)
    
    # Process multiple frames
    test_texture = MockTexture()
    for _ in range(1000):
        warped = manager.apply_warp(test_texture)
        manager.update_calibration()
        
    cpu_after = process.cpu_percent(interval=0.1)
    cpu_delta = cpu_after - cpu_before
    
    assert cpu_delta < 8.0, f"CPU usage increase {cpu_delta:.1f}% > 8% budget"
```

---

## Hardware Considerations

### Real-Time Performance

- Use high-resolution timers for precise timing
- Implement frame pacing to maintain consistent 60 FPS
- Use separate threads for processing and I/O
- Implement jitter compensation for timing drift
- Use lock-free data structures for shared state

### Memory Management

- Use object pooling for mesh and point cloud objects
- Implement lazy loading for large calibration datasets
- Use memory-mapped files for configuration storage
- Implement automatic cleanup of unused resources

---

## Error Handling

### Graceful Degradation

```python
class ProjectionMappingManager:
    def __init__(self, config: ProjectionMappingConfig):
        # ...
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        self.max_recovery_attempts = 5
        
    def start_calibration(self) -> bool:
        try:
            # Normal processing
            result = self._start_calibration()
            return result
        except CalibrationError as e:
            self.error_state = True
            self.last_error = str(e)
            logger.error(f"Calibration error: {e}")
            
            # Attempt recovery
            if self._recover_from_error():
                return self._get_fallback_result()
            else:
                # Return safe fallback
                return self._create_safe_fallback()
        except Exception as e:
            self.error_state = True
            self.last_error = str(e)
            logger.critical(f"Unexpected error: {e}")
            return self._create_safe_fallback()
    
    def _recover_from_error(self) -> bool:
        """Attempt to recover from transient errors."""
        if self.recovery_attempts > 5:
            return False
            
        try:
            # Reset internal state
            self._reset_internal_state()
            self.recovery_attempts += 1
            return True
        except:
            return False
    
    def _create_safe_fallback(self) -> bool:
        """Create a safe fallback state."""
        # Disable calibration, continue with identity warp
        logger.warning("Using fallback warp (identity matrix)")
        return True
```

### Error Recovery

```python
def recover_from_error(self):
    """Attempt to recover from transient errors."""
    if not self.error_state:
        return True
        
    # Try to reset state
    try:
        # Reinitialize hardware
        self._reinitialize_hardware()
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        return True
    except:
        # Escalate to manager-level recovery
        self._notify_manager_of_failure()
        return False
```

---

## Configuration System

### JSON Configuration

```json
{
  "projection_mapping": {
    "enabled": true,
    "camera_id": 0,
    "projector_count": 1,
    "calibration_algorithm": "auto",
    "point_cloud_density": 5000,
    "mesh_simplification": 0.1,
    "max_iterations": 10,
    "tolerance": 0.001,
    "network_discovery": true,
    "auto_calibrate": true,
    "fallback_mode": "identity",
    "network": {
      "discovery_port": 5000,
      "broadcast_interval": 2.0
    },
    "calibration": {
      "save_path": "/calibrations/projection_mappings",
      "auto_save": true,
      "version_control": true
    }
  }
}
```

### Configuration Loading

```python
def load_config(config_path: str) -> ProjectionMappingConfig:
    """Load projection mapping configuration from JSON."""
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    # Validate required fields
    required_fields = ['enabled', 'camera_id']
    for field in required_fields:
        if field not in config['projection_mapping']:
            raise ValueError(f"Missing required field: {field}")
            
    # Create config object
    cfg = config['projection_mapping']
    
    return ProjectionMappingConfig(
        enabled=cfg['enabled'],
        camera_id=cfg['camera_id'],
        projector_count=cfg.get('projector_count', 1),
        calibration_algorithm=cfg.get('calibration_algorithm', 'auto'),
        point_cloud_density=cfg.get('point_cloud_density', 5000),
        mesh_simplification=cfg.get('mesh_simplification', 0.1),
        max_iterations=cfg.get('max_iterations', 10),
        tolerance=cfg.get('tolerance', 0.001),
        network_discovery=cfg.get('network_discovery', True),
        auto_calibrate=cfg.get('auto_calibrate', True)
    )
```

---

## Implementation Tips

1. **Start Simple**: Begin with basic grid pattern calibration before adding complex patterns
2. **Use Data Classes**: For point cloud and mesh structures to ensure type safety
3. **Implement Proper Cleanup**: Handle resource cleanup on manager shutdown
4. **Add Debug Visualization**: Provide WebSocket endpoint to visualize point clouds and meshes
5. **Test Edge Cases**: Handle zero-feature surfaces, extreme lighting, and motion blur
6. **Profile Early**: Measure performance on target hardware from the start
7. **Use Dependency Injection**: Make camera and projector objects injectable
8. **Implement Fallbacks**: Provide identity warp when calibration fails
9. **Add Monitoring**: Track processing latency and error rates
10. **Document Calibration**: Provide clear documentation of calibration workflows

---

## Performance Optimization Checklist

- [ ] Use lock-free data structures for shared state
- [ ] Pre-allocate all mesh and point cloud buffers
- [ ] Use SIMD for point cloud processing operations
- [ ] Pin processing threads to dedicated CPU cores
- [ ] Set real-time scheduling priority for processing thread
- [ ] Implement buffer recycling to avoid allocations
- [ ] Monitor CPU and memory usage continuously
- [ ] Profile hot paths identified in profiling
- [ ] Optimize with SIMD where possible
- [ ] Use spatial indexing for correspondence finding
- [ ] Implement early termination for slow operations

---

## Testing Checklist

- [ ] All unit tests pass with 100% coverage
- [ ] Integration tests verify complete projection mapping pipeline
- [ ] Performance tests meet all latency and CPU budgets
- [ ] Stress tests with maximum mesh complexity and point density
- [ ] Edge case testing (low texture, motion blur, extreme angles)
- [ ] Hardware validation on Orange Pi 5
- [ ] CI/CD pipeline runs all tests on every commit
- [ ] No memory leaks detected with valgrind
- [ ] No performance regressions compared to baseline
- [ ] Calibration accuracy verified with measurement tools
- [ ] Dynamic surface tracking works with moving objects
- [ ] Multiple projector support verified
- [ ] Network discovery and synchronization works correctly

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 20 tests implemented and passing
- [ ] Test coverage >= 90%
- [ ] Performance budget met on Orange Pi 5 hardware
- [ ] Calibration accuracy < 0.5mm verified
- [ ] Dynamic surface tracking verified
- [ ] Multiple projector synchronization verified
- [ ] CI/CD pipeline runs tests on every commit
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-X4: Projection Mapping` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### .agent/workflows/manager-job.md (L97-116) [VJlive (Original)]
```markdown
- **Phase 11 — Audience & Advanced**: Camera motion detection, phone-as-pixel, projection mapping, gyro input.
```

### .agent/workflows/manager-role.md (L97-116) [VJlive (Original)]
```markdown
- **Phase 11 — Audience & Advanced**: Camera motion detection, phone-as-pixel, projection mapping, gyro input.
- **Phase 12 — Licensing & Deploy**: 5-tier system, license server, burst credits, packaging, distribution.
```

### core/projection/calibration.py (L1-20) [VJlive (Original)]
```python
"""
Projection Calibration and Configuration Management
"""

import json
import numpy as np
from typing import Dict, Any, Optional

class CalibrationManager:
    """Manage projection mapping calibrations"""

    def __init__(self):
        self.calibrations = {}  # projector_id -> calibration data
        self.current_projector = None

    def save_calibration(self, projector_id: int, calibration_data: Dict[str, Any]) -> bool:
        """
        Save calibration data for a projector

        Args:
```

### core/projection/mesh_warper.py (L1-20) [VJlive (Original)]
```python
"""
Mesh-based texture warping for projection mapping
"""

import moderngl
import numpy as np
from typing import List, Tuple, Optional

class MeshWarper:
    """GPU-accelerated mesh warping for projection mapping"""

    VERTEX_SHADER = """
    #version 330
    in vec2 in_position;    // Mesh vertex position
    in vec2 in_texcoord;    // Source texture coordinate
    out vec2 uv;

    void main() {
        gl_Position = vec4(in_position, 0.0, 1.0);
        uv = in_texcoord;
```

### core/projection/surface_scanner.py (L1-20) [VJlive (Original)]
```python
"""
Automatic Surface Detection for Projection Mapping
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional, Dict, Any

class SurfaceScanner:
    """Automatic 3D surface detection for projection mapping"""

    def __init__(self):
        self.camera = None
        self.projector_resolution = (1920, 1080)
        self.scan_patterns = []  # Structured light patterns
        self.detected_surfaces = []

    def initialize_camera(self, camera_id: int = 0) -> bool:
        """
        Initialize camera for surface scanning
```

### core/vision/auto_calibrator.py (L17-36) [VJlive (Original)]
```python
    """
    Automatic Projector-Camera Calibration System.
    
    Coordinates the calibration process:
    1. Generates Structured Light patterns.
    2. Projects them via the Matrix (injecting into output).
    3. Captures frames via VisionNode.
    4. Decodes pixel coordinates.
    5. Generates a Warp Map for projection mapping.
    """
    
    def __init__(self, matrix: UnifiedMatrix, vision_node_id: str, output_node_id: str):
        self.matrix = matrix
        self.vision_node_id = vision_node_id
        self.output_node_id = output_node_id
        
        self.width = matrix.width
        self.height = matrix.height
        
        self.generator = StructuredLightGenerator(self.width, self.height)
```

---

## Notes for Implementers

1. **Structured Light Patterns**: Implement multiple pattern types (grid, circle, random) for robust decoding
2. **Point Cloud Processing**: Use efficient data structures for large point clouds
3. **Mesh Simplification**: Implement quadric error metrics for quality preservation
4. **Warp Optimization**: Use RANSAC for robust correspondence detection
5. **Real-Time Performance**: Prioritize frame rate over absolute accuracy when needed
6. **User Feedback**: Provide visual indicators of calibration quality
7. **Fallback Strategies**: Implement multiple fallback modes for different failure scenarios
8. **Network Stack**: Use UDP for low-latency discovery messages
9. **Security**: Implement authentication for remote calibration control
10. **Documentation**: Provide clear examples for common calibration workflows

---

## Implementation Roadmap

1. **Week 1**: Design data structures and calibration pipeline
2. **Week 2**: Implement structured light scanner and point cloud generation
3. **Week 3**: Develop mesh creation and simplification algorithms
4. **Week 4**: Build warp optimization with RANSAC and least squares
5. [ ] **Week 5**: Implement real-time surface tracking and dynamic calibration
6. **Week 6**: Add network discovery and multi-projector support
7. **Week 7**: Performance optimization and comprehensive testing
8. [ ] **Week 8**: Final validation and documentation

---
-

## References

- `.agent/workflows/manager-job.md` (to be referenced)
- `.agent/workflows/manager-role.md` (to be referenced)
- `core/projection/calibration.py` (to be referenced)
- `core/projection/mesh_warper.py` (to be referenced)
- `core/projection/surface_scanner.py` (to be referenced)
- `core/vision/auto_calibrator.py` (to be referenced)
- `moderngl` library (for GPU operations)
- `numpy` (for array operations)
- `cv2` (for computer vision operations)
- Point Cloud Library (PCL) (for advanced processing)
- OpenCV (for pattern generation and decoding)
- Eigen (for linear algebra operations)

---

## Conclusion

The Projection Mapping module transforms VJLive3 into a precision tool for architectural projection and immersive installations. By combining structured light scanning, mesh-based warping, and real-time calibration, this module enables creators to project content onto complex physical surfaces with pixel-perfect accuracy. Its robust architecture, real-time performance, and seamless integration with existing systems empower artists and technicians to create breathtaking immersive experiences that respond dynamically to their environments.

---
