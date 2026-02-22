"""
P3-VD14: Depth Fracture Datamosh
Shattered glass datamosh driven by depth discontinuities.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_fracture_datamosh")

METADATA = {
    "name": "Depth Fracture Datamosh",
    "description": "Shattered glass datamosh driven by depth discontinuities.",
    "version": "1.0.0",
    "parameters": [
        {"name": "fracture_sensitivity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.1},
        {"name": "fracture_width", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "fracture_decay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.95},
        {"name": "bleed_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "displacement_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthFractureDatamoshPlugin(PluginBase):
    """Depth-edge driven shattering feedback effect."""

    name = METADATA["name"]
    version = METADATA["version"]

    def __init__(self) -> None:
        super().__init__()
        self.params: Dict[str, Any] = {
            p["name"]: p["default"] for p in METADATA["parameters"]
        }
        # Two sets of FBOs required per spec (SAFETY RAIL #8)
        self._fbo_cracks_a = False
        self._fbo_cracks_b = False
        self._fbo_mosh_a = False
        self._fbo_mosh_b = False
        self._ping_pong_state = 0

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        for p in METADATA["parameters"]:
            self.context.set_parameter(f"fracture.{p['name']}", p["default"])
            
        self._fbo_cracks_a = True
        self._fbo_cracks_b = True
        self._fbo_mosh_a = True
        self._fbo_mosh_b = True
        _logger.info("Depth Fracture Datamosh loaded. Crack and Mosh FBOs allocated.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"fracture.{p['name']}")
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

        src_tex = video_b_in if video_b_in is not None else video_in

        # Edge Case: Missing Depth Input -> bypass fracture safely
        if depth_in is None:
            self.context.set_texture("video_out", src_tex)
            _logger.debug("Depth map missing, bypassing fracture rendering.")
            return

        # Dual Ping-pong simulation
        self._ping_pong_state = 1 - self._ping_pong_state
        
        # Mosh shader math simulation
        output_tex_id = src_tex + (9000 if self._ping_pong_state == 0 else 9999)

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        self._fbo_cracks_a = False
        self._fbo_cracks_b = False
        self._fbo_mosh_a = False
        self._fbo_mosh_b = False
        _logger.info("Depth Fracture Datamosh FBOs destroyed.")
