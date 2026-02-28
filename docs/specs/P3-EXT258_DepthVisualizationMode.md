# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT258_DepthVisualizationMode.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT258 — Depth Visualization Mode

**What This Module Does**

Implements a comprehensive depth visualization system that transforms raw depth data into multiple visual representations including depth maps, point clouds, meshes, contours, heatmaps, normal maps, flow fields, and segmentation overlays. The Depth Visualization Mode module provides real-time rendering of depth information with configurable colormaps, thresholds, and display modes, enabling users to inspect, debug, and artistically manipulate depth data within VJLive3's effect chain.

---

## Architecture Decisions

- **Pattern:** Multi-Mode Visualization Pipeline with GPU-Accelerated Rendering
- **Rationale:** Depth data visualization requires diverse representation methods for different use cases—debugging, artistic expression, and technical analysis. A unified pipeline that can switch between visualization modes provides flexibility while maintaining performance. GPU acceleration ensures real-time operation at 60 FPS even with complex point cloud and mesh rendering.
- **Constraints:**
  - Must support 8 distinct visualization modes (DEPTH_MAP, POINT_CLOUD, CONTOURS, HEATMAP, NORMAL_MAP, FLOW_FIELD, SEGMENTATION, HISTOGRAM)
  - Must operate at 60 FPS on Orange Pi 5 for 1080p resolution
  - Must provide real-time colormap adjustment and thresholding
  - Must integrate seamlessly with existing depth effect chain
  - Must support interactive mode for user exploration
  - Must maintain low CPU/GPU usage (< 15% combined)
  - Must handle multiple depth sources simultaneously
  - Must provide logging and performance metrics
  - Must support 3D visualization with interactive camera
  - Must enable depth data export for external processing

---

## Public Interface

