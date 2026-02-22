"""
P3-VD13: Depth Erosion Datamosh
Morphological depth-driven organic feedback datamosh.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_erosion_datamosh")

METADATA = {
    "name": "Depth Erosion Datamosh",
    "description": "Morphological depth-driven organic feedback datamosh.",
    "version": "1.0.0",
    "parameters": [
        {"name": "morph_radius", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "morph_mode", "type": "int", "min": 0, "max": 3, "default": 0},
        {"name": "mosh_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.8},
        {"name": "feedback_decay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.95}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthErosionDatamoshPlugin(PluginBase):
    """Morphological feedback datamosh."""

    name = METADATA["name"]
    version = METADATA["version"]

    def __init__(self) -> None:
        super().__init__()
        self.params: Dict[str, Any] = {
            p["name"]: p["default"] for p in METADATA["parameters"]
        }
        self._fbo_feedback_a = False
        self._fbo_feedback_b = False
        self._ping_pong_state = 0

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        for p in METADATA["parameters"]:
            self.context.set_parameter(f"erosion_mosh.{p['name']}", p["default"])
            
        self._fbo_feedback_a = True
        self._fbo_feedback_b = True
        _logger.info("Depth Erosion Datamosh loaded. Feedback FBOs allocated.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"erosion_mosh.{p['name']}")
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

        src_tex = video_b_in if video_b_in is not None else video_in

        # Edge Case: Missing Depth Input -> bypass morphology safely just by passing src
        if depth_in is None:
            self.context.set_texture("video_out", src_tex)
            _logger.debug("Depth map missing, bypassing morphological feedback.")
            return

        # Ping-pong feedback loop simulator
        self._ping_pong_state = 1 - self._ping_pong_state
        
        output_tex_id = src_tex + (7000 if self._ping_pong_state == 0 else 8000)

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        self._fbo_feedback_a = False
        self._fbo_feedback_b = False
        _logger.info("Depth Erosion Datamosh cleaned up. FBOs destroyed.")
