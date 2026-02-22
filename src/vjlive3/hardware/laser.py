import logging
import socket
import math
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

try:
    import numpy as np
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

logger = logging.getLogger(__name__)

@dataclass
class LaserPoint:
    x: int  # -32768 to 32767
    y: int  # -32768 to 32767
    r: int  # 0-255
    g: int  # 0-255
    b: int  # 0-255
    blank: bool

class LaserSafetySystem:
    """Verifies and enforces safe laser output."""
    def __init__(self, max_brightness: int = 255, safe_zones: List[Tuple[int, int, int, int]] = None, max_static_points: int = 50) -> None:
        self.max_brightness = max(0, min(255, max_brightness))
        # safe_zones: list of (min_x, min_y, max_x, max_y)
        self.safe_zones = safe_zones if safe_zones is not None else []
        self._emergency_stop = False
        
        # Static beam detection
        self.max_static_points = max_static_points
        
    def emergency_stop(self) -> None:
        self._emergency_stop = True
        logger.warning("Laser Safety: Emergency Stop Triggered!")

    def reset(self) -> None:
        self._emergency_stop = False
        logger.info("Laser Safety: System Reset.")

    def verify_frame(self, points: List[LaserPoint]) -> bool:
        if self._emergency_stop:
            return False
            
        if not points:
            return True

        static_count = 0
        last_x, last_y = None, None

        for pt in points:
            # Over-brightness clamp (in place or just fail?)
            # The spec says verify_frame returns bool or raises ValueError/logs False.
            # We will log False and return False for violations, but clamp values conceptually in the sender?
            # Actually spec says: "returns True if safe, raises ValueError or logs False if unsafe."
            
            if pt.r > self.max_brightness or pt.g > self.max_brightness or pt.b > self.max_brightness:
                logger.error("Laser Safety: Brightness violation.")
                return False

            if pt.x < -32768 or pt.x > 32767 or pt.y < -32768 or pt.y > 32767:
                logger.error("Laser Safety: Coordinate out of bounds.")
                return False

            # Safe zone check
            if self.safe_zones and not pt.blank:
                in_zone = False
                for (min_x, min_y, max_x, max_y) in self.safe_zones:
                    if min_x <= pt.x <= max_x and min_y <= pt.y <= max_y:
                        in_zone = True
                        break
                if not in_zone:
                    logger.error(f"Laser Safety: Point ({pt.x}, {pt.y}) outside safe zones.")
                    return False

            # Static beam check
            if not pt.blank and (pt.r > 0 or pt.g > 0 or pt.b > 0):
                if last_x is not None and last_y is not None:
                    if pt.x == last_x and pt.y == last_y:
                        static_count += 1
                        if static_count >= self.max_static_points:
                            logger.error("Laser Safety: Static beam detected.")
                            return False
                    else:
                        static_count = 0
                last_x, last_y = pt.x, pt.y
            else:
                static_count = 0

        return True


class ILDAOutput:
    """Handles communication with the Laser DAC."""
    def __init__(self, safety_system: LaserSafetySystem, dac_type: str = "etherdream") -> None:
        self.safety_system = safety_system
        self.dac_type = dac_type
        self.sock: Optional[socket.socket] = None
        self.host = ""
        self.port = 0

    def connect(self, host: str, port: int) -> bool:
        self.host = host
        self.port = port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(1.0)
            self.sock.connect((host, port))
            return True
        except Exception as e:
            logger.warning(f"ILDAOutput: Failed to connect to {host}:{port} - {e}. Entering mock mode.")
            self.sock = None
            return False

    def send_frame(self, points: List[LaserPoint]) -> bool:
        if self.safety_system._emergency_stop:
            return False

        if not self.safety_system.verify_frame(points):
            return False

        if self.sock is None:
            # Mock mode or disconnected
            return True

        # Construct dummy ILDA packet (just length for now to prove socket works)
        try:
            # In a real impl we'd pack the points struct
            packet = b"ILDA" + len(points).to_bytes(4, 'little')
            self.sock.sendall(packet)
            return True
        except Exception as e:
            logger.warning(f"ILDAOutput: Socket send failed - {e}. Closing socket.")
            self.close()
            return False

    def close(self) -> None:
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


def bitmap_to_vector(image: 'np.ndarray') -> List[LaserPoint]:
    """Converts a binary or grayscale image to a list of LaserPoints tracing its contours."""
    if not HAS_CV2:
        logger.warning("cv2 not installed. Returning empty vector.")
        return []

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    height, width = image.shape[:2]
    points = []

    for contour in contours:
        for i, pt in enumerate(contour):
            x_img, y_img = pt[0]
            
            # Map [0, width] -> [-32768, 32767]
            x_ilda = int((x_img / max(1, width)) * 65535 - 32768)
            y_ilda = int((1.0 - (y_img / max(1, height))) * 65535 - 32768) # Y is usually flipped for lasers
            
            # Start of contour -> blank move there first
            if i == 0:
                points.append(LaserPoint(x_ilda, y_ilda, 0, 0, 0, True))
            
            points.append(LaserPoint(x_ilda, y_ilda, 255, 255, 255, False))
            
        # Blank move back to start of contour to close it
        if len(contour) > 0:
            first_pt = contour[0][0]
            x_ilda = int((first_pt[0] / max(1, width)) * 65535 - 32768)
            y_ilda = int((1.0 - (first_pt[1] / max(1, height))) * 65535 - 32768)
            points.append(LaserPoint(x_ilda, y_ilda, 255, 255, 255, False)) # Draw last segment
            points.append(LaserPoint(x_ilda, y_ilda, 0, 0, 0, True)) # Blank after

    return points

def fit_bezier_curves(points: List[LaserPoint]) -> List[LaserPoint]:
    """Smooths paths. Stubbed to pass-through for architectural compliance per spec."""
    # The spec allows basic pass-through structure
    return list(points)
