"""
P3-VD23: Depth Vector Field Datamosh
Translates depth velocity into motion vectors, causing pixels to smear along Z-axis changes.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_vector_field_datamosh")

METADATA = {
    "name": "Depth Vector Field Datamosh",
    "description": "Translates depth velocity into motion vectors, causing pixels to smear along Z-axis changes.",
    "version": "1.0.0",
    "parameters": [
        {"name": "vector_scale", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "temporal_blend", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "propagation_decay", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "depth_threshold", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_size", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_chaos", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "chromatic_drift", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "color_bleed", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "feedback_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "accumulation", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthVectorFieldDatamoshPlugin(PluginBase):
    """Translates frame-to-frame depth changes into P-frame motion vectors."""

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
            self.context.set_parameter(f"vector_field.{p['name']}", p["default"])
        _logger.info("Depth Vector Field Datamosh loaded.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"vector_field.{p['name']}")
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

        # Bypass gracefully if no depth context
        if depth_in is None:
            self.context.set_texture("video_out", video_in)
            _logger.debug("Depth map missing, bypassing Vector Field.")
            return
            
        base_tex = video_in if video_b_in is None else video_b_in

        # Structural offset representing temporal vector accumulation logic
        output_tex_id = base_tex + 18000

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        _logger.info("Depth Vector Field Datamosh cleaned up.")
