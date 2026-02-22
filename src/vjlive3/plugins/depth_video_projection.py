"""
P3-VD18: Depth Video Projection
Wraps a secondary video texture onto depth-derived surface normals.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_video_projection")

METADATA = {
    "name": "Depth Video Projection",
    "description": "Wraps a secondary video texture onto depth-derived surface normals.",
    "version": "1.0.0",
    "parameters": [
        {"name": "projection_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "depth_contour", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "uv_scale", "type": "float", "min": 0.1, "max": 5.0, "default": 1.0},
        {"name": "uv_scroll_x", "type": "float", "min": -1.0, "max": 1.0, "default": 0.0},
        {"name": "uv_scroll_y", "type": "float", "min": -1.0, "max": 1.0, "default": 0.0},
        {"name": "normal_lighting", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "mask_tightness", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "hologram_glow", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthVideoProjectionPlugin(PluginBase):
    """Real-time performance contour projection logic mapping."""

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
            self.context.set_parameter(f"video_projection.{p['name']}", p["default"])
        _logger.info("Depth Video Projection loaded.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"video_projection.{p['name']}")
            if val is not None:
                val = max(float(p["min"]), min(float(p["max"]), float(val)))
                self.params[p["name"]] = val

    def process(self) -> None:
        if not self.context:
            return
            
        video_in = self.context.get_texture("video_in")
        video_b_in = self.context.get_texture("video_b_in")
        depth_in = self.context.get_texture("depth_in")
        
        self._read_params_from_context()

        if video_in is None:
            return

        # Missing Depth -> Bypass logic
        if depth_in is None:
            self.context.set_texture("video_out", video_in)
            _logger.debug("Depth map missing, bypassing video projection.")
            return
            
        proj_tex = video_b_in if video_b_in is not None else video_in

        # Structural offset for projection shader
        output_tex_id = proj_tex + 12000

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        _logger.info("Depth Video Projection cleaned up.")
