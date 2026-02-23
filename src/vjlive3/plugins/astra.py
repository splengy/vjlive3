"""
P2-H3: Astra Depth Camera Integration
Captures raw depth and RGB frames from Orbbec Astra, with a Simulator fallback.
"""
import time
from typing import Optional, Tuple
import logging
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


_logger = logging.getLogger("vjlive3.plugins.astra")


class AstraDepthCamera:
    """Core hardware abstraction for the Astra camera."""

    def __init__(self, width: int = 640, height: int = 480, use_simulation: bool = False) -> None:
        self.width = width
        self.height = height
        self.use_simulation = use_simulation
        self._connected = False
        
        # OpenCV VideoCapture backend for OpenNI2 (Astra/Kinect fallback)
        self._cap: Optional[Any] = None  # type: ignore
        
        # Simulator state variables for procedural generation
        self._sim_phase = 0.0

    def start(self) -> bool:
        """Initialize and start the camera (or simulator)."""
        if self.use_simulation or cv2 is None:
            _logger.info("AstraDepthCamera: Starting in Simulator Mode.")
            self._connected = False
            return True
            
        try:
            # OpenCV backend for OpenNI2 cameras
            self._cap = cv2.VideoCapture(cv2.CAP_OPENNI2)
            if not self._cap.isOpened():
                raise RuntimeError("Failed to open CAP_OPENNI2 device.")
            
            # Request specific streams and resolutions
            self._cap.set(cv2.CAP_PROP_OPENNI2_MIRROR, 0)
            self._connected = True
            _logger.info("AstraDepthCamera: Hardware connected successfully.")
            return True
        except Exception as e:
            _logger.error("AstraDepthCamera: Hardware start failed: %s", e)
            _logger.warning("Falling back to Simulator Mode.")
            self._connected = False
            if self._cap:
                self._cap.release()
                self._cap = None
            return True

    def stop(self) -> None:
        """Stop the camera and release resources."""
        if self._cap and self._cap.isOpened():
            self._cap.release()
        self._cap = None
        self._connected = False
        _logger.info("AstraDepthCamera: Stopped.")

    def get_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Grab the latest frames.
        Returns:
            (depth_frame_normalized_0_to_1, rgb_frame_uint8)
        """
        # If hardware is supposedly connected but read fails, fallback
        if self._connected and self._cap and self._cap.isOpened():
            if self._cap.grab():
                # Retrieve depth map and BGR image
                ret_depth, depth_map_raw = self._cap.retrieve(None, cv2.CAP_OPENNI_DEPTH_MAP)
                ret_bgr, bgr_image = self._cap.retrieve(None, cv2.CAP_OPENNI_BGR_IMAGE)
                
                if ret_depth and ret_bgr:
                    # Normalize depth assuming Standard Astra (~10m max range usually mapped in 16-bit mm)
                    # We'll clip to 5000mm and scale
                    depth_map_raw = np.clip(depth_map_raw, 0, 5000)
                    depth_normalized = (depth_map_raw / 5000.0).astype(np.float32)
                    
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
                    
                    return depth_normalized, rgb_frame
            
            # Reaching here implies hardware read failure mid-stream
            _logger.warning("AstraDepthCamera: Hardware read failed. Dropping to Simulator Mode.")
            self._connected = False
            self._cap.release()
            self._cap = None
            
        # Simulator Mode Generator
        return self._generate_simulated_frames()

    def _generate_simulated_frames(self) -> Tuple[np.ndarray, np.ndarray]:
        """Procedural generation of depth and RGB data for testing/fallback."""
        self._sim_phase += 0.05
        
        # Create a procedural moving wave for depth
        x = np.linspace(-3, 3, self.width)
        y = np.linspace(-3, 3, self.height)
        xx, yy = np.meshgrid(x, y)
        
        wave = np.sin(xx + self._sim_phase) * np.cos(yy + self._sim_phase)
        # Normalize wave to 0.0 - 1.0 range
        depth = ((wave + 1.0) / 2.0).astype(np.float32)
        
        # Procedural RGB (moving color gradient based on phase)
        r = ((np.sin(xx * 2 + self._sim_phase) + 1) * 127).astype(np.uint8)
        g = ((np.cos(yy * 2 - self._sim_phase) + 1) * 127).astype(np.uint8)
        b = np.full((self.height, self.width), int((np.sin(self._sim_phase) + 1) * 127), dtype=np.uint8)
        rgb = np.stack((r, g, b), axis=-1)
        
        # Artificial delay to mimic hardware latency (~30fps)
        time.sleep(0.016)
        return depth, rgb

    def is_hardware_connected(self) -> bool:
        """Check if physical connection is active."""
        return self._connected


class AstraPlugin(object):
    """Plugin wrapper exposing the camera to the node graph."""
    
    name = "Astra Depth Camera"
    version = "1.0.0"
    
    def __init__(self) -> None:
        super().__init__()
        self.camera: Optional[AstraDepthCamera] = None
        self.last_depth: Optional[np.ndarray] = None
        self.last_rgb: Optional[np.ndarray] = None

    def initialize(self, context) -> None:
        """Initialize the camera hardware on plugin load."""
        super().initialize(context)
        _logger.info("Initializing Astra plugin...")
        self.camera = AstraDepthCamera(use_simulation=False)
        self.camera.start()

    def process(self) -> None:
        """Capture and emit frames. Typically called on frame update."""
        if not self.camera or not self.context:
            return
            
        depth, rgb = self.camera.get_frames()
        self.last_depth = depth
        self.last_rgb = rgb
        
        # Set parameters/state on context
        self.context.set_parameter("astra.depth", depth)
        self.context.set_parameter("astra.rgb", rgb)
        self.context.set_parameter("astra.is_hardware", self.camera.is_hardware_connected())

    def cleanup(self) -> None:
        """Cleanly stop camera stream."""
        super().cleanup()
        _logger.info("Unloading Astra plugin...")
        if self.camera:
            self.camera.stop()
            self.camera = None
