import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Temporarily mock NDIlib import failure to test mock mode natively
with patch.dict('sys.modules', {'NDIlib': None}):
    from vjlive3.plugins.ndi import NDIHub, NDISender, NDIReceiver, NDIPlugin
    from vjlive3.plugins.api import PluginContext

def test_ndi_mock_mode(caplog):
    hub = NDIHub()
    # It should log the fallback warning
    assert "NDI library not found" in caplog.text
    assert hub.mock_mode is True

def test_ndi_sender_mock():
    sender = NDISender("TestSender", mock_mode=True)
    frame = np.zeros((100, 100, 4), dtype=np.uint8)
    
    # Valid frame
    assert sender.send_frame(frame) is True
    
    # Invalid channel count should be caught
    bad_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    assert sender.send_frame(bad_frame) is False
    
    # Invalid type
    assert sender.send_frame("not_a_frame") is False
    
    sender.destroy()

def test_ndi_receiver_mock():
    receiver = NDIReceiver("TestSource", mock_mode=True)
    
    # Cannot read before connect
    assert receiver.read_frame() is None
    
    # Connect and read
    assert receiver.connect() is True
    frame = receiver.read_frame()
    
    assert frame is not None
    assert frame.shape == (1080, 1920, 4)
    assert frame.dtype == np.uint8
    
    receiver.disconnect()
    
    # Cannot read after disconnect
    assert receiver.read_frame() is None

def test_ndi_hub_discovery():
    hub = NDIHub()
    # Mock mode should return empty list safely
    sources = hub.get_available_sources()
    assert isinstance(sources, list)
    assert len(sources) == 0
    
    # Creating instances through hub
    sender = hub.create_sender("MyOut")
    receiver = hub.create_receiver("MyIn")
    
    assert len(hub._senders) == 1
    assert len(hub._receivers) == 1
    
    # Shutdown safely clears references
    hub.shutdown()
    assert len(hub._senders) == 0
    assert len(hub._receivers) == 0

def test_ndi_plugin_lifecycle():
    plugin = NDIPlugin()
    context = MagicMock(spec=PluginContext)
    
    plugin.initialize(context)
    assert plugin.hub is not None
    assert plugin.default_sender is not None
    
    # Process without frame
    context.get_parameter.return_value = None
    plugin.process()
    
    # Process with frame
    frame = np.zeros((10, 10, 4), dtype=np.uint8)
    context.get_parameter.return_value = frame
    plugin.process()
    # (In mock mode, this silently succeeds and does nothing under the hood)
    
    plugin.cleanup()
    assert plugin.hub is None

def test_ndi_real_mode_execution():
    import sys
    from unittest.mock import MagicMock
    
    mock_ndi = MagicMock()
    mock_ndi.FOURCC_VIDEO_TYPE_BGRA = 1
    mock_ndi.FRAME_TYPE_VIDEO = 1
    mock_ndi.RECV_COLOR_FORMAT_BGRX_BGRA = 1
    
    # Provide a mock source structure
    class MockSource:
        ndi_name = "MockNetSource"
    
    mock_ndi.find_get_current_sources.return_value = [MockSource()]
    
    with patch.dict('sys.modules', {'NDIlib': mock_ndi}):
        import importlib
        import vjlive3.plugins.ndi as ndi_module
        importlib.reload(ndi_module)
        
        # Test Sender
        sender = ndi_module.NDISender("TestReal", mock_mode=False)
        assert sender._ndi_send is not None
        frame = np.zeros((10, 10, 4), dtype=np.uint8)
        assert sender.send_frame(frame) is True
        sender.destroy()
        assert sender._ndi_send is None
        
        # Test Receiver
        receiver = ndi_module.NDIReceiver("TestSource", mock_mode=False)
        assert receiver.connect() is True
        class MockVideoFrame:
            data = np.zeros((10, 10, 4), dtype=np.uint8)
        mock_ndi.recv_capture_v2.return_value = (mock_ndi.FRAME_TYPE_VIDEO, MockVideoFrame(), None, None)
        f = receiver.read_frame()
        assert f is not None
        receiver.disconnect()
        
        # Test Hub
        hub = ndi_module.NDIHub()
        assert len(hub.get_available_sources()) == 1
        hub.create_sender("RealOut")
        hub.create_receiver("RealIn")
        hub.shutdown()
        
        # Restore normal state
        importlib.reload(ndi_module)