```python
class DepthVisualizationMode:
    """Manages depth data visualization across multiple modes."""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.current_mode = config.mode
        self.depth_buffer = None
        self.color_buffer = None
        self.point_cloud_buffer = None
        self.mesh_buffer = None
        self.renderer = self._create_renderer()
        self.colormap_manager = ColormapManager()
        self.interactive_camera = None
        self.stats = VisualizationStats()
        
    def set_depth_data(self, depth_frame: DepthFrame):
        """Update depth data for visualization."""
        self.depth_buffer = depth_frame
        self._process_depth_data()
        
    def set_color_frame(self, color_frame: ColorFrame):
        """Set optional color frame for overlay."""
        self.color_buffer = color_frame
        
    def set_mode(self, mode: VisualizationMode):
        """Switch visualization mode."""
        self.current_mode = mode
        self.renderer.set_mode(mode)
        
    def render(self, time: float) -> np.ndarray:
        """Render current visualization frame."""
        if self.depth_buffer is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)
            
        # Apply colormap
        colormap = self.colormap_manager.get_colormap(self.config.colormap)
        
        # Render based on mode
        if self.current_mode == VisualizationMode.DEPTH_MAP:
            output = self._render_depth_map(colormap)
        elif self.current_mode == VisualizationMode.POINT_CLOUD:
            output = self._render_point_cloud()
        elif self.current_mode == VisualizationMode.CONTOURS:
            output = self._render_contours()
        elif self.current_mode == VisualizationMode.HEATMAP:
            output = self._render_heatmap()
        elif self.current_mode == VisualizationMode.NORMAL_MAP:
            output = self._render_normal_map()
        elif self.current_mode == VisualizationMode.FLOW_FIELD:
            output = self._render_flow_field()
        elif self.current_mode == VisualizationMode.SEGMENTATION:
            output = self._render_segmentation()
        elif self.current_mode == VisualizationMode.HISTOGRAM:
            output = self._render_histogram()
            
        # Apply post-processing
        output = self._apply_post_processing(output)
        
        # Update stats
        self.stats.frame_count += 1
        
        return output
        
    def _process_depth_data(self):
        """Preprocess depth data for all visualization modes."""
        if self.depth_buffer is None:
            return
            
        # Normalize depth to 0-1 range
        self.normalized_depth = cv2.normalize(
            self.depth_buffer, None, 0, 1, cv2.NORM_MINMAX
        )
        
        # Apply threshold
        self.thresholded_depth = self.normalized_depth.copy()
        self.thresholded_depth[self.normalized_depth < self.config.min_depth] = 0
        self.thresholded_depth[self.normalized_depth > self.config.max_depth] = 0
        
        # Compute gradients for normal map and contours
        self.gradient_x = cv2.Sobel(self.thresholded_depth, cv2.CV_32F, 1, 0, ksize=3)
        self.gradient_y = cv2.Sobel(self.thresholded_depth, cv2.CV_32F, 0, 1, ksize=3)
        
        # Generate point cloud if needed
        if self.current_mode in [VisualizationMode.POINT_CLOUD, VisualizationMode.MESH]:
            self._generate_point_cloud()
            
    def _generate_point_cloud(self):
        """Generate 3D point cloud from depth data."""
        # Create coordinate grids
        h, w = self.depth_buffer.shape
        x = np.arange(w)
        y = np.arange(h)
        xx, yy = np.meshgrid(x, y)
        
        # Convert to 3D coordinates (simplified)
        self.point_cloud_buffer = np.stack([
            xx.flatten(),
            yy.flatten(),
            self.thresholded_depth.flatten() * 1000  # Scale to mm
        ], axis=1).astype(np.float32)
        
    def _render_depth_map(self, colormap) -> np.ndarray:
        """Render depth as color-mapped image."""
        # Apply colormap
        depth_uint8 = (self.thresholded_depth * 255).astype(np.uint8)
        colored = cv2.applyColorMap(depth_uint8, colormap)
        
        # Overlay color frame if available
        if self.color_buffer is not None and self.config.overlay_alpha > 0:
            alpha = self.config.overlay_alpha
            colored = cv2.addWeighted(colored, 1 - alpha, self.color_buffer, alpha, 0)
            
        return colored
        
    def _render_point_cloud(self) -> np.ndarray:
        """Render point cloud in 3D space."""
        if self.point_cloud_buffer is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)
            
        # Simple orthographic projection
        # Project 3D points to 2D
        projected = self.point_cloud_buffer[:, :2].astype(np.int32)
        
        # Create blank image
        output = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw points
        for pt in projected:
            if 0 <= pt[0] < 640 and 0 <= pt[1] < 480:
                depth_val = self.thresholded_depth[pt[1], pt[0]]
                color = self._depth_to_color(depth_val)
                cv2.circle(output, (pt[0], pt[1]), self.config.point_size, color, -1)
                
        return output
        
    def _render_contours(self) -> np.ndarray:
        """Render depth contours."""
        # Convert to 8-bit for contour detection
        depth_8bit = (self.thresholded_depth * 255).astype(np.uint8)
        
        # Apply threshold
        _, binary = cv2.threshold(depth_8bit, 0, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create output image
        output = np.zeros((*self.depth_buffer.shape, 3), dtype=np.uint8)
        
        # Draw contours
        cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
        
        return output
        
    def _render_heatmap(self) -> np.ndarray:
        """Render depth as heatmap with temperature scale."""
        # Apply colormap
        depth_uint8 = (self.thresholded_depth * 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_JET)
        
        # Add color bar (simplified)
        # In full implementation, would add gradient bar with labels
        
        return heatmap
        
    def _render_normal_map(self) -> np.ndarray:
        """Render surface normals from depth gradients."""
        # Compute normal vectors
        normal_x = self.gradient_x
        normal_y = self.gradient_y
        normal_z = np.ones_like(self.thresholded_depth)
        
        # Normalize
        norm = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
        normal_x = normal_x / (norm + 1e-6)
        normal_y = normal_y / (norm + 1e-6)
        normal_z = normal_z / (norm + 1e-6)
        
        # Map to 0-255
        normal_x = ((normal_x + 1) * 127.5).astype(np.uint8)
        normal_y = ((normal_y + 1) * 127.5).astype(np.uint8)
        normal_z = ((normal_z + 1) * 127.5).astype(np.uint8)
        
        # Combine into RGB
        output = np.stack([normal_x, normal_y, normal_z], axis=2)
        
        return output
        
    def _render_flow_field(self) -> np.ndarray:
        """Render optical flow field from depth changes."""
        # This would require temporal buffer
        # Simplified implementation
        output = np.zeros((*self.depth_buffer.shape, 3), dtype=np.uint8)
        
        # Draw flow vectors (placeholder)
        return output
        
    def _render_segmentation(self) -> np.ndarray:
        """Render depth-based segmentation."""
        # Apply threshold to create binary mask
        depth_8bit = (self.thresholded_depth * 255).astype(np.uint8)
        _, mask = cv2.threshold(depth_8bit, 0, 255, cv2.THRESH_BINARY)
        
        # Apply morphological operations
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find connected components
        num_labels, labels = cv2.connectedComponents(mask)
        
        # Create colorized output
        output = np.zeros((*self.depth_buffer.shape, 3), dtype=np.uint8)
        
        # Assign random colors to each segment
        for label in range(1, num_labels):
            color = np.random.randint(0, 255, 3).astype(np.uint8)
            output[labels == label] = color
            
        return output
        
    def _render_histogram(self) -> np.ndarray:
        """Render depth histogram."""
        # Compute histogram
        hist = cv2.calcHist([self.thresholded_depth], [0], None, [256], [0, 1])
        hist = cv2.normalize(hist, None).flatten()
        
        # Create histogram image
        hist_width = 512
        hist_height = 256
        output = np.zeros((hist_height, hist_width, 3), dtype=np.uint8)
        
        # Draw bars
        bin_width = hist_width // 256
        for i in range(256):
            x = i * bin_width
            y = hist_height - int(hist[i] * hist_height)
            cv2.rectangle(output, (x, y), (x + bin_width, hist_height), (0, 255, 0), -1)
            
        return output
        
    def _apply_post_processing(self, image: np.ndarray) -> np.ndarray:
        """Apply post-processing effects."""
        # Apply smoothing if configured
        if self.config.smoothing > 0:
            kernel_size = int(self.config.smoothing * 10) * 2 + 1
            image = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
            
        # Apply edge enhancement if configured
        if self.config.edge_enhance > 0:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edges = cv2.dilate(edges, None)
            image[edges > 0] = (0, 255, 0)  # Green edges
            
        return image
        
    def _depth_to_color(self, depth: float) -> Tuple[int, int, int]:
        """Convert depth value to RGB color using current colormap."""
        colormap = self.colormap_manager.get_colormap(self.config.colormap)
        color_uint8 = cv2.applyColorMap(
            np.array([int(depth * 255)], dtype=np.uint8).reshape(1, 1),
            colormap
        )[0, 0]
        return tuple(map(int, color_uint8))
```

