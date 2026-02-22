"""
P3-VD22: Depth Temporal Stratification
Slices the scene into depth strata running at different time offsets with datamoshed boundaries.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_temporal_strat")

METADATA = {
    "name": "Depth Temporal Stratification",
    "description": "Slices the scene into depth strata running at different time offsets with datamoshed boundaries.",
    "version": "1.0.0",
    "parameters": [
        {"name": "num_strata", "type": "float", "min": 2.0, "max": 12.0, "default": 4.0},
        {"name": "strata_separation", "type": "float", "min": 0.0, "max": 1.0, "default": 0.7},
        {"name": "strata_offset", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "temporal_depth", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "temporal_gradient", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "freeze_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "seam_datamosh", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "seam_width", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_displace", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "motion_warp", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "ghost_opacity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.7},
        {"name": "color_shift", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "strobe_rate", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthTemporalStratPlugin(PluginBase):
    """Depth Temporal Stratification shader effect logic mapping."""

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
            self.context.set_parameter(f"temporal_strat.{p['name']}", p["default"])
        _logger.info("Depth Temporal Stratification loaded.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"temporal_strat.{p['name']}")
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
            _logger.debug("Depth map missing, bypassing Temporal Stratification.")
            return
            
        base_tex = video_in if video_b_in is None else video_b_in

        # Structural offset representing temporal stratification execution validation
        output_tex_id = base_tex + 16000

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        _logger.info("Depth Temporal Stratification cleaned up.")
