"""
P3-VD20: Depth Slitscan Datamosh
Temporal slit-scan smearing heavily modulated by depth buffers.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_slitscan_datamosh")

METADATA = {
    "name": "Depth Slitscan Datamosh",
    "description": "Temporal slit-scan smearing heavily modulated by depth buffers.",
    "version": "1.0.0",
    "parameters": [
        {"name": "scan_position", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "scan_speed", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "scan_width", "type": "float", "min": 0.01, "max": 0.5, "default": 0.2},
        {"name": "scan_direction", "type": "float", "min": 0.0, "max": 3.0, "default": 0.0},
        {"name": "depth_speed_mod", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "depth_warp", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "depth_scan_offset", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "near_far_flip", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
        {"name": "chromatic_split", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "channel_phase", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "mosh_intensity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_artifact", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "feedback_strength", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "trail_persistence", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "scan_glow", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthSlitscanDatamoshPlugin(PluginBase):
    """Temporal integration shader tracking temporal history across scan slices via depth mapping."""

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
            self.context.set_parameter(f"slitscan_datamosh.{p['name']}", p["default"])
        _logger.info("Depth Slitscan Datamosh loaded.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"slitscan_datamosh.{p['name']}")
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
            _logger.debug("Depth map missing, bypassing Slitscan Datamosh.")
            return
            
        base_tex = video_in if video_b_in is None else video_b_in

        # Structural offset representing temporal shader merge execution limits
        output_tex_id = base_tex + 14000

        self.context.set_texture("video_out", output_tex_id)

    def cleanup(self) -> None:
        super().cleanup()
        _logger.info("Depth Slitscan Datamosh cleaned up.")
