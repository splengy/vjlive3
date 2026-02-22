import pytest
import numpy as np
import socket
from unittest.mock import patch, MagicMock
from vjlive3.hardware.laser import LaserPoint, LaserSafetySystem, ILDAOutput, bitmap_to_vector, fit_bezier_curves

def test_laser_safety_static_beam():
    """A frame with all identical coordinates is rejected by the safety system."""
    safety = LaserSafetySystem(max_static_points=10)
    
    # Generate 15 identical bright points
    points = [LaserPoint(0, 0, 255, 0, 0, False) for _ in range(15)]
    
    # Should fail verification because it exceeds max_static_points
    assert safety.verify_frame(points) is False
    
    # Generating alternating points should pass
    safe_points = []
    for i in range(15):
        safe_points.append(LaserPoint(i % 2, 0, 255, 0, 0, False))
    assert safety.verify_frame(safe_points) is True

def test_laser_safety_out_of_bounds():
    """Points outside safe zones are correctly flagged and the frame is rejected."""
    # Strict bounding box: x (-100, 100), y (-100, 100)
    safety = LaserSafetySystem(safe_zones=[(-100, -100, 100, 100)])
    
    valid_points = [LaserPoint(50, 50, 100, 100, 100, False)]
    assert safety.verify_frame(valid_points) is True
    
    invalid_zone_points = [LaserPoint(150, 50, 100, 100, 100, False)]
    assert safety.verify_frame(invalid_zone_points) is False
    
    # Test absolute hardware bounds (-32768 to 32767)
    safety_no_zones = LaserSafetySystem()
    invalid_hard_bounds = [LaserPoint(40000, 0, 255, 0, 0, False)]
    assert safety_no_zones.verify_frame(invalid_hard_bounds) is False
    
    # Test brightness bounds
    oversaturated = [LaserPoint(0, 0, 300, 0, 0, False)]
    assert safety_no_zones.verify_frame(oversaturated) is False

def test_ilda_emergency_stop():
    """Triggering emergency_stop() causes send_frame() to immediately return False and send zero-intensity."""
    safety = LaserSafetySystem()
    ilda = ILDAOutput(safety)
    
    # Verify works initially
    assert ilda.send_frame([LaserPoint(0, 0, 100, 0, 0, False)]) is True
    
    # Emergency Stop
    safety.emergency_stop()
    assert ilda.send_frame([LaserPoint(0, 0, 100, 0, 0, False)]) is False
    
    # Reset
    safety.reset()
    assert ilda.send_frame([LaserPoint(0, 0, 100, 0, 0, False)]) is True

@patch('vjlive3.hardware.laser.socket.socket')
def test_ilda_socket_networking(mock_socket_cls):
    """Test ILDA TCP connection and sending."""
    mock_sock = MagicMock()
    mock_socket_cls.return_value = mock_sock
    
    safety = LaserSafetySystem()
    ilda = ILDAOutput(safety)
    
    assert ilda.connect("127.0.0.1", 12345) is True
    mock_sock.connect.assert_called_with(("127.0.0.1", 12345))
    
    points = [LaserPoint(0, 0, 255, 255, 255, False)]
    assert ilda.send_frame(points) is True
    mock_sock.sendall.assert_called()
    
    # Force exception on send
    mock_sock.sendall.side_effect = Exception("Network dropped")
    assert ilda.send_frame(points) is False
    # Verify close was called via the wrapper
    assert ilda.sock is None
    
    # Test failed connection
    mock_socket_cls.side_effect = Exception("Connection Refused")
    assert ilda.connect("127.0.0.1", 12346) is False
    assert ilda.sock is None
    
    ilda.close() # Safe to close when none

def test_bitmap_to_vector_output():
    """A solid white square image results in 4 corner points (or perimeter trace) and not random noise."""
    import cv2 # Assume present
    # Create 100x100 black image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Draw a 50x50 white square in center
    cv2.rectangle(img, (25, 25), (75, 75), (255, 255, 255), -1)
    
    vectors = bitmap_to_vector(img)
    
    # Should trace the contours
    assert len(vectors) > 0
    # Must have blanking moves
    blanks = [v for v in vectors if v.blank]
    assert len(blanks) > 0
    
    # Ensure coordinates map between -32768 and 32767
    for v in vectors:
        assert -32768 <= v.x <= 32767
        assert -32768 <= v.y <= 32767
        
def test_fit_bezier_curves():
    points = [LaserPoint(0, 0, 0, 0, 0, False)]
    fitted = fit_bezier_curves(points)
    assert len(fitted) == 1
    assert fitted[0].x == 0
    
@patch('vjlive3.hardware.laser.HAS_CV2', False)
def test_bitmap_to_vector_no_cv2():
    img = np.zeros((10, 10), dtype=np.uint8)
    assert bitmap_to_vector(img) == []

def test_safety_verify_empty_frame():
    safety = LaserSafetySystem()
    assert safety.verify_frame([]) is True
