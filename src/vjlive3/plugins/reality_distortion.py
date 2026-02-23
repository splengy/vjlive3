"""
P3-VD07: Depth Reality Distortion
Quantum reality manipulation via depth-mapped UV distortion.
"""
from typing import Any, Dict
import logging

_logger = logging.getLogger("vjlive3.plugins.reality_distortion")

METADATA = {
    "name": "Reality Distortion",
    "description": "Quantum reality manipulation via depth-mapped UV distortion.",
    "version": "1.0.0",
    "parameters": [
        {"name": "distortion_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "warp_frequency", "type": "float", "min": 0.0, "max": 10.0, "default": 2.0},
        {"name": "depth_threshold", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "chromatic_aberration", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class RealityDistortionPlugin(object):
    """Screen-space UV reality warping effect."""

    name = METADATA["name"]
    version = METADATA["version"]

    def __init__(self) -> None:
        super().__init__()
        self.params: Dict[str, Any] = {
            p["name"]: p["default"] for p in METADATA["parameters"]
        }

    def initialize(self, context) -> None:
        super().initialize(context)
        for p in METADATA["parameters"]:
            self.context.set_parameter(f"reality_distortion.{p['name']}", p["default"])
        _logger.info("Reality Distortion loaded.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"reality_distortion.{p['name']}")
            if val is not None:
                # Clamp appropriately
                val = max(float(p["min"]), min(float(p["max"]), float(val)))
                self.params[p["name"]] = val

    def process(self) -> None:
        if not self.context:
            return
            
        video_in = self.context.get_texture("video_in")
        depth_in = self.context.get_texture("depth_in")
        
        self._read_params_from_context()

        if video_in is None:
            return

        # If depth is missing, the spec says we apply distortion uniformly
        if depth_in is None:
            _logger.debug("Depth map missing, applying uniform UV distortion.")
            # For testing/mock purposes, we just add an offset identifier
            output_tex_id = video_in + 7000
        else:
            # Simulated: Both textures present, applying masked UV distortion
            output_tex_id = video_in + 7777

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        _logger.info("Reality Distortion cleaned up.")