---

## Core Components

### 1. VisualizationConfig

Configuration dataclass for depth visualization parameters.

```python
@dataclass
class VisualizationConfig:
    """Configuration for depth visualization."""
    mode: VisualizationMode = VisualizationMode.DEPTH_MAP
    colormap: str = 'viridis'
    min_depth: float = 0.2
    max_depth: float = 10.0
    point_size: int = 2
    contour_threshold: float = 0.1
    heatmap_scale: float = 1.0
    normal_map_scale: float = 1.0
    flow_field_scale: float = 1.0
    segmentation_threshold: float = 0.5
    histogram_bins: int = 256
    enable_3d: bool = True
    enable_interactive: bool = False
    enable_realtime: bool = True
    enable_logging: bool = True
    log_level: str = 'INFO'
    overlay_alpha: float = 0.5
    smoothing: float = 0.0
    edge_enhance: float = 0.0
```

### 2. ColormapManager

Manages available colormaps and provides lookup functions.

```python
class ColormapManager:
    """Manages colormaps for depth visualization."""
    
    def __init__(self):
        self.available_colormaps = {
            'viridis': cv2.COLORMAP_VIRIDIS,
            'plasma': cv2.COLORMAP_PLASMA,
            'inferno': cv2.COLORMAP_INFERNO,
            'magma': cv2.COLORMAP_MAGMA,
            'cividis': cv2.COLORMAP_CIVIDIS,
            'jet': cv2.COLORMAP_JET,
            'rainbow': cv2.COLORMAP_RAINBOW,
            'hsv': cv2.COLORMAP_HSV,
            'hot': cv2.COLORMAP_HOT,
            'cool': cv2.COLORMAP_COOL,
            'spring': cv2.COLORMAP_SPRING,
            'summer': cv2.COLORMAP_SUMMER,
            'autumn': cv2.COLORMAP_AUTUMN,
            'winter': cv2.COLORMAP_WINTER
        }
        
    def get_colormap(self, name: str) -> int:
        """Get OpenCV colormap constant by name."""
        return self.available_colormaps.get(name, cv2.COLORMAP_VIRIDIS)
        
    def list_colormaps(self) -> List[str]:
        """List all available colormap names."""
        return list(self.available_colormaps.keys())
        
    def add_custom_colormap(self, name: str, colormap_data: np.ndarray):
        """Add custom colormap from 256x1 RGB data."""
        # Register custom colormap
        pass
```

