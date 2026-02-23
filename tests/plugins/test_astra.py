import sys
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from vjlive3.plugins.astra import AstraDepthCamera, AstraPlugin

def test_astra_simulator_fallback():
    cam = AstraDepthCamera(width=320, height=240, use_simulation=True)
    assert cam.start() is True
    assert cam.is_hardware_connected() is False
    
    depth, rgb = cam.get_frames()
    
    # Assert dimensions
    assert depth.shape == (240, 320)
    assert rgb.shape == (240, 320, 3)
    
    # Assert data types and normalization constraints
    assert depth.dtype == np.float32
    assert rgb.dtype == np.uint8
    assert np.min(depth) >= 0.0
    assert np.max(depth) <= 1.0
    
    cam.stop()

@patch('vjlive3.plugins.astra.cv2')
def test_astra_hardware_start_failure(mock_cv2, caplog):
    # Force cv2 backend to fail opening
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_OPENNI2 = 1600
    
    # Do not set use_simulation so it tries hardware first
    cam = AstraDepthCamera(use_simulation=False)
    assert cam.start() is True
    
    # It should have caught the failure and fallen back
    assert cam.is_hardware_connected() is False
    assert "Hardware start failed" in caplog.text
    assert "Falling back to Simulator" in caplog.text

@patch('vjlive3.plugins.astra.cv2')
def test_astra_disconnect_recovery(mock_cv2, caplog):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    
    # First grab succeeds, second fails
    mock_cap.grab.side_effect = [True, False]
    
    # Return mock BGR and Depth maps for retrieve
    def mock_retrieve(image, target):
        if target == mock_cv2.CAP_OPENNI_DEPTH_MAP:
            return True, np.ones((480, 640), dtype=np.uint16) * 1000
        if target == mock_cv2.CAP_OPENNI_BGR_IMAGE:
            return True, np.zeros((480, 640, 3), dtype=np.uint8)
        return False, None
        
    mock_cap.retrieve.side_effect = mock_retrieve
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_OPENNI2 = 1600
    mock_cv2.CAP_OPENNI_DEPTH_MAP = 1
    mock_cv2.CAP_OPENNI_BGR_IMAGE = 2

    # Provide a mock function for cvtColor
    mock_cv2.cvtColor.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
    
    cam = AstraDepthCamera(use_simulation=False)
    assert cam.start() is True
    assert cam.is_hardware_connected() is True
    
    # First frame (hardware grab succeeds)
    depth1, rgb1 = cam.get_frames()
    assert np.isclose(depth1[0,0], 1000.0 / 5000.0)  # normalized correctly
    
    # Second frame (hardware grab fails -> falls back to simulator)
    depth2, rgb2 = cam.get_frames()
    assert cam.is_hardware_connected() is False
    assert "Hardware read failed. Dropping to Simulator" in caplog.text
    
    cam.stop()

def test_astra_plugin_registration():
    # Setup mock API
    mock_context = MagicMock(spec=MagicMock())
    
    # Load plugin
    plugin = AstraPlugin()
    
    # Patch camera to use simulation strictly for speed
    with patch('vjlive3.plugins.astra.AstraDepthCamera') as MockCam:
        mock_cam_instance = MockCam.return_value
        mock_cam_instance.start.return_value = True
        mock_cam_instance.get_frames.return_value = (np.zeros((10,10), dtype=np.float32), np.zeros((10,10,3), dtype=np.uint8))
        mock_cam_instance.is_hardware_connected.return_value = False
        
        plugin.initialize(mock_context)
        
        # Verify Context Processing
        plugin.process()
        
        # Using context dictionary fallback
        mock_context.set_parameter.assert_any_call("astra.depth", mock_cam_instance.get_frames.return_value[0])
        mock_context.set_parameter.assert_any_call("astra.rgb", mock_cam_instance.get_frames.return_value[1])
        mock_context.set_parameter.assert_any_call("astra.is_hardware", False)
        
        plugin.cleanup()
        mock_cam_instance.stop.assert_called_once()


def test_astra_plugin_process_no_camera():
    plugin = AstraPlugin()
    mock_context = MagicMock(spec=MagicMock())
    
    # process should safely exit if camera wasn't init'd
    plugin.context = mock_context
    plugin.process()
    mock_context.set_parameter.assert_not_called()
