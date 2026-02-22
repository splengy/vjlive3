"""
P2-D6 DMX WebSocket Handler
Real-time communication layer between DMX engine and web UI.
"""
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import uuid
import logging

_logger = logging.getLogger("vjlive3.core.dmx.websocket")


@dataclass
class ParameterMapping:
    mapping_id: str
    parameter_name: str
    dmx_channel: int
    min_val: float = 0.0
    max_val: float = 1.0
    inverted: bool = False


class DmxWebSocketHandler:
    """
    Handles transmitting DMX state changes, receiving manual overrides,
    and managing DMX Learn mode to map incoming channels to UI parameters.
    """
    def __init__(self, dmx_engine: Any, socketio_server: Any = None) -> None:
        self.dmx_engine = dmx_engine
        # socketio_server is optional/generic for emitting outgoing messages 
        # (e.g., standard API or asyncio Queue/FastAPI broadcast mechanic)
        self.server = socketio_server
        
        self.mappings: Dict[str, ParameterMapping] = {}
        self.learn_target_parameter: Optional[str] = None
        
    def handle_message(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming WebSocket messages from the UI."""
        if action == "dmx/start_learn":
            param = payload.get("parameter")
            if not param:
                return {"status": "error", "message": "Missing 'parameter'"}
            self.start_learn(param)
            return {"status": "ok", "message": f"Learning {param}"}
            
        elif action == "dmx/stop_learn":
            self.stop_learn()
            return {"status": "ok"}
            
        elif action == "dmx/add_mapping":
            param = payload.get("parameter")
            channel = payload.get("channel")
            if param is None or channel is None:
                return {"status": "error", "message": "Missing 'parameter' or 'channel'"}
            
            mapping = self.add_mapping(
                parameter=param, 
                channel=channel, 
                min_val=payload.get("min_val", 0.0),
                max_val=payload.get("max_val", 1.0),
                inverted=payload.get("inverted", False)
            )
            return {"status": "ok", "mapping": asdict(mapping)}
            
        elif action == "dmx/remove_mapping":
            mapping_id = payload.get("id")
            if not mapping_id:
                return {"status": "error", "message": "Missing 'id'"}
            success = self.remove_mapping(mapping_id)
            return {"status": "ok" if success else "error"}
            
        return {"status": "error", "message": f"Unknown action: {action}"}

    def add_mapping(self, parameter: str, channel: int, **kwargs: Any) -> ParameterMapping:
        """Create and save a new parameter mapping."""
        mapping_id = str(uuid.uuid4())
        mapping = ParameterMapping(
            mapping_id=mapping_id,
            parameter_name=parameter,
            dmx_channel=channel,
            min_val=kwargs.get("min_val", 0.0),
            max_val=kwargs.get("max_val", 1.0),
            inverted=kwargs.get("inverted", False)
        )
        self.mappings[mapping_id] = mapping
        _logger.info("Added mapping %s for channel %d to %s", mapping_id, channel, parameter)
        return mapping

    def remove_mapping(self, mapping_id: str) -> bool:
        """Delete an existing parameter mapping."""
        if mapping_id in self.mappings:
            del self.mappings[mapping_id]
            _logger.info("Removed mapping %s", mapping_id)
            return True
        return False

    def get_mappings(self) -> Dict[str, ParameterMapping]:
        """Return all current parameter mappings."""
        return dict(self.mappings)

    def start_learn(self, parameter: str) -> None:
        """Enter learn mode for a specific UI parameter."""
        if self.learn_target_parameter:
            _logger.warning("Aborting existing learn session for %s", self.learn_target_parameter)
            
        self.learn_target_parameter = parameter
        _logger.info("Started learning DMX input for parameter: %s", parameter)

    def stop_learn(self) -> None:
        """Exit learn mode."""
        self.learn_target_parameter = None
        _logger.info("Stopped DMX learning")

    def process_dmx_input(self, channel: int, value: int) -> None:
        """Process incoming DMX data (e.g., from an external DMX-in controller)."""
        # If we are in learn mode, auto-map the first incoming signal that crosses a threshold
        if self.learn_target_parameter and value > 0:
            target = self.learn_target_parameter
            mapping = self.add_mapping(parameter=target, channel=channel)
            
            # Emit mapping created event if we have a server mock/handle
            if hasattr(self.server, "emit"):
                self.server.emit("dmx/mapping_created", asdict(mapping))
            
            # Learn mode completes automatically
            self.stop_learn()
            return
            
        # At runtime (not learn mode), we'd look up the channel and apply the parameter 
        # (This runtime mapping application logic usually interacts with the engine or node graph)
        # But this module strictly handles the routing/mapping persistence side of the WebSocket.
        
        # Outgoing emission (e.g., updating UI visualisers)
        if hasattr(self.server, "emit"):
            self.server.emit("dmx/input", {"channel": channel, "value": value})
