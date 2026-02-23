import pytest
from unittest.mock import MagicMock, patch

class DummyMidoMessage:
    def __init__(self, type, channel=0, note=0, velocity=0, value=0):
        self.type = type
        self.channel = channel
        self.note = note
        self.velocity = velocity
        self.value = value

@pytest.fixture
def mock_mido():
    with patch('vjlive3.core.midi_controller.mido') as mock:
        yield mock

def test_midi_scan(mock_mido):
    """Devices are scanned without error."""
    mock_mido.get_input_names.return_value = ["Launchpad Mini", "Akai MPK"]
    controller = MidiController()
    
    devices = controller.scan_devices()
    assert devices == ["Launchpad Mini", "Akai MPK"]
    mock_mido.get_input_names.assert_called_once()

def test_midi_scan_exception(mock_mido):
    """Scan fails gracefully."""
    mock_mido.get_input_names.side_effect = Exception("No RT Midi Backend")
    controller = MidiController()
    devices = controller.scan_devices()
    assert devices == []

def test_device_connection(mock_mido):
    mock_port = MagicMock()
    mock_mido.open_input.return_value = mock_port
    
    controller = MidiController()
    result = controller.connect("Launchpad Mini")
    
    assert result is True
    status = controller.get_status()
    assert status.is_connected is True
    assert status.name == "Launchpad Mini"

def test_device_connection_failure(mock_mido):
    mock_mido.open_input.side_effect = IOError("Device not found")
    
    controller = MidiController()
    result = controller.connect("Invalid")
    
    assert result is False
    status = controller.get_status()
    assert status.is_connected is False

def test_device_disconnect_graceful(mock_mido):
    """Disconnecting does not crash the application."""
    mock_port = MagicMock()
    mock_mido.open_input.return_value = mock_port
    
    controller = MidiController()
    controller.connect("Device")
    assert controller.get_status().is_connected is True
    
    controller.disconnect()
    
    mock_port.close.assert_called_once()
    assert controller.get_status().is_connected is False
    assert controller.get_status().name == ""

def test_midi_event_parsing_and_callback():
    """Raw messages correctly translate to MidiEvent objects and fire callbacks."""
    controller = MidiController()
    
    # Manually inject a mock port into the controller to bypass hardware mido.open_input
    mock_port = MagicMock()
    msg_note_on = DummyMidoMessage('note_on', channel=1, note=60, velocity=100)
    msg_note_off = DummyMidoMessage('note_off', channel=1, note=60, velocity=0)
    msg_cc = DummyMidoMessage('control_change', channel=2, value=127)
    msg_other = DummyMidoMessage('pitchwheel') # Should be ignored
    
    mock_port.iter_pending.return_value = [msg_note_on, msg_note_off, msg_cc, msg_other]
    controller._port = mock_port
    controller._is_connected = True
    
    received_events = []
    def callback(event: MidiEvent):
        received_events.append(event)
        
    controller.register_callback(callback)
    
    # Perform a poll
    controller.poll()
    
    assert len(received_events) == 3
    
    assert received_events[0].type == 'note_on'
    assert received_events[0].note == 60
    assert received_events[0].velocity == 100
    
    assert received_events[1].type == 'note_off'
    assert received_events[1].velocity == 0
    
    assert received_events[2].type == 'cc'
    assert received_events[2].channel == 2
    assert received_events[2].value == 127

def test_callback_exception_handling():
    """If a callback crashes, the poll loop should not die."""
    controller = MidiController()
    mock_port = MagicMock()
    mock_port.iter_pending.return_value = [DummyMidoMessage('note_on')]
    controller._port = mock_port
    controller._is_connected = True
    
    def crash_callback(event):
        raise ValueError("Bad callback")
        
    controller.register_callback(crash_callback)
    
    # Should not throw exception to caller
    controller.poll() 

def test_poll_hardware_disconnect():
    """If port throws read error, disconnect automatically."""
    controller = MidiController()
    mock_port = MagicMock()
    mock_port.iter_pending.side_effect = IOError("USB Device ripped out")
    controller._port = mock_port
    controller._is_connected = True
    
    controller.poll()
    
    assert controller.get_status().is_connected is False
    
def test_no_mido_graceful():
    """Checks operation if mido is completely uninstalled."""
    with patch('vjlive3.core.midi_controller.mido', None):
        controller = MidiController()
        assert controller.scan_devices() == []
        assert controller.connect("X") is False
