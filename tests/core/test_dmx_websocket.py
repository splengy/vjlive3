import pytest
from vjlive3.core.dmx.websocket import DmxWebSocketHandler

class MockSocketServer:
    def __init__(self):
        self.emitted = []
        
    def emit(self, event, payload):
        self.emitted.append((event, payload))

@pytest.fixture
def ws_handler():
    server = MockSocketServer()
    # Passing None for dmx_engine since it isn't actively called in this test suite
    return DmxWebSocketHandler(dmx_engine=None, socketio_server=server)

def test_dmx_ws_add_remove_mapping(ws_handler):
    # Add via direct call
    mapping = ws_handler.add_mapping("opacity", 10)
    assert len(ws_handler.get_mappings()) == 1
    assert mapping.parameter_name == "opacity"
    
    # Remove via handle_message
    res = ws_handler.handle_message("dmx/remove_mapping", {"id": mapping.mapping_id})
    assert res["status"] == "ok"
    assert len(ws_handler.get_mappings()) == 0

def test_dmx_ws_learn_mode(ws_handler):
    # Start learn mode
    res = ws_handler.handle_message("dmx/start_learn", {"parameter": "strobe_rate"})
    assert res["status"] == "ok"
    assert ws_handler.learn_target_parameter == "strobe_rate"
    
    # Process DMX input to trigger learn completion
    ws_handler.process_dmx_input(channel=5, value=127)
    
    # Learn mode should have cleared automatically
    assert ws_handler.learn_target_parameter is None
    
    # Ensure mapping was saved
    mappings = list(ws_handler.get_mappings().values())
    assert len(mappings) == 1
    assert mappings[0].parameter_name == "strobe_rate"
    assert mappings[0].dmx_channel == 5
    
    # Ensure event was emitted
    server = ws_handler.server
    assert len(server.emitted) == 1
    assert server.emitted[0][0] == "dmx/mapping_created"
    assert server.emitted[0][1]["parameter_name"] == "strobe_rate"

def test_dmx_ws_invalid_action(ws_handler):
    # Missing action fields
    res = ws_handler.handle_message("dmx/start_learn", {})
    assert res["status"] == "error"
    
    res = ws_handler.handle_message("dmx/add_mapping", {"parameter": "foo"})
    assert res["status"] == "error"
    
    res = ws_handler.handle_message("dmx/remove_mapping", {})
    assert res["status"] == "error"

    # Unknown action
    res = ws_handler.handle_message("unknown/action", {})
    assert res["status"] == "error"
    assert "Unknown action" in res["message"]

def test_dmx_ws_overlapping_learn(ws_handler):
    ws_handler.start_learn("alpha")
    assert ws_handler.learn_target_parameter == "alpha"
    
    # Starting a new one overwrites the old one
    ws_handler.start_learn("beta")
    assert ws_handler.learn_target_parameter == "beta"

def test_process_dmx_input_normal(ws_handler):
    # Direct pass-through input emission when not learning
    ws_handler.process_dmx_input(channel=12, value=42)
    server = ws_handler.server
    assert len(server.emitted) == 1
    assert server.emitted[0][0] == "dmx/input"
    assert server.emitted[0][1] == {"channel": 12, "value": 42}

def test_dmx_add_mapping_via_message(ws_handler):
    res = ws_handler.handle_message("dmx/add_mapping", {"parameter": "color", "channel": 6})
    assert res["status"] == "ok"
    
    mapping_id = res["mapping"]["mapping_id"]
    assert mapping_id in ws_handler.get_mappings()
    
def test_dmx_stop_learn_via_message(ws_handler):
    ws_handler.start_learn("temp")
    res = ws_handler.handle_message("dmx/stop_learn", {})
    assert res["status"] == "ok"
    assert ws_handler.learn_target_parameter is None
