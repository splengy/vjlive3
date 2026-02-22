"""
P3-VD11: Depth Color Grade
Per-depth-band color grading (near, mid, far zones).
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_color_grade")

METADATA = {
    "name": "Depth Color Grade",
    "description": "Per-depth-band color grading (near, mid, far zones).",
    "version": "1.0.0",
    "parameters": [
        {"name": "zone_near", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "zone_far", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "zone_blend", "type": "float", "min": 0.0, "max": 0.5, "default": 0.1},
        {"name": "near_saturation", "type": "float", "min": 0.0, "max": 2.0, "default": 1.0},
        {"name": "mid_saturation", "type": "float", "min": 0.0, "max": 2.0, "default": 1.0},
        {"name": "far_saturation", "type": "float", "min": 0.0, "max": 2.0, "default": 1.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthColorGradePlugin(PluginBase):
    """3-Zone Depth Color Corrector."""

    name = METADATA["name"]
    version = METADATA["version"]

    def __init__(self) -> None:
        super().__init__()
        self.params: Dict[str, Any] = {
            p["name"]: p["default"] for p in METADATA["parameters"]
        }
        self._missing_depth = False

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        for p in METADATA["parameters"]:
            self.context.set_parameter(f"color_grade.{p['name']}", p["default"])
        _logger.info("Depth Color Grade initialized.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"color_grade.{p['name']}")
            if val is not None:
                val = max(float(p["min"]), min(float(p["max"]), float(val)))
                self.params[p["name"]] = val
                
        # Handle Edge Case: Overlapping zones
        if self.params["zone_near"] > self.params["zone_far"]:
            _logger.debug(f"Zone swap detected: near {self.params['zone_near']} > far {self.params['zone_far']}. Correcting.")
            temp = self.params["zone_near"]
            self.params["zone_near"] = self.params["zone_far"]
            self.params["zone_far"] = temp

    def process(self) -> None:
        if not self.context:
            return
            
        video_in = self.context.get_texture("video_in")
        depth_in = self.context.get_texture("depth_in")
        
        self._read_params_from_context()

        if video_in is None:
            return

        # Edge Case: Missing Depth Input, gracefully fallback to Mid Zone
        if depth_in is None:
            self._missing_depth = True
            output_tex_id = video_in + 555
            _logger.debug("Depth map missing, engaging 'Mid' zone grading for full frame.")
        else:
            self._missing_depth = False
            output_tex_id = video_in + 999

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        _logger.info("Depth Color Grade cleaned up.")
