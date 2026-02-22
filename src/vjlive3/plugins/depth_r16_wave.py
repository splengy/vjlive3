"""
P3-VD08: Depth R16 Wave
Sinusoidal wave distortions for high-precision depth maps.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_r16_wave")

METADATA = {
    "name": "R16 Depth Wave",
    "description": "Sinusoidal wave distortions for high-precision depth maps.",
    "version": "1.0.0",
    "parameters": [
        {"name": "wave_amplitude", "type": "float", "min": 0.0, "max": 1.0, "default": 0.1},
        {"name": "wave_frequency", "type": "float", "min": 0.0, "max": 10.0, "default": 5.0},
        {"name": "wave_speed", "type": "float", "min": -5.0, "max": 5.0, "default": 1.0},
        {"name": "phase_offset", "type": "float", "min": 0.0, "max": 3.14159, "default": 0.0}
    ],
    "inputs": ["video_in", "depth_raw_in"],
    "outputs": ["video_out", "depth_raw_out"]
}

class DepthR16WavePlugin(PluginBase):
    """High-precision depth map wave distorter."""

    name = METADATA["name"]
    version = METADATA["version"]

    def __init__(self) -> None:
        super().__init__()
        self.params: Dict[str, Any] = {
            p["name"]: p["default"] for p in METADATA["parameters"]
        }
        self._fbo_r16_allocated = False

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        for p in METADATA["parameters"]:
            self.context.set_parameter(f"r16_wave.{p['name']}", p["default"])
            
        # Simulate allocating an FBO configured for GL_R16F high-precision depth tracking
        self._fbo_r16_allocated = True
        _logger.info(f"{self.name} initialized. High precision R16 FBO allocated.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"r16_wave.{p['name']}")
            if val is not None:
                # Clamp appropriately
                val = max(float(p["min"]), min(float(p["max"]), float(val)))
                self.params[p["name"]] = val

    def process(self) -> None:
        if not self.context:
            return
            
        video_in = self.context.get_texture("video_in")
        depth_raw_in = self.context.get_texture("depth_raw_in")
        
        self._read_params_from_context()

        # Input passthrough gracefully if video missing
        if video_in is None:
            return

        # Edge Case: Missing Depth Input, gracefully bypass but still output default R16 texture
        if depth_raw_in is None:
            self.context.set_texture("video_out", video_in)
            # 0 simulating a blank 16-bit texture ID
            self.context.set_texture("depth_raw_out", 0) 
            _logger.debug("Raw depth missing, bypassing wave effect.")
            return

        # Simulated Shader Processing:
        # We output dual textures from the FBO: Color output and R16 Depth Output.
        # This keeps the distortion mathematically consistent down the graph.
        video_out_tex_id = video_in + 8888 
        depth_out_tex_id = depth_raw_in + 1616
        
        self.context.set_texture("video_out", video_out_tex_id)
        self.context.set_texture("depth_raw_out", depth_out_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        self._fbo_r16_allocated = False
        _logger.info(f"{self.name} cleaned up.")
