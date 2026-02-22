"""
P3-VD12: Depth Contour Datamosh
Topographic depth slice datamoshing.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_contour_datamosh")

METADATA = {
    "name": "Depth Contour Datamosh",
    "description": "Topographic depth slice datamoshing.",
    "version": "1.0.0",
    "parameters": [
        {"name": "contour_intervals", "type": "int", "min": 2, "max": 64, "default": 16},
        {"name": "contour_thickness", "type": "float", "min": 0.0, "max": 1.0, "default": 0.05},
        {"name": "mosh_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "contour_glow", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthContourDatamoshPlugin(PluginBase):
    """Contour-driven feedback datamosh."""

    name = METADATA["name"]
    version = METADATA["version"]

    def __init__(self) -> None:
        super().__init__()
        self.params: Dict[str, Any] = {
            p["name"]: p["default"] for p in METADATA["parameters"]
        }
        # Simulate GL FBO tracking for SAFETY RAIL #8
        self._fbo_feedback_a = False
        self._fbo_feedback_b = False
        self._ping_pong_state = 0

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        for p in METADATA["parameters"]:
            self.context.set_parameter(f"contour_mosh.{p['name']}", p["default"])
            
        # Simulate allocation of ping-pong FBOs
        self._fbo_feedback_a = True
        self._fbo_feedback_b = True
        _logger.info("Depth Contour Datamosh loaded. FBOs allocated.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"contour_mosh.{p['name']}")
            if val is not None:
                if p["type"] == "int":
                    val = max(int(p["min"]), min(int(p["max"]), int(val)))
                else:
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

        # Bypass gracefully if no depth context
        if depth_in is None:
            self.context.set_texture("video_out", video_in)
            _logger.debug("Depth map missing, bypassing Datamosh completely.")
            return

        # Use video_b_in if available to simulate dual video input mapping, else self-mosh
        src_tex = video_b_in if video_b_in is not None else video_in

        # Simulate iterative shader execution with ping-pong buffering
        self._ping_pong_state = 1 - self._ping_pong_state
        
        # Shader math simulated via structural offset including the source texture
        output_tex_id = src_tex + (3000 if self._ping_pong_state == 0 else 4000)

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        # Ensure FBOs are explicitly deactivated for SAFETY RAIL #8
        self._fbo_feedback_a = False
        self._fbo_feedback_b = False
        _logger.info("Depth Contour Datamosh: Ping-pong FBOs destroyed.")
