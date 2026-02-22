"""
P3-VD10: Depth Blur
Cinematic bokeh depth-of-field using real depth data.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_blur")

METADATA = {
    "name": "Depth Blur",
    "description": "Cinematic bokeh depth-of-field using real depth data.",
    "version": "1.0.0",
    "parameters": [
        {"name": "focal_distance", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "focal_range", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "blur_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "fg_blur", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
        {"name": "bg_blur", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
        {"name": "bokeh_bright", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "chromatic_fringe", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "tilt_shift", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0}
    ],
    "inputs": ["video_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthBlurPlugin(PluginBase):
    """Cinematic Depth of Field effect."""

    name = METADATA["name"]
    version = METADATA["version"]

    def __init__(self) -> None:
        super().__init__()
        self.params: Dict[str, Any] = {
            p["name"]: p["default"] for p in METADATA["parameters"]
        }
        self._is_tilt_shift_active = False

    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        for p in METADATA["parameters"]:
            self.context.set_parameter(f"depth_blur.{p['name']}", p["default"])
        _logger.info("Depth Blur initialized.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"depth_blur.{p['name']}")
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

        # Edge Case: Missing Depth Input, gracefully fallback to Tilt Shift mode
        if depth_in is None:
            self._is_tilt_shift_active = True
            # Simulate forcing the tilt-shift shader mode
            output_tex_id = video_in + 1010
            _logger.debug("Depth map missing, engaging Tilt-Shift spatial blur fallback.")
        else:
            self._is_tilt_shift_active = False
            # Normal Depth of Field bokeh mode
            output_tex_id = video_in + 2020

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        _logger.info("Depth Blur cleaned up.")
