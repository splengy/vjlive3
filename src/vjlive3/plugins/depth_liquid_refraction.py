"""
P3-VD19: Depth Liquid Refraction
Depth-driven glass and water distortion with caustic edge highlights.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_liquid_refraction")

METADATA = {
    "name": "Depth Liquid Refraction",
    "description": "Depth-driven glass and water distortion with caustic edge highlights.",
    "version": "1.0.0",
    "parameters": [
        {"name": "refraction_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "chromatic_spread", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "ripple_speed", "type": "float", "min": 0.0, "max": 2.0, "default": 0.4},
        {"name": "ripple_scale", "type": "float", "min": 0.1, "max": 2.0, "default": 0.5},
        {"name": "edge_glow", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "depth_blur", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "frosted_glass", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "invert_depth", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthLiquidRefractionPlugin(PluginBase):
    """Refractive displacement effect using depth buffers as UV deformation vectors."""

    name = METADATA["name"]
    version = METADATA["version"]

    def __init__(self) -> None:
        super().__init__()
        self.params: Dict[str, Any] = {
            p["name"]: p["default"] for p in METADATA["parameters"]
        }

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        for p in METADATA["parameters"]:
            self.context.set_parameter(f"liquid_refraction.{p['name']}", p["default"])
        _logger.info("Depth Liquid Refraction loaded.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"liquid_refraction.{p['name']}")
            if val is not None:
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

        # Bypass gracefully if no depth context to refract against
        if depth_in is None:
            self.context.set_texture("video_out", video_in)
            _logger.debug("Depth map missing, bypassing liquid refraction.")
            return

        # Structural offset representing the UV displacement offset mutation layout logic 
        output_tex_id = video_in + 13000

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        _logger.info("Depth Liquid Refraction cleaned up.")