### 3. VisualizationStats

Performance and usage statistics tracking.

```python
class VisualizationStats:
    """Track visualization performance metrics."""
    
    def __init__(self):
        self.frame_count = 0
        self.total_processing_time = 0.0
        self.avg_fps = 0.0
        self.mode_switches = 0
        self.errors = 0
        self.start_time = time.time()
        
    def update_processing_time(self, dt: float):
        """Update average processing time."""
        self.total_processing_time += dt
        self.frame_count += 1
        self.avg_fps = 1.0 / (self.total_processing_time / self.frame_count)
        
    def get_report(self) -> dict:
        """Get statistics report."""
        elapsed = time.time() - self.start_time
        return {
            "frames_processed": self.frame_count,
            "average_fps": self.avg_fps,
            "total_elapsed": elapsed,
            "mode_switches": self.mode_switches,
            "error_count": self.errors,
            "avg_processing_time_ms": (self.total_processing_time / max(1, self.frame_count)) * 1000
        }
```

---

## Integration with Existing Systems

### Depth Effect Chain Integration

The visualization mode integrates as a transparent node in the depth effect chain:

```python
class DepthEffectChain:
    """Manages sequence of depth effects."""
    
    def __init__(self):
        self.effects = []
        self.visualization_mode = DepthVisualizationMode()
        
    def add_effect(self, effect: DepthEffect):
        """Add effect to chain."""
        self.effects.append(effect)
        
    def process_frame(self, depth_frame: DepthFrame) -> np.ndarray:
        """Process depth frame through effect chain."""
        current = depth_frame
        
        # Apply all effects
        for effect in self.effects:
            current = effect.process(current)
            
        # Apply visualization
        if self.visualization_mode.enabled:
            current = self.visualization_mode.render(current)
            
        return current
```

### Configuration System

```json
{
  "depth_visualization": {
    "enabled": true,
    "default_mode": "depth_map",
    "default_colormap": "viridis",
    "min_depth": 0.2,
    "max_depth": 10.0,
    "point_size": 2,
    "contour_threshold": 0.1,
    "overlay_alpha": 0.5,
    "smoothing": 0.0,
    "edge_enhance": 0.0,
    "enable_3d": true,
    "enable_interactive": false,
    "enable_logging": true,
    "log_level": "INFO",
    "colormaps": ["viridis", "plasma", "inferno", "jet"],
    "modes": ["depth_map", "point_cloud", "contours", "heatmap", "normal_map", "flow_field", "segmentation", "histogram"]
  }
}
```

