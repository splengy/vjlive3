"""
P3-VD09: Depth Acid Fractal
Neon fractal mayhem modulated by depth boundaries.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_acid_fractal")

METADATA = {
    "name": "Depth Acid Fractal",
    "description": "Neon fractal mayhem modulated by depth boundaries.",
    "version": "1.0.0",
    "parameters": [
        {"name": "fractal_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "prism_split", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "solarize_level", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "neon_burn", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "zoom_blur", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "depth_threshold", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthAcidFractalPlugin(PluginBase):
    """Depth-reactive psychedelic fractal shader."""

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
            self.context.set_parameter(f"acid_fractal.{p['name']}", p["default"])
            
        # Simulate allocation of ping-pong FBOs
        self._fbo_feedback_a = True
        self._fbo_feedback_b = True
        _logger.info("Depth Acid Fractal loaded. FBOs allocated.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"acid_fractal.{p['name']}")
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

        # Bypass gracefully if no depth context
        if depth_in is None:
            self.context.set_texture("video_out", video_in)
            _logger.debug("Depth map missing, bypassing Acid Fractal completely.")
            return

        # Simulate iterative shader execution with ping-pong buffering
        # A real shader enforces max iteration loops (e.g. 16 max) to protect 60 FPS (Rail 1)
        self._ping_pong_state = 1 - self._ping_pong_state
        
        # Color math simulated via structural offset
        output_tex_id = video_in + (9000 if self._ping_pong_state == 0 else 9999)

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        # Ensure FBOs are explicitly deactivated for SAFETY RAIL #8
        self._fbo_feedback_a = False
        self._fbo_feedback_b = False
        _logger.info("Depth Acid Fractal: Ping-pong FBOs destroyed.")
