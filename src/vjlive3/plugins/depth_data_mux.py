"""
P3-VD32: Depth Data Mux
Depth Data Multiplexer. 1 depth_in → N identical depth_out copies.
Zero processing — just fans depth data to multiple consumers.
"""
from typing import Any, Dict
from vjlive3.plugins.api import PluginBase, PluginContext
import logging

_logger = logging.getLogger("vjlive3.plugins.depth_data_mux")

METADATA = {
    "name": "Depth Data Mux",
    "description": "Depth Data Multiplexer. 1 depth_in → N identical depth_out copies. Zero processing.",
    "version": "1.0.0",
    "parameters": [
        {"name": "num_outputs", "type": "int", "min": 1, "max": 16, "default": 3}
    ],
    "inputs": ["depth_in"],
    "outputs": ["depth_out_1", "depth_out_2", "depth_out_3"]
}

class DepthDataMuxEffect(PluginBase):
    """
    Depth Data Multiplexer.
    1 depth_in → N identical depth_out copies.
    Starts with default outputs. Can grow dynamically based on num_outputs.
    """

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
            self.context.set_parameter(f"depth_data_mux.{p['name']}", p["default"])
            
        _logger.info(f"Depth Data Mux loaded with {self.params['num_outputs']} default outputs.")

    def _read_params_from_context(self) -> None:
        if not self.context:
            return
            
        for p in METADATA["parameters"]:
            val = self.context.get_parameter(f"depth_data_mux.{p['name']}")
            if val is not None:
                # Clamp appropriately
                if p["type"] == "int":
                    val = max(int(p["min"]), min(int(p["max"]), int(float(val))))
                else:
                    val = max(float(p["min"]), min(float(p["max"]), float(val)))
                self.params[p["name"]] = val

    def process(self) -> None:
        if not self.context:
            return
            
        depth_in = self.context.get_texture("depth_in")
        
        self._read_params_from_context()

        # Bypass gracefully if no depth context
        if depth_in is None:
            _logger.debug("Depth map missing, Depth Data Mux bypassing.")
            return

        # Simple pass-through (Fan out to N outputs)
        num_outs = self.params.get("num_outputs", 3)
        for i in range(1, num_outs + 1):
            out_key = f"depth_out_{i}"
            self.context.set_texture(out_key, depth_in)

    def cleanup(self) -> None:
        super().cleanup()
        _logger.info("Depth Data Mux unloaded.")