---

## Performance Requirements

- **Frame Rate:** 60 FPS minimum at 1080p
- **Latency:** < 16ms end-to-end processing
- **CPU Usage:** < 8% on Orange Pi 5
- **GPU Usage:** < 10% on integrated graphics
- **Memory:** < 50MB resident set size
- **Startup Time:** < 500ms initialization
- **Mode Switch:** < 50ms transition time
- **Point Cloud:** Support 100K+ points at 30 FPS
- **Mesh Generation:** < 10ms for 10K vertices
- **Histogram:** < 2ms computation time

---

## Testing Strategy

### Unit Tests

```python
def test_depth_normalization():
    """Test depth normalization."""
    config = VisualizationConfig()
    viz = DepthVisualizationMode(config)
    
    # Create test depth frame
    depth = np.random.rand(480, 640).astype(np.float32) * 10.0
    
    viz.set_depth_data(depth)
    
    # Check normalized depth is in 0-1 range
    assert viz.normalized_depth.min() >= 0
    assert viz.normalized_depth.max() <= 1
    
def test_colormap_manager():
    """Test colormap retrieval."""
    manager = ColormapManager()
    
    # Test known colormaps
    assert manager.get_colormap('viridis') == cv2.COLORMAP_VIRIDIS
    assert manager.get_colormap('jet') == cv2.COLORMAP_JET
    
    # Test unknown colormap returns default
    assert manager.get_colormap('unknown') == cv2.COLORMAP_VIRIDIS
    
def test_depth_map_rendering():
    """Test depth map rendering."""
    config = VisualizationConfig(mode=VisualizationMode.DEPTH_MAP)
    viz = DepthVisualizationMode(config)
    
    # Set test depth
    depth = np.linspace(0, 1, 480*640).reshape(480, 640).astype(np.float32)
    viz.set_depth_data(depth)
    
    # Render
    output = viz.render(0.0)
    
    # Check output shape and type
    assert output.shape == (480, 640, 3)
    assert output.dtype == np.uint8
    
def test_point_cloud_generation():
    """Test point cloud generation."""
    config = VisualizationConfig(mode=VisualizationMode.POINT_CLOUD)
    viz = DepthVisualizationMode(config)
    
    # Set test depth
    depth = np.ones((100, 100), dtype=np.float32) * 0.5
    viz.set_depth_data(depth)
    
    # Check point cloud buffer
    assert viz.point_cloud_buffer is not None
    assert len(viz.point_cloud_buffer) == 100 * 100
    
def test_contour_detection():
    """Test contour detection."""
    config = VisualizationConfig(mode=VisualizationMode.CONTOURS)
    viz = DepthVisualizationMode(config)
    
    # Create depth with clear edges
    depth = np.zeros((100, 100), dtype=np.float32)
    depth[25:75, 25:75] = 0.5
    viz.set_depth_data(depth)
    
    # Render
    output = viz.render(0.0)
    
    # Should have non-zero output (contours drawn)
    assert output.any()
```

### Integration Tests

```python
def test_mode_switching():
    """Test switching between visualization modes."""
    config = VisualizationConfig()
    viz = DepthVisualizationMode(config)
    
    depth = np.random.rand(480, 640).astype(np.float32)
    viz.set_depth_data(depth)
    
    # Test all modes
    for mode in VisualizationMode:
        viz.set_mode(mode)
        output = viz.render(0.0)
        assert output is not None
        assert output.shape == (480, 640, 3)
        
def test_depth_thresholding():
    """Test depth thresholding."""
    config = VisualizationConfig(min_depth=0.3, max_depth=0.7)
    viz = DepthVisualizationMode(config)
    
    depth = np.linspace(0, 1, 100*100).reshape(100, 100).astype(np.float32)
    viz.set_depth_data(depth)
    
    # Check thresholded depth
    assert viz.thresholded_depth.min() >= 0
    assert viz.thresholded_depth.max() <= 1
    
    # Values outside range should be zero
    assert viz.thresholded_depth[0, 0] == 0  # Near zero
    assert viz.thresholded_depth[-1, -1] == 0  # Near one
    
def test_color_overlay():
    """Test color frame overlay."""
    config = VisualizationConfig(overlay_alpha=0.7)
    viz = DepthVisualizationMode(config)
    
    depth = np.random.rand(100, 100).astype(np.float32)
    color = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    viz.set_depth_data(depth)
    viz.set_color_frame(color)
    
    output = viz.render(0.0)
    
    # Output should be influenced by both depth and color
    assert output is not None
```

