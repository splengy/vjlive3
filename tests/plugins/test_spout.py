import pytest
import numpy as np
import sys
from unittest.mock import patch, MagicMock

import vjlive3.plugins.spout as spout_mod
from vjlive3.plugins.api import PluginContext

def test_spout_mock_fallback_on_linux():
    """On non-Windows platforms, or if the library is missing, instantiation creates Mock objects without crashing."""
    mgr = spout_mod.SpoutManager()
    assert mgr._mock_mode is True
    assert mgr.get_senders() == []
    
def test_spout_sender_lifecycle():
    """SpoutSender can be created and destroy() cleans up resources without error."""
    sender = spout_mod.SpoutSender("Test_Out")
    assert sender._mock_mode is True
    
    assert sender.send_texture(1, 1920, 1080) is True
    
    dummy = np.zeros((10, 10, 4), dtype=np.uint8)
    assert sender.send_image(dummy) is True
    
    sender.destroy()
    assert sender._sender is None

def test_spout_receiver_mock_read():
    """receive_image on a Mock receiver returns None or a blank array safely."""
    receiver = spout_mod.SpoutReceiver("Test_In")
    assert receiver._mock_mode is True
    
    assert receiver.receive_texture(1) is True
    
    image = receiver.receive_image()
    assert image is None
    
    receiver.destroy()
    assert receiver._receiver is None

def test_spout_plugin_api():
    """Ensure the plugin wrapper implements the factory correctly."""
    plugin = spout_mod.SpoutPlugin()
    context = MagicMock(spec=PluginContext)
    
    plugin.initialize(context)
    assert plugin.manager is not None
    
    sender = plugin.create_sender("test")
    receiver = plugin.create_receiver("test")
    
    assert len(plugin.active_senders) == 1
    assert len(plugin.active_receivers) == 1
    
    plugin.cleanup()
    assert len(plugin.active_senders) == 0
    assert len(plugin.active_receivers) == 0

@patch('vjlive3.plugins.spout.HAS_SPOUT', True)
@patch('vjlive3.plugins.spout.SpoutGL', create=True)
def test_spout_full_execution(mock_spoutgl):
    # Setup mocks
    mock_sender_inst = MagicMock()
    mock_receiver_inst = MagicMock()
    mock_spout_inst = MagicMock()
    
    mock_spoutgl.SpoutSender.return_value = mock_sender_inst
    mock_spoutgl.SpoutReceiver.return_value = mock_receiver_inst
    mock_spoutgl.Spout.return_value = mock_spout_inst
    
    # Test Sender
    s = spout_mod.SpoutSender("S1")
    assert s._mock_mode is False
    
    s.send_texture(1, 100, 100)
    mock_sender_inst.sendTexture.assert_called_with(1, 100, 100)
    
    dummy = np.zeros((10, 10, 4), dtype=np.uint8)
    s.send_image(dummy)
    mock_sender_inst.sendImage.assert_called()
    
    s.destroy()
    mock_sender_inst.releaseSender.assert_called_once()
    
    # Test Receiver
    r = spout_mod.SpoutReceiver("R1")
    r.receive_texture(1)
    mock_receiver_inst.receiveTexture.assert_called_with(1, 0, 0)
    
    mock_receiver_inst.getSenderWidth.return_value = 10
    mock_receiver_inst.getSenderHeight.return_value = 10
    mock_receiver_inst.receiveImage.return_value = True
    
    img = r.receive_image()
    assert img is not None
    assert img.shape == (10, 10, 4)
    
    r.destroy()
    mock_receiver_inst.releaseReceiver.assert_called_once()
    
    # Test Manager
    m = spout_mod.SpoutManager()
    mock_spout_inst.getSenderCount.return_value = 2
    mock_spout_inst.getSenderName.side_effect = ["A", "B"]
    
    senders = m.get_senders()
    assert senders == ["A", "B"]

@patch('vjlive3.plugins.spout.HAS_SPOUT', True)
@patch('vjlive3.plugins.spout.SpoutGL', create=True)
def test_spout_exceptions(mock_spoutgl):
    # Ensure it fails gracefully when creating
    mock_spoutgl.SpoutSender.side_effect = Exception("Boom")
    s = spout_mod.SpoutSender("S1")
    assert s._mock_mode is True # Falls back
    
    mock_spoutgl.SpoutReceiver.side_effect = Exception("Boom")
    r = spout_mod.SpoutReceiver("R1")
    assert r._mock_mode is True
    
    mock_spoutgl.Spout.side_effect = Exception("Boom")
    m = spout_mod.SpoutManager()
    assert m._mock_mode is True

@patch('vjlive3.plugins.spout.HAS_SPOUT', True)
@patch('vjlive3.plugins.spout.SpoutGL', create=True)
def test_spout_runtime_exceptions(mock_spoutgl):
    # Ensure it handles exceptions during operations without crashing
    mock_sender_inst = MagicMock()
    mock_receiver_inst = MagicMock()
    
    mock_spoutgl.SpoutSender.return_value = mock_sender_inst
    mock_spoutgl.SpoutReceiver.return_value = mock_receiver_inst
    
    s = spout_mod.SpoutSender("S1")
    # Force exception inside sendTexture
    mock_sender_inst.sendTexture.side_effect = Exception("GPU Crash")
    assert s.send_texture(1, 100, 100) is False
    
    mock_sender_inst.sendImage.side_effect = Exception("Image Crash")
    assert s.send_image(np.zeros((10, 10, 4))) is False
    
    # Exception inside destroy shouldn't leak
    mock_sender_inst.releaseSender.side_effect = Exception("Crash")
    s.destroy()
    assert s._sender is None
    
    r = spout_mod.SpoutReceiver("R1")
    mock_receiver_inst.receiveTexture.side_effect = Exception("GPU Crash")
    assert r.receive_texture(1) is False
    
    mock_receiver_inst.getSenderWidth.side_effect = Exception("Size crash")
    assert r.receive_image() is None
    
    mock_receiver_inst.releaseReceiver.side_effect = Exception("Crash")
    r.destroy()
    assert r._receiver is None