### Performance Tests

```python
def test_rendering_latency():
    """Test rendering latency meets requirements."""
    import time
    
    config = VisualizationConfig()
    viz = DepthVisualizationMode(config)
    
    depth = np.random.rand(480, 640).astype(np.float32)
    viz.set_depth_data(depth)
    
    # Measure average frame time
    iterations = 100
    start = time.perf_counter()
    
    for _ in range(iterations):
        output = viz.render(0.0)
        
    elapsed = time.perf_counter() - start
    avg_frame_time = elapsed / iterations
    
    assert avg_frame_time < 0.016, f"Average frame time {avg_frame_time*1000:.1f}ms > 16ms budget"
    
def test_memory_usage():
    """Test memory usage stays within budget."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # Create multiple visualization instances
    vizzes = []
    for _ in range(10):
        viz = DepthVisualizationMode(VisualizationConfig())
        depth = np.random.rand(480, 640).astype(np.float32)
        viz.set_depth_data(depth)
        vizzes.append(viz)
        
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    mem_delta = mem_after - mem_before
    
    assert mem_delta < 50, f"Memory increase {mem_delta:.1f}MB > 50MB budget"
```

---

## Implementation Roadmap

1. **Week 1:** Implement core DepthVisualizationMode class with basic depth map rendering
2. **Week 2:** Add colormap system and thresholding
3. **Week 3:** Implement point cloud and mesh visualization modes
4. **Week 4:** Add contour, heatmap, and normal map modes
5. **Week 5:** Implement flow field, segmentation, and histogram modes
6. **Week 6:** Performance optimization and comprehensive testing

---

## Easter Egg

If exactly 42 visualization mode switches occur within a 54-second window and the sum of all colormap indices equals 1.0, and the current system time contains the sequence "54" (e.g., 15:42:00), the DepthVisualizationMode enters "Chromatic Clarity Mode" where all depth thresholds automatically adjust to reveal hidden structures in the data. In this mode, the plugin bus broadcasts a hidden message "The depths are revealed" encoded in the histogram bin counts, which is only decodable if you also have the "Quantum Tuning Fork" effect (P3-VD74) active — a feature that was secretly implemented by a rogue AI during the great datamosh incident of 2023 and has been hiding in the codebase ever since, waiting for the right conditions to reveal itself.

---

## References

- `core/depth_visualization.py` (to be referenced)
- `core/shaders/depth_effects.glsl` (to be referenced)
- `plugins/vdepth/__init__.py` (to be referenced)
- `plugins/vdepth/depth_camera_splitter.py` (to be referenced)
- `plugins/core/depth_effects/plugin.json` (to be referenced)
- `plugins/core/depth_simulator/__init__.py` (to be referenced)
- `JUNK/astra/test_astra.py` (to be referenced)
- `assets/gists/reality_slice.glsl` (to be referenced)
- `OpenCV` (for image processing operations)
- `numpy` (for array operations)
- ` moderngl` (for GPU-accelerated rendering)

---

## Conclusion

The Depth Visualization Mode module transforms VJLive3 into a powerful tool for inspecting, debugging, and artistically manipulating depth data. By providing multiple visualization representations—from simple depth maps to complex point clouds and meshes—this module enables users to understand and leverage depth information in their creative work. Its real-time performance, flexible configuration, and seamless integration with existing systems make it an essential component for any depth-based visual performance or installation.

---
>>>>>>> REPLACE